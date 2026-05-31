"""
Etapa 1 — Ingestão.

Lê os documentos da NovaTech (Anexo A), divide em chunks por seção de markdown,
gera embeddings com sentence-transformers e armazena no ChromaDB local.

Estratégia de chunking: SEÇÃO DE MARKDOWN (header-based / estrutural).
---------------------------------------------------------------------
Cada cabeçalho de seção (`##` ou `###`) inicia um novo chunk, que vai até o
próximo cabeçalho de nível igual ou superior. Justificativa:

1. Os documentos da NovaTech já são fortemente estruturados por seções
   semanticamente coesas (ex.: "3.1 Prazo geral", "2.1 Multiplicadores
   regionais"). Cada seção responde a uma pergunta de negócio inteira, então
   manter a seção íntegra preserva o contexto e evita cortar uma tabela ou uma
   regra no meio.
2. Chunking por tamanho fixo (ex.: 500 tokens) quebraria tabelas de frete/SLA e
   misturaria regras distintas, exatamente o erro mais perigoso do projeto
   (valor numérico errado com aparência de confiança).
3. O resultado fica alinhado com os chunks de referência do Anexo B, que também
   são por seção (POL-001-A = Seção 3.1, PROC-042v2-B = Seção 2.1, etc.).

Cada chunk carrega, no início do texto, um cabeçalho de procedência
(documento + versão + seção). Isso melhora o embedding (a seção "2.1" sozinha
não diz a que documento pertence) e permite citar a fonte na resposta.
"""
from __future__ import annotations

import re
import shutil

import chromadb
from sentence_transformers import SentenceTransformer

import config


def dividir_em_chunks(texto: str, arquivo: str) -> list[dict]:
    """Divide um documento markdown em chunks por seção (## e ###)."""
    meta_doc = config.DOC_METADATA[arquivo]
    linhas = texto.splitlines()

    # Título do documento = primeiro header de nível 1.
    titulo_doc = meta_doc["titulo"]
    for linha in linhas:
        if linha.startswith("# "):
            titulo_doc = linha[2:].strip()
            break

    chunks: list[dict] = []
    secao_atual = "Cabeçalho"
    buffer: list[str] = []

    def fechar_secao():
        corpo = "\n".join(buffer).strip()
        if not corpo:
            return
        cabecalho = (
            f"[Fonte: {titulo_doc} "
            f"(v{meta_doc['versao']}) | Seção: {secao_atual}]"
        )
        chunks.append(
            {
                "texto": f"{cabecalho}\n{corpo}",
                "secao": secao_atual,
            }
        )

    for linha in linhas:
        if re.match(r"^#{2,3}\s+", linha):
            # Novo header de seção: fecha a seção anterior e começa outra.
            fechar_secao()
            secao_atual = re.sub(r"^#{2,3}\s+", "", linha).strip()
            buffer = []
        elif linha.startswith("# "):
            # Header de nível 1 (título do doc): ignora como conteúdo.
            continue
        else:
            buffer.append(linha)
    fechar_secao()

    # Monta o registro final de cada chunk com id e metadados.
    registros = []
    for i, ch in enumerate(chunks):
        registros.append(
            {
                "id": f"{meta_doc['doc_id']}::{i:02d}",
                "texto": ch["texto"],
                "metadata": {
                    "doc_id": meta_doc["doc_id"],
                    "arquivo": arquivo,
                    "titulo": titulo_doc,
                    "secao": ch["secao"],
                    "classificacao": meta_doc["classificacao"],
                    "versao": meta_doc["versao"],
                    "confiavel": meta_doc["confiavel"],
                },
            }
        )
    return registros


def ingerir() -> None:
    print("== Etapa 1: Ingestão ==\n")

    # Recria o vector store do zero a cada execução (POC reproduzível).
    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)

    print(f"Carregando modelo de embeddings: {config.EMBEDDING_MODEL} ...")
    modelo = SentenceTransformer(config.EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    colecao = client.create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    todos: list[dict] = []
    for arquivo in config.SOURCE_FILES:
        caminho = config.DOCS_DIR / arquivo
        texto = caminho.read_text(encoding="utf-8")
        registros = dividir_em_chunks(texto, arquivo)
        todos.extend(registros)
        print(f"  {arquivo:<45} -> {len(registros):>2} chunks")

    print(f"\nTotal de chunks: {len(todos)}")
    print("Gerando embeddings ...")

    textos = [r["texto"] for r in todos]
    embeddings = modelo.encode(textos, show_progress_bar=False).tolist()

    colecao.add(
        ids=[r["id"] for r in todos],
        documents=textos,
        embeddings=embeddings,
        metadatas=[r["metadata"] for r in todos],
    )

    print(f"\nArmazenado em ChromaDB: {config.CHROMA_DIR}")
    print(f"Coleção '{config.COLLECTION_NAME}' com {colecao.count()} chunks.\n")


if __name__ == "__main__":
    ingerir()
