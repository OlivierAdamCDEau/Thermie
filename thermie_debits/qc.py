"""
qc.py — Contrôle qualité / nettoyage des artefacts (package thermie_debits).

Détecteurs paramétrables : bornes physiques, sonde hors d'eau (exondation),
plateau (sonde bloquée), outliers MAD. Chaque exclusion est tracée avec son
motif. Le paramétrage arrive via un dict (voir QCConfig.to_legacy_dict()).
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def controle_qualite(daily_eau, df_air, qc, verbose=True):
    """
    Applique les détecteurs d'artefacts activés dans `qc` sur la chronique
    journalière de température d'eau (déjà fusionnée avec l'air pour le
    diagnostic hors d'eau). Retourne (daily_propre, rapport) où `rapport`
    est un DataFrame des enregistrements écartés avec le motif.

    Les détecteurs sont volontairement conservateurs et indépendants : on
    n'invalide que ce qui est diagnostiqué, en traçant chaque exclusion.
    """
    df = daily_eau.merge(df_air, on="date", how="left").copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df["month"]   = df["date_dt"].dt.month
    df["year"]    = df["date_dt"].dt.year
    df = df.sort_values("date_dt").reset_index(drop=True)

    df["_flag"]  = False
    df["_motif"] = ""

    def _marque(mask, motif):
        n = int((mask & ~df["_flag"]).sum())
        df.loc[mask & ~df["_flag"], "_motif"] = motif
        df.loc[mask, "_flag"] = True
        return n

    log = []

    # 1) Bornes physiques
    if qc.get("bornes_physiques"):
        m = (df["T_eau_moy"] < qc["T_eau_min"]) | (df["T_eau_moy"] > qc["T_eau_max"]) \
            | (df["T_eau_max"] > qc["T_eau_max"])
        n = _marque(m, f"hors bornes [{qc['T_eau_min']};{qc['T_eau_max']}]°C")
        log.append(("Bornes physiques", n))

    # 2) Plateau / sonde bloquée (écart-type glissant ~nul)
    if qc.get("plateau"):
        w = qc["plateau_fenetre"]
        roll_std = df["T_eau_moy"].rolling(window=w, center=True,
                                           min_periods=w).std()
        m = roll_std < qc["plateau_ecart_type_min"]
        # ne pas flaguer les périodes hivernales stables proches de 0°C par gel
        n = _marque(m.fillna(False),
                    f"plateau σ<{qc['plateau_ecart_type_min']}°C/{w}j (sonde bloquée)")
        log.append(("Plateau/sonde bloquée", n))

    # 3) Sonde hors d'eau : T_eau_max >> T_air en étiage estival
    #    Diagnostic par (année) sur la fenêtre estivale.
    if qc.get("hors_eau"):
        mois = qc["hors_eau_mois"]
        seuil = qc["hors_eau_ecart_seuil"]
        min_j = qc["hors_eau_min_jours"]
        ecart = df["T_eau_max"] - df["T_air"]
        susp_jour = (df["month"].isin(mois)) & (ecart > seuil) & df["T_air"].notna()
        n_jours = 0
        annees_exclues = []
        for yr, sub in df[df["month"].isin(mois)].groupby("year"):
            e = (sub["T_eau_max"] - sub["T_air"])
            n_susp = int(((e > seuil) & sub["T_air"].notna()).sum())
            if n_susp >= min_j:
                if qc.get("hors_eau_exclut_saison"):
                    m = (df["year"] == yr) & (df["month"].isin(mois))
                    n_jours += _marque(m, f"hors d'eau — saison JJAS {yr} exclue "
                                          f"(écart>{seuil}°C sur {n_susp}j)")
                    annees_exclues.append(int(yr))
                else:
                    m = (df["year"] == yr) & susp_jour
                    n_jours += _marque(m, f"hors d'eau — jours suspects {yr}")
        log.append(("Sonde hors d'eau", n_jours))
        if verbose and annees_exclues:
            print(f"    ↳ saisons JJAS exclues (hors d'eau) : {annees_exclues}")

    # 4) Outliers MAD sur T_eau_moy
    if qc.get("mad_outliers"):
        base = df.copy()
        if qc.get("mad_mois"):
            base = base[base["month"].isin(qc["mad_mois"])]
        med = base["T_eau_moy"].median()
        mad = (base["T_eau_moy"] - med).abs().median()
        if mad > 0:
            seuil = qc["mad_k"] * mad
            m = (df["T_eau_moy"] - med).abs() > seuil
            if qc.get("mad_mois"):
                m = m & df["month"].isin(qc["mad_mois"])
            n = _marque(m, f"outlier MAD (>{qc['mad_k']}×MAD, |Δméd|>{seuil:.2f}°C)")
            log.append(("Outliers MAD", n))
        else:
            log.append(("Outliers MAD", 0))

    rapport = df[df["_flag"]][["date", "T_eau_moy", "T_eau_max", "T_air",
                                "_motif"]].rename(columns={"_motif": "motif"})
    propre = (df[~df["_flag"]]
              .drop(columns=["_flag", "_motif", "date_dt", "month", "year",
                             "T_air"])
              .reset_index(drop=True))

    if verbose:
        print("  ── Contrôle qualité ──")
        for nom_d, n in log:
            print(f"    {nom_d:28s} : {n:5d} enreg. écartés")
        print(f"    {'TOTAL écarté':28s} : {len(rapport):5d} / {len(df)} "
              f"({100*len(rapport)/max(len(df),1):.1f}%)")

    return propre, rapport
