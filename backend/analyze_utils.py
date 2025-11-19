import spacy
from backend.database import papers

try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","spacy","download","en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def analyze_paper(email, title):
    p = papers.find_one({"title": title})
    if not p:
        return {"detail": "Paper not found"}

    text = (p.get("summary") or p.get("abstract") or "").strip()
    clean = " ".join(text.split())

    doc = nlp(clean)
    ents = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

    return {"clean_text": clean, "entities": ents}
