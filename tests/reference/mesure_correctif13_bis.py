"""
mesure_correctif13_bis.py — ETAPE 20 : REPRISE DES SIGNAUX A ET B.

================================================================================
LE DEFAUT DU SCRIPT SCELLE, ET CE QUI EST CORRIGE
================================================================================
`mesure_correctif13.py` a ete scelle avant tout chiffre
(a93be1d7d93b22c8e984ed063c4fb240770142e953acca233b1c32db1fabc621) et il porte
un DEFAUT que la mesure a revele :

    il cherchait les journees nouvellement marquees dans `res.df`
    — or `res.df` est construit sur `vue_retenue`, d'ou les journees marquees
    sont precisement RETIREES.

L'ensemble collecte etait donc vide, et la console a imprime « +0 nouvellement
marquees » en face de « 69 -> 232 ». La contradiction est visible dans la trace
livree ; elle n'a pas ete effacee.

CE QUI RESTE VALIDE DANS LE SCRIPT SCELLE
  · Signal C — sens des verdicts. Calcule sur `res.vulnerabilite`,
    `res.sgvt` et `res.fraie`, qui ne dependent pas de la collecte fautive.
    Resultat : 0 point sur 31 deplace une categorie.
  · Signal D — les 69 doivent rester. Calcule sur les ensembles de dates
    marquees, independamment de `res.df`. Resultat : 0 journee perdue.

CE QUI EST REPRIS ICI
  · Signal A — volume.
  · Signal B — corroboration par le temoin scelle de l'etape 19.

CE QUI N'EST PAS TOUCHE, ET C'EST L'ESSENTIEL
    LES DEUX SEUILS SONT REPRIS MOT POUR MOT DU FICHIER SCELLE : 5 % pour le
    volume, 20 % pour la corroboration. Aucune valeur n'est deplacee. Le sceau
    de `mesure_correctif13.py` reste verifiable sur le fichier d'origine, qui
    n'est pas modifie ; les deux empreintes sont publiees cote a cote.

    Un sceau garantit qu'un critere n'a pas ete choisi apres coup. Il ne
    garantit pas qu'un script soit exempt de defaut. Corriger la collecte sans
    toucher au critere est la seule facon de reparer l'un sans annuler l'autre.

================================================================================
LA REGLE, REPRISE VERBATIM
================================================================================
  A — VOLUME. Le detecteur marque aujourd'hui 69 journees sur environ 20 000
      journees estivales, soit 0,35 %. Si l'extension marque PLUS DE 5 % des
      journees hors juin-septembre, le critere ne se comporte pas dehors comme
      dedans, et il faut comprendre pourquoi avant de poser.

  B — CORROBORATION. Les journees nouvellement marquees sont confrontees au
      temoin scelle de l'etape 19, qui est independant du detecteur et dont la
      specificite a ete etablie (tau = 0,205 %). Si MOINS DE 20 % des journees
      nouvellement marquees et jugeables sont classees `artefact` par le temoin,
      les nouvelles marques sont de qualite inferieure aux anciennes et il faut
      le dire avant de poser.

COMMENT LE TEMOIN EST LU, SANS ETRE REJOUE
Le verdict du temoin pour CHAQUE journee du corpus a deja ete produit a l'etape
19 et fige dans `out/etape19/B_populations.csv` — 67 123 lignes, calculees sur
la chronique detecteur ETEINT, donc sur une reference qui contient toutes les
journees. Le relire est plus exact que le recalculer : c'est le meme verdict,
issu du meme fichier scelle, sans risque d'en produire une variante.
"""
from __future__ import annotations

import contextlib
import io as _io
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
os.environ.setdefault("THERMIE_CODE", "app")

from _commun import RACINE, decouvrir, ecrire_csv, nom_point            # noqa: E402

import build_reference                                                  # noqa: E402
import temoin_regime as TR                                              # noqa: E402
from thermie_debits import orchestrator                                 # noqa: E402

