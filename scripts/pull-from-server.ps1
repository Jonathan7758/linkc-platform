# LinkC 文档拉取脚本 (Windows PowerShell)
# 用法: .\pull-from-server.ps1
# 功能: 从服务器拉取最新文档到本地

param(
    [string]$Server = "101.47.67.225",
    [string]$User = "root",
    [string]$RemotePath = "/root/linkc-platform"
)

$ErrorActionPreference = "Stop"

function Write-Step { param($msg) Write-Host "▶ $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "         LinkC 文档拉取工具 v1.0                        " -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Step "拉取目标: $ProjectRoot"

# 要拉取的文件
$PullFiles = @(
    "CLAUDE.md",
    "docs/LESSONS_LEARNED.md",
    "docs/ARCHITECTURE.md"
)

Write-Step "从服务器拉取最新文档..."

foreach ($file in $PullFiles) {
    $localPath = Join-Path $ProjectRoot $file
    $localDir = Split-Path -Parent $localPath
    
    # 确保本地目录存在
    if (-not (Test-Path $localDir)) {
        New-Item -ItemType Directory -Path $localDir -Force | Out-Null
    }
    
    Write-Host "  拉取: $file"
    scp "${User}@${Server}:${RemotePath}/${file}" $localPath 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "  已拉取: $file"
    } else {
        Write-Host "  跳过: $file (服务器不存在)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Success "拉取完成!"
Write-Host ""
