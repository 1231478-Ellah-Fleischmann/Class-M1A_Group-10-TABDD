# Design da Componente NoSQL — MongoDB

*Smart Tourism Platform · Tópicos Avançados de Bases de Dados*

## 1. Objetivo do MongoDB

No projeto Smart Tourism Platform, a componente NoSQL será implementada utilizando MongoDB, uma base de dados orientada a documentos que permite armazenar informação em estruturas BSON, oferecendo flexibilidade na organização dos dados.

A escolha do MongoDB justifica-se pelas características da informação associada aos utilizadores da plataforma, nomeadamente preferências pessoais e histórico de atividade. Estes dados podem apresentar estruturas diferentes e sofrer alterações ao longo da utilização da aplicação.

Assim, o MongoDB será utilizado para armazenar os perfis de preferências e as interações dos utilizadores. Os favoritos e os ratings permanecem no MySQL, que já contém as tabelas `favorito` e `rating`; esta decisão evita manter a mesma relação em duas bases de dados.

## 2. Organização dos dados

Para organizar a informação, serão utilizadas duas collections:

- `user_profiles`: armazena os perfis e as preferências dos utilizadores.
- `user_interactions`: regista as atividades realizadas pelos utilizadores na plataforma.

### 2.1. Diagrama de collections

```mermaid
classDiagram
    direction LR

    class user_profiles {
        ObjectId _id PK
        Long user_id
        Array~String~ interests
        String travel_style
        String budget_level
        Array~String~ preferred_activities
    }

    class user_interactions {
        ObjectId _id PK
        String event_id
        Long user_id
        String event_type
        Object context
        Date timestamp
    }

    user_profiles --> user_interactions : user_id

    note for user_interactions "context.query guarda o texto da pesquisa"
```

`user_id` é uma referência lógica ao identificador `BIGINT` de `utilizador.id` no MySQL. A relação entre perfil e interações também é lógica: o MongoDB não impõe chaves estrangeiras nem integridade referencial entre as collections ou entre bases de dados.

### 2.2. Perfis dos utilizadores — `user_profiles`

Esta collection guarda as preferências de cada utilizador, permitindo personalizar a sua experiência na plataforma.

| Campo | Tipo de dados | Descrição |
|---|---|---|
| `_id` | ObjectId | Identificador automático do documento |
| `user_id` | Inteiro de 64 bits | Referência lógica a `utilizador.id` no MySQL |
| `interests` | Array de Strings | Interesses do utilizador |
| `travel_style` | String | Estilo de viagem preferido |
| `budget_level` | String | Nível de orçamento |
| `preferred_activities` | Array de Strings | Atividades preferidas |

Exemplo de documento:

```javascript
{
    "user_id": 1,
    "interests": ["culture", "nature"],
    "travel_style": "relaxed",
    "budget_level": "medium",
    "preferred_activities": ["museums", "walking"]
}
```

Neste exemplo, o utilizador tem interesse em cultura e natureza, prefere viagens tranquilas e apresenta um orçamento médio.

Esta informação poderá ser utilizada para personalizar pesquisas e recomendações.

A utilização de arrays permite guardar vários interesses e atividades diretamente no documento do utilizador, evitando a necessidade de criar collections adicionais para estes elementos.

### 2.3. Histórico de atividade — `user_interactions`

Esta collection regista as interações dos utilizadores com a plataforma, incluindo pesquisas e visualizações de destinos.

| Campo | Tipo de dados | Descrição |
|---|---|---|
| `_id` | ObjectId | Identificador automático do documento |
| `event_id` | String | Identificador único do evento |
| `user_id` | Inteiro de 64 bits | Referência lógica a `utilizador.id` no MySQL |
| `event_type` | String | Tipo de interação |
| `context` | Document / Object | Informação adicional sobre a interação |
| `timestamp` | Date | Data e hora da interação |

Dentro do campo `context` podem existir diferentes atributos, dependendo do tipo de interação. Por exemplo, no caso de uma pesquisa, pode ser guardado o campo `query`, que contém o texto introduzido pelo utilizador.

