"""
mesure_aveuglement.py — ÉTAPE 2, TÂCHE D.

MESURE SEULE. Aucun code applicatif n'est modifié, aucun seuil n'est retenu,
aucune conclusion n'est tirée sur le critère à préférer.

CE QUE L'ON COMPARE
-------------------
Le régime mesuré est celui de `tests/reference_cli/` — détecteur hors d'eau
ALLUMÉ au seuil absolu de 4 °C —, puisque c'est le comportement qu'un
correctif viendrait remplacer.

  CRITÈRE ABSOLU (celui de V4.5, qc.py:64-65)
      jour de juin à septembre, T_air renseignée, et
      ecart = T_eau_max − T_air  >  4 °C

  CRITÈRE RELATIF (celui qu'on évalue)
      même fenêtre, même grandeur, mais comparée à la médiane du MÊME POINT au
      MÊME MOIS :
          ecart_rel = ecart − mediane_{point, mois}(ecart)
      déclenchement si ecart_rel > seuil, le seuil étant un quantile de la
      distribution poolée de ecart_rel sur l'ensemble des points-jours de la
      fenêtre.

RÈGLES DE DÉCISION (posées avant tout chiffre)
----------------------------------------------
  · un JOUR est « perdu par le relatif » s'il est marqué par l'absolu et pas
    par le relatif ;
  · un POINT est « perdu par le relatif » si l'absolu le marque au moins un
    jour et le relatif aucun ;
  · au moins trois quantiles de déclenchement sont testés, et TOUS sont
    rapportés.

Le mécanisme attendu : un point à sonde chroniquement mal posée décale sa
propre médiane, son ecart_rel reste petit, et il devient invisible au critère
relatif. S'il ne s'observe pas, il faut le dire aussi nettement.

Sorties :
  out/etape2/aveuglement_par_point.csv
  out/etape2/aveuglement_par_quantile.csv
  out/etape2/aveuglement_medianes.csv
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f
from thermie_debits import io_data

OUT = RACINE / "out" / "etape2"

# Paramètres du critère absolu, tels que V4.5 les applique par défaut dans
# QCConfig (config.py:81-83). Ce sont ceux de tests/reference_cli/.
SEUIL_ABSOLU = 4.0
MOIS = (6, 7, 8, 9)

# Quantiles de déclenchement explorés. Volontairement larges : la mesure doit
# rapporter aussi les valeurs qui arrangent moins.
QUANTILES = [0.90, 0.95, 0.99, 0.995]


def construire_socle():
    """
    Table point-jour de la fenêtre d'examen, avec l'écart T_eau_max − T_air.

    Reproduit exactement l'assiette de qc.controle_qualite : jointure À GAUCHE
    de la journalière d'eau sur l'air (qc.py:23), donc AVANT toute exclusion.
    Les loaders sont ceux de ref/v4_5 (D3).
    """
    lignes = []
    for j in decouvrir():
        if not j["air"]:
            continue
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            d = daily.merge(air, on="date", how="left")
            d["date_dt"] = pd.to_datetime(d["date"])
            d["month"] = d["date_dt"].dt.month
            d["year"] = d["date_dt"].dt.year
            d = d[d["month"].isin(MOIS)].copy()
            if not len(d):
                continue
            d["jeu"] = j["jeu"]
            d["point"] = pt
            d["ecart"] = d["T_eau_max"] - d["T_air"]
            lignes.append(d[["jeu", "point", "date", "year", "month",
                             "T_eau_max", "T_air", "ecart"]])
            print(f"  · {j['jeu']}/{pt} : {len(d)} jours JJAS", flush=True)
    return pd.concat(lignes, ignore_index=True)


def marquer(socle: pd.DataFrame):
    """Ajoute le marquage absolu et l'écart relatif au couple (point, mois)."""
    d = socle.copy()
    # Absolu : la condition exacte de qc.py:65.
    d["abs_marque"] = (d["ecart"] > SEUIL_ABSOLU) & d["T_air"].notna()
    # Relatif : écart à la médiane du point ET du mois.
    ref = (d.groupby(["point", "month"])["ecart"].median()
           .rename("ecart_ref").reset_index())
    d = d.merge(ref, on=["point", "month"], how="left")
    d["ecart_rel"] = d["ecart"] - d["ecart_ref"]
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Construction du socle point-jour (fenetre JJAS)...")
    socle = construire_socle()
    d = marquer(socle)
    diagnosticable = d["T_air"].notna() & d["ecart"].notna()
    d = d[diagnosticable].copy()
    print(f"\n{len(d)} points-jours diagnosticables, "
          f"{d['point'].nunique()} points.")

    # ---- Seuils relatifs, quantiles de la distribution poolee -------------
    seuils = {q: float(d["ecart_rel"].quantile(q)) for q in QUANTILES}
    for q, s in seuils.items():
        d[f"rel_{q}"] = d["ecart_rel"] > s

    # ---- Par point --------------------------------------------------------
    par_point, par_quantile = [], []
    for q in QUANTILES:
        col = f"rel_{q}"
        perdus = []
        for (jeu, pt), sub in d.groupby(["jeu", "point"]):
            n_abs = int(sub["abs_marque"].sum())
            n_rel = int(sub[col].sum())
            n_deux = int((sub["abs_marque"] & sub[col]).sum())
            perdu_pt = bool(n_abs > 0 and n_rel == 0)
            if perdu_pt:
                perdus.append(pt)
            par_point.append(dict(
                quantile=q, seuil_relatif=_f(seuils[q]), jeu=jeu, point=pt,
                n_jours_jjas=int(len(sub)),
                mediane_ecart_du_point=_f(float(sub["ecart"].median())),
                jours_absolu=n_abs, jours_relatif=n_rel, jours_les_deux=n_deux,
                jours_perdus_par_le_relatif=n_abs - n_deux,
                jours_gagnes_par_le_relatif=n_rel - n_deux,
                point_perdu_par_le_relatif=perdu_pt))
        n_abs_pts = int(d.groupby("point")["abs_marque"].any().sum())
        par_quantile.append(dict(
            quantile=q, seuil_relatif=_f(seuils[q]),
            jours_marques_absolu=int(d["abs_marque"].sum()),
            jours_marques_relatif=int(d[col].sum()),
            jours_marques_les_deux=int((d["abs_marque"] & d[col]).sum()),
            jours_perdus_par_le_relatif=int((d["abs_marque"] & ~d[col]).sum()),
            jours_gagnes_par_le_relatif=int((~d["abs_marque"] & d[col]).sum()),
            points_marques_absolu=n_abs_pts,
            points_marques_relatif=int(d.groupby("point")[col].any().sum()),
            points_perdus_par_le_relatif=len(perdus),
            liste_points_perdus=", ".join(sorted(perdus)) or "aucun"))

    # ---- Médianes par point : le mécanisme d'aveuglement ------------------
    med = []
    for (jeu, pt), sub in d.groupby(["jeu", "point"]):
        n_abs = int(sub["abs_marque"].sum())
        med.append(dict(
            jeu=jeu, point=pt, n_jours_jjas=int(len(sub)),
            mediane_ecart=_f(float(sub["ecart"].median())),
            p90_ecart=_f(float(sub["ecart"].quantile(0.90))),
            max_ecart=_f(float(sub["ecart"].max())),
            part_jours_au_dessus_de_4C=_f(100.0 * n_abs / max(len(sub), 1)),
            jours_absolu=n_abs,
            mediane_deja_au_dessus_du_seuil_absolu=bool(
                float(sub["ecart"].median()) > SEUIL_ABSOLU)))

    ecrire_csv(OUT / "aveuglement_par_point.csv",
               ["quantile", "seuil_relatif", "jeu", "point", "n_jours_jjas",
                "mediane_ecart_du_point", "jours_absolu", "jours_relatif",
                "jours_les_deux", "jours_perdus_par_le_relatif",
                "jours_gagnes_par_le_relatif", "point_perdu_par_le_relatif"],
               par_point, tri=["quantile", "jeu", "point"])
    ecrire_csv(OUT / "aveuglement_par_quantile.csv",
               ["quantile", "seuil_relatif", "jours_marques_absolu",
                "jours_marques_relatif", "jours_marques_les_deux",
                "jours_perdus_par_le_relatif", "jours_gagnes_par_le_relatif",
                "points_marques_absolu", "points_marques_relatif",
                "points_perdus_par_le_relatif", "liste_points_perdus"],
               par_quantile, tri=["quantile"])
    ecrire_csv(OUT / "aveuglement_medianes.csv",
               ["jeu", "point", "n_jours_jjas", "mediane_ecart", "p90_ecart",
                "max_ecart", "part_jours_au_dessus_de_4C", "jours_absolu",
                "mediane_deja_au_dessus_du_seuil_absolu"],
               med, tri=["jeu", "point"])

    print("\n=== Synthese par quantile ===")
    for l in par_quantile:
        print(f"  q={l['quantile']:<6} seuil={l['seuil_relatif']:>7.3f} degC  "
              f"jours abs={l['jours_marques_absolu']:>5} rel={l['jours_marques_relatif']:>5} "
              f"deux={l['jours_marques_les_deux']:>5} perdus={l['jours_perdus_par_le_relatif']:>5}  "
              f"points abs={l['points_marques_absolu']:>2} rel={l['points_marques_relatif']:>2} "
              f"perdus={l['points_perdus_par_le_relatif']:>2} ({l['liste_points_perdus']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
