# AI Interview Evaluator v8

## Fixed
- `'NoneType' object is not subscriptable` protection around question/evaluation results
- invalid/malformed LLM JSON handling
- retry with backoff for provider failures
- useful error messages in the Gradio UI

## Hugging Face
Added two choices:
1. **Hugging Face (Inference API)** — uses `HUGGINGFACEHUB_API_TOKEN` or `HF_TOKEN`.
2. **Hugging Face / Transformers (Local)** — model names are available in the Admin dropdown.

Example `.env`:
```text
HUGGINGFACEHUB_API_TOKEN=hf_xxxxxxxxx
```

## Local/free recommended stack
**Ollama + Qwen/Llama/DeepSeek + ChromaDB (Local)**

## Run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.main
```
