import os
from sentence_transformers import SentenceTransformer

# Load model globally (loads once on startup)
# Model name "all-MiniLM-L6-v2" is small (80MB) and very fast for CPU inference
MODEL_NAME = "all-MiniLM-L6-v2"
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    return model

def get_embedding(text: str):
    """
    Encodes text into a 384-dimensional vector list.
    """
    m = get_model()
    return m.encode(text).tolist()
