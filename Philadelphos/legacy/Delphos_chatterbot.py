#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'


import sys
from Pharos.Philadelphos.Phila import bot
from chatterbot.trainers import UbuntuCorpusTrainer

trainer = UbuntuCorpusTrainer(bot)

trainer.train()


