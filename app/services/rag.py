import asyncio
import os
from typing import List, Optional

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.core.logging import logger

class MockEmbeddings(Embeddings):
    """Mock embeddings for testing without an API key."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Return a fixed size dummy vector for each text
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return [0.1] * 1536

class RAGService:
    """Service for handling Retrieval Augmented Generation from local files."""

    def __init__(self, docs_dir: str = "data/company_docs", index_path: str = "data/faiss_index"):
        self.docs_dir = docs_dir
        self.index_path = index_path
        self.vector_store: Optional[FAISS] = None
        
        # Determine which embeddings to use
        embed_model = os.getenv("OLLAMA_EMBED_MODEL", settings.LONG_TERM_MEMORY_EMBEDDER_MODEL)
        
        try:
            self.embeddings = OllamaEmbeddings(
                model=embed_model,
                base_url=settings.LLM_BASE_URL,
            )
            logger.info(
                "rag_embeddings_initialized",
                provider="ollama",
                model=embed_model
            )
        except Exception as e:
            logger.error("rag_embeddings_init_failed", error=str(e))
            self.embeddings = MockEmbeddings()

        # Initial loading is fine as sync in constructor, 
        # but we'll provide an async init for runtime.
        self._initialize_vector_store_sync()

    def _initialize_vector_store_sync(self, force_rebuild: bool = False):
        """Build or load the vector store (sync version for startup)."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

            if not force_rebuild and os.path.exists(self.index_path):
                logger.info("rag_loading_existing_index", path=self.index_path)
                try:
                    self.vector_store = FAISS.load_local(
                        self.index_path, 
                        self.embeddings,
                        allow_dangerous_deserialization=True 
                    )
                    # Sanity check dimension to ensure compatibility with new model
                    test_embed = self.embeddings.embed_query("test")
                    if self.vector_store.index.d != len(test_embed):
                        logger.warning(
                            "rag_dimension_mismatch", 
                            index_dim=self.vector_store.index.d, 
                            embed_dim=len(test_embed)
                        )
                        raise ValueError("Dimension mismatch")
                    return
                except Exception as e:
                    logger.warning("rag_failed_to_load_index_rebuilding", error=str(e))

            if not os.path.exists(self.docs_dir):
                logger.warning("rag_docs_dir_not_found", path=self.docs_dir)
                os.makedirs(self.docs_dir, exist_ok=True)
                return

            logger.info("rag_loading_documents", path=self.docs_dir)
            loader = DirectoryLoader(
                self.docs_dir, 
                glob="**/*.md", 
                loader_cls=TextLoader,
                loader_kwargs={'encoding': 'utf-8'}
            )
            documents = loader.load()

            if not documents:
                logger.warning("rag_no_documents_found")
                return

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=100
            )
            splits = text_splitter.split_documents(documents)

            self.vector_store = FAISS.from_documents(splits, self.embeddings)
            self.vector_store.save_local(self.index_path)
            
            logger.info("rag_vector_store_initialized", doc_count=len(documents), split_count=len(splits))

        except Exception as e:
            logger.error("rag_initialization_failed", error=str(e))

    async def initialize_vector_store(self, force_rebuild: bool = False):
        """Async wrapper for initializing vector store."""
        return await asyncio.to_thread(self._initialize_vector_store_sync, force_rebuild=force_rebuild)

    async def reindex(self):
        """Force a rebuild of the vector store (async)."""
        logger.info("rag_reindexing_triggered")
        await self.initialize_vector_store(force_rebuild=True)
        return {"status": "success", "message": "Index rebuilt successfully."}

    async def query(self, query: str, k: int = 3) -> str:
        """Search for relevant content in the vector store (async)."""
        if self.vector_store is None:
            return "Internal Error: Knowledge base not initialized."

        try:
            # Running heavy similarity search in thread to avoid blocking loop
            docs = await asyncio.to_thread(self.vector_store.similarity_search, query, k=k)
            
            if not docs:
                return "No matching information found in company records."

            enhanced_results = []
            for doc in docs:
                source = os.path.basename(doc.metadata.get('source', 'unknown'))
                enhanced_results.append(f"Source: {source}\nContent: {doc.page_content}")

            return "\n\n---\n\n".join(enhanced_results)
        except Exception as e:
            logger.error("rag_query_failed", query=query, error=str(e))
            return f"Error searching documents: {str(e)}"

# Singleton instance
rag_service = RAGService()
