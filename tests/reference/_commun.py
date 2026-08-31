"""
_commun.py — socle partagé du harnais de non-régression (ÉTAPE 1, TÂCHE B).

Contient : la découverte des jeux, les wrappers de journalisation INERTES
(D8), l'écriture déterministe des artefacts (D5) et le manifeste SHA-256.

RÈGLES TENUES ICI
-----------------
D1  ref/v4_5/ et ref/thermie_points/ sont en lecture seule : ce module n'y
    écrit rien et n'y modifie aucun horodatage.
D2  aucun fichier de app/ n'est touché.
D3  la chaîne exécutée est celle de ref/v4_5/, insérée en tête de sys.path.
D5  artefacts texte UTF-8, séparateur « ; », tri stable et explicite, aucun
    horodatage ni chemin absolu, flottants à 6 décimales fixes.
D8  les wrappers enveloppent, journalisent et RETOURNENT LA VALEUR REÇUE SANS
    LA TOUCHER. Un wrapper qui modifierait un retour serait une modification
    du code de référence, donc interdit.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # aucune fenêtre, aucun backend interactif

import pandas as pd

ICI = Path(__file__).resolve().parent            # tests/reference
RACINE = ICI.parent.parent                       # THERMIE_BIO_V4_6
REF_V45 = RACINE / "ref" / "v4_5"
DATA = RACINE / "data"

APP = RACINE / "app"

# D1 — ref/ est en LECTURE SEULE, et cela se vérifie sur les horodatages.
# Importer un module y écrit un __pycache__/*.pyc : c'est une écriture dans
# ref/, silencieuse (le .gitignore la masque à `git status`) mais réelle. On
# la désactive AVANT le premier import de thermie_debits.
sys.dont_write_bytecode = True

# QUEL CODE LE HARNAIS EXÉCUTE-T-IL ?
#
# D3 attache la RÉFÉRENCE au code figé : elle a été construite depuis
# `ref/v4_5/`, et cela ne change pas. Mais à partir du correctif 3, il faut
# pouvoir REJOUER le corpus avec le code de `app/` pour le comparer à cette
# référence — c'est très exactement l'objet d'un harnais de non-régression.
#
#   THERMIE_CODE=ref  (défaut)  ref/v4_5/  — reconstruire la référence
#   THERMIE_CODE=app            app/       — vérifier une modification
#
# Le choix est explicite et se lit dans chaque exécution : jamais implicite.
CODE = os.environ.get("THERMIE_CODE", "ref").strip().lower()
if CODE not in ("ref", "app"):
    raise SystemExit(f"THERMIE_CODE doit valoir 'ref' ou 'app', pas {CODE!r}")
RACINE_CODE = REF_V45 if CODE == "ref" else APP

for _p in (str(REF_V45), str(APP)):
    while _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, str(RACINE_CODE))             # D3

DEC = 6                                          # D5 : 6 décimales fixes
SEP = ";"


# ============================================================
# Découverte du corpus
# ============================================================
def _fichiers(dossier: Path):
    if not dossier.is_dir():
        return []
    return sorted((p for p in dossier.iterdir()
                   if p.is_file() and p.suffix.lower() not in (".md", ".txt")),
                  key=lambda p: p.name)


def decouvrir():
    """
    Retourne la liste ordonnée des jeux : [{jeu, air, debit, points:[...]}].

    Un « point » est un fichier de eau/. Un jeu à 27 fichiers d'eau a donc 27
    points, chacun rejoué séparément contre la même chronique d'air : c'est
    ainsi que l'outil en service est utilisé (une sonde à la fois).
    """
    jeux = []
    for d in sorted((p for p in DATA.iterdir() if p.is_dir()),
                    key=lambda p: p.name):
        eaux = _fichiers(d / "eau")
        if not eaux:
            continue
        airs = _fichiers(d / "air")
        debits = _fichiers(d / "debit")
        jeux.append(dict(
            jeu=d.name,
            air=airs[0].relative_to(RACINE).as_posix() if airs else None,
            n_air=len(airs),
            debit=debits[0].relative_to(RACINE).as_posix() if debits else None,
            n_debit=len(debits),
            points=[e.relative_to(RACINE).as_posix() for e in eaux]))
    return jeux


def nom_point(chemin_rel: str) -> str:
    """Identifiant de point : nom de fichier sans extension, tel quel."""
    return Path(chemin_rel).stem


# ============================================================
# Wrappers de journalisation INERTES (D8)
# ============================================================
class Journal:
    """
    Collecte ce que les fonctions de ref/v4_5 ont vu et conclu, sans rien
    changer à ce qu'elles retournent.
    """

    def __init__(self):
        self.formats = []          # appels à sniff.lire_brut
        self.colonnes = []         # appels à sniff.deviner_colonnes
        self.eau = []              # appels à io_data.charger_eau
        self.air = []              # appels à io_data.charger_air_brut
        self.normales = []         # appels à io_data.calculer_normales_ecarts
        self.m_saisonnier = []     # appels à core._m_saisonnier
        self.lecture = []          # CORRECTIF 10 — mesures ecartees a la lecture

    def installer(self):
        """
        Remplace les fonctions par des enveloppes qui journalisent puis
        retournent l'objet reçu, à l'identique. Retourne le dict des originaux
        pour restauration.
        """
        from thermie_debits import sniff, io_data, core

        originaux = {
            (sniff, "lire_brut"): sniff.lire_brut,
            (sniff, "deviner_colonnes"): sniff.deviner_colonnes,
            (io_data, "lire_brut"): io_data.lire_brut,
            (io_data, "deviner_colonnes"): io_data.deviner_colonnes,
            (io_data, "charger_eau"): io_data.charger_eau,
            (io_data, "charger_air_brut"): io_data.charger_air_brut,
            (io_data, "calculer_normales_ecarts"): io_data.calculer_normales_ecarts,
            (core, "_m_saisonnier"): core._m_saisonnier,
        }
        j = self

        _lire_brut = originaux[(sniff, "lire_brut")]
        _deviner = originaux[(sniff, "deviner_colonnes")]
        _eau = originaux[(io_data, "charger_eau")]
        _airb = originaux[(io_data, "charger_air_brut")]
        _norm = originaux[(io_data, "calculer_normales_ecarts")]
        _ms = originaux[(core, "_m_saisonnier")]

        def lire_brut(source, *a, **k):
            res = _lire_brut(source, *a, **k)
            df, meta = res
            j.formats.append(dict(
                source=_relatif(source),
                appel=dict(nom=k.get("nom", ""), feuille=k.get("feuille"),
                           ligne_entete=k.get("ligne_entete"),
                           n_lignes=k.get("n_lignes")),
                meta=_jsonable(meta),
                colonnes=[str(c) for c in df.columns],
                n_lignes_lues=int(len(df))))
            return res                                   # inchangé

        def deviner_colonnes(df, *a, **k):
            res = _deviner(df, *a, **k)
            j.colonnes.append(dict(
                colonnes_disponibles=[str(c) for c in df.columns],
                mots_valeur=[str(m) for m in (a[0] if a else k.get("mots_valeur", []))]
                if (a or "mots_valeur" in k) else "MOTS_TEMP (defaut)",
                col_date_proposee=_s(res[0]), col_valeur_proposee=_s(res[1])))
            return res                                   # inchangé

        def charger_eau(fichier_eau, *a, **k):
            res = _eau(fichier_eau, *a, **k)
            daily = res[0] if isinstance(res, tuple) else res
            sub = res[1] if isinstance(res, tuple) and len(res) > 1 else None
            j.eau.append(dict(
                source=_relatif(fichier_eau),
                override=dict(col_date=_s(k.get("col_date")),
                              col_temp=_s(k.get("col_temp")),
                              feuille=_s(k.get("feuille")),
                              ligne_entete=k.get("ligne_entete")),
                n_journees=int(len(daily)),
                n_mesures_infra=int(len(sub)) if sub is not None else None,
                mesures_par_journee_min=(int(daily["n_mesures"].min())
                                         if len(daily) else None),
                mesures_par_journee_max=(int(daily["n_mesures"].max())
                                         if len(daily) else None),
                mesures_par_journee_mediane=(float(daily["n_mesures"].median())
                                             if len(daily) else None)))
            return res                                   # inchangé

        def charger_air_brut(source, *a, **k):
            res = _airb(source, *a, **k)
            j.air.append(dict(
                source=_relatif(source),
                override=dict(col_date=_s(k.get("col_date")),
                              col_temp=_s(k.get("col_temp")),
                              station_code=_s(k.get("station_code")),
                              station_nom=_s(k.get("station_nom"))),
                colonnes_retournees=[str(c) for c in res.columns],
                station_attrs=_jsonable(res.attrs.get("station")),
                n_journees=int(len(res))))
            return res                                   # inchangé

        def calculer_normales_ecarts(df_air, *a, **k):
            res = _norm(df_air, *a, **k)
            j.normales.append(dict(diag=_jsonable(res[2]),
                                   n_ecarts=int(len(res[0])),
                                   n_normales=int(len(res[1]))))
            return res                                   # inchangé

        def _m_saisonnier(df, mois, m_estival, *a, **k):
            res = _ms(df, mois, m_estival, *a, **k)
            j.m_saisonnier.append(dict(mois=[int(m) for m in mois],
                                       m_estival=float(m_estival),
                                       m_retenu=float(res[0]),
                                       info=_jsonable(res[1])))
            return res                                   # inchangé

        sniff.lire_brut = lire_brut
        sniff.deviner_colonnes = deviner_colonnes
        io_data.lire_brut = lire_brut
        io_data.deviner_colonnes = deviner_colonnes
        io_data.charger_eau = charger_eau
        io_data.charger_air_brut = charger_air_brut
        io_data.calculer_normales_ecarts = calculer_normales_ecarts
        core._m_saisonnier = _m_saisonnier

        # CORRECTIF 10 — l'orchestrateur appelle desormais `marquer_lecture`.
        # Sans enveloppe ici, `journal.eau` resterait vide et le bloc `eau` de
        # 01_colonnes_retenues.json disparaitrait : un artefact declare FIGE se
        # mettrait a bouger pour une raison sans rapport avec le correctif.
        # Conditionnel : ref/v4_5 n'a pas cette fonction, et le harnais doit
        # pouvoir rejouer les deux codes.
        if hasattr(io_data, "marquer_lecture"):
            _ml = io_data.marquer_lecture
            originaux[(io_data, "marquer_lecture")] = _ml

            def marquer_lecture(fichier_eau, *a, **k):
                res = _ml(fichier_eau, *a, **k)
                # (daily, sub, marques) ou (daily, marques)
                daily = res[0]
                sub = res[1] if len(res) == 3 else None
                marques = res[-1]
                j.eau.append(dict(
                    source=_relatif(fichier_eau),
                    override=dict(col_date=_s(k.get("col_date")),
                                  col_temp=_s(k.get("col_temp")),
                                  feuille=_s(k.get("feuille")),
                                  ligne_entete=k.get("ligne_entete")),
                    n_journees=int(len(daily)),
                    n_mesures_infra=int(len(sub)) if sub is not None else None,
                    mesures_par_journee_min=(int(daily["n_mesures"].min())
                                             if len(daily) else None),
                    mesures_par_journee_max=(int(daily["n_mesures"].max())
                                             if len(daily) else None),
                    mesures_par_journee_mediane=(float(daily["n_mesures"].median())
                                                 if len(daily) else None)))
                j.lecture.append(dict(source=_relatif(fichier_eau),
                                      n_mesures_ecartees=int(len(marques))))
                return res                                   # inchange

            io_data.marquer_lecture = marquer_lecture
        return originaux

    @staticmethod
    def restaurer(originaux):
        for (mod, attr), fn in originaux.items():
            setattr(mod, attr, fn)


def _relatif(source):
    """Chemin relatif à la racine du chantier — jamais un chemin absolu (D5)."""
    if not isinstance(source, (str, Path)):
        return f"<{type(source).__name__}>"
    try:
        return Path(source).resolve().relative_to(RACINE).as_posix()
    except ValueError:
        return Path(source).name


def _s(v):
    return None if v is None else str(v)


def _jsonable(o):
    """Rend un objet sérialisable, de façon stable et sans chemin absolu."""
    import numpy as np
    if o is None or isinstance(o, (bool, str)):
        return o
    if isinstance(o, (int, float)):
        return _f(o) if isinstance(o, float) else o
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return _f(float(o))
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in sorted(o.items(), key=lambda x: str(x[0]))}
    if isinstance(o, (list, tuple, set)):
        vals = [_jsonable(v) for v in o]
        return sorted(vals, key=str) if isinstance(o, set) else vals
    return str(o)


def _f(x):
    """Flottant à DEC décimales fixes, ou None si non fini (D5)."""
    import math
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    v = round(x, DEC)
    return 0.0 if v == 0 else v


# ============================================================
# Écriture déterministe
# ============================================================
def ecrire_json(chemin: Path, obj):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(_jsonable(obj), ensure_ascii=False, indent=2,
                     sort_keys=True)
    chemin.write_text(txt + "\n", encoding="utf-8", newline="\n")


def ecrire_csv(chemin: Path, colonnes, lignes, tri=None):
    """
    CSV UTF-8, séparateur « ; », fin de ligne LF, flottants à 6 décimales,
    tri stable et EXPLICITE sur les colonnes nommées par `tri` (D5).
    """
    chemin.parent.mkdir(parents=True, exist_ok=True)
    rows = [dict(l) for l in lignes]
    if tri:
        rows.sort(key=lambda r: tuple(_cle(r.get(c)) for c in tri))
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(colonnes), delimiter=SEP,
                           lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: _cell(r.get(c)) for c in colonnes})


def _cle(v):
    """Clé de tri totale : (rang de type, valeur) — jamais de comparaison
    entre types incomparables, sinon le tri n'est pas stable d'un run à
    l'autre selon l'ordre d'insertion."""
    if v is None or (isinstance(v, float) and v != v):
        return (0, "")
    if isinstance(v, bool):
        return (1, int(v))
    if isinstance(v, (int, float)):
        return (2, float(v))
    return (3, str(v))


