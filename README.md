# Atlas Entraxes 2025

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Dash](https://img.shields.io/badge/Dash-2.14+-orange.svg)](https://plotly.com/dash/)
[![Poetry](https://img.shields.io/badge/Poetry-1.7+-purple.svg)](https://python-poetry.org/)

Application web moderne et modulaire pour la visualisation des altitudes maximales admissibles par département français selon les configurations de serres et les zones réglementaires vent/neige.

## 🎯 Aperçu

Atlas Entraxes est un outil d'aide à la décision commerciale permettant de déterminer rapidement l'altitude maximale d'installation d'une serre selon :
- La configuration technique choisie
- L'entraxe des poteaux (2.5m ou 3.0m)
- Le département d'implantation
- Les zones vent/neige réglementaires

L'application offre une interface cartographique interactive avec intégration dynamique des configurations techniques et calculs automatiques des contraintes réglementaires.

## ✨ Fonctionnalités

- **🗺️ Visualisation cartographique** interactive des départements français
- **📊 Panneau de statistiques** avec répartition et couverture par altitude
- **🔧 Panneau de détails** techniques des configurations (dynamique depuis CSV)
- **🎨 Interface responsive** adaptée aux écrans desktop et mobile
- **🌈 Légende dynamique** avec palette de couleurs moderne et intuitive
- **⚡ Architecture modulaire** pour maintenance et déploiement simplifiés
- **🔍 Validation robuste** des fichiers de données avec gestion d'erreurs

## 🏗️ Architecture

### Structure du projet

```
atlas-entraxes/
├── atlas/                    # Module principal
│   ├── app.py              # Application Dash avec architecture optimisée
│   ├── config.py           # Configuration centralisée et validation
│   ├── utils.py            # Fonctions utilitaires (géographie, couleurs)
│   ├── run.py              # Script unifié de lancement
│   ├── data/               # Données sources centralisées
│   │   ├── departements.geojson         # Contours géographiques
│   │   ├── dept_zones_NORMALISE.csv     # Zones réglementaires
│   │   ├── details.csv                  # Métadonnées configurations
│   │   └── results_by_combo.csv         # Règles de calcul métier
│   └── scripts/            # Outils de traitement
│       ├── normalize_dept_zones.py      # Normalisation des données Excel
│       ├── preview_mapping.py           # Prévisualisation des mappings
│       └── quick_preview.py             # Aperçu rapide des données
├── pyproject.toml          # Configuration Poetry
├── poetry.lock             # Verrouillage des dépendances
└── README.md               # Documentation
```

### Architecture technique optimisée

#### Pré-calcul et cache
- **Pré-calcul au démarrage** : Toutes les combinaisons config/entraxe sont calculées à l'initialisation
- **Cache LRU multi-niveaux** : 
  - Palettes de couleurs (maxsize=16)
  - Choropleths de base (maxsize=50)
  - Détails de configuration (maxsize=100)
  - Panneaux UI (maxsize=10)
- **Threading sécurisé** : Gestion des accès concurrents avec locks

#### Performance
- **Temps de démarrage** : ~2-3 secondes (pré-calcul initial)
- **Interactions utilisateur** : Quasi-instantanées (données en cache)
- **Mémoire optimisée** : Cache intelligent avec limites configurables

#### Architecture modulaire
- **Point d'entrée unique** : `main()` avec gestion des arguments
- **Initialisation contrôlée** : `initialize_app()` pour la création de l'application
- **Configuration flexible** : Arguments en ligne de commande
- **Logging configurable** : Niveaux ajustables selon les besoins

## 🚀 Installation

### Prérequis

- Python 3.11 ou supérieur
- Poetry (gestionnaire de dépendances moderne)

### Installation avec Poetry (Recommandé)

```bash
# Cloner le repository
git clone https://github.com/apesseu/atlas-entraxes.git
cd atlas-entraxes

# Installer les dépendances
poetry install

# Activer l'environnement virtuel
poetry shell
```

### Installation alternative (pip)

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install dash plotly pandas numpy shapely pathlib
```

## 🎮 Utilisation

### Lancement de l'application

#### Méthode recommandée (script unifié)
```bash
# Lancement standard avec normalisation automatique
poetry run python atlas/run.py
```

#### Lancement direct avec options avancées
```bash
# Lancement standard
poetry run python atlas/app.py

# Avec port personnalisé
poetry run python atlas/app.py --port 3000

# Mode silencieux (supprime les warnings pandas)
poetry run python atlas/app.py --quiet

# Mode debug pour développement
poetry run python atlas/app.py --debug

# Désactiver le cache (débogage)
poetry run python atlas/app.py --no-cache

# Combinaison d'options
poetry run python atlas/app.py --port 8080 --host 0.0.0.0 --quiet --debug

# Aide complète
poetry run python atlas/app.py --help
```

#### Arguments disponibles

| Argument | Description | Défaut |
|----------|-------------|---------|
| `--port` | Port du serveur web | 8050 |
| `--host` | Adresse d'écoute | 127.0.0.1 |
| `--debug` | Active le mode debug Dash | False |
| `--quiet` | Supprime les warnings pandas | False |
| `--no-cache` | Désactive les optimisations LRU | False |

L'application sera accessible sur `http://127.0.0.1:8050` (ou le port spécifié)

### Scripts utilitaires

```bash
# Normalisation des données Excel vers CSV
poetry run python atlas/scripts/normalize_dept_zones.py

# Prévisualisation des mappings
poetry run python atlas/scripts/preview_mapping.py

# Aperçu rapide des données
poetry run python atlas/scripts/quick_preview.py
```

### Configuration

#### Configuration centralisée (`atlas/config.py`)
```python
# Chemins des fichiers de données (relatifs au module atlas/)
DATA_DIR = Path(__file__).parent / "data"
GEOJSON_PATH = DATA_DIR / "departements.geojson"
ZONES_PATH = DATA_DIR / "dept_zones_NORMALISE.csv"
DETAILS_PATH = DATA_DIR / "details.csv"
RULES_PATH = DATA_DIR / "results_by_combo.csv"

# Paramètres serveur (défauts, surchargeables par arguments)
HOST = "127.0.0.1"
PORT = 8050
DEBUG_MODE = False  # Mode production par défaut
```

#### Configuration en ligne de commande
Tous les paramètres peuvent être surchargés via les arguments :
```bash
# Exemple : serveur de production
poetry run python atlas/app.py --host 0.0.0.0 --port 8080 --quiet

# Exemple : développement local
poetry run python atlas/app.py --debug --port 3000
```

## 📊 Structure des données

### Fichiers requis

| Fichier | Description | Format | Validation |
|---------|-------------|---------|------------|
| `departements.geojson` | Contours géographiques des départements | GeoJSON | ✅ Taille et format |
| `dept_zones_NORMALISE.csv` | Association département → zones vent/neige | CSV | ✅ Structure et contenu |
| `results_by_combo.csv` | Règles de calcul (cœur métier) | CSV | ✅ Logique métier |

### Fichiers optionnels

| Fichier | Description | Impact si absent |
|---------|-------------|------------------|
| `details.csv` | Métadonnées des configurations | Détails affichés par défaut ("—") |

### Format des données

**dept_zones_NORMALISE.csv** :
```csv
Dept,Nom,Zone_Vent,Zone_Neige
01,Ain,2,A
02,Aisne,1,A
...
```

**details.csv** :
```csv
Config,Type_Serre,Hauteur_Poteau,Largeur,Toiture,Facade,Traverse
holyspirit4,Adour Portique,4.00m,8.00m,TOG + PV,Présente,Présente
...
```

**results_by_combo.csv** :
```csv
Entraxe,Zone_Vent,Zone_Neige,Altitude_Max
2.5,1,A,400
2.5,2,A,300
3.0,1,A,200
...
```

## 🛠️ Développement

### Tests et validation

```bash
# Validation de la configuration
python atlas/config.py

# Test des fonctions utilitaires
python -c "from atlas.utils import compute_centroids; print('✅ Utils OK')"

# Test de l'application
python atlas/app.py
```

### Ajout de nouvelles configurations

1. Ajouter les règles dans `atlas/data/results_by_combo.csv`
2. Optionnel : ajouter les métadonnées dans `atlas/data/details.csv`
3. Redémarrer l'application

### Débogage

Le mode debug est activé par défaut. Les logs sont affichés dans la console avec différents niveaux :

```
2025-09-04 02:24:20 - config - INFO - ✅ Validation réussie ! 3 fichier(s) validé(s).
2025-09-04 02:24:21 - utils - INFO - Calcul des centroïdes terminé : 96 succès, 0 échecs
```

## 🚀 Déploiement

### Serveur de production

```bash
# Modifier la configuration dans atlas/config.py
DEBUG_MODE = False
HOST = "0.0.0.0"  # Écoute sur toutes les interfaces

# Lancer avec un serveur WSGI (recommandé)
pip install gunicorn
gunicorn atlas.app:server -b 0.0.0.0:8050
```

### Docker (optionnel)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev
COPY . .
CMD ["python", "atlas/app.py"]
```

## 📦 Dépendances principales

- **Dash 2.14+** : Framework web interactif moderne
- **Plotly 5.15+** : Visualisations et cartes haute qualité
- **Pandas 2.0+** : Manipulation des données performante
- **Numpy 1.24+** : Calculs numériques optimisés
- **Shapely 2.0+** : Opérations géographiques avancées
- **Pathlib** : Gestion des chemins multiplateforme

## 🤝 Contribution

1. Fork du projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit des changements (`git commit -am 'Ajouter nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📚 Support

- **Documentation technique** : Ce README et les docstrings dans le code
- **Documentation utilisateur** : voir [USER_GUIDE.md](USER_GUIDE.md)
- **Issues** : [GitHub Issues](https://github.com/apesseu/atlas-entraxes/issues)
- **Architecture** : Voir la section Architecture ci-dessus

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📈 Changelog

### Version 2.1.0 (Actuelle)
- ⚡ **Architecture optimisée** avec pré-calcul et cache LRU multi-niveaux
- 🚀 **Performance maximale** : interactions quasi-instantanées
- 🛠️ **Arguments en ligne de commande** pour configuration flexible
- 🔇 **Mode silencieux** avec contrôle de la verbosité
- 🏗️ **Architecture modulaire** complète (config.py, utils.py, scripts/)
- 🔧 **Gestion centralisée des chemins** avec config.py
- 📁 **Structure de données cohérente** dans atlas/data/
- 🚀 **Scripts utilitaires** pour normalisation et prévisualisation
- ✅ **Validation robuste** des fichiers avec gestion d'erreurs
- 🎨 **Interface moderne** avec design système cohérent
- 📱 **Responsive design** pour tous les écrans

### Version 2.0.0
- 🏗️ **Architecture modulaire** complète (config.py, utils.py, scripts/)
- 🔧 **Gestion centralisée des chemins** avec config.py
- 📁 **Structure de données cohérente** dans atlas/data/
- 🚀 **Scripts utilitaires** pour normalisation et prévisualisation
- ✅ **Validation robuste** des fichiers avec gestion d'erreurs
- 🎨 **Interface moderne** avec design système cohérent
- 📱 **Responsive design** pour tous les écrans

### Version 1.0.0
- Version initiale monolithique
- Fonctionnalités de base de visualisation

---

**Développé avec ❤️ pour l'industrie des serres en France**
