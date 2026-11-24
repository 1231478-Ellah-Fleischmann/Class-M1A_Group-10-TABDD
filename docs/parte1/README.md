# Parte I — Esquemas e Arquitetura

Documento a apresentar na sessão de discussão da semana 9.

## 1. Funcionalidades e integrações

### 1.1 Funcionalidades

| # | Funcionalidade | Bases envolvidas |
|---|---|---|
| 1 | Pesquisa em linguagem natural (semântica) | Qdrant, MySQL, MongoDB |
| 2 | Página de detalhe do POI, com "locais semelhantes" | MySQL, Qdrant, MongoDB |
| 3 | Recomendações personalizadas | MySQL, MongoDB, Qdrant |
| 4 | Pesquisa por proximidade | MongoDB |
| 5 | Navegar destinos, categorias e POIs | MySQL |
| 6 | Favoritos | MySQL, MongoDB |
| 7 | Ratings e comentários | MongoDB |
| 8 | Registo, perfil e preferências | MySQL, MongoDB |

Os ratings e comentários dos POIs ficam no MongoDB, no documento do POI (padrão Subset).

### 1.2 Funcionalidades que integram várias bases

**1. Pesquisa em linguagem natural.** O Qdrant devolve os POIs semanticamente mais próximos do texto (com filtro por cidade e categoria). O MySQL fornece os dados estruturados desses POIs (nome, descrição) e o MongoDB o rating médio. O MongoDB regista também a pesquisa no histórico do utilizador.

**2. Página de detalhe do POI.** O MySQL fornece os dados base. O MongoDB fornece o rating médio e os comentários mais recentes. O Qdrant devolve "locais semelhantes" a partir do vetor do próprio POI. O MongoDB regista a visualização.

**3. Recomendações personalizadas.** O MongoDB fornece as preferências, o histórico e os ratings do utilizador. O MySQL fornece os favoritos. O Qdrant procura POIs semelhantes aos que o utilizador valorizou. O MySQL exclui o que já viu e devolve os detalhes.

## 2. Distribuição da informação pelas bases

**Princípio:** cada BD tem uma única fonte de verdade. O que se repete entre bases são identificadores (`poi_id`, `user_id`) e os campos de filtro no Qdrant.

| Dado | Base | Justificação |
|---|---|---|
| Utilizadores (nome, email, país, data de registo) | MySQL | Estrutura fixa, `email` único e referenciado por favoritos. |
| Destinos e categorias | MySQL | Dados de referência pequenos e estáveis, usados em junções e filtros. |
| POIs: dados estruturados (nome, morada, preço médio, destino, categoria) | MySQL | Esquema fixo e relações N:1. `poi.id` é o identificador canónico das três bases. |
| Descrição textual do POI | MySQL | Fonte do texto que gera os embeddings; fica junto dos restantes dados do POI. |
| Favoritos | MySQL | Relação N:M com chave composta que impede duplicados. |
| Ratings e comentários dos POIs | MongoDB | Lidos sempre com o POI; os mais recentes ficam no documento do POI e os antigos numa coleção à parte (padrão Subset). |
| Localização dos POIs (coordenadas) | MongoDB | Guardada no documento do POI, com índice geoespacial (`2dsphere`) para a pesquisa por proximidade. |
| Preferências do utilizador (interesses, estilo de viagem, orçamento, atividades) | MongoDB (`user_profiles`) | Estrutura flexível e variável; arrays no próprio documento. |
| Histórico de atividade (pesquisas, visualizações) | MongoDB (`user_interactions`) | Escritas frequentes e campo `context` flexível consoante o tipo de evento. |
| Embeddings dos POIs (vetores) | Qdrant | Pesquisa por similaridade (distância do cosseno). Dados derivados: recalculáveis a partir da descrição. |
| Payload no Qdrant (`nome`, `cidade`, `categoria`) | Qdrant | Permite filtrar a pesquisa semântica por cidade e categoria, com índice no Qdrant. |

