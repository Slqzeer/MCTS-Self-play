# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2", "numpy==2.3.4", "matplotlib==3.11.2"]
# ///
"""Comparer réseau entraîné, réseau non entraîné (témoin) et MCTS à rollouts."""

import argparse
import json
from pathlib import Path

import chess
from matplotlib.figure import Figure

from selfplay import Network, match

BLUE, GRAY, RED = '#2a78d6', '#c3c2b7', '#e34948'
INK, MUTED, SURFACE = '#0b0b0b', '#898781', '#fcfcfb'


def control(params):
    """Même tournoi que la campagne, avec le réseau initial non entraîné."""
    first = params['seed'] + params['iterations'] * params['parties']
    network = Network(params['seed'], params.get('cachees', 32))
    records = [match(network, params['simulations'], seed, color, params['demi_coups'])
               for seed in range(first, first + params['paires'])
               for color in (chess.WHITE, chess.BLACK)]
    scores = [r['score_reseau'] for r in records]
    return dict(victoires=scores.count(1), nuls=scores.count(0.5), defaites=scores.count(0),
                points=sum(scores),
                ms_par_coup=sum(sum(r['ms']['reseau']) for r in records) /
                sum(len(r['ms']['reseau']) for r in records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dossier', type=Path, nargs='?', default=Path('resultats/selfplay-60'))
    args = parser.parse_args()
    trained = json.loads((args.dossier / 'synthese.json').read_text(encoding='utf-8'))
    path = args.dossier / 'temoin.json'
    if path.exists():
        untrained = json.loads(path.read_text(encoding='utf-8'))
    else:
        untrained = control(trained['parametres'])
        path.write_text(json.dumps(untrained, indent=2) + '\n', encoding='utf-8')
    print('Témoin :', untrained)

    figure = Figure(figsize=(10, 3.2), facecolor=SURFACE, layout='constrained')
    outcomes, times = figure.subplots(1, 2, width_ratios=[3, 2])
    rows = [('Réseau non entraîné', untrained), ('Réseau entraîné', trained)]
    total = untrained['victoires'] + untrained['nuls'] + untrained['defaites']
    for y, (_, result) in enumerate(rows):
        left = 0
        for key, color, ink in [('victoires', BLUE, 'white'), ('nuls', GRAY, INK),
                                ('defaites', RED, 'white')]:
            width = result[key]
            outcomes.barh(y, width, left=left, color=color, height=0.6,
                          edgecolor=SURFACE, linewidth=2)
            if width >= 4:
                outcomes.text(left + width / 2, y, str(width), ha='center', va='center',
                              color=ink, fontsize=10)
            left += width
        outcomes.text(total + 1.5, y, f"{result['points']:g} pts".replace('.', ','), va='center', color=INK)
    outcomes.set_yticks(range(len(rows)), [name for name, _ in rows])
    outcomes.set_xlim(0, total * 1.12)
    outcomes.invert_yaxis()
    outcomes.set_xlabel(f'Parties contre le MCTS à rollouts (sur {total})', color=MUTED)
    outcomes.set_title('Victoires · nuls · défaites', loc='left', color=INK)
    outcomes.legend(handles=[outcomes.barh(0, 0, color=c, label=l)
                             for c, l in [(BLUE, 'Victoire'), (GRAY, 'Nul'), (RED, 'Défaite')]],
                    loc='upper center', bbox_to_anchor=(0.45, -0.28), ncol=3, frameon=False)

    labels = ['MCTS à rollouts', 'Réseau non entraîné', 'Réseau entraîné']
    values = [trained['ms_par_coup']['rollouts'], untrained['ms_par_coup'],
              trained['ms_par_coup']['reseau']]
    times.barh(range(3), values, color=BLUE, height=0.6)
    for y, value in enumerate(values):
        times.text(value + 2, y, f'{value:.1f} ms'.replace('.', ','), va='center', color=INK)
    times.set_yticks(range(3), labels)
    times.set_xlim(0, max(values) * 1.3)
    times.invert_yaxis()
    times.set_xlabel('Temps moyen par coup (ms)', color=MUTED)
    times.set_title('Temps de décision', loc='left', color=INK)

    for axis in (outcomes, times):
        axis.set_facecolor(SURFACE)
        axis.tick_params(colors=MUTED, length=0)
        axis.tick_params(axis='y', colors=INK)
        for side in ('top', 'right', 'left'):
            axis.spines[side].set_visible(False)
        axis.spines['bottom'].set_color(GRAY)
    figure.savefig(args.dossier / 'comparaison.png', dpi=200)


if __name__ == '__main__':
    main()
