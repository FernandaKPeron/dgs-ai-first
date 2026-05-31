# Exercício 1.3 — POC do Pipeline de RAG (NovaTech)

Prova de conceito funcional de um pipeline de **RAG** (Retrieval-Augmented
Generation) sobre a documentação da NovaTech, usando apenas ferramentas
**gratuitas e open-source**, rodando 100% local.

O pipeline ingere os 5 documentos do Anexo A, gera embeddings, armazena num
vector store (ChromaDB) e responde perguntas com base nos documentos, citando a
fonte. A geração final é feita por um LLM externo (Claude via chat manual ou
modelo local via Ollama) — esta POC entrega o prompt pronto para esse LLM.

---

## Stack

| Camada | Ferramenta | Observação |
|---|---|---|
| Linguagem | Python 3.13 | — |
| Embeddings | `sentence-transformers` | modelo `paraphrase-multilingual-MiniLM-L12-v2` (ver nota abaixo) |
| Vector store | `ChromaDB` (persistente local) | distância `cosine` |
| Busca | vetorial + reforço por palavra-chave (híbrida) | sem serviço externo |
| Geração | Claude (chat manual) ou Ollama | recebe o prompt montado |

### Nota sobre o modelo de embeddings

O enunciado sugere `all-MiniLM-L6-v2`. Esse modelo é treinado em **inglês** e
recuperou mal os documentos em português (**2/6** acertos no gabarito do Anexo
B). Trocamos pelo equivalente **multilíngue** da mesma família
(`paraphrase-multilingual-MiniLM-L12-v2`) — também gratuito e local — que
elevou a recuperação para **5/6**. A troca está documentada em
[config.py](config.py).

---

## Estrutura

| Arquivo | Etapa | Responsabilidade |
|---|---|---|
| [config.py](config.py) | — | caminhos, modelo, metadados de autoridade/recência por documento |
| [ingest.py](ingest.py) | 1. Ingestão | lê os `.md`, faz chunking, gera embeddings e grava no ChromaDB |
| [search.py](search.py) | 2. Busca | embedding da pergunta + busca híbrida + score |
| [prompt.py](prompt.py) | 3. Montagem de prompt | system prompt + chunks + pergunta |
| [test_pipeline.py](test_pipeline.py) | Validação | roda 6 perguntas do Anexo B contra o gabarito |

Os documentos de origem ficam em [`../pratica-1`](../pratica-1) (5 arquivos `.md`).

---

## Como rodar

```bash
cd exercicio-1.3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python ingest.py          # Etapa 1 — cria o vector store em ./chroma_db
python test_pipeline.py   # roda os 6 testes do gabarito

# uso avulso:
python search.py "Qual o SLA do cliente Gold?"
python prompt.py "Qual o SLA do cliente Gold?"   # imprime o prompt p/ o LLM
```

---

## Estratégia de chunking (e justificativa)

**Estratégia escolhida: por SEÇÃO de markdown** (`##` e `###`), um chunk por
seção, com cabeçalho de procedência (documento + versão + seção) embutido no
texto do chunk.

Justificativa:

1. **Os documentos já são estruturados por seções semanticamente coesas**
   ("3.1 Prazo geral", "2.1 Multiplicadores regionais"). Cada seção responde a
   uma pergunta de negócio inteira — mantê-la íntegra preserva o contexto.
2. **Evita quebrar tabelas e regras.** Chunking por tamanho fixo (ex.: 500
   tokens) cortaria tabelas de frete/SLA no meio, gerando o erro mais perigoso
   do projeto: valor numérico errado com aparência de confiança.
3. **Alinha-se ao gabarito do Anexo B**, cujos chunks de referência também são
   por seção (POL-001-A = Seção 3.1, PROC-042v2-B = Seção 2.1, etc.).
4. **Cabeçalho de procedência** resolve o problema de uma seção como "2.1"
   sozinha não dizer a que documento/versão pertence — melhora o embedding e
   permite citar a fonte na resposta.

