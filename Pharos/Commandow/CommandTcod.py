#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'



import tcod as libtcod

def main():
	
	screen_width = 80
	screen_height = 50
	
	player_x = int(screen_width / 2)
	player_y = int(screen_height / 2)
	
 # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
	libtcod.console_set_custom_font(PTOL_ROOT + '/Pharos/Commandow/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
	
	libtcod.console_init_root(screen_width, screen_height, 'libtcod tutorial revised', False)
	
	while not libtcod.console_is_window_closed():
		libtcod.console_set_default_foreground(0, libtcod.white)
		libtcod.console_put_char(0, player_x, player_y, '@', libtcod.BKGND_NONE)
		libtcod.console_flush()
		
		key = libtcod.console_check_for_keypress()
		
		if key.vk == libtcod.KEY_ESCAPE:
			return True
		
		
if __name__ == 'main':
	main()