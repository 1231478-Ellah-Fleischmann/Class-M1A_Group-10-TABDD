# Qdrant - estrutura do ponto

```mermaid
classDiagram
    class pois {
        UInt64 id  = poi.id do MySQL
        Float[384] vector
        String nome
        String cidade  (indice KEYWORD)
        String categoria  (indice KEYWORD)
    }
    note for pois "Distancia: cosseno · Modelo: intfloat/multilingual-e5-small"
```

Texto que gera o vetor (com o prefixo `passage: `):

```
passage: <Nome>. Categoria: <categoria>. Cidade: <cidade>. <Descrição>
```

As pesquisas usam o prefixo `query: `.