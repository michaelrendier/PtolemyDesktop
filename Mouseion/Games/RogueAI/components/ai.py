#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import tcod as libtcod

from random import randint

from game_messages import Message


class BasicMonster:
	
	def __init__(self):
		pass
	
	def __str__(self):
		return "FIX THIS BASIC MONSTER STRING"
	
	def __repr__(self):
		return f"{self.__class__.__name__}()"
	
	
	def take_turn(self, target, fov_map, game_map, entities):
		# print('The ' + self.owner.name + ' wonders when it will get to move.')
		# write_string(self.con, 0, 49, 'h', f"The {self.owner.name} wonders when it will get to move", libtcod.red)
		results = []
		
		monster = self.owner
		# print("MONSTER OWNER", repr(self.owner))
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
			
			if monster.distance_to(target) >= 2:
				monster.move_astar(target, entities, game_map)
				# monster.move_towards(target.x, target.y, game_map, entities)
				
			elif target.fighter.hp > 0:
				# write_string(self.con, 0, 49, 'h', f"The {monster.name} insults you!  Your ego is damaged!", libtcod.red)
				# print(f"The {monster.name} insults you!  Your ego is damaged!")
				# monster.fighter.attack(target)
				attack_results = monster.fighter.attack(target)
				results.extend(attack_results)
				
		return results
	
class ConfusedMonster:
	
	def __init__(self, previous_ai, number_of_turns=10):
		self.previous_ai = previous_ai
		self.number_of_turns = number_of_turns
		
	def __str__(self):
		return "FIX THIS CONFUSED MONSTER STRING"
	
	def __repr__(self):
		return f"{self.__class__.__name__}(previous_ai={repr(self.previous_ai)}, number_of_turns={self.number_of_turns})"
		
	def take_turn(self, target, fov_map, game_map, entities):
		results = []
		
		if self.number_of_turns > 0:
			random_x = self.owner.x + randint(0, 2) - 1
			random_y = self.owner.y + randint(0, 2) - 1
			
			if random_x != self.owner.x and random_y != self.owner.y:
				self.owner.move_towards(random_x, random_y, game_map, entities)
				
			self.number_of_turns -= 1
		else:
			self.owner.ai = self.previous_ai
			results.append({'message': Message(f"The {self.owner.name} is no longer confused!", libtcod.red)})
			
		return results