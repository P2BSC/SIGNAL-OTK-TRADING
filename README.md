# SIGNAL OTK TRADING V2 — prototype de surveillance

## Fonctionnel
- Collecte serveur des bougies XAU/USD M5, M15, H1 et H4 via Twelve Data.
- Tableau de bord noir et or, sans saisie manuelle des cours.
- Tendance indicative par comparaison de la dernière clôture confirmée à une moyenne des 20 clôtures précédentes.
- Aucun ordre, aucun signal de trading validé, aucune alerte push pour l'instant.

## Installation locale (ordinateur)
1. Installer Python 3.10+.
2. Dans le dossier : `python -m pip install -r requirements.txt`.
3. Définir `TWELVE_DATA_API_KEY` dans les variables d'environnement (ne jamais la publier sur GitHub).
4. Lancer `python app.py`, puis ouvrir `http://127.0.0.1:8080`.

## Déploiement permanent
Déployer sur un hébergeur exécutant Python en continu, configurer `TWELVE_DATA_API_KEY` comme secret d'environnement et un accès HTTPS. Le serveur de développement Flask ne convient pas à la production; utiliser un serveur WSGI, une supervision et une authentification avant exposition publique. GitHub Pages seul ne peut pas exécuter le backend. Vérifier les quotas Twelve Data, la disponibilité, les fuseaux horaires et les coûts d'hébergement. La surveillance en arrière-plan et les notifications ne seront actives qu'après déploiement et configuration de services supplémentaires.

## Travail restant avant les signaux
Formaliser les conditions objectives H4/H1/M15/M5 à partir de la vidéo (notamment structure, Fibonacci, liquidité, confirmation, ventes), intégrer spreads et caractéristiques Vantage, définir entrées/SL/TP, puis backtester hors échantillon. Aucun trade réel avant validation.
