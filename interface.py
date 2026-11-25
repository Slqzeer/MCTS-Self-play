# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2", "numpy==2.3.4"]
# ///
"""Interface graphique (tkinter) : Puissance 4 et échecs contre les agents MCTS."""

import argparse
import random
import tkinter as tk
from pathlib import Path

from mcts import mcts_move
from puissance4 import COLUMNS, ROWS, Game

LIGHT, DARK, SELECT, LAST = '#f0d9b5', '#b58863', '#f6f669', '#cdd26a'


class App:
    """Fenêtre commune : plateau, ligne d'état et bouton « Nouvelle partie »."""

    def __init__(self, root, args, width, height):
        self.root, self.args = root, args
        self.rng = random.Random(args.seed)
        self.canvas = tk.Canvas(root, width=width, height=height, highlightthickness=0)
        self.canvas.pack(padx=12, pady=(12, 6))
        self.canvas.bind('<Button-1>', self.on_click)
        bar = tk.Frame(root)
        bar.pack(fill='x', padx=12, pady=(0, 12))
        self.status = tk.Label(bar, anchor='w', font=('Segoe UI', 11))
        self.status.pack(side='left', fill='x', expand=True)
        tk.Button(bar, text='Nouvelle partie', command=self.new_game).pack(side='right')
        self.new_game()

    def new_game(self):
        self.game = self.create_game()
        self.thinking = False
        self.redraw()
        self.next_turn()

    def human_turn(self):
        return (self.args.humain != 'aucun' and not self.over()
                and self.game.player == self.human_player())

    def next_turn(self):
        if self.over():
            self.status['text'] = self.result_text()
            return
        if self.human_turn():
            self.status['text'] = 'À vous de jouer.' + self.extra()
        else:
            self.thinking = True
            self.status['text'] = "L'agent réfléchit…" + self.extra()
            # Laisser tkinter afficher le plateau avant le calcul bloquant.
            game = self.game
            self.root.after(300 if self.args.humain == 'aucun' else 50, self.agent_turn, game)

    def agent_turn(self, game):
        # Ignorer un appel périmé : nouvelle partie lancée, ou coup déjà joué.
        if game is not self.game or not self.thinking:
            return
        self.thinking = False
        self.play(self.agent_move())

    def extra(self):
        return ''

    def play(self, move):
        self.game.play(move)
        self.after_move(move)
        self.redraw()
        self.next_turn()

    def after_move(self, move):
        pass


class Connect4App(App):
    CELL = 80

    def __init__(self, root, args):
        super().__init__(root, args, COLUMNS * self.CELL, ROWS * self.CELL)

    def create_game(self):
        return Game()

    def human_player(self):
        return 1 if self.args.humain == 'premier' else 2

    def over(self):
        return not self.game.legal_moves()

    def result_text(self):
        if self.game.draw:
            return 'Match nul.'
        return ('Rouge' if self.game.winner == 1 else 'Jaune') + ' gagne !'

    def agent_move(self):
        if self.args.agent == 'aleatoire':
            return self.rng.choice(self.game.legal_moves())
        return mcts_move(self.game, self.rng, self.args.simulations)

    def on_click(self, event):
        column = event.x // self.CELL
        if not self.thinking and self.human_turn() and column in self.game.legal_moves():
            self.play(column)

    def redraw(self):
        c, s = self.canvas, self.CELL
        c.delete('all')
        c.create_rectangle(0, 0, COLUMNS * s, ROWS * s, fill='#1f4e9c', width=0)
        colors = {0: 'white', 1: '#e34948', 2: '#eda100'}
        for row in range(ROWS):
            for col in range(COLUMNS):
                y = (ROWS - 1 - row) * s
                c.create_oval(col * s + 8, y + 8, col * s + s - 8, y + s - 8,
                              fill=colors[self.game.board[row][col]], width=0)


