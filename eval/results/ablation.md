# Ablation results

Questions: 30 single/definition (Recall@5, MRR@10, PaperHit@5), 15 comparison (Cov, Full, PageCov), 5 unanswerable (excluded). Pool=30, per-paper cap=2.

| System | Recall@5 | MRR@10 | PaperHit@5 | Cov@5 | Cov@10 | Full@5 | Full@10 | PageCov@5 | ms/query |
|---|---|---|---|---|---|---|---|---|---|
| bm25 | 0.667 | 0.430 | 1.000 | 0.744 | 0.833 | 0.467 | 0.667 | 0.389 | 7 |
| dense | 0.700 | 0.450 | 1.000 | 0.844 | 0.900 | 0.667 | 0.800 | 0.267 | 22 |
| hybrid | 0.667 | 0.393 | 1.000 | 0.811 | 0.933 | 0.600 | 0.867 | 0.389 | 32 |
| hybrid+rerank | 0.733 | 0.434 | 1.000 | 0.811 | 0.867 | 0.600 | 0.733 | 0.444 | 1351 |
| hybrid+diversify | 0.367 | 0.283 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.389 | 29 |
| hybrid+rerank+diversify | 0.433 | 0.328 | 1.000 | 0.944 | 1.000 | 0.867 | 1.000 | 0.411 | 1358 |

```json
{
 "date_utc": "2026-10-14T12:34:59",
 "git_commit": "7b5eecd",
 "git_dirty": true,
 "gold_sha": "630f740a52ce",
 "chunks_sha": "596e67eec365",
 "n_chunks": 3212,
 "embedding_model": "BAAI/bge-small-en-v1.5",
 "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2",
 "pool": 30,
 "k_max": 10,
 "per_paper_cap": 2,
 "rrf_k": 60,
 "groups": {
  "single_definition": 30,
  "comparison": 15,
  "unanswerable": 5
 },
 "python": "3.12.3",
 "platform": "Linux-6.18.33.1-microsoft-standard-WSL2-x86_64-with-glibc2.39",
 "cpus": 12,
 "versions": {
  "sentence-transformers": "6.1.0",
  "faiss-cpu": "1.15.1",
  "rank-bm25": "0.2.2",
  "torch": "2.14.1+cpu",
  "numpy": "2.5.4"
 }
}
```