#Requires -Version 5.1
<#
.SYNOPSIS
    Compiles the textual-widgets storybook demo into a standalone Windows
    binary with Nuitka.

.DESCRIPTION
    textual-widgets is primarily a widget library; this script builds its
    interactive storybook demo app so the widgets can be tried out without a
    Python install on the target machine.

    Produces a self-contained --standalone build. Output:
    dist\textual-widgets-demo\textual-widgets-demo.exe plus its DLLs, and a
    zipped dist\textual-widgets-demo-vX.Y.Z-win64.zip ready to hand out.
#>

$ErrorActionPreference = "Stop"

# Pfade - alles relativ zum Skriptverzeichnis, damit der Aufruf ortsunabhaengig ist
$root    = $PSScriptRoot
$entry   = Join-Path $root "src\textual_widgets\storybook\__main__.py"
$initPy  = Join-Path $root "src\textual_widgets\__init__.py"
$outDir  = Join-Path $root "dist"
$distDir = Join-Path $outDir "textual-widgets-demo"

# venv-Python bevorzugen, sonst System-Python
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

# venv mit dem Lockfile abgleichen, damit Nuitka keine veralteten
# (Git-)Dependencies einkompiliert. --inexact laesst Extra-Pakete wie das
# ad-hoc installierte nuitka unangetastet. Das storybook-Extra muss dabei sein,
# sonst fehlt die textual-themes-Dependency der Demo-App.
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Syncing venv to lockfile (uv sync --inexact)..." -ForegroundColor Cyan
    & uv sync --inexact --extra storybook --project $root
    if ($LASTEXITCODE -ne 0) { throw "uv sync fehlgeschlagen" }
} else {
    Write-Host "uv nicht gefunden - venv-Sync uebersprungen" -ForegroundColor Yellow
}

# Version aus __init__.py lesen, damit die EXE-Metadaten nicht von pyproject driften
$version = ([regex]'__version__\s*=\s*"([^"]+)"').Match((Get-Content -Raw $initPy)).Groups[1].Value
if (-not $version) { throw "Konnte __version__ nicht aus $initPy lesen" }

Write-Host "Compiling textual-widgets-demo v$version with Nuitka..." -ForegroundColor Cyan

# Alten Build verwerfen - das Ergebnis soll reproduzierbar sein
if (Test-Path $distDir) { Remove-Item -Recurse -Force $distDir }

$started = Get-Date

# --standalone        : self-contained, kein Python auf dem Zielrechner noetig
# --remove-output     : C-/Objekt-Zwischendateien nach dem Build aufraeumen
# --include-package-data=textual_widgets : eventuelle Datendateien mitnehmen
# (kein --windows-console-mode: Default behaelt die Konsole - noetig fuer das TUI)
& $python -m nuitka `
    --standalone `
    --assume-yes-for-downloads `
    --remove-output `
    --include-package=textual_widgets `
    --include-package-data=textual_widgets `
    --output-dir=$outDir `
    --output-filename=textual-widgets-demo.exe `
    --company-name="Michael Blaess" `
    --product-name="textual-widgets-demo" `
    --file-version=$version `
    --product-version=$version `
    $entry

if ($LASTEXITCODE -ne 0) { throw "Nuitka-Build fehlgeschlagen (Exit $LASTEXITCODE)" }

# Nuitka benennt den dist-Ordner nach dem Hauptmodul (__main__.dist) - umbenennen
$nuitkaDist = Join-Path $outDir "__main__.dist"
if (Test-Path $nuitkaDist) { Rename-Item -Path $nuitkaDist -NewName "textual-widgets-demo" }

$elapsed = [int]((Get-Date) - $started).TotalSeconds
$exe     = Join-Path $distDir "textual-widgets-demo.exe"
$sizeMB  = [math]::Round(((Get-ChildItem -Recurse $distDir | Measure-Object Length -Sum).Sum) / 1MB, 1)

# Verteilbares ZIP erzeugen - der Top-Level-Ordner bleibt im Archiv erhalten,
# der Empfaenger entpackt also direkt einen sauberen textual-widgets-demo-Ordner
$zip = Join-Path $outDir "textual-widgets-demo-v$version-win64.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path $distDir -DestinationPath $zip
$zipMB = [math]::Round((Get-Item $zip).Length / 1MB, 1)

Write-Host ""
Write-Host "Done in ${elapsed}s" -ForegroundColor Green
Write-Host "  dist folder : $distDir  (${sizeMB} MB)"
Write-Host "  zip         : $zip  (${zipMB} MB)"
Write-Host "  run         : $exe"
