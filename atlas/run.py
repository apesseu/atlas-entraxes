#!/usr/bin/env python3
"""
Lanceur principal Atlas Entraxes.

Normalise les données et lance l'application web.
"""

import sys

def main():
    """Lance la normalisation des données puis l'application."""
    # Normalisation des données
    try:
        from scripts.normalize_dept_zones import main as normalize
        normalize()
        print("Normalisation réussie")
    except Exception as e:
        print(f"Attention - Normalisation échouée : {e}")
        print("L'application peut fonctionner si les données sont déjà normalisées")
    
    # Lancement de l'application
    try:
        from app import main as app_main
        print("Application chargée avec succès")
        print("Ouverture sur http://127.0.0.1:8050/")
        print("Appuyez sur Ctrl+C pour arrêter")
        
        app_main()
        
    except Exception as e:
        print(f"Erreur de lancement : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()