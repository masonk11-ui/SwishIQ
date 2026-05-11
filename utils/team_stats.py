import pandas as pd

def build_team_stats(df, stats):
    return (
        df.groupby("TEAM_NAME")[stats]
        .mean(numeric_only=True)
        .round(2)
        .reset_index()
        .sort_values(by="PLUS_MINUS", ascending=False)
        .rename(columns={
        #    "TEAM_NAME": "Team",
            "PTS": "PTS",
            "FG_PCT": "FG%",
            "FG3_PCT": "3PT%",
            "FT_PCT": "FT%",
            "OREB": "OREB",
            "DREB": "DREB",
            "REB": "REB",
            "AST": "ASTS",
            "TOV": "TO",
            "STL": "STL",
            "BLK": "BLK",
            "PLUS_MINUS": "+/-"
        })
    )

def build_team_ratings(df):
    team_ratings = df.groupby('TEAM_NAME').agg({
        'PTS' : 'sum',
        'PTSA' : 'sum',
        'Possessions' : 'sum',
        'OPP_Possessions' : 'sum',
        'PACE' : 'mean'
    }).reset_index()
    
    team_ratings['O_RTG'] = (100 * team_ratings['PTS'] / team_ratings['Possessions']).round(1)
    team_ratings['D_RTG'] = (100 * team_ratings['PTSA'] / team_ratings['Possessions']).round(1)
    team_ratings['NET_RTG'] = team_ratings['O_RTG'] - team_ratings['D_RTG']

    
    return team_ratings

def add_possessions(df):
    df = df.copy()

    df['Possessions'] = 0.96*(((df['FGA'])+(df['TOV']))+0.44*(df['FTA'])-df['OREB'])
    opp = df[['TEAM_NAME', 'GAME_ID', 'Possessions']].copy()
    opp = opp.rename(columns={
        "TEAM_NAME" : "OPP_TEAM_NAME",
        "Possessions" : "OPP_Possessions"
    })

    df = df.merge(opp, on="GAME_ID", how="left")
    df = df[df["TEAM_NAME"] != df['OPP_TEAM_NAME']]

    df['AVG_Possessions'] = (
        df['Possessions'] + df['OPP_Possessions']
    ) / 2

    df['PACE'] = (240 / df['GAME_MIN']) * df['AVG_Possessions']

    return df



