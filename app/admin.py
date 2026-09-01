import json
from pathlib import Path
from datetime import datetime

ADMIN_PATH = Path(__file__).resolve().parent / "data" / "admin_settings.json"
ADMIN_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULTS = {
    "sections": [
        "Generative AI / LLM fundamentals",
        "RAG",
        "AI agents",
        "AI system architecture",
        "Azure AI / Cloud",
        "Python / AI coding",
        "ML fundamentals",
        "Priority / Senior AI",
        "All",
    ],
    "difficulty": "Senior",
    "questions_per_session": 10,
    "adaptive": True,
    "time_limit_seconds": 180,
    "provider": "Ollama (Local)",
    "model": "llama3.1:8b",
    "vector_db": "ChromaDB (Local)",
    "rag_top_k": 5,
    "temperature": 0.2,
}

def load_settings():
    if not ADMIN_PATH.exists():
        save_settings(DEFAULTS)
        return DEFAULTS.copy()
    try:
        data = json.loads(ADMIN_PATH.read_text(encoding="utf-8"))
        merged = DEFAULTS.copy()
        merged.update(data)
        return merged
    except Exception:
        return DEFAULTS.copy()

def save_settings(settings):
    merged = DEFAULTS.copy()
    merged.update(settings)
    merged["updated_at"] = datetime.now().isoformat(timespec="seconds")
    ADMIN_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged
