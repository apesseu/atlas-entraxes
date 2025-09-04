#!/usr/bin/env python3
"""
run.py - Lanceur unifié Atlas Entraxes

Ce fichier fait tout en une fois :
1. Normalise les données si nécessaire
2. Lance l'application Dash
3. Une seule commande : poetry run python atlas/run.py
"""

import sys
from pathlib import Path

def main():
    """Fonction principale qui orchestre normalisation + lancement"""
    print("🚀 Atlas Entraxes - Lanceur unifié")
    print("=" * 50)
    
    # Étape 1 : Normalisation des données
    print("📊 Étape 1 : Normalisation des données...")
    try:
        from scripts.normalize_dept_zones import main as normalize
        success = normalize()
        if success:
            print("✅ Normalisation réussie")
        else:
            print("⚠️ Normalisation échouée")
    except Exception as e:
        print(f"❌ Erreur de normalisation : {e}")
        print("💡 L'app peut quand même fonctionner si les données sont déjà normalisées")
    
    print()
    
    # Étape 2 : Lancement de l'application
    print("🌐 Étape 2 : Lancement de l'application...")
    try:
        from app import app
        print("✅ Application chargée avec succès")
        print("🌍 Ouverture sur http://127.0.0.1:8050/")
        print("⏹️  Appuyez sur Ctrl+C pour arrêter")
        print("-" * 50)
        
        # Lancement de l'app
        app.run(debug=True)
        
    except Exception as e:
        print(f"❌ Erreur de lancement : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
