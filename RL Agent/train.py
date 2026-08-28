import sys
sys.path.append('RL Agent')
from Preflop import PokerEnv
import os

if __name__ == '__main__':
    env = PokerEnv()
    env.load_model('RL Agent/models/pre_flop_q_table2.pkl')  # Load the pre-trained model if it exists
    rewards = env.train(episodes=1000, simple_opponent=True)  # Set simple=False to use the new training method
    print('Training complete')
    print('Average reward:', sum(rewards) / len(rewards))
    print('Policy size:', len(env.get_policy()))

    # Save trained Q-table to RL Agent/models/pre_flop_q_table2.pkl
    env.save_model('RL Agent/models/pre_flop_q_table2.pkl')
   
#Test a random case
card1 = ['10', 'Hearts']
card2 = ['A', 'Diamonds']
print('\nDecision with trained model:')
print(env.make_decision(card1, card2))
