#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import tcod as libtcod

from game_messages import Message

class Fighter:
	
	def __init__(self, hp, defense, power, xp=0):
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power
		self.xp = xp
		
	def __str__(self):
		return self.__repr__()
	
	def __repr__(self):
		return f"{self.__class__.__name__}(hp={self.hp}, defense={self.defense}, power={self.power}, xp={self.xp})"
	
	def take_damage(self, amount):
		results = []
		
		self.hp -= amount
		
		if self.hp <= 0:
			results.append({'dead': self.owner, 'xp': self.xp})
			
		return results
	
	def heal(self, amount):
		self.hp += amount
		
		if self.hp > self.max_hp:
			self.hp = self.max_hp
		
	def attack(self, target):
		results = []
		
		damage = self.power - target.fighter.defense
		
		if damage > 0:
			results.append({'message': Message(f"{self.owner.name.capitalize()} attacks {target.name} for {str(damage)} hit points.", libtcod.white)})
			results.extend(target.fighter.take_damage(damage))
		else:
			results.append({'message': Message(f"{self.owner.name.capitalize()} attacks {target.name} but does no damage.", libtcod.white)})
			
		return results