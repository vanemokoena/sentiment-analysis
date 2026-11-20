import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt

### Adding a Title and Sidebar:
st.title("Sentimental Analysis of Tweets about US Airlines")
st.sidebar.title("Sentimental Analysis of Tweets about US Airlines")

### Adding Description in main page and sidebar:
st.markdown(" This application is a Streamlit dashboard to analyze the sentiments of tweets. 🐦")
st.sidebar.markdown(" This application is a Streamlit dashboard to analyze the sentiments of tweets. 🐦")

### Loading the data:
DATA_URL = "Tweets.csv"


@st.cache_data(persist="disk")
def load_data():
    data = pd.read_csv(DATA_URL)
    data['tweet_created'] = pd.to_datetime(data['tweet_created'])

    # st.map needs 'latitude' and 'longitude' columns. If the CSV only has
    # 'tweet_coord' (e.g. "[40.7, -73.9]"), split it into two columns.
    if 'latitude' not in data.columns and 'tweet_coord' in data.columns:
        coords = (data['tweet_coord'].astype(str)
                  .str.extract(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]'))
        data['latitude'] = pd.to_numeric(coords[0], errors='coerce')
        data['longitude'] = pd.to_numeric(coords[1], errors='coerce')
    return data


data = load_data()

st.sidebar.subheader("Show random tweet")
random_tweet = st.sidebar.radio('Sentiment:', ('positive', 'neutral', 'negative'))
st.sidebar.markdown(data.query('airline_sentiment == @random_tweet')[["text"]].sample(n=1).iat[0, 0])

### Data Visualization:
### Showing the number of Tweets by Sentiment using a Histogram or Pie Chart based on user's preference:
st.sidebar.markdown("### Number of Tweets by Sentiment")
select = st.sidebar.selectbox('Visualization type', ['Histogram', 'Pie Chart'], key='viz_type')
sentiment_count = data['airline_sentiment'].value_counts()
sentiment_count = pd.DataFrame({'Sentiment': sentiment_count.index, 'Tweets': sentiment_count.values})
if not st.sidebar.checkbox("Hide", True, key='hide_sentiment'):
    st.markdown("### Number of tweets by Sentiment")
    if select == "Histogram":
        fig = px.bar(sentiment_count, x='Sentiment', y='Tweets', color='Tweets', height=500)
        st.plotly_chart(fig)
    else:
        fig = px.pie(sentiment_count, values='Tweets', names='Sentiment')
        st.plotly_chart(fig)

### Showing the when and where these tweets were made from:
st.sidebar.subheader("When and Where are the Users tweeting from?")
hour = st.sidebar.slider("Hour of day", 0, 23)
modified_data = data[data['tweet_created'].dt.hour == hour]
if not st.sidebar.checkbox("Close", True, key='close_map'):
    st.markdown("### Tweets locations based on the time of day")
    st.markdown("%i tweets between %i:00 and %i:00" % (len(modified_data), hour, (hour + 1) % 24))
    if {'latitude', 'longitude'}.issubset(modified_data.columns):
        map_data = modified_data.dropna(subset=['latitude', 'longitude'])
        if len(map_data) > 0:
            st.map(map_data[['latitude', 'longitude']])
        else:
            st.info("No tweets with location data in this hour.")
    else:
        st.info("This dataset has no location data to map.")
    if st.sidebar.checkbox("Show raw data", False, key='raw_data'):
        st.write(modified_data)

### Displaying the number of positive, negative or neutral tweets by airline:
st.sidebar.subheader("Breakdown airline tweets by sentiment")
choice = st.sidebar.multiselect('Pick Airlines',
                                ('US Airways', 'United', 'American', 'Southwest', 'Delta', 'Virgin America'), key='0')

if len(choice) > 0:
    choice_data = data[data.airline.isin(choice)]
    fig_choice = px.histogram(choice_data, x='airline', y='airline_sentiment', histfunc='count',
                              color='airline_sentiment',
                              facet_col='airline_sentiment', labels={'airline_sentiment': 'tweets'}, height=600,
                              width=800)
    st.plotly_chart(fig_choice)

st.sidebar.header("Word Cloud")
word_sentiment = st.sidebar.radio('Display word cloud for which sentiment ?', ('positive', 'neutral', 'negative'))

if not st.sidebar.checkbox("Close", True, key='close_wordcloud'):
    st.header('Word Cloud for %s sentiment' % (word_sentiment))
    df = data[data['airline_sentiment'] == word_sentiment]
    words = ' '.join(df['text'])
    processed_words = ' '.join(
        [word for word in words.split() if 'http' not in word and not word.startswith('@') and word != 'RT'])
    wordcloud = WordCloud(stopwords=STOPWORDS, background_color='white', height=640, width=800).generate(
        processed_words)
    fig_wc, ax = plt.subplots()
    ax.imshow(wordcloud)
    ax.set_xticks([])
    ax.set_yticks([])
    st.pyplot(fig_wc)
