# Parte I — Esquemas e Arquitetura

Documento a apresentar na sessão de discussão da semana 9.

## 1. Funcionalidades e integrações

### 1.1 Funcionalidades

| # | Funcionalidade | Bases envolvidas |
|---|---|---|
| 1 | Pesquisa em linguagem natural (semântica) | Qdrant, MySQL, MongoDB |
| 2 | Página de detalhe do POI, com "locais semelhantes" | MySQL, Qdrant, MongoDB |
| 3 | Recomendações personalizadas | MySQL, MongoDB, Qdrant |
| 4 | Pesquisa por proximidade | MySQL |
| 5 | Navegar destinos, categorias e POIs | MySQL |
| 6 | Favoritos | MySQL, MongoDB |
| 7 | Ratings | MySQL |
| 8 | Registo, perfil e preferências | MySQL, MongoDB |

As reviews (texto dos comentários) ficam fora do âmbito: o projeto usa apenas ratings.

### 1.2 Funcionalidades que integram várias bases

**1. Pesquisa em linguagem natural.** O Qdrant devolve os POIs semanticamente mais próximos do texto (com filtro por cidade e categoria). O MySQL fornece os dados estruturados desses POIs (nome, coordenadas, rating médio). O MongoDB regista a pesquisa no histórico do utilizador.

**2. Página de detalhe do POI.** O MySQL fornece os dados base e a média dos ratings. O Qdrant devolve "locais semelhantes" a partir do vetor do próprio POI. O MongoDB regista a visualização.

**3. Recomendações personalizadas.** O MongoDB fornece as preferências e o histórico do utilizador. O MySQL fornece favoritos e ratings. O Qdrant procura POIs semelhantes aos que o utilizador valorizou. O MySQL exclui o que já viu e devolve os detalhes.

## 2. Distribuição da informação pelas bases

**Princípio:** cada BD tem uma única fonte de verdade. O que se repete entre bases são identificadores (`poi_id`, `user_id`) e os campos de filtro no Qdrant.

| Dado | Base | Justificação |
|---|---|---|
| Utilizadores (nome, email, país, data de registo) | MySQL | Estrutura fixa, `email` único e referenciado por favoritos e ratings. |
| Destinos e categorias | MySQL | Dados de referência pequenos e estáveis, usados em junções e filtros. |
| POIs: dados estruturados (nome, morada, coordenadas, preço médio, destino, categoria) | MySQL | Esquema fixo e relações N:1. Coordenadas em `POINT` com índice espacial. `poi.id` é o identificador canónico das três bases. |
| Descrição textual do POI | MySQL *(a confirmar)* | Fonte do texto que gera os embeddings; fica junto dos restantes dados do POI. |
| Favoritos | MySQL | Relação N:M com chave composta que impede duplicados. |
| Ratings (1 a 5) | MySQL | Relação N:M com `UNIQUE (utilizador_id, poi_id)` e `CHECK`; agregações (`AVG`) são o ponto forte do relacional. |
| Preferências do utilizador (interesses, estilo de viagem, orçamento, atividades) | MongoDB (`user_profiles`) | Estrutura flexível e variável; arrays no próprio documento. |
| Histórico de atividade (pesquisas, visualizações) | MongoDB (`user_interactions`) | Escritas frequentes e campo `context` flexível consoante o tipo de evento. |
| Embeddings dos POIs (vetores) | Qdrant | Pesquisa por similaridade (distância do cosseno). Dados derivados: recalculáveis a partir da descrição. |
| Payload no Qdrant (`nome`, `cidade`, `categoria`) | Qdrant | Permite filtrar a pesquisa semântica por cidade e categoria, com índice no Qdrant. |

**Consequências:** não há transações entre bases, por isso a consistência fica a cargo da aplicação (por exemplo, ao apagar um POI, remover também o vetor no Qdrant). A duplicação é controlada: só se repetem identificadores e os três campos do payload do Qdrant.

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
