"""Puissance 4 en terminal : humain contre agent ou deux agents."""

import argparse
import random

from mcts import mcts_move
from vendor import board as rules

ROWS, COLUMNS, ALIGNMENT = 6, 7, 4


class Game:
    def __init__(self):
        self.board = rules.create_board(ROWS, COLUMNS)
        self.player = 1
        self.winner = 0
        self.draw = False

    def legal_moves(self):
        if self.winner or self.draw:
            return []
        return rules.get_valid_locations(self.board, ROWS, COLUMNS)

    def play(self, column):
        if column not in self.legal_moves():
            raise ValueError("Coup illégal")
        row = rules.get_next_open_row(self.board, column, ROWS)
        rules.drop_piece(self.board, row, column, self.player)
        self.winner, self.draw = rules.detect_winner(self.board, ROWS, COLUMNS, ALIGNMENT)
        if not self.winner and not self.draw:
            self.player = 3 - self.player

    def display(self):
        symbols = '.XO'
        print('\n  1 2 3 4 5 6 7')
        for row in reversed(self.board):
            print('| ' + ' '.join(symbols[cell] for cell in row) + ' |')
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['humain', 'agents'], default='humain',
                        help='humain contre agent (défaut), ou deux agents')
    parser.add_argument('--seed', type=int, help='graine des coups aléatoires')
    parser.add_argument('--agent-x', choices=['aleatoire', 'mcts'], default='aleatoire',
                        help='agent du premier joueur en mode agents')
    parser.add_argument('--agent-o', choices=['aleatoire', 'mcts'], default='aleatoire',
                        help='agent du second joueur')
    parser.add_argument('--simulations', type=int, default=500,
                        help='nombre de simulations par coup MCTS (défaut : 500)')
    args = parser.parse_args()
    if args.simulations < 1:
        parser.error('--simulations doit être supérieur à zéro')
    rng = random.Random(args.seed)
    game = Game()
    game.display()
    while game.legal_moves():
        if args.mode == 'humain' and game.player == 1:
            try:
                column = int(input('Votre colonne (1-7) : ')) - 1
                game.play(column)
            except ValueError:
                print('Colonne invalide ou pleine, réessayez.')
                continue
            except EOFError:
                print('\nPartie interrompue.')
                return
        else:
            agent = args.agent_x if game.player == 1 else args.agent_o
            if agent == 'mcts':
                column = mcts_move(game, rng, simulations=args.simulations)
            else:
                column = rng.choice(game.legal_moves())
            print(f'Agent {game.player} joue colonne {column + 1}.')
            game.play(column)
        game.display()
    print(f'Joueur {game.winner} gagne !' if game.winner else 'Match nul !')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nPartie interrompue.')
