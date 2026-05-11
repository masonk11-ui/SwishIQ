import pandas as pd
from nba_api.stats.endpoints import synergyplaytypes


def team_play_types_freq(play_types, team_df):

    for play_type, prefix in play_types.items():

        data = synergyplaytypes.SynergyPlayTypes(
            league_id='00',
            season='2025-26',
            season_type_all_star='Playoffs',
            player_or_team_abbreviation='T',
            type_grouping_nullable='offensive',
            play_type_nullable=play_type
        )

        df_play_type = data.get_data_frames()[0]

        df_play_type = df_play_type[[
            'TEAM_NAME',
            'POSS_PCT',
            'PPP',
            'PERCENTILE'
        ]]

        df_play_type = df_play_type.rename(columns={
            'POSS_PCT': f'{prefix}_FREQ',
            'PPP': f'{prefix}_PPP',
            'PERCENTILE': f'{prefix}_RK'
        })

        team_df = team_df.merge(
            df_play_type,
            on='TEAM_NAME',
            how='left'
        )

    freq_cols = [
        col for col in team_df.columns
        if col.endswith('_FREQ')
    ]

    team_df['TOT_FREQ'] = team_df[freq_cols].sum(axis=1)

    team_df['OTHER_FREQ'] = 1 - team_df['TOT_FREQ']

    return team_df

