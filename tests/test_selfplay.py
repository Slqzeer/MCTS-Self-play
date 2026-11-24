import random
import unittest

try:
    import chess
    import numpy as np
except ModuleNotFoundError:
    raise unittest.SkipTest("Installer chess et NumPy pour tester le self-play.")

from echecs import ChessGame
from selfplay import Network, example, search


class SelfPlayTests(unittest.TestCase):
    def test_visits_favor_mate_for_either_color(self):
        board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1")
        network = Network(0)
        network.value.fill(0)
        network.policy.fill(0)
        for position in (board, board.mirror()):
            game = ChessGame(position)
            visits = search(game, network, 128, random.Random(7))
            self.assertEqual(sum(visits.values()), 128)
            self.assertEqual(set(visits), set(position.legal_moves))
            self.assertFalse(position.move_stack)
            game.play(max(visits, key=visits.get))
            self.assertTrue(game.board.is_checkmate())

    def test_fit_learns_visit_target_and_negative_outcome(self):
        row = dict(fen=chess.STARTING_FEN, visites={'e2e4': 3, 'd2d4': 1}, value=-1)
        active, actions, target, outcome = sample = example(row)
        self.assertAlmostEqual(target.max(), 0.75)
        network = Network(7)
        _, before, old_value = network.forward(active, actions)
        network.fit([sample], 10, random.Random(7))
        _, after, new_value = network.forward(active, actions)
        self.assertGreater(after[np.argmax(target)], before[np.argmax(target)])
        self.assertLess(abs(new_value - outcome), abs(old_value - outcome))
