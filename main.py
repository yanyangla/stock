#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股自选股每日【技术+新闻+X大佬观点】深度复盘与风控推送系统
自动运行脚本 - 支持 Gmail SMTP 发信
"""

import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import List, Dict, Any, Optional
import traceback

# 第三方库
import requests
import pandas as pd
import talib
from openai import OpenAI


# ============================================
# 工具函数：Markdown 转 HTML（带语法高亮）
# ============================================
def markdown_to_html(md_content: str) -> str:
    """
    将 Markdown 内容转换为带样式的 HTML
    支持：标题、粗体、列表、代码块、分割线、表格等
    """
    html_lines = []
    in_code_block = False
    in_table = False
    table_rows = []

    lines = md_content.split('\n')

    for line in lines:
        # 代码块处理
        if line.strip().startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                html_lines.append('<pre style="background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:6px;overflow-x:auto;font-family:Consolas,Monaco,monospace;font-size:13px;line-height:1.5;"><code>')
                in_code_block = True
            continue

        if in_code_block:
            # 转义 HTML
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(escaped)
            continue

        # 表格处理
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_rows = []

            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if all(c.replace('-', '').replace(':', '') == '' for c in cells):
                continue  # 跳过分隔行
            table_rows.append(cells)
            continue
        elif in_table:
            # 表格结束，输出 HTML 表格
            html_lines.append('<table style="border-collapse:collapse;width:100%;margin:12px 0;font-size:14px;">')
            for i, row in enumerate(table_rows):
                tag = 'th' if i == 0 else 'td'
                style = 'background:#f5f5f5;font-weight:600;' if i == 0 else ''
                cells_html = ''.join([f'<{tag} style="border:1px solid #ddd;padding:8px;text-align:left;{style}">{cell}</{tag}>' for cell in row])
                html_lines.append(f'<tr>{cells_html}</tr>')
            html_lines.append('</table>')
            in_table = False
            table_rows = []

        # 标题
        if line.startswith('### '):
            html_lines.append(f'<h3 style="color:#2563eb;margin:20px 0 10px;font-size:18px;">{line[4:].strip()}</h3>')
        elif line.startswith('## '):
            html_lines.append(f'<h2 style="color:#1e40af;margin:24px 0 12px;font-size:22px;border-bottom:2px solid #e5e7eb;padding-bottom:6px;">{line[3:].strip()}</h2>')
        elif line.startswith('# '):
            html_lines.append(f'<h1 style="color:#1e3a8a;margin:28px 0 14px;font-size:26px;">{line[2:].strip()}</h1>')
        # 分割线
        elif line.strip() in ['---', '———', '___']:
            html_lines.append('<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">')
        # 无序列表
        elif line.strip().startswith('- '):
            content = line.strip()[2:]
            content = _inline_format(content)
            html_lines.append(f'<li style="margin:4px 0 4px 20px;line-height:1.6;">{content}</li>')
        # 有序列表
        elif line.strip() and line.strip()[0].isdigit() and '. ' in line:
            content = line.split('. ', 1)[1] if '. ' in line else line
            content = _inline_format(content)
            html_lines.append(f'<li style="margin:4px 0 4px 20px;line-height:1.6;list-style-type:decimal;">{content}</li>')
        # 普通段落
        elif line.strip():
            content = _inline_format(line)
            html_lines.append(f'<p style="margin:8px 0;line-height:1.7;color:#374151;">{content}</p>')
        else:
            html_lines.append('')

    # 收尾：如果还在代码块或表格中
    if in_code_block:
        html_lines.append('</code></pre>')
    if in_table:
        html_lines.append('<table style="border-collapse:collapse;width:100%;margin:12px 0;font-size:14px;">')
        for i, row in enumerate(table_rows):
            tag = 'th' if i == 0 else 'td'
            cells_html = ''.join([f'<{tag} style="border:1px solid #ddd;padding:8px;text-align:left;">{cell}</{tag}>' for cell in row])
            html_lines.append(f'<tr>{cells_html}</tr>')
        html_lines.append('</table>')

    return '\n'.join(html_lines)


def _inline_format(text: str) -> str:
    """处理行内格式：粗体、斜体、行内代码"""
    import re
    # 行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'<code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;font-family:Consolas,monospace;font-size:13px;color:#d97706;">\1</code>', text)
    # 粗体 **text**
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong style="font-weight:600;color:#111827;">\1</strong>', text)
    # 斜体 *text*
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    return text


# ============================================
# 核心业务类：美股高级诊断 Skill
# ============================================
class USStockAdvancedSkill:
    """美股自选股深度诊断引擎"""

    def __init__(self, polygon_api_key: str, llm_api_key: str, llm_base_url: str = "https://open.bigmodel.cn/api/paas/v4/", llm_model: str = "glm-4-flash"):
        self.polygon_key = polygon_api_key
        self.llm_model = llm_model
        self.ai_client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)
        self.pure_sources = [
            "Bloomberg", "Reuters", "Wall Street Journal", "Dow Jones",
            "Benzinga", "PR Newswire", "Business Wire", "AP News",
            "Financial Times", "CNBC", "MarketWatch"
        ]

    def _check_market_and_post_market(self, ticker: str) -> str:
        """检查全局市场风险（VIX）和个股盘后异动"""
        try:
            # 获取 VIX 指数
            vix_url = f"https://api.polygon.io/v2/aggs/ticker/I:VIX/prev?apiKey={self.polygon_key}"
            vix_res = requests.get(vix_url, timeout=15).json()
            vix_close = vix_res.get('results', [{}])[0].get('c', 15.0)

            # 获取个股快照数据
            snapshot_url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}?apiKey={self.polygon_key}"
            snap_res = requests.get(snapshot_url, timeout=15).json()
            ticker_data = snap_res.get('ticker', {})

            close_price = ticker_data.get('min', {}).get('c', 0)
            if close_price == 0:
                close_price = ticker_data.get('lastQuote', {}).get('P', 0)

            post_market_price = ticker_data.get('lastTrade', {}).get('p', close_price)

            risk_status = "✅ 正常"

            # VIX 高位风险预警
            if vix_close > 22.0:
                risk_status = f"⚠️ **全局风险**：当前市场 VIX 恐慌指数高企 ({vix_close:.2f})，大盘环境恶劣，任何新开仓单笔仓位必须强制减半！"

            # 盘后暴跌风险预警
            if close_price > 0 and (post_market_price - close_price) / close_price < -0.04:
                pct = (post_market_price - close_price) / close_price * 100
                risk_status = f"🚨 **盘后暴雷**：该股在盘后交易中突发暴跌 {pct:.1f}%！技术面均线已被真实抛盘强行摧毁，今日所有买入策略【无条件强制取消】！"

            return risk_status

        except Exception as e:
            return f"⚠️ 风控数据获取失败: {str(e)}"

    def _fetch_technical_data(self, ticker: str) -> pd.DataFrame:
        """获取技术面数据并计算均线指标"""
        end_date = datetime.date.today().strftime('%Y-%m-%d')
        start_date = (datetime.date.today() - datetime.timedelta(days=365*2)).strftime('%Y-%m-%d')

        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}?adjusted=true&sort=asc&limit=5000&apiKey={self.polygon_key}"
        res = requests.get(url, timeout=30).json()

        if 'results' not in res or len(res['results']) < 200:
            raise ValueError(f"无法获取 {ticker} 的技术面数据，数据点不足。")

        df = pd.DataFrame(res['results'])
        df.rename(columns={'c': 'Close', 'h': 'High', 'l': 'Low', 'o': 'Open', 'v': 'Volume', 't': 'Timestamp'}, inplace=True)

        # 计算均线系统
        df['MA5'] = talib.SMA(df['Close'], timeperiod=5)
        df['MA10'] = talib.SMA(df['Close'], timeperiod=10)
        df['MA20'] = talib.SMA(df['Close'], timeperiod=20)
        df['MA50'] = talib.SMA(df['Close'], timeperiod=50)
        df['MA200'] = talib.SMA(df['Close'], timeperiod=200)
        df['Vol_MA20'] = talib.SMA(df['Volume'], timeperiod=20)
        df['RSI'] = talib.RSI(df['Close'], timeperiod=14)

        # MACD
        df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['Close'])

        return df

    def _fetch_pure_news(self, ticker: str) -> List[Dict[str, str]]:
        """获取高纯度源头新闻（过滤权威信源）"""
        url = f"https://api.polygon.io/v2/reference/news?ticker={ticker}&limit=15&apiKey={self.polygon_key}"
        res = requests.get(url, timeout=15).json()

        selected_news = []
        seen_titles = set()

        for item in res.get('results', []):
            publisher_name = item.get('publisher', {}).get('name', '')
            title = item.get('title', '').strip()

            # 过滤权威信源
            if any(src.lower() in publisher_name.lower() for src in self.pure_sources):
                if title.lower() not in seen_titles:
                    seen_titles.add(title.lower())
                    selected_news.append({
                        "title": title,
                        "description": item.get("description", "无内容摘要")[:200] + "...",
                        "source": publisher_name,
                        "url": item.get("article_url", "")
                    })

            if len(selected_news) == 3:
                break

        return selected_news

    def _fetch_x_influencer_insights(self, ticker: str) -> str:
        """获取 X 平台大佬观点（模拟数据库）"""
        x_database = {
            "NVDA": """【Leopold Aschenbrenner】: 百万卡集群扩容的物理极限与电力配给是核心。英伟达作为全栈黑盒交付，其卖方定价权在中期依然牢固，关注 CapEx 持续度。
