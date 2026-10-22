import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

load_dotenv()

VECTOR_HOST = os.getenv("VECTOR_HOST", "localhost")
VECTOR_PORT = int(os.getenv("VECTOR_PORT", "6333"))
VECTOR_API_KEY = os.getenv("VECTOR_API_KEY") or None
VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION", "pois")


def get_client() -> QdrantClient:
    """Cria e devolve uma ligação ao Qdrant."""
    return QdrantClient(host=VECTOR_HOST, port=VECTOR_PORT, api_key=VECTOR_API_KEY)


def create_collection(
    client: QdrantClient,
    vector_size: int,
    collection_name: str = VECTOR_COLLECTION,
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
    print(f"Coleção '{collection_name}' criada com vetores de {vector_size} dimensões.")


def upsert_pois(
    client: QdrantClient,
    pois: list[dict],
    vectors: list[list[float]],
    collection_name: str = VECTOR_COLLECTION,
) -> int:
    """Insere (ou atualiza) POIs na coleção. Devolve quantos pontos foram enviados."""
    if len(pois) != len(vectors):
        raise ValueError("O número de POIs e de vetores tem de ser igual.")

    points = [
        PointStruct(
            id=poi["id"],
            vector=vector,
            payload={
                "nome": poi["nome"],
                "cidade": poi["cidade"],
                "categoria": poi["categoria"],
            },
        )
        for poi, vector in zip(pois, vectors)
    ]

    client.upsert(collection_name=collection_name, points=points)
    return len(points)


def count_points(client: QdrantClient, collection_name: str = VECTOR_COLLECTION) -> int:
    """Devolve quantos pontos existem na coleção."""
    return client.count(collection_name=collection_name, exact=True).count

def search_pois(
    client: QdrantClient,
    query_vector: list[float],
    limit: int = 5,
    cidade: str | None = None,
    categoria: str | None = None,
    collection_name: str = VECTOR_COLLECTION,
) -> list[dict]:
    """Devolve os POIs mais semelhantes ao vetor da pesquisa, do mais para o menos semelhante."""
    condicoes = []
    if cidade:
        condicoes.append(FieldCondition(key="cidade", match=MatchValue(value=cidade)))
    if categoria:
        condicoes.append(FieldCondition(key="categoria", match=MatchValue(value=categoria)))

    filtro = Filter(must=condicoes) if condicoes else None

    resultado = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=filtro,
        limit=limit,
        with_payload=True,
    )

    return [{"id": p.id, "score": p.score, **p.payload} for p in resultado.points]


if __name__ == "__main__":
    client = get_client()
    print("Ligação ao Qdrant OK")
    print("Coleções existentes:", client.get_collections())