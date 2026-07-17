#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'


import tcod as libtcod

def menu(con, header, options, width, screen_width, screen_height):
	if len(options) > 26: raise ValueError("Cannot have a menu with nore than 26 ")
	
	# calculate total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, screen_height, header)
	height = len(options) + header_height + 1
	
	# create an off-screen console that represents the menu's window
	window = libtcod.console_new(width - 1, height)
	window.draw_frame(0, 0, width - 1, height, header, False, libtcod.white,
					  libtcod.black, libtcod.BKGND_NONE)
	
	# print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE,
								  libtcod.LEFT, header)
	
	# print all the options
	y = header_height
	letter_index = ord('a')
	for options_text in options:
		text = "(" + chr(letter_index) + ') ' + options_text
		libtcod.console_print_ex(window, 2, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1
		
	# Blit the contents of 'window' to the root console
	x = int(screen_width / 2 - width / 2)
	y = int(screen_height / 2 - height / 2)
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
	
def menu_inventory(con, header, inventory, inventory_width, screen_width, screen_height):
	# show a menu with each item of the inventory as an option
	if len(inventory.items) == 0:
		options = ['Inventory is empty.']
	else:
		options = [item.name for item in inventory.items]
		
	menu(con, header, options, inventory_width, screen_width, screen_height)
	
def main_menu(con, background_image, screen_width, screen_height):
	libtcod.image_blit_2x(background_image, 0, 0, 0)
	
	libtcod.console_set_default_foreground(0, libtcod.light_yellow)
	libtcod.console_print_ex(0, int(screen_width / 2), int(screen_height / 2) - 4,
							 libtcod.BKGND_NONE, libtcod.CENTER,
							 'By Michael Rendier')
	
	menu(con, '', ['New game', 'Continue', 'Quit'], 24, screen_width, screen_height)
	
def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
	options = [f"Constitution ( +20 HP, from {player.fighter.max_hp})",
			   f"Strength ( +1 attack, from {player.fighter.power})",
			   f"Agility ( +1 defense, from {player.fighter.defense})"]
	
	menu(con, header, options, menu_width, screen_width, screen_height)
	
def character_screen(player, character_screen_width, character_screen_height, screen_width, screen_height):
	window = libtcod.console_new(character_screen_width, character_screen_height)
	window.draw_frame(0, 0, character_screen_width - 1, character_screen_height, 'Player Status', False, libtcod.white, libtcod.black, libtcod.BKGND_NONE)
	
	
	libtcod.console_set_default_foreground(window, libtcod.white)
	
	libtcod.console_print_rect_ex(window, 4, 1, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Character Information')
	libtcod.console_print_rect_ex(window, 2, 2, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, f"{'Level':<20s}" + f"{player.level.current_level:>5d}")
	libtcod.console_print_rect_ex(window, 2, 3, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, f"{'Experience:':<20s}" + f"{player.level.current_xp:>5d}")
	libtcod.console_print_rect_ex(window, 2, 4, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, f"{'Experience to Level:':<20s}" + f"{player.level.experience_to_next_level:>5d}")
	libtcod.console_print_rect_ex(window, 2, 6, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, f"{'Maximum HP:':<20s}" + f"{player.fighter.max_hp:>5d}")
	libtcod.console_print_rect_ex(window, 2, 7, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, f"{'Attack:':<20s}" + f"{player.fighter.power:>5d}")
	libtcod.console_print_rect_ex(window, 2, 8, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, f"{'Defense:':<20s}" + f"{player.fighter.defense:>5d}")
	
	x = screen_width // 2 - character_screen_width // 2
	y = screen_height // 2 - character_screen_height // 2
	libtcod.console_blit(window, 0, 0, character_screen_width, character_screen_height, 0, x, y, 1.0, 0.7)
def message_box(con, header, width, screen_width, screen_height):
	menu(con, header, [], width, screen_width, screen_height)
	