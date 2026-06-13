#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地测试脚本 - 用于快速验证系统是否正常工作
运行前请先设置环境变量：
  $env:POLYGON_API_KEY = "你的key"
  $env:LLM_API_KEY = "你的key"
  $env:SENDER_EMAIL = "你的邮箱"
  $env:EMAIL_PASSWORD = "你的密码"
"""

import os
import sys

def check_environment():
    """检查环境变量是否设置"""
    print("=" * 50)
    print("🔍 检查环境变量...")
    print("=" * 50)

    required_vars = [
        "POLYGON_API_KEY",
        "LLM_API_KEY",
        "SENDER_EMAIL",
        "EMAIL_PASSWORD"
    ]

    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 隐藏部分内容
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: 未设置")
            all_set = False

    return all_set


def test_polygon_api():
    """测试 Polygon API 是否可用"""
    import requests

    print("\n" + "=" * 50)
    print("🔍 测试 Polygon API 连接...")
    print("=" * 50)

    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("❌ 跳过：POLYGON_API_KEY 未设置")
        return False

    try:
        # 测试获取 NVDA 数据
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/NVDA?apiKey={api_key}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                print("✅ Polygon API 连接成功！")
                ticker = data.get('ticker', {})
                print(f"   NVDA 当前价格: ${ticker.get('lastTrade', {}).get('p', 'N/A')}")
                return True
            else:
                print(f"❌ API 返回错误: {data.get('status')}")
                return False
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False


def test_openai_api():
    """测试 OpenAI API 是否可用"""
    from openai import OpenAI

    print("\n" + "=" * 50)
    print("🔍 测试 OpenAI API 连接...")
    print("=" * 50)

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("❌ 跳过：LLM_API_KEY 未设置")
        return False

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'API test successful' in 5 words or less."}],
            max_tokens=10
        )
        print("✅ OpenAI API 连接成功！")
        print(f"   模型响应: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False


def test_email_smtp():
    """测试 Gmail SMTP 连接"""
    import smtplib

    print("\n" + "=" * 50)
    print("🔍 测试 Gmail SMTP 连接...")
    print("=" * 50)

    sender_email = os.getenv("SENDER_EMAIL")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not email_password:
        print("❌ 跳过：邮箱配置不完整")
        return False

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
            server.login(sender_email, email_password)
        print("✅ Gmail SMTP 登录成功！")
        print(f"   发件人: {sender_email}")
        return True

    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        print("   提示: 请确保使用的是 Gmail 应用专用密码，而非登录密码")
        return False


def test_talib():
    """测试 TA-Lib 是否正确安装"""
    print("\n" + "=" * 50)
    print("🔍 测试 TA-Lib 库...")
    print("=" * 50)

    try:
        import talib
        import numpy as np

        # 测试 SMA 计算
        close_prices = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
        sma = talib.SMA(close_prices, timeperiod=5)

        print("✅ TA-Lib 工作正常！")
        print(f"   测试 SMA 计算: {sma[-1]:.2f}")
        return True

    except ImportError:
        print("❌ TA-Lib 未安装")
        print("   请运行: pip install TA-Lib")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def main():
    print("\n" + "🚀" * 25)
    print("美股自选股每日复盘系统 - 本地测试")
    print("🚀" * 25 + "\n")

    results = {
        "环境变量": check_environment(),
        "Polygon API": test_polygon_api(),
        "OpenAI API": test_openai_api(),
        "Gmail SMTP": test_email_smtp(),
        "TA-Lib": test_talib()
    }

    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)

    all_passed = True
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("\n🎉 所有测试通过！系统已准备就绪。")
        print("\n你现在可以:")
        print("1. 运行 'python main.py' 发送测试报告")
        print("2. 推送代码到 GitHub 让 Actions 自动运行")
    else:
        print("\n⚠️ 部分测试未通过，请检查上述错误信息。")
        print("\n常见问题:")
        print("- API Key 错误: 请检查是否正确复制")
        print("- Gmail 登录失败: 请使用应用专用密码")
        print("- TA-Lib 安装失败: 请参考 README.md 安装指南")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
