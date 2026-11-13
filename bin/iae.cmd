@echo off
REM Windows launcher: prefer uv (install from https://docs.astral.sh/uv/ if missing).
setlocal
set "ROOT=%~dp0.."
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
  echo iae: uv not found. Install from https://docs.astral.sh/uv/ then re-open the shell.
  exit /b 1
)
uv run --quiet --project "%ROOT%" python -m i_am_an_engineer %*
exit /b %ERRORLEVEL%
