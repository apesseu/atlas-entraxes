"""
Script de prévisualisation rapide des résultats de configuration.

Teste rapidement les calculs d'altitude pour une configuration donnée.
"""

import sys
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = "holyspirit4"
SHOW = 10

# Chemins des fichiers
root = Path(__file__).resolve().parent.parent
ZONES_FILE = root / "data/dept_zones_NORMALISE.csv"
RULES_FILE = root / "data/results_by_combo.csv"

# Types de données pandas
ZONES_DTYPES = {
    "Dept": "string", "Nom": "string", 
    "Zone_Vent": "string", "Zone_Neige": "string"
}

RULES_DTYPES = {
    "Config": "string", "Zone_Vent": "string", "Zone_Neige": "string",
    "AltMax_3m": "string", "AltMax_2_5m": "string"
}

# Configurations d'entraxe à tester
ENTRAXE_CONFIGS = [("AltMax_3m", "3.00 m"), ("AltMax_2_5m", "2.50 m")]


def load_data_files():
    """Charge les fichiers de données CSV."""
    logger.info("Chargement des fichiers de données...")
    
    if not ZONES_FILE.exists():
        raise FileNotFoundError(f"Fichier zones introuvable : {ZONES_FILE}")
    if not RULES_FILE.exists():
        raise FileNotFoundError(f"Fichier règles introuvable : {RULES_FILE}")
    
    try:
        dz = pd.read_csv(ZONES_FILE, dtype=ZONES_DTYPES)
        rb = pd.read_csv(RULES_FILE, dtype=RULES_DTYPES)
        
        if dz.empty or rb.empty:
            raise ValueError("Un des fichiers de données est vide")
        
        logger.info(f"Données chargées : {len(dz)} zones, {len(rb)} règles")
        return dz, rb
        
    except Exception as e:
        raise ValueError(f"Erreur lors du chargement des données : {e}")


def process_entraxe_configuration(dz, config_rules, entraxe_col, config, label):
    """Traite une configuration d'entraxe spécifique."""
    logger.info(f"Traitement de l'entraxe {label} pour la configuration {config}...")
    
    # Sélection des règles pour cette entraxe
    sel = config_rules.loc[:, ["Zone_Vent", "Zone_Neige", entraxe_col]].copy()
    
    if sel.empty:
        logger.warning(f"Aucune règle trouvée pour {config} - {label}")
        print(f"[{label}] aucune règle pour {config}")
        return None
    
    # Jointure zones ↔ règles
    m = dz.merge(sel, on=["Zone_Vent", "Zone_Neige"], how="left")
    
    # Calcul des altitudes et statuts
    m["AltMax_sel"] = pd.to_numeric(m[entraxe_col], errors="coerce")
    m["Statut"] = m["AltMax_sel"].apply(lambda x: "Admissible" if pd.notna(x) else "Non admissible")
    
    logger.info(f"Calculs terminés pour {label} : {len(m)} départements traités")
    return m


def display_results(m, config, label, show_lines):
    """Affiche les résultats calculés pour une configuration d'entraxe."""
    logger.info(f"Affichage des résultats pour {config} - {label}...")
    
    # Calcul des statistiques
    total_lines = len(m)
    admissible_count = (m["Statut"] == "Admissible").sum()
    non_admissible_count = (m["Statut"] == "Non admissible").sum()
    
    # Affichage
    print(f"\n=== {config} — {label} ===")
    print(f"Lignes: {total_lines} | Admissibles: {admissible_count} | Non admissibles: {non_admissible_count}")
    
    # Aperçu des données
    columns_to_show = ["Dept", "Nom", "Zone_Vent", "Zone_Neige", "AltMax_sel", "Statut"]
    preview_data = m[columns_to_show].head(show_lines)
    print(preview_data.to_string(index=False))
    
    logger.info(f"Résultats affichés : {admissible_count}/{total_lines} admissibles")


def main(config=CONFIG, show_lines=SHOW):
    """Fonction principale de prévisualisation des résultats."""
    logger.info("=== DÉBUT DE LA PRÉVISUALISATION DES RÉSULTATS ===")
    logger.info(f"Configuration : {config}")
    logger.info(f"Lignes à afficher : {show_lines}")
    
    try:
        # Chargement des données
        dz, rb = load_data_files()
        
        # Recherche des règles pour la configuration
        config_rules = rb.loc[rb["Config"] == config].copy()
        logger.info(f"Règles trouvées pour '{config}' : {len(config_rules)}")
        
        if config_rules.empty:
            available_configs = sorted(rb["Config"].dropna().unique().tolist())
            logger.warning(f"Configuration '{config}' introuvable")
            print(f"\n⚠️ Configuration '{config}' introuvable.")
            print(f"📋 Configurations disponibles : {', '.join(available_configs[:10])}")
            if len(available_configs) > 10:
                print(f"    ... et {len(available_configs) - 10} autres")
            return False
        
        # Traitement pour chaque entraxe
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
        
    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ [ERREUR] {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        print(f"\n💥 Erreur inattendue : {e}")
        sys.exit(1)