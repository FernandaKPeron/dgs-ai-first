# Avaliação de Viabilidade Técnica — Assistente de IA NovaTech

**Cliente:** NovaTech (setor de logística, 1.200 funcionários)
**Fornecedor:** DB1
**Objetivo:** Assistente de IA com RAG sobre a documentação interna, integrado ao ambiente Microsoft (Teams + SharePoint), com respostas em linguagem natural fundamentadas e com indicação de fonte.
**Meta de negócio:** reduzir o tempo médio de busca por chamado de 12 para menos de 2 minutos.

---

## Veredito

O projeto é **tecnicamente viável dentro da janela de 3 meses**, mas a viabilidade é **condicional** — não incondicional. O caminho de engenharia é claro e cabe no ecossistema Microsoft/Azure já contratado. A modelagem de linguagem é a parte madura e previsível do sistema. O que decide o sucesso são quatro frentes que **não são** problemas de LLM e que, se não forem endereçadas no discovery, afundam o cronograma ou a confiança da equipe:

1. **Ingestão confiável** de tabelas, planilhas e documentos escaneados.
2. **Governança de conteúdo contraditório** — que é mudança organizacional na NovaTech, não engenharia que a DB1 controla.
3. **Avaliação de qualidade e abstenção** — sem a qual não há critério de aceite nem segurança para go-live.
4. **Segurança de acesso (permission trimming) e privacidade (LGPD)** — sob risco de o assistente virar um canal de vazamento.

A formulação honesta do veredito é: **a meta de 12→2 minutos é plausível _se_ o investimento for direcionado para essas quatro frentes, e não para otimizar a camada de LLM.** Recomenda-se reservar parte substancial do discovery para curadoria documental, definição de autoridade/recência por fonte, e construção do conjunto de avaliação — antes de qualquer ajuste fino do modelo.

Esta avaliação cobre: tratamento por tipo de fonte, dimensionamento da base em tokens, orçamento de contexto, estratégia de chunking, estratégia de avaliação, segurança/privacidade, riscos transversais, stack e uma primeira leitura de custo (OpEx).

---

## 1. Análise por tipo de fonte

### 1.1 PDFs com tabelas complexas, fluxogramas e documentos escaneados

**Desafio para o pipeline.** A extração de texto "ingênua" (PyPDF e similares) lineariza tabelas: uma tabela de frete com 15+ colunas vira uma sequência de números desvinculada dos cabeçalhos. Fluxogramas embutidos como imagem são invisíveis para extratores de texto, de modo que todo o conhecimento de processo neles contido se perde. Documentos escaneados não possuem camada de texto — sem OCR, o chunk resulta vazio.

**Impacto na qualidade.** É o tipo de erro mais perigoso do projeto. Em frete e SLA o que importa é o número exato; se a coluna "Zona 3 / cliente premium" se mistura com "Zona 4", o assistente entrega um valor errado com aparência de confiança e com citação da fonte. Isso é pior do que não responder, porque o atendente confia.

**Estratégia de tratamento.** Usar parsing com reconhecimento de layout — **Azure AI Document Intelligence**, já presente no ecossistema deles — em vez de extração de texto plano. Ele devolve tabelas estruturadas (célula/linha/coluna) e faz OCR de escaneados no mesmo passo. Cada tabela torna-se um chunk íntegro em Markdown/JSON com o cabeçalho repetido. Validar numericamente uma amostra das tabelas extraídas — não confiar no OCR cegamente.

Para fluxogramas, aplicar um modelo de visão (o próprio GPT-4o) para gerar uma descrição textual pesquisável do fluxo. **Atenção:** a extração de fluxograma por visão é tão pouco confiável quanto a extração de tabela por método ingênuo — modelos de visão descrevem *branches* de decisão com erro frequente (trocam condições, perdem ramos). Logo, esse caminho exige **o mesmo passo de validação humana por amostragem** que se aplica às tabelas; não tratar como extração automática confiável. Onde o fluxograma for crítico (ex.: árvore de decisão de reclamação), sinalizar para transcrição manual.

