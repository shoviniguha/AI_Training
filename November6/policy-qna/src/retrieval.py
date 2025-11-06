from typing import List, Dict
import faiss
from .embeddings import embed_texts

def retrieve(index: faiss.IndexFlatIP, query: str, k: int = 6) -> List[int]:
    q = embed_texts([query])
    D, I = index.search(q, k)
    return [int(i) for i in I[0]]

def build_context(chunks: List[str], metas: List[Dict], indices: List[int]) -> str:
    lines = []
    for i in indices:
        page = metas[i]["page"]
        excerpt = chunks[i][:750]
        lines.append(f"(p. {page}) {excerpt}")
    return "\n\n".join(lines)
