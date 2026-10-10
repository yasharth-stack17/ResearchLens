import fitz, json, re
from pathlib import Path
from collections import Counter

SIZE, OVERLAP, MIN_LEN = 900, 150, 100
meta = json.load(open("data/meta.json"))

def clean(t):
    t = t.replace("\u00ad", "")
    t = re.sub(r"-\n(?=[a-z])", "", t)          # rejoin hyphenated line breaks
    return re.sub(r"\s+", " ", t).strip()

def chunk(text):
    out, i, n = [], 0, len(text)
    while i < n:
        end = min(i + SIZE, n)
        if end < n:                               # don't cut mid-word
            sp = text.rfind(" ", i + SIZE - 100, end)
            if sp > i:
                end = sp
        piece = text[i:end].strip()
        if len(piece) >= MIN_LEN:
            out.append(piece)
        if end >= n:
            break
        i = max(end - OVERLAP, i + 1)
    return out

recs, thin = [], []
for stem, m in sorted(meta.items()):
    with fitz.open(f"data/raw/{stem}.pdf") as doc:
        for pno, page in enumerate(doc, 1):
            text = clean(page.get_text("text", sort=True))
            if len(text) < 200:
                thin.append((stem, pno, len(text)))
            for j, c in enumerate(chunk(text)):
                recs.append({"chunk_id": f"{stem}-p{pno}-{j}", "paper": stem,
                             "arxiv_id": m["arxiv_id"], "title": m["title"],
                             "year": m["year"], "category": m["category"],
                             "page": pno, "text": c})

with open("data/chunks.jsonl", "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

per = Counter(r["paper"] for r in recs)
print(f"\n{len(recs)} chunks from {len(per)} papers | avg {sum(len(r['text']) for r in recs)//len(recs)} chars")
for stem, c in sorted(per.items()):
    print(f"  {stem:<18}{c:>5}  {meta[stem]['title'][:50]}")
print(f"\nPages with <200 chars of text: {len(thin)}", thin[:10])
print("\nSample chunk:\n", recs[len(recs)//2])