【Shay Boloor】: AI 核心硬件端依然处于疯狂吃货阶段，但需密切监控高位筹码在细分光模块及服务器组装厂之间的分歧。""",

            "TSLA": """【Leopold Aschenbrenner】: FSD 的质变配合分布式能源网络，使其本质上是算力基础设施股，不能用纯车企估值。
【Shay Boloor】: 硬件端算力中心扩容符合预期，技术面上关注长期箱体上轨的放量突破契机。""",

            "AMD": """【Shay Boloor】: 下游客户急切寻找英伟达替代品，MI300X 系列出货量及软件生态包围圈是追赶关键，注意多头均线回踩节点。""",

            "MU": """【Shay Boloor】: HBM 订单能见度已延伸至 2026 年，内存端在 AI 数据中心迭代周期中享有极高议价权，回调即是机会。""",

            "PLTR": """【Leopold Aschenbrenner】: 军事情报与政府合约的确定性收入是护城河，AIP 平台的商业端渗透率是二次增长曲线关键。""",

            "MRVL": """【Shay Boloor】: 定制化 ASIC 芯片（为 Google/Amazon 代工）是毛利放大器，数据中心收入占比突破 70% 后估值逻辑切换。"""
        }

        return x_database.get(ticker, "【Leopold & Shay】: 近期在 X 上未对此 Ticker 发表定向高权重产业观点。")

    def _judge_trading_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """判断交易结构（四线多头排列、回踩、突破等）"""
        today = df.iloc[-1]
        yesterday = df.iloc[-2]

        # 四线多头排列判断
        is_bullish_alignment = (
            today['MA5'] > today['MA10'] and
            today['MA10'] > today['MA20'] and
            today['MA20'] > today['MA50']
        )

        # 量能判断
        is_volume_shrinking = today['Volume'] < today['Vol_MA20'] * 0.75
        is_volume_exploding = today['Volume'] > today['Vol_MA20'] * 1.5

        # 突破判断（近 22 日新高）
        is_breakout = today['Close'] > max(df['Close'].iloc[-22:-1])

        # RSI 判断
        rsi_status = "中性"
        if today['RSI'] > 70:
            rsi_status = "⚠️ 超买区间"
        elif today['RSI'] < 30:
            rsi_status = "📉 超卖区间"

        # 交易结构判定
        if is_bullish_alignment:
            if is_breakout and is_volume_exploding:
                side = "🔥 **右侧交易 - 放量平台强行突破（主升浪确立点）**"
            elif today['Close'] < yesterday['Close'] and is_volume_shrinking and today['Low'] <= today['MA10'] * 1.02:
                side = "🎯 **右侧交易 - 强趋势股缩量回踩10日线（高性价比拦截点）**"
            else:
                side = "✅ **右侧交易 - 四线多头排列趋势正常持有中**"
        else:
            if today['Close'] <= today['MA200'] * 1.02 and today['RSI'] < 35:
                side = "💎 **左侧交易 - 超跌触及200日年线支撑（尝试左侧长线潜伏底）**"
            else:
                side = "⏸️ **中性观望区间 - 均线系统交织纠缠，暂无清晰量价结构**"

        return {
            "side": side,
            "current_price": f"${today['Close']:.2f}",
            "ma_status": f"MA5: ${today['MA5']:.2f} | MA10: ${today['MA10']:.2f} | MA20: ${today['MA20']:.2f} | MA50: ${today['MA50']:.2f}",
            "volume_status": f"今日量能 {'**良性缩量**' if is_volume_shrinking else ('**放量动能**' if is_volume_exploding else '正常')}，当前相对量比为 {today['Volume']/today['Vol_MA20']:.2f}x",
            "rsi_status": f"RSI(14): {today['RSI']:.1f} - {rsi_status}",
            "support_1": f"10日均线位 ${today['MA10']:.2f}",
            "support_2": f"50日均线/中期核心防御闸 ${today['MA50']:.2f}",
            "resistance": f"前高压力位 ${max(df['Close'].iloc[-22:]):.2f}"
        }

    def _generate_ai_report(self, ticker: str, risk_status: str, tech_res: Dict, news_res: List, x_insights: str) -> str:
        """使用 LLM 生成深度诊断报告"""

        news_text = "\n".join([f"- [{n['title']}]({n['url']}) ({n['source']})" for n in news_res]) if news_res else "无重大新闻"

        prompt = f"""你是一位精通威科夫量价理论、趋势交易，且深度跟踪美股 AI 产业的核心策略师。
