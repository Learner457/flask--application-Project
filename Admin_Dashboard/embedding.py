from sentence_transformers import SentenceTransformer
import numpy as np

# Load the pre-trained model for sentence embeddings (you can replace this with any model you'd like)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to get the embeddings
def get_embeddings(text: str):
    """
    This function will take text as input and return its embeddings using Sentence-Transformers model.
    """
    embeddings = model.encode(text)  # Encoding the text to get embeddings
    return embeddings

