@echo off
setlocal
pushd "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  call setup.bat
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -c "from PySide6 import QtCore; from Reader.storage import BookIndex; print('Reader runtime ready')"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m Reader.register --install
set "READER_SETUP_RESULT=%ERRORLEVEL%"
popd
exit /b %READER_SETUP_RESULT%

