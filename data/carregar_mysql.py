"""Carrega os dados de teste no MySQL.

- POIs: os mesmos 80 POIs (e os mesmos ids) que o Qdrant usa
  (data/sample/pois_teste_modelos.json).
- Coordenadas: geradas perto do centro de cada cidade (dados sintéticos).
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

# Centro aproximado de cada cidade: (latitude, longitude, região)
CIDADES = {
    "Porto": (41.1496, -8.6109, "Norte"),
    "Braga": (41.5454, -8.4265, "Norte"),
    "Guimarães": (41.4425, -8.2918, "Norte"),
    "Viana do Castelo": (41.6932, -8.8329, "Norte"),
    "Aveiro": (40.6405, -8.6538, "Centro"),
    "Coimbra": (40.2033, -8.4103, "Centro"),
    "Lisboa": (38.7223, -9.1393, "Lisboa"),
    "Sintra": (38.8029, -9.3817, "Lisboa"),
    "Évora": (38.5714, -7.9135, "Alentejo"),
    "Faro": (37.0194, -7.9322, "Algarve"),
    "Lagos": (37.1028, -8.6730, "Algarve"),
}

random.seed(42)  # mesma semente = mesmos dados sempre que se corre

repo = MySQLRepository()
cursor = repo.conn.cursor()

# 1. Apagar dados antigos (pela ordem das chaves estrangeiras)
for tabela in ("favorito", "poi", "utilizador", "destino", "categoria"):
    cursor.execute(f"DELETE FROM {tabela}")

# 2. Destinos (um por cidade)
destino_id = {}
for nome, (lat, lon, regiao) in CIDADES.items():
    cursor.execute(
        "INSERT INTO destino (nome, pais, regiao, localizacao) "
        "VALUES (%s, 'Portugal', %s, ST_GeomFromText(%s, 4326))",
        (nome, regiao, f"POINT({lat} {lon})"),
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

    lat, lon, _ = CIDADES[poi["cidade"]]
    lat += random.uniform(-0.015, 0.015)  # cerca de 1,5 km à volta do centro
    lon += random.uniform(-0.015, 0.015)
    cursor.execute(
        "INSERT INTO poi (id, destino_id, categoria_id, nome, descricao, localizacao) "
        "VALUES (%s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))",
        (poi["id"], destino_id[poi["cidade"]], categoria_id[poi["categoria"]],
         poi["nome"], poi["descricao"], f"POINT({lat} {lon})"),
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