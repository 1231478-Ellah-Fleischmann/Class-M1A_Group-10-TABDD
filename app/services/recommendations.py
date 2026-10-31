import sys

from app.repositories.vector.qdrant_repository import get_client, get_poi, recommend_pois
from app.services.semantic_search import mostrar_resultados


def similar_pois(
    poi_id: int,
    limit: int = 5,
    cidade: str | None = None,
    categoria: str | None = None,
) -> list[dict]:
    """Tipo A: locais semelhantes a um POI (usa o vetor do próprio POI, já guardado no Qdrant)."""
    return recommend_pois(
        get_client(),
        positivos=[poi_id],
        limit=limit,
        cidade=cidade,
        categoria=categoria,
    )


if __name__ == "__main__":
    ids = [int(x) for x in sys.argv[1:]] or [1, 2, 3]
    client = get_client()

    for poi_id in ids:
        poi = get_poi(client, poi_id)
        if poi is None:
            print(f"\nO POI {poi_id} não existe na coleção.")
            continue

        titulo = f"semelhantes a {poi['nome']} ({poi['cidade']}, {poi['categoria']})"
        mostrar_resultados(titulo, similar_pois(poi_id))
        mostrar_resultados(f"{titulo}, só {poi['categoria']}", similar_pois(poi_id, categoria=poi["categoria"]))