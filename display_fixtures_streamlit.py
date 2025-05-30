import boto3
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
from clean_data import CleanFixtures
import altair as alt
import plotly.express as px

# App Setup
st.set_page_config(page_title="League Dashboard", layout="wide")
st.title("🏆 Football Matchday Dashboard")

# AWS S3 Setup
s3 = boto3.client("s3",
                 aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                 aws_secret_access_key=st.secret["AWS_SECRET_ACCESS_KEY"],
                 region_name=st.secrets["AWS_DEFAULT_REGION"])
bucket = "ssportss"
folder = "football"

# Date selector
selected_date = st.date_input("Select Match Date", value=datetime.today())
file_prefix = selected_date.strftime('%Y-%m-%d')
file_key = f"{folder}/{file_prefix}.csv"

# Load from S3
try:
    obj = s3.get_object(Bucket=bucket, Key=file_key)
    df = pd.read_csv(BytesIO(obj["Body"].read()))
except Exception:
    st.warning(f"No data found for {file_prefix}")
    st.stop()

# Clean and enrich
cleaner = CleanFixtures(df)
cleaned_df = cleaner.remove_nan()
cleaned_df["total_goals"] = cleaned_df["score_home"] + cleaned_df["score_away"]
cleaned_df["goal_diff"] = abs(cleaned_df["score_home"] - cleaned_df["score_away"])

# League filter
leagues = sorted(cleaned_df["league"].dropna().unique())
selected_league = st.selectbox("Select League", ["All Leagues"] + list(leagues))
league_df = cleaned_df if selected_league == "All Leagues" else cleaned_df[cleaned_df["league"] == selected_league]

# KPIs
st.markdown("### 📊 Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Matches", len(league_df))
col2.metric("Goals", int(league_df["total_goals"].sum()))
col3.metric("Avg Goals", round(league_df["total_goals"].mean(), 2))
col4.metric("Draws", len(league_df[league_df["score_home"] == league_df["score_away"]]))

# Extra stats
home_wins = league_df[league_df["score_home"] > league_df["score_away"]]
away_wins = league_df[league_df["score_home"] < league_df["score_away"]]
clean_sheets = league_df[(league_df["score_home"] == 0) | (league_df["score_away"] == 0)]
zero_zero = league_df[(league_df["score_home"] == 0) & (league_df["score_away"] == 0)]

col5, col6, col7 = st.columns(3)
col5.metric("Home Wins", len(home_wins))
col6.metric("Away Wins", len(away_wins))
col7.metric("Clean Sheets", len(clean_sheets))

# Match table
st.markdown("### 📅 Match Results")
st.dataframe(league_df, use_container_width=True)

# High scoring matches
st.markdown("### 🥇 Highest Scoring Matches")
top_matches = league_df[league_df["total_goals"] == league_df["total_goals"].max()]
for _, row in top_matches.iterrows():
    st.success(f"{row['home']} {int(row['score_home'])} - {int(row['score_away'])} {row['away']} | {row['league']}")

# Top scoring teams
st.markdown("### 🔝 Top Attacking Teams (Goals Scored)")
teams = pd.concat([
    league_df[['home', 'score_home']].rename(columns={'home': 'team', 'score_home': 'goals'}),
    league_df[['away', 'score_away']].rename(columns={'away': 'team', 'score_away': 'goals'})
])
top_scorers = teams.groupby('team')['goals'].sum().sort_values(ascending=False).head(5)
st.bar_chart(top_scorers)

# Best defensive teams
st.markdown("### 🛡️ Top Defensive Teams (Least Goals Conceded)")
conceded = pd.concat([
    league_df[['home', 'score_away']].rename(columns={'home': 'team', 'score_away': 'conceded'}),
    league_df[['away', 'score_home']].rename(columns={'away': 'team', 'score_home': 'conceded'})
])
top_defenders = conceded.groupby('team')['conceded'].sum().sort_values().head(5)
st.bar_chart(top_defenders)

# Biggest wins
st.markdown("### 💥 Biggest Goal Margins")
max_diff = league_df["goal_diff"].max()
for _, row in league_df[league_df["goal_diff"] == max_diff].iterrows():
    st.info(f"{row['home']} {row['score_home']} - {row['score_away']} {row['away']} | Diff: {row['goal_diff']}")

# Goal Distribution
st.markdown("### 📈 Goal Count Distribution")
goal_dist = league_df["total_goals"].value_counts().sort_index()
st.bar_chart(goal_dist)

