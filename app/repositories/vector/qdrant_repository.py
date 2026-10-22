import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

VECTOR_HOST = os.getenv("VECTOR_HOST", "localhost")
VECTOR_PORT = int(os.getenv("VECTOR_PORT", "6333"))
VECTOR_API_KEY = os.getenv("VECTOR_API_KEY") or None


def get_client() -> QdrantClient:
    """Cria e devolve uma ligação ao Qdrant."""
    return QdrantClient(host=VECTOR_HOST, port=VECTOR_PORT, api_key=VECTOR_API_KEY)


if __name__ == "__main__":
    client = get_client()
    print("Ligação ao Qdrant OK")
    print("Coleções existentes:", client.get_collections())