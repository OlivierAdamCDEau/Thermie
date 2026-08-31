"""
restitution_documentaire.py — ÉTAPE 1, TÂCHE D.

Restitue, sans juger et sans rien proposer :

  D.1  le registre docs/CORRECTIFS_V4_6.md, un correctif par ligne, avec
       vérification de chaque référence « fichier:ligne » contre le code
       réellement observé ;
  D.2  le détecteur de mise hors d'eau de ref/thermie_points/ ;
  D.3  les décisions de docs/MANIFESTE.md qui portent sur la chaîne
       lecture → T_norm ;
  D.4  la structure de data/socle/reconciliation_v45.csv.

LECTURE SEULE (D1, D9)
----------------------
`ref/thermie_points/` ne contient qu'une archive. Elle n'est PAS ré-extraite :
ce module la lit en place avec `zipfile`, sans écrire un seul octet dans
`ref/`. Aucun horodatage de `ref/` n'est modifié.

Sorties :
  out/etape1/correctifs_v46.csv
  docs/etape1_restitution_correctifs.md
  docs/etape1_restitution_thermie_points.md
"""
from __future__ import annotations

import difflib
import re
import zipfile
from pathlib import Path

from _commun import (ICI, RACINE, decouvrir, ecrire_csv, ecrire_texte,
                     nom_point)

REF_V45 = RACINE / "ref" / "v4_5"
ARCHIVE = RACINE / "ref" / "thermie_points" / "thermie_points.zip"
OUT = RACINE / "out" / "etape1"
DOCS = RACINE / "docs"

# Dans l'archive, la copie de V4.5 que le projet clos a utilisée comme
# référentiel — c'est CE code que les « fichier:ligne » du registre visent.
PREFIXE_REF_ARCHIVE = "data/ref_V4_5/"

MODULES = ["io_data.py", "core.py", "qc.py", "config.py", "sniff.py",
           "orchestrator.py", "indicateurs.py", "climatique.py", "app.py",
           "figures.py", "exports.py", "livrables.py", "redaction.py"]

REF_LIGNE = re.compile(
    r"`(" + "|".join(re.escape(m) for m in MODULES) + r"):(\d+)(?:-(\d+))?`")


# ============================================================
# Accès en lecture à l'archive
# ============================================================
class Archive:
    def __init__(self, chemin: Path):
        self.z = zipfile.ZipFile(chemin)
        self._cache = {}

    def texte(self, nom: str) -> str:
        if nom not in self._cache:
            self._cache[nom] = self.z.read(nom).decode("utf-8")
        return self._cache[nom]

    def lignes(self, nom: str):
        return self.texte(nom).splitlines()

    def existe(self, nom: str) -> bool:
        try:
            self.z.getinfo(nom)
            return True
        except KeyError:
            return False


def chemin_archive(module: str) -> str:
    if module == "app.py":
        return PREFIXE_REF_ARCHIVE + "app.py"
    return PREFIXE_REF_ARCHIVE + "thermie_debits/" + module


def chemin_local(module: str) -> Path:
    if module == "app.py":
        return REF_V45 / "app.py"
    return REF_V45 / "thermie_debits" / module


def chemin_app(module: str) -> str:
    if module == "app.py":
        return "app/app.py"
    return "app/thermie_debits/" + module


# ============================================================
# Vérification d'une référence fichier:ligne
# ============================================================
def verifier(arc: Archive, module: str, l1: int, l2: int | None):
    """
    Le « fichier:ligne » cité correspond-il encore au code observé ?

    Le registre a été écrit contre la copie de V4.5 embarquée dans l'archive.
    On lit donc les lignes citées LÀ, puis on cherche le même contenu dans
    ref/v4_5/. Trois issues :
      identique    même numéro de ligne, même contenu ;
      DECALEE      contenu retrouvé, mais à un autre numéro de ligne ;
      INTROUVABLE  contenu non retrouvé dans ref/v4_5.
    """
    l2 = l2 or l1
    nom_arc = chemin_archive(module)
    loc = chemin_local(module)
    if not arc.existe(nom_arc) or not loc.exists():
        return dict(statut="MODULE ABSENT", extrait="", ligne_ref_v45="",
                    commentaire=f"{module} introuvable dans l'archive ou dans ref/v4_5")

    la = arc.lignes(nom_arc)
    ll = loc.read_text(encoding="utf-8").splitlines()
    if l1 > len(la):
        return dict(statut="HORS FICHIER", extrait="", ligne_ref_v45="",
                    commentaire=f"{module} de l'archive ne compte que "
                                f"{len(la)} lignes, la reference vise {l1}")
    bloc = [x.rstrip() for x in la[l1 - 1:l2]]
    extrait = " ⏎ ".join(x.strip() for x in bloc if x.strip())[:220]

    # Le même bloc figure-t-il au même endroit dans ref/v4_5 ?
    if l2 <= len(ll) and [x.rstrip() for x in ll[l1 - 1:l2]] == bloc:
        return dict(statut="identique", extrait=extrait,
                    ligne_ref_v45=f"{module}:{l1}" + (f"-{l2}" if l2 != l1 else ""),
                    commentaire="")

    # Sinon, où est-il passé ?
    ancre = next((x.strip() for x in bloc if len(x.strip()) > 12), "")
    if ancre:
        for i, x in enumerate(ll, 1):
            if x.strip() == ancre:
                delta = i - l1
                return dict(
                    statut="DECALEE", extrait=extrait,
                    ligne_ref_v45=f"{module}:{i}",
                    commentaire=f"meme code, decale de {delta:+d} ligne(s) "
                                f"dans ref/v4_5 (le registre vise l'instantane "
                                f"de l'archive)")
    proches = difflib.get_close_matches(ancre, [x.strip() for x in ll], n=1,
                                        cutoff=0.75) if ancre else []
    if proches:
        i = next(k for k, x in enumerate(ll, 1) if x.strip() == proches[0])
        return dict(statut="MODIFIEE", extrait=extrait,
                    ligne_ref_v45=f"{module}:{i}",
                    commentaire="code voisin mais non identique dans ref/v4_5")
    return dict(statut="INTROUVABLE", extrait=extrait, ligne_ref_v45="",
                commentaire="le code cite n'a pas ete retrouve dans ref/v4_5")


