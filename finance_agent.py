import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool
import requests
import pandas as pd
import yfinance as yf



@tool("get_ticker_sentiment", description="Get Stock News and its sentiment, you can also get up to 1000 news, can always get less too", return_direct=False)
def get_ticker_sentiment(company: str, news_num: int = 30):
    api_key = st.secrets["POLYGON_API_KEY"]
    header = {"Authorization": str(api_key)}
    params = {
        "ticker": company,
        "limit": news_num,
        "order": "desc"
    }
    get_news_url = 'https://api.polygon.io/v2/reference/news'
    response = requests.get(url=get_news_url, headers=header, params=params)

    news_response = response.json()
    news = news_response['results']
    news_dict = {}
    for idx, e in enumerate(news):
        news_dict[idx] = {}

        publisher = e['publisher']["name"]
        news_dict[idx]["publisher"] = publisher

        title = e["title"]
        news_dict[idx]["title"] = title

        time = e["published_utc"]
        news_dict[idx]["time"] = time

        article_url = e["article_url"]
        news_dict[idx]["article_url"] = article_url

        insights = e["insights"]

        for i in insights:
            if i["ticker"] == company:
                ticker = i["ticker"]
                news_dict[idx]["ticker"] = ticker

                sentiment = i["sentiment"]
                news_dict[idx]["sentiment"] = sentiment

                sentiment_reasoning = i["sentiment_reasoning"]
                news_dict[idx]["sentiment_reasoning"] = sentiment_reasoning

    positive = sum(1 for v in news_dict.values() if v.get("sentiment") == "positive")
    negative = sum(1 for v in news_dict.values() if v.get("sentiment") == "negative")
    neutral = sum(1 for v in news_dict.values() if v.get("sentiment") == "neutral")

    summary = f"Sentiment for {company}: {positive} positive, {negative} negative, {neutral} neutral out of {len(news_dict)} articles.\n\nRecent headlines:\n"
    for idx in list(news_dict.keys())[:10]:
        article = news_dict[idx]
        summary += f"- [{article.get('sentiment', 'N/A')}] {article.get('title', '')} ({article.get('time', '')})\n  Reason: {article.get('sentiment_reasoning', '')}\n"

    return summary


@tool("get_fear_greed_index", description="Get the CNN Fear and Greed Index with current value and recent trend.")
def get_fear_greed_index():
    from datetime import datetime, timedelta

    def get_label(score):
        score = float(score)
        if score <= 25: return "Extreme Fear"
        elif score <= 45: return "Fear"
        elif score <= 55: return "Neutral"
        elif score <= 75: return "Greed"
        else: return "Extreme Greed"

    csv_path = "./cnn_fear_and_greed_index.csv"
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False)

    latest_date = df.iloc[0]["date"].date()
    today = datetime.now().date()

    if (today - latest_date) > timedelta(days=1):
        try:
            r = requests.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata")
            data = r.json()
            score = data["fear_and_greed"]["score"]

            new_row = pd.DataFrame([{"date": today, "combined_value": round(score)}])
            df = pd.concat([new_row, df], ignore_index=True)
            df.to_csv(csv_path, index=False)
        except:
            pass

    latest = df.iloc[0]
    week_ago = df.iloc[5] if len(df) > 5 else df.iloc[-1]
    month_ago = df.iloc[22] if len(df) > 22 else df.iloc[-1]

    return (
        f"Fear & Greed Index as of {latest['date']}:\n"
        f"Current: {latest['combined_value']} ({get_label(latest['combined_value'])})\n"
        f"5 days ago: {week_ago['combined_value']} ({get_label(week_ago['combined_value'])})\n"
        f"~1 month ago: {month_ago['combined_value']} ({get_label(month_ago['combined_value'])})\n"
        f"Trend: {'Improving' if float(latest['combined_value']) > float(week_ago['combined_value']) else 'Declining'}"
    )

