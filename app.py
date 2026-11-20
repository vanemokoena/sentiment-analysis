"""Airline Sentiment Dashboard
Explore what travellers said about US airlines on Twitter (Feb 2015).
Built with Streamlit, Plotly, pandas and WordCloud.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

# ---------------------------------------------------------------- page setup
st.set_page_config(
    page_title="Airline Sentiment Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = "Tweets.csv"
SENTIMENTS = ["positive", "neutral", "negative"]
COLORS = {"positive": "#2fb67c", "neutral": "#9aa5b8", "negative": "#e5484d"}

st.markdown(
    """
    <style>
      .block-container {padding-top: 4.5rem; padding-bottom: 3rem; max-width: 1280px;}
      footer, #MainMenu {visibility: hidden;}
      .masthead {
        border-left: 6px solid #f5a524; padding: .2rem 0 .2rem 1rem; margin-bottom: 1.2rem;
      }
      .masthead .title {font-size: 2rem; font-weight: 700; line-height: 1.35; margin: 0; padding-top: .15rem;}
      .masthead .sub {opacity: .75; margin: .35rem 0 0 0; font-size: 1rem; max-width: 60rem;}
      [data-testid="stMetric"] {
        background: rgba(128,138,158,.10); border: 1px solid rgba(128,138,158,.25);
        border-radius: 12px; padding: .8rem 1rem;
      }
      [data-testid="stMetricLabel"] {opacity: .8;}
      [data-testid="stMetricValue"] {font-size: 2rem;}
      [data-testid="stMetricValue"] > div {white-space: normal; overflow: visible; text-overflow: clip; line-height: 1.2;}
      .quote {
        border-left: 4px solid #4f8cff; padding: .6rem 1rem; border-radius: 0 10px 10px 0;
        background: rgba(79,140,255,.08); font-size: 1.02rem;
      }
      .stTabs [data-baseweb="tab"] {font-weight: 600;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- data layer
@st.cache_data(show_spinner="Loading tweets…")
def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["tweet_created"] = pd.to_datetime(
        df["tweet_created"], utc=True, errors="coerce"
    ).dt.tz_localize(None)
    df = df.dropna(subset=["tweet_created"]).copy()
    df["date"] = df["tweet_created"].dt.date
    df["hour"] = df["tweet_created"].dt.hour
    df["negativereason"] = df["negativereason"].fillna("")

    # tweet_coord looks like "[40.7, -74.0]"; turn it into two numeric columns
    if "latitude" not in df.columns and "tweet_coord" in df.columns:
        coords = df["tweet_coord"].astype(str).str.extract(
            r"\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]"
        )
        df["latitude"] = pd.to_numeric(coords[0], errors="coerce")
        df["longitude"] = pd.to_numeric(coords[1], errors="coerce")
        df.loc[(df["latitude"] == 0) & (df["longitude"] == 0), ["latitude", "longitude"]] = None
    return df


try:
    data = load_data()
except FileNotFoundError:
    st.error("Tweets.csv was not found. Put it in the same folder as app.py and reload.")
    st.stop()

# ---------------------------------------------------------------- sidebar
FILTER_KEYS = ["f_airlines", "f_sentiments", "f_dates", "f_hours", "f_conf", "f_search"]


def reset_filters():
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


all_airlines = sorted(data["airline"].dropna().unique())
min_date, max_date = data["date"].min(), data["date"].max()

with st.sidebar:
    st.header("Filters")
    st.caption("Every chart, number and table on the page follows these filters.")

    airlines = st.multiselect("Airlines", all_airlines, default=all_airlines, key="f_airlines")
    sentiments = st.multiselect("Sentiment", SENTIMENTS, default=SENTIMENTS, key="f_sentiments")
    date_range = st.date_input(
        "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date, key="f_dates"
    )
    hours = st.slider("Hour of day (UTC)", 0, 23, (0, 23), key="f_hours")
    min_conf = st.slider(
        "Minimum label confidence", 0.0, 1.0, 0.0, 0.05, key="f_conf",
        help="How sure the labellers were about the sentiment. Raise it to keep only clear-cut tweets.",
    )
    search = st.text_input("Search tweet text", placeholder="e.g. delay, luggage, thanks", key="f_search")
    st.button("Reset filters", on_click=reset_filters)

# ---------------------------------------------------------------- apply filters
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = date_range
else:  # the user is still picking the second date
    start = end = date_range[0] if isinstance(date_range, (tuple, list)) and date_range else min_date

mask = (
    data["airline"].isin(airlines)
    & data["airline_sentiment"].isin(sentiments)
    & (data["date"] >= start)
    & (data["date"] <= end)
    & data["hour"].between(hours[0], hours[1])
    & (data["airline_sentiment_confidence"] >= min_conf)
)
if search.strip():
    mask &= data["text"].str.contains(search.strip(), case=False, na=False, regex=False)
df = data[mask]

with st.sidebar:
    st.divider()
    st.metric("Tweets matching", f"{len(df):,}", help=f"Out of {len(data):,} in the dataset")
    st.progress(len(df) / len(data) if len(data) else 0.0)

# ---------------------------------------------------------------- header
st.markdown(
    """
    <div class="masthead">
      <p class="title">✈️ What travellers said about US airlines</p>
      <p class="sub">Browse about 14,600 tweets from February 2015, labelled positive, neutral or negative.
      Narrow them down in the sidebar to compare airlines, spot busy hours and read what people complained about.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No tweets match these filters. Widen the date range, add more airlines or sentiments, or clear the search box.")
    st.stop()

# ---------------------------------------------------------------- headline numbers
total = len(df)
pct = lambda s: (df["airline_sentiment"] == s).mean() * 100
neg_reasons = df.loc[df["negativereason"] != "", "negativereason"]
top_reason = neg_reasons.value_counts().idxmax() if not neg_reasons.empty else "None"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Tweets", f"{total:,}")
c2.metric("Positive", f"{pct('positive'):.1f}%")
c3.metric("Negative", f"{pct('negative'):.1f}%")
c4.metric("Top complaint", top_reason)

st.write("")


def tidy(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=40, b=10), legend_title_text="")
    return fig


tab_overview, tab_trends, tab_complaints, tab_words, tab_explore = st.tabs(
    ["Overview", "Trends", "Complaints", "Word cloud", "Explore tweets"]
)

# ---------------------------------------------------------------- overview
with tab_overview:
    left, right = st.columns([1, 1.6])

    with left:
        with st.container(border=True):
            st.subheader("Overall mood")
            st.caption("Share of tweets by sentiment for the current filters.")
            mix = df["airline_sentiment"].value_counts().reindex(SENTIMENTS).dropna().reset_index()
            mix.columns = ["Sentiment", "Tweets"]
            fig = px.pie(mix, values="Tweets", names="Sentiment", hole=0.55,
                         color="Sentiment", color_discrete_map=COLORS)
            fig.update_traces(textinfo="percent", sort=False)
            st.plotly_chart(tidy(fig, 360))

    with right:
        with st.container(border=True):
            st.subheader("Sentiment by airline")
            st.caption("Airlines are sorted from most to least negative.")
            view = st.radio("Show", ["Percent", "Tweet count"], horizontal=True, label_visibility="collapsed")
            counts = df.groupby(["airline", "airline_sentiment"]).size().reset_index(name="Tweets")
            share = counts.assign(Percent=counts["Tweets"] / counts.groupby("airline")["Tweets"].transform("sum") * 100)
            neg_order = (
                share[share["airline_sentiment"] == "negative"].sort_values("Percent", ascending=False)["airline"].tolist()
            )
            order = neg_order + [a for a in share["airline"].unique() if a not in neg_order]
            fig = px.bar(
                share, x="airline", y="Percent" if view == "Percent" else "Tweets",
                color="airline_sentiment", color_discrete_map=COLORS,
                category_orders={"airline": order, "airline_sentiment": SENTIMENTS},
                labels={"airline": "", "airline_sentiment": "Sentiment"},
            )
            if view == "Percent":
                fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(tidy(fig, 360))

# ---------------------------------------------------------------- trends
with tab_trends:
    with st.container(border=True):
        st.subheader("Tweets per day")
        st.caption("How the volume of each sentiment moved across the dates you selected.")
        daily = df.groupby(["date", "airline_sentiment"]).size().reset_index(name="Tweets")
        fig = px.line(daily, x="date", y="Tweets", color="airline_sentiment", markers=True,
                      color_discrete_map=COLORS, labels={"date": "", "airline_sentiment": "Sentiment"})
        st.plotly_chart(tidy(fig))

    with st.container(border=True):
        st.subheader("Busiest hours")
        st.caption("When people tweeted, by hour of day (UTC).")
        hourly = df.groupby(["hour", "airline_sentiment"]).size().reset_index(name="Tweets")
        fig = px.bar(hourly, x="hour", y="Tweets", color="airline_sentiment", color_discrete_map=COLORS,
                     category_orders={"airline_sentiment": SENTIMENTS},
                     labels={"hour": "Hour of day", "airline_sentiment": "Sentiment"})
        fig.update_xaxes(dtick=2)
        st.plotly_chart(tidy(fig))

# ---------------------------------------------------------------- complaints
with tab_complaints:
    neg = df[df["negativereason"] != ""]
    if neg.empty:
        st.info("There are no negative tweets with a stated reason under these filters. Include 'negative' in the Sentiment filter to see complaints.")
    else:
        with st.container(border=True):
            st.subheader("Why people were unhappy")
            st.caption("Reasons given in negative tweets, most common first.")
            reasons = neg["negativereason"].value_counts().reset_index()
            reasons.columns = ["Reason", "Tweets"]
            fig = px.bar(reasons.sort_values("Tweets"), x="Tweets", y="Reason", orientation="h",
                         color_discrete_sequence=[COLORS["negative"]])
            fig.update_layout(yaxis_title="")
            st.plotly_chart(tidy(fig, 420))

        with st.container(border=True):
            st.subheader("Which airline gets which complaint")
            st.caption("Darker squares mean more complaints of that type.")
            grid = neg.groupby(["negativereason", "airline"]).size().unstack(fill_value=0)
            fig = px.imshow(grid, aspect="auto", color_continuous_scale="Reds",
                            labels=dict(x="", y="", color="Tweets"), text_auto=True)
            st.plotly_chart(tidy(fig, 460))

# ---------------------------------------------------------------- word cloud
EXTRA_STOP = {
    "flight", "flights", "amp", "co", "rt", "get", "got", "u", "will", "now", "still",
    "americanair", "united", "usairways", "southwestair", "delta", "jetblue", "virginamerica",
}


@st.cache_data(show_spinner="Drawing word cloud…")
def make_cloud(text: str):
    return WordCloud(
        stopwords=STOPWORDS | EXTRA_STOP, background_color=None, mode="RGBA",
        width=1000, height=480, colormap="viridis", max_words=150,
    ).generate(text)


with tab_words:
    with st.container(border=True):
        st.subheader("Most used words")
        st.caption("Bigger words appear more often. Links, @mentions and common filler words are removed.")
        pick = st.radio("Sentiment", SENTIMENTS, horizontal=True, index=2)
        subset = df.loc[df["airline_sentiment"] == pick, "text"].dropna()
        words = " ".join(
            w for t in subset for w in t.split()
            if "http" not in w and not w.startswith("@") and w != "RT"
        )
        if not words.strip():
            st.info(f"No {pick} tweets under these filters.")
        else:
            fig, ax = plt.subplots(figsize=(10, 4.8))
            fig.patch.set_alpha(0)
            ax.imshow(make_cloud(words), interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
            plt.close(fig)

# ---------------------------------------------------------------- explore
with tab_explore:
    with st.container(border=True):
        st.subheader("Read a random tweet")
        st.caption("Pulls one tweet from the filtered set so you can see what the numbers look like.")
        if st.button("Show another"):
            pass  # a button click reruns the script, which draws a new sample below
        row = df.sample(1).iloc[0]
        st.markdown(
            f"<div class='quote'>“{row['text']}”<br><small>{row['airline']} · {row['airline_sentiment']}</small></div>",
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.subheader("All matching tweets")
        st.caption(f"{total:,} tweets. Click a column header to sort.")
        table = df[["tweet_created", "airline", "airline_sentiment", "airline_sentiment_confidence",
                    "negativereason", "retweet_count", "text"]].sort_values("tweet_created", ascending=False)
        st.dataframe(
            table, hide_index=True,
            column_config={
                "tweet_created": st.column_config.DatetimeColumn("Posted", format="D MMM, HH:mm"),
                "airline": "Airline",
                "airline_sentiment": "Sentiment",
                "airline_sentiment_confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.2f"),
                "negativereason": "Complaint",
                "retweet_count": "Retweets",
                "text": st.column_config.TextColumn("Tweet", width="large"),
            },
        )
        st.download_button("Download these tweets (CSV)", table.to_csv(index=False).encode("utf-8"),
                           file_name="filtered_tweets.csv", mime="text/csv")

    geo = df.dropna(subset=["latitude", "longitude"]) if {"latitude", "longitude"} <= set(df.columns) else pd.DataFrame()
    with st.expander(f"Map of tweets with a location ({len(geo):,})"):
        if geo.empty:
            st.info("None of the matching tweets include coordinates.")
        else:
            st.caption("Green is positive, grey is neutral and red is negative.")
            st.map(geo.assign(color=geo["airline_sentiment"].map(COLORS)),
                   latitude="latitude", longitude="longitude", color="color", size=40)

st.divider()
st.caption("Data: Twitter US Airline Sentiment (Crowdflower / Kaggle) · Built by Vanessa Mokoena with Streamlit")