# ============================================================
# D.1 — parcours du registre
# ============================================================
def champs_table(corps: str):
    """Extrait les paires « | Libellé | Valeur |» d'une entrée en table."""
    out = {}
    for l in corps.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$", l)
        if m and not set(m.group(1)) <= {"-", " "}:
            cle = m.group(1).strip()
            if cle and cle != "":
                out[cle] = m.group(2).strip()
    return out


def champ_gras(corps: str, etiquette: str):
    """Extrait un paragraphe introduit par « **Étiquette** »."""
    m = re.search(r"\*\*" + etiquette + r"[^*]*\*\*\s*[:：]?\s*(.+?)(?:\n\n|\Z)",
                  corps, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def table_classement(texte: str):
    """
    Le tableau de tete du registre classe les quatorze incoherences I1..I14 et
    porte, pour chacune, la colonne « A porter en V4.6 (D22) ». Les entrees des
    familles A, B et C n'ont pas cette colonne dans leur propre tableau : elles
    la reprennent de la. On la retrouve par l'identifiant I<n> cite dans leur
    intitule.
    """
    out = {}
    for l in texte.splitlines():
        m = re.match(r"^\|\s*(I\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|",
                     l)
        if m:
            out[m.group(1)] = dict(
                famille=m.group(2).strip(),
                traitement=m.group(3).strip(),
                a_porter=re.sub(r"\*+", "", m.group(4)).strip(),
                motif=m.group(5).strip())
    return out


def lire_registre(arc: Archive):
    src = DOCS / "CORRECTIFS_V4_6.md"
    texte = src.read_text(encoding="utf-8")

    # Étape à laquelle chaque entrée appartient (les « ## » intermédiaires).
    sections = re.split(r"\n(?=## )", texte)
    entrees = []
    for sec in sections:
        titre_sec = sec.splitlines()[0].lstrip("# ").strip()
        for bloc in re.split(r"\n(?=### )", sec)[1:]:
            ligne_titre = bloc.splitlines()[0].lstrip("# ").strip()
            m = re.match(r"^([A-Z]?\d+[a-z]?|Réserve nommée)\s*[—-]\s*(.+)$",
                         ligne_titre)
            if m:
                ident, intitule = m.group(1), m.group(2)
            else:
                ident, intitule = "", ligne_titre
            entrees.append(dict(section=titre_sec, identifiant=ident,
                                intitule=re.sub(r"\*\*", "", intitule),
                                corps=bloc))
    return entrees


def restituer_correctifs(arc: Archive):
    entrees = lire_registre(arc)
    classement = table_classement(
        (DOCS / "CORRECTIFS_V4_6.md").read_text(encoding="utf-8"))
    lignes, details = [], []
    for e in entrees:
        corps = e["corps"]
        t = champs_table(corps)
        refs = REF_LIGNE.findall(corps)
        verifs = []
        for module, a, b in refs:
            v = verifier(arc, module, int(a), int(b) if b else None)
            v["citation"] = f"{module}:{a}" + (f"-{b}" if b else "")
            v["module"] = module
            verifs.append(v)
        modules = sorted({v["module"] for v in verifs})

        justif = (t.get("Justification") or t.get("Défaut constaté")
                  or champ_gras(corps, "Classement en famille")
                  or champ_gras(corps, "Justification") or "")
        impact = (t.get("Impact chiffré") or champ_gras(corps, "Constat")
                  or champ_gras(corps, "Écart mesuré")
                  or champ_gras(corps, "Mesure") or "")
        if not impact:
            m = re.search(r"\*\*Écart mesuré[^*]*\*\*\s*[:：]\s*(.+?)(?:\n\n|\Z)",
                          corps, re.S)
            impact = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

        # « À porter en V4.6 » est un paragraphe en gras, pas une ligne de
        # tableau : il faut l'extraire a part.
        mp = re.search(r"\*\*À porter en V4\.6\s*:\s*([^*]+?)\*\*", corps)
        a_porter = t.get("À porter en V4.6", "")
        if not a_porter and mp:
            a_porter = mp.group(1).strip().rstrip(".")
        if not a_porter:
            # Repli sur le tableau de classement, par l'identifiant I<n> que
            # l'intitule de l'entree cite.
            mi = re.match(r"^(I\d+)\b", e["intitule"])
            if mi and mi.group(1) in classement:
                a_porter = (classement[mi.group(1)]["a_porter"]
                            + f" (repris du tableau de classement, {mi.group(1)})")
        statuts = sorted({v["statut"] for v in verifs})
        lignes.append(dict(
            identifiant=e["identifiant"], section=e["section"],
            intitule=e["intitule"],
            reference_v45_citee=" | ".join(v["citation"] for v in verifs),
            reference_telle_qu_ecrite=_court(
                t.get("Référence V4.5") or t.get("Référence") or "", 200),
            comportement_actuel=_court(t.get("Comportement actuel", "")),
            comportement_retenu=_court(t.get("Comportement retenu", "")),
            justification=_court(justif),
            impact_chiffre=_court(impact),
            a_porter_en_v46=a_porter,
            fichiers_app_touches=" | ".join(chemin_app(m) for m in modules),
            statut_des_references=" | ".join(statuts),
            reference_dans_ref_v4_5=" | ".join(
                v["ligne_ref_v45"] for v in verifs if v["ligne_ref_v45"])))
        details.append((e, verifs))
    return lignes, details


def _court(s, n=600):
    s = re.sub(r"\s+", " ", re.sub(r"\*\*", "", str(s))).strip()
    return s[:n] + ("…" if len(s) > n else "")


COLS = ["identifiant", "section", "intitule", "reference_telle_qu_ecrite",
        "reference_v45_citee",
        "reference_dans_ref_v4_5", "statut_des_references",
        "fichiers_app_touches", "comportement_actuel", "comportement_retenu",
        "justification", "impact_chiffre", "a_porter_en_v46"]


def ecrire_d1(lignes, details):
    ecrire_csv(OUT / "correctifs_v46.csv", COLS, lignes,
               tri=["section", "identifiant", "intitule"])

    n_ref = sum(1 for _, v in details for _ in v)
    decalees = [(e["identifiant"], x) for e, vs in details for x in vs
                if x["statut"] != "identique"]
    txt = [
        "# Étape 1 · D.1 — restitution du registre `docs/CORRECTIFS_V4_6.md`",
        "",
        "Restitution seule : aucune appréciation, aucune proposition. **Lire "
        "ce registre ne vaut pas autorisation de l'appliquer** (D10).",
        "",
        "## Ce que vise le registre",
        "",
        "Le registre annonce en tête qu'il se compare à "
        "`data/ref_V4_5/thermie_debits`, c'est-à-dire à la copie de V4.5 "
        "**embarquée dans `thermie_points.zip`**. Cette copie n'est pas "
        "`ref/v4_5/` : elle correspond au commit `bb70055` (« V4.5 barbeau »), "
        "quand `ref/v4_5/` est au commit suivant `83ff67e` (« V4.5 message "
        "erreur amélioré »). Six fichiers diffèrent. **Toute référence "
        "`fichier:ligne` du registre est donc à lire contre l'instantané de "
        "l'archive**, et le tableau ci-dessous dit, pour chacune, où le même "
        "code se trouve aujourd'hui dans `ref/v4_5/`.",
        "",
        f"{len(lignes)} entrée(s) de registre, {n_ref} référence(s) "
        f"`fichier:ligne`, dont **{len(decalees)}** ne pointent plus sur la "
        "même ligne dans `ref/v4_5/`.",
        "",
        "## Tableau du registre",
        "",
        "| Id | Intitulé | `fichier:ligne` cité | État de la référence | "
        "Fichiers de `app/` touchés | Justification (telle qu'écrite) | "
        "Impact chiffré (tel qu'écrit) | À porter en V4.6 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for l in lignes:
        txt.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
            l["identifiant"] or "—", _md(l["intitule"]),
            _md(l["reference_v45_citee"]) or "—",
            _md(l["statut_des_references"]) or "—",
            _md(l["fichiers_app_touches"]) or "—",
            _md(_court(l["justification"], 300)) or "—",
            _md(_court(l["impact_chiffre"], 300)) or "—",
            _md(l["a_porter_en_v46"]) or "—"))

    txt += ["", "## Références qui ne pointent plus sur la même ligne", "",
            "Le contenu cité a été retrouvé dans `ref/v4_5/` à un autre "
            "numéro de ligne, ou pas retrouvé. C'est une information, pas un "
            "défaut du registre : `ref/v4_5/` a un commit d'avance sur la "
            "copie contre laquelle il a été écrit.", "",
            "| Id | Citation | État | Où dans `ref/v4_5/` | Code cité "
            "(archive) |", "|---|---|---|---|---|"]
    for ident, v in decalees:
        txt.append("| {} | `{}` | {} | {} | `{}` |".format(
            ident or "—", v["citation"], v["statut"],
            f"`{v['ligne_ref_v45']}`" if v["ligne_ref_v45"] else "—",
            _md(v["extrait"])))
    txt.append("")
    ecrire_texte(DOCS / "etape1_restitution_correctifs.md", "\n".join(txt) + "\n")
    return len(lignes), len(decalees)