class ChessApp(App):
    SQUARE = 72

    def __init__(self, root, args):
        import chess
        self.chess = chess
        if args.agent == 'reseau':
            from selfplay import Network, search
            self.network, self.search = Network.load(args.poids), search
        self.selected = None
        super().__init__(root, args, 8 * self.SQUARE, 8 * self.SQUARE)

    def create_game(self):
        from echecs import ChessGame
        self.selected = None
        self.last = None
        return ChessGame(max_plies=self.args.demi_coups)

    def human_player(self):
        return self.args.humain != 'second'  # chess.WHITE vaut True.

    def over(self):
        return self.game.outcome is not None

    def result_text(self):
        outcome, T = self.game.outcome, self.chess.Termination
        reason = {T.CHECKMATE: 'échec et mat', T.STALEMATE: 'pat',
                  T.INSUFFICIENT_MATERIAL: 'matériel insuffisant',
                  T.SEVENTYFIVE_MOVES: 'règle des 75 coups',
                  T.FIVEFOLD_REPETITION: 'répétition de la position',
                  T.VARIANT_WIN: f'plus de matériel après {self.game.max_plies} demi-coups',
                  T.VARIANT_DRAW: f'matériel égal après {self.game.max_plies} demi-coups',
                  }.get(outcome.termination, outcome.termination.name.lower())
        if outcome.winner is None:
            return f'Partie nulle : {reason} ({outcome.result()}).'
        winner = 'Les blancs gagnent' if outcome.winner else 'Les noirs gagnent'
        return f'{winner} : {reason} ({outcome.result()}).'

    def agent_move(self):
        if self.args.agent == 'rollouts':
            return mcts_move(self.game, self.rng, self.args.simulations)
        visits = self.search(self.game, self.network, self.args.simulations, self.rng)
        return max(visits, key=visits.get)

    def after_move(self, move):
        self.selected, self.last = None, move

    def extra(self):
        if not self.game.max_plies:
            return ''
        return f'  ·  {self.game.max_plies - len(self.game.board.move_stack)} demi-coups restants'

    def square_at(self, x, y):
        file, rank = x // self.SQUARE, 7 - y // self.SQUARE
        if self.args.humain == 'second':
            file, rank = 7 - file, 7 - rank
        return self.chess.square(file, rank) if 0 <= file < 8 and 0 <= rank < 8 else None

    def click_square(self, square):
        """Premier clic : choisir une pièce. Second clic : jouer, changer de pièce ou annuler."""
        board = self.game.board
        if self.selected is not None:
            moves = [m for m in board.legal_moves
                     if m.from_square == self.selected and m.to_square == square]
            if moves:
                # ponytail: promotion toujours en dame ; ajouter un choix si la sous-promotion compte.
                queen = [m for m in moves if m.promotion == self.chess.QUEEN]
                self.play((queen or moves)[0])
                return
        piece = board.piece_at(square)
        self.selected = square if piece and piece.color == board.turn else None
        self.redraw()

    def on_click(self, event):
        square = self.square_at(event.x, event.y)
        if not self.thinking and self.human_turn() and square is not None:
            self.click_square(square)

    def redraw(self):
        c, s, chess = self.canvas, self.SQUARE, self.chess
        board = self.game.board
        targets = {m.to_square for m in board.legal_moves if m.from_square == self.selected}
        c.delete('all')
        for square in chess.SQUARES:
            file, rank = chess.square_file(square), chess.square_rank(square)
            if self.args.humain == 'second':
                file, rank = 7 - file, 7 - rank
            x, y = file * s, (7 - rank) * s
            color = LIGHT if (file + rank) % 2 else DARK
            if self.last and square in (self.last.from_square, self.last.to_square):
                color = LAST
            if square == self.selected:
                color = SELECT
            c.create_rectangle(x, y, x + s, y + s, fill=color, width=0)
            if square in targets:
                c.create_oval(x + s * 0.4, y + s * 0.4, x + s * 0.6, y + s * 0.6,
                              fill='#555', outline='')
            piece = board.piece_at(square)
            if piece:
                # Glyphe plein teinté, puis contour noir pour les blancs.
                font = ('Segoe UI Symbol', int(s * 0.6))
                solid = chess.Piece(piece.piece_type, chess.BLACK).unicode_symbol()
                c.create_text(x + s / 2, y + s / 2, text=solid, font=font,
                              fill='white' if piece.color else 'black')
                if piece.color:
                    c.create_text(x + s / 2, y + s / 2, text=piece.unicode_symbol(),
                                  font=font, fill='black')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    games = parser.add_subparsers(dest='jeu', required=True)
    for name, agents, simulations in [('puissance4', ['mcts', 'aleatoire'], 500),
                                      ('echecs', ['reseau', 'rollouts'], 256)]:
        sub = games.add_parser(name)
        sub.add_argument('--humain', choices=['premier', 'second', 'aucun'], default='premier',
                         help="l'humain joue en premier (défaut), en second, ou deux agents s'affrontent")
        sub.add_argument('--agent', choices=agents, default=agents[0])
        sub.add_argument('--simulations', type=int, default=simulations)
        sub.add_argument('--seed', type=int)
        if name == 'echecs':
            sub.add_argument('--poids', type=Path, default=Path('resultats/selfplay-60-v2/reseau.npz'))
            sub.add_argument('--demi-coups', type=int, default=60,
                             help='horizon de la variante, 0 pour les échecs standard (défaut : 60)')
    args = parser.parse_args()
    if args.simulations < 1 or getattr(args, 'demi_coups', 0) < 0:
        parser.error('--simulations doit être positif et --demi-coups positif ou nul')
    root = tk.Tk()
    root.title('Puissance 4 · MCTS' if args.jeu == 'puissance4' else 'Échecs · MCTS')
    root.resizable(False, False)
    (Connect4App if args.jeu == 'puissance4' else ChessApp)(root, args)
    root.mainloop()


if __name__ == '__main__':
    main()