### 1.2 Wiki Confluence com links internos e macros customizadas

**Desafio para o pipeline.** Os links internos formam um grafo de conhecimento: o contexto de uma página frequentemente reside na página linkada ("conforme política X"). Chunkar a página isolada perde esse vínculo. As macros customizadas renderizam conteúdo dinâmico que não aparece no export bruto (storage format), o que leva à indexação de placeholders quebrados.

**Impacto na qualidade.** Respostas incompletas e referências penduradas — o assistente cita "ver procedimento de reclamação" sem possuir, de fato, aquele conteúdo. O retrieval perde o que está atrás de macro.

**Estratégia de tratamento.** Ingerir via REST API do Confluence capturando o **HTML renderizado** (não o storage format), para materializar a saída das macros. Armazenar os alvos dos links internos como metadado, permitindo co-recuperação de páginas relacionadas. A hierarquia de espaço/página torna-se metadado de filtro.

### 1.3 Planilhas com fórmulas interdependentes

**Desafio para o pipeline.** Para o usuário humano o que importa é o *valor*, mas o export pode trazer a fórmula (`=PROCV(...)`) ou valores sem a lógica. A interdependência faz com que uma célula só tenha sentido junto de outras, e a estrutura 2D significa que linearizar destrói a relação linha/coluna. Além disso, as planilhas mudam mensalmente, então o embedding envelhece.

**Impacto na qualidade.** O assistente devolve texto de fórmula em vez de resposta, ou um valor desatualizado. Como as regras de cálculo de frete moram aqui, o risco é alto.

**Estratégia de tratamento — em dois níveis, com escopo honesto.**

Para conteúdo de planilha que funciona como *referência tabular* (ler um valor de uma célula/linha): computar as fórmulas e exportar os *valores resolvidos*, convertendo cada tabela em linhas estruturadas com cabeçalho. Automatizar a reingestão no ciclo mensal, com versionamento.

Para perguntas de **cálculo de fato** ("qual o frete para X kg na zona Y, cliente premium?"), a melhor abordagem não é RAG sobre texto — é expor a lógica como uma *tool/function* (function calling) que o modelo chama, devolvendo o cálculo determinístico em vez de "lembrar" o número.

> **Atenção de escopo — este ponto está subdimensionado se tratado como passo de ingestão.** Expor "a planilha como function" **não** é apontar uma tool para o arquivo. É **reimplementar a lógica de negócio de frete em código determinístico**: fazer engenharia reversa das fórmulas interdependentes do Excel, tratar casos de borda (faixas de peso, exceções por cliente, sobretaxas), validar contra a planilha original, e **manter essa reimplementação sincronizada a cada atualização mensal**. Isso é um **mini-projeto de software dentro do projeto**, não uma tarefa de pipeline.
>
> A decisão tem que ser explícita e tomada no discovery:
> - **(A)** Assumir o function calling de frete no escopo e no cronograma (com esforço de engenharia e manutenção contínua reconhecidos), **ou**
> - **(B)** Aceitar servir valores de frete via RAG sobre valores resolvidos — ciente de que isso reintroduz o risco de valor desatualizado/aproximado que esta própria avaliação classifica como inaceitável para frete.
>
> Não é possível ter a precisão de (A) com o esforço de (B). Recomenda-se (A) para o subconjunto de cálculos de frete realmente críticos, e (B) para o restante das planilhas de referência.

---

## 2. Estimativa do tamanho da base (em tokens)

Regra prática: `tokens ≈ palavras ÷ 0,75`. Assumindo ~500 palavras por página de PDF.

| Fonte | Cálculo | Palavras | Tokens |
|---|---|---|---|
| PDFs | 800 × 10 pg × 500 | 4.000.000 | ~5,33 M |
| Wiki | 400 × 1.500 | 600.000 | ~0,80 M |
| Planilhas | ~50 × ~3.000* | ~150.000 | ~0,20 M |
| **Total** | | | **~6,3 M tokens** |

**Ressalvas sobre as premissas (mais fracas do que o número sugere):**

