from pathlib import Path
import pandas as pd

CONFIG = "holyspirit4"   # change si besoin
SHOW = 10                # nb de lignes à montrer

root = Path(__file__).resolve().parent.parent
dz = pd.read_csv(root/"data/dept_zones_NORMALISE.csv",
                 dtype={"Dept":"string","Nom":"string","Zone_Vent":"string","Zone_Neige":"string"})
rb = pd.read_csv(root/"data/results_by_combo.csv",
                 dtype={"Config":"string","Zone_Vent":"string","Zone_Neige":"string",
                        "AltMax_3m":"string","AltMax_2_5m":"string"})

for entraxe_col, label in [("AltMax_3m","3.00 m"), ("AltMax_2_5m","2.50 m")]:
    sel = rb.loc[rb["Config"]==CONFIG, ["Zone_Vent","Zone_Neige", entraxe_col]].copy()
    if sel.empty:
        print(f"[{label}] aucune règle pour {CONFIG}")
        continue

    m = dz.merge(sel, on=["Zone_Vent","Zone_Neige"], how="left")
    m["AltMax_sel"] = pd.to_numeric(m[entraxe_col], errors="coerce")
    m["Statut"] = m["AltMax_sel"].apply(lambda x: "Admissible" if pd.notna(x) else "Non admissible")

    print(f"\n=== {CONFIG} — {label} ===")
    print(f"Lignes: {len(m)} | Admissibles: {(m['Statut']=='Admissible').sum()} | Non admissibles: {(m['Statut']=='Non admissible').sum()}")
    print(m[["Dept","Nom","Zone_Vent","Zone_Neige","AltMax_sel","Statut"]].head(SHOW).to_string(index=False))