Resultado: 37 chunks (POL-001: 8, PROC-042 v1: 6, PROC-042-v2: 7, SLA-2024: 6,
FAQ: 10).

### Busca híbrida

A busca puramente vetorial falhou em dois padrões observados nesta base:

- **Tabelas markdown embedam mal**: o chunk `SLA-2024 / 2. Tabela de SLAs` (que
  contém a resposta do tier Gold) ficava como o **pior** ranqueado por cosseno,
  apesar de ser a resposta exata.
- **Descasamento de termos**: a pergunta cita "Sudeste"/"Gold" e o termo só
  existe dentro da tabela.

Para mitigar, a busca reranqueia os candidatos vetoriais combinando similaridade
de cosseno com sobreposição de palavras-chave:

```
score_final = 0.6 * similaridade_vetorial + 0.4 * score_keyword
```

Isso é *hybrid search*, técnica padrão de RAG de produção, e elevou a
recuperação de 3/6 (vetorial pura multilíngue) para **5/6**.

---

## Metadados e governança (anti-alucinação)

Cada chunk carrega metadados de **autoridade e recência** ([config.py](config.py)):
`classificacao` (normativo / contratual / procedimento / **informal**), `versao`,
`confiavel`. O system prompt ([prompt.py](prompt.py)) usa isso para impor:

- responder **somente** com base nos chunks recuperados;
- **citar a fonte** de cada afirmação;
- **abster-se** quando a informação não está no contexto;
- preferir a **versão mais recente** e sinalizar contradição (PROC-042 v1 × v2);
- tratar o **FAQ como fonte informal** não validada.

---

## Resultados dos testes (gabarito: Anexo B)

`top_k = 5`, busca híbrida. "ACERTO" = todos os chunks esperados pelo gabarito
foram recuperados.

| # | Pergunta | Chunks esperados (gabarito) | Recuperou? | Score (vec) do principal | Resultado |
|---|---|---|---|---|---|
| 1 | Qual o prazo de devolução? | POL-001-A (3.1), POL-001-B (3.2) | Sim — 3.1 e 3.2 no top 5 | 0.61 | ✅ ACERTO |
| 2 | Qual o SLA do cliente Gold? | SLA-2024-B (Tabela de SLAs) | Sim — tabela recuperada via híbrido | 0.35 (resgatada por keyword) | ✅ ACERTO |
| 3 | Frete para 600kg para Manaus? | PROC-042v2-A (Fórmula), PROC-042v2-B (2.1) | Parcial — só a Fórmula; **2.1 não recuperada** | 0.43 | ⚠️ DIVERGÊNCIA |
| 4 | Qual o SLA do cliente Platinum? | SLA-2024-A (Classificação) | Sim — chunk "só 3 tiers" recuperado | 0.53 | ✅ ACERTO |
| 5 | Frete para 300kg para Salvador? | Nenhum (frete <500kg não documentado) | Sim — nenhum chunk formal com sim. alta | < 0.40 | ✅ ACERTO |
| 6 | Qual o multiplicador para o Sudeste? | PROC-042v2-B (2.1) | Sim — v2 no topo; v1 logo abaixo | 0.62 | ✅ ACERTO |

**Resumo: 5/6 casos recuperam os chunks esperados.**

### Análise da divergência (caso 3 — "Frete para 600kg para Manaus?")

A tabela de multiplicadores (`PROC-042-v2 / 2.1`) **não é recuperada** porque:

- a pergunta usa **"Manaus"**, mas o documento só fala em **"Norte"** (a região,
  não a cidade) — descasamento de termo que nem o vetorial nem o keyword
  resolvem sem **expansão de sinônimos / mapeamento cidade→região**;
- a pergunta não contém as palavras "multiplicador" nem "região", que são as
  âncoras lexicais da tabela.

É uma limitação **conhecida e esperada** de RAG vetorial+keyword puro, e ilustra
exatamente o risco apontado na avaliação de viabilidade (tabelas e cálculo de
frete precisam de tratamento dedicado, não de RAG textual genérico).

