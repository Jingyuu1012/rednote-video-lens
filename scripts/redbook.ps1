param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $RedbookArgs
)

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$nodePath = if ($nodeCommand) { $nodeCommand.Source } else { $null }
if (-not $nodePath) {
    $bundledNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
    if (Test-Path -LiteralPath $bundledNode) {
        $nodePath = $bundledNode
    }
}

$cli = @(
    (Join-Path $env:USERPROFILE '.codex\skills\redbook\dist\cli.js'),
    (Join-Path $env:USERPROFILE '.claude\skills\redbook\dist\cli.js')
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $nodePath -or -not (Test-Path -LiteralPath $cli)) {
    Write-Error 'Redbook runtime is missing from the Codex and Claude skill directories. Run scripts\doctor.ps1 for details.'
    exit 1
}

& $nodePath $cli @RedbookArgs
exit $LASTEXITCODE
