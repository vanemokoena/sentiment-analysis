✈️ Airline Sentiment Dashboard

An interactive dashboard for exploring what travellers tweeted about US airlines in February 2015. Filter by airline, date, hour and keyword, then see the mood, the busiest hours, the most common complaints and the words people used most.

🔗 [Open the live demo](https://sentiment-analysis-kxbs6nvauyycuzn9wukng4.streamlit.app/)

Open in Streamlit

<img width="1596" height="806" alt="Screenshot 2026-11-20 212401" src="https://github.com/user-attachments/assets/523d8a66-6601-4ce3-8b96-b93d580a7b2b" />

What you can do
Filter everything from one sidebar. Pick airlines, sentiments, a date range, hours of the day, a minimum label confidence, or search the tweet text. A live counter shows how many tweets match, and Reset filters puts everything back.
See the overall mood. A donut chart shows the share of positive, neutral and negative tweets, and a bar chart compares airlines, ordered from most to least negative.
Follow trends. Tweets per day and per hour of day, split by sentiment.
Find out why people complained. A ranked list of complaint reasons and a heatmap showing which airline gets which complaint.
Read the words. A word cloud for each sentiment, with links, @mentions and filler words removed.
Dig into the tweets. Read a random tweet, sort and scroll the full table, download the filtered rows as CSV, and view tweets with a location on a map.
Architecture

Architecture diagram

Layer	What it does	Tools
Data	Raw tweets, one row per tweet	Tweets.csv
Data layer	Loads the file, parses dates, extracts latitude and longitude, adds date and hour columns, caches the result	pandas, @st.cache_data
Filters	Builds one filtered DataFrame from the sidebar choices	Streamlit widgets
Visuals	Charts, word cloud, table and map	Plotly, WordCloud, Matplotlib, st.map
Hosting	Redeploys on every push to main	GitHub, Streamlit Community Cloud
Run it on your computer
bash
git clone https://github.com/vanemokoena/sentiment-analysis.git
cd sentiment-analysis
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py

Then open http://localhost:8501.

Project structure
sentiment-analysis/
├── app.py                  # the dashboard
├── Tweets.csv              # the dataset
├── requirements.txt        # Python packages
├── .streamlit/
│   └── config.toml         # theme and server settings
└── docs/
    └── architecture.svg    # architecture diagram
Deploy your own copy
Fork this repository.
Sign in at share.streamlit.io with GitHub.
Choose Create app, select your fork, branch main and main file app.py.
Click Deploy.
Data

The Twitter US Airline Sentiment dataset (about 14,600 tweets from February 2015). Each tweet is labelled positive, neutral or negative, and negative tweets include a reason such as "Late Flight" or "Customer Service Issue".

Credits

This project started from the Airline Sentiment Analysis Dashboard by Akanksha Tetwar. I updated it for current Streamlit and Python versions and redesigned the interface, filters and charts.

Author

Vanessa Mokoena: GitHub · LinkedIn