1. **A regra `÷ 0,75` é heurística de inglês.** Em **português**, a tokenização gasta mais tokens por palavra (acentos e subwords menos frequentes no vocabulário dos modelos), tipicamente **+10% a +30%**. A base real provavelmente está **subestimada** nessa faixa. Isso não muda o veredito (segue obrigatório usar RAG), mas distorce contagem de chunks e, principalmente, **custo**.

2. **A premissa mais frágil não é "500 palavras/página" — é "10 páginas/documento".** A análise de sensibilidade original estressou a densidade da página (350–600 palavras), mas manuais de procedimento operacional e políticas de compliance passam de 10 páginas com facilidade. Se a média real for **25–30 páginas**, o total de PDFs **dobra ou triplica**. Esta é a alavanca de maior impacto e precisa ser **medida no discovery** (amostragem real do SharePoint), não assumida.

3. **3.000 palavras/planilha** permanece a premissa mais incerta — depende de abas e linhas.

**Leitura que importa:** a base tem ordem de **6 a ~15 milhões de tokens** (após corrigir as premissas acima), entre **~49× e mais de 100× a janela do GPT-4o (128K)**. Não existe a opção de "jogar tudo no contexto" — recuperação seletiva (RAG) é obrigatória, não uma escolha de design. O tamanho corrigido também alimenta a estimativa de custo de embeddings e de reprocessamento (ver Seção 9).

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

> **Tensão de tamanho de chunk a reconciliar.** O cálculo de "242 chunks" assume chunk uniforme de ~500 tokens, mas a Seção 4 manda que **a tabela inteira seja um chunk**. Uma tabela de frete de 15+ colunas com muitas linhas pode:
> - **estourar o limite de entrada do modelo de embedding** (≈8K tokens em `text-embedding-3`), o que exige quebrar por **grupos de linhas com cabeçalho repetido**; e
> - **consumir o orçamento de contexto** muito mais rápido do que a matemática de 500 tokens sugere.
>
> Conclusão: o orçamento de chunks deve ser calculado com **tamanho variável**, não fixo. Recuperar 10–15 chunks pode significar 6K ou 30K tokens dependendo de quantas tabelas vierem. O *budget* operacional tem que ser em **tokens**, não em contagem de chunks.

**Consequência arquitetural:** o gargalo de qualidade é a **precisão do retrieval**, não a janela. Isso justifica investir em reranking (o *semantic ranker* do Azure AI Search já entrega isso nativamente) e em busca híbrida (vetorial + BM25), porque consultas de SLA/frete têm termos exatos — códigos de cliente, zonas — em que a busca puramente vetorial erra.

---

## 4. Estratégia de chunking recomendada

As perguntas reais dos atendentes caem em três famílias, e cada uma pede um tratamento:

- **Lookup tabular** (prazos/SLA por tipo de cliente, regras de frete): a resposta está numa tabela e precisa dela inteira. Cortar a tabela ao meio destrói a resposta.
- **Procedural/narrativo** (devolução, reclamação): a resposta é uma sequência de passos que precisa permanecer coesa num único chunk.
- **Cross-versão** (as contradições): a resposta depende de *qual* versão e de *quem* é a fonte.

### Recomendação

1. **Chunking consciente da estrutura, não por tamanho fixo de caractere.** Quebrar respeitando títulos, seções e limites de tabela. Prosa: ~400–600 tokens com ~10–15% de overlap, para não cortar um procedimento no meio. Tabelas: o chunk é a tabela inteira (ou **grupos de linhas com cabeçalho repetido**, respeitando o limite do embedding), nunca fatiada arbitrariamente.

2. **Metadado rico por chunk** — fonte, título, seção, data de atualização, área dona (Operações/Compliance/Comercial), versão **e classificação de acesso/visibilidade** (ver Seção 6). Isso resolve três requisitos de uma vez: a *citação da fonte* exigida, o tratamento de contradição (priorizar o mais recente / mais autoritativo, ou explicitar o conflito ao atendente em vez de escolher silenciosamente), e o *permission trimming*.

