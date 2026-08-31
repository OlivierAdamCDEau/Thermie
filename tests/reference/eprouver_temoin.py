"""
eprouver_temoin.py — ETAPE 19, taches B et C : eprouver le temoin la ou il
n'a pas ete construit.

AUCUNE MODIFICATION APPLICATIVE. Ce script applique la regle scellee de
`temoin_regime.py` — qu'il importe et ne reecrit pas — a des populations que
cette regle n'a pas vues.

================================================================================
LES POPULATIONS, DECLAREES AVANT L'EXECUTION
================================================================================
Le detecteur est joue deux fois par point : ALLUME, pour savoir quelles
journees il marque ; ETEINT, pour disposer de toutes les journees et de leurs
grandeurs. Le temoin ne juge jamais que sur le rejeu ETEINT.

  B.1  LES 42 NON INSTRUITES
       Les journees marquees par le detecteur qui ne franchissaient aucun seuil
       piscicole, donc laissees de cote a l'etape 18. Le temoin ne les a jamais
       vues. S'il est bon, il doit y trouver une proportion elevee d'artefacts.

  B.2  LE TEMOIN DE CONTROLE — LE TEST QUI COMPTE
       Des journees NON marquees par le detecteur, appariees par point et par
       saison aux 69 marquees. Le temoin n'a aucune raison d'y sonner.

       DEFINITION PRIMAIRE, celle a laquelle le seuil scelle s'applique :
         journees NON marquees, aux points portant au moins une journee
         marquee, dans les MOIS ou ce point porte des journees marquees,
         ET SITUEES A PLUS DE 7 JOURS CALENDAIRES de toute journee marquee du
         MEME POINT ET DE LA MEME ANNEE.
       L'exclusion des voisines est necessaire et n'est pas un amenagement : une
       journee collee a un episode artefactuel appartient vraisemblablement au
       meme episode. Elle n'est pas une journee ordinaire, et la specificite se
       mesure sur des journees ordinaires. Ces voisines sont comptees a part, et
       relevent de la tache C.

       DEFINITION SECONDAIRE, publiee a cote sans que le seuil s'y applique :
         la meme population SANS l'exclusion des voisines.

  B.3  LES 27 DE L'ETAPE 18
       Rapportees POUR MEMOIRE SEULEMENT. C'est la que le temoin est ne : il
       les explique par construction et elles ne prouvent rien. Le dire est la
       seule chose qu'elles apportent.

  C    TOUTES LES JOURNEES DU CORPUS
       Le temoin applique partout. Une journee qu'il classe artefact et que le
       detecteur n'a pas marquee est une exondation possible RESTEE DANS
       L'ANALYSE — l'autre moitie de la question, celle qui surestime le risque
       au lieu de le sous-estimer.

================================================================================
CE QUE CE SCRIPT NE FAIT PAS
================================================================================
Il ne modifie ni ne propose de modifier le detecteur. Il ne reclasse aucune
journee dans aucun livrable. Il ne touche a aucune reference figee.

LE SCEAU DE CE FICHIER EST ROMPU, ET C'EST DELIBERE (etape 21, D121)
Son empreinte d'origine etait
    e78f370e7c7cba7844e70aceb359d78c755827122bd1abf27d5656f53886187e
et elle a rempli son office : a l'etape 20, ce script devait etre rejoue SANS
MODIFICATION pour que la comparaison des deux epreuves ait un sens. Elle l'a
ete, et le resultat est publie.

Le chemin de sortie etait fige vers `out/etape19/`. Rejoue a l'etape 20, il a
ecrase quatre artefacts de l'etape 19 — repares depuis. La sortie est desormais
REDIRIGEABLE : `--sortie <dossier>`, avec `out/etape19` pour defaut, de sorte
que rejouer sans argument reproduit exactement l'ancien comportement.

Rompre un sceau sans le dire serait pire que ne l'avoir jamais pose. Il est
rompu ici, en toutes lettres, et l'empreinte d'origine reste au dossier de
l'etape 19.

SORTIES, sous out/etape19/ par defaut, ou sous --sortie
  B_populations.csv     une ligne par journee jugee, avec sa population
  B_synthese.csv        les proportions, et le verdict de specificite
  C_faux_negatifs.csv   les journees signalees et non marquees
  C_par_point.csv       leur repartition par point et par saison
"""
from __future__ import annotations

