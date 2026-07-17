#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from enum import Enum


class GameStates(Enum):
	PLAYERS_TURN = 1
	ENEMY_TURN = 2
	PLAYER_DEAD = 3
	SHOW_INVENTORY = 4
	DROP_INVENTORY = 5
	TARGETING = 6
	LEVEL_UP = 7
	CHARACTER_SCREEN = 8
	
	# def __str___(self):
	# 	return "FIX THIS GAME STATE STRING"

	def __repr__(self):
		return f"{self.__class__.__name__}.{self.value}"