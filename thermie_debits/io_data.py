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


def charger_eau(fichier_eau, col_date=None, col_temp=None, nom="",
                feuille=None, ligne_entete=None, retour_sous_quotidien=False):
    """Charge une chronique de sonde thermique → daily (T_eau_moy/max/min).

    Détection robuste (CSV/Excel, séparateur, encodage, colonnes, en-tête
    décalé) via sniff. Les paramètres col_date / col_temp / feuille /
    ligne_entete permettent un override manuel (mapping app).

    Si retour_sous_quotidien=True, retourne (daily, sub) où `sub` conserve les
    mesures infra-journalières (datetime, T_eau) — utile pour l'amplitude
    nycthémérale et les indicateurs.
    """
    from .sniff import lire_brut, deviner_colonnes
    if not nom and isinstance(fichier_eau, str):
        nom = fichier_eau
    df_w, _meta = lire_brut(fichier_eau, nom=nom, feuille=feuille,
                            ligne_entete=ligne_entete)

    if col_temp is None:
        _, col_temp = deviner_colonnes(df_w)
    if col_date is None:
        cand = [c for c in df_w.columns
                if any(m in c.lower() for m in
                       ["date", "heure", "time", "timestamp", "horodat"])]
        for dc in cand:
            samp = str(df_w[dc].dropna().iloc[0]) if len(df_w[dc].dropna()) else ""
            if len(samp) > 8:
                col_date = dc; break
        if col_date is None and cand:
            col_date = cand[0]

    if col_date is None or col_temp is None:
        raise ValueError(
            f"Colonnes sonde non détectées (date={col_date}, temp={col_temp}). "
            f"Colonnes disponibles : {list(df_w.columns)}. "
            f"Précisez le mapping manuellement.")

    dt = _parse_dates_sonde(df_w[col_date])
    # Colonne heure séparée : tout nom commençant par 'heure' (ex. 'Heure, GMT+02:00')
    col_h = next((c for c in df_w.columns
                  if c.lower().startswith("heure") and c != col_date), None)
    if col_h is not None and dt.notna().any() and (dt.dt.hour == 0).all():
        def _td(h):
            try:
                h = str(h).strip()
                return pd.Timedelta(h) if ":" in h else pd.Timedelta(0)
            except Exception:
                return pd.Timedelta(0)
        dt = dt + df_w[col_h].apply(_td)

    df_w = df_w.copy()
    df_w["datetime"] = dt
    df_w["T_eau"] = pd.to_numeric(
        df_w[col_temp].astype(str).str.replace(",", ".").str.replace(" ", ""),
        errors="coerce")
    df_w["date"] = df_w["datetime"].dt.date
    df_w = df_w.dropna(subset=["date", "T_eau"])

    daily = df_w.groupby("date").agg(
        T_eau_moy=("T_eau", "mean"),
        T_eau_max=("T_eau", "max"),
        T_eau_min=("T_eau", "min"),
        n_mesures=("T_eau", "size")).reset_index()

    if retour_sous_quotidien:
        sub = df_w[["datetime", "date", "T_eau"]].dropna(subset=["datetime"]).copy()
        return daily, sub
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
    désinfluencé.

    BASE D'ANALYSE (recherche du seuil biologique Q*_vuln, test de
    causalité débit↔température) : TOUJOURS l'influencé. C'est l'eau
    réellement présente qui gouverne la température observée cette
    année-là ; le désinfluencé est une reconstruction hypothétique,
    impropre à servir de variable causale. Il n'y a donc plus de
    « bascule » de l'analyse elle-même selon la proximité des deux séries
    — décision volontairement simple et toujours motivée de la même façon.

    Le désinfluencé, quand il est fourni, est systématiquement conservé et
    valorisé pour la RESTITUTION (PNDA + courbe des débits classés sur sa
    propre distribution, ailleurs dans le pipeline) — jamais conditionné à
    un seuil de proximité avec l'influencé : une forte divergence est
    elle-même une information utile (intensité de la pression anthropique
    sur la station), pas une raison de l'écarter.

    Deux écarts relatifs médians sont calculés et restitués, sans qu'aucun
    ne soit choisi par défaut à la place de l'autre :
      - écart ANNUEL (toutes saisons) ;
      - écart JUIN-SEPTEMBRE (JJAS — la fenêtre qui conditionne l'étiage).
    Un écart annuel faible peut masquer une divergence estivale majeure
    (prélèvements concentrés en été, recharge hivernale complète) : les
    deux sont donc toujours calculés plutôt que d'en choisir un seul.

    Le comblement des trous du désinfluencé par l'influencé (pour disposer
    d'une distribution désinfluencée aussi complète que possible en vue de
    son PNDA propre) reste conditionné à un seuil, mais retenu seulement si
    les DEUX écarts (annuel ET JJAS) sont sous ce seuil — le pire des deux
    doit être acceptable, pour ne pas combler des trous d'été avec un
    influencé très éloigné alors que l'écart annuel semblerait rassurant.

    Retourne (df_q, diag) où :
      df_q : DataFrame [date, Q, Q_inf, (Q_desinf)] — Q = influencé (base
             d'analyse), Q_desinf = série désinfluencée (comblée ou non).
      diag : dict décrivant les écarts et l'état du comblement.
    """
    if fichier_influence is None:
        return None, dict(base="aucune", message="Aucun fichier débit fourni.")

    df_inf = charger_debit(fichier_influence).rename(columns={"Q": "Q_inf"})
    diag = dict(base="influencé", desinfluence_disponible=False,
                ecart_annuel=None, ecart_jjas=None, n_inf=len(df_inf),
                n_desinf=0, n_comble=0, comble=False,
                seuil_comblement=seuil_comblement)

    if not fichier_desinfluence:
        df_inf["Q"] = df_inf["Q_inf"]
        diag["message"] = ("Base d'analyse : influencé (désinfluencé non "
                           "fourni — la restitution finale y perd la lecture "
                           "PNDA désinfluencée, à privilégier si disponible).")
        if verbose:
            print(f"  Base d'analyse (débit) : influencé ({len(df_inf)} j) — "
                  f"désinfluencé non fourni")
        return df_inf[["date", "Q_inf", "Q"]], diag

    df_des = charger_debit(fichier_desinfluence).rename(columns={"Q": "Q_desinf"})
    df = df_inf.merge(df_des, on="date", how="outer").sort_values("date")
    diag["desinfluence_disponible"] = True
    diag["n_desinf"] = int(df["Q_desinf"].notna().sum())

    def _ecart_median(sub):
        commun = sub.dropna(subset=["Q_inf", "Q_desinf"])
        commun = commun[commun["Q_inf"] > 0]
        if len(commun) < 5:
            return np.nan, len(commun)
        return float(np.median(
            (commun["Q_desinf"] - commun["Q_inf"]).abs() / commun["Q_inf"])), len(commun)

    ecart_an, n_commun_an = _ecart_median(df)
    mois = pd.to_datetime(df["date"]).dt.month
    ecart_jjas, n_commun_jjas = _ecart_median(df[mois.isin([6, 7, 8, 9])])
    diag.update(ecart_annuel=ecart_an, n_commun_annuel=n_commun_an,
                ecart_jjas=ecart_jjas, n_commun_jjas=n_commun_jjas)

    # Comblement des trous du désinfluencé : retenu seulement si le PIRE des
    # deux écarts (annuel, JJAS) reste sous le seuil — un écart annuel
    # rassurant ne suffit pas si la divergence estivale est forte.
    ecarts_valides = [e for e in (ecart_an, ecart_jjas) if not np.isnan(e)]
    comble_ok = bool(ecarts_valides) and max(ecarts_valides) < seuil_comblement

    df["Q"] = df["Q_inf"]  # base d'analyse : toujours influencé
    if comble_ok:
        n_comble = int((df["Q_desinf"].isna() & df["Q_inf"].notna()).sum())
        df["Q_desinf"] = df["Q_desinf"].where(df["Q_desinf"].notna(), df["Q_inf"])
        diag.update(comble=True, n_comble=n_comble)
        msg_comble = (f"trous du désinfluencé comblés par l'influencé "
                     f"({n_comble} j)")
    else:
        msg_comble = ("trous du désinfluencé NON comblés — écart annuel "
                     f"{ecart_an*100:.1f}%" if not np.isnan(ecart_an) else
                     "trous du désinfluencé NON comblés") + \
                     (f" / JJAS {ecart_jjas*100:.1f}%" if not np.isnan(ecart_jjas)
                      else "") + f" ≥ seuil {seuil_comblement*100:.0f}%"

    diag["message"] = (
        f"Base d'analyse : influencé ({len(df)} j). Désinfluencé disponible "
        f"({diag['n_desinf']} j) — écart médian annuel "
        f"{ecart_an*100:.1f}% / JJAS "
        f"{ecart_jjas*100:.1f}% ; {msg_comble}." if not (np.isnan(ecart_an) or
        np.isnan(ecart_jjas)) else
        f"Base d'analyse : influencé ({len(df)} j). Désinfluencé disponible "
        f"({diag['n_desinf']} j) ; {msg_comble}.")
    if verbose:
        ea = f"{ecart_an*100:.1f}%" if not np.isnan(ecart_an) else "n/d"
        ej = f"{ecart_jjas*100:.1f}%" if not np.isnan(ecart_jjas) else "n/d"
        print(f"  Base d'analyse (débit) : influencé — désinfluencé "
              f"disponible, écart médian annuel {ea} / JJAS {ej} — "
              f"{msg_comble}")

    cols = ["date", "Q_inf", "Q_desinf", "Q"]
    return df[[c for c in cols if c in df.columns]].dropna(subset=["Q"]), diag


# ============================================================
# AIR — chargement brut flexible + calcul des normales/écarts
# ============================================================
from .sniff import lire_brut, deviner_colonnes

REF_NORMALES = (1991, 2020)


def _parse_dates_air(serie):
    """Parse dates air : gère AAAAMMJJ (YYYYMMDD), ISO, DD/MM/YYYY."""
    s = serie.astype(str).str.strip()
    if s.str.match(r"^\d{8}$").mean() > 0.8:
        return pd.to_datetime(s, format="%Y%m%d", errors="coerce")
    best = None
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y%m%d", "%d/%m/%Y %H:%M"]:
        att = pd.to_datetime(s, format=fmt, errors="coerce")
        if best is None or att.notna().sum() > best.notna().sum():
            best = att
    if best is None or best.notna().sum() == 0:
        best = pd.to_datetime(s, format="mixed", dayfirst=True, errors="coerce")
    return best


def charger_air_brut(source, col_date=None, col_temp=None):
    """
    Charge un fichier air brut (T° journalières station de référence),
    couvrant potentiellement une plage large. Auto-détecte séparateur,
    encodage et colonnes (date, TM). Conserve RR si présent.
    Retourne un DataFrame [date, T_air, (RR)].
    """
    df, meta = lire_brut(source)
    if col_date is None:
        col_date = next((c for c in df.columns if c.upper() == "AAAAMMJJ"), None)
    if col_date is None:
        col_date, _ = deviner_colonnes(df, mots_valeur=[])
    if col_temp is None:
        col_temp = next((c for c in df.columns if c.upper() == "TM"), None)
    if col_temp is None:
        _, col_temp = deviner_colonnes(
            df, mots_valeur=["tm", "temp", "t_air", "tair", "°c", "degr", "valeur"])
    if col_date is None or col_temp is None:
        raise ValueError(
            f"Colonnes air non détectées (date={col_date}, temp={col_temp}). "
            f"Colonnes disponibles : {list(df.columns)}")

    out = pd.DataFrame()
    out["date"] = _parse_dates_air(df[col_date]).dt.date
    out["T_air"] = pd.to_numeric(
        df[col_temp].astype(str).str.replace(",", "."), errors="coerce")
    rr_col = next((c for c in df.columns if c.upper() == "RR"), None)
    if rr_col:
        out["RR"] = pd.to_numeric(
            df[rr_col].astype(str).str.replace(",", "."), errors="coerce")
    return out.dropna(subset=["date", "T_air"])


def calculer_normales_ecarts(df_air, ref=REF_NORMALES, fenetre_lissage=10,
                             min_annees=20, verbose=True):
    """
    À partir de l'air brut, calcule la normale lissée de chaque jour calendaire
    (moyenne sur ±fenetre_lissage jours, années de `ref`) et l'écart
    Delta_TMm = T_air − normale, pour TOUS les jours observés.
    Retourne (ecart_by_date, normales_lkp, diag).
    """
    df = df_air.copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df["year"]  = df["date_dt"].dt.year
    df["month"] = df["date_dt"].dt.month
    df["day"]   = df["date_dt"].dt.day
    df["doy"]   = df["date_dt"].dt.dayofyear

    y0, y1 = ref
    df_ref = df[(df["year"] >= y0) & (df["year"] <= y1)]
    annees_ref = sorted(df_ref["year"].unique().tolist())
    n_annees = len(annees_ref)

    diag = dict(ref=ref, n_annees_ref=n_annees, annees_ref=annees_ref,
                fenetre_lissage=fenetre_lissage, min_annees=min_annees,
                periode_totale=(int(df["year"].min()), int(df["year"].max())),
                avertissements=[])

    if n_annees == 0:
        raise ValueError(
            f"Aucune année de la période de référence {y0}-{y1} trouvée dans "
            f"le fichier air (couvre {diag['periode_totale']}).")
    if n_annees < min_annees:
        msg = (f"Normales calculées sur {n_annees} année(s) seulement "
               f"(< {min_annees} requis) sur {y0}-{y1}. Fiabilité réduite.")
        diag["avertissements"].append(msg)
        if verbose:
            print(f"  ⚠️  {msg}")

    brute = df_ref.groupby("doy")["T_air"].mean()
    idx = pd.Series(index=range(1, 367), dtype=float)
    idx.loc[brute.index] = brute.values
    idx = idx.interpolate(limit_direction="both")
    w = 2 * fenetre_lissage + 1
    triple = pd.concat([idx, idx, idx], ignore_index=True)
    liss = triple.rolling(window=w, center=True, min_periods=1).mean()
    normale_doy = liss.iloc[366:366*2].reset_index(drop=True)
    normale_doy.index = range(1, 367)

    ref_dates = pd.to_datetime(pd.Series(pd.date_range("2000-01-01", "2000-12-31")))
    lkp = pd.DataFrame({
        "day": ref_dates.dt.day.values,
        "month": ref_dates.dt.month.values,
        "doy": ref_dates.dt.dayofyear.values})
    lkp["T_normale"] = lkp["doy"].map(normale_doy)
    normales_lkp = lkp[["day", "month", "T_normale"]]

    df = df.merge(normales_lkp, on=["day", "month"], how="left")
    df["Delta_TMm"] = df["T_air"] - df["T_normale"]
    ecart_by_date = df[["date", "Delta_TMm"]].dropna()

    if verbose:
        print(f"  Normales 1991–2020 : {n_annees} ans, lissage ±{fenetre_lissage}j "
              f"| écarts sur {len(ecart_by_date)} jours "
              f"({diag['periode_totale'][0]}–{diag['periode_totale'][1]})")

    return ecart_by_date, normales_lkp, diag
