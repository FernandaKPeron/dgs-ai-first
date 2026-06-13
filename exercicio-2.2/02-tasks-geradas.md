# Evidência 02 — `tasks.md` gerado pelo Claude

## Identificação

- Exercício: Desenvolvedor 2.2 — Implementação de spec com Spec Driven Development
- Artefato: Output do Claude para `specs/query-endpoint/tasks.md`
- Ferramenta usada: Claude Chat
- Arquivo final aplicado no projeto: `specs/query-endpoint/tasks.md`

## Output bruto do Claude

O output bruto do Claude foi recebido como arquivo Markdown (`tasks.md`) e está evidenciado no print associado (`02-tasks-geradas.png`). O conteúdo original continha 16 tasks (`QE-01` a `QE-16`) para o query endpoint, com grafo de dependências, critérios de aceite, dependências, estimativas P/M/G e evidência esperada por task.

Resumo do conteúdo bruto recebido:

```markdown
# Tasks — Query Endpoint (`POST /api/query`)

Escopo: implementar o endpoint de ponta a ponta sem depender de serviços Azure reais; integrações externas exercidas via mocks/stubs com contratos tipados.

Tasks geradas:
- QE-01 — Setup do endpoint HTTP + validação de input (sem Azure)
- QE-02 — Service de embedding (stub do Azure OpenAI)
- QE-03 — Service de busca top-5 (stub do Azure AI Search)
- QE-04 — Resolução de documentos contraditórios por vigência (ADR-0003)
- QE-05 — Prompt builder com context budget (ADR-0002)
- QE-06 — Completion service GPT-4o com retry + exponential backoff (stub)
- QE-07 — Response builder com `source_document`
- QE-08 — Validação de output com Zod (`response-validator`)
- QE-09 — Structured logging com pino
- QE-10 — Orquestração no handler (wire-up E2E com stubs)
- QE-11 — Fixtures de teste
- QE-12 — Testes unitários: validação de input
- QE-13 — Testes unitários: prompt builder / context budget
- QE-14 — Testes unitários: retry / exponential backoff
- QE-15 — Testes de integração (handler com mocks/stubs)
- QE-16 — Revisão determinística de guardrails

Convenções presentes no output bruto:
- IDs no formato `QE-NN`.
- Estimativas `P`, `M` ou `G` em todas as tasks.
- Critérios de aceite verificáveis por teste automatizado, `tsc --noEmit` ou inspeção determinística.
- Dependências explícitas por task e grafo de dependências.
- Nenhuma task depende de serviço Azure real nesta fase.
```

## Conteúdo aprovado para aplicar em `specs/query-endpoint/tasks.md`

A versão aprovada foi aplicada integralmente em `specs/query-endpoint/tasks.md`. Ela preserva a estrutura do output bruto do Claude e incorpora os ajustes da revisão humana abaixo.

Diferenças aplicadas na versão revisada:

```markdown
1. QE-01:
	- Mantida como primeira task.
	- Ajustada para permitir handler testável quando o runtime/configuração local de Azure Functions não estiver disponível.
	- Evidência esperada aceita `npm run build`/teste unitário/chamada direta do handler, com `curl` apenas quando o runtime local estiver configurado.

2. QE-03:
	- Metadados internos padronizados para camelCase: `sourceDocument`, `effectiveDate`, `score`.
	- Conversão para o contrato externo da API fica no boundary de resposta.

3. QE-05:
	- Rastreabilidade do contexto usa `sourceDocument` nos tipos internos.

4. QE-07:
	- Response builder explicita conversão de `sourceDocument` interno para `source_document` no JSON externo.

5. QE-09:
	- Caminho do logger ajustado de `src/services/logger.ts` para `src/shared/logger.ts`, alinhado à estrutura real do projeto.

6. QE-13:
	- Critério de aceite usa `sourceDocument`s internos para chunks que sobreviveram ao corte de budget.
```

