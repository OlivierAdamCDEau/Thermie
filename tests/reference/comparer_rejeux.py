"""
comparer_rejeux.py — comparer DEUX rejeux entre eux, artefact par artefact.

POURQUOI CE MODULE PLUTOT QUE check_reference
----------------------------------------------
`check_reference.py` compare un rejeu à la référence figée, qui est l'état
V4.5. Depuis l'étape 6, `app/` porte plusieurs correctifs : comparer à V4.5
mesure leur effet CUMULÉ, jamais l'effet du dernier. Pour isoler un correctif,
il faut comparer le rejeu d'après au rejeu d'avant — et c'est ce que fait ce
module.

Les lignes sont appariées par leur CLÉ, jamais par leur rang : un correctif
peut faire disparaître ou apparaître des lignes, et un appariement positionnel
comparerait alors des lignes sans rapport.

USAGE
    python tests/reference/comparer_rejeux.py AVANT APRES --sortie X.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from _commun import RACINE, ecrire_csv, sha256, _f

CLES = {
    "02_effectifs.csv": ["point", "annee"],
    "03_journees_ecartees.csv": ["point", "date"],
    "04_normales.csv": ["point", "mois", "jour"],
    "05_anomalies.csv": ["point", "date"],
    "06_coefficients.csv": ["point", "grandeur", "diagnostic"],
    "07_t_norm.csv": ["point", "grandeur", "date"],
    "08_scores.csv": ["point", "indicateur"],
}


def num(s):
    return pd.to_numeric(s, errors="coerce")


def comparer(avant: Path, apres: Path):
    bilan, ecarts = [], []
    for jeu in sorted(p.name for p in apres.iterdir() if p.is_dir()):
        for f in sorted((apres / jeu).iterdir()):
            g = avant / jeu / f.name
            if not g.exists():
                bilan.append(dict(jeu=jeu, artefact=f.name,
                                  constate="NOUVEAU", lignes_retirees=0,
                                  lignes_ajoutees=0, valeurs_changees=0,
                                  colonnes_changees="", colonnes_nouvelles=""))
                continue
            if sha256(f) == sha256(g):
                bilan.append(dict(jeu=jeu, artefact=f.name, constate="fige",
                                  lignes_retirees=0, lignes_ajoutees=0,
                                  valeurs_changees=0, colonnes_changees="",
                                  colonnes_nouvelles=""))
                continue

            l = dict(jeu=jeu, artefact=f.name, constate="BOUGE",
                     lignes_retirees=0, lignes_ajoutees=0,
                     valeurs_changees=0, colonnes_changees="",
                     colonnes_nouvelles="")
            if f.suffix == ".csv":
                a = pd.read_csv(g, sep=";", dtype=str, keep_default_na=False)
                b = pd.read_csv(f, sep=";", dtype=str, keep_default_na=False)
                l["colonnes_nouvelles"] = " ".join(
                    c for c in b.columns if c not in a.columns) or "-"
                cle = [c for c in CLES.get(f.name, []) if c in a.columns
                       and c in b.columns]
                # Une cle declaree mais ABSENTE du fichier faisait retomber la
                # comparaison en positionnel, et le decompte de valeurs a zero
                # quand les longueurs differaient : un artefact pouvait bouger
                # sans qu'aucune valeur ne soit rapportee. Le silence est
                # desormais impossible.
                if CLES.get(f.name) and len(cle) != len(CLES[f.name]):
                    l["colonnes_changees"] = ("CLE ABSENTE : "
                                              + " ".join(CLES[f.name]))
                if cle:
                    a2, b2 = a.set_index(cle), b.set_index(cle)
                    communes = a2.index.intersection(b2.index)
                    l["lignes_retirees"] = int(len(a2.index.difference(b2.index)))
                    l["lignes_ajoutees"] = int(len(b2.index.difference(a2.index)))
                    a2, b2 = a2.loc[communes], b2.loc[communes]
                else:
                    a2, b2 = a, b
                cols, n_tot = [], 0
                if len(a2) != len(b2):
                    l["colonnes_changees"] = (
                        l["colonnes_changees"]
                        or "lignes non appariables — voir lignes_retirees")
                if len(a2) == len(b2):
                    for c in [c for c in a2.columns if c in b2.columns]:
                        neq = (a2[c] != b2[c]).to_numpy()
                        if not neq.any():
                            continue
                        cols.append(c)
                        n_tot += int(neq.sum())
                        xa, xb = num(a2[c]).to_numpy(), num(b2[c]).to_numpy()
                        d = np.abs(xb - xa)
                        fini = np.isfinite(d) & neq
                        ecarts.append(dict(
                            jeu=jeu, artefact=f.name, colonne=c,
                            lignes=len(a2), valeurs_changees=int(neq.sum()),
                            part_pct=_f(100.0 * neq.sum() / max(len(a2), 1)),
                            ecart_median=_f(float(np.median(d[fini]))
                                            if fini.any() else np.nan),
                            ecart_max=_f(float(d[fini].max())
                                         if fini.any() else np.nan)))
                l["valeurs_changees"] = n_tot
                l["colonnes_changees"] = " ".join(cols) or "-"
            else:
                ta = g.read_text(encoding="utf-8").splitlines()
                tb = f.read_text(encoding="utf-8").splitlines()
                l["lignes_retirees"] = max(0, len(ta) - len(tb))
                l["lignes_ajoutees"] = max(0, len(tb) - len(ta))
                l["valeurs_changees"] = sum(
                    1 for x, y in zip(ta, tb) if x != y)
                l["colonnes_changees"] = "(texte)"
            bilan.append(l)
    return bilan, ecarts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("avant")
    ap.add_argument("apres")
    ap.add_argument("--sortie", default=None)
    ap.add_argument("--titre", default="COMPARAISON DE DEUX REJEUX")
    args = ap.parse_args()

    avant, apres = Path(args.avant).resolve(), Path(args.apres).resolve()
    bilan, ecarts = comparer(avant, apres)
    base = Path(args.sortie) if args.sortie else \
        RACINE / "out" / "etape7" / "comparaison_rejeux.csv"
    base.parent.mkdir(parents=True, exist_ok=True)
    ecrire_csv(base,
               ["jeu", "artefact", "constate", "lignes_retirees",
                "lignes_ajoutees", "valeurs_changees", "colonnes_changees",
                "colonnes_nouvelles"],
               bilan, tri=["jeu", "artefact"])
    ecrire_csv(base.with_name(base.stem + "_valeurs.csv"),
               ["jeu", "artefact", "colonne", "lignes", "valeurs_changees",
                "part_pct", "ecart_median", "ecart_max"],
               ecarts, tri=["artefact", "jeu", "colonne"])

    print("=" * 74)
    print(args.titre)
    print("=" * 74)
    print(f"  avant : {avant}")
    print(f"  apres : {apres}")

    # ETAPE 14 — un outil qui n'a RIEN lu ne doit pas repondre « rien n'a
    # bouge ». Le zero est un resultat, l'absence de resultat n'en est pas un
    # (etape 10) : la garde posee alors protegeait d'une CLE absente dans un
    # artefact, pas d'un CORPUS absent. Un rejeu qui echoue laisse un dossier
    # vide, et le comparateur rendait « 0 compares, 0 bougent, retour 0 ».
    if not bilan:
        print("\n  ARRET — AUCUN artefact compare.")
        print("  Un dossier est vide ou ne porte aucun jeu. Ce n'est pas un")
        print("  verdict de non-regression : c'est l'absence de mesure.")
        return 2

    b = [l for l in bilan if l["constate"] == "BOUGE"]
    print(f"\n  artefacts compares : {len(bilan)}")
    print(f"  figes              : {sum(1 for l in bilan if l['constate']=='fige')}")
    print(f"  qui bougent        : {len(b)}")
    print(f"  nouveaux           : "
          f"{sum(1 for l in bilan if l['constate']=='NOUVEAU')}")
    print("\n  Par artefact :")
    noms = sorted({l["artefact"] for l in bilan})
    for n in noms:
        ls = [l for l in bilan if l["artefact"] == n]
        nb = sum(1 for l in ls if l["constate"] == "BOUGE")
        etat = "FIGE" if nb == 0 else f"{nb}/{len(ls)} bougent"
        print(f"    {n:<28} {etat}")
    if b:
        print("\n  Detail :")
        for l in b:
            print(f"    {l['jeu']}/{l['artefact']} : "
                  f"-{l['lignes_retirees']} / +{l['lignes_ajoutees']} ligne(s), "
                  f"{l['valeurs_changees']} valeur(s) [{l['colonnes_changees']}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
