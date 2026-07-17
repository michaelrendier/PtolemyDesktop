#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
__author__ = 'rendier'


# Imports
from dataclasses import dataclass, field
from typing import Any, List
from math import asin, cos, radians, sin, sqrt
from random import sample



RANKS = '2 3 4 5 6 7 8 9 10 J Q K A'.split()
SUITS = '♣ ♢ ♡ ♠'.split()

def make_french_deck():
    return [Card(r, s) for s in SUITS for r in RANKS]

@dataclass(order=True)
class Card:
    sort_index: int = field(init=False, repr=False)
    rank: str
    suit: str

    def __post_init__(self):
        self.sort_index = (RANKS.index(self.rank) * len(SUITS) + SUITS.index(self.suit))
    
    def __str__(self):
        return f'{self.suit}{self.rank}'
    
@dataclass
class Deck:
    cards: List[Card] = field(default_factory=make_french_deck)

    def __repr__(self):
        cards = ', '.join(f'{c!s}' for c in self.cards)
        return f'{self.__class__.__name__}({cards})'
    


    

@dataclass(frozen=True)
class Position:
    name: str
    lon: float = field(default=0.0, metadata={'unit': 'degrees'})
    lat: float = field(default=0.0, metadata={'unit': 'degrees'})
    
    def distance_to(self, other):
        r = 6371 # Radius of earth in km
        lam1, lam2 = radians(self.lon), radians(other.lon)
        phi1, phi2 = radians(self.lat), radians(other.lat)
        h = (sin((phi2 - phi1)/2)**2 + cos(phi1) * cos(phi2) * sin((lam2 - lam1)/2)**2)
        return 2 * r * asin(sqrt(h))
    
@dataclass
class Capital(Position):
    country: str