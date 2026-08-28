#Modified version of game class in directory betting_sim, this version is designed to be used with a reinforcement learning agent, and allows for the user to input their own actions for each player in the game.
import sys
sys.path.insert(0, '/Users/jackbrach/dev/Poker_Sim/Base_Sim')
from Deck_Hand import deck, hand
import random
import numpy as np
import pandas as pd
import ast
import pickle

sys.path.insert(0, '/Users/jackbrach/dev/Poker_Sim')
#Import the 4_player_results.csv file to determine hand strengths
strengths_df = pd.read_csv('4_player_results.csv')
#Convert hand column from string to tuple
strengths_df['hand'] = strengths_df['hand'].apply(ast.literal_eval)

#Change the hand column to four seperate columns of string for each card
strengths_df[['card_1', 'card_2']] = pd.DataFrame(strengths_df['hand'].to_list(), index=strengths_df.index)
strengths_df[['card1_value', 'card1_suit']] = pd.DataFrame(strengths_df['card_1'].to_list(), index=strengths_df.index)
strengths_df[['card2_value', 'card2_suit']] = pd.DataFrame(strengths_df['card_2'].to_list(), index=strengths_df.index)



random.seed()

class game():
    """
    Creates a  game to simulate full game with raising / folding and betting. 

    inputs:
    -------
    players: int: Number of players in this specific game between 2 and 8

    card1: list of length 2: the first card in order ['value', 'suit'] of the players hand, can be set to None if random value desired
    
    card2: list of length 2: the second card in order ['value', 'suit'] of the players hand, can be set to None if random value desired

    community: dict of length 5: a dictionary containing lists for all the wanted specified community cards, values can be set to None if wanted to be random

    chip_dict: dict of length players, values are a dictionary of how many chips each player has to start

    dealer: int : player that is the dealer, is important for blinds
    """

    def __init__(self, players = 4, card1 = None, card2 = None, community = None, chip_dict = None, dealer = 0):
        #Set a random state
        if community is None:
            self.community = {0 : None, 1 : None, 2 : None, 3 : None, 4 : None}
        else:
            self.community = community
        self.deck = deck()

        #Remove community cards from deck if specified before drawing stuff
        for i in range(5):
            if self.community[i] != None:
                card = self.community[i]
                key_to_remove = 0
                for key, val in self.deck.vals.items():
                    if val == card[0] and self.deck.suits[key] == card[1]:
                        del self.deck.vals[key]
                        del self.deck.suits[key]
                        break

        self.hands_dict = {}

        #Make players hand
        self.hands_dict[0] = hand(deck = self.deck, card1=card1, card2=card2)
        #Create random hands for other players
        for i in range(players - 1):
            self.hands_dict[i+1] = hand(deck = self.deck)
        
        #Get cards for community
        for i in range(5):
            if self.community[i] == None:
                self.community[i] = self.deck.draw_card()
        #print(self.community)
        
        #Get all chip values
        if chip_dict == None:
            self.chips = {}
            for i in range(players):
                self.chips[i] = 20 #Default of 20 to start
        else:
            self.chips = chip_dict
        
        #Determine the order of players
        self.order = []

        #Create true order of players, dealer is last in order
        curr = dealer 

        for i in range(players):
            if curr == players - 1:
                curr = 0
            else:
                curr += 1
            self.order.append(curr)
        self.players_unfolded = self.order.copy()

        #Make dict of player that are all in,
        self.all_in = {}

        #Condition to check if someone has raised
        self.check_raise = -1
            
    def get_value(self, hand):
        """Get the value of the hand within this game after gameplay is done
        
        Hierarchy of hands: Straight flush = 8, Four-of-a-Kind = 7, Full House = 6, Flush = 5, Straight = 4, Three-of-a-Kind = 3,
        Two-Pair = 2, One-Pair = 1, High-Card = 0
        
        hand is a list of lists
        """
        #Look at special hands, use docstring for number guide
        conditions = {"High Card" : True, "Pair" : False, "Two-Pair" : False, "Three-of-a-Kind" : False, "Straight" : False, 
                      "Flush" : False, "Full House" : False, "Four-of-a-Kind" : False, "Straight Flush" : False} #False if satisfied

        #Combine community and hand
        all_cards = [hand.card1 , hand.card2] + list(self.community.values())
        #print(all_cards)

        all_vals = []
        all_suits = []
        #Find all suits and values of the cards
        for card in all_cards:
            #print(card)
            all_vals.append(card[0])
            all_suits.append(card[1])

        #Keep track of highest card in winning combo
        high_cards = {}
        hand_vals = hand.get_vals()
        #Check for pairs, 3-of-a kinds and such by getting frequncy dictionary
        frequencies = {}

        for item in all_vals:
            frequencies[item] = frequencies.get(item, 0) + 1
        #print(frequencies)
        pair_counter = 0
        three_counter = 0 #Check for number of pairs and 3 of kinds
        for key in frequencies.keys():
            val = frequencies[key]
            #Check for pair
            if val ==2:
                pair_counter += 1
                if key in hand_vals:
                    high_cards[f'Pair-{pair_counter}'] = key
            elif val == 3:
                #3 of a kind still fits two pair and pair def
                three_counter += 1
                #Set three of a kind to true
                conditions["Three-of-a-Kind"] = True
                #Add to card list
                if key in hand_vals:
                    high_cards[f'Three-{three_counter}'] = key
            elif val == 4:
                conditions["Four-of-a-Kind"] = True
                three_counter += 1
                if key in hand_vals:
                    high_cards['Four'] = key
        #Check if there are pairs
        if pair_counter + three_counter >= 1:
            conditions["Pair"] = True
            #Check for two pairs
            if pair_counter + three_counter >= 2:
                conditions["Two-Pair"] = True
                #Check for full house
                if pair_counter >= 1 and three_counter >= 1:
                    conditions["Full House"] = True
        
        #look for straight and straight flush
        possible_values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        #Sort all_vals by order in possible values
        sorted_vals = []
        for val in possible_values:
            if val in all_vals and val not in sorted_vals:
                sorted_vals.append(val)
        
        #Use sorted vals to find high card
        i = -1
        first = True
        while (-1 * i) <= len(sorted_vals):
            if first and sorted_vals[i] in hand_vals:
                high_cards['High'] = sorted_vals[i]
                #print(high_cards['High'])
                first = False
            elif sorted_vals[i] in hand_vals:
                high_cards['Low'] = sorted_vals[i]
                #print(high_cards['Low'])
                break
            i += -1
        #Issue with pairs, low card is not being set if there is a pair, need to check for that
        if 'Low' not in high_cards.keys():
            high_cards['Low'] = high_cards['High']
        #print(sorted_vals)
        
        if len(sorted_vals) >= 5:
            for s in range(3):
                i = 0 + s
                while i < len(sorted_vals) - 1:
                    p_values_index = possible_values.index(sorted_vals[i])
                    if sorted_vals[i + 1] == possible_values[p_values_index + 1]:
                        i += 1
                        if i == 4 + s:
                            conditions['Straight'] = True

                            high_cards['Straight'] = sorted_vals[i]

                            #Check for flush too
                            if all_suits[all_vals == sorted_vals[i]] == all_suits[all_vals == sorted_vals[i-1]] == all_suits[all_vals == sorted_vals[i-2]] == all_suits[all_vals == sorted_vals[i-3]] == all_suits[all_vals == sorted_vals[i-4]]:
                                conditions["Straight Flush"] = True
                            break
                    else:
                        break
                
        #Check for flush
        suit_frequency = {}
        for item in all_suits:
            suit_frequency[item] = suit_frequency.get(item, 0) + 1
        #print(suit_frequency)
        for suit in suit_frequency.keys():
            if suit_frequency[suit] >= 5:
                conditions["Flush"] = True
                #Get card values
                temp = []
                for i in range(len(all_vals)):
                    if all_suits[i] == suit:
                        temp.append(all_vals[i])
                high_cards['Flush'] = temp
                break

        return(conditions, high_cards)

    def get_winner(self, players_in_game = None):
        hands = {}
        highs = {}
        for i in range(len(self.hands_dict.values())):
            if players_in_game == None:
                hands[i], highs[i] = self.get_value(self.hands_dict[i])
            elif i in players_in_game:
                #print(i)
                hands[i], highs[i] = self.get_value(self.hands_dict[i])
        #print(hands, highs)
        heirarchy = {}
        index = 0
        for hand in hands.values():
            key = list(hands.keys())[index]
            if hand['Straight Flush'] != False:
                heirarchy[key] = 8
            elif hand['Four-of-a-Kind'] != False:
                heirarchy[key] = 7
            elif hand['Full House'] != False:
                heirarchy[key] = 6
            elif hand['Flush'] != False:
                heirarchy[key] = 5
            elif hand['Straight'] != False:  
                heirarchy[key] = 4
            elif hand['Three-of-a-Kind'] != False:
                heirarchy[key] = 3
            elif hand['Two-Pair'] != False:
                heirarchy[key] = 2
            elif hand['Pair'] != False:
                heirarchy[key] = 1
            else:
                heirarchy[key] = 0
            index += 1
        #print(heirarchy)

        #Get heirarchy of cards
        possible_values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

        #Get winner by heirarchy, if tie get winner by high card
        winner = max(heirarchy, key=heirarchy.get)
        #print(winner)

        #Create tiebreaker function
        def determine_winner(tops, top_card, tied_players):
            top_values = list(tops.values())
            if top_values.count(top_card) == 1:
                    for player in tied_players:
                        if tops[player] == top_card:
                            winner = player
            else:
                top_ties = {}
                
                for player in tied_players:
                    if tops[player] == top_card:
                        top_ties[player] = highs[player]['High']
                #print(f'DEBUG: top_ties = {top_ties}')
                #print(f'DEBUG: tied_players = {tied_players}')
                #print(f'DEBUG: tops = {tops}')
                #print(f'DEBUG: top_card = {top_card}')
                if not top_ties.values():
                    print('ERROR: top_ties is empty!')
                top_card = max(top_ties.values(), key=possible_values.index)
                top_values = list(top_ties.values())
                if top_values.count(top_card) == 1:
                    for player in top_ties.keys():
                        if top_ties[player] == top_card:
                            winner = player
                else:
                    top_ties_2 = {}
                    for player in top_ties.keys():
                        if top_ties[player] == top_card:
                            top_ties_2[player] = highs[player]['Low']
                    
                    top_card = max(top_ties_2.values(), key=possible_values.index)  
                    top_values = list(top_ties_2.values())
                    if top_values.count(top_card) == 1:
                        for player in top_ties_2.keys():
                            if top_ties_2[player] == top_card:
                                winner = player
                    else:
                        winner = list(top_ties.keys())
            return(winner)
        

        #Check for tie
        tie = False
        for key in heirarchy.keys():
            if heirarchy[key] == heirarchy[winner] and key != winner:
                tie = True
                break
        if tie:
            tied_players = []
            for key in heirarchy.keys():
                if heirarchy[key] == heirarchy[winner]:
                    tied_players.append(key)
            #print(tied_players)

            #Need to find pairs that are exclusively in the community cards and not in the players hand, if there are two pairs, need to find the highest pair that is in the players hand, if there is a tie on that, need to find the second pair that is in the players hand, if there is a tie on that, need to find the high card in the players hand
            frequency = {}
            for card in self.community.values():
                frequency[card[0]] = frequency.get(card[0], 0) + 1
            community_pairs = []
            community_threes = []
            community_fours = []
            for key in frequency.keys():
                if frequency[key] == 2:
                    community_pairs.append(key)
                elif frequency[key] == 3:
                    community_threes.append(key)
                elif frequency[key] == 4:
                    community_fours.append(key) #If there is a four of a kind in the community, that also counts as a three of a kind for tie breaking purposes

            #Find hand winners are tied on
            hand_type = heirarchy[winner]
            if hand_type == 8:
                tops = {}
                for player in tied_players:
                    tops[player] = highs[player]['Straight']
                top_card = max(tops.values(), key=possible_values.index)
                winner = determine_winner(tops = tops, top_card= top_card, tied_players= tied_players)
            elif hand_type == 7:
                tops = {}
                for player in tied_players:
                    if 'Four' in highs[player].keys():
                        tops[player] = highs[player]['Four']
                    else:
                        tops[player] = community_fours[0] #only 1 community four of a kind can exist, so just take that value
                top_card = max(tops.values(), key=possible_values.index)
                winner = determine_winner(tops = tops, top_card= top_card, tied_players= tied_players)
            elif hand_type == 6:
                threes = {}
                pairs = {}
                for player in tied_players:
                    if 'Three-1' in highs[player].keys():
                        threes[player] = highs[player]['Three-1']
                    else:
                        threes[player] = community_threes[0] #only 1 community three of a kind can exist, so just take that value
                    if 'Pair-1' in highs[player].keys():
                        pairs[player] = highs[player]['Pair-1']
                    else:
                        pairs[player] = community_pairs[0] #only 1 community pair can exist, so just take that value
                max_three = max(threes.values(), key=possible_values.index)
                three_ties = []
                for player in tied_players:
                    if threes[player] == max_three:
                        three_ties.append(player)
                if len(three_ties) == 1:
                    winner = three_ties[0]
                else:
                    pair_ties = {}
                    for player in three_ties:
                        pair_ties[player] = pairs[player]
                    top_pair = max(pair_ties.values(), key = possible_values.index) 
                    winner = determine_winner(tops = pair_ties, top_card= top_pair, tied_players= three_ties)
            elif hand_type == 5:
                #Flush is unique in that the high card is determined by the highest card in the flush and ties go down the flush
                tie_counter = 0
                flushes = {}
                #Get all 5 flush cards and sort by value, then compare the highest card in the flush, if tie compare second highest and so on
                for player in tied_players: #First sort all flushes by value
                    temp = highs[player]['Flush']
                    temp.sort(key= possible_values.index, reverse=True)
                    flushes[player] = temp
                
                while tie_counter < 5:
                    top_card = max([flushes[player][tie_counter] for player in flushes.keys()], key=possible_values.index)
                    for player in tied_players:
                        if flushes[player][tie_counter] == top_card:
                            'keep'
                        else:
                            del flushes[player]
                            del tied_players[tied_players.index(player)]
                    if len(flushes) == 1:
                        winner = list(flushes.keys())[0]
                        break
                    elif len(flushes) == 0:
                        winner = tied_players
                        print("Error in tie breaker, all flushes eliminated")
                        break
                    tie_counter += 1
                
                if tie_counter == 5:
                    #Go into tiebreaker
                    tops = {}
                    for player in tied_players:
                        tops[player] = flushes[player][0]
                    top_card = max(tops.values(), key=possible_values.index)
                    winner = determine_winner(tops = tops, top_card= top_card, tied_players= tied_players)
            elif hand_type == 4:
                straights = {}
                for player in tied_players:
                    straights[player] = highs[player]['Straight']
                top_card = max(straights.values(), key=possible_values.index)
                winner = determine_winner(tops = straights, top_card= top_card, tied_players= tied_players)
            elif hand_type == 3: 
                threes = {}
                for player in tied_players:
                    if 'Three-1' in highs[player].keys():
                        threes[player] = highs[player]['Three-1']
                    else:
                        threes[player] = community_threes[0] #only 1 community three of a kind can exist, so just take that value
                top_card = max(threes.values(), key=possible_values.index)
                winner = determine_winner(tops = threes, top_card= top_card, tied_players= tied_players)
            elif hand_type == 2: 
                #Need to find pairs that are exclusively in the community cards and not in the players hand, if there are two pairs, need to find the highest pair that is in the players hand, if there is a tie on that, need to find the second pair that is in the players hand, if there is a tie on that, need to find the high card in the players hand
                frequency = {}
                for card in self.community.values():
                    frequency[card[0]] = frequency.get(card[0], 0) + 1
                community_pairs = []
                for key in frequency.keys():
                    if frequency[key] == 2:
                        community_pairs.append(key)
                pairs = {}
                for player in tied_players:
                    if 'Pair-2' in highs[player].keys():
                        temp_list = [highs[player]['Pair-1'], highs[player]['Pair-2']] + community_pairs
                        pairs[player] = max(temp_list, key=possible_values.index)
                    elif 'Pair-1' in highs[player].keys():
                        temp_list = [highs[player]['Pair-1']] + community_pairs
                        pairs[player] = max(temp_list, key=possible_values.index)
                    else:
                        temp_list = community_pairs
                        pairs[player] = max(temp_list, key=possible_values.index)
                top_card = max(pairs.values(), key=possible_values.index)
                pair_values = list(pairs.values())
                if pair_values.count(top_card) == 1:
                    for player in tied_players:
                        if pairs[player] == top_card:
                            winner = player
                else:
                    double_ties = {}
                    for player in tied_players:
                        if pairs[player] == top_card:
                            if 'Pair-2' in highs[player].keys():
                                temp_list = [highs[player]['Pair-1'], highs[player]['Pair-2']] + community_pairs
                            elif 'Pair-1' in highs[player].keys():
                                temp_list = [highs[player]['Pair-1']] + community_pairs
                            else:
                                temp_list =  community_pairs
                            #Filter out top card from temp list
                            temp_list = [x for x in temp_list if x != top_card]
                            double_ties[player] = max(temp_list, key=possible_values.index)
                    top_card = max(double_ties.values(), key=possible_values.index)
                    winner = determine_winner(tops = double_ties, top_card= top_card, tied_players= double_ties.keys())
            elif hand_type == 1:
                pairs = {}
                for player in tied_players:
                    if 'Pair-1' in highs[player].keys():
                        pairs[player] = highs[player]['Pair-1']
                    else:
                        pairs[player] = community_pairs[0] #only 1 community pair can exist, so just take that value
                winner = max(pairs.values(), key=possible_values.index)
            else:
                h_cards = {}
                for player in tied_players:
                    h_cards[player] = highs[player]['High']
                top_card = max(h_cards.values(), key=possible_values.index)
                winner = determine_winner(tops = h_cards, top_card= top_card, tied_players= tied_players)
        return winner

    def player_action(self, player, curr_bet, curr_raise):
        """Get the action of the player, fold, call or raise, and return the new bet and raise values
        
        player: int: the player number
        
        curr_bet: the player's current bet, if they have not bet yet it is 0
        
        curr_raise: the current raise value to stay in game, starts at 2 chips
        
        Returns the bet of the player followed by the current raise value"""

        if self.chips[player] <= curr_raise - curr_bet: #Check for players that need to go all in
            print(f'Player{player} has {self.chips[player]} chips, and the current raise is {curr_raise}, they must go all in to stay in the game')
            action = input(f'Player {player}, do you want to fold or go all in? (f/a): ')
            if action == 'f':
                print(f'Player {player} has folded')
                self.players_unfolded.remove(player)
                print(f'Players still in game: {self.players_unfolded}')
                return(curr_bet, curr_raise)
            elif action == 'a':
                print(f'Player {player} has gone all in with {self.chips[player]} chips')
                curr_bet += self.chips[player]
                self.chips[player] = 0
                self.all_in[player] = curr_bet
                return(curr_bet, curr_raise)
        elif curr_bet < curr_raise:
            print(f'Player {player} has {self.chips[player]} chips and the current raise is {curr_raise}')
            action = input(f'Player {player}, do you want to fold, call or raise? (f/c/r): ')
            if action == 'f':
                print(f'Player {player} has folded')
                self.players_unfolded.remove(player)
                print(f'Players still in game: {self.players_unfolded}')
                return(curr_bet, curr_raise)
            elif action == 'c':
                print(f'Player {player} has called')
                
                self.chips[player] -= curr_raise - curr_bet
                return(curr_raise, curr_raise)
            elif action == 'r':
                new_raise = int(input(f'Player {player}, how much do you want to raise? (must be greater than current raise of {curr_raise}): '))
                if new_raise <= curr_raise or new_raise > self.chips[player]:
                    print(f'Invalid raise amount, must be greater than current raise of {curr_raise}')
                    return(self.player_action(player, curr_bet, curr_raise))
                else:
                    print(f'Player {player} has raised to {new_raise}')
                    self.chips[player] -= new_raise - curr_bet
                    if self.chips[player] == 0:
                        self.all_in[player] = new_raise
                        print(f'Player {player} has gone all in with {new_raise} chips')
                    self.check_raise = player 
                    return(new_raise, new_raise)
            else:
                print('Invalid action, please enter f, c or r')
                return(self.player_action(player, curr_bet, curr_raise))
        elif curr_bet == curr_raise:
            print(f'Player {player} has {self.chips[player]} chips and the current raise is {curr_raise}')
            action = input(f'Player {player}, do you want to call or raise? (c/r): ')
            if action == 'r':
                new_raise = int(input(f'Player {player}, how much do you want to raise? (must be greater than current raise of {curr_raise}): '))
                if new_raise <= curr_raise:
                    print(f'Invalid raise amount, must be greater than current raise of {curr_raise}')
                    return(self.player_action(player, curr_bet, curr_raise))
                else:
                    print(f'Player {player} has raised to {new_raise}')
                    self.chips[player] -= new_raise - curr_bet
                    self.check_raise = player 
                    return(new_raise, new_raise)
            elif action == 'c':
                print(f'Player {player} has called')
                self.chips[player] -= curr_raise - curr_bet
                return(curr_raise, curr_raise)
            else:
                print('Invalid action, please enter f, c or r')
                return(self.player_action(player, curr_bet, curr_raise))

    def play_game(self):
        """Play the game of raising and folding until there is a winner, then adjust chips accordingly"""
        
        #Order is set and cards are dealt

        bets = {}
        for i in range(len(self.players_unfolded)):
            bets[i] = 0
        
        raise_value = 2 #Start raise value at 2

        #Go around the table and have each player bet, raise or fold to see who plays intitially
        for player in self.order:
            #Print cards so they know
            print(f'Player {player} has cards {self.hands_dict[player].card1} and {self.hands_dict[player].card2}')
            #if player is second they are the big blind

            if player == self.order[0]:
                print(f'Player {player} is the big blind and must bet 2 chips')
                bets[player] += 2
                self.chips[player] -= 2

                bets[player], raise_value = self.player_action(player, bets[player], raise_value)
            else:
                bets[player], raise_value = self.player_action(player, bets[player], raise_value)
        
        #Check if there is only one player left, if so they win
        if len(self.players_unfolded) == 1:
            winner = self.players_unfolded[0]
            print(f'The winner is player {winner} and they win the pot of {sum(bets.values())} chips')
            self.chips[winner] += sum(bets.values())
            return(self.chips)
        
        #if a player has raised loop around until all players have called or folded
        while self.check_raise != -1:
            current_raiser = self.check_raise
            for player in self.order:
                if player == current_raiser:
                    break
                if player in self.players_unfolded and player not in self.all_in.keys():
                    bets[player], raise_value = self.player_action(player, bets[player], raise_value)
            #Check if there is only one player left, if so they win
            if len(self.players_unfolded) == 1:
                winner = self.players_unfolded[0]
                print(f'The winner is player {winner} and they win the pot of {sum(bets.values())} chips')
                self.chips[winner] += sum(bets.values())
                return(self.chips)
            #Reset check_raise to -1 to see if anyone raises again
            if self.check_raise == current_raiser:
                self.check_raise = -1
        #Reveal flop
        print(f'The flop is {self.community[0]}, {self.community[1]}, {self.community[2]}')

        for player in self.order:
            if player in self.players_unfolded and player not in self.all_in.keys():
                bets[player], raise_value = self.player_action(player, bets[player], raise_value)
        
        #Check if there is only one player left, if so they win
        if len(self.players_unfolded) == 1:
            winner = self.players_unfolded[0]
            print(f'The winner is player {winner} and they win the pot of {sum(bets.values())} chips')
            self.chips[winner] += sum(bets.values())
            return(self.chips)
        
        #Reveal turn
        print(f'The turn is {self.community[3]}')
        for player in self.order:
            if player in self.players_unfolded and player not in self.all_in.keys():
                bets[player], raise_value = self.player_action(player, bets[player], raise_value)

        #Check if there is only one player left, if so they win
        if len(self.players_unfolded) == 1:
            winner = self.players_unfolded[0]
            print(f'The winner is player {winner} and they win the pot of {sum(bets.values())} chips')
            self.chips[winner] += sum(bets.values())
            return(self.chips)
        
        #Reveal river
        print(f'The river is {self.community[4]}')
        for player in self.order and player not in self.all_in.keys():
            if player in self.players_unfolded:
                bets[player], raise_value = self.player_action(player, bets[player], raise_value)
        
        #Determine winner
        winner = self.get_winner(players_in_game = self.players_unfolded)

         #Add chips to winner
        total_pot = sum(bets.values())

        #Check if winner is all in, if they are the pot is split
        if type(winner) == list and any(player in self.all_in.keys() for player in winner):
            all_in_winners = []
            for player in winner:
                if player in self.all_in.keys():
                    print(f'Player {player} is all in and the pot is split between players {winner}')
                    all_in_winners.append(player)
            if len(all_in_winners) == 1:
                remaining_pot = 0
                for player in self.bets.keys():
                    if player != all_in_winners[0]:
                        if self.bets[player] > self.all_in[all_in_winners[0]]:
                            remaining_pot += self.bets[player] - self.all_in[all_in_winners[0]]
                if remaining_pot / (len(winner) - 1) > total_pot / len(winner): #If the remaining pot is greater than just splitting the pot, the all in player gets their all in amount and the rest of the pot is split between the other players
                    all_in_player = all_in_winners[0]
                    self.chips[all_in_player] += total_pot - remaining_pot
                    for player in winner:
                        if player != all_in_player:
                            self.chips[player] += remaining_pot / (len(winner) - 1)
                else:
                    for player in winner:
                        self.chips[player] += total_pot / len(winner)
            else:
                #Complicated edge case, just split the pot evenly although this is not technically correct, but it is a rare case and will be hard to implement correctly
                for player in winner:
                    self.chips[player] += total_pot / len(winner)        

                
        elif winner in self.all_in.keys():
            print(f'Player {winner} is all in and gets only as many chips as they put in, the rest of the pot is won by second place')
            remaining_pot = 0
            for player in self.bets.keys():
                if player != winner:
                    if self.bets[player] > self.all_in[winner]:
                        remaining_pot += self.bets[player] - self.all_in[winner]
            second_place = self.get_winner(players_in_game = [player for player in self.players_unfolded if player != winner])
            print(f'Player {second_place} wins the remaining pot of {remaining_pot} chips')
            self.chips[winner] += total_pot - remaining_pot
            self.chips[second_place] += remaining_pot
        else:
            if type(winner) == list:
                print(f'The winners are players {winner} and they split the pot of {total_pot} chips')
                for player in winner:
                    self.chips[player] += total_pot / len(winner)
            else:
                print(f'The winner is player {winner} and they win the pot of {total_pot} chips')
                self.chips[winner] += total_pot
        
        #Get hand type of winner
        hand_type, high_cards = self.get_value(self.hands_dict[winner])
        #print(f'\nThe winning hand is {hand_type} with high cards {high_cards} \n')
        #Subtract chips from losers

        return(self.chips)


