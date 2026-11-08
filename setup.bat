@echo off
rem M14 0.15.34 + Reader 1.0: independent fast reader with .vay association.
rem Letter proof 3 separates the leading display blank from the duplex print master; private proofs are never rebuilt.
rem Later dramatic language 0.13 corrects play name labels, referents and native cultural vocabulary; inherited clause flow stays intact.
rem Remaining Shakespeare expands that pinned base in one private project; setup tests Unta values, source word/digit notation, contextual quantities such as moiety, compound-fold, fractional-prefix and ordinal-grade review and source accounting without rebuilding books.
rem Unta includes words and figures: preserve the source choice; never convert all written-out numbers to glyphs.
rem Spoken ratios, ages, clock readings, ordinal speaker labels/lists and contextual pair quantities use the same tested Unta path; no new installation step is needed.
rem Historical 0.10-kjv.284 verifies the chart-corrected Unta readings in both Bibles.
rem Historical 0.10-kjv.285 verifies the native vocabulary and name revision.
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
