# MCTS et Self-Play pour jeux à deux joueurs

_De Puissance 4 aux échecs_

## Contexte

Ce projet porte sur l'implémentation d'un agent jouant à un jeu à deux joueurs à information complète, en utilisant Monte Carlo Tree Search (MCTS), avec une montée en puissance progressive vers du self-play et du deep learning (façon AlphaZero).

## Objectifs pédagogiques

- Comprendre et implémenter l'algorithme MCTS (sélection, expansion, simulation, rétropropagation).
- Mettre en place une boucle de self-play pour générer des parties et améliorer un agent.
- *(Niveau avancé)* Intégrer un réseau de neurones pour remplacer ou guider les rollouts et évaluer les positions.

## Niveau 1 — Puissance 4 (obligatoire)

- Utiliser une implémentation existante du jeu (bibliothèque, code fourni ou trouvé par le groupe) : pas besoin de coder le moteur de jeu soi-même.
- Implémenter un agent MCTS pur (rollouts aléatoires ou heuristique simple, pas de deep learning requis).
- Faire jouer l'agent contre un joueur aléatoire ou un humain, puis mesurer le taux de victoire.
- Étudier l'influence des hyperparamètres (nombre de simulations, constante d'exploration UCB1, etc.).

## Niveau 2 — Échecs (extension avancée)

- Utiliser une implémentation existante des règles ou du moteur d'échecs (ex. bibliothèque comme `python-chess`, ou code fourni) : l'objectif est l'agent, pas le moteur de jeu.
- Adapter l'approche MCTS à un jeu plus complexe (espace d'états et d'actions bien plus grand).
- Mettre en place une boucle de self-play : l'agent joue contre lui-même pour générer des données.
- Entraîner un réseau de neurones (policy + value, style AlphaZero simplifié) pour guider le MCTS à la place des rollouts aléatoires.
- Comparer les performances de l'agent avec et sans réseau de neurones.

> Le Niveau 2 peut être exploré sur une variante allégée des échecs (échiquier réduit, moins de pièces) si le temps est limité.

## Références

- Kocsis & Szepesvári, *Bandit Based Monte-Carlo Planning (UCT)*, 2006.
- Browne et al., *A Survey of Monte Carlo Tree Search Methods*, IEEE TCIAIG, 2012.
- Silver et al., *Mastering the Game of Go with Deep Neural Networks and Tree Search* (AlphaGo), Nature, 2016.
- Silver et al., *Mastering Chess and Shogi by Self-Play with a General RL Algorithm* (AlphaZero), 2017.

> ⚠️ **Note :** Le self-play n'apporte un vrai bénéfice que s'il sert à entraîner un modèle (policy/value network) sur les parties générées. Avec de simples rollouts aléatoires, faire jouer l'agent contre lui-même ne l'améliore pas : c'est pour cela que le self-play est introduit au Niveau 2, couplé à l'entraînement du réseau de neurones.

## Consignes techniques

- Langage libre (Python recommandé).
- Le code doit permettre de faire jouer deux agents l'un contre l'autre ou un agent contre un humain.

## Livrables et barème

À définir ultérieurement.
