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
porto = repo.criar_destino("TESTE_Porto", "Portugal")
clerigos = repo.criar_poi(porto, cat, "TESTE_Clérigos", descricao="Torre barroca.")
bolhao = repo.criar_poi(porto, cat, "TESTE_Bolhão")
moledo = repo.criar_poi(porto, cat, "TESTE_Moledo")
ana = repo.criar_utilizador("TESTE_Ana", "teste_ana@exemplo.pt")

try:
    poi = repo.obter_poi(clerigos)
    verificar(poi["descricao"] == "Torre barroca." and poi["destino"] == "TESTE_Porto",
              "obter_poi devolve a descrição e o nome do destino")

    verificar(len(repo.listar_pois(porto)) == 3, "listar_pois devolve os 3 POIs do destino")

    ids = [p["id"] for p in repo.obter_pois_por_ids([moledo, clerigos])]
    verificar(ids == [moledo, clerigos], "obter_pois_por_ids mantém a ordem pedida")

    repo.adicionar_favorito(ana, clerigos)
    repo.adicionar_favorito(ana, clerigos)
    verificar(repo.listar_favoritos(ana) == [clerigos], "o mesmo favorito não fica duplicado")
finally:
    # Limpeza (os favoritos são apagados em cascata)
    for poi_id in (clerigos, bolhao, moledo):
        repo.escrever("DELETE FROM poi WHERE id = %s", (poi_id,))
    repo.escrever("DELETE FROM utilizador WHERE id = %s", (ana,))
    repo.escrever("DELETE FROM destino WHERE id = %s", (porto,))
    repo.escrever("DELETE FROM categoria WHERE id = %s", (cat,))
    repo.close()
    print("Dados de teste apagados.")