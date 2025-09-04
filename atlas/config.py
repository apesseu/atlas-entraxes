"""
Configuration et constantes pour Atlas Entraxes.

Ce module centralise tous les paramètres de configuration, chemins de fichiers,
et constantes utilisées dans l'application Atlas Entraxes. Il fournit également
les fonctions de validation pour s'assurer que tous les fichiers requis sont
présents avant le démarrage de l'application.

Auteur: apesseu
Version: 0.1.0
"""

from pathlib import Path
from typing import List, Optional, Tuple
import logging
import sys

# Configuration du logging pour ce module
logger = logging.getLogger(__name__)

# ====== CHEMINS DE FICHIERS ======

# Répertoire racine des données
DATA_DIR: Path = Path(__file__).parent / "data"
"""Répertoire contenant tous les fichiers de données de l'application."""

# Fichiers de données principaux
GEOJSON_PATH: Path = DATA_DIR / "departements.geojson"
"""Fichier GeoJSON contenant les contours géographiques des départements français."""

ZONES_PATH: Path = DATA_DIR / "dept_zones_NORMALISE.csv"
"""Fichier CSV contenant l'association département -> zones vent/neige."""

RULES_PATH: Path = DATA_DIR / "results_by_combo.csv"
"""Fichier CSV contenant les règles de calcul (cœur métier de l'application)."""

DETAILS_PATH: Path = DATA_DIR / "details.csv"
"""Fichier CSV contenant les métadonnées descriptives des configurations."""

# Fichiers optionnels
EXCEL_ZONES_PATH: Path = DATA_DIR / "dept_zones.xlsx"
"""Fichier Excel source des zones (optionnel, pour référence)."""

# ====== PARAMÈTRES APPLICATION ======

APP_TITLE: str = "Atlas Entraxes 2025"
"""Titre principal de l'application Dash."""

APP_DESCRIPTION: str = "Visualisation moderne des altitudes maximales par département"
"""Description affichée sous le titre principal."""

DEBUG_MODE: bool = True
"""Active le mode debug de l'application Dash."""

HOST: str = "127.0.0.1"
"""Adresse IP d'écoute du serveur Dash."""

PORT: int = 8050
"""Port d'écoute du serveur Dash."""

# ====== PARAMÈTRES TECHNIQUES ======

DEFAULT_ENCODING: str = "utf-8"
"""Encodage par défaut pour la lecture des fichiers texte."""

MAX_FILE_SIZE_MB: int = 100
"""Taille maximale autorisée pour les fichiers de données (en MB)."""

# Types de données pandas pour garantir la cohérence
ZONES_DTYPES: dict = {
    "Dept": "string",
    "Nom": "string", 
    "Zone_Vent": "string",
    "Zone_Neige": "string"
}
"""Types de données pour le fichier des zones départementales."""

RULES_DTYPES: dict = {
    "Config": "string",
    "Zone_Vent": "string",
    "Zone_Neige": "string",
    "AltMax_3m": "string",
    "AltMax_2_5m": "string"
}
"""Types de données pour le fichier des règles de calcul."""

DETAILS_DTYPES: dict = {
    "Config": "string",
    "Type_Serre": "string",
    "Hauteur_Poteau": "string",
    "Largeur": "string",
    "Toiture": "string",
    "Facade": "string",
    "Traverse": "string",
    "Materiau": "string",
    "Resistance_Vent": "string",
    "Date_Creation": "string",
    "Version": "string"
}
"""Types de données pour le fichier des détails de configuration."""

# ====== FONCTIONS DE VALIDATION ======

