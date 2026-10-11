from sentence_transformers import CrossEncoder
from retrieve import Retriever

class Reranker:
    def __init__(self, name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(name, device="cpu", max_length=512)

    def rerank(self, query, cands, retr, k=5):
        ids = [cid for cid, _ in cands]
        scores = self.model.predict([(query, retr.get(c)["text"]) for c in ids], batch_size=32)
        ranked = sorted(zip(ids, scores), key=lambda x: -x[1])
        return [(cid, float(s)) for cid, s in ranked[:k]]

if __name__ == "__main__":
    r, rr = Retriever(), Reranker()
    for q in ["What is the difference between LoRA and QLoRA?",
              "How does DPO avoid training a separate reward model?",
              "What GPU did OpenAI use to train GPT-4?"]:
        print(f"\nQ: {q}")
        for cid, s in rr.rerank(q, r.hybrid(q, 30), r, 5):
            c = r.get(cid)
            print(f"{s:7.2f} {c['arxiv_id']} p{c['page']:<3} {c['text'][:70]}")