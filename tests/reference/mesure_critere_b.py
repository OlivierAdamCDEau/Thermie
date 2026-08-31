"""
mesure_critere_b.py — ÉTAPE 3, TÂCHE A.

MESURE SEULE. Aucun code applicatif n'est modifié, aucun seuil n'est retenu.

CE QUE L'ÉTAPE 2 N'AVAIT PAS MESURÉ
-----------------------------------
Le critère mesuré à l'étape 2 centre par point-mois puis applique UN SEUIL
POOLÉ unique. Il est donc relatif EN POSITION et absolu EN DISPERSION : un
point dont les écarts varient peu ne franchit jamais ce nombre, quelle que
soit l'anomalie de sa journée au regard de sa propre habitude. C'est une
explication mécanique du résultat observé, et elle appelle la variante
pleinement relative.

  CRITÈRE A — poolé (étape 2)
      ecart_rel_A = ecart − médiane_{point,mois}(ecart)
      déclenchement si ecart_rel_A > q, q = quantile poolé de ecart_rel_A

  CRITÈRE B — dispersion propre (étape 3)
      ecart_rel_B = (ecart − médiane_{point,mois}) / MAD*_{point,mois}
      déclenchement si ecart_rel_B > k

  où MAD* = 1,4826 × médiane(|ecart − médiane|), c'est-à-dire l'estimateur
  robuste de l'écart-type. Le facteur 1,4826 est retenu pour que k se lise
  directement comme un NOMBRE D'ÉCARTS-TYPES : k = 3 est alors le seuil
  d'aberration usuel. Sans ce facteur, k ne serait comparable à rien.

CAS DU MAD NUL OU QUASI NUL — traité explicitement
--------------------------------------------------
Un couple (point, mois) dont le MAD est nul ferait exploser le rapport : la
moindre variation deviendrait une aberration. Deux garde-fous, tous deux
déclarés :

  1. MAD* <= PLANCHER_MAD : le couple est déclaré NON DIAGNOSTICABLE par B.
     Le plancher vaut 0,05 °C. Ce n'est pas un nombre inventé ni importé du
     projet clos (D15) : c'est le seuil que V4.5 utilise déjà pour dire qu'un
     signal est immobile — `plateau_ecart_type_min` (config.py:89).
  2. moins de MIN_JOURS_GROUPE jours dans le couple (point, mois) : médiane et
     MAD n'y ont pas de sens. Le couple est déclaré NON DIAGNOSTICABLE.

Les points-jours écartés à ce titre ne sont ni marqués ni déclarés sains ; ils
sont comptés et restitués.

RÈGLE DE DÉCISION — ÉCRITE AVANT DE REGARDER LES CHIFFRES
---------------------------------------------------------
Question : le mécanisme d'aveuglement existe-t-il, c'est-à-dire un point à
sonde chroniquement mal posée décale-t-il sa propre médiane au point de
devenir invisible au critère relatif ?

La durée de chronique est un facteur confondant : un point court a peu de
chances de produire une excursion extrême, indépendamment de sa médiane. Les
deux facteurs sont donc stratifiés en 2×2 — durée courte/longue et médiane
basse/haute, coupées à leur médiane respective — et l'on regarde le taux de
points perdus dans chaque cellule.

  CONCLUSION « LE MÉCANISME EXISTE » si, À DURÉE CONTRÔLÉE, le taux de perte
  des points à médiane haute dépasse celui des points à médiane basse d'au
  moins 20 points de pourcentage, dans le même sens, pour au moins deux des
  valeurs de k testées.

  CONCLUSION « LE MÉCANISME N'EXISTE PAS » si cet écart est inférieur à
  10 points de pourcentage, ou de signe contraire, pour la majorité des
  valeurs de k testées.

  CONCLUSION « LE CORPUS NE PERMET PAS DE TRANCHER » si l'une au moins de ces
  conditions est remplie : une cellule de la stratification compte moins de
  3 points ; le signe de l'écart change avec k sans régularité ; ou l'étendue
  des médianes propres parmi les points marqués est inférieure à 2 °C, auquel
  cas le corpus ne porte pas le contraste que le test demande.

Les trois issues sont acceptables. Ce qui ne l'est pas serait de choisir le
critère après avoir vu le résultat : il est donc écrit ici, dans le code qui
produit les chiffres.

Sorties :
  out/etape3/critere_b_par_quantile.csv    A et B cote a cote
  out/etape3/critere_b_par_point.csv       le detail, par point et par seuil
  out/etape3/critere_b_stratification.csv  duree x mediane (A3)
  out/etape3/critere_b_chateau_voue.csv    le cas nomme (A4)
  out/etape3/critere_b_diagnosticabilite.csv  ce que les garde-fous ecartent
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _commun import RACINE, ecrire_csv, _f
from mesure_aveuglement import construire_socle, SEUIL_ABSOLU, MOIS, QUANTILES

OUT = RACINE / "out" / "etape3"

# Garde-fous du critère B, déclarés ci-dessus.
PLANCHER_MAD = 0.05          # °C — config.py:89, plateau_ecart_type_min
MIN_JOURS_GROUPE = 10        # jours dans un couple (point, mois)
FACTEUR_MAD = 1.4826         # MAD -> ecart-type robuste

# Seuils de k explorés. Cinq valeurs, de l'aberration franche au tres severe.
K_VALEURS = [2.0, 3.0, 4.0, 5.0, 6.0]

POINT_NOMME = "Le ruisseau de la Flotte à Château-Voue"


def preparer(d: pd.DataFrame) -> pd.DataFrame:
    """Ajoute le marquage absolu, ecart_rel_A et ecart_rel_B."""
    d = d[d["T_air"].notna() & d["ecart"].notna()].copy()
    d["abs_marque"] = (d["ecart"] > SEUIL_ABSOLU) & d["T_air"].notna()

    g = d.groupby(["point", "month"])["ecart"]
    d["ecart_ref"] = g.transform("median")
    d["n_groupe"] = g.transform("size")
    d["ecart_centre"] = d["ecart"] - d["ecart_ref"]
    # MAD robuste du couple (point, mois).
    d["mad"] = (d.assign(_a=(d["ecart"] - d["ecart_ref"]).abs())
                 .groupby(["point", "month"])["_a"].transform("median")
                * FACTEUR_MAD)

    d["ecart_rel_A"] = d["ecart_centre"]
    d["diagnosticable_B"] = (d["mad"] > PLANCHER_MAD) & (d["n_groupe"] >= MIN_JOURS_GROUPE)
    d["ecart_rel_B"] = np.where(d["diagnosticable_B"],
                                d["ecart_centre"] / d["mad"].replace(0, np.nan),
                                np.nan)
    return d


def table_criteres(d: pd.DataFrame, colonnes_marque, sous_ensemble: str):
    """Table jours/points marques, perdus, gagnes — pour chaque critere."""
    lignes = []
    for libelle, col in colonnes_marque:
        n_abs = int(d["abs_marque"].sum())
        n_rel = int(d[col].sum())
        deux = int((d["abs_marque"] & d[col]).sum())
        pts_abs = int(d.groupby("point")["abs_marque"].any().sum())
        pts_rel = int(d.groupby("point")[col].any().sum())
        perdus = sorted(p for p, s in d.groupby("point")
                        if bool(s["abs_marque"].any()) and not bool(s[col].any()))
        lignes.append(dict(
            sous_ensemble=sous_ensemble, critere=libelle,
            jours_marques_absolu=n_abs, jours_marques_relatif=n_rel,
            jours_marques_les_deux=deux,
            jours_perdus_par_le_relatif=n_abs - deux,
            jours_gagnes_par_le_relatif=n_rel - deux,
            points_marques_absolu=pts_abs, points_marques_relatif=pts_rel,
            points_perdus_par_le_relatif=len(perdus),
            liste_points_perdus=", ".join(perdus) or "aucun"))
    return lignes


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Construction du socle point-jour (fenetre JJAS)...", flush=True)
    d = preparer(construire_socle())
    print(f"\n{len(d)} points-jours, {d['point'].nunique()} points.")

    # ---- Diagnosticabilite : ce que les garde-fous de B ecartent ---------
    diag = []
    for (pt, mo), sub in d.groupby(["point", "month"]):
        diag.append(dict(
            point=pt, mois=int(mo), n_jours=int(len(sub)),
            mediane_ecart=_f(float(sub["ecart"].median())),
            mad_robuste=_f(float(sub["mad"].iloc[0])),
            diagnosticable_par_B=bool(sub["diagnosticable_B"].iloc[0]),
            motif_si_non=("MAD* <= 0.05 degC (dispersion nulle ou quasi nulle)"
                          if sub["mad"].iloc[0] <= PLANCHER_MAD else
                          (f"moins de {MIN_JOURS_GROUPE} jours dans le couple "
                           f"(point, mois)" if len(sub) < MIN_JOURS_GROUPE
                           else ""))))
    ecrire_csv(OUT / "critere_b_diagnosticabilite.csv",
               ["point", "mois", "n_jours", "mediane_ecart", "mad_robuste",
                "diagnosticable_par_B", "motif_si_non"], diag,
               tri=["point", "mois"])
    n_non = sum(1 for x in diag if not x["diagnosticable_par_B"])
    n_jours_non = int((~d["diagnosticable_B"]).sum())
    print(f"Garde-fous de B : {n_non} couples (point, mois) sur {len(diag)} "
          f"non diagnosticables, soit {n_jours_non} points-jours "
          f"({100*n_jours_non/len(d):.1f} %).")

    # ---- Marquage, pour chaque seuil ------------------------------------
    for q in QUANTILES:
        seuil = float(d["ecart_rel_A"].quantile(q))
        d[f"A_{q}"] = d["ecart_rel_A"] > seuil
    for k in K_VALEURS:
        d[f"B_{k}"] = (d["ecart_rel_B"] > k).fillna(False)

    cols_A = [(f"A poole, q={q} (seuil {d['ecart_rel_A'].quantile(q):.3f} degC)",
               f"A_{q}") for q in QUANTILES]
    cols_B = [(f"B dispersion propre, k={k} MAD*", f"B_{k}") for k in K_VALEURS]

    # Sous-ensemble commun : les points-jours que B sait diagnostiquer.
    commun = d[d["diagnosticable_B"]].copy()
    lignes = (table_criteres(d, cols_A, "tous les points-jours")
              + table_criteres(d, cols_B, "tous les points-jours")
              + table_criteres(commun, cols_A, "diagnosticables par B")
              + table_criteres(commun, cols_B, "diagnosticables par B"))
    ecrire_csv(OUT / "critere_b_par_quantile.csv",
               ["sous_ensemble", "critere", "jours_marques_absolu",
                "jours_marques_relatif", "jours_marques_les_deux",
                "jours_perdus_par_le_relatif", "jours_gagnes_par_le_relatif",
                "points_marques_absolu", "points_marques_relatif",
                "points_perdus_par_le_relatif", "liste_points_perdus"],
               lignes, tri=["sous_ensemble", "critere"])

    # ---- Detail par point ------------------------------------------------
    par_point = []
    for libelle, col in cols_A + cols_B:
        for pt, sub in d.groupby("point"):
            n_abs = int(sub["abs_marque"].sum())
            n_rel = int(sub[col].sum())
            deux = int((sub["abs_marque"] & sub[col]).sum())
            par_point.append(dict(
                critere=libelle, point=pt, n_jours_jjas=int(len(sub)),
                mediane_ecart_du_point=_f(float(sub["ecart"].median())),
                mad_median_du_point=_f(float(sub["mad"].median())),
                jours_absolu=n_abs, jours_relatif=n_rel, jours_les_deux=deux,
                jours_perdus_par_le_relatif=n_abs - deux,
                jours_gagnes_par_le_relatif=n_rel - deux,
                point_perdu_par_le_relatif=bool(n_abs > 0 and n_rel == 0)))
    ecrire_csv(OUT / "critere_b_par_point.csv",
               ["critere", "point", "n_jours_jjas", "mediane_ecart_du_point",
                "mad_median_du_point", "jours_absolu", "jours_relatif",
                "jours_les_deux", "jours_perdus_par_le_relatif",
                "jours_gagnes_par_le_relatif", "point_perdu_par_le_relatif"],
               par_point, tri=["critere", "point"])

    # ---- A3 : stratification duree x mediane -----------------------------
    prof = d.groupby("point").agg(
        n_jours=("ecart", "size"),
        mediane=("ecart", "median"),
        jours_absolu=("abs_marque", "sum")).reset_index()
    prof["jours_absolu"] = prof["jours_absolu"].astype(int)
    marques = prof[prof["jours_absolu"] > 0].copy()
    coupe_duree = float(marques["n_jours"].median())
    coupe_med = float(marques["mediane"].median())
    marques["strate_duree"] = np.where(marques["n_jours"] >= coupe_duree,
                                       "longue", "courte")
    marques["strate_mediane"] = np.where(marques["mediane"] >= coupe_med,
                                         "haute", "basse")

    strat = []
    for libelle, col in cols_A + cols_B:
        perdus = {p: bool(s["abs_marque"].any() and not s[col].any())
                  for p, s in d.groupby("point")}
        marques["_perdu"] = marques["point"].map(perdus)
        for sd in ("courte", "longue"):
            for sm in ("basse", "haute"):
                c = marques[(marques.strate_duree == sd)
                            & (marques.strate_mediane == sm)]
                strat.append(dict(
                    critere=libelle, strate_duree=sd, strate_mediane=sm,
                    n_points=int(len(c)),
                    n_perdus=int(c["_perdu"].sum()) if len(c) else 0,
                    taux_de_perte_pct=(_f(100.0 * c["_perdu"].mean())
                                       if len(c) else None),
                    duree_mediane=_f(float(c["n_jours"].median())) if len(c) else None,
                    mediane_mediane=_f(float(c["mediane"].median())) if len(c) else None,
                    points=", ".join(sorted(c["point"])) if len(c) else ""))
    ecrire_csv(OUT / "critere_b_stratification.csv",
               ["critere", "strate_duree", "strate_mediane", "n_points",
                "n_perdus", "taux_de_perte_pct", "duree_mediane",
                "mediane_mediane", "points"], strat,
               tri=["critere", "strate_duree", "strate_mediane"])

    # ---- A4 : le cas nomme ----------------------------------------------
    cv = []
    sub = d[d["point"] == POINT_NOMME]
    for libelle, col in cols_A + cols_B:
        n_abs = int(sub["abs_marque"].sum())
        n_rel = int(sub[col].sum())
        cv.append(dict(
            point=POINT_NOMME, critere=libelle,
            n_jours_jjas=int(len(sub)),
            mediane_ecart=_f(float(sub["ecart"].median())),
            mad_median=_f(float(sub["mad"].median())),
            part_jours_au_dessus_de_4C=_f(100.0 * n_abs / max(len(sub), 1)),
            jours_absolu=n_abs, jours_relatif=n_rel,
            jours_les_deux=int((sub["abs_marque"] & sub[col]).sum()),
            perdu=bool(n_abs > 0 and n_rel == 0),
            ecart_rel_max=_f(float(sub["ecart_rel_A"].max())),
            ecart_rel_B_max=_f(float(sub["ecart_rel_B"].max()))))
    ecrire_csv(OUT / "critere_b_chateau_voue.csv",
               ["point", "critere", "n_jours_jjas", "mediane_ecart",
                "mad_median", "part_jours_au_dessus_de_4C", "jours_absolu",
                "jours_relatif", "jours_les_deux", "perdu", "ecart_rel_max",
                "ecart_rel_B_max"], cv, tri=["critere"])

    # ---- Restitution console --------------------------------------------
    print("\n=== A et B cote a cote, sur TOUS les points-jours ===")
    for l in lignes:
        if l["sous_ensemble"] != "tous les points-jours":
            continue
        print(f"  {l['critere']:<48} jours abs={l['jours_marques_absolu']:>5} "
              f"rel={l['jours_marques_relatif']:>5} perdus={l['jours_perdus_par_le_relatif']:>5} "
              f"gagnes={l['jours_gagnes_par_le_relatif']:>5} | "
              f"pts perdus={l['points_perdus_par_le_relatif']:>2} "
              f"({l['liste_points_perdus'][:60]})")

    print(f"\n=== Stratification (coupes : duree {coupe_duree:.0f} j, "
          f"mediane {coupe_med:+.2f} degC) ===")
    print(f"  etendue des medianes parmi les points marques : "
          f"{marques['mediane'].min():+.2f} a {marques['mediane'].max():+.2f} degC "
          f"(= {marques['mediane'].max() - marques['mediane'].min():.2f} degC)")
    for libelle, col in cols_A + cols_B:
        c = [s for s in strat if s["critere"] == libelle]
        tot = sum(s["n_perdus"] for s in c)
        if tot == 0:
            continue
        d_ct = {(s["strate_duree"], s["strate_mediane"]): s for s in c}
        for sd in ("courte", "longue"):
            b, h = d_ct[(sd, "basse")], d_ct[(sd, "haute")]
            if b["taux_de_perte_pct"] is None or h["taux_de_perte_pct"] is None:
                continue
            print(f"  {libelle[:40]:<40} duree {sd:<7} : "
                  f"mediane basse {b['taux_de_perte_pct']:>5.1f} % (n={b['n_points']}) "
                  f"| haute {h['taux_de_perte_pct']:>5.1f} % (n={h['n_points']}) "
                  f"| ecart {h['taux_de_perte_pct'] - b['taux_de_perte_pct']:+6.1f} pts")

    print(f"\n=== {POINT_NOMME} ===")
    for l in cv:
        print(f"  {l['critere']:<48} abs={l['jours_absolu']:>3} "
              f"rel={l['jours_relatif']:>3} perdu={'OUI' if l['perdu'] else 'non'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
