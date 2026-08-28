# Poker Sim Project
### Jack Brach - Undergraduate Data Science Student at Michigan State University

Creates a working simulation of a simple game of Texas Hold-em Poker in python.

Uses this simulation to find the probabilities of each hand and the overall winning probability of the hand in a 4 person game

Then uses the simulation to train a Q-Learning algorithm with 4 possible decisions: fold, call, raise small, and raise big. 

## Base Sim

A basic simulation of poker without betting or any user actions. Has classes for hands, deck, and the base logic for determining a winner in each game, 
used for calculating the probability of different hands and winning chances.

## Betting Sim

A modification of the base sim but now with user actions and standard betting actions of poker

## RL Agent

Uses a q learning model to analyze the game state and make the best decision. Models are contained in pickle files in models directory. Different models for the before and after community cards are revealed, as the preflop model uses calculated win percentage from monte carlo simulations, while that wasn't possible for community cards. 

## Webapp

Application buit using FastAPI, runs monte carlo simulations of an inputed scenario and has a page where users can play against the q learning model

## Win Calculator

Runs monte carlo simulations of all possible conditions and returns the win probabilities.

