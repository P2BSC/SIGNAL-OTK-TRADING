# SIGNAL OTK V4 — moteur expérimental

## Installation Render
Remplacer `app.py`, `index.html`, `requirements.txt` à la racine du dépôt privé. Ajouter `test_engine.py` pour tests locaux. Build : `pip install -r requirements.txt`. Start : `python app.py`. Variable secrète Render : `TWELVE_DATA_API_KEY`. Ne jamais la commiter.

## Vérifications
`python -m unittest test_engine.py` : tests hors ligne. `/api/status` : état de la collecte. Le tableau de bord actualise l'affichage toutes les 30 s mais les cours sont récupérés environ toutes les 10 minutes. La limite théorique est 576 requêtes/jour pour un seul processus (hors redémarrages). Attention : un deuxième serveur ou des redémarrages peuvent augmenter la consommation. Un compte Render gratuit se met en veille : surveillance 24/7 non garantie.

## Sécurité et limites
Aucun ordre ni alerte de trading réelle. Les tendances EMA20/EMA50, swing 20 et Fibonacci 50–61,8 % sont des hypothèses de travail et ne représentent pas une transcription validée de la formation. Les tests vérifient la cohérence logicielle, **pas** la performance d'une stratégie. L'horodatage des bougies est demandé en UTC et doit être vérifié sur l'API. La bougie la plus récente est exclue pour éviter les bougies incomplètes, mais l'exactitude de l'horodatage dépend du fournisseur.

## Prochain jalon
Formaliser la stratégie de la vidéo, définir les entrées/sorties/invalidation sans ambiguïté, télécharger un historique suffisamment long, puis réaliser un backtest chronologique avec coûts/spreads/slippage, statistiques et validation hors échantillon. Ne pas utiliser pour prendre une position réelle.
