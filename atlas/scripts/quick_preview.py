"""
quick_preview.py

Script de prévisualisation rapide des résultats de configuration pour Atlas Entraxes.
Permet de tester rapidement les calculs d'altitude pour une configuration donnée.

Ce script charge les données normalisées et les règles de calcul, puis affiche
un aperçu des résultats pour chaque type d'entraxe (3.00m et 2.50m).

Usage:
    python scripts/quick_preview.py

Fichiers requis:
    - data/dept_zones_NORMALISE.csv (zones départementales normalisées)
    - data/results_by_combo.csv (règles de calcul)

Auteur: apesseu
Version: 1.0
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ====== CONFIGURATION (VOTRE LOGIQUE EXACTE) ======

CONFIG = "holyspirit4"   # change si besoin
SHOW = 10               # nb de lignes à montrer

# Chemins des fichiers (votre logique exacte)
root = Path(__file__).resolve().parent.parent
ZONES_FILE = root / "atlas/data/dept_zones_NORMALISE.csv"
RULES_FILE = root / "atlas/data/results_by_combo.csv"

# Types de données pandas (vos définitions exactes)
ZONES_DTYPES = {
    "Dept": "string",
    "Nom": "string", 
    "Zone_Vent": "string",
    "Zone_Neige": "string"
}
"""Types de données pour le fichier des zones départementales."""

RULES_DTYPES = {
    "Config": "string",
    "Zone_Vent": "string",
    "Zone_Neige": "string",
    "AltMax_3m": "string",
    "AltMax_2_5m": "string"
}
"""Types de données pour le fichier des règles de calcul."""

# Configuration des entraxes (votre logique exacte)
ENTRAXE_CONFIGS = [("AltMax_3m", "3.00 m"), ("AltMax_2_5m", "2.50 m")]
"""Liste des configurations d'entraxe à tester : (colonne, label)."""

# ====== FONCTIONS DE VALIDATION ======

def validate_required_files() -> bool:
    """
    Valide l'existence des fichiers de données requis.
    
    Vérifie que les fichiers dept_zones_NORMALISE.csv et results_by_combo.csv
    existent et sont accessibles en lecture.
    
    Returns:
        bool: True si tous les fichiers requis sont présents et accessibles
        
    Raises:
        FileNotFoundError: Si un ou plusieurs fichiers requis sont manquants
        
    Example:
        >>> validate_required_files()
        True
    """
    logger.info("Validation des fichiers requis...")
    
    required_files = [
        (ZONES_FILE, "fichier des zones départementales normalisées"),
        (RULES_FILE, "fichier des règles de calcul")
    ]
    
    missing_files = []
    
    for file_path, description in required_files:
        if not file_path.exists():
            error_msg = f"{description} introuvable : {file_path}"
            logger.error(error_msg)
            missing_files.append(error_msg)
        elif not file_path.is_file():
            error_msg = f"{description} n'est pas un fichier : {file_path}"
            logger.error(error_msg)
            missing_files.append(error_msg)
        else:
            logger.info(f"✓ {description} trouvé")
    
    if missing_files:
        error_summary = "Fichiers manquants :\n" + "\n".join(f"  • {f}" for f in missing_files)
        raise FileNotFoundError(error_summary)
    
    logger.info("Tous les fichiers requis sont présents")
    return True


def validate_dataframes(dz: pd.DataFrame, rb: pd.DataFrame) -> bool:
    """
    Valide le contenu des DataFrames chargés.
    
    Vérifie que les DataFrames ne sont pas vides et contiennent les colonnes
    attendues.
    
    Args:
        dz (pd.DataFrame): DataFrame des zones départementales
        rb (pd.DataFrame): DataFrame des règles de calcul
        
    Returns:
        bool: True si les DataFrames sont valides
        
    Raises:
        ValueError: Si les DataFrames ne sont pas valides
        
    Example:
        >>> dz = pd.DataFrame({"Dept": ["01"], "Nom": ["Ain"]})
        >>> rb = pd.DataFrame({"Config": ["test"]})
        >>> validate_dataframes(dz, rb)
        True
    """
    logger.info("Validation du contenu des DataFrames...")
    
    # Validation du DataFrame des zones
    if dz.empty:
        raise ValueError("Le fichier des zones départementales est vide")
    
    missing_zones_cols = [col for col in ZONES_DTYPES.keys() if col not in dz.columns]
    if missing_zones_cols:
        raise ValueError(f"Colonnes manquantes dans le fichier des zones : {missing_zones_cols}")
    
    # Validation du DataFrame des règles
    if rb.empty:
        raise ValueError("Le fichier des règles de calcul est vide")
    
    missing_rules_cols = [col for col in RULES_DTYPES.keys() if col not in rb.columns]
    if missing_rules_cols:
        raise ValueError(f"Colonnes manquantes dans le fichier des règles : {missing_rules_cols}")
    
    logger.info(f"DataFrames validés : {len(dz)} zones, {len(rb)} règles")
    return True


