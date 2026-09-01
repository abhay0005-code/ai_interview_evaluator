import anthropic

class AnthropicProvider:
    def __init__(self,key,model):
        self.client=anthropic.Anthropic(api_key=key)
        self.model=model

    def generate(self,system,user):
        r=self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.1,
            system=system,
            messages=[{"role":"user","content":user}]
        )
        return r.content[0].text