### Armadilhas do Anexo B verificadas

- **Contradição PROC-042 v1 × v2** (casos 3 e 6): o pipeline recupera **ambas as
  versões**. O system prompt instrui o LLM a usar a v2 e sinalizar a divergência
  — a mitigação está na geração, não na recuperação.
- **Tier Platinum inexistente** (caso 4): recupera o chunk que afirma "só há 3
  tiers" → o LLM deve **negar**, não inventar SLA.
- **Pergunta sem cobertura** (caso 5): nenhum chunk formal com similaridade alta
  → o LLM deve **abster-se**.
- **FAQ informal**: aparece em várias buscas; é marcado `<FAQ informal>` e
  `confiavel=False` para o LLM tratar com cautela.

---

## Limitações de POC (não escalam para o cenário real)

Alguns elementos desta POC são simplificações deliberadas que funcionam com 5
documentos, mas **não escalam** para os ~800 PDFs do SharePoint + 400 páginas de
Confluence + planilhas, atualizados mensalmente por 3 áreas diferentes.

### Metadados curados manualmente (`DOC_METADATA`)

O dicionário `DOC_METADATA` em [config.py](config.py) atribui **à mão**
`classificacao`, `confiavel` e `obsoleto_por` para cada documento. Isso
**fortalece os guardrails** (FAQ marcado como informal, contradição PROC-042 v1
× v2 sinalizada), mas classificar centenas de documentos individualmente é
inviável — e ninguém manteria `obsoleto_por` sincronizado quando uma das 3 áreas
publica uma revisão sem avisar.

No cenário real, esses metadados devem ser **derivados automaticamente da
fonte**, não escritos documento a documento:

| Campo | Na POC (manual) | No cenário real (escalável) |
|---|---|---|
| `doc_id`, `titulo` | escrito à mão | extraído do nome/cabeçalho ou do SharePoint |
| `data`, `versao` | escrito à mão | **metadado nativo** do SharePoint/Confluence (já existe) |
| `classificacao` | escrito à mão | herdada da **biblioteca/site** de origem (ex.: site "Compliance" → normativo) |
| `confiavel` | escrito à mão | **regra por fonte**, não por documento (ex.: wiki colaborativa → informal) |
| `obsoleto_por` | escrito à mão | exige **governança humana** ou heurística frágil (data mais recente) |

A virada conceitual: a autoridade deve vir da **fonte/local** do documento, não
de uma curadoria individual. Classifica-se ~10 bibliotecas/sites uma vez, e cada
documento herda os metadados de onde está. O caso `obsoleto_por` permanece
dependente de governança humana — que a avaliação de viabilidade já apontou como
**mudança organizacional, não problema de engenharia**.

### Lista de fontes fixa (`SOURCE_FILES`)

A lista explícita de 5 arquivos em [config.py](config.py) também não escala. No
real, a ingestão varreria as bibliotecas via **SharePoint/Confluence REST API**,
descobrindo os documentos dinamicamente. É uma troca trivial que não altera a
arquitetura.

### O que continua válido no cenário real

Nem tudo é artifício de POC. Independem da curadoria manual e funcionam igual com
800+ documentos: a **estratégia de chunking** por seção, a **busca híbrida**, e a
ideia de **carregar metadados de autoridade/recência no chunk** (muda só a
*origem* dos metadados — de um dict para o sistema de gestão documental).

---

## Próximos passos (produção)

Itens fora do escopo desta POC, mas necessários para go-live:

1. **Resolver o caso da tabela de frete** com expansão de consulta
   (cidade→região, sinônimos) e/ou *function calling* determinístico para
   cálculo de frete (ver avaliação de viabilidade).
2. **Migrar embeddings** para Azure OpenAI (`text-embedding-3-large`) e o vector
   store para **Azure AI Search**, no ecossistema Microsoft já contratado.
3. **Permission trimming** (segurança de acesso por documento) e **LGPD**.
4. **Conjunto de avaliação** maior e automatizado, com métrica de abstenção.
