"""
Mede o impacto dos índices no Qdrant (correr depois de qdrant_indices_preparar).

Para cada filtro, cada coleção (sem / com índices de payload) e cada modo
(HNSW ou pesquisa exata), corre as 50 pesquisas de teste várias vezes e mede:
  - tempo no SERVIDOR (campo 'time' da resposta do Qdrant): mediana e p95, em ms
  - tempo no CLIENTE (inclui o pedido HTTP): mediana, em ms
  - recall@10 em relação à pesquisa exata

Usa a API REST do Qdrant diretamente, porque o cliente Python não expõe o campo 'time'.

Uso: python -m benchmarks.qdrant_indices_medir
"""
import statistics
import time
from datetime import date
from pathlib import Path

import httpx

from app.repositories.vector.qdrant_repository import VECTOR_API_KEY, VECTOR_HOST, VECTOR_PORT
from app.services.embeddings import embed_query
from benchmarks.casos_teste import carregar_testes
from benchmarks.qdrant_indices_preparar import COLECAO_COM_INDICE, COLECAO_SEM_INDICE

K = 10            # número de resultados por pesquisa
REPETICOES = 5    # quantas vezes se repete cada pesquisa

# 127.0.0.1 em vez de "localhost": no Windows, "localhost" tenta primeiro IPv6, o que atrasa cada pedido
HOST = "127.0.0.1" if VECTOR_HOST == "localhost" else VECTOR_HOST
http = httpx.Client(
    base_url=f"http://{HOST}:{VECTOR_PORT}",
    headers={"api-key": VECTOR_API_KEY} if VECTOR_API_KEY else {},
    timeout=60,
)


def filtro(**campos) -> dict:
    """filtro(cidade="Lisboa") -> filtro do Qdrant em JSON, com uma condição obrigatória por campo."""
    return {"must": [{"key": k, "match": {"value": v}} for k, v in campos.items()]}


FILTROS = {
    "sem filtro": None,
    "cidade=Lisboa (pouco seletivo)": filtro(cidade="Lisboa"),
    "cidade=Aveiro + categoria=bar (muito seletivo)": filtro(cidade="Aveiro", categoria="bar"),
}
MODOS = {"HNSW": False, "exata": True}


def contar(colecao: str, filtro_: dict | None) -> int:
    corpo = {"exact": True, **({"filter": filtro_} if filtro_ else {})}
    r = http.post(f"/collections/{colecao}/points/count", json=corpo)
    r.raise_for_status()
    return r.json()["result"]["count"]


def pesquisar(colecao: str, vetor: list[float], filtro_: dict | None, exata: bool):
    """Faz uma pesquisa e devolve (ms no cliente, ms no servidor, lista de ids)."""
    corpo = {
        "query": vetor,
        "limit": K,
        "with_payload": False,
        "params": {"exact": exata},
        **({"filter": filtro_} if filtro_ else {}),
    }
    t0 = time.perf_counter()
    r = http.post(f"/collections/{colecao}/points/query", json=corpo)
    ms_cliente = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    dados = r.json()
    ms_servidor = dados["time"] * 1000  # o Qdrant devolve o tempo em segundos
    return ms_cliente, ms_servidor, [p["id"] for p in dados["result"]["points"]]


def percentil(valores: list[float], p: int) -> float:
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, round(p / 100 * (len(ordenados) - 1)))]


if __name__ == "__main__":
    testes = carregar_testes(Path("benchmarks/casos_teste_modelos.json"))
    vetores = [embed_query(texto) for texto, _ in testes]

    linhas = []

    def mostrar(texto: str = "") -> None:
        """Escreve no ecrã e guarda a linha para o ficheiro de resultados."""
        print(texto)
        linhas.append(texto)

    mostrar(f"Benchmark de índices no Qdrant - {date.today()}")
    mostrar(f"{len(vetores)} pesquisas x {REPETICOES} repetições, top {K}.")
    mostrar("servidor = campo 'time' do Qdrant; cliente = inclui o pedido HTTP.")

    for nome_filtro, f in FILTROS.items():
        mostrar()
        mostrar(f"=== {nome_filtro}: {contar(COLECAO_COM_INDICE, f)} pontos cumprem o filtro ===")

        # Resposta "verdadeira": a pesquisa exata (os dados são iguais nas duas coleções)
        verdade = [set(pesquisar(COLECAO_COM_INDICE, v, f, True)[2]) for v in vetores]

        mostrar(f"{'coleção':<18}{'modo':<7}{'servidor med':>14}{'servidor p95':>14}"
                f"{'cliente med':>13}{'recall@10':>11}")
        for colecao in (COLECAO_SEM_INDICE, COLECAO_COM_INDICE):
            for nome_modo, exata in MODOS.items():
                for v in vetores[:5]:                 # aquecimento (não conta)
                    pesquisar(colecao, v, f, exata)

                t_cliente, t_servidor, recalls = [], [], []
                for _ in range(REPETICOES):
                    for v, certos in zip(vetores, verdade):
                        ms_c, ms_s, ids = pesquisar(colecao, v, f, exata)
                        t_cliente.append(ms_c)
                        t_servidor.append(ms_s)
                        recalls.append(len(certos & set(ids)) / len(certos) if certos else 1.0)

                mostrar(
                    f"{colecao:<18}{nome_modo:<7}"
                    f"{statistics.median(t_servidor):>14.3f}{percentil(t_servidor, 95):>14.3f}"
                    f"{statistics.median(t_cliente):>13.2f}{statistics.mean(recalls):>11.3f}"
                )

    ficheiro = Path(f"benchmarks/resultados/qdrant_indices_{date.today()}.txt")
    ficheiro.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nResultados guardados em {ficheiro}")