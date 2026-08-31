"""
comparer_cli_avant_apres.py — ÉTAPE 6, TÂCHE B4.

`tests/reference_cli/` a été figé AVANT que le harnais ne gagne
`10_parametres.json` et la colonne `sortie_v45`. Une comparaison d'empreintes
entre l'ancien dossier et le nouveau mélangerait donc deux choses : un
changement de CODE (celui qu'on veut mesurer) et un changement de SCHÉMA DU
HARNAIS (celui qu'on ne veut pas mesurer). Elle ne prouverait rien.

Ce module compare donc **colonne par colonne, sur les seules colonnes communes
aux deux schémas**. Ce qui est nouveau est déclaré comme nouveau ; ce qui
existait des deux côtés doit être identique, valeur par valeur.

  · CSV  : colonnes communes, lignes alignées sur les colonnes de clé
  · JSON : clés communes, comparées récursivement
  · 99_log.txt : traité à part — il porte le chemin du code, que D36 neutralise

USAGE
    python tests/reference/comparer_cli_avant_apres.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from _commun import RACINE, ecrire_csv

AVANT = RACINE / "out" / "etape6" / "reference_cli_avant"
APRES = RACINE / "tests" / "reference_cli"
OUT = RACINE / "out" / "etape6"

# Colonnes de clé par artefact : ce qui identifie une ligne. Reprises de
# l'ordre de tri employé à l'écriture par build_reference.
CLES = {
    "02_effectifs.csv": ["point", "annee"],
    "03_journees_ecartees.csv": ["point", "date"],
    "04_normales.csv": ["point", "doy"],
    "05_anomalies.csv": ["point", "date"],
    "06_coefficients.csv": ["point", "grandeur", "diagnostic"],
    "07_t_norm.csv": ["point", "grandeur", "date"],
    "08_scores.csv": ["point", "indicateur"],
}


def aplatir(o, prefixe=""):
    """Un JSON imbriqué, ramené à un dictionnaire plat chemin -> valeur."""
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

    res = dict(artefact=nom, lignes_avant=len(a), lignes_apres=len(b),
               colonnes_communes=len(communes),
               colonnes_nouvelles=" ".join(nouvelles) or "-",
               colonnes_disparues=" ".join(disparues) or "-")
    if len(a) != len(b):
        res.update(verdict="NOMBRE DE LIGNES DIFFERENT",
                   colonnes_divergentes="(comparaison impossible)",
                   valeurs_divergentes=-1)
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
        valeurs_divergentes=n_val)
    return res


def comparer_json(pa: Path, pb: Path, nom: str):
    a = aplatir(json.loads(pa.read_text(encoding="utf-8")))
    b = aplatir(json.loads(pb.read_text(encoding="utf-8")))
    communes = [k for k in a if k in b]
    div = [k for k in communes if a[k] != b[k]]
    return dict(artefact=nom, lignes_avant=len(a), lignes_apres=len(b),
                colonnes_communes=len(communes),
                colonnes_nouvelles=" ".join(k for k in b if k not in a)[:200] or "-",
                colonnes_disparues=" ".join(k for k in a if k not in b)[:200] or "-",
                verdict="IDENTIQUE sur les cles communes" if not div else "DIVERGENT",
                colonnes_divergentes=" ".join(div)[:200] or "-",
                valeurs_divergentes=len(div))


def main():
    if not AVANT.exists():
        print(f"instantane absent : {AVANT}", file=sys.stderr)
        return 2

    lignes, nouveaux, logs = [], [], []
    for jeu in sorted(p.name for p in APRES.iterdir() if p.is_dir()):
        for f in sorted((APRES / jeu).iterdir()):
            rel = f"{jeu}/{f.name}"
            av = AVANT / jeu / f.name
            if not av.exists():
                nouveaux.append(rel)
                continue
            if f.suffix == ".csv":
                r = comparer_csv(av, f, f.name)
            elif f.suffix == ".json":
                r = comparer_json(av, f, f.name)
            else:
                ta, tb = av.read_text(encoding="utf-8"), f.read_text(encoding="utf-8")
                logs.append(dict(artefact=rel, identique=(ta == tb),
                                 lignes_avant=len(ta.splitlines()),
                                 lignes_apres=len(tb.splitlines()),
                                 lignes_avec_CODE=sum(
                                     1 for l in tb.splitlines() if "<CODE>/" in l)))
                continue
            r["artefact"] = rel
            lignes.append(r)

    ecrire_csv(OUT / "B4_invariance_cli.csv",
               ["artefact", "lignes_avant", "lignes_apres", "colonnes_communes",
                "colonnes_nouvelles", "colonnes_disparues", "verdict",
                "colonnes_divergentes", "valeurs_divergentes"],
               lignes, tri=["artefact"])
    ecrire_csv(OUT / "B4_logs_cli.csv",
               ["artefact", "identique", "lignes_avant", "lignes_apres",
                "lignes_avec_CODE"],
               logs, tri=["artefact"])

    div = [l for l in lignes if l["verdict"].startswith("DIVERGENT")
           or l["verdict"].startswith("NOMBRE")]
    print("=" * 74)
    print("B4 — INVARIANCE DU REGIME CLI, COLONNE PAR COLONNE")
    print("=" * 74)
    print(f"  artefacts compares (hors 99_log)        : {len(lignes)}")
    print(f"  identiques sur les colonnes communes    : {len(lignes)-len(div)}")
    print(f"  DIVERGENTS                              : {len(div)}")
    print(f"  colonnes communes confrontees (total)   : "
          f"{sum(l['colonnes_communes'] for l in lignes)}")
    print(f"  valeurs divergentes (total)             : "
          f"{sum(max(l['valeurs_divergentes'],0) for l in lignes)}")
    for l in div:
        print(f"    - {l['artefact']} : {l['verdict']} "
              f"[{l['colonnes_divergentes']}]")
    nouv_cols = sorted({c for l in lignes for c in l["colonnes_nouvelles"].split()
                        if c != "-"})
    print(f"\n  colonnes AJOUTEES par le harnais        : "
          f"{', '.join(nouv_cols) if nouv_cols else 'aucune'}")
    disp = sorted({c for l in lignes for c in l["colonnes_disparues"].split()
                   if c != "-"})
    print(f"  colonnes DISPARUES                      : "
          f"{', '.join(disp) if disp else 'aucune'}")
    print(f"\n  artefacts NOUVEAUX (absents avant)      : {len(nouveaux)}")
    for n in nouveaux:
        print(f"    + {n}")
    print(f"\n  99_log.txt : {sum(1 for l in logs if l['identique'])}/{len(logs)} "
          f"identiques ; lignes portant <CODE>/ : "
          f"{sum(l['lignes_avec_CODE'] for l in logs)}")
    return 1 if div else 0


if __name__ == "__main__":
    sys.exit(main())
