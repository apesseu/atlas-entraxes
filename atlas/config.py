"""
Configuration et constantes pour Atlas Entraxes.

Ce module centralise les chemins de fichiers et fonctions de validation
nécessaires au bon fonctionnement de l'application.
"""

from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Chemins des fichiers de données
DATA_DIR = Path(__file__).parent / "data"

GEOJSON_PATH = DATA_DIR / "departements.geojson"
ZONES_PATH = DATA_DIR / "dept_zones_NORMALISE.csv"
RULES_PATH = DATA_DIR / "results_by_combo.csv"
DETAILS_PATH = DATA_DIR / "details.csv"

# Types de données pour la cohérence pandas
ZONES_DTYPES = {
    "Dept": "string",
    "Nom": "string", 
    "Zone_Vent": "string",
    "Zone_Neige": "string"
}

RULES_DTYPES = {
    "Config": "string",
    "Zone_Vent": "string",
    "Zone_Neige": "string",
    "AltMax_3m": "string",
    "AltMax_2_5m": "string"
}

DETAILS_DTYPES = {
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


def check_required_files():
    """
    Vérifie que tous les fichiers requis sont présents et accessibles.
    
    Raises:
        FileNotFoundError: Si un fichier requis est manquant
    """
    logger.info("Démarrage de la validation des fichiers requis...")
    
    required_files = [
        (GEOJSON_PATH, "données géographiques des départements"),
        (ZONES_PATH, "zones réglementaires par département"), 
        (RULES_PATH, "règles de calcul principales")
    ]
    
    validation_errors = []
    
    for file_path, description in required_files:
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Fichier introuvable : {file_path}")
            
            if not file_path.is_file():
                raise FileNotFoundError(f"Le chemin n'est pas un fichier : {file_path}")
            
            # Test d'accès en lecture
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)
            except PermissionError as e:
                raise PermissionError(f"Impossible de lire le fichier : {e}")
            
            # Validation de la taille (max 100MB)
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                raise ValueError(f"Fichier trop volumineux : {file_size_mb:.1f} MB")
            
            logger.info(f"Fichier {description} validé avec succès : {file_path}")
            logger.info(f"Taille du fichier '{file_path.name}' validée : {file_size_mb:.1f} MB")
            logger.info(f"✓ {description} : OK")
            
        except (FileNotFoundError, PermissionError, ValueError) as e:
            validation_errors.append(str(e))
            logger.error(f"✗ {description} : ERREUR - {e}")
    
    if validation_errors:
        error_summary = (
            f"Validation échouée. {len(validation_errors)} erreur(s) détectée(s) :\n" +
            "\n".join(f"  • {error}" for error in validation_errors)
        )
        logger.critical(error_summary)
        raise FileNotFoundError(error_summary)
    
    logger.info(f"✅ Validation réussie ! {len(required_files)} fichier(s) validé(s).")


def setup_logging(level="INFO"):
    """Configure le système de logging pour l'application."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.info(f"Logging configuré au niveau {level}")


# Configuration automatique du logging
setup_logging("INFO")