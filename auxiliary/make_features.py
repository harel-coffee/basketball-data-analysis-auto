# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 17:13:33 2018

@author: Georgios
"""
import numpy as np
import pandas as pd
from auxiliary.make_standings import make_standings


def find_form(df, game_round, team_id):
    form = np.nan
    team_df = df[((df['Home Team ID'] == team_id) | 
                 (df['Away Team ID'] == team_id)) &
                 ((df['Game Round'] < game_round) & (df['Game Round'] >= game_round - 5))]
    n_games = team_df.shape[0]
    
    if n_games == 0:
        return np.nan

    home_games = team_df['Home Team ID'] == team_id
    away_games = team_df['Away Team ID'] == team_id
    wins = np.sum(team_df['Home Score'][home_games] > team_df['Away Score'][home_games])
    wins += np.sum(team_df['Home Score'][away_games] < team_df['Away Score'][away_games])

    form = wins / n_games
    return form


def make_features_from_df(data, standings):
    '''game-level features:
        standing of home team
        standing of away team
        avg scoring points of home team
        avg scoring points of away team
        avg against points of home team
        avg against points of away team
        wins to losses of home team
        wins to losses of away team
        form of home team (wins over the last 5 games)
        form of away team (wins over the last 5 games)
    '''
    stands = standings.copy()
    stands['Round'] += 1
    new_df = data.merge(stands, how='left', 
                        left_on=['Round', 'Home Team'],
                        right_on=['Round', 'Club Name'])
    new_df = new_df.merge(stands, how='left',
                          left_on=['Round', 'Away Team'],
                          right_on=['Round', 'Club Name'])

    tmp = new_df[['Offence_x', 'Offence_y', 'Defence_x', 'Defence_y']].values
    tmp /= np.repeat((new_df['Round'].values - 1)[:, np.newaxis], tmp.shape[1], axis=1)

    new_df[['Offence_x', 'Offence_y', 'Defence_x', 'Defence_y']] = tmp

#    tmp = new_df[['Wins_x', 'Losses_x']].values
#    new_df['Wins_to_Losses_x'] = tmp[:, 0] / tmp[:, 1]
#    tmp = new_df[['Wins_y', 'Losses_y']].values
#    new_df['Wins_to_Losses_y'] = tmp[:, 0] / tmp[:, 1]
    
    forms_home = np.zeros(new_df.shape[0])
    forms_away = np.zeros(new_df.shape[0])
    for index, row in new_df.iterrows():
        g_round = row['Round']
        home_team = row['Home Team']
        away_team = row['Away Team']
        form_home = 0.
        form_away = 0.
        if g_round > 6:
            form_home = standings[(standings['Club Name'] == home_team) &
                                  (standings['Round'] == g_round-1)]['Wins'].values[0] -\
                        standings[(standings['Club Name'] == home_team) &
                                  (standings['Round'] == g_round-6)]['Wins'].values[0]
    
            form_away = standings[(standings['Club Name'] == away_team) &
                                  (standings['Round'] == g_round-1)]['Wins'].values[0] -\
                        standings[(standings['Club Name'] == away_team) &
                                  (standings['Round'] == g_round-6)]['Wins'].values[0]
        elif g_round > 1:
            form_home = standings[(standings['Club Name'] == home_team) &
                                   (standings['Round'] == g_round-1)]['Wins'].values[0]
            form_away = standings[(standings['Club Name'] == away_team) &
                                   (standings['Round'] == g_round-1)]['Wins'].values[0]
        print(g_round, form_home, form_away)
        forms_home[index] = form_home
        forms_away[index] = form_away

    new_df['form_x'] = forms_home
    new_df['form_y'] = forms_away

    new_df = new_df[['Round', 'Home Team', 'Away Team',
                     'Position_x', 'Position_y', 
                     'Offence_x', 'Offence_y',
                     'Defence_x', 'Defence_y',
#                     'Wins_to_Losses_x', 'Wins_to_Losses_y',
                     'form_x', 'form_y']]
    
    return new_df

def make_features(df, standings=None):
    '''game-level features:
        standing of home team
        standing of away team
        form of home team (wins over the last 5 games)
        form of away team (wins over the last 5 games)
        avg scoring points of home team
        avg scoring points of away team
        avg against points of home team
        avg against points of away team
    '''
    teams = np.unique(df['Home Team ID'].values)

    if standings is None:
        standings = {}
        for i in range(1, 31):
            standings[i] = make_standings(df, i)

    f4 = [3514, 3501, 3540, 6663]
    top8 = [3508, 3515, 3553]

    n_features = 14 + 32
    features = np.zeros((df.shape[0], n_features))
    for row in range(df.shape[0]):

        game_round = df['Game Round'].iloc[row]
        home_team = df['Home Team ID'].iloc[row]
        away_team = df['Away Team ID'].iloc[row]

        if game_round == 1:
            features[row, :] = -1 * np.ones(n_features)
            continue

        standing = standings[game_round-1]

        standing_home_team = standing[standing['Team ID'] == home_team].index[0] + 1
        standing_away_team = standing[standing['Team ID'] == away_team].index[0] + 1

        form_home_team = find_form(df, game_round, home_team)
        form_away_team = find_form(df, game_round, away_team)

        avg_attack_home_team = standing[standing['Team ID'] == home_team]['Score+'] / game_round
        avg_attack_away_team = standing[standing['Team ID'] == away_team]['Score+'] / game_round

        avg_defence_home_team = standing[standing['Team ID'] == home_team]['Score-'] / game_round
        avg_defence_away_team = standing[standing['Team ID'] == away_team]['Score-'] / game_round
        home_team_inf4 = 1 if home_team in f4 else 0
        home_team_intop8 = 1 if home_team in top8 else 0
        home_team_inrest = 0 if (home_team_inf4 or home_team_intop8) else 1
        away_team_inf4 = 1 if away_team in f4 else 0
        away_team_intop8 = 1 if away_team in top8 else 0
        away_team_inrest = 0 if (away_team_inf4 or away_team_intop8) else 1

        features[row, 0] = standing_home_team
        features[row, 1] = standing_away_team
        features[row, 2] = form_home_team
        features[row, 3] = form_away_team
        features[row, 4] = avg_attack_home_team
        features[row, 5] = avg_attack_away_team
        features[row, 6] = avg_defence_home_team
        features[row, 7] = avg_defence_away_team
        features[row, 8] = home_team_inf4
        features[row, 9] = home_team_intop8
        features[row, 10] = home_team_inrest
        features[row, 11] = away_team_inf4
        features[row, 12] = away_team_intop8
        features[row, 13] = away_team_inrest
        features[row, 14:30] = (teams == home_team).astype(int)
        features[row, 30:] = (teams == away_team).astype(int)

        headers = ['standing-home-team', 'standing-away-team',
                   'form-home-team', 'form-away-team',
                   'avg-attack-home-team', 'avg-attack-away-team',
                   'avg-defence-home-team', 'avg-defence-away-team',
                   'home-team-f4', 'home-team-top8', 'home-team-rest',
                   'away-team-f4', 'away-team-top8', 'away-team-rest']
        headers.extend([str(t)+'-home' for t in teams])
        headers.extend([str(t)+'-away' for t in teams])

    df = pd.DataFrame(data=features, columns=headers)
#    df = df.astype(dtype={'standing-home-team': int, 'standing-away-team': int,
#               'form-home-team': float, 'form-away-team': float,
#               'avg-attack-home-team': float, 'avg-attack-away-team': float,
#               'avg-defence-home-team': float, 'avg-defence-away-team': float,
#               'home-team-f4': int, 'home-team-top8': int, 'home-team-rest': int,
#               'away-team-f4': int, 'away-team-top8': int, 'away-team-rest': int})
    headers_dict = dict(zip(headers, [int]*features.shape[1]))
    headers_dict['form-home-team'] = float
    headers_dict['form-away-team'] = float
    headers_dict['avg-attack-home-team'] = float
    headers_dict['avg-attack-away-team'] = float
    headers_dict['avg-defence-home-team'] = float
    headers_dict['avg-defence-away-team'] = float
    df = df.astype(dtype=headers_dict)
    return df


def make_team_features(game_feat_df):
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    home_game = np.ones(game_feat_df.shape[0], dtype=int)
    away_game = np.zeros(game_feat_df.shape[0], dtype=int)
    for u in game_feat_df.keys():
        if 'home-team' in u:
            df1[u.replace('home-team', '')] = game_feat_df[u]
        elif 'away-team' in u:
            df2[u.replace('away-team', '')] = game_feat_df[u]
        else:
            print('Warning: Something went wrong')

    features_df = pd.concat([df1, df2])
    home_games = np.concatenate((home_game, away_game), axis=0)
    features_df['Home Team'] = home_games
    return features_df