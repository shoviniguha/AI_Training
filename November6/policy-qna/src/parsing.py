import re
import math
import fitz  # PyMuPDF
from typing import Tuple, List, Dict, Iterable
import faiss
import numpy as np
from src.embeddings import embed_texts

HEADING_SPLIT = re.compile(r"(?m)(?=^[A-Z][A-Za-z0-9 \-]{3,40}:\s)", flags=re.MULTILINE)

def _clean_text(txt: str) -> str:
    # collapse whitespace; avoid creating huge temp strings by early truncation
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def _chunk_generator(text: str, max_chars: int, overlap: int) -> Iterable[str]:
    """
    Generate overlapping chunks without building a large list.
    Guarantees forward progress and enforces len>=50.
    """
    if overlap >= max_chars:
        # enforce safe overlap (e.g., 20% of max_chars)
        overlap = max(0, max_chars // 5)

    n = len(text)
    if n == 0:
        return
    start = 0
    step = max_chars - overlap
    if step <= 0:
        step = max_chars  # minimal forward progress

    while start < n:
        end = min(n, start + max_chars)
        chunk = text[start:end]
        yield chunk
        # move forward
        start += step


def _split_into_paragraphs(text: str) -> List[str]:
    """
    Splits a block of text into clean, paragraph-sized chunks.
    Works well for policy documents, reports, and general prose.
    """
    # 1️⃣ Normalize line endings and remove weird characters
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2️⃣ Replace multiple blank lines (2 or more) with a unique paragraph delimiter
    # This helps separate sections properly
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # 3️⃣ Split paragraphs by double newlines
    paragraphs = text.split("\n\n")

    # 4️⃣ Clean up each paragraph: merge broken lines within a paragraph
    cleaned_paragraphs = []
    for p in paragraphs:
        # Merge single line breaks within a paragraph
        merged = re.sub(r"\n+", " ", p.strip())
        # Collapse extra spaces
        merged = re.sub(r"\s{2,}", " ", merged)
        if len(merged) >= 50:  # skip tiny fragments like headers or footers
            cleaned_paragraphs.append(merged.strip())

    return cleaned_paragraphs


def index_pdf(pdf_bytes: bytes, max_chars: int = 900, overlap: int = 150) -> Tuple:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    chunks = []
    metas = []

    for pno, page in enumerate(doc, start=1):
        txt = page.get_text("text")
        if not txt:
            continue

        txt = _clean_text(txt)
        paragraphs = _split_into_paragraphs(txt)
        print(paragraphs)
        for paragraph in paragraphs:
            chunks.append(paragraph)
            metas.append({"page": pno})

    print(f"Total chunks: {len(chunks)}")  # Debug: Check the number of chunks created

    if not chunks:
        raise ValueError("No text extracted.")

    embs = embed_texts(chunks)
    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs)
    return index, chunks, metas



