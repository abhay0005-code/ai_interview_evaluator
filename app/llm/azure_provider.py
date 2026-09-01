from openai import AzureOpenAI

class AzureProvider:
    def __init__(self,key,endpoint,version,deployment):
        self.client=AzureOpenAI(
            api_key=key,
            azure_endpoint=endpoint,
            api_version=version
        )
        self.deployment=deployment

    def generate(self,system,user):
        r=self.client.chat.completions.create(
            model=self.deployment,
            temperature=0.1,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ]
        )
        return r.choices[0].message.content
