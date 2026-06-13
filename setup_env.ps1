# ============================================================
# 快速设置环境变量脚本 (Windows PowerShell)
# 使用方法: 在 PowerShell 中运行此脚本
#   .\setup_env.ps1
# ============================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "美股自选股每日复盘系统 - 环境变量配置" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 提示用户输入
$POLYGON_API_KEY = Read-Host "请输入 Polygon.io API Key"
$LLM_API_KEY = Read-Host "请输入 OpenAI API Key"
$SENDER_EMAIL = Read-Host "请输入发件人 Gmail 邮箱"
$EMAIL_PASSWORD = Read-Host "请输入 Gmail 应用专用密码" -AsSecureString

# 转换安全字符串
$EMAIL_PASSWORD_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($EMAIL_PASSWORD)
)

# 设置环境变量（当前会话）
$env:POLYGON_API_KEY = $POLYGON_API_KEY
$env:LLM_API_KEY = $LLM_API_KEY
$env:SENDER_EMAIL = $SENDER_EMAIL
$env:EMAIL_PASSWORD = $EMAIL_PASSWORD_PLAIN

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "✅ 环境变量已设置（当前 PowerShell 会话有效）" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "接下来你可以运行:" -ForegroundColor Yellow
Write-Host "  python test_local.py  # 测试系统" -ForegroundColor White
Write-Host "  python main.py        # 生成并发送报告" -ForegroundColor White
Write-Host ""
Write-Host "提示: 关闭 PowerShell 后环境变量会失效" -ForegroundColor Gray
Write-Host "如需永久保存，请将变量添加到系统环境变量中" -ForegroundColor Gray
