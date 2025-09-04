"""
Script de normalisation des données départementales depuis Excel vers CSV.

Transforme le fichier Excel source en format CSV compatible avec l'application.
"""

import pandas as pd
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration des chemins
root = Path(__file__).resolve().parent.parent
XLSX = root / "data/dept_zones.xlsx"
OUT = root / "data/dept_zones_NORMALISE.csv"
SHEET_NAME = "Zonage_Departements"

# Colonnes attendues dans l'Excel
EXPECTED_COLUMNS = [
    "Code_Dept", "Nom_Departement", "Zone_Neige_Max", 
    "Zone_Vent_Max", "Zones_Neige_Orig", "Zones_Vent_Orig"
]

# Normalisation des valeurs de zones neige
NEIGE_NORMALIZE_VALUES = {"0": "", "Aucune": ""}


def load_excel_data() -> pd.DataFrame:
    """Charge les données depuis le fichier Excel."""
    logger.info(f"Lecture de la feuille '{SHEET_NAME}' depuis {XLSX}...")
    
    if not XLSX.exists():
        raise FileNotFoundError(f"Fichier Excel introuvable : {XLSX}")
    
    try:
        with pd.ExcelFile(XLSX) as xls:
            if SHEET_NAME not in xls.sheet_names:
                available_sheets = ", ".join(xls.sheet_names)
                raise ValueError(f"Feuille '{SHEET_NAME}' introuvable. Feuilles disponibles : {available_sheets}")
        
        df = pd.read_excel(XLSX, sheet_name=SHEET_NAME, dtype={"Code_Dept": "string"})
        logger.info(f"Données lues avec succès : {len(df)} lignes")
        return df
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier Excel : {e}")


def validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Valide et nettoie les données du DataFrame."""
    logger.info("Validation de la structure des données...")
    
    if df.empty:
        raise ValueError("Le fichier Excel ne contient aucune donnée")
    
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        available_cols = ", ".join(df.columns.tolist())
        raise ValueError(f"Colonnes manquantes : {missing}. Colonnes disponibles : {available_cols}")
    
    logger.info(f"Structure validée : {len(df)} lignes, {len(df.columns)} colonnes")
    
    # Nettoyage des données
    logger.info("Nettoyage des données...")
    df_clean = df.copy()
    df_clean["Code_Dept"] = df_clean["Code_Dept"].astype("string").str.strip()
    df_clean["Nom_Departement"] = df_clean["Nom_Departement"].astype("string").str.strip()
    df_clean["Zone_Vent_Max"] = df_clean["Zone_Vent_Max"].astype("string").str.strip()
    df_clean["Zone_Neige_Max"] = df_clean["Zone_Neige_Max"].astype("string").str.strip()
    
    # Vérification des codes départements problématiques
    null_codes = df_clean["Code_Dept"].isnull().sum()
    empty_codes = df_clean["Code_Dept"].eq("").sum()
    if null_codes > 0 or empty_codes > 0:
        logger.warning(f"Codes département problématiques : {null_codes} null, {empty_codes} vides")
    
    logger.info("Nettoyage terminé")
    return df_clean


def create_normalized_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame normalisé au format requis par l'application."""
    logger.info("Création du DataFrame normalisé...")
    
    norm = pd.DataFrame({
        "Dept": df["Code_Dept"],
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


def save_normalized_csv(norm: pd.DataFrame) -> None:
    """Sauvegarde le DataFrame normalisé au format CSV."""
    logger.info(f"Sauvegarde vers {OUT}...")
    
    # Créer le répertoire de sortie si nécessaire
    OUT.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        norm.to_csv(OUT, index=False, encoding="utf-8")
        
        if not OUT.exists():
            raise IOError(f"Le fichier de sortie n'a pas été créé : {OUT}")
        
        file_size = OUT.stat().st_size
        logger.info(f"Sauvegarde réussie : {file_size} octets")
    except Exception as e:
        raise IOError(f"Erreur lors de la sauvegarde : {e}")


def main() -> bool:
    """Fonction principale de normalisation des données départementales."""
    logger.info("=== DÉBUT DE LA NORMALISATION DES DONNÉES DÉPARTEMENTALES ===")
    logger.info(f"Fichier source : {XLSX}")
    logger.info(f"Fichier destination : {OUT}")
    
    try:
        # Chargement des données
        df = load_excel_data()
        
        # Validation et nettoyage
        df_clean = validate_and_clean_data(df)
        
        # Normalisation
        norm = create_normalized_dataframe(df_clean)
        
        # Sauvegarde
        save_normalized_csv(norm)
        
        # Affichage des résultats
        print(f"✅ Écrit: {OUT} ({len(norm)} lignes)")
        print(norm.head(5).to_string(index=False))
        
        logger.info("=== NORMALISATION TERMINÉE AVEC SUCCÈS ===")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la normalisation : {e}")
        raise


if __name__ == "__main__":
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