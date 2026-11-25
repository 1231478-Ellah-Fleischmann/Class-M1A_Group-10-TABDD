"""Repositório MySQL: todas as consultas da aplicação à base relacional.

Os serviços não escrevem SQL: chamam estas funções.
A ligação usa as variáveis MYSQL_* do ficheiro .env.

A localização dos POIs (coordenadas) está no MongoDB.
"""

import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Leitura base de um POI: dados do POI e nome do destino e da categoria.
# (Os ratings e comentários estão no MongoDB.)
SELECT_POI = """
    SELECT p.id, p.nome, p.morada, p.descricao, p.preco_medio,
           d.nome AS destino, c.nome AS categoria
    FROM poi p
    JOIN destino d   ON d.id = p.destino_id
    JOIN categoria c ON c.id = p.categoria_id
"""


class MySQLRepository:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
        )

    def close(self):
        self.conn.close()

    # --- auxiliares -------------------------------------------------------
    def ler(self, sql, params=()):
        """Executa um SELECT e devolve uma lista de dicionários."""
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        linhas = cursor.fetchall()
        cursor.close()
        return linhas

    def escrever(self, sql, params=()):
        """Executa um INSERT/UPDATE/DELETE, grava (commit) e devolve o id criado."""
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        return novo_id

    # --- utilizadores -----------------------------------------------------
    def criar_utilizador(self, nome, email, pais_origem=None):
        return self.escrever(
            "INSERT INTO utilizador (nome, email, pais_origem) VALUES (%s, %s, %s)",
            (nome, email, pais_origem),
        )

    def obter_utilizador(self, utilizador_id):
        linhas = self.ler("SELECT * FROM utilizador WHERE id = %s", (utilizador_id,))
        return linhas[0] if linhas else None

    # --- destinos e categorias --------------------------------------------
    def criar_destino(self, nome, pais, regiao=None):
        return self.escrever(
            "INSERT INTO destino (nome, pais, regiao) VALUES (%s, %s, %s)",
            (nome, pais, regiao),
        )

    def criar_categoria(self, nome):
        return self.escrever("INSERT INTO categoria (nome) VALUES (%s)", (nome,))

    def listar_destinos(self):
        return self.ler("SELECT id, nome, pais, regiao FROM destino ORDER BY nome")

    def listar_categorias(self):
        return self.ler("SELECT id, nome FROM categoria ORDER BY nome")

    # --- POIs -------------------------------------------------------------
    def criar_poi(self, destino_id, categoria_id, nome,
                  morada=None, descricao=None, preco_medio=None, poi_id=None):
        """poi_id é opcional: permite usar o mesmo id que o POI tem no Qdrant."""
        return self.escrever(
            "INSERT INTO poi (id, destino_id, categoria_id, nome, morada, descricao, preco_medio) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (poi_id, destino_id, categoria_id, nome, morada, descricao, preco_medio),
        )

    def obter_poi(self, poi_id):
        """Página do POI: dados estruturados do POI."""
        linhas = self.ler(SELECT_POI + " WHERE p.id = %s", (poi_id,))
        return linhas[0] if linhas else None

    def obter_pois_por_ids(self, ids):
        """Detalhes dos POIs devolvidos pelo Qdrant, pela mesma ordem (semelhança)."""
        if not ids:
            return []
        marcadores = ", ".join(["%s"] * len(ids))
        linhas = self.ler(SELECT_POI + f" WHERE p.id IN ({marcadores})", tuple(ids))
        por_id = {linha["id"]: linha for linha in linhas}
        return [por_id[i] for i in ids if i in por_id]

    def listar_pois(self, destino_id, categoria_id=None):
        """Navegar: POIs de um destino, opcionalmente de uma categoria."""
        if categoria_id is None:
            return self.ler(SELECT_POI + " WHERE p.destino_id = %s ORDER BY p.nome",
                            (destino_id,))
        return self.ler(SELECT_POI + " WHERE p.destino_id = %s AND p.categoria_id = %s "
                        "ORDER BY p.nome", (destino_id, categoria_id))

    # --- favoritos --------------------------------------------------------
    def adicionar_favorito(self, utilizador_id, poi_id):
        # INSERT IGNORE: se o favorito já existir, não dá erro nem duplica.
        self.escrever("INSERT IGNORE INTO favorito (utilizador_id, poi_id) VALUES (%s, %s)",
                      (utilizador_id, poi_id))

    def remover_favorito(self, utilizador_id, poi_id):
        self.escrever("DELETE FROM favorito WHERE utilizador_id = %s AND poi_id = %s",
                      (utilizador_id, poi_id))

    def listar_favoritos(self, utilizador_id):
        linhas = self.ler("SELECT poi_id FROM favorito WHERE utilizador_id = %s",
                          (utilizador_id,))
        return [linha["poi_id"] for linha in linhas]