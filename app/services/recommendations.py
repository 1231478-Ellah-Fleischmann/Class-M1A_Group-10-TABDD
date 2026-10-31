import sys

from qdrant_client.models import RecommendStrategy

from app.repositories.vector.qdrant_repository import (
    find_ids_by_name,
    get_client,
    get_poi,
    recommend_pois,
)
from app.services.semantic_search import mostrar_resultados, semantic_search

NOTA_POSITIVA = 4  # avaliações >= 4 estrelas contam como "gosto"
NOTA_NEGATIVA = 2  # avaliações <= 2 estrelas contam como "não gosto"


def similar_pois(
    poi_id: int,
    limit: int = 5,
    cidade: str | None = None,
    categoria: str | None = None,
    excluir_cidade: str | None = None,
) -> list[dict]:
    """Tipo A: locais semelhantes a um POI (usa o vetor do próprio POI, já guardado no Qdrant)."""
    return recommend_pois(
        get_client(),
        positivos=[poi_id],
        limit=limit,
        cidade=cidade,
        categoria=categoria,
        excluir_cidade=excluir_cidade,
    )


def personalized_pois(
    favoritos: list[int],
    avaliacoes: dict[int, int],
    vistos: list[int] | None = None,
    categorias_preferidas: list[str] | None = None,
    limit: int = 5,
    cidade: str | None = None,
    estrategia: RecommendStrategy = RecommendStrategy.AVERAGE_VECTOR,
) -> list[dict]:
    """
    Tipo B: recomendações personalizadas a partir do historial do utilizador.
    favoritos: ids dos POIs favoritos
    avaliacoes: {poi_id: estrelas de 1 a 5}
    vistos: ids dos POIs já visitados (não são recomendados)
    categorias_preferidas: usadas só se o utilizador ainda não tiver historial (cold start)
    """
    bem_avaliados = [p for p, nota in avaliacoes.items() if nota >= NOTA_POSITIVA]
    positivos = list(dict.fromkeys(favoritos + bem_avaliados))
    negativos = [p for p, nota in avaliacoes.items() if nota <= NOTA_NEGATIVA and p not in positivos]

    if positivos:
        return recommend_pois(
            get_client(),
            positivos=positivos,
            negativos=negativos,
            excluir=vistos,
            limit=limit,
            cidade=cidade,
            estrategia=estrategia,
        )

    if categorias_preferidas:
        texto = "Locais de interesse: " + ", ".join(categorias_preferidas)
        return semantic_search(texto, limit=limit, cidade=cidade)

    return []


def _ids(client, nomes: list[str]) -> list[int]:
    """Converte nomes em ids (para os testes) e avisa se algum não existir."""
    mapa = find_ids_by_name(client, nomes)
    em_falta = set(nomes) - set(mapa)
    if em_falta:
        print("Atenção, não encontrei:", em_falta)
    return [mapa[n] for n in nomes if n in mapa]


def demo_tipo_a(ids: list[int]) -> None:
    client = get_client()
    for poi_id in ids:
        poi = get_poi(client, poi_id)
        if poi is None:
            print(f"\nO POI {poi_id} não existe na coleção.")
            continue
        titulo = f"semelhantes a {poi['nome']} ({poi['cidade']}, {poi['categoria']})"
        mostrar_resultados(f"{titulo}, nesta cidade", similar_pois(poi_id, cidade=poi["cidade"]))
        mostrar_resultados(f"{titulo}, noutros destinos", similar_pois(poi_id, excluir_cidade=poi["cidade"]))


def demo_tipo_b() -> None:
    client = get_client()

    # Utilizador 1: gosta de museus e não gostou de uma praia
    favoritos = _ids(client, ["Museu Nacional Soares dos Reis"])
    avaliacoes = {i: 5 for i in _ids(client, ["Museu do Carro Elétrico"])}
    avaliacoes |= {i: 1 for i in _ids(client, ["Praia de Matosinhos"])}
    mostrar_resultados(
        "Utilizador 1 (gosta de museus, não gostou de uma praia)",
        personalized_pois(favoritos, avaliacoes),
    )

    # Utilizador 2: gostos variados -> comparar as duas estratégias
    favoritos = _ids(client, ["Praia de Matosinhos", "Museu da Ciência da Universidade de Coimbra"])
    for estrategia in (RecommendStrategy.AVERAGE_VECTOR, RecommendStrategy.BEST_SCORE):
        mostrar_resultados(
            f"Utilizador 2 (praia + museu de ciência), estratégia {estrategia.value}",
            personalized_pois(favoritos, {}, limit=6, estrategia=estrategia),
        )

    # Utilizador 3: novo, só tem preferências no perfil (cold start)
    mostrar_resultados(
        "Utilizador 3 (novo; prefere praia e miradouro)",
        personalized_pois([], {}, categorias_preferidas=["praia", "miradouro"]),
    )


if __name__ == "__main__":
    if "--b" in sys.argv:
        demo_tipo_b()
    else:
        ids = [int(x) for x in sys.argv[1:]] or [1, 2, 3]
        demo_tipo_a(ids)