"""
mesure_marche2_marges.py — ÉTAPE 3, TÂCHE B, complément.

Deux corrections et un ajout au relevé de `mesure_marche2.py` :

1. `part_TN_manquante_pct` y était rapportée sur TOUTES les lignes du fichier
   d'air, y compris les décennies où AUCUNE température n'est renseignée. Elle
   mesurait donc le vide du fichier, pas celui de TN. La question utile est :
   parmi les jours où TM existe, combien manquent de TN ou de TX ? C'est ce
   qui est recalculé ici.

2. Symétriquement : combien de jours portent TN et TX SANS porter TM ? Ce sont
   des jours que la marche 2 rendrait diagnosticables et que la chaîne
   actuelle ne voit pas.

3. LA MARGE. C'est l'argument de fond du projet clos, et il se mesure. Sous
   exondation, le maximum de la sonde tend vers le maximum de l'air :

       E_max = T_eau_max − TX  ->  0
       E_moy = T_eau_max − TM  ->  TX − TM   (l'amplitude diurne de l'air)

   La marge d'un écart est la distance entre sa médiane en régime immergé et
   sa valeur limite sous exondation. On la rapporte en °C et en MAD*, la
   seconde étant la seule comparable entre les deux grandeurs.

Sortie : out/etape3/marche2_marges.csv
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f
from mesure_critere_b import PLANCHER_MAD, MIN_JOURS_GROUPE, FACTEUR_MAD
from mesure_aveuglement import MOIS
from mesure_marche2 import lire_air_complet
from thermie_debits import io_data

OUT = RACINE / "out" / "etape3"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dispo, marges = [], []

    for j in decouvrir():
        if not j["air"]:
            continue
        air = lire_air_complet(str(RACINE / j["air"]))
        a_tm = air["TM"].notna()
        a_tn = air["TN"].notna()
        a_tx = air["TX"].notna()
        tm_sans = int((a_tm & (~a_tn | ~a_tx)).sum())
        sans_tm = int((~a_tm & a_tn & a_tx).sum())
        trois = air.dropna(subset=["TM", "TN", "TX"])
        incoh = ((trois["TN"] > trois["TM"]) | (trois["TM"] > trois["TX"]))
        dispo.append(dict(
            jeu=j["jeu"], fichier=j["air"].split("/")[-1],
            jours_avec_TM=int(a_tm.sum()),
            jours_avec_TN=int(a_tn.sum()), jours_avec_TX=int(a_tx.sum()),
            jours_TM_sans_TN_ou_TX=tm_sans,
            part_TM_perdue_par_la_marche2_pct=_f(100.0 * tm_sans / max(int(a_tm.sum()), 1)),
            jours_TN_TX_sans_TM=sans_tm,
            gain_de_jours_par_la_marche2_pct=_f(100.0 * sans_tm / max(int(a_tm.sum()), 1)),
            triplets_complets=int(len(trois)),
            incoherences_TN_TM_TX=int(incoh.sum()),
            part_incoherente_pct=_f(100.0 * incoh.mean()),
            amplitude_air_mediane=_f(float((trois["TX"] - trois["TN"]).median())),
            TX_moins_TM_median=_f(float((trois["TX"] - trois["TM"]).median())),
            exerce_la_marche2=("oui" if a_tn.any() and a_tx.any() else
                               "NON — colonnes presentes mais vides")))

        # --- la marge, sur la fenetre JJAS des points du jeu ---
        blocs = []
        for point_rel in j["points"]:
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            d = daily.merge(air, on="date", how="left")
            d["month"] = pd.to_datetime(d["date"]).dt.month
            d = d[d["month"].isin(MOIS)]
            if len(d):
                d = d.assign(point=nom_point(point_rel))
                blocs.append(d[["point", "month", "T_eau_max", "TM", "TN", "TX"]])
        if not blocs:
            continue
        d = pd.concat(blocs, ignore_index=True).dropna(subset=["T_eau_max", "TM", "TX"])
        d["E_moy"] = d["T_eau_max"] - d["TM"]
        d["E_max"] = d["T_eau_max"] - d["TX"]
        d["limite_E_moy"] = d["TX"] - d["TM"]     # valeur de E_moy sous exondation
        d["limite_E_max"] = 0.0                   # valeur de E_max sous exondation

        for pt, sub in d.groupby("point"):
            ligne = dict(jeu=j["jeu"], point=pt, n_jours=int(len(sub)))
            for nom, col in (("E_moy", "E_moy"), ("E_max", "E_max")):
                med = float(sub[col].median())
                mad = float((sub[col] - med).abs().median()) * FACTEUR_MAD
                lim = float(sub[f"limite_{col}"].median())
                ligne[f"{nom}_mediane"] = _f(med)
                ligne[f"{nom}_mad"] = _f(mad)
                ligne[f"{nom}_limite_exondation"] = _f(lim)
                ligne[f"{nom}_marge_degC"] = _f(lim - med)
                ligne[f"{nom}_marge_en_MAD"] = _f((lim - med) / mad
                                                  if mad > PLANCHER_MAD else np.nan)
            ligne["marge_MAD_gagnee_par_le_maximum"] = _f(
                (ligne["E_max_marge_en_MAD"] or 0) - (ligne["E_moy_marge_en_MAD"] or 0))
            marges.append(ligne)
        print(f"  · {j['jeu']} : {len(set(d['point']))} point(s)", flush=True)

    ecrire_csv(OUT / "marche2_disponibilite.csv",
               ["jeu", "fichier", "jours_avec_TM", "jours_avec_TN",
                "jours_avec_TX", "jours_TM_sans_TN_ou_TX",
                "part_TM_perdue_par_la_marche2_pct", "jours_TN_TX_sans_TM",
                "gain_de_jours_par_la_marche2_pct", "triplets_complets",
                "incoherences_TN_TM_TX", "part_incoherente_pct",
                "amplitude_air_mediane", "TX_moins_TM_median",
                "exerce_la_marche2"], dispo, tri=["jeu"])
    ecrire_csv(OUT / "marche2_marges.csv",
               ["jeu", "point", "n_jours",
                "E_moy_mediane", "E_moy_mad", "E_moy_limite_exondation",
                "E_moy_marge_degC", "E_moy_marge_en_MAD",
                "E_max_mediane", "E_max_mad", "E_max_limite_exondation",
                "E_max_marge_degC", "E_max_marge_en_MAD",
                "marge_MAD_gagnee_par_le_maximum"], marges, tri=["jeu", "point"])

    print("\n=== B3 corrige — TN et TX parmi les jours ou TM existe ===")
    for l in dispo:
        print(f"  {l['jeu']:<18} TM={l['jours_avec_TM']:>6} | TM sans TN/TX : "
              f"{l['jours_TM_sans_TN_ou_TX']:>4} ({l['part_TM_perdue_par_la_marche2_pct']:.2f} %) "
              f"| TN/TX sans TM : {l['jours_TN_TX_sans_TM']:>3} "
              f"| incoherences : {l['incoherences_TN_TM_TX']} "
              f"({l['part_incoherente_pct']:.3f} %) | {l['exerce_la_marche2']}")

    t = pd.DataFrame(marges)
    print("\n=== La marge, en MAD* (distance de la mediane a la limite d'exondation) ===")
    print(f"  E_moy = T_eau_max - TM : mediane {t['E_moy_marge_en_MAD'].median():+.2f} MAD*, "
          f"etendue {t['E_moy_marge_en_MAD'].min():+.2f} a {t['E_moy_marge_en_MAD'].max():+.2f}")
    print(f"  E_max = T_eau_max - TX : mediane {t['E_max_marge_en_MAD'].median():+.2f} MAD*, "
          f"etendue {t['E_max_marge_en_MAD'].min():+.2f} a {t['E_max_marge_en_MAD'].max():+.2f}")
    g = t["marge_MAD_gagnee_par_le_maximum"]
    print(f"  gain du MAXIMUM sur la MOYENNE : mediane {g.median():+.2f} MAD*, "
          f"positif sur {int((g > 0).sum())} / {len(g)} points")
    return 0


if __name__ == "__main__":
    sys.exit(main())
