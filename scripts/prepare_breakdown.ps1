[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Url,

    [Parameter(Mandatory = $true)]
    [string] $OutputDirectory
)

$skillRoot = Split-Path -Parent $PSScriptRoot
$cli = Join-Path $PSScriptRoot 'rednote_video_lens.py'
$venvPython = Join-Path $skillRoot '.venv\Scripts\python.exe'
$preferredPython = Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python\Python39\python.exe'

if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
    & $venvPython $cli prepare --url $Url --output-dir $OutputDirectory
} elseif (Test-Path -LiteralPath $preferredPython -PathType Leaf) {
    & $preferredPython $cli prepare --url $Url --output-dir $OutputDirectory
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $cli prepare --url $Url --output-dir $OutputDirectory
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $cli prepare --url $Url --output-dir $OutputDirectory
} else {
    Write-Error 'Python 3.9+ is required.'
    exit 1
}
exit $LASTEXITCODE
