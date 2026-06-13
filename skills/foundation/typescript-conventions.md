# Foundation Skill: TypeScript Conventions

Use esta skill sempre que for criar ou editar qualquer arquivo TypeScript ou TSX do NovaTech Assistant em `src/functions`, `src/services`, `src/pipeline`, `src/bot`, `src/web` ou `src/shared`.

Esta skill define o padrão base de TypeScript strict para agentes que geram backend, bot, pipeline de ingestão e painel web. Skills de domínio e de artefato devem depender dela antes de aplicar regras mais específicas.

## Contexto do projeto

O NovaTech Assistant é um assistente RAG para atendimento logístico. O código roda em módulos ES, usa TypeScript strict, Zod para contratos de entrada e saída, Vitest para testes e pino para logging estruturado.

A estrutura principal de código é:

- `src/functions`: endpoints HTTP em Azure Functions, com validação na borda.
- `src/services`: lógica de busca, completion, prompt e validação determinística de resposta.
- `src/pipeline`: ingestão, chunking, embeddings e indexação de documentos.
- `src/bot`: bot do Teams e Adaptive Cards.
- `src/web`: painel React.
- `src/shared`: tipos, configuração, logger e erros compartilhados.

Regra de domínio crítica: respostas do assistente só podem afirmar fatos logísticos quando houver fonte recuperada. Todo resultado RAG deve carregar `source_document` e não deve inventar prazo, política, regra de frete, canal de atendimento ou exceção operacional.

## Regras prescritivas

### DEVE

- DEVE tratar entrada externa como `unknown` até ser validada por Zod.
- DEVE derivar tipos de contratos Zod com `z.infer<typeof schema>` quando o schema for a fonte de verdade.
- DEVE usar unions discriminadas para resultados de validação, busca, geração, pipeline e chamadas externas.
- DEVE tipar retornos públicos de funções exportadas, principalmente handlers, serviços e builders.
- DEVE usar imports e exports ES, nunca CommonJS.
- DEVE preferir named exports para funções, schemas, tipos e constantes compartilhadas.
- DEVE usar `import type` para importar apenas tipos.
- DEVE manter dados de domínio com nomes explícitos, como `source_document`, `documentId`, `chunkId`, `score`, `answer` e `citations`.
- DEVE manter funções pequenas e orientadas a uma ação observável, como `validateQueryInput`, `buildGroundedPrompt` ou `mapSearchHitToChunk`.
- DEVE usar `async` apenas quando houver `await` ou quando a assinatura exigida pelo runtime precisar retornar `Promise`.
- DEVE escrever testes com Vitest para regras de validação, transformação e fallback.

### NÃO DEVE

- NÃO DEVE usar `any` em código de produção, testes, fixtures ou exemplos de referência.
- NÃO DEVE silenciar erros com `catch {}` sem mapear uma resposta, erro tipado ou log estruturado.
- NÃO DEVE usar `console.log`, `console.error`, `console.warn` ou `console.debug`; use o logger compartilhado baseado em pino.
- NÃO DEVE criar objetos de resposta RAG sem `source_document` quando houver resposta factual.
- NÃO DEVE preencher `source_document` com valor inventado como `unknown`, `internal`, `generated` ou `NovaTech FAQ` sem origem real.
- NÃO DEVE aceitar propriedades extras em payloads de API; use `.strict()` nos schemas Zod de request.
- NÃO DEVE misturar parsing, regra de negócio, logging e transporte HTTP na mesma função quando houver separação clara por módulo.
- NÃO DEVE usar default export em módulos compartilhados do projeto.
- NÃO DEVE criar constantes mágicas dentro de funções quando o valor representa limite, código de erro, rota ou configuração.
- NÃO DEVE gerar classes para modelos simples quando `type`, `interface` e schemas Zod resolvem o contrato.

## Convenções de tipos

- Use `type` para unions, aliases derivados de Zod e modelos fechados de payload.
- Use `interface` quando o contrato representar uma superfície extensível, como request mínimo de handler, client externo ou logger.
- Use `readonly` em arrays e propriedades que não devem ser alteradas após a criação.
- Use literais e `as const` para códigos HTTP, códigos de erro e headers estáveis.
- Modele ausência explicitamente com `undefined` ou uma variante da union, não com string sentinela.
- Prefira `Record<string, string>` apenas quando as chaves forem realmente dinâmicas. Para contratos conhecidos, declare campos explícitos.
- Não use non-null assertion (`!`) para contornar strict null checks. Faça narrowing antes.

