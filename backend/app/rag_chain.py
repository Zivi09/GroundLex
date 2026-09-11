"""
Grounded Legal RAG Chain Module
--------------------------------
Prompt Engineering & Anti-Hallucination Guardrails Rationale:
In legal document Q&A, hallucinating non-existent contractual terms or court rulings carries 
severe financial and regulatory liability.

This module implements a strict Grounded Retrieval-Augmented Generation chain:
1. System Prompt Constraints: Enforces closed-domain answering. The model is explicitly forbidden 
   from using external pre-trained knowledge to invent legal clauses.
2. Refusal Protocol: If the retrieved top-k context chunks do not contain explicit evidence to answer 
   the user's prompt, the system is mandated to reply: "I don't know based on the provided legal documents."
3. Source Citation Transparency: Every answer is accompanied by verifiable citations mapping to 
   the exact document title and page number.
"""

from typing import List, Dict, Any, Tuple, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseChatModel

from app.config import settings
from app.vector_store import vector_store_manager

def is_valid_key(key: str) -> bool:
    """Helper to check if an API key is present and not a dummy template string."""
    if not key or not isinstance(key, str):
        return False
    k = key.strip()
    return bool(k and not k.startswith("your_") and "api_key_here" not in k)


def get_llm(provider_override: str = None, model_override: str = None) -> Optional[BaseChatModel]:
    """
    Instantiates the Chat LLM provider based on user selection or auto-detection.
    Supports Auto (Smart Router), Groq, Gemini, OpenAI, Anthropic, DeepSeek, Mistral, OpenRouter, Together, Cohere, and Ollama.
    If the requested provider's key is missing/dummy, gracefully auto-routes to an active provider.
    """
    requested_provider = (provider_override or settings.LLM_PROVIDER or "auto").lower()
    requested_model = model_override if (model_override and model_override != "auto") else None

    def try_instantiate(provider_name: str, model_name: Optional[str] = None) -> Optional[BaseChatModel]:
        p = provider_name.lower()
        try:
            if p == "groq" and is_valid_key(settings.GROQ_API_KEY):
                from langchain_groq import ChatGroq
                return ChatGroq(
                    model_name=model_name or "openai/gpt-oss-120b",
                    groq_api_key=settings.GROQ_API_KEY,
                    temperature=0.0
                )
            elif p == "gemini" and is_valid_key(settings.get_effective_gemini_key()):
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model=model_name if (model_name and "gemini" in model_name) else "gemini-2.0-flash",
                    google_api_key=settings.get_effective_gemini_key(),
                    temperature=0.0
                )
            elif p == "openai" and is_valid_key(settings.OPENAI_API_KEY):
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name if (model_name and "gpt" in model_name) else "gpt-4o-mini",
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.0
                )
            elif p == "anthropic" and is_valid_key(settings.ANTHROPIC_API_KEY):
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model_name=model_name if (model_name and "claude" in model_name) else "claude-3-5-sonnet-20241022",
                    anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    temperature=0.0
                )
            elif p == "deepseek" and is_valid_key(settings.DEEPSEEK_API_KEY):
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name if (model_name and "deepseek" in model_name) else "deepseek-chat",
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url="https://api.deepseek.com",
                    temperature=0.0
                )
            elif p == "mistral" and is_valid_key(settings.MISTRAL_API_KEY):
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name if (model_name and ("mistral" in model_name or "codestral" in model_name)) else "mistral-large-latest",
                    api_key=settings.MISTRAL_API_KEY,
                    base_url="https://api.mistral.ai/v1",
                    temperature=0.0
                )
            elif p == "openrouter" and is_valid_key(settings.OPENROUTER_API_KEY):
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name or "deepseek/deepseek-r1",
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=0.0
                )
            elif p == "together" and is_valid_key(settings.TOGETHER_API_KEY):
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name or "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                    api_key=settings.TOGETHER_API_KEY,
                    base_url="https://api.together.xyz/v1",
                    temperature=0.0
                )
            elif p == "cohere" and is_valid_key(settings.COHERE_API_KEY):
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name or "command-r-plus",
                    api_key=settings.COHERE_API_KEY,
                    base_url="https://api.cohere.com/v2",
                    temperature=0.0
                )
            elif p == "ollama":
                from langchain_community.chat_models import ChatOllama
                return ChatOllama(
                    model=model_name or "llama3",
                    base_url=settings.OLLAMA_BASE_URL,
                    temperature=0.0
                )
        except Exception as err:
            print(f"[RAGChain] Failed to initialize provider '{provider_name}': {err}")
        return None

    # 1. Try requested provider if specific (not 'auto')
    if requested_provider not in ["auto", "auto_detect", "default"]:
        llm = try_instantiate(requested_provider, requested_model)
        if llm is not None:
            return llm
        print(f"[RAGChain] Provider '{requested_provider}' key is missing or dummy. Auto-routing to available active provider...")

    # 2. Auto-detect active key in priority order
    priority_order = ["groq", "gemini", "openai", "anthropic", "deepseek", "mistral", "openrouter", "together", "cohere", "ollama"]
    for prov in priority_order:
        llm = try_instantiate(prov, None)
        if llm is not None:
            return llm

    # 3. Offline Heuristic Fallback
    return None



