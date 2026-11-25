# Puissance 4

## Interface graphique

```sh
uv run interface.py puissance4                         # humain (rouge) contre MCTS, 500 simulations
uv run interface.py puissance4 --humain second --agent aleatoire
uv run interface.py echecs                             # humain (blancs) contre le réseau entraîné, horizon 60
uv run interface.py echecs --humain second --agent rollouts
uv run interface.py echecs --humain aucun              # deux agents s'affrontent
uv run interface.py echecs --demi-coups 0              # échecs standard
```

L’interface utilise tkinter, fourni avec Python. Au Puissance 4, on clique sur une colonne. Aux échecs, on clique sur une pièce : ses cases d’arrivée possibles s’affichent. Un second clic joue le coup. La promotion se fait toujours en dame. Le dernier coup est surligné, et la ligne d’état indique qui a la main et le nombre de demi-coups restants dans la variante. Le bouton « Nouvelle partie » relance une partie. Pendant que l’agent calcule, la fenêtre ne répond pas.


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

## Échecs · mesurer le coût du self-play

Depuis la racine, lancer trois parties entre deux agents MCTS sur l'échiquier standard.

```sh
uv run echecs.py
uv run --with chess==1.11.2 python -m unittest discover -s tests
```

Le lot utilise les graines 42 à 44, 24 simulations aléatoires complètes par décision et la constante UCB1 √2. La bibliothèque python-chess applique les règles. Les agents jouent jusqu'au mat ou à une nulle automatique (pat, matériel insuffisant, répétition quintuple ou règle des 75 coups). Ils ne réclament pas les nulles facultatives.

Le [journal du lot](resultats/echecs.jsonl) contient les coups en notation UCI, le résultat, le motif de fin et la durée de chaque partie. Chaque demi-coup correspond à une position pour laquelle le MCTS a pris une décision. Le débit affiché inclut la recherche et les coups joués. Pour estimer une campagne avec un autre budget, refaire la mesure avec ce budget et un fichier de sortie distinct.

```sh
uv run echecs.py --parties 5 --simulations 64 --seed 100 --output resultats/echecs-64.jsonl
```

**Choix pour l'étape 5.** On retient les échecs standard pour un premier lot d'entraînement. Sous Windows avec Python 3.14.0, les trois parties ont produit 1 197 décisions en 321,69 s, soit 3,72 positions/s. À ce débit, générer 10 000 positions prendrait environ 45 minutes sur un seul processus. Pour un objectif exprimé en parties, compter environ 3 h pour 100 parties, ou 30 h pour 1 000. Ces projections portent sur la génération seule, au même budget de recherche. Les parties du lot ont duré de 297 à 598 demi-coups et se sont toutes terminées par une nulle, deux par matériel insuffisant et une par la règle des 75 coups.

## Échecs · entraîner et comparer le réseau

Depuis la racine du dépôt, relancer l’expérience dans un dossier distinct des résultats publiés.

```sh
uv run selfplay.py --output resultats/essai-selfplay
uv run --with chess==1.11.2 --with numpy==2.3.4 python -m unittest discover -s tests
```

Le protocole par défaut effectue deux itérations de quatre parties de self-play (graines 42 à 49). Chaque recherche PUCT effectue huit simulations par coup. Aux feuilles, un réseau NumPy à une couche cachée de 32 unités donne une probabilité aux coups légaux et évalue la position pour le joueur au trait. En self-play, on ajoute du bruit de Dirichlet à la racine et on tire le coup proportionnellement aux visites. Après chaque lot, le réseau s’entraîne pendant trois époques sur toutes les positions accumulées. Le lot suivant utilise les poids appris.

Le [journal d’entraînement](resultats/selfplay/positions.jsonl.gz) contient une partie par ligne JSON compressée. Chaque position indique sa FEN, le coup joué, les visites des coups explorés et la valeur finale (+1 victoire, 0 nulle, −1 défaite pour le joueur au trait). Diviser les visites par leur somme donne la cible de policy. Les coups légaux absents ont une cible nulle. Les [poids entraînés](resultats/selfplay/reseau.npz) se rechargent avec `Network.load` dans `selfplay.py`.

