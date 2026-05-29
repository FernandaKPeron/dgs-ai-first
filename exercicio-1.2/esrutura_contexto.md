## Contexto estático (vai igual em toda query)

| Seção | Tipo | Palavras | Tokens (~PT) |
|---|---|---|---|
| IDENTIDADE | Estático | 98 | ~145–170 |
| REGRAS INVIOLÁVEIS (7 guardrails) | Estático | 294 | ~430–510 |
| POLÍTICA DE CONFLITO | Estático | 196 | ~285–340 |
| COMO USAR OS TRECHOS | Estático | 101 | ~150–175 |
| FORMATO DE RESPOSTA | Estático | 89 | ~130–155 |
| EXEMPLOS DE COMPORTAMENTO | Estático | 184 | ~270–320 |
| LEMBRETE CRÍTICO | Estático | 42 | ~60–75 |
| **Subtotal estático** | | **1.004** | **~1.470–1.740** |

## Contexto dinâmico (muda a cada query)

| Bloco | Tipo | Referência no prompt | Tokens típicos |
|---|---|---|---|
| Dados do chamado/cliente (tier, região, peso) | Dinâmico | regras de SLA/frete | ~100–300 |
| Trechos recuperados (chunks RAG + metadados) | Dinâmico | "TRECHOS DE DOCUMENTAÇÃO" / "COMO USAR OS TRECHOS" | ~6.000–30.000 |
| Resultado de ferramenta (cálculo de frete) | Dinâmico | "RESULTADOS DE FERRAMENTA" | ~100–400 |
| Histórico da conversa (multi-turn) | Dinâmico | implícito | ~1.000–3.000 |
| Pergunta atual do atendente | Dinâmico | a query em si | ~50–200 |
| **Subtotal dinâmico** | | | **~7.250–33.900** |
