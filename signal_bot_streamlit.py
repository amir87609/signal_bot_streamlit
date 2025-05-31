import streamlit as st
import requests
import talib
import numpy as np
import telegram
import os

# إعداد تيليجرام من متغيرات البيئة (أفضل للأمان)
TELEGRAM_TOKEN = os.getenv("8112822168:AAFlMU3El0ysMPssjztTZybp_f7wlRrWk2I")
TELEGRAM_CHAT_ID = os.getenv("6083602720")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# قائمة الأصول الجاهزة
ASSETS = {
    "EUR/USD": "EURUSD=X",
    "USD/JPY": "USDJPY=X",
    "GBP/USD": "GBPUSD=X",
    "GOLD": "XAUUSD=X",
    "S&P 500": "^GSPC",
    # أضف أصول أخرى هنا
}

def fetch_prices(symbol, interval="1m", limit=120):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range=1d"
    data = requests.get(url).json()
    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    closes = [c for c in closes if c is not None]
    return closes[-limit:]

def get_signals(prices):
    p = np.array(prices)
    signals = []

    # بعض المؤشرات القوية
    rsi = talib.RSI(p, timeperiod=14)
    macd, macdsignal, _ = talib.MACD(p, fastperiod=12, slowperiod=26, signalperiod=9)
    sma = talib.SMA(p, timeperiod=20)
    ema = talib.EMA(p, timeperiod=20)
    upper, middle, lower = talib.BBANDS(p, timeperiod=20)
    slowk, slowd = talib.STOCH(p, p, p, fastk_period=14, slowk_period=3, slowd_period=3)

    if rsi[-1] < 30: signals.append("buy")
    elif rsi[-1] > 70: signals.append("sell")
    else: signals.append("neutral")

    if macd[-1] > macdsignal[-1]: signals.append("buy")
    elif macd[-1] < macdsignal[-1]: signals.append("sell")
    else: signals.append("neutral")

    if p[-1] > sma[-1] and p[-1] > ema[-1]: signals.append("buy")
    elif p[-1] < sma[-1] and p[-1] < ema[-1]: signals.append("sell")
    else: signals.append("neutral")

    if p[-1] < lower[-1]: signals.append("buy")
    elif p[-1] > upper[-1]: signals.append("sell")
    else: signals.append("neutral")

    if slowk[-1] < 20 and slowd[-1] < 20: signals.append("buy")
    elif slowk[-1] > 80 and slowd[-1] > 80: signals.append("sell")
    else: signals.append("neutral")

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