Exemplo:

```javascript
{
    "event_id": "E001",
    "user_id": 1,
    "event_type": "search",
    "context": {
        "query": "museums and cultural activities"
    },
    "timestamp": ISODate("2026-10-19T11:00:00Z")
}
```

Este documento representa uma pesquisa realizada por um utilizador.

A utilização de um documento embutido no campo `context` permite armazenar informação adicional associada a cada evento, mantendo a estrutura flexível para diferentes tipos de interação.

O histórico é organizado através de documentos independentes, permitindo acrescentar novos eventos sem modificar os registos anteriores.

### 2.4. Relações entre os dados

As duas collections relacionam-se logicamente através do campo `user_id`.

Um utilizador pode ter um perfil em `user_profiles` e gerar vários registos em `user_interactions`.

O valor de `user_id` corresponde ao `utilizador.id` numérico do MySQL. Os favoritos e os ratings são geridos no MySQL; o MongoDB não mantém uma cópia desses dados.

## 3. Schema Design Patterns utilizados

Na modelação da componente MongoDB foram considerados diferentes padrões de organização de documentos.

### 3.1. Embedding

O padrão Embedding consiste em armazenar informação relacionada dentro do mesmo documento.

É utilizado em dois contextos:

- Na collection `user_profiles`, os interesses e as atividades preferidas são guardados em arrays dentro do documento do utilizador.
- Na collection `user_interactions`, o campo `context` permite armazenar informação adicional diretamente no documento do evento.

Esta abordagem reduz a necessidade de consultas adicionais para obter informação que está diretamente relacionada com o documento principal.

### 3.2. Referencing

O padrão Referencing consiste em utilizar identificadores para estabelecer relações entre documentos ou entidades armazenadas em diferentes collections ou bases de dados.

É utilizado através de `user_id`, que referencia logicamente o utilizador do MySQL. A aplicação valida a existência do utilizador quando necessário, pois esta referência não é uma chave estrangeira.

Esta decisão permite associar preferências e interações ao utilizador sem duplicar o seu registo relacional.

### 3.3. Separação de collections

A informação foi dividida em duas collections de acordo com a sua finalidade e comportamento.

Esta decisão permite tratar separadamente os perfis e o histórico de atividade.

Os perfis são atualizados ao longo do tempo, enquanto o histórico recebe continuamente novos registos.

Esta organização facilita a manutenção e evita que diferentes tipos de informação com ciclos de vida distintos sejam armazenados num único documento.

## 4. Operações que o MongoDB vai permitir

A comunicação entre a aplicação Python e o MongoDB será realizada através da biblioteca PyMongo.

As principais operações previstas incluem a criação e atualização de perfis e o registo e consulta do histórico de atividade. A gestão de favoritos é feita no MySQL.

### 4.1. Consultar o perfil de um utilizador

```python
profile = user_profiles.find_one({
    "user_id": 1
})
```

Esta operação procura o documento correspondente ao utilizador com `id` 1 no MySQL.

### 4.2. Criar ou atualizar um perfil

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

Esta operação permite atualizar as preferências de um utilizador. Caso o documento ainda não exista, a opção `upsert=True` permite criá-lo.

### 4.3. Registar uma interação

```python
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

Esta operação permite registar uma nova pesquisa realizada pelo utilizador, contribuindo para a construção do histórico de atividade.

### 4.4. Consultar as interações recentes

```python
interactions = list(
    user_interactions.find({"user_id": 1})
    .sort("timestamp", -1)
    .limit(20)
)
```

Esta operação devolve as 20 interações mais recentes do utilizador.

Estas operações estão reunidas em `app/repositories/nosql/mongodb_repository.py`, na classe `MongoDBRepository`. A ligação usa `MONGODB_URI` e `MONGODB_DATABASE`; se não forem definidos, assume `mongodb://localhost:27017` e `smart_tourism`.