**Consequências:** não há transações entre bases, por isso a consistência fica a cargo da aplicação (por exemplo, ao apagar um POI, remover também o documento no MongoDB e o vetor no Qdrant). A duplicação é controlada: só se repetem identificadores e os três campos do payload do Qdrant.

## 3. Modelos de dados

Para cada base: o que guarda, como se organiza, relações, operações, padrões de desenho, decisões de modelação e impacto em desempenho, escalabilidade e manutenção.

### 3.1 MySQL (base relacional)

**O que guarda.** Dados estruturados e com relações bem definidas: utilizadores, destinos, categorias, POIs (nome, morada, descrição, preço médio) e favoritos.

**Como está organizada.** Cinco tabelas (`utilizador`, `destino`, `categoria`, `poi`, `favorito`). Diagrama ER em [`mysql_er.md`](mysql_er.md) e esquema executável em [`sql/schema.sql`](../../sql/schema.sql).

**Relações.**
- Um destino tem muitos POIs e uma categoria classifica muitos POIs (1:N).
- Utilizadores e POIs relacionam-se de forma N:M através de `favorito`.

**Operações principais.**
- Leituras: listar POIs por destino e categoria, obter um POI, obter vários POIs pelos ids devolvidos pelo Qdrant, favoritos de um utilizador.
- Escritas: registar utilizador, adicionar ou remover favorito.

#### Decisões de modelação e justificação

| Decisão | Justificação |
|---|---|
| Dados estruturados e relacionais no MySQL | Esquema fixo, relações bem definidas e necessidade de integridade referencial e de `JOIN`, que são o ponto forte do modelo relacional. |
| `poi.id` (`BIGINT UNSIGNED`) como identificador canónico das três bases | Permite cruzar MySQL, MongoDB e Qdrant sem ambiguidade. É compatível com os ids inteiros de 64 bits do Qdrant. |
| Descrição textual no `poi` | Fica junto dos restantes dados do POI e é a fonte do texto que gera os embeddings. |
| Localização fora do MySQL | Após o feedback, as coordenadas passaram para o MongoDB, que também tem índices geoespaciais. O MySQL fica só com dados estruturados e relações. |
| Chave primária `(utilizador_id, poi_id)` em `favorito` | Um utilizador não pode guardar o mesmo POI duas vezes. |
| Chaves estrangeiras e `ON DELETE CASCADE` em `favorito` | Impedem registos órfãos: apagar um utilizador ou um POI remove os seus favoritos. Só atua no MySQL (ver Consistência). |
| Ratings e comentários fora do MySQL | Após o feedback, passaram para o MongoDB, junto do POI (padrão Subset): são lidos sempre com o POI e crescem sem limite. |

#### Desempenho

- Índices de chave primária e de unicidade (`email`, `(nome, pais)` em destino).
- Índice composto `(destino_id, categoria_id)` em `poi`, para as listagens por destino e categoria.
- Índice em `favorito(poi_id)`; a chave primária `(utilizador_id, poi_id)` serve as consultas por utilizador.
- Os índices foram testados em `benchmarks/indices_mysql.py` (ver relatório, análise de índices).

#### Escalabilidade

A tabela que mais cresce é `favorito`. O acesso faz-se sempre por `utilizador_id` ou `poi_id`, ambos indexados. A tabela `poi` cresce devagar.

#### Consistência

O InnoDB garante transações ACID dentro do MySQL. Entre bases não há transações distribuídas: ao apagar um POI, a aplicação remove também o documento no MongoDB (ratings e comentários) e o vetor no Qdrant.

#### Manutenção

O esquema está versionado em `sql/schema.sql`, as regras de integridade estão na própria base (e não espalhadas pelo código) e a estrutura fixa torna as alterações explícitas e controladas.

### 3.2 MongoDB

