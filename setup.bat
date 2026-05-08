@echo off
echo === textual-widgets Setup ===
echo.

if not exist ".venv" (
    echo Erstelle virtuelle Umgebung...
    python -m venv .venv
)

REM SSL-Workaround fuer Corporate-Proxy (Zscaler etc.) — pip.ini fuer ALLE
REM pip-Aufrufe inkl. Build-Subprocesses.
if not exist ".venv\pip.ini" (
    echo [global]> ".venv\pip.ini"
    echo trusted-host = pypi.org pypi.python.org files.pythonhosted.org>> ".venv\pip.ini"
)

echo Aktiviere .venv...
call .venv\Scripts\activate.bat

echo Aktualisiere pip...
python -m pip install --upgrade pip >nul 2>&1

echo Installiere textual-widgets mit Storybook-Themes und Dev-Dependencies...
pip install -e ".[dev,storybook]"

echo.
echo === Setup abgeschlossen ===
echo Storybook starten mit: run.bat
echo Tests laufen lassen mit: .venv\Scripts\pytest tests
