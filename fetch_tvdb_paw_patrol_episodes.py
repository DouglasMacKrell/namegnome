import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Loads .env file

API_KEY = os.getenv("TVDB_API_KEY")
SERIES_ID = "272472"  # Paw Patrol

if not API_KEY:
    raise RuntimeError("Missing TVDB_API_KEY in .env file.")

# Authenticate
print("Authenticating with TheTVDB...")
auth_url = "https://api.thetvdb.com/login"
auth_payload = {"apikey": API_KEY}
auth_resp = requests.post(auth_url, json=auth_payload)
auth_resp.raise_for_status()
token = auth_resp.json()["token"]

headers = {"Authorization": f"Bearer {token}"}

# Fetch all episodes (paginated)
episodes = []
page = 1
print("Fetching episodes...")
while True:
    url = f"https://api.thetvdb.com/series/{SERIES_ID}/episodes?page={page}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    episodes.extend(data["data"])
    if not data.get("links") or data["links"]["last"] == page:
        break
    page += 1

# Save to mocks directory
mock_path = Path("tests/mocks/tv/paw_patrol_tvdb_episodes.json")
mock_path.parent.mkdir(parents=True, exist_ok=True)
with open(mock_path, "w") as f:
    json.dump(episodes, f, indent=2)

print(f"Saved {len(episodes)} episodes to {mock_path}")
