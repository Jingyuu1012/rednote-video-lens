param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $DownloaderArgs
)

$preferredPython = Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python\Python39\python.exe'
$pythonPath = if (Test-Path -LiteralPath $preferredPython) {
    $preferredPython
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonCommand.Source } else { $null }
}
$downloader = @(
    (Join-Path $env:USERPROFILE '.codex\skills\xiaohongshu-downloader\scripts\download_xiaohongshu.py'),
    (Join-Path $env:USERPROFILE '.claude\skills\xiaohongshu-downloader\scripts\download_xiaohongshu.py')
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $pythonPath -or -not (Test-Path -LiteralPath $downloader)) {
    Write-Error 'Xiaohongshu downloader runtime is missing from the Codex and Claude skill directories. Run scripts\doctor.ps1 for details.'
    exit 1
}

& $pythonPath $downloader @DownloaderArgs
exit $LASTEXITCODE
