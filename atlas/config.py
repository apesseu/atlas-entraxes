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
DATA_DIR: Path = Path("data")
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

# ====== FONCTIONS DE VALIDATION ======

def validate_file_existence(file_path: Path, file_description: str = "") -> bool:
    """
    Valide qu'un fichier existe et est accessible en lecture.
    
    Args:
        file_path (Path): Chemin vers le fichier à valider.
        file_description (str, optional): Description du fichier pour les messages d'erreur.
            Defaults to "".
    
    Returns:
        bool: True si le fichier existe et est accessible.
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        PermissionError: Si le fichier n'est pas accessible en lecture.
        
    Example:
        >>> validate_file_existence(Path("data/test.csv"), "fichier de test")
        True
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
        max_size_mb (int, optional): Taille maximale en MB. Defaults to MAX_FILE_SIZE_MB.
        
    Returns:
        bool: True si la taille est acceptable.
        
    Raises:
        ValueError: Si le fichier est trop volumineux.
        
    Example:
        >>> validate_file_size(Path("data/small.csv"), max_size_mb=10)
        True
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
    
    Cette fonction est appelée au démarrage de l'application pour s'assurer que
    tous les fichiers de données nécessaires sont disponibles avant de continuer.
    
    Args:
        include_optional (bool, optional): Si True, inclut aussi les fichiers optionnels
            dans la validation. Defaults to False.
    
    Returns:
        List[Path]: Liste des fichiers validés avec succès.
        
    Raises:
        FileNotFoundError: Si un ou plusieurs fichiers requis sont manquants.
        PermissionError: Si un fichier n'est pas accessible en lecture.
        ValueError: Si un fichier est trop volumineux.
        
    Example:
        >>> validated_files = check_required_files()
        >>> print(f"Fichiers validés : {len(validated_files)}")
        Fichiers validés : 3
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


def get_data_dir_info() -> dict:
    """
    Retourne des informations sur le répertoire de données.
    
    Utile pour le debugging et les logs de diagnostic.
    
    Returns:
        dict: Informations sur le répertoire (existence, permissions, contenu, etc.)
        
    Example:
        >>> info = get_data_dir_info()
        >>> print(f"Répertoire existe : {info['exists']}")
        >>> print(f"Fichiers présents : {info['file_count']}")
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


def setup_logging(level: str = "INFO") -> None:
    """
    Configure le système de logging pour l'application.
    
    Args:
        level (str, optional): Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Defaults to "INFO".
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configuration basique du logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.info(f"Logging configuré au niveau {level}")


# ====== INITIALISATION DU MODULE ======

# Configuration automatique du logging lors de l'import
if __name__ != "__main__":  # Seulement si importé, pas si exécuté directement
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
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        sys.exit(1)
    
    print(f"\n✨ Module de configuration prêt à être utilisé !")