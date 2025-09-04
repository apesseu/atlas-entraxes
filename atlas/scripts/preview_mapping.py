"""
preview_mapping.py

Script de normalisation des données départementales depuis Excel vers CSV.
Version identique à normalize_dept_zones.py pour prévisualisation/backup.

Ce script est un duplicata du script de normalisation principal, utilisé pour
tester les transformations avant application sur les données de production.

Usage:
    python scripts/preview_mapping.py

Fichiers requis:
    - data/dept_zones.xlsx (fichier source Excel)
    
Fichiers produits:
    - data/dept_zones_NORMALISE.csv (fichier normalisé pour l'app)

Auteur: apesseu
Version: 1.0
"""

import pandas as pd
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ====== CONFIGURATION ======

# Chemins des fichiers (votre logique exacte)
root = Path(__file__).resolve().parent.parent
XLSX = root / "atlas/data/dept_zones.xlsx"          # on lit TON Excel tel quel
OUT = root / "atlas/data/dept_zones_NORMALISE.csv"  # sortie pour l'app

# Paramètres Excel
SHEET_NAME = "Zonage_Departements"
"""Nom de la feuille Excel à traiter."""

# Colonnes attendues dans l'Excel (votre logique exacte)
EXPECTED_COLUMNS = [
    "Code_Dept",
    "Nom_Departement",
    "Zone_Neige_Max", 
    "Zone_Vent_Max",
    "Zones_Neige_Orig",
    "Zones_Vent_Orig"
]
"""Liste des colonnes qui doivent être présentes dans le fichier Excel."""

# Valeurs à normaliser pour les zones neige (votre logique exacte)
NEIGE_NORMALIZE_VALUES = {"0": "", "Aucune": ""}
"""Dictionnaire des valeurs de Zone_Neige_Max à remplacer par une chaîne vide."""

# Types de données pandas
EXCEL_DTYPES = {"Code_Dept": "string"}
"""Types de données pour la lecture du fichier Excel."""

# ====== FONCTIONS DE VALIDATION ======

def validate_input_file() -> bool:
    """
    Valide l'existence et l'accessibilité du fichier Excel source.
    
    Returns:
        bool: True si le fichier est valide et accessible
        
    Raises:
        FileNotFoundError: Si le fichier Excel n'existe pas
        ValueError: Si le fichier n'est pas accessible ou lisible
        
    Example:
        >>> validate_input_file()
        True
    """
    logger.info(f"Validation du fichier Excel source : {XLSX}")
    
    if not XLSX.exists():
        error_msg = f"Fichier Excel introuvable : {XLSX.absolute()}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    if not XLSX.is_file():
        error_msg = f"Le chemin spécifié n'est pas un fichier : {XLSX.absolute()}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Test rapide d'ouverture du fichier Excel
    try:
        with pd.ExcelFile(XLSX) as xls:
            if SHEET_NAME not in xls.sheet_names:
                available_sheets = ", ".join(xls.sheet_names)
                error_msg = (
                    f"Feuille '{SHEET_NAME}' introuvable dans {XLSX}. "
                    f"Feuilles disponibles : {available_sheets}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Impossible d'ouvrir le fichier Excel : {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Fichier Excel validé avec succès")
    return True


def validate_dataframe_structure(df: pd.DataFrame) -> bool:
    """
    Valide la structure du DataFrame lu depuis Excel.
    
    Vérifie que toutes les colonnes attendues sont présentes et que le DataFrame
    n'est pas vide.
    
    Args:
        df (pd.DataFrame): DataFrame à valider
        
    Returns:
        bool: True si la structure est valide
        
    Raises:
        ValueError: Si des colonnes sont manquantes ou si le DataFrame est vide
        
    Example:
        >>> df = pd.DataFrame({"Code_Dept": ["01"], "Nom_Departement": ["Ain"]})
        >>> validate_dataframe_structure(df)  # Lèvera une exception (colonnes manquantes)
    """
    logger.info("Validation de la structure des données...")
    
    # Vérifier que le DataFrame n'est pas vide
    if df.empty:
        error_msg = "Le fichier Excel ne contient aucune donnée"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Vérifier les colonnes (votre logique exacte)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        available_cols = ", ".join(df.columns.tolist())
        error_msg = (
            f"Colonnes manquantes : {missing}. "
            f"Colonnes disponibles : {available_cols}"
        )
        logger.error(error_msg)
        raise ValueError(f"[ERREUR] colonnes manquantes: {missing}")
    
    logger.info(f"Structure validée : {len(df)} lignes, {len(df.columns)} colonnes")
    return True


