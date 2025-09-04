# Guide Utilisateur - Atlas Entraxes

## Table des matières
1. [Introduction](#introduction)
2. [Premiers pas](#premiers-pas)
3. [Interface utilisateur](#interface-utilisateur)
4. [Utilisation pas-à-pas](#utilisation-pas-à-pas)
5. [Interprétation des résultats](#interprétation-des-résultats)
6. [Cas d'usage métier](#cas-dusage-métier)
7. [Limitations et précautions](#limitations-et-précautions)
8. [FAQ](#faq)

## Introduction

Atlas Entraxes est un outil d'aide à la décision pour déterminer l'**altitude maximale d'implantation** d'une serre selon :
- Le **modèle/configuration** de serre choisi
- L'**entraxe des poteaux** (2,50 m ou 3,00 m)
- Le **département** d'implantation

L'outil applique automatiquement les règles de calcul selon la **norme EN 13031** en croisant les zones vent et neige réglementaires.

### À qui s'adresse cet outil ?

- **Équipes commerciales** : qualification rapide des prospects
- **Bureaux d'études** : pré-dimensionnement et vérifications
- **Responsables de projets** : aide à la décision technique

### Avertissement important

⚠️ **Cet outil est une aide commerciale et ne remplace pas une note de calcul officielle.**

En cas de :
- Site exposé (catégorie de terrain I)
- Altitude élevée ou conditions particulières
- Doute sur les résultats

→ **Consultez systématiquement le bureau d'études avant toute offre.**

## Premiers pas

### Accès à l'application

1. Ouvrez votre navigateur web
2. Accédez à l'URL fournie par votre administrateur
3. L'interface se charge automatiquement

**Navigateurs recommandés :** Chrome, Firefox, Edge (versions récentes)

### Vue d'ensemble de l'interface

L'écran principal est divisé en **3 zones** :

```
┌─────────────────┬──────────────────────────┬─────────────────┐
│   Statistiques  │         Carte de         │    Détails      │
│     carte       │         France           │ configuration   │
│                 │                          │                 │
│ - Couverture    │ - Carte colorée par      │ - Référence     │
│ - Répartition   │   altitude max           │ - Spécifications│
│ - Pourcentages  │ - Légende interactive    │ - Règles d'usage│
└─────────────────┴──────────────────────────┴─────────────────┘
```

## Interface utilisateur

### Zone de contrôles (en haut)

#### 1. Sélecteur de Configuration
- **Dropdown** listant toutes les configurations disponibles
- **Exemple** : "holyspirit4", "modele_standard", etc.
- Change automatiquement la carte lors de la sélection

#### 2. Sélecteur d'Entraxe
- **Boutons radio** : "3.00 m" ou "2.50 m"
- **Impact** : modifie les altitudes maximales calculées
- **Règle** : plus l'entraxe est faible, plus la structure est résistante

### Panneau gauche : Statistiques

#### Barre de couverture
- **Jauge visuelle** indiquant le % de départements couverts
- **Exemple** : "92 / 101 dép (91%)"

#### Répartition par altitude
- **Liste colorée** des altitudes avec nombre de départements
- **Couleurs cohérentes** avec la carte
- **Pourcentages** calculés sur les départements admissibles

#### Non admissibles
- Départements où **aucune règle** ne permet cette configuration
- Nécessitent une **étude spécifique**

### Carte centrale

#### Visualisation
- **Départements colorés** selon l'altitude maximale admissible
- **Numéros de départements** affichés pour identification rapide
- **Légende** en haut et en bas de la carte

#### Interactions
- **Survol** : affiche nom du département et altitude
- **Zoom/Pan** : navigation libre sur la carte
- **Export** : bouton téléchargement SVG haute résolution

#### Outils de dessin
- **Ligne, cercle, rectangle** : pour annotations
- **Gomme** : effacer les dessins
- **Utile** pour présenter des zones spécifiques

### Panneau droit : Détails configuration

#### Spécifications techniques
- **Type de serre** : tunnel, chapelle, etc.
- **Dimensions** : hauteur, largeur
- **Matériaux** : structure, couverture
- **Résistance** : données techniques

#### Règles d'usage (section dépliable)
- **Hypothèses de calcul** utilisées
- **Catégories de terrain** applicables
- **Rappels réglementaires**

#### Conditions détaillées (section dépliable)
- **Portée et limites** de l'outil
- **Cas non couverts** nécessitant une étude BE
- **Responsabilités** et avertissements

## Utilisation pas-à-pas

### Scénario 1 : Qualification commerciale rapide

1. **Client prospect** vous indique :
   - Département : Ain (01)
   - Altitude du terrain : 400m
   - Serre souhaitée : Adour Portique

2. **Dans Atlas Entraxes** :
   - Sélectionnez "holyspirit4" (Adour Portique)
   - Choisissez entraxe "3.00 m"
   - Regardez la couleur du département 01

3. **Interprétation** :
   - Couleur bleue = 650m max → ✅ **ADMISSIBLE** (400m < 650m)
   - Couleur grise = Non admissible → ❌ **ÉTUDE BE REQUISE**

4. **Réponse client** :
   - Si admissible : "Faisable, nous pouvons établir un devis"
   - Si non admissible : "Étude technique préalable nécessaire"

### Scénario 2 : Optimisation technique

1. **Objectif** : maximiser la surface couverte
2. **Méthode** :
   - Testez différentes configurations
   - Comparez les couvertures (panneau statistiques)
   - Choisissez celle avec le meilleur ratio admissible/non-admissible

3. **Exemple** :
   - Configuration A : 85% de couverture
   - Configuration B : 91% de couverture
   - → Configuration B plus polyvalente

### Scénario 3 : Analyse régionale

1. **Contexte** : étude de marché sur une région
2. **Utilisation des outils** :
   - Utilisez les outils de dessin pour délimiter la région
   - Analysez visuellement les couleurs dominantes
   - Consultez les statistiques pour quantifier

3. **Export** :
   - Téléchargez la carte en SVG
   - Intégrez dans vos présentations

## Interprétation des résultats

### Code couleur

**⚠️ IMPORTANT : Les couleurs sont générées aléatoirement et changent à chaque session !**

| Type | Signification | Action recommandée |
|------|---------------|-------------------|
| **Couleurs vives** | Altitudes maximales admissibles | ✅ Consultez la légende pour la valeur exacte |
| **⚪ Gris** | Non admissible | ❌ Étude BE obligatoire |

**Comment interpréter :**
1. **Regardez la légende** en haut/bas de la carte
2. **Identifiez la couleur** de votre département
3. **Consultez la valeur** correspondante dans la légende
4. **Comparez** avec l'altitude du client

### Marge de sécurité

**Recommandation** : appliquez une marge de sécurité de **50m** par rapport à l'altitude maximale affichée.

**Exemple** :
- Altitude max affichée : 400m
- Altitude client : 350m
- Marge : 400m - 350m = 50m ✅ **ACCEPTABLE**
- Si altitude client > 350m → étude complémentaire

### Cas particuliers

#### Sites exposés (catégorie I)
- **Littoral** : moins de 3km de la côte
- **Plateaux ouverts** : exposition aux vents dominants
- **Montagne** : cols, crêtes, versants exposés

→ **L'atlas n'est PAS applicable**, étude BE systématique

#### Microclimats
- **Vallées encaissées** : protection contre le vent
- **Couloirs de vent** : effet Venturi
- **Proximité d'obstacles** : bâtiments, relief

→ Expertise terrain recommandée

## Cas d'usage métier

### Pour les commerciaux

#### Qualification de prospects
```
Prospect → Département + Altitude → Atlas → GO/NO GO
```

#### Préparation d'offres
1. Vérifiez l'admissibilité avec Atlas
2. Si admissible : établissez le devis
3. Si limite : mentionnez les conditions dans l'offre
4. Si non admissible : proposez une étude préalable

#### Argumentaire client
- **Montrez la carte** au client
- **Expliquez la logique** zones vent/neige
- **Rassurez** sur la conformité réglementaire

### Pour les bureaux d'études

#### Pré-dimensionnement
- **Validation rapide** des hypothèses initiales
- **Comparaison** de plusieurs configurations
- **Identification** des cas nécessitant calculs poussés

#### Support commercial
- **Expertise technique** lors de rendez-vous clients
- **Validation** des propositions commerciales
- **Recommandations** d'optimisation

### Pour les chefs de projets

#### Analyse de faisabilité
- **Screening** rapide des opportunités
- **Priorisation** des affaires selon complexité
- **Allocation** des ressources BE

#### Reporting
- **Tableaux de bord** avec exports SVG
- **Analyses régionales** pour stratégie commerciale

## Limitations et précautions

### Hypothèses de calcul

L'Atlas repose sur des **hypothèses standardisées** :

- **Norme** EN 13031
- **Catégorie de terrain II** (site relativement plat et dégagé)
- **Pas d'effets particuliers** (site, obstacles, microclimats)

### Cas NON couverts par l'Atlas

❌ **Sites catégorie I** (très exposés)
❌ **Altitudes > 1000m** (conditions extrêmes)
❌ **Charges particulières** (équipements lourds)
❌ **Modifications structurelles** du modèle standard
❌ **Réglementations locales** spécifiques

### Responsabilités

- **Atlas Entraxes** : outil d'aide à la décision
- **Utilisateur** : validation par expertise métier
- **Bureau d'études** : note de calcul officielle pour cas complexes

### Mise à jour des données

- Les **zones réglementaires** peuvent évoluer
- Les **configurations** sont mises à jour régulièrement
- **Vérifiez** la date de dernière mise à jour (bas de page)

## FAQ

### Questions fréquentes

**Q: Puis-je faire confiance aux résultats pour tous mes projets ?**
R: L'Atlas est fiable pour les cas standards (catégorie II). Pour les sites exposés ou cas particuliers, une étude BE reste nécessaire.

**Q: Que faire si mon département apparaît en gris ?**
R: Contactez le bureau d'études. Aucune configuration standard n'est admissible, mais une solution sur-mesure peut exister.

**Q: Comment interpréter une altitude maximale de 200m pour un client à 180m ?**
R: C'est admissible avec une bonne marge. Vous pouvez proposer cette configuration en toute confiance.

**Q: L'outil prend-il en compte les DOM-TOM ?**
R: Actuellement, seule la France métropolitaine est couverte.

**Q: Puis-je utiliser l'Atlas pour des projets à l'export ?**
R: Non, les zones vent/neige sont spécifiques à la réglementation française.

### Support technique

**En cas de problème** :
1. Rafraîchissez la page (F5)
2. Vérifiez votre connexion internet
3. Contactez votre administrateur système

**Pour questions métier** :
- Consultez ce guide
- Contactez le bureau d'études
- Référez-vous aux conditions d'utilisation détaillées

---

**Dernière mise à jour** : Septembre 2025
**Version du guide** : 1.0
**Contact** : avicenne.pesseu@gmain.com
