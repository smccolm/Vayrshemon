@echo off
setlocal
set "SETUP_NO_PAUSE="
if "%~1"=="" goto run
if /I "%~1"=="--no-pause" if "%~2"=="" (
    set "SETUP_NO_PAUSE=1"
    goto run
)
echo Usage: setup.bat [--no-pause]
exit /b 2

:run
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\setup.ps1"
set "SETUP_EXIT_CODE=%ERRORLEVEL%"
echo.
if not defined SETUP_NO_PAUSE pause
exit /b %SETUP_EXIT_CODE%
