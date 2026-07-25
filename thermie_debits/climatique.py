"""
climatique.py — Volet climatique bonus (package thermie_debits).

Contexte descriptif long terme : tendance thermique (écart aux normales),
étiages, débit estival, température d'eau inter-annuelle, précipitations.

IMPORTANT : volet purement descriptif, sur données BRUTES (contexte observé
réel, artefacts inclus) — distinct des volets thermie/débits qui appliquent
le QC. N'alimente pas les débits de référence.

Restitution en Plotly (plutôt que matplotlib) pour ce volet : les graphiques
sont interactifs (zoom, survol, export) et l'axe des années s'affiche
nativement en entiers, sans les tickmarks décimaux que produisait parfois
l'axe numérique matplotlib sur de courtes séries annuelles.

Les fonctions retournent la liste des figures Plotly produites (et exportent
un PNG statique via kaleido si output_dir est fourni, pour le mode CLI).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .io_data import charger_debit

TEMPLATE = "plotly_white"
BLUE, RED, DKRED, AMBER, GREEN, PURPLE = (
    "#378ADD", "#E24B4A", "#A32D2D", "#BA7517", "#2E8B57", "#7D3C98")


def _clim_fin(fig, output_dir, filename):
    """Export PNG optionnel (mode CLI, via kaleido) puis retourne la figure
    Plotly (mode app, affichée avec st.plotly_chart)."""
    fig.update_layout(template=TEMPLATE, font=dict(size=13),
                      margin=dict(t=70, b=50, l=60, r=30))
    if output_dir:
        try:
            fig.write_image(f"{output_dir}{filename}", scale=2, width=1000, height=460)
            print(f"✅ {filename}")
        except Exception as e:
            print(f"  ⚠️  Export PNG non disponible ({filename}) : {e}")
    return fig


def _annees_axis(fig, annees):
    """Force un axe des abscisses en années entières, sans tickmark décimal
    (le point signalé sur le graphique de tendance climatique)."""
    annees = sorted(int(a) for a in annees)
    step = 1 if len(annees) <= 15 else max(1, len(annees) // 12)
    fig.update_xaxes(tickmode="array", tickvals=annees[::step],
                     ticktext=[str(a) for a in annees[::step]],
                     tickangle=-40)


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

    # ---- Clim1 — Écart annuel à la normale 1991-2020 (graphique du haut) ----
    if "Delta_TMm" in df.columns:
        dd = df.dropna(subset=["Delta_TMm"]).copy()
        dd["Year"] = pd.to_datetime(dd["date"]).dt.year
        annual_delta = dd.groupby("Year")["Delta_TMm"].mean()
        roll10 = annual_delta.rolling(10, center=True, min_periods=3).mean()
        if len(annual_delta) >= 2:
            yrs = annual_delta.index.values.astype(int); vals = annual_delta.values
            fig = go.Figure()
            fig.add_bar(x=yrs, y=vals,
                       marker_color=[RED if v >= 0 else BLUE for v in vals],
                       opacity=0.65, name="Écart annuel",
                       hovertemplate="Année %{x}<br>Écart : %{y:+.2f} °C<extra></extra>")
            r = roll10.dropna()
            if len(r):
                fig.add_scatter(x=r.index.values.astype(int), y=r.values, mode="lines",
                               line=dict(color=AMBER, width=3),
                               name="Moyenne mobile 10 ans",
                               hovertemplate="Année %{x}<br>Moy. 10 ans : %{y:+.2f} °C<extra></extra>")
            fig.add_hline(y=0, line_dash="dash", line_color="#888888", line_width=1)
            fig.update_layout(
                title=f"Air — écart à la normale 1991–2020<br><sup>{nom} · "
                      f"{int(yrs.min())}–{int(yrs.max())} — période de référence "
                      f"utilisée pour la normalisation climatique (§2.3)</sup>",
                yaxis_title="Écart à la normale (°C)", xaxis_title="Année",
                legend=dict(orientation="h", y=1.10, x=0))
            _annees_axis(fig, yrs)
            figs.append(_clim_fin(fig, output_dir, "Clim1_Ecart_Normale.png"))

    # ---- Clim5 — Précipitations annuelles ----
    if "RR" in dfa.columns:
        rr = dfa.groupby("Year")["RR"].sum()
        rr = rr[rr > 0]
        if len(rr) >= 2:
            rr_mean = float(rr.mean())
            yrs = rr.index.values.astype(int)
            fig = go.Figure()
            fig.add_bar(x=yrs, y=rr.values,
                       marker_color=[BLUE if v >= rr_mean else RED for v in rr.values],
                       opacity=0.6, name="Précipitations annuelles",
                       hovertemplate="Année %{x}<br>%{y:.0f} mm<extra></extra>")
            fig.add_hline(y=rr_mean, line_dash="dash", line_color=AMBER, line_width=2,
                         annotation_text=f"Moyenne {rr_mean:.0f} mm",
                         annotation_position="top left")
            fig.update_layout(title=f"Précipitations annuelles (cumul)<br><sup>{nom} · "
                                    f"{int(yrs.min())}–{int(yrs.max())}</sup>",
                             yaxis_title="Cumul annuel (mm)", xaxis_title="Année")
            _annees_axis(fig, yrs)
            figs.append(_clim_fin(fig, output_dir, "Clim5_Precipitations.png"))

    # ---- Clim2 / Clim3 — Débit : étiage et débit moyen estival ----
    if fichier_debit and "Q" in df.columns:
        dq = charger_debit(fichier_debit)
        dq["date_dt"] = pd.to_datetime(dq["date"])
        dq["Year"] = dq["date_dt"].dt.year
        dq["Month"] = dq["date_dt"].dt.month
        daily = dq.set_index("date_dt")["Q"]
        med = daily.median()
        # Seuils relatifs à la médiane du débit de la station (et non des
        # valeurs absolues arbitraires) — explicité dans le titre et les
        # info-bulles, à la demande d'une lecture plus transparente.
        s1, s05 = max(1.0, round(med * 0.3, 2)), max(0.5, round(med * 0.15, 2))
        days_lt1 = (daily < s1).groupby(daily.index.year).sum()
        days_lt05 = (daily < s05).groupby(daily.index.year).sum()
        all_yrs = sorted(set(days_lt1.index) | set(days_lt05.index))
        if len(all_yrs) >= 2:
            fig = go.Figure()
            fig.add_bar(x=all_yrs, y=[int(days_lt1.get(y, 0)) for y in all_yrs],
                       marker_color=RED, opacity=0.5,
                       name=f"Jours Q < {s1:.2f} m³/s  (30 % de la médiane {med:.2f})",
                       hovertemplate="Année %{x}<br>%{y} jour(s)<extra></extra>")
            fig.add_bar(x=all_yrs, y=[int(days_lt05.get(y, 0)) for y in all_yrs],
                       marker_color=DKRED, opacity=0.85,
                       name=f"Jours Q < {s05:.2f} m³/s — critique (15 % de la médiane)",
                       hovertemplate="Année %{x}<br>%{y} jour(s)<extra></extra>")
            fig.update_layout(
                barmode="overlay",
                title=f"Débits d'étiage — jours sous seuils<br><sup>{nom} · "
                      f"{all_yrs[0]}–{all_yrs[-1]} · seuils exprimés en % de la "
                      f"médiane des débits journaliers de la station (influencé)</sup>",
                yaxis_title="Jours / an", xaxis_title="Année",
                legend=dict(orientation="h", y=1.14, x=0))
            _annees_axis(fig, all_yrs)
            figs.append(_clim_fin(fig, output_dir, "Clim2_Jours_Etiage.png"))

        summer_q = dq[dq["Month"].isin([7, 8, 9])].groupby("Year")["Q"].mean()
        if len(summer_q) >= 2:
            yrs3 = summer_q.index.values.astype(int); sq3 = summer_q.values
            fig = go.Figure()
            fig.add_bar(x=yrs3, y=sq3,
                       marker_color=[DKRED if v < s1 else (RED if v < 2*s1 else BLUE)
                                    for v in sq3], opacity=0.75,
                       name="Débit moyen estival",
                       hovertemplate="Année %{x}<br>%{y:.3f} m³/s<extra></extra>")
            fig.add_hline(y=s1, line_dash="dash", line_color=DKRED, line_width=1.5,
                         annotation_text=f"Seuil étiage {s1:.2f} m³/s (30 % médiane)",
                         annotation_position="bottom right")
            fig.update_layout(
                title=f"Débit moyen estival (juillet–septembre)<br><sup>{nom} · "
                      f"{int(yrs3.min())}–{int(yrs3.max())} · couleur : "
                      f"rouge foncé sous le seuil d'étiage, rouge clair sous 2× ce "
                      f"seuil, bleu au-delà</sup>",
                yaxis_title="Débit moyen (m³/s)", xaxis_title="Année")
            _annees_axis(fig, yrs3)
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
        fig = go.Figure()
        for i, yr in enumerate(years):
            sub = de[de["Year"] == yr]
            data = [round(float(teau_moy.get(yr, 0)), 2)]
            for s in seuils:
                data.append(int((sub["T_eau_max"] > s).sum()))
            fig.add_bar(x=cats, y=data, name=str(int(yr)),
                       marker_color=palette[i % len(palette)], opacity=0.75,
                       text=[f"{v:.1f}" if v < 10 else f"{int(v)}" for v in data],
                       textposition="outside",
                       hovertemplate="%{x}<br>%{y}<extra>" + str(int(yr)) + "</extra>")
        fig.update_layout(
            title=f"Température de l'eau — comparaison inter-annuelle<br>"
                  f"<sup>{nom} · seuils {contexte['label']} (T_eau_max brute, "
                  f"non normalisée)</sup>",
            yaxis_title="Valeur", barmode="group",
            legend=dict(orientation="h", y=1.15, x=0))
        figs.append(_clim_fin(fig, output_dir, "Clim4_Temperature_Eau.png"))

    print(f"  → {len(figs)} figure(s) climatique(s) produite(s) (Plotly, interactives)")
    return figs
