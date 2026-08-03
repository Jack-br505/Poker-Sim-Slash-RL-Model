import csv
import sys
sys.path.insert(0, '/Users/jackbrach/dev/Poker_Sim/Base_Sim')
from Deck_Hand import hand, deck
from Game import quick_game, many_games


#Get a proability of winning for every hand combination in a 4 plyaer game with no community cards specified.
four_player_results = []

default_deck = deck()

#Get a list of all the cards in an array of format [<card_value>, <suit>]
default_deck_cards = []
for key in default_deck.vals.keys():
    card = [default_deck.vals[key], default_deck.suits[key]]
    default_deck_cards.append(card)


n = 10000

for card1 in default_deck_cards:
    for card2 in default_deck_cards:
        if card1 != card2:
            #Create dictionary to hold results for this hand combination
            results = {}
            #Use tuple for name of hand combination
            hand1_tuple = (card1, card2)
            results['hand'] = hand1_tuple

            sim_results = many_games(n, card1=card1, card2=card2, community=None, print_output=False)
            #Get win probability for this hand combination and add to results dictionary
            results['win_prob'] = sim_results['Win Probability']
            results['tie_prob'] = sim_results['Tie Probability']
            results['loss_prob'] = sim_results['Loss Probability']

            #Get different hand probabilities for this hand combination and add to results dictionary
            results['pair_prob'] = sim_results['Pair']
            results['two_pair_prob'] = sim_results['Two-Pair']
            results['three_of_a_kind_prob'] = sim_results['Three-of-a-Kind']
            results['straight_prob'] = sim_results['Straight']
            results['flush_prob'] = sim_results['Flush']
            results['full_house_prob'] = sim_results['Full House']
            results['four_of_a_kind_prob'] = sim_results['Four-of-a-Kind']
            results['straight_flush_prob'] = sim_results['Straight Flush']

            #Keep track of sim number
            results['n_simulations'] = n
            four_player_results.append(results)

#If the csv already exists find the mean of the win probabilities for each hand combination and update the results with the new mean. This way we can run more simulations and get more accurate results without losing the previous results.
try:    
    with open("4_player_results.csv", "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        existing_results = list(reader)

    #Create a dictionary to hold the existing results for easy lookup
    existing_results_dict = {tuple(row['hand'].strip("()").split(", ")): row for row in existing_results}

    #Update the results with the new mean win probabilities
    for result in four_player_results:
        hand_tuple = result['hand']
        if str(hand_tuple) in existing_results_dict:
            existing_result = existing_results_dict[str(hand_tuple)]
            #Get number of simulations for existing results and new results to calculate the new mean win probability and other probabilities
            n_existing = int(existing_result['n_simulations'])
            n_new = result['n_simulations']
            total_n = n_existing + n_new
            for key in result.keys():
                if key != 'hand' or key != 'n_simulations':
                    existing_value = float(existing_result[key])
                    new_value = float(result[key])
                    #Calculate the new mean value
                    mean_value = (existing_value * n_existing + new_value * n_new) / total_n
                    #Update the csv with the new mean value
                    existing_result[key] = mean_value
            #Update the number of simulations for this hand combination            
            existing_result['n_simulations'] = total_n
        else:
            #If this hand combination does not exist in the existing results, add it to the existing results
            existing_results.append(result)

except FileNotFoundError:
    #If the file does not exist, we will create it with the new results
   # Write to the CSV file
    with open("4_player_results.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(results.keys()))
    
        writer.writeheader()  # Writes the header row
        writer.writerows(four_player_results)  # Writes all data rows

