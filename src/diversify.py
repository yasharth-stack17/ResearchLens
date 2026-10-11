def diversify(ranked, get, k=5, per_paper=2):
    """ranked: [(chunk_id, score)] best-first; get: retriever.get"""
    out, cnt = [], {}
    for cid, s in ranked:
        p = get(cid)["arxiv_id"]
        if cnt.get(p, 0) < per_paper:
            out.append((cid, s))
            cnt[p] = cnt.get(p, 0) + 1
        if len(out) == k:
            break
    return out