**O que guarda.** Dados flexíveis relacionados com os utilizadores, nomeadamente as suas preferências de viagem e o histórico de atividade na plataforma. O MongoDB guarda informação que pode variar de utilizador para utilizador e que não necessita de relações rígidas, complementando os dados estruturados armazenados no MySQL.

**Como está organizada.** Duas coleções: `user_profiles` e `user_interactions`.

- `user_profiles`: guarda as preferências de cada utilizador, incluindo interesses, estilo de viagem, orçamento e atividades preferidas.
- `user_interactions`: guarda o histórico de atividade, como pesquisas e visualizações de POIs, incluindo o tipo de evento, a data e um objeto `context` com informação adicional que depende da interação.

**Relações.**

- Cada documento de `user_profiles` está associado a um utilizador do MySQL através do campo `user_id`.
- Cada documento de `user_interactions` também referencia um utilizador através de `user_id`.
- Quando uma interação envolve um POI, o campo `context` pode guardar o respetivo `poi_id`, que corresponde ao identificador do POI no MySQL e no Qdrant.
- Estas referências são lógicas: o MongoDB não impõe chaves estrangeiras nem integridade referencial entre bases de dados.

**Operações principais.**

- Leituras: consultar as preferências de um utilizador e recuperar as suas interações mais recentes.
- Escritas: criar ou atualizar preferências e registar novas pesquisas ou visualizações.
- Atualizações: modificar os interesses, o estilo de viagem, o orçamento ou as atividades preferidas de um utilizador.

#### Decisões de modelação e justificação

| Decisão | Justificação |
|---|---|
| Separação em `user_profiles` e `user_interactions` | As preferências são atualizadas ocasionalmente, enquanto o histórico recebe novos eventos frequentemente. A separação permite gerir cada tipo de informação de forma independente. |
| Arrays em `user_profiles` | Permitem guardar vários interesses e atividades preferidas diretamente no documento, sem criar coleções adicionais. |
| Campo `context` em `user_interactions` | Permite guardar informação variável conforme o tipo de evento, sem obrigar todos os documentos a terem exatamente os mesmos campos. |
| Referência através de `user_id` | Permite associar os documentos ao utilizador existente no MySQL sem duplicar os seus dados pessoais. |
| Referência a POIs através de `poi_id` | Permite relacionar as interações com os POIs do MySQL e do Qdrant, mantendo o MySQL como fonte de verdade dos dados estruturados. |
| Identificadores `user_id` do tipo Long | Mantêm a compatibilidade com os identificadores `BIGINT` utilizados no MySQL. |

#### Desempenho

- Índice único em `user_profiles(user_id)`, para localizar rapidamente as preferências de um utilizador e garantir que existe apenas um perfil por utilizador.
- Índice único em `user_interactions(event_id)`, para evitar o registo duplicado do mesmo evento.
- Índice composto em `user_interactions(user_id, timestamp DESC)`, para consultar eficientemente o histórico recente de um utilizador.
- A utilização destes índices reduz a quantidade de documentos examinados nas consultas mais frequentes, embora introduza algum custo adicional nas operações de escrita e no armazenamento.

#### Escalabilidade

A coleção `user_interactions` deverá crescer mais rapidamente, uma vez que cada pesquisa ou visualização pode gerar um novo documento. A estrutura flexível do MongoDB permite adicionar novos tipos de interação e novos campos ao objeto `context` sem alterar um esquema rígido. Caso o volume de dados aumente significativamente, poderá ser considerada a utilização de *sharding*.

#### Consistência

O MongoDB mantém a consistência das operações dentro da própria base de dados, mas não existem transações distribuídas com o MySQL ou o Qdrant. Os campos `user_id` e `poi_id` são referências lógicas, pelo que a aplicação é responsável por garantir que correspondem a registos existentes nas restantes bases. O MySQL continua a ser a fonte de verdade dos dados dos utilizadores e dos POIs.

#### Manutenção

