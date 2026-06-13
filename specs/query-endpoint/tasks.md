# Tasks — Query Endpoint (`POST /api/query`)

> Escopo desta fase: implementar o endpoint de ponta a ponta **sem depender de serviços Azure reais**.
> Toda integração externa (Azure OpenAI embeddings, Azure AI Search, GPT-4o) é exercida via **mocks/stubs** com contratos tipados.
> A subida para Azure real fica para uma fase posterior (não coberta aqui).

## Convenções

- **ID**: `QE-NN`.
- **Estimativa**: `P` (≤ ~0,5 dia) · `M` (~0,5–1,5 dia) · `G` (~2–3 dias).
- **Evidência**: artefato verificável que comprova a conclusão (saída de teste, diff de PR, trecho de log estruturado, etc.).
- **Critérios de aceite**: sempre verificáveis por teste automatizado, `tsc --noEmit` ou inspeção determinística — nada subjetivo.
- Stack alvo: TypeScript strict, Azure Functions v4, Zod, Vitest, pino.

## Grafo de dependências (resumo)

```
QE-01 ──┬─ QE-02 (embedding stub)
        ├─ QE-03 (search stub) ── QE-04 (vigência) ── QE-05 (prompt builder)
        ├─ QE-06 (completion + retry)
        ├─ QE-09 (logging)
        └─ QE-11 (fixtures)

QE-06 ── QE-07 (response builder) ── QE-08 (output validation)

QE-10 (handler/orquestração)  ← QE-02, QE-05, QE-06, QE-07, QE-08, QE-09
QE-12..QE-15 (testes)         ← respectivas implementações + QE-11
QE-16 (guardrails review)     ← QE-10, QE-15
```

---

## QE-01 — Setup do endpoint HTTP + validação de input (sem Azure)

**Descrição:** Implementar o setup inicial do endpoint `POST /api/query` com validação do corpo da requisição via Zod. Se o scaffold local já tiver Azure Functions v4 configurado, registrar o HTTP trigger; caso contrário, manter um handler testável e tipado, sem introduzir configuração incompleta. Sem nenhuma chamada a Azure: o handler apenas valida e retorna um stub determinístico (ex.: `501 Not Implemented` com `echo` da pergunta validada).

**Arquivos prováveis:**
- `src/functions/query/handler.ts`
- `src/functions/query/validator.ts`
- `host.json` / configuração da function (route, methods), somente se já for compatível com o scaffold local

**Critérios de aceite:**
- Rota `POST /api/query` responde (não 404) ao subir o runtime local, quando o runtime/configuração de Azure Functions estiver disponível; caso contrário, o handler deve ser validável por teste automatizado ou chamada direta tipada.
- Payload válido (`{ "question": "..." }`, demais campos opcionais conforme schema) passa pela validação.
- Payload inválido (sem `question`, tipos errados, string vazia) retorna `400` com corpo de erro estruturado e estável.
- `tsc --noEmit` passa em strict mode; `validator.ts` exporta o schema e o tipo inferido.

**Dependências:** —

**Estimativa:** P

**Evidência esperada:** diff do PR + saída de `tsc --noEmit`/`npm run build` limpa + teste unitário ou chamada direta do handler mostrando `400` para input inválido e `501` (stub) para input válido. Se o runtime local de Azure Functions estiver configurado, incluir também chamada `curl`/REST client.

---

## QE-02 — Service de embedding (stub do Azure OpenAI)

**Descrição:** Criar a interface tipada do service que converte a pergunta em embedding, com implementação **stub** determinística (ex.: vetor fixo derivado do texto) e ponto de injeção para a implementação Azure futura.

**Arquivos prováveis:**
- `src/services/embedding.ts` (novo)
- `tests/fixtures/embeddings/` (vetores de exemplo)

**Critérios de aceite:**
- Interface `EmbeddingService` definida; assinatura `embed(text: string): Promise<number[]>`.
- Stub retorna vetor de dimensão fixa e é determinístico para a mesma entrada.
- Nenhuma dependência de SDK/credencial Azure é carregada no caminho de stub.

**Dependências:** QE-01

**Estimativa:** M

**Evidência esperada:** diff + teste unitário do stub mostrando determinismo (mesma entrada → mesmo vetor).

---

## QE-03 — Service de busca top-5 (stub do Azure AI Search)

