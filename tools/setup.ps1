# Windows entry point: setup.bat. Keep native stdout/stderr visible and recorded.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$environmentPath = Join-Path $projectRoot '.venv'
$environmentPython = Join-Path $environmentPath 'Scripts\python.exe'
$transcribing = $false
$locationPushed = $false
$setupExitCode = 1
$logPath = $null
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONNOUSERSITE = '1'

function Invoke-Python {
    param([string]$Executable, [string[]]$Arguments)
    Write-Host ('> "{0}" {1}' -f $Executable, ($Arguments -join ' '))
    $previousPreference = $ErrorActionPreference
    try {
        # Windows PowerShell represents native stderr as ErrorRecords. Preserve
        # those lines, and use the process exit code to decide success.
        $ErrorActionPreference = 'Continue'
        $global:LASTEXITCODE = 1
        & $Executable @Arguments 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $_.Exception.Message
            }
            else { Write-Host $_ }
        }
        $nativeExitCode = $global:LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($nativeExitCode -ne 0) {
        throw "Python command failed with exit code $nativeExitCode. See the output above."
    }
}

. (Join-Path $PSScriptRoot 'setup_python.ps1')

function Ensure-ShellBuildTools {
    $finder = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    $found = $null
    if (Test-Path -LiteralPath $finder) {
        $found = & $finder -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    }
    if (!$found) {
        $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (!$winget) { throw 'Install Visual Studio 2022 Build Tools with Desktop development with C++, then rerun setup.bat (winget is unavailable).' }
        Write-Host 'Installing Microsoft C++ build tools and Windows SDK for the native Explorer component.'
        & $winget.Source install --id Microsoft.VisualStudio.2022.BuildTools --exact --source winget --silent --accept-package-agreements --accept-source-agreements --override '--wait --passive --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended'
        if ($LASTEXITCODE -notin @(0,3010)) { throw 'C++ tools installation failed. See this setup log; rerun after resolving the installer error.' }
    }
}