import argparse
import contextlib
import io as _io
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
os.environ.setdefault("THERMIE_CODE", "app")

from _commun import (CODE, RACINE, RACINE_CODE, decouvrir, ecrire_csv,  # noqa: E402
                     nom_point, _f)

import build_reference                                                  # noqa: E402
import temoin_regime as TR                                              # noqa: E402
from thermie_debits import orchestrator                                 # noqa: E402

OUT = RACINE / "out" / "etape19"   # defaut ; voir --sortie
MOIS_ETE = (6, 7, 8, 9)
VOISINAGE = 7          # jours : rayon d'exclusion des voisines d'une marquee


def _run(jeu, point_rel, hors_eau=None):
    cfg = build_reference.construire_config(jeu, point_rel, "application")
    if hors_eau is not None:
        cfg.qc.hors_eau = hors_eau
    with contextlib.redirect_stdout(_io.StringIO()), \
         contextlib.redirect_stderr(_io.StringIO()):
        return orchestrator.run(cfg, verbose=False)


def _stats_reference(df):
    """
    Cache (doy, annee) -> (max_T_eau_autres, q95_ecart_autres, n_annees, n_jours).

    Le calcul est identique a `TR.reference` suivi des agregats que `TR.juger`
    en tire ; il est simplement memorise, une chronique comptant plusieurs
    milliers de journees pour quelques milliers de couples distincts.
    """
    cache = {}

    def stats(doy, an):
        cle = (int(doy), int(an))
        if cle in cache:
            return cache[cle]
        r = TR.reference(df, doy, an).dropna(subset=["T_eau_moy", "T_air"])
        if len(r):
            v = (float(r["T_eau_moy"].max()),
                 float((r["T_eau_moy"] - r["T_air"]).quantile(TR.Q_DECOUPLAGE)),
                 int(r["an"].nunique()), int(len(r)))
        else:
            v = (np.nan, np.nan, 0, 0)
        cache[cle] = v
        return v

    return stats


def _juger_serie(df):
    """Applique la regle scellee a toutes les journees de `df`."""
    stats = _stats_reference(df)
    verdicts, excs, decs, nans, njs = [], [], [], [], []
    for _, j in df.iterrows():
        mx, q95, n_an, n_j = stats(j["doy"], j["an"])
        if (n_an < TR.MIN_ANNEES or n_j < TR.MIN_JOURS
                or pd.isna(j["T_eau_moy"]) or pd.isna(j["T_air"])):
            verdicts.append(TR.INDETERMINABLE)
            excs.append(np.nan); decs.append(np.nan)
        else:
            exc = float(j["T_eau_moy"]) - mx
            dec = float(j["T_eau_moy"]) - float(j["T_air"]) - q95
            verdicts.append(TR.ARTEFACT if (exc > 0 and dec > 0)
                            else TR.COMPATIBLE)
            excs.append(exc); decs.append(dec)
        nans.append(n_an); njs.append(n_j)
    return pd.DataFrame({"verdict": verdicts, "exc": excs, "dec": decs,
                         "n_annees": nans, "n_jours_ref": njs}, index=df.index)


