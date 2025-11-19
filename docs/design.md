
# Design mapping to the provided PDF

This document maps the scaffolded project to the PDF "AI-PaperIQ Research Insight Analyzer".

Milestones:
- Weeks 1-2: Authentication (FastAPI JWT), ingestion script (scripts/ingest_arxiv.py), sample storage (sample_data/)
- Weeks 3-4: Preprocessing (backend/utils.py), spaCy NER pipeline (placeholder), Streamlit UI to highlight extracted entities
- Weeks 5-6: Embeddings using sentence-transformers (backend/utils.py), semantic search endpoint (backend/app.py)
- Weeks 7-8: Relation extraction (placeholder), admin endpoints, Dockerfile and docker-compose for containerization

Files of interest:
- `backend/app.py` — FastAPI backend: auth, ingest, preprocess, embeddings, search
- `frontend/streamlit_app.py` — Streamlit UI following the PDF steps
- `scripts/ingest_arxiv.py` — ingestion template for ArXiv/PubMed APIs