def _md(s):
    return re.sub(r"\s+", " ", str(s)).replace("|", "\\|").strip()


# ============================================================
# D.2 — détecteur de mise hors d'eau de thermie_points
# ============================================================
def extraire(arc: Archive, nom: str, motif: str, avant=0, apres=40):
    """Retourne (numero_de_ligne, extrait) de la première occurrence."""
    lignes = arc.lignes(nom)
    for i, l in enumerate(lignes, 1):
        if re.search(motif, l):
            return i, "\n".join(lignes[max(0, i - 1 - avant): i - 1 + apres])
    return None, ""


def restituer_thermie_points(arc: Archive):
    P = "thermie_points/"
    txt = ["# Étape 1 · D.2 — le détecteur de mise hors d'eau de "
           "`ref/thermie_points/`", "",
           "Restitution seule. `ref/thermie_points/` ne contient qu'une "
           "archive ; elle est lue en place, jamais ré-extraite (D9), et rien "
           "n'est écrit dans `ref/` (D1). Les numéros de ligne renvoient aux "
           "fichiers **tels qu'ils sont dans l'archive**.", ""]

    # --- Fonctions concernées ---
    txt += ["## Les fonctions, avec fichier:ligne", "",
            "| Fichier (dans l'archive) | Ligne | Fonction | Rôle |",
            "|---|---|---|---|"]
    fonctions = [
        (P + "qualite.py", r"^def calculer_signatures", "calculer_signatures",
         "calcule les trois signatures R_ampl, E_min, E_max sur la fenêtre "
         "d'examen, et restreint les jours diagnosticables"),
        (P + "qualite.py", r"^def ajouter_reference_par_point",
         "ajouter_reference_par_point",
         "relativise une signature à la médiane du même point au même mois"),
        (P + "qualite.py", r"^def marquer_episodes", "marquer_episodes",
         "déclenchement, prolongation par hystérésis, marge calendaire, fusion"),
        (P + "criteres.py", r"^def ajouter_grandeurs_relativisees",
         "ajouter_grandeurs_relativisees",
         "ajoute E_max_rel (écart) et R_ampl_rel (rapport)"),
        (P + "criteres.py", r"^def appliquer_couple", "appliquer_couple",
         "applique le couple de conditions EN CONJONCTION"),
        (P + "criteres.py", r"^def couverture_analytique", "couverture_analytique",
         "déclare, point par point et par le calcul, si la détection est opérante"),
        (P + "criteres.py", r"^def couverture_par_saison", "couverture_par_saison",
         "même déclaration, par point ET par saison"),
        (P + "criteres.py", r"^def garde_fou", "garde_fou",
         "ajoute le plancher R_ampl au candidat, si l'artefact est confirmé"),
        (P + "criteres.py", r"^def plancher_r_ampl", "plancher_r_ampl",
         "calcule le plancher comme quantile de R_ampl sur les négatifs terrain"),
        (P + "criteres.py", r"^def rejouer_selection", "rejouer_selection",
         "rejoue la règle de sélection, garde-fous compris"),
        (P + "fiches.py", r"^def extraire_episodes", "extraire_episodes",
         "regroupe les jours marqués en épisodes, avec hystérésis et fusion"),
    ]
    for fic, motif, nom, role in fonctions:
        i, _ = extraire(arc, fic, motif)
        txt.append(f"| `{fic}` | {i or '—'} | `{nom}` | {role} |")

    # --- Entrées exigées ---
    txt += ["", "## Les entrées exigées", "",
            "| Grandeur | Définition | Entrée exigée |", "|---|---|---|",
            "| `R_ampl` | `(T_eau_max − T_eau_min) / (TX − TN)` | extrêmes "
            "journaliers d'eau **et** `TX` et `TN` de la station d'air |",
            "| `E_min` | `T_eau_min − TN` | `T_eau_min` et `TN` |",
            "| `E_max` | `T_eau_max − TX` | `T_eau_max` et `TX` |",
            "| `E_max_rel` | `E_max −` médiane de `E_max` du même point au "
            "même mois | l'historique du point, mois par mois |",
            "| `R_ampl_rel` | `R_ampl /` médiane de `R_ampl` du même point au "
            "même mois | idem |", "",
            "Les extrêmes journaliers ne sont retenus que sur les jours de "
            "niveau « complet », c'est-à-dire construits à partir de mesures "
            "infra-journalières suffisamment denses. **Le détecteur exige donc "
            "TN, TX et de l'infra-journalier ; il ne fonctionne pas sur une "
            "moyenne journalière seule.**", ""]

    # --- Paramètres ---
    txt += ["## Les paramètres et leurs valeurs", "",
            "| Constante | Valeur | Fichier:ligne | Ce qu'elle règle |",
            "|---|---|---|---|"]
    constantes = [
        (P + "qualite.py", r"^AMPL_AIR_MIN\s*=", "AMPL_AIR_MIN",
         "amplitude d'air minimale sous laquelle le jour n'est pas "
         "diagnosticable"),
        (P + "qualite.py", r"^EPISODE_MIN_JOURS\s*=", "EPISODE_MIN_JOURS",
         "longueur minimale d'une séquence pour ouvrir un épisode"),
        (P + "qualite.py", r"^EPISODE_MARGE_JOURS\s*=", "EPISODE_MARGE_JOURS",
         "marge ajoutée de part et d'autre d'un épisode"),
        (P + "criteres.py", r"^QUANTILE_PLANCHER\s*=", "QUANTILE_PLANCHER",
         "quantile de R_ampl sur les négatifs terrain, pour le garde-fou strict"),
        (P + "criteres.py", r"^QUANTILE_PLANCHER_PROLONGATION\s*=",
         "QUANTILE_PLANCHER_PROLONGATION",
         "quantile relâché, pour la seule prolongation"),
        (P + "criteres.py", r"^PROLONGATION\s*=", "PROLONGATION",
         "couple relâché du maintien (hystérésis)"),
        (P + "criteres.py", r"^SPECIFICITE_MIN\s*=", "SPECIFICITE_MIN",
         "spécificité minimale exigée par la règle de sélection"),
        (P + "criteres.py", r"^COUVERTURE_MIN_POINTS\s*=", "COUVERTURE_MIN_POINTS",
         "part des points devant détecter à w = 1"),
        (P + "fiches.py", r"^FUSION_JOURS\s*=", "FUSION_JOURS",
         "écart maximal entre deux épisodes pour qu'ils soient fusionnés"),
        (P + "fiches.py", r"^MARGE_JOURS\s*=", "MARGE_JOURS",
         "marge affichée autour d'un épisode sur la fiche (affichage seul)"),
        (P + "etape4.py", r"^CRITERE_RETENU\s*=", "CRITERE_RETENU",
         "le couple retenu à l'étape 4"),
        (P + "etape4.py", r"^VARIANTE_PLANCHER_060\s*=", "VARIANTE_PLANCHER_060",
         "la variante conservée pour comparaison"),
        (P + "etape5.py", r"^CRITERE_ETAPE5\s*=", "CRITERE_ETAPE5",
         "le vainqueur de la sélection rejouée à l'étape 5"),
        (P + "common.py", r"^MOIS_ESTIVAUX\s*=", "MOIS_ESTIVAUX",
         "fenêtre d'examen par défaut"),
        (P + "common.py", r"^MARGE_TX_C\s*=", "MARGE_TX_C",
         "marge du signalement indépendant fondé sur TX (n'exclut rien)"),
        (P + "common.py", r"^TROU_MAX_COMPLET_H\s*=", "TROU_MAX_COMPLET_H",
         "trou maximal pour qu'un jour soit « complet »"),
        (P + "common.py", r"^HEURES_MIN_COMPLET\s*=", "HEURES_MIN_COMPLET",
         "heures minimales renseignées pour qu'un jour soit « complet »"),
        (P + "common.py", r"^TROU_MAX_VALIDE_H\s*=", "TROU_MAX_VALIDE_H",
         "trou maximal pour qu'un jour soit « valide »"),
    ]
    for fic, motif, nom, role in constantes:
        i, _ = extraire(arc, fic, motif, apres=1)
        val = ""
        if i:
            lignes_f = arc.lignes(fic)
            val = lignes_f[i - 1].split("=", 1)[1].strip()
            j = i
            while val.count("{") > val.count("}") and j < len(lignes_f):
                val += " " + lignes_f[j].strip()
                j += 1
            val = re.sub(r"\s*#.*$", "", val).strip()
        txt.append(f"| `{nom}` | `{_md(val)}` | `{fic}:{i or '—'}` | {role} |")

    txt += ["", "## La règle, en conjonction", "",
            "`criteres.appliquer_couple` applique **deux conditions et leur "
            "conjonction**, jamais leur disjonction. La raison est écrite dans "
            "la fonction : le maximum d'un cours d'eau peu profond et exposé "
            "peut dépasser `TX` par rayonnement direct sans exondation ; seule "
            "la conjonction de deux signatures désigne une sonde hors d'eau.",
            "",
            "Quatre couples candidats sont définis (`criteres.CANDIDATS`), et "
            "le sens de chaque comparaison compte : sous exondation `E_min` "
            "**descend** vers 0 tandis que `E_max` **monte**. Le couple retenu "
            "à l'étape 4 est `R_ampl_rel > 1,5` **ET** `E_max_rel > 1,5`, "
            "assorti du garde-fou `R_ampl > 0,67`. Le vainqueur de la "
            "sélection rejouée à l'étape 5 est `R_ampl > plancher` **ET** "
            "`E_max_rel > 1,0`.", "",
            "## L'hystérésis", "",
            "`qualite.marquer_episodes` enchaîne trois mécanismes, dans cet "
            "ordre :", "",
            "1. **Déclenchement** — une séquence d'au moins "
            "`EPISODE_MIN_JOURS` jours suspects **consécutifs dans le "
            "calendrier** ouvre un épisode ; un jour suspect isolé est signalé "
            "sans exclure.",
            "2. **Prolongation** — une fois l'épisode ouvert, il s'étend de "
            "part et d'autre tant que le critère **relâché** `PROLONGATION` "
            "reste vérifié. La prolongation ne peut jamais *ouvrir* un "
            "épisode.",
            "3. **Fusion** — deux épisodes séparés de moins de `FUSION_JOURS` "
            "jours sont fusionnés, et les jours intercalaires marqués.", "",
            "La marge est **calendaire et non positionnelle** : la série "
            "n'est indexée que sur juin-septembre, si bien qu'une marge "
            "positionnelle rattacherait le 30 septembre d'une année au 1er "
            "juin de la suivante.", "",
            "## Valeurs codées en dur, et hypothèses implicites sur les "
            "données", "",
            "| Valeur / hypothèse | Où | Ce qu'elle suppose |", "|---|---|---|",
            "| `AMPL_AIR_MIN = 6.0` °C | `qualite.py` | que le dénominateur "
            "`TX − TN` soit assez grand pour que le rapport ait un sens ; en "
            "deçà, le jour est déclaré non diagnosticable, ni marqué ni sain |",
            "| Seuils `1,5` / `1,5` et plancher `0,67` | `etape4.py` | calés "
            "sur la distribution du bassin de la Bienne et sur des négatifs "
            "terrain ; ce sont des propriétés du jeu, pas de la méthode |",
            "| `POINTS_RESERVE` et `GROUPES_RELECTURE` | `fiches.py` | des "
            "codes de points du bassin de la Bienne sont écrits en dur, ainsi "
            "qu'un **jugement humain** de relecture attaché à un couple "
            "(point, année) |",
            "| `STATION_REFERENCE = \"LA_PESSE\"` | `common.py` | une station "
            "d'air unique, nommée en dur, plus haute et plus froide que les "
            "sites — c'est cette asymétrie qui donne sa marge à `E_max` et la "
            "retire à `E_min` |",
            "| `NOMS_COURS_EAU = {\"BIE\": \"Bienne\"}` et "
            "`MOTIF_CODE_POINT` | `common.py` | que les codes de points "
            "suivent la nomenclature à trois lettres du réseau de la Bienne |",
            "| `MOIS_ESTIVAUX = (6, 7, 8, 9)` | `common.py` | que l'exondation "
            "soit un phénomène estival ; l'émersion hivernale a une signature "
            "**inverse** et relève d'autres contrôles |",
            "| Niveau de jour « complet » | `common.py` | de l'infra-"
            "journalier dense : aucun trou > 3 h et au moins 20 h renseignées. "
            "Une chronique déjà agrégée au jour ne peut pas satisfaire ce "
            "critère |",
            "| `TN` et `TX` de la station d'air | partout | qu'ils soient lus "
            "et transmis. La chaîne de V4.5 ne les lit pas (`io_data.py:432`) |",
            ""]
    ecrire_texte(DOCS / "etape1_restitution_thermie_points.md",
                 "\n".join(txt) + "\n")