Le tournoi fige le réseau, désactive le bruit et choisit le coup le plus visité. Il l’oppose au MCTS UCB1 à rollouts aléatoires de l’étape 4, avec huit simulations par coup pour chacun. Chaque graine de tournoi (50 et 51) sert à deux parties, une par couleur pour le réseau. Le [journal du tournoi](resultats/selfplay/tournoi.jsonl) consigne les coups et les durées de décision des deux agents. La [synthèse](resultats/selfplay/synthese.json) donne le score du réseau et le temps moyen par décision de chaque agent, calculé sur l’ensemble de ses coups.
**Résultat du premier tournoi.** Le réseau marque 2 points sur 4 avec quatre nulles. Sur cette machine, il prend en moyenne 4,60 ms par coup, contre 106,49 ms pour les rollouts. Les huit parties d’entraînement comptaient déjà six nulles. Ce petit échantillon met en évidence un écart de temps de calcul et laisse la différence de force de jeu indéterminée.

## Échecs · variante à horizon limité

Les rollouts aléatoires ne trouvent presque jamais le mat. Sur neuf parties de test, les finales de pions, les finales avec tours et pions, et même roi et dame contre roi seul ont toutes fini en nulle. Comme le sujet autorise une variante allégée, l’option `--demi-coups N` arrête la partie après N demi-coups. Le camp qui a le plus de matériel gagne (pion 1, cavalier et fou 3, tour 5, dame 9). À égalité de matériel, la partie est nulle. Le mat et les nulles réglementaires restent valables avant cette limite. La règle s’applique aussi aux simulations des deux agents. La valeur 0, par défaut, garde les échecs standard.

```sh
uv run selfplay.py --demi-coups 60 --iterations 10 --parties 50 --simulations 32 --paires 50 --output resultats/selfplay-60
```

Le self-play joue 500 parties (graines 42 à 541), soit 28 885 positions. Le tournoi compte 100 parties contre le MCTS à rollouts (graines 542 à 591, chaque couleur une fois par graine), avec 32 simulations par coup pour chaque agent. La campagne a pris environ 14 minutes avec Python 3.14. Les fichiers sont dans [resultats/selfplay-60](resultats/selfplay-60).

Le témoin oppose aux rollouts un réseau **non entraîné**, sur les mêmes graines de tournoi, avec le même budget. Il mesure ce que PUCT apporte avant tout apprentissage.

```sh
uv run comparaison.py resultats/selfplay-60
```

Le script relit les paramètres de la campagne dans `synthese.json`. Il joue le témoin s’il n’existe pas encore (environ 5 minutes) et l’enregistre dans `temoin.json`. Il trace ensuite le [graphique de comparaison](resultats/selfplay-60/comparaison.png).

| Agent PUCT contre MCTS à rollouts | Victoires | Nuls | Défaites | Points sur 100 |
|---|---|---|---|---|
| Réseau non entraîné (témoin) | 58 | 3 | 39 | 59,5 |
| Réseau après 10 itérations de self-play | 81 | 5 | 14 | **83,5** |

**Lecture.** L’entraînement fait passer le score de 59,5 à 83,5 points. L’écart de 24 points dépasse largement l’incertitude d’un échantillon de 100 parties (environ ±7 à ±10 points à 95 %). Le réseau entraîné marque 42 points sur 50 avec les blancs et 41,5 sur 50 avec les noirs. Il prend en moyenne 14,3 ms par coup, contre 98,5 ms pour les rollouts. Ce résultat porte sur une variante où le matériel décide de la partie. Il ne dit pas que l’agent saurait mater aux échecs complets.

## Échecs · jouer contre l’agent

```sh
uv run jouer_echecs.py                                     # humain (blancs) contre le réseau entraîné, horizon 60
uv run jouer_echecs.py --couleur noirs --agent rollouts    # humain (noirs) contre le MCTS à rollouts
uv run jouer_echecs.py --demi-coups 0 --simulations 200    # échecs standard, sans limite de demi-coups
```

Saisir les coups en notation algébrique (`e4`, `Nf3`, `O-O`) ou en UCI (`e2e4`). Un coup illégal est refusé. Par défaut, le réseau charge les poids de `resultats/selfplay-60/reseau.npz`. L’option `--poids` en désigne d’autres.