3. **Contra o lost in the middle:** recuperar com *k* pequeno (5–15 chunks reranqueados, não 200) e ordenar os chunks com os mais relevantes no início e no fim do prompt, deixando o meio para os de apoio. O reranker, posicionado após a busca vetorial, é o que mais move o ponteiro de qualidade aqui.

4. **Modelo de embedding — registrar a decisão.** Para conteúdo em **português**, a escolha (`text-embedding-3-large` vs `-small`) importa para qualidade de retrieval; o `large` tende a separar melhor termos próximos (zonas, tipos de cliente) ao custo de mais dimensões/preço. A busca híbrida + semantic ranker amenizam, mas a decisão deve ser explícita e validada contra o conjunto de avaliação (Seção 5), não assumida.

A escolha de ~500 tokens é razoável como base para prosa, mas não como regra única — tabelas de frete podem precisar de chunks maiores justamente para manter a integridade que torna a resposta correta.

---

## 5. Estratégia de avaliação e critérios de aceite

> **Esta era a maior lacuna da avaliação original e é a frente que mais protege a DB1 no go-live.** O documento afirmava, corretamente, que "errado com confiança é pior que não responder" — mas não propunha **nenhum** mecanismo para medir isso. Sem avaliação não há critério de aceite, não se sabe se a meta foi batida, e não se pode afirmar que é seguro colocar em produção.

### 5.1 Conjunto de avaliação ("gold set")

Construir, **no discovery**, um conjunto de **perguntas-ouro reais**, coletadas com os 45 atendentes (as perguntas que de fato chegam: prazos, frete, devolução, reclamação), cada uma com:

- a **resposta correta validada** por quem hoje "sabe a resposta" nas três áreas;
- a **fonte oficial** esperada (documento/seção), para medir citação;
- a **classificação** (lookup tabular / procedural / cross-versão / cálculo de frete).

Cobrir explicitamente os casos difíceis: tabelas de frete, perguntas que dependem de versão/autoridade, e perguntas **sem resposta na base** (para medir abstenção).

### 5.2 Métricas mínimas

| Métrica | O que mede | Por que importa aqui |
|---|---|---|
| **Retrieval recall@k** | O chunk certo está entre os *k* recuperados? | Se o retrieval não traz a fonte, nenhuma geração salva. |
| **Faithfulness / groundedness** | A resposta está fundamentada nos chunks recuperados (sem inventar)? | É o que evita o "errado com confiança". |
| **Acurácia de citação** | A fonte citada é a fonte correta? | Requisito de negócio explícito do projeto. |
| **Acurácia numérica (frete/SLA)** | O número está exato? | Tolerância zero; subconjunto avaliado à parte. |
| **Taxa de abstenção correta** | Diz "não sei / fontes conflitantes" quando deve? | Ver 5.3. |
| **Latência ponta a ponta** | Tempo de resposta | Conecta com a meta 12→2 min. |

### 5.3 Requisito de abstenção (faltava como requisito explícito)

O sistema deve ser **desenhado e avaliado para se abster** — responder *"não encontrei na documentação oficial"* ou *"há fontes conflitantes: versão A (Operações, mar/2026) diz X; versão B (Compliance, jan/2026) diz Y"* — em vez de chutar. Abstenção bem-feita é uma feature de segurança, não uma falha; e precisa entrar no gold set com exemplos próprios.

### 5.4 Critério de aceite e regressão

- Definir **limiares de aceite por métrica** com o Tech Lead e a NovaTech **antes** de desenvolver (ex.: groundedness ≥ X%, acurácia numérica de frete = 100% no gold set), de modo que "pronto" seja objetivo.
- Rodar o gold set como **suíte de regressão** a cada mudança de chunking, modelo, prompt ou reingestão — para que uma "melhoria" não derrube silenciosamente outra métrica.

---

## 6. Segurança de acesso, permissões e privacidade (LGPD)

> Frente **ausente** na avaliação original e que pode transformar o assistente num canal de vazamento se não for desenhada desde o início (não dá para retrofitar).

### 6.1 Permission trimming (security trimming)