def validate_file_existence(file_path: Path, file_description: str = "") -> bool:
    """
    Valide qu'un fichier existe et est accessible en lecture.
    
    Args:
        file_path (Path): Chemin vers le fichier à valider.
        file_description (str, optional): Description du fichier pour les messages d'erreur.
    
    Returns:
        bool: True si le fichier existe et est accessible.
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        PermissionError: Si le fichier n'est pas accessible en lecture.
    """
    description = file_description or f"'{file_path.name}'"
    
    if not file_path.exists():
        error_msg = f"Le fichier {description} est introuvable : {file_path.absolute()}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    if not file_path.is_file():
        error_msg = f"Le chemin {description} n'est pas un fichier : {file_path.absolute()}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Vérifier les permissions de lecture
    try:
        with open(file_path, 'r', encoding=DEFAULT_ENCODING) as f:
            f.read(1)  # Lire juste 1 caractère pour tester l'accès
    except PermissionError as e:
        error_msg = f"Impossible de lire le fichier {description} : {e}"
        logger.error(error_msg)
        raise PermissionError(error_msg)
    except UnicodeDecodeError:
        # Fichier binaire, on teste juste l'ouverture en mode binaire
        try:
            with open(file_path, 'rb') as f:
                f.read(1)
        except PermissionError as e:
            error_msg = f"Impossible de lire le fichier {description} : {e}"
            logger.error(error_msg)
            raise PermissionError(error_msg)
    
    logger.info(f"Fichier {description} validé avec succès : {file_path}")
    return True


