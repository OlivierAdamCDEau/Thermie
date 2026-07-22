"""
sniff.py — Détection robuste de format CSV (package thermie_debits).

Auto-détecte le séparateur, l'encodage et propose un mapping de colonnes
(date / valeur) à partir d'un vocabulaire élargi. Utilisé par les loaders
sonde et air, et exposé à l'app pour un mapping manuel corrigeable.
"""
from __future__ import annotations
import io
import csv
import pandas as pd


ENCODAGES = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
SEPARATEURS = [";", ",", "\t", "|"]

# Vocabulaire de détection (minuscules, sans accent géré séparément)
MOTS_DATE = ["date", "heure", "time", "timestamp", "horodat", "jour", "aaaammjj",
             "aaaa", "datetime"]
MOTS_TEMP = ["temp", "°c", "degr", "tw", "t_eau", "teau", "water", "eau",
             "valeur", "value", "tm", "t (", "t("]


def lire_brut(source, n_lignes=None):
    """
    Lit un CSV en auto-détectant encodage et séparateur.
    `source` : chemin de fichier ou bytes (upload Streamlit).
    Retourne (df, meta) où meta = {encodage, separateur}.
    """
    # Récupérer les octets bruts
    if isinstance(source, (bytes, bytearray)):
        raw = bytes(source)
    else:
        with open(source, "rb") as f:
            raw = f.read()

    # Encodage : premier qui décode sans erreur
    texte = None; enc_ok = None
    for enc in ENCODAGES:
        try:
            texte = raw.decode(enc); enc_ok = enc; break
        except (UnicodeDecodeError, LookupError):
            continue
    if texte is None:
        texte = raw.decode("utf-8", errors="replace"); enc_ok = "utf-8(replace)"

    # Séparateur : celui qui maximise le nb de colonnes cohérent
    echantillon = "\n".join(texte.splitlines()[:30])
    sep_ok = None; best_cols = 0
    try:
        dialect = csv.Sniffer().sniff(echantillon, delimiters=";,\t|")
        sep_ok = dialect.delimiter
    except Exception:
        pass
    if sep_ok is None:
        for sep in SEPARATEURS:
            n = echantillon.split("\n")[0].count(sep)
            if n > best_cols:
                best_cols = n; sep_ok = sep
        sep_ok = sep_ok or ";"

    df = pd.read_csv(io.StringIO(texte), sep=sep_ok, engine="python")
    df.columns = [str(c).lstrip("\ufeff").strip() for c in df.columns]
    if n_lignes:
        df = df.head(n_lignes)
    return df, {"encodage": enc_ok, "separateur": sep_ok}


def _norm(s):
    """Minuscule + suppression des accents pour la détection."""
    s = str(s).lower()
    for a, b in [("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("ô", "o")]:
        s = s.replace(a, b)
    return s


def deviner_colonnes(df, mots_valeur=MOTS_TEMP):
    """
    Propose (col_date, col_valeur) par vocabulaire. Retourne des None si
    aucune correspondance — l'app demandera alors un mapping manuel.
    """
    cols = list(df.columns)
    col_date = next((c for c in cols
                     if any(m in _norm(c) for m in MOTS_DATE)), None)
    # colonne valeur : match vocabulaire ET numérique de préférence
    candidates = [c for c in cols
                  if any(m in _norm(c) for m in mots_valeur) and c != col_date]
    col_val = None
    for c in candidates:
        serie = pd.to_numeric(df[c].astype(str).str.replace(",", "."),
                              errors="coerce")
        if serie.notna().mean() > 0.5:
            col_val = c; break
    if col_val is None and candidates:
        col_val = candidates[0]
    return col_date, col_val
