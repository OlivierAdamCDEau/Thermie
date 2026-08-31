"""
mesurer_effet_correctif2.py — ÉTAPE 6, TÂCHE C.

`check_reference.py` dit QUELS artefacts bougent. Ce module dit DE COMBIEN, et
confronte le résultat à la liste d'artefacts déclarée par la commande d'étape.

Il compare la référence figée (`tests/reference/`, produite par `ref/v4_5/`) au
rejeu conservé du code corrigé (`out/etape6/rejeu_correctif2/`). Il ne touche
ni l'une ni l'autre.

Sortie :
  out/etape6/C_artefacts_bilan.csv     un artefact par ligne, declare vs constate
  out/etape6/C_ecarts_valeurs.csv      par colonne numerique : combien, de combien
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from _commun import ICI, RACINE, ecrire_csv, sha256, _f

REJEU = RACINE / "out" / "etape6" / "rejeu_correctif2"
OUT = RACINE / "out" / "etape6"

# Ce que la commande d'étape déclare, artefact par artefact.
DECLARE = {
    "00_format_detecte.json": "fige",
    "01_colonnes_retenues.json": "fige",
    "02_effectifs.csv": "fige",
    "03_journees_ecartees.csv": "fige",
    "04_normales.csv": "fige",
    "05_anomalies.csv": "doit bouger",
    "06_coefficients.csv": "doit bouger",
    "07_t_norm.csv": "doit bouger",
    "08_scores.csv": "doit bouger (ricochet)",
    "10_parametres.json": "fige (sauf si min_periods devient parametre)",
    "99_log.txt": "non declare",
}

CLES = {
    "02_effectifs.csv": ["point", "annee"],
    "03_journees_ecartees.csv": ["point", "date"],
    "04_normales.csv": ["point", "doy"],
    "05_anomalies.csv": ["point", "date"],
    "06_coefficients.csv": ["point", "grandeur", "diagnostic"],
    "07_t_norm.csv": ["point", "grandeur", "date"],
    "08_scores.csv": ["point", "indicateur"],
}


def num(serie):
    return pd.to_numeric(serie, errors="coerce")


def main():
    if not REJEU.exists():
        print(f"rejeu absent : {REJEU}", file=sys.stderr)
        return 2

    bilan, ecarts = [], []
    for jeu in sorted(p.name for p in ICI.iterdir() if p.is_dir()):
        for f in sorted((ICI / jeu).iterdir()):
            if f.name not in DECLARE:
                continue
            g = REJEU / jeu / f.name
            if not g.exists():
                continue
            bouge = sha256(f) != sha256(g)
            ligne = dict(jeu=jeu, artefact=f.name,
                         declare=DECLARE[f.name],
                         constate="BOUGE" if bouge else "fige",
                         accord="", valeurs_changees=0, colonnes_changees="",
                         lignes_retirees=0, lignes_ajoutees=0)

            if bouge and f.suffix == ".csv":
                a = pd.read_csv(f, sep=";", dtype=str, keep_default_na=False)
                b = pd.read_csv(g, sep=";", dtype=str, keep_default_na=False)
                cle = [c for c in CLES.get(f.name, []) if c in a.columns]
                # Les lignes sont appariees par leur CLE, jamais par leur rang :
                # le correctif 2 peut faire disparaitre des lignes (une journee
                # qui perd Tmh perd Tmh_norm), et un appariement positionnel
                # comparerait alors des lignes sans rapport.
                if cle:
                    a = a.set_index(cle)
                    b = b.set_index(cle)
                    communes = a.index.intersection(b.index)
                    ligne["lignes_retirees"] = int(len(a.index.difference(b.index)))
                    ligne["lignes_ajoutees"] = int(len(b.index.difference(a.index)))
                    a, b = a.loc[communes], b.loc[communes]
                cols, n_tot = [], 0
                for c in [c for c in a.columns if c in b.columns]:
                    if len(a) != len(b):
                        continue
                    neq = (a[c] != b[c]).to_numpy()
                    if not neq.any():
                        continue
                    cols.append(c)
                    n_tot += int(neq.sum())
                    xa, xb = num(a[c]).to_numpy(), num(b[c]).to_numpy()
                    d = np.abs(xb - xa)
                    fini = np.isfinite(d) & neq
                    perdues = int((neq & ~pd.isna(xa) & pd.isna(xb)).sum())
                    ecarts.append(dict(
                        jeu=jeu, artefact=f.name, colonne=c,
                        lignes=len(a), valeurs_changees=int(neq.sum()),
                        part_pct=_f(100.0 * neq.sum() / max(len(a), 1)),
                        valeurs_devenues_vides=perdues,
                        ecart_median=_f(float(np.median(d[fini])) if fini.any() else np.nan),
                        ecart_max=_f(float(d[fini].max()) if fini.any() else np.nan)))
                ligne["valeurs_changees"] = n_tot
                ligne["colonnes_changees"] = " ".join(cols)

            d = DECLARE[f.name]
            if d == "non declare":
                ligne["accord"] = "-"
            elif d.startswith("fige"):
                ligne["accord"] = "CONFORME" if not bouge else "ECART A LA DECLARATION"
            else:
                ligne["accord"] = "CONFORME" if bouge else "ECART A LA DECLARATION"
            bilan.append(ligne)

    ecrire_csv(OUT / "C_artefacts_bilan.csv",
               ["jeu", "artefact", "declare", "constate", "accord",
                "lignes_retirees", "lignes_ajoutees",
                "valeurs_changees", "colonnes_changees"],
               bilan, tri=["jeu", "artefact"])
    ecrire_csv(OUT / "C_ecarts_valeurs.csv",
               ["jeu", "artefact", "colonne", "lignes", "valeurs_changees",
                "part_pct", "valeurs_devenues_vides", "ecart_median", "ecart_max"],
               ecarts, tri=["artefact", "jeu", "colonne"])

    print("=" * 74)
    print("EFFET DU CORRECTIF 2 SUR LES 66 ARTEFACTS")
    print("=" * 74)
    b = sum(1 for l in bilan if l["constate"] == "BOUGE")
    print(f"  artefacts examines : {len(bilan)}")
    print(f"  qui bougent        : {b}")
    print(f"  figes              : {len(bilan)-b}")
    dev = [l for l in bilan if l["accord"] == "ECART A LA DECLARATION"]
    print(f"  ECARTS A LA DECLARATION : {len(dev)}")
    for l in dev:
        print(f"    - {l['jeu']}/{l['artefact']} : declare « {l['declare']} », "
              f"constate « {l['constate']} »")
    print("\n  Par artefact :")
    for nom in DECLARE:
        ls = [l for l in bilan if l["artefact"] == nom]
        nb = sum(1 for l in ls if l["constate"] == "BOUGE")
        print(f"    {nom:<28} {nb}/{len(ls)} bougent   "
              f"[declare : {DECLARE[nom]}]")
    print("\n  Ecarts de valeurs les plus larges :")
    for e in sorted(ecarts, key=lambda x: -(x["ecart_max"] or 0))[:10]:
        print(f"    {e['jeu']}/{e['artefact']}::{e['colonne']:<14} "
              f"{e['valeurs_changees']:>5} valeur(s) ({e['part_pct']:.2f} %), "
              f"median {e['ecart_median']}, max {e['ecart_max']}, "
              f"vidées {e['valeurs_devenues_vides']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
