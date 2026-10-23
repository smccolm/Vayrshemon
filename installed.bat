@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup.bat first.
    popd
    exit /b 1
)
rem Manage verified local installs. See docs\M6.md for install and rollback.
".venv\Scripts\python.exe" -m tools.release %*
set "RELEASE_EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %RELEASE_EXIT_CODE%
