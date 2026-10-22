import re
from collections import Counter
from pathlib import Path

from app.services.poi_indexing import load_pois
from benchmarks.casos_teste import carregar_testes

POIS_FILE = Path("data/sample/pois_teste_modelos.json")
TESTES_FILE = Path("benchmarks/casos_teste_modelos.json")
CAMPOS = ["id", "nome", "cidade", "categoria", "descricao"]


def palavras(texto: str) -> set[str]:
    """Palavras de um texto, em minúsculas, ignorando as muito curtas (de, o, em...)."""
    return {p for p in re.findall(r"\w+", texto.lower()) if len(p) > 3}


if __name__ == "__main__":
    pois = load_pois(POIS_FILE)
    testes = carregar_testes(TESTES_FILE)
    erros = 0

    # 1. Verificar os POIs
    print(f"POIs: {len(pois)}")
    ids = [p.get("id") for p in pois]
    if len(ids) != len(set(ids)):
        print("  ERRO: há ids repetidos")
        erros += 1
    for p in pois:
        for campo in CAMPOS:
            if not p.get(campo):
                print(f"  ERRO: POI {p.get('id')} não tem o campo '{campo}'")
                erros += 1

    if erros:
        print(f"\n{erros} erro(s). Corrige-os antes de continuar.")
        raise SystemExit(1)

    print("  Por cidade:", dict(Counter(p["cidade"] for p in pois)))
    print("  Por categoria:", dict(Counter(p["categoria"] for p in pois)))
    n_palavras = [len(p["descricao"].split()) for p in pois]
    print(f"  Palavras por descrição: mínimo {min(n_palavras)}, máximo {max(n_palavras)}")

    # 2. Verificar as pesquisas
    print(f"\nPesquisas: {len(testes)}")
    print("  Com mais do que uma resposta certa:", sum(1 for _, ok in testes if len(ok) > 1))

    por_id = {p["id"]: p for p in pois}
    avisos = 0
    for pesquisa, ids_ok in testes:
        em_falta = ids_ok - set(por_id)
        if em_falta:
            print(f"  ERRO: '{pesquisa}' refere ids que não existem: {em_falta}")
            erros += 1
            continue

        palavras_descricoes = set().union(*(palavras(por_id[i]["descricao"]) for i in ids_ok))
        palavras_pesquisa = palavras(pesquisa)
        if palavras_pesquisa:
            repetidas = len(palavras_pesquisa & palavras_descricoes) / len(palavras_pesquisa)
            if repetidas > 0.5:
                print(f"  AVISO: '{pesquisa}' repete {repetidas:.0%} das palavras da descrição")
                avisos += 1

    print(f"\n{erros} erro(s), {avisos} aviso(s).")