"""
Vector Store Management Module
-------------------------------
Architectural Abstraction Rationale:
To maintain clean separation of concerns, the retrieval layer is abstracted via VectorStoreManager.
For this zero-config MVP, ChromaDB is used locally as an embedded vector database.
Because retrieval logic is decoupled from ChromaDB specifics, swapping this implementation to a hosted
vector store (e.g., Pinecone, Qdrant Cloud, or Supabase pgvector) requires zero changes to the RAG chain.

Embeddings Strategy:
- Default: HuggingFace 'sentence-transformers/all-MiniLM-L6-v2' (Zero API cost, works offline/without key).
- OpenAI: 'text-embedding-3-small' if `EMBEDDING_PROVIDER="openai"` and `OPENAI_API_KEY` is present.
"""

import os
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.config import settings

def get_embedding_function() -> Embeddings:
    """
    Resolves the embedding provider based on application configuration and key availability.
    """
    if settings.EMBEDDING_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )
        except Exception as e:
            print(f"[VectorStore] Failed to initialize OpenAI Embeddings ({e}). Falling back to local HuggingFace model.")

    # Fallback to local HuggingFace embeddings
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


class VectorStoreManager:
    def __init__(self):
        self.embeddings = get_embedding_function()
        self.persist_directory = settings.CHROMA_DB_DIR
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.vector_store = Chroma(
            collection_name="legal_documents",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Converts extracted chunk dicts into LangChain Documents and batch-upserts into ChromaDB.
        """
        documents = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk["text"],
                metadata=chunk["metadata"],
                id=chunk["chunk_id"]
            )
            documents.append(doc)

        if documents:
            # Upsert into ChromaDB
            ids = [doc.id for doc in documents]
            self.vector_store.add_documents(documents=documents, ids=ids)
        return len(documents)

    def similarity_search(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Performs similarity search with relevance scores and returns document context dicts.
        """
        k_val = k if k is not None else settings.TOP_K_RESULTS
        
        # Retrieve top-k documents with distance scores
        results_with_scores = self.vector_store.similarity_search_with_score(query=query, k=k_val)

        context_list = []
        for doc, score in results_with_scores:
            context_list.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)  # Lower is closer in L2 distance / higher similarity
            })

        return context_list

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieves a summary of indexed documents, total chunks per document, and page counts.
        """
        try:
            collection = self.vector_store._collection
            get_res = collection.get(include=["metadatas"])
            metadatas = get_res.get("metadatas", [])
            
            doc_summary: Dict[str, Dict[str, Any]] = {}
            for meta in metadatas:
                if not meta:
                    continue
                doc_name = meta.get("doc_name", "Unknown Document")
                page_num = meta.get("page_number", 1)
                
                if doc_name not in doc_summary:
                    doc_summary[doc_name] = {
                        "doc_name": doc_name,
                        "chunk_count": 0,
                        "pages": set()
                    }
                doc_summary[doc_name]["chunk_count"] += 1
                doc_summary[doc_name]["pages"].add(page_num)

            formatted_list = []
            for doc_name, summary in doc_summary.items():
                formatted_list.append({
                    "doc_name": doc_name,
                    "chunk_count": summary["chunk_count"],
                    "total_pages": len(summary["pages"])
                })

            return formatted_list
        except Exception as e:
            print(f"[VectorStore] Error listing documents: {e}")
            return []

    def delete_document(self, doc_name: str) -> bool:
        """
        Deletes all chunks associated with a specific document name.
        """
        try:
            collection = self.vector_store._collection
            get_res = collection.get(where={"doc_name": doc_name})
            ids_to_delete = get_res.get("ids", [])
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
            return True
        except Exception as e:
            print(f"[VectorStore] Failed to delete document {doc_name}: {e}")
            return False

    def reset(self):
        """
        Clears all stored documents from the collection.
        """
        try:
            collection = self.vector_store._collection
            all_ids = collection.get().get("ids", [])
            if all_ids:
                collection.delete(ids=all_ids)
        except Exception as e:
            print(f"[VectorStore] Failed to reset vector store: {e}")

# Global singleton instance for application reuse
vector_store_manager = VectorStoreManager()
