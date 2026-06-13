import { describe, expect, it } from "vitest";

import { queryHandler } from "../../src/functions/query/handler";
import { MAX_HISTORY_TURNS, validateQueryInput } from "../../src/functions/query/validator";

describe("query input validation", () => {
  it("normaliza payload válido", () => {
    const result = validateQueryInput({
      question: "  Como consultar frete especial?  ",
      conversationId: "  atendimento-123  ",
      history: [{ role: "user", content: "  Cliente perguntou sobre SLA.  " }],
    });

    expect(result.success).toBe(true);

    if (result.success) {
      expect(result.data.question).toBe("Como consultar frete especial?");
      expect(result.data.conversationId).toBe("atendimento-123");
      expect(result.data.history?.[0]?.content).toBe("Cliente perguntou sobre SLA.");
    }
  });

  it("rejeita history acima de 3 turnos", () => {
    const result = validateQueryInput({
      question: "Como consultar frete especial?",
      history: Array.from({ length: MAX_HISTORY_TURNS + 1 }, () => ({
        role: "user",
        content: "Pergunta anterior",
      })),
    });

    expect(result.success).toBe(false);

    if (!result.success) {
      expect(result.issues).toContainEqual({
        path: "history",
        message: "history aceita no máximo 3 turnos.",
      });
    }
  });
});

describe("queryHandler", () => {
  it("retorna 400 para JSON inválido", async () => {
    const response = await queryHandler({ method: "POST", body: "{" });

    expect(response.status).toBe(400);
    expect(response.jsonBody).toMatchObject({
      error: {
        code: "INVALID_JSON",
        message: "Corpo da requisição deve ser um JSON válido.",
      },
    });
  });

  it("retorna 400 para payload vazio", async () => {
    const response = await queryHandler({ method: "POST", body: {} });

    expect(response.status).toBe(400);
    expect(response.jsonBody).toMatchObject({
      error: {
        code: "INVALID_REQUEST",
        message: "Payload não pode ser vazio.",
      },
    });
  });

  it("retorna 400 para question inválida", async () => {
    const response = await queryHandler({ method: "POST", body: { question: "  " } });

    expect(response.status).toBe(400);
    expect(response.jsonBody).toMatchObject({
      error: {
        code: "INVALID_REQUEST",
        details: [{ path: "question", message: "question deve ter pelo menos 3 caracteres." }],
      },
    });
  });

  it("retorna 501 com echo normalizado para payload válido", async () => {
    const response = await queryHandler({
      method: "POST",
      body: { question: "  Como consultar frete especial?  " },
    });

    expect(response.status).toBe(501);
    expect(response.jsonBody).toMatchObject({
      error: { code: "QUERY_FLOW_NOT_IMPLEMENTED" },
      echo: { question: "Como consultar frete especial?" },
    });
  });
});