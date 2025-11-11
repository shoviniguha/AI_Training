# frontend/app.py
import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/call_tool")

st.set_page_config(page_title="Tools + OpenRouter demo", layout="centered")
st.title("Tools + OpenRouter demo")

tool = st.selectbox("Select tool", ["math", "reverse", "date", "llm"])

payload = {"tool": tool}

if tool == "math":
    op = st.selectbox("Operation", ["add", "sub", "mul", "div"])
    a = st.number_input("a", value=45.0)
    b = st.number_input("b", value=35.0)
    payload.update({"op": op, "a": float(a), "b": float(b)})

elif tool == "reverse":
    txt = st.text_input("Text to reverse", "Abdullah")
    payload.update({"text": txt})

elif tool == "date":
    st.write("Returns server's current date/time (UTC)")

elif tool == "llm":
    model = st.text_input("OpenRouter model (optional)", value="mistralai/mistral-small-3")
    query = st.text_area("Ask the LLM", "Explain why FastAPI + async httpx is useful.")
    payload.update({"query": query, "model": model})

if st.button("Execute"):
    try:
        r = requests.post(BACKEND_URL, json=payload, timeout=60)
    except Exception as e:
        st.error(f"Request failed: {e}")
    else:
        if r.ok:
            data = r.json()
            st.success(data.get("result"))
        else:
            st.error(f"{r.status_code}: {r.text}")
