import {
  app,
  HttpRequest,
  HttpResponseInit,
  InvocationContext,
} from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';
import { DefaultAzureCredential } from '@azure/identity';
import { randomUUID } from 'node:crypto';
import { z } from 'zod';
import pino from 'pino';

const logger = pino({ name: 'feedback' });

/**
 * Fail-fast: configuração ausente derruba o processo no startup, não em runtime.
 * Usa Managed Identity (DefaultAzureCredential) em vez de connection string.
 */
const cosmosEndpoint = process.env.COSMOS_ENDPOINT;
if (!cosmosEndpoint) {
  throw new Error('COSMOS_ENDPOINT não configurada');
}

/**
 * Cliente e container instanciados UMA vez por processo (reuso de conexões).
 */
const credential = new DefaultAzureCredential();
const cosmosClient = new CosmosClient({
  endpoint: cosmosEndpoint,
  aadCredentials: credential,
});
const container = cosmosClient.database('novatech').container('feedbacks');

/**
 * Validação de input com Zod.
 * .strict() rejeita campos extras — mais seguro.
 */
const feedbackSchema = z
  .object({
    queryId: z.string().min(1, 'queryId não pode ser vazio'),
    rating: z
      .number({ invalid_type_error: 'rating deve ser numérico' })
      .int('rating deve ser inteiro')
      .min(1, 'rating deve estar entre 1 e 5')
      .max(5, 'rating deve estar entre 1 e 5'),
    comment: z
      .string({ invalid_type_error: 'comment deve ser string' })
      .max(5000, 'comment máximo 5000 caracteres')
      .optional(),
    attendantEmail: z
      .string({ invalid_type_error: 'attendantEmail deve ser string' })
      .email('attendantEmail deve ser um e-mail válido'),
  })
  .strict();

type FeedbackInput = z.infer<typeof feedbackSchema>;

export async function feedbackHandler(
  request: HttpRequest,
  context: InvocationContext
): Promise<HttpResponseInit> {
  // request.json() lança em body ausente/JSON malformado: tratamos como 400
  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return { status: 400, jsonBody: { error: 'JSON inválido' } };
  }

  const parsed = feedbackSchema.safeParse(raw);
  if (!parsed.success) {
    // Logamos issues (path + message), que não contêm os valores enviados
    logger.warn(
      {
        invocationId: context.invocationId,
        issues: parsed.error.issues,
      },
      'Validação de feedback falhou'
    );
    return {
      status: 400,
      jsonBody: { error: 'Payload inválido', issues: parsed.error.issues },
    };
  }

  const data: FeedbackInput = parsed.data;

  const feedback = {
    id: randomUUID(),
    ...data,
    timestamp: new Date().toISOString(),
  };

  /**
   * NUNCA logar PII (email/nome). Só metadados não sensíveis.
   */
  logger.info(
    {
      invocationId: context.invocationId,
      queryId: feedback.queryId,
      rating: feedback.rating,
    },
    'Feedback recebido'
  );

  try {
    await container.items.create(feedback);
  } catch (err) {
    // Erro detalhado vai só para o log interno; resposta ao cliente é genérica
    logger.error(
      {
        invocationId: context.invocationId,
        err,
      },
      'Falha ao persistir feedback'
    );
    return { status: 500, jsonBody: { error: 'Erro interno' } };
  }

  return { status: 201, jsonBody: { status: 'created' } };
}

app.http('feedback', {
  methods: ['POST'],
  /**
   * 'function' exige chave de API. Alternativa mais segura:
   * proteger com Easy Auth/APIM e derivar attendantEmail da identidade
   * autenticada (elimina spoofing do email no body).
   */
  authLevel: 'function',
  handler: feedbackHandler,
});