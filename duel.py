# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2", "numpy==2.3.4"]
# ///
"""Match direct entre deux réseaux (A et B), chacun jouant une fois de chaque couleur par graine."""

import argparse
import random
from pathlib import Path

import chess

from echecs import ChessGame
from selfplay import Network, search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('poids_a', type=Path)
    parser.add_argument('poids_b', type=Path)
    parser.add_argument('--simulations-a', type=int, default=64)
    parser.add_argument('--simulations-b', type=int, default=64)
    parser.add_argument('--paires', type=int, default=50)
    parser.add_argument('--seed', type=int, default=3000)
    parser.add_argument('--demi-coups', type=int, default=60)
    args = parser.parse_args()
    if min(args.simulations_a, args.simulations_b, args.paires) < 1 or args.demi_coups < 0:
        parser.error('Les quantités doivent être positives.')
    a, b = Network.load(args.poids_a), Network.load(args.poids_b)
    scores = []
    for seed in range(args.seed, args.seed + args.paires):
        for a_white in (True, False):
            game = ChessGame(max_plies=args.demi_coups)
            rng = random.Random(seed)
            while not game.outcome:
                turn_a = (game.player == chess.WHITE) == a_white
                visits = search(game, a if turn_a else b, args.simulations_a if turn_a
                                else args.simulations_b, rng)
                game.play(max(visits, key=visits.get))
            scores.append(0.5 if game.draw else float(game.winner == a_white))
    print(f'A : {scores.count(1)} victoires, {scores.count(0.5)} nuls, {scores.count(0)} défaites, '
          f'{sum(scores):g} points sur {len(scores)}')


if __name__ == '__main__':
    main()
