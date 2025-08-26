import os
from flask import Flask, request, render_template, redirect, url_for
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

app = Flask(__name__, static_folder="static", template_folder="templates")

def fetch_stock_data(ticker):
    """Fetch 3 months of stock data with fallback for rate limits."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="3mo")  # shorter period = lighter calls
        if df.empty:
            return None
        return df
    except Exception as e:
        print("Error fetching stock data:", e)
        return None

def calculate_indicators(df):
    """Simpler indicators: MACD + RSI only"""
    short_ema = df["Close"].ewm(span=12, adjust=False).mean()
    long_ema = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = short_ema - long_ema
    df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def generate_chart(df, ticker):
    """Closing Price + MACD chart"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close Price", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD", line=dict(color="green")))
    fig.add_trace(go.Scatter(x=df.index, y=df["Signal_Line"], mode="lines", name="Signal", line=dict(color="red")))

    fig.update_layout(title=f"{ticker} Price & MACD", template="plotly_dark")
    return fig.to_html(full_html=False)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search", methods=["POST"])
def search():
    ticker = request.form["ticker"].upper()
    return redirect(url_for("stock", ticker=ticker))

@app.route("/stock/<ticker>")
def stock(ticker):
    df = fetch_stock_data(ticker)
    if df is None:
        return render_template("stock.html", ticker=ticker, error="⚠ Could not fetch data. Try again later.")

    df = calculate_indicators(df)
    chart = generate_chart(df, ticker)

    # Simple recommendation
    recommendation = "⚠ HOLD Recommendation"
    if df["MACD"].iloc[-1] > df["Signal_Line"].iloc[-1] and df["RSI"].iloc[-1] < 70:
        recommendation = f"✅ BUY Recommendation: {ticker} is bullish."
    elif df["MACD"].iloc[-1] < df["Signal_Line"].iloc[-1] and df["RSI"].iloc[-1] > 30:
        recommendation = f"❌ SELL Recommendation: {ticker} is bearish."

    return render_template("stock.html", ticker=ticker, chart=chart, recommendation=recommendation)

if __name__ == "__main__":
    app.run(debug=True)
