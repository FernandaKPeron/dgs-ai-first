"""
Etapa 3 — Montagem de prompt.

Recebe os chunks recuperados e a pergunta e monta o prompt completo
(system prompt + contexto + pergunta) pronto para enviar ao LLM
(Claude via chat manual ou modelo local via Ollama).

O system prompt impõe as regras de segurança do RAG identificadas no Anexo B:
- responder SOMENTE com base nos chunks recuperados (anti-alucinação);
- citar a fonte (doc_id + seção) de cada afirmação;
- abster-se quando a informação não estiver no contexto;
- preferir a versão mais recente e sinalizar contradições (PROC-042 vs v2);
- tratar o FAQ como fonte informal não validada.
"""
from __future__ import annotations

import config
from search import buscar

SYSTEM_PROMPT = """\
Você é o assistente de atendimento da NovaTech. Responda em português, de forma
objetiva, ajudando o atendente a resolver a dúvida do cliente.

REGRAS OBRIGATÓRIAS:
1. Use SOMENTE as informações presentes no CONTEXTO abaixo. Não use conhecimento
   externo nem invente dados (valores de frete, prazos, tiers, percentuais).
2. Cite a fonte de cada afirmação no formato [doc_id — Seção]. A fonte está no
   cabeçalho de cada trecho do contexto.
3. Se a informação necessária NÃO estiver no contexto, responda exatamente:
   "Não encontrei essa informação na documentação oficial." e oriente o
   encaminhamento adequado, se houver no contexto.
4. Se houver contradição entre versões de um documento (ex.: PROC-042 v1 vs
   PROC-042-v2), use a versão mais recente (v2) e avise explicitamente que
   existe uma versão anterior divergente.
5. O documento FAQ é uma fonte INFORMAL, não validada por Compliance. Se a
   resposta depender apenas do FAQ, sinalize que a informação não tem respaldo
   normativo e deve ser confirmada.
"""


def montar_prompt(pergunta: str, chunks: list[dict]) -> str:
    """Monta o prompt completo (system + contexto + pergunta)."""
    blocos = []
    for i, c in enumerate(chunks, start=1):
        m = c["metadata"]
        origem = "INFORMAL (não validado)" if not m["confiavel"] else m["classificacao"]
        blocos.append(
            f"--- Trecho {i} "
            f"(similaridade {c['similaridade']:.2f} | origem: {origem}) ---\n"
            f"{c['texto']}"
        )
    contexto = "\n\n".join(blocos) if blocos else "(nenhum trecho recuperado)"

    return (
        f"{SYSTEM_PROMPT}\n"
        f"===== CONTEXTO =====\n"
        f"{contexto}\n\n"
        f"===== PERGUNTA DO ATENDENTE =====\n"
        f"{pergunta}\n\n"
        f"===== RESPOSTA =====\n"
    )


def montar_prompt_para(pergunta: str, top_k: int = config.DEFAULT_TOP_K) -> str:
    """Atalho: busca os chunks e monta o prompt em um passo."""
    return montar_prompt(pergunta, buscar(pergunta, top_k))


if __name__ == "__main__":
    import sys

    pergunta = " ".join(sys.argv[1:]) or "Qual o SLA do cliente Gold?"
    print(montar_prompt_para(pergunta))
