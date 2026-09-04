[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Url,

    [Parameter(Mandatory = $true)]
    [string] $OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'

$preferredPython = Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python\Python39\python.exe'
$pythonPath = if (Test-Path -LiteralPath $preferredPython) {
    $preferredPython
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonCommand.Source } else { $null }
}
if (-not $pythonPath) {
    throw 'Python is unavailable. Run scripts\doctor.ps1 for details.'
}

$publicFetcher = Join-Path $PSScriptRoot 'fetch_public_note.py'
$downloader = Join-Path $PSScriptRoot 'download.ps1'
$frameExtractor = Join-Path $PSScriptRoot 'extract_keyframes.py'
foreach ($required in @($publicFetcher, $downloader, $frameExtractor)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required helper is missing: $required"
    }
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$resolvedOutput = (Resolve-Path -LiteralPath $OutputDirectory).Path
$noteJson = Join-Path $resolvedOutput 'note.json'
$platformSubtitle = Join-Path $resolvedOutput 'platform.zh-CN.srt'
$mediaDirectory = Join-Path $resolvedOutput 'media'
$framesDirectory = Join-Path $resolvedOutput 'frames'

$savedErrorAction = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$publicOutput = & $pythonPath $publicFetcher $Url --output $noteJson --subtitle-output $platformSubtitle --quiet 2>&1
$publicExitCode = $LASTEXITCODE
$ErrorActionPreference = $savedErrorAction
if ($publicExitCode -ne 0) {
    $publicOutput | Select-Object -Last 20 | Write-Error
    throw 'Anonymous public-note fetch failed. Stop before attempting any browser-cookie route.'
}

$note = Get-Content -Raw -Encoding UTF8 -LiteralPath $noteJson | ConvertFrom-Json
$hasPlatformSubtitle = Test-Path -LiteralPath $platformSubtitle -PathType Leaf

$downloadArguments = @($Url, '--output', $mediaDirectory, '--browser', 'none')
if (-not $hasPlatformSubtitle) {
    $downloadArguments += '--full'
}
$ErrorActionPreference = 'Continue'
$downloadOutput = & $downloader @downloadArguments 2>&1
$downloadExitCode = $LASTEXITCODE
$ErrorActionPreference = $savedErrorAction
if ($downloadExitCode -ne 0) {
    $downloadOutput | Select-Object -Last 20 | Write-Error
    throw 'Anonymous video download failed. Stop before attempting any browser-cookie route.'
}

$video = Get-ChildItem -LiteralPath $mediaDirectory -Recurse -File |
    Where-Object { $_.Extension -in @('.mp4', '.mkv', '.webm') } |
    Sort-Object Length -Descending |
    Select-Object -First 1
if (-not $video) {
    throw "No downloaded video was found under $mediaDirectory"
}

$ErrorActionPreference = 'Continue'
$frameOutput = & $pythonPath $frameExtractor $video.FullName --output $framesDirectory 2>&1
$frameExitCode = $LASTEXITCODE
$ErrorActionPreference = $savedErrorAction
if ($frameExitCode -ne 0) {
    $frameOutput | Write-Error
    throw 'Keyframe extraction failed.'
}

$manifest = [ordered]@{
    prepared_at = [DateTimeOffset]::UtcNow.ToString('o')
    source_url = $note.source_url
    note_json = $noteJson
    title = $note.title
    creator = $note.creator
    interactions = $note.interactions
    duration_seconds = $note.duration_seconds
    transcript = if ($hasPlatformSubtitle) { $platformSubtitle } else { $null }
    transcript_source = if ($hasPlatformSubtitle) { 'xiaohongshu-platform-source' } else { 'downloader-fallback-or-unavailable' }
    video = $video.FullName
    frames_manifest = Join-Path $framesDirectory 'frames.json'
}
$manifestPath = Join-Path $resolvedOutput 'evidence-manifest.json'
$utf8 = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText(
    $manifestPath,
    ($manifest | ConvertTo-Json -Depth 8),
    $utf8
)

$manifest | ConvertTo-Json -Depth 8