请对股票 **{ticker}** 进行每日深度结构诊断，输出结构化、可操作的交易建议。

## 输入数据
### 1. 风控状态
{risk_status}

### 2. 技术面结构
- 交易信号: {tech_res['side']}
- 当前价格: {tech_res['current_price']}
- 均线系统: {tech_res['ma_status']}
- 量能状态: {tech_res['volume_status']}
- RSI 指标: {tech_res['rsi_status']}
- 核心支撑: {tech_res['support_1']} / {tech_res['support_2']}
- 压力位: {tech_res['resistance']}

### 3. 源头新闻
{news_text}

### 4. X 大佬观点对撞
{x_insights}

## 输出要求
请按以下 Markdown 格式输出（不要省略任何部分）：

### 📊 [{ticker}] 技术面结构诊断
（一段话总结当前技术状态，明确趋势方向与量价配合情况）

### 📰 核心新闻驱动
（列出 2-3 条关键新闻及其对股价的影响判断）

### 🎯 交易策略建议
（明确的买入/持有/卖出建议，包含具体触发条件和止损位）

### ⚠️ 风险警示
（当前最大的 2-3 个风险点）

### 🧠 X 大佬观点对撞
（对比 Leopold 和 Shay 的观点，指出分歧与一致性，给出你的综合判断）
"""

        try:
            response = self.ai_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1200
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ AI 报告生成失败: {str(e)}"

    def execute_skill(self, watchlist: List[str]) -> str:
        """执行完整诊断流程，返回 Markdown 报告"""
        final_report = f"""# 📅 美股自选股每日【技术 + 新闻 + X大佬】深度复盘报告

