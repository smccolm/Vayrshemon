@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo Run setup.bat first to install the Vayrshemon environment.
    pause
    popd
    exit /b 1
)
rem The windowless launcher records output and reports errors without a console.
start "" ".venv\Scripts\pythonw.exe" "%~dp0tools\launch_editor.py" %*
set "LAUNCH_EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %LAUNCH_EXIT_CODE%
