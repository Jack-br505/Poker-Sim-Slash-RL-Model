from Deck_Hand import deck, hand
import random
import numpy as np
random.seed()
class quick_game():
    """
    Creates a quick game to simulate probabilities of hands and of a hand winning in that game without any raising / folding. The game has no turns
    just whoever has the best hand overall

    inputs:
    -------
    players: int: Number of players in this specific game between 2 and 8

    card1: list of length 2: the first card in order ['value', 'suit'] of the players hand, can be set to None if random value desired
    
    card2: list of length 2: the second card in order ['value', 'suit'] of the players hand, can be set to None if random value desired

    community: dict of length 5: a dictionary containing lists for all the wanted specified community cards, values can be set to None if wanted to be random

    """

    def __init__(self, players = 4, card1 = None, card2 = None, community = None):
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
        
    def get_value(self, hand):
        """Get the value of the hand within this game
        
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

    def get_winner(self):
        hands = {}
        highs = {}
        for i in range(len(self.hands_dict.values())):
            hands[i], highs[i] = self.get_value(self.hands_dict[i])
            #print(hands[i], highs[i])
        heirarchy = {}
        index = 0
        for hand in hands.values():
            if hand['Straight Flush'] != False:
                heirarchy[index] = 8
            elif hand['Four-of-a-Kind'] != False:
                heirarchy[index] = 7
            elif hand['Full House'] != False:
                heirarchy[index] = 6
            elif hand['Flush'] != False:
                heirarchy[index] = 5
            elif hand['Straight'] != False:  
                heirarchy[index] = 4
            elif hand['Three-of-a-Kind'] != False:
                heirarchy[index] = 3
            elif hand['Two-Pair'] != False:
                heirarchy[index] = 2
            elif hand['Pair'] != False:
                heirarchy[index] = 1
            else:
                heirarchy[index] = 0
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

def many_games(n, players = 4, card1 = None, card2 = None, community = None, print_output = True):
    """
    Runs many trials of a specific scenario and gets the aggregate probabilities in this scenario

    Inputs:
    -------
    n : int : number of runs of the trial

    players: int : number of players in game
    
    card1 : list : starting card for the player
    card2: list : starting card for the player

    community : dict : The community cards if specified
    """
    if community is None:
        c = None
    else:
        c = community
    
    pair_counter = 0
    two_pair_counter = 0
    three_counter = 0
    straight_counter = 0
    flush_counter = 0
    full_counter = 0
    four_counter = 0 
    straight_flush_counter = 0 

    #Find wins and losses
    wins = 0
    losses = 0
    ties_w_player = 0
    
    for i in range(n):
        new_game = quick_game(players=players, card1=card1, card2=card2, community=c)

        output, ignore = new_game.get_value(new_game.hands_dict[0])

        if output["Pair"]:
            pair_counter += 1
            if output["Two-Pair"]:
                two_pair_counter += 1
            if output["Three-of-a-Kind"]:
                three_counter += 1
                if output["Full House"]:
                    full_counter += 1
            if output["Four-of-a-Kind"]:
                four_counter += 1
        if output["Straight"]:
            straight_counter += 1
        if output["Flush"]:
            flush_counter += 1
            if output["Straight Flush"]:
                straight_flush_counter += 1
        #Find win probability of player with specified hand
        winner = new_game.get_winner()
        if winner == 0:
            wins += 1
        elif type(winner) == list and 0 in winner:
            ties_w_player += 1
        else:
            losses += 1

    if print_output:    
        if card1 != None:
            print(f"Starting cards: {card1[0]} of {card1[1]} and {card2[0]} of {card2[1]} \n")
        print(f"Pair probability: {pair_counter / n}")
        print(f"Two-Pair probability: {two_pair_counter / n}")
        print(f"Three of a kind probability: {three_counter / n}")
        print(f"Flush probability: {flush_counter / n}")
        print(f"Straight probability: {straight_counter / n}")
        print(f"Full House probability: {full_counter / n}")
        print(f"Four of a kind probability: {four_counter / n}")
        print(f"Straight Flush probability: {straight_flush_counter / n}")
    
        print("\n #Probabilities of winning with this hand in this scenario: \n")
        print("Win probability: ", wins / n)
        print("Loss probability: ", losses / n)
        print("Tie probability: ", ties_w_player / n)
    else:
        info_dict = {"Pair": pair_counter / n, "Two-Pair": two_pair_counter / n, "Three-of-a-Kind": three_counter / n, "Straight": straight_counter / n, "Flush": flush_counter / n, "Full House": full_counter / n, "Four-of-a-Kind": four_counter / n, "Straight Flush": straight_flush_counter / n, "Win Probability": wins / n, "Loss Probability": losses / n, "Tie Probability": ties_w_player / n}
        return(info_dict)



