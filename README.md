Multi-Agent Chess Game

Overview

This project implements the AlphaZero Reinforcement Learning (RL) algorithm for a multi-agent chess environment. The chess game is designed as a Gym-like environment to facilitate simulation and experimentation with RL techniques. The goal of this project is to demonstrate how AlphaZero can be used to train agents capable of playing chess at a competitive level.

Key Features

AlphaZero Algorithm: Implementation of AlphaZero’s core principles, including Monte Carlo Tree Search (MCTS) and self-play.

Multi-Agent Framework: Simulates the interactions between two agents in a competitive chess environment.

Gym-Style Environment: Designed to be modular and extensible, following the OpenAI Gym API principles for RL environments.

Customizable Training: Easily configurable training parameters for experimenting with different AlphaZero variations.

Installation

Clone the repository:

git clone https://github.com/highcansavci/multi-agent-chess-game.git
cd multi-agent-chess-game

Install dependencies:

pip install torch pygame vidmaker

Usage

Running the Environment

You can test the chess environment by running the following script:

python alphazero/train.py

This will initialize a chess game and allow you to train with AlphaZero code.

python alphazero/inference.py

This will initialize a chess game and allow you to infer with AlphaZero model.

Training AlphaZero

To train an AlphaZero agent from scratch, execute:

python alphazero/train.py

Evaluation

Evaluate a trained AlphaZero model against another agent:

python alphazero/inference.py

Results

The agents trained using AlphaZero demonstrate:

Improved Strategic Depth: Agents learn complex chess strategies through self-play.

High Adaptability: Trained agents are capable of competing with varying levels of opponent strength.


Graph: Cumulative reward and MCTS search depth over training epochs.

Video Demo

Watch a demonstration of the trained AlphaZero agent in action:
[alphazero/alphazero.mp4]

Future Work

Experiment with hybrid architectures combining IRL and RL.

Contributing

Contributions are welcome! If you have ideas for improvements or new features, feel free to:

Fork the repository.

Create a feature branch.

Submit a pull request with a detailed explanation of your changes.

License

This project is licensed under the MIT License.

Acknowledgments

AlphaZero Paper by DeepMind

OpenAI Gym

Special thanks to the open-source community for inspiration and guidance.



