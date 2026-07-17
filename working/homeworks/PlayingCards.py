#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import itertools as it
import random 

ranks = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
suits = ['♠', '♣', '♥', '♦']
# ~ suits = [chr(9824), chr(9827), chr(9829), chr(9830)]

cards = it.product(ranks, suits)

def shuffle(deck):
    """Return iterator over shuffled deck."""
    deck = list(deck)
    random.shuffle(deck)
    return iter(tuple(deck))
    
cards = shuffle(cards)

def cut(deck, n):
    """Return an iterator over a deck of cards cut at index `n`."""
    deck1, deck2 = it.tee(deck, 2)
    top = it.islice(deck1, n)
    bottom = it.islice(deck2, n, None)
    return it.chain(bottom, top)

cards = cut(cards, 26)

def deal(deck, num_hands=1, hand_size=5):
    iters = [iter(deck)] * hand_size
    return tuple(zip(*(tuple(it.islice(itr, num_hands)) for itr in iters)))
    
p1_hand, p2_hand, p3_hand = deal(cards, num_hands=3)

print("Hand 1")
for i in p1_hand: print("".join(i))
print("\nHand 2")
for i in p2_hand: print("".join(i))
print('\nHand 3')
for i in p3_hand: print("".join(i))

