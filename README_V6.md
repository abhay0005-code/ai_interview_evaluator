# AI Interview Evaluator v6

## Added in v6
- Admin interview configuration
- Interview section selection
- Question count control
- LLM provider/model selection
- Vector DB selection
- Start / Skip / Submit / End Interview lifecycle
- Final outcome dashboard
- Question + answer + evaluation report
- PDF, Excel, CSV and JSON export
- Session close persistence
- RAG memory remains connected to the interview session

## Important
Configure `.env` before using paid LLMs or remote vector databases.
Default RAG is local ChromaDB.

## Run
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.main
```

## Default Vector DB
The application defaults to **ChromaDB (Local)**. **FAISS (Local)** is also available as a local option. Qdrant and Pinecone are optional remote backends.
