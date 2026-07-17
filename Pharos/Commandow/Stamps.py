#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'



shape_3x3 = [
	'tl', 'tc', 'tr',
	'cl', 'cc', 'cr',
	'bl', 'bc', 'br'
]

shape_2x3 = [
	'tl', 'tc', 'tr',
	'bl', 'bc', 'br'
]

shape_3x2 = [
	'tl', 'tr',
	'cl', 'cr',
	'bl', 'br'
]

shape_2x2 = [
	'tl', 'tr',
	'bl', 'br'
]

regular_h = ['─']
regular_v = ['│']
regular_shape = [
    ['┌', '┬', '┐'],
    ['├', '┼', '┤'],
    ['└', '┴', '┘']
]

bold_h = ['━']
bold_v = ['┃']
bold_shape = [
    ['┏', '┳', '┓'],
    ['┣', '╋', '┫'],
    ['┗', '┻', '┛']
]

mix_vert_h = ['─']
mix_vert_v = ['┃']
mix_vert_shape = [
    ['┎', '┰', '┒'],
    ['┠', '╂', '┨'],
    ['┖', '┸', '┚']
]

mix_hor_h = ['━']
mix_hor_v = ['│']
mix_hor_shape = [
    ['┍', '┯', '┑'],
    ['┝', '┿', '┥'],
    ['┕', '┷', '┙']
]

double_h = ['═']
double_v = ['║']
double_shape = [
    ['╔', '╦', '╗'],
    ['╠', '╬', '╣'],
    ['╚', '╩', '╝']
]

mix_double_vert_h = mdv_h = ['─']
mix_double_vert_v = mdv_v = ['║']
mix_double_vert_shape = mdv_shape = [
    ['╓', '╥', '╖'],
    ['╟', '╫', '╢'],
    ['╙', '╨', '╜']
]

mix_double_hor_h = mdh_h = ['═']
mix_double_hor_v = mdh_v = ['│']
mix_double_hor_shape = mdh_shape = [
    ['╒', '╤', '╕'],
    ['╞', '╪', '╡'],
    ['╘', '╧', '╛']
]

single_to_bold_h = stb_h = ['╼', '╾']
single_to_bold_v = stb_v = ['╽', '╿']
single_to_bold_shape = stb_shape = [
    ['╆', '╈', '╅'],
    ['╊', '╋', '╉'],
    ['╄', '╇', '╃']
]

single_to_bold_vert_corners = stbv_corners = [
    ['┢', '┪'],
    ['┡', '┩']
]

single_to_bold_hor_corners = stbh_corners = [
    ['┲', '┱'],
    ['┺', '┹']
]

single_to_bold_vert_shape = stbv_shape = [
    ['┟', '╁', '┧'],
    ['┞', '╀', '┦']
]

single_to_bold_hor_shape = stbh_shape = [
    ['┮', '┭'],
    ['┾', '┽'],
    ['┶', '┵']
]

regular_dash = [
    ['╌', '╎'],
    ['┄', '┆'],
    ['┈', '┊']
]

bold_dash = [
    ['╍', '╏'],
    ['┅', '┇'],
    ['┉', '┋']
]

curved_corners = [
    ['╭', '╮'],
    ['╰', '╯']
]

strikes = ['╱', '╲', '╳']

regular_cross = ['╴', '╵', '╶', '╷']

bold_cross = ['╸', '╹', '╺', '╻']

block_vert = ['█', '▉', '▊', '▋', '▌', '▍', '▎', '▏']

block_hor = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

top_bottom = ['▀', '▃']

left_right = ['▌', '▐']

shading = ['░', '▒', '▓']

cursor_top = ['▔']

cursor_right = ['▕']

quadrant = ['▖', '▗', '▘', '▝']

double_quadrant = ['▚', '▞', '▄', '▀', '▌', '▐']

triple_quadrant = ['▙', '▛', '▜', '▟']

shapes = [
    regular_h, regular_v, regular_shape,
    bold_h, bold_v, bold_shape,
    mix_vert_h, mix_vert_v, mix_vert_shape,
    mix_hor_h, mix_hor_v, mix_hor_shape,
    double_h, double_v, double_shape,
    mdv_h, mdv_v, mdv_shape,
    mdh_h, mdh_v, mdh_shape,
    stb_h, stb_v, stb_shape,
    stbv_corners, stbh_corners,
    stbv_shape, stbh_shape,
    regular_dash, bold_dash,
    curved_corners,
    strikes,
    regular_cross, bold_cross,
    block_vert, block_hor,
    top_bottom, left_right,
    shading,
    cursor_top, cursor_right,
    quadrant, double_quadrant,
    triple_quadrant
]