OUT = RACINE / "out" / "etape20"
ETE = (6, 7, 8, 9)
ANNEE = tuple(range(1, 13))
SEUIL_VOLUME = 0.05          # verbatim du fichier scelle
SEUIL_CORROBORATION = 0.20   # verbatim du fichier scelle


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("ETAPE 20 — SIGNAUX A ET B, REPRIS")
    print("Seuils repris verbatim du fichier scelle : 5 % et 20 %")
    print("=" * 78)

    # Les 69 deja marquees, telles que l'etape 18 les a figees.
    a18 = pd.read_csv(RACINE / "out" / "etape18" / "A_toutes_marquees.csv",
                      sep=";", encoding="utf-8")
    deja = set(zip(a18["point"], a18["date"].astype(str).str.slice(0, 10)))
    print(f"  journees deja marquees (etape 18) : {len(deja)}")

    # Le temoin de l'etape 19, tel qu'il a ete produit.
    pop = pd.read_csv(RACINE / "out" / "etape19" / "B_populations.csv",
                      sep=";", encoding="utf-8")
    temoin = {(r.point, r.date): (r.verdict, r.exc, r.dec, r.n_annees,
                                  r.T_eau_moy, r.T_air, r.morphologie)
              for r in pop.itertuples()}
    print(f"  verdicts du temoin disponibles    : {len(temoin)}")

    nouvelles, echecs = [], []
    n_hors_ete = 0
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            cfg = build_reference.construire_config(jeu, point_rel,
                                                    "application")
            cfg.qc.hors_eau_mois = ANNEE
            try:
                with contextlib.redirect_stdout(_io.StringIO()), \
                     contextlib.redirect_stderr(_io.StringIO()):
                    res = orchestrator.run(cfg, verbose=False)
            except Exception as exc:
                echecs.append((jeu["jeu"], pt, type(exc).__name__))
                print(f"  · {jeu['jeu']}/{pt} : ECHEC ({type(exc).__name__})",
                      flush=True)
                continue
            rq = res.rapport_qc
            marquees = {}
            if rq is not None and len(rq):
                for _, x in rq.iterrows():
                    if "hors d" in str(x.get("motif", "")):
                        marquees[str(x["date"])[:10]] = str(x.get("motif", ""))
            n_pt = int((~pop.loc[pop.point == pt, "mois"].isin(ETE)).sum())
            n_hors_ete += n_pt
            ajoutees = sorted(d for d in marquees if (pt, d) not in deja)
            for ds in ajoutees:
                t = temoin.get((pt, ds))
                nouvelles.append(dict(
                    jeu=jeu["jeu"], point=pt, date=ds,
                    mois=int(ds[5:7]), motif=marquees[ds],
                    temoin=(t[0] if t else "absent du releve d'etape 19"),
                    exc=(t[1] if t else None), dec=(t[2] if t else None),
                    n_annees=(t[3] if t else None),
                    T_eau_moy=(t[4] if t else None), T_air=(t[5] if t else None),
                    morphologie=(t[6] if t else None)))
            print(f"  · {jeu['jeu']}/{pt} : {len(marquees)} marquee(s), "
                  f"+{len(ajoutees)} nouvelle(s)", flush=True)

    ecrire_csv(OUT / "B_nouvelles.csv",
               ["jeu", "point", "date", "mois", "temoin", "exc", "dec",
                "n_annees", "T_eau_moy", "T_air", "morphologie", "motif"],
               nouvelles, tri=["jeu", "point", "date"])

    nv = pd.DataFrame(nouvelles)
    jug = nv[~nv.temoin.isin([TR.INDETERMINABLE,
                              "absent du releve d'etape 19"])] if len(nv) else nv
    n_cor = int((jug.temoin == TR.ARTEFACT).sum()) if len(jug) else 0
    taux_cor = (n_cor / len(jug)) if len(jug) else np.nan
    taux_vol = (len(nv) / n_hors_ete) if n_hors_ete else np.nan

    print("\n" + "=" * 78)
    print("  A — VOLUME")
    print(f"      journees hors juin-septembre : {n_hors_ete}")
    print(f"      nouvellement marquees        : {len(nv)}  "
          f"({100*taux_vol:.3f} %)")
    print(f"      seuil : 5 %  ->  "
          f"{'ALERTE' if taux_vol > SEUIL_VOLUME else 'SOUS LE SEUIL'}")
    print("\n  B — CORROBORATION par le temoin scelle de l'etape 19")
    print(f"      nouvelles          : {len(nv)}")
    print(f"      jugeables          : {len(jug)}")
    print(f"      classees artefact  : {n_cor}  ({100*taux_cor:.1f} %)")
    print(f"      seuil : 20 %  ->  "
          f"{'ALERTE' if taux_cor < SEUIL_CORROBORATION else 'AU-DESSUS DU SEUIL'}")
    if len(nv):
        print(f"      repartition : {nv.temoin.value_counts().to_dict()}")
        print(f"\n      rappel : le temoin classe `artefact` 0,205 % des "
              f"journees ordinaires.")
        print(f"      il en classe {100*taux_cor:.1f} % ici, soit "
              f"x {taux_cor/0.00205:.0f}")
        print("\n  Les nouvelles marques, par mois :")
        for m, n in nv.groupby("mois").size().items():
            print(f"     mois {int(m):>2} : {n:>4}")
        print("\n  Les points les plus concernes :")
        for p, n in nv.groupby("point").size().sort_values(
                ascending=False).head(12).items():
            sub = nv[nv.point == p]
            art = int((sub.temoin == TR.ARTEFACT).sum())
            print(f"     {p:<36} +{n:>3}   dont {art:>3} corrobore(s)")
    if echecs:
        print("\n  ECHECS DE REJEU (declares) :")
        for j, p, e in echecs:
            print(f"     {j}/{p} : {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
