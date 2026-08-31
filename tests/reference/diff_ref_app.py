"""
diff_ref_app.py — ÉTAPE 5, TÂCHE B : diagnostic A/B, sans toucher la référence.

POURQUOI CE DIAGNOSTIC EXISTE
------------------------------
`check_reference.py` a signalé une divergence sur `jeu_bienne/99_log.txt` :
la trace d'erreur figée par D7 porte le CHEMIN du code exécuté, et il passe de
`ref\\v4_5\\thermie_debits\\core.py` à `app\\thermie_debits\\core.py`. Les
numéros de ligne et les messages sont identiques : aucun comportement n'a
changé.

La consigne interdit de rebaser la référence pour absorber cela, et elle a
raison. Ce module ne la touche donc pas. Il construit deux rejeux — l'un avec
le code de `ref/v4_5/`, l'autre avec celui de `app/` — et les compare entre
EUX, après avoir neutralisé la seule chose qui les sépare par construction :
la racine du code.

Il répond ainsi à la question qui compte — « quelque chose d'autre a-t-il
bougé ? » — sans modifier un seul octet de `tests/reference/`.

Il traite les DEUX régimes. Le régime CLI ne peut pas se comparer à
`tests/reference_cli/` : ce dossier a été figé avant que le harnais ne gagne
`10_parametres.json` et la colonne `sortie_v45`. Le comparer aujourd'hui
mélangerait un changement de code et un changement de schéma du harnais. Un
A/B construit à l'instant avec le MÊME harnais évite ce piège.

USAGE
    python tests/reference/diff_ref_app.py [--garder DOSSIER]
"""
from __future__ import annotations

import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _commun import ICI, RACINE, decouvrir, est_artefact, sha256

MAX_LIGNES = 30

# La racine du code, telle qu'elle apparaît dans les traces figées. C'est la
# SEULE chose qu'un changement de dossier fait bouger ; le module et le numéro
# de ligne, eux, portent l'information et sont conservés.
RACINE_CODE = re.compile(r"<RACINE>[\\/](?:ref[\\/]v4_5|app)[\\/]")


def normaliser(texte: str) -> str:
    return RACINE_CODE.sub("<CODE>/", texte)


def construire(dest: Path, code: str, chemin: str):
    """Construit un rejeu complet, dans un sous-processus, avec le code voulu."""
    env = dict(os.environ, THERMIE_CODE=code, PYTHONIOENCODING="utf-8")
    dest.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-W", "ignore", str(ICI / "build_reference.py"),
           "--sortie", str(dest), "--chemin", chemin, "--sans-manifeste"]
    r = subprocess.run(cmd, cwd=str(ICI), env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], file=sys.stderr)
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit(f"construction {code}/{chemin} en echec")
    return dest


def artefacts(racine: Path):
    out = []
    for d in sorted(p for p in racine.iterdir() if p.is_dir()):
        for p in sorted(d.iterdir()):
            rel = p.relative_to(racine).as_posix()
            if p.is_file() and est_artefact(rel):
                out.append(rel)
    return sorted(out)


def comparer(a: Path, b: Path, titre: str):
    ra, rb = set(artefacts(a)), set(artefacts(b))
    identiques = bruts = normalises = 0
    divergences = []
    for rel in sorted(ra | rb):
        if rel not in ra or rel not in rb:
            divergences.append((rel, "ABSENT D'UN COTE", []))
            continue
        if sha256(a / rel) == sha256(b / rel):
            identiques += 1
            continue
        bruts += 1
        ta = normaliser((a / rel).read_text(encoding="utf-8"))
        tb = normaliser((b / rel).read_text(encoding="utf-8"))
        if ta == tb:
            normalises += 1
            continue
        d = list(difflib.unified_diff(ta.splitlines(), tb.splitlines(),
                                      fromfile=f"ref/{rel}", tofile=f"app/{rel}",
                                      lineterm=""))
        n_p = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
        n_m = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
        divergences.append((rel, f"CONTENU DIFFERENT ({n_m} retirees, "
                                 f"{n_p} ajoutees)", d[:MAX_LIGNES]))

    print(f"\n########## {titre} ##########")
    print(f"{len(ra | rb)} artefact(s) compare(s).")
    print(f"  identiques au bit pres                       : {identiques}")
    print(f"  differents seulement par la racine du code   : {normalises}")
    print(f"  DIVERGENTS APRES NEUTRALISATION DU CHEMIN    : {len(divergences)}")
    if not divergences:
        print("\nAUCUNE DIVERGENCE DE COMPORTEMENT. La seule difference entre "
              "ref/v4_5 et app est le chemin du code inscrit dans les traces.")
        return 0
    print()
    for rel, quoi, extrait in divergences:
        print(f"  ### {rel} — {quoi}")
        for l in extrait:
            print(f"      {l}")
        print()
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--garder", default=None)
    args = ap.parse_args()

    base = Path(args.garder).resolve() if args.garder else Path(
        tempfile.mkdtemp(prefix="thermie_ab_"))
    base.mkdir(parents=True, exist_ok=True)
    code_retour = 0
    try:
        for chemin, titre in (("application", "REGIME APPLICATION — ref/v4_5 contre app"),
                              ("cli", "REGIME CLI — ref/v4_5 contre app "
                                      "(8 565 journees ecartees)")):
            print(f"\nConstruction du rejeu ref/{chemin}...", flush=True)
            a = construire(base / f"ref_{chemin}", "ref", chemin)
            print(f"Construction du rejeu app/{chemin}...", flush=True)
            b = construire(base / f"app_{chemin}", "app", chemin)
            code_retour |= comparer(a, b, titre)
    finally:
        if not args.garder:
            shutil.rmtree(base, ignore_errors=True)
    return code_retour


if __name__ == "__main__":
    sys.exit(main())
