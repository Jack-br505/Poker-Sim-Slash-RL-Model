import sys
sys.path.append('RL Agent')
from Preflop import PokerEnv
from Flop import advancedPokerEnv
import time
import os

if __name__ == '__main__':
    env = advancedPokerEnv()
    #If a model exists, load it, otherwise train a new model
    model_path = 'models/q_table_after_flop.pkl'
    if os.path.exists(model_path):
        env.load_model(model_path)
        print(f'Model loaded from {model_path}')
    
    start_time = time.perf_counter()
    rewards = env.train(episodes=1000000, alpha=0.1, gamma=0.95, epsilon=0.2, epsilon_decay=0.99995, min_epsilon=0.05, simple_opponent=False)
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
card1 = ['5', 'Hearts']
card2 = ['8', 'Diamonds']
community = {0: ["J", "Hearts"], 1:["5", "Clubs"], 2:['7', "Spades"], 3:None,4:None}
print('\nDecision with trained model:')
print(env.make_decision(card1, card2, community))