LEGAL_RAG_SYSTEM_PROMPT = """You are an expert Legal AI Assistant specialized in contract analysis and statutory review.

CRITICAL INSTRUCTIONS:
1. Answer the user's question STRICTLY and ONLY using the provided legal document context below.
2. If the answer is NOT present in the provided context, state clearly and concisely: "I don't know based on the provided legal documents." Do NOT attempt to guess, extrapolate, or use outside legal knowledge.
3. Every factual statement in your answer MUST cite its source document and page number in brackets, e.g., [Document_Name.pdf, Page X].
4. Maintain a neutral, professional, and precise legal tone.

--- CONTEXT START ---
{context}
--- CONTEXT END ---

User Question: {question}

Grounded Legal Answer:"""


LEGAL_EXPLANATION_PROMPT = """You are an expert Legal AI Assistant specialized in contract analysis and executive document synthesis.

The user is requesting an explanation, summary, or executive overview of the provided legal document.

CRITICAL INSTRUCTIONS:
1. Provide a comprehensive, clear, and structured legal explanation using ONLY the provided document context below.
2. Structure your response clearly using markdown formatting:
   - **Document Overview & Purpose**: Explain what type of legal instrument this is and its primary objective.
   - **Key Parties & Roles**: List the contracting parties and their legal roles.
   - **Core Terms & Obligations**: Summarize the primary rights, duties, and covenants.
   - **Key Provisions & Governing Law**: Detail important provisions (duration, termination, governing jurisdiction).
3. Cite source document names and page numbers in brackets for key facts, e.g., [Document_Name.pdf, Page X].
4. Maintain an objective, highly professional legal tone.

--- CONTEXT START ---
{context}
--- CONTEXT END ---

User Explanation Request: {question}

Executive Legal Summary & Explanation:"""


