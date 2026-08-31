"""
mesure_cout_verdict.py — ETAPE 18 : ce que le marquage a change AU VERDICT.

Ni correctif ni regle : deux rejeux du meme point, detecteur allume puis eteint,
et la difference lue sur les grandeurs publiees. C'est le chiffrage exact de ce
que la question du commanditaire met en jeu — « un faux positif RETIRE UNE
ALERTE REELLE d'un document remis a un maitre d'ouvrage ».

Porte sur les points ou au moins une journee marquee franchissait un seuil
piscicole : ailleurs, par construction, le marquage ne coute aucun verdict.
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

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f       # noqa: E402

import build_reference                                                 # noqa: E402
from thermie_debits import orchestrator                                # noqa: E402

OUT = RACINE / "out" / "etape18"


def _lire(res):
    v = res.vulnerabilite or {}
    s = res.sensibilite or {}
    sg = getattr(res, "sgvt", None) or {}
    return dict(
        pct_chr=v.get("pct_chr"), cat_chr=v.get("cat_chr"),
        n_aigu=v.get("n_aigu"), cat_aigu=v.get("cat_aigu"),
        n_total_tmh=v.get("n_total_tmh"), n_total_tmax=v.get("n_total_tmax"),
        m=s.get("m"), validite=s.get("validite"),
        sgvt=sg.get("sgvt") if isinstance(sg, dict) else None,
        classe=sg.get("interp") if isinstance(sg, dict) else None,
        composantes=sg.get("composantes") if isinstance(sg, dict) else None)


def main():
    src = OUT / "A_sous_ensemble.csv"
    cand = pd.read_csv(src, sep=";", encoding="utf-8")
    besoin = set(zip(cand["jeu"], cand["point"]))
    print("=" * 78)
    print("CE QUE LE MARQUAGE A CHANGE AU VERDICT")
    print("detecteur ALLUME (livre) contre detecteur ETEINT (contrefactuel)")
    print("=" * 78)

    lignes = []
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            if (jeu["jeu"], pt) not in besoin:
                continue
            res = {}
            for etat, flag in (("allume", True), ("eteint", False)):
                cfg = build_reference.construire_config(jeu, point_rel,
                                                        "application")
                cfg.qc.hors_eau = flag
                with contextlib.redirect_stdout(_io.StringIO()), \
                     contextlib.redirect_stderr(_io.StringIO()):
                    res[etat] = _lire(orchestrator.run(cfg, verbose=False))
            a, e = res["allume"], res["eteint"]
            n = int(((cand.jeu == jeu["jeu"]) & (cand.point == pt)).sum())
            lignes.append(dict(
                jeu=jeu["jeu"], point=pt, journees_instruites=n,
                pct_chr_allume=_f(a["pct_chr"]), pct_chr_eteint=_f(e["pct_chr"]),
                cat_chr_allume=a["cat_chr"], cat_chr_eteint=e["cat_chr"],
                n_aigu_allume=a["n_aigu"], n_aigu_eteint=e["n_aigu"],
                cat_aigu_allume=a["cat_aigu"], cat_aigu_eteint=e["cat_aigu"],
                sgvt_allume=_f(a["sgvt"]), sgvt_eteint=_f(e["sgvt"]),
                classe_allume=a["classe"], classe_eteint=e["classe"],
                m_allume=_f(a["m"]), m_eteint=_f(e["m"]),
                verdict_deplace=("OUI" if (a["cat_chr"] != e["cat_chr"]
                                           or a["cat_aigu"] != e["cat_aigu"]
                                           or a["classe"] != e["classe"])
                                 else "non")))
            r = lignes[-1]
            print(f"\n  {pt}   ({n} journee(s) instruite(s))")
            print(f"     chronique  {r['pct_chr_eteint']}% « {r['cat_chr_eteint']} »"
                  f"   ->   {r['pct_chr_allume']}% « {r['cat_chr_allume']} »")
            print(f"     aigu       {r['n_aigu_eteint']}j « {r['cat_aigu_eteint']} »"
                  f"   ->   {r['n_aigu_allume']}j « {r['cat_aigu_allume']} »")
            print(f"     SGVT       {r['sgvt_eteint']} « {r['classe_eteint']} »"
                  f"   ->   {r['sgvt_allume']} « {r['classe_allume']} »")
            print(f"     verdict deplace : {r['verdict_deplace']}")

    ecrire_csv(OUT / "E_cout_verdict.csv",
               ["jeu", "point", "journees_instruites", "pct_chr_eteint",
                "pct_chr_allume", "cat_chr_eteint", "cat_chr_allume",
                "n_aigu_eteint", "n_aigu_allume", "cat_aigu_eteint",
                "cat_aigu_allume", "sgvt_eteint", "sgvt_allume",
                "classe_eteint", "classe_allume", "m_eteint", "m_allume",
                "verdict_deplace"],
               lignes, tri=["jeu", "point"])
    n_dep = sum(1 for l in lignes if l["verdict_deplace"] == "OUI")
    print("\n" + "=" * 78)
    print(f"  points instruits          : {len(lignes)}")
    print(f"  dont le verdict se deplace : {n_dep}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
