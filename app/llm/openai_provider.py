from openai import OpenAI

class OpenAIProvider:
    def __init__(self,key,model):
        self.client=OpenAI(api_key=key)
        self.model=model

    def generate(self,system,user):
        r=self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ]
        )
        return r.choices[0].message.content
