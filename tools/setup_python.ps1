# Definitions only. setup.ps1 calls Ensure-Python312 only when .venv is absent.
# Official installer options: https://docs.python.org/3.12/using/windows.html#installing-without-ui
# SHA-256 from python.org's python-3.12.10-amd64.exe.sigstore messageDigest.

function Get-Python312Candidates {
    $paths = @()
    foreach ($key in @('HKCU:\Software\Python\PythonCore\3.12\InstallPath',
                       'HKLM:\Software\Python\PythonCore\3.12\InstallPath',
                       'HKCU:\Software\Python\PythonCore\3.12-64\InstallPath',
                       'HKLM:\Software\Python\PythonCore\3.12-64\InstallPath')) {
        $install = Get-Item -LiteralPath $key -ErrorAction SilentlyContinue
        if ($install) {
            $executable = $install.GetValue('ExecutablePath')
            $directory = $install.GetValue('')
            if ($executable) { $paths += $executable }
            elseif ($directory) { $paths += Join-Path $directory 'python.exe' }
        }
    }
    if ($env:LOCALAPPDATA) { $paths += Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe' }
    if ($env:ProgramFiles) { $paths += Join-Path $env:ProgramFiles 'Python312\python.exe' }
    foreach ($python in (Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
        # Never activate the Microsoft Store's uninstalled-Python alias.
        if ($python.Source -notlike '*\Microsoft\WindowsApps\*') { $paths += $python.Source }
    }
    foreach ($path in ($paths | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            @{ Executable = $path; Prefix = @() }
        }
    }
    foreach ($launcher in (Get-Command py.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
        @{ Executable = $launcher.Source; Prefix = @('-3.12') }
    }
}

function Find-Python312 {
    foreach ($candidate in (Get-Python312Candidates)) {
        try {
            Invoke-Python $candidate.Executable ($candidate.Prefix + @('-c',
                "import struct, sys, venv, ensurepip; print(sys.version); sys.exit(0 if sys.version_info[:2] == (3, 12) and struct.calcsize('P') == 8 else 1)"))
            return $candidate
        }
        catch {
            Write-Host ('Candidate unavailable or not usable Python 3.12, 64-bit: {0}' -f $candidate.Executable)
            Write-Host $_.Exception.Message
        }
    }
    return $null
}

function Install-Python312 {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    if (!$env:LOCALAPPDATA) { throw 'LOCALAPPDATA is unavailable; cannot install Python for the current user.' }
    $target = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312'
    if (Test-Path -LiteralPath $target) {
        throw "Python's default folder already exists but no usable Python 3.12 x64 was found: $target. It has been left intact; repair that Python installation before rerunning setup."
    }
    $runId = [Guid]::NewGuid().ToString('N')
    $downloadDirectory = Join-Path $ProjectRoot ".local\installers\python-$runId"
    $logDirectory = Join-Path $ProjectRoot '.local\logs'
    New-Item -ItemType Directory -Path $downloadDirectory -Force | Out-Null
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $installer = Join-Path $downloadDirectory 'python-3.12.10-amd64.exe'
    $installerLog = Join-Path $logDirectory "python-install-$runId.log"
    $url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe'
    $expectedHash = '67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb'
    Write-Host "Python 3.12 x64 was not found. Downloading the official installer: $url"
    $protocol = [Net.ServicePointManager]::SecurityProtocol
    try {
        [Net.ServicePointManager]::SecurityProtocol = $protocol -bor [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
    }
    finally { [Net.ServicePointManager]::SecurityProtocol = $protocol }
    if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash -ne $expectedHash) {
        throw 'Python installer checksum did not match the pinned official release. Nothing was installed.'
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $installer
    if ($signature.Status -ne 'Valid' -or !$signature.SignerCertificate -or
        $signature.SignerCertificate.GetNameInfo([Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false) -ne 'Python Software Foundation') {
        throw 'Python installer publisher signature is invalid. Nothing was installed.'
    }
    Write-Host "Verified Python installer. Installing for the current user in $target"
    Write-Host "Python installer log: $installerLog"
    $arguments = @('/quiet', '/norestart', '/log', ('"{0}"' -f $installerLog),
        'InstallAllUsers=0', ('TargetDir="{0}"' -f $target), 'PrependPath=0', 'AppendPath=0',
        'Include_launcher=0', 'InstallLauncherAllUsers=0', 'AssociateFiles=0', 'Shortcuts=0',
        'Include_pip=1', 'Include_test=0', 'Include_doc=0')
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -notin @(0,3010)) {
        throw "Python installation failed with exit code $($process.ExitCode). See $installerLog"
    }
    if ($process.ExitCode -eq 3010) { Write-Host 'Python installer reports that Windows may need a restart.' }
}

function Ensure-Python312 {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    $found = Find-Python312
    if ($null -ne $found) { return $found }
    Install-Python312 -ProjectRoot $ProjectRoot
    $found = Find-Python312
    if ($null -eq $found) { throw 'Python installation finished but Python 3.12 x64 could not be validated. See the Python installer log and rerun setup after any required restart.' }
    return $found
}
