@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup.bat first to install the Vayrshemon environment.
    pause
    popd
    exit /b 1
)
".venv\Scripts\python.exe" -u -m vayrshemon lab %*
set "LAB_EXIT_CODE=%ERRORLEVEL%"
if not "%LAB_EXIT_CODE%"=="0" (
    echo.
    echo The lab stopped with an error. Diagnostics are in .local\logs.
    pause
)
popd
exit /b %LAB_EXIT_CODE%
