# Revisões à Parte I após o feedback

*Responsável: todo o grupo*

O enunciado pede que este relatório descreva as revisões feitas à Parte I depois da sessão de feedback (semana 9).
A versão apresentada na sessão está marcada no Git com a tag `parte1-feedback`; a diferença até à versão final pode ser vista com:

```
git diff parte1-feedback..main -- docs/parte1
```

## Feedback recebido

(resumir o feedback da professora)

## Alterações realizadas

| O que mudou | Porquê | Onde (ficheiro/secção) |
|---|---|---|
| Ratings passaram do MySQL para o MongoDB, junto dos comentários (padrão Subset) | Sugestão da professora: são lidos sempre com o POI e crescem sem limite | `sql/schema.sql` (tabela `rating` removida), secções 1, 2, 3.1, 4.2 e 4.3 |
| Localização (coordenadas) passou do MySQL para o MongoDB | Sugestão da professora: o MongoDB tem índices geoespaciais (2dsphere) e a localização fica junto dos ratings e comentários, no documento do POI; o MySQL fica só com dados estruturados e relações | `sql/schema.sql` (colunas `localizacao` e índices espaciais removidos), secções 1.1, 2, 3.1 e 4.3 |
| Descrição textual do POI ficou no MySQL (`poi.descricao`) | Fonte do texto que gera os embeddings, junto dos restantes dados do POI | `sql/schema.sql`, secções 2 e 3.1 |
