import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "app/data/interview.db")
CHROMA_PATH = os.getenv("CHROMA_PATH", "app/data/chroma")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_ACCESS_MODE = os.getenv("ADMIN_ACCESS_MODE", "protected").strip().lower()

PROVIDERS = {
    "ChatGPT / OpenAI": "openai",
    "Claude / Anthropic": "anthropic",
    "Azure OpenAI": "azure",
    "Ollama / Open Source": "ollama",
}

MODELS = {
    "openai": [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gpt-4.1",
    ],
    "anthropic": [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
    ],
    "azure": [
        "Use Azure deployment name from .env",
    ],
    "ollama": [
        "llama3.1:8b",
        "llama3.1:70b",
        "llama3.2:3b",
        "llama3.2:1b",
        "qwen2.5:7b",
        "qwen2.5:14b",
        "mistral:7b",
        "gemma3:4b",
        "deepseek-r1:7b",
    ],
}


VECTOR_PROVIDERS = {
    "ChromaDB (Local)": "chroma",
    "FAISS (Local)": "faiss",
    "Qdrant": "qdrant",
    "Pinecone": "pinecone",
}
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "ai_interview_memory")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "ai-interview-memory")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

DEFAULT_VECTOR_DB = "chroma"


# Comprehensive open-source/local LLM catalog.
# Models are selectable in the Admin panel when using Ollama or another compatible
# OpenAI-compatible local endpoint. Pull the model with Ollama before use.
OPEN_SOURCE_MODELS = {
    "Ollama (Local)": [
        "llama3.3:70b",
        "llama3.1:8b",
        "llama3.1:70b",
        "llama3.2:3b",
        "llama3.2:1b",
        "qwen2.5:7b",
        "qwen2.5:14b",
        "qwen2.5:32b",
        "qwen2.5:72b",
        "qwen2.5-coder:7b",
        "qwen2.5-coder:14b",
        "deepseek-r1:7b",
        "deepseek-r1:14b",
        "deepseek-r1:32b",
        "deepseek-r1:70b",
        "deepseek-coder-v2:16b",
        "mistral:7b",
        "mixtral:8x7b",
        "gemma2:9b",
        "gemma3:4b",
        "gemma3:12b",
        "phi4:14b",
        "phi3:mini",
        "command-r:35b",
        "nous-hermes2:10.7b",
    ],
    "Hugging Face / Transformers (Local)": [
        "meta-llama/Llama-3.1-8B-Instruct",
        "meta-llama/Llama-3.1-70B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-14B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "Qwen/Qwen2.5-Coder-7B-Instruct",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "microsoft/Phi-4-mini-instruct",
        "google/gemma-3-4b-it",
    ],
}
