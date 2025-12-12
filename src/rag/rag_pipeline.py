# src/rag/rag_pipeline.py

import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter

from chromadb.utils import embedding_functions
import chromadb
from chromadb import Client

from src.core.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_TOP_K,
)


# -----------------------------
# PDF Loader
# -----------------------------
class PDFLoader:
    """
    Loads a PDF file and extracts text page by page.
    Returns list of text blocks.
    """

    def __init__(self):
        self.documents = [] # list of page texts
        self.metadata = {} # e.g., document_name, page_count

    def load_pdf(self, file):
        self.metadata["document_name"] = getattr(file, "name", "uploaded.pdf")
        extracted_pages = []

        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text() # extract text from the page
                if text and text.strip():
                    extracted_pages.append(text.strip())

        self.documents = extracted_pages
        self.metadata["page_count"] = len(extracted_pages)

        return self.documents


# -----------------------------
# Chunker
# -----------------------------
class Chunker:
    """
    Character-based chunking.
    """

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " ", ""], 
            chunk_size=chunk_size, 
            chunk_overlap=overlap,
        )

    def prepare_chunks(self, pages):
        """
        Returns:
            chunks: list of chunk strings
        """
        combined_text = "\n\n".join(pages)
        chunks = self.splitter.split_text(combined_text)
        return chunks


# -----------------------------
# Embedder (SentenceTransformer)
# -----------------------------
class Embedder:
    """
    Uses SentenceTransformerEmbeddingFunction.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )

    # Embeds a list of texts
    def embed(self, texts):
        return self.embedding_function(texts)
    
    # Embeds a single query
    def embed_query(self, query):
        return self.embedding_function([query])[0]


# -----------------------------
# VectorStore (ChromaDB)
# -----------------------------
class VectorStore:
    def __init__(self, collection_name: str, embedding_function):
        self.client = Client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

    def add_chunks(self, chunks, document_name, start_id=0):
        ids = [str(i + start_id) for i in range(len(chunks))]
        metadatas = [
            {"document": document_name, "chunk_index": i}
            for i in range(len(chunks))
        ]

        self.collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        return len(ids)

    def query(self, text, k: int = DEFAULT_TOP_K):
        return self.collection.query(
            query_texts=[text],
            n_results=k,
            include=["documents"],
        )

    def count(self):
        return self.collection.count()


# -----------------------------
# RAG Pipeline
# -----------------------------
class RAGPipeline:
    """
    High-level RAG pipeline:
    - loads PDF
    - chunks pages
    - embeds + indexes chunks
    """

    def __init__(
        self,
        collection_name: str = COLLECTION_NAME,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

        self.loader = PDFLoader()
        self.chunker = Chunker(chunk_size=self.chunk_size, overlap=self.overlap)
        self.embedder = Embedder()
        self.vstore = VectorStore(collection_name, self.embedder.embedding_function)

        self.offset = 0

    def index_pdf(self, file, chunk_size: int | None = None, overlap: int | None = None):
        pages = self.loader.load_pdf(file)
        meta = self.loader.metadata
        doc_name = meta["document_name"]

        chunks = self.chunker.prepare_chunks(pages)

        count_new = self.vstore.add_chunks(
            chunks,
            document_name=doc_name,
            start_id=self.offset,
        )

        self.offset += count_new

        return {
            "document_name": doc_name,
            "page_count": meta["page_count"],
            "chunks_added": count_new,
            "total_chunks_in_db": self.vstore.count(),
        }

    def search(self, query: str, k: int = DEFAULT_TOP_K):
        return self.vstore.query(query, k)