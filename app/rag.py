from pathlib import Path
import json
from .config import CHROMA_PATH, QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION
from .config import PINECONE_API_KEY, PINECONE_INDEX, EMBEDDING_MODEL

class EmbeddingEngine:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(EMBEDDING_MODEL)
    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype("float32")

class ChromaStore:
    def __init__(self):
        import chromadb
        Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection("interview_memory")
    def add(self, record_id, text, metadata):
        self.collection.upsert(ids=[str(record_id)], documents=[text], metadatas=[metadata])
    def retrieve(self, query, k=5, session_ids=None):
        n=self.collection.count()
        if not n: return []
        where = {"session_id": {"$in": [str(value) for value in session_ids]}} if session_ids else None
        r=self.collection.query(query_texts=[query], n_results=min(k,n), where=where, include=["documents","metadatas","distances"])
        return [{"text":d,"metadata":m,"distance":dist} for d,m,dist in zip(r.get("documents",[[]])[0],r.get("metadatas",[[]])[0],r.get("distances",[[]])[0])]
    def count(self): return self.collection.count()
    def all(self, limit=100):
        n=min(limit,self.collection.count())
        if not n: return []
        r=self.collection.get(limit=n, include=["documents","metadatas"])
        return [{"text":d,"metadata":m} for d,m in zip(r.get("documents",[]),r.get("metadatas",[]))]

class FaissStore:
    def __init__(self):
        import faiss, json
        self.faiss=faiss; base=Path(CHROMA_PATH).parent
        self.index_path=base/'faiss.index'; self.meta_path=base/'faiss_metadata.json'; self.embedder=EmbeddingEngine()
        if self.index_path.exists() and self.meta_path.exists():
            self.index=faiss.read_index(str(self.index_path)); self.meta=json.loads(self.meta_path.read_text())
        else:
            self.index=faiss.IndexFlatIP(384); self.meta=[]
    def _save(self):
        self.faiss.write_index(self.index,str(self.index_path)); self.meta_path.write_text(json.dumps(self.meta))
    def add(self,record_id,text,metadata):
        self.index.add(self.embedder.encode([text])); self.meta.append({"id":str(record_id),"text":text,"metadata":metadata}); self._save()
    def retrieve(self,query,k=5):
        if not self.index.ntotal:return []
        scores,ids=self.index.search(self.embedder.encode([query]),min(k,self.index.ntotal)); out=[]
        for score,idx in zip(scores[0],ids[0]):
            if 0<=idx<len(self.meta):
                x=self.meta[idx]; out.append({"text":x["text"],"metadata":x["metadata"],"distance":float(1-score)})
        return out
    def count(self): return self.index.ntotal
    def all(self, limit=100):
        return [{"text": item["text"], "metadata": item["metadata"]} for item in self.meta[:limit]]

class QdrantStore:
    def __init__(self):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance,VectorParams
        if not QDRANT_URL: raise ValueError("QDRANT_URL is not configured")
        self.client=QdrantClient(url=QDRANT_URL,api_key=QDRANT_API_KEY or None); self.name=QDRANT_COLLECTION; self.embedder=EmbeddingEngine()
        if self.name not in [x.name for x in self.client.get_collections().collections]:
            self.client.create_collection(collection_name=self.name,vectors_config=VectorParams(size=384,distance=Distance.COSINE))
    def add(self,record_id,text,metadata):
        from qdrant_client.models import PointStruct
        self.client.upsert(collection_name=self.name,points=[PointStruct(id=int(record_id),vector=self.embedder.encode([text])[0].tolist(),payload={"text":text,**metadata})])
    def retrieve(self,query,k=5):
        result=self.client.query_points(collection_name=self.name,query=self.embedder.encode([query])[0].tolist(),limit=k,with_payload=True)
        return [{"text":p.payload.get("text",""),"metadata":{a:b for a,b in p.payload.items() if a!='text'},"distance":1-float(p.score)} for p in result.points]
    def count(self):
        try:return self.client.count(collection_name=self.name).count
        except:return 0

class PineconeStore:
    def __init__(self):
        from pinecone import Pinecone
        if not PINECONE_API_KEY: raise ValueError("PINECONE_API_KEY is not configured")
        self.index=Pinecone(api_key=PINECONE_API_KEY).Index(PINECONE_INDEX); self.embedder=EmbeddingEngine()
    def add(self,record_id,text,metadata):
        self.index.upsert(vectors=[{"id":str(record_id),"values":self.embedder.encode([text])[0].tolist(),"metadata":{"text":text,**metadata}}])
    def retrieve(self,query,k=5):
        r=self.index.query(vector=self.embedder.encode([query])[0].tolist(),top_k=k,include_metadata=True)
        return [{"text":x.metadata.get("text",""),"metadata":{a:b for a,b in x.metadata.items() if a!='text'},"distance":1-float(x.score)} for x in r.matches]
    def count(self):
        try:return self.index.describe_index_stats().get('total_vector_count',0)
        except:return 0

class InterviewRAG:
    def __init__(self,provider='chroma'):
        self.provider=provider; self.store=self._make(provider)
    def _make(self,p):
        return {'chroma':ChromaStore,'faiss':FaissStore,'qdrant':QdrantStore,'pinecone':PineconeStore}[p]()
    def switch(self,p): self.provider=p; self.store=self._make(p)
    def retrieve(self,query,k=5,session_id=None):
        # Current-session records plus admin-created (manual) memory are sent
        # to the LLM. Other candidates' records remain private.
        if session_id is not None and isinstance(self.store, ChromaStore):
            return self.store.retrieve(query, k, session_ids=[str(session_id), 'manual'])
        if session_id is not None and hasattr(self.store, 'all'):
            records = self.store.all(1000)
            allowed = {str(session_id), 'manual'}
            return [record for record in records if record.get('metadata', {}).get('session_id') in allowed][:k]
        return self.store.retrieve(query,k)
    def add(self,attempt_id,question,answer,evaluation,session_id=None):
        text=(f"Interview Question: {question}\nCandidate Answer: {answer}\n"
              f"AI Evaluation: {json.dumps(evaluation,ensure_ascii=False)}\nSession: {session_id or ''}")
        meta={'type':'interview_attempt','session_id':str(session_id or ''),'attempt_id':str(attempt_id),'score':str(evaluation.get('score',''))}
        self.store.add(attempt_id,text,meta)
    def count(self): return self.store.count()
    def preview(self,limit=20):
        if hasattr(self.store,'all'): return self.store.all(limit)
        return []
