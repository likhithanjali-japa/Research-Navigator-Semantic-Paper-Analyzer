# backend/app.py
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from backend.auth_utils import register_user, login_user
from backend.ingest_utils import ingest_arxiv, ingest_pubmed
from backend.ner_utils import process_text_for_ner, extract_text_from_pdf_bytes
from backend.semantic import semantic_search, recommendations_for_paper, build_index
from backend.database import papers, users, search_logs, feedbacks

from datetime import datetime
from bson import ObjectId
from fpdf import FPDF
import io
import threading
import traceback

app = FastAPI(title="Research Navigator API")

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Streamlit + browser apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Index build state --------------------
# We guard index builds so we don't rebuild repeatedly and block endpoints.
_index_built = False
_index_lock = threading.Lock()

def ensure_index_built_async():
    """
    Launch a background thread to build the index if not built.
    Non-blocking for the calling request.
    """
    global _index_built
    with _index_lock:
        if _index_built:
            return
        def _build():
            global _index_built
            try:
                build_index()
                _index_built = True
            except Exception:
                # swallow here but log
                traceback.print_exc()
        t = threading.Thread(target=_build, daemon=True)
        t.start()

# -------------------- Health endpoint --------------------
@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Backend running"}

# -------------------- AUTH --------------------
@app.post("/register")
async def register(request: Request):
    data = await request.json()
    result = register_user(
        name=data.get("name"),
        email=data.get("email"),
        password=data.get("password"),
        institution=data.get("institution"),
        research=data.get("research")
    )

    if "error" in result:
        return JSONResponse(status_code=400, content={"error": result["error"]})

    return result


@app.post("/login")
async def login(request: Request):
    data = await request.json()
    result = login_user(data.get("email"), data.get("password"))

    # if returned tuple → (error, status)
    if isinstance(result, tuple):
        err, status = result
        return JSONResponse(status_code=status, content=err)

    return result


# -------------------- INGEST --------------------
@app.post("/ingest/arxiv")
async def ingest_arxiv_api(request: Request):
    """
    Ingest from arXiv. This can take time; we run index build asynchronously
    so the endpoint returns quickly after ingestion completes.
    """
    data = await request.json()
    try:
        out = ingest_arxiv(
            keyword=data.get("keyword", ""),
            max_results=int(data.get("max_results", 5)),
            owner_email=data.get("email")
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"ingest_arxiv failed: {str(e)}"})

    # ensure index build in background (non-blocking)
    ensure_index_built_async()
    return {"data": out}

@app.post("/ingest/pubmed")
async def ingest_pubmed_api(request: Request):
    data = await request.json()
    try:
        out = ingest_pubmed(
            keyword=data.get("keyword", ""),
            max_results=int(data.get("max_results", 5)),
            owner_email=data.get("email")
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"ingest_pubmed failed: {str(e)}"})

    # ensure index build in background (non-blocking)
    ensure_index_built_async()
    return {"data": out}

# -------------------- PAPERS LIST --------------------
@app.get("/papers")
def get_papers_api(email: str = None, limit: int = 50):
    query = {}
    if email:
        query["ingested_by"] = email

    docs = list(papers.find(query).sort("created_at", -1).limit(limit))
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

# -------------------- NER --------------------
@app.post("/ner/process")
async def ner_process(request: Request):
    data = await request.json()
    text = data.get("text", "")
    if not text:
        return JSONResponse(status_code=400, content={"error": "No text provided"})
    try:
        out = process_text_for_ner(text)
        return {"data": out}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ner/upload")
async def ner_upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        txt = extract_text_from_pdf_bytes(content)
        out = process_text_for_ner(txt)
        return {"data": out}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# -------------------- SEMANTIC SEARCH --------------------
# -------------------- SEMANTIC SEARCH --------------------
@app.post("/semantic/search")
async def semantic_search_api(request: Request):
    data = await request.json()
    q = data.get("query", "")
    email = data.get("email")

    if not q:
        return JSONResponse(status_code=400, content={"error": "No query"})

    # Log query
    try:
        search_logs.insert_one({
            "email": email,
            "query": q,
            "created_at": datetime.utcnow()
        })
    except:
        pass

    ensure_index_built_async()

    try:
        from backend.semantic import semantic_search as _search
        items = _search(q)      # returns list
        return {"results": items}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# -------------------- RECOMMENDATIONS --------------------
@app.get("/semantic/recommendations")
def semantic_recommend_api(paper_id: str, limit: int = 6):
    try:
        ensure_index_built_async()
        from backend.semantic import recommendations_for_paper as recs_func

        items = recs_func(paper_id, top_k=limit)   # returns list
        return {"results": items}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# -------------------- FEEDBACK --------------------
@app.post("/feedback")
async def post_feedback(request: Request):
    data = await request.json()
    try:
        feedbacks.insert_one({
            "email": data.get("email"),
            "text": data.get("text"),
            "stars": int(data.get("stars", 5)),
            "created_at": datetime.utcnow()
        })
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# -------------------- ANALYTICS --------------------
@app.get("/analytics/user")
def user_analytics(email: str):
    if not email:
        return JSONResponse(status_code=400, content={"error": "missing-email"})

    total_searches = search_logs.count_documents({"email": email})

    pipeline = [
        {"$match": {"email": email}},
        {"$group": {"_id": "$query", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top_queries = list(search_logs.aggregate(pipeline))
    top_q = [[t["_id"], t["count"]] for t in top_queries]

    return {
        "total_searches": total_searches,
        "top_queries": top_q
    }

@app.get("/analytics/global")
def global_analytics():
    total_users = users.count_documents({})
    total_papers = papers.count_documents({})
    total_searches = search_logs.count_documents({})

    pipeline = [
        {"$group": {"_id": "$query", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    topics = [[t["_id"], t["count"]] for t in search_logs.aggregate(pipeline)]

    return {
        "total_users": total_users,
        "total_papers": total_papers,
        "total_searches": total_searches,
        "top_topics": topics
    }

# -------------------- EXPORT PDF --------------------
@app.get("/export/{paper_id}")
def export_pdf(paper_id: str):
    try:
        p = papers.find_one({"_id": ObjectId(paper_id)})
    except Exception:
        return JSONResponse(status_code=404, content={"error": "paper not found"})

    if not p:
        return JSONResponse(status_code=404, content={"error": "paper not found"})

    try:
        recs = recommendations_for_paper(paper_id, top_k=6)
    except Exception:
        recs = []

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 10, p.get("title", "Untitled"))

    # Summary
    pdf.ln(4)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8, p.get("summary", ""))

    # Recommendations
    pdf.ln(6)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Recommended Papers:", ln=True)
    pdf.set_font("Arial", size=12)
    for r in recs:
        pdf.multi_cell(0, 7, f"- {r.get('title', '')[:180]}")

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{p.get('title','paper')[:40]}.pdf\""}
    )
