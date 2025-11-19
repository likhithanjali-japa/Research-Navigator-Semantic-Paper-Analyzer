import fitz
import spacy
import re

try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","spacy","download","en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf_bytes(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for p in doc:
        text += p.get_text("text") + "\n"
    return re.sub(r'\s+', ' ', text)

def process_text_for_ner(text):
    clean = re.sub(r'\s+', ' ', text).strip()
    doc = nlp(clean)

    ents = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    return {"clean_text": clean, "entities": ents}
