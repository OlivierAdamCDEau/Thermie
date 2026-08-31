"""
check_reference.py — ÉTAPE 1, TÂCHE B : rejeu et diff de la référence.

Rejoue build_reference.py dans un dossier temporaire, puis compare artefact par
artefact avec la référence figée dans tests/reference/.

CRITÈRE D'ACCEPTATION (étape 1) : deux constructions successives produisent un
diff VIDE. Tant qu'il ne l'est pas, la référence n'en est pas une — c'est un
enregistrement du hasard.

Ce script sert ensuite, tout au long du chantier, à répondre à la seule
question qui compte : « ce que je viens de changer déplace-t-il quelque chose,
et quoi exactement ? »

USAGE
    python tests/reference/check_reference.py                 # tout le corpus
    python tests/reference/check_reference.py jeu_02 jeu_03   # une partie
    python tests/reference/check_reference.py --garder DOSSIER
        conserve le rejeu au lieu de le détruire (pour inspection manuelle)
    python tests/reference/check_reference.py --rejeu DOSSIER
        compare un rejeu DÉJÀ construit, sans le reconstruire

CODE DE RETOUR
    0  diff vide — aucune régression détectée
    1  au moins un artefact diffère
    2  erreur d'usage
    3  REFUS D70 — la référence n'a pas été produite par la source de code
       (ou le chemin de paramètres) qu'on lui demande de comparer, et le
       désaccord n'a pas été assumé explicitement

D70 — POURQUOI CE SCRIPT REFUSE PARFOIS DE COMPARER
----------------------------------------------------
Une référence ne dit rien par elle-même du code qui l'a produite. Comparer un
rejeu de `app/` à une référence construite depuis `ref/v4_5/` est un usage
LÉGITIME — c'est la mesure de l'effet cumulé des correctifs. Comparer sans
SAVOIR qu'on le fait ne l'est pas : le diff est alors massif, et rien ne
distingue « les correctifs ont bougé » de « le dépôt est corrompu ».

Le désaccord n'est donc pas interdit, il est rendu EXPLICITE. Par défaut le
script s'arrête et nomme les deux sources ; `--source-differente-assumee` le
laisse passer, et l'exécution le répète en tête de sa sortie.
"""
from __future__ import annotations

import argparse
import difflib
import shutil
import sys
import tempfile
from pathlib import Path

from _commun import CODE, ICI, RACINE, RACINE_CODE, decouvrir, est_artefact, sha256

import build_reference
from build_reference import NOM_SOURCE_CODE, lire_source_code


MAX_LIGNES_DIFF = 40          # extrait montré par artefact divergent


def verdict_source(reference: Path, chemin: str, assume: bool):
    """
    D70 — la référence a-t-elle été produite par la source qu'on lui compare ?

    Retourne (autorise, lignes_a_afficher). Le désaccord nomme LES DEUX
    sources : dire « désaccord » sans dire lequel contre lequel ne permet
    pas de choisir quoi corriger.
    """
    rel = reference.name
    try:
        rel = reference.relative_to(RACINE).as_posix()
    except ValueError:
        pass
    champs = lire_source_code(reference)
    if champs is None:
        return False, [
            f"REFUS (D70) — la reference {rel} ne porte pas de "
            f"{NOM_SOURCE_CODE}.",
            f"  Une reference non etiquetee ne dit pas quel code l'a "
            f"produite ; c'est exactement ce que D70 corrige.",
            f"  Source demandee : THERMIE_CODE={CODE}, chemin={chemin}.",
            f"  Ecrire le fichier avant de comparer.",
        ]
    src = champs.get("SOURCE_CODE", "")
    chem = champs.get("CHEMIN_DE_PARAMETRES", "")
    etape = champs.get("ETAPE", "?")
    ecarts = []
    if src != CODE:
        ecarts.append(f"source de code : la reference a ete produite par "
                      f"'{src}', le rejeu demande est '{CODE}'")
    if chem and chem != chemin:
        ecarts.append(f"chemin de parametres : la reference porte '{chem}', "
                      f"le rejeu demande est '{chemin}'")
    entete = [f"D70 — {rel} : source={src}, chemin={chem}, etablie a "
              f"l'etape {etape}."]
    if not ecarts:
        return True, entete + ["  Concordance avec le rejeu demande."]
    if assume:
        return True, entete + [
            "  DESACCORD ASSUME (--source-differente-assumee) :"] + \
            [f"    {e}" for e in ecarts] + [
            "  Le diff qui suit mesure l'effet CUMULE de cet ecart, pas une "
            "regression."]
    return False, entete + [
        "  REFUS (D70) — comparaison arretee :"] + \
        [f"    {e}" for e in ecarts] + [
        "  Si le desaccord est voulu, le declarer avec "
        "--source-differente-assumee."]


