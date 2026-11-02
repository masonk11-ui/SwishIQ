
import os
import json
import time
from dotenv import load_dotenv
from supabase import create_client
from nba_api.stats.endpoints import (
    teamgamelogs,
    playergamelogs,
    shotchartdetail
)

load_dotenv()

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

SEASON = "2026-27"


def upload_data(df, table_name, key_columns):
    records = json.loads(df.to_json(orient="records"))

    rows = []
    for record in records:
        row = {
            "season": SEASON,
            "stats": record
        }
        for db_column, nba_column in key_columns.items():
            row[db_column] = record[nba_column]
        rows.append(row)

    for i in range(0, len(rows), 200):
        supabase.table(table_name).upsert(
            rows[i:i + 200],
            on_conflict=",".join(key_columns.keys())
        ).execute()

    print(f"{table_name}: uploaded {len(rows)} records")


# 1. TEAM GAME LOGS
print("Fetching team game logs...")

teams = teamgamelogs.TeamGameLogs(
    season_nullable=SEASON,
    season_type_nullable="Regular Season",
    timeout=60
).get_data_frames()[0]

teams["PTSA"] = teams["PTS"] - teams["PLUS_MINUS"]
teams["GAME_MIN"] = 5 * teams["MIN"]

upload_data(
    teams,
    "team_game_logs",
    {"game_id": "GAME_ID", "team_id": "TEAM_ID"}
)

time.sleep(2)

# 2. PLAYER GAME LOGS
print("Fetching player game logs...")

players = playergamelogs.PlayerGameLogs(
    season_nullable=SEASON,
    season_type_nullable="Regular Season",
    timeout=60
).get_data_frames()[0]

upload_data(
    players,
    "player_game_logs",
    {"game_id": "GAME_ID", "player_id": "PLAYER_ID"}
)

time.sleep(2)

# 3. SHOT CHART
print("Fetching shot chart data...")

shots = shotchartdetail.ShotChartDetail(
    player_id=0,
    team_id=0,
    season_type_all_star="Regular Season",
    season_nullable=SEASON,
    context_measure_simple="FGA",
    timeout=120
).get_data_frames()[0]

upload_data(
    shots,
    "shot_chart",
    {"game_id": "GAME_ID", "game_event_id": "GAME_EVENT_ID"}
)

print("All 2026-27 NBA datasets updated!")
