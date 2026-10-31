import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    HasIdCondition,
    MatchAny,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    RecommendInput,
    RecommendQuery,
    RecommendStrategy,
    VectorParams,
)

load_dotenv()

VECTOR_HOST = os.getenv("VECTOR_HOST", "localhost")
VECTOR_PORT = int(os.getenv("VECTOR_PORT", "6333"))
VECTOR_API_KEY = os.getenv("VECTOR_API_KEY") or None
VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION", "pois")

# Campos do payload usados em filtros: cada um tem um índice no Qdrant
CAMPOS_FILTRAVEIS = ["cidade", "categoria"]


def get_client() -> QdrantClient:
    """Cria e devolve uma ligação ao Qdrant."""
    return QdrantClient(host=VECTOR_HOST, port=VECTOR_PORT, api_key=VECTOR_API_KEY)


def create_collection(
    client: QdrantClient,
    vector_size: int,
    collection_name: str = VECTOR_COLLECTION,
    recreate: bool = False,
) -> None:
    """Cria a coleção no Qdrant (e os índices do payload), se ainda não existir."""
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
    for campo in CAMPOS_FILTRAVEIS:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=campo,
            field_schema=PayloadSchemaType.KEYWORD,
        )
    print(
        f"Coleção '{collection_name}' criada com vetores de {vector_size} dimensões "
        f"e índices em {CAMPOS_FILTRAVEIS}."
    )


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


def _filtro_payload(
    cidade: str | None = None,
    categoria: str | None = None,
    excluir_ids: set[int] | None = None,
    excluir_cidade: str | None = None,
) -> Filter | None:
    """Constrói o filtro do Qdrant: condições obrigatórias (must) e condições proibidas (must_not)."""
    must = []
    if cidade:
        must.append(FieldCondition(key="cidade", match=MatchValue(value=cidade)))
    if categoria:
        must.append(FieldCondition(key="categoria", match=MatchValue(value=categoria)))

    must_not = []
    if excluir_ids:
        must_not.append(HasIdCondition(has_id=list(excluir_ids)))
    if excluir_cidade:
        must_not.append(FieldCondition(key="cidade", match=MatchValue(value=excluir_cidade)))

    if not must and not must_not:
        return None
    return Filter(must=must or None, must_not=must_not or None)


def search_pois(
    client: QdrantClient,
    query_vector: list[float],
    limit: int = 5,
    cidade: str | None = None,
    categoria: str | None = None,
    collection_name: str = VECTOR_COLLECTION,
) -> list[dict]:
    """Devolve os POIs mais semelhantes ao vetor da pesquisa, do mais para o menos semelhante."""
    resultado = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=_filtro_payload(cidade, categoria),
        limit=limit,
        with_payload=True,
    )
    return [{"id": p.id, "score": p.score, **p.payload} for p in resultado.points]


def get_poi(
    client: QdrantClient,
    poi_id: int,
    collection_name: str = VECTOR_COLLECTION,
) -> dict | None:
    """Devolve o id e o payload de um POI, ou None se não existir."""
    pontos = client.retrieve(collection_name=collection_name, ids=[poi_id], with_payload=True)
    if not pontos:
        return None
    return {"id": pontos[0].id, **pontos[0].payload}


def recommend_pois(
    client: QdrantClient,
    positivos: list[int],
    negativos: list[int] | None = None,
    excluir: list[int] | None = None,
    limit: int = 5,
    cidade: str | None = None,
    categoria: str | None = None,
    excluir_cidade: str | None = None,
    estrategia: RecommendStrategy = RecommendStrategy.AVERAGE_VECTOR,
    collection_name: str = VECTOR_COLLECTION,
) -> list[dict]:
    """
    Recomenda POIs parecidos com os 'positivos' e diferentes dos 'negativos',
    usando os vetores já guardados no Qdrant.
    Os positivos, os negativos e os ids em 'excluir' nunca aparecem nos resultados.
    """
    negativos = negativos or []
    excluir_ids = set(positivos) | set(negativos) | set(excluir or [])

    resultado = client.query_points(
        collection_name=collection_name,
        query=RecommendQuery(
            recommend=RecommendInput(
                positive=positivos,
                negative=negativos or None,
                strategy=estrategia,
            )
        ),
        query_filter=_filtro_payload(cidade, categoria, excluir_ids, excluir_cidade),
        limit=limit,
        with_payload=True,
    )
    return [{"id": p.id, "score": p.score, **p.payload} for p in resultado.points]

def find_ids_by_name(
    client: QdrantClient,
    nomes: list[str],
    collection_name: str = VECTOR_COLLECTION,
) -> dict[str, int]:
    """Devolve {nome: id} dos POIs com esses nomes (útil para testes)."""
    pontos, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=Filter(must=[FieldCondition(key="nome", match=MatchAny(any=nomes))]),
        limit=len(nomes),
        with_payload=True,
    )
    return {p.payload["nome"]: p.id for p in pontos}

if __name__ == "__main__":
    client = get_client()
    print("Ligação ao Qdrant OK")
    print("Coleções existentes:", client.get_collections())