import sys, json, re, fitz
meta = json.load(open("data/meta.json"))
aid, terms = sys.argv[1], [t.lower() for t in sys.argv[2:]]
for stem, m in meta.items():
    if aid != "all" and m["arxiv_id"] != aid:
        continue
    with fitz.open(f"data/raw/{stem}.pdf") as doc:
        for pno, page in enumerate(doc, 1):
            text = re.sub(r"\s+", " ", page.get_text("text", sort=True))
            low = text.lower()
            hits = [t for t in terms if t in low]
            if hits:
                i = low.find(hits[0])
                print(f"{m['arxiv_id']} p{pno:<3} [{len(hits)}/{len(terms)}] ...{text[max(0, i-80):i+120]}...")
