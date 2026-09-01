import os
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .azure_provider import AzureProvider
from .ollama_provider import OllamaProvider

def build(provider_name, model):
    if provider_name=="openai":
        return OpenAIProvider(os.getenv("OPENAI_API_KEY",""),model)
    if provider_name=="anthropic":
        return AnthropicProvider(os.getenv("ANTHROPIC_API_KEY",""),model)
    if provider_name=="azure":
        return AzureProvider(
            os.getenv("AZURE_OPENAI_API_KEY",""),
            os.getenv("AZURE_OPENAI_ENDPOINT",""),
            os.getenv("AZURE_OPENAI_API_VERSION","2024-10-21"),
            os.getenv("AZURE_OPENAI_DEPLOYMENT","")
        )
    if provider_name=="ollama":
        return OllamaProvider(os.getenv("OLLAMA_BASE_URL","http://localhost:11434"),model)
    raise ValueError("Unsupported provider")
