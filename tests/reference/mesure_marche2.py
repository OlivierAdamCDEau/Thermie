"""
mesure_marche2.py — ÉTAPE 3, TÂCHE B : ce que la marche 2 apporterait.

MESURE SEULE. **Aucun code applicatif n'est modifié.** `io_data.charger_air_brut`
ne lit ni TN ni TX (`io_data.py:432`, usecols) ; le harnais lit donc les
fichiers d'air lui-même, en parallèle, pour mesurer ce que la marche 2
apporterait si ces colonnes remontaient. Rien de ce qui est calculé ici
n'entre dans la référence de non-régression.

CE QUI EST COMPARÉ
------------------
  écart à la MOYENNE d'air  E_moy = T_eau_max − TM   (ce que V4.5 sait faire)
  écart au MAXIMUM d'air    E_max = T_eau_max − TX   (ce que la marche 2 ouvre)

Les deux sont relativisés de la même façon, avec le meilleur critère de la
tâche A — dispersion propre, `(E − médiane_{point,mois}) / MAD*_{point,mois}`,
mêmes garde-fous (plancher de MAD, taille minimale de groupe).

POURQUOI E_max PLUTÔT QUE E_moy, en une ligne de physique
----------------------------------------------------------
Sous exondation, le maximum de la sonde tend vers le maximum de l'air : E_max
tend vers zéro par en dessous, alors qu'il est franchement négatif en régime
immergé. E_moy, lui, compare un maximum d'eau à une moyenne d'air : la marge
y est mélangée à l'amplitude diurne de l'air, qui n'a rien à voir avec la
sonde. C'est l'argument du projet clos ; il est ici MESURÉ, non repris.

Sorties :
  out/etape3/marche2_disponibilite.csv   B3 — TN/TX sont-ils exploitables ?
  out/etape3/marche2_par_quantile.csv    B1/B2 — les deux ecarts, cote a cote
  out/etape3/marche2_par_point.csv       le detail
  out/etape3/marche2_croisement.csv      B2 — qui marque quoi, ensemble et seul
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f
from mesure_critere_b import (PLANCHER_MAD, MIN_JOURS_GROUPE, FACTEUR_MAD,
                              K_VALEURS)
from mesure_aveuglement import SEUIL_ABSOLU, MOIS
from thermie_debits import io_data
from thermie_debits.sniff import lire_brut

OUT = RACINE / "out" / "etape3"


# ============================================================
# B3 — TN et TX sont-ils exploitables ?
# ============================================================
def lire_air_complet(chemin: str) -> pd.DataFrame:
    """
    Lit un fichier d'air avec TM, TN et TX.

    Reproduit le chemin de `io_data.charger_air_brut` — même détection de
    format, même parseur de dates (`io_data._parse_dates_air`), même
    conversion décimale — mais SANS le `usecols` qui supprime TN et TX.
    C'est la seule chose que la marche 2 changerait à la lecture.
    """
    fmt = io_data._colonnes_meteo_france(chemin)
    if fmt is not None:
        usecols = ["NUM_POSTE", "NOM_USUEL", "AAAAMMJJ", "TM", "TN", "TX", "RR"]
        morceaux = []
        for chunk in pd.read_csv(chemin, sep=fmt["sep"], encoding=fmt["enc"],
                                 usecols=lambda c: c in usecols,
                                 dtype={"NUM_POSTE": str, "AAAAMMJJ": str},
                                 chunksize=100_000):
            morceaux.append(chunk[[c for c in ("AAAAMMJJ", "TM", "TN", "TX")
                                   if c in chunk.columns]])
        df = pd.concat(morceaux, ignore_index=True)
        col_date = "AAAAMMJJ"
    else:
        df, _ = lire_brut(chemin)
        col_date = next((c for c in df.columns if str(c).upper() == "AAAAMMJJ"), None)
    out = pd.DataFrame()
    out["date"] = io_data._parse_dates_air(df[col_date]).dt.date
    for marque in ("TM", "TN", "TX"):
        col = next((c for c in df.columns if str(c).upper() == marque), None)
        out[marque] = (pd.to_numeric(df[col].astype(str).str.replace(",", "."),
                                     errors="coerce")
                       if col is not None else np.nan)
    return out.dropna(subset=["date"])


def disponibilite():
    """B3 — taux de manquants, couverture comparée à TM, cohérence TN<=TM<=TX."""
    lignes, airs = [], {}
    for j in decouvrir():
        if not j["air"]:
            continue
        chemin = str(RACINE / j["air"])
        a = lire_air_complet(chemin)
        airs[j["jeu"]] = a
        n = len(a)
        d = pd.to_datetime(a["date"])
        def cover(c):
            s = a[c].notna()
            return (int(s.sum()),
                    (str(d[s].min().date()) if s.any() else ""),
                    (str(d[s].max().date()) if s.any() else ""))
        n_tm, tm0, tm1 = cover("TM")
        n_tn, tn0, tn1 = cover("TN")
        n_tx, tx0, tx1 = cover("TX")
        trois = a.dropna(subset=["TM", "TN", "TX"])
        incoh = int(((trois["TN"] > trois["TM"]) | (trois["TM"] > trois["TX"])).sum())
        # Jours ou TM existe mais pas TN ou TX : ce que la marche 2 perdrait.
        manque = int((a["TM"].notna() & (a["TN"].isna() | a["TX"].isna())).sum())
        lignes.append(dict(
            jeu=j["jeu"], fichier=j["air"].split("/")[-1], n_lignes=n,
            TM_renseignee=n_tm, TN_renseignee=n_tn, TX_renseignee=n_tx,
            part_TN_manquante_pct=_f(100.0 * (n - n_tn) / max(n, 1)),
            part_TX_manquante_pct=_f(100.0 * (n - n_tx) / max(n, 1)),
            periode_TM=f"{tm0} -> {tm1}", periode_TN=f"{tn0} -> {tn1}",
            periode_TX=f"{tx0} -> {tx1}",
            jours_TM_sans_TN_ou_TX=manque,
            part_TM_perdue_par_la_marche2_pct=_f(100.0 * manque / max(n_tm, 1)),
            n_triplets_complets=int(len(trois)),
            incoherences_TN_TM_TX=incoh,
            part_incoherente_pct=_f(100.0 * incoh / max(len(trois), 1)),
            exerce_la_marche2=("oui" if n_tn > 0 and n_tx > 0 else
                               "NON — colonnes presentes mais vides")))
    return lignes, airs


# ============================================================
# B1 / B2 — les deux écarts, relativisés de la même façon
# ============================================================
def socle_deux_ecarts(airs):
    """Table point-jour avec E_moy = T_eau_max − TM et E_max = T_eau_max − TX."""
    blocs = []
    for j in decouvrir():
        if not j["air"] or j["jeu"] not in airs:
            continue
        air = airs[j["jeu"]]
        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            d = daily.merge(air, on="date", how="left")
            d["date_dt"] = pd.to_datetime(d["date"])
            d["month"] = d["date_dt"].dt.month
            d = d[d["month"].isin(MOIS)].copy()
            if not len(d):
                continue
            d["jeu"] = j["jeu"]
            d["point"] = pt
            d["E_moy"] = d["T_eau_max"] - d["TM"]
            d["E_max"] = d["T_eau_max"] - d["TX"]
            blocs.append(d[["jeu", "point", "date", "month", "T_eau_max",
                            "TM", "TN", "TX", "E_moy", "E_max"]])
            print(f"  · {j['jeu']}/{pt} : {len(d)} jours JJAS", flush=True)
    return pd.concat(blocs, ignore_index=True)


def relativiser(d: pd.DataFrame, col: str):
    """Ajoute <col>_rel = (E − médiane) / MAD*, avec les garde-fous de la tâche A."""
    g = d.groupby(["point", "month"])[col]
    ref = g.transform("median")
    n = g.transform("size")
    mad = (d.assign(_a=(d[col] - ref).abs())
            .groupby(["point", "month"])["_a"].transform("median") * FACTEUR_MAD)
    ok = (mad > PLANCHER_MAD) & (n >= MIN_JOURS_GROUPE) & d[col].notna()
    d[f"{col}_ref"] = ref
    d[f"{col}_mad"] = mad
    d[f"{col}_diag"] = ok
    d[f"{col}_rel"] = np.where(ok, (d[col] - ref) / mad.replace(0, np.nan), np.nan)
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("=== B3 — TN et TX sont-ils exploitables ? ===", flush=True)
    dispo, airs = disponibilite()
    ecrire_csv(OUT / "marche2_disponibilite.csv",
               ["jeu", "fichier", "n_lignes", "TM_renseignee", "TN_renseignee",
                "TX_renseignee", "part_TN_manquante_pct", "part_TX_manquante_pct",
                "periode_TM", "periode_TN", "periode_TX",
                "jours_TM_sans_TN_ou_TX", "part_TM_perdue_par_la_marche2_pct",
                "n_triplets_complets", "incoherences_TN_TM_TX",
                "part_incoherente_pct", "exerce_la_marche2"],
               dispo, tri=["jeu"])
    for l in dispo:
        print(f"  {l['jeu']:<18} TM={l['TM_renseignee']:>6} TN={l['TN_renseignee']:>6} "
              f"TX={l['TX_renseignee']:>6} | TM sans TN/TX : {l['jours_TM_sans_TN_ou_TX']:>5} "
              f"({l['part_TM_perdue_par_la_marche2_pct']:.1f} %) | "
              f"incoherences : {l['incoherences_TN_TM_TX']} | {l['exerce_la_marche2']}")

    print("\n=== B1/B2 — construction du socle ===", flush=True)
    d = socle_deux_ecarts(airs)
    d = relativiser(d, "E_moy")
    d = relativiser(d, "E_max")
    d["abs_marque"] = (d["E_moy"] > SEUIL_ABSOLU) & d["TM"].notna()

    # Sous-ensemble ou LES DEUX criteres sont diagnosticables : seul terrain
    # ou la comparaison a un sens.
    commun = d[d["E_moy_diag"] & d["E_max_diag"]].copy()
    print(f"\n{len(d)} points-jours ; {len(commun)} diagnosticables par les DEUX "
          f"({100*len(commun)/max(len(d),1):.1f} %).")

    lignes, croise, par_point = [], [], []
    for k in K_VALEURS:
        commun[f"moy_{k}"] = commun["E_moy_rel"] > k
        commun[f"max_{k}"] = commun["E_max_rel"] > k
        a, b = commun[f"moy_{k}"], commun[f"max_{k}"]
        for libelle, col in ((f"ecart a la MOYENNE (T_eau_max - TM), k={k}", f"moy_{k}"),
                             (f"ecart au MAXIMUM (T_eau_max - TX), k={k}", f"max_{k}")):
            perdus = sorted(p for p, s in commun.groupby("point")
                            if bool(s["abs_marque"].any()) and not bool(s[col].any()))
            lignes.append(dict(
                k=k, critere=libelle,
                jours_marques=int(commun[col].sum()),
                points_marques=int(commun.groupby("point")[col].any().sum()),
                jours_marques_absolu_v45=int(commun["abs_marque"].sum()),
                jours_communs_avec_absolu=int((commun["abs_marque"] & commun[col]).sum()),
                points_perdus_vs_absolu=len(perdus),
                liste_points_perdus=", ".join(perdus) or "aucun"))
        croise.append(dict(
            k=k, jours_diagnosticables=int(len(commun)),
            marques_par_les_deux=int((a & b).sum()),
            marques_par_la_MOYENNE_seule=int((a & ~b).sum()),
            marques_par_le_MAXIMUM_seul=int((~a & b).sum()),
            marques_par_aucun=int((~a & ~b).sum()),
            points_marques_moyenne=int(commun.groupby("point")[f"moy_{k}"].any().sum()),
            points_marques_maximum=int(commun.groupby("point")[f"max_{k}"].any().sum()),
            accord_pct=_f(100.0 * ((a & b) | (~a & ~b)).mean()),
            jaccard_pct=_f(100.0 * (a & b).sum() / max((a | b).sum(), 1))))
        for pt, sub in commun.groupby("point"):
            par_point.append(dict(
                k=k, point=pt, n_jours=int(len(sub)),
                mediane_E_moy=_f(float(sub["E_moy"].median())),
                mediane_E_max=_f(float(sub["E_max"].median())),
                mad_E_moy=_f(float(sub["E_moy_mad"].median())),
                mad_E_max=_f(float(sub["E_max_mad"].median())),
                jours_moyenne=int(sub[f"moy_{k}"].sum()),
                jours_maximum=int(sub[f"max_{k}"].sum()),
                jours_les_deux=int((sub[f"moy_{k}"] & sub[f"max_{k}"]).sum()),
                jours_maximum_seul=int((~sub[f"moy_{k}"] & sub[f"max_{k}"]).sum())))

    ecrire_csv(OUT / "marche2_par_quantile.csv",
               ["k", "critere", "jours_marques", "points_marques",
                "jours_marques_absolu_v45", "jours_communs_avec_absolu",
                "points_perdus_vs_absolu", "liste_points_perdus"],
               lignes, tri=["k", "critere"])
    ecrire_csv(OUT / "marche2_croisement.csv",
               ["k", "jours_diagnosticables", "marques_par_les_deux",
                "marques_par_la_MOYENNE_seule", "marques_par_le_MAXIMUM_seul",
                "marques_par_aucun", "points_marques_moyenne",
                "points_marques_maximum", "accord_pct", "jaccard_pct"],
               croise, tri=["k"])
    ecrire_csv(OUT / "marche2_par_point.csv",
               ["k", "point", "n_jours", "mediane_E_moy", "mediane_E_max",
                "mad_E_moy", "mad_E_max", "jours_moyenne", "jours_maximum",
                "jours_les_deux", "jours_maximum_seul"],
               par_point, tri=["k", "point"])

    print("\n=== B2 — croisement des deux ecarts ===")
    for l in croise:
        print(f"  k={l['k']:<4} les deux={l['marques_par_les_deux']:>5} "
              f"MOYENNE seule={l['marques_par_la_MOYENNE_seule']:>5} "
              f"MAXIMUM seul={l['marques_par_le_MAXIMUM_seul']:>5} "
              f"| pts moy={l['points_marques_moyenne']:>2} "
              f"max={l['points_marques_maximum']:>2} "
              f"| Jaccard {l['jaccard_pct']:.1f} %")

    print("\n=== marges : ou chaque ecart se situe ===")
    print(f"  mediane de E_moy sur le corpus : {d['E_moy'].median():+.2f} degC "
          f"(min {d['E_moy'].min():+.2f}, max {d['E_moy'].max():+.2f})")
    print(f"  mediane de E_max sur le corpus : {d['E_max'].median():+.2f} degC "
          f"(min {d['E_max'].min():+.2f}, max {d['E_max'].max():+.2f})")
    print(f"  MAD* median de E_moy : {d['E_moy_mad'].median():.3f} degC")
    print(f"  MAD* median de E_max : {d['E_max_mad'].median():.3f} degC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
