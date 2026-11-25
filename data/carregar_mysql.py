"""Carrega os dados de teste no MySQL.

- POIs: os mesmos 80 POIs (e os mesmos ids) que o Qdrant usa
  (data/sample/pois_teste_modelos.json).
- A localização (coordenadas) fica no MongoDB, não aqui.
- Utilizadores e favoritos: gerados aleatoriamente (dados sintéticos).

Apaga os dados que existam e volta a carregar tudo, por isso pode correr-se várias vezes.
Correr a partir da raiz do repositório:
    python -m data.carregar_mysql
"""

import json
import random

from app.repositories.mysql.mysql_repository import MySQLRepository

FICHEIRO_POIS = "data/sample/pois_teste_modelos.json"
NUM_UTILIZADORES = 2000
MAX_FAVORITOS_POR_UTILIZADOR = 30

# Região de cada cidade
CIDADES = {
    "Porto": "Norte",
    "Braga": "Norte",
    "Guimarães": "Norte",
    "Viana do Castelo": "Norte",
    "Aveiro": "Centro",
    "Coimbra": "Centro",
    "Lisboa": "Lisboa",
    "Sintra": "Lisboa",
    "Évora": "Alentejo",
    "Faro": "Algarve",
    "Lagos": "Algarve",
}

random.seed(42)  # mesma semente = mesmos dados sempre que se corre

repo = MySQLRepository()
cursor = repo.conn.cursor()

# 1. Apagar dados antigos (pela ordem das chaves estrangeiras)
for tabela in ("favorito", "poi", "utilizador", "destino", "categoria"):
    cursor.execute(f"DELETE FROM {tabela}")

# 2. Destinos (um por cidade)
destino_id = {}
for nome, regiao in CIDADES.items():
    cursor.execute(
        "INSERT INTO destino (nome, pais, regiao) VALUES (%s, 'Portugal', %s)",
        (nome, regiao),
    )
    destino_id[nome] = cursor.lastrowid

# 3. Categorias e POIs (com os ids do ficheiro)
with open(FICHEIRO_POIS, encoding="utf-8") as f:
    pois = json.load(f)

categoria_id = {}
for poi in pois:
    if poi["categoria"] not in categoria_id:
        cursor.execute("INSERT INTO categoria (nome) VALUES (%s)", (poi["categoria"],))
        categoria_id[poi["categoria"]] = cursor.lastrowid

    cursor.execute(
        "INSERT INTO poi (id, destino_id, categoria_id, nome, descricao) "
        "VALUES (%s, %s, %s, %s, %s)",
        (poi["id"], destino_id[poi["cidade"]], categoria_id[poi["categoria"]],
         poi["nome"], poi["descricao"]),
    )

# 4. Utilizadores
paises = ["Portugal", "Espanha", "França", "Brasil", "Reino Unido", "Alemanha"]
utilizadores = [(f"Utilizador {i}", f"utilizador{i}@exemplo.pt", random.choice(paises))
                for i in range(1, NUM_UTILIZADORES + 1)]
cursor.executemany(
    "INSERT INTO utilizador (nome, email, pais_origem) VALUES (%s, %s, %s)", utilizadores
)
cursor.execute("SELECT id FROM utilizador")
ids_utilizadores = [linha[0] for linha in cursor.fetchall()]

# 5. Favoritos (cada utilizador guarda entre 0 e 30 POIs diferentes)
ids_pois = [poi["id"] for poi in pois]
favoritos = []
for u in ids_utilizadores:
    for p in random.sample(ids_pois, random.randint(0, MAX_FAVORITOS_POR_UTILIZADOR)):
        favoritos.append((u, p))
cursor.executemany("INSERT INTO favorito (utilizador_id, poi_id) VALUES (%s, %s)", favoritos)

repo.conn.commit()

# Atualizar as estatísticas que o MySQL usa para escolher os índices
# (depois de mudar muitos dados, como recomendado na aula).
cursor.execute("ANALYZE TABLE destino, categoria, poi, utilizador, favorito")
cursor.fetchall()

# 6. Verificação
print("Linhas carregadas:")
for tabela in ("destino", "categoria", "poi", "utilizador", "favorito"):
    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
    print(f"  {tabela:<11} {cursor.fetchone()[0]}")

cursor.execute("SELECT id FROM poi ORDER BY id")
ids_mysql = [linha[0] for linha in cursor.fetchall()]
print("Ids dos POIs iguais aos do ficheiro do Qdrant:", ids_mysql == sorted(ids_pois))

cursor.close()
repo.close()