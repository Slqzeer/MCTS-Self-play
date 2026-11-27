# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Compare les réglages du MCTS au Puissance 4, contre l’aléatoire ou un MCTS de référence."""

import argparse
import csv
import json
import math
import random
from concurrent.futures import ProcessPoolExecutor
from itertools import product
from pathlib import Path
from time import perf_counter_ns

from matplotlib.figure import Figure

from mcts import mcts_move
from puissance4 import Game

REFERENCE_C = math.sqrt(2)


def play_game(simulations, exploration, seed, player, opponent="aleatoire"):
    search_rng = random.Random(f"mcts:{seed}")
    opponent_rng = random.Random(f"{opponent}:{seed}")
    game = Game()
    times_ms = []
    while moves := game.legal_moves():
        if game.player == player:
            start = perf_counter_ns()
            column = mcts_move(game, search_rng, simulations, exploration)
            times_ms.append((perf_counter_ns() - start) / 1_000_000)
        elif opponent == "mcts":
            column = mcts_move(game, opponent_rng, simulations, REFERENCE_C)
        else:
            column = opponent_rng.choice(moves)
        game.play(column)
    outcome = "nul" if game.draw else ("victoire" if game.winner == player else "defaite")
    return dict(simulations=simulations, exploration=exploration, adversaire=opponent,
                graine=seed, joueur_mcts=player, resultat=outcome, temps_coups_mcts_ms=times_ms)


def wilson(successes, n, z=1.96):
    """Intervalle de confiance à 95 % d’une proportion (Wilson), en pourcentage."""
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return 100 * (centre - half), 100 * (centre + half)


def summarize(games):
    n = len(games)
    wins = sum(g["resultat"] == "victoire" for g in games)
    draws = sum(g["resultat"] == "nul" for g in games)
    times = [ms for g in games for ms in g["temps_coups_mcts_ms"]]
    low, high = wilson(wins, n)
    return dict(simulations=games[0]["simulations"], exploration=games[0]["exploration"],
                parties=n, victoires=wins, nuls=draws, defaites=n - wins - draws,
                victoires_pct=100 * wins / n, ic95_bas=low, ic95_haut=high,
                score_pct=100 * (wins + draws / 2) / n, ms_par_coup=sum(times) / len(times))


def plot(rows, opponent, path):
    fig = Figure(figsize=(11, 4.5), layout="constrained")
    wins, times = fig.subplots(1, 2)
    for budget in sorted({row["simulations"] for row in rows}):
        series = [row for row in rows if row["simulations"] == budget]
        cs = [row["exploration"] for row in series]
        pct = [row["victoires_pct"] for row in series]
        errors = [[max(0, p - row["ic95_bas"]) for p, row in zip(pct, series)],
                  [max(0, row["ic95_haut"] - p) for p, row in zip(pct, series)]]
        wins.errorbar(cs, pct, yerr=errors, marker="o", capsize=3, label=f"{budget} simulations")
        times.plot(cs, [row["ms_par_coup"] for row in series], marker="o", label=f"{budget} simulations")
    if opponent == "mcts":
        wins.axhline(50, color="grey", linestyle=":", linewidth=1)
        wins.axvline(REFERENCE_C, color="grey", linestyle=":", linewidth=1)
    wins.set(ylabel="Victoires MCTS (%) · IC 95 %", ylim=(-2, 102))
    times.set(ylabel="Temps moyen de décision MCTS (ms)", ylim=(0, None))
    for axis in (wins, times):
        axis.set_xlabel("Constante d’exploration C")
        axis.grid(alpha=0.25)
    wins.legend()
    name = "aléatoire" if opponent == "aleatoire" else "MCTS C = √2 (même budget)"
    fig.suptitle(f"Puissance 4 · MCTS contre {name} · {rows[0]['parties']} parties par réglage")
    fig.savefig(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulations", type=int, nargs="+", default=[16, 64, 256])
    parser.add_argument("--exploration", type=float, nargs="+",
                        default=[0, 0.25, 0.5, 1, REFERENCE_C, 2, 3, 4])
    parser.add_argument("--adversaire", choices=["aleatoire", "mcts"], default="aleatoire",
                        help="aléatoire, ou MCTS C = racine de 2 avec le même budget")
    parser.add_argument("--paires", type=int, default=50, help="paires de parties par réglage")
    parser.add_argument("--seed", type=int, default=42, help="première graine de la série")
    parser.add_argument("--output", type=Path, default=Path("resultats"))
    args = parser.parse_args()
    if args.paires < 1 or min(args.simulations) < 1:
        parser.error("Les budgets et le nombre de paires doivent être strictement positifs.")
    if any(c < 0 or not math.isfinite(c) for c in args.exploration):
        parser.error("Les constantes d’exploration doivent être finies et positives ou nulles.")

    args.output.mkdir(parents=True, exist_ok=True)
    settings = list(product(sorted(set(args.simulations)), sorted(set(args.exploration))))
    jobs = [(budget, c, seed, player, args.adversaire) for budget, c in settings
            for seed in range(args.seed, args.seed + args.paires) for player in (1, 2)]
    with ProcessPoolExecutor() as pool:
        games = list(pool.map(play_game, *zip(*jobs), chunksize=8))
    per_setting = 2 * args.paires
    summary = [summarize(games[i:i + per_setting]) for i in range(0, len(games), per_setting)]

    with (args.output / "parties.jsonl").open("w", encoding="utf-8") as log:
        log.writelines(json.dumps(game) + "\n" for game in games)
    with (args.output / "synthese.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)
    plot(summary, args.adversaire, args.output / "hyperparametres.png")
    print(f"Résultats disponibles dans {args.output}")


if __name__ == "__main__":
    main()
