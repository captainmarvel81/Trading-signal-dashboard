import streamlit as st
import yfinance as yf
import ta
import pandas as pd
import datetime
from telegram import Bot
from streamlit_autorefresh import st_autorefresh

# Telegram setup
TELEGRAM_TOKEN = st.secrets["telegram"]["token"]
CHAT_ID = st.secrets["telegram"]["chat_id"]
bot = Bot(token=TELEGRAM_TOKEN)

# Auto-refresh every 5 minutes (300000 ms)
st_autorefresh(interval=300000, key="refresh")

st.title("Live Trading Signal Dashboard")

symbols = st.multiselect("Select assets", ['EURUSD=X', 'BTC-USD', 'AAPL', 'XAUUSD=X'], default=['EURUSD=X'])

for symbol in symbols:
    st.subheader(f"Asset: {symbol}")
    try:
        df = yf.download(tickers=symbol, interval='5m', period='1d')
        df.dropna(inplace=True)

        df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['ma20'] = df['Close'].rolling(window=20).mean()

        latest = df.iloc[-1]
        signals = []

        if latest['rsi'] < 30:
            signals.append("RSI: Oversold (Buy)")
        elif latest['rsi'] > 70:
            signals.append("RSI: Overbought (Sell)")

        if latest['macd'] > latest['macd_signal']:
            signals.append("MACD: Bullish Crossover (Buy)")
        elif latest['macd'] < latest['macd_signal']:
            signals.append("MACD: Bearish Crossover (Sell)")

        if latest['Close'] > latest['ma20']:
            signals.append("Price above MA20 (Uptrend)")
        else:
            signals.append("Price below MA20 (Downtrend)")

        # Display signals and chart
        for sig in signals:
            st.write(f"- {sig}")
        st.line_chart(df[['Close', 'ma20']])

        # Telegram message
        message = f"{symbol} Signal @ {datetime.datetime.now().strftime('%H:%M:%S')}:
" + "\n".join(signals)
        bot.send_message(chat_id=CHAT_ID, text=message)

    except Exception as e:
        st.error(f"Error for {symbol}: {str(e)}")