# ====== FONCTIONS DE CHARGEMENT ======

def load_data_files() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Charge les fichiers de données CSV.
    
    Lit les fichiers dept_zones_NORMALISE.csv et results_by_combo.csv avec
    les types de données appropriés.
    
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (zones_df, rules_df)
        
    Raises:
        ValueError: En cas d'erreur lors du chargement des fichiers
        
    Example:
        >>> zones_df, rules_df = load_data_files()
        >>> print(f"Chargé : {len(zones_df)} zones, {len(rules_df)} règles")
    """
    logger.info("Chargement des fichiers de données...")
    
    try:
        # Chargement des zones (votre code exact)
        dz = pd.read_csv(ZONES_FILE, dtype=ZONES_DTYPES)
        logger.info(f"Zones chargées : {len(dz)} départements")
        
        # Chargement des règles (votre code exact)
        rb = pd.read_csv(RULES_FILE, dtype=RULES_DTYPES)
        logger.info(f"Règles chargées : {len(rb)} règles")
        
        return dz, rb
        
    except Exception as e:
        error_msg = f"Erreur lors du chargement des données : {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)


# ====== FONCTIONS DE TRAITEMENT ======

def get_configuration_rules(rb: pd.DataFrame, config: str) -> pd.DataFrame:
    """
    Récupère les règles pour une configuration spécifique.
    
    Filtre le DataFrame des règles pour ne garder que celles correspondant
    à la configuration demandée.
    
    Args:
        rb (pd.DataFrame): DataFrame des règles de calcul
        config (str): Nom de la configuration à rechercher
        
    Returns:
        pd.DataFrame: Règles filtrées pour la configuration
        
    Example:
        >>> rules_df = pd.DataFrame({"Config": ["test", "other"], "Zone_Vent": ["1", "2"]})
        >>> config_rules = get_configuration_rules(rules_df, "test")
        >>> print(len(config_rules))  # 1
    """
    logger.info(f"Recherche des règles pour la configuration '{config}'...")
    
    # Filtrage des règles (votre logique exacte)
    config_rules = rb.loc[rb["Config"] == config].copy()
    
    logger.info(f"Règles trouvées pour '{config}' : {len(config_rules)}")
    return config_rules


def process_entraxe_configuration(
    dz: pd.DataFrame,
    config_rules: pd.DataFrame,
    entraxe_col: str,
    config: str,
    label: str
) -> Optional[pd.DataFrame]:
    """
    Traite une configuration d'entraxe spécifique.
    
    Applique la logique de calcul pour un type d'entraxe donné :
    - Sélection des règles pour cette entraxe
    - Jointure avec les zones départementales
    - Calcul des altitudes et statuts
    
    Args:
        dz (pd.DataFrame): DataFrame des zones départementales
        config_rules (pd.DataFrame): Règles pour la configuration
        entraxe_col (str): Colonne d'entraxe à traiter (ex: "AltMax_3m")
        config (str): Nom de la configuration
        label (str): Label d'affichage (ex: "3.00 m")
        
    Returns:
        Optional[pd.DataFrame]: DataFrame avec résultats calculés, ou None si aucune règle
        
    Example:
        >>> zones = pd.DataFrame({"Dept": ["01"], "Zone_Vent": ["1"], "Zone_Neige": ["1"]})
        >>> rules = pd.DataFrame({"Zone_Vent": ["1"], "Zone_Neige": ["1"], "AltMax_3m": ["500"]})
        >>> result = process_entraxe_configuration(zones, rules, "AltMax_3m", "test", "3.00 m")
        >>> print(result["Statut"].iloc[0])  # "Admissible"
    """
    logger.info(f"Traitement de l'entraxe {label} pour la configuration {config}...")
    
    # Sélection des règles pour cette entraxe (votre logique exacte)
    sel = config_rules.loc[:, ["Zone_Vent", "Zone_Neige", entraxe_col]].copy()
    
    if sel.empty:
        logger.warning(f"Aucune règle trouvée pour {config} - {label}")
        print(f"[{label}] aucune règle pour {config}")
        return None
    
    # Jointure zones ↔ règles (votre logique exacte)
    m = dz.merge(sel, on=["Zone_Vent", "Zone_Neige"], how="left")
    
    # Calcul des altitudes et statuts (votre logique exacte)
    m["AltMax_sel"] = pd.to_numeric(m[entraxe_col], errors="coerce")
    m["Statut"] = m["AltMax_sel"].apply(lambda x: "Admissible" if pd.notna(x) else "Non admissible")
    
    logger.info(f"Calculs terminés pour {label} : {len(m)} départements traités")
    return m


def display_results(m: pd.DataFrame, config: str, label: str, show_lines: int) -> None:
    """
    Affiche les résultats calculés pour une configuration d'entraxe.
    
    Affiche les statistiques et un aperçu des résultats au format défini.
    
    Args:
        m (pd.DataFrame): DataFrame avec les résultats calculés
        config (str): Nom de la configuration
        label (str): Label d'affichage de l'entraxe
        show_lines (int): Nombre de lignes à afficher dans l'aperçu
        
    Example:
        >>> results_df = pd.DataFrame({
        ...     "Dept": ["01"], "Nom": ["Ain"], "Statut": ["Admissible"]
        ... })
        >>> display_results(results_df, "test", "3.00 m", 5)
        === test — 3.00 m ===
        ...
    """
    logger.info(f"Affichage des résultats pour {config} - {label}...")
    
    # Calcul des statistiques (votre logique exacte)
    total_lines = len(m)
    admissible_count = (m["Statut"] == "Admissible").sum()
    non_admissible_count = (m["Statut"] == "Non admissible").sum()
    
    # Affichage du header (votre format exact)
    print(f"\n=== {config} — {label} ===")
    
    # Affichage des statistiques (votre format exact)
    print(f"Lignes: {total_lines} | Admissibles: {admissible_count} | Non admissibles: {non_admissible_count}")
    
    # Affichage de l'aperçu des données (votre format exact)
    columns_to_show = ["Dept", "Nom", "Zone_Vent", "Zone_Neige", "AltMax_sel", "Statut"]
    preview_data = m[columns_to_show].head(show_lines)
    print(preview_data.to_string(index=False))
    
    logger.info(f"Résultats affichés : {admissible_count}/{total_lines} admissibles")


# ====== FONCTION PRINCIPALE ======

def main(config: str = CONFIG, show_lines: int = SHOW) -> bool:
    """
    Fonction principale de prévisualisation des résultats de configuration.
    
    Orchestration complète du processus de prévisualisation :
    1. Validation des fichiers requis
    2. Chargement des données
    3. Validation des DataFrames
    4. Recherche des règles pour la configuration
    5. Traitement et affichage pour chaque entraxe
    
    Args:
        config (str): Nom de la configuration à tester (défaut: CONFIG)
        show_lines (int): Nombre de lignes à afficher (défaut: SHOW)
        
    Returns:
        bool: True si la prévisualisation s'est déroulée avec succès
        
    Raises:
        FileNotFoundError: Si des fichiers requis sont manquants
        ValueError: En cas d'erreur de validation ou de traitement
        
    Example:
        >>> success = main("holyspirit4", 10)
        >>> if success:
        ...     print("Prévisualisation réussie")
    """
    logger.info("=== DÉBUT DE LA PRÉVISUALISATION DES RÉSULTATS ===")
    logger.info(f"Configuration : {config}")
    logger.info(f"Lignes à afficher : {show_lines}")
    
    try:
        # Étape 1 : Validation des fichiers
        validate_required_files()
        
        # Étape 2 : Chargement des données (votre code exact)
        dz, rb = load_data_files()
        
        # Étape 3 : Validation des DataFrames
        validate_dataframes(dz, rb)
        
        # Étape 4 : Recherche des règles pour la configuration
        config_rules = get_configuration_rules(rb, config)
        
        if config_rules.empty:
            available_configs = sorted(rb["Config"].dropna().unique().tolist())
            logger.warning(f"Configuration '{config}' introuvable")
            print(f"\n⚠️ Configuration '{config}' introuvable.")
            print(f"📋 Configurations disponibles : {', '.join(available_configs[:10])}")
            if len(available_configs) > 10:
                print(f"    ... et {len(available_configs) - 10} autres")
            return False
        
        # Étape 5 : Traitement pour chaque entraxe (votre logique exacte)
        results_found = False
        
        for entraxe_col, label in ENTRAXE_CONFIGS:
            result_df = process_entraxe_configuration(
                dz, config_rules, entraxe_col, config, label
            )
            
            if result_df is not None:
                display_results(result_df, config, label, show_lines)
                results_found = True
        
        if not results_found:
            logger.warning(f"Aucun résultat trouvé pour la configuration '{config}'")
            return False
        
        logger.info("=== PRÉVISUALISATION TERMINÉE AVEC SUCCÈS ===")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la prévisualisation : {e}")
        raise


# ====== POINT D'ENTRÉE ======

if __name__ == "__main__":
    """
    Point d'entrée du script de prévisualisation.
    
    Exécute la prévisualisation avec les paramètres par défaut ou passés
    en ligne de commande.
    
    Usage:
        python scripts/quick_preview.py
    """
    try:
        # Exécution de la prévisualisation (votre logique exacte)
        success = main()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interruption utilisateur (Ctrl+C)")
        print("\n⏹️ Script interrompu par l'utilisateur.")
        sys.exit(130)
        
    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ [ERREUR] {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        print(f"\n💥 Erreur inattendue : {e}")
        sys.exit(1)