Vão ser indexadas políticas de compliance, regras de frete por tipo de cliente e normas de segurança de carga. **Os 45 atendentes têm permissão de ver todos os 800 documentos do SharePoint hoje?** O SharePoint tem ACLs por documento; se o índice as ignora, o assistente recupera e responde a partir de conteúdo que o usuário não deveria ver.

- O **Azure AI Search** suporta filtros de segurança no retrieval — propagar as ACLs do SharePoint para o índice como metadado de visibilidade e **filtrar por identidade do usuário** na consulta.
- Mesmo que a conclusão do discovery seja "todos os atendentes veem tudo", isso precisa ser **verificado e registrado explicitamente**, não assumido.

### 6.2 Privacidade / LGPD

Dados de cliente que aparecem no chamado (e na própria pergunta do atendente) vão **trafegar pelo Azure OpenAI**. Registrar no discovery: **onde** isso é processado (região do recurso Azure OpenAI), **política de retenção** (o Azure OpenAI Service não usa prompts para treinar modelos de base, mas confirmar a configuração de retenção/abuse monitoring contratada), e se há necessidade de **mascaramento de PII** antes do envio. Documentar para o DPO/jurídico da NovaTech.

---

## 7. Riscos transversais (recomenda-se subir ao Tech Lead)

Estes riscos **não são técnicos de RAG** e podem afundar o cronograma ou a adoção se não forem endereçados no discovery.

### 7.1 Contradições entre versões + governança é mudança organizacional
O RAG recuperará alegremente dois chunks que se contradizem. Nenhuma engenharia de prompt resolve dado de origem inconsistente — hoje a equipe resolve "perguntando para quem sabe", e o assistente não tem para quem perguntar.

O ponto a ser explícito com o Tech Lead: fazer **Operações, Compliance e Comercial concordarem** sobre dono por documento, ranking de autoridade e processo de revisão **é política interna da NovaTech, não engenharia que a DB1 controla** — e costuma demorar mais que o build técnico. O metadado de "recência/autoridade" que esta avaliação propõe **pressupõe datas de versão limpas e ownership claro**, exatamente o que o contexto diz que não existe ("sem processo unificado de revisão"). Sem esse acordo no discovery, automatiza-se a entrega de respostas erradas — só que mais rápido. **Este é o item de maior risco de cronograma do projeto, e está fora do controle técnico da DB1.**

### 7.2 Pipeline de atualização
Três áreas atualizam a documentação mensalmente, sem revisão unificada. Sem **reingestão automatizada e versionada** (webhooks ou sync agendado de SharePoint/Confluence), a base se desatualiza em 30 dias e a confiança da equipe despenca.

### 7.3 Adoção e confiança (risco de produto)
A meta de negócio depende de **45 pessoas adotarem** o bot no Teams. Esse risco não vale só para desatualização (7.2) — vale igualmente para a **acurácia inicial**: uma onda de respostas erradas nas primeiras semanas mata a confiança, e aí a métrica de tempo **nunca é atingida**, independentemente da qualidade técnica posterior. Mitigações: piloto com subgrupo, lançamento por família de pergunta (começar pelo que o gold set mostra mais sólido), e abstenção visível (Seção 5.3) para que o erro seja "não sei" e não "número errado".

### 7.4 Tempo de verificação humana no cronômetro
A meta 12→2 min precisa modelar que, dado o risco de alucinação, **o atendente deve conferir a citação** — e esse tempo de verificação entra no relógio. O alvo de "2 minutos" só é realista se a citação for direta o suficiente (link para a seção exata, não para o documento de 40 páginas) para que a conferência seja rápida. Desenhar a citação para verificação rápida é, portanto, um requisito de produto, não um detalhe.

---

## 8. Stack recomendada

Tudo encaixa no que a NovaTech já licencia/provisiona (Microsoft 365 E3 + Azure AI Services):

