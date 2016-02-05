# -*- coding: utf-8 -*-
"""
Created on Fr Jan  8 14:11:30 2016

@author: sporz
"""

from collections import defaultdict

import pandas as pd


import trueskill
trueskill = trueskill.TrueSkill(backend = "scipy", draw_probability = 0.01)


# settings
path_ranks = "brawl_ranks.csv"
path_out = "brawl_trueskill.csv"

data = pd.read_csv(path_ranks)

players = defaultdict(trueskill.Rating)

gby = data.groupby("Game.number")

game_numbers = gby.groups.keys()
game_numbers.sort()

for idg in game_numbers:
    if idg <= 0:
        continue
    data_game = gby.get_group(idg)
    playernames_game = [name for name in data_game["Player"].values]   
    players_game = [players[name] for name in data_game["Player"].values]

    # decide if we need team or solo data
    if pd.isnull(data_game["Team.Rank"]).any():
        teams_list = [[player] for player in players_game]
        names_list_flat = playernames_game
        ranks_list = data_game["Rank"].values       
    else:
        ranks_lookup = dict(zip(data_game["Team"].values, data_game["Team.Rank"].values))
        teams_dict = defaultdict(list)
        teams_playernames_dict = defaultdict(list)
       
        for player_id, team_name in enumerate(data_game["Team"].values):
            teams_dict[team_name].append(players_game[player_id])
            teams_playernames_dict[team_name].append(playernames_game[player_id])

        teams_list = [teams_dict[team_name] for team_name in teams_dict]
        names_list = [teams_playernames_dict[team_name] for team_name in teams_dict]
        ranks_list = [ranks_lookup[team_name] for team_name in teams_dict]

        names_list_flat = [item for sublist in names_list for item in sublist]
        
    result = trueskill.rate(teams_list, ranks = ranks_list)
    result_flat = [item for sublist in result for item in sublist]
        
    for idx in range(len(result_flat)):
        players[names_list_flat[idx]] = result_flat[idx]

    
player_dicts = [{"Name": player, 
                 "mu": players[player].mu, 
                 "sigma": players[player].sigma} 
                for player in players]

player_df = pd.DataFrame(player_dicts)

# add conservative skill estimation, 99% confidence
player_df["TrueSkill"] = player_df["mu"] - 2.575829303549 * player_df["sigma"]
player_df.sort("TrueSkill", ascending = False, inplace = True)

player_df.to_csv(path_out, index = False)
