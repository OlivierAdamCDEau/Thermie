"""
verifier_classeurs.py — ÉTAPE 2, TÂCHE B : critère d'acceptation.

Confronte la référence reconstruite (chemin application) aux valeurs lues dans
les classeurs livrables déjà présents dans tests/reference/<jeu>/. Ces
classeurs sont la seule trace du chemin de paramètres de l'application (D11) :
s'ils ne sont pas retrouvés, la reconstruction n'est pas la bonne.

Rien n'est arrondi pour faire coïncider : l'écart, s'il subsiste, est chiffré
tel quel.

Sortie : out/etape2/verification_classeurs.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from _commun import ICI, RACINE, ecrire_csv
from parametres import ATTENDU_CLASSEUR

OUT = RACINE / "out" / "etape2"

# Tolérance de LECTURE, pas de calcul : les classeurs arrondissent m à quatre
# décimales et R² à quatre décimales. Un écart inférieur au demi-dernier
# chiffre affiché n'est pas un écart, c'est l'arrondi du livrable.
TOL = {"m": 5e-5, "r2": 5e-5, "robustesse": 5e-5, "sgvt": 5e-3}


def lire_reference(jeu: str, racine: Path):
    """Ce que la référence reconstruite dit, pour le point unique du jeu."""
    d = racine / jeu
    eff = pd.read_csv(d / "02_effectifs.csv", sep=";") if (d / "02_effectifs.csv").exists() else pd.DataFrame()
    coef = pd.read_csv(d / "06_coefficients.csv", sep=";") if (d / "06_coefficients.csv").exists() else pd.DataFrame()
    sc = pd.read_csv(d / "08_scores.csv", sep=";", dtype=str,
                     keep_default_na=False) if (d / "08_scores.csv").exists() else pd.DataFrame()
    out = {}
    if len(eff):
        t = eff[eff.annee == -1].iloc[0]
        out["journees_lues"] = int(t.journees_lues)
        out["journees_ecartees_qc"] = int(t.journees_ecartees_qc)
        out["journees_propres"] = int(t.journees_lues) - int(t.journees_ecartees_qc)
        out["journees_retenues"] = int(t.journees_retenues_apres_fusion)
    if len(coef):
        m = coef[coef.grandeur == "m_estival"]
        if len(m):
            r = m.iloc[0]
            out["m"] = float(r.m)
            out["r2"] = float(r.r2)
            out["n_ete"] = int(r.n)
            out["robustesse"] = float(r.robustesse)
    if len(sc):
        g = sc[sc.indicateur == "sgvt"]
        if len(g) and g.iloc[0].valeur:
            out["sgvt"] = float(g.iloc[0].valeur)
        c = sc[sc.indicateur == "sgvt_composantes"]
        if len(c) and c.iloc[0].valeur:
            out["composantes"] = int(float(c.iloc[0].valeur))
    return out


LIB = {
    "journees_lues": "journees brutes lues",
    "journees_ecartees_qc": "journees ecartees par le controle qualite",
    "journees_propres": "journees retenues apres controle qualite",
    "journees_retenues": "journees retenues apres jointure eau x air",
    "m": "coefficient m estival",
    "r2": "R2 de la regression air-eau",
    "n_ete": "jours estivaux de la regression",
    "robustesse": "indice de robustesse |rho - r|",
    "sgvt": "SGVT /10 (hors perimetre, temoin)",
    "composantes": "nombre de composantes du SGVT (temoin)",
}

COLS = ["jeu", "grandeur", "libelle", "attendu_classeur", "obtenu_harnais",
        "ecart", "verdict"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    racine = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ICI
    lignes, n_ko = [], 0
    for jeu, att in sorted(ATTENDU_CLASSEUR.items()):
        obt = lire_reference(jeu, racine)
        for cle, va in att.items():
            vo = obt.get(cle)
            if vo is None:
                verdict, ecart = "MANQUANT — le harnais ne produit pas cette valeur", ""
                n_ko += 1
            else:
                e = float(vo) - float(va)
                tol = TOL.get(cle, 0.0)
                if abs(e) <= tol:
                    verdict = ("retrouve" if tol == 0 else
                               f"retrouve (ecart {abs(e):.2e} <= arrondi du livrable)")
                else:
                    verdict = "ECART"
                    n_ko += 1
                ecart = f"{e:+.6f}" if isinstance(va, float) else f"{int(e):+d}"
            lignes.append(dict(jeu=jeu, grandeur=cle, libelle=LIB.get(cle, ""),
                               attendu_classeur=va, obtenu_harnais=vo,
                               ecart=ecart, verdict=verdict))
    ecrire_csv(OUT / "verification_classeurs.csv", COLS, lignes,
               tri=["jeu", "grandeur"])
    n = len(lignes)
    print(f"verification_classeurs.csv : {n} confrontations, "
          f"{n - n_ko} retrouvees, {n_ko} en ecart")
    for l in lignes:
        if l["verdict"].startswith(("ECART", "MANQUANT")):
            print(f"   {l['jeu']:>18} {l['grandeur']:<22} "
                  f"attendu={l['attendu_classeur']} obtenu={l['obtenu_harnais']} "
                  f"ecart={l['ecart']}")
    return 1 if n_ko else 0


if __name__ == "__main__":
    sys.exit(main())
