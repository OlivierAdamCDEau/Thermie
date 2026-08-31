"""
empreintes_app.py — le releve d'empreintes des sources applicatives.

POURQUOI CE SCRIPT REMPLACE LE PRECEDENT
-----------------------------------------
`verifier_aucune_pose.py` (etape 18) confrontait `app/` a l'exemplaire scelle
dans `out/livraison_etape17.zip`. Les archives de livraison sont retirees de
`out/` une fois remises au commanditaire : le temoin a disparu, et le controle
a echoue au premier appel de l'etape 20.

La faute est de conception, pas d'exploitation. Un temoin d'integrite ne doit
pas dependre d'un fichier destine a etre emporte. Le releve vit desormais dans
`tests/reference/empreintes/`, qui n'est livre a personne et ne bouge pas.

USAGE
    python empreintes_app.py relever <etiquette>
        Ecrit tests/reference/empreintes/<etiquette>.sha256

    python empreintes_app.py comparer <etiquette>
        Confronte app/ au releve. Retour 0 si identique, 2 sinon.

    python empreintes_app.py comparer <avant> <apres>
        Confronte deux releves entre eux, et dit ce qui a bouge. C'est la forme
        utile autour d'une pose : elle nomme les fichiers touches et refuse de
        laisser passer un fichier touche qui n'etait pas prevu.

CE QU'IL COUVRE
    Les onze sources de `app/` — les dix modules de `thermie_debits` plus
    `app.py`. La liste est DECOUVERTE, pas declaree : un douzieme module ajoute
    sans etre annonce doit apparaitre comme tel, et non passer inapercu parce
    qu'il ne figurait pas dans une liste.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent.parent
APP = RACINE / "app"
DEPOT = Path(__file__).resolve().parent / "empreintes"


def relever():
    """point relatif -> empreinte, pour toute source .py de app/."""
    out = {}
    for p in sorted(APP.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        rel = p.relative_to(RACINE).as_posix()
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def lire(etiquette):
    f = DEPOT / f"{etiquette}.sha256"
    if not f.exists():
        raise SystemExit(f"ECHEC : releve introuvable — {f}")
    d = {}
    for ligne in f.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        h, _, chemin = ligne.partition("  ")
        d[chemin] = h
    return d


def ecrire(etiquette, emp):
    DEPOT.mkdir(parents=True, exist_ok=True)
    f = DEPOT / f"{etiquette}.sha256"
    lignes = [f"# releve des sources applicatives — {etiquette}",
              f"# {len(emp)} fichier(s)"]
    lignes += [f"{h}  {c}" for c, h in sorted(emp.items())]
    f.write_text("\n".join(lignes) + "\n", encoding="utf-8", newline="\n")
    return f


def _comparer(a, b, nom_a, nom_b):
    tous = sorted(set(a) | set(b))
    ident, bouges, ajoutes, retires = [], [], [], []
    for c in tous:
        if c not in a:
            ajoutes.append(c)
        elif c not in b:
            retires.append(c)
        elif a[c] == b[c]:
            ident.append(c)
        else:
            bouges.append(c)
    print("=" * 74)
    print(f"EMPREINTES DES SOURCES APPLICATIVES : {nom_a}  ->  {nom_b}")
    print("=" * 74)
    for c in ident:
        print(f"  IDENTIQUE  {c:<44} {a[c][:16]}")
    for c in bouges:
        print(f"  MODIFIE    {c}")
        print(f"     {nom_a} : {a[c]}")
        print(f"     {nom_b} : {b[c]}")
    for c in ajoutes:
        print(f"  AJOUTE     {c}  {b[c][:16]}")
    for c in retires:
        print(f"  RETIRE     {c}")
    print("-" * 74)
    print(f"  identiques {len(ident)} | modifies {len(bouges)} | "
          f"ajoutes {len(ajoutes)} | retires {len(retires)}")
    return bouges, ajoutes, retires


def main(argv):
    if len(argv) < 3 or argv[1] not in ("relever", "comparer"):
        print(__doc__)
        return 2
    action = argv[1]
    if action == "relever":
        emp = relever()
        f = ecrire(argv[2], emp)
        print(f"{len(emp)} source(s) relevee(s) -> "
              f"{f.relative_to(RACINE).as_posix()}")
        for c, h in sorted(emp.items()):
            print(f"  {h[:16]}  {c}")
        return 0

    if len(argv) == 3:
        a, na = lire(argv[2]), argv[2]
        b, nb = relever(), "app/ maintenant"
    else:
        a, na = lire(argv[2]), argv[2]
        b, nb = lire(argv[3]), argv[3]
    bouges, ajoutes, retires = _comparer(a, b, na, nb)
    ok = not (bouges or ajoutes or retires)
    print("  VERDICT : " + ("AUCUNE SOURCE N'A BOUGE" if ok
                            else "DES SOURCES ONT BOUGE — a declarer"))
    print("=" * 74)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
