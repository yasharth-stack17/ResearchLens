import json, pickle, random
import numpy as np, faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from common import IDX, EMB_MODEL, load_chunks, tokenize

chunks = load_chunks()
ids = [c["chunk_id"] for c in chunks]
assert len(set(ids)) == len(ids), "duplicate chunk_ids"
IDX.mkdir(parents=True, exist_ok=True)

# --- dense ---
model = SentenceTransformer(EMB_MODEL, device="cpu")
emb = model.encode([c["text"] for c in chunks], batch_size=64, normalize_embeddings=True,
                   show_progress_bar=True, convert_to_numpy=True).astype("float32")
index = faiss.IndexFlatIP(emb.shape[1])
index.add(emb)
faiss.write_index(index, str(IDX / "faiss.index"))
np.save(IDX / "embeddings.npy", emb)
json.dump(ids, open(IDX / "chunk_ids.json", "w"))

# --- sparse ---
tok = [tokenize(c["text"]) for c in chunks]
bm25 = BM25Okapi(tok)
pickle.dump(bm25, open(IDX / "bm25.pkl", "wb"))

# --- verification ---
norms = np.linalg.norm(emb, axis=1)
print(f"\nchunks={len(chunks)} | faiss.ntotal={index.ntotal} | dim={emb.shape[1]}")
print(f"embedding norms: min={norms.min():.4f} max={norms.max():.4f} (expect ~1.0)")
print(f"empty BM25 docs: {sum(1 for t in tok if not t)} (expect 0)")
assert index.ntotal == len(chunks)

random.seed(0)
sample = random.sample(range(len(chunks)), 200)
_, I = index.search(emb[sample], 1)
print(f"dense self-retrieval@1: {np.mean(I[:, 0] == np.array(sample)):.3f} (expect >= 0.98)")

hits = 0
for i in sample[:100]:
    s = bm25.get_scores(tok[i][:15])
    hits += i in np.argsort(s)[::-1][:5]
print(f"BM25 self-retrieval@5 (first 15 tokens): {hits/100:.2f} (expect >= 0.95)")