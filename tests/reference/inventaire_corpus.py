"""
inventaire_corpus.py — ÉTAPE 1, TÂCHE A.

Relève, sans rien modifier, les caractéristiques de format de chaque fichier
de data/. N'exécute AUCUN code applicatif de calcul : seules les fonctions de
détection de ref/v4_5/thermie_debits/sniff.py sont appelées, en lecture, pour
que l'encodage et le séparateur relevés soient bien CEUX QUE L'OUTIL VOIT et
non ceux qu'un détecteur tiers croirait voir (D3).

Sorties (déterministes, D5) :
  out/etape1/inventaire_corpus.csv   une ligne par fichier
  docs/etape1_extraits_bruts.md      cinq premières lignes brutes par fichier

Aucun horodatage, aucun chemin absolu dans le contenu produit.
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd

# --- Racines -----------------------------------------------------------------
ICI = Path(__file__).resolve().parent          # tests/reference
RACINE = ICI.parent.parent                     # THERMIE_BIO_V4_6
REF_V45 = RACINE / "ref" / "v4_5"
DATA = RACINE / "data"
OUT = RACINE / "out" / "etape1"
DOCS = RACINE / "docs"

# D1 : ref/ est en LECTURE SEULE. Importer un module y ecrirait un
# __pycache__/*.pyc ; on le desactive avant tout import.
sys.dont_write_bytecode = True

# D3 : le harnais s'exécute sur le code de ref/v4_5/, jamais sur app/.
sys.path.insert(0, str(REF_V45))
from thermie_debits.sniff import (                       # noqa: E402
    ENCODAGES, _detecter_separateur, _detecter_ligne_entete, est_excel,
    lister_feuilles, lire_brut, deviner_colonnes,
)
from thermie_debits.io_data import (                     # noqa: E402
    _parse_dates_sonde, _parse_dates_air,
)

VIDE = ""          # cellule sans objet
NA = "n/a"         # caractéristique sans objet pour ce type de fichier
INCONNU = "indetermine"

# --- Encodage ----------------------------------------------------------------
BOMS = [(b"\xef\xbb\xbf", "BOM UTF-8"),
        (b"\xff\xfe", "BOM UTF-16-LE"),
        (b"\xfe\xff", "BOM UTF-16-BE")]


def detecter_encodage(brut: bytes):
    """
    Reproduit la cascade de sniff.lire_brut : premier encodage de ENCODAGES
    qui décode sans erreur. Retourne (encodage, methode, bom).
    """
    bom = next((lbl for sig, lbl in BOMS if brut.startswith(sig)), "aucun")
    for enc in ENCODAGES:
        try:
            brut.decode(enc)
            return enc, f"cascade sniff.ENCODAGES {ENCODAGES} — 1er decodage sans erreur", bom
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8(replace)", "cascade sniff.ENCODAGES epuisee — repli utf-8 errors=replace", bom


def fins_de_ligne(brut: bytes) -> str:
    crlf = brut.count(b"\r\n")
    lf = brut.count(b"\n") - crlf
    cr = brut.count(b"\r") - crlf
    parts = [f"CRLF={crlf}", f"LF={lf}", f"CR={cr}"]
    return " ".join(p for p in parts if not p.endswith("=0")) or "aucune"


# --- Dates -------------------------------------------------------------------
MOTIFS_DATE = [
    (r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$", "ISO YYYY-MM-DDTHH:MM:SS(.mmm)(Z)"),
    (r"^\d{4}-\d{2}-\d{2}[ ]\d{2}:\d{2}:\d{2}$",         "YYYY-MM-DD HH:MM:SS"),
    (r"^\d{4}-\d{2}-\d{2}$",                             "YYYY-MM-DD"),
    (r"^\d{2}/\d{2}/\d{4}[ ]\d{2}:\d{2}:\d{2}$",         "DD/MM/YYYY HH:MM:SS"),
    (r"^\d{2}/\d{2}/\d{4}[ ]\d{2}:\d{2}$",               "DD/MM/YYYY HH:MM"),
    (r"^\d{2}/\d{2}/\d{4}$",                             "DD/MM/YYYY"),
    (r"^\d{8}$",                                         "AAAAMMJJ (YYYYMMDD)"),
    (r"^\d{2}:\d{2}:\d{2}$",                             "HH:MM:SS (heure seule)"),
    (r"^\d{2}:\d{2}$",                                   "HH:MM (heure seule)"),
]


def formats_date(valeurs) -> str:
    """Formats de date rencontrés, avec leur effectif, triés (stable)."""
    c = Counter()
    for v in valeurs:
        if v is None:
            continue
        if hasattr(v, "isoformat") and not isinstance(v, str):
            c["objet datetime/date/time natif (Excel)"] += 1
            continue
        s = str(v).strip()
        if not s or s.lower() in ("nan", "nat"):
            continue
        for rx, lbl in MOTIFS_DATE:
            if re.match(rx, s):
                c[lbl] += 1
                break
        else:
            c[f"non reconnu (ex. {s[:24]!r})"] += 1
    return " | ".join(f"{k} x{v}" for k, v in sorted(c.items())) or VIDE


def separateur_decimal(valeurs) -> str:
    """Séparateur décimal observé sur des valeurs à l'apparence numérique."""
    virg = pt = ent = num = 0
    for v in valeurs:
        if v is None or (isinstance(v, (int, float)) and not isinstance(v, bool)):
            if isinstance(v, float) and pd.notna(v):
                num += 1          # typé numérique : aucun séparateur textuel
            continue
        s = str(v).strip()
        if not s or s.lower() in ("nan", "nat"):
            continue
        if re.fullmatch(r"-?\d+,\d+", s):
            virg += 1
        elif re.fullmatch(r"-?\d+\.\d+", s):
            pt += 1
        elif re.fullmatch(r"-?\d+", s):
            ent += 1
    lst = []
    if virg:
        lst.append(f"virgule x{virg}")
    if pt:
        lst.append(f"point x{pt}")
    if ent:
        lst.append(f"entier sans decimale x{ent}")
    if num:
        lst.append(f"valeur deja numerique (sans forme textuelle) x{num}")
    return " | ".join(lst) or VIDE


