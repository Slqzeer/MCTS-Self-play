# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Compare les réglages du MCTS contre un adversaire aléatoire au Puissance 4."""

import argparse
import csv
import json
import math
import random
from itertools import product
from pathlib import Path
from time import perf_counter_ns

from matplotlib.figure import Figure

from mcts import mcts_move
from puissance4 import Game


def play_game(simulations, exploration, seed, player):
    search_rng = random.Random(f"mcts:{seed}")
    opponent_rng = random.Random(f"aleatoire:{seed}")
    game = Game()
    times_ms = []
    while moves := game.legal_moves():
        if game.player == player:
            start = perf_counter_ns()
            column = mcts_move(game, search_rng, simulations, exploration)
            times_ms.append((perf_counter_ns() - start) / 1_000_000)
        else:
            column = opponent_rng.choice(moves)
        game.play(column)
    outcome = "nul" if game.draw else ("victoire" if game.winner == player else "defaite")
    return dict(simulations=simulations, exploration=exploration, graine=seed,
                joueur_mcts=player, resultat=outcome, temps_coups_mcts_ms=times_ms)


def summarize(games):
    wins = sum(g["resultat"] == "victoire" for g in games)
    draws = sum(g["resultat"] == "nul" for g in games)
    times = [ms for g in games for ms in g["temps_coups_mcts_ms"]]
    return dict(simulations=games[0]["simulations"], exploration=games[0]["exploration"],
                victoires=wins, nuls=draws, defaites=len(games) - wins - draws,
                victoires_pct=100 * wins / len(games), ms_par_coup=sum(times) / len(times))


def plot(rows, games_per_setting, path):
    fig = Figure(figsize=(10, 4.5), layout="constrained")
    wins, times = fig.subplots(1, 2)
    for exploration in sorted({row["exploration"] for row in rows}):
        series = [row for row in rows if row["exploration"] == exploration]
        budgets = [row["simulations"] for row in series]
        for axis, metric in [(wins, "victoires_pct"), (times, "ms_par_coup")]:
            axis.plot(budgets, [row[metric] for row in series], marker="o",
                      label=f"C = {exploration:g}")
    wins.set(ylabel="Victoires MCTS (%)", ylim=(-2, 102))
    times.set(ylabel="Temps moyen de décision MCTS (ms)", ylim=(0, None))
    for axis in (wins, times):
        axis.set_xlabel("Simulations par coup")
        axis.grid(alpha=0.25)
    times.legend()
    fig.suptitle(f"Puissance 4 · MCTS contre aléatoire · {games_per_setting} parties par réglage")
    fig.savefig(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulations", type=int, nargs="+", default=[4, 16, 64])
    parser.add_argument("--exploration", type=float, nargs="+", default=[0.5, math.sqrt(2)])
    parser.add_argument("--paires", type=int, default=10, help="paires de parties par réglage")
    parser.add_argument("--seed", type=int, default=42, help="première graine de la série")
    parser.add_argument("--output", type=Path, default=Path("resultats"))
    args = parser.parse_args()
    if args.paires < 1 or min(args.simulations) < 1:
        parser.error("Les budgets et le nombre de paires doivent être strictement positifs.")
    if any(c < 0 or not math.isfinite(c) for c in args.exploration):
        parser.error("Les constantes d’exploration doivent être finies et positives ou nulles.")

    args.output.mkdir(parents=True, exist_ok=True)
    summary = []
    with (args.output / "parties.jsonl").open("w", encoding="utf-8") as log:
        for budget, c in product(sorted(set(args.simulations)), sorted(set(args.exploration))):
            games = []
            for seed in range(args.seed, args.seed + args.paires):
                for player in (1, 2):
                    game = play_game(budget, c, seed, player)
                    games.append(game)
                    print(json.dumps(game), file=log)
            summary.append(summarize(games))
    with (args.output / "synthese.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)
    plot(summary, 2 * args.paires, args.output / "hyperparametres.png")
    print(f"Résultats disponibles dans {args.output}")


if __name__ == "__main__":
    main()
