# Evidência 05 — Revisão de maturidade da skill Foundation

## Identificação

- Exercício: Desenvolvedor 2.3 — Definição de estratégia de skills do projeto
- Artefato: Revisão humana da skill `typescript-conventions.md`
- Ferramenta usada: Copilot para apoio na revisão; decisão final humana
- Arquivo revisado: `skills/foundation/typescript-conventions.md`
- Evidência associada: output bruto da revisão registrado neste arquivo; print/export externo não anexado.

## Prompt utilizado para revisão

```text
Atue como revisor de skills do projeto NovaTech Assistant.

Tarefa:
Avalie o conteúdo de `skills/foundation/typescript-conventions.md` e diga se ele está maduro para uso pelo time.

Critérios de maturidade:
- Tem frase de ativação clara.
- É prescritivo e verificável.
- Contém exemplos DO/DON'T com código real.
- Cobre anti-padrões que o Copilot realmente poderia gerar.
- Conecta TypeScript strict, Zod, pino, Vitest e padrões de resposta com fonte.
- Pode ser usado por outras skills Domain/Artifact sem ambiguidade.

Formato:
1. Veredito: maduro / quase maduro / imaturo.
2. Pontos fortes.
3. Lacunas objetivas.
4. Ajustes recomendados.
5. Checklist final de aceite.
```

## Output bruto da revisão

