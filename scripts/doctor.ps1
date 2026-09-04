$skillRoot = Split-Path -Parent $PSScriptRoot
$redbook = Join-Path $PSScriptRoot 'redbook.ps1'
$download = Join-Path $PSScriptRoot 'download.ps1'
$frameScript = Join-Path $PSScriptRoot 'extract_keyframes.py'
$publicFetchScript = Join-Path $PSScriptRoot 'fetch_public_note.py'
$prepareScript = Join-Path $PSScriptRoot 'prepare_breakdown.ps1'

$checks = [ordered]@{}
$checks['skill_root'] = Test-Path -LiteralPath (Join-Path $skillRoot 'SKILL.md')
$redbookCandidates = @(
    (Join-Path $env:USERPROFILE '.codex\skills\redbook\dist\cli.js'),
    (Join-Path $env:USERPROFILE '.claude\skills\redbook\dist\cli.js')
)
$downloaderCandidates = @(
    (Join-Path $env:USERPROFILE '.codex\skills\xiaohongshu-downloader\scripts\download_xiaohongshu.py'),
    (Join-Path $env:USERPROFILE '.claude\skills\xiaohongshu-downloader\scripts\download_xiaohongshu.py')
)
$checks['redbook_cli'] = [bool]($redbookCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1)
$checks['downloader'] = [bool]($downloaderCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1)
$checks['keyframe_script'] = Test-Path -LiteralPath $frameScript
$checks['public_fetch_script'] = Test-Path -LiteralPath $publicFetchScript
$checks['prepare_script'] = Test-Path -LiteralPath $prepareScript

& $redbook --version
$redbookExit = $LASTEXITCODE
& $download --doctor
$downloadExit = $LASTEXITCODE

$checks['redbook_runtime'] = ($redbookExit -eq 0)
$checks['media_runtime'] = ($downloadExit -eq 0)
$checks.GetEnumerator() | ForEach-Object { "{0}: {1}" -f $_.Key, $_.Value }

if ($checks.Values -contains $false) {
    exit 1
}
exit 0
