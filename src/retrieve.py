import json, pickle, sys
import numpy as np, faiss
from sentence_transformers import SentenceTransformer
from common import IDX, EMB_MODEL, QUERY_PREFIX, load_chunks, tokenize

class Retriever:
    def __init__(self):
        self.chunks = load_chunks()
        self.by_id = {c["chunk_id"]: c for c in self.chunks}
        self.ids = json.load(open(IDX / "chunk_ids.json"))
        assert self.ids == [c["chunk_id"] for c in self.chunks], \
            "index out of sync with chunks.jsonl: rerun src/index.py"
        self.index = faiss.read_index(str(IDX / "faiss.index"))
        self._bm25 = pickle.load(open(IDX / "bm25.pkl", "rb"))
        self.model = SentenceTransformer(EMB_MODEL, device="cpu")

    def bm25(self, q, k=10):
        s = self._bm25.get_scores(tokenize(q))
        return [(self.ids[i], float(s[i])) for i in np.argsort(s)[::-1][:k]]

    def dense(self, q, k=10):
        v = self.model.encode([QUERY_PREFIX + q], normalize_embeddings=True).astype("float32")
        D, I = self.index.search(v, k)
        return [(self.ids[i], float(d)) for d, i in zip(D[0], I[0])]

    def hybrid(self, q, k=10, pool=50, rrf_k=60):
        scores = {}
        for lst in (self.bm25(q, pool), self.dense(q, pool)):
            for rank, (cid, _) in enumerate(lst, 1):
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        return sorted(scores.items(), key=lambda x: -x[1])[:k]

    def get(self, cid):
        return self.by_id[cid]

CHECKS = [  # (query, expected arXiv ids)
    ("What is low-rank adaptation and how many trainable parameters does it need?", {"2106.09685"}),
    ("How does DPO avoid training a separate reward model?", {"2305.18290"}),
    ("What is PagedAttention and how does it manage the KV cache?", {"2309.06180"}),
    ("How does Mamba make its state space parameters input-dependent?", {"2312.00752"}),
    ("grouped-query attention versus multi-query attention", {"2305.13245"}),
    ("What is the difference between LoRA and QLoRA?", {"2106.09685", "2305.14314"}),
]

if __name__ == "__main__":
    r = Retriever()
    if len(sys.argv) > 1:                                  # manual query mode
        q = " ".join(sys.argv[1:])
        for name, fn in (("BM25", r.bm25), ("DENSE", r.dense), ("HYBRID", r.hybrid)):
            print(f"\n== {name}")
            for cid, s in fn(q, 5):
                c = r.get(cid)
                print(f"{s:7.3f} {c['arxiv_id']} p{c['page']:<3} {c['title'][:35]} | {c['text'][:80]}")
    else:                                                  # built-in sanity checks
        for q, exp in CHECKS:
            print(f"\nQ: {q}   expect {sorted(exp)}")
            for name, fn in (("bm25", r.bm25), ("dense", r.dense), ("hybrid", r.hybrid)):
                got = [r.get(cid)["arxiv_id"] for cid, _ in fn(q, 5)]
                print(f"  {name:<7}found {sorted(exp & set(got))}  top5={got}")