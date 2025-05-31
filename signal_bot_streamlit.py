import streamlit as st
import requests
import numpy as np
import telegram
import os
import pandas as pd
import ta

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

ASSETS = {
    "EUR/USD": "EURUSD=X",
    "USD/JPY": "USDJPY=X",
    "GBP/USD": "GBPUSD=X",
    "GOLD": "XAUUSD=X",
    "S&P 500": "^GSPC",
}

def fetch_prices(symbol, interval="1m", limit=120):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range=1d"
    data = requests.get(url).json()
    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    closes = [c for c in closes if c is not None]
    return closes[-limit:]

def get_signals(prices):
    df = pd.DataFrame(prices, columns=['close'])
    signals = []

    # RSI
    df["rsi"] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    if df["rsi"].iloc[-1] < 30:
        signals.append("buy")
    elif df["rsi"].iloc[-1] > 70:
        signals.append("sell")
    else:
        signals.append("neutral")

    # MACD
    macd = ta.trend.MACD(df['close'])
    if macd.macd_diff().iloc[-1] > 0:
        signals.append("buy")
    elif macd.macd_diff().iloc[-1] < 0:
        signals.append("sell")
    else:
        signals.append("neutral")

    # SMA & EMA
    df["sma20"] = ta.trend.SMAIndicator(df["close"], 20).sma_indicator()
    df["ema20"] = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
    if df['close'].iloc[-1] > df["sma20"].iloc[-1] and df['close'].iloc[-1] > df["ema20"].iloc[-1]:
        signals.append("buy")
    elif df['close'].iloc[-1] < df["sma20"].iloc[-1] and df['close'].iloc[-1] < df["ema20"].iloc[-1]:
        signals.append("sell")
    else:
        signals.append("neutral")

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["close"], window=20)
    if df["close"].iloc[-1] < bb.bollinger_lband().iloc[-1]:
        signals.append("buy")
    elif df["close"].iloc[-1] > bb.bollinger_hband().iloc[-1]:
        signals.append("sell")
    else:
        signals.append("neutral")

    return signals

def summarize_signals(signals):
    buy = signals.count("buy")
    sell = signals.count("sell")
    total = buy + sell
    if total == 0:
        return "السوق متذبذب عُد لاحقاً"
    if buy/len(signals) > 0.7:
        return "شراء قوي"
    elif sell/len(signals) > 0.7:
        return "بيع قوي"
    else:
        return "السوق متذبذب عُد لاحقاً"

st.title("بوت إشارات تحليل صارم")
asset_name = st.selectbox("اختر الأصل الذي تريد تحليله:", list(ASSETS.keys()))
if st.button("Start / ابدأ التحليل"):
    symbol = ASSETS[asset_name]
    try:
        prices = fetch_prices(symbol)
        signals = get_signals(prices)
        summary = summarize_signals(signals)
        st.success(f"تحليل {asset_name}: {summary}")
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"تحليل {asset_name}: {summary}")
    except Exception as e:
        st.error("خطأ في جلب البيانات أو التحليل. حاول لاحقًا أو اختر أصل آخر.")
