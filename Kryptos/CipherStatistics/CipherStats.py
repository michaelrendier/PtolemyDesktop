#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import string as st
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

# TODO:SETTINGS — hardcoded path, use PTOL_ROOT
file = open(PTOL_ROOT + '/Kryptos/TheCodeBook/data/words/clivebarker_weaveworld.txt', 'r')
text = file.read()


class CipherStats():

    def __init__(self, text):
        super().__init__()

        self.ascii_total = st.ascii_lowercase[-1:: -1]
        self.text = text

        self.count_these = [self.ascii_total, st.ascii_lowercase, st.ascii_uppercase, st.ascii_letters,
                            st.digits,
                            st.printable, st.hexdigits, st.octdigits, st.punctuation, st.whitespace]

        self.stats = []  # {char: self.text.count(char) for char in charList} for charlist in self.count_these]

        #         self.stats.append({char: self.text.lower().count(char) for char in st.ascii_lowercase})

        for charList in self.count_these:
            if self.count_these.index(charList) == 0:
                self.stats.append({char: self.text.lower().count(char) for char in charList})
            else:
                self.stats.append({char: self.text.count(char) for char in charList})

        for charList in self.stats:
            print("\n*****" + self.count_these[self.stats.index(charList)] + "*****\n")
            print(self.order_stats(charList))
            self.plot_bar_x(charList)

        #             for char in charList:
        #                 print(char, charList[char])

        print("Word Count (Whitespace)\n", self.word_count())
        print("Letter Count (len(text) - word_count)\n", self.letter_count())

    def word_count(self):
        return sum(self.stats[-1].values())

    def letter_count(self):
        return len(text) - self.word_count()

    def order_stats(self, charList):
        return {k: charList[k] for k in sorted(charList, key=charList.get, reverse=True)}

    def plot_bar_x(self, charList):
        # this is for plotting purpose
        # mpl.rcParams['grid.color'] = 'white'
        # mpl.rcParams['grid.linestyle'] = ':'
        # mpl.rcParams['figure.figsize'] = [8.5, 11]
        mpl.rcParams['font.size'] = 12
        mpl.rcParams['text.color'] = 'white'
        mpl.rcParams['legend.fontsize'] = 'large'
        mpl.rcParams['figure.titlesize'] = 'medium'
        mpl.rcParams['patch.force_edgecolor'] = True
        mpl.rcParams['axes.edgecolor'] = 'white'
        mpl.rcParams['axes.facecolor'] = 'black'
        mpl.rcParams['axes.labelcolor'] = 'white'
        mpl.rcParams['patch.facecolor'] = 'black'
        index = np.arange(len(charList))
        plt.figure(figsize=[8.5, 11.0], facecolor='black', dpi=150)
        plt.grid(color='white')
        plt.grid(linestyle=':')
        plt.xticks(color='white')
        plt.yticks(color='white')
        
        plt.barh(index,
                 [charList[i] for i in charList], color='cyan', edgecolor='blue')
        plt.ylabel('Character', fontsize=12)
        plt.xlabel('Occurances', fontsize=12)
        plt.yticks(index, charList, fontsize=12,
                   rotation=0)
        plt.title(f'Cipher {self.count_these[self.stats.index(charList)]} Stats Graph')
        plt.show()


TryThis = CipherStats(text)