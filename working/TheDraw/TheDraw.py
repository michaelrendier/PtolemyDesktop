#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'


from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import *

from PIL import Image, ImageDraw, ImageFont

walls = [[i, chr(i)] for i in range(9472, 9632)]

# I Ching
iching = [[i, chr(i)] for i in range(9866, 9872)]
for i in range(9775, 9784): iching.append([i, chr(i)])
for i in range(119552, 119639): iching.append([i, chr(i)])

# White Circle Numbers
circlenumberwhite = [[i, chr(i)] for i in range(9312, 9331)]
circleletterupperwhite = [[i, chr(i)] for i in range(9398, 9398 + 26)]
circleletterlowerwhite = [[i, chr(i)] for i in range(9398 + 26, 9450)]

# Chess
chess = [[i, chr(i)] for i in range(9812, 9824)]
chesswhite = [[i, chr(i)] for i in range(9812, 9812 + 6)]
chessblack = [[i, chr(i)] for i in range(9812 + 6, 9824)]

# Playing Card Suits
cardsuits = [[i, chr(i)] for i in range(9824, 9831)]
cardsuitswhite = [[9825, chr(9825)], [9826, chr(9826)], [9828, chr(9828)], [9831, chr(9831)]]
cardsuitsblack = [[9824, chr(9824)], [9827, chr(9827)], [9829, chr(9829)], [9830, chr(9830)]]

# Music
music = [[i, chr(i)] for i in range(9832, 9840)]
for i in range(119040, 119273): music.append([i, chr(i)])

# Black Circle Numbers
circlenumberblack = [[i, chr(i)] for i in range(10102, 10112)]
for i in range(9451, 9461): circlenumberwhite.append([i, chr(i)])


def renderImage(text, x=25, y=48, fontsize=41):
	image = Image.new('RGB', (x, y))
	draw = ImageDraw.Draw(image)
	draw.text((0, 0), text, font=ImageFont.truetype('DejaVuSans.ttf', fontsize))
	image.save(str(ord(text)) + '.jpg')
	image.close()
	
make viewer window