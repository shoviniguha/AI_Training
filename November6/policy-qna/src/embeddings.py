from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import streamlit as st

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

@st.cache_resource(show_spinner=False)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(EMB_MODEL)

def embed_texts(texts: List[str]) -> np.ndarray:
    if isinstance(texts, str):
        texts = [texts]  # convert single string to list

    model = get_embedder()
    embs = model.encode(texts, normalize_embeddings=True)
    return np.array(embs, dtype="float32")



