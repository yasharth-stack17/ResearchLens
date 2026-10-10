import re, json, time, sys
from pathlib import Path
import arxiv, requests, fitz

RAW = Path("data/raw"); RAW.mkdir(parents=True, exist_ok=True)

# arxiv_id: (category, keyword that must appear in the title, lowercase)
PAPERS = {
 "1706.03762": ("transformers", "attention is all you need"),
 "1810.04805": ("transformers", "bert"),
 "2005.14165": ("transformers", "few-shot learners"),
 "2001.08361": ("transformers", "scaling laws"),
 "2203.15556": ("transformers", "compute-optimal"),
 "2205.14135": ("efficiency", "flashattention"),
 "2307.08691": ("efficiency", "flashattention-2"),
 "2210.17323": ("efficiency", "gptq"),
 "2306.00978": ("efficiency", "awq"),
 "2309.06180": ("efficiency", "pagedattention"),
 "2211.17192": ("efficiency", "speculative decoding"),
 "2305.13245": ("efficiency", "gqa"),
 "2106.09685": ("finetuning", "lora"),
 "2305.14314": ("finetuning", "qlora"),
 "2203.02155": ("alignment", "human feedback"),
 "2305.18290": ("alignment", "direct preference optimization"),
 "2212.08073": ("alignment", "constitutional ai"),
 "2005.11401": ("retrieval", "retrieval-augmented generation"),
 "2004.04906": ("retrieval", "dense passage retrieval"),
 "2310.11511": ("retrieval", "self-rag"),
 "2312.00752": ("architectures", "mamba"),
 "2401.04088": ("architectures", "mixtral"),
 "2307.09288": ("architectures", "llama 2"),
 "2310.06825": ("architectures", "mistral 7b"),
 "2104.09864": ("architectures", "roformer"),
}

# ---- Phase 1: fetch metadata and verify titles (no downloads yet) ----
client = arxiv.Client(page_size=50, delay_seconds=3, num_retries=5)
found = {}
for r in client.results(arxiv.Search(id_list=list(PAPERS), max_results=len(PAPERS))):
    found[re.sub(r"v\d+$", "", r.get_short_id())] = r

bad = []
print(f"{'ID':<12}{'YEAR':<6}{'CATEGORY':<14}TITLE")
for pid, (cat, kw) in PAPERS.items():
    r = found.get(pid)
    if r is None:
        print(f"{pid:<12}{'-':<6}{cat:<14}** NOT FOUND **"); bad.append(pid); continue
    ok = kw in r.title.lower()
    print(f"{pid:<12}{r.published.year:<6}{cat:<14}{r.title[:75]}{'' if ok else '   <-- MISMATCH'}")
    if not ok: bad.append(pid)
if bad:
    print("\nABORTING. Fix these IDs, then rerun:", *bad, sep="\n  "); sys.exit(1)
print("\nAll 25 titles verified. Downloading...\n")

# ---- Phase 2: download PDFs ----
meta = {}
for pid, (cat, kw) in PAPERS.items():
    r = found[pid]
    stem = f"{r.published.year}_{pid}"
    path = RAW / f"{stem}.pdf"
    if not path.exists() or path.stat().st_size < 50_000:
        resp = requests.get(f"https://arxiv.org/pdf/{pid}",
                            headers={"User-Agent": "researchlens/0.1"}, timeout=90)
        resp.raise_for_status()
        if not resp.content.startswith(b"%PDF"):
            sys.exit(f"{pid}: response was not a PDF")
        path.write_bytes(resp.content)
        time.sleep(3)
    with fitz.open(path) as d:
        pages = len(d)
    meta[stem] = {"arxiv_id": pid, "title": r.title, "year": r.published.year,
                  "category": cat, "pages": pages}
    print(f"ok  {stem}.pdf  {pages:>3} pages  {path.stat().st_size/1e6:5.1f} MB")

json.dump(meta, open("data/meta.json", "w"), indent=1)
print(f"\n{len(meta)} papers | {sum(m['pages'] for m in meta.values())} pages total")
