import json
from pathlib import Path

# Casos de teste para avaliar a pesquisa semântica.
# Cada caso: (pesquisa, ids dos POIs considerados resposta certa).
# NOTA: casos para os POIs de exemplo (data/sample/pois_exemplo.json).
# Com o dataset real, esta lista tem de ser refeita.

TESTES = [
    # Pesquisas "normais"
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
    # Pesquisas mais difíceis (vagas ou sem as palavras da descrição)
    ("Arte contemporânea", {5}),
    ("Azulejos e telhados antigos", {8}),
    ("Arquitetura barroca", {1}),
    ("Where can I buy fresh fish?", {3}),
    ("Romantic place to watch the sunset", {8}),
]


def posicao_esperada(resultados: list[dict], ids_esperados: set[int]) -> int | None:
    """Devolve a posição (1, 2, 3...) do primeiro resultado certo, ou None se não aparecer."""
    for posicao, r in enumerate(resultados, start=1):
        if r["id"] in ids_esperados:
            return posicao
    return None

def carregar_testes(path: Path) -> list[tuple[str, set[int]]]:
    """Lê casos de teste de um ficheiro JSON com os campos 'pesquisa' e 'ids_corretos'."""
    with open(path, encoding="utf-8") as f:
        dados = json.load(f)
    return [(d["pesquisa"], set(d["ids_corretos"])) for d in dados]