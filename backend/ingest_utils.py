# backend/ingest_utils.py
import requests
from datetime import datetime
import time
from backend.database import papers

ARXIV_API = "http://export.arxiv.org/api/query"

def ingest_arxiv(keyword, max_results=5, owner_email=None):
    try:
        params = {
            "search_query": f"all:{keyword}",
            "start": 0,
            "max_results": max_results,
        }
        r = requests.get(ARXIV_API, params=params, timeout=10)

        if r.status_code == 200 and "<entry>" in r.text:
            entries = r.text.split("<entry>")
            created = 0

            for e in entries[1:1+max_results]:
                try:
                    title = e.split("<title>")[1].split("</title>")[0].strip()
                except:
                    title = "Untitled"

                try:
                    summary = e.split("<summary>")[1].split("</summary>")[0].strip()
                except:
                    summary = ""

                doc = {
                    "title": title,
                    "summary": summary,
                    "source": "arXiv",
                    "ingested_by": owner_email,
                    "created_at": datetime.utcnow(),
                }
                papers.insert_one(doc)
                created += 1

            return {"count": created}

    except Exception:
        pass

    created = 0
    for i in range(max_results):
        doc = {
            "title": f"{keyword.title()} — sample #{i+1}",
            "summary": f"Mock summary for {keyword}.",
            "source": "arXiv-mock",
            "ingested_by": owner_email,
            "created_at": datetime.utcnow(),
        }
        papers.insert_one(doc)
        created += 1

    return {"count": created}


def ingest_pubmed(keyword, max_results=5, owner_email=None):
    created = 0
    for i in range(max_results):
        doc = {
            "title": f"PubMed: {keyword.title()} Study #{i+1}",
            "summary": f"Mock PubMed summary for {keyword}.",
            "source": "PubMed-mock",
            "ingested_by": owner_email,
            "created_at": datetime.utcnow(),
        }
        papers.insert_one(doc)
        created += 1

    return {"count": created}
