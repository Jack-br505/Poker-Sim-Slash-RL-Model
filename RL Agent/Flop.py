import sys
import pickle
import os
import time
import numpy as np
sys.path.append('RL Agent')
from Preflop import game, PokerEnv

class advancedPokerEnv(PokerEnv):
    """Use the preflop decision as a base and make decisions after the flop, turn and river"""
    def __init__(self):
        super().__init__()
        


    def determine_strength(self, hand, revealed_cards):
        """Cannot use monte carlo sims for the flop and after, determine if hand has a pair, triple, etc, or is close to a flush or straight
        
        inputs:
        hand: the players hand, type hand
        revealed cards: int: the amount of community cards revealed

        Designate a number to the hand strength: 2-14 = high card; 15-27=pair; 28-40=two-pair; 
        41-53=triple; 80-92 = straight; 93-105 = flush; 106-118 = full house
        119-131 = four of a kind; 132-144 = straight flush

        if one off a straight or flush use a different category, 0 nothing, 1 almost straight, 2 almost flush, 3 almost flush and almost straight
        """
        conv_dict =  {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        hand_strength_num = 2
        almost_num = 0
        

        community_values = []
        community_suits = []
        for i in range(revealed_cards):
            community_values.append(self.game.community[i][0])
            community_suits.append(self.game.community[i][1])
        
        #Get the defaualt higher card in hand:
        if conv_dict[hand.card1[0]] >= conv_dict[hand.card2[0]]:
            high_card = conv_dict[hand.card1[0]]
        else:
            high_card = conv_dict[hand.card2[0]]

        hand_strength_num = high_card

        #Check for a pair
        for hand_val in hand.get_vals():
            if hand_val in community_values:
                #Figure out pair, two-pair or triple
                #Find frequency of value
                freq = 0
                for com_val in community_values:
                    if com_val == hand_val:
                        freq += 1
                if freq == 1: #Only a pair
                    #Check if there already is a pair or triple
                    if hand_strength_num > 14:
                        #Check for full house
                        if hand_strength_num > 41 and hand_strength_num < 119:
                            hand_strength_num += 65
                            return([hand_strength_num, 0]) #Full house and 4 of a kind are greater than straight/flush so return automatically
                        else: #Two-pair
                            if conv_dict[hand_val] + 12 > hand_strength_num: #This card is higher than other pair
                                hand_strength_num = conv_dict[hand_val] + 24
                            else:
                                hand_strength_num += 12
                    else:
                        #THis is first pair
                        hand_strength_num = conv_dict[hand_val] + 12
                elif freq == 2:
                    #Check if there already is a pair or triple
                    if hand_strength_num > 14:
                        #Check for full house
                        if hand_strength_num > 41 and hand_strength_num < 119: #Already a triple
                            if conv_dict[hand_val] + 36 > hand_strength_num: #This card is higher than other pair
                                    hand_strength_num = conv_dict[hand_val] + 104
                                    return([hand_strength_num, 0])
                            else:
                                hand_strength_num += 65
                        else: #There is already a pair so full house
                            hand_strength_num = conv_dict[hand_val] + 104
                            return([hand_strength_num, 0])
                    else:
                        #THis is first pair
                        hand_strength_num = conv_dict[hand_val] + 36
                elif freq == 3:
                    hand_strength_num = conv_dict[hand_val] + 116 #FOur of a kind
                    return([hand_strength_num, 0])
        
        #Look for a straight

        #Put all cards in a list and use corresponding integer for values
        hand_vals = hand.get_vals()

        all_vals = hand_vals + community_values
        conv_vals = []
        for val in all_vals:
            #Check if val in list
            if conv_dict[val] not in conv_vals:
                conv_vals.append(conv_dict[val])
        #sort list
        conv_vals.sort()

        #print(conv_vals)
        #Check for a straight
        a = 0
        streaks = {0:2} #streaks is a dictionary with the key being the length of the streak and value being the high card, set deafult value for 0 so dict isnt empty
        while a < len(conv_vals) - 4:
            b = a
            streak = 1
            #Set a default for h_card
            h_card = 2
            while b < len(conv_vals) - 1:
                if conv_vals[b+1] == conv_vals[b] + 1:
                    b += 1
                    a += 1
                    streak += 1
                else:
                    h_card = conv_vals[b]
                    break
            a += 1
            streaks[streak] = h_card
        
        #Check if there was a streak of 5
        if max(list(streaks.keys())) == 5:
            hand_strength_num = streaks[5] + 78
        elif max(list(streaks.keys())) == 4:
            almost_num = 1

        #Check for flushes
        suit_frequency = {"Clubs" : 0, "Spades" : 0, "Hearts": 0, "Diamonds" : 0}
        for item in community_suits: #Get frequency of each suit 
            suit_frequency[item] += 1

        #Find suits of hand
        if hand.card1[1] == hand.card2[1]:
            target_suit = hand.card1[1]
    
            if suit_frequency[target_suit] >= 3: #there are 5 community cards of target suit so 5 total
                hand_strength_num = high_card + 104
            elif suit_frequency[target_suit] == 2: #4 total same suit
                if almost_num == 1:
                    almost_num = 3
                else:
                    almost_num = 2
        else:
            target_suit = hand.card1[1]

            if suit_frequency[target_suit] >= 4: #there are 4 community cards of target suit so 5 total
                hand_strength_num = conv_dict[hand.card1[0]] + 104
            elif suit_frequency[target_suit] == 3: #4 total same suit
                if almost_num == 1:
                    almost_num = 3
                else:
                    almost_num = 2

            #Repeat for card 2
            target_suit = hand.card2[1]

            if suit_frequency[target_suit] >= 4: #there are 4 community cards of target suit so 5 total
                #Check if flush is already fufilled
                if hand_strength_num < 106:
                    hand_strength_num = conv_dict[hand.card2[0]] + 104
                if conv_dict[hand.card2[0]] == high_card: #
                    hand_strength_num = high_card + 104
            elif suit_frequency[target_suit] == 3: #4 total same suit
                if almost_num == 1 or almost_num == 3:
                    almost_num = 3
                else:
                    almost_num = 2
        
        #Return an array of the strength_num and the almost num
        return([hand_strength_num, almost_num])

    def _get_state(self):
        hand_strength = self.determine_strength(self.game.hands_dict[0], self.rev_cards)
        return(
            hand_strength[0],
            hand_strength[1],
            self.rev_cards,
            self.current_to_call - self.agent_contribution
        )

    def reset(self, card1=None, card2=None, community = {0: None, 1:None, 2:None,3:None, 4:None}):
        if card1 is not None and card2 is not None:
            self.game = game(
                players=self.players,
                chip_dict={i: self.starting_stack for i in range(self.players)},
                dealer=1,
                card1=card1,
                card2=card2,
                community=community
            )
        else:
            self.game = game(
                players=self.players,
                chip_dict={i: self.starting_stack for i in range(self.players)},
                dealer=1,
            )
        #Set to a scenario where each player has contribuited 2 chips
        self.pot = 4
        self.current_to_call = 2
        self.agent_contribution = 2
        self.opponent_contribution = 2
        self.done = False
        self.reward = 4
        return self._get_state()

    def _opponent_policy(self, action):
        """Set the basic opponent policy for the agent to learn against. The opponent will fold with a 20% chance if the agent raises small, 
        40% if big and will call if the agent calls. Adjust fold chances based off hand strength of opponent"""
        opp_strength = self.determine_strength(self.game.hands_dict[1], self.rev_cards)


        if action == 2:
            if opp_strength[0] > 14 or (self.rev_cards == 3 and opp_strength[1] > 0):
                return 1 if np.random.rand() < 0.95 else 0 #If opponent has a good hand and raise is small, small chance of folding
            elif opp_strength[0] <= 14 and self.rev_cards == 5:
                return 1 if np.random.rand() < 0.25 else 0 #If opponent has a bad hand and you raise, they likely fold
            else:
                return 1 if np.random.rand() < 0.75 else 0 #Higher chance of folding if opponent has a bad hand
        if action == 3:
            if opp_strength[0] > 14 or (self.rev_cards == 3 and opp_strength[1] > 0):
                return 1 if np.random.rand() < 0.85 else 0 #If opponent has a good hand and raise is small, small chance of folding
            elif opp_strength[0] <= 14 and self.rev_cards == 5:
                return 1 if np.random.rand() < 0.05 else 0 #If opponent has a bad hand and you raise, they likely fold
            else:
                return 1 if np.random.rand() < 0.6 else 0 #Higher chance of folding if opponent has a bad hand
        return 1 
    
    def step(self, action):
        if self.done:
            raise RuntimeError("Environment is already done. Call reset() first.")

        action = int(action)
        if action not in self.action_names:
            raise ValueError(f"Action must be one of {list(self.action_names.values())}")

        if action == 0:  # fold
            self.reward = -2.0
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
    
    def train(self, episodes=50000, alpha=0.1, gamma=0.95, epsilon=0.2, epsilon_decay=0.9995, min_epsilon=0.05):
        rewards = []
        for episode in range(episodes):
            for i in [3, 4, 5]:
                self.rev_cards = i
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

    def make_decision(self, card1=None, card2=None, community={0: None, 1:None, 2:None, 3:None,4:None}):
        self.reset(card1, card2, community)
        state = self._get_state()
        action = self.select_action(state, epsilon=0.0)  # No exploration during decision making
        return self.action_names[action]

if __name__ == '__main__':
    env = advancedPokerEnv()
    #If a model exists, load it, otherwise train a new model
    model_path = 'models/q_table_after_flop.pkl'
    if os.path.exists(model_path):
        env.load_model(model_path)
        print(f'Model loaded from {model_path}')
    
    start_time = time.perf_counter()
    rewards = env.train(episodes=1000)
    print(f"Training time: {-start_time + time.perf_counter()}")
    print('Training complete')
    print('Average reward:', sum(rewards) / len(rewards))
    print('Policy size:', len(env.get_policy()))

    # Save trained Q-table
    models_dir = 'models'
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'q_table_after_flop.pkl')
    env.save_model(model_path)
    print(f'Model saved to {model_path}')


#Test a random case
card1 = ['A', 'Diamonds']
card2 = ['K', 'Hearts']
community = {0: ["3", "Clubs"], 1:["K", "Spades"], 2:['5', "Hearts"], 3:None,4:None}
print('\nDecision with trained model:')
print(env.make_decision(card1, card2, community))
