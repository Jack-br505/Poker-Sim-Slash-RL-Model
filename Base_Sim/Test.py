import random
from Deck_Hand import hand, deck
from Game import quick_game, many_games

many_games(100000, card1 = ['10', 'Hearts'], card2= ['9', 'Hearts'], community=None, print_output = True)

#game = quick_game(card1 = ['4', 'Diamonds'], card2= ['6', 'Diamonds'], community=None)
#print(game.get_winner())
#r = ['f', 'm', 'n', 'o', 'p']
#e = {0: 'f', 1: 'n', 2: 'o'}
#print(max(e.values(), key=r.index))