# League total goals
st.markdown("### 🏅 Total Goals by League")
league_goals = cleaned_df.groupby("league")["total_goals"].sum().sort_values(ascending=False).reset_index()
chart = alt.Chart(league_goals).mark_bar().encode(
    x=alt.X("total_goals:Q", title="Total Goals"),
    y=alt.Y("league:N", sort="-x", title="League"),
    tooltip=["league", "total_goals"]
).properties(height=300)
st.altair_chart(chart, use_container_width=True)

# Goals by hour
st.markdown("### ⏰ Goals by Hour")
try:
    league_df["hour"] = pd.to_datetime(league_df["time"], format="%H:%M").dt.hour
    hourly = league_df.groupby("hour")["total_goals"].sum().reset_index()
    st.line_chart(hourly.set_index("hour"))
except:
    st.info("Match times not parsed.")

# Heatmap
st.markdown("### 🔥 Heatmap: Goals by League and Hour")
try:
    cleaned_df["hour"] = pd.to_datetime(cleaned_df["time"], format="%H:%M").dt.hour
    heatmap_data = cleaned_df.groupby(["league", "hour"])["total_goals"].sum().reset_index()
    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X('hour:O'),
        y=alt.Y('league:N'),
        color=alt.Color('total_goals:Q', scale=alt.Scale(scheme='reds')),
        tooltip=['league', 'hour', 'total_goals']
    ).properties(height=400)
    st.altair_chart(heatmap, use_container_width=True)
except:
    st.info("Could not generate heatmap.")

# Pie chart - Outcomes
st.markdown("### 🥧 Match Outcomes")
outcomes = {
    "Home Wins": len(home_wins),
    "Away Wins": len(away_wins),
    "Draws": len(league_df) - len(home_wins) - len(away_wins)
}
outcome_df = pd.DataFrame({
    "Outcome": list(outcomes.keys()),
    "Count": list(outcomes.values())
})
fig = px.pie(outcome_df, names="Outcome", values="Count", title="Match Outcomes", hole=0.3)
st.plotly_chart(fig, use_container_width=True)

# Over/Under 2.5 goals
st.markdown("### ⚖️ Over/Under 2.5 Goals")
over_25 = len(league_df[league_df["total_goals"] > 2.5])
under_25 = len(league_df[league_df["total_goals"] <= 2.5])
col8, col9 = st.columns(2)
col8.metric("Over 2.5 Goals", f"{over_25}")
col9.metric("Under 2.5 Goals", f"{under_25}")

# Most active leagues
st.markdown("### 📈 Most Active Leagues by Match Count")
league_activity = cleaned_df["league"].value_counts().head(5)
st.bar_chart(league_activity)

# Match results by league
st.markdown("### 📊 Match Outcome Breakdown by League")
outcomes_league = league_df.copy()
outcomes_league["result"] = outcomes_league.apply(
    lambda row: "Draw" if row["score_home"] == row["score_away"] else
                "Home Win" if row["score_home"] > row["score_away"] else "Away Win", axis=1)
result_by_league = outcomes_league.groupby(["league", "result"]).size().reset_index(name='count')
fig = px.bar(result_by_league, x='league', y='count', color='result', barmode='stack',
             title="Match Outcomes by League")
st.plotly_chart(fig, use_container_width=True)

# Team performance selector
st.markdown("### 🎯 Team Performance Explorer")
teams_all = pd.concat([league_df['home'], league_df['away']]).unique()
selected_team = st.selectbox("Select a Team", sorted(teams_all))
if selected_team:
    team_matches = league_df[(league_df["home"] == selected_team) | (league_df["away"] == selected_team)].copy()
    team_matches["scored"] = team_matches.apply(
        lambda row: row["score_home"] if row["home"] == selected_team else row["score_away"], axis=1)
    team_matches["conceded"] = team_matches.apply(
        lambda row: row["score_away"] if row["home"] == selected_team else row["score_home"], axis=1)
    team_matches["result"] = team_matches.apply(
        lambda row: "Win" if row["scored"] > row["conceded"] else
                    "Draw" if row["scored"] == row["conceded"] else "Loss", axis=1)
    team_summary = {
        "Matches": len(team_matches),
        "Goals Scored": int(team_matches["scored"].sum()),
        "Goals Conceded": int(team_matches["conceded"].sum()),
        "Wins": (team_matches["result"] == "Win").sum(),
        "Draws": (team_matches["result"] == "Draw").sum(),
        "Losses": (team_matches["result"] == "Loss").sum()
    }
    st.write(team_summary)
    fig = px.pie(names=team_matches["result"], title="Match Outcomes for " + selected_team)
    st.plotly_chart(fig, use_container_width=True)
