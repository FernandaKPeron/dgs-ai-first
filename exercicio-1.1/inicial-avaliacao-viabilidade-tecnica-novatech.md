# Avaliação de Viabilidade Técnica — Assistente de IA NovaTech

**Cliente:** NovaTech (setor de logística, 1.200 funcionários)
**Fornecedor:** DB1
**Objetivo:** Assistente de IA com RAG sobre a documentação interna, integrado ao ambiente Microsoft (Teams + SharePoint), com respostas em linguagem natural fundamentadas e com indicação de fonte.
**Meta de negócio:** reduzir o tempo médio de busca por chamado de 12 para menos de 2 minutos.

---

## Veredito

O projeto é **tecnicamente viável dentro da janela de 3 meses** (discovery + desenvolvimento + go-live). O risco crítico, porém, **não está no LLM** — está na **ingestão dos documentos** e na **governança de conteúdo contraditório**. A modelagem de linguagem é a parte madura e previsível do sistema; a extração confiável de tabelas, planilhas e documentos escaneados, somada à inexistência de um processo unificado de revisão, é onde o cronograma e a qualidade podem afundar.

Esta avaliação cobre: tratamento por tipo de fonte, dimensionamento da base em tokens, orçamento de contexto e estratégia de chunking — e fecha com dois riscos transversais que recomendamos subir explicitamente ao Tech Lead.

---

## 1. Análise por tipo de fonte

### 1.1 PDFs com tabelas complexas, fluxogramas e documentos escaneados

**Desafio para o pipeline.** A extração de texto "ingênua" (PyPDF e similares) lineariza tabelas: uma tabela de frete com 15+ colunas vira uma sequência de números desvinculada dos cabeçalhos. Fluxogramas embutidos como imagem são invisíveis para extratores de texto, de modo que todo o conhecimento de processo neles contido se perde. Documentos escaneados não possuem camada de texto — sem OCR, o chunk resulta vazio.

**Impacto na qualidade.** É o tipo de erro mais perigoso do projeto. Em frete e SLA o que importa é o número exato; se a coluna "Zona 3 / cliente premium" se mistura com "Zona 4", o assistente entrega um valor errado com aparência de confiança e com citação da fonte. Isso é pior do que não responder, porque o atendente confia.

**Estratégia de tratamento.** Usar parsing com reconhecimento de layout — **Azure AI Document Intelligence**, já presente no ecossistema deles — em vez de extração de texto plano. Ele devolve tabelas estruturadas (célula/linha/coluna) e faz OCR de escaneados no mesmo passo. Cada tabela torna-se um chunk íntegro em Markdown/JSON com o cabeçalho repetido. Para fluxogramas, aplicar um modelo de visão (o próprio GPT-4o) para gerar uma descrição textual pesquisável do fluxo, ou sinalizar para transcrição manual. Validar numericamente uma amostra das tabelas extraídas — não confiar no OCR cegamente.

### 1.2 Wiki Confluence com links internos e macros customizadas

**Desafio para o pipeline.** Os links internos formam um grafo de conhecimento: o contexto de uma página frequentemente reside na página linkada ("conforme política X"). Chunkar a página isolada perde esse vínculo. As macros customizadas renderizam conteúdo dinâmico que não aparece no export bruto (storage format), o que leva à indexação de placeholders quebrados.

**Impacto na qualidade.** Respostas incompletas e referências penduradas — o assistente cita "ver procedimento de reclamação" sem possuir, de fato, aquele conteúdo. O retrieval perde o que está atrás de macro.

**Estratégia de tratamento.** Ingerir via REST API do Confluence capturando o **HTML renderizado** (não o storage format), para materializar a saída das macros. Armazenar os alvos dos links internos como metadado, permitindo co-recuperação de páginas relacionadas. A hierarquia de espaço/página torna-se metadado de filtro.

### 1.3 Planilhas com fórmulas interdependentes

