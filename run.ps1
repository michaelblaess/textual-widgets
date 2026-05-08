$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython -m textual_widgets.storybook @args
} else {
    & python -m textual_widgets.storybook @args
}
