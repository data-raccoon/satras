#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created 2017-02-10

@author: sporz
"""

import os
from collections import defaultdict

import pandas as pd

import trueskill

from wisentparser import Parser


# settings --------------------------------------------------------------------
trueskill = trueskill.TrueSkill(backend = "scipy", draw_probability = 0.10)
path_games  = 'game_scores.txt'
path_scores = "player_data.csv"
path_table  = "player_scores.txt"

# parse input to teams and ranks using wisent ---------------------------------
def print_tree(tree, terminals, indent=0):
    """Print a parse tree to stdout."""
    prefix = "    "*indent
    if tree[0] in terminals:
        print prefix + repr(tree)
    else:
        print prefix + unicode(tree[0])
        for x in tree[1:]:
            print_tree(x, terminals, indent+1)

def tokenize(str):
    from re import match

    res = []
    while str:
        if str[0].isspace():
            str = str[1:]
            continue

        m = match('[A-Za-z0-9]+', str)
        if m:
            res.append(('PLAYER', m.group(0)))
            str = str[m.end(0):]
            continue

        res.append((str[0],))
        str = str[1:]

    return res

def eval_tree(tree):
    if tree[0] == 'game':
        return eval_tree(tree[1])

    elif tree[0] == 'leftwins':
        left = eval_tree(tree[1])
        right = eval_tree(tree[3])
        res_teams = left["teams"] + right["teams"]
        res_ranks = left["ranks"] + [
            rank + max(left["ranks"]) for rank in right["ranks"]]
        return {"teams": res_teams, "ranks": res_ranks}

    elif tree[0] == 'draw':
        left = eval_tree(tree[1])
        right = eval_tree(tree[3])
        res_teams = left["teams"] + right["teams"]
        res_ranks = left["ranks"] + [
            rank + max(left["ranks"]) - 1 for rank in right["ranks"]]
        return {"teams": res_teams, "ranks": res_ranks}

    elif tree[0] == 'brackets':
        return eval_tree(tree[2])

    elif tree[0] == 'player_in_team':
        left = eval_tree(tree[1])
        right = eval_tree(tree[3])
        # combine individual players into team
        res_teams = [left["teams"][0] + right["teams"][0]]
        res_ranks = left["ranks"]
        return {"teams": res_teams, "ranks": res_ranks}

    elif tree[0] == 'PLAYER':
        return {"teams": [[tree[1]]], "ranks": [1]}


def parse_game(game_line):
    p = Parser()
    tokens = tokenize(game_line)
    tree = p.parse(tokens)
    return eval_tree(tree)


if __name__ == '__main__':
    with open(path_games, 'r') as fobj:
        lines = fobj.readlines()
    lines = [line for line in lines if (line != '\n' and line[0] != "#")]
    games = [parse_game(line) for line in lines]

    # TODO: keep history of player development

    players = defaultdict(trueskill.Rating)
    for game in games:
        players_flat = [name for team in game["teams"] for name in team]

        # exchange strings with names to corresponding player objects
        for team in game["teams"]:
            for idn, name in enumerate(team):
                team[idn] = players[name]

        # calc new skills
        result = trueskill.rate(game["teams"], ranks = game["ranks"])
        result_flat = [player for team in result for player in team]

        # update players with new skill
        for idx in range(len(result_flat)):
            players[players_flat[idx]] = result_flat[idx]

    # output ------------------------------------------------------------------
    player_dicts = [{"Name": player,
                     "mu": players[player].mu,
                     "sigma": players[player].sigma}
                    for player in players]
    player_df = pd.DataFrame(player_dicts)

    # add conservative skill estimation, 99% confidence
    player_df["TrueSkill"] = (
        player_df["mu"] - 2.575829303549 * player_df["sigma"])
    player_df.sort_values("TrueSkill", ascending = False, inplace = True)

    player_df.to_csv(path_scores, index = False)
    os.system("cat " + path_scores + " | column -s, -t > " + path_table)

