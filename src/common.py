import json, re
from pathlib import Path

CHUNKS = Path("data/chunks.jsonl")
IDX = Path("data/index")
EMB_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
STOP = {"the","a","an","of","and","or","to","in","is","are","for","on","with",
        "that","this","by","as","be","it","from","at","we","our","which","can"}

def load_chunks():
    with open(CHUNKS, encoding="utf-8") as f:
        return [json.loads(l) for l in f]

def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]