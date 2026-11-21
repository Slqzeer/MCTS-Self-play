# Puissance 4

Le jeu en terminal utilise Python 3.10 ou plus récent, sans dépendance externe.

```sh
python puissance4.py                  # humain (X, premier joueur) contre agent aléatoire (O)
python puissance4.py --mode agents    # deux agents aléatoires
python puissance4.py --agent-o mcts   # humain contre MCTS
python puissance4.py --mode agents --agent-x mcts --simulations 500 --seed 42
python -m unittest discover -s tests
```

Choisir une colonne de 1 à 7. Le premier à aligner quatre pions horizontalement, verticalement ou en diagonale gagne ; si la grille est pleine sans alignement, la partie est nulle.

Les primitives du plateau sont adaptées de [connect-4-game-engine](https://github.com/RenaudGaudron/connect-4-game-engine), par Renaud Gaudron, sous licence MIT (voir `vendor/LICENSE`).

## Mesurer l’effet des hyperparamètres

Depuis la racine du dépôt, lancer le tournoi avec uv, qui prépare Python et Matplotlib.

```sh
uv run benchmark.py
```

Le protocole par défaut compare 4, 16 et 64 simulations par coup pour deux constantes UCB1 (0,5 et √2). Chaque réglage utilise les mêmes dix graines (42 à 51). Pour chaque graine, MCTS joue une fois en premier et une fois en second, avec un générateur aléatoire distinct pour chaque agent. Cela donne 20 parties par réglage et 120 au total.

Le [graphique](resultats/hyperparametres.png) présente le pourcentage de victoires parmi toutes les parties et le temps moyen par décision MCTS. Le [tableau de synthèse](resultats/synthese.csv) donne aussi les nuls et les défaites. Le [journal des parties](resultats/parties.jsonl) contient les paramètres, la graine, le numéro du joueur MCTS, l’issue de son point de vue et la durée de chacun de ses coups en millisecondes. À version de Python identique, les graines permettent de rejouer les parties. Les durées varient avec la machine et sa charge.

Pour augmenter l’échantillon ou modifier la grille, choisir un autre dossier de sortie pour conserver les mesures précédentes.

```sh
uv run benchmark.py --simulations 16 64 256 --exploration 0.5 1 2 --paires 50 --seed 100 --output resultats-50
```
