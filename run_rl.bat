@echo off
REM One-button RL run on Windows. Usage: run_rl.bat [hours]   (default 8; "smoke" = ~6 min check)
cd /d "%~dp0"
if not exist .venv_rl python -m venv .venv_rl
call .venv_rl\Scripts\activate.bat
pip install -q --upgrade pip
pip install -q -r rl\requirements.txt
if "%1"=="smoke" (
  python -m rl.run_all --smoke
) else (
  if "%1"=="" (python -m rl.run_all --hours 8) else (python -m rl.run_all --hours %1)
)
pause
