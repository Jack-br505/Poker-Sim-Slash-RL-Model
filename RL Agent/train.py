import sys
sys.path.append('RL Agent')
from Preflop import PokerEnv
import os

if __name__ == '__main__':
    env = PokerEnv()
    env.load_model('RL Agent/models/pre_flop_q_table.pkl')  # Load the pre-trained model if it exists
    rewards = env.train(episodes=20, simple_opponent=False)  # Set advanced=True to use the new training method
    print('Training complete')
    print('Average reward:', sum(rewards) / len(rewards))
    print('Policy size:', len(env.get_policy()))

    # Save trained Q-table
    models_dir = 'models'
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'pre_flop_q_table.pkl')
    env.save_model(model_path)
    print(f'Model saved to {model_path}')

#Test a random case
card1 = ['K', 'Diamonds']
card2 = ['7', 'Hearts']
print('\nDecision with trained model:')
print(env.make_decision(card1, card2))
