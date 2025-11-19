from fastapi import APIRouter, Request, Query, HTTPException
from backend import semantic
from backend.database import papers as papers_collection
from backend.ingest_utils import ingest_arxiv as ingest_from_arxiv
from backend.ingest_utils import ingest_pubmed as ingest_from_pubmed
from backend.analyze_utils import analyze_paper
from bson import ObjectId

router = APIRouter()

# --- PAPER LIST ENDPOINT ---
@router.get("/papers")
def get_papers_by_user(email: str = Query(...), limit: int = 50):
    papers = list(papers_collection.find({"ingested_by": email}).limit(limit))
    for p in papers:
        p["_id"] = str(p["_id"])
    return papers

# --- INGESTION ENDPOINTS ---
@router.post("/ingest/arxiv")
async def ingest_arxiv(request: Request):
    data = await request.json()
    return ingest_from_arxiv(
        keyword=data.get("keyword"),
        max_results=data.get("max_results"),
        owner_email=data.get("email"),
    )

@router.post("/ingest/pubmed")
async def ingest_pubmed(request: Request):
    data = await request.json()
    return ingest_from_pubmed(
        keyword=data.get("keyword"),
        max_results=data.get("max_results"),
        owner_email=data.get("email"),
    )

# --- NER PROCESS (INGESTED PAPER) ---
@router.post("/ner/process")
async def ner_process_ingested(request: Request):
    data = await request.json()
    email = data.get("email")
    title = data.get("title")

    if not email or not title:
        raise HTTPException(status_code=400, detail="Missing email or title")

    result = analyze_paper(email, title)
    if "detail" in result:
        raise HTTPException(status_code=404, detail=result["detail"])

    return result.get("data", {})

# --- SEMANTIC SEARCH ---
@router.post("/semantic/search")
async def semantic_search_query(request: Request):
    data = await request.json()
    query = data.get("query")
    top_k = data.get("top_k", 8)

    if not query:
        return {"results": []}

    return {"results": semantic.semantic_search(query, top_k)}

@router.post("/semantic/recommend")
async def semantic_recommend_paper(request: Request):
    data = await request.json()
    paper_id = data.get("paper_id")
    top_k = data.get("top_k", 6)

    if not paper_id or not ObjectId.is_valid(paper_id):
        return {"results": []}

    return {"results": semantic.recommendations_for_paper(paper_id, top_k)}
