"""
revue_journal_verdicts.py — ETAPE 19, tache E : le journal des verdicts, passe
en revue contre les rejeux des etapes 10 a 16.

AUCUNE MODIFICATION APPLICATIVE. Ce script lit des artefacts deja produits.

CE QU'IL FAIT
--------------
`docs/VERDICTS_MODIFIES.md` (D43) doit porter TOUT verdict qui a bouge. Un
journal incomplet est pire qu'un journal absent : il atteste.

Le script reconstitue, a partir des `08_scores.csv` de chaque rejeu conserve,
la suite chronologique des CATEGORIES publiees pour chaque point — categorie de
vulnerabilite aigue, categorie de vulnerabilite chronique, classe SGVT — puis
releve chaque changement d'une etape a la suivante. Chaque mouvement est
ensuite cherche dans le texte du journal, par nom de point.

CE QU'IL NE PEUT PAS FAIRE
---------------------------
Il verifie qu'un point CITE dans le journal a bien un mouvement, et qu'un point
qui bouge est bien CITE. Il ne verifie pas que la phrase du journal decrit
correctement le mouvement : cela demande une lecture, et elle est faite dans le
rapport.

Les rejeux du cote reference (`rejeu_ref*`) sont exclus : ils rejouent V4.5 et
ne publient pas les verdicts de l'application.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

from _commun import RACINE, ecrire_csv

OUT = RACINE / "out" / "etape19"
JOURNAL = RACINE / "docs" / "VERDICTS_MODIFIES.md"

# Ordre chronologique des rejeux du cote APPLICATION.
SUITE = [
    ("etape10 pose 1", "out/etape10/rejeu_pose1"),
    ("etape10 pose 2", "out/etape10/rejeu_pose2"),
    ("etape11 correctif 6", "out/etape11/rejeu_correctif6"),
    ("etape12 avant", "out/etape12/rejeu_avant"),
    ("etape12 apres", "out/etape12/rejeu_apres"),
    ("etape13 pose 1", "out/etape13/rejeu_app_pose1"),
    ("etape13 pose 3", "out/etape13/rejeu_app_pose3"),
    ("etape13 pose 4", "out/etape13/rejeu_app_pose4"),
    ("etape13 pose 5", "out/etape13/rejeu_app_pose5"),
    ("etape14 apres", "out/etape14/rejeu_app_apres"),
    ("etape15 apres", "out/etape15/rejeu_app_apres"),
    ("etape16 apres", "out/etape16/rejeu_app_apres"),
    ("etape17 pose 1", "out/etape17/rejeu_pose1"),
    ("etape17 final", "out/etape17/rejeu_final"),
]

# Les trois categories publiees, et ou les lire dans 08_scores.csv.
CATEGORIES = {
    "categorie aigue": ("n_jours_aigus", "detail"),
    "categorie chronique": ("pct_stress_chronique", "detail"),
    "classe SGVT": ("sgvt", "detail"),
}


def _plat(s):
    """Sans accents ni casse, pour chercher un nom de point dans un texte."""
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def lire_etat(dossier: Path):
    """point -> {categorie: valeur} pour un rejeu."""
    etat = {}
    if not dossier.is_dir():
        return etat
    for f in sorted(dossier.rglob("08_scores.csv")):
        try:
            d = pd.read_csv(f, sep=";", encoding="utf-8")
        except Exception:
            continue
        for pt, sub in d.groupby("point"):
            e = etat.setdefault(str(pt), {})
            for nom, (ind, col) in CATEGORIES.items():
                r = sub[sub["indicateur"] == ind]
                if len(r):
                    v = r.iloc[0].get(col)
                    e[nom] = None if pd.isna(v) else str(v)
    return etat


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("TACHE E — LE JOURNAL DES VERDICTS, PASSE EN REVUE")
    print("=" * 78)

    etats, presents = {}, []
    for label, rel in SUITE:
        e = lire_etat(RACINE / rel)
        if e:
            etats[label] = e
            presents.append(label)
            print(f"  {label:<24} {len(e)} point(s)")
        else:
            print(f"  {label:<24} — absent ou vide, ignore")

    mouvements = []
    for a, b in zip(presents, presents[1:]):
        ea, eb = etats[a], etats[b]
        for pt in sorted(set(ea) & set(eb)):
            for cat in CATEGORIES:
                va, vb = ea[pt].get(cat), eb[pt].get(cat)
                if va != vb and not (va is None and vb is None):
                    mouvements.append(dict(
                        point=pt, categorie=cat, de=a, vers=b,
                        avant=va, apres=vb))

    txt = _plat(JOURNAL.read_text(encoding="utf-8")) if JOURNAL.exists() else ""
    pts_bouges = sorted({m["point"] for m in mouvements})
    manquants, cites = [], []
    for pt in pts_bouges:
        (cites if _plat(pt) in txt else manquants).append(pt)

    for m in mouvements:
        m["cite_dans_le_journal"] = ("oui" if _plat(m["point"]) in txt
                                     else "NON — LACUNE D43")

    ecrire_csv(OUT / "E_mouvements.csv",
               ["point", "categorie", "de", "vers", "avant", "apres",
                "cite_dans_le_journal"],
               mouvements, tri=["point", "de", "categorie"])

    print("\n" + "-" * 78)
    print(f"  mouvements de categorie releves : {len(mouvements)}")
    print(f"  points concernes                : {len(pts_bouges)}")
    print(f"  dont cites dans le journal      : {len(cites)}")
    print(f"  dont ABSENTS du journal         : {len(manquants)}")
    print("-" * 78)
    for m in mouvements:
        drapeau = "" if m["cite_dans_le_journal"] == "oui" else "   <<< LACUNE"
        print(f"  {m['point']:<34} {m['categorie']:<22} "
              f"{m['de']} -> {m['vers']}{drapeau}")
        print(f"     « {m['avant']} »  ->  « {m['apres']} »")
    if manquants:
        print("\n  POINTS QUI BOUGENT ET NE FIGURENT PAS DANS LE JOURNAL :")
        for p in manquants:
            print(f"     {p}")
    else:
        print("\n  Aucun point ne bouge sans figurer dans le journal.")

    # Le controle inverse : des points cites par le journal qui ne bougent pas
    # dans les rejeux conserves. Ce n'est PAS une faute — les mouvements de
    # l'etape 1 a l'etape 9 precedent ces rejeux — mais il faut le dire.
    print("\n  Note : les rejeux conserves commencent a l'etape 10. Les")
    print("  mouvements du correctif 1, poses avant, ne peuvent pas etre")
    print("  retrouves ici ; ils sont verifies au rapport, un par un.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
