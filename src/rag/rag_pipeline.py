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
)


class PDFLoader:
    """
    Loads a PDF file and extracts text page by page.
    Returns list of: { text: "...", page_number: X, document_name: "..." }
    """

    def __init__(self):
        self.documents = []
        self.metadata = {}

    def load_pdf(self, file):
        self.metadata["document_name"] = getattr(file, "name", "uploaded.pdf")
        extracted_pages = []

        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    extracted_pages.append(
                        {
                            "text": text.strip(),
                            "page_number": page_num,
                            "document_name": self.metadata["document_name"],
                        }
                    )

        self.documents = extracted_pages
        self.metadata["page_count"] = len(extracted_pages)

        return self.documents


class Chunker:
    """
    Character-based chunking.
    Includes page_number mapping for each chunk.
    """

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = 0):
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
            page_numbers: list of page_number corresponding to each chunk
        """
        # 1) Combine all pages into one text block
        texts = [p["text"] for p in pages]
        combined = "\n\n".join(texts)

        # 2) Compute starting offset for each page
        page_offsets = []
        offset = 0
        for p in pages:
            page_offsets.append((offset, p["page_number"]))
            offset += len(p["text"]) + 2  # joining with "\n\n"

        # 3) Split into chunks
        chunks = self.splitter.split_text(combined)

        # 4) Map each chunk start offset → page_number
        page_numbers = []
        running_offset = 0
        for chunk in chunks:
            # Find which page this chunk belongs to
            page_num = self._find_page_for_offset(running_offset, page_offsets)
            page_numbers.append(page_num)
            running_offset += len(chunk)

        return chunks, page_numbers

    def _find_page_for_offset(self, offset, page_offsets):
        """
        Given a character offset in the combined text, return the page_number.
        """
        current_page = page_offsets[0][1]
        for start, page in page_offsets:
            if offset >= start:
                current_page = page
            else:
                break
        return current_page


# -----------------------------
# Embedder (SentenceTransformer)
# -----------------------------
class Embedder:
    """
    Uses SentenceTransformerEmbeddingFunction.
    This REQUIRES torch, but does NOT force GPU.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )

    def embed(self, texts):
        return self.embedding_function(texts)

    def embed_query(self, query):
        return self.embedding_function([query])[0]


# -----------------------------
# VectorStore (ChromaDB)
# -----------------------------
class VectorStore:
    def __init__(self, collection_name: str, embedding_function):
        # İstersen ileride PersistentClient'e geçebiliriz
        self.client = Client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

    def add_chunks(self, chunks, document_name, start_id=0, page_numbers=None):
        ids = [str(i + start_id) for i in range(len(chunks))]

        metadatas = [
            {
                "document": document_name,
                "chunk_index": i,
                "page_number": page_numbers[i] if page_numbers else None,
            }
            for i in range(len(chunks))
        ]

        self.collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        return len(ids)

    def query(self, text, k: int = 5, where=None):
        return self.collection.query(
            query_texts=[text],
            where=where,
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

    def count(self) -> int:
        return self.collection.count()


# -----------------------------
# RAG Pipeline
# -----------------------------
class RAGPipeline:
    def __init__(
        self,
        collection_name: str = COLLECTION_NAME,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        """
        High-level RAG pipeline:
        - loads PDF
        - chunks pages
        - embeds & indexes chunks into Chroma
        """

        # Varsayılan değerler (UI'dan gelirse override edilir)
        self.chunk_size = chunk_size
        self.overlap = overlap

        self.loader = PDFLoader()
        self.chunker = Chunker(chunk_size=self.chunk_size, overlap=self.overlap)
        self.embedder = Embedder()
        self.vstore = VectorStore(collection_name, self.embedder.embedding_function)
        self.offset = 0

    def index_pdf(self, file, chunk_size: int | None = None, overlap: int | None = None):
        """
        Indexes a PDF into the vector store.
        If chunk_size / overlap are provided, override current values.
        """

        # Update if new value comes from UI / caller
        if chunk_size is not None or overlap is not None:
            if chunk_size is not None:
                self.chunk_size = chunk_size
            if overlap is not None:
                self.overlap = overlap

            # Rebuild Chunker based on new values
            self.chunker = Chunker(
                chunk_size=self.chunk_size,
                overlap=self.overlap,
            )

        pages = self.loader.load_pdf(file)
        meta = self.loader.metadata
        doc_name = meta["document_name"]

        chunks, page_numbers = self.chunker.prepare_chunks(pages)

        count_new = self.vstore.add_chunks(
            chunks,
            document_name=doc_name,
            start_id=self.offset,
            page_numbers=page_numbers,
        )

        self.offset += count_new

        return {
            "document_name": doc_name,
            "page_count": meta["page_count"],
            "chunks_added": count_new,
            "total_chunks_in_db": self.vstore.count(),
        }

    def search(self, query: str, k: int = 5):
        return self.vstore.query(query, k)

    def search_in_document(self, query: str, doc_name: str, k: int = 5):
        return self.vstore.query(
            query,
            k=k,
            where={"document": doc_name},
        )