def _cell(v):
    import math
    import numpy as np
    if v is None:
        return ""
    if isinstance(v, (np.integer,)):
        return str(int(v))
    if isinstance(v, (np.floating,)):
        v = float(v)
    if isinstance(v, float):
        if not math.isfinite(v):
            return ""
        return f"{v:.{DEC}f}"
    if isinstance(v, bool):
        return "oui" if v else "non"
    s = str(v)
    # Aucun séparateur ni saut de ligne dans une cellule : le diff doit rester
    # ligne à ligne.
    return s.replace("\r", " ").replace("\n", " ").replace(SEP, ",")


def ecrire_texte(chemin: Path, texte: str):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8", newline="\n")


# ============================================================
# Manifeste
# ============================================================
def sha256(chemin: Path) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


MANIFESTE = ICI / "MANIFEST.sha256"
EXCLUS_MANIFESTE = {"MANIFEST.sha256"}


# Un artefact du harnais est un fichier <NN>_....{csv,json,txt} dans un
# dossier de jeu. Tout le reste est hors du manifeste (D11) : les scripts .py
# ne sont pas la reference mais l'outil qui la produit, et les .xlsx / .docx
# livrables ne sont pas produits par le harnais du tout.
import re as _re
MOTIF_ARTEFACT = _re.compile(r"^\d{2}_[^/]+\.(csv|json|txt)$")


