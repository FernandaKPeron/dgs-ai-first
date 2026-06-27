import { z } from 'zod';

export const assistantResponseSchema = z.object({
	answer: z.string().min(1, 'answer cannot be empty'),
	source_document: z.string().min(1, 'source_document cannot be empty'),
	confidence_score: z
		.number()
		.min(0, 'confidence_score must be greater than or equal to 0')
		.max(1, 'confidence_score must be less than or equal to 1'),
});

export type AssistantResponse = z.infer<typeof assistantResponseSchema>;