A utilização de duas coleções com responsabilidades distintas facilita a manutenção e a evolução do modelo. A estrutura flexível permite introduzir novos campos nas preferências ou novos tipos de interação sem alterações complexas. Os índices devem ser revistos à medida que os padrões de consulta e o volume de dados evoluem.

### 3.3 Base de dados vetorial (Qdrant)

**O que guarda.** Um vetor (embedding) por POI, que representa o significado do texto do POI, e um pequeno payload com campos de filtro. O Qdrant não é fonte de verdade de nenhum dado: é uma cópia derivada, que pode ser recalculada a partir dos dados do POI no MySQL.

**Como está organizada.** Uma coleção `pois`. Cada ponto tem como `id` o `poi.id` do MySQL, um vetor de 384 dimensões e o payload `nome`, `cidade` e `categoria`. Diagrama em [`qdrant_ponto.md`](qdrant_ponto.md). O texto que gera o vetor junta nome, categoria, cidade e descrição ("texto enriquecido").

**Relações.** Não há relações dentro do Qdrant. A ligação às outras bases faz-se só pelo identificador: o `id` do ponto é o `poi.id`, e os `poi_id` dos favoritos (MySQL) e dos ratings e eventos (MongoDB) servem como exemplos positivos e negativos nas recomendações.

**Operações principais.**
- Indexação: gerar os embeddings em lote e fazer `upsert`; recriar a coleção quando muda o modelo ou o formato do texto.
- Pesquisa semântica: converter a pergunta em vetor e devolver os k POIs mais próximos, com filtro opcional por cidade e categoria.
- Locais semelhantes (página do POI): pesquisa a partir do vetor do próprio POI, em dois blocos: "nesta cidade" (filtro pela cidade) e "noutros destinos" (exclui a cidade).
- Recomendação personalizada: positivos = favoritos e ratings ≥ 4; negativos = ratings ≤ 2; exclui POIs já vistos. Utilizador novo (cold start): pesquisa semântica com as categorias preferidas guardadas no MongoDB.
- Manutenção: `upsert` do ponto quando um POI muda e `delete` quando é apagado.

#### Decisões de modelação e justificação

| Decisão | Justificação |
|---|---|
| Qdrant como base vetorial | Base dedicada a vetores, com filtros por payload durante a pesquisa, API de recomendação com exemplos positivos e negativos e cliente Python. Corre em Docker. |
| Modelo `intfloat/multilingual-e5-small` (384 dimensões) | Os dados e as pesquisas estão em português e inglês. É pequeno e corre em CPU. Numa experiência com 80 POIs e 50 pesquisas acertou no 1.º resultado em 37/50 e ficou no top 5 em 46/50. |
| Prefixos `query:` e `passage:` | O E5 foi treinado com estes prefixos; sem eles a qualidade desce. |
| Texto enriquecido (nome, categoria, cidade, descrição) | Pesquisas como "museu no Porto" passam a encontrar POIs pela categoria e pela cidade, e não só pela descrição. |
| Distância do cosseno | Mede a semelhança de significado independentemente do tamanho do vetor; é a métrica para que o E5 foi treinado. |
| `id` do ponto = `poi.id` | Não é preciso uma tabela de correspondência; o Qdrant aceita inteiros de 64 bits, compatíveis com `BIGINT UNSIGNED`. |
| Payload mínimo com índices `KEYWORD` em `cidade` e `categoria` | Filtrar na própria pesquisa vetorial, sem ir ao MySQL. É a única duplicação de dados (controlada). |
| Estratégia `best_score` nas recomendações personalizadas | Com `average_vector`, um utilizador com dois gostos diferentes (ex.: praias e museus) recebia resultados "a meio caminho" que não correspondiam a nenhum dos gostos; `best_score` respeita cada gosto. |
| Ordenar por ranking e não usar um limiar fixo de semelhança | Os scores do E5 ficam muito próximos (cerca de 0,85 a 0,92), por isso um limiar fixo não separa bem resultados bons de maus. |

