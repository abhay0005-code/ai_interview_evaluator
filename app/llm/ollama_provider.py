import json
import urllib.request

class OllamaProvider:
    def __init__(self,url,model):
        self.url=url.rstrip("/")
        self.model=model

    def generate(self,system,user):
        payload=json.dumps({
            "model":self.model,
            "stream":False,
            "format":"json",
            "options":{"temperature":0.1},
            "messages":[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ]
        }).encode()
        req=urllib.request.Request(
            self.url+"/api/chat",
            data=payload,
            headers={"Content-Type":"application/json"}
        )
        with urllib.request.urlopen(req,timeout=180) as response:
            return json.loads(response.read())["message"]["content"]