def artefacts(racine: Path, jeux):
    """
    Chemins relatifs des artefacts attendus, triés.

    D11 : seuls les fichiers <NN>_....{csv,json,txt} sont inspectés. Les
    classeurs et rapports .xlsx / .docx présents dans tests/reference/<jeu>/
    ne sont pas produits par le harnais ; ils restent dans le dossier mais
    n'entrent ni dans le manifeste ni dans le diff.
    """
    noms = {j["jeu"] for j in jeux}
    out = []
    for d in sorted(racine.iterdir() if racine.is_dir() else []):
        if not d.is_dir() or d.name not in noms:
            continue
        for p in sorted(d.iterdir()):
            rel = p.relative_to(racine).as_posix()
            if p.is_file() and est_artefact(rel):
                out.append(rel)
    return sorted(out)


def _scinder_sortie_v45(lignes):
    """
    Sépare les lignes d'un artefact selon la colonne `sortie_v45` (D13).

    Retourne (comptent, hors_verdict). Une ligne dont `sortie_v45` vaut « non »
    porte une valeur que le HARNAIS a calculée, pas V4.5 : elle contrôle le
    harnais, pas l'application, et n'entre donc pas dans le verdict de
    non-régression. Elle est rapportée à part.

    Un artefact sans colonne `sortie_v45` compte intégralement.
    """
    if not lignes:
        return [], []
    entete = lignes[0].split(";")
    if "sortie_v45" not in entete:
        return lignes, []
    i = entete.index("sortie_v45")
    comptent, hors = [lignes[0]], [lignes[0]]
    for l in lignes[1:]:
        champs = l.split(";")
        if len(champs) > i and champs[i].strip() == "non":
            hors.append(l)
        else:
            comptent.append(l)
    return comptent, hors


def _diff(la, lb, rel, etiquette):
    d = list(difflib.unified_diff(la, lb, fromfile=f"reference/{rel}",
                                  tofile=f"rejeu/{rel}", lineterm=""))
    if not d:
        return None
    n_plus = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
    n_moins = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
    return (rel, f"{etiquette} ({n_moins} ligne(s) retiree(s), "
                 f"{n_plus} ajoutee(s))", d[:MAX_LIGNES_DIFF])