def pas_mesure(dt):
    """
    Pas médian ET modal, en secondes, à partir d'une série DÉJÀ datée par
    les parseurs de ref/v4_5 (jamais par pd.to_datetime générique : celui-ci
    lit 19540101 comme un compte de nanosecondes et 10/05/2021 en ordre
    américain, ce qui fausse période et pas).
    """
    s = pd.Series(dt).dropna().sort_values()
    if len(s) < 3:
        return VIDE, VIDE, VIDE, VIDE, VIDE, VIDE
    d = s.diff().dropna().dt.total_seconds()
    d = d[d > 0]
    if d.empty:
        return VIDE, VIDE, VIDE, VIDE, VIDE, VIDE
    med = float(d.median())
    modes = d.mode()
    mod = float(modes.iloc[0]) if len(modes) else float("nan")
    n_dbl = int((s.diff().dt.total_seconds() == 0).sum())
    # Distribution des intervalles : un pas modal unique masque les periodes
    # ou la sonde a change de cadence. La matrice de couverture en depend.
    vc = d.value_counts().head(8)
    distrib = " | ".join(f"{int(k)}s x{int(v)}" for k, v in vc.items())
    return (f"{med:.0f}", f"{mod:.0f}",
            str(s.min().date()), str(s.max().date()), str(n_dbl), distrib)


# --- Lecture des extraits bruts ----------------------------------------------
def cinq_lignes_csv(brut: bytes, enc: str):
    txt = brut.decode(enc, errors="replace")
    return txt.splitlines()[:5]


def cinq_lignes_excel(chemin: Path, feuille):
    d = pd.read_excel(chemin, sheet_name=feuille, header=None, nrows=5)
    return ["\t".join("" if pd.isna(v) else str(v) for v in d.iloc[i].tolist())
            for i in range(len(d))]


# --- Rôle d'un fichier -------------------------------------------------------
def role_de(rel: Path) -> str:
    parties = [p.lower() for p in rel.parts]
    for r in ("eau", "air", "debit", "referentiel"):
        if r in parties:
            return r
    return "autre"


COLONNES = [
    "jeu", "role", "fichier", "extension", "taille_octets",
    "encodage", "methode_encodage", "bom", "fins_de_ligne",
    "separateur", "n_feuilles", "feuilles", "ligne_entete_detectee",
    "n_colonnes", "entetes",
    "separateur_decimal", "formats_date", "colonne_heure_separee",
    "pas_median_s", "pas_modal_s", "pas_observes",
    "periode_debut", "periode_fin", "n_points", "n_lignes",
    "doublons_horodatage",
    "colonne_date_retenue_v45", "colonne_temp_retenue_v45",
    "presence_TM", "presence_TN", "presence_TX", "presence_RR",
    "presence_debit", "remarques",
]