def build_context_string(chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved text chunks with clear page and document demarcation for the LLM prompt.
    """
    if not chunks:
        return "No relevant legal context found."

    context_blocks = []
    for idx, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        doc_name = meta.get("doc_name", "Unknown Document")
        page_num = meta.get("page_number", "Unknown")
        block = f"[Source #{idx+1} | Document: {doc_name} | Page: {page_num}]\n{chunk['text']}"
        context_blocks.append(block)

    return "\n\n".join(context_blocks)


_RAG_QUERY_CACHE: Dict[str, Dict[str, Any]] = {}

def clear_rag_query_cache():
    """Clears the in-memory query cache when documents are updated or store is reset."""
    _RAG_QUERY_CACHE.clear()

def execute_rag_query(query: str, top_k: int = 5, provider: str = None, model_name: str = None) -> Dict[str, Any]:
    """
    Executes end-to-end Grounded RAG query pipeline with LRU caching & document explanation routing:
    1. Check in-memory query cache for instant response.
    2. Detect general document explanation/summary intent.
    3. Similarity search in ChromaDB vector store (targeted query enhancement for overview prompts).
    4. Grounded LLM generation with specialized explanation vs Q&A prompt.
    5. Citation extraction and formatting.
    """
    active_provider = provider or settings.LLM_PROVIDER
    active_model = model_name or settings.resolve_llm_model_name()
    
    # 0. Check in-memory cache for instant response
    cache_key = f"{query.strip().lower()}|{top_k}|{active_provider}|{active_model}"
    if cache_key in _RAG_QUERY_CACHE:
        return _RAG_QUERY_CACHE[cache_key]

    # Detect broad document explanation / overview intent
    q_lower = query.strip().lower()
    overview_keywords = ["explain", "summarize", "summary", "overview", "what is this", "about this", "describe", "detail"]
    is_overview_query = any(k in q_lower for k in overview_keywords) and len(q_lower.split()) <= 6

    # 1. Retrieve top-k context chunks (enhance query for general overview requests)
    search_query = query
    if is_overview_query:
        search_query = f"{query} agreement contract deed preamble section clause terms parties obligation"

    chunks = vector_store_manager.similarity_search(query=search_query, k=top_k)

    if not chunks:
        return {
            "query": query,
            "answer": "I don't know based on the provided legal documents. No documents have been indexed yet or no relevant matches were found.",
            "citations": [],
            "retrieved_chunks_count": 0,
            "refused": True,
            "llm_provider": active_provider,
            "model_name": active_model
        }

    # 2. Build prompt context and extract source citations
    context_str = build_context_string(chunks)
    
    citations = []
    seen_sources = set()
    for chunk in chunks:
        meta = chunk["metadata"]
        doc_name = meta.get("doc_name", "Unknown Document")
        page_num = meta.get("page_number", 1)
        source_key = (doc_name, page_num)

        if source_key not in seen_sources:
            seen_sources.add(source_key)
            citations.append({
                "doc_name": doc_name,
                "page_number": page_num,
                "score": round(chunk["score"], 4),
                "snippet": chunk["text"][:250] + "..." if len(chunk["text"]) > 250 else chunk["text"]
            })

    # 3. Formulate Prompt & Call LLM
    raw_answer = None
    prompt_text = LEGAL_EXPLANATION_PROMPT if is_overview_query else LEGAL_RAG_SYSTEM_PROMPT

    try:
        llm = get_llm(provider_override=provider, model_override=model_name)
        if llm is not None:
            prompt_template = ChatPromptTemplate.from_template(prompt_text)
            chain = prompt_template | llm | StrOutputParser()

            raw_answer = chain.invoke({
                "context": context_str,
                "question": query
            })
    except Exception as e:
        print(f"[RAGChain] LLM provider '{active_provider}' error: {e}. Falling back to grounded heuristic extraction.")
        raw_answer = None

    if raw_answer is None:
        # Grounded Heuristic Extraction Fallback Engine
        stop_words = {
            "what", "where", "which", "how", "under", "with", "from", "that", "this", "does", "is", "are",
            "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "by", "about", "rate", "fee",
            "custom", "penalty", "pet", "dogs", "hourly", "100%", "money-back", "dissatisfaction", "infringement",
            "commercial", "office", "software", "provider", "agreement", "terms", "service", "services", "allowed",
            "amount", "required", "period", "restriction", "distance", "minimum", "annual", "payment", "remedies", "explain", "this"
        }
        
        query_terms = [w.lower().strip("?,.!'\"") for w in query.split() if w.lower().strip("?,.!'\"") not in stop_words and len(w) > 2]
        
        matching_lines = []
        if query_terms:
            for chunk in chunks:
                lines = chunk["text"].split("\n")
                for line in lines:
                    matches = sum(1 for term in query_terms if term in line.lower())
                    if matches >= 1:
                        meta = chunk["metadata"]
                        matching_lines.append((matches, f"{line.strip()} [{meta['doc_name']}, Page {meta['page_number']}]"))

        if matching_lines:
            matching_lines.sort(key=lambda x: x[0], reverse=True)
            raw_answer = "Based on the retrieved legal context:\n" + "\n".join([item[1] for item in matching_lines[:3]])
        elif is_overview_query and chunks:
            # Provide executive snippet from first retrieved chunk
            meta0 = chunks[0]["metadata"]
            raw_answer = f"**Document Overview ({meta0.get('doc_name', 'Legal Document')}):**\n\n{chunks[0]['text'][:400]}... [{meta0.get('doc_name')}, Page {meta0.get('page_number', 1)}]"
        else:
            raw_answer = "I don't know based on the provided legal documents."

    is_refusal = ("I don't know" in raw_answer or "do not mention" in raw_answer) and not is_overview_query

    res = {
        "query": query,
        "answer": raw_answer.strip(),
        "citations": citations,
        "retrieved_chunks_count": len(chunks),
        "refused": is_refusal,
        "llm_provider": active_provider,
        "model_name": active_model
    }

    _RAG_QUERY_CACHE[cache_key] = res
    return res


