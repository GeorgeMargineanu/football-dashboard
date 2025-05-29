import requests
import pandas as pd
from datetime import datetime

# ==== CONFIG ====
API_KEY = "8b7322adcf661b91a386b0092bd9e1b4"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

# ==== FUNCTIONS ====
def get_leagues():
    url = f"{BASE_URL}/leagues"
    response = requests.get(url, headers=HEADERS)
    return response.json()["response"]

def get_fixtures(league_id=39, season=2023):
    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()["response"]

def get_todays_fixtures():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/fixtures?date={today}"
    response = requests.get(url, headers=HEADERS)
    return response.json()["response"]

# ==== MAIN SCRIPT ====

print("Fetching today's fixtures...")
fixtures = get_todays_fixtures()

if not fixtures:
    print("No matches today.")
else:
    fixture_df = pd.DataFrame([{
        "date": f["fixture"]["date"][:10],
        "time": f["fixture"]["date"][11:16],
        "league": f["league"]["name"],
        "home": f["teams"]["home"]["name"],
        "away": f["teams"]["away"]["name"],
        "score": f["goals"]["home"],
        "score_away": f["goals"]["away"]
    } for f in fixtures])

    print(f"\nShowing {len(fixture_df)} matches today:")
    print(fixture_df.head(10))  # Show first 10

    # Save to CSV
    fixture_df.to_csv("fixtures_today.csv", index=False)
    print("\nToday's fixtures saved to fixtures_today.csv ✅")
    