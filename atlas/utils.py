"""
utils.py - VERSION ULTIMATE

Fonctions utilitaires pour Atlas Entraxes.
Contient les fonctions de calcul géographique, traitement des données, 
génération des couleurs, export et utilitaires avancés.

Auteur: apesseu
Version: 2.0 (Fusion Claude + Assistant)
"""

import pandas as pd
import numpy as np
import logging
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Tuple
import plotly.graph_objects as go

# Configuration du logging
logger = logging.getLogger(__name__)

# Test d'import de Shapely pour les calculs géographiques
try:
    from shapely.geometry import shape
    HAS_SHAPELY = True
    logger.info("Shapely disponible pour les calculs géographiques")
except ImportError:
    HAS_SHAPELY = False
    logger.warning("Shapely non disponible - calculs géographiques désactivés")

# ====== CONSTANTES ======

# Palette de couleurs moderne pour les cartes
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
"""Palette de couleurs moderne pour les visualisations."""

GRAY_COLOR = "#e5e7eb"
"""Couleur grise pour les éléments non admissibles."""

# ====== FONCTIONS GÉOGRAPHIQUES ======

def compute_centroids(geojson: Dict[str, Any]) -> pd.DataFrame:
    """
    Calcule les centroïdes des départements à partir d'un GeoJSON.
    
    Pour chaque département dans le GeoJSON, calcule le point représentatif
    (centroïde géométrique) qui sera utilisé pour placer les numéros de départements
    sur la carte.
    
    Args:
        geojson (Dict[str, Any]): Dictionnaire GeoJSON contenant les géométries 
                                  des départements avec leurs codes dans properties.code
    
    Returns:
        pd.DataFrame: DataFrame avec colonnes :
                     - Dept : Code département
                     - lat : Latitude du centroïde  
                     - lon : Longitude du centroïde
                     Retourne un DataFrame vide si Shapely n'est pas disponible.
    
    Example:
        >>> geojson = {"features": [{"properties": {"code": "01"}, "geometry": {...}}]}
        >>> centroids = compute_centroids(geojson)
        >>> print(centroids.columns.tolist())
        ['Dept', 'lat', 'lon']
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
            # Extraction du code département
            if "properties" not in feature or "code" not in feature["properties"]:
                logger.warning("Feature sans code département ignorée")
                continue
                
            code = feature["properties"]["code"]
            
            # Extraction de la géométrie
            if "geometry" not in feature:
                logger.warning(f"Département {code} sans géométrie")
                points.append((code, None, None))
                failed_calcs += 1
                continue
            
            # Calcul du centroïde avec Shapely
            geometry = shape(feature["geometry"])
            centroid = geometry.representative_point()
            
            points.append((code, centroid.y, centroid.x))
            successful_calcs += 1
            
        except Exception as e:
            logger.warning(f"Erreur calcul centroïde pour département {code if 'code' in locals() else 'inconnu'}: {e}")
            points.append((code if 'code' in locals() else "??", None, None))
            failed_calcs += 1
    
    # Création du DataFrame résultat
    centroids_df = pd.DataFrame(points, columns=["Dept", "lat", "lon"])
    
    logger.info(f"Calcul terminé : {successful_calcs} succès, {failed_calcs} échecs")
    
    # Statistiques des centroïdes calculés
    valid_centroids = centroids_df.dropna()
    if len(valid_centroids) > 0:
        lat_range = (valid_centroids["lat"].min(), valid_centroids["lat"].max())
        lon_range = (valid_centroids["lon"].min(), valid_centroids["lon"].max())
        logger.info(f"Portée géographique : lat {lat_range}, lon {lon_range}")
    
    return centroids_df


def validate_geojson_structure(geojson_data: dict) -> bool:
    """
    Valide la structure du fichier GeoJSON.
    
    Vérifie que le GeoJSON contient les éléments requis pour Atlas Entraxes :
    - Présence de la clé "features"
    - Chaque feature a une propriété "code" (code département)
    - Géométries valides
    
    Args:
        geojson_data (dict): Données GeoJSON à valider
        
    Returns:
        bool: True si la structure est valide
        
    Raises:
        ValueError: Si la structure GeoJSON est invalide
        
    Example:
        >>> with open("data/departements.geojson") as f:
        ...     geojson = json.load(f)
        >>> if validate_geojson_structure(geojson):
        ...     print("GeoJSON valide")
    """
    logger.info("Validation de la structure GeoJSON...")
    
    if not isinstance(geojson_data, dict):
        raise ValueError("Le GeoJSON doit être un dictionnaire")
    
    if "features" not in geojson_data:
        raise ValueError("Le GeoJSON doit contenir une clé 'features'")
    
    features = geojson_data["features"]
    if not isinstance(features, list) or len(features) == 0:
        raise ValueError("La liste des features doit être non vide")
    
    # Validation de chaque feature
    valid_features = 0
    invalid_features = 0
    
    for i, feature in enumerate(features):
        if not isinstance(feature, dict):
            logger.warning(f"Feature {i} n'est pas un dictionnaire")
            invalid_features += 1
            continue
            
        properties = feature.get("properties", {})
        if "code" not in properties:
            logger.warning(f"Feature {i} n'a pas de propriété 'code'")
            invalid_features += 1
            continue
            
        if "geometry" not in feature:
            logger.warning(f"Feature {i} n'a pas de géométrie")
            invalid_features += 1
            continue
            
        valid_features += 1
    
    logger.info(f"Validation GeoJSON : {valid_features} features valides, {invalid_features} invalides")
    
    if valid_features == 0:
        raise ValueError("Aucune feature valide trouvée dans le GeoJSON")
    
    return True


# ====== FONCTIONS DE TRAITEMENT DES DONNÉES ======

def build_map_df(zones: pd.DataFrame, rules: pd.DataFrame, config: str, entraxe_col: str) -> pd.DataFrame:
    """
    Construit le DataFrame pour la visualisation cartographique.
    
    Croise les données des zones départementales avec les règles de calcul
    pour une configuration et un entraxe donnés, puis calcule les altitudes
    maximales admissibles par département.
    
    Args:
        zones (pd.DataFrame): DataFrame des zones départementales avec colonnes :
                             Dept, Nom, Zone_Vent, Zone_Neige
        rules (pd.DataFrame): DataFrame des règles de calcul avec colonnes :
                             Config, Zone_Vent, Zone_Neige, AltMax_3m, AltMax_2_5m
        config (str): Nom de la configuration à traiter (ex: "holyspirit4")
        entraxe_col (str): Colonne d'entraxe à utiliser ("AltMax_3m" ou "AltMax_2_5m")
    
    Returns:
        pd.DataFrame: DataFrame enrichi avec colonnes :
                     - Toutes les colonnes de zones
                     - AltMax_sel : Altitude maximale sélectionnée (numérique)
                     - Label : Label d'affichage ("XXX m" ou "Non admissible")
    
    Example:
        >>> zones = pd.DataFrame({"Dept": ["01"], "Zone_Vent": ["2"], "Zone_Neige": ["A1"]})
        >>> rules = pd.DataFrame({"Config": ["test"], "Zone_Vent": ["2"], "Zone_Neige": ["A1"], "AltMax_3m": ["500"]})
        >>> result = build_map_df(zones, rules, "test", "AltMax_3m")
        >>> print(result["Label"].iloc[0])  # "500 m"
    """
    logger.info(f"Construction DataFrame pour config='{config}', entraxe='{entraxe_col}'...")
    
    # Validation des paramètres d'entrée
    if zones.empty:
        logger.error("DataFrame zones vide")
        return pd.DataFrame()
    
    if rules.empty:
        logger.warning("DataFrame rules vide - tous départements non admissibles")
        df = zones.copy()
        df["AltMax_sel"] = np.nan
        df["Label"] = "Non admissible"
        return df
    
    # Vérification des colonnes requises
    required_zones_cols = ["Dept", "Zone_Vent", "Zone_Neige"]
    missing_zones = [col for col in required_zones_cols if col not in zones.columns]
    if missing_zones:
        raise ValueError(f"Colonnes manquantes dans zones : {missing_zones}")
    
    required_rules_cols = ["Config", "Zone_Vent", "Zone_Neige", entraxe_col]
    missing_rules = [col for col in required_rules_cols if col not in rules.columns]
    if missing_rules:
        raise ValueError(f"Colonnes manquantes dans rules : {missing_rules}")
    
    # Sélection des règles pour cette configuration
    selected_rules = rules.loc[rules["Config"] == config, ["Zone_Vent", "Zone_Neige", entraxe_col]].copy()
    
    if selected_rules.empty:
        logger.warning(f"Aucune règle trouvée pour la configuration '{config}'")
        df = zones.copy()
        df["AltMax_sel"] = np.nan
        df["Label"] = "Non admissible"
        return df
    
    logger.info(f"Règles trouvées : {len(selected_rules)}")
    
    # Jointure zones ↔ règles
    merged_df = zones.merge(selected_rules, on=["Zone_Vent", "Zone_Neige"], how="left")
    
    # Conversion des altitudes en numérique
    merged_df["AltMax_sel"] = pd.to_numeric(merged_df[entraxe_col], errors="coerce")
    
    # Création des labels d'affichage
    def create_label(altitude_value):
        """Crée le label d'affichage pour une valeur d'altitude."""
        if pd.isna(altitude_value):
            return "Non admissible"
        try:
            return f"{int(altitude_value)} m"
        except (ValueError, OverflowError):
            return "Non admissible"
    
    merged_df["Label"] = merged_df["AltMax_sel"].apply(create_label)
    
    # Statistiques finales
    total_depts = len(merged_df)
    admissible_count = merged_df["AltMax_sel"].notna().sum()
    non_admissible_count = total_depts - admissible_count
    
    logger.info(f"Résultats : {total_depts} départements, {admissible_count} admissibles, {non_admissible_count} non admissibles")
    
    return merged_df


def get_map_statistics(map_df: pd.DataFrame) -> Dict[str, Union[int, float]]:
    """
    Calcule les statistiques de la carte pour l'affichage.
    
    Args:
        map_df (pd.DataFrame): DataFrame de la carte (résultat de build_map_df)
        
    Returns:
        Dict[str, Union[int, float]]: Dictionnaire des statistiques
        
    Example:
        >>> stats = get_map_statistics(map_df)
        >>> print(f"Total départements : {stats['total_departements']}")
    """
    if map_df.empty:
        return {
            "total_departements": 0,
            "admissible": 0,
            "non_admissible": 0,
            "altitude_moyenne": 0.0,
            "altitude_max": 0.0
        }
    
    admissible_mask = map_df["AltMax_sel"] == map_df["AltMax_sel"]
    admissible_df = map_df[admissible_mask]
    
    stats = {
        "total_departements": len(map_df),
        "admissible": admissible_mask.sum(),
        "non_admissible": (~admissible_mask).sum(),
        "altitude_moyenne": admissible_df["AltMax_sel"].mean() if not admissible_df.empty else 0.0,
        "altitude_max": admissible_df["AltMax_sel"].max() if not admissible_df.empty else 0.0
    }
    
    return stats


def get_altitude_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les statistiques sur les altitudes d'un DataFrame de résultats.
    
    Args:
        df (pd.DataFrame): DataFrame avec colonne AltMax_sel
    
    Returns:
        Dict[str, Any]: Statistiques calculées (total, admissible, non_admissible, etc.)
    
    Example:
        >>> df = pd.DataFrame({"AltMax_sel": [500, np.nan, 400]})
        >>> stats = get_altitude_statistics(df)
        >>> print(stats["admissible"])  # 2
    """
    if "AltMax_sel" not in df.columns:
        return {"total": len(df), "admissible": 0, "non_admissible": len(df)}
    
    total = len(df)
    admissible = df["AltMax_sel"].notna().sum()
    non_admissible = total - admissible
    
    stats = {
        "total": total,
        "admissible": int(admissible),
        "non_admissible": int(non_admissible),
        "pourcentage_admissible": round(100 * admissible / total, 1) if total > 0 else 0,
    }
    
    if admissible > 0:
        valid_altitudes = df["AltMax_sel"].dropna()
        stats.update({
            "altitude_min": float(valid_altitudes.min()),
            "altitude_max": float(valid_altitudes.max()),
            "altitude_moyenne": round(float(valid_altitudes.mean()), 1),
        })
    
    return stats


