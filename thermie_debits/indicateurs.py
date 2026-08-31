"""
indicateurs.py — Indicateurs thermiques bruts (package thermie_debits).

Calcule, par mois et à l'année :
  - Tmax et Tmin (avec date/heure d'occurrence) ;
  - amplitude nycthémérale (écart Tmax-Tmin journalier) : moyenne + écart-type ;
  - Tmm30j : température moyenne maximale sur 30 jours consécutifs (année civile).

CORRECTIF 4 (D18), VOIE B — la famille « compensation » a été RETIRÉE.
Ce module produisait trois séries journalières `T - Delta_TMm` : anomalie
BRUTE, aucun coefficient. La chaîne applique par ailleurs une convention
unique, `T - m x Delta_TMm_liss` — anomalie lissée, coefficient estimé —, et
le même mot « compensé » servait à désigner les deux. Ce module ne publie plus
que des indicateurs BRUTS ; les températures corrigées sont celles de
`core.py`, et elles s'appellent normalisées.

Ce qui disparaît avec elles, et qui n'a d'équivalent nulle part : la
couverture de janvier à décembre (la normalisation n'agrège que juin-septembre
et les fenêtres de reproduction), le minimum corrigé, et la moyenne mobile de
trente jours corrigée. Le journal des verdicts le consigne.

Fournit aussi les données des 4 corrélations linéaires (amplitude/débit,
amplitude/Teau, écart Teau-Tair/débit, écart Teau-Tair/Teau) avec R².

Aucun I/O, aucune figure : renvoie des DataFrames et des dicts exploitables
par figures.py et l'app.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats

MOIS_FR = {1: "Janv", 2: "Févr", 3: "Mars", 4: "Avr", 5: "Mai", 6: "Juin",
           7: "Juil", 8: "Août", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Déc"}


def _amplitude_journaliere(sub):
    """Amplitude nycthémérale par jour = Tmax - Tmin infra-journalier.
    Retourne un DataFrame [date, ampl, T_moy_jour]."""
    if sub is None or len(sub) == 0:
        return pd.DataFrame(columns=["date", "ampl", "T_moy_jour"])
    g = sub.groupby("date")["T_eau"]
    amp = (g.max() - g.min()).rename("ampl")
    tmoy = g.mean().rename("T_moy_jour")
    n = g.size().rename("n")
    out = pd.concat([amp, tmoy, n], axis=1).reset_index()
    # amplitude fiable seulement si assez de mesures dans la journée
    out.loc[out["n"] < 3, "ampl"] = np.nan
    out["date"] = pd.to_datetime(out["date"])
    return out[["date", "ampl", "T_moy_jour"]]


def _extrema_avec_date(sub, mode="max"):
    """Trouve l'extremum (max ou min) et l'horodatage où il survient."""
    if sub is None or len(sub) == 0:
        return np.nan, None
    idx = sub["T_eau"].idxmax() if mode == "max" else sub["T_eau"].idxmin()
    return float(sub.loc[idx, "T_eau"]), sub.loc[idx, "datetime"]


def _tmm30j(serie_journaliere):
    """Température moyenne maximale sur 30 jours consécutifs (moy. mobile)."""
    s = pd.Series(serie_journaliere).dropna()
    if len(s) < 30:
        return np.nan
    return float(s.rolling(30, min_periods=25).mean().max())


def calcul_indicateurs(df, sub, verbose=False):
    """
    Calcule les indicateurs bruts par mois et à l'année.

    df  : DataFrame journalier fusionné (avec T_eau_moy/max/min, Delta_TMm,
          date_dt, month ; éventuellement Q, T_air).
    sub : DataFrame infra-journalier (datetime, date, T_eau) pour l'amplitude
          nycthémérale et les extrema horodatés.

    Retourne un dict :
      table_mensuelle : DataFrame (une ligne par mois + ligne « Année »)
      correlations    : dict des 4 corrélations {x, y, r2, pente, ...}
    """
    d = df.copy()
    d["date_dt"] = pd.to_datetime(d["date_dt"] if "date_dt" in d else d["date"])
    d["month"] = d["date_dt"].dt.month
    d["year"] = d["date_dt"].dt.year

    # amplitude nycthémérale journalière (depuis l'infra-journalier)
    amp_j = _amplitude_journaliere(sub)
    if len(amp_j):
        amp_j["month"] = amp_j["date"].dt.month
        d = d.merge(amp_j[["date", "ampl"]].rename(columns={"date": "date_dt"}),
                    on="date_dt", how="left")
    else:
        d["ampl"] = np.nan

    # CORRECTIF 4, VOIE B — les trois séries `T - Delta_TMm` sont retirées.
    #
    # `has_delta` RESTE, et ce n'est pas un oubli : il a un second
    # consommateur, plus bas, qui conditionne le calcul de `ecart_eau_air` et
    # donc DEUX des quatre corrélations. Cette grandeur ne lit pas
    # `Delta_TMm` — mais sa condition de calcul, si. Retirer la variable avec
    # la famille aurait fait apparaître deux corrélations sur tout point ayant
    # un `T_air` sans `Delta_TMm`, sans que rien ne le signale.
    has_delta = "Delta_TMm" in d.columns

    lignes = []

    def _stats_periode(sub_d, sub_infra, label):
        row = {"Période": label}
        # Tmax / Tmin bruts avec horodatage (depuis l'infra si dispo)
        if sub_infra is not None and len(sub_infra):
            tmax, dmax = _extrema_avec_date(sub_infra, "max")
            tmin, dmin = _extrema_avec_date(sub_infra, "min")
        else:
            tmax = sub_d["T_eau_max"].max() if len(sub_d) else np.nan
            tmin = sub_d["T_eau_min"].min() if len(sub_d) else np.nan
            dmax = dmin = None
        row["Tmax (°C)"] = round(tmax, 2) if pd.notna(tmax) else np.nan
        row["Tmax date"] = dmax.strftime("%d/%m %Hh") if dmax is not None else "—"
        row["Tmin (°C)"] = round(tmin, 2) if pd.notna(tmin) else np.nan
        row["Tmin date"] = dmin.strftime("%d/%m %Hh") if dmin is not None else "—"
        # amplitude nycthémérale : moyenne ± écart-type
        a = sub_d["ampl"].dropna()
        row["Ampl. moy (°C)"] = round(a.mean(), 2) if len(a) else np.nan
        row["Ampl. σ (°C)"] = round(a.std(), 2) if len(a) > 1 else np.nan
        return row

    for m in range(1, 13):
        sub_d = d[d["month"] == m]
        if len(sub_d) == 0:
            continue
        sub_infra = sub[pd.to_datetime(sub["date"]).dt.month == m] if (sub is not None and len(sub)) else None
        lignes.append(_stats_periode(sub_d, sub_infra, MOIS_FR[m]))

    # ligne Année
    row_an = _stats_periode(d, sub, "Année")
    row_an["Tmm30j brut (°C)"] = round(_tmm30j(d["T_eau_moy"]), 2) if "T_eau_moy" in d else np.nan
    lignes.append(row_an)

    table = pd.DataFrame(lignes)

    # -------- Corrélations (4 graphiques) --------
    def _correl(x, y, xlabel, ylabel, log_x=False):
        """
        log_x=True : régresse sur log(x) plutôt que x brut — retenu pour les
        deux corrélations à débit en abscisse. Justification : le tampon
        thermique (amplitude nycthémérale, écart eau-air) croît avec le
        volume/profondeur à rendements décroissants, une relation en loi de
        puissance qui s'écrit linéairement en log(Q) ; cela rejoint aussi la
        convention déjà adoptée ailleurs dans la méthode (PNDA, corrélation
        partielle Q↔T°, débits classés — tous traités en échelle log).
        """
        m_ = pd.DataFrame({"x": x, "y": y}).dropna()
        if log_x:
            m_ = m_[m_["x"] > 0]
        if len(m_) < 5:
            return dict(x=[], y=[], r2=np.nan, pente=np.nan, ordonnee=np.nan,
                        n=len(m_), xlabel=xlabel, ylabel=ylabel, log_x=log_x)
        xv = np.log(m_["x"].values) if log_x else m_["x"].values
        sl, ic, r, p, _ = stats.linregress(xv, m_["y"])
        return dict(x=m_["x"].values, y=m_["y"].values, r2=r**2, pente=sl,
                    ordonnee=ic, n=len(m_), xlabel=xlabel, ylabel=ylabel,
                    log_x=log_x)

    correlations = {}
    has_q = "Q" in d.columns and d["Q"].notna().any()
    has_air = "T_air" in d.columns and d["T_air"].notna().any()
    # `has_delta` est ici le SECOND consommateur annonce plus haut. La
    # condition est conservee TELLE QUELLE par le correctif 4 : la modifier
    # ferait apparaitre deux correlations la ou il n'y en avait pas, ce qui
    # serait un changement de comportement deguise en nettoyage.
    if has_delta and has_air:
        d["ecart_eau_air"] = d["T_eau_moy"] - d["T_air"]

    if has_q:
        correlations["ampl_vs_debit"] = _correl(
            d["Q"], d["ampl"], "Débit (m³/s)", "Amplitude nycthémérale (°C)",
            log_x=True)
    correlations["ampl_vs_teau"] = _correl(
        d["T_eau_moy"], d["ampl"], "T° eau (°C)", "Amplitude nycthémérale (°C)")
    if has_air:
        if has_q:
            correlations["ecart_vs_debit"] = _correl(
                d["Q"], d["ecart_eau_air"], "Débit (m³/s)", "Écart T°eau − T°air (°C)",
                log_x=True)
        correlations["ecart_vs_teau"] = _correl(
            d["T_eau_moy"], d["ecart_eau_air"], "T° eau (°C)", "Écart T°eau − T°air (°C)")

    if verbose:
        print(f"  Indicateurs : {len(table)} lignes, "
              f"{len([c for c in correlations.values() if c['n']>=5])} corrélations exploitables")

    return dict(table_mensuelle=table, correlations=correlations)
