import random
import unittest

try:
    import chess
except ModuleNotFoundError:
    raise unittest.SkipTest("Installer chess pour tester l'extension échecs.")

from echecs import ChessGame
from mcts import mcts_move


class ChessTests(unittest.TestCase):
    def test_repetition_history_survives_search(self):
        game = ChessGame()
        cycle = ['g1f3', 'g8f6', 'f3g1', 'f6g8']
        for uci in (cycle * 4)[:-1]:
            game.play(chess.Move.from_uci(uci))
        history = game.board.move_stack.copy()
        self.assertIn(mcts_move(game, random.Random(42), 2), game.legal_moves())
        clone = game.copy()
        clone.play(chess.Move.from_uci(cycle[-1]))
        self.assertEqual(clone.outcome.termination, chess.Termination.FIVEFOLD_REPETITION)
        self.assertTrue(clone.draw)
        self.assertEqual(clone.legal_moves(), [])
        self.assertIsNone(game.outcome)
        self.assertEqual(game.board.move_stack, history)

    def test_black_checkmate(self):
        game = ChessGame()
        for uci in ['f2f3', 'e7e5', 'g2g4', 'd8h4']:
            game.play(chess.Move.from_uci(uci))
        self.assertEqual(game.winner, chess.BLACK)
        self.assertFalse(game.draw)
        with self.assertRaises(ValueError):
            mcts_move(game, random.Random(0), 1)
