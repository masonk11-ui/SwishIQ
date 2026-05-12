import streamlit as st
import matplotlib.pyplot as plt
from utils.court_plot import draw_court
import pandas as pd
from utils.data_loader import get_playoff_shots

st.markdown("""
<style>
.glass-card {
    background: rgba(255, 255, 255, 0.055);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 14px;
    padding: 16px 14px;
    min-height: 135px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.16);
}

.metric-label {
    color: #B8C2CC;
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 14px;
    line-height: 1.25;
    min-height: 34px;
}

.metric-value {
    color: white;
    font-size: 1.95rem;
    font-weight: 700;
    line-height: 1;
    white-space: nowrap;
}

.metric-attempts {
    color: #8A96A8;
    font-size: 0.78rem;
    margin-top: 12px;
    white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* radio container */
div[role="radiogroup"] {
    display: flex;
    gap: 0.5rem;
}

/* each option */
div[role="radiogroup"] label {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 10px 18px;
    border-radius: 12px;
    transition: 0.2s ease;
}

/* hover */
div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.10);
}

/* selected */
div[role="radiogroup"] label[data-selected="true"] {
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.18);
}

</style>
""", unsafe_allow_html=True)

def glass_metric_card(label, value, attempts=None):
    attempts_html = f'<div class="metric-attempts">{attempts} attempts</div>' if attempts is not None else ""

    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {attempts_html}
    </div>
    """, unsafe_allow_html=True)



st.title("Shot Analysis")
st.write("Explore shot location, efficiency, and scoring tendencies across the 2026 NBA Playoffs.")
st.divider()

@st.cache_data
def get_shots():
    return get_playoff_shots()


def classify_shot_loc(x):
    if x < -80:
        return 'Left'
    elif x > 80:
        return 'Right'
    else:
        return 'Center'


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

filtered["SHOT_SIDE"] = filtered["LOC_X"].apply(classify_shot_loc).astype(str)
made = filtered[filtered["SHOT_MADE_FLAG"] == 1]
missed = filtered[filtered["SHOT_MADE_FLAG"] == 0]

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

side_stats = (
    filtered
    .dropna(subset=["SHOT_SIDE"])
    .groupby("SHOT_SIDE")
    .agg(
        attempts=("SHOT_MADE_FLAG", "count"),
        fg_pct=("SHOT_MADE_FLAG", "mean")
    )
    .reset_index()
)

zone_order = [
    "Less Than 8 ft.",
    "8-16 ft.",
    "16-24 ft.",
    "24+ ft.",
    "Back Court Shot"
]

zone_stats["SHOT_ZONE_RANGE"] = pd.Categorical(
    zone_stats["SHOT_ZONE_RANGE"],
    categories=zone_order,
    ordered=True
)

zone_stats = zone_stats.sort_values("SHOT_ZONE_RANGE")
zone_stats["fg_pct"] = (zone_stats["fg_pct"] * 100).round(1)

side_order = ["Left", "Center", "Right"]

side_stats["SHOT_SIDE"] = pd.Categorical(
    side_stats["SHOT_SIDE"],
    categories=side_order,
    ordered=True
)

side_stats = side_stats.sort_values("SHOT_SIDE")

side_stats["fg_pct"] = (side_stats["fg_pct"] * 100).round(1)

st.subheader('FG% by Shot Range')
cols = st.columns(len(zone_stats))


for i, row in zone_stats.reset_index(drop=True).iterrows():
    with cols[i]:
        glass_metric_card(
            str(row["SHOT_ZONE_RANGE"]),
            f"{row['fg_pct']}%",
            row["attempts"]
        )

st.subheader("FG% by Shot Side")
cols = st.columns(5)

for i, row in side_stats.reset_index(drop=True).iterrows():
    with cols[i]:
        glass_metric_card(
            str(row["SHOT_SIDE"]),
            f"{row['fg_pct']}%",
            row["attempts"]
        )

st.divider()

st.subheader("Shot Chart")

fig, ax = plt.subplots(figsize=(8, 7))

fig.patch.set_facecolor("#0A192F")
ax.set_facecolor("#0A192F")

chart_type = st.radio(
    "Shot Chart View",
    ["Shot Chart", "Shot Frequency"],
    horizontal=True
)

if selected_player == "All Players":
    gridsize = 17
    mincnt = 1
else:
    gridsize = 17
    mincnt = 1

if chart_type == 'Shot Chart':
    ax.scatter(missed["LOC_X"], missed["LOC_Y"], c="#e74c3c", s=14, alpha=0.25)
    ax.scatter(made["LOC_X"], made["LOC_Y"], c="#2ecc71", s=14, alpha=0.60)


elif chart_type == 'Shot Frequency':
    ax.hexbin(
        filtered['LOC_X'],
        filtered['LOC_Y'],
        gridsize=17,
        cmap="plasma",
        mincnt=1,
        alpha=0.85,
        linewidths=0.15
    )

draw_court(ax, color="white", lw=1.2)

ax.set_xlim(-250, 250)
ax.set_ylim(-50, 325)

ax.invert_yaxis()
ax.axis("off")


st.pyplot(fig)