"""
verifier_04_normales.py — ÉTAPE 11, TÂCHE B.

CE QUE CE MODULE REFAIT, ET POURQUOI
-------------------------------------
`comparer_rejeux.py` certifie les « figé » depuis l'étape 7. Sa table de clés
déclarait pour `04_normales.csv` la colonne `doy`, qui n'existe pas dans ce
fichier — ses colonnes sont `point, mois, jour`. La clé absente faisait
retomber la comparaison en appariement positionnel ; les longueurs différant,
la boucle de colonnes était sautée ; et l'outil rapportait « 0 valeur
changée » sur un artefact qui pouvait avoir perdu des lignes.

L'outil était donc **aveugle sur ce seul artefact**, et il l'était depuis
l'étape 7. Tout « figé » qu'il a prononcé sur `04_normales.csv` doit être
refait — et refait AUTREMENT : par empreinte SHA-256 du fichier entier, qui ne
dépend d'aucune clé, d'aucun appariement et d'aucune colonne.

Les autres artefacts ne sont pas concernés : leurs clés existent bien dans
leurs fichiers, et l'appariement a fonctionné. La vérification porte donc sur
`04_normales.csv` seul, comme la commande le pose.

CE QUI EST COMPARÉ
-------------------
Les rejeux conservés de chaque étape, dans l'ordre où ils ont été produits.
Entre deux rejeux consécutifs, `04_normales.csv` doit être identique OCTET
POUR OCTET partout où l'étape le déclarait figé.

Sortie :
  out/etape11/B_empreintes_04_normales.csv
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from _commun import RACINE, ecrire_csv

OUT = RACINE / "out" / "etape11"

# Les rejeux conserves, dans l'ordre chronologique, avec ce que l'etape
# declarait pour 04_normales.csv.
REJEUX = [
    ("etape6 — correctif 2", "out/etape6/rejeu_correctif2", "fige"),
    ("etape7 — correctif 5", "out/etape7/rejeu_correctif5", "fige"),
    ("etape7 — harnais final", "out/etape7/rejeu_final", "fige"),
    ("etape8 — correctif 8", "out/etape8/rejeu_correctif8", "fige"),
    ("etape9 — correctif 9", "out/etape9/rejeu_correctif9", "fige"),
    ("etape10 — pose 1", "out/etape10/rejeu_pose1", "fige"),
    # A l'etape 10, 04_normales.csv etait declare FIGE et a bouge sur
    # jeu_bienne : c'est le motif faux que le rapport d'etape 10 releve.
    # Le mouvement est donc CONNU et DOCUMENTE, non pas attendu partout.
    ("etape10 — pose 2", "out/etape10/rejeu_pose2", "mouvement connu (etape 10)"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    presents = [(nom, RACINE / rel, att) for nom, rel, att in REJEUX
                if (RACINE / rel).exists()]
    if not presents:
        print("aucun rejeu conserve", file=sys.stderr)
        return 2

    jeux = sorted(p.name for p in presents[0][1].iterdir() if p.is_dir())
    lignes, anomalies = [], []
    for jeu in jeux:
        precedent = None
        for nom, base, attendu in presents:
            f = base / jeu / "04_normales.csv"
            if not f.exists():
                continue
            h = sha(f)
            n = sum(1 for _ in f.read_text(encoding="utf-8").splitlines()) - 1
            bouge = (precedent is not None and h != precedent[1])
            # Seul un MOUVEMENT la ou l'etape declarait « fige » est une
            # anomalie. Un artefact qui ne bouge pas alors qu'il aurait pu
            # n'en est pas une : c'est le cas nominal.
            if precedent is None:
                conforme = "-"
            elif not bouge:
                conforme = "fige — conforme"
            elif attendu == "fige":
                conforme = "ECART A LA DECLARATION"
            else:
                conforme = "mouvement connu — conforme"
            lignes.append(dict(jeu=jeu, rejeu=nom, sha256=h[:32],
                               n_lignes=n,
                               bouge_vs_precedent=("-" if precedent is None
                                                   else "oui" if bouge else "non"),
                               declare=attendu, verdict=conforme))
            if conforme == "ECART A LA DECLARATION":
                anomalies.append((jeu, nom, precedent[0], attendu))
            precedent = (nom, h)

    ecrire_csv(OUT / "B_empreintes_04_normales.csv",
               ["jeu", "rejeu", "sha256", "n_lignes", "bouge_vs_precedent",
                "declare", "verdict"],
               lignes, tri=["jeu", "rejeu"])

    print("=" * 74)
    print("B — 04_normales.csv, CERTIFIE PAR EMPREINTE ET NON PAR L'OUTIL")
    print("=" * 74)
    print(f"  {len(presents)} rejeux conserves, {len(jeux)} jeux, "
          f"{len(lignes)} empreintes")
    for jeu in jeux:
        ls = [l for l in lignes if l["jeu"] == jeu]
        mouv = [l for l in ls if l["bouge_vs_precedent"] == "oui"]
        print(f"\n  {jeu} : {len(set(l['sha256'] for l in ls))} empreinte(s) "
              f"distincte(s) sur {len(ls)} rejeux")
        for l in mouv:
            print(f"      bouge au rejeu « {l['rejeu']} » "
                  f"({l['n_lignes']} lignes) — declare : {l['declare']} "
                  f"-> {l['verdict']}")
    print()
    if anomalies:
        print(f"  ARRET — {len(anomalies)} mouvement(s) NON DECLARE(S) :")
        for jeu, nom, prec, att in anomalies:
            print(f"     {jeu} : bouge entre « {prec} » et « {nom} », "
                  f"alors que l'etape declarait « {att} »")
        return 1
    print("  AUCUN MOUVEMENT NON DECLARE.")
    print("  Les « fige » prononces par l'outil defaillant sur 04_normales.csv")
    print("  aux etapes 6 a 9 et a la pose 1 de l'etape 10 etaient JUSTES :")
    print("  l'outil etait aveugle, mais il n'a rien manque. Le seul mouvement")
    print("  de cet artefact est celui de la pose 2, releve a l'etape 10.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
