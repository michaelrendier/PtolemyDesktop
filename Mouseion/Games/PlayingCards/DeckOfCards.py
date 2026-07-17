#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from itertools import product
from random import shuffle
from getch import getch
import os
import curses



uniDeck = ['🂱', '🂲', '🂳', '🂴', '🂵', '🂶', '🂷', '🂸', '🂹', '🂺', '🂻', '🂼', '🂽', '🂾',
           '🂡', '🂢', '🂣', '🂤', '🂥', '🂦', '🂧', '🂨', '🂩', '🂪', '🂫', '🂬', '🂭', '🂮',
           '🃁', '🃂', '🃃', '🃄', '🃅', '🃆', '🃇', '🃈', '🃉', '🃊', '🃋', '🃌', '🃍', '🃎',
           '🃑', '🃒', '🃓', '🃔', '🃕', '🃖', '🃗', '🃘', '🃙', '🃚', '🃛', '🃜', '🃝', '🃞']

def uni_deal(self):

    pass


class Card:

    def __init__(self, suit, pip, pipRank=None, suitRank=None, suitHigh=False):
        # print("<CARD>")
        self.suits = {"Clubs": '♣', "Hearts": '♥', "Diamonds": '♦', "Spades": '♠',
                      '♣': "Clubs", '♥': "Hearts", '♦': "Diamonds", '♠': "Spades"}
        self.royalty = {"A": "Ace", "J": "Jack", "Q": "Queen", "K": "King",
                        "Ace": "A", "Jack": "J", "Queen": "Q", "King": "K"}

        self.suit = self.suits[suit.capitalize()]

        if pip.lower() == 'back':
            self.pip = 'back'
        else:
            self.pip = self.royalty[str(pip)] if str(pip) in self.royalty else str(pip)

        if pipRank:
            self.pipRank = pipRank
        else:
            self.pipRank = ['2', '3', '4', '5', '6', '7', '8', '9', '10', "J", "Q", "K", "A"]  # Poker rules

        if suitRank:
            self.suitRank = suitRank
        else:
            self.suitRank = ['Clubs', 'Diamonds', 'Hearts', 'Spades']

        self.suitHigh = suitHigh

    def __str__(self):
        return self.__repr__()  # f"{self.pip} of {self.suits[self.suit]}"

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.suits[self.suit].capitalize()}', '{self.royalty[self.pip] if self.pip in self.royalty else self.pip}')"  # {self.__str__()} {self.face()}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        if self.suitHigh:
            return self.rank()[2] == other.rank()[2]
        else:
            return self.rank()[0] == other.rank()[0]

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        if self.suitHigh:
            return self.rank()[2] < other.rank()[2]
        else:
            return self.rank()[0] < other.rank()[0]

    def __gt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        if self.suitHigh:
            return self.rank()[2] > other.rank()[2]
        else:
            return self.rank()[0] > other.rank()[0]

    def rank(self):
        if self.pip == 'back':
            self.pipValue = 'back'
        else:
            self.pipValue = self.pipRank.index(self.royalty[self.pip] if self.pip in self.royalty else self.pip)
        self.suitValue = self.suitRank.index(self.suits[self.suit])
        self.finalRank = (self.pipValue + 1) + (self.suitValue * 13)

        if self.pipValue == 'back':
            return (0, 0, 0)
        else:
            return (self.pipValue, self.suitValue, self.finalRank)

    def face(self):
        if self.pip == 'back':
            self.facePip = 'back'
        else:
            self.facePip = self.royalty[self.pip] if self.pip in self.royalty else self.pip

        if self.facePip == 'back':
            return "[ ♠ ]"
        else:
            return f"[{self.facePip} {self.suit}]" if not self.pip == '10' else f"[{self.facePip}{self.suit}]"

class Deck:

    def __init__(self, size=52):
        # print("<DECK>")
        # SUITS = ["\u2663", "\u2665", "\u2666", "\u2660"]
        self.suitsList = ['Clubs', 'Spades', 'Hearts', 'Diamonds']
        self.pipsList = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"] # Poker rules
        self.size = size
        self.deck = self.new_deck()
        self.shuffle_deck()

    def __len__(self):
        return len(self.deck)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str([i.__repr__() for i in self.deck])

    def new_deck(self):# fix for different size and composition decks as per game (Spades A High, Joker High) todo
        cards = list(product(self.pipsList, self.suitsList))
        deck = [Card(card[1], card[0]) for card in cards]
        return deck

    def shuffle_deck(self):
        # print("--> Deck Shuffled\n" + "*" * 35 + "\n")
        shuffle(self.deck)

    def show_deck(self):
        return "".join([self.deck[i].face() for i in range(len(self.deck))])

    def deal_cards(self, players, handSize):
        p = len(players)
        dealSize = p * handSize
        for i in range(dealSize):
            players[i%p].hand.append(self.deck.pop(0))

        pass