# ============================================================
# D.3 — MANIFESTE.md, décisions portant sur lecture -> T_norm
# ============================================================
# Le périmètre du chantier est la chaîne « lecture des fichiers -> T_norm »
# (D4). Une décision du manifeste en relève si elle change une valeur de cette
# chaîne. Les autres sont listées par titre, sans être développées.
PORTE_SUR_LA_CHAINE = {
    "Station d'air de référence": (
        "La station d'air fixe la normale journaliere, donc Delta_TMm, donc "
        "T_air_std et la temperature normalisee. Elle fixe aussi la periode "
        "de reference effective, que V4.5 code en dur a 1991-2020 "
        "(io_data.py:306) mais calcule sur les seules annees disponibles "
        "(io_data.py:511-512)."),
}


def _citation(bloc: str) -> str:
    """Bloc de citation Markdown, sans ligne vide en tete ni en queue."""
    corps = [l.rstrip() for l in bloc.splitlines()[1:]]
    while corps and not corps[0].strip():
        corps.pop(0)
    while corps and not corps[-1].strip():
        corps.pop()
    return "\n".join(("> " + l).rstrip() for l in corps)


def restituer_manifeste(arc: Archive):
    texte = arc.texte("docs/MANIFESTE.md")
    # Les décisions sont les « ### » de la section 5.
    m = re.search(r"\n## 5\.(.*?)(?=\n## 6\.)", texte, re.S)
    section5 = m.group(1) if m else ""
    blocs = re.split(r"\n(?=### )", section5)
    decisions = []
    for b in blocs[1:]:
        titre = b.splitlines()[0].lstrip("# ").strip()
        decisions.append((titre, b))

    txt = ["# Étape 1 · D.3 — `docs/MANIFESTE.md`, ce qui porte sur la chaîne "
           "lecture → T_norm", "",
           "Restitution seule. Les décisions retenues sont **citées telles "
           "quelles**, sans reformulation. Les autres sont listées par titre "
           "et ne sont pas développées.", "",
           "Le manifeste est lu dans `ref/thermie_points/thermie_points.zip` "
           "(`docs/MANIFESTE.md`), en place, sans ré-extraction (D9).", "",
           "## Décisions qui portent sur la chaîne lecture → T_norm", ""]
    retenues = [d for d in decisions if d[0] in PORTE_SUR_LA_CHAINE]
    if not retenues:
        txt.append("Aucune.")
    for titre, bloc in retenues:
        txt += [f"### {titre}", "",
                f"*Pourquoi cette décision relève du périmètre :* "
                f"{PORTE_SUR_LA_CHAINE[titre]}", "",
                "Citation intégrale :", "",
                _citation(bloc), ""]

    txt += ["## Décisions hors périmètre — titres seuls", "",
            "Elles sont nommées, non développées : les développer reviendrait "
            "à ouvrir un débat que l'étape 1 n'a pas à ouvrir.", ""]
    for titre, _ in decisions:
        if titre not in PORTE_SUR_LA_CHAINE:
            txt.append(f"- {titre}")

    # Les autres sections du manifeste, par titre.
    autres = re.findall(r"^## (.+)$", texte, re.M)
    txt += ["", "## Autres sections du manifeste — titres seuls", ""]
    for a in autres:
        txt.append(f"- {a.strip()}")
    txt.append("")
    ecrire_texte(DOCS / "etape1_restitution_manifeste.md", "\n".join(txt) + "\n")
    return len(retenues), len(decisions)


