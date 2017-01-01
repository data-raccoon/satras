# -*- coding: utf-8 -*-
"""
Created on Su Jan  1 10:31:15 2017

@author: sporz
"""

import json
import os
from itertools import compress
from collections import defaultdict

import pandas as pd

import trueskill
trueskill = trueskill.TrueSkill(backend = "scipy", draw_probability = 0.01)

path_games = "mtg_games.json"
path_scores = "mtg_scores.csv"
path_table = "mtg_scores.txt"

# remove comments before parsing
data_raw = open(path_games).readlines()
fil = [ mystr.find("#") != 4 for mystr in data_raw ]
data_json = list(compress(data_raw, fil))
data = json.loads("".join(data_json))

# prep
players = defaultdict(trueskill.Rating)

# calc latest skill
for game in data:
    players_flat = [item for sublist in game for item in sublist]    

    # exchange string names to players
    for team in game:
        for idn, name in enumerate(team):
            team[idn] = players[name]

    # calc new skills  
    result = trueskill.rate(game, ranks = range(len(game)))
    result_flat = [item for sublist in result for item in sublist]
    
    # update players with new skill
    for idx in range(len(result_flat)):
        players[players_flat[idx]] = result_flat[idx]

# output
player_dicts = [{"Name": player, 
                 "mu": players[player].mu, 
                 "sigma": players[player].sigma} 
                for player in players]
player_df = pd.DataFrame(player_dicts)

# add conservative skill estimation, 99% confidence
player_df["TrueSkill"] = player_df["mu"] - 2.575829303549 * player_df["sigma"]
player_df.sort("TrueSkill", ascending = False, inplace = True)

player_df.to_csv(path_scores, index = False)

os.system("cat " + path_scores + " | column -s, -t > " + path_table)