**Descrição:** Implementar o contrato do service de busca que recebe um embedding e retorna os top-5 chunks, com **stub** lendo de fixtures. Cada chunk inclui metadados internos em camelCase (`sourceDocument`, `effectiveDate`, `score`), com conversão posterior para o contrato externo da API quando necessário.

**Arquivos prováveis:**
- `src/services/search.ts`
- `tests/fixtures/search/top5.json`

**Critérios de aceite:**
- `search(embedding: number[], k=5): Promise<Chunk[]>` retorna no máximo `k` chunks.
- Tipo `Chunk` inclui `content`, `sourceDocument`, `effectiveDate` e `score`.
- Stub é determinístico a partir das fixtures; ordenação por `score` desc.

**Dependências:** QE-01

**Estimativa:** M

**Evidência esperada:** diff + teste unitário validando shape, limite de 5 e ordenação.

---

## QE-04 — Resolução de documentos contraditórios por vigência (ADR-0003)

**Descrição:** Implementar a regra determinística que, diante de chunks contraditórios sobre o mesmo assunto/`sourceDocument`, prioriza a versão de vigência mais recente, descartando ou rebaixando as anteriores antes da montagem do prompt.

**Arquivos prováveis:**
- `src/services/search.ts` (pós-processamento) **ou** `src/services/prompt-builder.ts`
- `tests/fixtures/search/conflicting.json`

**Critérios de aceite:**
- Dados dois chunks do mesmo `sourceDocument` com datas distintas, apenas o de vigência mais recente é mantido.
- Empate de data resolvido por critério determinístico documentado (ex.: maior `score`).
- Função pura e testável isoladamente (sem I/O).

**Dependências:** QE-03

**Estimativa:** M

**Evidência esperada:** teste unitário com fixture de chunks contraditórios provando que a versão antiga é removida/rebaixada.

---

## QE-05 — Prompt builder com context budget (ADR-0002)

**Descrição:** Montar o prompt final (system prompt versionado + chunks priorizados + pergunta + histórico limitado) respeitando o orçamento de tokens: ~4K system, ~8K chunks, mais pergunta e histórico limitado. Truncar/descartar chunks de menor relevância quando o budget estourar, de forma determinística.

**Arquivos prováveis:**
- `src/services/prompt-builder.ts`
- `prompts/system-prompt.md` (leitura)

**Critérios de aceite:**
- Lê o system prompt de `prompts/system-prompt.md` (versionado).
- Estimativa de tokens centralizada em uma função; quando o total excede o budget, chunks de menor `score` são removidos primeiro até caber.
- O system prompt **nunca** é truncado; a pergunta do atendente **nunca** é truncada.
- Saída inclui rastreabilidade dos `sourceDocument` que entraram no contexto.
- Função pura: mesma entrada → mesmo prompt.

**Dependências:** QE-04 (chunks já resolvidos por vigência)

**Estimativa:** G

**Evidência esperada:** teste unitário com caso dentro do budget e caso acima do budget, comprovando truncamento determinístico e preservação de system prompt/pergunta.

---

## QE-06 — Completion service GPT-4o com retry + exponential backoff (stub)

**Descrição:** Implementar o contrato do service de completion com política de retry e backoff exponencial sobre erros transitórios. Implementação **stub** (sem Azure) que simula sucessos e falhas transitórias configuráveis para testar a política.

**Arquivos prováveis:**
- `src/services/completion.ts`
- `src/services/retry.ts` (helper de backoff, novo)

**Critérios de aceite:**
- `complete(prompt): Promise<CompletionResult>` com retry configurável (nº máximo, base de backoff, jitter opcional).
- Erros transitórios (429/5xx simulados) disparam retry; erros não transitórios (4xx de validação) falham imediatamente.
- Backoff é injetável (clock/sleep mockável) para tornar os testes rápidos e determinísticos.
- Esgotados os retries, lança erro tipado.

**Dependências:** QE-01

**Estimativa:** M

**Evidência esperada:** teste unitário contando tentativas em cenário transitório (ex.: falha 2x, sucesso na 3ª) e cenário não transitório (1 tentativa).

---

## QE-07 — Response builder com `source_document`

**Descrição:** Montar a resposta final da API a partir da completion, incluindo o campo externo `source_document` (rastreabilidade dos chunks usados) e demais campos do contrato de saída. A função deve converter metadados internos em camelCase (`sourceDocument`) para o contrato JSON esperado pela API.

