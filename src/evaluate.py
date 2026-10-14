import os, sys, json, time, csv, hashlib, platform, subprocess, datetime
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT); sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from retrieve import Retriever
from rerank import Reranker
from diversify import diversify
from common import EMB_MODEL

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
POOL, KMAX, PER_PAPER = 30, 10, 2
OUT = ROOT / "eval" / "results"; OUT.mkdir(parents=True, exist_ok=True)

def ver(p):
    try: return version(p)
    except PackageNotFoundError: return "n/a"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]
def git(*a):
    try: return subprocess.check_output(["git", *a], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: return "n/a"

gold = [json.loads(l) for l in open("eval/gold.jsonl", encoding="utf-8")]
single = [g for g in gold if g["type"] in ("single", "definition")]
comp = [g for g in gold if g["type"] == "comparison"]
unans = [g for g in gold if not g["answerable"]]
print(f"gold: {len(single)} single/definition | {len(comp)} comparison | {len(unans)} unanswerable")
assert single and comp

r, rr = Retriever(), Reranker()

def sys_rerank(q, k=KMAX):
    return rr.rerank(q, r.hybrid(q, POOL), r, k)
SYSTEMS = {
    "bm25": lambda q: r.bm25(q, KMAX),
    "dense": lambda q: r.dense(q, KMAX),
    "hybrid": lambda q: r.hybrid(q, KMAX),
    "hybrid+rerank": lambda q: sys_rerank(q),
    "hybrid+diversify": lambda q: diversify(r.hybrid(q, POOL), r.get, k=KMAX, per_paper=PER_PAPER),
    "hybrid+rerank+diversify": lambda q: diversify(sys_rerank(q, POOL), r.get, k=KMAX, per_paper=PER_PAPER),
}

raw = {}
for name, fn in SYSTEMS.items():
    fn(gold[0]["question"])                                   # warm-up, not timed
    raw[name] = {}
    for g in gold:
        t = time.perf_counter(); ranked = fn(g["question"]); ms = (time.perf_counter() - t) * 1000
        items = [(cid, float(s), r.get(cid)["arxiv_id"], r.get(cid)["page"]) for cid, s in ranked]
        raw[name][g["id"]] = (items, ms)
    print(f"{name:<26} done | {np.mean([v[1] for v in raw[name].values()]):.0f} ms/query")

def first_rank(items, paper, pages, any_page=False):
    for i, (_, _, aid, pg) in enumerate(items, 1):
        if aid == paper and (any_page or pg in pages):
            return i
    return None

def single_metrics(name):
    rec = mrr = ph = 0.0
    for g in single:
        items = raw[name][g["id"]][0]; p = g["gold_papers"][0]
        fr = first_rank(items, p, g["gold_pages"][p]); pr = first_rank(items, p, [], any_page=True)
        rec += bool(fr and fr <= 5); mrr += (1 / fr if fr else 0.0); ph += bool(pr and pr <= 5)
    n = len(single)
    return {"recall@5": rec / n, "mrr@10": mrr / n, "paper_hit@5": ph / n}

def comp_metrics(name):
    out = {}
    for k in (5, 10):
        cov = full = 0.0
        for g in comp:
            got = {aid for _, _, aid, _ in raw[name][g["id"]][0][:k]}; need = set(g["gold_papers"])
            cov += len(need & got) / len(need); full += float(need <= got)
        out[f"cov@{k}"] = cov / len(comp); out[f"full@{k}"] = full / len(comp)
    pc = 0.0
    for g in comp:
        top5 = raw[name][g["id"]][0][:5]
        pc += np.mean([any(aid == p and pg in g["gold_pages"][p] for _, _, aid, pg in top5)
                       for p in g["gold_papers"]])
    out["page_cov@5"] = pc / len(comp)
    return out

rows = []
for name in SYSTEMS:
    lat = [v[1] for v in raw[name].values()]
    ans = [g for g in gold if g["answerable"]]
    rows.append({"system": name, **single_metrics(name), **comp_metrics(name),
                 "ms_mean": float(np.mean(lat)), "ms_median": float(np.median(lat)),
                 "avg_returned": float(np.mean([len(raw[name][g["id"]][0]) for g in ans]))})

config = {"date_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"),
          "git_commit": git("rev-parse", "--short", "HEAD"), "git_dirty": bool(git("status", "--porcelain")),
          "gold_sha": sha("eval/gold.jsonl"), "chunks_sha": sha("data/chunks.jsonl"),
          "n_chunks": sum(1 for _ in open("data/chunks.jsonl", encoding="utf-8")),
          "embedding_model": EMB_MODEL, "reranker": RERANK_MODEL,
          "pool": POOL, "k_max": KMAX, "per_paper_cap": PER_PAPER, "rrf_k": 60,
          "groups": {"single_definition": len(single), "comparison": len(comp), "unanswerable": len(unans)},
          "python": platform.python_version(), "platform": platform.platform(), "cpus": os.cpu_count(),
          "versions": {p: ver(p) for p in ("sentence-transformers", "faiss-cpu", "rank-bm25", "torch", "numpy")}}

json.dump({"config": config, "systems": rows}, open(OUT / "results.json", "w"), indent=1)
with open(OUT / "ablation.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

with open(OUT / "per_query.jsonl", "w", encoding="utf-8") as f:
    for name in SYSTEMS:
        for g in gold:
            items, ms = raw[name][g["id"]]
            fr = (first_rank(items, g["gold_papers"][0], g["gold_pages"][g["gold_papers"][0]])
                  if g in single else None)
            f.write(json.dumps({"system": name, "id": g["id"], "type": g["type"], "answerable": g["answerable"],
                                "gold_papers": g["gold_papers"], "gold_pages": g["gold_pages"],
                                "first_hit_rank": fr, "latency_ms": round(ms, 1),
                                "retrieved": [list(x) for x in items]}) + "\n")

H = ["System", "Recall@5", "MRR@10", "PaperHit@5", "Cov@5", "Cov@10", "Full@5", "Full@10", "PageCov@5", "ms/query"]
md = ["# Ablation results", "",
      f"Questions: {len(single)} single/definition (Recall@5, MRR@10, PaperHit@5), {len(comp)} comparison "
      f"(Cov, Full, PageCov), {len(unans)} unanswerable (excluded). Pool={POOL}, per-paper cap={PER_PAPER}.", "",
      "| " + " | ".join(H) + " |", "|" + "---|" * len(H)]
for x in rows:
    md.append(f"| {x['system']} | {x['recall@5']:.3f} | {x['mrr@10']:.3f} | {x['paper_hit@5']:.3f} | "
              f"{x['cov@5']:.3f} | {x['cov@10']:.3f} | {x['full@5']:.3f} | {x['full@10']:.3f} | "
              f"{x['page_cov@5']:.3f} | {x['ms_mean']:.0f} |")
md += ["", "```json", json.dumps(config, indent=1), "```"]
(OUT / "ablation.md").write_text("\n".join(md), encoding="utf-8")

print("\n" + "\n".join(md[:5 + len(rows)]))
if "hybrid+rerank" in raw:                                    # evidence for the Step 7 abstention threshold
    top = lambda grp: [raw["hybrid+rerank"][g["id"]][0][0][1] for g in grp]
    ans = [g for g in gold if g["answerable"]]
    for label, grp in (("answerable", ans), ("unanswerable", unans)):
        s = top(grp); print(f"top-1 rerank score, {label:<12}: min={min(s):.2f} median={np.median(s):.2f} max={max(s):.2f}")
print(f"\nsaved to {OUT}/ (results.json, ablation.md, ablation.csv, per_query.jsonl)")
