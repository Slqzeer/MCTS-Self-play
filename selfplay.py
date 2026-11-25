# /// script
# requires-python = ">=3.10"
# dependencies = ["chess==1.11.2", "numpy==2.3.4; python_version >= '3.11'", "numpy==2.2.6; python_version < '3.11'"]
# ///
"""Entraîner un réseau policy/value aux échecs et mesurer son MCTS."""

import argparse
import gzip
import json
import math
import random
from pathlib import Path
from time import perf_counter

import chess
import numpy as np

from echecs import ChessGame
from mcts import mcts_move


def features(board):
    """Indices actifs dans le repère du joueur au trait."""
    def square(sq):
        return sq if board.turn else chess.square_mirror(sq)

    active = [64 * (p.piece_type - 1 + 6 * (p.color != board.turn)) + square(sq)
              for sq, p in board.piece_map().items()]
    for side, color in enumerate((board.turn, not board.turn)):
        if board.has_kingside_castling_rights(color):
            active.append(768 + 2 * side)
        if board.has_queenside_castling_rights(color):
            active.append(769 + 2 * side)
    if board.ep_square is not None:
        active.append(772 + chess.square_file(board.ep_square))
    active.append(780 + min(board.halfmove_clock // 10, 15))
    return active


def move_indices(board, moves):
    # Un logit par coup, somme des sorties départ, arrivée et promotion.
    return np.array([(m.from_square if board.turn else chess.square_mirror(m.from_square),
                      64 + (m.to_square if board.turn else chess.square_mirror(m.to_square)),
                      128 + (m.promotion or 0)) for m in moves])


class Network:
    def __init__(self, seed):
        rng = np.random.default_rng(seed)
        self.encoder = rng.normal(0, 0.04, (796, 32))
        self.policy = rng.normal(0, 0.04, (32, 134))
        self.value = rng.normal(0, 0.04, 32)

    @classmethod
    def load(cls, path):
        network = cls(0)
        with np.load(path) as weights:
            network.encoder = weights['encoder']
            network.policy = weights['policy']
            network.value = weights['value']
        return network

    def forward(self, active, actions):
        hidden = np.tanh(self.encoder[active].sum(axis=0))
        logits = (hidden @ self.policy)[actions].sum(axis=1)
        weights = np.exp(logits - logits.max())
        return hidden, weights / weights.sum(), float(np.tanh(hidden @ self.value))

    def fit(self, examples, epochs, rng):
        for _ in range(epochs):
            rng.shuffle(examples)
            for active, actions, target, outcome in examples:
                hidden, probs, value = self.forward(active, actions)
                # Gradients de l'entropie croisée et de la demi-erreur quadratique.
                dp = np.zeros(self.policy.shape[1])
                np.add.at(dp, actions, (probs - target)[:, None])
                dv = (value - outcome) * (1 - value ** 2)
                dh = (self.policy @ dp + self.value * dv) * (1 - hidden ** 2)
                self.encoder[active] -= 0.01 * dh
                self.policy -= 0.01 * np.outer(hidden, dp)
                self.value -= 0.01 * hidden * dv


class Node:
    def __init__(self):
        self.children = {}
        self.visits = 0
        self.total = 0.0  # Valeur du point de vue du joueur au trait ici.

    def expand(self, game, network, rng):
        moves = game.legal_moves()
        _, priors, value = network.forward(features(game.board), move_indices(game.board, moves))
        order = list(range(len(moves)))
        rng.shuffle(order)
        self.children = {moves[i]: (Node(), float(priors[i])) for i in order}
        return value


def search(game, network, simulations, rng, training=False):
    root = Node()
    root.expand(game, network, rng)
    if training:
        noise = [rng.gammavariate(0.3, 1) for _ in root.children]
        total = sum(noise)
        for (move, (child, prior)), sample in zip(root.children.items(), noise):
            root.children[move] = child, 0.75 * prior + 0.25 * sample / total
    for _ in range(simulations):
        state = game.copy()
        node = root
        path = [node]
        while node.children:
            scale = math.sqrt(1 + node.visits)

            def puct(item):
                child, prior = item[1]
                mean = -child.total / child.visits if child.visits else 0
                return mean + 1.5 * prior * scale / (1 + child.visits)

            move, (node, _) = max(node.children.items(), key=puct)
            state.play(move)
            path.append(node)
        if state.outcome:
            value = 0 if state.draw else (1 if state.winner == state.player else -1)
        else:
            value = node.expand(state, network, rng)
        for node in reversed(path):
            node.visits += 1
            node.total += value
            value = -value
    return {m: child.visits for m, (child, _) in root.children.items()}


def self_play(network, simulations, seed, max_plies=0):
    game = ChessGame(max_plies=max_plies)
    rng = random.Random(seed)
    positions = []
    while not game.outcome:
        visits = search(game, network, simulations, rng, training=True)
        move = rng.choices(list(visits), weights=list(visits.values()))[0]
        positions.append(dict(fen=game.board.fen(), coup=move.uci(),
                              visites={m.uci(): n for m, n in visits.items() if n}))
        game.play(move)
    for ply, row in enumerate(positions):
        row['value'] = 0 if game.draw else (1 if game.winner == (ply % 2 == 0) else -1)
    return dict(seed=seed, resultat=game.outcome.result(), positions=positions)


def example(row):
    board = chess.Board(row['fen'])
    moves = list(board.legal_moves)
    counts = np.array([row['visites'].get(m.uci(), 0) for m in moves])
    return features(board), move_indices(board, moves), counts / counts.sum(), row['value']


def match(network, simulations, seed, neural_color, max_plies=0):
    game = ChessGame(max_plies=max_plies)
    rng = random.Random(seed)
    baseline_rng = random.Random(~seed)
    elapsed = {'reseau': [], 'rollouts': []}
    while not game.outcome:
        neural = game.player == neural_color
        start = perf_counter()
        if neural:
            visits = search(game, network, simulations, rng)
            move = max(visits, key=visits.get)
        else:
            move = mcts_move(game, baseline_rng, simulations)
        elapsed['reseau' if neural else 'rollouts'].append(1000 * (perf_counter() - start))
        game.play(move)
    return dict(seed=seed, couleur_reseau='blancs' if neural_color else 'noirs',
                simulations=simulations, resultat=game.outcome.result(),
                score_reseau=0.5 if game.draw else int(game.winner == neural_color),
                coups_uci=[m.uci() for m in game.board.move_stack], ms=elapsed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in [('iterations', 2), ('parties', 4), ('epochs', 3),
                          ('simulations', 8), ('paires', 2), ('seed', 42), ('demi_coups', 0)]:
        parser.add_argument('--' + name.replace('_', '-'), type=int, default=default)
    parser.add_argument('--output', type=Path, default=Path('resultats/selfplay'))
    args = parser.parse_args()
    if min(args.iterations, args.parties, args.epochs, args.simulations, args.paires) < 1 or min(args.seed, args.demi_coups) < 0:
        parser.error('Les quantités doivent être positives et la graine positive ou nulle.')
    args.output.mkdir(parents=True, exist_ok=True)
    network = Network(args.seed)
    rng = random.Random(args.seed)
    seed = args.seed
    examples = []
    with gzip.open(args.output / 'positions.jsonl.gz', 'wt', encoding='utf-8') as stream:
        for iteration in range(args.iterations):
            for _ in range(args.parties):
                record = self_play(network, args.simulations, seed, args.demi_coups)
                print(json.dumps(dict(iteration=iteration + 1, **record)), file=stream)
                examples.extend(example(row) for row in record['positions'])
                seed += 1
            network.fit(examples, args.epochs, rng)
            print(f'Itération {iteration + 1} | {len(examples)} positions cumulées', flush=True)
    np.savez_compressed(args.output / 'reseau.npz', **vars(network))
    network = Network.load(args.output / 'reseau.npz')
    matches = []
    with (args.output / 'tournoi.jsonl').open('w', encoding='utf-8') as stream:
        for pair_seed in range(seed, seed + args.paires):
            for color in (chess.WHITE, chess.BLACK):
                record = match(network, args.simulations, pair_seed, color, args.demi_coups)
                print(json.dumps(record), file=stream, flush=True)
                matches.append(record)
                print(pair_seed, record['couleur_reseau'], record['resultat'], flush=True)
    scores = [r['score_reseau'] for r in matches]
    summary = dict(parametres={k: v for k, v in vars(args).items() if k != 'output'},
                   positions=len(examples), victoires=scores.count(1), nuls=scores.count(0.5),
                   defaites=scores.count(0), points=sum(scores),
                   ms_par_coup={agent: sum(sum(r['ms'][agent]) for r in matches) /
                                sum(len(r['ms'][agent]) for r in matches)
                                for agent in ('reseau', 'rollouts')})
    (args.output / 'synthese.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(summary)


if __name__ == '__main__':
    main()
