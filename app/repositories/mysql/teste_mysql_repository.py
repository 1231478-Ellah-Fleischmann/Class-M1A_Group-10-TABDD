"""Teste do repositório MySQL.

Cria dados de teste (nomes começados por TESTE_), verifica as funções e apaga tudo no fim.
Correr a partir da raiz do repositório:
    python -m app.repositories.mysql.teste_mysql_repository
"""

from app.repositories.mysql.mysql_repository import MySQLRepository


def verificar(condicao, descricao):
    print(("OK     " if condicao else "FALHA  ") + descricao)


repo = MySQLRepository()

# Dados de teste
cat = repo.criar_categoria("TESTE_monumento")
porto = repo.criar_destino("TESTE_Porto", "Portugal", 41.1496, -8.6109)
clerigos = repo.criar_poi(porto, cat, "TESTE_Clérigos", 41.1458, -8.6145, descricao="Torre barroca.")
bolhao = repo.criar_poi(porto, cat, "TESTE_Bolhão", 41.1497, -8.6058)
moledo = repo.criar_poi(porto, cat, "TESTE_Moledo", 41.8389, -8.8667)
ana = repo.criar_utilizador("TESTE_Ana", "teste_ana@exemplo.pt")

try:
    poi = repo.obter_poi(clerigos)
    verificar(round(poi["latitude"], 4) == 41.1458 and round(poi["longitude"], 4) == -8.6145,
              "coordenadas lidas = coordenadas gravadas")

    verificar(len(repo.listar_pois(porto)) == 3, "listar_pois devolve os 3 POIs do destino")

    ids = [p["id"] for p in repo.obter_pois_por_ids([moledo, clerigos])]
    verificar(ids == [moledo, clerigos], "obter_pois_por_ids mantém a ordem pedida")

    repo.adicionar_favorito(ana, clerigos)
    repo.adicionar_favorito(ana, clerigos)
    verificar(repo.listar_favoritos(ana) == [clerigos], "o mesmo favorito não fica duplicado")

    # Só os POIs de teste (a base pode ter outros POIs perto, carregados pelo script de dados)
    nomes = [p["nome"] for p in repo.pois_proximos(41.1458, -8.6145, raio_m=1000)
             if p["nome"].startswith("TESTE_")]
    verificar(nomes == ["TESTE_Clérigos", "TESTE_Bolhão"],
              "pois_proximos: só os que estão a menos de 1 km, por distância")
finally:
    # Limpeza (os favoritos são apagados em cascata)
    for poi_id in (clerigos, bolhao, moledo):
        repo.escrever("DELETE FROM poi WHERE id = %s", (poi_id,))
    repo.escrever("DELETE FROM utilizador WHERE id = %s", (ana,))
    repo.escrever("DELETE FROM destino WHERE id = %s", (porto,))
    repo.escrever("DELETE FROM categoria WHERE id = %s", (cat,))
    repo.close()
    print("Dados de teste apagados.")