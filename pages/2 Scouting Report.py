import streamlit as st
import matplotlib.pyplot as plt
from utils.court_plot import draw_court
import pandas as pd
from utils.data_loader import get_playoff_shots, get_player_game_logs
from nba_api.stats.endpoints import playergamelogs
from utils.play_style import team_play_types_freq
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go




st.title('Scouting Report')
st.write("Explore team and player offensive profiles over the 2026 NBA Playoffs.")


@st.cache_data
def get_shots():
    return get_playoff_shots()


@st.cache_data
def get_player_logs():
    return get_player_game_logs()


def classify_zone(row):
    if row["SHOT_DISTANCE"] <= 5:
        return "Rim"
    elif row["SHOT_TYPE"] == "3PT Field Goal":
        return "3PT"
    else:
        return "Midrange"


shots = get_shots()
player_logs = get_player_logs()

team_abbrev = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Cleveland Cavaliers": "CLE",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Houston Rockets": "HOU",
    "Los Angeles Lakers": "LAL",
    "Minnesota Timberwolves": "MIN",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
}

team_abbrev_reverse = {v: k for k, v in team_abbrev.items()}

shots = shots.copy()

shots["TEAM_ABBR"] = shots["TEAM_NAME"].map(team_abbrev)

shots["OPP_ABBR"] = shots.apply(
    lambda row: row["VTM"] if row["HTM"] == row["TEAM_ABBR"] else row["HTM"],
    axis=1
)

shots["OPP_TEAM_NAME"] = shots["OPP_ABBR"].map(team_abbrev_reverse)


# -----------------------
# Sidebar Filters
# -----------------------

with st.sidebar:
    #st.title("HoopIQ")
    #st.divider()
    st.subheader("Filters")
    st.divider()

    team_options = ['All Teams'] + sorted(shots['TEAM_NAME'].dropna().unique())
    selected_team = st.selectbox('Team', team_options)


shots_filt = shots.copy()
team_player_logs = player_logs.copy()

if selected_team != 'All Teams':
    shots_filt = shots_filt[shots_filt['TEAM_NAME'] == selected_team]
    team_player_logs = team_player_logs[
        team_player_logs['TEAM_NAME'] == selected_team
    ]


with st.sidebar:
    opponent_options = (
        ["All Opponents"] +
        sorted(shots_filt["OPP_TEAM_NAME"].dropna().unique())
    )
    selected_opponent = st.selectbox('Opponent', opponent_options)


if selected_opponent != "All Opponents":
    shots_filt = shots_filt[
        shots_filt["OPP_TEAM_NAME"] == selected_opponent
    ]


series_game_ids = shots_filt["GAME_ID"].unique()

team_player_logs = team_player_logs[
    team_player_logs["GAME_ID"].isin(series_game_ids)
]

if selected_team == "All Teams" and selected_opponent != "All Opponents":
    team_player_logs = team_player_logs[
        team_player_logs["TEAM_NAME"] != selected_opponent
    ].copy()


with st.sidebar:
    player_options = (
        ["All Players"] +
        sorted(shots_filt["PLAYER_NAME"].dropna().unique())
    )
    selected_player = st.selectbox('Player', player_options)


if selected_player != 'All Players':
    shots_filt = shots_filt[
        shots_filt['PLAYER_NAME'] == selected_player
    ]

    team_player_logs = team_player_logs[
        team_player_logs['PLAYER_NAME'] == selected_player
    ]


# -----------------------
# Offensive Threats
# -----------------------

player_stats = (
    team_player_logs
    .groupby("PLAYER_NAME")
    .agg({
        "PTS": "mean",
        "AST": "mean",
        "TOV": "mean",
        "FGM": "sum",
        "FGA": "sum",
        "FG3M": "sum",
        "FG3A": "sum"
    })
    .reset_index()
)

player_stats["PRFPG"] = player_stats["PTS"] + (2.2 * player_stats["AST"])
player_stats["FG%"] = player_stats["FGM"] / player_stats["FGA"]
player_stats["3P%"] = player_stats["FG3M"] / player_stats["FG3A"]
player_stats["3P Rate"] = player_stats["FG3A"] / player_stats["FGA"]

rim_stats = (
    shots_filt.groupby("PLAYER_NAME")
    .agg(
        FGA=("SHOT_MADE_FLAG", "count"),
        RIM_FGA=("SHOT_DISTANCE", lambda x: (x <= 5).sum())
    )
    .reset_index()
)

rim_stats['Rim Rate'] = rim_stats['RIM_FGA'] / rim_stats['FGA']

st.divider()
st.subheader('Offensive Threats')

player_stats = player_stats.merge(rim_stats, on="PLAYER_NAME", how="left")

summary_df = player_stats.copy()

summary_df = summary_df[
    ["PLAYER_NAME", "PRFPG", "PTS", "AST", "TOV", "FG%", "3P Rate", "Rim Rate"]
]

summary_df = summary_df.sort_values("PRFPG", ascending=False)

summary_df = summary_df.rename(columns={
    "PLAYER_NAME": "Player",
    "PTS": "PPG",
    "AST": "APG",
    "TOV": "TOPG"
})

summary_df_styled = (
    summary_df.style
    .format({
        "PRFPG": "{:.1f}",
        "PPG": "{:.1f}",
        "APG": "{:.1f}",
        "TOPG": "{:.1f}",
        "FG%": "{:.0%}",
        "3P%": "{:.0%}",
        "3P Rate": "{:.0%}",
        "Rim Rate": "{:.0%}"
    })
    .background_gradient(
        subset=["PRFPG"],
        cmap="Reds",
        vmin=summary_df["PRFPG"].min()
    )
)