```python
from app.repositories.nosql.mongodb_repository import MongoDBRepository

mongo = MongoDBRepository()
try:
    mongo.ensure_indexes()
    mongo.save_profile(
        user_id=1,
        interests=["culture", "nature"],
        travel_style="relaxed",
        budget_level="medium",
        preferred_activities=["museums", "walking"],
    )
    mongo.record_interaction(
        user_id=1,
        event_type="search",
        context={"query": "museums in Porto"},
    )
    profile = mongo.get_profile(user_id=1)
    history = mongo.get_recent_interactions(user_id=1)
finally:
    mongo.close()
```

## 5. Índices e desempenho

Os índices permitem melhorar a eficiência das consultas, reduzindo a necessidade de percorrer todos os documentos de uma collection.

Na modelação proposta, serão considerados índices de acordo com os padrões de acesso à informação.

### 5.1. Índice nos perfis dos utilizadores

Será considerado um índice único no campo `user_id` da collection `user_profiles`.

```python
user_profiles.create_index(
    [("user_id", 1)],
    unique=True
)
```

Este índice permite localizar rapidamente o perfil de um utilizador e garantir que não existem vários documentos de perfil com o mesmo identificador.

### 5.2. Índices no histórico de atividade

Na collection `user_interactions`, será criado um índice único em `event_id` e um índice composto em `user_id` e `timestamp`.

```python
user_interactions.create_index("event_id", unique=True)
user_interactions.create_index([
    ("user_id", 1),
    ("timestamp", -1)
])
```

O índice único evita duplicar eventos identificados pelo mesmo `event_id`. O índice composto permite filtrar pelo utilizador e obter as interações mais recentes primeiro.

O valor `1` representa uma ordenação ascendente e `-1` uma ordenação descendente.

### 5.3. Avaliação do impacto dos índices

Para avaliar o impacto do índice no histórico, será executada a mesma consulta antes e depois da sua criação.

```python
query = {"user_id": 1}

result = (
    user_interactions
    .find(query)
    .sort("timestamp", -1)
    .limit(20)
    .explain("executionStats")
)

print(result["executionStats"])
```

A consulta recupera as 20 interações mais recentes do utilizador e apresenta estatísticas relacionadas com a execução.

A análise deverá considerar indicadores como:

- `executionTimeMillis`: tempo de execução da consulta.
- `totalDocsExamined`: número de documentos analisados.
- `totalKeysExamined`: número de entradas do índice analisadas.

A comparação permitirá verificar se a utilização do índice reduz o número de documentos analisados e melhora o desempenho da consulta.

Os índices também introduzem custos adicionais de armazenamento e manutenção durante as operações de escrita. Por esse motivo, a sua utilização deverá ser justificada pelos padrões de consulta da aplicação.

## 6. Integração com as outras bases de dados

O MongoDB será integrado com o MySQL e o Qdrant através do backend Python, que será responsável por coordenar as operações entre os diferentes sistemas.

A integração permitirá desenvolver funcionalidades que utilizam informação proveniente de mais do que uma base de dados.

### 6.1. Pesquisa turística personalizada

Quando um utilizador realiza uma pesquisa, o backend poderá consultar as suas preferências no MongoDB.

Com base nessa informação, poderá utilizar o Qdrant para encontrar destinos semanticamente semelhantes aos interesses do utilizador.

Posteriormente, os identificadores canónicos dos POIs poderão ser utilizados para obter os detalhes estruturados no MySQL.

### 6.2. Consulta de atividade associada a POIs

O backend consulta no MongoDB o histórico de interações de um utilizador. Quando os eventos incluem um `poi_id` no campo `context`, esse identificador permite obter os dados estruturados do POI no MySQL.

Os favoritos não são guardados no MongoDB: são consultados no MySQL, onde existe a tabela `favorito`.

### 6.3. Recomendações personalizadas

O histórico armazenado no MongoDB poderá ser utilizado para identificar os interesses e os padrões de utilização da plataforma.

Esta informação poderá apoiar a geração de recomendações através do Qdrant, recorrendo a mecanismos de pesquisa por similaridade.

Os resultados poderão ser complementados com informação detalhada dos POIs armazenada no MySQL.

