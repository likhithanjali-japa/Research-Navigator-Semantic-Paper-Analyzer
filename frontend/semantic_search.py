# semantic_search.py
import streamlit as st
import requests
import os

st.set_page_config(page_title="Semantic Search", layout="wide")
BACKEND = st.secrets.get("backend_url", os.environ.get("BACKEND_URL", "http://backend:8000"))

st.title("Semantic Search & Recommendations")
query = st.text_input("Enter natural language query", value="neural networks for NLP")
top_k = st.number_input("Number of results", min_value=1, max_value=20, value=8)

if st.button("Search"):
    if not query.strip():
        st.warning("Enter a query.")
    else:
        try:
            resp = requests.post(BACKEND.rstrip("/") + "/semantic/search", json={"query": query, "top_k": int(top_k)}, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
        except Exception as e:
            st.error("Search failed — ensure backend is running and index is built.")
            results = []

        if not results:
            st.info("No results found.")
        else:
            for r in results:
                st.markdown(f"**{r.get('title','Untitled')}** — {r.get('authors','')}")
                st.write(r.get('abstract','')[:400] + "...")
                if st.button(f"Recommend for {r.get('_id')}", key=f"rec_{r.get('_id')}"):
                    try:
                        rec = requests.post(BACKEND.rstrip("/") + "/semantic/recommendations", json={"paper_id": r.get('_id')}, timeout=20)
                        rec.raise_for_status()
                        recs = rec.json().get("results", [])
                    except:
                        recs = []
                    if not recs:
                        st.info("No recommendations.")
                    else:
                        for rr in recs:
                            st.markdown(f"- {rr.get('title')} — {rr.get('authors')}")
