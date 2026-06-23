param(
    [string]$PythonExe = "python",
    [switch]$EnableNacos,
    [string]$NacosServerAddr = "127.0.0.1:8848",
    [string]$NacosNamespace = "public",
    [string]$NacosGroup = "DEFAULT_GROUP",
    [string]$NacosUsername = "",
    [string]$NacosPassword = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$aiServiceDir = Join-Path $repoRoot "ai-service"

if (-not (Test-Path (Join-Path $aiServiceDir "app.py"))) {
    throw "Cannot find ai-service/app.py under $aiServiceDir"
}

function Set-NacosEnv {
    param(
        [string]$ServerAddr,
        [string]$Namespace,
        [string]$Group,
        [string]$Username,
        [string]$Password
    )

    $env:NACOS_ENABLED = "true"
    $env:NACOS_DISCOVERY_ENABLED = "true"
    $env:NACOS_CONFIG_ENABLED = "true"
    $env:NACOS_SERVER_ADDR = $ServerAddr
    $env:NACOS_NAMESPACE = $Namespace
    $env:NACOS_GROUP = $Group

    if ($Username) {
        $env:NACOS_USERNAME = $Username
    }
    if ($Password) {
        $env:NACOS_PASSWORD = $Password
    }
}

Push-Location $aiServiceDir
try {
    if ($EnableNacos) {
        Set-NacosEnv -ServerAddr $NacosServerAddr -Namespace $NacosNamespace -Group $NacosGroup -Username $NacosUsername -Password $NacosPassword
        Write-Host "Starting ai-service with Nacos: $NacosServerAddr"
    } else {
        Write-Host "Starting ai-service without Nacos"
    }

    Write-Host "Working directory: $aiServiceDir"
    & $PythonExe "app.py"
} finally {
    Pop-Location
}
