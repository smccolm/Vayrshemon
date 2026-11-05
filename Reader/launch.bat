@echo off
setlocal
if not exist "%~dp0..\.venv\Scripts\pythonw.exe" (
  echo Run Reader\setup.bat first.
  pause
  exit /b 1
)
if exist "%~dp0VayrshemonReader.exe" (
  start "" "%~dp0VayrshemonReader.exe" %*
) else (
  start "" "%~dp0..\.venv\Scripts\pythonw.exe" "%~dp0launch.py" %*
)
exit /b %ERRORLEVEL%

