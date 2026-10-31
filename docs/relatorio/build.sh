#!/usr/bin/env bash
# Gera o relatório em Word a partir dos ficheiros .md desta pasta.
# Requer: pandoc (https://pandoc.org/installing.html)
set -e
cd "$(dirname "$0")"
mkdir -p _build
pandoc metadata.yaml \
  00_introducao.md 01_parte1_revisoes.md 02_mysql.md 03_nosql.md \
  04_vetorial.md 05_integracao.md 06_indices.md 07_conclusao.md 08_uso_ia.md \
  --toc --toc-depth=2 --number-sections \
  --resource-path=. \
  -o _build/relatorio.docx
echo "Gerado: docs/relatorio/_build/relatorio.docx"
