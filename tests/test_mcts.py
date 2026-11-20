import random
import unittest

from mcts import mcts_move
from puissance4 import Game


class MctsTests(unittest.TestCase):
    def test_immediate_win_and_forced_block_for_each_player(self):
        positions = [
            ((2, 5, 2, 5, 2, 6), 2),     # X gagne
            ((5, 2, 5, 2, 6, 2, 6), 2),  # O gagne
            ((5, 2, 5, 2, 6, 2), 2),     # X doit bloquer O
            ((2, 5, 2, 6, 2), 2),        # O doit bloquer X
        ]
        for moves, expected in positions:
            with self.subTest(moves=moves):
                game = Game()
                for move in moves:
                    game.play(move)
                board = [row.copy() for row in game.board]
                player = game.player
                self.assertEqual(mcts_move(game, random.Random(42), 500), expected)
                self.assertEqual((game.board, game.player, game.winner, game.draw),
                                 (board, player, 0, False))

    def test_smallest_budget_and_terminal_position(self):
        game = Game()
        rng = random.Random(7)
        self.assertIn(mcts_move(game, rng, 1), game.legal_moves())
        for move in (0, 1, 0, 1, 0, 1, 0):
            game.play(move)
        with self.assertRaises(ValueError):
            mcts_move(game, rng, 1)
