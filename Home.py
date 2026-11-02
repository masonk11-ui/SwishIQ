import streamlit as st
from utils.data_loader import load_team_game_logs
from utils.team_stats import build_team_stats
from utils.team_stats import build_team_ratings
from utils.team_stats import add_possessions
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from zoneinfo import ZoneInfo
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


st.title("SwishIQ")
st.write("Welcome to SwishIQ. Tracking team and player performance over the course of " \
"the 2027 NBA Season.")
st.divider()


team_game_logs = load_team_game_logs()
team_game_logs = add_possessions(team_game_logs)


# Calculate team win-loss records
team_records = (
    team_game_logs
    .groupby("TEAM_NAME")["WL"]
    .value_counts()
    .unstack(fill_value=0)
    .reindex(columns=["W", "L"], fill_value=0)
    .reset_index()
)

team_records["W-L"] = (
    team_records["W"].astype(str)
    + "-"
    + team_records["L"].astype(str)
)

team_records = team_records[["TEAM_NAME", "W-L"]]


# Create team logo lookup using NBA team IDs

# Create team logo lookup using ESPN logos
team_logos = (
    team_game_logs[["TEAM_NAME", "TEAM_ABBREVIATION"]]
    .drop_duplicates(subset="TEAM_NAME")
    .copy()
)

# NBA abbreviations that differ from ESPN
espn_abbreviations = {
    "GSW": "gs",
    "NYK": "ny",
    "NOP": "no",
    "SAS": "sa",
    "UTA": "utah"
}

def get_logo_url(abbreviation):
    espn_code = espn_abbreviations.get(
        abbreviation,
        abbreviation.lower()
    )
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{espn_code}.png"

team_logos["LOGO"] = team_logos["TEAM_ABBREVIATION"].apply(
    get_logo_url
)

team_logos = team_logos[["TEAM_NAME", "LOGO"]]



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


# Merge team win-loss records into team metrics
team_metrics = team_metrics.merge(
    team_records,
    on="TEAM_NAME",
    how="left"
)

team_metrics = team_metrics.merge(
    team_logos,
    on="TEAM_NAME",
    how="left"
)


