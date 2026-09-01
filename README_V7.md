# AI Interview Evaluator v7

## Admin panel
The application now has a dedicated **🔐 Admin** tab where an administrator can configure:
- interview sections
- difficulty
- questions per session
- adaptive/RAG questioning
- per-question time limit
- LLM provider
- LLM model
- default vector database
- RAG Top-K
- temperature

Settings are persisted in `app/data/admin_settings.json`.

## LLM providers
### Open source / local
- Ollama
- Hugging Face / Transformers
- Llama 3.x
- Qwen 2.5
- Qwen Coder
- DeepSeek R1 / DeepSeek Coder
- Mistral / Mixtral
- Gemma
- Phi
- Command R
- Nous Hermes

### Paid / hosted
- OpenAI / ChatGPT
- Anthropic / Claude
- Azure OpenAI

The open-source model list is selectable from the Admin panel. Ollama is the easiest local option.

## Vector DB
Default: **ChromaDB (Local)**

Also supported:
- FAISS (Local)
- Qdrant
- Pinecone

## Run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.main
```

For Ollama, install Ollama separately and pull the model you select, for example:
```bash
ollama pull llama3.1:8b
```