Arquivo revisado aplicado: `specs/query-endpoint/tasks.md`.

## Revisão humana das tasks

| Critério | Resultado | Observações |
|---|---|---|
| As tasks são atômicas? | Sim, com pequenos ajustes recomendados | As tasks separam validação, embedding, search, vigência, prompt builder, completion, response builder, validação de output, logging, orquestração e testes. `QE-01` é aceitável como primeira task, mas pode ficar mais segura se a evidência não depender obrigatoriamente do runtime local da Azure Functions. |
| Cada task tem critérios de aceite verificáveis? | Sim | Os aceites usam `tsc --noEmit`, Vitest, testes unitários/integrados, checks determinísticos, status HTTP e diff/log verificável. Não há critérios vagos como “funcionar corretamente”. |
| As dependências entre tasks estão claras? | Sim | Há grafo de dependências e cada task lista dependências explícitas. As dependências transitivas de `QE-10` ficam claras pelo grafo; `QE-05` já encapsula `QE-03`/`QE-04`. |
| A primeira task é pequena e implementável sem Azure real? | Sim, com ressalva | `QE-01` não chama Azure e foca validação/stub. Recomenda-se permitir handler testável sem runtime local caso o projeto ainda não tenha dependências completas de Azure Functions. |
| Há tasks de teste e validação determinística de guardrails? | Sim | `QE-12` a `QE-15` cobrem testes unitários e integração; `QE-16` cobre guardrails determinísticos como budget, fonte, vigência e ausência de segredos em logs. |

## Ajustes recomendados antes de aplicar

1. Em `QE-09`, trocar `src/services/logger.ts` por `src/shared/logger.ts`, que é o caminho previsto na estrutura atual do projeto.
2. Em `QE-01`, ajustar a evidência esperada para aceitar `npm run build`/teste unitário do handler quando o runtime local de Azure Functions não estiver configurado. O `curl` local é desejável, mas não deve bloquear esta primeira task no starter repo.
3. Padronizar a nomenclatura de metadados entre contrato externo e tipos internos: usar `source_document` no JSON de API quando exigido pelo produto, mas preferir `sourceDocument`/`effectiveDate` nos tipos TypeScript internos, com conversão explícita no boundary.
4. Em `QE-01`, se `host.json` não existir ou Azure Functions v4 não estiver instalado, não criar configuração incompleta só para cumprir a task; implementar handler testável e registrar a limitação como parte da evidência.

## Primeira task selecionada para implementação

- ID: `QE-01`
- Título: Setup do endpoint HTTP + validação de input (sem Azure)
- Arquivos esperados: `src/functions/query/handler.ts`, `src/functions/query/validator.ts` e, somente se necessário/compatível com o scaffold, `host.json` ou configuração equivalente da function.
- Critérios de aceite principais: payload válido passa pela validação; payload inválido retorna `400` com erro estruturado; `question` é obrigatória e normalizada; o handler retorna stub determinístico sem chamar Azure; `tsc --noEmit`/`npm run build` passa em strict mode.

## Evidência de aplicação no repo

```text
O conteúdo revisado foi aplicado em specs/query-endpoint/tasks.md.

Validação visual/técnica realizada:
- O arquivo contém as tasks QE-01 a QE-16.
- As tasks mantêm dependências e estimativas P/M/G.
- QE-01 foi revisada para não depender obrigatoriamente do runtime local de Azure Functions.
- QE-09 aponta para src/shared/logger.ts.
- O contrato diferencia metadados internos camelCase de campos externos como source_document.
```

## Checklist de aceite

- [x] O output do Claude foi registrado.
- [x] A versão aprovada do `tasks.md` está neste arquivo.
- [x] O conteúdo foi aplicado em `specs/query-endpoint/tasks.md`.
- [x] Todas as tasks têm ID no formato `QE-NN`.
- [x] Todas as tasks têm aceite verificável.
- [x] A primeira task não chama Azure OpenAI nem Azure AI Search.