| Camada | Componente |
|---|---|
| Extração/ingestão | Azure AI Document Intelligence (layout + OCR de tabelas e escaneados) |
| Embeddings | Azure OpenAI `text-embedding-3` (`large` vs `small` a validar p/ PT-BR) |
| Busca/retrieval | Azure AI Search (vetorial + híbrido BM25 + semantic ranker + **security filters**) |
| **Roteamento** | **Camada de roteador/agente que decide RAG (procedural/lookup) vs function calling (frete)** |
| Cálculo determinístico | Function calling sobre a lógica de frete reimplementada (ver 1.3) |
| Modelo de geração | Azure OpenAI — GPT-4o |
| Interface | Bot no Microsoft Teams |
| Avaliação | Suíte de gold set + métricas (Seção 5), em CI |

**Camada de roteamento (não aparecia no desenho original).** Usar RAG para procedural/lookup **e** function calling para frete implica um **roteador** que classifica a pergunta e escolhe o caminho. Isso é complexidade arquitetural real (mais um ponto de falha, mais um ponto a avaliar) e precisa estar no cronograma.

**Concorrência / quota do Azure OpenAI.** ~320 chamados/dia × 60% ≈ **~190 consultas/dia** é baixo no agregado, mas o que importa é o **pico** (vários atendentes ao mesmo tempo): dimensionar **TPM/RPM provisionado** para o horário de pico, não para a média, para não introduzir latência justamente quando a meta de 2 min está sendo medida.

**Observação sobre o modelo:** o GPT-4o atende bem. Mesmo modelos com janela maior mantêm o efeito *lost in the middle* — logo, a estratégia de retrieval seletivo é **independente do tamanho da janela** e permanece válida em futuras trocas de modelo.

---

## 9. Estimativa de custo (OpEx) — a levantar antes da proposta

> A frase "tudo encaixa no que já licenciam" é verdadeira quanto à **disponibilidade** dos serviços, mas **enganosa quanto ao custo**: Azure AI Services é **consumo**, não licença flat. A diretoria vai pedir um OpEx aproximado.

Os direcionadores de custo a estimar (com pricing **atual** do Azure, que muda — puxar antes de cotar; **não** foram cravados valores aqui de propósito):

- **Document Intelligence:** cobrado **por página** — carga inicial (~8.000 páginas, dependendo da premissa de páginas/documento da Seção 2) **mais reprocessamento mensal** das três áreas.
- **Embeddings:** por token, sobre os ~6–15 M tokens da base (Seção 2) na carga inicial + reembedding mensal das partes alteradas.
- **Azure AI Search:** custo do **tier/réplicas/partições** + semantic ranker (mensal fixo, escala com volume e QPS).
- **Azure OpenAI (GPT-4o):** por token de entrada **e** saída, por consulta — sensível ao número de chunks no contexto (mais um motivo para o *k* pequeno da Seção 3).
- **Function calling de frete:** custo de **desenvolvimento e manutenção** (Seção 1.3), que é engenharia, não consumo de API.

Recomenda-se entregar à diretoria um **OpEx mensal aproximado em três cenários** (base / +30% volume / pico), construído com o pricing vigente — e não a afirmação genérica de que "já está contratado".

---

## Conclusão

O caminho técnico é claro e cabe no ecossistema Microsoft/Azure já contratado. A meta de 12→2 minutos é **plausível, porém condicional**: depende menos da camada de LLM (madura e previsível) e mais de quatro frentes que precisam ser tratadas no discovery —

1. **ingestão de qualidade** (tabelas, escaneados, fluxogramas com validação humana, e frete via function calling reescopado como subprojeto);
2. **governança de conteúdo**, que é mudança organizacional da NovaTech e o maior risco de cronograma fora do controle da DB1;
3. **avaliação e abstenção**, sem as quais não há critério de aceite nem segurança de go-live; e
4. **segurança de acesso e privacidade (LGPD)**, sob risco de vazamento.

Recomenda-se reservar parte substancial do discovery para curadoria documental, definição de autoridade/recência por fonte, construção do conjunto de avaliação e verificação de permissões — e entregar à diretoria um OpEx aproximado **antes** de otimizar a camada de LLM. Tratadas essas frentes, o projeto é executável na janela de 3 meses.
