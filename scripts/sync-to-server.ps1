# LinkC 文档同步脚本 (Windows PowerShell)
# 用法: .\sync-to-server.ps1
# 功能: 将本地文档同步到服务器并推送到Git

param(
    [string]$Server = "101.47.67.225",
    [string]$User = "root",
    [string]$RemotePath = "/root/linkc-platform",
    [switch]$DocsOnly,
    [switch]$GitPush
)

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-Step { param($msg) Write-Host "▶ $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "⚠ $msg" -ForegroundColor Yellow }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "         LinkC 文档同步工具 v1.0                        " -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

# 获取脚本所在目录的父目录（项目根目录）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Step "项目目录: $ProjectRoot"

# 要同步的文件列表
$SyncFiles = @(
    "CLAUDE.md",
    "docs/LESSONS_LEARNED.md",
    "docs/ARCHITECTURE.md",
    "docs/CONVENTIONS.md",
    "interfaces/data_models.py",
    "interfaces/mcp_tools.py",
    "interfaces/events.py",
    "interfaces/__init__.py"
)

# 要同步的目录
$SyncDirs = @(
    "docs/specs",
    ".claude/prompts"
)

Write-Step "开始同步文件到服务器..."

# 同步单个文件
foreach ($file in $SyncFiles) {
    $localPath = Join-Path $ProjectRoot $file
    if (Test-Path $localPath) {
        $remotePath = "$RemotePath/$file"
        Write-Host "  同步: $file"
        scp $localPath "${User}@${Server}:${remotePath}" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  已同步: $file"
        } else {
            Write-Warn "  跳过(可能不存在远程目录): $file"
        }
    } else {
        Write-Warn "  本地不存在: $file"
    }
}

# 同步目录
foreach ($dir in $SyncDirs) {
    $localPath = Join-Path $ProjectRoot $dir
    if (Test-Path $localPath) {
        Write-Host "  同步目录: $dir"
        scp -r $localPath "${User}@${Server}:${RemotePath}/$(Split-Path -Parent $dir)/" 2>$null
    }
}

Write-Success "文件同步完成!"

# Git推送（可选）
if ($GitPush) {
    Write-Step "推送到Git仓库..."
    
    ssh "${User}@${Server}" @"
cd $RemotePath
git add -A
git status
git commit -m "docs: 同步更新文档 $(Get-Date -Format 'yyyy-MM-dd HH:mm')" || echo '没有新更改'
git push origin main || git push origin master
"@
    
    Write-Success "Git推送完成!"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "                   同步完成!                            " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "  1. SSH到服务器查看: ssh ${User}@${Server}"
Write-Host "  2. 推送到Git: .\sync-to-server.ps1 -GitPush"
Write-Host ""
