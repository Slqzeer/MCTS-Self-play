# /// script
# requires-python = ">=3.10"
# dependencies = ["chess==1.11.2"]
# ///
"""Chronométrer des parties complètes de MCTS contre lui-même aux échecs."""

import argparse
import json
import random
from pathlib import Path
from time import perf_counter

import chess

from mcts import mcts_move


class ChessGame:
    def __init__(self, board=None):
        self.board = chess.Board() if board is None else board
        self.outcome = self.board.outcome()

    def copy(self):
        # L'historique est nécessaire à la détection des répétitions.
        return ChessGame(self.board.copy())

    @property
    def player(self):
        return self.board.turn

    @property
    def winner(self):
        return self.outcome.winner if self.outcome else None

    @property
    def draw(self):
        return self.outcome is not None and self.outcome.winner is None

    def legal_moves(self):
        return [] if self.outcome else list(self.board.legal_moves)

    def play(self, move):
        if self.outcome or not self.board.is_legal(move):
            raise ValueError("Coup illégal")
        self.board.push(move)
        self.outcome = self.board.outcome()


def play_game(seed, simulations):
    rng = random.Random(seed)
    game = ChessGame()
    start = perf_counter()
    while game.outcome is None:
        game.play(mcts_move(game, rng, simulations))
    seconds = perf_counter() - start
    return dict(seed=seed, simulations=simulations, resultat=game.outcome.result(),
                fin=game.outcome.termination.name, secondes=seconds,
                coups_uci=[m.uci() for m in game.board.move_stack])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parties', type=int, default=3)
    parser.add_argument('--simulations', type=int, default=24)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', type=Path, default=Path('resultats/echecs.jsonl'))
    args = parser.parse_args()
    if min(args.parties, args.simulations) < 1:
        parser.error('--parties et --simulations doivent être strictement positifs')

    args.output.parent.mkdir(parents=True, exist_ok=True)
    total = 0.0
    positions = 0
    with args.output.open('w', encoding='utf-8') as journal:
        for seed in range(args.seed, args.seed + args.parties):
            record = play_game(seed, args.simulations)
            print(json.dumps(record), file=journal, flush=True)
            count = len(record['coups_uci'])
            total += record['secondes']
            positions += count
            print(f"Graine {seed} | {record['resultat']} | {count} demi-coups | "
                  f"{record['secondes']:.2f} s", flush=True)
    print(f"{positions / total:.2f} positions/s | "
          f"{1000 * total / args.parties / 3600:.2f} h pour 1 000 parties")


if __name__ == '__main__':
    main()
