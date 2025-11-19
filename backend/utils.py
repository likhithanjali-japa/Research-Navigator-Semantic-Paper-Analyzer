
# Utilities: preprocessing, NER, embeddings placeholders
import spacy
from sentence_transformers import SentenceTransformer
import os
import numpy as np
import json

# Note: Loading models requires internet and disk space. These calls are placeholders.
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except Exception as e:
        print("spaCy model not available:", e)
        return None

def simple_preprocess(text):
    # Basic cleaning and sentence splitting
    text = text.replace("\n"," ").strip()
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return sentences

def extract_entities(text):
    nlp = load_spacy_model()
    if nlp:
        doc = nlp(text)
        ents = [{"text": e.text, "label": e.label_} for e in doc.ents]
        return ents
    else:
        # Fallback: naive uppercase word extraction
        tokens = text.split()
        ents = [t for t in tokens if t.istitle() and len(t)>3]
        return [{"text":e, "label":"MISC"} for e in ents]

def compute_embeddings(texts):
    try:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        return model.encode(texts, show_progress_bar=False)
    except Exception as e:
        print("Embedding model not available:", e)
        # fallback: random vectors
        return np.random.rand(len(texts), 384)
