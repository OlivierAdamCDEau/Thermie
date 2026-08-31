"""
mesure_impact_faux_negatifs.py — ETAPE 19, tache C : CE QUE CELA IMPLIQUERAIT.

AUCUNE MODIFICATION APPLICATIVE, ET AUCUNE PROPOSITION D'EN FAIRE. Ce script
appelle les fonctions applicatives TELLES QUELLES sur une chronique dont on a
retire les journees que le temoin signale, et lit ce que les indicateurs
deviennent. C'est un chiffrage, pas un correctif : rien n'est pose, et la
chaine livree n'est pas touchee.

POURQUOI CETTE MESURE
----------------------
La tache C demande de dire ce que les faux negatifs impliqueraient. Le dire
sans le mesurer serait une conjecture. Les journees signalees et non marquees
tombent, sur certains points, DANS LA FENETRE DE REPRODUCTION de l'espece
repere — mai est un mois de fraie pour l'ombre commun (3-4-5), le barbeau et la
breme (4-5-6-7). Elles alimentent donc `analyse_fraie_croissance` et le
coefficient saisonnier `_m_saisonnier` qu'elle derive.

Le contrefactuel est simple et ne demande aucun parametre nouveau : on retire
de `res.df` les journees que le temoin signale, on rappelle les memes fonctions
applicatives, et on compare. La vulnerabilite estivale et la sensibilite sont
recalculees aussi, pour verifier qu'elles ne bougent pas la ou les journees
signalees sont hors de l'ete.
"""
from __future__ import annotations

import contextlib
import io as _io
import os
import sys
import warnings

import pandas as pd

warnings.filterwarnings("ignore")
os.environ.setdefault("THERMIE_CODE", "app")

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f      # noqa: E402

import build_reference                                                # noqa: E402
from thermie_debits import core, orchestrator                         # noqa: E402

OUT = RACINE / "out" / "etape19"


def _indicateurs(df, ctx, cle):
    sens = core.analyse_sensibilite(df)
    vul = core.analyse_vulnerabilite(df, sens["m"], ctx, cle)
    fraie = core.analyse_fraie_croissance(df, sens["m"], ctx, cle, verbose=False)
    sgvt = core.calcul_sgvt(sens, vul, fraie)
    return dict(m=sens.get("m"), n_aigu=vul.get("n_aigu"),
                cat_aigu=vul.get("cat_aigu"),
                pct_chr=vul.get("pct_chr"), cat_chr=vul.get("cat_chr"),
                P_fraie=(fraie or {}).get("P_fraie"),
                espece=(fraie or {}).get("espece_limitante"),
                sgvt=sgvt.get("sgvt"), classe=sgvt.get("interp"))


def main():
    fn = pd.read_csv(OUT / "C_faux_negatifs.csv", sep=";", encoding="utf-8")
    if not len(fn):
        print("aucun faux negatif : rien a chiffrer")
        return 0
    cibles = (fn.groupby(["jeu", "point"]).size()
                .sort_values(ascending=False))
    print("=" * 78)
    print("TACHE C — CE QUE LE RETRAIT DES JOURNEES SIGNALEES CHANGERAIT")
    print("Aucune pose. Les fonctions applicatives sont appelees telles quelles.")
    print("=" * 78)

    lignes = []
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            if (jeu["jeu"], pt) not in cibles.index:
                continue
            dates = set(fn.loc[(fn.jeu == jeu["jeu"]) & (fn.point == pt),
                               "date"].astype(str))
            cfg = build_reference.construire_config(jeu, point_rel,
                                                    "application")
            try:
                with contextlib.redirect_stdout(_io.StringIO()), \
                     contextlib.redirect_stderr(_io.StringIO()):
                    res = orchestrator.run(cfg, verbose=False)
            except Exception as exc:
                print(f"  · {pt} : rejeu en echec ({type(exc).__name__})")
                continue
            ctx, cle = res.contexte, cfg.contexte_piscicole
            df = res.df.copy()
            df["ds"] = df["date"].astype(str).str.slice(0, 10)
            garde = df[~df["ds"].isin(dates)].drop(columns=["ds"])
            try:
                with contextlib.redirect_stdout(_io.StringIO()), \
                     contextlib.redirect_stderr(_io.StringIO()):
                    tel_quel = _indicateurs(res.df.copy(), ctx, cle)
                    sans = _indicateurs(garde, ctx, cle)
            except Exception as exc:
                print(f"  · {pt} : contrefactuel en echec ({type(exc).__name__})")
                continue
            bouge = [k for k in ("cat_aigu", "cat_chr", "P_fraie", "classe")
                     if tel_quel[k] != sans[k]]
            lignes.append(dict(
                jeu=jeu["jeu"], point=pt, n_signalees=len(dates),
                espece=tel_quel["espece"],
                P_fraie_tel_quel=_f(tel_quel["P_fraie"]),
                P_fraie_sans=_f(sans["P_fraie"]),
                n_aigu_tel_quel=tel_quel["n_aigu"], n_aigu_sans=sans["n_aigu"],
                cat_aigu_tel_quel=tel_quel["cat_aigu"],
                cat_aigu_sans=sans["cat_aigu"],
                pct_chr_tel_quel=_f(tel_quel["pct_chr"]),
                pct_chr_sans=_f(sans["pct_chr"]),
                m_tel_quel=_f(tel_quel["m"]), m_sans=_f(sans["m"]),
                sgvt_tel_quel=_f(tel_quel["sgvt"]), sgvt_sans=_f(sans["sgvt"]),
                classe_tel_quel=tel_quel["classe"], classe_sans=sans["classe"],
                ce_qui_bouge=(", ".join(bouge) if bouge else "rien")))
            r = lignes[-1]
            print(f"\n  {pt}  ({len(dates)} journee(s) signalee(s), "
                  f"espece {r['espece']})")
            print(f"     P_fraie   {r['P_fraie_tel_quel']} -> {r['P_fraie_sans']}")
            print(f"     aigu      {r['n_aigu_tel_quel']}j « {r['cat_aigu_tel_quel']} »"
                  f"  ->  {r['n_aigu_sans']}j « {r['cat_aigu_sans']} »")
            print(f"     SGVT      {r['sgvt_tel_quel']} « {r['classe_tel_quel']} »"
                  f"  ->  {r['sgvt_sans']} « {r['classe_sans']} »")
            print(f"     ce qui bouge : {r['ce_qui_bouge']}")

    ecrire_csv(OUT / "C_impact.csv",
               ["jeu", "point", "n_signalees", "espece", "P_fraie_tel_quel",
                "P_fraie_sans", "n_aigu_tel_quel", "n_aigu_sans",
                "cat_aigu_tel_quel", "cat_aigu_sans", "pct_chr_tel_quel",
                "pct_chr_sans", "m_tel_quel", "m_sans", "sgvt_tel_quel",
                "sgvt_sans", "classe_tel_quel", "classe_sans", "ce_qui_bouge"],
               lignes, tri=["jeu", "point"])
    n = sum(1 for l in lignes if l["ce_qui_bouge"] != "rien")
    print("\n" + "=" * 78)
    print(f"  points chiffres            : {len(lignes)}")
    print(f"  dont un indicateur bougerait : {n}")
    print("  RAPPEL : rien n'est pose. C'est un chiffrage de ce qui est en jeu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