try {
    Push-Location -LiteralPath $projectRoot
    $locationPushed = $true
    $logDirectory = Join-Path $projectRoot '.local\logs'
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $runId = '{0}-{1}' -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), $PID
    $logPath = Join-Path $logDirectory "setup-$runId.log"
    Start-Transcript -LiteralPath $logPath | Out-Null
    $transcribing = $true
    Write-Host "Vayrshemon M14 0.15.18 setup - $projectRoot"
    Write-Host "Console log: $logPath"
    $savesDirectory = Join-Path $projectRoot 'Saves'
    New-Item -ItemType Directory -Path $savesDirectory -Force | Out-Null
    Write-Host "Default document folder: $savesDirectory"
    $exportsDirectory = Join-Path $projectRoot 'Exports'
    New-Item -ItemType Directory -Path $exportsDirectory -Force | Out-Null
    Write-Host "Default PNG/SVG/PDF export folder: $exportsDirectory"

    if (Test-Path -LiteralPath $environmentPath) {
        if (!(Test-Path -LiteralPath $environmentPython -PathType Leaf) -or
            !(Test-Path -LiteralPath (Join-Path $environmentPath 'pyvenv.cfg') -PathType Leaf)) {
            throw 'The existing .venv is incomplete. Rename it to keep its contents, then rerun setup.bat to create a fresh environment.'
        }
        Write-Host 'Reusing the existing .venv.'
    }
    else {
        $basePython = Ensure-Python312 -ProjectRoot $projectRoot
        # Run ensurepip separately so its full failure output reaches the log.
        Invoke-Python $basePython.Executable ($basePython.Prefix + @('-m', 'venv', '--without-pip', $environmentPath))
    }

    # Refuse an incompatible environment or an interpreter pointing elsewhere.
    Invoke-Python $environmentPython @('-c',
        "import pathlib, struct, sys; print(sys.version); assert sys.version_info[:2] == (3, 12) and struct.calcsize('P') == 8, 'Expected Python 3.12, 64-bit; rename .venv and rerun setup'; assert sys.prefix != sys.base_prefix and pathlib.Path(sys.prefix).resolve() == pathlib.Path(sys.argv[1]).resolve(), 'Interpreter does not belong to this project environment'",
        $environmentPath)
    Invoke-Python $environmentPython @('-m', 'tools.verify_runtime_fonts')
    Invoke-Python $environmentPython @('-m', 'ensurepip', '--upgrade', '--default-pip')
    $wheelArguments = @()
    if ($env:VAYRSHEMON_WHEELHOUSE) {
        $wheelDirectory = (Resolve-Path -LiteralPath $env:VAYRSHEMON_WHEELHOUSE).Path
        $wheelArguments = @('--no-index', '--find-links', $wheelDirectory)
        Write-Host "Offline wheelhouse: $wheelDirectory"
    }
    Invoke-Python $environmentPython (@('-m', 'pip', '--require-virtualenv', 'install',
        '--disable-pip-version-check', '--no-input', '--only-binary=:all:', '-r', 'requirements/requirements-m14.txt') + $wheelArguments)
    Invoke-Python $environmentPython @('-m', 'pip', '--disable-pip-version-check', 'check')
    if (!(Test-Path -LiteralPath (Join-Path $environmentPath 'Scripts\pythonw.exe') -PathType Leaf)) {
        throw 'The windowless Python launcher is missing from .venv. Repair the Python 3.12 installation, then rerun setup.bat.'
    }
    Invoke-Python $environmentPython @('-m', 'tools.dependency_audit', '--out', ".local/logs/dependencies-$runId.json")
    Invoke-Python $environmentPython @('-m', 'tools.m0', '--log', ".local/logs/setup-check-$runId.jsonl", 'check')
    Ensure-ShellBuildTools
    Invoke-Python $environmentPython @('-m', 'tools.windows_shell', '--build')
    Invoke-Python $environmentPython @('-m', 'unittest', 'discover', '-s', 'tests', '-v')
    Invoke-Python $environmentPython @('-m', 'tools.windows_shell', '--install')
    & (Join-Path $PSScriptRoot 'create_shortcut.ps1') -ProjectRoot $projectRoot

    $mcpConfiguration = @{
        mcpServers = @{
            vayrshemon = @{
                command = $environmentPython
                args = @((Join-Path $projectRoot 'tools\run_lab.py'), 'mcp')
                env = @{ PYTHONUTF8 = '1' }
            }
        }
    }
    $mcpConfiguration | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $projectRoot '.local\mcp-config.json') -Encoding UTF8

    Write-Host ''
    Write-Host 'Setup complete. Bundled fonts, dependencies, evidence checks, and tests passed.'
    Write-Host 'Thimfora 79/80/81 and Transliteration 7 are included in data\runtime-fonts, verified by hash, and loaded privately by the app. Inputs is optional; no Windows font installation is needed.'
    Write-Host 'Double-click the Vayrshemon desktop shortcut, launch.bat or a .vay file to open M14 (Language Workbench + Language Forge).'
    Write-Host 'Normal launches close the command window. Full launch output is recorded in .local\logs\launch-*.log; an error dialog points to the log if the editor fails.'
    Write-Host 'Language > Update transliteration refreshes the Roman column in one undo step in either page view. Reading-copy controls are removed from the main ribbon.'
    Write-Host 'All exports start in Exports with timestamp names. PNG/SVG export the visible page or _Left / _Right pair; PDF exports every page in one file and opens in the current single/facing view. Exports is excluded from Git.'
    Write-Host 'Save for new documents, Save As and Open start in Saves. Save updates an existing file in place. Saves is excluded from Git.'
    Write-Host '.vay files include centered Memon mode icons and saved page/spread thumbnails. Legacy .vay.json and .vaylab.json files remain readable.'
    Write-Host 'Explorer integration: per-user file associations + isolated system thumbnail component. See docs\M14.md.'
    Write-Host 'Remove integration: .venv\Scripts\python.exe -m tools.windows_shell --uninstall'
    Write-Host 'Forge projects: *.vayforge; versioned dictionaries, wiki, branches and tests. Construction glosses, four-column spreads, Maxima, tests and PNG export: docs\M13.md.'
    Write-Host 'Panel shortcuts: Ctrl+Alt+B expands/collapses; Ctrl+Alt+P pins/unpins. See docs\M6.1.md.'
    Write-Host 'Blank startup always uses Fit Height and single-page mode; saved documents restore their saved page view. Fresh installs open maximized with controls collapsed/unpinned and source/diagnostics/guides hidden. Existing panel choices are retained.'
    Write-Host 'The app uses its own Windows taskbar identity and centered Memon icon. Restart existing windows to apply this update.'
    Write-Host 'Offline recovery: python -S tools\recovery.py --help'
    Write-Host 'Versioned installation and rollback: installed.bat --help (see docs\M6.md).'
    Write-Host 'CLI: .venv\Scripts\python.exe -m vayrshemon --help'
    Write-Host 'MCP client configuration: .local\mcp-config.json (connects to the active editor or lab).'
    $setupExitCode = 0
}
catch {
    Write-Host ''
    Write-Host ('SETUP FAILED: {0}' -f $_.Exception.Message) -ForegroundColor Red
    Write-Host $_.ScriptStackTrace
    Write-Host 'Fix the reported problem, then rerun setup.bat. Existing environments are never deleted automatically.'
}
finally {
    if ($logPath) { Write-Host "Console log: $logPath" }
    if ($transcribing) { Stop-Transcript | Out-Null }
    if ($locationPushed) { Pop-Location }
}
exit $setupExitCode
