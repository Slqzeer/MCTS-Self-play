import unittest
from argparse import Namespace
from types import SimpleNamespace

try:
    import chess
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
except (ModuleNotFoundError, tk.TclError):
    raise unittest.SkipTest("Interface graphique indisponible (tkinter, affichage ou chess).")

from echecs import ChessGame
from interface import ChessApp, Connect4App


def chess_app(humain='premier'):
    args = Namespace(humain=humain, agent='rollouts', simulations=2, seed=0, demi_coups=60)
    return ChessApp(tk.Toplevel(root), args)


class InterfaceTests(unittest.TestCase):
    def test_connect4_click_plays_column_then_agent_answers(self):
        args = Namespace(humain='premier', agent='aleatoire', simulations=1, seed=0)
        app = Connect4App(tk.Toplevel(root), args)
        app.on_click(SimpleNamespace(x=3 * app.CELL + 5, y=10))
        self.assertEqual(app.game.board[0][3], 1)
        self.assertTrue(app.thinking)
        app.on_click(SimpleNamespace(x=5, y=10))  # Ignoré : l'agent a la main.
        app.agent_turn(app.game)
        app.agent_turn(app.game)  # Appel en double : l'agent ne rejoue pas.
        self.assertEqual(sum(cell == 2 for row in app.game.board for cell in row), 1)
        self.assertEqual(sum(cell == 1 for row in app.game.board for cell in row), 1)

    def test_chess_select_move_reselect_and_cancel(self):
        app = chess_app()
        app.click_square(chess.E2)
        self.assertEqual(app.selected, chess.E2)
        app.click_square(chess.G1)  # Autre pièce du joueur : nouvelle sélection.
        self.assertEqual(app.selected, chess.G1)
        app.click_square(chess.G4)  # Case inaccessible : annulation.
        self.assertIsNone(app.selected)
        app.click_square(chess.E2)
        app.click_square(chess.E4)
        self.assertEqual(app.game.board.move_stack, [chess.Move.from_uci('e2e4')])
        self.assertIn('59 demi-coups restants', app.status['text'])
        app.agent_turn(app.game)
        self.assertEqual(len(app.game.board.move_stack), 2)

    def test_chess_ignores_clicks_after_ply_limit(self):
        app = chess_app()
        app.game = ChessGame(max_plies=2)
        for uci in ['e2e4', 'e7e5']:
            app.game.play(chess.Move.from_uci(uci))
        app.next_turn()
        self.assertFalse(app.human_turn())
        app.on_click(SimpleNamespace(x=5 * app.SQUARE + 5, y=7 * app.SQUARE + 5))  # Fou f1.
        self.assertIsNone(app.selected)
        self.assertEqual(app.status['text'], 'Partie nulle : matériel égal après 2 demi-coups (1/2-1/2).')

    def test_chess_promotes_to_queen_and_flips_for_black(self):
        app = chess_app()
        app.game = ChessGame(chess.Board('8/P6k/8/8/8/8/8/K7 w - - 0 1'))
        app.click_square(chess.A7)
        app.click_square(chess.A8)
        self.assertEqual(app.game.board.piece_at(chess.A8).piece_type, chess.QUEEN)
        black = chess_app('second')
        self.assertEqual(black.square_at(0, 0), chess.H1)
        self.assertEqual(black.square_at(7 * black.SQUARE, 7 * black.SQUARE), chess.A8)
        self.assertEqual(len(black.game.board.move_stack), 0)  # L'agent blanc n'a pas encore joué.


if __name__ == '__main__':
    unittest.main()
