# Parte I — Esquemas e Arquitetura

Documento a apresentar na sessão de discussão da semana 9.

## 1. Funcionalidades e integrações

- Funcionalidades escolhidas:
- As 3 funcionalidades que integram mais de uma base (pelo menos uma com a BD vetorial):
  1.
  2.
  3.

## 2. Distribuição da informação pelas bases

| Dado | Base | Justificação |
|---|---|---|
| | | |

## 3. Modelos de dados

Para cada base: o que guarda, como se organiza, relações, operações, padrões de desenho, decisões de modelação e impacto em desempenho, escalabilidade e manutenção.

### 3.1 MySQL

**O que guarda.** Dados estruturados e com relações bem definidas: utilizadores, destinos, categorias, POIs (nome, morada, coordenadas, preço médio), favoritos e ratings.

**Como está organizada.** Seis tabelas (`utilizador`, `destino`, `categoria`, `poi`, `favorito`, `rating`). Diagrama ER em [`mysql_er.md`](mysql_er.md) e esquema executável em [`sql/schema.sql`](../../sql/schema.sql).

**Relações.**
- Um destino tem muitos POIs e uma categoria classifica muitos POIs (1:N).
- Utilizadores e POIs relacionam-se de forma N:M através de `favorito` e `rating`.

**Operações principais.**
- Leituras: listar POIs por destino e categoria, pesquisa por proximidade, rating médio de um POI, favoritos e ratings de um utilizador.
- Escritas: registar utilizador, adicionar ou remover favorito, criar ou alterar um rating.

#### Decisões de modelação e justificação

| Decisão | Justificação |
|---|---|
| Dados estruturados e relacionais no MySQL | Esquema fixo, relações bem definidas e necessidade de integridade referencial e de agregações (`AVG`, `JOIN`), que são o ponto forte do modelo relacional. |
| `poi.id` (`BIGINT UNSIGNED`) como identificador canónico das três bases | Permite cruzar MySQL, MongoDB e Qdrant sem ambiguidade. É compatível com os ids inteiros de 64 bits do Qdrant. |
| `UNIQUE (utilizador_id, poi_id)` e `CHECK (valor BETWEEN 1 AND 5)` em `rating` | Garante na própria base que um utilizador só avalia um POI uma vez e que o valor é válido, sem depender da aplicação. |
| `POINT SRID 4326` com `SPATIAL INDEX` em `poi` e `destino` | Pesquisa por proximidade sem percorrer a tabela toda. O SRID 4326 corresponde a coordenadas GPS (latitude, longitude). |
| Chaves estrangeiras em todas as relações | Impedem registos órfãos e mantêm a consistência dentro do MySQL. |
| `ON DELETE CASCADE` em `favorito` e `rating` | Apagar um utilizador ou um POI remove os registos associados. Só atua no MySQL (ver Consistência). |
| Rating individual guardado só no MySQL | Fonte única de verdade. O MongoDB guarda apenas o texto das reviews e referencia `poi_id` e `utilizador_id`, evitando duplicação e dados contraditórios. |

#### Desempenho

- Índices de chave primária e de unicidade (`email`, `(nome, pais)` em destino, `(utilizador_id, poi_id)` em rating).
- Índice composto `(destino_id, categoria_id)` em `poi`, para as listagens por destino e categoria.
- Índices em `rating(poi_id)` e `favorito(poi_id)`, para consultar por POI.
- A média dos ratings calcula-se com `AVG`. *(A confirmar: guardar a média numa coluna de `poi`, padrão Computed, se for uma consulta muito frequente.)*
- Na pesquisa por proximidade, filtra-se primeiro por uma caixa envolvente que usa o índice espacial e só depois se calcula a distância exata nos candidatos, porque `ST_Distance_Sphere` não usa o índice.

#### Escalabilidade

A tabela que mais cresce é `rating`. O acesso faz-se sempre por `poi_id` ou `utilizador_id`, ambos indexados, por isso o crescimento afeta sobretudo o tamanho dos índices e não a forma das consultas.

#### Consistência

O InnoDB garante transações ACID dentro do MySQL. Entre bases não há transações distribuídas: o `ON DELETE CASCADE` só limpa o MySQL, por isso, ao apagar ou alterar um POI, a aplicação atualiza também o documento no MongoDB e o vetor no Qdrant.

#### Manutenção

O esquema está versionado em `sql/schema.sql`, as regras de integridade estão na própria base (e não espalhadas pelo código) e a estrutura fixa torna as alterações explícitas e controladas.

### 3.2 MongoDB

### 3.3 Base de dados vetorial

## 4. Arquitetura da aplicação

- Diagrama (componentes, papel de cada base, interação entre sistemas)
- Fluxo de cada uma das 3 integrações
- Justificação das escolhas (tipo de dados, operações, desempenho, escalabilidade, flexibilidade, consistência, complexidade das queries)

## 5. Questões para a professora