st.dataframe(
    summary_df_styled,
    use_container_width=True,
    hide_index=True,
    height=275
)


# -----------------------
# Shot Distribution
# -----------------------

st.subheader('Shot Distribution')

total_shots = len(shots_filt)
rim_shots = len(shots_filt[shots_filt["SHOT_DISTANCE"] <= 5])
three_shots = len(shots_filt[shots_filt['SHOT_TYPE'] == '3PT Field Goal'])
mid_shots = total_shots - rim_shots - three_shots

rim_rate = rim_shots / total_shots if total_shots > 0 else 0
three_rate = three_shots / total_shots if total_shots > 0 else 0
mid_rate = mid_shots / total_shots if total_shots > 0 else 0

shots_filt['Zone'] = shots_filt.apply(classify_zone, axis=1)

zone_stats = (
    shots_filt.groupby('Zone')
    .agg(
        FGA=("SHOT_MADE_FLAG", "count"),
        FGM=("SHOT_MADE_FLAG", "mean")
    )
    .reset_index()
)

zone_stats["FREQ"] = zone_stats["FGA"] / zone_stats["FGA"].sum()
zone_stats["FG%"] = zone_stats["FGM"]

zone_display = zone_stats[[
    "Zone",
    "FREQ",
    "FG%"
]].copy()

zone_display = zone_display.rename(columns={
    'FREQ': 'Shot Mix'
})

styled = (
    zone_display.style
    .bar(
        subset=['Shot Mix'],
        color='#2563eb',
        vmin=0,
        vmax=1
    )
    .background_gradient(
        subset=['FG%'],
        cmap='RdYlGn'
    )
    .format({
        'Shot Mix': '{:.0%}',
        'FG%': '{:.0%}'
    })
)

st.table(styled)
st.divider()
st.subheader('Offensive Play Style / Tendencies')

play_types = {
    'Transition': 'TRANS',
    'Isolation': 'ISO',
    'PRBallHandler': 'PNR_BH',
    'PRRollman': 'PNR_RM',
    'Postup': 'POST',
    'Spotup' : 'SPOT',
    'OffScreen' :'OFF_SCREEN',
    'Handoff' : 'HANDOFF'
}

teams_df = pd.DataFrame({
    "TEAM_NAME": sorted(shots["TEAM_NAME"].dropna().unique())
})

play_types_df = team_play_types_freq(
    play_types,
    teams_df
)

show_team_play_style = (
    selected_team != "All Teams"
    and selected_opponent == "All Opponents"
    and selected_player == "All Players"
)

if show_team_play_style:

    team_play_style = play_types_df[
        play_types_df["TEAM_NAME"] == selected_team
    ].iloc[0]

    donut_data = pd.DataFrame({
        "Play Type": [
            "PnR Ball Handler",
            "Transition",
            "Spot Up",
            "Isolation",
            "PnR Roll Man",
            "Handoff",
            "Off Ball Screen",
            "Post Up",
            "Other / Misc"
        ],
        "Frequency": [
            team_play_style["PNR_BH_FREQ"],
            team_play_style["TRANS_FREQ"],
            team_play_style["SPOT_FREQ"],
            team_play_style["ISO_FREQ"],
            team_play_style["PNR_RM_FREQ"],
            team_play_style["HANDOFF_FREQ"],
            team_play_style["OFF_SCREEN_FREQ"],
            team_play_style["POST_FREQ"],
            team_play_style["OTHER_FREQ"]
        ]
    })

    donut_data = donut_data.sort_values(
        "Frequency",
        ascending=False
    )

    colors = [
        "#38BDF8",  # cyan
        "#2563EB",  # blue
        "#8B5CF6",  # purple
        "#22C55E",  # green
        "#F59E0B",  # amber
        "#EF4444",  # red
        "#14B8A6",  # teal
        "#A855F7",  # violet
        "#475569"   # other
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=donut_data["Play Type"],
                values=donut_data["Frequency"],
                hole=0.68,
                sort=False,
                direction="clockwise",
                marker=dict(
                    colors=colors,
                    line=dict(
                        color="#0A192F",
                        width=3
                    )
                ),
                textinfo="label+percent",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Frequency: %{percent}"
                    "<extra></extra>"
                ),
                pull=[
                    0.03 if i == 0 else 0
                    for i in range(len(donut_data))
                ]
            )
        ]
    )

    top_play = donut_data.iloc[0]["Play Type"]
    top_freq = donut_data.iloc[0]["Frequency"]

    fig.update_layout(

        annotations=[
            dict(
                text=(
                    "<span style='font-size:12px;color:#94A3B8'>Top Action</span><br>"
                    f"<span style='font-size:24px'><b>{top_play}</b></span>"
                ),
                x=0.5,
                y=0.5,
                showarrow=False,
                align='center',
                font=dict(
                    size=22,
                    color="white"
                )
            )
        ],

        showlegend=False,

        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                size=13,
                color="white"
            )
        ),

        paper_bgcolor="#0A192F",
        plot_bgcolor="#0A192F",

        font=dict(color="white"),

        margin=dict(
            t=70,
            b=30,
            l=20,
            r=180
        ),

        height=520
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:
    st.info("Select one team with All Opponents and All Players to view team-level offensive play style.")