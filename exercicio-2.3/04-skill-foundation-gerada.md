# Evidência 04 — Skill Foundation gerada e aprovada

## Identificação

- Exercício: Desenvolvedor 2.3 — Definição de estratégia de skills do projeto
- Artefato: Conteúdo final aprovado da skill Foundation principal
- Ferramenta usada: GitHub Copilot + revisão humana
- Arquivo aplicado no projeto: `skills/foundation/typescript-conventions.md`
- Evidência associada: output bruto do Copilot registrado em `03-prompt-copilot-skill-foundation.md`; arquivo final aplicado em `skills/foundation/typescript-conventions.md`.

## Critérios usados para aprovar a skill

- A skill tem frase de ativação clara.
- A skill é prescritiva e verificável.
- A skill contém exemplos DO/DON'T com TypeScript real.
- A skill cobre anti-padrões que o Copilot realmente poderia gerar.
- A skill conecta TypeScript strict, Zod, pino, Vitest e resposta com fonte.
- A skill pode ser usada como dependência por skills Domain/Artifact sem ambiguidade.

## Conteúdo aprovado

A versão aprovada da skill está aplicada no projeto em:

- `skills/foundation/typescript-conventions.md`

O conteúdo foi considerado aprovado porque contém as seções exigidas pelo exercício:

| Critério | Evidência no arquivo aplicado |
|---|---|
| Título e frase de ativação | `# Foundation Skill: TypeScript Conventions` e frase inicial indicando uso em `src/functions`, `src/services`, `src/pipeline`, `src/bot`, `src/web` e `src/shared`. |
| Contexto do projeto | Seção `## Contexto do projeto`, conectando NovaTech Assistant, RAG/logística, TypeScript strict, Zod, Vitest e pino. |
| Regras prescritivas | Seção `## Regras prescritivas`, com blocos `DEVE` e `NÃO DEVE`. |
| Tipos, imports, exports, naming e async | Seções `## Convenções de tipos`, `## Convenções de imports e exports`, `## Convenções de naming` e `## Convenções async`. |
| Validação com Zod | Seção `## Validação com Zod`, com exemplo de `queryRequestSchema`, `z.infer`, `safeParse`, `.strict()` e retorno discriminado. |
| Erros e logging | Seção `## Erros e logging`, proibindo `console.log` e orientando pino/logger estruturado. |
| Exemplos DO/DON'T | Exemplos em TypeScript nas seções de imports, async, Zod, logging, RAG/fonte e testes. |
| Anti-padrões | Seção `## Anti-padrões comuns gerados por LLMs neste projeto`. |
| Checklist final | Seção `## Checklist antes de finalizar código TypeScript`. |

## Resumo do conteúdo gerado

A skill define o padrão Foundation de TypeScript para agentes que geram backend, bot, pipeline de ingestão e painel web no NovaTech Assistant. Ela orienta o uso de TypeScript strict, entrada externa como `unknown`, contratos derivados de Zod, unions discriminadas, named exports, `import type`, funções com retorno explícito e testes Vitest. Também reforça regras de domínio para RAG, exigindo `source_document` real em respostas factuais e fallback explícito quando não houver fonte confiável.

Os exemplos `DO` mostram padrões copiáveis para validação Zod, retorno discriminado, logging com logger tipado, construção de contexto com fonte e teste Vitest. Os exemplos `DON'T` representam falhas plausíveis de IA, como `any`, CommonJS, `console.log`, fonte inventada, payload sem schema, teste contra serviço externo real e resposta logística sem grounding.

## Skills que devem depender desta Foundation

- `skills/foundation/error-handling.md`
- `skills/foundation/project-structure.md`
- `skills/domain/azure-functions-endpoint.md`
- `skills/domain/azure-ai-search-integration.md`
- `skills/domain/azure-openai-integration.md` *(planejada na árvore aprovada)*
- `skills/domain/rag-pipeline.md` *(planejada na árvore aprovada)*
- `skills/domain/react-components.md`
- `skills/domain/testing-patterns.md`
- `skills/artifact/create-rag-endpoint.md`
- `skills/artifact/create-integration-test.md`
- `skills/artifact/create-react-card.md`
- `skills/artifact/create-technical-doc.md` *(planejada na árvore aprovada)*
- `skills/artifact/write-adr.md` *(planejada na árvore aprovada)*
- `skills/artifact/create-sdd-spec.md` *(planejada na árvore aprovada)*

## Checklist

- [x] A versão aprovada foi aplicada em `skills/foundation/typescript-conventions.md`.
- [x] O conteúdo aprovado está registrado nesta evidência por referência ao arquivo aplicado e resumo das seções aprovadas.
- [x] A skill contém contexto específico do NovaTech Assistant.
- [x] A skill contém regras DEVE/NÃO DEVE.
- [x] A skill contém exemplos DO/DON'T com código.
- [x] A skill contém anti-padrões úteis.
- [x] A skill contém checklist antes de finalizar geração de código.
