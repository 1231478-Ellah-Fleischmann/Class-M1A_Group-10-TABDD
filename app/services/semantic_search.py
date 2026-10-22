from app.repositories.vector.qdrant_repository import VECTOR_COLLECTION, get_client, search_pois
from app.services.embeddings import embed_text


def semantic_search(
    texto: str,
    limit: int = 5,
    cidade: str | None = None,
    categoria: str | None = None,
    collection_name: str = VECTOR_COLLECTION,
) -> list[dict]:
    """Pesquisa em linguagem natural: transforma o texto num vetor e procura no Qdrant."""
    vetor = embed_text(texto)
    return search_pois(
        get_client(),
        vetor,
        limit=limit,
        cidade=cidade,
        categoria=categoria,
        collection_name=collection_name,
    )


def mostrar_resultados(titulo: str, resultados: list[dict]) -> None:
    """Escreve os resultados de forma legível no terminal."""
    print(f"\nPesquisa: {titulo}")
    for posicao, r in enumerate(resultados, start=1):
        print(f"  {posicao}. {r['nome']} ({r['cidade']}, {r['categoria']}) - score {r['score']:.3f}")


if __name__ == "__main__":
    pesquisas = [
        "Museus para visitar no Porto",
        "Sítio calmo para ir com crianças",
        "Comida tradicional portuguesa",
        "Vista bonita sobre o rio",
        "Quiet beach for families",
    ]

    for texto in pesquisas:
        mostrar_resultados(texto, semantic_search(texto, limit=3))

    mostrar_resultados(
        "museus para visitar (filtro: cidade = Lisboa)",
        semantic_search("museus para visitar", limit=3, cidade="Lisboa"),
    )