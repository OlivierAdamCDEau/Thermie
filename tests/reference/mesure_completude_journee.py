"""
mesure_completude_journee.py — ETAPE 15, POSE 2 : de quoi le correctif 12
aurait besoin.

LE DEFAUT
----------
`io_data.marquer_lecture` produit, pour chaque journee :

    n_mesures=("T_eau", "size")            io_data.py

et ce nombre n'est relu NULLE PART dans `app/` — recherche exhaustive, une
seule occurrence. Une journee d'UNE mesure pese donc autant qu'une journee de
vingt-quatre dans `T_eau_moy`, donc dans `Tmh`, donc dans `m`, donc dans
`T_norm`.

Une asymetrie le rend visible : l'amplitude nycthemerale, elle, A un critere —
`out.loc[out["n"] < 3, "ampl"] = np.nan` dans `indicateurs.py`. Le meme
projet exige trois mesures pour publier une amplitude et n'en exige aucune
pour publier une moyenne.

LA REGLE DE DECISION, ECRITE AVANT LES CHIFFRES (methode de l'etape 3)
-----------------------------------------------------------------------
La question que la specification devra trancher est : FAUT-IL un critere, et
si oui de quelle FORME ? Les trois issues sont ecrites ici, dans le code qui
produit les chiffres, pour qu'aucune ne se choisisse apres coup.

  ISSUE A — un critere est necessaire et se derive.
    Si une part NON NEGLIGEABLE des journees repose sur tres peu de mesures
    (seuil : plus de 1 % des journees du corpus a moins du QUART de l'effectif
    attendu du point), ET si ces journees se distinguent des autres sur un
    temoin INDEPENDANT du critere lui-meme — leur ecart a la moyenne des
    journees voisines.

  ISSUE B — un critere est necessaire mais ne se derive pas du corpus.
    Si la part est notable mais que les journees maigres ne se distinguent PAS
    du reste sur le temoin independant. Le critere serait alors une precaution
    de robustesse, et son seuil une convention a arbitrer, non une mesure.

  ISSUE C — le corpus ne justifie pas de critere.
    Si moins de 0,1 % des journees du corpus sont concernees, ou si aucun point
    n'a de pas de mesure infra-journalier (auquel cas `n_mesures` vaut 1
    partout par construction et le critere n'a pas d'objet).

  PRECISION AJOUTEE D'AVANCE, comme a l'etape 3 : un point dont TOUTES les
  journees ont le meme effectif ne porte aucun contraste et ne compte pas dans
  le verdict ; il est rapporte a part.

LE TEMOIN INDEPENDANT
----------------------
Comparer les journees maigres aux autres sur `T_eau_moy` seule serait
circulaire : c'est la grandeur que le critere protege. Le temoin retenu est
l'ECART DE LA JOURNEE A LA MOYENNE DE SES VOISINES (les journees a J-1 et J+1
qui, elles, sont completes). Une journee d'une seule mesure prise a 14 h doit
s'en ecarter davantage qu'une journee complete, si le defaut a un effet.

SORTIES
  out/etape15/P2_completude_par_point.csv
  out/etape15/P2_completude_distribution.csv
  out/etape15/P2_journees_maigres.csv
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import (CODE, RACINE, RACINE_CODE, decouvrir, ecrire_csv,  # noqa: E402
                     nom_point, _f)
from thermie_debits import io_data                                      # noqa: E402

OUT = RACINE / "out" / "etape15"

# Les deux seuils de la regle de decision, ecrits ici et nulle part ailleurs.
PART_NOTABLE = 1.0      # % des journees du corpus, au-dela : issue A ou B
PART_NEGLIGEABLE = 0.1  # % en deca : issue C
FRACTION_MAIGRE = 0.25  # « moins du quart de l'effectif attendu du point »


def trous_par_journee(sub: pd.DataFrame):
    """
    Le TROU MAXIMAL de chaque journee : le plus long intervalle non observe,
    bornes de minuit comprises. En heures.

    Cette grandeur ne depend d'AUCUNE cadence de reference. Une journee
    horaire reguliere rend 1 h, une journee a six heures reguliere rend 6 h,
    une journee dont les mesures sont groupees le matin rend ~18 h. C'est ce
    que la moyenne journaliere IGNORE, dit sans convention prealable.

    Elle remplace le critere « moins du quart de l'effectif attendu », qui
    reposait sur un pas modal unique et confondait donc une CADENCE PLUS LARGE
    avec une journee TRONQUEE — l'erreur que l'etape 1 avait corrigee sur la
    matrice de couverture.
    """
    if sub is None or not len(sub):
        return pd.DataFrame(columns=["date", "trou_max_h"])
    s = sub.copy()
    s["dt"] = pd.to_datetime(s["datetime"])
    s["jour"] = s["dt"].dt.normalize()
    lignes = []
    for jour, g in s.groupby("jour"):
        t = g["dt"].sort_values()
        bornes = [jour] + list(t) + [jour + pd.Timedelta(days=1)]
        ecarts = pd.Series(bornes).diff().dropna().dt.total_seconds() / 3600.0
        lignes.append(dict(date=jour.date(),
                           trou_max_h=float(ecarts.max()) if len(ecarts) else 24.0))
    return pd.DataFrame(lignes)


def pas_modal_minutes(sub: pd.DataFrame):
    """Le pas de mesure infra-journalier le plus frequent, en minutes."""
    if sub is None or len(sub) < 3:
        return None
    dt = pd.to_datetime(sub["datetime"]).sort_values()
    d = dt.diff().dropna().dt.total_seconds() / 60.0
    d = d[(d > 0) & (d <= 24 * 60)]
    if not len(d):
        return None
    return float(d.mode().iloc[0]) if len(d.mode()) else float(d.median())


def ecart_aux_voisines(daily: pd.DataFrame):
    """
    Ecart de T_eau_moy a la moyenne des journees J-1 et J+1.

    Temoin INDEPENDANT du critere : il ne regarde pas l'effectif, seulement la
    coherence de la journee avec ses voisines calendaires.
    """
    d = daily.copy()
    d["date_dt"] = pd.to_datetime(d["date"])
    d = d.sort_values("date_dt").reset_index(drop=True)
    s = pd.Series(d["T_eau_moy"].to_numpy(),
                  index=pd.DatetimeIndex(d["date_dt"]))
    prec = s.reindex(s.index - pd.Timedelta(days=1)).to_numpy()
    suiv = s.reindex(s.index + pd.Timedelta(days=1)).to_numpy()
    voisines = np.nanmean(np.vstack([prec, suiv]), axis=0)
    d["ecart_voisines"] = s.to_numpy() - voisines
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print("=" * 74)
    print("POSE 2 — LA COMPLETUDE DE JOURNEE : de quoi le correctif 12 aurait")
    print("         besoin. Regle de decision ecrite en tete de ce fichier.")
    print("=" * 74)

    par_point, distribution, maigres = [], [], []
    tot_j = tot_maigres = tot_trouees = 0
    sans_contraste = []

    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            try:
                daily, sub, _m = io_data.marquer_lecture(
                    str(RACINE / point_rel), nom=point_rel.split("/")[-1],
                    retour_sous_quotidien=True)
            except Exception as exc:
                par_point.append(dict(jeu=jeu["jeu"], point=pt,
                                      statut=f"ECHEC {type(exc).__name__}"))
                continue
            if not len(daily):
                continue

            n = daily["n_mesures"].to_numpy()
            pas = pas_modal_minutes(sub)
            attendu = (1440.0 / pas) if pas else None
            # L'effectif ATTENDU est celui du point, derive de son pas de
            # mesure : aucun nombre importe, aucune valeur de bassin.
            seuil = (attendu * FRACTION_MAIGRE) if attendu else None

            d = ecart_aux_voisines(daily)
            d["n_mesures"] = daily["n_mesures"].to_numpy()
            est_maigre = (d["n_mesures"].to_numpy() < seuil) if seuil else \
                np.zeros(len(d), dtype=bool)

            # --- SECONDE VERSION : le trou maximal, sans cadence de reference
            tr = trous_par_journee(sub)
            d = d.merge(tr, on="date", how="left")
            trou = d["trou_max_h"].to_numpy()
            trou_med = float(np.nanmedian(trou)) if np.isfinite(trou).any() else None
            # « Le trou depasse le QUADRUPLE de celui d'une journee ordinaire
            # de ce point » : le repere est la mediane du point lui-meme, donc
            # sa propre cadence, quelle qu'elle soit et qu'elle change ou non.
            seuil_trou = (4.0 * trou_med) if trou_med else None
            est_trouee = ((trou > seuil_trou) if seuil_trou
                          else np.zeros(len(d), dtype=bool))
            est_trouee = np.where(np.isfinite(trou), est_trouee, False)

            e = d["ecart_voisines"].to_numpy()
            fini = np.isfinite(e)
            e_maigre = np.abs(e[fini & est_maigre])
            e_autres = np.abs(e[fini & ~est_maigre])

            contraste = len(set(n.tolist())) > 1
            if not contraste:
                sans_contraste.append(pt)

            tot_j += len(d)
            tot_maigres += int(est_maigre.sum())
            tot_trouees += int(est_trouee.sum())
            e_trouee = np.abs(e[fini & est_trouee])

            par_point.append(dict(
                jeu=jeu["jeu"], point=pt, statut="OK",
                pas_modal_min=_f(pas), effectif_attendu=_f(attendu),
                seuil_maigre=_f(seuil),
                journees=len(d),
                n_min=int(n.min()), n_median=_f(float(np.median(n))),
                n_max=int(n.max()),
                journees_n_egal_1=int((n == 1).sum()),
                journees_maigres=int(est_maigre.sum()),
                part_maigres_pct=_f(100.0 * est_maigre.sum() / len(d)),
                contraste_effectif="oui" if contraste else "NON",
                ecart_voisines_median_maigres=_f(
                    float(np.median(e_maigre)) if len(e_maigre) else None),
                ecart_voisines_median_autres=_f(
                    float(np.median(e_autres)) if len(e_autres) else None),
                ecart_voisines_max_maigres=_f(
                    float(e_maigre.max()) if len(e_maigre) else None),
                trou_max_median_h=_f(trou_med),
                trou_max_p95_h=_f(float(np.nanpercentile(trou, 95))
                                  if np.isfinite(trou).any() else None),
                trou_max_max_h=_f(float(np.nanmax(trou))
                                  if np.isfinite(trou).any() else None),
                seuil_trou_h=_f(seuil_trou),
                journees_trouees=int(est_trouee.sum()),
                part_trouees_pct=_f(100.0 * est_trouee.sum() / len(d)),
                ecart_voisines_median_trouees=_f(
                    float(np.median(e_trouee)) if len(e_trouee) else None)))

            for v in sorted(set(n.tolist())):
                distribution.append(dict(
                    jeu=jeu["jeu"], point=pt, n_mesures=int(v),
                    journees=int((n == v).sum())))

            marquees = est_maigre | est_trouee
            if marquees.any():
                for _, r in d[marquees].iterrows():
                    maigres.append(dict(
                        jeu=jeu["jeu"], point=pt, date=str(r["date"]),
                        n_mesures=int(r["n_mesures"]),
                        trou_max_h=_f(r.get("trou_max_h")),
                        maigre="oui" if r["n_mesures"] < (seuil or 0) else "non",
                        trouee=("oui" if (seuil_trou
                                          and r.get("trou_max_h", 0) > seuil_trou)
                                else "non"),
                        T_eau_moy=_f(r["T_eau_moy"]),
                        ecart_voisines=_f(r["ecart_voisines"])))
            print(f"  · {jeu['jeu']}/{pt} : pas={pas} min, n de {int(n.min())} "
                  f"a {int(n.max())}, maigres {int(est_maigre.sum())}/{len(d)}",
                  flush=True)

    ecrire_csv(OUT / "P2_completude_par_point.csv",
               ["jeu", "point", "statut", "pas_modal_min", "effectif_attendu",
                "seuil_maigre", "journees", "n_min", "n_median", "n_max",
                "journees_n_egal_1", "journees_maigres", "part_maigres_pct",
                "contraste_effectif", "ecart_voisines_median_maigres",
                "ecart_voisines_median_autres", "ecart_voisines_max_maigres",
                "trou_max_median_h", "trou_max_p95_h", "trou_max_max_h",
                "seuil_trou_h", "journees_trouees", "part_trouees_pct",
                "ecart_voisines_median_trouees"],
               par_point, tri=["jeu", "point"])
    ecrire_csv(OUT / "P2_completude_distribution.csv",
               ["jeu", "point", "n_mesures", "journees"],
               distribution, tri=["jeu", "point", "n_mesures"])
    ecrire_csv(OUT / "P2_journees_maigres.csv",
               ["jeu", "point", "date", "n_mesures", "trou_max_h", "maigre",
                "trouee", "T_eau_moy", "ecart_voisines"],
               maigres, tri=["jeu", "point", "date"])

    d = pd.DataFrame([l for l in par_point if l.get("journees")])
    part = 100.0 * tot_maigres / tot_j if tot_j else 0.0
    print("\n" + "=" * 74)
    print("CE QUE LE CORPUS DIT DE LA COMPLETUDE DE JOURNEE")
    print("=" * 74)
    print(f"  journees du corpus              : {tot_j}")
    print(f"  journees MAIGRES (< 1/4 attendu): {tot_maigres}  ({part:.3f} %)")
    print(f"  points sans contraste d'effectif: {len(sans_contraste)}")
    if len(d):
        av = d[d.contraste_effectif == "oui"]
        print(f"  points avec contraste           : {len(av)} / {len(d)}")
        print(f"\n  journees a UNE seule mesure     : "
              f"{int(d.journees_n_egal_1.sum())}")
        em = d["ecart_voisines_median_maigres"].dropna()
        ea = d["ecart_voisines_median_autres"].dropna()
        if len(em):
            print(f"\n  TEMOIN INDEPENDANT — ecart absolu a la moyenne des "
                  f"journees voisines :")
            print(f"     journees maigres  : mediane des medianes "
                  f"{em.median():.4f} degC  (sur {len(em)} points)")
            print(f"     autres journees   : mediane des medianes "
                  f"{ea.median():.4f} degC")
    part_tr = 100.0 * tot_trouees / tot_j if tot_j else 0.0
    print("\n" + "=" * 74)
    print("SECONDE VERSION — LE TROU MAXIMAL, SANS CADENCE DE REFERENCE")
    print("=" * 74)
    print(f"  journees TROUEES (> 4x le trou median du point) : "
          f"{tot_trouees}  ({part_tr:.3f} %)")
    if len(d):
        print(f"  trou median d'une journee ordinaire, par point :")
        tm = d["trou_max_median_h"].dropna()
        print(f"     de {tm.min():.2f} h a {tm.max():.2f} h "
              f"(mediane {tm.median():.2f} h)")
        et = d["ecart_voisines_median_trouees"].dropna()
        ea2 = d["ecart_voisines_median_autres"].dropna()
        if len(et):
            print(f"  TEMOIN INDEPENDANT sur les journees trouees :")
            print(f"     journees trouees : mediane des medianes "
                  f"{et.median():.4f} degC  (sur {len(et)} points)")
            print(f"     autres journees  : mediane des medianes "
                  f"{ea2.median():.4f} degC")

    print("\n" + "-" * 74)
    print("  VERDICT SELON LA REGLE ECRITE AVANT LES CHIFFRES :")
    if part < PART_NEGLIGEABLE:
        print(f"     ISSUE C — {part:.3f} % < {PART_NEGLIGEABLE} % : le corpus")
        print( "     ne justifie pas de critere derive de lui.")
    elif part >= PART_NOTABLE:
        print(f"     part notable ({part:.3f} % >= {PART_NOTABLE} %) : issue A")
        print( "     ou B selon le temoin independant.")
    else:
        print(f"     part intermediaire ({part:.3f} %) : entre C et A/B, a")
        print( "     instruire dans la specification.")
    print("-" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
