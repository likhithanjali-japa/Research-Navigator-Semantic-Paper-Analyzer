
"""Ingestion template for ArXiv or PubMed.

This script shows how to call ArXiv API, parse results and save as JSON.
Fill in network code when running in an environment with internet access.
"""
import requests
import json
import time

def ingest_arxiv(query="machine learning", max_results=5, save_path="sample_data/arxiv_sample.json"):
    base = "http://export.arxiv.org/api/query?search_query=all:{}&start=0&max_results={}"
    url = base.format(query, max_results)
    print("Would fetch:", url)
    # When online, use requests.get(url) and parse the Atom feed.
    # For now, this template saves an empty list.
    data = []
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

if __name__ == '__main__':
    ingest_arxiv()
