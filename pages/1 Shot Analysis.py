import streamlit as st
import matplotlib.pyplot as plt
from utils.court_plot import draw_court
import pandas as pd
from utils.data_loader import get_playoff_shots

st.title("Shot Analysis")
st.write("Explore shot location, efficiency, and scoring tendencies across the 2026 NBA Playoffs.")
st.divider()

@st.cache_data
def get_shots():
    return get_playoff_shots()

shots = get_shots()

with st.sidebar:
    st.header("Filters")
    st.divider()

    team_options = ["All Teams"] + sorted(shots["TEAM_NAME"].dropna().unique())
    selected_team = st.selectbox("Team", team_options)

filtered = shots.copy()

if selected_team != "All Teams":
    filtered = filtered[filtered["TEAM_NAME"] == selected_team]

with st.sidebar:
    player_options = ["All Players"] + sorted(filtered["PLAYER_NAME"].dropna().unique())
    selected_player = st.selectbox("Player", player_options)

if selected_player != "All Players":
    filtered = filtered[filtered["PLAYER_NAME"] == selected_player]

made = filtered[filtered["SHOT_MADE_FLAG"] == 1]
missed = filtered[filtered["SHOT_MADE_FLAG"] == 0]

st.subheader('FG% by Shot Range')

zone_stats = (
    filtered
    .dropna(subset=["SHOT_ZONE_RANGE"])
    .groupby("SHOT_ZONE_RANGE")
    .agg(
        attempts=("SHOT_MADE_FLAG", "count"),
        fg_pct=("SHOT_MADE_FLAG", "mean")
    )
    .reset_index()
)

order = [
    "Less Than 8 ft.",
    "8-16 ft.",
    "16-24 ft.",
    "24+ ft.",
    "Back Court Shot"
]

zone_stats["SHOT_ZONE_RANGE"] = pd.Categorical(
    zone_stats["SHOT_ZONE_RANGE"],
    categories=order,
    ordered=True
)

zone_stats = zone_stats.sort_values("SHOT_ZONE_RANGE")
zone_stats["fg_pct"] = (zone_stats["fg_pct"] * 100).round(1)

cols = st.columns(len(zone_stats))

for i, row in zone_stats.reset_index(drop=True).iterrows():
    cols[i].metric(
        label=row["SHOT_ZONE_RANGE"],
        value=f"{row['fg_pct']}%"
      #  delta=f"{row['attempts']} shots"
    )

st.divider()

st.subheader("Shot Chart")

fig, ax = plt.subplots(figsize=(8, 7))

fig.patch.set_facecolor("#0A192F")
ax.set_facecolor("#0A192F")

ax.scatter(missed["LOC_X"], missed["LOC_Y"], c="#e74c3c", s=14, alpha=0.25)
ax.scatter(made["LOC_X"], made["LOC_Y"], c="#2ecc71", s=14, alpha=0.60)

draw_court(ax, color="white", lw=1.2)

ax.set_xlim(-250, 250)
ax.set_ylim(-50, 325)

ax.invert_yaxis()
ax.axis("off")


st.pyplot(fig)