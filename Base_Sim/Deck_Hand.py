import random
import numpy as np

class deck():
    """Class for the full deck
    
    Attribuites:
    
    vals: dict: dictionary storing the value of the number/face on each card
    suits: dict: dictionary storing suit of each card
    
    """
    def __init__(self):
        vals = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        suits = ["Spades", "Clubs", "Hearts", "Diamonds"]

        random.seed()
        self.vals = {}
        self.suits = {}
        i = 0
        for suit in suits:
            for val in vals:
                #Add a unique index for each card in deck tracking suit and value
                self.vals[i] = val
                self.suits[i] = suit
                i += 1


        

    def get_deck(self):
        """Dev tool to make sure deck looks right"""
        return(self.vals, self.suits)
        
    def remove_card(self, index):
        """Uses the index of the card to remove that card from the deck"""
        # Remove the key-value pair
        del self.vals[index]
        del self.suits[index] 

    def draw_card(self):
        """Draws a card from the deck, removing the value from self.vals and self.suits
        Returns a list: [val, suit] 
        """
        random_key = np.random.choice(list(self.vals.keys()))

        card = [self.vals[random_key], self.suits[random_key]]
        #Remove from deck
        del self.vals[random_key]
        del self.suits[random_key]

        return card

class hand():
    def __init__(self, deck, card1 = None, card2 = None):
        """
        Initializes a new hand for a poker game, no attribuites needed

        inputs: 
        -------
        deck : class deck: the deck for the game that the hand is part of
        
        card1: array: array of format [<card_value>, <suit>], both vals are strings

        """
        #Draw a random card from deck if no card is specified
        if card1 == None:
            self.card1 = deck.draw_card()
        else:
            self.card1 = card1
            #Remove card1 from deck if specified
            for key, val in deck.vals.items():
                    if val == self.card1[0] and deck.suits[key] == self.card1[1]:
                        del deck.vals[key]
                        del deck.suits[key]
                        break
        #repeat for card2
        if card2 == None:
            self.card2 = deck.draw_card()
        else:
            self.card2 = card2
            #Remove card2 from deck
            for key, val in deck.vals.items():
                    if val == self.card2[0] and deck.suits[key] == self.card2[1]:
                        del deck.vals[key]
                        del deck.suits[key]
                        break
    def get_vals(self):
        return([self.card1[0], self.card2[0]])
    