team_metrics = team_metrics[["LOGO", "TEAM_NAME", "W-L", 'NET_RTG', "O_RTG", "D_RTG", "PTS", 'FG%', 
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


# Sort teams by NET Rating (highest to lowest)
team_metrics = team_metrics.sort_values(
    by="NET",
    ascending=False
).reset_index(drop=True)

# Assign each team a ranking
team_metrics.insert(
    0,
    "RK",
    range(1, len(team_metrics) + 1)
)


st.subheader("Team Power Rankings")
st.caption("2026–27 NBA Regular Season | Ranked by Net Rating")

eliminated_teams = ['']

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


# --------------------------------
# SWISHIQ TEAM RATINGS TABLE
# --------------------------------

# Keep the most important columns visible
display_columns = [
    "RK", "LOGO", "Team", "W-L",
    "NET", "ORTG", "DRTG"
]

grid_df = team_metrics[display_columns].copy()

# Custom renderer for team logos
logo_renderer = JsCode("""
class LogoRenderer {
    init(params) {
        this.eGui = document.createElement('div');
        this.eGui.style.display = 'flex';
        this.eGui.style.alignItems = 'center';
        this.eGui.style.justifyContent = 'center';
        this.eGui.style.height = '100%';

        const img = document.createElement('img');
        img.src = params.value || '';
        img.style.width = '32px';
        img.style.height = '32px';
        img.style.objectFit = 'contain';

        this.eGui.appendChild(img);
    }

    getGui() {
        return this.eGui;
    }

    refresh(params) {
        return false;
    }
}
""")

# Net rating colors
net_style = JsCode("""
function(params) {
    if (params.value == null) return {};

    const value = Number(params.value);

    let bg = "#1E293B";   // default dark
    let text = "#F8FAFC";

    if (value >= 10) {
        bg = "#0B7A3B";
        text = "#F8FAFC";
    } else if (value >= 5) {
        bg = "#2EA44F";
        text = "#F8FAFC";
    } else if (value >= 0) {
        bg = "#84CC6A";
        text = "#0F172A";
    } else if (value >= -5) {
        bg = "#FACC15";
        text = "#0F172A";
    } else if (value >= -10) {
        bg = "#FB923C";
        text = "#0F172A";
    } else {
        bg = "#DC2626";
        text = "#F8FAFC";
    }

    return {
        backgroundColor: bg,
        color: text,
        fontWeight: '700',
        textAlign: 'center'
    };
}
""")


logo_renderer = JsCode("""
class LogoRenderer {
    init(params) {
        this.eGui = document.createElement('div');
        this.eGui.style.display = 'flex';
        this.eGui.style.alignItems = 'center';
        this.eGui.style.justifyContent = 'center';
        this.eGui.style.height = '100%';

        const img = document.createElement('img');
        img.src = params.value || '';
        img.style.width = '32px';
        img.style.height = '32px';
        img.style.objectFit = 'contain';

        this.eGui.appendChild(img);
    }

    getGui() {
        return this.eGui;
    }

    refresh(params) {
        return false;
    }
}
""")

gb = GridOptionsBuilder.from_dataframe(grid_df)



gb = GridOptionsBuilder.from_dataframe(grid_df)

gb.configure_default_column(
    sortable=True,
    filter=False,
    resizable=True,
    suppressHeaderMenuButton=True
)

gb.configure_column("RK", width=65)

gb.configure_column(
    "LOGO",
    header_name="",
    width=65,
    sortable=False,
    cellRenderer=logo_renderer
)

gb.configure_column("Team", header_name="TEAM", width=250)
gb.configure_column("W-L", width=90)

number_formatter = JsCode("""
function(params) {
    return params.value == null
        ? ''
        : Number(params.value).toFixed(1);
}
""")

gb.configure_column(
    "NET",
    width=105,
    valueFormatter=number_formatter,
    cellStyle=net_style
)

gb.configure_column(
    "ORTG",
    width=105,
    valueFormatter=number_formatter
)

gb.configure_column(
    "DRTG",
    width=105,
    valueFormatter=number_formatter
)

grid_options = gb.build()

grid_options["rowHeight"] = 50
grid_options["headerHeight"] = 44
grid_options["domLayout"] = "normal"
grid_options["suppressCellFocus"] = True
grid_options["animateRows"] = True
grid_options["suppressMenuHide"] = True
grid_options["suppressMovableColumns"] = True

# Only subtle horizontal row separators
custom_css = {
    ".ag-root-wrapper": {
        "border": "1px solid #27364C !important",
        "border-radius": "10px !important"
    },
    ".ag-root, .ag-header, .ag-row": {
        "background-color": "#0B1B31 !important",
        "color": "#F1F5F9 !important",
        "font-size": "15px !important"
    },
    ".ag-header": {
        "background-color": "#15253B !important",
        "border-bottom": "1px solid #334155 !important"
    },
    ".ag-header-cell, .ag-cell": {
        "border-right": "none !important"
    },
    ".ag-row": {
        "border-bottom": "1px solid #25354A !important"
    },
    ".ag-row-hover": {
        "background-color": "#19314F !important"
    },
    ".ag-header-cell-text": {
        "color": "#A8B8CC !important",
        "font-weight": "700 !important",
        "font-size": "15px !important"
    },
    ".ag-cell": {
        "display": "flex",
        "align-items": "center",
        "font-size": "13px !important"
    },
    ".ag-cell-focus, .ag-cell-no-focus": {
        "border": "none !important",
        "outline": "none !important"
    },
    ".ag-header-cell:focus-within": {
        "outline": "none !important",
        "box-shadow": "none !important"
    }
}

AgGrid(
    grid_df,
    gridOptions=grid_options,
    height=430,
    theme="streamlit",
    custom_css=custom_css,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=False,
    key="swishiq_team_ratings"
)



#st.dataframe(
#    styled_df,
#    column_config={
#        "RK": st.column_config.NumberColumn(
#            "RK", width="small"
#        ),
#        "LOGO": st.column_config.ImageColumn(
#            " ", width="small"
##        ),
 #       "Team": st.column_config.TextColumn(
  #          "Team", width="medium"
 #       ),
 ##       "W-L": st.column_config.TextColumn(
  ##          "W-L", width="small"
  #      ),
  #      "NET": st.column_config.NumberColumn(
  #          "NET", format="%.1f", width="small"
   #     )
#    },
#    column_order=(
#        ["RK", "LOGO", "Team", "W-L", "NET", "ORTG", "DRTG", "PTS"]
#    ),
##    use_container_width=True,
 #   hide_index=True,
 #   height=350
#)
