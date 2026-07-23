import pandas as pd
from nba_api.stats.endpoints import teamgamelogs
from nba_api.stats.endpoints import shotchartdetail

def load_team_game_logs():
    df = teamgamelogs.TeamGameLogs(
        season_nullable='2025-26',
        season_type_nullable='Playoffs',
        timeout=60
    ).get_data_frames()[0]

    # df['Possessions'] = 0.96*(((df['FGA'])+(df['TOV']))+0.44*(df['FTA'])-df['OREB'])
    df['PTSA'] = df['PTS'] - df['PLUS_MINUS']
    df['GAME_MIN'] = 5*df['MIN']

    return df

def get_playoff_shots():
    shot_data = shotchartdetail.ShotChartDetail(
        player_id=0,
        team_id=0,
        season_type_all_star='Playoffs',
        season_nullable='2025-26',
        context_measure_simple='FGA',
        timeout=120
    )
    df = shot_data.get_data_frames()[0]

    return df

from nba_api.stats.endpoints import playergamelogs

def get_player_game_logs():
    df = playergamelogs.PlayerGameLogs(
        season_nullable="2025-26",
        season_type_nullable="Playoffs",
        timeout=60
    ).get_data_frames()[0]

    return df