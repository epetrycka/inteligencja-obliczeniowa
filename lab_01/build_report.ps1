$ErrorActionPreference = 'Stop'

$texBin = 'C:\Program Files\MiKTeX\miktex\bin\x64'
$pdflatex = Join-Path $texBin 'pdflatex.exe'

if (-not (Test-Path $pdflatex)) {
    throw "Nie znaleziono pdflatex.exe w $texBin"
}

uv run python lab_01/generate_plots.py

& $pdflatex -interaction=nonstopmode -output-directory lab_01 lab_01/report.tex
& $pdflatex -interaction=nonstopmode -output-directory lab_01 lab_01/report.tex

Write-Host "Gotowe: lab_01/report.pdf"
