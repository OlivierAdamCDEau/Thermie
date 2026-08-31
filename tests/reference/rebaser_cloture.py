"""
rebaser_cloture.py — ETAPE 21, POSE 2 : le rebasage de cloture (D83, branche B).

CE QUI CHANGE
--------------
`tests/reference/` cesse d'etre l'etat V4.5 de l'etape 6 et devient l'etat V4.6
d'aujourd'hui. C'est la branche B, arretee a l'etape 13 : la reference suit le
code corrige, et l'ancienne est CONSERVEE A COTE plutot que perdue.

LES TROIS REFERENCES, APRES CETTE ETAPE
    tests/reference/          V4.6, source `app`, chemin application.
                              Ce que l'outil produit aujourd'hui.
    tests/reference_v4_5/     V4.5, source `ref`, chemin application.
                              L'ancienne `tests/reference/`, deplacee telle
                              quelle. C'est le point de comparaison avec la
                              version EN SERVICE, et le chantier entier s'y
                              adosse : chaque correctif a ete mesure contre
                              elle.
    tests/reference_cli/      V4.5, source `ref`, chemin cli. Inchangee.
                              Elle atteste que les deux chemins de parametres
                              donnaient le meme resultat sous V4.5.

POURQUOI CONSERVER PLUTOT QUE REMPLACER
Rebaser sans conserver reviendrait a effacer le temoin contre lequel treize
correctifs ont ete mesures. Les rapports d'etape citent des chiffres qui n'ont
de sens que rapportes a cette reference ; les perdre rendrait le chantier
inverifiable. Et c'est elle qui permettra a la V4.7 de mesurer son ecart a la
V4.6 comme nous avons mesure le notre a la V4.5.

CE QUE LE SCRIPT FAIT, DANS CET ORDRE
    1. copie `tests/reference/` vers `tests/reference_v4_5/` — les six dossiers
       de jeu, le manifeste, la provenance ;
    2. verifie que la copie est FIDELE, empreinte par empreinte, avant de
       toucher a quoi que ce soit d'autre ;
    3. reconstruit `tests/reference/` depuis `app` ;
    4. complete sa provenance : la mention que la V4.5 est conservee a cote.

Si la verification de l'etape 2 echoue, le script s'arrete AVANT le rebasage.
On ne detruit pas un temoin sur la foi d'une copie non verifiee.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
ANCIENNE = RACINE / "tests" / "reference_v4_5"
JEUX = ("jeu_02", "jeu_03", "jeu_04", "jeu_05", "jeu_bienne",
        "jeu_exemples_v45")


def empreintes(dossier: Path):
    out = {}
    for j in JEUX:
        d = dossier / j
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if p.is_file():
                out[f"{j}/{p.name}"] = hashlib.sha256(p.read_bytes()).hexdigest()
    for n in ("MANIFEST.sha256", "SOURCE_CODE.txt"):
        p = dossier / n
        if p.exists():
            out[n] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main():
    print("=" * 78)
    print("ETAPE 21, POSE 2 — LE REBASAGE DE CLOTURE (D83, branche B)")
    print("=" * 78)

    if ANCIENNE.exists():
        print(f"  {ANCIENNE.name}/ existe deja — le rebasage a deja eu lieu.")
        return 1

    # --- 1. la copie
    avant = empreintes(ICI)
    print(f"\n  1. conservation de l'ancienne reference")
    print(f"     {len(avant)} fichier(s) a copier")
    ANCIENNE.mkdir(parents=True)
    for j in JEUX:
        s = ICI / j
        if s.is_dir():
            shutil.copytree(s, ANCIENNE / j)
    for n in ("MANIFEST.sha256", "SOURCE_CODE.txt"):
        p = ICI / n
        if p.exists():
            shutil.copy2(p, ANCIENNE / n)

    # --- 2. la verification, AVANT de toucher a la reference
    copie = empreintes(ANCIENNE)
    manquants = sorted(set(avant) - set(copie))
    divergents = sorted(k for k in set(avant) & set(copie)
                        if avant[k] != copie[k])
    print(f"     copies : {len(copie)}")
    print(f"     manquants  : {len(manquants)}")
    print(f"     divergents : {len(divergents)}")
    if manquants or divergents:
        print("\n  ECHEC — la copie n'est pas fidele. Le rebasage n'a PAS eu")
        print("  lieu. On ne detruit pas un temoin sur une copie non verifiee.")
        for k in (manquants + divergents)[:10]:
            print(f"     {k}")
        return 2
    print(f"     VERDICT : copie FIDELE, empreinte par empreinte")

    # --- 3. le rebasage
    print(f"\n  2. reconstruction de tests/reference/ depuis `app`")
    r = subprocess.run(
        [sys.executable, str(ICI / "build_reference.py"),
         "--etape", "21", "--est-une-reference"],
        cwd=str(ICI), env={**__import__("os").environ,
                           "THERMIE_CODE": "app",
                           "PYTHONIOENCODING": "utf-8"},
        capture_output=True, text=True)
    print("     " + "\n     ".join(r.stdout.strip().splitlines()[-4:]))
    if r.returncode != 0:
        print(f"     ECHEC (retour {r.returncode})")
        print(r.stderr[-2000:])
        return 2

    # --- 4. la provenance completee
    p = ICI / "SOURCE_CODE.txt"
    t = p.read_text(encoding="utf-8")
    mention = (
        "\n# ETAPE 21 — REBASAGE DE CLOTURE (D83, branche B)\n"
        "# Cette reference decrit desormais V4.6, telle que treize correctifs\n"
        "# l'ont faite. L'etat V4.5 de l'etape 6, contre lequel chacun de ces\n"
        "# correctifs a ete mesure, EST CONSERVE a cote :\n"
        "#\n"
        "#     tests/reference_v4_5/   V4.5, source ref, chemin application\n"
        "#     tests/reference_cli/    V4.5, source ref, chemin cli\n"
        "#\n"
        "# Les trois se verifient separement, chacune contre la source qu'elle\n"
        "# declare. C'est `tests/reference_v4_5/` qui permettra a une version\n"
        "# ulterieure de mesurer son ecart a V4.6 comme nous avons mesure le\n"
        "# notre a V4.5.\n")
    if "REBASAGE DE CLOTURE" not in t:
        p.write_text(t.rstrip("\n") + "\n" + mention, encoding="utf-8",
                     newline="\n")
    print(f"\n  3. provenance completee : {p.relative_to(RACINE).as_posix()}")
    for l in p.read_text(encoding="utf-8").splitlines():
        if l.startswith(("SOURCE_CODE=", "ETAPE=", "CHEMIN_")):
            print(f"     {l}")
    print("\n" + "=" * 78)
    print("  LES TROIS REFERENCES")
    for d, quoi in ((ICI, "V4.6, source app"),
                    (ANCIENNE, "V4.5, source ref, chemin application"),
                    (RACINE / "tests" / "reference_cli",
                     "V4.5, source ref, chemin cli")):
        n = len([1 for j in JEUX for p2 in (d / j).iterdir()
                 if (d / j).is_dir() and p2.is_file()]) if d.exists() else 0
        print(f"     {d.name:<22} {quoi:<42} {n} fichier(s)")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
