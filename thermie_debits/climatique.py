"""
climatique.py — Volet climatique bonus (package thermie_debits).

Contexte descriptif long terme : tendance thermique (écart aux normales),
étiages, débit estival, température d'eau inter-annuelle, précipitations.

IMPORTANT : volet purement descriptif, sur données BRUTES (contexte observé
réel, artefacts inclus) — distinct des volets thermie/débits qui appliquent
le QC. N'alimente pas les débits de référence.

Les fonctions retournent la liste des figures produites (et les sauvegardent
si output_dir est fourni).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .io_data import charger_debit


def _clim_fin(fig, output_dir, filename):
    """Sauvegarde optionnelle puis retourne la figure (comme figures._finalise)."""
    if output_dir:
        fig.savefig(f"{output_dir}{filename}", dpi=150, bbox_inches="tight")
        print(f"\u2705 {filename}")
    return fig



def volet_climatique(daily_eau, df_air, df, contexte, nom, output_dir,
                     fichier_debit=None):
    import matplotlib.patches as mpatches
    BLUE, RED, DKRED, AMBER = "#378ADD", "#E24B4A", "#A32D2D", "#BA7517"
    print("\nVolet climatique (bonus)...")
    print("  ℹ️  Volet descriptif : température d'eau BRUTE (contexte observé réel,")
    print("      artefacts inclus) — distinct des volets thermie/débits (QC appliqué).")
    figs = []

    # -- Données annualisées --
    dfa = df_air.copy()
    dfa["date_dt"] = pd.to_datetime(dfa["date"])
    dfa["Year"] = dfa["date_dt"].dt.year
    dfa["Month"] = dfa["date_dt"].dt.month

    # Écart aux normales (depuis df fusionné : Delta_TMm)
    if "Delta_TMm" in df.columns:
        dd = df.dropna(subset=["Delta_TMm"]).copy()
        dd["Year"] = pd.to_datetime(dd["date"]).dt.year
        annual_delta = dd.groupby("Year")["Delta_TMm"].mean()
        roll10 = annual_delta.rolling(10, center=True, min_periods=3).mean()
        if len(annual_delta) >= 2:
            fig, ax = plt.subplots(figsize=(11, 4))
            yrs = annual_delta.index.values; vals = annual_delta.values
            ax.bar(yrs, vals, color=[RED if v >= 0 else BLUE for v in vals],
                   alpha=0.55, width=0.8, zorder=2)
            r = roll10.dropna()
            if len(r): ax.plot(r.index, r.values, color=AMBER, lw=2.2, zorder=3)
            ax.axhline(0, color="#888", lw=0.8, ls="--")
            ax.set_ylabel("°C"); ax.set_facecolor("#FAFAF7")
            ax.set_title(f"Air — écart à la normale 1991–2020\n{nom} · "
                         f"{int(yrs.min())}–{int(yrs.max())}", fontsize=11)
            ax.legend(handles=[
                mpatches.Patch(color=RED, alpha=0.55, label="Année chaude"),
                mpatches.Patch(color=BLUE, alpha=0.55, label="Année froide"),
                plt.Line2D([], [], color=AMBER, lw=2.2, label="Moy. mobile 10 ans"),
            ], loc="upper left", ncol=3, frameon=False)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim1_Ecart_Normale.png"))

    # Précipitations annuelles (si RR disponible)
    if "RR" in dfa.columns:
        rr = dfa.groupby("Year")["RR"].sum()
        rr = rr[rr > 0]
        if len(rr) >= 2:
            rr_mean = float(rr.mean())
            fig, ax = plt.subplots(figsize=(11, 3.8))
            ax.bar(rr.index, rr.values,
                   color=[BLUE if v >= rr_mean else RED for v in rr.values],
                   alpha=0.5, width=0.8, zorder=2)
            ax.axhline(rr_mean, color=AMBER, lw=1.8, ls="--",
                       label=f"Moyenne {round(rr_mean):.0f} mm")
            ax.set_ylabel("mm"); ax.set_ylim(0); ax.set_facecolor("#FAFAF7")
            ax.set_title(f"Précipitations annuelles — {nom} · "
                         f"{int(rr.index.min())}–{int(rr.index.max())}", fontsize=11)
            ax.legend(loc="upper left", frameon=False)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim5_Precipitations.png"))

    # Débit : jours d'étiage + débit estival (si débit chargé)
    if fichier_debit and "Q" in df.columns:
        dq = charger_debit(fichier_debit)
        dq["date_dt"] = pd.to_datetime(dq["date"])
        dq["Year"] = dq["date_dt"].dt.year
        dq["Month"] = dq["date_dt"].dt.month
        daily = dq.set_index("date_dt")["Q"]
        # seuils adaptatifs : médiane/4 et médiane/8 (au cas où l'échelle diffère)
        med = daily.median()
        s1, s05 = max(1.0, round(med * 0.3, 2)), max(0.5, round(med * 0.15, 2))
        days_lt1 = (daily < s1).groupby(daily.index.year).sum()
        days_lt05 = (daily < s05).groupby(daily.index.year).sum()
        all_yrs = sorted(set(days_lt1.index) | set(days_lt05.index))
        if len(all_yrs) >= 2:
            fig, ax = plt.subplots(figsize=(11, 4))
            x = np.arange(len(all_yrs))
            ax.bar(x, [int(days_lt1.get(y, 0)) for y in all_yrs], color=RED,
                   alpha=0.45, width=0.8, label=f"Jours Q < {s1} m³/s")
            ax.bar(x, [int(days_lt05.get(y, 0)) for y in all_yrs], color=DKRED,
                   alpha=0.85, width=0.8, label=f"Jours Q < {s05} m³/s (critique)")
            ax.set_xticks(x[::2]); ax.set_xticklabels([str(y) for y in all_yrs[::2]],
                                                      rotation=45, ha="right")
            ax.set_ylabel("Jours / an"); ax.set_facecolor("#FAFAF7")
            ax.set_title(f"Débits d'étiage — jours sous seuils\n{nom} · "
                         f"{all_yrs[0]}–{all_yrs[-1]}", fontsize=11)
            ax.legend(loc="upper left", frameon=False)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim2_Jours_Etiage.png"))

        summer_q = dq[dq["Month"].isin([7, 8, 9])].groupby("Year")["Q"].mean()
        if len(summer_q) >= 2:
            fig, ax = plt.subplots(figsize=(11, 4))
            yrs3, sq3 = summer_q.index.values, summer_q.values
            ax.bar(yrs3, sq3, color=[DKRED if v < s1 else (RED if v < 2 * s1 else BLUE)
                   for v in sq3], alpha=0.75, width=0.8)
            ax.axhline(s1, color=DKRED, lw=1.2, ls="--", alpha=0.7)
            ax.set_ylim(0); ax.set_ylabel("m³/s"); ax.set_facecolor("#FAFAF7")
            ax.set_title(f"Débit moyen estival (juil.–sept.)\n{nom} · "
                         f"{int(yrs3.min())}–{int(yrs3.max())}", fontsize=11)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim3_Debit_Estival.png"))

    # Température de l'eau inter-annuelle (seuils du contexte)
    de = daily_eau.copy()
    de["date_dt"] = pd.to_datetime(de["date"])
    de["Year"] = de["date_dt"].dt.year
    teau_moy = de.groupby("Year")["T_eau_moy"].mean()
    s_chr, s_aig = contexte["seuil_chr"], contexte["seuil_aigu"]
    seuils = sorted({18, 21, s_chr, s_aig})
    if len(teau_moy) >= 1:
        years = sorted(teau_moy.index)
        cats = ["T° moy (°C)"] + [f"Jours >{s}°C" for s in seuils]
        palette = [BLUE, RED, AMBER, DKRED, "#639922", "#8E44AD"]
        x = np.arange(len(cats))
        w = min(0.35, 0.8 / max(len(years), 1))
        offs = np.linspace(-(len(years) - 1) * w / 2, (len(years) - 1) * w / 2, len(years))
        fig, ax = plt.subplots(figsize=(9, 4.5))
        for yr, off, col in zip(years, offs, palette * 3):
            sub = de[de["Year"] == yr]
            data = [round(float(teau_moy.get(yr, 0)), 2)]
            for s in seuils:
                data.append(int((sub["T_eau_max"] > s).sum()))
            bars = ax.bar(x + off, data, w * 0.9, color=col, alpha=0.7, label=str(yr))
            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.4,
                        f"{h:.1f}" if h < 10 else f"{int(h)}", ha="center",
                        va="bottom", fontsize=7, color="#444")
        ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=9)
        ax.set_facecolor("#FAFAF7")
        ax.set_title(f"Température de l'eau — comparaison inter-annuelle\n"
                     f"{nom} · seuils {contexte['label']}", fontsize=11)
        h_, l_ = ax.get_legend_handles_labels()
        if h_: ax.legend(h_, l_, loc="upper right", frameon=False, ncol=2)
        plt.tight_layout()
        figs.append(_clim_fin(fig, output_dir, "Clim4_Temperature_Eau.png"))

    print(f"  → {len(figs)} figure(s) climatique(s) produite(s)")
    return figs


