from backend.database import papers, users, search_logs

def get_user_analytics(email):
    total_searches = search_logs.count_documents({"email": email})
    total_papers = papers.count_documents({"ingested_by": email})

    pipeline = [
        {"$match": {"email": email}},
        {"$group": {"_id": "$query", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    tq = list(search_logs.aggregate(pipeline))

    top_queries = [{"query": t["_id"], "count": t["count"]} for t in tq]

    return {
        "total_searches": total_searches,
        "total_papers": total_papers,
        "top_queries": top_queries
    }

def get_global_analytics():
    return {
        "total_users": users.count_documents({}),
        "total_papers": papers.count_documents({}),
        "total_searches": search_logs.count_documents({})
    }
