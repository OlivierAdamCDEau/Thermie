"""
io_data.py — Chargement des données (package thermie_debits).

Loaders mutualisés pour les chroniques d'eau, d'air (+RR), les normales
1991–2020 et les débits (influencé / désinfluencé). Inclut la logique de
fusion des débits avec comblement conditionnel (note : décisions projet).

Fonctions pures : elles lisent des fichiers et retournent des DataFrames,
sans effet de bord ni configuration globale.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def _parse_dates_sonde(serie):
    """
    Parse robuste des dates de sonde. FIX v5.7.1 conservé : on teste les
    formats DD/MM explicites AVANT le fallback 'mixed', pour éviter
    l'inversion jour/mois sur les dates ambiguës (jour ≤ 12).
    """
    s = serie.astype(str)
    best = None
    for fmt in ["%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
        att = pd.to_datetime(s, format=fmt, errors="coerce")
        if best is None or att.notna().sum() > best.notna().sum():
            best = att
    if best is None or best.notna().sum() == 0:
        best = pd.to_datetime(s, format="mixed", dayfirst=True, errors="coerce")
    return best


def charger_eau(fichier_eau):
    """Charge une chronique de sonde thermique → daily (T_eau_moy, T_eau_max)."""
    df_w = pd.read_csv(fichier_eau, sep=";", encoding="utf-8-sig")
    df_w.columns = [c.lstrip("\ufeff").strip() for c in df_w.columns]

    date_cols = [c for c in df_w.columns if "date" in c.lower() or "heure" in c.lower()]
    temp_col  = [c for c in df_w.columns if "temp" in c.lower()
                 or "°c" in c.lower() or "degr" in c.lower()][0]

    # Choisir la meilleure colonne date+heure (ignorer les colonnes "heure seule")
    dt_parsed = None
    for dc in date_cols:
        samp = str(df_w[dc].dropna().iloc[0]) if len(df_w[dc].dropna()) else ""
        if len(samp) <= 8:   # "14:59:10" = heure seule
            continue
        att = _parse_dates_sonde(df_w[dc])
        if dt_parsed is None or att.notna().sum() > dt_parsed.notna().sum():
            dt_parsed = att
    # Cas colonnes séparées Date + Heure
    if dt_parsed is None or dt_parsed.notna().sum() == 0:
        col_d = next((c for c in df_w.columns if c.lower() == "date"), None)
        col_h = next((c for c in df_w.columns if c.lower() == "heure"), None)
        if col_d is not None:
            dd = _parse_dates_sonde(df_w[col_d])
            if col_h is not None:
                def _td(h):
                    try: return pd.Timedelta(str(h))
                    except: return pd.Timedelta(0)
                dd = dd + df_w[col_h].astype(str).apply(_td)
            dt_parsed = dd
    if dt_parsed is None:
        dt_parsed = pd.to_datetime(df_w[date_cols[0]].astype(str),
                                   format="mixed", dayfirst=True, errors="coerce")

    df_w["datetime"] = dt_parsed
    df_w["T_eau"] = pd.to_numeric(
        df_w[temp_col].astype(str).str.replace(",", "."), errors="coerce")
    df_w["date"] = df_w["datetime"].dt.date
    df_w = df_w.dropna(subset=["date", "T_eau"])
    daily = df_w.groupby("date").agg(
        T_eau_moy=("T_eau", "mean"),
        T_eau_max=("T_eau", "max"),
        n_mesures=("T_eau", "size")).reset_index()
    return daily


def charger_air(fichier_air):
    """Charge la T° air journalière Météo-France (colonnes AAAAMMJJ, TM).
    Conserve RR (précipitations) si présent, pour le volet climatique bonus."""
    df_a = pd.read_csv(fichier_air, sep=";", low_memory=False)
    df_a = df_a.dropna(subset=["AAAAMMJJ"])
    df_a["AAAAMMJJ"] = df_a["AAAAMMJJ"].astype(int)
    df_a["date"]  = pd.to_datetime(df_a["AAAAMMJJ"].astype(str),
                                   format="%Y%m%d").dt.date
    df_a["T_air"] = pd.to_numeric(df_a["TM"], errors="coerce")
    cols = ["date", "T_air"]
    if "RR" in df_a.columns:
        df_a["RR"] = pd.to_numeric(df_a["RR"].astype(str).str.replace(",", "."),
                                   errors="coerce")
        cols.append("RR")
    return df_a[cols].dropna(subset=["date", "T_air"])


def charger_normales(fichier_normales):
    """
    Charge EcartNormales.csv (normales 1991–2020, note §2.3).
    Retourne (ecart_by_date, normales_lkp) où :
      - ecart_by_date : Delta_TMm par date (base de la normalisation)
      - normales_lkp  : TMm par (jour, mois) (pour la chronique/figures)
    """
    df_n = pd.read_csv(fichier_normales, sep=None, engine="python",
                       encoding="latin-1")
    for col in ["Delta_TMm", "TMm", "TM"]:
        if col in df_n.columns:
            df_n[col] = df_n[col].astype(str).str.replace(",", ".").astype(float)
    df_n["Date_parsed"] = pd.to_datetime(df_n["Date"], format="%d/%m/%Y",
                                         errors="coerce")
    df_n["date"]  = df_n["Date_parsed"].dt.date
    df_n["day"]   = df_n["Date_parsed"].dt.day
    df_n["month"] = df_n["Date_parsed"].dt.month
    df_n["Delta_TMm"] = pd.to_numeric(df_n["Delta_TMm"], errors="coerce")
    df_n["TMm"]       = pd.to_numeric(df_n["TMm"], errors="coerce")
    normales_lkp = (df_n.dropna(subset=["TMm"])
                        .groupby(["day", "month"])["TMm"].mean()
                        .reset_index().rename(columns={"TMm": "T_normale"}))
    ecart_by_date = df_n[["date", "Delta_TMm"]].dropna()
    return ecart_by_date, normales_lkp


def charger_debit(fichier_debit):
    """
    Parse CSV Vigicrues/Hub'eau (HYDRO). Robuste aux deux variantes de format
    rencontrées (champs entre guillemets ; date ISO éventuellement avec T/tz).
    Retourne un DataFrame [date, Q].
    """
    with open(fichier_debit, encoding="utf-8") as f:
        raw = f.read()
    rows = []
    for line in raw.strip().split("\n"):
        line = line.strip().strip('"')
        parts = (line.replace(',""', '|').replace('","', '|')
                     .replace('"', '').split('|'))
        if len(parts) >= 2:
            rows.append(parts[:2])
    df_q = pd.DataFrame(rows[1:], columns=["Date_raw", "Debit_raw"])
    # date : garder la partie avant 'T' (ISO) ou avant espace
    d = df_q["Date_raw"].str.split("T").str[0].str.split(" ").str[0]
    df_q["date"] = pd.to_datetime(d, errors="coerce").dt.date
    df_q["Q"]    = pd.to_numeric(
        df_q["Debit_raw"].astype(str).str.replace(",", "."), errors="coerce")
    return df_q[["date", "Q"]].dropna()



# ============================================================
# FUSION DES DÉBITS — comblement conditionnel (décisions projet)
# ============================================================
def fusionner_debits(fichier_influence, fichier_desinfluence=None,
                     seuil_comblement=0.10, verbose=True):
    """
    Fusionne les chroniques de débit influencé et (optionnellement)
    désinfluencé, et détermine la base de calcul selon la règle projet :

      - Influencé seul                → base "influencé".
      - Influencé + désinfluencé :
          * on mesure l'écart relatif médian sur la période commune :
                e = médiane(|Q_desinf − Q_inf| / Q_inf)
          * si e < seuil_comblement    → base "désinfluencé", trous du
                                         désinfluencé comblés par l'influencé
                                         (séries proches, comblement sans risque) ;
          * si e ≥ seuil_comblement    → BASCULE en base "influencé" (séries
                                         trop divergentes : mélanger fausserait
                                         la base ; on privilégie l'homogénéité
                                         et le nombre de jours) + avertissement.

    Retourne (df_q, diag) où :
      df_q : DataFrame [date, Q, Q_inf, (Q_desinf)]  — Q = base de calcul
      diag : dict décrivant la base retenue et le diagnostic d'écart.
    """
    if fichier_influence is None:
        return None, dict(base="aucune", message="Aucun fichier débit fourni.")

    df_inf = charger_debit(fichier_influence).rename(columns={"Q": "Q_inf"})
    diag = dict(base="influencé", ecart_median=None, n_inf=len(df_inf),
                n_desinf=0, n_comble=0, bascule=False,
                seuil_comblement=seuil_comblement)

    if not fichier_desinfluence:
        df_inf["Q"] = df_inf["Q_inf"]
        diag["message"] = ("Base influencée (désinfluencé non fourni). "
                           "La note recommande le désinfluencé pour la synthèse.")
        if verbose:
            print(f"  Base de débit : influencé ({len(df_inf)} j) — "
                  f"désinfluencé non fourni")
        return df_inf[["date", "Q_inf", "Q"]], diag

    df_des = charger_debit(fichier_desinfluence).rename(columns={"Q": "Q_desinf"})
    df = df_inf.merge(df_des, on="date", how="outer").sort_values("date")
    diag["n_desinf"] = int(df["Q_desinf"].notna().sum())

    # Écart relatif médian sur la période commune (les deux existent)
    commun = df.dropna(subset=["Q_inf", "Q_desinf"])
    commun = commun[commun["Q_inf"] > 0]
    if len(commun) >= 5:
        ecart = float(np.median(
            (commun["Q_desinf"] - commun["Q_inf"]).abs() / commun["Q_inf"]))
    else:
        ecart = np.nan
    diag["ecart_median"] = ecart
    diag["n_commun"] = len(commun)

    seuil_ok = (not np.isnan(ecart)) and ecart < seuil_comblement

    if seuil_ok:
        # Base désinfluencée, trous comblés par l'influencé
        df["Q"] = df["Q_desinf"].where(df["Q_desinf"].notna(), df["Q_inf"])
        n_comble = int(df["Q_desinf"].isna().sum() & df["Q_inf"].notna().sum()) \
            if False else int((df["Q_desinf"].isna() & df["Q_inf"].notna()).sum())
        diag.update(base="désinfluencé", n_comble=n_comble, bascule=False,
                    message=(f"Base désinfluencée (écart médian "
                             f"{ecart*100:.1f}% < {seuil_comblement*100:.0f}%). "
                             f"{n_comble} jour(s) comblé(s) par l'influencé. "
                             f"Influencé chargé pour information."))
        if verbose:
            print(f"  Base de débit : désinfluencé — écart médian {ecart*100:.1f}% "
                  f"< {seuil_comblement*100:.0f}% → {n_comble} j comblés par influencé")
    else:
        # Écart trop fort → bascule tout en influencé + avertissement
        df["Q"] = df["Q_inf"]
        diag.update(base="influencé", bascule=True,
                    message=(f"⚠ Écart médian influencé/désinfluencé "
                             f"{ecart*100:.1f}% ≥ {seuil_comblement*100:.0f}% : "
                             f"séries trop divergentes. BASCULE en base INFLUENCÉE "
                             f"(homogénéité + nb de jours). Attention : forte "
                             f"divergence = fortes pressions anthropiques — les "
                             f"seuils sont donc exprimés en influencé pour cette "
                             f"station."))
        if verbose:
            print(f"  ⚠️  Base de débit : influencé (BASCULE) — écart médian "
                  f"{ecart*100:.1f}% ≥ {seuil_comblement*100:.0f}%")

    cols = ["date", "Q_inf", "Q_desinf", "Q"]
    return df[[c for c in cols if c in df.columns]].dropna(subset=["Q"]), diag