**Desafio para o pipeline.** Para o usuário humano o que importa é o *valor*, mas o export pode trazer a fórmula (`=PROCV(...)`) ou valores sem a lógica. A interdependência faz com que uma célula só tenha sentido junto de outras, e a estrutura 2D significa que linearizar destrói a relação linha/coluna. Além disso, as planilhas mudam mensalmente, então o embedding envelhece.

**Impacto na qualidade.** O assistente devolve texto de fórmula em vez de resposta, ou um valor desatualizado. Como as regras de cálculo de frete moram aqui, o risco é alto.

**Estratégia de tratamento.** Computar as fórmulas e exportar os *valores resolvidos*, convertendo cada tabela em linhas estruturadas com cabeçalho. Para perguntas de cálculo de fato ("qual o frete para X kg na zona Y?"), a melhor abordagem não é RAG sobre texto — é expor a planilha como uma *tool/function* (function calling) que o modelo chama, devolvendo o cálculo determinístico em vez de "lembrar" o número. Automatizar a reingestão no ciclo mensal, com versionamento.

---

## 2. Estimativa do tamanho da base (em tokens)

Regra prática: `tokens = palavras ÷ 0,75`. Assumindo ~500 palavras por página de PDF.

| Fonte | Cálculo | Palavras | Tokens |
|---|---|---|---|
| PDFs | 800 × 10 pg × 500 | 4.000.000 | ~5,33 M |
| Wiki | 400 × 1.500 | 600.000 | ~0,80 M |
| Planilhas | ~50 × ~3.000* | ~150.000 | ~0,20 M |
| **Total** | | | **~6,3 M tokens** |

\* As duas premissas mais frágeis são **500 palavras/página** (varia de 350 a 600 conforme densidade) e **3.000 palavras/planilha** (a mais incerta — depende de quantas abas e linhas). Mesmo errando por ±30%, a conclusão não muda.

**Leitura que importa:** a base tem ~6 milhões de tokens, cerca de **49× a janela do GPT-4o (128K)**. Não existe a opção de "jogar tudo no contexto" — recuperação seletiva (RAG) é obrigatória, não uma escolha de design.

---

## 3. Análise de orçamento de contexto

A conta direta: `(128K − 2K) ÷ 500 ≈ 252 chunks` caberiam fisicamente. Mas esse é o teto *físico*, não o operacional. O orçamento realista:

| Item | Tokens |
|---|---|
| Janela total | 128.000 |
| System prompt + instruções | −2.000 |
| Histórico de conversa (multi-turn) | −~3.000 |
| Reserva para resposta + citações | −~2.000 |
| **Disponível para chunks** | **~121.000** → ~242 chunks |

O ponto central é a distância entre os **~242 que cabem** e os **~10 a 30 que se deve realmente usar**. Encher a janela é contraproducente por quatro motivos:

1. **Lost in the middle** — o modelo atende mal ao que está no meio de um contexto longo, então o chunk 120 é quase ruído.
2. **Diluição de atenção** — 200 chunks medianos afogam os 5 que respondem à pergunta.
3. **Custo e latência** crescem linearmente com os tokens de entrada; a diretoria quer 12→2 min, então latência conta.
4. **Precisão do retrieval** — se são necessários 200 chunks para garantir cobertura, o problema é o ranqueamento, não o tamanho da janela.

**Consequência arquitetural:** o gargalo de qualidade é a **precisão do retrieval**, não a janela. Isso justifica investir em reranking (o *semantic ranker* do Azure AI Search já entrega isso nativamente) e em busca híbrida (vetorial + BM25), porque consultas de SLA/frete têm termos exatos — códigos de cliente, zonas — em que a busca puramente vetorial erra.

---

## 4. Estratégia de chunking recomendada

As perguntas reais dos atendentes caem em três famílias, e cada uma pede um tratamento:

