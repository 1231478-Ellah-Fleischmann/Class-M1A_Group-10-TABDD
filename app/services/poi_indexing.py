import json
from pathlib import Path

from app.repositories.vector.qdrant_repository import (
    count_points,
    create_collection,
    get_client,
    upsert_pois,
)
from app.services.embeddings import embed_texts, get_dimension

SAMPLE_FILE = Path("data/sample/pois_exemplo.json")


def load_pois(path: Path) -> list[dict]:
    """Lê uma lista de POIs de um ficheiro JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def index_pois(pois: list[dict], recreate: bool = False) -> int:
    """Gera os embeddings das descrições e guarda os POIs no Qdrant."""
    client = get_client()
    create_collection(client, vector_size=get_dimension(), recreate=recreate)

    descricoes = [poi["descricao"] for poi in pois]
    vectors = embed_texts(descricoes)

    return upsert_pois(client, pois, vectors)


if __name__ == "__main__":
    pois = load_pois(SAMPLE_FILE)
    print(f"{len(pois)} POIs lidos de {SAMPLE_FILE}")

    inseridos = index_pois(pois)
    print(f"{inseridos} pontos inseridos/atualizados")
    print("Total de pontos na coleção:", count_points(get_client()))