#### Desempenho

- Índice HNSW (o padrão do Qdrant): pesquisa aproximada que não compara a pergunta com todos os vetores.
- Os índices de payload permitem aplicar os filtros durante a pesquisa, em vez de filtrar depois e perder resultados.
- Cada vetor ocupa cerca de 1,5 KB (384 × 4 bytes); 10 000 POIs ocupam cerca de 15 MB de vetores.
- O passo mais lento é calcular o embedding da pergunta; o modelo é carregado uma única vez.

#### Escalabilidade

O número de POIs cresce devagar, ao contrário dos ratings e dos eventos. Se fosse preciso, o Qdrant suporta modo distribuído (shards e réplicas) e quantização para reduzir a memória.

#### Consistência

Não há transações entre o Qdrant e o MySQL: a aplicação faz o `upsert` ou o `delete` do ponto quando o POI muda. Se as duas bases ficarem diferentes, basta reindexar, porque os dados do Qdrant são derivados.

#### Manutenção

O servidor corre em Docker (`qdrant/qdrant:v1.20.0`, com volume para os dados). A indexação é um script que se pode repetir (`--recriar`). Mudar de modelo obriga a reindexar todos os POIs, porque muda o espaço vetorial e pode mudar a dimensão.

## 4. Arquitetura da aplicação

### 4.1 Componentes

Diagrama em [`arquitetura.md`](arquitetura.md).

A aplicação é um backend em Python organizado em camadas:

- **Serviços:** implementam as funcionalidades (pesquisa semântica, página do POI, recomendações, gestão de utilizadores, favoritos e ratings). São a única camada que combina dados de várias bases.
- **Repositórios:** um por base de dados. Escondem os detalhes de cada sistema (SQL, PyMongo, qdrant-client), para os serviços não dependerem da tecnologia.
- **Modelo de embeddings:** transforma texto em vetores de 384 dimensões. É usado na pesquisa semântica, no cold start das recomendações e na indexação. Os "locais semelhantes" não precisam dele, porque usam o vetor já guardado do POI.
- **Script de indexação:** lê os POIs do MySQL, gera os vetores e guarda-os no Qdrant. Volta a correr quando muda o modelo ou o formato do texto.

**Papel de cada base:**

| Base | Papel |
|---|---|
| MySQL | Fonte de verdade dos dados estruturados: utilizadores, destinos, categorias, POIs e favoritos. Cria o `poi.id` e o `utilizador.id`. |
| MongoDB | Preferências e histórico de atividade do utilizador, e ratings e comentários dos POIs, com estrutura flexível. |
| Qdrant | Vetores dos POIs para pesquisa por semelhança e recomendações. Cópia derivada do MySQL. |

**Princípios da interação entre sistemas:**

- As bases não comunicam entre si: é sempre o backend que consulta cada uma e junta os resultados.
- A ligação entre bases faz-se por identificadores comuns (`poi_id`, `user_id`), criados no MySQL.
- Não há transações distribuídas: a consistência entre bases é responsabilidade da aplicação (ver secção 2).

### 4.2 Fluxo das integrações

Diagramas de sequência em [`arquitetura.md`](arquitetura.md).

**1. Pesquisa em linguagem natural.** O serviço converte a pergunta num vetor (prefixo `query:`), e o Qdrant devolve os `poi_id` mais próximos, com filtro opcional por cidade e categoria. O MySQL devolve os dados estruturados desses POIs numa só consulta (`WHERE id IN (...)`) e o MongoDB o rating médio. O MongoDB regista a pesquisa no histórico. A ordem final é a do Qdrant (semelhança).

**2. Página do POI.** O MySQL devolve os dados do POI. O MongoDB devolve o rating médio e os comentários mais recentes, guardados no documento do POI (padrão Subset). O Qdrant faz duas recomendações a partir do vetor guardado do próprio POI: uma filtrada pela cidade ("nesta cidade") e outra que a exclui ("noutros destinos"). Fizemos dois blocos porque, numa só lista, a categoria pesava mais do que a cidade e os resultados misturavam destinos. O MongoDB regista a visualização.