def est_artefact(rel: str) -> bool:
    """Le chemin relatif designe-t-il un artefact produit par le harnais ?"""
    morceaux = rel.split("/")
    return len(morceaux) == 2 and bool(MOTIF_ARTEFACT.match(morceaux[1]))


def fichiers_a_manifester(racine: Path = None):
    """
    Les artefacts produits par le harnais, triés par chemin relatif.

    D11 : les .xlsx et .docx de tests/reference/<jeu>/ SORTENT de l'ensemble
    haché — ils ne sont pas produits par le harnais, et les hacher ferait
    échouer toute vérification pour une raison qui n'a rien à voir avec la
    non-régression. Ils NE sortent PAS du dossier : ils y restent comme seule
    trace du chemin de paramètres de l'application.
    """
    base = racine or ICI
    out = []
    for p in sorted(base.rglob("*"), key=lambda q: q.relative_to(base).as_posix()):
        if not p.is_file():
            continue
        rel = p.relative_to(base).as_posix()
        if est_artefact(rel):
            out.append((rel, p))
    return out


def ecrire_manifeste(racine: Path = None):
    base = racine or ICI
    lignes = [f"{sha256(p)}  {rel}" for rel, p in fichiers_a_manifester(base)]
    ecrire_texte(base / "MANIFEST.sha256", "\n".join(lignes) + "\n")
    return len(lignes)