def validate_file_size(file_path: Path, max_size_mb: int = MAX_FILE_SIZE_MB) -> bool:
    """
    Valide que la taille d'un fichier ne dépasse pas la limite autorisée.
    
    Args:
        file_path (Path): Chemin vers le fichier à valider.
        max_size_mb (int, optional): Taille maximale en MB.
        
    Returns:
        bool: True si la taille est acceptable.
        
    Raises:
        ValueError: Si le fichier est trop volumineux.
    """
    file_size_bytes = file_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        error_msg = (
            f"Le fichier '{file_path.name}' est trop volumineux "
            f"({file_size_mb:.1f} MB > {max_size_mb} MB)"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Taille du fichier '{file_path.name}' validée : {file_size_mb:.1f} MB")
    return True


def check_required_files(include_optional: bool = False) -> List[Path]:
    """
    Vérifie que tous les fichiers requis pour l'application sont présents et accessibles.
    
    Args:
        include_optional (bool, optional): Si True, inclut aussi les fichiers optionnels.
    
    Returns:
        List[Path]: Liste des fichiers validés avec succès.
        
    Raises:
        FileNotFoundError: Si un ou plusieurs fichiers requis sont manquants.
    """
    logger.info("Démarrage de la validation des fichiers requis...")
    
    # Fichiers obligatoires avec leurs descriptions
    required_files: List[Tuple[Path, str]] = [
        (GEOJSON_PATH, "données géographiques des départements"),
        (ZONES_PATH, "zones réglementaires par département"), 
        (RULES_PATH, "règles de calcul principales")
    ]
    
    # Fichiers optionnels
    optional_files: List[Tuple[Path, str]] = [
        (DETAILS_PATH, "détails des configurations"),
        (EXCEL_ZONES_PATH, "fichier Excel des zones (source)")
    ]
    
    validated_files: List[Path] = []
    validation_errors: List[str] = []
    
    # Validation des fichiers requis
    for file_path, description in required_files:
        try:
            validate_file_existence(file_path, description)
            validate_file_size(file_path)
            validated_files.append(file_path)
            logger.info(f"✓ {description} : OK")
            
        except (FileNotFoundError, PermissionError, ValueError) as e:
            validation_errors.append(str(e))
            logger.error(f"✗ {description} : ERREUR - {e}")
    
    # Validation des fichiers optionnels si demandé
    if include_optional:
        for file_path, description in optional_files:
            try:
                if file_path.exists():
                    validate_file_existence(file_path, description)
                    validate_file_size(file_path)
                    validated_files.append(file_path)
                    logger.info(f"✓ {description} (optionnel) : OK")
                else:
                    logger.info(f"○ {description} (optionnel) : absent (pas d'erreur)")
                    
            except (PermissionError, ValueError) as e:
                # Pour les fichiers optionnels, on log l'erreur mais on n'arrête pas
                logger.warning(f"! {description} (optionnel) : ATTENTION - {e}")
    
    # Si des erreurs sur fichiers requis, on arrête tout
    if validation_errors:
        error_summary = (
            f"Validation échouée. {len(validation_errors)} erreur(s) détectée(s) :\n" +
            "\n".join(f"  • {error}" for error in validation_errors)
        )
        logger.critical(error_summary)
        raise FileNotFoundError(error_summary)
    
    logger.info(f"✅ Validation réussie ! {len(validated_files)} fichier(s) validé(s).")
    return validated_files


def validate_data_consistency() -> bool:
    """
    Valide la cohérence entre les différents fichiers de données.
    
    Returns:
        bool: True si tous les fichiers sont cohérents.
        
    Raises:
        ValueError: En cas d'incohérence détectée.
    """
    try:
        import pandas as pd
    except ImportError:
        logger.warning("Pandas non disponible, validation de cohérence ignorée")
        return True
    
    logger.info("Validation de la cohérence des données...")
    
    try:
        # Chargement des données
        zones_df = pd.read_csv(ZONES_PATH, dtype=ZONES_DTYPES)
        rules_df = pd.read_csv(RULES_PATH, dtype=RULES_DTYPES)
        
        # Validation optionnelle du fichier details
        if DETAILS_PATH.exists():
            details_df = pd.read_csv(DETAILS_PATH, dtype=DETAILS_DTYPES)
            
            # Vérifier que toutes les configs dans details existent dans rules
            configs_details = set(details_df['Config'].dropna().unique())
            configs_rules = set(rules_df['Config'].dropna().unique())
            
            missing_configs = configs_details - configs_rules
            if missing_configs:
                raise ValueError(
                    f"Configurations dans details.csv absentes de results_by_combo.csv: "
                    f"{', '.join(missing_configs)}"
                )
            
            logger.info(f"✓ Cohérence details.csv ↔ results_by_combo.csv : {len(configs_details)} configurations")
        
        # Vérifier que toutes les zones dans rules existent dans zones
        zones_in_rules = set()
        zones_in_rules.update(rules_df['Zone_Vent'].dropna().unique())
        zones_in_rules.update(rules_df['Zone_Neige'].dropna().unique())
        
        zones_available = set()
        zones_available.update(zones_df['Zone_Vent'].dropna().unique())
        zones_available.update(zones_df['Zone_Neige'].dropna().unique())
        
        missing_zones = zones_in_rules - zones_available
        if missing_zones:
            raise ValueError(
                f"Zones dans results_by_combo.csv absentes de dept_zones_NORMALISE.csv: "
                f"{', '.join(missing_zones)}"
            )
        
        logger.info(f"✓ Cohérence results_by_combo.csv ↔ dept_zones_NORMALISE.csv : {len(zones_in_rules)} zones")
        logger.info("✅ Validation de cohérence réussie !")
        return True
        
    except Exception as e:
        error_msg = f"Erreur lors de la validation de cohérence : {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def get_data_dir_info() -> dict:
    """
    Retourne des informations sur le répertoire de données.
    
    Returns:
        dict: Informations sur le répertoire (existence, permissions, contenu, etc.)
    """
    info = {
        "path": str(DATA_DIR.absolute()),
        "exists": DATA_DIR.exists(),
        "is_directory": DATA_DIR.is_dir() if DATA_DIR.exists() else False,
        "file_count": 0,
        "files": [],
        "readable": False
    }
    
    if info["exists"] and info["is_directory"]:
        try:
            files = list(DATA_DIR.iterdir())
            info["file_count"] = len([f for f in files if f.is_file()])
            info["files"] = [f.name for f in files if f.is_file()]
            info["readable"] = True
        except PermissionError:
            logger.warning(f"Impossible de lister le contenu de {DATA_DIR}")
    
    return info


def get_config_details(config_name: str) -> Optional[dict]:
    """
    Récupère les détails d'une configuration spécifique.
    
    Args:
        config_name (str): Nom de la configuration (ex: "holyspirit4")
    
    Returns:
        Optional[dict]: Dictionnaire avec les détails de la configuration,
                       ou None si la configuration n'existe pas.
    """
    if not DETAILS_PATH.exists():
        logger.info(f"Fichier {DETAILS_PATH} non trouvé, détails non disponibles")
        return None
    
    try:
        import pandas as pd
        details_df = pd.read_csv(DETAILS_PATH, dtype=DETAILS_DTYPES)
        
        # Recherche de la configuration
        config_row = details_df[details_df['Config'] == config_name]
        
        if config_row.empty:
            logger.info(f"Configuration '{config_name}' non trouvée dans details.csv")
            return None
        
        # Conversion en dictionnaire (première ligne si plusieurs)
        details_dict = config_row.iloc[0].to_dict()
        
        # Nettoyage des valeurs NaN
        details_clean = {
            key: value for key, value in details_dict.items() 
            if pd.notna(value) and str(value).strip()
        }
        
        logger.info(f"Détails trouvés pour la configuration '{config_name}'")
        return details_clean
        
    except Exception as e:
        logger.error(f"Erreur lors de la lecture des détails pour '{config_name}': {e}")
        return None


def list_available_configs() -> List[str]:
    """
    Retourne la liste de toutes les configurations disponibles.
    
    Returns:
        List[str]: Liste triée des noms de configurations disponibles.
    """
    configs = set()
    
    try:
        import pandas as pd
        
        # Configurations depuis rules.csv (fichier principal)
        if RULES_PATH.exists():
            rules_df = pd.read_csv(RULES_PATH, dtype=RULES_DTYPES)
            configs.update(rules_df['Config'].dropna().unique())
        
        # Configurations depuis details.csv (métadonnées)
        if DETAILS_PATH.exists():
            details_df = pd.read_csv(DETAILS_PATH, dtype=DETAILS_DTYPES)
            configs.update(details_df['Config'].dropna().unique())
        
        sorted_configs = sorted(list(configs))
        logger.info(f"Configurations disponibles : {len(sorted_configs)}")
        return sorted_configs
        
    except Exception as e:
        logger.error(f"Erreur lors de la lecture des configurations : {e}")
        return []


def setup_logging(level: str = "INFO") -> None:
    """
    Configure le système de logging pour l'application.
    
    Args:
        level (str, optional): Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.info(f"Logging configuré au niveau {level}")


# ====== INITIALISATION DU MODULE ======

# Configuration automatique du logging lors de l'import
if __name__ != "__main__":
    setup_logging("INFO" if not DEBUG_MODE else "DEBUG")


# ====== POINT D'ENTRÉE POUR TESTS ======

if __name__ == "__main__":
    """
    Point d'entrée pour tester le module de configuration.
    
    Usage:
        python config.py
    """
    print("=== Test du module de configuration Atlas Entraxes ===")
    
    # Configuration du logging pour les tests
    setup_logging("DEBUG")
    
    try:
        # Affichage des informations de base
        print(f"\n📁 Répertoire de données : {DATA_DIR.absolute()}")
        data_info = get_data_dir_info()
        print(f"   Existe : {data_info['exists']}")
        print(f"   Fichiers : {data_info['file_count']}")
        if data_info['files']:
            print("   Contenu :", ", ".join(data_info['files']))
        
        print(f"\n🔧 Configuration application :")
        print(f"   Titre : {APP_TITLE}")
        print(f"   Debug : {DEBUG_MODE}")
        print(f"   Serveur : {HOST}:{PORT}")
        
        # Test de validation des fichiers
        print(f"\n🔍 Validation des fichiers requis...")
        validated_files = check_required_files(include_optional=True)
        print(f"✅ {len(validated_files)} fichier(s) validé(s) avec succès !")
        
        # Test de cohérence des données
        print(f"\n🔗 Validation de la cohérence des données...")
        try:
            validate_data_consistency()
            print("✅ Cohérence des données validée !")
        except Exception as e:
            print(f"⚠️  Validation de cohérence échouée : {e}")
        
        # Test des fonctions utilitaires
        print(f"\n📋 Test des fonctions utilitaires...")
        configs = list_available_configs()
        print(f"   Configurations trouvées : {len(configs)}")
        if configs:
            print(f"   Exemples : {', '.join(configs[:3])}")
            
            # Test de récupération des détails pour la première config
            if configs:
                details = get_config_details(configs[0])
                if details:
                    print(f"   Détails pour '{configs[0]}' : {len(details)} champs")
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        sys.exit(1)
    
    print(f"\n✨ Module de configuration prêt à être utilisé !")