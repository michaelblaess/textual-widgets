@echo off
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m textual_widgets.storybook %*
) else (
    python -m textual_widgets.storybook %*
)
