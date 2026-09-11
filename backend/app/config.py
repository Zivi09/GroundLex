import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings for Legal Document RAG Assistant.
    Configurable via environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LLM & Embedding configuration
    LLM_PROVIDER: Literal[
        "openai", "gemini", "groq", "anthropic", "deepseek", "mistral", "openrouter", "together", "cohere", "ollama"
    ] = Field(
        default="openai",
        description="LLM provider: 'openai', 'gemini', 'groq', 'anthropic', 'deepseek', 'mistral', 'openrouter', 'together', 'cohere', or 'ollama'"
    )
    
    EMBEDDING_PROVIDER: Literal["openai", "huggingface"] = Field(
        default="huggingface",
        description="Embedding provider: 'huggingface' (free local) or 'openai'"
    )

    # API Keys
    OPENAI_API_KEY: str = Field(default="")
    GOOGLE_API_KEY: str = Field(default="")  # Used for Gemini
    GEMINI_API_KEY: str = Field(default="")  # Alternative key name for Gemini
    GROQ_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")
    DEEPSEEK_API_KEY: str = Field(default="")
    MISTRAL_API_KEY: str = Field(default="")
    OPENROUTER_API_KEY: str = Field(default="")
    TOGETHER_API_KEY: str = Field(default="")
    COHERE_API_KEY: str = Field(default="")

    # Ollama settings
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")

    # Custom Model Names (defaults set per provider if left blank)
    MODEL_NAME: str = Field(default="")

    # Ingestion & Chunking parameters
    CHUNK_SIZE: int = Field(default=1200, description="Target chunk size in characters")
    CHUNK_OVERLAP: int = Field(default=150, description="Overlap between consecutive chunks")
    TOP_K_RESULTS: int = Field(default=5, description="Number of context chunks to retrieve")

    # Storage paths
    CHROMA_DB_DIR: str = Field(
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db"),
        description="Local ChromaDB storage directory"
    )
    SAMPLE_DOCS_DIR: str = Field(
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_docs"),
        description="Directory containing sample legal PDFs"
    )

    def get_effective_gemini_key(self) -> str:
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY or os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))

    def resolve_llm_model_name(self) -> str:
        if self.MODEL_NAME:
            return self.MODEL_NAME
        defaults = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-2.0-flash",
            "groq": "llama-3.3-70b-versatile",
            "anthropic": "claude-3-5-sonnet-20241022",
            "deepseek": "deepseek-chat",
            "mistral": "mistral-large-latest",
            "openrouter": "deepseek/deepseek-r1",
            "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "cohere": "command-r-plus",
            "ollama": "llama3"
        }
        return defaults.get(self.LLM_PROVIDER, "gpt-4o-mini")

settings = Settings()

