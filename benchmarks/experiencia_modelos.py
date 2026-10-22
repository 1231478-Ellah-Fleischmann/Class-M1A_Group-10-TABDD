import time

from app.repositories.vector.qdrant_repository import (
    create_collection,
    get_client,
    search_pois,
    upsert_pois,
)
from app.services.embeddings import embed_text, embed_texts, get_dimension
from app.services.poi_indexing import SAMPLE_FILE, build_text, load_pois
from benchmarks.casos_teste import TESTES, posicao_esperada

# (rótulo, nome do modelo, coleção, prefixo das pesquisas, prefixo dos textos dos POIs)
MODELOS = [
    ("MiniLM", "paraphrase-multilingual-MiniLM-L12-v2", "exp_modelo_minilm", "", ""),
    ("MPNet", "paraphrase-multilingual-mpnet-base-v2", "exp_modelo_mpnet", "", ""),
    ("E5-small", "intfloat/multilingual-e5-small", "exp_modelo_e5", "query: ", "passage: "),
]


if __name__ == "__main__":
    client = get_client()
    pois = load_pois(SAMPLE_FILE)
    textos = [build_text(poi, "enriquecido") for poi in pois]

    posicoes = {}   # rótulo -> lista de posições, uma por pesquisa
    resumo = {}     # rótulo -> métricas finais

    for rotulo, modelo, colecao, prefixo_pesquisa, prefixo_texto in MODELOS:
        print(f"\n=== {rotulo} ===")

        # 1. Carregar o modelo e criar a coleção com a dimensão certa
        dimensao = get_dimension(modelo)
        create_collection(client, vector_size=dimensao, collection_name=colecao, recreate=True)

        # 2. Indexar os POIs
        vetores = embed_texts([prefixo_texto + t for t in textos], modelo)
        upsert_pois(client, pois, vetores, collection_name=colecao)

        # 3. Correr as pesquisas e medir
        posicoes[rotulo] = []
        tempos = []
        for texto, esperados in TESTES:
            inicio = time.perf_counter()
            vetor = embed_text(prefixo_pesquisa + texto, modelo)
            tempos.append(time.perf_counter() - inicio)

            resultados = search_pois(client, vetor, limit=len(pois), collection_name=colecao)
            posicoes[rotulo].append(posicao_esperada(resultados, esperados))

        resumo[rotulo] = {
            "dimensao": dimensao,
            "em_primeiro": sum(1 for p in posicoes[rotulo] if p == 1),
            "posicao_media": sum(posicoes[rotulo]) / len(posicoes[rotulo]),
            "ms_por_pesquisa": 1000 * sum(tempos) / len(tempos),
        }

    # Tabela por pesquisa
    rotulos = [m[0] for m in MODELOS]
    print()
    print(f"{'Pesquisa':<42}" + "".join(f"{r:>10}" for r in rotulos))
    print("-" * (42 + 10 * len(rotulos)))
    for i, (texto, _) in enumerate(TESTES):
        print(f"{texto:<42}" + "".join(f"{str(posicoes[r][i]):>10}" for r in rotulos))

    # Resumo
    print()
    print(f"{'Métrica':<32}" + "".join(f"{r:>10}" for r in rotulos))
    print("-" * (32 + 10 * len(rotulos)))
    print(f"{'Dimensão dos vetores':<32}" + "".join(f"{resumo[r]['dimensao']:>10}" for r in rotulos))
    print(f"{'Local certo em 1.º lugar':<32}" + "".join(f"{resumo[r]['em_primeiro']:>7}/{len(TESTES):<2}" for r in rotulos))
    print(f"{'Posição média do local certo':<32}" + "".join(f"{resumo[r]['posicao_media']:>10.2f}" for r in rotulos))
    print(f"{'Tempo médio por pesquisa (ms)':<32}" + "".join(f"{resumo[r]['ms_por_pesquisa']:>10.1f}" for r in rotulos))