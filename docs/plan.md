# Plan du projet MCTS et Self-Play

Le premier jalon est un **Puissance 4 jouable, avec un agent MCTS et des résultats reproductibles**. Une fois ce socle validé, on évaluera le coût de l’extension aux échecs avant de lancer l’entraînement. Le [sujet](subject.md) rend le Puissance 4 obligatoire et présente les échecs comme une extension avancée. Il laisse les livrables officiels et le barème à définir.

## Plan de réalisation

| Étape | Travail à faire | Critère de validation |
|---|---|---|
| **1. Rendre le Puissance 4 jouable** | Partir sur Python et réutiliser une implémentation existante du Puissance 4. Préparer un mode en terminal pour les parties entre agents et contre un humain. Créer un agent qui tire ses coups au hasard. | Une partie complète se joue dans les deux modes. Les coups illégaux sont rejetés et les victoires et matchs nuls sont détectés. |
| **2. Implémenter le MCTS** | Coder les quatre phases du MCTS avec UCB1 pour la sélection et des simulations aléatoires. Vérifier que la rétropropagation tient compte du joueur au trait. | Sur des positions préparées, l’agent trouve un gain immédiat et sait bloquer une menace directe avec un budget suffisant. |
| **3. Mesurer l’effet des hyperparamètres** | Faire jouer MCTS contre l’agent aléatoire en alternant le premier joueur. Faire varier le nombre de simulations et la constante d’exploration. Enregistrer les graines aléatoires, les victoires, les nuls, les défaites et le temps par coup. | Une commande permet de reproduire les essais. Les graphiques montrent comment le taux de victoire et le temps de décision évoluent selon les réglages. |
| **4. Adapter le MCTS aux échecs** | Réutiliser une implémentation des règles et chronométrer un premier lot de parties. Selon le débit observé et le temps disponible, retenir les échecs standard ou une variante allégée autorisée par le sujet. | L’agent joue des parties complètes et on dispose d’une estimation du temps nécessaire pour générer les données d’entraînement. |
| **5. Entraîner et comparer l’agent neuronal** | Générer des parties en self-play. Enregistrer pour chaque position la distribution des visites du MCTS comme cible de *policy* et le résultat final comme cible de *value*. Entraîner le réseau, l’intégrer à la recherche, puis le comparer au MCTS à simulations aléatoires. | Un tournoi sur des parties distinctes de l’entraînement compare les deux agents en alternant les couleurs. On publie les scores et le temps par coup pour un même nombre de simulations. |
| **6. Préparer le rendu et la soutenance** | Documenter les commandes pour jouer et relancer les expériences. Sélectionner les graphiques, une position illustrant le comportement de l’agent et les limites observées. Construire le PowerPoint à partir de ces éléments. | Le projet se relance depuis les instructions et la présentation tient entre 10 et 15 minutes lors d’une répétition. |

L’ordre de priorité est **1 → 2 → 3**, puis **4 → 5** si le temps et le débit de génération des parties le permettent. Pendant les expériences, on conservera quelques positions où l’agent prend une décision surprenante. Elles donneront des exemples concrets à analyser dans la soutenance.

## Trame du PowerPoint · environ 12 minutes

| Temps | Contenu |
|---|---|
| **1 min** | Question du projet et objectifs. |
| **2 min** | Les quatre phases du MCTS illustrées par un coup de Puissance 4. |
| **2 min** | Implémentation et protocole de comparaison, avec une courte démonstration ou une position commentée. |
| **3 min** | Résultats au Puissance 4 et effet des réglages sur le taux de victoire et le temps de calcul. |
| **3 min** | Résultats du self-play et comparaison aux échecs si l’extension est terminée. Sinon, analyse détaillée d’un échec ou d’une limite du MCTS au Puissance 4. |
| **1 min** | Bilan des découvertes et limites des expériences. |

Le premier incrément à réaliser est **une partie complète de Puissance 4 entre deux agents aléatoires, puis entre un humain et un agent aléatoire**. Ce point d’entrée servira ensuite à brancher le MCTS et à automatiser les comparaisons.