def comparer(ref: Path, rejeu: Path, jeux):
    """
    Retourne (divergences, hors_verdict).

    `divergences` fait le verdict. `hors_verdict` rassemble les écarts portant
    sur des lignes marquées `sortie_v45 = non` : ils sont rapportés, jamais
    comptés (D13).
    """
    a = set(artefacts(ref, jeux))
    b = set(artefacts(rejeu, jeux))
    divergences, hors_verdict = [], []

    for rel in sorted(a - b):
        divergences.append((rel, "ABSENT DU REJEU", []))
    for rel in sorted(b - a):
        divergences.append((rel, "ABSENT DE LA REFERENCE", []))

    for rel in sorted(a & b):
        pa, pb = ref / rel, rejeu / rel
        if sha256(pa) == sha256(pb):
            continue
        la = pa.read_text(encoding="utf-8").splitlines()
        lb = pb.read_text(encoding="utf-8").splitlines()
        a_ok, a_hors = _scinder_sortie_v45(la)
        b_ok, b_hors = _scinder_sortie_v45(lb)
        d1 = _diff(a_ok, b_ok, rel, "CONTENU DIFFERENT")
        if d1:
            divergences.append(d1)
        d2 = _diff(a_hors, b_hors, rel,
                   "CONTENU DIFFERENT sur des lignes sortie_v45=non "
                   "- HORS VERDICT (D13)")
        if d2:
            hors_verdict.append(d2)
    return divergences, hors_verdict


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jeux", nargs="*", help="jeux a verifier (defaut : tous)")
    ap.add_argument("--garder", default=None,
                    help="dossier ou conserver le rejeu (non detruit)")
    ap.add_argument("--rejeu", default=None,
                    help="comparer un rejeu deja construit, sans reconstruire")
    ap.add_argument("--reference", default=None,
                    help="dossier de reference a comparer (defaut : "
                         "tests/reference). Utiliser tests/reference_cli pour "
                         "verifier la reference seconde.")
    ap.add_argument("--chemin", choices=["application", "cli"],
                    default="application",
                    help="jeu de parametres du rejeu ; doit correspondre a la "
                         "reference comparee")
    ap.add_argument("--source-differente-assumee", action="store_true",
                    help="D70 : comparer malgre un desaccord entre la source "
                         "qui a produit la reference et celle du rejeu "
                         "demande. Le desaccord est alors repete en tete de "
                         "la sortie.")
    args = ap.parse_args()

    # --- D70, AVANT tout rejeu : un rejeu de vingt minutes lance contre la
    # mauvaise reference coute vingt minutes et une conclusion fausse.
    reference_d70 = (Path(args.reference).resolve() if args.reference else ICI)
    autorise, lignes_d70 = verdict_source(reference_d70, args.chemin,
                                          args.source_differente_assumee)
    for l in lignes_d70:
        print(l)
    print()
    if not autorise:
        return 3

    tous = decouvrir()
    if args.jeux:
        voulus = set(args.jeux)
        jeux = [j for j in tous if j["jeu"] in voulus]
        manquants = voulus - {j["jeu"] for j in tous}
        if manquants:
            print(f"jeux inconnus : {sorted(manquants)}", file=sys.stderr)
            return 2
    else:
        jeux = tous

    temporaire = None
    if args.rejeu:
        rejeu = Path(args.rejeu).resolve()
        if not rejeu.is_dir():
            print(f"dossier de rejeu introuvable : {rejeu}", file=sys.stderr)
            return 2
        print(f"Rejeu fourni : {rejeu.name}")
    else:
        if args.garder:
            rejeu = Path(args.garder).resolve()
            rejeu.mkdir(parents=True, exist_ok=True)
        else:
            temporaire = tempfile.mkdtemp(prefix="thermie_rejeu_")
            rejeu = Path(temporaire)
        print(f"Code rejoue : {CODE}  "
              f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
        _ref = (Path(args.reference).resolve() if args.reference else ICI)
        print(f"Reference comparee : "
              f"{_ref.relative_to(RACINE).as_posix()} "
              f"(construite depuis ref/v4_5, D3) — chemin de parametres : "
              f"{args.chemin}")
        print(f"Rejeu de {len(jeux)} jeu(x), "
              f"{sum(len(j['points']) for j in jeux)} point(s)...")
        build_reference.construire(jeux, rejeu, args.chemin)

    reference = Path(args.reference).resolve() if args.reference else ICI
    try:
        divergences, hors_verdict = comparer(reference, rejeu, jeux)
        n_art = len(artefacts(reference, jeux))
        print(f"\n{n_art} artefact(s) compare(s).")
        if hors_verdict:
            print(f"\n{len(hors_verdict)} artefact(s) divergent(s) sur "
                  f"des lignes HORS VERDICT (sortie_v45=non, D13) - "
                  f"rapportes, non comptes :\n")
            for rel, quoi, extrait in hors_verdict:
                print(f"  ### {rel} - {quoi}")
                for l in extrait:
                    print(f"      {l}")
                print()
        if not divergences:
            print("DIFF VIDE — la reference est reproductible.")
            return 0
        print(f"{len(divergences)} artefact(s) divergent(s) :\n")
        for rel, quoi, extrait in divergences:
            print(f"  ### {rel} — {quoi}")
            for l in extrait:
                print(f"      {l}")
            print()
        return 1
    finally:
        if temporaire:
            shutil.rmtree(temporaire, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
