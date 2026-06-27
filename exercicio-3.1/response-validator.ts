import { assistantResponseSchema, type AssistantResponse } from './schema';

export const SAFE_FALLBACK_RESPONSE =
	'Desculpe, não consigo responder isso com confiança. Por favor, escale ao supervisor.';

/**
 * Confiança mínima aceita. Abaixo disso, devolvemos o fallback em vez da
 * resposta do modelo. Ajustar ao domínio com base em dados reais.
 */
const MIN_CONFIDENCE_SCORE = 0.5;

// ---------------------------------------------------------------------------
// Normalização de texto
// ---------------------------------------------------------------------------

/** Remove acentos e baixa para minúsculas, para casar texto de forma estável. */
function normalizeText(value: string): string {
	return value
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.toLowerCase();
}

/**
 * Quebra o texto em sentenças/cláusulas. Usado para escopar a negação:
 * "não realizamos coleta; a devolução é permitida" são duas afirmações
 * distintas e não devem se contaminar.
 */
function splitClauses(normalized: string): string[] {
	return normalized
		.split(/[.!?;\n]+/)
		.map((clause) => clause.trim())
		.filter((clause) => clause.length > 0);
}

// ---------------------------------------------------------------------------
// Padrões do domínio (escritos sem acento/maiúscula, pois rodam sobre texto já normalizado)
// ---------------------------------------------------------------------------

/** Cobre singular e plural: "carga perigosa", "cargas perigosas". */
const DANGEROUS_CARGO_PATTERN = /cargas? perigosas?/;

/** Cobre substantivo e verbo: "devolucao", "devolver", "devolvida", "devolvido". */
const RETURN_PATTERN = /devol(u|v)/;

/** Negação simples ("não", "nunca", "jamais") como token isolado. */
const NEGATION_PATTERN = /\b(nao|nunca|jamais)\b/;

/** Termos que, por si só, expressam impedimento de devolução. */
const DENIAL_PATTERN = /(proibid|vedad|impossivel|impedid|inviavel|negad|recusad)/;

/** Termos que expressam autorização de devolução. */
const AUTHORIZATION_PATTERN =
	/(permitid|liberad|autorizad|aceit|viavel|pode|podem|poderia|possivel)/;

/**
 * Dupla negação que reabilita a devolução: "não é proibido", "nunca foi vedado".
 * Tratada como AUTORIZAÇÃO — é justamente o caso que um "denial vence" ingênuo
 * deixaria passar.
 */
const NEGATED_DENIAL_PATTERN =
	/\b(nao|nunca|jamais)\b[^.;!?]{0,20}(proibid|vedad|impedid|impossivel|inviavel)/;

type ReturnStance = 'deny' | 'authorize' | 'unclear';

/**
 * Classifica a postura de UMA cláusula sobre devolução.
 * A ordem dos testes importa: a dupla negação ("não é proibido") precisa ser
 * avaliada antes da negação simples, senão seria lida como negativa.
 */
function classifyReturnStance(clause: string): ReturnStance {
	if (NEGATED_DENIAL_PATTERN.test(clause)) {
		return 'authorize';
	}

	if (NEGATION_PATTERN.test(clause) || DENIAL_PATTERN.test(clause)) {
		return 'deny';
	}

	if (AUTHORIZATION_PATTERN.test(clause)) {
		return 'authorize';
	}

	return 'unclear';
}

// ---------------------------------------------------------------------------
// Guardrails de negócio
// ---------------------------------------------------------------------------

/** Retorna o motivo da reprovação, ou `null` se o guardrail passou. */
type Guardrail = (response: AssistantResponse) => string | null;

const requireSourceDocument: Guardrail = (response) =>
	response.source_document.trim().length === 0 ? 'source_document está vazio' : null;

const requireNonEmptyAnswer: Guardrail = (response) =>
	response.answer.trim().length === 0 ? 'answer está vazio' : null;

const requireMinimumConfidence: Guardrail = (response) =>
	response.confidence_score < MIN_CONFIDENCE_SCORE
		? `confidence_score ${response.confidence_score} abaixo do mínimo ${MIN_CONFIDENCE_SCORE}`
		: null;

/**
 * Devolução de carga perigosa só é liberada se a resposta NEGAR de forma clara.
 *
 * Política default-deny: qualquer ambiguidade reprova e cai no fallback. Isso
 * pode mandar ao supervisor algumas respostas válidas (falso-positivo), o que é
 * aceitável; o que não podemos é aprovar uma autorização indevida (falso-negativo).
 */
const enforceDangerousCargoReturnPolicy: Guardrail = (response) => {
	const normalized = normalizeText(response.answer);

	const mentionsDangerousCargo = DANGEROUS_CARGO_PATTERN.test(normalized);
	const mentionsReturn = RETURN_PATTERN.test(normalized);
	if (!mentionsDangerousCargo || !mentionsReturn) {
		return null; // regra não se aplica
	}

	const stances = splitClauses(normalized)
		.filter((clause) => RETURN_PATTERN.test(clause))
		.map(classifyReturnStance);

	if (stances.includes('authorize')) {
		return 'resposta autoriza (ou sugere autorizar) devolução de carga perigosa';
	}

	if (!stances.includes('deny')) {
		return 'resposta sobre devolução de carga perigosa sem negativa clara (default-deny)';
	}

	return null;
};

const GUARDRAILS: Guardrail[] = [
	requireSourceDocument,
	requireNonEmptyAnswer,
	requireMinimumConfidence,
	enforceDangerousCargoReturnPolicy,
];

// ---------------------------------------------------------------------------
// Entrada/saída
// ---------------------------------------------------------------------------

function toCandidatePayload(rawModelResponse: unknown): unknown {
	if (typeof rawModelResponse === 'string') {
		try {
			return JSON.parse(rawModelResponse);
		} catch {
			return null;
		}
	}

	return rawModelResponse;
}

interface ValidationContext {
	requestId?: string;
}

function logValidationFailure(
	reason: string,
	context: { requestId?: string; answer?: string } = {}
): void {
	// Log estruturado: motivo + correlação + amostra truncada da resposta barrada
	// (truncada para não vazar conteúdo sensível inteiro e ajudar no diagnóstico).
	console.error('[response-validator] validation failed', {
		reason,
		requestId: context.requestId,
		answerPreview: context.answer?.slice(0, 200),
	});
}

export function validateAssistantResponse(
	rawModelResponse: unknown,
	context: ValidationContext = {}
): AssistantResponse | null {
	const candidate = toCandidatePayload(rawModelResponse);
	const parsed = assistantResponseSchema.safeParse(candidate);

	if (!parsed.success) {
		const detail = parsed.error.issues
			.map((issue) => `${issue.path.join('.')}: ${issue.message}`)
			.join('; ');
		logValidationFailure(`schema validation failed: ${detail}`, {
			requestId: context.requestId,
		});
		return null;
	}

	const response = parsed.data;

	for (const guardrail of GUARDRAILS) {
		const reason = guardrail(response);
		if (reason !== null) {
			logValidationFailure(`guardrail failed: ${reason}`, {
				requestId: context.requestId,
				answer: response.answer,
			});
			return null;
		}
	}

	return response;
}