# setup_mediamtx.ps1
# Automates downloading and setting up MediaMTX for Windows

$version = "v1.19.0"
$url = "https://github.com/bluenviron/mediamtx/releases/download/$version/mediamtx_${version}_windows_amd64.zip"
$binDir = Join-Path $PSScriptRoot "..\bin\mediamtx"
$zipPath = Join-Path $binDir "mediamtx.zip"
$exePath = Join-Path $binDir "mediamtx.exe"

# Create directory if it doesn't exist
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
    Write-Output "Created directory $binDir"
}

# Download MediaMTX if executable doesn't exist
if (-not (Test-Path $exePath)) {
    Write-Output "Downloading MediaMTX $version from $url..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
        Write-Output "Downloaded successfully. Extracting..."
        
        Expand-Archive -Path $zipPath -DestinationPath $binDir -Force
        Remove-Item -Path $zipPath -Force
        Write-Output "MediaMTX extracted to $binDir"
    }
    catch {
        Write-Error "Failed to download or extract MediaMTX: $_"
        exit 1
    }
} else {
    Write-Output "MediaMTX already exists at $exePath"
}

# Generate a default mediamtx.yml if it doesn't exist
$configPath = Join-Path $binDir "mediamtx.yml"
if (-not (Test-Path $configPath)) {
    Write-Output "Generating default mediamtx.yml..."
    $configContent = @"
# MediaMTX Configuration for NTPC PPE Detection PoC
paths:
  all:
    # Allow local RTSP streams
    source: publisher
"@
    Set-Content -Path $configPath -Value $configContent
    Write-Output "Configuration created at $configPath"
}
