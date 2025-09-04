"""
Fonctions utilitaires pour Atlas Entraxes.

Ce module fournit les outils nécessaires pour les calculs géographiques
et la génération des palettes de couleurs pour la visualisation.
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Test de disponibilité de Shapely pour les calculs géographiques
try:
    from shapely.geometry import shape
    HAS_SHAPELY = True
    logger.info("Shapely disponible pour les calculs géographiques")
except ImportError:
    HAS_SHAPELY = False
    logger.warning("Shapely non disponible - calculs géographiques désactivés")

# Palette de couleurs modernes
MODERN_COLORS = [
    "#2563eb",  # Bleu moderne
    "#059669",  # Vert émeraude
    "#dc2626",  # Rouge moderne
    "#7c3aed",  # Violet
    "#ea580c",  # Orange
    "#0891b2",  # Cyan
    "#be123c",  # Rose
    "#16a34a",  # Vert lime
]

GRAY_COLOR = "#e5e7eb"


def compute_centroids(geojson: Dict[str, Any]) -> pd.DataFrame:
    """
    Calcule les centroïdes des départements à partir d'un GeoJSON.
    
    Pour chaque département, calcule le point représentatif qui sera utilisé
    pour placer les numéros de départements sur la carte.
    
    Args:
        geojson: Dictionnaire GeoJSON contenant les géométries des départements
    
    Returns:
        DataFrame avec colonnes Dept, lat, lon
    """
    logger.info("Calcul des centroïdes des départements...")
    
    if not HAS_SHAPELY:
        logger.warning("Shapely non disponible - retour DataFrame vide")
        return pd.DataFrame(columns=["Dept", "lat", "lon"])
    
    if not geojson or "features" not in geojson:
        logger.error("GeoJSON invalide ou vide")
        return pd.DataFrame(columns=["Dept", "lat", "lon"])
    
    points = []
    successful_calcs = 0
    failed_calcs = 0
    
    for feature in geojson["features"]:
        try:
            if "properties" not in feature or "code" not in feature["properties"]:
                logger.warning("Feature sans code département ignorée")
                continue
                
            code = feature["properties"]["code"]
            
            if "geometry" not in feature:
                logger.warning(f"Département {code} sans géométrie")
                points.append((code, None, None))
                failed_calcs += 1
                continue
            
            geometry = shape(feature["geometry"])
            centroid = geometry.representative_point()
            
            points.append((code, centroid.y, centroid.x))
            successful_calcs += 1
            
        except Exception as e:
            logger.warning(f"Erreur calcul centroïde pour département {code if 'code' in locals() else 'inconnu'}: {e}")
            points.append((code if 'code' in locals() else "??", None, None))
            failed_calcs += 1
    
    centroids_df = pd.DataFrame(points, columns=["Dept", "lat", "lon"])
    
    logger.info(f"Calcul terminé : {successful_calcs} succès, {failed_calcs} échecs")
    
    # Statistiques des centroïdes calculés
    valid_centroids = centroids_df.dropna()
    if len(valid_centroids) > 0:
        lat_range = (valid_centroids["lat"].min(), valid_centroids["lat"].max())
        lon_range = (valid_centroids["lon"].min(), valid_centroids["lon"].max())
        logger.info(f"Portée géographique : lat {lat_range}, lon {lon_range}")
    
    return centroids_df


def build_modern_color_palette(labels_order: List[str]) -> Dict[str, str]:
    """
    Génère une palette de couleurs moderne pour la visualisation.
    
    Attribue des couleurs distinctes à chaque label d'altitude, en utilisant
    une couleur grise pour "Non admissible" et des couleurs vives pour les autres.
    
    Args:
        labels_order: Liste ordonnée des labels à colorier
    
    Returns:
        Dictionnaire mapping label vers couleur hexadécimale
    """
    logger.info(f"Génération palette couleurs pour {len(labels_order)} labels...")
    
    if not labels_order:
        logger.warning("Liste de labels vide")
        return {}
    
    color_map = {}
    color_index = 0
    colors_used = 0
    
    for label in labels_order:
        if label == "Non admissible":
            color_map[label] = GRAY_COLOR
            logger.debug(f"Label '{label}' → couleur grise")
        else:
            color = MODERN_COLORS[color_index % len(MODERN_COLORS)]
            color_map[label] = color
            color_index += 1
            colors_used += 1
            logger.debug(f"Label '{label}' → couleur {color}")
    
    logger.info(f"Palette générée : {colors_used} couleurs vives, {len(labels_order) - colors_used} grises")
    
    # Avertissement si répétition de couleurs nécessaire
    if colors_used > len(MODERN_COLORS):
        logger.warning(f"Répétition de couleurs : {colors_used} labels pour {len(MODERN_COLORS)} couleurs disponibles")
    
    return color_map