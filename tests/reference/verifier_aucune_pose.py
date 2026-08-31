"""
verifier_aucune_pose.py — ETAPE 18 : la preuve qu'il n'y a eu AUCUNE pose.

L'etape 18 est une VERIFICATION. La commande l'ecrit deux fois : « AUCUNE
modification applicative. Aucun correctif, aucune regle nouvelle. » Un rapport
qui se contente de l'affirmer ne vaut rien ; ce script le PROUVE, octet par
octet, en confrontant chaque source applicative a l'exemplaire scelle dans
`out/livraison_etape17.zip`.

Deux verdicts sont possibles, et un seul est acceptable :
  IDENTIQUE  chaque fichier applicatif a exactement l'empreinte qu'il avait a
             la cloture de l'etape 17.
  DIVERGENT  un fichier a bouge : l'etape 18 aurait alors pose quelque chose,
             et le rapport devrait le declarer avant toute autre conclusion.

Retour 0 si tout est identique, 2 sinon.
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent.parent
ZIP = RACINE / "out" / "livraison_etape17.zip"


def main():
    if not ZIP.exists():
        print(f"ECHEC : {ZIP} introuvable — impossible de prouver quoi que ce soit")
        return 2
    print("=" * 74)
    print("ETAPE 18 — PREUVE D'ABSENCE DE POSE")
    print(f"temoin : {ZIP.relative_to(RACINE).as_posix()}")
    print("=" * 74)
    ident, diff, absents = [], [], []
    with zipfile.ZipFile(ZIP) as z:
        noms = [n for n in z.namelist() if n.startswith("app/")]
        for n in sorted(noms):
            attendu = hashlib.sha256(z.read(n)).hexdigest()
            p = RACINE / n
            if not p.exists():
                absents.append(n)
                continue
            obtenu = hashlib.sha256(p.read_bytes()).hexdigest()
            (ident if obtenu == attendu else diff).append((n, attendu, obtenu))
    for n, a, o in ident:
        print(f"  IDENTIQUE  {n:<44} {a[:16]}")
    for n, a, o in diff:
        print(f"  DIVERGENT  {n}")
        print(f"     etape 17 : {a}")
        print(f"     aujourdhui: {o}")
    for n in absents:
        print(f"  ABSENT     {n}")
    print("-" * 74)
    print(f"  identiques : {len(ident)}   divergents : {len(diff)}   "
          f"absents : {len(absents)}")
    ok = not diff and not absents
    print("  VERDICT : " + ("AUCUNE POSE — l'application est celle de l'etape 17"
                            if ok else "UNE SOURCE A BOUGE — a declarer"))
    print("=" * 74)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