def validate_output_directory() -> bool:
    """
    Valide que le répertoire de sortie existe et est accessible en écriture.
    
    Returns:
        bool: True si le répertoire de sortie est accessible
        
    Raises:
        PermissionError: Si le répertoire n'est pas accessible en écriture
        
    Example:
        >>> validate_output_directory()
        True
    """
    output_dir = OUT.parent
    logger.info(f"Validation du répertoire de sortie : {output_dir}")
    
    # Créer le répertoire s'il n'existe pas
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        error_msg = f"Impossible de créer le répertoire de sortie : {e}"
        logger.error(error_msg)
        raise PermissionError(error_msg)
    
    # Vérifier les permissions d'écriture
    if not output_dir.exists() or not output_dir.is_dir():
        error_msg = f"Répertoire de sortie invalide : {output_dir}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Répertoire de sortie validé")
    return True


# ====== FONCTIONS DE TRAITEMENT ======

def load_excel_data() -> pd.DataFrame:
    """
    Charge les données depuis le fichier Excel.
    
    Lit la feuille Excel spécifiée avec les types de données appropriés.
    
    Returns:
        pd.DataFrame: DataFrame contenant les données Excel brutes
        
    Raises:
        ValueError: En cas d'erreur lors de la lecture du fichier
        
    Example:
        >>> df = load_excel_data()
        >>> print(len(df))  # Affiche le nombre de lignes lues
    """
    logger.info(f"Lecture de la feuille '{SHEET_NAME}' depuis {XLSX}...")
    
    try:
        # 1) Lire Excel (1ère feuille) avec tes noms de colonnes d'origine
        df = pd.read_excel(XLSX, sheet_name=SHEET_NAME, dtype=EXCEL_DTYPES)
        
        logger.info(f"Données lues avec succès : {len(df)} lignes")
        return df
        
    except Exception as e:
        error_msg = f"Erreur lors de la lecture du fichier Excel : {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie les données du DataFrame.
    
    Applique les transformations de nettoyage sur les colonnes textuelles :
    - Conversion en type string
    - Suppression des espaces en début/fin de chaîne
    
    Args:
        df (pd.DataFrame): DataFrame brut à nettoyer
        
    Returns:
        pd.DataFrame: DataFrame nettoyé
        
    Example:
        >>> df_raw = pd.DataFrame({"Code_Dept": [" 01 "], "Nom_Departement": [" Ain "]})
        >>> df_clean = clean_dataframe(df_raw)
        >>> print(df_clean["Code_Dept"].iloc[0])  # "01" (espaces supprimés)
    """
    logger.info("Nettoyage des données...")
    
    # Copie pour éviter de modifier l'original
    df_clean = df.copy()
    
    # Nettoyage des colonnes textuelles (votre logique exacte)
    df_clean["Code_Dept"] = df_clean["Code_Dept"].astype("string").str.strip()
    df_clean["Nom_Departement"] = df_clean["Nom_Departement"].astype("string").str.strip()
    df_clean["Zone_Vent_Max"] = df_clean["Zone_Vent_Max"].astype("string").str.strip()
    df_clean["Zone_Neige_Max"] = df_clean["Zone_Neige_Max"].astype("string").str.strip()
    
    # Log des statistiques de nettoyage
    null_codes = df_clean["Code_Dept"].isnull().sum()
    empty_codes = df_clean["Code_Dept"].eq("").sum()
    
    if null_codes > 0 or empty_codes > 0:
        logger.warning(f"Codes département problématiques : {null_codes} null, {empty_codes} vides")
    
    logger.info("Nettoyage terminé")
    return df_clean


def create_normalized_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crée le DataFrame normalisé au format requis par l'application.
    
    Transforme les données nettoyées au format attendu par Atlas Entraxes :
    - Renommage des colonnes selon les conventions de l'app
    - Normalisation des valeurs de zones neige (0/Aucune → chaîne vide)
    
    Args:
        df (pd.DataFrame): DataFrame nettoyé
        
    Returns:
        pd.DataFrame: DataFrame au format application avec colonnes :
                     - Dept : Code département (jointure avec GeoJSON)
                     - Nom : Nom du département  
                     - Zone_Vent : Zone vent maximale
                     - Zone_Neige : Zone neige maximale (normalisée)
                     
    Example:
        >>> df_clean = pd.DataFrame({
        ...     "Code_Dept": ["01"], "Nom_Departement": ["Ain"],
        ...     "Zone_Vent_Max": ["2"], "Zone_Neige_Max": ["0"]
        ... })
        >>> df_norm = create_normalized_dataframe(df_clean)
        >>> print(df_norm["Zone_Neige"].iloc[0])  # "" (normalisé depuis "0")
    """
    logger.info("Création du DataFrame normalisé...")
    
    # 3) Normalisation pour l'app (votre logique exacte - neige '0'/'Aucune' => vide)
    norm = pd.DataFrame({
        "Dept": df["Code_Dept"],            # jointure avec properties.code du GeoJSON
        "Nom": df["Nom_Departement"],
        "Zone_Vent": df["Zone_Vent_Max"],
        "Zone_Neige": df["Zone_Neige_Max"].replace(NEIGE_NORMALIZE_VALUES),
    })
    
    # Statistiques de normalisation
    original_neige_values = df["Zone_Neige_Max"].value_counts()
    normalized_neige_values = norm["Zone_Neige"].value_counts()
    
    logger.info(f"DataFrame normalisé créé : {len(norm)} lignes")
    logger.info(f"Valeurs Zone_Neige avant : {original_neige_values.to_dict()}")
    logger.info(f"Valeurs Zone_Neige après : {normalized_neige_values.to_dict()}")
    
    return norm


