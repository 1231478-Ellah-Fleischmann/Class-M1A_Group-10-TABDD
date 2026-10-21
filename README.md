# Class-M1A_Group-10-TABDD

Projeto de Persistência Poliglota — **Smart Tourism Platform**
Unidade curricular: Tópicos Avançados de Bases de Dados (DEI)

Plataforma de turismo em Python que integra três paradigmas de persistência: relacional, NoSQL e vetorial.

## Tecnologias

| Camada | Tecnologia | Estado |
|---|---|---|
| Relacional | MySQL Server | Decidido |
| NoSQL | MongoDB | Decidido |
| Vetorial | A definir | Por decidir |
| Aplicação | Python | Decidido |
| Frontend | A definir (prova de conceito) | Por decidir |

## Membros

| Nome | Nº de aluno | Responsabilidade principal |
| Ellah Fleischmann | 1231478 | MySQL |
| Francisca Moreira | 1230769 | NoSQL |
| Inês Martinho | 1230806 | Vetorial |

## Datas

- Semana 9: sessão de discussão e feedback (Parte I: esquemas e arquitetura)
- 8 de dezembro de 2026, 23:59: entrega final (relatório em ZIP + aplicação)
- Semanas 13 e 14: apresentação oral (presença obrigatória de todos os membros)

## Estrutura do repositório

```
docs/parte1/      Modelos de dados, arquitetura e justificações (Parte I)
docs/relatorio/   Relatório final
app/              Aplicação Python (repositories, services, ui)
data/             Recolha e geração de dados
sql/              DDL e scripts de índices (MySQL)
benchmarks/       Cenários de análise de índices
```

## Como correr (a preencher)

1. Copiar `.env.example` para `.env` e preencher as credenciais (o `.env` nunca vai para o repositório).
2. Instalar dependências: `pip install -r requirements.txt`
3. Criar o esquema MySQL: ver `sql/`
4. Carregar os dados: ver `data/`
5. Arrancar a aplicação: a definir

## Fluxo de trabalho

- Um ramo por área (`mysql`, `nosql`, `vector`, `docs`) e integração no `main` por pull request.
- Mensagens de commit curtas e descritivas.
- O identificador canónico dos POIs (`poi_id`) nasce no MySQL e é reutilizado nas restantes bases.

## Declaração de uso de IA

O enunciado exige a declaração do uso de ferramentas de IA. O registo está em [AI_USAGE.md](AI_USAGE.md).