**Arquivos prováveis:**
- `src/functions/query/response-builder.ts`

**Critérios de aceite:**
- Saída contém `answer` e `source_document`/`source_documents` derivados dos chunks efetivamente usados no prompt (recebidos de QE-05).
- Sem chunks utilizáveis, retorna estado explícito (ex.: resposta de "sem base documental") em vez de inventar fonte.
- Função pura sobre `(completion, usedChunks)`.

**Dependências:** QE-06

**Estimativa:** M

**Evidência esperada:** teste unitário comprovando que `source_document` reflete exatamente os chunks usados e o caso "sem fonte".

---

## QE-08 — Validação de output com Zod (`response-validator`)

**Descrição:** Definir o schema Zod da resposta e validar o objeto produzido pelo response builder antes de devolver ao cliente, falhando de forma controlada se o contrato for violado.

**Arquivos prováveis:**
- `src/services/response-validator.ts`

**Critérios de aceite:**
- Schema cobre `answer` (string não vazia) e `source_document` (formato definido).
- Resposta fora do contrato é rejeitada e logada como erro (não enviada ao cliente como `200`).
- Tipo de saída inferido do schema e reutilizado pelo handler.

**Dependências:** QE-07

**Estimativa:** M

**Evidência esperada:** teste unitário com objeto válido (passa) e objeto malformado (rejeitado).

---

## QE-09 — Structured logging com pino

**Descrição:** Configurar logger pino com campos estruturados padrão (correlation/request id, etapa, latência por etapa, contagem de retries) e integrar nos pontos-chave sem vazar PII/segredos.

**Arquivos prováveis:**
- `src/shared/logger.ts`
- pontos de instrumentação nos services existentes

**Critérios de aceite:**
- Logs em JSON com `requestId`, `step` e `durationMs` por etapa.
- Nível configurável por env var; default sensato.
- Nenhum segredo (chaves Azure) nem conteúdo sensível do atendente é logado em claro.

**Dependências:** QE-01

**Estimativa:** P

**Evidência esperada:** trecho de log estruturado de uma requisição local mostrando os campos e a ausência de segredos.

---

## QE-10 — Orquestração no handler (wire-up E2E com stubs)

**Descrição:** Conectar todas as etapas no `handler.ts`: validação de input → embedding → search → vigência → prompt builder → completion → response builder → validação de output, usando os stubs/mocks. Tratamento de erros e mapeamento para status HTTP corretos.

**Arquivos prováveis:**
- `src/functions/query/handler.ts`
- injeção de dependências dos services

**Critérios de aceite:**
- Fluxo feliz com stubs retorna `200` e payload válido por QE-08.
- Erros de validação de input → `400`; falha definitiva de dependência → `502/503`; erro inesperado → `500`.
- Services são injetados (não instanciados rígidos), permitindo substituição por mocks nos testes.

**Dependências:** QE-02, QE-05, QE-06, QE-07, QE-08, QE-09

**Estimativa:** M

**Evidência esperada:** diff + execução local do fluxo completo com stubs (request → `200` com `source_document`).

---

## QE-11 — Fixtures de teste

**Descrição:** Centralizar fixtures determinísticas para perguntas, embeddings, chunks (incluindo contraditórios), prompts esperados e respostas, reutilizáveis pelos testes.

**Arquivos prováveis:**
- `tests/fixtures/` (subpastas `queries/`, `embeddings/`, `search/`, `prompts/`, `responses/`)

**Critérios de aceite:**
- Fixtures versionadas e tipadas/validadas pelos schemas Zod correspondentes.
- Cobrem ao menos: pergunta simples, chunks contraditórios, e cenário acima do context budget.

**Dependências:** QE-01

**Estimativa:** P

**Evidência esperada:** diff das fixtures + teste rápido garantindo que cada fixture casa com seu schema.

---

## QE-12 — Testes unitários: validação de input

**Descrição:** Cobrir o `validator.ts` com casos válidos e inválidos (campos faltando, tipos errados, limites de tamanho).

**Arquivos prováveis:**
- `tests/unit/validator.test.ts`

**Critérios de aceite:**
- Casos válidos passam; cada classe de invalidez é rejeitada com mensagem estável.
- Cobertura das ramificações do schema de input.

