"""
climatique.py — Volet climatique bonus (package thermie_debits).

Contexte descriptif long terme : tendance thermique (écart aux normales),
étiages, débit estival, température d'eau inter-annuelle, précipitations.

IMPORTANT : volet purement descriptif, sur données BRUTES (contexte observé
réel, artefacts inclus) — distinct des volets thermie/débits qui appliquent
le QC. N'alimente pas les débits de référence.

Restitution en matplotlib, cohérente avec le reste de l'application. L'axe
des années est forcé en entiers (MaxNLocator(integer=True)) pour éviter tout
tickmark décimal sur les séries annuelles courtes.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from .io_data import charger_debit
from .print_style import style_legend

BLUE, RED, DKRED, AMBER, GREEN, PURPLE = (
    "#378ADD", "#C0392B", "#7B241C", "#B9770D", "#1E8449", "#7D3C98")


def _annees_entieres(ax):
    """Force l'axe des abscisses en années entières — corrige les tickmarks
    décimaux que produisait l'axe numérique par défaut sur de courtes
    séries annuelles (ex. « 2021.5 »)."""
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))


def _clim_fin(fig, output_dir, filename):
    if output_dir:
        fig.savefig(f"{output_dir}{filename}", dpi=150, bbox_inches="tight")
        print(f"✅ {filename}")
    return fig


def volet_climatique(daily_eau, df_air, df, contexte, nom, output_dir,
                     fichier_debit=None):
    print("\nVolet climatique (bonus)...")
    print("  ℹ️  Volet descriptif : température d'eau BRUTE (contexte observé réel,")
    print("      artefacts inclus) — distinct des volets thermie/débits (QC appliqué).")
    figs = []

    dfa = df_air.copy()
    dfa["date_dt"] = pd.to_datetime(dfa["date"])
    dfa["Year"] = dfa["date_dt"].dt.year
    dfa["Month"] = dfa["date_dt"].dt.month

    # ---- Clim1 — Écart annuel à la normale 1991-2020 ----
    annual_delta = None
    if "Delta_TMm" in df.columns:
        dd = df.dropna(subset=["Delta_TMm"]).copy()
        dd["Year"] = pd.to_datetime(dd["date"]).dt.year
        annual_delta = dd.groupby("Year")["Delta_TMm"].mean()
        roll10 = annual_delta.rolling(10, center=True, min_periods=3).mean()
        if len(annual_delta) >= 2:
            yrs = annual_delta.index.values
            fig, ax = plt.subplots(figsize=(10, 4.6))
            ax.set_facecolor("#f8f9fa")
            ax.bar(yrs, annual_delta.values,
                  color=[RED if v >= 0 else BLUE for v in annual_delta.values],
                  alpha=0.65, width=0.75, label="Écart annuel")
            r = roll10.dropna()
            if len(r):
                ax.plot(r.index.values, r.values, color=AMBER, lw=2.5,
                       label="Moyenne mobile 10 ans")
            ax.axhline(0, color="#888888", lw=0.8, ls="--")
            ax.set_ylabel("Écart à la normale (°C)", fontsize=10)
            ax.set_xlabel("Année", fontsize=10)
            ax.set_title(f"{nom} — Air : écart à la normale 1991–2020\n"
                        f"{int(yrs.min())}–{int(yrs.max())} — période de référence de "
                        f"la normalisation climatique (§2.3)", fontsize=11, fontweight="bold")
            leg = ax.legend(fontsize=8.5, loc="upper left"); style_legend(leg)
            ax.grid(True, alpha=0.3)
            _annees_entieres(ax)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim1_Ecart_Normale.png"))

    # ---- Clim5 — Précipitations annuelles ----
    rr_annual = None
    if "RR" in dfa.columns:
        rr_annual = dfa.groupby("Year")["RR"].sum()
        rr_annual = rr_annual[rr_annual > 0]
        if len(rr_annual) >= 2:
            rr_mean = float(rr_annual.mean())
            yrs = rr_annual.index.values
            fig, ax = plt.subplots(figsize=(10, 4.6))
            ax.set_facecolor("#f8f9fa")
            ax.bar(yrs, rr_annual.values,
                  color=[BLUE if v >= rr_mean else RED for v in rr_annual.values],
                  alpha=0.6, width=0.75, label="Précipitations annuelles")
            ax.axhline(rr_mean, color=AMBER, lw=2, ls="--",
                      label=f"Moyenne {rr_mean:.0f} mm")
            ax.set_ylabel("Cumul annuel (mm)", fontsize=10)
            ax.set_xlabel("Année", fontsize=10)
            ax.set_title(f"{nom} — Précipitations annuelles (cumul)\n"
                        f"{int(yrs.min())}–{int(yrs.max())}", fontsize=11, fontweight="bold")
            leg = ax.legend(fontsize=8.5, loc="best"); style_legend(leg)
            ax.grid(True, alpha=0.3)
            _annees_entieres(ax)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim5_Precipitations.png"))

    # ---- Clim2 / Clim3 — Débit : étiage et débit moyen estival ----
    days_lt1 = days_lt05 = None
    s1 = s05 = med = None
    if fichier_debit and "Q" in df.columns:
        dq = charger_debit(fichier_debit)
        dq["date_dt"] = pd.to_datetime(dq["date"])
        dq["Year"] = dq["date_dt"].dt.year
        dq["Month"] = dq["date_dt"].dt.month
        daily = dq.set_index("date_dt")["Q"]
        med = daily.median()
        # Seuils relatifs à la médiane du débit de la station (et non des
        # valeurs absolues arbitraires) — explicités dans le titre et la
        # légende, pour une lecture transparente des seuils d'étiage.
        s1, s05 = max(1.0, round(med * 0.3, 2)), max(0.5, round(med * 0.15, 2))
        days_lt1 = (daily < s1).groupby(daily.index.year).sum()
        days_lt05 = (daily < s05).groupby(daily.index.year).sum()
        all_yrs = sorted(set(days_lt1.index) | set(days_lt05.index))
        if len(all_yrs) >= 2:
            fig, ax = plt.subplots(figsize=(10, 4.6))
            ax.set_facecolor("#f8f9fa")
            v1 = [int(days_lt1.get(y, 0)) for y in all_yrs]
            v05 = [int(days_lt05.get(y, 0)) for y in all_yrs]
            ax.bar(all_yrs, v1, color=RED, alpha=0.5, width=0.75,
                  label=f"Jours Q < {s1:.2f} m³/s  (30 % de la médiane {med:.2f} m³/s)")
            ax.bar(all_yrs, v05, color=DKRED, alpha=0.85, width=0.75,
                  label=f"Jours Q < {s05:.2f} m³/s — critique (15 % de la médiane)")
            ax.set_ylabel("Jours / an", fontsize=10)
            ax.set_xlabel("Année", fontsize=10)
            ax.set_title(f"{nom} — Débits d'étiage : jours sous seuils\n"
                        f"{all_yrs[0]}–{all_yrs[-1]} — seuils exprimés en % de la "
                        f"médiane des débits journaliers (base influencée)",
                        fontsize=11, fontweight="bold")
            leg = ax.legend(fontsize=8, loc="upper right"); style_legend(leg)
            ax.grid(True, alpha=0.3)
            _annees_entieres(ax)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim2_Jours_Etiage.png"))

        summer_q = dq[dq["Month"].isin([7, 8, 9])].groupby("Year")["Q"].mean()
        if len(summer_q) >= 2:
            yrs3 = summer_q.index.values; sq3 = summer_q.values
            fig, ax = plt.subplots(figsize=(10, 4.6))
            ax.set_facecolor("#f8f9fa")
            cols = [DKRED if v < s1 else (RED if v < 2*s1 else BLUE) for v in sq3]
            ax.bar(yrs3, sq3, color=cols, alpha=0.75, width=0.75,
                  label="Débit moyen estival")
            ax.axhline(s1, color=DKRED, lw=1.5, ls="--",
                      label=f"Seuil étiage {s1:.2f} m³/s (30 % médiane)")
            ax.set_ylabel("Débit moyen (m³/s)", fontsize=10)
            ax.set_xlabel("Année", fontsize=10)
            ax.set_title(f"{nom} — Débit moyen estival (juillet–septembre)\n"
                        f"{int(yrs3.min())}–{int(yrs3.max())} — rouge foncé sous le seuil "
                        f"d'étiage, rouge clair sous 2× ce seuil, bleu au-delà",
                        fontsize=11, fontweight="bold")
            leg = ax.legend(fontsize=8.5, loc="best"); style_legend(leg)
            ax.grid(True, alpha=0.3)
            _annees_entieres(ax)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim3_Debit_Estival.png"))

    # ---- Clim4 — Température de l'eau, comparaison inter-annuelle ----
    de = daily_eau.copy()
    de["date_dt"] = pd.to_datetime(de["date"])
    de["Year"] = de["date_dt"].dt.year
    teau_moy = de.groupby("Year")["T_eau_moy"].mean()
    s_chr, s_aig = contexte["seuil_chr"], contexte["seuil_aigu"]
    seuils = sorted({18, 21, s_chr, s_aig})
    if len(teau_moy) >= 1:
        years = sorted(teau_moy.index)
        cats = ["T° moy (°C)"] + [f"Jours >{s}°C" for s in seuils]
        palette = [BLUE, RED, AMBER, DKRED, GREEN, PURPLE]
        fig, ax = plt.subplots(figsize=(10.5, 5.0))
        ax.set_facecolor("#f8f9fa")
        x = np.arange(len(cats))
        width = 0.8 / max(len(years), 1)
        for i, yr in enumerate(years):
            sub = de[de["Year"] == yr]
            data = [round(float(teau_moy.get(yr, 0)), 2)]
            for s in seuils:
                data.append(int((sub["T_eau_max"] > s).sum()))
            ax.bar(x + i*width - 0.4 + width/2, data, width=width,
                  color=palette[i % len(palette)], alpha=0.8, label=str(int(yr)))
        ax.set_xticks(x); ax.set_xticklabels(cats, rotation=15, ha="right", fontsize=9)
        ax.set_ylabel("Valeur", fontsize=10)
        ax.set_title(f"{nom} — Température de l'eau : comparaison inter-annuelle\n"
                    f"Seuils {contexte['label']} (T_eau_max brute, non normalisée)",
                    fontsize=11, fontweight="bold")
        leg = ax.legend(fontsize=8, loc="best", ncol=min(len(years), 4)); style_legend(leg)
        ax.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        figs.append(_clim_fin(fig, output_dir, "Clim4_Temperature_Eau.png"))

    # ---- Clim6 (bonus) — Étiage vs précipitations : les années sèches se
    # traduisent-elles en étiages plus sévères sur cette station ? ----
    if annual_delta is not None and rr_annual is not None and days_lt1 is not None:
        yrs_communes = sorted(set(rr_annual.index) & set(days_lt1.index))
        if len(yrs_communes) >= 4:
            x_rr = [rr_annual[y] for y in yrs_communes]
            y_et = [int(days_lt1.get(y, 0)) for y in yrs_communes]
            fig, ax = plt.subplots(figsize=(8.5, 5.2))
            ax.set_facecolor("#f8f9fa")
            sc = ax.scatter(x_rr, y_et, c=yrs_communes, cmap="viridis", s=90,
                           edgecolors="white", zorder=3)
            for xi, yi, yr in zip(x_rr, y_et, yrs_communes):
                ax.annotate(str(int(yr)), (xi, yi), fontsize=7.5, ha="center",
                           va="bottom", xytext=(0, 4), textcoords="offset points",
                           color="#555555")
            if len(x_rr) >= 3:
                sl = np.polyfit(x_rr, y_et, 1)
                xs = np.linspace(min(x_rr), max(x_rr), 50)
                ax.plot(xs, np.polyval(sl, xs), color=DKRED, lw=1.8, ls="--",
                       alpha=0.7, label="Tendance linéaire", zorder=2)
                leg = ax.legend(fontsize=8.5, loc="best"); style_legend(leg)
            ax.set_xlabel("Précipitations annuelles (mm)", fontsize=10)
            ax.set_ylabel(f"Jours d'étiage (Q < {s1:.2f} m³/s)", fontsize=10)
            ax.set_title(f"{nom} — Précipitations et sévérité de l'étiage\n"
                        f"Les années les plus sèches se traduisent-elles par des "
                        f"étiages plus marqués sur cette station ? (bonus)",
                        fontsize=11, fontweight="bold")
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            figs.append(_clim_fin(fig, output_dir, "Clim6_Precip_vs_Etiage.png"))

    print(f"  → {len(figs)} figure(s) climatique(s) produite(s)")
    return figs
