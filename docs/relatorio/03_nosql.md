# Base de dados NoSQL — MongoDB

*Responsável: Francisca*

## Modelo e decisões

**O que guarda.** Informação semiestruturada relacionada com os utilizadores da plataforma, nomeadamente as suas preferências turísticas e o histórico de atividade. O MongoDB permite armazenar estes dados em documentos BSON, oferecendo flexibilidade na organização da informação.

Os favoritos e os ratings são armazenados exclusivamente no MySQL, evitando duplicação de informação entre bases de dados.

**Como está organizada.** Duas collections:

- `user_profiles`: armazena os perfis e as preferências dos utilizadores.
- `user_interactions`: regista as atividades realizadas pelos utilizadores na plataforma, nomeadamente pesquisas e visualizações de POIs.

**Estrutura de `user_profiles`:**

| Campo | Tipo de dados | Descrição |
|---|---|---|
| `_id` | ObjectId | Identificador automático do documento |
| `user_id` | Long | Referência lógica a `utilizador.id` no MySQL |
| `interests` | Array de Strings | Interesses turísticos |
| `travel_style` | String | Estilo de viagem preferido |
| `budget_level` | String | Nível de orçamento |
| `preferred_activities` | Array de Strings | Atividades preferidas |

**Estrutura de `user_interactions`:**

| Campo | Tipo de dados | Descrição |
|---|---|---|
| `_id` | ObjectId | Identificador automático do documento |
| `event_id` | String | Identificador único do evento |
| `user_id` | Long | Referência lógica a `utilizador.id` no MySQL |
| `event_type` | String | Tipo de interação |
| `context` | Document / Object | Informação adicional sobre a interação |
| `timestamp` | Date | Data e hora da interação |

O campo `context` permite guardar informação variável consoante o tipo de evento. Por exemplo, numa pesquisa pode conter o campo `query` com o texto introduzido pelo utilizador; numa visualização pode conter o `poi_id` do POI consultado.

**Relações.**

- Um utilizador registado no MySQL pode ter um perfil na collection `user_profiles`.
- Um utilizador pode gerar várias interações, armazenadas na collection `user_interactions`.
- As duas collections relacionam-se através de `user_id`, que corresponde ao campo `utilizador.id` no MySQL.
- O `poi_id`, quando guardado no contexto de uma interação, referencia logicamente o identificador do POI no MySQL.

Estas relações são referências lógicas, não chaves estrangeiras impostas pelo MongoDB. A validação das referências é assegurada pela aplicação.

**Operações principais.**

- Leituras: consultar o perfil de um utilizador e recuperar as suas últimas interações.
- Escritas: criar e atualizar perfis, registar pesquisas e registar visualizações de POIs.
- Os favoritos e os ratings são consultados e atualizados no MySQL.

**Decisões de modelação e justificação**

| Decisão | Justificação |
|---|---|
| Separar os perfis e o histórico em duas collections | Têm finalidades e padrões de utilização diferentes. Os perfis são atualizados, enquanto o histórico recebe continuamente novos registos. |
| Utilizar arrays em `user_profiles` | Permite guardar vários interesses e atividades preferidas diretamente no documento do utilizador. |
| Utilizar um documento embutido em `context` | Permite armazenar informação adicional variável consoante o tipo de interação, sem obrigar todos os eventos a terem exatamente os mesmos campos. |
| Utilizar `user_id` como referência lógica | Permite associar os dados do MongoDB aos utilizadores do MySQL sem duplicar os seus dados principais. |
| Utilizar `poi_id` nas interações quando necessário | Permite relacionar o histórico com os POIs armazenados no MySQL. |
| Manter favoritos e ratings no MySQL | São relações entre utilizadores e POIs que beneficiam das chaves estrangeiras e das regras de integridade do modelo relacional. |

**Schema Design Patterns**

- **Embedding:** utilizado nos arrays de interesses e atividades preferidas de `user_profiles` e no documento `context` de `user_interactions`. Permite agrupar informação relacionada no mesmo documento.
- **Referencing:** utilizado através de `user_id` e `poi_id`, para relacionar os documentos com os dados existentes no MySQL.
- **Separação de collections:** permite gerir separadamente os perfis e o histórico, considerando os seus diferentes ciclos de vida e padrões de escrita.

**Desempenho**

- Índice único em `user_profiles(user_id)`, para localizar rapidamente o perfil e garantir que existe apenas um perfil por utilizador.
- Índice único em `user_interactions(event_id)`, para evitar eventos duplicados.
- Índice composto em `user_interactions(user_id, timestamp DESC)`, para filtrar pelo utilizador e ordenar o histórico do mais recente para o mais antigo.
- A consulta das últimas 20 interações utiliza o índice composto, reduzindo a necessidade de percorrer todos os documentos.

A avaliação do impacto dos índices será feita através de `explain("executionStats")`, comparando a mesma consulta antes e depois da criação do índice. Serão analisados o tempo de execução, o número de documentos examinados e o número de entradas do índice examinadas.

