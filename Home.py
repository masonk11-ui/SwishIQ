import streamlit as st
from utils.data_loader import load_team_game_logs
from utils.team_stats import build_team_stats
from utils.team_stats import build_team_ratings
from utils.team_stats import add_possessions
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from zoneinfo import ZoneInfo

st.title("SwishIQ")
st.write("Welcome to SwishIQ. Tracking team and player performance over the course of " \
"the 2026 NBA playoffs.")
st.divider()


team_game_logs = load_team_game_logs()
team_game_logs = add_possessions(team_game_logs)
stats_to_include = ['PTS', 'FG_PCT', 'FG3_PCT', 'FT_PCT', 'OREB',
         'DREB', 'REB', 'AST', 'TOV', 'STL', 'BLK',
         'PLUS_MINUS']



now = datetime.now(ZoneInfo("America/Chicago")).strftime("%m/%d %I:%M %p")

team_stats_df = build_team_stats(team_game_logs, stats_to_include)
team_ratings_df = build_team_ratings(team_game_logs)

columns = (team_stats_df.columns)

team_metrics = team_stats_df.merge(
    team_ratings_df[["TEAM_NAME", "O_RTG", "D_RTG", 'NET_RTG', 'PACE']],
    on="TEAM_NAME"
)

team_metrics = team_metrics[["TEAM_NAME", 'NET_RTG', "O_RTG", "D_RTG", "PTS", 'FG%', 
                             '3PT%', 'FT%', 'REB', 'ASTS', 'TO', "PACE"]]

team_metrics = team_metrics.rename(columns={'TEAM_NAME' : 'TEAM'})

team_metrics["FG%"] = team_metrics["FG%"].map("{:.0%}".format)
team_metrics["3PT%"] = team_metrics["3PT%"].map("{:.0%}".format)
team_metrics["FT%"] = team_metrics["FT%"].map("{:.0%}".format)
team_metrics = team_metrics.round({
    'PTS' : 1,
    'ASTS' : 1,
    'TO' : 1,
    'REB' : 1,
    'PACE' : 1
})

team_metrics = team_metrics.rename(columns = {
    'NET_RTG' : 'NET',
    'O_RTG' : 'ORTG',
    'D_RTG' : 'DRTG',
    'ASTS' : 'AST',
    'TO': 'TOV'
})

team_metrics = team_metrics.sort_values(by='NET', ascending=False)

st.subheader(f'Team Ratings & Per Game Stats — {now} CT')

eliminated_teams = ['Phoenix Suns', 'Denver Nuggets', 'Houston Rockets', 'Portland Trail Blazers',
                    'Boston Celtics', 'Atlanta Hawks', 'Toronto Raptors', 'Orlando Magic', 'Philadelphia 76ers',
                    'Detroit Pistons', 'Los Angeles Lakers', 'Minnesota Timberwolves', 'Cleveland Cavaliers', 
                    'Oklahoma City Thunder']

team_metrics["TEAM"] = team_metrics["TEAM"].apply(
    lambda x: f"{x} (e)" if x in eliminated_teams else x
)

team_metrics = team_metrics.rename(columns = {
    'TEAM' : 'Team'
})

styled_df = (
    team_metrics.style
    .format({
        "NET": "{:.1f}",
        "ORTG": "{:.1f}",
        "DRTG": "{:.1f}",
        "PTS": "{:.1f}",
        "REB": "{:.1f}",
        "AST": "{:.1f}",
        "TOV": "{:.1f}",
        "PACE": "{:.1f}"
    })
    .background_gradient(subset=["NET"], cmap="RdYlGn")
)

st.dataframe(styled_df, #.background_gradient(cmap='RdYlGn'), 
             use_container_width=True, 
             hide_index=True)