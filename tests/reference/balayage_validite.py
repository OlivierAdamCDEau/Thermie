"""
balayage_validite.py — ÉTAPE 3, TÂCHE C2/C3, complément.

Le premier balayage de `mesure_validite_m.py` plaçait ses seuils par
convention (0,05 · 0,10 · 0,15 · 0,20 · 0,30 · 0,50 · 1,00). Quatre d'entre
eux n'écartent rien du tout : la distribution observée est bien plus resserrée
que ces valeurs. Un balayage dont la moitié des points est inopérante ne
balaie pas la distribution, il la survole.

Celui-ci place ses seuils SUR la distribution observée — ses déciles — puis y
ajoute les valeurs rondes usuelles et le repère de 0,15 du projet clos, qui
n'est jamais retenu (D15). Il recalcule tout depuis
`validite_m_par_point.csv`, sans refaire les régressions.

Il ajoute aussi la question que le balayage par précision ne pose pas : une
pente peut être TRÈS PRÉCISE et NE RIEN VOULOIR DIRE. Le tableau porte donc,
à côté de la demi-largeur, le R² et l'appartenance à [0 ; 1,2].

Sortie : out/etape3/validite_m_balayage.csv (remplace le précédent)
         out/etape3/validite_m_criteres_croises.csv
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _commun import RACINE, ecrire_csv, _f

OUT = RACINE / "out" / "etape3"
REPERE_PROJET_CLOS = 0.15


def main():
    t = pd.read_csv(OUT / "validite_m_par_point.csv", sep=";")
    t = t.dropna(subset=["demi_largeur_ic95"])

    # Seuils : deciles de la distribution observee (tous coefficients confondus)
    # + valeurs rondes + le repere du projet clos.
    v = t["demi_largeur_ic95"]
    seuils = sorted(set(
        [round(float(v.quantile(q)), 4) for q in np.arange(0.1, 1.0, 0.1)]
        + [0.05, 0.10, REPERE_PROJET_CLOS, 0.20]))

    lignes = []
    for coef, sub in t.groupby("coefficient"):
        for s in seuils:
            sortis = sub[sub["demi_largeur_ic95"] > s]
            lignes.append(dict(
                coefficient=coef, seuil_demi_largeur_ic95=s,
                statut_du_seuil=("REPERE du projet clos, NON retenu (D15)"
                                 if abs(s - REPERE_PROJET_CLOS) < 1e-9
                                 else "decile ou valeur ronde"),
                n_estimations=int(len(sub)),
                n_sortent=int(len(sortis)),
                part_sortante_pct=_f(100.0 * len(sortis) / max(len(sub), 1)),
                BLE3_0_sort=("oui" if "BLE3-0" in set(sortis["point"]) else "non"),
                points_sortants=", ".join(sorted(set(sortis["point"])))[:500]))
    ecrire_csv(OUT / "validite_m_balayage.csv",
               ["coefficient", "seuil_demi_largeur_ic95", "statut_du_seuil",
                "n_estimations", "n_sortent", "part_sortante_pct",
                "BLE3_0_sort", "points_sortants"],
               lignes, tri=["coefficient", "seuil_demi_largeur_ic95"])

    # --- Ce que chaque critere de validite ecarterait, isolement ----------
    croise = []
    for coef, sub in t.groupby("coefficient"):
        n = len(sub)
        tests = [
            ("precision : demi-IC 95 % > 0,05", sub["demi_largeur_ic95"] > 0.05),
            ("precision : demi-IC 95 % > 0,10", sub["demi_largeur_ic95"] > 0.10),
            ("precision : demi-IC 95 % > 0,15 (repere, non retenu)",
             sub["demi_largeur_ic95"] > REPERE_PROJET_CLOS),
            ("variance expliquee : R2 < 0,30 (regle de core.py:258)",
             sub["r2"] < 0.30),
            ("domaine : pente hors [0 ; 1,2] (regle de core.py:258)",
             sub["dans_0_1_2"] == "non"),
            ("effectif : n < 20 (regle de core.py:251)", sub["n"] < 20),
        ]
        for libelle, masque in tests:
            pts = sorted(set(sub.loc[masque, "point"]))
            croise.append(dict(
                coefficient=coef, critere=libelle, n_estimations=n,
                n_ecartes=int(masque.sum()),
                part_ecartee_pct=_f(100.0 * masque.mean()),
                BLE3_0_ecarte=("oui" if "BLE3-0" in pts else "non"),
                points=", ".join(pts)[:500]))
    ecrire_csv(OUT / "validite_m_criteres_croises.csv",
               ["coefficient", "critere", "n_estimations", "n_ecartes",
                "part_ecartee_pct", "BLE3_0_ecarte", "points"],
               croise, tri=["coefficient", "critere"])

    print("=== Balayage sur les deciles de la distribution observee ===")
    for coef in sorted(set(l["coefficient"] for l in lignes)):
        print(f"  -- {coef}")
        for l in lignes:
            if l["coefficient"] != coef:
                continue
            marque = "  <- repere du projet clos, NON retenu" if l["statut_du_seuil"].startswith("REPERE") else ""
            print(f"     seuil {l['seuil_demi_largeur_ic95']:<8} : "
                  f"{l['n_sortent']:>2} / {l['n_estimations']} sortent "
                  f"({l['part_sortante_pct']:>5.1f} %)  BLE3-0 sort : "
                  f"{l['BLE3_0_sort']}{marque}")

    print("\n=== Ce que chaque critere ecarterait, isolement ===")
    for l in croise:
        print(f"  {l['coefficient']:<14} {l['critere']:<52} "
              f"{l['n_ecartes']:>2}/{l['n_estimations']} "
              f"({l['part_ecartee_pct']:>5.1f} %)  BLE3-0 : {l['BLE3_0_ecarte']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
