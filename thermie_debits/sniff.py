"""
sniff.py — Détection robuste de format tabulaire (package thermie_debits).

Gère CSV (auto-détection séparateur/encodage) ET Excel (.xls/.xlsx), avec :
  - choix de la feuille (Excel multi-feuilles) ;
  - détection d'une ligne d'en-tête décalée (l'en-tête n'est pas toujours
    la 1re ligne — ex. sondes qui préfixent des métadonnées) ;
  - proposition de mapping de colonnes (date / valeur) par vocabulaire.

Utilisé par les loaders sonde et air, et exposé à l'app pour un mapping
manuel corrigeable.
"""
from __future__ import annotations
import io
import csv
import pandas as pd


ENCODAGES = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
SEPARATEURS = [";", ",", "\t", "|"]

MOTS_DATE = ["date", "heure", "time", "timestamp", "horodat", "jour", "aaaammjj",
             "aaaa", "datetime", "cet", "cest", "gmt"]
MOTS_TEMP = ["temp", "°c", "degr", "tw", "t_eau", "teau", "water", "eau",
             "valeur", "value", "tm", "t (", "t(", ", °c", "temp,"]


def _norm(s):
    s = str(s).lower()
    for a, b in [("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("ô", "o")]:
        s = s.replace(a, b)
    return s


def est_excel(nom):
    """Détecte un fichier Excel d'après son extension."""
    n = str(nom).lower()
    return n.endswith(".xls") or n.endswith(".xlsx") or n.endswith(".xlsm")


def lister_feuilles(source, nom=""):
    """Retourne la liste des feuilles d'un Excel (vide si CSV)."""
    if not est_excel(nom):
        return []
    engine = "xlrd" if str(nom).lower().endswith(".xls") else "openpyxl"
    buf = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
    try:
        return pd.ExcelFile(buf, engine=engine).sheet_names
    except Exception:
        try:
            return pd.ExcelFile(buf).sheet_names
        except Exception:
            return []


def _detecter_ligne_entete(df_brut, max_scan=15):
    """
    Trouve la ligne qui ressemble le plus à un en-tête : celle qui contient
    le plus de cellules correspondant au vocabulaire date/température.
    Retourne l'indice de ligne (0 si rien de mieux trouvé).
    """
    best_row, best_score = 0, 0
    for i in range(min(max_scan, len(df_brut))):
        cells = [_norm(v) for v in df_brut.iloc[i].tolist()]
        score = sum(1 for c in cells
                    if any(m in c for m in MOTS_DATE + MOTS_TEMP))
        # bonus : une ligne d'en-tête a peu de valeurs numériques pures
        n_num = sum(1 for c in cells
                    if c.replace(".", "").replace(",", "").replace("-", "").isdigit())
        if score > best_score and n_num <= len(cells) / 2:
            best_score, best_row = score, i
    return best_row


def lire_brut(source, nom="", n_lignes=None, feuille=None, ligne_entete=None):
    """
    Lit un CSV ou Excel en auto-détectant le format.

    source : chemin de fichier OU bytes (upload Streamlit).
    nom    : nom du fichier (pour détecter l'extension). Si source est un
             chemin, nom est déduit automatiquement.
    feuille : nom de feuille Excel (défaut : 1re feuille).
    ligne_entete : indice de la ligne d'en-tête (défaut : auto-détection).

    Retourne (df, meta) où meta décrit le format détecté.
    """
    if not nom and isinstance(source, str):
        nom = source

    # ---- Excel ----
    if est_excel(nom):
        engine = "xlrd" if str(nom).lower().endswith(".xls") else "openpyxl"
        buf = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
        feuilles = lister_feuilles(source, nom)
        sh = feuille if feuille in feuilles else (feuilles[0] if feuilles else 0)
        # lire brut sans header pour trouver la ligne d'en-tête
        brut = pd.read_excel(buf, sheet_name=sh, header=None, engine=engine)
        hdr = ligne_entete if ligne_entete is not None else _detecter_ligne_entete(brut)
        df = brut.iloc[hdr + 1:].copy()
        df.columns = [str(c).strip() for c in brut.iloc[hdr].tolist()]
        df = df.reset_index(drop=True).dropna(how="all")
        if n_lignes:
            df = df.head(n_lignes)
        return df, {"format": "excel", "engine": engine, "feuille": sh,
                    "feuilles": feuilles, "ligne_entete": hdr}

    # ---- CSV ----
    if isinstance(source, (bytes, bytearray)):
        raw = bytes(source)
    else:
        with open(source, "rb") as f:
            raw = f.read()
    texte = None; enc_ok = None
    for enc in ENCODAGES:
        try:
            texte = raw.decode(enc); enc_ok = enc; break
        except (UnicodeDecodeError, LookupError):
            continue
    if texte is None:
        texte = raw.decode("utf-8", errors="replace"); enc_ok = "utf-8(replace)"

    echantillon = "\n".join(texte.splitlines()[:30])
    sep_ok = None
    try:
        sep_ok = csv.Sniffer().sniff(echantillon, delimiters=";,\t|").delimiter
    except Exception:
        pass
    if sep_ok is None:
        best = 0
        for sep in SEPARATEURS:
            n = echantillon.split("\n")[0].count(sep)
            if n > best:
                best, sep_ok = n, sep
        sep_ok = sep_ok or ";"

    # détection ligne d'en-tête pour CSV aussi (rare mais possible)
    brut = pd.read_csv(io.StringIO(texte), sep=sep_ok, engine="python", header=None)
    hdr = ligne_entete if ligne_entete is not None else _detecter_ligne_entete(brut)
    df = brut.iloc[hdr + 1:].copy()
    df.columns = [str(c).lstrip("\ufeff").strip() for c in brut.iloc[hdr].tolist()]
    df = df.reset_index(drop=True).dropna(how="all")
    if n_lignes:
        df = df.head(n_lignes)
    return df, {"format": "csv", "encodage": enc_ok, "separateur": sep_ok,
                "ligne_entete": hdr}


def deviner_colonnes(df, mots_valeur=MOTS_TEMP):
    """Propose (col_date, col_valeur) par vocabulaire. None si non trouvé."""
    cols = list(df.columns)
    col_date = next((c for c in cols
                     if any(m in _norm(c) for m in MOTS_DATE)), None)
    candidates = [c for c in cols
                  if any(m in _norm(c) for m in mots_valeur) and c != col_date]
    col_val = None
    for c in candidates:
        serie = pd.to_numeric(
            df[c].astype(str).str.replace(",", ".").str.replace(" ", ""),
            errors="coerce")
        if serie.notna().mean() > 0.5:
            col_val = c; break
    if col_val is None and candidates:
        col_val = candidates[0]
    return col_date, col_val
