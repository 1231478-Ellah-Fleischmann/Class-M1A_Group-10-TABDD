# Relatório final

Escrevemos o relatório em Markdown e geramos o Word no fim. Cada secção é um ficheiro; cada pessoa edita o seu.

| Ficheiro | Secção | Responsável |
|---|---|---|
| `00_introducao.md` | Introdução | Grupo |
| `01_parte1_revisoes.md` | Revisões à Parte I após o feedback | Grupo |
| `02_mysql.md` | MySQL | Ellah |
| `03_nosql.md` | MongoDB | Francisca |
| `04_vetorial.md` | Qdrant | Inês |
| `05_integracao.md` | Arquitetura e integração | Grupo |
| `06_indices.md` | Análise de índices | Cada membro |
| `07_conclusao.md` | Conclusão | Grupo |
| `08_uso_ia.md` | Uso de IA | Grupo |

## Gerar o Word

1. Instalar o pandoc (Windows: `winget install JohnMacFarlane.Pandoc`).
2. Nesta pasta, correr `./build.ps1` (Windows) ou `./build.sh` (Linux/macOS).
3. O ficheiro sai em `_build/relatorio.docx` (não vai para o Git).

## Diagramas

Os diagramas Mermaid **não aparecem** no Word: o pandoc mostra-os como código. Para o relatório, exportar cada diagrama para PNG e incluí-lo:

```
npx -y @mermaid-js/mermaid-cli -i diagrama.mmd -o img/diagrama.png
```
```
![Diagrama ER do MySQL](img/mysql_er.png)
```

Alternativa: abrir o diagrama no [Mermaid Live Editor](https://mermaid.live) e descarregar a imagem para `img/`.

## Marcar a versão da sessão de feedback

Depois da sessão da semana 9, criar a tag para depois se ver o que mudou:

```
git tag parte1-feedback
git push origin parte1-feedback
```

## Entrega

O enunciado pede um ZIP com o nome `ClasseQ_Ramo_nº1_nº2_nº3.ZIP` (números de aluno dos três membros) com o relatório e a aplicação.
