"""
comparer_schemas.py — comparer deux dossiers d'artefacts DONT LE SCHEMA DIFFERE.

POURQUOI CE MODULE
-------------------
`check_reference.py` diffe des fichiers. Quand le HARNAIS a gagne des colonnes
entre le moment ou une reference a ete figee et aujourd'hui, ce diff ne peut
pas etre vide — et il ne dit rien de ce qu'on veut savoir : les valeurs qui
existaient des deux cotes ont-elles bouge ?

C'est la methode de la tache B4 de l'etape 6, generalisee a deux dossiers
quelconques : comparer **colonne par colonne, sur les seules colonnes communes
aux deux schemas**. Ce qui est nouveau est declare comme nouveau ; ce qui
existait des deux cotes doit etre identique, valeur par valeur.

Melanger un changement de code et un changement de schema du harnais produit
un diff dont on ne peut rien conclure. Ce module les separe.

  · CSV        colonnes communes, lignes appariees sur les colonnes de cle
  · JSON       cles communes, comparees recursivement
  · 99_log.txt traite a part : il porte le chemin du code, que D36 neutralise

USAGE
    python tests/reference/comparer_schemas.py AVANT APRES --sortie X.csv

CODE DE RETOUR
    0  aucune valeur divergente sur les colonnes communes
    1  au moins une
    2  erreur d'usage
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from _commun import RACINE, ecrire_csv, est_artefact

# Colonnes de cle par artefact : ce qui identifie une ligne. Reprises de
# l'ordre de tri employe a l'ecriture par build_reference.
CLES = {
    "02_effectifs.csv": ["point", "annee"],
    "03_journees_ecartees.csv": ["point", "date", "etape", "motif"],
    "04_normales.csv": ["point", "mois", "jour"],
    "05_anomalies.csv": ["point", "date"],
    "06_coefficients.csv": ["point", "grandeur", "diagnostic"],
    "07_t_norm.csv": ["point", "grandeur", "date"],
    "08_scores.csv": ["point", "indicateur"],
}


def aplatir(o, prefixe=""):
    plat = {}
    if isinstance(o, dict):
        for k, v in o.items():
            plat.update(aplatir(v, f"{prefixe}.{k}" if prefixe else str(k)))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            plat.update(aplatir(v, f"{prefixe}[{i}]"))
    else:
        plat[prefixe] = o
    return plat


def comparer_csv(pa: Path, pb: Path, nom: str):
    a = pd.read_csv(pa, sep=";", dtype=str, keep_default_na=False)
    b = pd.read_csv(pb, sep=";", dtype=str, keep_default_na=False)
    communes = [c for c in a.columns if c in b.columns]
    nouvelles = [c for c in b.columns if c not in a.columns]
    disparues = [c for c in a.columns if c not in b.columns]

    cle = [c for c in CLES.get(nom, []) if c in communes]
    if cle:
        a = a.sort_values(cle, kind="mergesort").reset_index(drop=True)
        b = b.sort_values(cle, kind="mergesort").reset_index(drop=True)

    res = dict(lignes_avant=len(a), lignes_apres=len(b),
               colonnes_communes=len(communes),
               colonnes_nouvelles=" ".join(nouvelles) or "-",
               colonnes_disparues=" ".join(disparues) or "-")
    if len(a) != len(b):
        res.update(verdict="NOMBRE DE LIGNES DIFFERENT",
                   colonnes_divergentes="(comparaison impossible)",
                   valeurs_divergentes=-1, valeurs_confrontees=0)
        return res

    divergentes, n_val = [], 0
    for c in communes:
        neq = (a[c] != b[c])
        if neq.any():
            divergentes.append(f"{c}({int(neq.sum())})")
            n_val += int(neq.sum())
    res.update(
        verdict="IDENTIQUE sur les colonnes communes" if not divergentes
                else "DIVERGENT",
        colonnes_divergentes=" ".join(divergentes) or "-",
        valeurs_divergentes=n_val,
        valeurs_confrontees=len(communes) * len(a))
    return res


def comparer_json(pa: Path, pb: Path):
    a = aplatir(json.loads(pa.read_text(encoding="utf-8")))
    b = aplatir(json.loads(pb.read_text(encoding="utf-8")))
    communes = [k for k in a if k in b]
    div = [k for k in communes if a[k] != b[k]]
    return dict(lignes_avant=len(a), lignes_apres=len(b),
                colonnes_communes=len(communes),
                colonnes_nouvelles=" ".join(k for k in b if k not in a)[:300] or "-",
                colonnes_disparues=" ".join(k for k in a if k not in b)[:300] or "-",
                verdict="IDENTIQUE sur les cles communes" if not div
                        else "DIVERGENT",
                colonnes_divergentes=" ".join(div)[:300] or "-",
                valeurs_divergentes=len(div),
                valeurs_confrontees=len(communes))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("avant")
    ap.add_argument("apres")
    ap.add_argument("--sortie", default=None)
    ap.add_argument("--titre", default="COMPARAISON A SCHEMAS DIFFERENTS")
    args = ap.parse_args()

    avant, apres = Path(args.avant).resolve(), Path(args.apres).resolve()
    for d in (avant, apres):
        if not d.is_dir():
            print(f"dossier introuvable : {d}", file=sys.stderr)
            return 2

    lignes, logs, absents = [], [], []
    for jeu in sorted(p.name for p in apres.iterdir() if p.is_dir()):
        for f in sorted((apres / jeu).iterdir()):
            rel = f"{jeu}/{f.name}"
            if not (f.is_file() and est_artefact(rel)):
                continue
            av = avant / jeu / f.name
            if not av.exists():
                absents.append(rel)
                continue
            if f.suffix == ".csv":
                r = comparer_csv(av, f, f.name)
            elif f.suffix == ".json":
                r = comparer_json(av, f)
            else:
                ta = av.read_text(encoding="utf-8")
                tb = f.read_text(encoding="utf-8")
                logs.append(dict(artefact=rel, identique=(ta == tb),
                                 lignes_avant=len(ta.splitlines()),
                                 lignes_apres=len(tb.splitlines())))
                continue
            r["artefact"] = rel
            lignes.append(r)

    base = Path(args.sortie) if args.sortie else \
        RACINE / "out" / "comparaison_schemas.csv"
    base.parent.mkdir(parents=True, exist_ok=True)
    ecrire_csv(base,
               ["artefact", "lignes_avant", "lignes_apres", "colonnes_communes",
                "valeurs_confrontees", "colonnes_nouvelles", "colonnes_disparues",
                "verdict", "colonnes_divergentes", "valeurs_divergentes"],
               lignes, tri=["artefact"])
    ecrire_csv(base.with_name(base.stem + "_logs.csv"),
               ["artefact", "identique", "lignes_avant", "lignes_apres"],
               logs, tri=["artefact"])

    div = [l for l in lignes if not l["verdict"].startswith("IDENTIQUE")]
    print("=" * 74)
    print(args.titre)
    print("=" * 74)
    print(f"  avant : {avant}")
    print(f"  apres : {apres}")
    print(f"\n  artefacts compares (hors 99_log)      : {len(lignes)}")
    print(f"  identiques sur les colonnes communes  : {len(lignes) - len(div)}")
    print(f"  DIVERGENTS                            : {len(div)}")
    print(f"  colonnes communes confrontees (total) : "
          f"{sum(l['colonnes_communes'] for l in lignes)}")
    print(f"  VALEURS confrontees (total)           : "
          f"{sum(l['valeurs_confrontees'] for l in lignes)}")
    print(f"  VALEURS DIVERGENTES (total)           : "
          f"{sum(max(l['valeurs_divergentes'], 0) for l in lignes)}")
    for l in div:
        print(f"    - {l['artefact']} : {l['verdict']} "
              f"[{l['colonnes_divergentes']}]")

    nouv = sorted({c for l in lignes for c in l["colonnes_nouvelles"].split()
                   if c != "-"})
    disp = sorted({c for l in lignes for c in l["colonnes_disparues"].split()
                   if c != "-"})
    print(f"\n  colonnes AJOUTEES par le schema d'apres ({len(nouv)}) :")
    for c in nouv:
        print(f"      + {c}")
    print(f"  colonnes DISPARUES ({len(disp)}) : "
          f"{', '.join(disp) if disp else 'aucune'}")
    if absents:
        print(f"\n  artefacts absents du dossier d'avant : {len(absents)}")
        for a_ in absents:
            print(f"      + {a_}")
    n_log_ok = sum(1 for l in logs if l["identique"])
    print(f"\n  99_log.txt : {n_log_ok}/{len(logs)} identiques au bit pres")
    for l in logs:
        if not l["identique"]:
            print(f"      - {l['artefact']} : {l['lignes_avant']} -> "
                  f"{l['lignes_apres']} lignes")
    return 1 if div else 0


if __name__ == "__main__":
    sys.exit(main())
