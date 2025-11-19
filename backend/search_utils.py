from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

# Load model once globally
model = SentenceTransformer('all-MiniLM-L6-v2')  # or any suitable S-BERT

def embed_texts(text_list):
    # Returns array of shape (n, 384)
    return model.encode(text_list, show_progress_bar=False)

def build_index(abstracts):
    # abstracts: list of paper abstracts
    vectors = embed_texts(abstracts)
    # Build FAISS index
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype(np.float32))
    return index, vectors

def search_similar(query, abstracts, vectors, topk=5):
    q_emb = embed_texts([query])
    D, I = faiss.IndexFlatL2(vectors.shape[1]).search(np.array(q_emb).astype(np.float32), topk)
    results = []
    for i, idx in enumerate(I[0]):
        results.append({"abstract": abstracts[idx], "score": float(1-D[0][i]/2)})  # normalize to similarity
    return results