**Dependências:** QE-01, QE-11

**Estimativa:** P

**Evidência esperada:** saída do Vitest com testes verdes e relatório de cobertura do `validator.ts`.

---

## QE-13 — Testes unitários: prompt builder / context budget

**Descrição:** Validar a montagem do prompt e o respeito ao orçamento de tokens, incluindo truncamento determinístico e preservação de system prompt/pergunta.

**Arquivos prováveis:**
- `tests/unit/prompt-builder.test.ts`

**Critérios de aceite:**
- Caso dentro do budget mantém todos os chunks; caso acima remove os de menor `score` até caber.
- System prompt e pergunta nunca são truncados (assert explícito).
- `sourceDocument`s no contexto correspondem aos chunks que sobreviveram ao corte.

**Dependências:** QE-05, QE-11

**Estimativa:** M

**Evidência esperada:** saída do Vitest com cenários dentro/acima do budget verdes.

---

## QE-14 — Testes unitários: retry / exponential backoff

**Descrição:** Cobrir a política de retry do completion service: contagem de tentativas, distinção transitório vs não transitório, e esgotamento de retries — com clock/sleep mockados.

**Arquivos prováveis:**
- `tests/unit/retry.test.ts` / `tests/unit/completion.test.ts`

**Critérios de aceite:**
- Falha transitória repetida e sucesso posterior → nº de tentativas esperado.
- Erro não transitório → 1 tentativa, sem retry.
- Retries esgotados → erro tipado; testes rodam sem espera real (sleep mockado).

**Dependências:** QE-06, QE-11

**Estimativa:** M

**Evidência esperada:** saída do Vitest verde com asserts na contagem de tentativas e backoff mockado.

---

## QE-15 — Testes de integração (handler com mocks/stubs)

**Descrição:** Exercitar o fluxo completo do handler com dependências injetadas por mocks/stubs, cobrindo fluxo feliz e os principais caminhos de erro.

**Arquivos prováveis:**
- `tests/integration/query-endpoint.test.ts`

**Critérios de aceite:**
- Fluxo feliz → `200` com payload validado por QE-08 e `source_document` presente.
- Input inválido → `400`; falha definitiva de dependência → `5xx` mapeado.
- Cenário de chunks contraditórios → resposta cita a versão mais recente.
- Nenhuma chamada de rede real (asserção de que stubs foram usados).

**Dependências:** QE-10, QE-11

**Estimativa:** G

**Evidência esperada:** saída do Vitest de integração verde + asserção de zero chamadas externas reais.

---

## QE-16 — Revisão determinística de guardrails

**Descrição:** Implementar uma checagem determinística (testável, não baseada em julgamento de LLM) das invariantes de segurança/contrato: orçamento de tokens respeitado, system prompt íntegro, ausência de segredos em logs, priorização de vigência aplicada, e `source_document` sempre coerente com os chunks usados.

**Arquivos prováveis:**
- `tests/unit/guardrails.test.ts`
- `src/services/guardrails.ts` (asserções/checagens reutilizáveis, opcional)

**Critérios de aceite:**
- Asserção: prompt final nunca excede o budget configurado.
- Asserção: hash/conteúdo do system prompt enviado == versão de `prompts/system-prompt.md`.
- Asserção: logs de uma requisição não contêm padrões de segredo/credencial.
- Asserção: toda resposta com `answer` não vazia possui `source_document` rastreável; sem fonte → estado explícito.
- Asserção: dado conjunto contraditório, a versão antiga não aparece no contexto.
- Todas as checagens são determinísticas e parte do CI.

**Dependências:** QE-10, QE-15

**Estimativa:** M

**Evidência esperada:** suíte de guardrails verde no CI cobrindo cada invariante acima, com pelo menos um teste negativo (viola a invariante → falha esperada).

---

### Notas de execução

- QE-02, QE-03, QE-06, QE-09 e QE-11 podem ser paralelizadas após QE-01.
- Nenhuma task desta fase deve abrir conexão real com Azure; qualquer caminho que exija credencial fica atrás de injeção de dependência e é coberto por stub.
- A fase de integração com Azure real (credenciais, índice populado, GPT-4o) deve virar um `tasks.md` próprio quando as dependências de infra (pipeline de ingestão, system prompt finalizado) estiverem prontas.
