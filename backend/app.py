import os
import requests
from flask import Flask, request, render_template
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Initialize Flask App
app = Flask(__name__, static_folder="static", template_folder="templates")

# Ensure the static directory exists
if not os.path.exists("static"):
    os.makedirs("static")


def fetch_stock_data(ticker):
    """Fetch stock data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")  # Fetch 6 months of data

        if df.empty:
            return None, None
        return df, stock
    except Exception as e:
        print("Error fetching stock data:", e)
        return None, None


def calculate_indicators(df):
    """Calculate MACD, RSI, OBV, and Ichimoku Cloud indicators."""

    # MACD Calculation
    short_ema = df["Close"].ewm(span=12, adjust=False).mean()
    long_ema = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = short_ema - long_ema
    df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # RSI Calculation
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # OBV Calculation
    df["Volume_Change"] = df["Volume"] * (df["Close"].diff().apply(lambda x: 1 if x > 0 else -1))
    df["OBV"] = df["Volume_Change"].cumsum()

    # Ichimoku Cloud
    df["Tenkan_Sen"] = df["High"].rolling(9).mean()
    df["Kijun_Sen"] = df["High"].rolling(26).mean()
    df["Senkou A"] = ((df["Tenkan_Sen"] + df["Kijun_Sen"]) / 2).shift(26)
    df["Senkou B"] = df["High"].rolling(52).mean().shift(26)

    return df


def generate_charts(ticker):
    """Generate interactive charts for different indicators with descriptions."""
    df, stock = fetch_stock_data(ticker)
    if df is None or stock is None:
        return None, None, None, None, None, None, None, None, None

    df = calculate_indicators(df)

    ## 1️⃣ Closing Price with Buy/Sell Signals
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Closing Price", line=dict(color="blue")))

    price_signal = "hold"
    if df["MACD"].iloc[-1] > df["Signal_Line"].iloc[-1]:
        price_signal = "buy"
    elif df["MACD"].iloc[-1] < df["Signal_Line"].iloc[-1]:
        price_signal = "sell"

    fig_price.update_layout(title=f"{ticker} Price & Buy/Sell Signals", template="plotly_dark")
    price_chart = fig_price.to_html(full_html=False)

    ## 2️⃣ MACD & Signal Line
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD", line=dict(color="green")))
    fig_macd.add_trace(go.Scatter(x=df.index, y=df["Signal_Line"], mode="lines", name="Signal Line", line=dict(color="red")))

    macd_signal = "hold"
    if df["MACD"].iloc[-1] > df["Signal_Line"].iloc[-1]:
        macd_signal = "buy"
    elif df["MACD"].iloc[-1] < df["Signal_Line"].iloc[-1]:
        macd_signal = "sell"

    fig_macd.update_layout(title=f"{ticker} MACD & Signal Line", template="plotly_dark")
    macd_chart = fig_macd.to_html(full_html=False)

    ## 3️⃣ Ichimoku Cloud
    fig_ichimoku = go.Figure()
    fig_ichimoku.add_trace(go.Scatter(x=df.index, y=df["Tenkan_Sen"], mode="lines", name="Tenkan-Sen", line=dict(color="blue")))
    fig_ichimoku.add_trace(go.Scatter(x=df.index, y=df["Kijun_Sen"], mode="lines", name="Kijun-Sen", line=dict(color="red")))
    fig_ichimoku.add_trace(go.Scatter(x=df.index, y=df["Senkou A"], mode="lines", name="Senkou A", line=dict(color="lightblue")))
    fig_ichimoku.add_trace(go.Scatter(x=df.index, y=df["Senkou B"], mode="lines", name="Senkou B", line=dict(color="pink")))
    fig_ichimoku.add_trace(go.Scatter(x=df.index, y=df["Close"].shift(-26), mode="lines", name="Chikou Span", line=dict(color="green")))

    ichimoku_signal = "hold"
    if df["Tenkan_Sen"].iloc[-1] > df["Kijun_Sen"].iloc[-1]:
        ichimoku_signal = "buy"
    elif df["Tenkan_Sen"].iloc[-1] < df["Kijun_Sen"].iloc[-1]:
        ichimoku_signal = "sell"

    fig_ichimoku.update_layout(title=f"{ticker} Ichimoku Cloud", template="plotly_dark")
    ichimoku_chart = fig_ichimoku.to_html(full_html=False)

    ## 4️⃣ OBV
    fig_obv = go.Figure()
    fig_obv.add_trace(go.Scatter(x=df.index, y=df["OBV"], mode="lines", name="OBV", line=dict(color="orange")))

    obv_signal = "hold"
    if df["OBV"].iloc[-1] > df["OBV"].iloc[-2]:
        obv_signal = "buy"
    elif df["OBV"].iloc[-1] < df["OBV"].iloc[-2]:
        obv_signal = "sell"

    fig_obv.update_layout(title=f"{ticker} On-Balance Volume", template="plotly_dark")
    obv_chart = fig_obv.to_html(full_html=False)

    ## Generate Buy/Sell Recommendation
    latest_macd = df["MACD"].iloc[-1]
    latest_signal = df["Signal_Line"].iloc[-1]
    latest_rsi = df["RSI"].iloc[-1]

    if latest_macd > latest_signal and latest_rsi < 70:
        recommendation = f"✅ **BUY Recommendation:** {ticker} is showing bullish momentum. MACD is above the signal line, and RSI is below overbought levels."
    elif latest_macd < latest_signal and latest_rsi > 30:
        recommendation = f"❌ **SELL Recommendation:** {ticker} is showing bearish momentum. MACD is below the signal line, indicating a downtrend."
    else:
        recommendation = f"⚠ **HOLD Recommendation:** {ticker} is in a neutral zone. Consider waiting for stronger buy/sell signals."

    # Return the charts and signals
    return price_chart, macd_chart, ichimoku_chart, obv_chart, recommendation, price_signal, macd_signal, ichimoku_signal, obv_signal


def fetch_news():
    url = "https://gnews.io/api/v4/search"
    params = {
        "q": "stock",  # You can modify the query to search for specific topics
        "lang": "en",  # Language of the news
        "country": "us",  # Country for the news (you can change this to any supported country)
        "max": 10,  # Number of articles to fetch
        "apikey": "161d577d64c08c9c78396e820b30f83f"  # Your API key
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()["articles"]  # Returning articles from the response
    else:
        print("Failed to fetch news:", response.status_code)
        return []  # Return an empty list if there's an error


@app.route("/")
def home():
    news_data = fetch_news()  # Fetch news data here
    return render_template("index.html", news_data=news_data)


@app.route("/search", methods=["POST"])
def search():
    ticker = request.form["ticker"].upper()
    return stock(ticker)


@app.route("/stock/<ticker>")
def stock(ticker):
    price_chart, macd_chart, ichimoku_chart, obv_chart, recommendation, price_signal, macd_signal, ichimoku_signal, obv_signal = generate_charts(ticker)

    # Pass the signals and charts to the template
    return render_template("stock.html", ticker=ticker,
                           price_chart=price_chart,
                           macd_chart=macd_chart,
                           ichimoku_chart=ichimoku_chart,
                           obv_chart=obv_chart,
                           price_signal=price_signal,
                           macd_signal=macd_signal,
                           ichimoku_signal=ichimoku_signal,
                           obv_signal=obv_signal,
                           recommendation=recommendation)


if __name__ == "__main__":
    app.run(debug=True)