**报告时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**自选股池**: 共 {len(watchlist)} 只
**数据源**: Polygon.io（技术面/新闻） + 智谱AI GLM-4（策略生成）

---

"""

        for ticker in watchlist:
            try:
                print(f"正在诊断: {ticker}...")

                risk_status = self._check_market_and_post_market(ticker)
                df = self._fetch_technical_data(ticker)
                tech_res = self._judge_trading_structure(df)
                news_res = self._fetch_pure_news(ticker)
                x_insights = self._fetch_x_influencer_insights(ticker)

                stock_analysis = self._generate_ai_report(ticker, risk_status, tech_res, news_res, x_insights)

                final_report += stock_analysis + "\n\n" + ("—" * 40) + "\n\n"

            except Exception as e:
                error_msg = f"### ❌ [{ticker}] 诊断失败\n\n**原因**: {str(e)}\n\n**堆栈追踪**:\n```\n{traceback.format_exc()}\n```\n\n"
                final_report += error_msg + ("—" * 40) + "\n\n"

        return final_report


# ============================================
# 邮件发送模块
# ============================================
def send_email_report(
    subject: str,
    html_content: str,
    sender_email: str,
    sender_password: str,
    recipient_email: str
) -> bool:
    """
    使用 Gmail SMTP 发送 HTML 格式邮件

    Args:
        subject: 邮件主题
        html_content: HTML 格式的邮件正文
        sender_email: 发件人邮箱
        sender_password: 发件人应用专用密码
        recipient_email: 收件人邮箱

    Returns:
        bool: 发送是否成功
    """
    try:
        # 构建邮件对象
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = formataddr(('美股智能复盘系统', sender_email))
        message['To'] = recipient_email

        # 添加 HTML 正文
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)

        # 连接 Gmail SMTP 服务器（SSL 加密）
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        print(f"✅ 邮件发送成功: {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        traceback.print_exc()
        return False


# ============================================
# 主程序入口
# ============================================
def main():
    """主函数：生成报告并发送邮件"""

    # ========== 1. 从环境变量读取配置 ==========
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    # 收件人邮箱（写死）
    RECIPIENT_EMAIL = "yanyanggou7@gmail.com"

    # 自选股列表
    WATCHLIST = [
        "AMD", "ASTS", "BE", "CRDO", "DRAM", "INTC", "IREN", "MRVL", "MU",
        "NBIS", "NOK", "NVDA", "OKLO", "PLTR", "QQQ", "RKLB", "SATS",
        "SMH", "SNDK", "SPCX", "TSLA", "VOO", "VRT"
    ]

    # ========== 2. 环境变量校验 ==========
    missing_vars = []
    for var_name, var_value in [
        ("POLYGON_API_KEY", POLYGON_API_KEY),
        ("LLM_API_KEY", LLM_API_KEY),
        ("SENDER_EMAIL", SENDER_EMAIL),
        ("EMAIL_PASSWORD", EMAIL_PASSWORD)
    ]:
        if not var_value:
            missing_vars.append(var_name)

    if missing_vars:
        print(f"❌ 错误: 以下环境变量未设置: {', '.join(missing_vars)}")
        return False

    print("=" * 60)
    print("🚀 美股自选股每日深度复盘系统启动")
    print("=" * 60)
    print(f"📅 日期: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 自选股数量: {len(WATCHLIST)}")
    print(f"📧 收件人: {RECIPIENT_EMAIL}")
    print("=" * 60)

    # ========== 3. 生成诊断报告 ==========
    try:
        print("\n[1/3] 初始化诊断引擎...")
        skill = USStockAdvancedSkill(
            polygon_api_key=POLYGON_API_KEY,
            llm_api_key=LLM_API_KEY,
            llm_base_url=LLM_BASE_URL,
            llm_model=LLM_MODEL
        )

        print("[2/3] 执行多维度诊断（技术面 + 新闻 + X观点）...")
        md_report = skill.execute_skill(WATCHLIST)

        print("[3/3] 转换 Markdown 为 HTML...")
        html_report = markdown_to_html(md_report)

        # 添加整体样式
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9fafb;
            color: #1f2937;
            line-height: 1.6;
        }}
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: Consolas, Monaco, monospace;
            font-size: 13px;
        }}
    </style>
</head>
<body>
{html_report}
</body>
</html>"""

        print("✅ 报告生成完成")

    except Exception as e:
        print(f"❌ 报告生成失败: {str(e)}")
        traceback.print_exc()
        return False

    # ========== 4. 发送邮件 ==========
    print("\n[邮件发送] 正在发送至 Gmail...")
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    subject = f"📊 美股自选股每日深度复盘 [{today_str}]"

    success = send_email_report(
        subject=subject,
        html_content=full_html,
        sender_email=SENDER_EMAIL,
        sender_password=EMAIL_PASSWORD,
        recipient_email=RECIPIENT_EMAIL
    )

    if success:
        print("\n" + "=" * 60)
        print("🎉 任务完成！报告已成功发送至邮箱。")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ 任务失败！请检查邮件配置。")
        print("=" * 60)
        return False


if __name__ == "__main__":
    main()
