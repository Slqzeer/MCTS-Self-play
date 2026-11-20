"""Recherche Monte-Carlo avec sélection UCB1 et simulations aléatoires."""

import math
from copy import copy


class _Node:
    def __init__(self, game, parent=None, move=None, player=None):
        self.parent = parent
        self.move = move
        self.player = player  # Joueur ayant choisi le coup qui mène à ce nœud.
        self.untried = game.legal_moves()
        self.children = []
        self.visits = 0
        self.score = 0.0

    def select_child(self, exploration):
        log_visits = math.log(self.visits)
        return max(self.children, key=lambda child: (
            child.score / child.visits
            + exploration * math.sqrt(log_visits / child.visits)
        ))


def mcts_move(game, rng, simulations=500, exploration=math.sqrt(2)):
    """Renvoie la colonne la plus visitée, sans modifier la partie."""
    if simulations < 1:
        raise ValueError("Le nombre de simulations doit être positif.")
    if not math.isfinite(exploration) or exploration < 0:
        raise ValueError("La constante d'exploration doit être finie et positive ou nulle.")
    root = _Node(game)
    if not root.untried:
        raise ValueError("La partie est terminée.")

    for _ in range(simulations):
        state = copy(game)
        state.board = [row.copy() for row in game.board]
        node = root
        while not node.untried and node.children:
            node = node.select_child(exploration)
            state.play(node.move)

        if node.untried:
            move = node.untried.pop(rng.randrange(len(node.untried)))
            player = state.player
            state.play(move)
            child = _Node(state, node, move, player)
            node.children.append(child)
            node = child

        while moves := state.legal_moves():
            state.play(rng.choice(moves))

        while node is not None:
            node.visits += 1
            if state.draw:
                node.score += 0.5
            elif state.winner == node.player:
                node.score += 1
            node = node.parent

    return max(root.children, key=lambda child: child.visits).move
