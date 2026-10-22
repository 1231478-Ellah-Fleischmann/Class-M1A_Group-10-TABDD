import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()

VECTOR_HOST = os.getenv("VECTOR_HOST", "localhost")
VECTOR_PORT = int(os.getenv("VECTOR_PORT", "6333"))
VECTOR_API_KEY = os.getenv("VECTOR_API_KEY") or None
VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION", "pois")

# Dimensão dos vetores do modelo paraphrase-multilingual-MiniLM-L12-v2
VECTOR_SIZE = 384

def get_client() -> QdrantClient:
    """Cria e devolve uma ligação ao Qdrant."""
    return QdrantClient(host=VECTOR_HOST, port=VECTOR_PORT, api_key=VECTOR_API_KEY)

def create_collection(
    client: QdrantClient,
    collection_name: str = VECTOR_COLLECTION,
    vector_size: int = VECTOR_SIZE,
    recreate: bool = False,
) -> None:
    """Cria a coleção no Qdrant, se ainda não existir."""
    if client.collection_exists(collection_name):
        if not recreate:
            print(f"A coleção '{collection_name}' já existe. Nada a fazer.")
            return
        client.delete_collection(collection_name)
        print(f"Coleção '{collection_name}' apagada para ser recriada.")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"Coleção '{collection_name}' criada.")
    
if __name__ == "__main__":
    client = get_client()
    print("Ligação ao Qdrant OK")

    create_collection(client)

    info = client.get_collection(VECTOR_COLLECTION)
    print("Dimensão dos vetores:", info.config.params.vectors.size)
    print("Métrica:", info.config.params.vectors.distance)
    print("Número de pontos:", info.points_count)
