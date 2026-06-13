import { z } from "zod";

export const MAX_QUESTION_LENGTH = 1000;
export const MAX_CONVERSATION_ID_LENGTH = 128;
export const MAX_HISTORY_TURNS = 3;
export const MAX_HISTORY_CONTENT_LENGTH = 2000;

export const queryHistoryTurnSchema = z
	.object({
		role: z.enum(["user", "assistant"], {
			invalid_type_error: "history.role deve ser user ou assistant.",
			required_error: "history.role é obrigatório.",
		}),
		content: z
			.string({
				invalid_type_error: "history.content deve ser uma string.",
				required_error: "history.content é obrigatório.",
			})
			.trim()
			.min(1, "history.content não pode ser vazio.")
			.max(
				MAX_HISTORY_CONTENT_LENGTH,
				`history.content deve ter no máximo ${MAX_HISTORY_CONTENT_LENGTH} caracteres.`,
			),
	})
	.strict();

export const queryRequestSchema = z
	.object(
		{
			question: z
				.string({
					invalid_type_error: "question deve ser uma string.",
					required_error: "question é obrigatório.",
				})
				.trim()
				.min(3, "question deve ter pelo menos 3 caracteres.")
				.max(
					MAX_QUESTION_LENGTH,
					`question deve ter no máximo ${MAX_QUESTION_LENGTH} caracteres.`,
				),
			conversationId: z
				.string({ invalid_type_error: "conversationId deve ser uma string." })
				.trim()
				.min(1, "conversationId não pode ser vazio.")
				.max(
					MAX_CONVERSATION_ID_LENGTH,
					`conversationId deve ter no máximo ${MAX_CONVERSATION_ID_LENGTH} caracteres.`,
				)
				.optional(),
			history: z
				.array(queryHistoryTurnSchema, {
					invalid_type_error: "history deve ser uma lista de turnos.",
				})
				.max(MAX_HISTORY_TURNS, `history aceita no máximo ${MAX_HISTORY_TURNS} turnos.`)
				.optional(),
		},
		{
			invalid_type_error: "Payload deve ser um objeto JSON.",
			required_error: "Payload é obrigatório.",
		},
	)
	.strict();

export type QueryHistoryTurn = z.infer<typeof queryHistoryTurnSchema>;
export type QueryRequest = z.infer<typeof queryRequestSchema>;

export interface ValidationIssue {
	path: string;
	message: string;
}

export type QueryValidationResult =
	| { success: true; data: QueryRequest }
	| { success: false; issues: ValidationIssue[] };

export function validateQueryInput(payload: unknown): QueryValidationResult {
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