Desta forma, o MongoDB contribui para funcionalidades integradas, não funcionando apenas como um sistema isolado de armazenamento.

## 7. Justificação da escolha do MongoDB

Para a componente NoSQL, foram consideradas duas alternativas: MongoDB e Amazon DynamoDB.

Ambas permitem armazenar informação de forma flexível, mas apresentam diferenças na organização dos dados, nas operações suportadas e na gestão da infraestrutura.

| Critério | MongoDB | Amazon DynamoDB |
|---|---|---|
| Modelo de dados | Base de dados orientada a documentos BSON | Base de dados NoSQL de chave-valor e documentos |
| Flexibilidade | Permite documentos com campos e estruturas variáveis | Permite atributos flexíveis, considerando os padrões de acesso |
| Consultas | Suporta filtros, ordenação e operações de agregação | Otimizado para consultas baseadas em chaves e índices |
| Indexação | Suporta índices simples, compostos, únicos e outros tipos | Suporta índices secundários locais e globais |
| Desempenho | Depende das consultas, índices, volume de dados e configuração | Depende dos padrões de acesso, chaves, índices e capacidade configurada |
| Escalabilidade | Suporta replicação e sharding | Oferece escalabilidade gerida pela AWS |
| Implementação | Permite trabalhar com documentos e consultas através de Python e PyMongo | Integra-se com os serviços da AWS e respetivas ferramentas |

### 7.1. Justificação da decisão

A escolha do MongoDB foi motivada pela adequação do seu modelo documental aos dados que serão armazenados na componente dos utilizadores.

As preferências e o histórico de atividade apresentam características diferentes e podem evoluir ao longo da utilização da plataforma. O modelo documental permite organizar esta informação de forma flexível, sem exigir uma estrutura rígida para todos os documentos.

Outro fator relevante é a possibilidade de utilizar documentos embutidos e referências, permitindo escolher a organização mais adequada para cada tipo de informação.

A capacidade de criar índices simples e compostos também permite otimizar consultas específicas, como a recuperação do perfil e do histórico de atividade.

Além disso, a integração com Python através da biblioteca PyMongo facilita a comunicação entre o backend e a base de dados.

Em comparação com o Amazon DynamoDB, o MongoDB foi considerado mais adequado aos objetivos de modelação e experimentação definidos para esta componente do projeto, nomeadamente a utilização de documentos, diferentes padrões de consulta e mecanismos de indexação.

### 7.2. Impacto na performance, escalabilidade e manutenção

**Performance:** a utilização de documentos embutidos reduz a necessidade de consultas adicionais para obter informação relacionada. A criação de índices nos campos utilizados frequentemente nas pesquisas permite melhorar a eficiência das operações de leitura.

**Escalabilidade:** a separação dos perfis e do histórico em collections distintas permite gerir diferentes tipos de informação de acordo com as respetivas necessidades. O MongoDB suporta mecanismos de replicação e sharding, que poderão ser considerados caso o volume de dados e as necessidades da aplicação o justifiquem.

**Manutenção:** a separação da informação por finalidade facilita a compreensão e evolução do modelo. A estrutura flexível dos documentos permite acrescentar novos atributos, por exemplo novas preferências ou informações contextuais das interações, sem obrigar à alteração de todos os documentos existentes.

## 8. Conclusão

A utilização do MongoDB na Smart Tourism Platform permite armazenar e gerir informação relacionada com os utilizadores de forma flexível e adequada às características dos dados.

A criação das collections `user_profiles` e `user_interactions` permite separar diferentes tipos de informação, tendo em consideração os respetivos padrões de utilização.

A utilização dos padrões Embedding e Referencing permite equilibrar a eficiência das consultas com a redução da duplicação de informação.

A integração com MySQL e Qdrant, através do backend Python, possibilita a utilização dos dados dos utilizadores em pesquisas personalizadas e mecanismos de recomendação. Os favoritos e ratings são mantidos no MySQL.

Assim, o MongoDB desempenha um papel importante na arquitetura de persistência da aplicação, complementando as restantes bases de dados e contribuindo para a implementação de uma plataforma turística integrada.