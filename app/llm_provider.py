import os, json, re, time
from typing import Any, Dict, Optional

def _clean_json(text: str):
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S | re.I)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            pass
    m = re.search(r"(\{.*\})", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            return None
    return None

class LLMError(RuntimeError):
    pass

class LLMClient:
    def __init__(self, provider: str, model: str, temperature: float = 0.2):
        self.provider = provider
        self.model = model
        self.temperature = temperature

    def generate(self, prompt: str) -> str:
        p = self.provider.lower()
        last = None
        for attempt in range(3):
            try:
                if "hugging" in p:
                    return self._huggingface(prompt)
                if "ollama" in p:
                    return self._ollama(prompt)
                if "anthropic" in p or "claude" in p:
                    return self._anthropic(prompt)
                if "azure" in p:
                    return self._azure(prompt)
                if "openai" in p or "chatgpt" in p:
                    return self._openai(prompt)
                raise LLMError(f"Unsupported LLM provider: {self.provider}")
            except Exception as e:
                last = e
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
        raise LLMError(f"{self.provider}/{self.model} failed: {last}")

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        raw = self.generate(prompt)
        data = _clean_json(raw)
        if not isinstance(data, dict):
            raise LLMError(f"LLM returned invalid JSON. Raw response: {raw[:500]}")
        return data

    def _ollama(self, prompt):
        import requests
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        r = requests.post(
            f"{base}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False,
                  "options": {"temperature": self.temperature}},
            timeout=180,
        )
        r.raise_for_status()
        data = r.json()
        out = data.get("response")
        if not out:
            raise LLMError("Ollama returned no response.")
        return out

    def _huggingface(self, prompt):
        token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
        if not token:
            raise LLMError("HUGGINGFACEHUB_API_TOKEN/HF_TOKEN is not configured.")
        # Uses Hugging Face Inference API; compatible with supported text-generation/chat models.
        import requests
        model = self.model
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1200,
                "temperature": self.temperature,
                "return_full_text": False,
            }
        }
        r = requests.post(url, headers=headers, json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and data.get("error"):
            raise LLMError(data["error"])
        if isinstance(data, list) and data:
            item = data[0]
            if isinstance(item, dict):
                out = item.get("generated_text") or item.get("text")
                if out: return out
        if isinstance(data, dict):
            out = data.get("generated_text") or data.get("text")
            if out: return out
        raise LLMError("Hugging Face returned no generated text.")

    def _openai(self, prompt):
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("OPENAI_API_KEY is not configured.")
        client = OpenAI(api_key=key)
        r = client.chat.completions.create(
            model=self.model, temperature=self.temperature,
            messages=[{"role":"user","content":prompt}]
        )
        out = r.choices[0].message.content if r.choices else None
        if not out: raise LLMError("OpenAI returned no response.")
        return out

    def _anthropic(self, prompt):
        import anthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key: raise LLMError("ANTHROPIC_API_KEY is not configured.")
        client = anthropic.Anthropic(api_key=key)
        r = client.messages.create(
            model=self.model, max_tokens=1200, temperature=self.temperature,
            messages=[{"role":"user","content":prompt}]
        )
        out = "".join(getattr(x, "text", "") for x in r.content)
        if not out: raise LLMError("Anthropic returned no response.")
        return out

    def _azure(self, prompt):
        from openai import AzureOpenAI
        key=os.getenv("AZURE_OPENAI_API_KEY")
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        version=os.getenv("AZURE_OPENAI_API_VERSION","2024-10-21")
        deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT") or self.model
        if not key or not endpoint:
            raise LLMError("Azure OpenAI credentials are not configured.")
        client=AzureOpenAI(api_key=key, azure_endpoint=endpoint, api_version=version)
        r=client.chat.completions.create(
            model=deployment, temperature=self.temperature,
            messages=[{"role":"user","content":prompt}]
        )
        out=r.choices[0].message.content if r.choices else None
        if not out: raise LLMError("Azure OpenAI returned no response.")
        return out
