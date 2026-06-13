# 📊 美股自选股每日深度复盘系统

自动化的美股技术面 + 新闻 + X大佬观点深度分析系统，每日收盘后自动生成报告并发送至邮箱。

## 🎯 核心功能

- **技术面分析**：四线多头排列、10日线回踩、量价结构、RSI、MACD 等
- **新闻过滤**：只抓取 Bloomberg、Reuters、WSJ 等权威信源
- **X大佬观点**：集成 Leopold Aschenbrenner、Shay Boloor 等产业大佬观点
- **风控预警**：VIX 高位预警、盘后暴跌实时拦截
- **自动推送**：HTML 格式邮件自动发送至指定邮箱

## 📦 项目结构

```
us_stock_daily_report/
├── main.py                          # 主程序
├── requirements.txt                 # Python 依赖
└── .github/
    └── workflows/
        └── daily_stock.yml          # GitHub Actions 工作流
```

## 🔧 本地运行

### 1. 安装 TA-Lib C 语言依赖

**Windows:**
```powershell
# 下载预编译的 wheel 文件
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp311-cp311-win_amd64.whl
```

**macOS:**
```bash
brew install ta-lib
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install -y build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 设置环境变量

**Windows (PowerShell):**
```powershell
$env:POLYGON_API_KEY = "你的 Polygon.io API Key"
$env:LLM_API_KEY = "你的 OpenAI API Key"
$env:SENDER_EMAIL = "你的 Gmail 邮箱"
$env:EMAIL_PASSWORD = "你的 Gmail 应用专用密码"
```

**macOS/Linux:**
```bash
export POLYGON_API_KEY="你的 Polygon.io API Key"
export LLM_API_KEY="你的 OpenAI API Key"
export SENDER_EMAIL="你的 Gmail 邮箱"
export EMAIL_PASSWORD="你的 Gmail 应用专用密码"
```

### 4. 运行程序

```bash
python main.py
```

## ☁️ GitHub Actions 自动化部署

### 步骤 1：创建 GitHub 仓库

1. 在 GitHub 创建新仓库（例如：`us-stock-daily-report`）
2. 将本项目代码推送至仓库

### 步骤 2：配置 Secrets

进入仓库页面 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

添加以下 4 个 Secrets：

| Secret 名称 | 说明 | 获取方式 |
|------------|------|---------|
| `POLYGON_API_KEY` | Polygon.io API 密钥 | 访问 [polygon.io](https://polygon.io) 注册获取 |
| `LLM_API_KEY` | OpenAI API 密钥 | 访问 [platform.openai.com](https://platform.openai.com) 获取 |
| `SENDER_EMAIL` | 发件人 Gmail 邮箱 | 你的 Gmail 地址 |
| `EMAIL_PASSWORD` | Gmail 应用专用密码 | 见下方说明 |

### 步骤 3：启用 GitHub Actions

1. 进入仓库的 **Actions** 页面
2. 如果看到提示，点击 **I understand my workflows, go ahead and enable them**
3. 工作流将在每天 UTC 21:30（美东时间 16:30/17:30）自动执行

### 步骤 4：手动测试

在 Actions 页面选择 **US Stock Daily Analysis** 工作流，点击 **Run workflow** 进行手动测试。

## 📧 Gmail 应用专用密码设置

1. 登录 Google 账号：https://myaccount.google.com/
2. 开启 **两步验证**（如果未开启）
3. 搜索 **应用专用密码** 或访问：https://myaccount.google.com/apppasswords
4. 创建新密码：
   - 应用名称：`美股复盘系统`
   - 点击 **创建**
5. 复制生成的 16 位密码（格式：`xxxx xxxx xxxx xxxx`）
6. 将此密码设置为 `EMAIL_PASSWORD` Secret

## 🔑 API 密钥获取

### Polygon.io API Key
1. 访问：https://polygon.io
2. 注册账号（免费版每分钟 5 次调用）
3. 进入 Dashboard 复制 API Key

### OpenAI API Key
1. 访问：https://platform.openai.com/api-keys
2. 创建新的 API Key
3. 复制 Key（以 `sk-` 开头）

## 📝 自选股修改

在 `main.py` 中修改 `WATCHLIST` 变量：

```python
WATCHLIST = [
    "AMD", "NVDA", "TSLA", ...  # 你的自选股代码
]
```

## 🐛 常见问题

### Q: TA-Lib 安装失败？
A: 确保先安装了 C 语言依赖（见上文"安装 TA-Lib C 语言依赖"部分）

### Q: 邮件发送失败？
A: 检查：
1. Gmail 是否开启了两步验证
2. 是否使用了应用专用密码（不是登录密码）
3. 发件人邮箱是否正确

### Q: GitHub Actions 报错？
A: 检查：
1. 4 个 Secrets 是否都已正确配置
2. 查看 Actions 日志定位具体错误

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
