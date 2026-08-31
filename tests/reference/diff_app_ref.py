"""
diff_app_ref.py — D44 : LE CONTRÔLE PERMANENT.

Diff OCTET de `app/` contre `ref/v4_5/`. La liste des fichiers qui diffèrent
est confrontée à la liste que l'étape en cours déclare. **Un fichier qui
diffère sans être déclaré arrête l'étape.**

POURQUOI CE CONTRÔLE EXISTE
----------------------------
À l'étape 6, `app/thermie_debits/qc.py` et `core.py` avaient été réécrits en
CRLF par mes propres scripts de correctif, depuis l'étape 5, sans que rien ne
le signale. Aucune valeur n'en dépendait — mais `app/` cessait d'être
comparable octet pour octet à `ref/v4_5/` en dehors des corrections voulues.
Un moyen de contrôle disparaissait en silence, ce qui est pire qu'un contrôle
qui échoue.

Ce module rend cette disparition impossible : il distingue explicitement une
différence de CONTENU d'une différence de FINS DE LIGNE, et la seconde est
traitée comme une anomalie au même titre que la première. Rien dans `app/` ne
doit différer de `ref/v4_5/` autrement que par une correction déclarée.

CE QUI EST IGNORÉ, ET POURQUOI
-------------------------------
`__pycache__/` (D1 : le harnais interdit déjà son écriture) et `.git/` — ni
l'un ni l'autre n'est du code, et ni l'un ni l'autre n'est produit par les
correctifs.

USAGE
    python tests/reference/diff_app_ref.py
    python tests/reference/diff_app_ref.py --declares app/thermie_debits/qc.py app/thermie_debits/core.py

Code de retour : 0 si la liste constatée est celle déclarée, 1 sinon.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from _commun import APP, REF_V45, RACINE, ecrire_csv

IGNORE = ("__pycache__", ".git")


def pertinent(chemin: Path) -> bool:
    return not any(p in IGNORE for p in chemin.parts)


def empreinte(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def nature(a: bytes, b: bytes) -> str:
    """CONTENU, FINS DE LIGNE, ou les deux. La distinction est le cœur de D44."""
    if a == b:
        return "identique"
    na, nb = a.replace(b"\r\n", b"\n"), b.replace(b"\r\n", b"\n")
    if na == nb:
        return "FINS DE LIGNE SEULEMENT"
    if (a.count(b"\r\n") > 0) != (b.count(b"\r\n") > 0):
        return "CONTENU + FINS DE LIGNE"
    return "CONTENU"


def comparer():
    lignes = []
    vus = set()
    for p in sorted(APP.rglob("*")):
        if not p.is_file() or not pertinent(p):
            continue
        rel = p.relative_to(APP).as_posix()
        vus.add(rel)
        q = REF_V45 / rel
        a = p.read_bytes()
        if not q.exists():
            lignes.append(dict(
                fichier=f"app/{rel}", etat="ABSENT DE ref/v4_5",
                nature="-", lignes_app=a.count(b"\n"), lignes_ref=0,
                octets_app=len(a), octets_ref=0,
                crlf_app=a.count(b"\r\n"), crlf_ref=0,
                sha_app=empreinte(a)[:16], sha_ref="-"))
            continue
        b = q.read_bytes()
        if a == b:
            continue
        lignes.append(dict(
            fichier=f"app/{rel}", etat="DIFFERENT", nature=nature(a, b),
            lignes_app=a.count(b"\n"), lignes_ref=b.count(b"\n"),
            octets_app=len(a), octets_ref=len(b),
            crlf_app=a.count(b"\r\n"), crlf_ref=b.count(b"\r\n"),
            sha_app=empreinte(a)[:16], sha_ref=empreinte(b)[:16]))

    for q in sorted(REF_V45.rglob("*")):
        if not q.is_file() or not pertinent(q):
            continue
        rel = q.relative_to(REF_V45).as_posix()
        if rel in vus:
            continue
        b = q.read_bytes()
        lignes.append(dict(
            fichier=f"app/{rel}", etat="ABSENT DE app", nature="-",
            lignes_app=0, lignes_ref=b.count(b"\n"),
            octets_app=0, octets_ref=len(b),
            crlf_app=0, crlf_ref=b.count(b"\r\n"),
            sha_app="-", sha_ref=empreinte(b)[:16]))
    return lignes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--declares", nargs="*", default=None,
                    help="fichiers que l'etape declare modifies "
                         "(chemins depuis la racine, ex. app/thermie_debits/qc.py)")
    ap.add_argument("--sortie", default=None,
                    help="CSV recapitulatif (defaut : out/etape7/D44_diff_app_ref.csv)")
    args = ap.parse_args()

    lignes = comparer()
    sortie = Path(args.sortie) if args.sortie else \
        RACINE / "out" / "etape7" / "D44_diff_app_ref.csv"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    ecrire_csv(sortie,
               ["fichier", "etat", "nature", "lignes_app", "lignes_ref",
                "octets_app", "octets_ref", "crlf_app", "crlf_ref",
                "sha_app", "sha_ref"],
               lignes, tri=["fichier"])

    print("=" * 78)
    print("D44 — DIFF OCTET DE app/ CONTRE ref/v4_5/")
    print("=" * 78)
    if not lignes:
        print("  Aucun fichier ne differe.")
    for l in lignes:
        print(f"  {l['fichier']}")
        print(f"      etat   : {l['etat']}   nature : {l['nature']}")
        print(f"      lignes : app {l['lignes_app']} / ref {l['lignes_ref']}"
              f"      octets : app {l['octets_app']} / ref {l['octets_ref']}")
        if l["crlf_app"] or l["crlf_ref"]:
            print(f"      CRLF   : app {l['crlf_app']} / ref {l['crlf_ref']}")

    # --- Confrontation a la liste declaree
    constates = sorted(l["fichier"] for l in lignes)
    if args.declares is None:
        print(f"\n  {len(constates)} fichier(s) different(s). "
              f"Aucune liste declaree n'a ete fournie : rien n'est confronte.")
        return 0

    declares = sorted(set(args.declares))
    manquants = [d for d in declares if d not in constates]
    surprises = [c for c in constates if c not in declares]

    print(f"\n  declares  : {len(declares)}")
    for d in declares:
        print(f"      {d}")
    print(f"  constates : {len(constates)}")
    print()
    if surprises:
        print("  ARRET — fichier(s) different(s) SANS ETRE DECLARE(S) :")
        for c in surprises:
            print(f"      {c}")
    if manquants:
        print("  Fichier(s) declare(s) qui ne different PAS :")
        for d in manquants:
            print(f"      {d}")
    if not surprises and not manquants:
        print("  CONFORME — la liste constatee est exactement la liste declaree.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
