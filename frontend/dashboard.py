# dashboard.py
import streamlit as st
import requests
import os
st.set_page_config(page_title="Dashboard", layout="wide")

BACKEND = st.secrets.get("backend_url", os.environ.get("BACKEND_URL", "http://backend:8000"))

if "user" not in st.session_state or not st.session_state.user:
    st.warning("You are not signed in. Please sign in on the Login page.")
    st.stop()

user = st.session_state.user
st.markdown(f"## Welcome, {user.get('name','Researcher')}")

col1, col2 = st.columns(2)
with col1:
    if st.button("Ingest Papers"):
        st.session_state.page = "ingest"

with col2:
    if st.button("Run NER"):
        st.session_state.page = "analyze"

st.markdown("---")
st.markdown("### Your profile")
st.write(f"**Email:** {user.get('email')}")
st.write(f"**Institution:** {user.get('institution','-')}")
st.write(f"**Research:** {user.get('research','-')}")