**3. Recomendações personalizadas.** O MongoDB fornece os interesses do perfil, os POIs já vistos e os ratings do utilizador; o MySQL fornece os favoritos. Favoritos e ratings ≥ 4 são exemplos positivos e ratings ≤ 2 são negativos. O Qdrant recomenda POIs próximos dos positivos e afastados dos negativos (estratégia `best_score`), excluindo os já vistos. Sem positivos (utilizador novo), usa-se a pesquisa semântica com os interesses como texto; como o modelo é multilingue, interesses em inglês encontram POIs descritos em português. O MySQL devolve os detalhes.

### 4.3 Justificação das escolhas

| Critério | MySQL | MongoDB | Qdrant |
|---|---|---|---|
| Tipo de dados | Estruturados, esquema fixo | Semiestruturados, campos variáveis | Vetores densos + payload pequeno |
| Operações | `JOIN`, integridade referencial | Escritas frequentes de eventos, leitura do perfil por `user_id` | Pesquisa por semelhança (k vizinhos mais próximos) com filtros |
| Desempenho | Índices B-tree (chave primária, únicos, compostos e em chaves estrangeiras) | Índices `user_id` e `(user_id, timestamp)` | Índice HNSW (aproximado) + índices de payload |
| Escalabilidade | Cresce sobretudo `favorito`, sempre acedida por chaves indexadas | Histórico cresce sem limite; suporta sharding | Nº de POIs cresce devagar; suporta shards e quantização |
| Flexibilidade | Baixa (alterar o esquema é explícito) | Alta (novos campos sem migração) | Mudar de modelo obriga a reindexar |
| Consistência | ACID, fonte de verdade | Referências lógicas, validadas pela aplicação | Cópia derivada, consistência eventual |
| Complexidade das queries | SQL declarativo, junções complexas | Filtros e agregações sobre documentos | Uma operação de semelhança + filtro |

**Alternativa considerada.** Usar uma só base (por exemplo, PostgreSQL com `JSONB` e `pgvector`) simplificava a consistência, porque haveria transações entre todos os dados. Escolhemos a persistência poliglota para usar o sistema mais adequado a cada tipo de dado, que é o objetivo do projeto. Aceitamos em troca mais componentes para gerir e a consistência entre bases a cargo da aplicação.

## 5. Questões para a professora
### Base de dados vetorial

1. **Payload por nome ou por id.** O payload guarda `cidade` e `categoria` em texto, para filtrar sem ir ao MySQL. A alternativa é guardar `destino_id` e `categoria_id`, que não ficam desatualizados se um nome mudar, mas obrigam a converter nomes em ids antes de cada pesquisa. Qual das opções é preferível?
2. **Sincronização com o MySQL.** O Qdrant é uma cópia derivada: a aplicação faz `upsert`/`delete` do ponto quando o POI muda e, se as bases divergirem, reindexa-se tudo. Esta consistência eventual é aceitável, ou espera-se um mecanismo mais forte (por exemplo, uma fila de eventos)?
3. **Avaliação da pesquisa semântica.** Medimos a qualidade com 50 pesquisas de teste sobre 80 POIs (acerto no 1.º resultado e no top 5). Chega, ou espera-se outra métrica (por exemplo, recall@k ou MRR) ou um conjunto maior?
4. **Cenário de índices no Qdrant.** Para a análise de índices pensamos comparar a pesquisa com filtro com e sem índice de payload, e a pesquisa HNSW com a pesquisa exata (`exact=True`). Algum destes cenários é o mais adequado?
5. **Limiar de semelhança.** Os scores do E5 ficam muito próximos (0,85 a 0,92), por isso ordenamos por ranking (top k) e não usamos um limiar fixo. Esta abordagem é adequada?