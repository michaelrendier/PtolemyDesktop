#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import os
import shelve

def save_game(player, entities, game_map, message_log, game_state, dungeon_levels):
    with shelve.open('savegame.dat', 'n') as data_file:
        data_file['player_index'] = entities.index(player)
        data_file['entities'] = entities
        data_file['game_map'] = game_map
        data_file['message_log'] = message_log
        data_file['game_state'] = game_state
        data_file['dungeon_levels'] = dungeon_levels
		
def load_game():
    if not os.path.isfile('savegame.dat'):
        raise FileNotFoundError

    with shelve.open('savegame.dat', 'r') as data_file:
        player_index = data_file['player_index']
        entities = data_file['entities']
        game_map = data_file['game_map']
        message_log = data_file['message_log']
        game_state = data_file['game_state']
        dungeon_levels = data_file['dungeon_levels']

    player = entities[player_index]

    return player, entities, game_map, message_log, game_state, dungeon_levels