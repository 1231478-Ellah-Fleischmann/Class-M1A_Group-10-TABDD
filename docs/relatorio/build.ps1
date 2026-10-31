# Gera o relatório em Word a partir dos ficheiros .md desta pasta (Windows).
# Requer: pandoc (winget install JohnMacFarlane.Pandoc)
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force -Path _build | Out-Null
pandoc metadata.yaml `
  00_introducao.md 01_parte1_revisoes.md 02_mysql.md 03_nosql.md `
  04_vetorial.md 05_integracao.md 06_indices.md 07_conclusao.md 08_uso_ia.md `
  --toc --toc-depth=2 --number-sections `
  --resource-path=. `
  -o _build/relatorio.docx
Write-Host "Gerado: docs/relatorio/_build/relatorio.docx"