**Escalabilidade**

A collection `user_interactions` deverá apresentar um crescimento superior, uma vez que cada pesquisa ou visualização gera um novo documento. A separação do histórico dos perfis evita que o documento do utilizador cresça continuamente. O MongoDB também suporta replicação e sharding, que poderão ser considerados caso o volume de dados o justifique.

**Consistência**

O MongoDB não impõe chaves estrangeiras para os identificadores do MySQL. A aplicação é responsável por validar as referências lógicas entre as bases de dados.

Como não existem transações distribuídas entre MySQL, MongoDB e Qdrant, a consistência entre sistemas é coordenada pelo backend Python. Cada base mantém a sua própria fonte de verdade: o MySQL para utilizadores, POIs, favoritos e ratings; o MongoDB para preferências e histórico; e o Qdrant para embeddings e pesquisa semântica.

**Manutenção**

A separação das collections facilita a evolução independente dos perfis e do histórico. A estrutura flexível dos documentos permite acrescentar novas preferências ou informações contextuais às interações sem exigir alterações a todos os documentos existentes.

## Implementação

A comunicação entre a aplicação Python e o MongoDB é realizada através da biblioteca **PyMongo**.

A implementação está organizada em `app/repositories/nosql/mongodb_repository.py`, através da classe `MongoDBRepository`.

A ligação à base de dados é configurada através das variáveis de ambiente `MONGODB_URI` e `MONGODB_DATABASE`.

As principais operações implementadas/preparadas incluem:

- `get_profile()`: consulta o perfil de um utilizador.
- `save_profile()`: cria ou atualiza as preferências de um utilizador.
- `record_interaction()`: regista uma nova interação.
- `get_recent_interactions()`: consulta as interações mais recentes.
- `ensure_indexes()`: garante a criação dos índices necessários.
- `close()`: encerra a ligação à base de dados.

## Queries principais

**1. Consultar o perfil de um utilizador**

```python
profile = user_profiles.find_one({
    "user_id": 1
})
```

Procura o documento correspondente ao utilizador com o identificador `1` no MySQL.

**2. Criar ou atualizar um perfil**

```python
user_profiles.update_one(
    {"user_id": 1},
    {
        "$set": {
            "interests": ["culture", "nature"],
            "travel_style": "relaxed",
            "budget_level": "medium",
            "preferred_activities": ["museums", "walking"]
        }
    },
    upsert=True
)
```

Atualiza as preferências do utilizador ou cria o documento caso ainda não exista.

**3. Registar uma interação**

```python
from datetime import datetime, timezone

user_interactions.insert_one({
    "event_id": "E002",
    "user_id": 1,
    "event_type": "search",
    "context": {
        "query": "traditional restaurants in Porto"
    },
    "timestamp": datetime.now(timezone.utc)
})
```

Regista uma pesquisa no histórico de atividade do utilizador.

**4. Consultar as 20 interações mais recentes**

```python
interactions = list(
    user_interactions.find({"user_id": 1})
    .sort("timestamp", -1)
    .limit(20)
)
```

Devolve as 20 interações mais recentes do utilizador, utilizando o índice composto em `user_id` e `timestamp`.

**5. Criar os índices**

```python
user_profiles.create_index(
    [("user_id", 1)],
    unique=True
)

user_interactions.create_index(
    "event_id",
    unique=True
)

user_interactions.create_index([
    ("user_id", 1),
    ("timestamp", -1)
])
```

Estes índices permitem acelerar as consultas mais frequentes e evitar duplicação de perfis e eventos.

## Integração com as outras bases de dados

O backend Python coordena a comunicação entre MongoDB, MySQL e Qdrant.

- **Pesquisa em linguagem natural:** o Qdrant encontra POIs semanticamente semelhantes à pesquisa, o MySQL fornece os respetivos detalhes e o MongoDB regista a pesquisa no histórico.
- **Página de detalhe de um POI:** o MySQL fornece os dados do POI, o Qdrant encontra locais semelhantes e o MongoDB regista a visualização.
- **Recomendações personalizadas:** o MongoDB fornece as preferências e o histórico do utilizador, o Qdrant procura POIs semelhantes aos seus interesses e o MySQL fornece os detalhes e permite consultar favoritos e ratings.

Desta forma, o MongoDB complementa as restantes bases de dados, contribuindo para as funcionalidades integradas da Smart Tourism Platform.

## Justificação da escolha do MongoDB

A escolha do MongoDB foi motivada pela adequação do modelo documental à informação que será armazenada, nomeadamente as preferências e o histórico dos utilizadores.

Em comparação com o Amazon DynamoDB, o MongoDB oferece funcionalidades de consulta, agregação e indexação adequadas aos objetivos de modelação e experimentação deste projeto. A utilização da biblioteca PyMongo também facilita a integração com o backend Python.

Embora ambas as tecnologias sejam alternativas válidas, o MongoDB foi considerado mais adequado à organização dos dados e aos padrões de consulta previstos para esta componente.