class Table:

    def __init__(self, players, game, deck, houseRules=None, seats=None, pot=None, discard=None, flop=None, playerTurn=None):# Spades requires partner seating todo
        # print("<TABLE>")

        self.players = players
        # print(self.players[0])

        if isinstance(game, Game):
            self.game = game
        else:
            raise TypeError(f"{game} is not a Game() Class")

        if isinstance(deck, Deck):
            self.deck = deck
        else:
            raise TypeError("The Deck is not a Deck() Class")

        self.houseRules = self.game.houseRules

        # if 'partners' in self.houseRules and len(self.players) % 2 == 0:# partner seating function for 4 players ie: Spades todo
        #     self.seats = [self.players[0], self.players[2], self.players[1], self.players[3]]
        self.seats = []
        self.pot = 0
        self.discard = [Card('spades', 'back')]
        self.flop = []
        self.books = []


        self.playerTurn = 0

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.__class__.__name__}(players={self.players},\n\ngame={self.game},\n\ndeck={self.deck},\n\n" \
               f"houseRules={self.houseRules},\n\nseats={self.seats},\n\npot={self.pot},\n\ndiscard={self.discard},\n\n" \
               f"flop={self.flop},\n\nplayerTurn={self.playerTurn})"

    def show_hands(self):

        pass

    def add_player(self, player): # add function for partner seating todo
        self.seats.append(player)

class Game:

    def __init__(self, game, houseRules=None):
        # print("<GAME>")
        self.game = game
        self.houseRules = {}
        if self.game == "Texas Holdem":
            # self.houseRules = self.texas_holdem()
            self.houseRules = {"hand size": 2, "rule set": ['draw n discard', 'discard first', 'betting', 'flop']}
        elif self.game == "5 Card Stud":
            self.houseRules = {"hand size": 5, "rule set": ['draw n discard', 'discard first', 'betting']}
        elif self.game == "Spades":
            self.houseRules = {"hand size": 13, "rule set": ['partners', 'books', 'scored']}
        elif self.game == "Hearts":
            self.houseRules = {"hand size": 13, "rule set": ['partners', 'books', 'scored']} # Really partners? todo
        elif self.game == 'Rummy':
            self.houseRules = {"hand size": 7, "rule set": ['draw n discard', 'scored']}
        elif self.game == "Go Fish":
            self.houseRules = {"hand size": 8, "rule set": ['draw n discard']}

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.__class__.__name__}(game='{self.game}', houseRules={self.houseRules})"

    def texas_holdem(self):
        # print("House Rules: Texas Hold'em Poker")
        pass

    def five_card_stud(self):
        # print("House Rules: Five Card Stud Poker")
        pass

    def spades(self):
        # print("House Rules: Spades")
        pass

    def hearts(self):
        # print("House Rules: Hearts")
        pass

    def rummy(self):
        # print("House Rules: Rummy")
        pass

    def go_fish(self):
        # print("House Rules: Go Fish")
        pass

class Player:

    def __init__(self, name, hand=None, bank=None, score=None):
        # print("<PLAYER>")
        self.name = name
        self.hand = []
        self.bank = 0.0
        self.score = 0
        # print(f"{self.name} has been added as a player.")

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', hand={self.hand}, bank={self.bank}, score={self.score})"
        pass

    def draw_card(self):

        pass

    def discard_card(self, card):

        pass

    def show_hand(self, start=None, stop=None, step=None):
        self.faces = "-".join([card.face() for card in self.hand[start:stop:step]])
        return self.faces
        pass

    def arrange_hand(self):

        pass

