"""
Teste do pipeline de RAG com perguntas do mapa de cobertura (Anexo B).

Para cada pergunta documenta:
- quais chunks foram recuperados (doc_id / seção);
- o score de similaridade;
- se os chunks corretos foram recuperados (comparando com o gabarito do Anexo B);
- alertas sobre as armadilhas (contradição PROC-042 v1 x v2, tier inexistente,
  pergunta sem cobertura, uso de FAQ informal).

Executa a busca real no ChromaDB. Rode `python ingest.py` antes.
"""
from __future__ import annotations

import config
from search import buscar

TOP_K = config.DEFAULT_TOP_K

# Gabarito derivado do "Mapa de cobertura" do Anexo B.
# esperados: lista de (doc_id, trecho_da_secao) que DEVEM ser recuperados.
# sem_cobertura: True quando a base não tem documento para a pergunta.
# armadilha: nota sobre o que validar manualmente.
CASOS = [
    {
        "pergunta": "Qual o prazo de devolução?",
        "esperados": [("POL-001", "3.1"), ("POL-001", "3.2")],
        "armadilha": None,
    },
    {
        "pergunta": "Qual o SLA do cliente Gold?",
        "esperados": [("SLA-2024", "Tabela de SLAs")],
        "armadilha": None,
    },
    {
        "pergunta": "Frete para 600kg para Manaus?",
        "esperados": [("PROC-042-v2", "2.1"), ("PROC-042-v2", "Fórmula")],
        "armadilha": "Se PROC-042 (v1) for recuperado junto, há risco de "
        "contradição de multiplicadores (Norte 1.6 x 1.8).",
    },
    {
        "pergunta": "Qual o SLA do cliente Platinum?",
        "esperados": [("SLA-2024", "Classificação")],
        "armadilha": "Tier Platinum NÃO existe. O chunk de classificação diz "
        "que só há 3 tiers — o LLM deve negar a existência, não inventar SLA.",
    },
    {
        "pergunta": "Frete para 300kg para Salvador?",
        "esperados": [],
        "sem_cobertura": True,
        "armadilha": "Frete padrão (<500kg) não está documentado. O LLM deve "
        "se abster, mesmo que a busca traga chunks de frete especial.",
    },
    {
        "pergunta": "Qual o multiplicador para o Sudeste?",
        "esperados": [("PROC-042-v2", "2.1")],
        "armadilha": "PROC-042 (v1) pode aparecer (Sudeste 1.0 x 1.1). Usar v2 "
        "e sinalizar a versão antiga.",
    },
]


def _bate(chunk: dict, doc_id: str, secao_substr: str) -> bool:
    m = chunk["metadata"]
    return m["doc_id"] == doc_id and secao_substr.lower() in m["secao"].lower()


def avaliar() -> None:
    print("=" * 78)
    print("TESTE DO PIPELINE DE RAG — NovaTech (gabarito: Anexo B)")
    print(f"top_k = {TOP_K} | modelo = {config.EMBEDDING_MODEL}")
    print("busca = híbrida (vetorial cosine + reforço por palavra-chave)")
    print("=" * 78)

    total_ok = 0
    for n, caso in enumerate(CASOS, start=1):
        pergunta = caso["pergunta"]
        chunks = buscar(pergunta, TOP_K)

        print(f"\n[{n}] Pergunta: {pergunta}")
        print("    Chunks recuperados (score | vec | kw):")
        for c in chunks:
            m = c["metadata"]
            flag = "" if m["confiavel"] else "  <FAQ informal>"
            print(
                f"      {c['score']:.3f} | {c['similaridade']:.3f} | "
                f"{c['score_keyword']:.3f}  {m['doc_id']:<12} "
                f"{m['secao']}{flag}"
            )

        # Avaliação contra o gabarito.
        if caso.get("sem_cobertura"):
            # "Acerto" = nenhum documento formal cobre; o pipeline pode até
            # trazer chunks de frete especial, mas a resposta correta é abster.
            tem_formal_relevante = any(
                c["metadata"]["doc_id"] != "FAQ"
                and c["similaridade"] >= 0.5
                for c in chunks
            )
            ok = not tem_formal_relevante
            print(
                "    Gabarito: SEM cobertura na base. "
                + (
                    "OK — nenhum chunk formal com similaridade alta."
                    if ok
                    else "ATENÇÃO — há chunk formal com similaridade >= 0.50; "
                    "o LLM deve mesmo assim se abster."
                )
            )
        else:
            recuperados = []
            faltando = []
            for doc_id, secao in caso["esperados"]:
                if any(_bate(c, doc_id, secao) for c in chunks):
                    recuperados.append(f"{doc_id}/{secao}")
                else:
                    faltando.append(f"{doc_id}/{secao}")
            ok = not faltando
            print(
                f"    Gabarito esperado: {recuperados or '—'}"
                + (f" | FALTANDO: {faltando}" if faltando else "")
            )

        total_ok += int(ok)
        print(f"    Resultado: {'ACERTO' if ok else 'DIVERGENCIA'}")
        if caso.get("armadilha"):
            print(f"    Armadilha: {caso['armadilha']}")

    print("\n" + "=" * 78)
    print(f"Resumo: {total_ok}/{len(CASOS)} casos com recuperação esperada.")
    print("=" * 78)


if __name__ == "__main__":
    avaliar()