# ============================================================
# D.4 — reconciliation_v45.csv
# ============================================================
def restituer_reconciliation(arc: Archive, jeux):
    chemin = "data/socle/reconciliation_v45.csv"
    if not arc.existe(chemin):
        ecrire_texte(DOCS / "etape1_restitution_reconciliation.md",
                     "# Étape 1 · D.4\n\nFichier introuvable dans l'archive.\n")
        return
    lignes = arc.texte(chemin).splitlines()
    entete = [c.strip() for c in lignes[0].lstrip("\ufeff").split(";")]
    corps = [l.split(";") for l in lignes[1:] if l.strip()]
    points = sorted(r[0] for r in corps)

    # Les colonnes se lisent « <grandeur> <statistique> — <convention> ».
    grandeurs, stats_, conventions = [], [], []
    for c in entete[4:]:
        m = re.match(r"^(\S+)\s+(\S+)\s+—\s+(.+)$", c)
        if m:
            grandeurs.append(m.group(1))
            stats_.append(m.group(2))
            conventions.append(m.group(3))

    # Ce que le harnais possède, point par point.
    # thermie_points normalise les codes de points : le suffixe « __NA » du
    # nom de fichier n'apparait pas dans ses tables (common.MOTIF_CODE_POINT).
    # On apparie donc sur le code normalise, et on le dit.
    def code(nom):
        return re.sub(r"__NA$|_regroup$", "", nom)
    pts_harnais = {code(nom_point(p)): nom_point(p)
                   for j in jeux for p in j["points"]}
    couverts = sorted(p for p in points if p in pts_harnais)
    absents_harnais = sorted(p for p in points if p not in pts_harnais)
    absents_csv = sorted(v for k, v in pts_harnais.items() if k not in set(points))
    renommes = sorted(f"{v} -> {k}" for k, v in pts_harnais.items() if k != v)

    txt = [
        "# Étape 1 · D.4 — `data/socle/reconciliation_v45.csv`", "",
        "Restitution seule : la structure est décrite, **aucun écart n'est "
        "recalculé** à ce stade.", "",
        "Le fichier est lu dans `ref/thermie_points/thermie_points.zip`, en "
        "place, sans ré-extraction (D9).", "",
        "## Structure", "",
        f"- {len(corps)} lignes de données, {len(entete)} colonnes, "
        f"séparateur `;`, BOM UTF-8, virgule décimale.",
        "- Une ligne par **point de mesure**, pas par date : le fichier ne "
        "porte aucune chronique, seulement des statistiques agrégées.",
        "",
        "### Les grandeurs comparées", "",
        "| Grandeur | Statistiques | Conventions comparées | Unité de l'écart |",
        "|---|---|---|---|",
        "| `Tmh_norm` | médiane, p95, maximum | thermie_points / convention "
        "V4.5 | °C |",
        "| `Tmax_norm` | médiane, p95, maximum | thermie_points / convention "
        "V4.5 | °C |",
        "| Jours retenus | effectif | thermie_points / convention V4.5 | "
        "jours, plus une part conservée en % |",
        "",
        "Chaque triplet est écrit trois fois : la valeur sous chaque "
        "convention, puis leur différence, en colonne `… — écart`. **L'unité "
        "d'écart est le degré Celsius** pour les températures normalisées, le "
        "**jour** pour les effectifs, le **point de pourcentage** pour la part "
        "conservée.",
        "",
        "### Ce que l'écart isole, d'après `thermie_points/reconciliation.py`",
        "",
        "> Les deux versions sont calculées dans la **même chaîne**, à partir "
        "des mêmes colonnes de la couche L2 : `qc_ok` pour thermie_points, "
        "`qc_ok_v45` pour la convention V4.5. […] L'écart mesuré isole donc "
        "exactement les familles **D1 et D2** du registre […]. C'est une "
        "limite de la mesure et il faut la dire : ce n'est pas « V4.5 rejoué "
        "intégralement », c'est « la convention d'exclusion de V4.5 appliquée "
        "à nos données corrigées ».",
        "",
        "## Période couverte", "",
        "Le fichier **ne porte aucune colonne de date** : ni période, ni année. "
        "La période n'est donc pas lisible dans le fichier lui-même. Elle se "
        "déduit du contexte du projet clos — la fenêtre estivale "
        "(juin-septembre) des chroniques du bassin de la Bienne — mais elle "
        "n'y est pas écrite.",
        "",
        "## Les points couverts", "",
        f"- {len(points)} points dans le fichier.",
        f"- **{len(couverts)}** de ces points sont dans le corpus `data/` et "
        f"donc dans le harnais.",
        f"- **{len(absents_harnais)}** point(s) du fichier ne sont pas dans le "
        f"corpus : {', '.join(absents_harnais) if absents_harnais else '—'}.",
        f"- **{len(absents_csv)}** point(s) du corpus ne sont pas dans le "
        f"fichier : {', '.join(absents_csv) if absents_csv else '—'}.",
        "  Les points des jeux `jeu_02` a `jeu_05` et `jeu_exemples_v45` en "
        "font partie par construction : le fichier ne couvre que le bassin de "
        "la Bienne. Ceux du bassin de la Bienne qui n'y figurent pas sont "
        "signales ci-dessous.",
        f"- Point(s) du bassin de la Bienne absent(s) du fichier : "
        f"{', '.join(p for p in absents_csv if p in _codes_bienne(jeux)) or '—'}.",
        f"- Appariement par code normalise (le suffixe `__NA` du nom de "
        f"fichier ne figure pas dans les tables du projet clos) : "
        f"{', '.join(renommes) if renommes else 'aucun renommage necessaire'}.",
        "",
        "## Les artefacts du harnais permettraient-ils de recalculer ces "
        "écarts ?", "",
        "| Grandeur du fichier | Artefact du harnais | Recalculable ? |",
        "|---|---|---|",
        "| `Tmh_norm` médiane / p95 / maximum | `07_t_norm.csv`, grandeur "
        "`Tmh_norm` | **oui**, côté convention V4.5 seulement |",
        "| `Tmax_norm` médiane / p95 / maximum | `07_t_norm.csv`, grandeur "
        "`Tmax_norm` | **oui**, côté convention V4.5 seulement |",
        "| Jours retenus — convention V4.5 | `02_effectifs.csv`, colonne "
        "`journees_retenues_apres_fusion` | **oui** |",
        "| Jours retenus — thermie_points | aucun | **non** : le harnais "
        "n'exécute que `ref/v4_5/` (D3) |",
        "| `… — écart` | — | **non** : un écart exige les deux côtés |",
        "",
        "Autrement dit : le harnais fournit **une** des deux colonnes de "
        "chaque paire. La colonne thermie_points ne peut venir que du projet "
        "clos ou d'un rejeu de son code, ce que l'étape 1 ne fait pas.",
        "",
        "Deux réserves s'ajoutent, et elles ne sont pas mineures :",
        "",
        f"1. La fenêtre n'est pas la même. Le fichier agrège la fenêtre "
        f"estivale ; `07_t_norm.csv` porte **toutes** les journées retenues. "
        f"Un filtre sur juin-septembre serait nécessaire, et il n'est pas "
        f"écrit dans le fichier — il se lit dans `reconciliation.py`.",
        f"2. Sur les {len(couverts)} points communs, **"
        f"{len([p for p in couverts if pts_harnais[p] in _points_en_echec()])}"
        f"** font échouer la chaîne de V4.5 dans le harnais : ils ne "
        f"produisent aucune valeur de `Tmh_norm`, donc aucun terme à "
        f"comparer.",
        "",
    ]
    ecrire_texte(DOCS / "etape1_restitution_reconciliation.md",
                 "\n".join(txt) + "\n")


