
# Research Navigator: Semantic Paper Analyzer (AI Project)

A complete project scaffold built from the provided PDF specification.  
This deliverable contains a backend (FastAPI), a frontend (Streamlit), ingestion & preprocessing scripts, placeholders for NER/embeddings/semantic search, Docker support, and sample data — organized exactly to follow the PDF's steps and milestones.

## What's included
- `backend/` — FastAPI app, utilities, ingestion script, Dockerfile
- `frontend/` — Streamlit UI to follow the PDF UI flow: auth, ingestion, view extracted entities, semantic search
- `sample_data/` — small sample papers dataset
- `scripts/` — additional helper scripts, e.g., example ingestion
- `docker-compose.yml` — to run backend + frontend together
- `requirements.txt` — Python dependencies (placeholders; adjust versions)
- `docs/design.md` — mapping between PDF and this implementation

## Quick start (local)
1. Create a virtual env: `python -m venv venv && source venv/bin/activate`
2. Install: `pip install -r requirements.txt`
3. Start backend: `uvicorn backend.app:app --reload --port 8000`
4. Start frontend: `streamlit run frontend/streamlit_app.py`
5. Open Streamlit UI (usually http://localhost:8501)

> NOTE: Some advanced features (fine-tuning NER, large-scale FAISS index, SciBERT embeddings) require internet access and model downloads. This scaffold includes clear placeholders and example code to run them when models are available.

