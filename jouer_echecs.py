# /// script
# requires-python = ">=3.10"
# dependencies = ["chess==1.11.2", "numpy==2.3.4; python_version >= '3.11'", "numpy==2.2.6; python_version < '3.11'"]
# ///
"""Échecs en terminal : humain contre MCTS à rollouts ou contre le réseau entraîné."""

import argparse
import random
from pathlib import Path

import chess

from echecs import ChessGame
from mcts import mcts_move


def display(board):
    rows = str(board).splitlines()
    print()
    for rank, row in zip(range(8, 0, -1), rows):
        print(rank, row)
    print('  a b c d e f g h\n')


def parse(board, text):
    for parser in (board.parse_san, board.parse_uci):
        try:
            return parser(text)
        except ValueError:
            pass
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--couleur', choices=['blancs', 'noirs'], default='blancs',
                        help="couleur de l'humain (défaut : blancs)")
    parser.add_argument('--agent', choices=['rollouts', 'reseau'], default='reseau')
    parser.add_argument('--poids', type=Path, default=Path('resultats/selfplay-60/reseau.npz'))
    parser.add_argument('--simulations', type=int, default=32)
    parser.add_argument('--demi-coups', type=int, default=60,
                        help='horizon de la variante, 0 pour les échecs standard (défaut : 60)')
    parser.add_argument('--seed', type=int)
    args = parser.parse_args()
    if args.simulations < 1 or args.demi_coups < 0:
        parser.error('--simulations doit être positif et --demi-coups positif ou nul')
    if args.agent == 'reseau':
        from selfplay import Network, search
        network = Network.load(args.poids)
    rng = random.Random(args.seed)
    human = args.couleur == 'blancs'
    game = ChessGame(max_plies=args.demi_coups)
    display(game.board)
    while not game.outcome:
        if game.player == human:
            try:
                text = input('Votre coup (SAN ou UCI, ex. e4 ou e2e4) : ').strip()
            except EOFError:
                print('\nPartie interrompue.')
                return
            move = parse(game.board, text)
            if move is None:
                print('Coup illégal ou illisible, réessayez.')
                continue
        else:
            if args.agent == 'reseau':
                visits = search(game, network, args.simulations, rng)
                move = max(visits, key=visits.get)
            else:
                move = mcts_move(game, rng, args.simulations)
            print(f'Agent joue {game.board.san(move)}.')
        game.play(move)
        display(game.board)
    print(f'{game.outcome.result()} ({game.outcome.termination.name})')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nPartie interrompue.')
