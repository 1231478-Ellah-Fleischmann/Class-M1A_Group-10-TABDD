# Class-M1A_Group-10-TABDD

Projeto de Persistência Poliglota — **Smart Tourism Platform**
Unidade curricular: Tópicos Avançados de Bases de Dados (DEI, ISEP)

Plataforma de turismo em Python que integra três paradigmas de persistência: relacional, NoSQL e vetorial.

## Tecnologias

| Camada | Tecnologia | Estado |
|---|---|---|
| Relacional | MySQL (servidor do DEI) | Decidido |
| NoSQL | MongoDB (Atlas) | Decidido |
| Vetorial | Qdrant (Docker) | Decidido |
| Embeddings | `intfloat/multilingual-e5-small` (384 dimensões) | Decidido |
| Aplicação | Python | Decidido |
| Frontend | A definir (prova de conceito) | Por decidir |

## Membros

| Nome | Nº de aluno | Responsabilidade principal |
|---|---|---|
| Ellah Fleischmann | 1231478 | MySQL |
| Francisca Moreira | 1230769 | MongoDB |
| Inês Martinho | 1230806 | Qdrant (vetorial) |

## Datas

- Semana 9: sessão de discussão e feedback da Parte I (feita; versão apresentada marcada com a tag `parte1-feedback`)
- 8 de dezembro de 2026, 23:59: entrega final (relatório em ZIP + aplicação)
- Semanas 13 e 14: apresentação oral (presença obrigatória de todos os membros)

## Estrutura do repositório

```
app/repositories/   Acesso a cada base (mysql/, nosql/, vector/)
app/services/       Lógica da aplicação (embeddings, pesquisa, recomendações...)
app/ui/             Frontend (prova de conceito)
data/               Scripts de carga de dados e amostras (data/sample/)
sql/                Esquema MySQL (schema.sql)
benchmarks/         Experiências e cenários de análise de índices (resultados em benchmarks/resultados/)
docs/parte1/        Parte I: modelos de dados, arquitetura e justificações
docs/relatorio/     Relatório final (um ficheiro .md por secção, gerado em Word)
```

## Documentação: os três README

| Ficheiro | Para que serve |
|---|---|
| `README.md` (este) | Apresentação do projeto e como correr |
| `docs/parte1/README.md` | Documento da Parte I: modelo de cada base, distribuição dos dados e arquitetura |
| `docs/relatorio/README.md` | Como escrever e gerar o relatório final em Word |

**Regra para não haver texto repetido:** o modelo de cada base (o que guarda, decisões, desempenho, escalabilidade...) escreve-se **só em `docs/parte1/`**. Em `docs/relatorio/` escreve-se apenas o que é da Parte II (implementação, queries, índices, integração). Na versão final, a secção "Modelo e decisões" de cada base é copiada de `docs/parte1/` para o relatório, uma única vez.

## Como correr

1. Copiar `.env.example` para `.env` e preencher as credenciais (o `.env` nunca vai para o repositório). As passwords do MySQL e do MongoDB Atlas pedem-se ao grupo.
2. Instalar dependências: `pip install -r requirements.txt`
3. Arrancar o Qdrant (Docker). Da primeira vez:
   ```
   docker run -d --name qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant:v1.20.0
   ```
   Das vezes seguintes basta `docker start qdrant`.
4. Criar o esquema MySQL: `sql/schema.sql`
5. Carregar os dados no MySQL: `python -m data.carregar_mysql` (apaga e recarrega a base)
6. Indexar os POIs no Qdrant: `python -m app.services.poi_indexing --recriar --maior`
7. Arrancar a aplicação: a definir

## Fluxo de trabalho

- Um branch por tarefa (por exemplo `vetorial`, `mysql-dados`) e integração no `main` por pull request revisto por outro membro.
- Mensagens de commit curtas e descritivas.
- O identificador canónico dos POIs (`poi_id`) nasce no MySQL e é reutilizado no MongoDB e no Qdrant.

## Declaração de uso de IA

O enunciado exige a declaração do uso de ferramentas de IA. O registo está em [AI_USAGE.md](AI_USAGE.md) e é resumido em `docs/relatorio/08_uso_ia.md`.