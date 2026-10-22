import json
from pathlib import Path

from app.repositories.vector.qdrant_repository import (
    VECTOR_COLLECTION, 
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


def build_text(poi: dict, modo: str = "descricao") -> str:
    """Constrói o texto que vai ser transformado em vetor."""
    if modo == "descricao":
        return poi["descricao"]
    if modo == "enriquecido":
        return (
            f"{poi['nome']}. Categoria: {poi['categoria']}. "
            f"Cidade: {poi['cidade']}. {poi['descricao']}"
        )
    raise ValueError(f"Modo de texto desconhecido: {modo}")


def index_pois(
    pois: list[dict],
    collection_name: str = VECTOR_COLLECTION,
    modo_texto: str = "enriquecido",
    recreate: bool = False,
) -> int:
    """Gera os embeddings dos POIs e guarda-os no Qdrant."""
    client = get_client()
    create_collection(
        client,
        vector_size=get_dimension(),
        collection_name=collection_name,
        recreate=recreate,
    )

    textos = [build_text(poi, modo_texto) for poi in pois]
    vectors = embed_texts(textos)

    return upsert_pois(client, pois, vectors, collection_name=collection_name)


if __name__ == "__main__":
    pois = load_pois(SAMPLE_FILE)
    print(f"{len(pois)} POIs lidos de {SAMPLE_FILE}")

    inseridos = index_pois(pois)
    print(f"{inseridos} pontos inseridos/atualizados")
    print("Total de pontos na coleção:", count_points(get_client()))