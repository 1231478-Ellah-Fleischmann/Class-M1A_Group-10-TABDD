"""Gráfico dos cenários de índices do MySQL.

Lê benchmarks/resultados/indices_mysql.csv (criado por benchmarks.indices_mysql)
e grava docs/relatorio/img/indices_mysql.png.
Um painel por cenário, todos com a MESMA escala: assim vê-se logo que só no
cenário 1 o índice faz diferença. Em cada barra: o tempo e as linhas lidas.

Correr a partir da raiz do repositório:
    python -m benchmarks.grafico_indices_mysql
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # gera a imagem sem abrir janelas
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

FICHEIRO_RESULTADOS = Path("benchmarks/resultados/indices_mysql.csv")
FICHEIRO_IMAGEM = Path("docs/relatorio/img/indices_mysql.png")

TITULOS = {
    "Cenário 1": "1. Quem guardou o POI 5\n(favorito, ~30 000 linhas)",
    "Cenário 2": "2. Museus do Porto\n(poi, 80 linhas)",
    "Cenário 3": "3. Ordem das colunas\n(poi, 80 linhas)",
}
AZUL, LARANJA = "#2a78d6", "#eb6834"         # usa o índice / não usa o índice
TEXTO, TEXTO_2, GRELHA = "#0b0b0b", "#52514e", "#e4e3df"


def numero(valor, casas):
    """Número no formato português (vírgula decimal, espaço nos milhares)."""
    return f"{valor:,.{casas}f}".replace(",", " ").replace(".", ",")


with open(FICHEIRO_RESULTADOS, encoding="utf-8") as f:
    linhas = list(csv.DictReader(f))

cenarios = list(dict.fromkeys(linha["cenario"] for linha in linhas))
fig, eixos = plt.subplots(1, len(cenarios), figsize=(11, 4.2), dpi=150, sharey=True)
maximo = max(float(linha["tempo_ms"]) for linha in linhas)
fig.patch.set_facecolor("white")

for eixo, cenario in zip(eixos, cenarios):
    versoes = [linha for linha in linhas if linha["cenario"] == cenario]
    tempos = [float(v["tempo_ms"]) for v in versoes]
    cores = [AZUL, LARANJA]  # 1.ª versão usa o índice, a 2.ª não

    eixo.bar(range(len(versoes)), tempos, width=0.45, color=cores, zorder=3)
    for i, v in enumerate(versoes):
        eixo.annotate(f"{numero(tempos[i], 2)} ms\n{numero(int(v['linhas']), 0)} linhas\nacesso: {v['acesso']}",
                      (i, tempos[i]), xytext=(0, 4), textcoords="offset points",
                      ha="center", va="bottom", fontsize=8.5, color=TEXTO)

    eixo.set_title(TITULOS.get(cenario, cenario), fontsize=10, color=TEXTO, loc="left")
    eixo.set_xticks(range(len(versoes)), [v["versao"] for v in versoes],
                    fontsize=9, color=TEXTO_2)
    eixo.set_ylim(0, maximo * 1.3)            # espaço para as etiquetas
    eixo.yaxis.set_major_formatter(FuncFormatter(lambda y, _: numero(y, 0)))
    eixo.tick_params(axis="y", labelsize=8, colors=TEXTO_2, length=0)
    eixo.tick_params(axis="x", length=0)
    eixo.grid(axis="y", color=GRELHA, linewidth=0.8, zorder=0)
    for lado in ("top", "right", "left"):
        eixo.spines[lado].set_visible(False)
    eixo.spines["bottom"].set_color(TEXTO_2)

eixos[0].set_ylabel("tempo médio (ms)", fontsize=8.5, color=TEXTO_2)
fig.legend(handles=[Patch(color=AZUL, label="usa o índice testado"),
                    Patch(color=LARANJA, label="não usa o índice testado")],
           loc="upper right", ncol=2, frameon=False, fontsize=9)
fig.suptitle("MySQL: tempo de execução com e sem índice", x=0.01, ha="left",
             fontsize=12, color=TEXTO, weight="bold")
fig.text(0.01, 0.01,
         "Tempo medido no servidor (EXPLAIN ANALYZE), média de 20 execuções. Mesma escala nos três painéis.\n"
         "Linhas e acesso vêm do EXPLAIN: ref = vai direto às linhas pelo índice; "
         "index = percorre o índice todo; ALL = lê a tabela toda.",
         fontsize=7.5, color=TEXTO_2)
fig.tight_layout(rect=(0, 0.07, 1, 0.93))

FICHEIRO_IMAGEM.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(FICHEIRO_IMAGEM)
print(f"Gráfico guardado em {FICHEIRO_IMAGEM}")