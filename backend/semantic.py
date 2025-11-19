# backend/semantic.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.database import papers
from bson import ObjectId

_vectorizer = None
_matrix = None
_ids = []


# ------------------------------------------------------
# BUILD INDEX
# ------------------------------------------------------
def build_index():
    global _vectorizer, _matrix, _ids

    docs = list(papers.find({}))

    if not docs:
        _vectorizer = None
        _matrix = None
        _ids = []
        return

    texts = []
    ids = []

    for d in docs:
        title = d.get("title") or ""
        summary = (
            d.get("summary")
            or d.get("abstract")
            or d.get("clean_text")
            or d.get("text")
            or d.get("description")
            or ""
        )

        full_text = f"{title} {summary}".strip()

        if not full_text:
            full_text = title

        texts.append(full_text)
        ids.append(str(d["_id"]))

    if all(len(t.strip()) == 0 for t in texts):
        _vectorizer = None
        _matrix = None
        _ids = []
        return

    _vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    _matrix = _vectorizer.fit_transform(texts)
    _ids = ids


# ------------------------------------------------------
# SEMANTIC SEARCH
# ------------------------------------------------------
def semantic_search(query):
    global _vectorizer, _matrix, _ids

    if not query.strip():
        return []

    if _vectorizer is None or _matrix is None:
        build_index()

    if _vectorizer is None or _matrix is None:
        return []

    q_vec = _vectorizer.transform([query])
    sims = cosine_similarity(q_vec, _matrix)[0]

    idxs = sims.argsort()[::-1][:10]

    results = []
    for i in idxs:
        try:
            pid = _ids[i]
            p = papers.find_one({"_id": ObjectId(pid)})
            if not p:
                continue

            results.append({
                "_id": pid,
                "title": p.get("title"),
                "authors": p.get("authors", ""),
                "abstract": p.get("summary") or p.get("abstract") or "",
                "score": float(sims[i])
            })
        except:
            continue

    return results


# ------------------------------------------------------
# RECOMMENDATIONS
# ------------------------------------------------------
def recommendations_for_paper(paper_id, top_k=6):
    global _vectorizer, _matrix, _ids

    if _vectorizer is None or _matrix is None:
        build_index()

    if _vectorizer is None or _matrix is None:
        return []

    if paper_id not in _ids:
        return []

    idx = _ids.index(paper_id)
    sims = cosine_similarity(_matrix[idx], _matrix)[0]

    idxs = sims.argsort()[::-1][1: top_k + 1]

    results = []
    for i in idxs:
        try:
            pid = _ids[i]
            p = papers.find_one({"_id": ObjectId(pid)})
            if not p:
                continue

            results.append({
                "_id": pid,
                "title": p.get("title"),
                "authors": p.get("authors", ""),
                "score": float(sims[i])
            })
        except:
            continue

    return results
