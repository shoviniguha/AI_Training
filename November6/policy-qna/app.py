# Run: streamlit run app.py
import time
import streamlit as st
from dotenv import load_dotenv

from src.parsing import index_pdf
from src.retrieval import retrieve, build_context
from src.llm import build_prompt, generate_answer

# -------- Fixed config --------
MAX_CHARS = 500
OVERLAP = 250
TOP_K = 10

load_dotenv()
st.set_page_config(page_title="Policy Q&A Assistant", layout="wide")
st.title("🧭 Policy Q&A Assistant")

uploaded = st.file_uploader("Upload a policy PDF", type=["pdf"])
if "state" not in st.session_state:
    st.session_state.state = {}

c1, c2 = st.columns([1, 1])
with c1:
    if uploaded and st.button("📥 Index document"):
        with st.spinner("Parsing & indexing…"):
            try:
                pdf_bytes = uploaded.read()
                index, chunks, metas = index_pdf(pdf_bytes, max_chars=MAX_CHARS, overlap=OVERLAP)
                st.session_state.state.update({
                    "index": index,
                    "chunks": chunks,
                    "metas": metas,
                    "doc_name": uploaded.name,
                    "ts": time.time(),
                })
                st.success(f"Indexed: {uploaded.name}")
            except Exception as e:
                st.error(f"Indexing error: {e}")

with c2:
    if st.session_state.state.get("index") is not None and st.button("🧹 Clear"):
        st.session_state.state = {}
        st.toast("Cleared.")

st.divider()

if st.session_state.state.get("index") is not None:
    st.subheader("Ask a question")

    # Use a form so the text_input value and the submit happen in one rerun
    with st.form("ask_form", clear_on_submit=False):
        q = st.text_input("e.g., What is the leave encashment policy?")
        submitted = st.form_submit_button("🔎 Ask")

    if submitted:
        try:
            with st.spinner("Retrieving relevant policy excerpts…"):
                idxs = retrieve(st.session_state.state["index"], q, k=TOP_K)
                ctx = build_context(
                    st.session_state.state["chunks"],
                    st.session_state.state["metas"],
                    idxs
                )

            prompt = build_prompt(ctx, q)
            with st.spinner("Calling the model…"):
                ans = generate_answer(prompt)

            st.markdown("### Answer")
            st.write(ans)
            with st.expander("Sources (excerpts with pages)"):
                st.code(ctx, language="markdown")

        except Exception as e:
            # Show any LLM/network errors loudly so you know what's wrong
            st.error(f"Error: {e}")

else:
    st.info("Upload a policy PDF and click **Index document** to begin.")
