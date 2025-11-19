# main.py
import streamlit as st
import requests

# This file acts as the default entry point. 
# Since the app uses multi-page structure based on session state, 
# it will immediately route to the main app logic defined in frontend/app.py 
# if you were using a single-file application.
# For a multi-page app (Login.py, dashboard.py), this file might be replaced
# by the pages directory, but we will keep the original file for continuity.

st.set_page_config(page_title="AI PaperIQ — Research Insight Analyzer", layout="wide")
st.title("Research Navigator")
st.write("Welcome! Please navigate to the Login page.")

if st.button("Go to Login"):
    # This simulates navigation in a single-file or simplified multi-page structure
    st.switch_page("Login.py")