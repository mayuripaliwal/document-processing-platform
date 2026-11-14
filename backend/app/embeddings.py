from fastembed import TextEmbedding

def load_embedding_model():
    """
    Loads the embedding model for vector search
    """
    model=TextEmbedding(
        model_name='sentence-transformers/all-MiniLM-L6-v2'
        )
    return model