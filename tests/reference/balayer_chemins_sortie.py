"""
balayer_chemins_sortie.py — ETAPE 21, tache 1.3 : ou chaque script du harnais
ecrit-il ?

CE QUI EST DANGEREUX, ET CE QUI NE L'EST PAS
---------------------------------------------
Presque tous les scripts de mesure portent un chemin de sortie fige vers LEUR
PROPRE etape. Ce n'est pas un defaut : un script ecrit pour l'etape 3 qui ecrit
dans `out/etape3/` ne peut ecraser que ses propres sorties, et le rejouer est
sans consequence.

Le danger est d'une autre nature, et l'etape 20 l'a rencontre : **un script
qu'une etape ULTERIEURE rejoue, et qui ecrit dans le dossier de l'etape qui l'a
vu naitre**. `eprouver_temoin.py`, ecrit a l'etape 19 et rejoue a l'etape 20 sur
consigne expresse, a ainsi ecrase quatre artefacts d'etape 19.

Le critere de risque n'est donc pas « le chemin est-il fige » mais :

    le script peut-il etre rejoue plus tard, et si oui, sa sortie
    est-elle redirigeable ?

Un script est REDIRIGEABLE s'il accepte une option de sortie — comme
`build_reference.py --sortie`. Sinon sa sortie est FIGEE.

CE QUE CE SCRIPT RELEVE
    · les dossiers d'etape ou chaque script ecrit ;
    · l'etape a laquelle il appartient, lue dans son en-tete ;
    · s'il expose une option de sortie ;
    · s'il LIT dans une autre etape que la sienne — signe qu'il est concu pour
      etre employe au-dela de son etape d'origine, donc candidat au rejeu.

Il ne corrige rien : il nomme.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _commun import RACINE, ecrire_csv

ICI = Path(__file__).resolve().parent
OUT = RACINE / "out" / "etape21"

# La racine d'ECRITURE est l'affectation `OUT = RACINE / "out" / "etapeN"`,
# plus toute ecriture explicite vers un chemin d'etape litteral. Tout le reste
# — `read_csv(RACINE / "out" / "etapeN" / ...)` — est une LECTURE. Confondre
# les deux faisait signaler six scripts au lieu d'un.
RE_ECRIT = re.compile(
    r'^\s*OUT\s*=\s*RACINE\s*/\s*"out"\s*/\s*"(etape\d+)"'
    r'|(?:ecrire_csv|ecrire_texte|write_text|write_bytes|copy2)\('
    r'[^)]*?RACINE\s*/\s*"out"\s*/\s*"(etape\d+)"',
    re.MULTILINE | re.DOTALL)
RE_LIT = re.compile(r'RACINE\s*/\s*"out"\s*/\s*"(etape\d+)"'
                    r'|out/(etape\d+)/[A-Za-z0-9_]+\.(?:csv|txt|json)')
RE_ETAPE = re.compile(r'ETAPE\s+(\d+)', re.IGNORECASE)
RE_SORTIE = re.compile(r'add_argument\(\s*"--sortie"|--sortie')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("ETAPE 21, 1.3 — OU CHAQUE SCRIPT DU HARNAIS ECRIT-IL ?")
    print("=" * 78)

    lignes = []
    for p in sorted(ICI.glob("*.py")):
        t = p.read_text(encoding="utf-8")
        entete = t[:t.find('"""', 3) + 3] if t.startswith('"""') else t[:2000]
        m = RE_ETAPE.search(entete)
        etape_du_script = int(m.group(1)) if m else None
        ecrit = sorted({e for pair in RE_ECRIT.findall(t)
                        for e in pair if e})
        lit = sorted({(a or b) for a, b in RE_LIT.findall(t)} - set(ecrit))
        redirigeable = bool(RE_SORTIE.search(t))
        # candidat au rejeu : il lit ailleurs que chez lui, ou il n'a pas
        # d'etape d'origine identifiable
        autres = [e for e in lit
                  if etape_du_script is None
                  or int(e.removeprefix("etape")) != etape_du_script]
        risque = ""
        if ecrit and not redirigeable:
            cibles = [int(e.removeprefix("etape")) for e in ecrit]
            if etape_du_script is not None and any(
                    c < etape_du_script for c in cibles):
                risque = "ECRIT DANS UNE ETAPE ANTERIEURE A LA SIENNE"
            elif autres:
                risque = ("sortie figee, et lit dans une autre etape : "
                          "candidat au rejeu")
        lignes.append(dict(
            script=p.name, etape_du_script=etape_du_script,
            ecrit_dans=" ".join(ecrit), lit_dans=" ".join(lit),
            redirigeable=("oui" if redirigeable else "non"),
            risque=(risque or "aucun")))

    ecrire_csv(OUT / "B_chemins_sortie.csv",
               ["script", "etape_du_script", "ecrit_dans", "lit_dans",
                "redirigeable", "risque"], lignes, tri=["script"])

    n = len(lignes)
    avec = [l for l in lignes if l["ecrit_dans"]]
    red = [l for l in avec if l["redirigeable"] == "oui"]
    risq = [l for l in lignes if l["risque"] != "aucun"]
    print(f"  scripts du harnais              : {n}")
    print(f"  qui ecrivent dans une etape     : {len(avec)}")
    print(f"  dont redirigeables (--sortie)   : {len(red)}")
    print(f"  A RISQUE                        : {len(risq)}")
    print("-" * 78)
    for l in risq:
        print(f"  {l['script']:<34} etape {l['etape_du_script']}")
        print(f"     ecrit dans : {l['ecrit_dans']}")
        print(f"     lit dans   : {l['lit_dans'] or '—'}")
        print(f"     -> {l['risque']}")
    if not risq:
        print("  Aucun script n'ecrit dans une etape anterieure a la sienne,")
        print("  et aucun script a sortie figee ne lit ailleurs que chez lui.")
    print("-" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
