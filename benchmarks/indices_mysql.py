"""Cenários de análise de índices no MySQL.

Cenários 1 e 2: a mesma consulta COM e SEM o índice.
"Sem índice" usa IGNORE INDEX: o MySQL é obrigado a não usar aquele índice,
sem alterar o esquema (não se apaga nada).
Cenário 3: num índice de duas colunas, a pesquisa só pela 2.ª coluna
não consegue usar a árvore do índice (FORCE INDEX obriga a tentar).

Os tempos vêm do EXPLAIN ANALYZE, que mede a execução dentro do servidor.
Assim, o tempo da rede (casa -> servidor do DEI) não entra na comparação.

Correr a partir da raiz do repositório (depois de data.carregar_mysql):
    python -m benchmarks.indices_mysql
Os resultados ficam em benchmarks/resultados/indices_mysql.csv
(o gráfico faz-se com: python -m benchmarks.grafico_indices_mysql).
"""

import csv
import re
import statistics
from pathlib import Path

from app.repositories.mysql.mysql_repository import MySQLRepository

REPETICOES = 20
FICHEIRO_RESULTADOS = Path("benchmarks/resultados/indices_mysql.csv")

# Cada cenário compara duas versões da mesma pesquisa.
# %(destino)s e %(categoria)s são substituídos pelo id do Porto e da categoria "museu".
CENARIOS = [
    {
        "titulo": "Cenário 1 - quem guardou o POI 5 nos favoritos (tabela favorito, ~30 000 linhas)",
        "versoes": [
            ("com índice", "SELECT COUNT(*) FROM favorito WHERE poi_id = 5"),
            ("sem índice", "SELECT COUNT(*) FROM favorito IGNORE INDEX (ix_favorito_poi) "
                           "WHERE poi_id = 5"),
        ],
    },
    {
        "titulo": "Cenário 2 - museus do Porto (tabela poi, 80 linhas)",
        "versoes": [
            ("com índice", "SELECT id, nome FROM poi "
                           "WHERE destino_id = %(destino)s AND categoria_id = %(categoria)s"),
            ("sem índice", "SELECT id, nome FROM poi IGNORE INDEX (ix_poi_destino_categoria) "
                           "WHERE destino_id = %(destino)s AND categoria_id = %(categoria)s"),
        ],
    },
    {
        "titulo": "Cenário 3 - ordem das colunas no índice (destino_id, categoria_id)",
        "versoes": [
            ("1.ª coluna", "SELECT id, nome FROM poi FORCE INDEX (ix_poi_destino_categoria) "
                           "WHERE destino_id = %(destino)s"),
            ("só 2.ª col.", "SELECT id, nome FROM poi FORCE INDEX (ix_poi_destino_categoria) "
                            "WHERE categoria_id = %(categoria)s"),
        ],
    },
]


def plano(cursor, sql, params):
    """Tipo de acesso, índice usado e nº de linhas que o MySQL estima ler (EXPLAIN)."""
    cursor.execute("EXPLAIN " + sql, params)
    colunas = [c[0] for c in cursor.description]
    linha = dict(zip(colunas, cursor.fetchone()))
    return linha["type"], linha["key"], linha["rows"]


def tempo_servidor_ms(cursor, sql, params):
    """Tempo da consulta medido pelo servidor (EXPLAIN ANALYZE), em milissegundos."""
    cursor.execute("EXPLAIN ANALYZE " + sql, params)
    texto = cursor.fetchone()[0]
    # A 1.ª linha do plano tem "actual time=início..fim": o fim é o tempo total.
    return float(re.search(r"actual time=[\d.]+\.\.([\d.]+)", texto).group(1))


repo = MySQLRepository()
cursor = repo.conn.cursor()

cursor.execute("SELECT id FROM destino WHERE nome = 'Porto'")
porto = cursor.fetchone()[0]
cursor.execute("SELECT id FROM categoria WHERE nome = 'museu'")
museu = cursor.fetchone()[0]

ids = {"destino": porto, "categoria": museu}
resultados = []

for cenario in CENARIOS:
    print("\n" + cenario["titulo"])
    print(f"  {'':<13}{'acesso':<8}{'índice usado':<26}{'linhas (estim.)':>16}{'tempo médio':>14}")
    for rotulo, sql in cenario["versoes"]:
        tipo, indice, linhas = plano(cursor, sql, ids)
        tempos = [tempo_servidor_ms(cursor, sql, ids) for _ in range(REPETICOES)]
        print(f"  {rotulo:<13}{tipo:<8}{str(indice):<26}{linhas:>16}"
              f"{statistics.mean(tempos):>11.3f} ms")
        resultados.append({"cenario": cenario["titulo"].split(" - ")[0], "versao": rotulo,
                           "acesso": tipo, "indice": indice, "linhas": linhas,
                           "tempo_ms": round(statistics.mean(tempos), 3)})

print(f"\n(tempo médio de {REPETICOES} execuções, medido no servidor)")

# Guardar os resultados (para o gráfico e para o relatório)
FICHEIRO_RESULTADOS.parent.mkdir(parents=True, exist_ok=True)
with open(FICHEIRO_RESULTADOS, "w", newline="", encoding="utf-8") as f:
    escritor = csv.DictWriter(f, fieldnames=resultados[0].keys())
    escritor.writeheader()
    escritor.writerows(resultados)
print(f"Resultados guardados em {FICHEIRO_RESULTADOS}")
cursor.close()
repo.close()