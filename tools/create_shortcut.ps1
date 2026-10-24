param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Destination = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$target = (Resolve-Path -LiteralPath (Join-Path $ProjectRoot 'launch.bat')).Path
$icon = (Resolve-Path -LiteralPath (Join-Path $ProjectRoot 'data\icons\memon-color.ico')).Path
if (!$Destination) {
    $desktop = [Environment]::GetFolderPath('Desktop')
    if (!$desktop) { throw 'Windows did not provide a Desktop folder for this user.' }
    $Destination = Join-Path $desktop 'Vayrshemon.lnk'
}
$Destination = [IO.Path]::GetFullPath($Destination)
if ([IO.Path]::GetExtension($Destination) -ine '.lnk') { throw 'Shortcut destination must end in .lnk.' }
if (!(Test-Path -LiteralPath (Split-Path -Parent $Destination) -PathType Container)) { throw 'Shortcut destination folder does not exist.' }
$shell = $null
$shortcut = $null
try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Destination)
    if ((Test-Path -LiteralPath $Destination) -and
        ($shortcut.TargetPath -ine $target -or $shortcut.Arguments)) {
        throw "An existing shortcut points elsewhere and has been left intact: $Destination"
    }
    $shortcut.TargetPath = $target
    $shortcut.Arguments = ''
    $shortcut.WorkingDirectory = $ProjectRoot
    $shortcut.IconLocation = "$icon,0"
    $shortcut.Description = 'Vayrshemon - Language Workbench and Language Forge'
    $shortcut.WindowStyle = 7 # Minimize the short-lived batch window; the editor maximizes itself.
    $shortcut.Save()
    Write-Host "Desktop shortcut ready: $Destination"
}
finally {
    if ($shortcut) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shortcut) }
    if ($shell) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shell) }
}