def inventorier(chemin: Path, rel: Path) -> dict:
    jeu = rel.parts[0]
    ligne = {c: VIDE for c in COLONNES}
    ligne.update(jeu=jeu, role=role_de(rel), fichier=rel.as_posix(),
                 extension=chemin.suffix.lower(),
                 taille_octets=str(chemin.stat().st_size))
    remarques = []

    excel = est_excel(chemin.name)
    ligne["presence_debit"] = "oui" if ligne["role"] == "debit" else "non"

    # ---------- Excel ----------
    if excel:
        feuilles = lister_feuilles(str(chemin), chemin.name)
        ligne["encodage"] = NA
        ligne["methode_encodage"] = NA
        ligne["bom"] = NA
        ligne["fins_de_ligne"] = NA
        ligne["separateur"] = NA
        ligne["n_feuilles"] = str(len(feuilles))
        ligne["feuilles"] = " | ".join(feuilles)
        feuille = feuilles[0] if feuilles else 0
        brut = pd.read_excel(chemin, sheet_name=feuille, header=None)
        hdr = _detecter_ligne_entete(brut)
        ligne["ligne_entete_detectee"] = str(hdr)
        entetes = [str(c).strip() for c in brut.iloc[hdr].tolist()]
        corps = brut.iloc[hdr + 1:].copy()
        corps.columns = entetes
        corps = corps.reset_index(drop=True).dropna(how="all")
        ligne["n_colonnes"] = str(len(entetes))
        ligne["entetes"] = " | ".join(entetes)
        ligne["n_lignes"] = str(len(corps))
        if len(feuilles) > 1:
            remarques.append(f"classeur multi-feuilles ({len(feuilles)}) — "
                             f"sniff retient la premiere : « {feuille} »")

    # ---------- CSV / texte ----------
    else:
        brut_octets = chemin.read_bytes()
        enc, methode, bom = detecter_encodage(brut_octets)
        ligne["encodage"], ligne["methode_encodage"], ligne["bom"] = enc, methode, bom
        ligne["fins_de_ligne"] = fins_de_ligne(brut_octets)
        ligne["n_feuilles"] = NA
        ligne["feuilles"] = NA
        texte = brut_octets.decode(enc, errors="replace")
        lignes = texte.splitlines()
        sep = _detecter_separateur(lignes)
        ligne["separateur"] = repr(sep)
        try:
            brut = pd.read_csv(io.StringIO(texte), sep=sep, engine="python",
                               header=None)
        except Exception as exc:                       # D7 : l'echec est un fait
            ligne["remarques"] = f"lecture pandas impossible : {type(exc).__name__}: {exc}"
            return ligne
        hdr = _detecter_ligne_entete(brut)
        ligne["ligne_entete_detectee"] = str(hdr)
        entetes = [str(c).lstrip("﻿").strip() for c in brut.iloc[hdr].tolist()]
        corps = brut.iloc[hdr + 1:].copy()
        corps.columns = entetes
        corps = corps.reset_index(drop=True).dropna(how="all")
        ligne["n_colonnes"] = str(len(entetes))
        ligne["entetes"] = " | ".join(entetes)
        ligne["n_lignes"] = str(len(corps))

    cols_up = {str(c).upper().strip(): c for c in corps.columns}
    for marque in ("TM", "TN", "TX", "RR"):
        ligne[f"presence_{marque}"] = "oui" if marque in cols_up else "non"

    # ---------- Colonnes date / heure / valeur telles que V4.5 les verrait ----
    dev_date, dev_temp = deviner_colonnes(corps)
    col_h = next((c for c in corps.columns
                  if str(c).lower().startswith(("heure", "hrana", "hrprel"))
                  and c != dev_date), None)
    ligne["colonne_heure_separee"] = str(col_h) if col_h is not None else "non"

    if ligne["role"] == "eau":
        # Reproduit la priorite de io_data.charger_eau (lignes 55-68).
        cand = [c for c in corps.columns
                if any(m in str(c).lower() for m in
                       ["date", "heure", "time", "timestamp", "horodat"])
                or any(m in str(c).lower() for m in ["dtana", "dtprel"])]
        col_date = None
        for dc in cand:
            nn = corps[dc].dropna()
            samp = str(nn.iloc[0]) if len(nn) else ""
            if len(samp) > 8 and not str(dc).lower().startswith(("heure", "hr")):
                col_date = dc
                break
        if col_date is None:
            col_date = dev_date or (cand[0] if cand else None)
        col_temp = dev_temp
    elif ligne["role"] == "air":
        col_date = next((c for c in corps.columns
                         if str(c).upper() == "AAAAMMJJ"), None) or dev_date
        col_temp = cols_up.get("TM") or dev_temp
    else:
        col_date, col_temp = dev_date, dev_temp

    ligne["colonne_date_retenue_v45"] = str(col_date) if col_date is not None else "AUCUNE"
    ligne["colonne_temp_retenue_v45"] = str(col_temp) if col_temp is not None else "AUCUNE"

    # ---------- Formats de date, decimales, pas ----------
    if col_date is not None and col_date in corps.columns:
        ech = corps[col_date].dropna().head(3000).tolist()
        f_date = formats_date(ech)
        if col_h is not None and col_h in corps.columns:
            f_h = formats_date(corps[col_h].dropna().head(3000).tolist())
            f_date = f"{f_date}  ++ colonne heure « {col_h} » : {f_h}"
        ligne["formats_date"] = f_date

        # Datation par les parseurs de ref/v4_5, jamais par un parseur generique :
        # le releve doit dire ce que l'outil lit, y compris ses erreurs.
        if ligne["role"] == "air":
            dt = _parse_dates_air(corps[col_date])
        else:
            dt = _parse_dates_sonde(corps[col_date])
            # Regle exacte de io_data.charger_eau:83-90 pour la colonne d heure.
            if (col_h is not None and col_h in corps.columns
                    and dt.notna().any() and (dt.dt.hour == 0).all()):
                def _td(h):
                    try:
                        h = str(h).strip()
                        return pd.Timedelta(h) if ":" in h else pd.Timedelta(0)
                    except Exception:
                        return pd.Timedelta(0)
                dt = dt + corps[col_h].apply(_td)
                ligne["colonne_heure_separee"] = (
                    f"{col_h} (RECOMPOSEE avec la date par V4.5)")
            elif col_h is not None:
                ligne["colonne_heure_separee"] = (
                    f"{col_h} (detectee, NON recomposee : la date porte deja une heure)")
        med, mod, d0, d1, ndbl, distrib = pas_mesure(dt)
        ligne["pas_median_s"], ligne["pas_modal_s"] = med, mod
        ligne["pas_observes"] = distrib
        ligne["periode_debut"], ligne["periode_fin"] = d0, d1
        ligne["doublons_horodatage"] = ndbl
        ligne["n_points"] = str(int(dt.notna().sum()))
        n_perdues = int(len(corps) - dt.notna().sum())
        if n_perdues:
            remarques.append(f"{n_perdues} ligne(s) sur {len(corps)} sans date "
                             f"exploitable par le parseur de V4.5")
    else:
        remarques.append("aucune colonne de date identifiable")

    if col_temp is not None and col_temp in corps.columns:
        ligne["separateur_decimal"] = separateur_decimal(
            corps[col_temp].dropna().head(3000).tolist())

    ligne["remarques"] = " ; ".join(remarques)
    return ligne


