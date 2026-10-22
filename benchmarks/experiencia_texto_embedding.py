from app.repositories.vector.qdrant_repository import VECTOR_COLLECTION
from app.services.poi_indexing import SAMPLE_FILE, index_pois, load_pois
from app.services.semantic_search import semantic_search

COLECOES = {
    "descricao": VECTOR_COLLECTION,
    "enriquecido": "pois_enriquecido",
}

# (pesquisa, ids considerados resposta certa)
TESTES = [
    ("Museus para visitar no Porto", {2}),
    ("Museus em Lisboa", {7}),
    ("Sítio calmo para ir com crianças", {4, 5}),
    ("Comida tradicional portuguesa", {6}),
    ("Vista bonita sobre o rio em Lisboa", {8}),
    ("Monumento no Porto com vista panorâmica", {1}),
    ("Quiet beach for families", {4}),
    ("Mercado com produtos regionais no Porto", {3}),
    ("Jardins para passear no Porto", {5}),
    ("Onde comer no Porto", {6}),
]


def posicao_esperada(resultados: list[dict], ids_esperados: set[int]) -> int | None:
    """Devolve a posição (1, 2, 3...) do primeiro resultado certo, ou None se não aparecer."""
    for posicao, r in enumerate(resultados, start=1):
        if r["id"] in ids_esperados:
            return posicao
    return None


if __name__ == "__main__":
    pois = load_pois(SAMPLE_FILE)

    for modo, colecao in COLECOES.items():
        index_pois(pois, collection_name=colecao, modo_texto=modo, recreate=True)

    print()
    print(f"{'Pesquisa':<42}{'descricao':>12}{'enriquecido':>14}")
    print("-" * 68)

    em_primeiro = {modo: 0 for modo in COLECOES}

    for texto, esperados in TESTES:
        posicoes = []
        for modo, colecao in COLECOES.items():
            resultados = semantic_search(texto, limit=len(pois), collection_name=colecao)
            pos = posicao_esperada(resultados, esperados)
            posicoes.append(pos)
            if pos == 1:
                em_primeiro[modo] += 1
        print(f"{texto:<42}{str(posicoes[0]):>12}{str(posicoes[1]):>14}")

    print("-" * 68)
    for modo, n in em_primeiro.items():
        print(f"{modo}: {n}/{len(TESTES)} pesquisas com o local certo em 1.º lugar")