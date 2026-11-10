"""
Prepara as coleções do benchmark de índices no Qdrant.

Cria duas coleções com os MESMOS pontos sintéticos:
  - bench_sem_indice: sem índices de payload
  - bench_com_indice: com índices de payload em 'cidade' e 'categoria'
A coleção 'pois' da aplicação não é tocada.

Uso: python -m benchmarks.qdrant_indices_preparar [N]   (por defeito, N = 50000)
"""
import sys
import time
from pathlib import Path

import numpy as np
from qdrant_client.models import (
    CollectionStatus, Distance, OptimizersConfigDiff, PayloadSchemaType, VectorParams,
)

from app.repositories.vector.qdrant_repository import get_client
from app.services.embeddings import embed_documents
from app.services.poi_indexing import build_text, load_pois

COLECAO_SEM_INDICE = "bench_sem_indice"
COLECAO_COM_INDICE = "bench_com_indice"
POIS_BASE = Path("data/sample/pois_teste_modelos.json")
RUIDO = 0.03     # quanto cada variação se afasta do POI original
SEMENTE = 42     # mesma semente = mesmos dados sempre que se corre
# Tamanho (KB) a partir do qual um segmento recebe HNSW. O valor por defeito (10 000 KB)
# deixava os nossos segmentos (~9,6 MB cada) sem índice. Com 1000 KB todos o recebem.
LIMIAR_INDEXACAO_KB = 1000

# Percentagem de pontos em cada cidade (distribuição desigual, como na realidade)
PESOS_CIDADES = {
    "Lisboa": 25, "Porto": 20, "Faro": 10, "Lagos": 8, "Sintra": 8, "Braga": 7,
    "Coimbra": 7, "Évora": 5, "Guimarães": 4, "Viana do Castelo": 4, "Aveiro": 2,
}


def gerar_pontos(n: int) -> tuple[np.ndarray, list[dict]]:
    """Gera n vetores (variações dos 80 POIs reais) e os respetivos payloads."""
    rng = np.random.default_rng(SEMENTE)

    pois = load_pois(POIS_BASE)
    base = np.array(
        embed_documents([build_text(p, "enriquecido") for p in pois]), dtype=np.float32
    )

    # Cada ponto novo é uma variação de um POI real escolhido ao acaso
    escolhidos = rng.integers(0, len(pois), size=n)
    ruido = rng.normal(0, RUIDO, size=(n, base.shape[1])).astype(np.float32)
    vetores = base[escolhidos] + ruido
    vetores /= np.linalg.norm(vetores, axis=1, keepdims=True)  # normalizar (cosseno)

    cidades = list(PESOS_CIDADES)
    pesos = np.array(list(PESOS_CIDADES.values()), dtype=float)
    cidades_sorteadas = rng.choice(cidades, size=n, p=pesos / pesos.sum())

    payloads = [
        {
            "nome": f"{pois[i]['nome']} #{k}",
            "cidade": str(cidade),
            "categoria": pois[i]["categoria"],
        }
        for k, (i, cidade) in enumerate(zip(escolhidos, cidades_sorteadas))
    ]
    return vetores, payloads


def criar_colecao(client, nome: str, vetores: np.ndarray, payloads: list[dict], com_indice: bool) -> None:
    """(Re)cria a coleção e carrega os pontos. Os índices de payload são criados ANTES dos pontos."""
    if client.collection_exists(nome):
        client.delete_collection(nome)

    client.create_collection(
        collection_name=nome,
        vectors_config=VectorParams(size=vetores.shape[1], distance=Distance.COSINE),
        optimizers_config=OptimizersConfigDiff(indexing_threshold=LIMIAR_INDEXACAO_KB),
    )

    if com_indice:
        for campo in ("cidade", "categoria"):
            client.create_payload_index(
                collection_name=nome, field_name=campo, field_schema=PayloadSchemaType.KEYWORD
            )

    client.upload_collection(
        collection_name=nome,
        vectors=vetores,
        payload=payloads,
        ids=list(range(1, len(payloads) + 1)),
        batch_size=256,
    )


def esperar_indexacao(client, nome: str, timeout: int = 600) -> None:
    """Espera até o Qdrant acabar de construir o HNSW (estado GREEN)."""
    inicio = time.time()
    time.sleep(2)  # dar tempo ao otimizador para arrancar
    while time.time() - inicio < timeout:
        info = client.get_collection(nome)
        if info.status == CollectionStatus.GREEN and (info.indexed_vectors_count or 0) > 0:
            print(
                f"  {nome}: {info.points_count} pontos, "
                f"{info.indexed_vectors_count} no HNSW, "
                f"{info.segments_count} segmentos, "
                f"índices de payload: {list(info.payload_schema) or 'nenhum'}"
            )
            return
        print(f"  ... estado {info.status}, {info.indexed_vectors_count or 0}/{info.points_count} no HNSW")
        time.sleep(2)
    print(f"  ATENÇÃO: {nome} ainda não acabou de indexar ao fim de {timeout}s.")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50_000
    client = get_client()

    print(f"A gerar {n} pontos sintéticos...")
    vetores, payloads = gerar_pontos(n)

    for nome, com_indice in [(COLECAO_SEM_INDICE, False), (COLECAO_COM_INDICE, True)]:
        print(f"A criar '{nome}' ({'com' if com_indice else 'sem'} índices de payload)...")
        t0 = time.perf_counter()
        criar_colecao(client, nome, vetores, payloads, com_indice)
        esperar_indexacao(client, nome)
        print(f"  pronta em {time.perf_counter() - t0:.1f}s")