def save_normalized_csv(norm: pd.DataFrame) -> bool:
    """
    Sauvegarde le DataFrame normalisé au format CSV.
    
    Écrit le DataFrame au format CSV avec les paramètres standardisés :
    - Encodage UTF-8
    - Pas d'index numérique
    - Séparateur virgule
    
    Args:
        norm (pd.DataFrame): DataFrame normalisé à sauvegarder
        
    Returns:
        bool: True si la sauvegarde a réussi
        
    Raises:
        IOError: En cas d'erreur lors de la sauvegarde
        
    Example:
        >>> df = pd.DataFrame({"Dept": ["01"], "Nom": ["Ain"]})
        >>> save_normalized_csv(df)
        True
    """
    logger.info(f"Sauvegarde vers {OUT}...")
    
    try:
        # Sauvegarde avec vos paramètres exacts
        norm.to_csv(OUT, index=False, encoding="utf-8")
        
        # Validation de la sauvegarde
        if not OUT.exists():
            raise IOError(f"Le fichier de sortie n'a pas été créé : {OUT}")
        
        file_size = OUT.stat().st_size
        logger.info(f"Sauvegarde réussie : {file_size} octets")
        return True
        
    except Exception as e:
        error_msg = f"Erreur lors de la sauvegarde : {e}"
        logger.error(error_msg)
        raise IOError(error_msg)


# ====== FONCTION PRINCIPALE ======

def main() -> bool:
    """
    Fonction principale de prévisualisation/normalisation des données départementales.
    
    Orchestration complète du processus de normalisation :
    1. Validation des fichiers d'entrée et de sortie
    2. Chargement des données Excel
    3. Validation de la structure des données
    4. Nettoyage des données
    5. Normalisation au format application
    6. Sauvegarde du fichier CSV
    7. Affichage des résultats
    
    Returns:
        bool: True si la normalisation s'est déroulée avec succès
        
    Raises:
        FileNotFoundError: Si le fichier Excel source est introuvable
        ValueError: En cas d'erreur de validation ou de traitement
        IOError: En cas d'erreur de sauvegarde
        
    Example:
        >>> success = main()
        >>> if success:
        ...     print("Normalisation réussie")
    """
    logger.info("=== DÉBUT DE LA PRÉVISUALISATION/NORMALISATION ===")
    logger.info(f"Fichier source : {XLSX}")
    logger.info(f"Fichier destination : {OUT}")
    
    try:
        # Étape 1 : Validations préalables
        validate_input_file()
        validate_output_directory()
        
        # Étape 2 : Chargement des données
        df = load_excel_data()
        
        # Étape 3 : Validation de la structure
        validate_dataframe_structure(df)
        
        # Étape 4 : Nettoyage des données
        df_clean = clean_dataframe(df)
        
        # Étape 5 : Normalisation
        norm = create_normalized_dataframe(df_clean)
        
        # Étape 6 : Sauvegarde
        save_normalized_csv(norm)
        
        # Étape 7 : Affichage des résultats (votre format exact)
        print(f"✅ Écrit: {OUT} ({len(norm)} lignes)")
        print(norm.head(5).to_string(index=False))
        
        logger.info("=== PRÉVISUALISATION/NORMALISATION TERMINÉE AVEC SUCCÈS ===")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la normalisation : {e}")
        raise


# ====== POINT D'ENTRÉE ======

if __name__ == "__main__":
    """
    Point d'entrée du script de prévisualisation/normalisation.
    
    Usage:
        python scripts/preview_mapping.py
    """
    try:
        success = main()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interruption utilisateur (Ctrl+C)")
        print("\n⏹️ Script interrompu par l'utilisateur.")
        sys.exit(130)
        
    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"\n❌ [ERREUR] {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        print(f"\n💥 Erreur inattendue : {e}")
        sys.exit(1)