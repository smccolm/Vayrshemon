"""Check setup decisions using mocked downloads/installers; never reinstall."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name=='nt','Windows setup and shortcuts')
class SetupBootstrapTests(unittest.TestCase):
    def setUp(self):
        directory=ROOT/'.local/test-setup-bootstrap';directory.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='setup space ',dir=directory)
        self.addCleanup(self.temp.cleanup);self.work=Path(self.temp.name)

    def run_ps(self,body):
        source=self.work/'check.ps1'
        source.write_text("$ErrorActionPreference='Stop'\nSet-StrictMode -Version Latest\n"
            +". '"+str(ROOT/'tools/setup_python.ps1')+"'\n"
            +"function Invoke-WebRequest { throw 'UNEXPECTED_REAL_DOWNLOAD' }\n"
            +"function Start-Process { throw 'UNEXPECTED_REAL_INSTALLER' }\n"
            +"function Assert($condition,$message) { if (!$condition) { throw $message } }\n"
            +"$work='"+str(self.work)+"'\n"+body,encoding='utf-8-sig')
        return subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(source)],
            cwd=ROOT,capture_output=True,text=True,timeout=30)

    def assert_success(self,body):
        result=self.run_ps(body);self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_existing_usable_python_never_calls_installer(self):
        self.assert_success(r'''
function Get-Python312Candidates {
    @{Executable='wrong-version.exe';Prefix=@()}
    @{Executable='existing-python.exe';Prefix=@()}
}
$script:probes=0
function Invoke-Python($Executable,$Arguments) {
    $script:probes++
    if ($Executable -eq 'wrong-version.exe') { throw 'wrong version' }
}
function Install-Python312 { throw 'Existing Python must never trigger installation' }
$result=Ensure-Python312 -ProjectRoot $work
Assert ($result.Executable -eq 'existing-python.exe') 'Did not reuse Python'
Assert ($script:probes -eq 2) 'Did not skip incompatible Python'
''')

    def test_missing_python_installs_once_then_validates(self):
        self.assert_success(r'''
$script:finds=0;$script:installs=0
function Find-Python312 {
    $script:finds++
    if ($script:finds -gt 1) { return @{Executable='new-python.exe';Prefix=@()} }
    return $null
}
function Install-Python312($ProjectRoot) { $script:installs++ }
$result=Ensure-Python312 -ProjectRoot $work
Assert ($result.Executable -eq 'new-python.exe') 'New interpreter not returned'
Assert ($script:finds -eq 2 -and $script:installs -eq 1) 'Unexpected installation sequence'
''')

    def test_unusable_result_after_installation_fails(self):
        self.assert_success(r'''
function Find-Python312 { return $null }
function Install-Python312 { }
$failed=$false
try { Ensure-Python312 -ProjectRoot $work } catch { $failed=$_.Exception.Message -like '*could not be validated*' }
Assert $failed 'Unusable installation reported success'
''')

    def test_download_validation_install_flags_and_failures_without_installing(self):
        self.assert_success(r'''
$env:LOCALAPPDATA=Join-Path $work 'local-appdata'
$script:downloads=0;$script:starts=0;$script:mode='good'
function Invoke-WebRequest($Uri,$OutFile,[switch]$UseBasicParsing) {
    Assert ($Uri -eq 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe') 'Wrong source'
    $script:downloads++
    [IO.File]::WriteAllText($OutFile,'mock download, never executed')
}
function Get-FileHash($LiteralPath,$Algorithm) {
    $hash='67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb'
    if ($script:mode -eq 'hash') { $hash='bad' }
    return [pscustomobject]@{Hash=$hash}
}
function Get-AuthenticodeSignature($LiteralPath) {
    $certificate=New-Object PSObject
    $certificate | Add-Member -MemberType ScriptMethod -Name GetNameInfo -Value {
        param($type,$issuer)
        if ($script:mode -eq 'publisher') { return 'Unrelated publisher' }
        return 'Python Software Foundation'
    }
    $status=if ($script:mode -eq 'signature') {'NotSigned'} else {'Valid'}
    return [pscustomobject]@{Status=$status;SignerCertificate=$certificate}
}
function Start-Process($FilePath,$ArgumentList,[switch]$Wait,[switch]$PassThru,$WindowStyle) {
    $script:starts++
    Assert ($Wait -and $PassThru -and $WindowStyle -eq 'Hidden') 'Installer not waited/hidden'
    foreach ($option in @('/quiet','/norestart','InstallAllUsers=0','PrependPath=0','AppendPath=0','Include_launcher=0','AssociateFiles=0')) {
        Assert ($ArgumentList -contains $option) ('Missing option '+$option)
    }
    Assert (@($ArgumentList | Where-Object {$_ -like 'TargetDir="*"'}).Count -eq 1) 'Unquoted target path'
    $exitCode=if ($script:mode -eq 'exit') {1603} else {0}
    return [pscustomobject]@{ExitCode=$exitCode}
}
Install-Python312 -ProjectRoot $work
Assert ($script:downloads -eq 1 -and $script:starts -eq 1) 'Mock installation sequence failed'
foreach ($failure in @('hash','signature','publisher','exit')) {
    $script:mode=$failure;$before=$script:starts;$failed=$false
    try { Install-Python312 -ProjectRoot $work } catch { $failed=$true }
    Assert $failed ('Failure ignored: '+$failure)
    if ($failure -ne 'exit') { Assert ($script:starts -eq $before) 'Unverified installer executed' }
}
$target=Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312'
New-Item -ItemType Directory -Path $target -Force | Out-Null
$before=$script:downloads;$failed=$false
try { Install-Python312 -ProjectRoot $work } catch { $failed=$_.Exception.Message -like '*left intact*' }
Assert ($failed -and $script:downloads -eq $before) 'Existing unusable installation was touched'
''')

    def test_shortcut_target_icon_and_safe_repeat(self):
        self.assert_success("$project='"+str(ROOT)+"'\n"+'''
$destination=Join-Path $work 'Vayrshemon.lnk'
& (Join-Path $project 'tools/create_shortcut.ps1') -ProjectRoot $project -Destination $destination
& (Join-Path $project 'tools/create_shortcut.ps1') -ProjectRoot $project -Destination $destination
$shell=New-Object -ComObject WScript.Shell
$link=$shell.CreateShortcut($destination)
try {
    Assert ($link.TargetPath -eq (Join-Path $project 'launch.bat')) 'Wrong shortcut target'
    Assert ($link.WorkingDirectory -eq $project) 'Wrong working directory'
    Assert ($link.IconLocation -eq ((Join-Path $project 'data/icons/memon-color.ico')+',0')) 'Wrong icon'
    Assert (!$link.Arguments -and $link.WindowStyle -eq 7) 'Wrong launch options'
    $link.TargetPath=Join-Path $project 'setup.bat';$link.Save()
    $before=[Convert]::ToBase64String([IO.File]::ReadAllBytes($destination))
    $failed=$false
    try { & (Join-Path $project 'tools/create_shortcut.ps1') -ProjectRoot $project -Destination $destination } catch { $failed=$true }
    Assert ($failed -and [Convert]::ToBase64String([IO.File]::ReadAllBytes($destination)) -eq $before) 'Unrelated shortcut overwritten'
}
finally {
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($link)
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shell)
}
''')