# ====== FONCTIONS DE VISUALISATION ======

def build_modern_color_palette(labels_order: List[str]) -> Dict[str, str]:
    """
    Génère une palette de couleurs moderne pour la visualisation.
    
    Attribue des couleurs distinctes à chaque label d'altitude, en utilisant
    une couleur grise pour "Non admissible" et des couleurs vives pour les autres.
    
    Args:
        labels_order (List[str]): Liste ordonnée des labels à colorier.
                                 Exemple: ["500 m", "400 m", "Non admissible"]
    
    Returns:
        Dict[str, str]: Dictionnaire mapping label → couleur hexadécimale.
                       Exemple: {"500 m": "#2563eb", "Non admissible": "#e5e7eb"}
    
    Example:
        >>> labels = ["500 m", "400 m", "Non admissible"]
        >>> palette = build_modern_color_palette(labels)
        >>> print(palette["Non admissible"])  # "#e5e7eb"
        >>> print(len([c for c in palette.values() if c != "#e5e7eb"]))  # 2 (couleurs vives)
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
            # Sélection cyclique des couleurs modernes
            color = MODERN_COLORS[color_index % len(MODERN_COLORS)]
            color_map[label] = color
            color_index += 1
            colors_used += 1
            logger.debug(f"Label '{label}' → couleur {color}")
    
    logger.info(f"Palette générée : {colors_used} couleurs vives, {len(labels_order) - colors_used} grises")
    
    # Vérification de la diversité des couleurs
    unique_colors = len(set(color_map.values()))
    if unique_colors < len(labels_order) and len(labels_order) > len(MODERN_COLORS) + 1:
        logger.warning(f"Répétition de couleurs : {len(labels_order)} labels pour {len(MODERN_COLORS)} couleurs disponibles")
    
    return color_map


# ====== FONCTIONS D'EXPORT ======

def export_map_to_image(
    figure: go.Figure,
    output_path: Path,
    format: str = "png",
    width: int = 1200,
    height: int = 800,
    scale: float = 1.0
) -> bool:
    """
    Exporte la carte vers un fichier image.
    
    Args:
        figure (go.Figure): Figure Plotly à exporter
        output_path (Path): Chemin de sortie du fichier
        format (str): Format d'export ("png", "jpg", "svg", "pdf")
        width (int): Largeur de l'image en pixels
        height (int): Hauteur de l'image en pixels
        scale (float): Facteur d'échelle pour la qualité
        
    Returns:
        bool: True si l'export a réussi
        
    Raises:
        ValueError: Si le format n'est pas supporté
        IOError: En cas d'erreur d'écriture
        
    Example:
        >>> success = export_map_to_image(fig, Path("export/carte.png"))
        >>> if success:
        ...     print("Carte exportée avec succès")
    """
    logger.info(f"Export de la carte vers {output_path} ({format})")
    
    # Validation du format
    supported_formats = ["png", "jpg", "jpeg", "svg", "pdf"]
    if format.lower() not in supported_formats:
        raise ValueError(f"Format non supporté : {format}. Formats supportés : {supported_formats}")
    
    # Création du répertoire de sortie si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Configuration des options d'export
        export_options = {
            "format": format.lower(),
            "width": width,
            "height": height,
            "scale": scale
        }
        
        # Export selon le format
        if format.lower() in ["png", "jpg", "jpeg"]:
            figure.write_image(str(output_path), **export_options)
        elif format.lower() == "svg":
            figure.write_image(str(output_path), **export_options)
        elif format.lower() == "pdf":
            figure.write_image(str(output_path), **export_options)
        
        # Validation de l'export
        if not output_path.exists():
            raise IOError(f"Le fichier d'export n'a pas été créé : {output_path}")
        
        file_size = output_path.stat().st_size
        logger.info(f"Export réussi : {file_size} octets")
        return True
        
    except Exception as e:
        error_msg = f"Erreur lors de l'export : {e}"
        logger.error(error_msg)
        raise IOError(error_msg)


def export_data_to_csv(
    map_df: pd.DataFrame,
    output_path: Path,
    include_metadata: bool = True
) -> bool:
    """
    Exporte les données de la carte vers un fichier CSV.
    
    Args:
        map_df (pd.DataFrame): DataFrame de la carte à exporter
        output_path (Path): Chemin de sortie du fichier CSV
        include_metadata (bool): Si True, ajoute des métadonnées en commentaires
        
    Returns:
        bool: True si l'export a réussi
        
    Raises:
        IOError: En cas d'erreur d'écriture
        
    Example:
        >>> success = export_data_to_csv(map_df, Path("export/resultats.csv"))
        >>> if success:
        ...     print("Données exportées avec succès")
    """
    logger.info(f"Export des données vers {output_path}")
    
    # Création du répertoire de sortie si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Préparation des données pour l'export
        export_df = map_df.copy()
        
        # Ajout de métadonnées si demandé
        if include_metadata:
            # Création d'un fichier avec métadonnées en en-tête
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                # Métadonnées en commentaires
                f.write(f"# Export Atlas Entraxes - {pd.Timestamp.now()}\n")
                f.write(f"# Total départements : {len(export_df)}\n")
                f.write(f"# Admissibles : {(export_df['AltMax_sel'].notna()).sum()}\n")
                f.write(f"# Non admissibles : {(export_df['AltMax_sel'].isna()).sum()}\n")
                f.write("#\n")
                
                # Données CSV
                export_df.to_csv(f, index=False, encoding="utf-8")
        else:
            # Export simple sans métadonnées
            export_df.to_csv(output_path, index=False, encoding="utf-8")
        
        # Validation de l'export
        if not output_path.exists():
            raise IOError(f"Le fichier CSV n'a pas été créé : {output_path}")
        
        file_size = output_path.stat().st_size
        logger.info(f"Export CSV réussi : {file_size} octets")
        return True
        
    except Exception as e:
        error_msg = f"Erreur lors de l'export CSV : {e}"
        logger.error(error_msg)
        raise IOError(error_msg)


# ====== FONCTIONS UTILITAIRES ======

def format_altitude(altitude: Union[float, int, str]) -> str:
    """
    Formate une altitude pour l'affichage.
    
    Args:
        altitude: Valeur d'altitude (numérique ou chaîne)
        
    Returns:
        str: Altitude formatée (ex: "3.00 m")
        
    Example:
        >>> format_altitude(3.0)
        '3.00 m'
        >>> format_altitude("2.5")
        '2.50 m'
    """
    try:
        # Conversion en float
        alt_float = float(altitude)
        
        # Formatage avec 2 décimales
        if alt_float.is_integer():
            return f"{int(alt_float)}.00 m"
        else:
            return f"{alt_float:.2f} m"
            
    except (ValueError, TypeError):
        return str(altitude)


def get_unique_configurations(rules_df: pd.DataFrame) -> List[str]:
    """
    Extrait la liste des configurations uniques depuis les règles.
    
    Args:
        rules_df (pd.DataFrame): DataFrame des règles de calcul
        
    Returns:
        List[str]: Liste des configurations uniques, triées
        
    Example:
        >>> configs = get_unique_configurations(rules_df)
        >>> print(f"Configurations disponibles : {len(configs)}")
    """
    if rules_df.empty or "Config" not in rules_df.columns:
        return []
    
    unique_configs = rules_df["Config"].unique()
    return sorted([str(config) for config in unique_configs if pd.notna(config)])


def get_entraxe_options() -> List[Tuple[str, str]]:
    """
    Retourne les options d'entraxe disponibles.
    
    Returns:
        List[Tuple[str, str]]: Liste des tuples (valeur, label) pour les entraxes
        
    Example:
        >>> options = get_entraxe_options()
        >>> for value, label in options:
        ...     print(f"{value} -> {label}")
    """
    return [
        ("AltMax_3m", "3.00 m"),
        ("AltMax_2_5m", "2.50 m")
    ]


def validate_dataframe_structure(df: pd.DataFrame, required_columns: List[str], df_name: str = "DataFrame") -> bool:
    """
    Valide la structure d'un DataFrame.
    
    Vérifie qu'un DataFrame n'est pas vide et contient toutes les colonnes requises.
    
    Args:
        df (pd.DataFrame): DataFrame à valider
        required_columns (List[str]): Liste des colonnes requises
        df_name (str): Nom du DataFrame pour les messages d'erreur
    
    Returns:
        bool: True si la structure est valide
        
    Raises:
        ValueError: Si la structure n'est pas valide
    
    Example:
        >>> df = pd.DataFrame({"A": [1], "B": [2]})
        >>> validate_dataframe_structure(df, ["A", "B"], "test")
        True
    """
    logger.debug(f"Validation structure {df_name}...")
    
    if df.empty:
        error_msg = f"{df_name} est vide"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        available_cols = ", ".join(df.columns.tolist())
        error_msg = (
            f"Colonnes manquantes dans {df_name} : {missing_columns}. "
            f"Colonnes disponibles : {available_cols}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.debug(f"{df_name} validé : {len(df)} lignes, {len(df.columns)} colonnes")
    return True


# ====== FONCTIONS DE LOGGING ET DEBUG ======

def log_dataframe_info(df: pd.DataFrame, name: str = "DataFrame") -> None:
    """
    Affiche des informations de debug sur un DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame à analyser
        name (str): Nom du DataFrame pour les logs
    """
    logger.debug(f"=== Informations {name} ===")
    logger.debug(f"Dimensions : {df.shape}")
    logger.debug(f"Colonnes : {df.columns.tolist()}")
    logger.debug(f"Types : {df.dtypes.to_dict()}")
    
    if not df.empty:
        logger.debug(f"Aperçu :")
        logger.debug(f"\n{df.head(3).to_string()}")
    
    # Vérification des valeurs manquantes
    null_counts = df.isnull().sum()
    if null_counts.any():
        logger.debug(f"Valeurs manquantes : {null_counts[null_counts > 0].to_dict()}")


# ====== TESTS UNITAIRES INTÉGRÉS ======

def run_utils_tests() -> bool:
    """
    Exécute les tests unitaires des fonctions utilitaires.
    
    Returns:
        bool: True si tous les tests passent
    """
    logger.info("=== TESTS UNITAIRES UTILS VERSION ULTIMATE ===")
    
    try:
        # Test 1 : Palette de couleurs
        labels = ["500 m", "400 m", "Non admissible"]
        palette = build_modern_color_palette(labels)
        assert len(palette) == 3
        assert palette["Non admissible"] == GRAY_COLOR
        assert len(set(palette.values())) == 3  # Couleurs distinctes
        logger.info("✓ Test palette couleurs : OK")
        
        # Test 2 : Validation DataFrame
        df_test = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        validate_dataframe_structure(df_test, ["A", "B"], "test")
        logger.info("✓ Test validation DataFrame : OK")
        
        # Test 3 : Statistiques altitudes
        df_stats = pd.DataFrame({"AltMax_sel": [500, np.nan, 400, 600]})
        stats = get_altitude_statistics(df_stats)
        assert stats["total"] == 4
        assert stats["admissible"] == 3
        assert stats["non_admissible"] == 1
        logger.info("✓ Test statistiques altitudes : OK")
        
        # Test 4 : Format altitude
        assert format_altitude(3.0) == "3.00 m"
        assert format_altitude(2.5) == "2.50 m"
        assert format_altitude("4.75") == "4.75 m"
        logger.info("✓ Test format altitude : OK")
        
        # Test 5 : Options entraxe
        options = get_entraxe_options()
        assert len(options) == 2
        assert options[0][0] == "AltMax_3m"
        assert options[1][0] == "AltMax_2_5m"
        logger.info("✓ Test options entraxe : OK")
        
        logger.info("=== TOUS LES TESTS PASSENT - VERSION ULTIMATE ===")
        return True
        
    except Exception as e:
        logger.error(f"Échec des tests : {e}")
        return False


# ====== POINT D'ENTRÉE POUR TESTS ======

if __name__ == "__main__":
    """
    Tests et démonstration des fonctions utilitaires VERSION ULTIMATE.
    """
    # Configuration logging pour les tests
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("=== TESTS VERSION ULTIMATE - Fusion Claude + Assistant ===")
    print("🚀 Le meilleur des deux mondes réuni !")
    
    success = run_utils_tests()
    
    if success:
        print("✅ TOUS LES TESTS PASSENT - Module utils.py ULTIMATE prêt !")
        print("🎯 Fonctionnalités disponibles :")
        print("   • Calculs géographiques (centroïdes)")
        print("   • Traitement des données (construction cartes)")
        print("   • Gestion des couleurs (palettes modernes)")
        print("   • Export complet (images + CSV)")
        print("   • Utilitaires avancés (formatage, validation)")
        print("   • Tests unitaires complets")
        sys.exit(0)
    else:
        print("❌ Certains tests ont échoué")
        sys.exit(1)
