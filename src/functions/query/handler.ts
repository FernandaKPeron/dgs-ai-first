import type { QueryRequest, ValidationIssue } from "./validator";
import { validateQueryInput } from "./validator";

const QUERY_ROUTE = "/api/query";
const POST_METHOD = "POST";
const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" } as const;

export interface QueryHttpRequest {
  method?: string;
  url?: string;
  body?: unknown;
  json?: () => Promise<unknown>;
}

export interface QueryErrorBody {
  error: {
    code: "INVALID_JSON" | "INVALID_REQUEST" | "METHOD_NOT_ALLOWED";
    message: string;
    details?: ValidationIssue[];
  };
}

export interface QueryNotImplementedBody {
  error: {
    code: "QUERY_FLOW_NOT_IMPLEMENTED";
    message: string;
  };
  echo: QueryRequest;
}

export type QueryHandlerBody = QueryErrorBody | QueryNotImplementedBody;

export interface QueryHandlerResponse {
  status: number;
  headers: typeof JSON_HEADERS;
  jsonBody: QueryHandlerBody;
}

type BodyReadResult =
  | { success: true; payload: unknown }
  | { success: false; code: "INVALID_JSON" | "INVALID_REQUEST"; message: string };

export async function queryHandler(request: QueryHttpRequest): Promise<QueryHandlerResponse> {
  if (request.method !== undefined && request.method.toUpperCase() !== POST_METHOD) {
    return errorResponse(405, "METHOD_NOT_ALLOWED", `Use ${POST_METHOD} ${QUERY_ROUTE}.`);
  }

  const body = await readJsonBody(request);

  if (!body.success) {
    return errorResponse(400, body.code, body.message);
  }

  if (isEmptyObject(body.payload)) {
    return errorResponse(400, "INVALID_REQUEST", "Payload não pode ser vazio.");
  }

  const validation = validateQueryInput(body.payload);

  if (!validation.success) {
    return errorResponse(400, "INVALID_REQUEST", "Payload inválido.", validation.issues);
  }

  return notImplementedResponse(validation.data);
}

async function readJsonBody(request: QueryHttpRequest): Promise<BodyReadResult> {
  if (request.body !== undefined) {
    return parseBodyValue(request.body);
  }

  if (request.json === undefined) {
    return {
      success: false,
      code: "INVALID_REQUEST",
      message: "Payload é obrigatório.",
    };
  }

  try {
    return parseBodyValue(await request.json());
  } catch {
    return {
      success: false,
      code: "INVALID_JSON",
      message: "Corpo da requisição deve ser um JSON válido.",
    };
  }
}

function parseBodyValue(value: unknown): BodyReadResult {
  if (typeof value !== "string") {
    return { success: true, payload: value };
  }

  const trimmed = value.trim();

  if (trimmed.length === 0) {
    return {
      success: false,
      code: "INVALID_REQUEST",
      message: "Payload é obrigatório.",
    };
  }

  try {
    return { success: true, payload: JSON.parse(trimmed) as unknown };
  } catch {
    return {
      success: false,
      code: "INVALID_JSON",
      message: "Corpo da requisição deve ser um JSON válido.",
    };
  }
}

function isEmptyObject(value: unknown): boolean {
  return typeof value === "object" && value !== null && !Array.isArray(value) && Object.keys(value).length === 0;
}

function errorResponse(
  status: number,
  code: QueryErrorBody["error"]["code"],
  message: string,
  details?: ValidationIssue[],
): QueryHandlerResponse {
  return {
    status,
    headers: JSON_HEADERS,
    jsonBody: {
      error: {
        code,
        message,
        ...(details === undefined ? {} : { details }),
      },
    },
  };
}

function notImplementedResponse(payload: QueryRequest): QueryHandlerResponse {
  return {
    status: 501,
    headers: JSON_HEADERS,
    jsonBody: {
      error: {
        code: "QUERY_FLOW_NOT_IMPLEMENTED",
        message: "Fluxo RAG ainda não implementado nesta task.",
      },
      echo: payload,
    },
  };
}
