#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created 2017-02-10

@author: sporz
"""

import os
import re
from collections import defaultdict

import pandas as pd
import dash_core_components as dcc
import dash_html_components as dhtml

import dash
import trueskill

from wisentparser import Parser


# settings --------------------------------------------------------------------
trueskill = trueskill.TrueSkill(backend = "scipy", draw_probability = 0.10)
path_games  = 'game_scores.txt'
path_scores = "player_data.csv"
path_table  = "player_scores.txt"

# parse input to teams and ranks using wisent ---------------------------------
def print_tree(tree, terminals, indent=0):
    """Print a parse tree to stdout, for debugging purposes only."""
    prefix = "    "*indent
    if tree[0] in terminals:
        print prefix + repr(tree)
    else:
        print prefix + unicode(tree[0])
        for x in tree[1:]:
            print_tree(x, terminals, indent+1)

def tokenize(line):
    result = []
    # tokenize elements one by one
    while line:
        # Match regular expression for free form tokens (PLAYER)
        matches = re.match('[^>=,]+', line)
        if matches:
            result.append(('PLAYER', matches.group(0).strip()))
            line = line[matches.end(0):]
            continue

        # Keep 1-char tokens ">", "=", "," and ":"
        # parsing will fail later if there are other 1-char tokens
        result.append((line[0],))
        line = line[1:]

    return result

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

    elif tree[0] == 'player_in_team':
        left = eval_tree(tree[1])
        right = eval_tree(tree[3])
        # combine individual players into team
        res_teams = [left["teams"][0] + right["teams"][0]]
        res_ranks = left["ranks"]
        return {"teams": res_teams, "ranks": res_ranks}

    elif tree[0] == 'PLAYER':
        return {"teams": [[tree[1]]], "ranks": [1]}
    
def game_line2game_tree(game_line):
    p = Parser()
    tokens = tokenize(game_line)
    return p.parse(tokens)
    
def remove_unused(lines):
    # comments and empty lines don't need parsing
    return [line.strip() for line in lines if (line != '\n' and line[0] != "#")]
    
def structure_games(lines):
    match_groups = [defaultdict(list)]
    lastwasgame = False
    for line in lines:
        keyvalue = line.split(":")
        if len(keyvalue) == 2:
            if lastwasgame: # here starts the metadata new group of matches
                match_groups.append(defaultdict(list))
            match_groups[len(match_groups) - 1][keyvalue[0].strip()] = (
                    keyvalue[1].strip())
            lastwasgame = False
        else: # not a key value pair but a game
            game_tree = game_line2game_tree(line)
            match_groups[len(match_groups) - 1]["_games"].append(game_tree)
            lastwasgame = True
    return match_groups

def flatten_structure(match_groups):
    match_groups = pd.DataFrame(match_groups)
    games_df = match_groups.apply(
            lambda x: pd.Series(x['_games']),
            axis=1).stack().reset_index(level=1, drop=True)
    games_df.name = "_games"
    games_df = match_groups.drop('_games', axis=1).join(games_df)
    return games_df    


app = dash.Dash()

#app.layout = TODO

# tab: player comparison, final
# tab: player comparison, development
# control: choose game (mendatory)
# control: choose date
# control: choose custom variable content
# vis: colorize influencing factors



def main():
    with open(path_games, 'r') as fobj:
        lines = fobj.readlines()
    lines = remove_unused(lines)
    match_groups = structure_games(lines)
    games_df = flatten_structure(match_groups)
    
    # TODO parse games after user we know what to show (UI)
    app.run_server(debug=True)    



    # old stuff --------------------------------------------------------------

    # TODO parse from new data structure
    games = [parse_game_line(game_line) for game_line in lines]

    # TODO: keep history of player development

    players = defaultdict(trueskill.Rating)
    players_history = []
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
            players_history.append((players_flat[idx], result_flat[idx]))

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

if __name__ == '__main__':
    main()

