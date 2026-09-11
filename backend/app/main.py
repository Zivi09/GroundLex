"""
GroundLex AI - FastAPI Application Entry Point
-----------------------------------------------
Provides REST API endpoints for document ingestion, grounded RAG Q&A query processing,
sample document initialization, and index management.
"""

import os
import shutil
import tempfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.ingestion import process_pdf_file
from app.vector_store import vector_store_manager
from app.rag_chain import execute_rag_query, clear_rag_query_cache
from app.conversations_store import conversations_store
from sample_docs.generate_samples import generate_all_samples, SAMPLE_DIR


app = FastAPI(
    title="GroundLex AI API",
    description="Production-Grade Grounded Retrieval-Augmented Generation for Legal Contracts & Statutory Analysis",
    version="1.0.0"
)

# Enable CORS for local Vite frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class QueryRequest(BaseModel):
    query: str = Field(..., example="What is the security deposit amount in the lease agreement?")
    top_k: Optional[int] = Field(default=5, ge=1, le=15)
    provider: Optional[str] = Field(default=None)
    model_name: Optional[str] = Field(default=None)
    conversation_id: Optional[str] = Field(default=None)


class CitationModel(BaseModel):
    doc_name: str
    page_number: int
    score: float
    snippet: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[CitationModel]
    retrieved_chunks_count: int
    refused: bool
    llm_provider: str
    model_name: str
    conversation_id: str


class TitleUpdateRequest(BaseModel):
    title: str = Field(..., example="New Custom Conversation Title")


class DocumentSummary(BaseModel):
    doc_name: str
    chunk_count: int
    total_pages: int


class HealthStatus(BaseModel):
    status: str
    llm_provider: str
    model_name: str
    embedding_provider: str
    indexed_documents_count: int


# --- API Endpoints ---

@app.get("/api/health", response_model=HealthStatus)
def get_health():
    """
    Returns system status, active LLM provider, and vector store stats.
    """
    docs = vector_store_manager.list_documents()
    return HealthStatus(
        status="online",
        llm_provider=settings.LLM_PROVIDER,
        model_name=settings.resolve_llm_model_name(),
        embedding_provider=settings.EMBEDDING_PROVIDER,
        indexed_documents_count=len(docs)
    )


@app.get("/api/documents", response_model=List[DocumentSummary])
def list_indexed_documents():
    """
    Lists all legal documents currently indexed in ChromaDB with page & chunk metrics.
    """
    return vector_store_manager.list_documents()


@app.post("/api/upload")
async def upload_pdf_file(file: UploadFile = File(...)):
    """
    Uploads a legal PDF document, parses pages, performs clause-aware chunking,
    and indexes the vector embeddings in ChromaDB.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks = process_pdf_file(temp_file_path)
        if not chunks:
            raise HTTPException(status_code=400, detail="No readable text extracted from PDF file.")

        added_count = vector_store_manager.add_chunks(chunks)
        clear_rag_query_cache()

        return {
            "status": "success",
            "filename": file.filename,
            "chunks_indexed": added_count,
            "message": f"Successfully indexed '{file.filename}' into vector store ({added_count} clause chunks)."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest PDF document: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



@app.post("/api/query", response_model=QueryResponse)
def query_rag_assistant(payload: QueryRequest):
    """
    Executes grounded RAG pipeline for user question.
    Returns verifiable answer with document name and page citations.
    Persists query and response into conversation history store.
    """
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    res = execute_rag_query(
        query=payload.query,
        top_k=payload.top_k,
        provider=payload.provider,
        model_name=payload.model_name
    )

    if payload.conversation_id:
        conv = conversations_store.add_message_to_conversation(
            conv_id=payload.conversation_id,
            user_query=payload.query,
            assistant_response=res
        )
        conv_id = conv["id"] if conv else payload.conversation_id
    else:
        conv = conversations_store.create_conversation(
            title=payload.query[:60],
            user_query=payload.query,
            assistant_response=res
        )
        conv_id = conv["id"]

    res["conversation_id"] = conv_id
    return res


# --- Conversation History & Search Endpoints ---

@app.get("/api/conversations")
def list_conversations():
    """
    Returns list of all saved conversation threads.
    """
    return conversations_store.list_conversations()


@app.get("/api/conversations/search")
def search_conversations(q: str = ""):
    """
    Searches past conversations by title or message contents.
    """
    return conversations_store.search(q)


@app.get("/api/conversations/{conversation_id}")
def get_conversation_details(conversation_id: str):
    """
    Retrieves full conversation details including message thread and citations.
    """
    conv = conversations_store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation thread not found.")
    return conv


@app.patch("/api/conversations/{conversation_id}")
def update_conversation_title(conversation_id: str, payload: TitleUpdateRequest):
    """
    Renames conversation title.
    """
    conv = conversations_store.update_title(conversation_id, payload.title)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation thread not found.")
    return conv


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    """
    Deletes conversation thread.
    """
    success = conversations_store.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation thread not found.")
    return {"status": "success", "message": "Conversation deleted successfully."}


@app.post("/api/load-samples")
def load_sample_documents():
    """
    Generates and ingests 3 realistic sample legal PDFs (Mutual NDA, Lease Agreement, SaaS Terms).
    Allows instant out-of-the-box demo testing.
    """
    try:
        if not os.path.exists(SAMPLE_DIR) or not os.listdir(SAMPLE_DIR):
            generate_all_samples()

        sample_files = [f for f in os.listdir(SAMPLE_DIR) if f.endswith(".pdf")]
        if not sample_files:
            generate_all_samples()
            sample_files = [f for f in os.listdir(SAMPLE_DIR) if f.endswith(".pdf")]

        total_chunks_added = 0
        ingested_docs = []

        for sample_file in sample_files:
            pdf_path = os.path.join(SAMPLE_DIR, sample_file)
            chunks = process_pdf_file(pdf_path)
            added_count = vector_store_manager.add_chunks(chunks)
            total_chunks_added += added_count
            ingested_docs.append(sample_file)

        clear_rag_query_cache()

        return {
            "status": "success",
            "message": f"Successfully loaded {len(ingested_docs)} sample legal documents ({total_chunks_added} total chunks).",
            "documents": ingested_docs,
            "total_chunks": total_chunks_added
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading sample documents: {str(e)}")


@app.post("/api/reset")
def reset_vector_store():
    """
    Clears all indexed documents from ChromaDB vector store.
    """
    vector_store_manager.reset()
    clear_rag_query_cache()
    return {"status": "success", "message": "Vector store database reset successfully."}


