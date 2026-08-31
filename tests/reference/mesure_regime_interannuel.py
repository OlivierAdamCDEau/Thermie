"""
mesure_regime_interannuel.py — ETAPE 18, TEMOIN POST HOC. DECLARE COMME TEL.

CE TEMOIN N'EST PAS DANS LA REGLE SCELLEE. Il a ete construit APRES avoir vu
les journees. Il ne reclasse rien, il ne corrige aucun verdict de
`verifier_faux_positifs.py`, et il ne doit pas etre lu comme un cinquieme
temoin de la regle : ce serait exactement la faute que la regle scellee
interdisait — choisir le critere apres avoir vu les resultats.

Il est produit, et publie, pour UNE seule raison : la regle scellee a classe
six journees en « evenement thermique reel », et le devoir de dire ce qui,
dans la methode, aurait pu produire ce resultat sans qu'il soit vrai impose
de chercher la refutation la plus severe possible. La voici.

CE QU'IL MESURE
----------------
Le point se compare a LUI-MEME, d'une annee sur l'autre, a la meme date. Pour
chaque journee instruite, la temperature moyenne de l'eau est rapportee a la
distribution des memes journees calendaires (+/- 7 jours) des AUTRES annees du
meme point. Aucun autre point n'intervient : ce n'est pas de la synchronie
spatiale, c'est le regime propre du point (D15, D41 respectes).

  ecart_deg    la journee, moins la mediane des memes dates des autres annees
  n_annees     combien d'autres annees fournissent la comparaison
  ecart_max    l'ecart de la journee, moins le MAXIMUM observe aux memes dates
               des autres annees. Positif, il dit que la journee sort de tout
               ce que le point a jamais montre a cette saison.

CE QU'IL NE MESURE PAS
-----------------------
Il ne distingue pas une sonde hors d'eau d'une sonde en panne, d'une sonde
deplacee ou d'une annee reellement exceptionnelle. Il dit seulement si la
valeur est compatible avec l'histoire thermique du point. Un point d'une seule
annee ne peut rien en tirer, et le fichier le dit ligne par ligne.
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

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f       # noqa: E402

import build_reference                                                 # noqa: E402
from thermie_debits import orchestrator                                # noqa: E402

OUT = RACINE / "out" / "etape18"
FENETRE = 7


def main():
    src = OUT / "A_sous_ensemble.csv"
    if not src.exists():
        raise SystemExit(f"{src} absent : lance d'abord verifier_faux_positifs.py")
    cand = pd.read_csv(src, sep=";", encoding="utf-8")
    if not len(cand):
        raise SystemExit("le sous-ensemble est vide : rien a mesurer")
    print("=" * 78)
    print("TEMOIN POST HOC — le point compare a lui-meme, annee sur annee")
    print("Il ne reclasse rien. Il refute ou confirme, il ne vote pas.")
    print("=" * 78)
    print(f"  journees instruites : {len(cand)}")

    besoin = set(zip(cand["jeu"], cand["point"]))
    lignes = []
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            if (jeu["jeu"], pt) not in besoin:
                continue
            cfg = build_reference.construire_config(jeu, point_rel,
                                                    "application")
            cfg.qc.hors_eau = False
            with contextlib.redirect_stdout(_io.StringIO()), \
                 contextlib.redirect_stderr(_io.StringIO()):
                r = orchestrator.run(cfg, verbose=False)
            d = r.df.copy()
            d["ds"] = d["date"].astype(str).str.slice(0, 10)
            d["dt"] = pd.to_datetime(d["ds"])
            d["an"] = d["dt"].dt.year
            d["doy"] = d["dt"].dt.dayofyear
            sous = cand[(cand.jeu == jeu["jeu"]) & (cand.point == pt)]
            for _, c in sous.iterrows():
                jr = d[d.ds == str(c["date"])[:10]]
                if not len(jr):
                    continue
                jr = jr.iloc[0]
                # meme fenetre calendaire, AUTRES annees du meme point
                ecart_doy = (d["doy"] - jr["doy"]).abs()
                ecart_doy = np.minimum(ecart_doy, 365 - ecart_doy)
                comp = d[(ecart_doy <= FENETRE) & (d["an"] != jr["an"])]
                comp = comp.dropna(subset=["T_eau_moy"])
                n_an = int(comp["an"].nunique())
                if n_an == 0:
                    lignes.append(dict(
                        jeu=jeu["jeu"], point=pt, date=str(c["date"])[:10],
                        T_eau_moy=_f(jr["T_eau_moy"]), n_annees=0,
                        n_journees_comparees=0,
                        lecture="AUCUNE AUTRE ANNEE — ce temoin ne peut rien dire"))
                    continue
                med = float(comp["T_eau_moy"].median())
                mx = float(comp["T_eau_moy"].max())
                e_med = float(jr["T_eau_moy"]) - med
                e_max = float(jr["T_eau_moy"]) - mx
                if e_max > 0:
                    lect = (f"hors de tout precedent : +{e_max:.2f} degC "
                            f"au-dessus du MAXIMUM jamais observe a cette "
                            f"saison sur ce point")
                elif e_med > 0:
                    lect = (f"+{e_med:.2f} degC au-dessus de la mediane "
                            f"saisonniere du point, mais dans l'enveloppe deja "
                            f"observee")
                else:
                    lect = (f"{e_med:.2f} degC : la journee est DANS le regime "
                            f"habituel du point a cette date")
                lignes.append(dict(
                    jeu=jeu["jeu"], point=pt, date=str(c["date"])[:10],
                    T_eau_moy=_f(jr["T_eau_moy"]),
                    mediane_autres_annees=_f(med), max_autres_annees=_f(mx),
                    ecart_deg=_f(e_med), ecart_max=_f(e_max),
                    n_annees=n_an, n_journees_comparees=int(len(comp)),
                    lecture=lect))
            print(f"  · {jeu['jeu']}/{pt}", flush=True)

    ecrire_csv(OUT / "D_regime_interannuel.csv",
               ["jeu", "point", "date", "T_eau_moy", "mediane_autres_annees",
                "max_autres_annees", "ecart_deg", "ecart_max", "n_annees",
                "n_journees_comparees", "lecture"],
               lignes, tri=["jeu", "point", "date"])

    t = pd.DataFrame(lignes)
    hors = t[t.ecart_max.astype(float) > 0] if "ecart_max" in t else t.iloc[:0]
    print("\n" + "=" * 78)
    print(f"  journees mesurees                         : {len(t)}")
    print(f"  sans autre annee pour comparer            : "
          f"{int((t.n_annees == 0).sum())}")
    print(f"  HORS de tout precedent saisonnier du point : {len(hors)}")
    print("=" * 78)
    for _, r in t.sort_values(["point", "date"]).iterrows():
        print(f"  {r['point']:<34} {r['date']}  "
              f"T_eau {r['T_eau_moy']:>6}  {r['lecture']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
