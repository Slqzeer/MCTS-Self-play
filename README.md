# Puissance 4

Python 3.10 ou plus récent, sans dépendance externe.

```sh
python puissance4.py                  # humain (X, premier joueur) contre agent aléatoire (O)
python puissance4.py --mode agents    # deux agents aléatoires
python puissance4.py --agent-o mcts   # humain contre MCTS
python puissance4.py --mode agents --agent-x mcts --simulations 500 --seed 42
python -m unittest discover -s tests
```

Choisir une colonne de 1 à 7. Le premier à aligner quatre pions horizontalement, verticalement ou en diagonale gagne ; si la grille est pleine sans alignement, la partie est nulle.

Les primitives du plateau sont adaptées de [connect-4-game-engine](https://github.com/RenaudGaudron/connect-4-game-engine), par Renaud Gaudron, sous licence MIT (voir `vendor/LICENSE`).
