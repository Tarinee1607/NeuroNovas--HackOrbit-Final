# memory.py

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Initialize SentenceTransformer and FAISS
model = SentenceTransformer('all-MiniLM-L6-v2')
dimension = 384
index = faiss.IndexFlatL2(dimension)

# Store text + metadata
message_store = {}  # For session-based access
text_store = []     # For FAISS index metadata

USE_FAISS = True  # ✅ Toggle FAISS-based semantic search

def embed_text(text):
    return model.encode([text])[0]

def add_message(session_id, sender, message):
    # Store in session-wise dict
    if session_id not in message_store:
        message_store[session_id] = []
    message_store[session_id].append({
        "sender": sender,
        "message": message
    })

    # Store in FAISS index
    if USE_FAISS:
        vec = embed_text(message)
        index.add(np.array([vec]).astype('float32'))
        text_store.append({
            "session_id": session_id,
            "sender": sender,
            "message": message
        })

def get_messages(session_id):
    return message_store.get(session_id, [])

def search_similar(query, top_k=3):
    vec = embed_text(query)

    if index.ntotal == 0:
        return []

    # Search and sort by most recent matching
    D, I = index.search(np.array([vec]), top_k)
    return sorted(
        [text_store[i] for i in I[0] if i < len(text_store)],
        key=lambda x: text_store.index(x),  # prioritize recency
        reverse=True
    )
