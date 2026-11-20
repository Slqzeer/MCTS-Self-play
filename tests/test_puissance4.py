import contextlib
import io
import random
import sys
import unittest
from unittest.mock import patch

from puissance4 import Game, main
from vendor import board as rules


class GameTests(unittest.TestCase):
    def test_gravity_invalid_moves_and_full_column(self):
        game = Game()
        for _ in range(6):
            game.play(0)
        self.assertEqual([row[0] for row in game.board], [1, 2, 1, 2, 1, 2])
        for move in (-1, 7, 0):
            with self.assertRaises(ValueError):
                game.play(move)
        self.assertEqual(game.player, 1)

    def test_win_directions(self):
        for cells in ([(0, c) for c in range(4)], [(r, 0) for r in range(4)],
                      [(i, i) for i in range(4)], [(3 - i, i) for i in range(4)]):
            board = rules.create_board(6, 7)
            for row, column in cells:
                board[row][column] = 1
            self.assertEqual(rules.detect_winner(board, 6, 7, 4), (1, False))

    def test_win_ends_game(self):
        game = Game()
        for move in (0, 1, 0, 1, 0, 1, 0):
            game.play(move)
        self.assertEqual(game.winner, 1)
        self.assertEqual(game.legal_moves(), [])
        with self.assertRaises(ValueError):
            game.play(2)

    def test_draw(self):
        moves = [3, 3, 0, 2, 5, 4, 5, 6, 4, 2, 2, 3, 3, 5, 5, 2, 2, 4, 3, 3, 1,
                 1, 2, 1, 5, 5, 0, 4, 0, 4, 4, 6, 6, 6, 6, 0, 1, 0, 6, 0, 1, 1]
        game = Game()
        for move in moves:
            game.play(move)
        self.assertTrue(game.draw)
        self.assertEqual(game.winner, 0)
        self.assertEqual(game.legal_moves(), [])

    def test_complete_terminal_games_and_invalid_input(self):
        for mode in ('agents', 'humain'):
            output = io.StringIO()
            # Human input tries an invalid entry, then cycles through columns.
            choices = iter(['x', '0'] + [str(c) for _ in range(42) for c in range(1, 8)])
            with patch.object(sys, 'argv', ['connect4.py', '--mode', mode, '--seed', '42']), \
                 patch('builtins.input', side_effect=lambda _: next(choices)), \
                 contextlib.redirect_stdout(output):
                main()
            self.assertTrue('gagne !' in output.getvalue() or 'Match nul !' in output.getvalue())
            if mode == 'humain':
                self.assertIn('Colonne invalide', output.getvalue())

    def test_seeded_random_games_finish(self):
        for seed in range(20):
            game = Game()
            rng = random.Random(seed)
            while game.legal_moves():
                game.play(rng.choice(game.legal_moves()))
            self.assertTrue(game.winner or game.draw)


if __name__ == '__main__':
    unittest.main()
