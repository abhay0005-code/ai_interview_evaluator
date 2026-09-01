# AI Interview Evaluator v2

A polished Gradio AI interview practice application with:
- Pre-populated SQLite question database
- 100+ AI interview questions across the requested sections
- Question selector that is guaranteed to populate after startup
- LLM dropdown with OpenAI/ChatGPT, Claude, Azure OpenAI and Ollama/open-source models
- Candidate answer timer
- LLM scoring and feedback
- Adaptive next-question selection
- ChromaDB RAG memory for previous answers
- Dashboard/history
- Seed/reset question database controls

## Quick start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
python -m app.main
```

The app will show a Gradio URL.

### Ollama
Install Ollama and pull a model:
```bash
ollama pull llama3.1:8b
```

### Paid providers
Configure the appropriate API key in `.env`.

The UI lets you select:
- ChatGPT/OpenAI
- Claude
- Azure OpenAI
- Ollama / Open-source

The model dropdown changes based on the selected provider.

## Important
The question DB is created and seeded automatically on startup. Use the **Database** tab to inspect/reset the question bank.


## RAG / Vector database
Every submitted answer is persisted to SQLite and to the selected vector database as an interview-memory document containing the question, candidate answer, score and evaluation. Before evaluating the next answer, the RAG retriever fetches similar previous interview attempts and supplies them to the evaluator.

Supported vector stores:
- ChromaDB (local, default)
- FAISS (local)
- Qdrant
- Pinecone

Configure Qdrant/Pinecone credentials in `.env` before selecting them. Local ChromaDB is persistent under `app/data/chroma`.

The **Question Database** tab includes a **Stored RAG Interview Memory** section so you can verify that submitted answers were actually persisted.
