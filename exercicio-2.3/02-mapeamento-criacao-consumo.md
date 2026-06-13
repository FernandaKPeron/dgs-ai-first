# Evidência 02 — Mapeamento de criação e consumo das skills

## Identificação

- Exercício: Desenvolvedor 2.3 — Definição de estratégia de skills do projeto
- Artefato: Tabela de criação, consumo e frequência de uso das skills
- Ferramenta usada: Claude
- Evidência associada: output bruto do Claude registrado em `01-arvore-skills.md`; print/export disponível em `01-arvore-skills.png`.

## Objetivo

Demonstrar que a estratégia de skills tem visão de time: quem cria, quem mantém, quem consome e com qual frequência cada skill será usada.

## Tabela de mapeamento

| Skill | Nível | Frase de ativação | Quem cria/mantém | Quem consome | Agentes consumidores prováveis | Frequência | Dependências | Exemplo de uso |
|---|---|---|---|---|---|---|---|---|
| `typescript-conventions.md` | Foundation | Use quando gerar ou revisar qualquer código TypeScript do NovaTech Assistant. | Tech Lead + Desenvolvedor sênior | Devs, Tech Lead, QA | Copilot, Claude Code | Alta | — | Gerar validator Zod e handler tipado sem `any`. |
| `error-handling.md` | Foundation | Use quando gerar erros, responses, retries ou logging estruturado. | Tech Lead + Desenvolvedor sênior | Devs, QA | Copilot, Claude Code | Alta | `typescript-conventions.md` | Padronizar erro `400`, `422`, retry e logs com pino. |
| `project-structure.md` | Foundation | Use quando criar módulo, pasta, exports ou novos arquivos no repositório. | Tech Lead | Devs, Tech Lead | Copilot, Claude Code | Média | `typescript-conventions.md` | Criar nova function em `src/functions/<name>/`. |
| `azure-functions-endpoint.md` | Domain | Use quando criar ou revisar endpoint HTTP em Azure Functions v4. | Tech Lead + Desenvolvedor | Devs, QA | Copilot, Claude Code | Alta | `typescript-conventions.md`, `error-handling.md`, `project-structure.md` | Criar `POST /api/query` ou `POST /api/feedback`. |
| `azure-ai-search-integration.md` | Domain | Use quando gerar busca, contratos de chunks ou integração/stub do Azure AI Search. | Tech Lead + Desenvolvedor sênior | Devs, Product Specialist, QA | Copilot, Claude Code | Média | `typescript-conventions.md`, `error-handling.md` | Criar service que retorna top-5 chunks com `sourceDocument` e `effectiveDate`. |
| `azure-openai-integration.md` | Domain | Use quando gerar embeddings, chat completion, controle de tokens ou stubs do Azure OpenAI. | Tech Lead + Desenvolvedor sênior | Devs RAG, Devs de pipeline, QA | Copilot, Claude Code | Média | `typescript-conventions.md`, `error-handling.md` | Criar adapter tipado para embeddings sem chamada real a Azure em testes. |
| `rag-pipeline.md` | Domain | Use quando orquestrar recuperação, grounding, geração, citação de fonte e fallback sem resposta. | Tech Lead + Desenvolvedor sênior + Product Specialist | Devs RAG, QA, Product Specialist | Copilot, Claude Code | Alta | `azure-ai-search-integration.md`, `azure-openai-integration.md`, `error-handling.md` | Garantir resposta com fonte real e fallback `NO_RELEVANT_SOURCE` quando não houver chunk confiável. |
| `react-components.md` | Domain | Use quando gerar componentes React do painel web interno. | Tech Lead + Desenvolvedor frontend | Devs, Product Specialist | Copilot | Média | `typescript-conventions.md`, `project-structure.md` | Criar card de resposta com fonte, confiança e feedback. |
| `testing-patterns.md` | Domain | Use quando gerar ou revisar testes Vitest, fixtures e mocks. | QA + Tech Lead | Devs, QA | Copilot, Claude Code | Alta | `typescript-conventions.md`, `error-handling.md`, `project-structure.md` | Criar teste de handler cobrindo payload inválido e resposta estruturada. |
| `documentation-standards.md` | Domain | Use quando gerar ADR, README de módulo, documentação técnica ou convenção de documentação. | Tech Lead + Delivery Manager | Devs, Tech Lead, Product Specialist, Delivery Manager | Claude, Copilot, Claude Code | Média | `project-structure.md` | Documentar um endpoint e registrar decisão arquitetural em `docs/adr/`. |
| `create-rag-endpoint.md` | Artifact | Use quando implementar um endpoint RAG completo de ponta a ponta. | Desenvolvedor sênior + Tech Lead | Devs | Copilot, Claude Code | Alta | `azure-functions-endpoint.md`, `rag-pipeline.md`, `testing-patterns.md` | Implementar endpoint que valida input, busca chunks, monta prompt e retorna resposta com fonte. |
| `create-integration-test.md` | Artifact | Use quando criar teste de integração para endpoint ou fluxo RAG. | QA + Desenvolvedor | Devs, QA | Copilot | Alta | `testing-patterns.md`, `azure-functions-endpoint.md` | Testar `POST /api/query` com fixture de pergunta e chunks esperados. |
| `create-react-card.md` | Artifact | Use quando criar card reutilizável para o painel web. | Desenvolvedor frontend + Product Specialist | Devs, Product Specialist | Copilot | Média | `react-components.md`, `typescript-conventions.md` | Criar card de resposta com `source_document`, status e ação de feedback. |
| `create-technical-doc.md` | Artifact | Use quando gerar documentação técnica de endpoint, README de módulo ou contrato de API. | Tech Lead + Desenvolvedor | Devs, Tech Lead, Delivery Manager | Claude, Copilot, Claude Code | Média | `documentation-standards.md`, `azure-functions-endpoint.md` | Gerar README do módulo `query` com rota, payload, respostas e validação. |
| `write-adr.md` | Artifact | Use quando registrar decisão arquitetural numerada e rastreável. | Tech Lead | Tech Lead, Devs, Delivery Manager | Claude, Copilot | Baixa | `documentation-standards.md` | Registrar decisão de priorizar documento vigente em conflito de versões. |
| `create-sdd-spec.md` | Artifact | Use quando criar ou revisar spec SDD com requirements, plan ou tasks. | Product Specialist + Tech Lead + Desenvolvedor | Product Specialist, Tech Lead, Devs, QA | Claude, Copilot, Claude Code | Média | `documentation-standards.md` | Criar `requirements.md`, `plan.md` ou `tasks.md` para novo módulo. |

## Observações de governança

- Skills Foundation devem ser revisadas pelo Tech Lead antes de virarem base para skills Domain/Artifact.
- Skills de teste devem ter validação do QA, especialmente quando definirem fixtures, assertions e critérios de aceite.
- Skills que impactam linguagem de produto, fontes ou guardrails devem ser revisadas pelo Product Specialist.
- Mudanças em skills consumidas por muitas outras skills devem registrar impacto e motivo no próprio arquivo ou em changelog de prompts/skills.
- Skills planejadas na árvore, mas ainda não materializadas no repositório, podem aparecer no mapeamento porque o exercício pede a estratégia completa. Neste momento, apenas a Foundation principal precisa ser gerada como arquivo aplicado.

## Checklist

- [x] Todas as skills da árvore aparecem na tabela.
- [x] Cada skill tem criador/mantenedor claro.
- [x] Cada skill tem consumidor humano e agente provável.
- [x] A frequência de uso está preenchida.
- [x] QA e Product Specialist aparecem onde fazem sentido.
- [x] A tabela não contém skills sem exemplo real de uso no projeto.
