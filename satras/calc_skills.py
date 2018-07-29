#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: sporz
"""

import re
from collections import defaultdict
from csv import QUOTE_ALL
from itertools import chain

import yaml
import numpy as np
import pandas as pd

import trueskill

"""
output: csv files for use in superset

separate by game-name, separate significantly different game modes

assume time if not given, split day (10 to 22) evenly accross games if multiple

for high level stats, for development of player scores
game_stats.csv
datetime, game-name, player, score, score_min, score_max, rank, has_won (rank == 1 & rank < max(rank)), has_lost (rank > 1)

carry over annotations to visualization
annotations.csv
datetime, game-name, annotation

"""


# settings --------------------------------------------------------------------
trueskill = trueskill.TrueSkill(backend = "scipy", draw_probability = 0.10)
path_games  = 'data/game_scores.yaml'
path_annotations = 'annotations.csv'
path_data = 'database.csv'


def main():
    with open(path_games, 'r') as fobj:
        try:
            games_dict = yaml.load(fobj)
        except yaml.YAMLError as exc:
            print(exc)

    # have one developing score per player and game-name
        # combine all games of each game_name
        # calculate scores for each game_name separately
        # calculate scores one game at a time

    games_df = pd.DataFrame(games_dict)
    games_df.sort_values('datetime', inplace=True)
    games_df.reset_index(drop=True, inplace=True)
    games_flat = games_df.apply(lambda x: pd.Series(x['scores']), axis=1).stack().reset_index(level=1, drop=True)
    games_flat.name = 'scores'
    games_df = games_df.drop('scores', axis=1).join(games_flat)
    # prepare a different time for each game for multiple games
    games_df.reset_index(drop=True, inplace=True)
    
    def spreaddatetimes(datetimes):
        base = datetimes.values[0]
        base_next = base.astype('datetime64[D]') + np.timedelta64(1, 'D')
        delta = (base_next - base) / len(datetimes)
        deltas = np.array([delta * i for i in range(len(datetimes))])
        return datetimes + deltas      
    games_df['datetime'] = games_df.groupby(['game_name', 'datetime'], group_keys=False).datetime.apply(spreaddatetimes)

    games_df[['datetime','game_name', 'annotation']].to_csv(path_annotations, index=False, quoting=QUOTE_ALL)
    games_df.drop(columns='annotation', inplace=True)

    def signs2ranks(signs):
        ranks = [1]
        for idx, sign in enumerate(signs):
            if sign == "=":
                ranks.append(ranks[idx])
            elif sign == ">":
                ranks.append(ranks[idx] + 1)
        return ranks

    def calc_metrics(scores):
        scores_current = defaultdict(trueskill.Rating)
        scores_history = {"player": [],
                          "score": [],
                          "score_sigma": [],
                          "pos": [],
                          "has_won": []}
        index_history = []

        for ids, score in enumerate(scores.values):
            parent_index = scores.index[ids]
            score = score.replace(" ", "")
            teams = re.split("=|>", score)
            teams_players = [team.split(",") for team in teams]
            ranks = signs2ranks(re.sub("[^=>]", "", score))
            teams = list(chain.from_iterable(([part.split(">") for part in game.split(sep='=')])))
            players_flat = [name for team in teams_players for name in team]
            ranks_flat = []
            for idt, team in enumerate(teams_players):
                for name in team:
                    ranks_flat.append(ranks[idt])
            # we want to operate with score objects, not player names
            for team in teams_players:
                for idp, name in enumerate(team):
                    team[idp] = scores_current[name]
            result = trueskill.rate(teams_players, ranks = ranks)
            result_flat = [score for team in result for score in team]
            
            for idx in range(len(result_flat)):
                scores_current[players_flat[idx]] = result_flat[idx]
                scores_history["player"].append(players_flat[idx])
                scores_history["score"].append(result_flat[idx].mu)
                scores_history["score_sigma"].append(result_flat[idx].sigma)
                scores_history["pos"].append(ranks_flat[idx])
                scores_history["has_won"].append((ranks_flat[idx] == 1) & (max(ranks_flat) > 1))
                index_history.append(parent_index)
        
        return pd.DataFrame(scores_history, index=index_history)
    metrics_df = games_df.groupby(['game_name', 'datetime'], group_keys=False).scores.apply(calc_metrics).reset_index(level=1, drop=True).reset_index(level=0, drop=True)
    new_df = games_df.drop('scores', axis=1).join(metrics_df)
    
    new_df['score_lower'] = new_df.score - new_df.score_sigma
    new_df['score_higher'] = new_df.score + new_df.score_sigma
    new_df['has_lost'] = new_df.pos > 1

    new_df.to_csv(path_data, index=False, quoting=QUOTE_ALL)

if __name__ == '__main__':
    main()