```markdown
Vou revisar a skill aberta contra os critérios de maturidade e cruzar com as convenções do próprio repositório, sem editar nada. Primeiro vou checar o entorno do projeto e o arquivo completo para não avaliar fora do contexto.

Read [](file:///Users/fernanda.peron/Documents/repositories/dgs-ai-first/skills/foundation/typescript-conventions.md#1-1), lines 1 to 260

Searched for regex `typescript-conventions|Foundation Skill|source_document|pino|Vitest|Zod` (`**/skills/**`), 48 results

O arquivo já mostra uma base bem consistente: ele ativa por escopo de pastas, traz regras verificáveis e amarra RAG com `source_document`. Vou olhar o trecho final e também se as demais skills realmente apontam para esta foundation, porque isso pesa no critério de reuso sem ambiguidade.

Read [](file:///Users/fernanda.peron/Documents/repositories/dgs-ai-first/skills/foundation/typescript-conventions.md#261-261), lines 261 to 415

Searched for regex `typescript-conventions|TypeScript Conventions|foundation/typescript|Use esta skill|dependem|depender|consumir|consumir esta Foundation` (`**/skills/**`), 4 results

Encontrei um ponto importante de governança: a própria skill lista consumidores esperados, mas a busca nas outras skills não mostrou referência explícita a ela. Vou só confirmar os arquivos existentes para separar lacuna real de item futuro planejado.

Searched for files matching `**/skills/**/*.md`, 10 matches

1. **Veredito: quase maduro**

O conteúdo de typescript-conventions.md está muito forte e já é utilizável como referência pelo time. Eu classificaria como **quase maduro**, não por falta de qualidade técnica, mas porque ainda há pequenos ajustes de operacionalização para virar uma foundation skill sem ambiguidade em cadeia com Domain/Artifact.

2. **Pontos Fortes**

- A frase de ativação é clara: a skill diz quando deve ser usada e delimita bem o escopo em functions, services, pipeline, bot, web e shared em typescript-conventions.md.
- É prescritiva e verificável: usa blocos `DEVE` / `NÃO DEVE`, regras de naming, async, imports, validação, logging, RAG e checklist final.
- Os exemplos DO/DON'T são concretos e úteis: mostram `z.infer`, `.strict()`, `safeParse`, union discriminada, `import type`, `logger.warn`, Vitest e anti-exemplos com `any`, `console`, CommonJS e fonte inventada.
- Conecta bem TypeScript strict, Zod, pino, Vitest e resposta grounded com `source_document`.
- Os anti-padrões são realistas para Copilot: handler gigante, `any` para calar erro, mock sem tipo, `source_document` falso, alias inexistente, `fetch` real em teste e erro HTTP 200 com `{ error }`.

3. **Lacunas Objetivas**

- A ativação cobre arquivos em src, mas a própria skill impõe regras para testes e fixtures. Seria melhor incluir explicitamente `tests/**/*.ts`, `tests/**/*.tsx` ou dizer quando ela também se aplica a testes.
- A seção “Skills que devem consumir esta Foundation” lista consumidores, mas a busca nas demais skills não encontrou referência explícita a esta foundation. Isso enfraquece a adoção por Domain/Artifact.
- A lista final inclui arquivos que não existem hoje no workspace, como `skills/domain/azure-openai-integration.md`, `skills/domain/rag-pipeline.md` e `skills/artifact/create-technical-doc.md`. Pode ser roadmap, mas como regra operacional fica ambíguo.
- Falta uma regra curta de precedência: quando uma Domain/Artifact skill contradizer a foundation, qual vence? O ideal é: foundation define baseline; Domain/Artifact pode restringir mais, mas não relaxar TypeScript strict, validação, logging ou grounding.
- O padrão de resposta com fonte está bem coberto no nível RAG, mas poderia declarar um contrato mínimo esperado para respostas factuais: `answer`, `source_document`, `citations` quando aplicável, e variante explícita para ausência de fonte.

4. **Ajustes Recomendados**

- Ajustar a frase de ativação para incluir testes:
	“Use esta skill sempre que criar ou editar arquivos TypeScript/TSX em `src/**` ou testes relacionados em `tests/**`."
- Adicionar uma seção pequena de consumo:
	“Domain e Artifact skills devem declarar dependência desta foundation antes de regras específicas.”
- Atualizar as skills existentes para referenciar esta foundation, especialmente azure-functions-endpoint.md, azure-ai-search-integration.md, react-components.md, testing-patterns.md, create-rag-endpoint.md, create-integration-test.md e create-react-card.md.
- Marcar skills ainda inexistentes como “planejadas” ou remover da lista final até existirem.
- Acrescentar um contrato mínimo de resposta grounded para reduzir variação entre endpoints, bot e web.

5. **Checklist Final De Aceite**

- Frase de ativação cobre `src/**` e testes relacionados.
- Todas as regras críticas são verificáveis por leitura, teste, lint ou revisão.
- Há exemplos DO/DON'T para Zod, imports, async, logging, RAG e Vitest.
- Anti-padrões refletem erros prováveis de geração por IA.
- Não há permissão implícita para `any`, `console`, CommonJS, fonte falsa ou resposta factual sem grounding.
- Domain/Artifact skills existentes referenciam esta foundation.
- A lista de skills consumidoras só contém arquivos existentes ou itens claramente marcados como planejados.
- Precedência entre Foundation, Domain e Artifact está explícita.
- O contrato mínimo de resposta com `source_document` real está declarado.

Minha leitura final: **conteúdo tecnicamente maduro; governança de consumo quase lá**. Com esses ajustes pequenos, eu aprovaria para uso oficial pelo time.
```

## Veredito final

- Veredito: quase maduro
- Decisão: aprovada como referência técnica, com ajustes recomendados antes de uso oficial pelo time

## Pontos fortes

- Frase de ativação clara para código em `src/functions`, `src/services`, `src/pipeline`, `src/bot`, `src/web` e `src/shared`.
- Regras `DEVE`/`NÃO DEVE` prescritivas e verificáveis, cobrindo naming, async, imports, validação, logging, RAG e checklist final.
- Exemplos DO/DON'T concretos com Zod, `z.infer`, `.strict()`, `safeParse`, union discriminada, `import type`, `logger.warn`, Vitest e anti-exemplos com `any`, `console`, CommonJS e fonte inventada.
- Boa conexão entre TypeScript strict, Zod, pino, Vitest e resposta grounded com `source_document`.
- Anti-padrões realistas para Copilot, como handler grande demais, mock sem tipo, alias inexistente, `fetch` real em teste e erro HTTP 200 com `{ error }`.

## Lacunas objetivas

| ID | Lacuna | Impacto | Ajuste recomendado | Status |
|---|---|---|---|---|
| SKILL-01 | A frase de ativação cobre `src/**`, mas a própria skill também define regras para testes e fixtures. | Pode deixar dúvida se a foundation deve ser usada ao gerar testes em `tests/**`. | Ajustar a ativação para incluir arquivos TypeScript/TSX em `src/**` e testes relacionados em `tests/**`. | Pendente |
| SKILL-02 | As demais skills existentes ainda não referenciam explicitamente esta Foundation. | Enfraquece a adoção por Domain/Artifact e pode fazer agentes ignorarem a base TypeScript. | Atualizar skills existentes para declarar dependência de `typescript-conventions.md`. | Pendente |
| SKILL-03 | A lista de consumidores inclui skills planejadas que ainda não existem no workspace. | Como regra operacional, pode parecer que arquivos inexistentes já estão disponíveis. | Marcar consumidores inexistentes como planejados ou remover da lista até serem criados. | Pendente |
| SKILL-04 | Falta regra explícita de precedência entre Foundation, Domain e Artifact. | Pode gerar ambiguidade se uma skill específica parecer relaxar uma regra da Foundation. | Declarar que Domain/Artifact podem restringir mais, mas não relaxar TypeScript strict, Zod, logging, ausência de `any` ou grounding. | Pendente |
| SKILL-05 | O contrato mínimo de resposta grounded poderia ser mais explícito. | Pode haver variação entre endpoints, bot e web no formato de respostas factuais. | Declarar contrato mínimo com `answer`, `source_document`, `citations` quando aplicável e variante explícita para ausência de fonte. | Pendente |

## O que ficou bom e deve ser mantido

- A orientação de entrada externa como `unknown` e validação por Zod.
- O padrão de tipos derivados com `z.infer` e retorno discriminado.
- A proibição explícita de `any`, CommonJS, `console` e `source_document` inventado.
- Os exemplos DO/DON'T para Zod, imports, async, logging, RAG e Vitest.
- A lista de anti-padrões, porque reflete erros prováveis de geração por IA no projeto.
- O checklist final antes de encerrar uma geração de código TypeScript.

## O que ajustaria em uma próxima versão

- Ajustar a frase de ativação para cobrir também testes em `tests/**`.
- Adicionar seção curta dizendo que Domain e Artifact skills devem declarar dependência desta Foundation.
- Atualizar as skills existentes para referenciar `typescript-conventions.md`.
- Marcar skills ainda inexistentes como planejadas na lista de consumidores.
- Adicionar regra de precedência entre Foundation, Domain e Artifact.
- Declarar contrato mínimo de resposta grounded com `answer`, `source_document`, `citations` quando aplicável e fallback explícito sem fonte.

## Checklist final de aceite

- [ ] A frase de ativação cobre `src/**` e testes relacionados.
- [x] A skill é prescritiva e verificável.
- [x] A skill contém exemplos DO/DON'T com código real.
- [x] A skill cobre anti-padrões plausíveis de IA.
- [x] A skill conecta TypeScript strict, Zod, pino, Vitest e fonte (`source_document`).
- [ ] As Domain/Artifact skills existentes referenciam esta Foundation.
- [ ] A lista de skills consumidoras diferencia arquivos existentes de itens planejados.
- [ ] A precedência entre Foundation, Domain e Artifact está explícita.
- [ ] O contrato mínimo de resposta grounded está declarado.
- [x] A revisão aponta evidências concretas, não elogios genéricos.