Exemplo de retorno discriminado:

```ts
export type RetrievalResult =
	| { success: true; chunks: readonly RetrievedChunk[] }
	| { success: false; code: "SEARCH_UNAVAILABLE" | "NO_RELEVANT_SOURCE"; message: string };

export interface RetrievedChunk {
	readonly chunkId: string;
	readonly source_document: string;
	readonly content: string;
	readonly score: number;
}
```

## Convenções de imports e exports

- Agrupe imports externos antes de imports locais.
- Use `import type` para tipos vindos de outros módulos.
- Use caminhos relativos claros dentro de `src`; não invente aliases se eles não existirem no `tsconfig.json`.
- Exporte schemas e tipos quando forem consumidos por handler, serviço ou teste.
- Não use barrels (`index.ts`) até haver necessidade real de consolidar múltiplos consumidores.
- Não misture default export com named exports no mesmo arquivo.

DO:

```ts
import { z } from "zod";

import type { Logger } from "../../shared/logger";
import { logger } from "../../shared/logger";
```

DON'T:

```ts
const z = require("zod");
const logger = require("../../shared/logger");

module.exports = { z, logger };
```

## Convenções de naming

- Arquivos: use kebab-case para módulos, como `response-builder.ts` e `prompt-builder.ts`.
- Schemas Zod: use camelCase com sufixo `Schema`, como `queryRequestSchema`.
- Tipos derivados: use PascalCase, como `QueryRequest`.
- Funções: use camelCase com verbo, como `validateQueryInput`, `buildResponseCard`, `indexDocumentChunks`.
- Constantes de limite, rota e código fixo: use UPPER_SNAKE_CASE, como `MAX_HISTORY_TURNS`.
- Campos JSON expostos para RAG devem preservar contrato externo. Use `source_document` quando esse for o nome exigido pelo corpus, resposta ou avaliação.
- Evite nomes genéricos como `data`, `result`, `item` e `obj` quando o domínio já tem nome melhor.

## Convenções async

- Handlers HTTP podem ser `async` porque o runtime e leitura de body são assíncronos.
- Builders puros, mappers e validadores devem ser síncronos quando não chamam I/O.
- Use `Promise.all` apenas quando as operações forem independentes e a ordem de efeitos não importar.
- Não execute chamadas externas dentro de `map`, `forEach` ou builders sem controle de concorrência.
- Sempre tipar a promessa retornada por função exportada: `Promise<QueryHandlerResponse>`.
- Em `catch`, receba `error: unknown` e normalize antes de logar ou retornar.

DO:

```ts
export async function queryHandler(request: QueryHttpRequest): Promise<QueryHandlerResponse> {
	const payload = await request.json();
	const validation = validateQueryInput(payload);

	if (!validation.success) {
		return buildValidationErrorResponse(validation.issues);
	}

	return buildQueryResponse(validation.data);
}
```

DON'T:

```ts
export async function buildPrompt(chunks: any) {
	return chunks.map(async (chunk: any) => chunk.text).join("\n");
}
```

Problemas do DON'T: usa `any`, marca builder puro como `async`, cria array de Promises dentro de `join` e usa `text` sem contrato.

## Validação com Zod

- Todo payload vindo de HTTP, bot, arquivo de ingestão, variável de ambiente ou API externa deve passar por schema Zod antes de uso.
- Schemas de request HTTP devem usar `.strict()` para recusar campos extras.
- Mensagens de validação devem ser específicas e acionáveis.
- Use `.trim()` antes de `.min()` para strings de usuário.
- Limites de tamanho devem ficar em constantes exportadas quando forem relevantes para testes.
- Para enums de domínio, prefira `z.enum([...])` em vez de string livre.
- Use `safeParse`, não `parse`, em bordas de sistema. `parse` pode ser usado em setup/testes quando falhar rápido é desejado.
- Mapeie `ZodIssue` para um formato estável de erro antes de responder HTTP.
- Derive o tipo do schema e não duplique a estrutura em `interface` paralela.

DO:

```ts
import { z } from "zod";

export const MAX_QUESTION_LENGTH = 1000;

export const queryRequestSchema = z
	.object({
		question: z
			.string({ required_error: "question é obrigatório." })
			.trim()
			.min(3, "question deve ter pelo menos 3 caracteres.")
			.max(MAX_QUESTION_LENGTH, `question deve ter no máximo ${MAX_QUESTION_LENGTH} caracteres.`),
		conversationId: z.string().trim().min(1).optional(),
	})
	.strict();

export type QueryRequest = z.infer<typeof queryRequestSchema>;

export type ValidationResult =
	| { success: true; data: QueryRequest }
	| { success: false; issues: readonly ValidationIssue[] };

export interface ValidationIssue {
	readonly path: string;
	readonly message: string;
}

export function validateQueryInput(payload: unknown): ValidationResult {
	const parsed = queryRequestSchema.safeParse(payload);

	if (parsed.success) {
		return { success: true, data: parsed.data };
	}

	return {
		success: false,
		issues: parsed.error.issues.map((issue) => ({
			path: issue.path.length > 0 ? issue.path.join(".") : "$",
			message: issue.message,
		})),
	};
}
```

DON'T:

```ts
interface QueryRequest {
	question: string;
	conversationId?: string;
}

export function validateQueryInput(payload: any): QueryRequest {
	if (!payload.question) {
		throw new Error("bad request");
	}

	return payload;
}
```

Problemas do DON'T: usa `any`, não valida tipo real, aceita campos extras, duplica contrato sem schema, lança erro genérico e retorna objeto não normalizado.

## Erros e logging

- Use erros tipados de `src/shared/errors.ts` quando existirem; se ainda não existirem, modele uma union de erro local e mantenha o contrato explícito.
- Erros esperados de validação, ausência de fonte e regra de negócio devem virar resposta controlada, não stack trace.
- Erros inesperados devem ser logados com pino via `logger.error` e retornar mensagem segura.
- Logs devem ser estruturados com objeto no primeiro argumento e mensagem curta no segundo.
- Inclua `correlationId`, `route`, `operation`, `documentId`, `chunkId` ou `source_document` quando ajudarem diagnóstico.
- Não logue pergunta completa, resposta completa, documentos inteiros, tokens, chaves, CPF, telefone, email ou payload sensível.
- Não use `console.log` em produção, testes ou exemplos de skill.
- Não converta `unknown` para string diretamente sem normalizar.

DO:

```ts
import type { Logger } from "../shared/logger";

export type QueryServiceResult =
	| { success: true; answer: GroundedAnswer }
	| { success: false; code: "NO_RELEVANT_SOURCE" | "COMPLETION_FAILED"; message: string };

export interface GroundedAnswer {
	readonly answer: string;
	readonly source_document: string;
}

export function logQueryFailure(logger: Logger, correlationId: string, result: QueryServiceResult): void {
	if (result.success) {
		return;
	}

	logger.warn(
		{ correlationId, code: result.code, operation: "query" },
		"Query flow finished without grounded answer.",
	);
}
```

DON'T:

```ts
try {
	const answer = await openai.chat(question);
	console.log("answer", answer);
	return { answer, source_document: "NovaTech FAQ" };
} catch (error: any) {
	console.error(error);
	return { answer: "Tente novamente mais tarde", source_document: "generated" };
}
```

Problemas do DON'T: usa `any`, loga conteúdo potencialmente sensível, inventa fonte, usa `console`, esconde falha externa e retorna resposta factual sem grounding.

## Regras para RAG e fontes

- Toda resposta factual deve ser construída a partir de chunks recuperados.
- A resposta final deve carregar `source_document` de um chunk real usado no prompt.
- Quando não houver chunk confiável, retorne uma variante explícita como `NO_RELEVANT_SOURCE`.
- Não preencha lacunas com conhecimento geral do modelo.
- Não derive prazo, SLA, política de devolução ou regra de frete de nomes de arquivo, memória da conversa ou suposição.
- O prompt builder deve receber chunks já validados e manter a referência da fonte junto ao trecho.

DO:

```ts
export interface GroundingChunk {
	readonly content: string;
	readonly source_document: string;
	readonly score: number;
}

export type GroundingResult =
	| { success: true; promptContext: string; sources: readonly string[] }
	| { success: false; code: "NO_RELEVANT_SOURCE" };

export function buildGroundingContext(chunks: readonly GroundingChunk[]): GroundingResult {
	const groundedChunks = chunks.filter((chunk) => chunk.score >= 0.75 && chunk.source_document.length > 0);

	if (groundedChunks.length === 0) {
		return { success: false, code: "NO_RELEVANT_SOURCE" };
	}

	return {
		success: true,
		promptContext: groundedChunks
			.map((chunk) => `[source_document=${chunk.source_document}]\n${chunk.content}`)
			.join("\n\n"),
		sources: groundedChunks.map((chunk) => chunk.source_document),
	};
}
```

DON'T:

```ts
export function answerShippingQuestion(question: string): { answer: string; source_document: string } {
	if (question.includes("frete especial")) {
		return {
			answer: "O frete especial sempre leva 2 dias úteis.",
			source_document: "PROC-042",
		};
	}

	return { answer: "Consulte o atendimento.", source_document: "unknown" };
}
```

Problemas do DON'T: inventa regra logística, usa heurística por substring, não consulta chunks recuperados e usa fonte incompleta ou falsa.

## Testes com Vitest

- Escreva testes para schemas Zod, mappers, builders, fallback sem fonte e normalização de erro.
- Fixtures devem ser tipadas e pequenas.
- Testes não devem chamar Azure, OpenAI, AI Search ou serviços externos reais.
- Use dados de `tests/fixtures` quando o cenário for compartilhado.
- Verifique casos negativos: payload vazio, tipo errado, campo extra, fonte ausente e score insuficiente.

DO:

```ts
import { describe, expect, it } from "vitest";

import { validateQueryInput } from "../../../src/functions/query/validator";

describe("validateQueryInput", () => {
	it("rejects extra fields", () => {
		const result = validateQueryInput({ question: "Qual é o prazo de entrega?", debug: true });

		expect(result.success).toBe(false);
	});
});
```

DON'T:

```ts
it("works", async () => {
	const response: any = await fetch("https://real-openai-endpoint.example.com");
	expect(response.status).toBe(200);
});
```

Problemas do DON'T: teste depende de serviço externo real, usa `any`, não testa regra do projeto e gera resultado instável.

## Anti-padrões comuns gerados por LLMs neste projeto

- Criar handlers grandes que validam payload, chamam AI Search, montam prompt, chamam OpenAI e formatam resposta no mesmo arquivo.
- Usar `any` para resolver erro de compilação strict.
- Criar `source_document` falso quando o fluxo RAG ainda não recuperou documento.
- Transformar `ZodError` em string solta e perder `path` dos campos inválidos.
- Usar `console.log` para depuração permanente.
- Usar CommonJS em projeto com `type: "module"`.
- Duplicar tipos de request manualmente em vez de derivar de Zod.
- Criar classes `QueryRequest`, `SearchResult` ou `PipelineConfig` sem comportamento real.
- Fazer mock de tudo com objetos sem tipo, deixando testes passarem mesmo quando contrato muda.
- Misturar nomes em português e inglês nos identificadores do mesmo módulo.
- Criar aliases de import como `@/shared` sem configurar `tsconfig.json` e build.
- Retornar erro HTTP 200 com `{ error: ... }` em falhas de validação ou dependência.
- Capturar erro externo e devolver resposta genérica como se fosse resposta do assistente.
- Logar pergunta, histórico completo ou chunks inteiros para facilitar debug.

## Checklist antes de finalizar código TypeScript

- O código compila com `strict: true` sem `any`, non-null assertion ou casts desnecessários?
- Todo input externo começa como `unknown` e passa por Zod?
- Schemas de request usam `.strict()` e mensagens úteis?
- Tipos públicos são derivados de Zod quando o schema é a fonte de verdade?
- Imports usam ES modules e `import type` quando aplicável?
- Exports são named exports e têm nomes estáveis?
- Funções exportadas têm tipo de retorno explícito?
- Fluxos assíncronos usam `await` de forma controlada e tratam erro como `unknown`?
- Não há `console.log`, `console.error`, `console.warn` ou `console.debug`?
- Logs são estruturados, úteis e sem dados sensíveis?
- Respostas RAG factuais carregam `source_document` real?
- Quando não há fonte confiável, o código retorna fallback explícito em vez de inventar resposta?
- Testes Vitest cobrem sucesso, falha de validação e pelo menos um caso de ausência de fonte quando houver RAG?
- O arquivo novo está na pasta correta de `src` e não rompe as fronteiras entre function, service, pipeline, bot, web e shared?

## Skills que devem consumir esta Foundation

- `skills/foundation/error-handling.md`
- `skills/foundation/project-structure.md`
- `skills/domain/azure-functions-endpoint.md`
- `skills/domain/azure-ai-search-integration.md`
- `skills/domain/azure-openai-integration.md`
- `skills/domain/rag-pipeline.md`
- `skills/domain/react-components.md`
- `skills/domain/testing-patterns.md`
- `skills/artifact/create-rag-endpoint.md`
- `skills/artifact/create-integration-test.md`
- `skills/artifact/create-react-card.md`
- `skills/artifact/create-technical-doc.md`
