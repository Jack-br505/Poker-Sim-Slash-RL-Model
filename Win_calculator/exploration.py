import pandas as pd

# Load the CSV file into a DataFrame
try:
    df = pd.read_csv("4_player_results.csv")
    #print(df.head())  # Print the first few rows of the DataFrame to verify it loaded correctly
except FileNotFoundError:
    print("The file '4_player_results.csv' was not found. Please make sure it exists in the current directory.")

print(df['hand'][df['win_prob'] == df['win_prob'].max()])
print(df['hand'][df['win_prob'] == df['win_prob'].min()])