- **Lookup tabular** (prazos/SLA por tipo de cliente, regras de frete): a resposta está numa tabela e precisa dela inteira. Cortar a tabela ao meio destrói a resposta.
- **Procedural/narrativo** (devolução, reclamação): a resposta é uma sequência de passos que precisa permanecer coesa num único chunk.
- **Cross-versão** (as contradições): a resposta depende de *qual* versão e de *quem* é a fonte.

### Recomendação

1. **Chunking consciente da estrutura, não por tamanho fixo de caractere.** Quebrar respeitando títulos, seções e limites de tabela. Prosa: ~400–600 tokens com ~10–15% de overlap, para não cortar um procedimento no meio. Tabelas: o chunk é a tabela inteira (ou grupos de linhas com cabeçalho repetido), nunca fatiada arbitrariamente.

2. **Metadado rico por chunk** — fonte, título, seção, data de atualização, área dona (Operações/Compliance/Comercial) e versão. Isso resolve dois requisitos de uma vez: a *citação da fonte* exigida, e o tratamento de contradição (priorizar o mais recente / mais autoritativo, ou explicitar o conflito ao atendente em vez de escolher silenciosamente).

3. **Contra o lost in the middle:** recuperar com *k* pequeno (5–15 chunks reranqueados, não 200) e ordenar os chunks com os mais relevantes no início e no fim do prompt, deixando o meio para os de apoio. O reranker, posicionado após a busca vetorial, é o que mais move o ponteiro de qualidade aqui.

A escolha de ~500 tokens é razoável como base para prosa, mas não como regra única — tabelas de frete podem precisar de chunks maiores justamente para manter a integridade que torna a resposta correta.

---

## 5. Riscos transversais (recomenda-se subir ao Tech Lead)

Estes dois riscos **não são técnicos de RAG** e podem afundar o cronograma se não forem endereçados no discovery.

### 5.1 Contradições entre versões
O RAG recuperará alegremente dois chunks que se contradizem. Nenhuma quantidade de engenharia de prompt resolve dado de origem inconsistente — hoje a equipe resolve "perguntando para quem sabe", e o assistente não tem para quem perguntar. Isso exige um passo de **governança/curadoria** no discovery (dono por documento, ranking de autoridade, recência). Sem isso, automatiza-se a entrega de respostas erradas — só que mais rápido.

### 5.2 Pipeline de atualização
Três áreas atualizam a documentação mensalmente, sem revisão unificada. Sem **reingestão automatizada e versionada** (webhooks ou sync agendado de SharePoint/Confluence), a base se desatualiza em 30 dias e a confiança da equipe despenca.

---

## 6. Stack recomendada

Tudo encaixa no que a NovaTech já licencia (Microsoft 365 E3 + Azure AI Services):

| Camada | Componente |
|---|---|
| Extração/ingestão | Azure AI Document Intelligence (layout + OCR de tabelas e escaneados) |
| Busca/retrieval | Azure AI Search (vetorial + híbrido BM25 + semantic ranker) |
| Modelo | Azure OpenAI — GPT-4o |
| Cálculo determinístico | Function calling sobre as planilhas de frete |
| Interface | Bot no Microsoft Teams |

**Observação sobre o modelo:** o GPT-4o atende bem. Vale registrar que mesmo modelos com janela maior mantêm o efeito *lost in the middle* — logo, a estratégia de retrieval seletivo é **independente do tamanho da janela** e permanece válida em futuras trocas de modelo.

---

## Conclusão

O caminho técnico é claro e cabe no ecossistema Microsoft/Azure já contratado. A meta de 12→2 minutos é plausível **se** o investimento for direcionado para onde está o risco real: ingestão de qualidade (tabelas, escaneados, planilhas) e governança de conteúdo. Recomenda-se reservar parte substancial do discovery para curadoria documental e definição de autoridade/recência por fonte, antes de otimizar a camada de LLM.
