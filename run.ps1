# ============================================================
# 一键运行脚本 (Windows PowerShell)
# 使用方法: 在 PowerShell 中运行此脚本
#   .\run.ps1
# ============================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🚀 美股自选股每日复盘系统 - 一键运行" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python 是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python 版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 未安装，请先安装 Python 3.11+" -ForegroundColor Red
    exit 1
}

# 检查是否已安装依赖
Write-Host ""
Write-Host "检查 Python 依赖..." -ForegroundColor Yellow

$taLibInstalled = python -c "import talib" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ TA-Lib 未安装，正在安装..." -ForegroundColor Yellow
    pip install TA-Lib
}

# 检查其他依赖
pip install -r requirements.txt --quiet

Write-Host "✅ 依赖检查完成" -ForegroundColor Green

# 检查环境变量
Write-Host ""
Write-Host "检查环境变量..." -ForegroundColor Yellow

$missing = @()
if (-not $env:POLYGON_API_KEY) { $missing += "POLYGON_API_KEY" }
if (-not $env:LLM_API_KEY) { $missing += "LLM_API_KEY" }
if (-not $env:SENDER_EMAIL) { $missing += "SENDER_EMAIL" }
if (-not $env:EMAIL_PASSWORD) { $missing += "EMAIL_PASSWORD" }

if ($missing.Count -gt 0) {
    Write-Host "❌ 以下环境变量未设置:" -ForegroundColor Red
    foreach ($var in $missing) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "请先运行以下命令设置环境变量:" -ForegroundColor Yellow
    Write-Host '  $env:POLYGON_API_KEY = "你的key"' -ForegroundColor White
    Write-Host '  $env:LLM_API_KEY = "你的key"' -ForegroundColor White
    Write-Host '  $env:SENDER_EMAIL = "你的邮箱"' -ForegroundColor White
    Write-Host '  $env:EMAIL_PASSWORD = "你的密码"' -ForegroundColor White
    Write-Host ""
    Write-Host "或运行 setup_env.ps1 脚本进行交互式配置" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 环境变量已设置" -ForegroundColor Green

# 运行主程序
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "开始生成报告..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

python main.py

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "任务完成！" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
