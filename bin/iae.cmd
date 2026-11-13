@echo off
REM Windows launcher for iae. Prefer uv when available.
setlocal
set "ROOT=%~dp0.."
where uv >nul 2>nul
if %ERRORLEVEL%==0 (
  uv run --quiet --project "%ROOT%" python -m i_am_an_engineer %*
  exit /b %ERRORLEVEL%
)
set "PYTHONPATH=%ROOT%;%PYTHONPATH%"
python -m i_am_an_engineer %*
exit /b %ERRORLEVEL%
