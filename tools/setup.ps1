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
    Write-Host "Vayrshemon M14 0.15.34 setup - $projectRoot"
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
    Invoke-Python $environmentPython @('-c', 'import jsonschema_rs; jsonschema_rs.Draft202012Validator(dict(type=''object''), offline=True).validate({}); print(''Native book validation accelerator ready'')')
    if (!(Test-Path -LiteralPath (Join-Path $environmentPath 'Scripts\pythonw.exe') -PathType Leaf)) {
        throw 'The windowless Python launcher is missing from .venv. Repair the Python 3.12 installation, then rerun setup.bat.'
    }
    Invoke-Python $environmentPython @('-m', 'tools.dependency_audit', '--out', ".local/logs/dependencies-$runId.json")
    Invoke-Python $environmentPython @('-m', 'tools.kjv_print_proof', '--check')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_print_edition', '--check')
    Invoke-Python $environmentPython @('-m', 'tools.m0', '--log', ".local/logs/setup-check-$runId.jsonl", 'check')
    Write-Host 'Checking the pinned later dramatic language (0.12), dictionary, grammar and compiler identity. Existing books and frozen Bible editions are never rebuilt by setup.'
    Invoke-Python $environmentPython @('-m', 'tools.editorial_language', '--verify')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.2')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.3')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.4')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.5')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.6')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.7')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.8')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.9')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.10')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.11')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.12')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.13')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.14')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.15')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.16')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.17')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.18')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.22')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.23')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.24')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.25')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.26')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.27')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.28')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.29')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.30')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.31')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.32')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.33')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.36')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.37')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.38')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.39')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.40')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.41')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.42')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.43')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.44')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.45')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.46')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.47')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.49')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.50')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.51')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.52')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.53')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.54')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.55')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.56')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.57')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.58')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.59')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.60')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.61')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.62')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.63')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.64')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.65')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.66')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.67')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.68')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.69')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.70')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.71')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.72')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.73')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.74')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.75')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.76')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.48')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.77')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.78')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.79')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.80')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.81')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.84')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.85')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.86')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.87')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.88')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.89')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.90')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.91')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.92')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.93')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.94')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.95')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.96')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.97')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.98')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.99')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.100')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.101')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.102')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.103')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.104')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.105')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.106')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.107')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.108')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.109')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.110')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.111')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.112')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.113')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.114')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.115')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.116')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.117')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.118')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.119')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.120')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.121')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.122')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.123')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.124')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.125')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.126')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.127')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.128')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.129')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.130')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.131')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.132')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.133')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.134')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.135')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.136')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.137')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.138')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.139')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.140')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.141')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.142')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.143')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.144')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.145')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.146')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.147')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.148')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.149')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.150')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.151')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.152')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.153')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.154')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.155')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.156')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.157')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.158')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.159')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.160')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.161')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.162')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.163')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.164')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.165')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.166')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.167')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.168')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.169')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.170')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.171')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.172')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.173')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.174')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.175')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.176')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.177')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.178')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.179')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.180')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.181')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.182')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.183')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.184')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.185')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.186')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.187')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.188')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.189')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.190')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.191')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.192')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.193')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.194')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.195')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.196')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.197')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.198')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.199')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.200')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.201')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.202')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.203')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.204')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.205')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.206')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.207')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.208')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.209')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.210')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.211')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.212')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.213')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.214')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.215')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.216')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.217')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.218')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.219')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.220')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.221')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.222')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.223')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.224')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.225')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.226')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.227')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.228')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.229')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.230')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.231')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.232')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.233')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.234')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.235')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.236')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.237')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.238')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.239')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.240')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.241')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.242')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.243')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.244')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.245')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.246')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.247')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.248')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.249')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.250')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.251')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.252')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.253')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.254')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.255')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.256')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.257')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.258')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.259')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.260')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.261')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.262')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.263')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.264')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.265')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.266')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.267')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.268')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.269')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.270')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.271')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.272')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.273')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.274')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.275')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.276')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.277')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.278')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.279')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.280')
    Invoke-Python $environmentPython @('-m', 'tools.kjv_archive', '--verify-register', '--register-version', '0.10-kjv.281')
    Ensure-ShellBuildTools
    Invoke-Python $environmentPython @('-m', 'tools.windows_shell', '--build')
    Invoke-Python $environmentPython @('-m', 'unittest', 'discover', '-s', 'tests', '-v')
    Invoke-Python $environmentPython @('-m', 'tools.windows_shell', '--install')
    Invoke-Python $environmentPython @('-m', 'Reader.register', '--install')
    & (Join-Path $PSScriptRoot 'create_shortcut.ps1') -ProjectRoot $projectRoot

    $mcpConfiguration = @{
        mcpServers = @{
            vayrshemon = @{
                command = $environmentPython
                args = @((Join-Path $projectRoot 'tools\run_lab.py'), 'mcp')
                env = @{ PYTHONUTF8 = '1' }
            }
            vayrshemonReader = @{
                command = $environmentPython
                args = @((Join-Path $projectRoot 'Reader\mcp.py'))
                env = @{ PYTHONUTF8 = '1' }
            }
        }
    }
    $mcpConfiguration | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $projectRoot '.local\mcp-config.json') -Encoding UTF8

    Write-Host ''
    Write-Host 'Setup complete. Bundled fonts, dependencies, evidence checks, and tests passed.'
    Write-Host 'Thimfora 79/80/81 and Transliteration 7 are included in data\runtime-fonts, verified by hash, and loaded privately by the app. Inputs is optional; no Windows font installation is needed.'
    Write-Host 'Workbench: desktop shortcut or launch.bat. Reader: Reader\launch.bat or a .vay file. Both apps can run together; Explorer also offers Edit in Vayrshemon Workbench.'
    Write-Host 'Reader builds a disposable page index on first open, then loads only requested pages. Help > Performance shows timings and slow-action diagnostics. Reader\setup.bat only checks the shared runtime and registers the Reader; it does not reinstall a working environment.'
    Write-Host 'Normal launches close the command window. Full launch output is recorded in .local\logs\launch-*.log; an error dialog points to the log if the editor fails.'
    Write-Host 'Language > Update transliteration refreshes the Roman column in one undo step in either page view. Reading-copy controls are removed from the main ribbon.'
    Write-Host 'Page navigation: zoom, one/two-page icons, previous, Page [number] of total, next. Enter a number to jump; paired arrows move by spreads. Navigation preserves text, Maxima, formatting and Undo history.'
    Write-Host 'New documents automatically show Unta page numbers when they have multiple pages: 50 pt, preferred 28 pt edge inset. View > Page numbering controls visibility, the multipage-only rule and separate single/left/right positions; changes are saved and undoable. Existing document settings are preserved. All exports honor the captured view. Numbers keep 4 pt clear of text regions and effects; blocked placements are flagged instead of overlapping. No new dependencies.'
    Write-Host 'Native books: limits of 32,768 pages, 65,536 frames, 32,000,000 text scalars, 1.5 GiB compact state and 384 MiB file. Books of 100+ pages save with the checksummed 0.7 compressed envelope; editable state and old-file reading stay compatible. Memory and render time depend on content. Lazy frame editors, bounded-header Explorer previews and compressed recovery preserve large books. No new dependencies.'
    Write-Host 'All exports start in Exports with timestamp names. PNG/SVG export the visible page or _Left / _Right pair; PDF exports every page in one file and opens in the current single/facing view. Exports is excluded from Git.'
    Write-Host 'PDF exports show progress, page count, elapsed time and Cancel. Monochrome and color books with a decorated first page check and draw each page once. Bounded glyph geometry reuse speeds color without reducing resolution or changing bevel/glow, formatting or Maxima.'
    Write-Host 'Save for new documents, Save As and Open start in Saves. Save updates an existing file in place. Saves is excluded from Git.'
    Write-Host '.vay files include centered Memon mode icons and saved page/spread thumbnails. Legacy .vay.json and .vaylab.json files remain readable.'
    Write-Host 'Explorer integration: per-user file associations + isolated system thumbnail component. See docs\M14.md.'
    Write-Host 'Remove integration: .venv\Scripts\python.exe -m tools.windows_shell --uninstall'
    Write-Host 'Forge projects: *.vayforge; versioned dictionaries, wiki, branches and tests. Construction glosses, four-column spreads, Maxima, tests and PNG export: docs\M13.md.'
    Write-Host 'New translations start from the hash-verified later dramatic 0.12 language in data\language\current.json. Dictionary, historical-reference scopes, grammar, inherited clause-flow tests and prior compiler bytes are bundled; see docs\CURRENT_LANGUAGE.md. Definitive historical 281 stays frozen. Private books and archived Forge history remain in Saves.'
    Write-Host 'Historical correction 281 adds construct phrases, dependent pronouns and varied clause continuation. Its compact edition opens each book on the next available page, left or right. Setup verifies the bundled grammar and tests; it never regenerates private Bible editions or changes older saves.'
    Write-Host 'Panel shortcuts: Ctrl+Alt+B expands/collapses; Ctrl+Alt+P pins/unpins. See docs\M6.1.md.'
    Write-Host 'Blank startup uses Monochrome: black on white, Fit Height and single-page mode. File > New also starts black on white. Saved documents restore their saved color mode and page view. Fresh installs open maximized with controls collapsed/unpinned and source/diagnostics/guides hidden. Existing panel choices are retained.'
    Write-Host 'File > Close (Ctrl+W) closes the document without quitting. Close and New return to a centered, single blank page in Fit Height without marking it edited. Unsaved changes offer Save, Discard or Cancel; cancelling or failing a save keeps the document open.'
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
