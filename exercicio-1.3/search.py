"""
Etapa 2 — Busca.

Recebe uma pergunta, gera o embedding da pergunta, busca os N chunks mais
similares no ChromaDB e retorna os chunks com score de similaridade.

O ChromaDB foi criado com espaço de distância "cosine", então a distância
retornada está em [0, 2]. Convertemos para similaridade = 1 - distância, de
modo que valores próximos de 1.0 indicam alta similaridade.

Busca híbrida
-------------
A busca puramente vetorial recupera mal dois casos comuns nesta base:
- tabelas markdown (SLA, multiplicadores de frete) embedam mal e afundam no
  ranking, mesmo contendo a resposta exata;
- descasamento de termos (a pergunta cita "Sudeste"/"Gold" e o termo está só na
  tabela).
Para mitigar, reranqueamos os candidatos vetoriais combinando a similaridade de
cosseno com um score de sobreposição de palavras-chave (estilo BM25 simples):

    score_final = ALPHA * similaridade_vetorial + (1 - ALPHA) * score_keyword

Isso é padrão em RAG de produção (hybrid search) e não exige serviço externo.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

import config

# Peso da componente vetorial no score híbrido (0..1).
ALPHA = 0.6

# Stopwords PT-BR mínimas para o componente de palavra-chave.
_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "para",
    "por", "com", "sem", "em", "no", "na", "nos", "nas", "que", "qual", "quais",
    "e", "ou", "se", "ao", "à", "the", "of", "is",
}


def _normalizar(texto: str) -> list[str]:
    """Minúsculas, sem acento, só palavras de conteúdo."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    palavras = re.findall(r"[a-z0-9]+", texto)
    return [p for p in palavras if p not in _STOPWORDS and len(p) > 1]


def _score_keyword(termos: list[str], texto: str) -> float:
    """Fração dos termos da pergunta presentes no chunk (0..1)."""
    if not termos:
        return 0.0
    alvo = set(_normalizar(texto))
    return sum(1 for t in set(termos) if t in alvo) / len(set(termos))


@lru_cache(maxsize=1)
def _modelo() -> SentenceTransformer:
    return SentenceTransformer(config.EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _colecao():
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_collection(name=config.COLLECTION_NAME)


def buscar(
    pergunta: str,
    top_k: int = config.DEFAULT_TOP_K,
    hibrido: bool = True,
) -> list[dict]:
    """Retorna os top_k chunks mais relevantes para a pergunta.

    Cada item: {id, texto, similaridade, distancia, score_keyword, score,
    metadata}. Quando hibrido=True, ordena por score híbrido; senão, por
    similaridade vetorial pura.
    """
    embedding = _modelo().encode([pergunta]).tolist()
    # Recupera mais candidatos do que o necessário para permitir o rerank.
    n_cand = max(top_k * 3, 12) if hibrido else top_k
    resultado = _colecao().query(
        query_embeddings=embedding,
        n_results=n_cand,
        include=["documents", "metadatas", "distances"],
    )

    termos = _normalizar(pergunta)
    chunks: list[dict] = []
    for i in range(len(resultado["ids"][0])):
        distancia = resultado["distances"][0][i]
        similaridade = 1 - distancia
        texto = resultado["documents"][0][i]
        kw = _score_keyword(termos, texto)
        score = ALPHA * similaridade + (1 - ALPHA) * kw if hibrido else similaridade
        chunks.append(
            {
                "id": resultado["ids"][0][i],
                "texto": texto,
                "distancia": distancia,
                "similaridade": round(similaridade, 4),
                "score_keyword": round(kw, 4),
                "score": round(score, 4),
                "metadata": resultado["metadatas"][0][i],
            }
        )

    chunks.sort(key=lambda c: c["score"], reverse=True)
    return chunks[:top_k]


if __name__ == "__main__":
    import sys

    pergunta = " ".join(sys.argv[1:]) or "Qual o prazo de devolução?"
    print(f"Pergunta: {pergunta}\n")
    for c in buscar(pergunta):
        m = c["metadata"]
        print(
            f"  score={c['score']:.4f} (vec={c['similaridade']:.3f} "
            f"kw={c['score_keyword']:.3f})  {m['doc_id']} / {m['secao']}"
        )