def main(argv=None):
    global OUT
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sortie", default=None,
                    help="dossier de sortie (defaut : out/etape19)")
    args = ap.parse_args(argv)
    if args.sortie:
        OUT = Path(args.sortie).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print(f"Sortie       : {OUT}")
    print("=" * 78)
    print("ETAPE 19 — EPROUVER LE TEMOIN LA OU IL N'A PAS ETE CONSTRUIT")
    print(f"regle scellee : temoin_regime.py  "
          f"(fenetre +/-{TR.FENETRE} j, q{TR.Q_DECOUPLAGE:.2f}, "
          f"min {TR.MIN_ANNEES} annees / {TR.MIN_JOURS} journees)")
    print("=" * 78)

    # Les 27 de l'etape 18, pour les distinguer des 42.
    a18 = pd.read_csv(RACINE / "out" / "etape18" / "A_sous_ensemble.csv",
                      sep=";", encoding="utf-8")
    cles18 = set(zip(a18["point"], a18["date"].astype(str).str.slice(0, 10)))

    lignes, echecs = [], []
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            try:
                allume = _run(jeu, point_rel)
                eteint = _run(jeu, point_rel, hors_eau=False)
            except Exception as exc:
                echecs.append((jeu["jeu"], pt, type(exc).__name__))
                print(f"  · {jeu['jeu']}/{pt} : ECHEC ({type(exc).__name__})",
                      flush=True)
                continue

            rq = allume.rapport_qc
            marquees = set()
            if rq is not None and len(rq):
                marquees = {str(x["date"])[:10] for _, x in rq.iterrows()
                            if "hors d" in str(x.get("motif", ""))}

            d = eteint.df.copy()
            d["ds"] = d["date"].astype(str).str.slice(0, 10)
            dt = pd.to_datetime(d["ds"])
            d["an"], d["doy"] = dt.dt.year, dt.dt.dayofyear
            d["marquee"] = d["ds"].isin(marquees)

            # morphologie : quantiles estivaux du point
            ete = d[d["month"].isin(MOIS_ETE)]
            if {"TX", "TN", "T_eau_min"} <= set(d.columns):
                aa = (d["TX"] - d["TN"]).replace(0, np.nan)
                d["R_ampl"] = (d["T_eau_max"] - d["T_eau_min"]) / aa
                re_ = d.loc[ete.index, "R_ampl"].dropna()
                q10 = float(re_.quantile(0.10)) if len(re_) else np.nan
                q90 = float(re_.quantile(0.90)) if len(re_) else np.nan
            else:
                d["R_ampl"] = np.nan
                q10 = q90 = np.nan

            d = pd.concat([d, _juger_serie(d)], axis=1)

            # --- appartenance aux populations
            mois_marques = set(d.loc[d["marquee"], "month"].astype(int))
            jours_marques = {(int(a), int(dd)) for a, dd
                             in zip(d.loc[d["marquee"], "an"],
                                    d.loc[d["marquee"], "doy"])}

            def voisine(an, doy):
                for a2, d2 in jours_marques:
                    if a2 != an:
                        continue
                    e = abs(int(doy) - d2)
                    if min(e, 365 - e) <= VOISINAGE:
                        return True
                return False

            for _, j in d.iterrows():
                est_marquee = bool(j["marquee"])
                cle = (pt, j["ds"])
                if est_marquee:
                    pop = "B3_les_27" if cle in cles18 else "B1_les_42"
                elif (mois_marques and int(j["month"]) in mois_marques):
                    pop = ("B2_controle_voisine" if voisine(j["an"], j["doy"])
                           else "B2_controle")
                else:
                    pop = "hors_appariement"
                lignes.append(dict(
                    jeu=jeu["jeu"], point=pt, date=j["ds"],
                    mois=int(j["month"]), annee=int(j["an"]),
                    population=pop, marquee=("oui" if est_marquee else "non"),
                    verdict=j["verdict"], exc=_f(j["exc"]), dec=_f(j["dec"]),
                    n_annees=int(j["n_annees"]), n_jours_ref=int(j["n_jours_ref"]),
                    T_eau_moy=_f(j["T_eau_moy"]), T_air=_f(j["T_air"]),
                    R_ampl=_f(j["R_ampl"]),
                    morphologie=TR.morphologie(j["R_ampl"], q10, q90)))
            print(f"  · {jeu['jeu']}/{pt} : {len(d)} journees, "
                  f"{len(marquees)} marquee(s)", flush=True)

    t = pd.DataFrame(lignes)
    ecrire_csv(OUT / "B_populations.csv",
               ["jeu", "point", "date", "mois", "annee", "population",
                "marquee", "verdict", "exc", "dec", "n_annees", "n_jours_ref",
                "T_eau_moy", "T_air", "R_ampl", "morphologie"],
               lignes, tri=["population", "jeu", "point", "date"])

    # ================= synthese des populations =================
    syn = []
    for pop in ["B1_les_42", "B2_controle", "B2_controle_voisine",
                "B3_les_27", "hors_appariement"]:
        s = t[t.population == pop]
        if not len(s):
            continue
        jug = s[s.verdict != TR.INDETERMINABLE]
        n_art = int((s.verdict == TR.ARTEFACT).sum())
        syn.append(dict(
            population=pop, n=len(s),
            n_jugeables=len(jug),
            n_indeterminables=int((s.verdict == TR.INDETERMINABLE).sum()),
            n_artefact=n_art,
            pct_artefact_sur_jugeables=_f(100 * n_art / len(jug) if len(jug) else np.nan),
            exc_median_des_artefacts=_f(
                s.loc[s.verdict == TR.ARTEFACT, "exc"].median()
                if n_art else np.nan)))
    ecrire_csv(OUT / "B_synthese.csv",
               ["population", "n", "n_jugeables", "n_indeterminables",
                "n_artefact", "pct_artefact_sur_jugeables",
                "exc_median_des_artefacts"], syn, tri=["population"])

    ctrl = t[t.population == "B2_controle"]
    ctrl_j = ctrl[ctrl.verdict != TR.INDETERMINABLE]
    tau = ((ctrl_j.verdict == TR.ARTEFACT).sum() / len(ctrl_j)
           if len(ctrl_j) else np.nan)
    verdict_spe, phrase = TR.verdict_specificite(tau)

    print("\n" + "=" * 78)
    print("TACHE B — L'EPREUVE")
    print("=" * 78)
    for r in syn:
        print(f"  {r['population']:<22} n={r['n']:>6}  jugeables="
              f"{r['n_jugeables']:>6}  artefact={r['n_artefact']:>5}  "
              f"({r['pct_artefact_sur_jugeables']} %)")
    print()
    print(f"  tau (temoin de controle, definition PRIMAIRE) = {100*tau:.2f} %")
    print(f"  seuil scelle : <=5 % specifique | 5-20 % partiel | >=20 % non")
    print(f"  VERDICT : {verdict_spe}")
    print(f"            {phrase}")

    # ================= tache C — faux negatifs =================
    fn = t[(t.marquee == "non") & (t.verdict == TR.ARTEFACT)].copy()
    ecrire_csv(OUT / "C_faux_negatifs.csv",
               ["jeu", "point", "date", "mois", "annee", "population",
                "exc", "dec", "T_eau_moy", "T_air", "R_ampl", "morphologie",
                "n_annees", "n_jours_ref"],
               fn.to_dict("records"), tri=["jeu", "point", "date"])
    if len(fn):
        pp = (fn.groupby(["jeu", "point"])
                .agg(n_signalees=("date", "size"),
                     exc_max=("exc", "max"), exc_median=("exc", "median"),
                     premier=("date", "min"), dernier=("date", "max"))
                .reset_index())
        tot = t[t.marquee == "non"].groupby(["jeu", "point"]).size()
        pp["n_non_marquees"] = pp.apply(
            lambda r: int(tot.get((r["jeu"], r["point"]), 0)), axis=1)
        ecrire_csv(OUT / "C_par_point.csv",
                   ["jeu", "point", "n_signalees", "n_non_marquees",
                    "exc_max", "exc_median", "premier", "dernier"],
                   pp.to_dict("records"), tri=["n_signalees", "point"])

    print("\n" + "=" * 78)
    print("TACHE C — LES FAUX NEGATIFS")
    print("=" * 78)
    n_nm = int((t.marquee == "non").sum())
    print(f"  journees non marquees par le detecteur : {n_nm}")
    print(f"  dont le temoin signale artefact        : {len(fn)}"
          f"  ({100*len(fn)/n_nm:.2f} %)")
    print(f"  journees marquees par le detecteur     : "
          f"{int((t.marquee == 'oui').sum())}")
    if len(fn):
        print(f"  points concernes : {fn['point'].nunique()}")
        print("\n  par point (les dix premiers) :")
        for _, r in pp.sort_values("n_signalees", ascending=False).head(10).iterrows():
            print(f"     {r['point']:<34} {r['n_signalees']:>4} / "
                  f"{r['n_non_marquees']:>5}   exc max {r['exc_max']:.2f}   "
                  f"{r['premier']} -> {r['dernier']}")
        print("\n  par mois :")
        for m, n in fn.groupby("mois").size().items():
            print(f"     mois {int(m):>2} : {n}")
    if echecs:
        print("\n  ECHECS DE REJEU (declares) :")
        for j, p, e in echecs:
            print(f"     {j}/{p} : {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