class PokerEnv:
    """A lightweight RL environment built around the poker game simulator.

    This first version focuses on a simple two-player, preflop decision problem.
    The agent can fold, call, or raise. The opponent uses a simple heuristic
    policy, and the environment returns a reward based on the hand outcome.
    """

    def __init__(self, players=2, starting_stack=20, blind=2):
        self.players = players
        self.starting_stack = starting_stack
        self.blind = blind
        self.action_names = {0: "Fold", 1: "Call", 2: "Raise Small", 3: "Raise Big"}
        self.q_table = {}
        self.last_state = None

    def reset(self, card1=None, card2=None, dealer=1):
        if card1 is not None and card2 is not None:
            self.game = game(
                players=self.players,
                chip_dict={i: self.starting_stack for i in range(self.players)},
                dealer=dealer,
                card1=card1,
                card2=card2,
            )
        else:
            self.game = game(
                players=self.players,
                chip_dict={i: self.starting_stack for i in range(self.players)},
                dealer=dealer,
            )
        self.pot = self.blind
        self.current_to_call = self.blind
        if dealer == 0:
            self.agent_contribution = 0
            self.opponent_contribution = self.blind
        else:
            self.agent_contribution = self.blind
            self.opponent_contribution = 0
        
        self.done = False
        self.reward = 2
        return self._get_state()

    def _encode_card(self, card):
        values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        suits = {"Spades": 0, "Clubs": 1, "Hearts": 2, "Diamonds": 3}
        return values[card[0]] * 4 + suits[card[1]]

    def _get_state(self):
        player_hand = self.game.hands_dict[0]
        hand_strength = self._preflop_strength(player_hand)
        return(
            hand_strength,
            self.current_to_call - self.agent_contribution
        )
    def _get_opp_state(self):
            player_hand = self.game.hands_dict[1]
            hand_strength = self._preflop_strength(player_hand)
            return(
                hand_strength,
                self.current_to_call - self.opponent_contribution
            )
    
    def _card_value(self, card):
        values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        return values[card[0]]

    def _preflop_strength(self, hand):
        # Use the strengths df to determine the strength of the hand
        card1_value = hand.card1[0]
        card2_value = hand.card2[0]
        card1_suit = hand.card1[1]
        card2_suit = hand.card2[1]

        strengths_hand = strengths_df[(strengths_df['card1_value'] == card1_value) & 
                                       (strengths_df['card2_value'] == card2_value) & 
                                       (strengths_df['card1_suit'] == card1_suit) & 
                                       (strengths_df['card2_suit'] == card2_suit)]
        win_rate = strengths_hand['win_prob']
        
        if len(win_rate) == 0:
            print(f"Warning: Hand {hand.card1, hand.card2} not found in strengths_df. Defaulting to 0.5.")
            return 0.5
        return list(win_rate)[0]
    def _opponent_policy(self, action):
        """Set the basic opponent policy for the agent to learn against. The opponent will fold with a 20% chance if the agent raises small, 40% if big and will call if the agent calls."""
        if action == 0:
            return 1
        if action == 2:
            return 1 if np.random.rand() < 0.8 else 0
        if action == 3:
            return 1 if np.random.rand() < 0.6 else 0
        return 1 

    def _complex_opponent_policy(self, environment):
        """Set a a more complex opponent by having the agent learn against itself. Update policy every 1000 episodes"""
        pass
    def _resolve_showdown(self):
        winner = self.game.get_winner(players_in_game=[0, 1])
        if winner == 0:
            self.reward = self.pot - self.agent_contribution  # Agent wins the pot
        else:
            self.reward = -1 * self.agent_contribution  # Opponent wins the pot and agent loses their contribution
        return self.reward

    def step(self, action):
        if self.done:
            raise RuntimeError("Environment is already done. Call reset() first.")

        action = int(action)
        if action not in self.action_names:
            raise ValueError(f"Action must be one of {list(self.action_names.values())}")

        if action == 0:  # fold
            self.reward = -1.0
            self.done = True
            return self._get_state(), self.reward, self.done, {"winner": 1}

        # Agent calls or raises
        if action == 1:
            amount = self.current_to_call
        elif action == 2:
            amount = min(self.current_to_call + 2, self.game.chips[0])
        elif action == 3:
            amount = min(self.current_to_call + 10, self.game.chips[0])

        if amount > self.game.chips[0]:
            amount = self.game.chips[0]

        self.game.chips[0] -= amount
        self.agent_contribution += amount
        self.pot += amount
        self.current_to_call = max(self.current_to_call, amount)

        opponent_action = self._opponent_policy(action)
        if opponent_action == 0:  # opponent folds
            self.reward = self.pot - self.agent_contribution  # Agent wins the pot
            self.done = True
            return self._get_state(), self.reward, self.done, {"winner": 0}

        # Opponent calls if able
        if self.game.chips[1] >= self.current_to_call:
            self.game.chips[1] -= self.current_to_call
            self.opponent_contribution += self.current_to_call
            self.pot += self.current_to_call
        else:
            self.game.chips[1] = 0
            self.opponent_contribution += self.game.chips[1]

        self.reward = self._resolve_showdown()
        self.done = True
        return self._get_state(), self.reward, self.done, {"winner": 0 if self.reward > 0 else 1}

    def advanced_step(self, epsilon=0.2):
        """Modified version of the step function that allows for more complex opponent behavior, pitting the model agaisnt itself. Also allows for different dealers"""
        if self.done:
            raise RuntimeError("Environment is already done. Call reset() first.")

        if self.game.order[0] == 0:
            #Agent is dealer, opponent acts first
            opp_state = self._get_opp_state()
            opp_action = self.select_action(opp_state, epsilon=0.0)  # No exploration for opponent
            if opp_action == 0:  # opponent folds
                self.reward = self.pot - self.agent_contribution  # Agent wins the pot
                self.done = True
                state = self._get_state()
                action = 1
                return state, action, self._get_state(), self.reward, self.done, {"winner": 0}
            elif opp_action == 1:
                amount = self.current_to_call
            elif opp_action == 2:
                amount = min(self.current_to_call + 2, self.game.chips[1])
            elif opp_action == 3:
                amount = min(self.current_to_call + 10, self.game.chips[1])

            self.current_to_call = amount
            self.game.chips[1] -= amount
            self.opponent_contribution += amount - 2
            self.pot += amount - 2
            #player action in response
            state = self._get_state()
            action = self.select_action(state, epsilon=epsilon)

            if action == 0:  # fold
                self.reward = 0
                self.done = True
                return state, action, self._get_state(), self.reward, self.done, {"winner": 1}
            elif action == 1:
                amount = self.current_to_call
            elif action == 2:
                amount = min(self.current_to_call + 2, self.game.chips[0])
            elif action == 3:
                amount = min(self.current_to_call + 10, self.game.chips[0])

            self.current_to_call = amount
            self.game.chips[0] -= amount - self.agent_contribution
            self.agent_contribution += amount - self.agent_contribution
            self.pot += amount - self.agent_contribution
            
            #Go back to opponent if there was a raise
            if amount > self.current_to_call:

                #Opponent responds to raise
                opp_state = self._get_opp_state()
                opp_action = self.select_action(opp_state, epsilon=0.0)  # No exploration for opponent
                if opp_action == 0:  # opponent folds
                    self.reward = self.pot - self.agent_contribution  # Agent wins the pot
                    self.done = True
                    return state, action, self._get_state(), self.reward, self.done, {"winner": 0}
                elif opp_action >= 1:
                    amount = self.current_to_call
                    #Opponent can only call or fold, on second go around for simplicity
                    self.game.chips[1] -= amount - self.opponent_contribution
                    self.opponent_contribution += amount - self.opponent_contribution
                    self.pot += amount - self.opponent_contribution

            self.reward = self._resolve_showdown()
            self.done = True
            return state, action, self._get_state(), self.reward, self.done, {"winner": 0 if self.reward > 0 else 1}
                
        else:
            state = self._get_state()
            action = self.select_action(state, epsilon=epsilon)
            
            if action == 0:  # fold
                self.reward = 0
                self.done = True
                return state, action, self._get_state(), self.reward, self.done, {"winner": 1}
            elif action == 1:
                amount = self.current_to_call
            elif action == 2:
                amount = min(self.current_to_call + 2, self.game.chips[0])
            elif action == 3:
                amount = min(self.current_to_call + 10, self.game.chips[0])

            self.current_to_call = amount
            self.game.chips[1] -= amount
            self.agent_contribution += amount - 2
            self.pot += amount - 2

            #opponent action in response
            opp_state = self._get_opp_state()
            opp_action = self.select_action(opp_state, epsilon=0.0)  # No exploration for opponent
            if opp_action == 0:  # opponent folds
                self.reward = self.pot - self.agent_contribution  # Agent wins the pot
                self.done = True
                return state, action, self._get_state(), self.reward, self.done, {"winner": 0}
            elif opp_action == 1:
                amount = self.current_to_call
            elif action == 2:
                amount = min(self.current_to_call + 2, self.game.chips[0])
            elif action == 3:
                amount = min(self.current_to_call + 10, self.game.chips[0])

            self.game.chips[1] -= amount - self.opponent_contribution
            self.opponent_contribution += amount - self.opponent_contribution
            self.pot += amount - self.opponent_contribution
            self.current_to_call = amount
            if amount > self.current_to_call:
                #Go back to agent is there was a raise
                state_2 = self._get_state()
                action_2 = self.select_action(state_2, epsilon=epsilon)
                if action_2 == 0:  # fold
                    self.reward = 0
                    self.done = True
                    return state, action, self._get_state(), self.reward, self.done, {"winner": 1}
                elif action_2 >= 1:
                    action_2 = 1 #For simplicty only call or fold to prevent infinite loop, but this could be improved in future versions
                    amount = self.current_to_call
                    self.game.chips[1] -= amount - self.agent_contribution
                    self.agent_contribution += amount - self.agent_contribution
                    self.pot += amount - self.agent_contribution

            self.reward = self._resolve_showdown()
            self.done = True
            return state, action, self._get_state(), self.reward, self.done, {"winner": 0 if self.reward > 0 else 1}

        
    def _get_q_value(self, state, action):
        if state not in self.q_table:
            self.q_table[state] = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
        return self.q_table[state][action]

    def _set_q_value(self, state, action, value):
        if state not in self.q_table:
            self.q_table[state] = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
        self.q_table[state][action] = value

    def select_action(self, state, epsilon=0.2):
        if np.random.rand() < epsilon:
            return np.random.choice([0, 1, 2, 3])
        q_values = self.q_table.get(state, {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0})
        best_action = max(q_values, key=q_values.get)
        return best_action

    def train(self, episodes=2000, alpha=0.1, gamma=0.95, epsilon=0.2, epsilon_decay=0.9995, min_epsilon=0.05, simple_opponent=True):
        if simple_opponent: 
            rewards = []
            for episode in range(episodes):
                state = self.reset()
                total_reward = 0.0
                done = False
                while not done:
                    action = self.select_action(state, epsilon)
                    next_state, reward, done, info = self.step(action)
                    old_value = self._get_q_value(state, action)
                    best_next_value = max(self.q_table.get(next_state, {0: 0.0, 1: 0.0, 2: 0.0, 3 : 0.0}).values())
                    new_value = old_value + alpha * (reward + gamma * best_next_value - old_value)
                    self._set_q_value(state, action, new_value)
                    total_reward += reward
                    state = next_state
                rewards.append(total_reward)
                epsilon = max(min_epsilon, epsilon * epsilon_decay)
            return rewards
        else:
            rewards = []
            for episode in range(episodes):
                state = self.reset(dealer=0 if np.random.rand() < 0.5 else 1) #Make dealer random to avoid biasing agent
                total_reward = 0.0
                done = False
                while not done:
                    state, action, next_state, reward, done, info = self.advanced_step(epsilon=epsilon)
                    state = self._get_state()
                    old_value = self._get_q_value(state, action)
                    best_next_value = max(self.q_table.get(next_state, {0: 0.0, 1: 0.0, 2: 0.0, 3 : 0.0}).values())
                    new_value = old_value + alpha * (reward + gamma * best_next_value - old_value)
                    self._set_q_value(state, action, new_value)
                    total_reward += reward
                    state = next_state
                rewards.append(total_reward)
                epsilon = max(min_epsilon, epsilon * epsilon_decay)
            return rewards

    def get_policy(self):
        return {state: max(values, key=values.get) for state, values in self.q_table.items()}
    def save_model(self, path):
        """Save the Q-table to `path` using pickle."""
        with open(path, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load_model(self, path):
        """Load the Q-table from `path` using pickle."""
        with open(path, 'rb') as f:
            self.q_table = pickle.load(f)

    def make_decision(self, card1, card2, text=True):
        self.reset(card1, card2)
        state = self._get_state()
        action = self.select_action(state, epsilon=0.0)  # No exploration during decision making
        if text:
            return self.action_names[action]
        else: 
            return action