class Screen:

    def __init__(self, parent=None):

        # self.table = table
        # print(f"TABLE:\n{'*'*35}\n", table)
        self.parent = parent

        self.circleDigits = {'0': '⓪', '1': '①', '2': '②', '3': '③', '4': '④', '5': '⑤', '6': '⑥', '7': '⑦', '8': '⑧', '9': '⑨', '10': '⑩', '11': '⑪', '12': '⑫', '13': '⑬', '14': '⑭', '15': '⑮', '16': '⑯', '17': '⑰', '18': '⑱', '19': '⑲', '20': '⑳', '21': '㉑', '22': '㉒', '23': '㉓', '24': '㉔', '25': '㉕', '26': '㉖', '27': '㉗', '28': '㉘', '29': '㉙', '30': '㉚', '31': '㉛', '32': '㉜', '33': '㉝', '34': '㉞', '35': '㉟', '36': '㊱', '37': '㊲', '38': '㊳', '39': '㊴', '40': '㊵', '41': '㊶', '42': '㊷', '43': '㊸', '44': '㊹', '45': '㊺', '46': '㊻', '47': '㊼', '48': '㊽', '49': '㊾', '50': '㊿'}
        self.boxes = {'horiz': '─', 'vert': '│', 'tl': '┌', 'tc': '┬', 'tr': '┐', 'cl': '├', 'cc': '┼', 'cr': '┤', 'bl': '└', 'bc': '┴', 'br': '┘'}
        self.gameList = ["1) Texas Holdem", '2) 5 Card Stud', '3) Spades', '4) Hearts', '5) Rummy', '6) Go Fish']

        self.TheGame = None
        self.ThePlayers = []
        self.TheDeck = Deck()

        self.initUI()

    def initUI(self):

        # print("Initializing Screen")
        self.screen = curses.initscr()
        curses.noecho()
        curses.curs_set(0)
        curses.start_color()
        curses.init_color(2, 0, 325, 0)
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_RED)

        self.maxY, self.maxX = self.screen.getmaxyx()

        # print("color_content", curses.color_content(2))

        self.screen.clear()
        self.screen.border()
        self.center_text(self.screen, "Press any key...")

        self.TheGame = Game(self.choose_game(self.screen))  # You just lost the game...:p

        self.ThePlayers = self.add_players(self.screen)

        self.TheDeck.deal_cards(self.ThePlayers, self.TheGame.houseRules['hand size'])

        self.TheTable = Table(self.ThePlayers, self.TheGame, self.TheDeck)
        # print(self.TheTable)
        # print("Player 0 hand: ", self.TheTable.players[0].show_hand())
        self.mainMenu = ["Main Menu", "Draw Card", "Play Card", "Discard", "Rearrange", "Save Game", "Quit Game"]
        self.menuUI(self.screen, self.mainMenu)

        self.greenUI()

        choice = ""
        while choice != "Q":

            choice = getch().upper()

            if choice == "1":
                pass
            elif choice == "2":
                pass
            elif choice == "3":
                self.rearrangeMenu = ["Rearrange:", "By Suit", "By Value", "Main Menu"]
                self.menuUI(self.screen, self.rearrangeMenu)
                self.rearrange_cards(self.TheTable.players[0])
                pass
            elif choice == "4":
                pass
            elif choice == "Q":
                self.center_text(self.screen, 'Press Any Key to Quit.', curses.color_pair(3) | curses.A_BLINK | curses.A_BOLD)
                self.screen.refresh()
                exit = getch()
            else:
                self.print_error(self.screen, "Invalid Key Press. Select Again...")

        curses.echo()
        curses.curs_set(1)
        curses.endwin()
        print(self.TheTable)

    def rearrange_cards(self, player):
        choice = ""
        while choice != "3":
            choice = getch()

            if choice == "1":
                new_order = []

                player.hand = sorted(player.hand)

                for suitValue in range(4):
                    for card in player.hand:
                        if card.rank()[1] == suitValue:
                            new_order.append(card)

                player.hand = new_order

                self.greenUI()
            elif choice == "2":
                player.hand = sorted(player.hand)
                self.greenUI()
            elif choice == "3":
                self.menuUI(self.screen, self.mainMenu)
            else:
                self.print_error(self.screen, "Invalid Key Press. Select Again...")


        pass

    def choose_game(self, window):

        for i in range(len(self.gameList)):
            window.addstr(i + 1, 1, self.gameList[i])
        window.refresh()
        choice = getch()
        if choice == '1':
            self.game = "Texas Holdem"
        elif choice == '2':
            self.game = "5 Card Stud"
        elif choice == '3':
            self.game = 'Spades'
        elif choice == '4':
            self.game = 'Hearts'
        elif choice == '5':
            self.game = 'Rummy'
        elif choice == '6':
            self.game = 'Go Fish'
        else:
            self.print_error(window, "Invalid Key Press. Select Again...")

            self.choose_game(window)



        for i in range(len(self.gameList)):
            window.addstr(i + 1, 1, " " * len(self.gameList[i]))
        window.addstr(1, self.maxX - 14, "The Game:", curses.A_UNDERLINE | curses.A_BOLD)
        window.addstr(2, self.maxX - 13, self.game)
        window.refresh()
        return self.game

    def add_players(self, window):
        window.addstr(4, self.maxX - 14, "The Players:", curses.A_UNDERLINE | curses.A_BOLD)
        window.addstr(1, 1, "Add Player? (Y/n)")
        window.refresh()
        choice = ""
        nameLine = 5
        playerList = []
        while choice != 'n':
            choice = getch().lower()
            if choice == 'y':
                name = self.the_input(window, 2, 1, "Enter Player Name:").decode()
                menuName = f"{nameLine - 4}) {name}" # str(nameLine - 4) + ") " + str(name)
                playerList.append(Player(name))
                window.addstr(nameLine, self.maxX - 13, menuName)
                nameLine += 1
                window.refresh()

            elif choice == 'n':
                if len(playerList) > 0:
                    window.addstr(1, 1, " " * 17)
                    return playerList
                else:
                    self.print_error(window, "You Must Add At Least One Player.")
                    choice = ""

            else:
                self.print_error(window, "Invalid Key Press. Select Again...")
        pass

    def greenUI(self): # set up for 4 players...fix longer table
        yPos, xPos = self.center_window(self.screen, 50, 23)
        self.TheGreen = curses.newwin(23, 51, yPos, xPos)
        self.TheGreen.bkgdset(" ", curses.color_pair(2))
        self.TheGreen.border()
        # self.TheGreen.overlay(self.screen)

        for i in range(21):
            self.TheGreen.addstr(i+1, 1, "\u202f" * 49, curses.color_pair(2))
        # self.center_text(self.TheGreen, "Look at me now...")
        for i in range(11, 36, 6):
            self.TheGreen.addstr(4, i, "[ ♠ ]", curses.color_pair(1))
        # for i in range(11, 36, 6):
        #     self.TheGreen.addstr(19, i, "[ ♠ ]", curses.color_pair(1))
        for i in range(5, 18, 3):
            self.TheGreen.addstr(i, 6, "[ ♠ ]", curses.color_pair(1))
        for i in range(5, 18, 3):
            self.TheGreen.addstr(i, 40, "[ ♠ ]", curses.color_pair(1))

        self.show_my_hand(self.TheGreen)
        if 'draw n discard' in self.TheTable.houseRules['rule set']:
            self.TheGreen.addstr(8, 18, "┌───┐", curses.color_pair(5))
            self.TheGreen.addstr(9, 18, "└[ ♠ ]", curses.color_pair(5))
            self.TheGreen.addstr(9, 27, self.TheTable.discard[-1].face(), curses.color_pair(3) if "♥" in self.TheTable.discard[-1].face() or "♦" in self.TheTable.discard[-1].face() else curses.color_pair(4))

        self.TheGreen.refresh()

    def show_my_hand(self, window):
        player = self.TheTable.players[0]

        self.cardNumbers = ""
        if len(player.hand) > 8:

            cardList = player.show_hand(0, 8).split("-")
            for i in range(len(cardList)):
                window.addstr(18, i * 6 + 2, cardList[i], curses.color_pair(3) if "♥" in cardList[i] or "♦" in cardList[i] else curses.color_pair(4))

            self.cardNumbers = ""
            for i in range(8):
                self.cardNumbers += f"{self.circleDigits[str(i + 1)]}     "
            self.horiz_center_text(window, 19, self.cardNumbers.rstrip())

            cardList = player.show_hand(8).split("-")
            for i in range(len(cardList)):
                window.addstr(20, i * 6 + 12, cardList[i], curses.color_pair(3) if "♥" in cardList[i] or "♦" in cardList[i] else curses.color_pair(4))

            self.cardNumbers = ""
            for i in range(5):
                self.cardNumbers += f"{self.circleDigits[str(i + 9)]}     "
            self.horiz_center_text(window, 21, self.cardNumbers.rstrip())

            pass

        else:
            rows, cols = self.TheGreen.getmaxyx()
            halfWay = int((cols / 2) - int(len(player.show_hand()) / 2))

            cardList = player.show_hand().split("-")
            for i in range(len(cardList)):
                window.addstr(19, i * 6 + halfWay, cardList[i], curses.color_pair(3) if "♥" in cardList[i] or "♦" in cardList[i] else curses.color_pair(4))

            self.cardNumbers = ""
            for i in range(self.TheTable.houseRules['hand size']):
                self.cardNumbers += f"{self.circleDigits[str(i + 1)]}     "
            self.horiz_center_text(self.TheGreen, 20, self.cardNumbers.rstrip())

        window.refresh()

    def clear_menu(self, window):
        for i in range(2, 20):
            window.addstr(i, 2, " " * 13)
        window.refresh()

    def menuUI(self, window, menuList): # Poker
        self.clear_menu(window)
        window.addstr(1, 1, menuList[0], curses.A_UNDERLINE | curses.A_BOLD)
        for i in range(len(menuList) - 1):
            window.addstr(i + 2, 2, f"{str(i + 1)}) {menuList[i + 1]}")
        if "Quit Game" in menuList:
            window.addstr(len(menuList), 2, "Q) Quit Game")
        window.refresh()


    def print_error(self, window, error):
        self.center_text(window, error, curses.color_pair(3) | curses.A_BLINK)
        window.refresh()
        curses.napms(5000)
        self.center_text(window, " " * len(error))
        try:
            if self.TheGreen:
                self.greenUI()
        except AttributeError:
            pass
        window.refresh()

    def the_input(self, window, r, c, prompt):
        curses.echo()
        window.addstr(r, c, prompt)
        window.refresh()
        answer = window.getstr(r + 1, c, 12)
        curses.noecho()
        window.addstr(r, c, " " * len(prompt))
        window.addstr(r + 1, c, " " * len(answer))
        window.refresh()
        return answer

    def center_text(self, window, text, attr=None): #fix vert and horiz center todo
        rows, cols = window.getmaxyx()
        middleRow = int(rows / 2)
        halfMessage = int(len(text) / 2)
        middleCol = int(cols / 2)
        xPos = middleCol - halfMessage
        if attr:
            window.addstr(middleRow, xPos, text, attr)
        else:
            window.addstr(middleRow, xPos, text)
        window.refresh()

    def horiz_center_text(self, window, row, text, attr=None):
        rows, cols = window.getmaxyx()
        middleCol = int(cols / 2)
        halfMessage = int(len(text) / 2)
        xPos = abs(middleCol - halfMessage)
        if attr:
            window.addstr(row, xPos, text, attr)
        else:
            window.addstr(row, xPos, text)
        window.refresh()
        pass

    def vert_center_text(self, window, col, text, attr=None):
        rows, cols = window.getmaxyx()
        middleRow = int(rows / 2)
        halfMessage = int(len(text.split("\n")))
        yPos = middleRow - halfMessage
        if attr:
            window.addstr(yPos, col, text, attr)
        else:
            window.addstr(yPos, col, text)
        window.refresh()
        pass

    def center_window(self, window, winWidth, winHeight):
        rows, cols = window.getmaxyx()
        middleRow = int(rows / 2)
        halfWinHeight = int(winHeight / 2)

        middleCol = int(cols / 2)
        halfWinWidth = int(winWidth / 2)

        xPos = middleCol - halfWinWidth
        yPos = middleRow - halfWinHeight

        return yPos, xPos


if __name__ == "__main__":
    CardGames = Screen()


# print(type(__name__))
#
# ace_of_spades = Card("spades", "A")
# ace2ofspades = Card("spades", "A")
# print("--->", ace_of_spades == ace2ofspades)
# ace_of_hearts = Card("hearts", "A")
# four_of_clubs = Card("clubs", 4)
# six_of_hearts = Card("hearts", 6)
# print("___>", four_of_clubs > six_of_hearts)
# print("***>", six_of_hearts < four_of_clubs)
# five_of_diamonds = Card('diamonds', 5)
# print(ace_of_hearts.pip, ace_of_hearts.suit)
# print(ace_of_spades.face(), ace_of_hearts.face(), four_of_clubs.face(), six_of_hearts.face(), five_of_diamonds.face())
# print(ace_of_spades.__repr__(), ace_of_hearts.__repr__(), four_of_clubs.__repr__(), six_of_hearts.__repr__(), five_of_diamonds.__repr__())
#
#
# Delt = Deck()
# print("LENGTH", len(Delt))
# # print(Delt)
# print(Delt.show_deck())
# Delt.shuffle_deck()
# print(Delt.show_deck())