def inventorier_debit(chemin: Path, rel: Path) -> dict:
    """
    Les CSV de débit Vigicrues/Hub'eau ne passent pas par sniff : V4.5 les lit
    avec un parseur dédié (io_data.charger_debit). L'inventaire relève donc ce
    que ce parseur-là voit.
    """
    ligne = {c: VIDE for c in COLONNES}
    brut_octets = chemin.read_bytes()
    enc, methode, bom = detecter_encodage(brut_octets)
    texte = brut_octets.decode(enc, errors="replace")
    lignes = texte.splitlines()
    ligne.update(
        jeu=rel.parts[0], role="debit", fichier=rel.as_posix(),
        extension=chemin.suffix.lower(), taille_octets=str(chemin.stat().st_size),
        encodage=enc, methode_encodage=methode, bom=bom,
        fins_de_ligne=fins_de_ligne(brut_octets),
        separateur="','  (parseur dedie charger_debit, pas sniff)",
        n_feuilles=NA, feuilles=NA, ligne_entete_detectee="0",
        presence_debit="oui", presence_TM="non", presence_TN="non",
        presence_TX="non", presence_RR="non", colonne_heure_separee="non",
    )
    entetes = lignes[0].strip().strip('"')
    entetes = (entetes.replace(',""', "|").replace('","', "|")
                      .replace('"', "").split("|"))
    ligne["entetes"] = " | ".join(entetes)
    ligne["n_colonnes"] = str(len(entetes))
    ligne["n_lignes"] = str(max(len(lignes) - 1, 0))

    dates, vals = [], []
    for l in lignes[1:]:
        l = l.strip().strip('"')
        parts = (l.replace(',""', "|").replace('","', "|")
                  .replace('"', "").split("|"))
        if len(parts) >= 2:
            dates.append(parts[0])
            vals.append(parts[1])
    ligne["colonne_date_retenue_v45"] = entetes[0] if entetes else VIDE
    ligne["colonne_temp_retenue_v45"] = entetes[1] if len(entetes) > 1 else VIDE
    ligne["formats_date"] = formats_date(dates[:3000])
    ligne["separateur_decimal"] = separateur_decimal(vals[:3000])
    # Datation identique a io_data.charger_debit:172-173 (partie avant T ou espace).
    d = pd.Series(dates).str.split("T").str[0].str.split(" ").str[0]
    dt = pd.to_datetime(d, errors="coerce")
    med, mod, d0, d1, ndbl, distrib = pas_mesure(dt)
    ligne.update(pas_median_s=med, pas_modal_s=mod, pas_observes=distrib,
                 periode_debut=d0, periode_fin=d1, doublons_horodatage=ndbl,
                 n_points=str(int(dt.notna().sum())))
    return ligne


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(
        (p for p in DATA.rglob("*")
         if p.is_file() and p.suffix.lower() not in (".md", ".txt")
         and p.name != "corpus.csv"),
        key=lambda p: p.relative_to(DATA).as_posix())

    lignes, extraits = [], []
    for p in fichiers:
        rel = p.relative_to(DATA)
        try:
            l = (inventorier_debit(p, rel) if role_de(rel) == "debit"
                 else inventorier(p, rel))
        except Exception as exc:                        # D7 : on fige l'echec
            l = {c: VIDE for c in COLONNES}
            l.update(jeu=rel.parts[0], role=role_de(rel), fichier=rel.as_posix(),
                     extension=p.suffix.lower(),
                     taille_octets=str(p.stat().st_size),
                     remarques=f"ECHEC INVENTAIRE {type(exc).__name__}: {exc}")
        lignes.append(l)

        # --- extrait brut ---
        bloc = [f"## `{rel.as_posix()}`", ""]
        try:
            if est_excel(p.name):
                fs = lister_feuilles(str(p), p.name)
                for f in fs:
                    bloc.append(f"Feuille « {f} » — cinq premieres lignes brutes :")
                    bloc.append("")
                    bloc.append("```")
                    bloc.extend(cinq_lignes_excel(p, f))
                    bloc.append("```")
                    bloc.append("")
            else:
                enc, _, _ = detecter_encodage(p.read_bytes())
                bloc.append(f"Cinq premieres lignes brutes (decodees en `{enc}`) :")
                bloc.append("")
                bloc.append("```")
                bloc.extend(cinq_lignes_csv(p.read_bytes(), enc))
                bloc.append("```")
                bloc.append("")
        except Exception as exc:
            bloc.append(f"*Extrait impossible : {type(exc).__name__}: {exc}*")
            bloc.append("")
        extraits.append("\n".join(bloc))

    cible = OUT / "inventaire_corpus.csv"
    with open(cible, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES, delimiter=";",
                           lineterminator="\n")
        w.writeheader()
        for l in lignes:
            w.writerow(l)

    entete = [
        "# Étape 1 — extraits bruts du corpus",
        "",
        "Cinq premières lignes de chaque fichier de `data/`, telles quelles,",
        "décodées avec l'encodage que retient la cascade `sniff.ENCODAGES`.",
        "Aucun fichier n'a été modifié. Pour les classeurs, toutes les feuilles",
        "sont extraites, y compris celles que l'outil n'ouvre pas.",
        "",
        f"{len(fichiers)} fichiers inventoriés.",
        "",
        "---",
        "",
    ]
    (DOCS / "etape1_extraits_bruts.md").write_text(
        "\n".join(entete) + "\n\n".join(extraits) + "\n", encoding="utf-8")

    print(f"inventaire_corpus.csv : {len(lignes)} lignes")
    print(f"etape1_extraits_bruts.md : {len(extraits)} fichiers")


if __name__ == "__main__":
    main()
