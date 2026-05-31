## Resultados dos testes (gabarito: Anexo B)

`top_k = 5`, busca híbrida.
"ACERTO" = todos os chunks esperados pelo gabarito
foram recuperados.

| # | Pergunta | Chunks esperados (gabarito) | Recuperou? | Score (vec) do principal | Resultado |
|---|---|---|---|---|---|
| 1 | Qual o prazo de devolução? | POL-001-A (3.1), POL-001-B (3.2) | Sim — 3.1 e 3.2 no top 5 | 0.61 | ✅ ACERTO |
| 2 | Qual o SLA do cliente Gold? | SLA-2024-B (Tabela de SLAs) | Sim — tabela recuperada via híbrido | 0.35 (resgatada por keyword) | ✅ ACERTO |
| 3 | Frete para 600kg para Manaus? | PROC-042v2-A (Fórmula), PROC-042v2-B (2.1) | Parcial — só a Fórmula; **2.1 não recuperada** | 0.43 | ⚠️ DIVERGÊNCIA |
| 4 | Qual o SLA do cliente Platinum? | SLA-2024-A (Classificação) | Sim — chunk "só 3 tiers" recuperado | 0.53 | ✅ ACERTO |
| 5 | Frete para 300kg para Salvador? | Nenhum (frete <500kg não documentado) | Sim — nenhum chunk formal com sim. alta | < 0.40 | ✅ ACERTO |
| 6 | Qual o multiplicador para o Sudeste? | PROC-042v2-B (2.1) | Sim — v2 no topo; v1 logo abaixo | 0.62 | ✅ ACERTO |


## Propostas de melhorias

**Problema 1** — Modelo de embeddings em inglês recuperava mal em PT-BR
Sintoma: na primeira versão, com o modelo sugerido all-MiniLM-L6-v2, o gabarito do Anexo B deu apenas 2/6 acertos. Perguntas simples como "Qual o prazo de devolução?" traziam chunks do FAQ e de custos no topo, em vez da Seção 3.1.

Causa: all-MiniLM-L6-v2 é treinado em corpus inglês. Os documentos da NovaTech são em português — acentuação e subwords menos frequentes degradam o embedding, então a similaridade de cosseno fica "achatada" (todos os scores próximos, sem separação clara entre relevante e irrelevante).

Correção: troca pelo equivalente multilíngue da mesma família, paraphrase-multilingual-MiniLM-L12-v2 — também gratuito e local (sem custo, sem API). Resultado subiu para 3/6 e, principalmente, o chunk primário correto passou a aparecer no topo na maioria dos casos. Documentado em config.py.

**Problema 2** — Tabelas markdown "embedam mal" e afundam no ranking
Sintoma: mesmo com o modelo multilíngue, "Qual o SLA do cliente Gold?" não trazia a tabela com os valores do Gold. O chunk SLA-2024 / 2. Tabela de SLAs — que é a resposta exata — era o pior ranqueado por similaridade vetorial (vec=0.361), abaixo de chunks tematicamente próximos mas sem a resposta (penalidades, medição).

Causa: uma tabela markdown vira uma "sopa" de cabeçalhos e números (| Gold | Até 2h | Até 24h |). Esse texto fragmentado produz um vetor pouco parecido com uma pergunta em linguagem natural. É um modo de falha conhecido de RAG sobre tabelas.

Correção: busca híbrida (search.py) — reranqueia os candidatos vetoriais somando um score de palavra-chave:

score = 0.6 ⋅ similaridade vetorial + 0.4 ⋅ score keyword

Como a palavra "Gold" aparece literalmente na tabela, o componente de keyword a resgata. Subiu de 3/6 → 5/6.

