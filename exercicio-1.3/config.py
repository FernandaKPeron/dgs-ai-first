"""
Configurações compartilhadas do pipeline de RAG (POC NovaTech).

Centraliza caminhos, nome do modelo de embeddings, parâmetros de chunking e
metadados de autoridade/recência por documento — usados por ingest, search e
prompt.
"""
from pathlib import Path

# Diretórios
BASE_DIR = Path(__file__).resolve().parent
# Os 5 documentos individuais (.md) ficam na pasta da prática 1.
DOCS_DIR = BASE_DIR.parent / "pratica-1"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Modelo de embeddings open-source (gratuito, roda local).
# Os documentos da NovaTech estão em português. O modelo sugerido no enunciado
# (all-MiniLM-L6-v2) é treinado em inglês e recupera mal em PT-BR (testado: 2/6
# acertos no gabarito). Trocamos pelo equivalente MULTILÍNGUE da mesma família
# sentence-transformers, que mantém o caráter gratuito/local e melhora muito a
# recuperação em português.
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Vector store
COLLECTION_NAME = "novatech_docs"

# Quantos chunks recuperar por padrão na busca.
# 5 é o valor validado no gabarito (Anexo B): tabelas markdown (SLA, frete)
# embedam mal e caem para o 5º lugar mesmo contendo a resposta exata, então um
# top_k menor cortaria o chunk certo.
DEFAULT_TOP_K = 5

# Arquivos que compõem a base. A ordem não importa, mas a lista explícita evita
# ingerir acidentalmente os anexos agregados (anexo-a / anexo-b).
SOURCE_FILES = [
    "POL-001-politica-devolucao.md",
    "PROC-042-frete-especial-v1.md",
    "PROC-042-v2-frete-especial-revisado.md",
    "SLA-2024-tabela-sla-clientes.md",
    "FAQ-atendimento.md",
]

# Metadados de autoridade e recência por documento.
# Usados como metadado dos chunks para que o LLM (e eventuais filtros) saibam
# distinguir documento normativo de FAQ informal e versão antiga de revisada.
DOC_METADATA = {
    "POL-001-politica-devolucao.md": {
        "doc_id": "POL-001",
        "titulo": "Política de Devolução de Mercadorias",
        "classificacao": "normativo",
        "versao": "3.1",
        "data": "2024-01-15",
        "confiavel": True,
    },
    "PROC-042-frete-especial-v1.md": {
        "doc_id": "PROC-042",
        "titulo": "Cálculo de Frete Especial (v1)",
        "classificacao": "procedimento",
        "versao": "1.0",
        "data": "2023-03-03",
        "confiavel": True,
        "obsoleto_por": "PROC-042-v2",
    },
    "PROC-042-v2-frete-especial-revisado.md": {
        "doc_id": "PROC-042-v2",
        "titulo": "Cálculo de Frete Especial (Revisado)",
        "classificacao": "procedimento",
        "versao": "2.0",
        "data": "2023-11-10",
        "confiavel": True,
    },
    "SLA-2024-tabela-sla-clientes.md": {
        "doc_id": "SLA-2024",
        "titulo": "Tabela de SLA por Tipo de Cliente",
        "classificacao": "contratual",
        "versao": "2024.1",
        "data": "2024-01-02",
        "confiavel": True,
    },
    "FAQ-atendimento.md": {
        "doc_id": "FAQ",
        "titulo": "FAQ de Atendimento",
        "classificacao": "informal",
        "versao": "nao-controlada",
        "data": "",
        "confiavel": False,
    },
}
