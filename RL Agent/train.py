import sys
sys.path.append('RL Agent')
from Preflop import PokerEnv
import os

if __name__ == '__main__':
    env = PokerEnv()
    rewards = env.train(episodes=40000)
    print('Training complete')
    print('Average reward:', sum(rewards) / len(rewards))
    print('Policy size:', len(env.get_policy()))

    # Save trained Q-table
    models_dir = 'models'
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'q_table.pkl')
    env.save_model(model_path)
    print(f'Model saved to {model_path}')

#Test a random case
card1 = ['A', 'Diamonds']
card2 = ['K', 'Hearts']
print('\nDecision with trained model:')
print(env.make_decision(card1, card2))

# Example: load into a new environment and use the saved model
new_env = PokerEnv()
new_env.load_model(model_path)
print('Loaded policy size:', len(new_env.get_policy()))
print('Decision from loaded model:', new_env.make_decision(card1, card2))
