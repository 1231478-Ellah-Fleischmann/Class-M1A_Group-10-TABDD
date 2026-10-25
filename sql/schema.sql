-- Smart Tourism Platform - esquema MySQL 8.0 (RASCUNHO para discussão)
-- Executar com o utilizador do projeto, na base smart_tourism.
-- Nota: em MySQL 8, para SRID 4326 a ordem das coordenadas em POINT é (latitude, longitude).
-- Falta decidir/acrescentar
--   1. Onde fica a descrição textual dos POIs (proposta: MongoDB). É a base dos embeddings do Qdrant.
--   2. Onde ficam as preferências do utilizador (proposta: MongoDB para mais flexibilidade).
--   3. Onde fica o histórico de atividade (proposta: MongoDB).

USE smart_tourism;

CREATE TABLE utilizador (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome          VARCHAR(100)    NOT NULL,
  email         VARCHAR(255)    NOT NULL,
  pais_origem   VARCHAR(60)     NULL,
  data_registo  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_utilizador_email (email)
) ENGINE=InnoDB;

CREATE TABLE destino (
  id           INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  nome         VARCHAR(100)  NOT NULL,
  pais         VARCHAR(60)   NOT NULL,
  regiao       VARCHAR(100)  NULL,
  localizacao  POINT SRID 4326 NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_destino_nome_pais (nome, pais),
  SPATIAL INDEX sx_destino_localizacao (localizacao)
) ENGINE=InnoDB;

CREATE TABLE categoria (
  id    SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome  VARCHAR(60)       NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_categoria_nome (nome)
) ENGINE=InnoDB;

-- poi.id e o identificador canonico, reutilizado no NoSQL e no Qdrant.
-- NOTA: BIGINT UNSIGNED é compatível com os ids do Qdrant (inteiros de 64 bits sem sinal).
-- NOTA: o ON DELETE CASCADE só limpa o MySQL. Ao apagar um POI, a aplicação tem de apagar 
-- também o documento no MongoDB e o vetor no Qdrant (consistência gerida pela aplicação).
CREATE TABLE poi (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  destino_id    INT UNSIGNED      NOT NULL,
  categoria_id  SMALLINT UNSIGNED NOT NULL,
  nome          VARCHAR(200)      NOT NULL,
  morada        VARCHAR(255)      NULL,
  localizacao   POINT SRID 4326   NOT NULL,
  preco_medio   DECIMAL(8,2)      NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_poi_destino   FOREIGN KEY (destino_id)   REFERENCES destino (id),
  CONSTRAINT fk_poi_categoria FOREIGN KEY (categoria_id) REFERENCES categoria (id),
  KEY ix_poi_destino_categoria (destino_id, categoria_id),
  SPATIAL INDEX sx_poi_localizacao (localizacao)
) ENGINE=InnoDB;

CREATE TABLE favorito (
  utilizador_id   BIGINT UNSIGNED NOT NULL,
  poi_id          BIGINT UNSIGNED NOT NULL,
  data_adicionado DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (utilizador_id, poi_id),
  KEY ix_favorito_poi (poi_id),
  CONSTRAINT fk_favorito_utilizador FOREIGN KEY (utilizador_id) REFERENCES utilizador (id) ON DELETE CASCADE,
  CONSTRAINT fk_favorito_poi        FOREIGN KEY (poi_id)        REFERENCES poi (id)        ON DELETE CASCADE
) ENGINE=InnoDB;

-- NOTA: o rating médio de cada POI é calculado com AVG(valor), apoiado pelo ix_rating_poi.
--       Se for uma consulta muito frequente, pode discutir-se guardar a média numa coluna
--       de poi, atualizada a cada novo rating (padrão Computed). Possível cenário para a Parte II.
CREATE TABLE rating (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  utilizador_id  BIGINT UNSIGNED NOT NULL,
  poi_id         BIGINT UNSIGNED NOT NULL,
  valor          TINYINT UNSIGNED NOT NULL,
  data           DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_rating_utilizador_poi (utilizador_id, poi_id),
  KEY ix_rating_poi (poi_id),
  CONSTRAINT ck_rating_valor CHECK (valor BETWEEN 1 AND 5),
  CONSTRAINT fk_rating_utilizador FOREIGN KEY (utilizador_id) REFERENCES utilizador (id) ON DELETE CASCADE,
  CONSTRAINT fk_rating_poi        FOREIGN KEY (poi_id)        REFERENCES poi (id)        ON DELETE CASCADE
) ENGINE=InnoDB;