def _codes_bienne(jeux):
    """Noms de points du jeu de la Bienne, tels que le corpus les nomme."""
    for j in jeux:
        if j["jeu"] == "jeu_bienne":
            return {nom_point(p) for p in j["points"]}
    return set()


def _points_en_echec():
    """Points dont la chaîne de V4.5 échoue, lus dans les artefacts figés."""
    import json
    out = set()
    for p in sorted((ICI).glob("*/00_format_detecte.json")):
        for e in json.loads(p.read_text(encoding="utf-8")):
            if e.get("statut") == "ECHEC":
                out.add(e["point"])
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    arc = Archive(ARCHIVE)
    lignes, details = restituer_correctifs(arc)
    n, n_dec = ecrire_d1(lignes, details)
    restituer_thermie_points(arc)
    n_ret, n_tot = restituer_manifeste(arc)
    restituer_reconciliation(arc, decouvrir())
    print(f"correctifs_v46.csv : {n} entrees")
    print(f"etape1_restitution_correctifs.md : {n_dec} reference(s) decalee(s)")
    print("etape1_restitution_thermie_points.md : ecrit")
    print(f"etape1_restitution_manifeste.md : {n_ret}/{n_tot} decision(s) "
          f"dans le perimetre")
    print("etape1_restitution_reconciliation.md : ecrit")


if __name__ == "__main__":
    main()
