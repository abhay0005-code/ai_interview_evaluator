# AI Interview Evaluator v9

## Interview Section Dropdown

The Admin panel now uses a **single-select Interview Section dropdown**.

Available sections:
- Generative AI / LLM fundamentals
- RAG
- AI agents
- AI system architecture
- Azure AI / Cloud
- Python / AI coding
- ML fundamentals
- Senior AI
- All

The administrator selects one section, saves the configuration, and can use **Apply Section to Interview** to populate the candidate-side interview section.

The selected section is persisted in `app/data/admin_settings.json`.

## Vector DB
Default: ChromaDB (Local)
Alternative local option: FAISS (Local)
Remote options: Qdrant and Pinecone

## LLMs
- Ollama
- Hugging Face Inference API
- Hugging Face / Transformers Local
- OpenAI / ChatGPT
- Anthropic / Claude
- Azure OpenAI

## Run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.main
```
