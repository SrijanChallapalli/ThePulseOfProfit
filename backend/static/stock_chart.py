import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd


def fetch_stock_data(ticker):
    """Fetch historical stock data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="30d")  # Get last 30 days of data

        if df.empty:
            print("⚠️ No data found for", ticker)
            return None

        return df, stock
    except Exception as e:
        print("❌ Error fetching stock data:", e)
        return None, None


def calculate_indicators(df):
    """Calculate RSI, MACD, and Bollinger Bands."""
    # RSI Calculation
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD Calculation
    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands Calculation
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    df["Upper Band"] = df["SMA20"] + (df["Close"].rolling(window=20).std() * 2)
    df["Lower Band"] = df["SMA20"] - (df["Close"].rolling(window=20).std() * 2)

    return df


def plot_stock_chart(ticker):
    """Fetch stock data, calculate indicators, and generate a price chart."""
    data, stock = fetch_stock_data(ticker)

    if data is None or stock is None:
        return

    data = calculate_indicators(data)

    fig, axs = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})

    # Plot Closing Price
    axs[0].plot(data.index, data["Close"], label=f"{ticker} Closing Price", color="blue")
    axs[0].fill_between(data.index, data["Lower Band"], data["Upper Band"], color='gray', alpha=0.3,
                        label="Bollinger Bands")
    axs[0].set_title(f"{ticker} Stock Price & Bollinger Bands")
    axs[0].set_ylabel("Price (USD)")
    axs[0].legend()
    axs[0].grid()

    # Plot MACD Indicator
    axs[1].plot(data.index, data["MACD"], label="MACD", color="red")
    axs[1].plot(data.index, data["Signal"], label="Signal Line", color="green")
    axs[1].set_title("MACD Indicator")
    axs[1].legend()
    axs[1].grid()

    # Save the chart
    plt.tight_layout()
    plt.savefig("stock_chart.png")
    print("📊 Chart saved as stock_chart.png")

    # Fetch & Save Stock Info (Latest Price, Volume)
    latest_price = data["Close"].iloc[-1]
    latest_volume = data["Volume"].iloc[-1]

    with open("stock_data.txt", "w") as file:
        file.write(f"📌 {ticker} Stock Data\n")
        file.write(f"💰 Latest Price: ${latest_price:.2f}\n")
        file.write(f"📊 Volume: {latest_volume:,}\n")

    print("✅ Stock data saved to stock_data.txt")


# Example Usage (Replace with user input)
plot_stock_chart("AAPL")  # Change ticker symbol as needed
