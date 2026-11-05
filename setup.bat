@echo off
rem M14 0.15.34 + Reader 1.0: independent fast reader with .vay association.
rem Letter proof 3 separates the leading display blank from the duplex print master; private proofs are never rebuilt.
rem Later dramatic language 0.12 inherits reviewed clause flow from definitive historical 0.10-kjv.281.
rem Historical 0.10-kjv.282 corrects Yeshua spelling and name glosses; setup never rebuilds private editions.
rem New editions are stored once; prior books and complete Forge ancestry use verified compressed archives.
rem New print editions use either side for book openings; older saved layouts are preserved.
rem Setup verifies the language packages; the complete historical Bible is sealed in Saves. Private books are never rebuilt.
rem Setup and regressions live in tools\setup.ps1.
rem First shell install uses Windows administrator approval for the isolated native thumbnail component.
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
