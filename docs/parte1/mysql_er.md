# MySQL - diagrama ER (rascunho)

```mermaid
erDiagram
  DESTINO   ||--o{ POI        : contem
  CATEGORIA ||--o{ POI        : classifica
  UTILIZADOR ||--o{ FAVORITO  : guarda
  POI        ||--o{ FAVORITO  : e_guardado
  UTILIZADOR ||--o{ RATING    : avalia
  POI        ||--o{ RATING    : e_avaliado

  UTILIZADOR { bigint id PK
    varchar nome
    varchar email UK
    varchar pais_origem
    datetime data_registo }
  DESTINO { int id PK
    varchar nome
    varchar pais
    varchar regiao
    point localizacao }
  CATEGORIA { smallint id PK
    varchar nome UK }
  POI { bigint id PK
    int destino_id FK
    smallint categoria_id FK
    varchar nome
    varchar morada
    point localizacao
    decimal preco_medio }
  FAVORITO { bigint utilizador_id PK
    bigint poi_id PK
    datetime data_adicionado }
  RATING { bigint id PK
    bigint utilizador_id FK
    bigint poi_id FK
    tinyint valor
    datetime data }
```

## Pontos a discutir com o grupo
- `poi.id` e o identificador canonico usado no MongoDB e no Qdrant.
- O rating individual fica so no MySQL (fonte de verdade); o MongoDB guarda o texto das reviews e referencia `poi_id` e `utilizador_id`.
- Restricao `UNIQUE (utilizador_id, poi_id)` em `rating`: um utilizador so avalia um POI uma vez.
- Indices espaciais em `poi` e `destino` (pesquisa por proximidade); indice composto `(destino_id, categoria_id)` em `poi`.
