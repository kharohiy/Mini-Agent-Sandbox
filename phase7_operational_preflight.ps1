[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [int]$ApiPort = 8017
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = Split-Path -Parent $PSCommandPath
}

function Test-LocalHttp([string]$Uri) {
    try {
        $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch { return $false }
}

function Test-DockerReady {
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & docker info *> $null
        return $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $savedPreference
    }
}

if (-not (Test-DockerReady)) {
    $dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
    $dockerCliRoot = if ($dockerCommand) {
        Split-Path (Split-Path (Split-Path $dockerCommand.Source -Parent) -Parent) -Parent
    }
    $dockerDesktop = @(
        'C:\Program Files\Docker\Docker\Docker Desktop.exe',
        $(if ($dockerCliRoot) { Join-Path $dockerCliRoot 'Docker Desktop.exe' })
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    if (-not (Test-Path -LiteralPath $dockerDesktop)) {
        throw 'Docker Desktop is unavailable and its executable was not found.'
    }
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    $deadline = (Get-Date).AddSeconds(60)
    do {
        Start-Sleep -Seconds 2
    } while (-not (Test-DockerReady) -and (Get-Date) -lt $deadline)
    if (-not (Test-DockerReady)) { throw 'Docker Desktop did not become ready within 60 seconds.' }
}

$tags = (& ollama list 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw "Native Ollama is unavailable: $tags" }
foreach ($model in 'qwen2.5:14b', 'nomic-embed-text:latest') {
    if ($tags -notmatch [regex]::Escape($model)) { throw "Required Ollama model is not installed: $model" }
}
if (-not (Test-LocalHttp 'http://127.0.0.1:11434/api/tags')) { throw 'Native Ollama endpoint did not answer.' }

$apiProcess = Start-Process -FilePath python -ArgumentList '-m','uvicorn','api:app','--host','127.0.0.1',"--port=$ApiPort" -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru
try {
    $deadline = (Get-Date).AddSeconds(20)
    do {
        if (Test-LocalHttp "http://127.0.0.1:$ApiPort/openapi.json") { break }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    if (-not (Test-LocalHttp "http://127.0.0.1:$ApiPort/openapi.json")) { throw 'FastAPI did not become ready.' }
} finally {
    if (-not $apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id -Force }
}

[pscustomobject]@{
    docker = 'ready'; ollama_endpoint = 'ready'; required_models = 'present'; fastapi = 'ready'
    runner_command = 'python runner.py --resume <new-task-id>'
    runner_policy = 'Start separately; do not wrap it in an external short timeout.'
} | ConvertTo-Json
