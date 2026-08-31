"""
verifier_integrite_references.py — ETAPE 12 : deux controles qui n'existaient
nulle part, et qui ont chacun trouve quelque chose.

CONTROLE 1 — CHAQUE MANIFEST.sha256 DECRIT-IL SON DOSSIER ?
------------------------------------------------------------
`_commun.ecrire_manifeste` existe depuis l'etape 1, mais `build_reference.main`
ne l'appelle que si le dossier de sortie est `tests/reference` :

    if not args.sans_manifeste and sortie == ICI:
        ecrire_manifeste()

`tests/reference_cli/` n'est donc JAMAIS remanifestee, quoi qu'on y
reconstruise. Son manifeste ne peut pas suivre ses rebasages, et rien ne le
signale : un manifeste perime ne differe d'un manifeste juste que si on le
verifie.

CONTROLE 2 — RESTE-T-IL DU BYTECODE SOUS ref/ ?
------------------------------------------------
D1 met `ref/` en lecture seule. `_commun.py` pose `sys.dont_write_bytecode`
avant tout import, et cela protege le harnais — mais PAS un script de
diagnostic ecrit a cote, qui importerait `ref/v4_5/` par ses propres moyens.
L'ecriture est silencieuse : le `.gitignore` du depot la masque a
`git status`, exactement comme a l'etape 1.

Ce module ne repare rien. Il constate, et il rend le constat rejouable.

USAGE
    python tests/reference/verifier_integrite_references.py

CODE DE RETOUR
    0  les deux controles passent
    1  au moins un constat
"""
from __future__ import annotations

import sys
from pathlib import Path

from _commun import RACINE, REF_V45, est_artefact, sha256

# ETAPE 21 — le rebasage de cloture ajoute une TROISIEME reference.
# `tests/reference_v4_5/` est l'ancienne `tests/reference/`, figee a
# l'etape 6, contre laquelle les treize correctifs ont ete mesures. Son
# manifeste doit continuer de la decrire : c'est le seul controle qui
# ait un sens sur un temoin fige, `check_reference.py` demandant lui la
# reproductibilite par le code d'aujourd'hui.
REFERENCES = ["tests/reference", "tests/reference_cli",
              "tests/reference_v4_5"]


def artefacts_sur_disque(base: Path):
    """Les artefacts presents, au sens de `est_artefact` — la meme regle que
    celle qui gouverne le manifeste et le diff."""
    out = {}
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        for p in sorted(d.iterdir()):
            rel = p.relative_to(base).as_posix()
            if p.is_file() and est_artefact(rel):
                out[rel] = p
    return out


def controle_manifeste(rel_ref: str):
    base = RACINE / rel_ref
    man = base / "MANIFEST.sha256"
    print(f"\n  {rel_ref}")
    if not man.is_file():
        print("      MANIFEST.sha256 ABSENT")
        return False
    attendu = {}
    for ligne in man.read_text(encoding="utf-8").splitlines():
        if "  " not in ligne:
            continue
        h, r = ligne.split("  ", 1)
        attendu[r] = h
    presents = artefacts_sur_disque(base)

    absents_du_manifeste = sorted(set(presents) - set(attendu))
    absents_du_disque = sorted(set(attendu) - set(presents))
    divergents = sorted(r for r in set(attendu) & set(presents)
                        if sha256(presents[r]) != attendu[r])

    print(f"      artefacts sur disque : {len(presents)}")
    print(f"      lignes au manifeste  : {len(attendu)}")
    print(f"      hors manifeste       : {len(absents_du_manifeste)}")
    print(f"      manifestes et absents: {len(absents_du_disque)}")
    print(f"      EMPREINTES DIVERGENTES : {len(divergents)}")
    for r in absents_du_manifeste:
        print(f"         hors manifeste : {r}")
    for r in absents_du_disque:
        print(f"         absent du disque : {r}")
    for r in divergents:
        print(f"         empreinte differente : {r}")
    ok = not (absents_du_manifeste or absents_du_disque or divergents)
    print(f"      VERDICT : {'le manifeste decrit son dossier' if ok else 'LE MANIFESTE NE DECRIT PAS SON DOSSIER'}")
    return ok


def controle_bytecode():
    print(f"\n  ref/ — bytecode (D1)")
    pyc = sorted(p for p in REF_V45.parent.rglob("*.pyc"))
    caches = sorted(p for p in REF_V45.parent.rglob("__pycache__") if p.is_dir())
    for p in pyc:
        print(f"      .pyc : {p.relative_to(RACINE).as_posix()}")
    for p in caches:
        print(f"      dossier : {p.relative_to(RACINE).as_posix()}")
    ok = not pyc and not caches
    print(f"      {len(pyc)} fichier(s) de bytecode, {len(caches)} dossier(s)")
    print(f"      VERDICT : {'ref/ est propre' if ok else 'ECRITURE DANS ref/ — D1'}")
    return ok


def main():
    print("=" * 74)
    print("INTEGRITE DES REFERENCES — deux controles")
    print("=" * 74)
    ok = True
    print("\nCONTROLE 1 — chaque MANIFEST.sha256 decrit-il son dossier ?")
    for r in REFERENCES:
        ok &= controle_manifeste(r)
    print("\nCONTROLE 2 — reste-t-il du bytecode sous ref/ ?")
    ok &= controle_bytecode()
    print("\n" + "=" * 74)
    print("VERDICT GLOBAL :", "les deux controles passent" if ok
          else "AU MOINS UN CONSTAT — voir ci-dessus")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
