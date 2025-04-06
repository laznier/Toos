import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Replace with your actual FMP API key or use Streamlit secrets for deployment
API_KEY = st.secrets["FMP_API_KEY"] if "FMP_API_KEY" in st.secrets else "YOUR_FMP_API_KEY"

# Normalize helper
def normalize(x, min_val, max_val):
    return max(0, min(100, 100 * (x - min_val) / (max_val - min_val)))

# Fetch sentiment data
def fetch_sentiment(ticker):
    url = f"https://financialmodelingprep.com/api/v4/social-sentiment/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Score calculator
def calculate_score(data_point):
    pos = data_point.get("positiveMentions", 0)
    neg = data_point.get("negativeMentions", 0)
    total = max(1, pos + neg)
    bullish = data_point.get("bullishPercent", 0) / 100
    bearish = data_point.get("bearishPercent", 0) / 100
    change = data_point.get("mentionChangePercent", 0)

    pos_ratio = pos / total
    bull_bear_diff = bullish - bearish
    pos_neg_ratio = pos / (neg + 1e-5)

    score = (
        0.4 * normalize(pos_ratio, 0, 1) +
        0.3 * normalize(bull_bear_diff, -1, 1) +
        0.2 * normalize(change, -100, 100) +
        0.1 * normalize(pos_neg_ratio, 0, 10)
    )
    return round(score, 2)

# UI
st.title("Stock Social Sentiment Dashboard")
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", value="AAPL")

if st.button("Analyze Sentiment"):
    data = fetch_sentiment(ticker.upper())

    if data:
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df = df.sort_values(by='date')
        df['sentiment_score'] = df.apply(calculate_score, axis=1)

        latest_score = df['sentiment_score'].iloc[-1]
        st.metric(label=f"{ticker.upper()} Sentiment Score", value=f"{latest_score}/100")

        # Plotting
        fig, ax = plt.subplots()
        ax.plot(df['date'], df['sentiment_score'], marker='o')
        ax.set_title(f"{ticker.upper()} Sentiment Score Over Time")
        ax.set_ylabel("Sentiment Score (0–100)")
        ax.set_xlabel("Date")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Raw data
        with st.expander("Show raw data"):
            st.dataframe(df[[
                'date', 'positiveMentions', 'negativeMentions',
                'bullishPercent', 'bearishPercent', 'mentionChangePercent',
                'sentiment_score'
            ]])
    else:
        st.error("No sentiment data found or API error.")