@tool("get_short_interest", description="Get short interest data for a stock ticker from NASDAQ. Returns current short interest, days to cover, and recent trend.")
def get_short_interest(ticker: str):
    import requests
    import pandas as pd

    url = f"https://api.nasdaq.com/api/quote/{ticker}/short-interest?assetclass=stocks"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        js = resp.json()
        rows = js["data"]["shortInterestTable"]["rows"]
    except Exception as e:
        return f"Failed to fetch short interest for {ticker}: {e}"

    if not rows:
        return f"No short interest data found for {ticker}."

    df = pd.DataFrame(rows)
    df['interest'] = df['interest'].str.replace(',', '').astype(int)
    df['avgDailyShareVolume'] = df['avgDailyShareVolume'].str.replace(',', '').astype(int)
    df['daysToCover'] = df['daysToCover'].astype(float)
    df['settlementDate'] = pd.to_datetime(df['settlementDate'], format='%m/%d/%Y')
    df = df.sort_values('settlementDate', ascending=False)

    latest = df.iloc[0]
    prev = df.iloc[1] if len(df) > 1 else None

    change_str = ""
    if prev is not None:
        change = latest['interest'] - prev['interest']
        pct = (change / prev['interest']) * 100 if prev['interest'] > 0 else 0
        direction = "up" if change > 0 else "down"
        change_str = f"Change from prior: {direction} {abs(change):,} shares ({abs(pct):.1f}%)"

    return (
        f"Short Interest for {ticker} as of {latest['settlementDate'].strftime('%Y-%m-%d')}:\n"
        f"Short Interest: {latest['interest']:,} shares\n"
        f"Avg Daily Volume: {latest['avgDailyShareVolume']:,}\n"
        f"Days to Cover: {latest['daysToCover']}\n"
        f"{change_str}"
    )

@tool("get_stock_price", description="Get current and recent stock price data for a ticker. Returns current price, daily change, and key stats.")
def get_stock_price(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")
    except Exception as e:
        return f"Failed to fetch price data for {ticker}: {e}"

    if hist.empty:
        return f"No price data found for {ticker}."

    current = hist.iloc[-1]
    prev = hist.iloc[-2] if len(hist) > 1 else None

    change_str = ""
    if prev is not None:
        change = current['Close'] - prev['Close']
        pct = (change / prev['Close']) * 100
        direction = "+" if change > 0 else ""
        change_str = f"Daily Change: {direction}{change:.2f} ({direction}{pct:.2f}%)"

    return (
        f"Price data for {ticker}:\n"
        f"Current Price: ${current['Close']:.2f}\n"
        f"Day High: ${current['High']:.2f}\n"
        f"Day Low: ${current['Low']:.2f}\n"
        f"Volume: {int(current['Volume']):,}\n"
        f"{change_str}\n"
        f"Market Cap: {info.get('marketCap', 'N/A'):,}\n"
        f"52-Week High: ${info.get('fiftyTwoWeekHigh', 0):.2f}\n"
        f"52-Week Low: ${info.get('fiftyTwoWeekLow', 0):.2f}\n"
        f"P/E Ratio: {info.get('trailingPE', 'N/A')}"
    )


## BUILD AGENT
@st.cache_resource
def build_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=st.secrets["GEMINI_API_KEY"]
    )
    return create_agent(
        model=llm,
        tools=[get_ticker_sentiment, get_fear_greed_index, get_short_interest, get_stock_price],
        system_prompt="""You are a senior investment research analyst. Your job is to answer financial questions using the tools available to you.

Rules:
- Always use tools to get real data before forming an opinion. Never guess.
- When analysing sentiment, report the sentiment score AND the reasoning behind it.
- If a tool returns no data, say so clearly. Do not fabricate results.
- Keep answers concise and data-driven. No filler.
- When multiple articles exist, summarise the overall trend, not every article.""",)

st.title("📈 Investment Research Agent")
st.caption("Powered by LangChain, Gemini, Polygon, CNN Fear & Greed, NASDAQ, yfinance")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me about any stock..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            agent = build_agent()
            response = agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
            reply = response["messages"][-1].content
            if isinstance(reply, list):
                reply = reply[0]["text"] if reply else ""
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
