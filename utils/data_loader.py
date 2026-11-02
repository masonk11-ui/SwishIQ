
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase credentials in Streamlit Cloud"
        )

    return create_client(url, key)





import time

@st.cache_data(ttl=3600)
def fetch_table(table_name):
    start = time.perf_counter()
    supabase = get_supabase()

    records = []
    page_size = 1000
    offset = 0

    while True:
        response = (
            supabase.table(table_name)
            .select("stats")
            .order("game_id")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        batch = response.data
        records.extend(row["stats"] for row in batch)

        if len(batch) < page_size:
            break

        offset += page_size

    df = pd.DataFrame(records)

    elapsed = time.perf_counter() - start
    print(
        f"{table_name}: {len(df)} rows "
        f"loaded in {elapsed:.2f} seconds",
        flush=True
    )

    return df



def load_team_game_logs():
    return fetch_table("team_game_logs")


def get_regular_season_shots():
    return fetch_table("shot_chart")


def get_player_game_logs():
    return fetch_table("player_game_logs")
