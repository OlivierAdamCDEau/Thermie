"""
figures.py — Restitution graphique matplotlib (package thermie_debits).

Chaque fonction fig_* construit une figure matplotlib et RETOURNE l'objet
Figure (pour affichage Streamlit via st.pyplot). Si un chemin `output_dir`
est fourni, la figure est aussi sauvegardée sur disque (mode CLI).

La bascule sélective vers Plotly (2-3 figures interactives) est prévue en
étape ultérieure ; l'interface (retour d'objet) reste identique.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats

from .core import _pnda
from .print_style import enforce_min_fontsize, style_legend


def _locator_dates_adaptatif(ax, dates):
    """
    Espace les repères de l'axe des dates selon l'étendue réelle de la
    période affichée — un repère par mois devient illisible au-delà de
    quelques années (c'était le cas signalé : des dizaines d'étiquettes
    chevauchées sur une chronique pluriannuelle).
    """
    dates = pd.to_datetime(pd.Series(dates)).dropna()
    if dates.empty:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        return
    span = (dates.max() - dates.min()).days
    if span <= 400:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    elif span <= 900:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    elif span <= 2200:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _finalise(fig, output_dir, filename):
    """Retourne la figure telle qu'autrice (proportions d'écran inchangées).
    Le plancher de lisibilité à l'impression n'est plus appliqué ici — il est
    calculé à la demande, uniquement sur la copie téléchargée ou exportée en
    CLI (voir print_style.make_print_ready), pour ne pas gonfler l'affichage
    à l'écran alors que l'utilisateur n'imprime pas forcément la figure."""
    if output_dir:
        from .print_style import make_print_ready
        fig_print = make_print_ready(fig)
        fig_print.savefig(f"{output_dir}{filename}", dpi=150, bbox_inches="tight")
        print(f"✅ {filename}")
    return fig


def fig_chronique(df, nom, output_dir, periode=None):
    from .core import inserer_lacunes
    # Couper la courbe de T° eau (Tmh) aux lacunes de mesure pour ne pas
    # relier des points de part et d'autre d'un trou (point 2 des retours).
    # Si la normalisation a été calculée, on trace aussi l'eau compensée pour
    # que l'écart entre observé et « année standard » soit lisible d'un coup
    # d'œil (c'est cet écart qui matérialise l'anomalie climatique de la période).
    cols_coupe = ["Tmh"] + (["Tmh_norm"] if "Tmh_norm" in df.columns else [])
    df = inserer_lacunes(df, col_date="date_dt", cols_valeurs=cols_coupe,
                         seuil_pas=3)
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    ax.set_facecolor("#f8f9fa")
    ax.fill_between(df["date_dt"], df["T_normale"], df["T_air"],
                    where=df["T_air"] >= df["T_normale"],
                    alpha=0.25, color="#e74c3c", label="Excédent thermique air")
    ax.fill_between(df["date_dt"], df["T_normale"], df["T_air"],
                    where=df["T_air"] < df["T_normale"],
                    alpha=0.25, color="#3498db", label="Déficit thermique air")
    ax.plot(df["date_dt"], df["T_normale"], color="#95a5a6", lw=1.5, ls="--",
            label="Normale 1991–2020 (TMm)")
    ax.plot(df["date_dt"], df["T_air"], color="#e67e22", lw=1.2, alpha=0.8,
            label="T air mesurée")
    ax.plot(df["date_dt"], df["Tmh"], color="#2980b9", lw=2.5,
            label="Tmh — eau BRUTE (moy. mobile 7 j)")
    if "Tmh_norm" in df.columns and df["Tmh_norm"].notna().any():
        ax.plot(df["date_dt"], df["Tmh_norm"], color="#117A65", lw=2.0,
                ls="-.", alpha=0.95,
                label="Tmh — eau COMPENSÉE (année standard)")
        ax.fill_between(df["date_dt"], df["Tmh"], df["Tmh_norm"],
                        color="#16A085", alpha=0.13, zorder=0,
                        label="Écart brut ↔ compensé")
    ax.set_xlabel("Date", fontsize=11); ax.set_ylabel("Température (°C)", fontsize=11)
    ax.set_title(f"{nom} — Chronique thermique\nNormales 1991–2020, T air et Tmh",
                 fontsize=13, fontweight="bold", pad=15)
    leg = ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.24),
                    ncol=3, frameon=True)
    style_legend(leg)
    ax.grid(True, alpha=0.3)
    _locator_dates_adaptatif(ax, df["date_dt"])
    if periode:
        ax.set_xlim(periode[0], periode[1])
    plt.xticks(rotation=30)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig0_Chronique.png")


# ============================================================
# ÉTAPE 1 — SENSIBILITÉ (note §2.4)
# ============================================================


def fig_sensibilite(res, nom, output_dir):
    from .print_style import wrap_rows, apply_row_heights, table_fontsize, col_width_chars
    df_ete = res["df_ete"]
    x, y = df_ete["T_air"].values, df_ete["T_eau_moy"].values
    slope, intercept, r2 = res["m"], res["intercept"], res["r2"]

    FIG_W = 11.0
    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 6.0))
    fig.patch.set_facecolor("white")
    ax1 = axes[0]; ax1.set_facecolor("#f8f9fa")
    all_vals = np.concatenate([x, y])
    pad = (all_vals.max() - all_vals.min()) * 0.07
    ax_min, ax_max = all_vals.min() - pad, all_vals.max() + pad
    ax1.set_xlim(ax_min, ax_max); ax1.set_ylim(ax_min, ax_max)
    ax1.set_aspect("equal", adjustable="box")
    ref_x = np.array([ax_min, ax_max])
    ax1.plot(ref_x, ref_x, color="#bdc3c7", lw=1.5, ls=":",
             label="Référence pente 1 (T_eau = T_air)", zorder=1)
    ax1.scatter(x, y, c="#2980b9", alpha=0.7, edgecolors="white", s=80, zorder=3)
    ax1.plot(ref_x, slope * ref_x + intercept, color="#e74c3c", lw=2.5, zorder=4,
             label=f"Régression : y = {slope:.3f}x + {intercept:.2f}")
    ax1.set_xlabel("T air (°C)", fontsize=11); ax1.set_ylabel("T eau moy (°C)", fontsize=11)
    ax1.set_title("Corrélation T air / T eau — Juin–Sept\n(axes à même échelle)",
                  fontsize=11, fontweight="bold")
    leg = ax1.legend(fontsize=9, loc="upper left")
    style_legend(leg)
    ax1.grid(True, alpha=0.3)
    textstr = (f"m = {slope:.3f}   |   R² = {r2:.3f}\n"
               f"ρ_Spearman = {res['r_spearman']:.4f}\n"
               f"Robustesse |ρ−r| = {res['robustesse']:.4f}\n"
               f"p (régr.) = {res['p_reg']:.5f}\n{res['sens_cat']}")
    ax1.text(0.98, 0.03, textstr, transform=ax1.transAxes, fontsize=9,
             va="bottom", ha="right",
             bbox=dict(boxstyle="round", facecolor="#ecf0f1", alpha=0.90))

    ax2 = axes[1]; ax2.axis("off")
    rows = [
        ["Nb jours analysés (juin–sept)", str(res["n"])],
        ["Test de normalité", "Shapiro-Wilk"],
        ["p-value T_air", f'{res["p_x"]:.4f} — {"Normale" if res["p_x"]>0.05 else "Non-normale"}'],
        ["p-value T_eau", f'{res["p_y"]:.4f} — {"Normale" if res["p_y"]>0.05 else "Non-normale"}'],
        ["Test principal retenu", res["test_used"]],
        ["── RÉGRESSION LINÉAIRE ──", ""],
        ["Pente m", f'{slope:.4f}'],
        ["Intercept", f'{intercept:.4f}'],
        ["p-value (régression)", f'{res["p_reg"]:.5f}'],
        ["── CORRÉLATIONS ──", ""],
        ["r de Pearson", f'{res["r_pearson"]:.4f}  (p={res["p_pearson"]:.5f})'],
        ["ρ de Spearman", f'{res["r_spearman"]:.4f}  (p={res["p_spearman"]:.5f})'],
        ["── INDICES ──", ""],
        ["R² — Variance expliquée", f'{r2:.4f}  →  {res["r2_cat"]}'],
        ["Indice de robustesse |ρ−r|", f'{res["robustesse"]:.4f}  →  {res["rob_cat"]}'],
        ["── SYNTHÈSE ──", ""],
        ["Catégorie de sensibilité", res["sens_cat"]],
    ]
    section_rows = {5, 9, 12, 15}
    FS_ECRAN = 10.0                     # police confortable à l'écran
    # ax2 n'occupe que la moitié de la figure (1x2, panneaux égaux) — le
    # budget de caractères doit se baser sur cette largeur réelle, pas sur
    # FIG_W entier (cause du débordement précédemment observé).
    AX2_FRAC = 0.5 * 0.92                # 0.92 = marge de sécurité (tight_layout)
    ax2_width_in = FIG_W * AX2_FRAC
    fs_impr = table_fontsize(FIG_W)      # police anticipée pour l'impression
    col_chars = [col_width_chars(0.5, ax2_width_in, fs_impr),
                col_width_chars(0.5, ax2_width_in, fs_impr)]
    wrapped, counts = wrap_rows(rows, col_chars=col_chars)
    tbl = ax2.table(cellText=wrapped, colLabels=["Paramètre", "Valeur"],
                    cellLoc="left", loc="center", bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False); tbl.set_fontsize(FS_ECRAN)
    apply_row_heights(tbl, counts)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor("#bdc3c7")
        if row == 0:
            cell.set_facecolor("#2c3e50"); cell.set_text_props(color="white", fontweight="bold")
        elif (row - 1) in section_rows:
            cell.set_facecolor("#d6e4f0"); cell.set_text_props(color="#1a5276", fontweight="bold")
        elif (row - 1) == 13:
            cell.set_facecolor("#e8f4f8"); cell.set_text_props(color="#154360")
        elif (row - 1) == 14:
            cell.set_facecolor("#eafaf1"); cell.set_text_props(color="#1e8449")
        elif (row - 1) == 16:
            cell.set_facecolor("#fef9e7")
        elif row % 2 == 0:
            cell.set_facecolor("#f5f5f5")
    ax2.set_title("Résultats — Analyse de sensibilité", fontsize=11, fontweight="bold", pad=15)
    plt.suptitle(f"{nom} — Sensibilité thermique", fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig1_Sensibilite.png")


# ============================================================
# ÉTAPE 2 — VULNÉRABILITÉ (note §2.5)
# ============================================================


def fig_vulnerabilite(vul, contexte, nom, output_dir, periode=None):
    """
    Vulnérabilité chronique et aiguë (juin-septembre), une courbe par année
    plutôt qu'une chronique continue — même code couleur par année que la
    figure fraie-croissance, pour une lecture cohérente entre les deux
    onglets. `periode`, si fourni, filtre les ANNÉES affichées (l'axe des
    abscisses n'est plus une chronologie réelle mais un calendrier
    saisonnier juin-septembre commun à toutes les années).
    """
    from .core import inserer_lacunes
    df_e = vul["df_ete"].copy()
    df_e["date_dt"] = pd.to_datetime(df_e["date_dt"])
    df_e["Year"] = df_e["date_dt"].dt.year
    annees = sorted(df_e["Year"].unique())
    if periode:
        y0, y1 = periode[0].year, periode[1].year
        annees = [a for a in annees if y0 <= a <= y1] or annees

    fig, axes = plt.subplots(2, 1, figsize=(9.5, 8.2), sharex=True)
    fig.patch.set_facecolor("white")
    ax1, ax2 = axes[0], axes[1]
    ax1.set_facecolor("#f8f9fa"); ax2.set_facecolor("#f8f9fa")

    x0_min = x1_max = None
    for annee in annees:
        sub = df_e[df_e["Year"] == annee].sort_values("date_dt")
        if len(sub) < 2:
            continue
        sub = inserer_lacunes(sub, col_date="date_dt",
                              cols_valeurs=["Tmh_norm", "Tmax_norm"], seuil_pas=3)
        synth = sub["date_dt"].apply(lambda d: pd.Timestamp(2000, d.month, d.day)
                                     if pd.notna(d) else pd.NaT)
        col = _couleur_annee(annee)
        ax1.plot(synth, sub["Tmh_norm"], color=col, lw=1.8, alpha=0.88, label=str(annee))
        ax2.plot(synth, sub["Tmax_norm"], color=col, lw=1.8, alpha=0.88, label=str(annee))
        vs = synth.dropna()
        if len(vs):
            x0_min = vs.min() if x0_min is None else min(x0_min, vs.min())
            x1_max = vs.max() if x1_max is None else max(x1_max, vs.max())

    ax1.axhline(vul["seuil_chr"], color="#e67e22", lw=2, ls="--",
               label=f"Seuil de stress {vul['seuil_chr']}°C")
    ax1.set_ylabel("Température (°C)", fontsize=11)
    ax1.set_title(f"Vulnérabilité Chronique — Tmh normalisée (juin–sept)\n"
                 f"Stress systémique · [{contexte['label']}] · {vul['pct_chr']:.1f}% de dépassement",
                 fontsize=11, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax1.tick_params(axis="x", labelbottom=True, labelrotation=30)

    ax2.axhline(vul["seuil_aigu"], color="#e74c3c", lw=2, ls="--",
               label=f"Seuil de létalité {vul['seuil_aigu']}°C")
    ax2.set_xlabel("Date (calendrier saisonnier)", fontsize=11)
    ax2.set_ylabel("Température (°C)", fontsize=11)
    ax2.set_title(f"Vulnérabilité Aiguë — Tmax normalisée (juin–sept)\n"
                 f"Létalité systémique · [{contexte['label']}] · {vul['n_aigu']} j de dépassement",
                 fontsize=11, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    if x0_min is not None:
        pad = (x1_max - x0_min) * 0.02
        ax2.set_xlim(x0_min - pad, x1_max + pad)
    plt.setp(ax1.get_xticklabels(), rotation=30)
    plt.setp(ax2.get_xticklabels(), rotation=30)
    # Légende unique pour toute la figure (une entrée par année, partagée
    # entre les deux panneaux), sous le second panneau.
    handles, labels = ax2.get_legend_handles_labels()
    h1, l1 = ax1.get_legend_handles_labels()
    for h, l in zip(h1, l1):
        if l not in labels:
            handles.append(h); labels.append(l)
    leg = fig.legend(handles, labels, fontsize=8, loc="upper center",
                     bbox_to_anchor=(0.5, 0.02), ncol=min(len(annees) + 2, 8),
                     title="Année", title_fontsize=8.5)
    style_legend(leg)
    plt.suptitle(f"{nom} — Vulnérabilité thermique\n{contexte['label']}",
                 fontsize=13, fontweight="bold", y=1.03)
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    return _finalise(fig, output_dir, "Fig2_Vulnerabilite.png")


# ============================================================
# ÉTAPE 3 — SGVT (note §2.6) — information d'appoint
# ============================================================


NOMS_PHASE = {"prefrai": "Pré-frai", "ponte": "Ponte", "incubation": "Incubation"}

# Palette qualitative déterministe par ANNÉE CIVILE (cycle sur 10 teintes) :
# une année donnée porte toujours la même couleur, y compris d'une figure à
# l'autre (fraie-croissance et vulnérabilité partagent ce code couleur, à la
# demande d'une lecture cohérente entre les deux onglets).
_PALETTE_ANNEES = plt.get_cmap("tab10").colors


def _couleur_annee(annee):
    return _PALETTE_ANNEES[int(annee) % 10]


def _mois_debut_saison(phases):
    """Premier mois de la première phase (pré-frai) — sert de point de
    bascule pour construire un calendrier synthétique sur lequel superposer
    plusieurs campagnes, y compris celles à cheval sur le nouvel an."""
    for ph in phases:
        if ph.get("mois"):
            return ph["mois"][0]
    return 1


def _synth_date(date, mois_debut):
    """Date synthétique (année de référence 2000/2001) permettant de
    superposer des campagnes réelles d'années différentes sur un même axe :
    les mois postérieurs au début de la saison restent en 2000, ceux
    antérieurs (fin d'une saison à cheval sur le nouvel an, ex. truite
    janvier-mars) basculent en 2001 pour rester après dans la chronologie."""
    yr = 2000 if date.month >= mois_debut else 2001
    try:
        return pd.Timestamp(year=yr, month=date.month, day=date.day)
    except ValueError:
        return pd.Timestamp(year=yr, month=date.month, day=28)


def fig_fraie_croissance(fraie_res, contexte, nom, output_dir, periode=None):
    """
    Vulnérabilité fraie-croissance, par espèce repère et par PHASE.
    Quand plusieurs années sont disponibles, chaque campagne (occurrence
    annuelle de la fenêtre de reproduction) est superposée sur un même axe —
    une couleur par année — plutôt que juxtaposée en petits multiples : les
    campagnes restent directement comparables sans multiplier les panneaux
    (et sans risque de chevauchement de titres lorsque les années sont
    nombreuses). `periode`, si fourni, filtre les CAMPAGNES affichées par
    année (l'axe n'étant plus une chronologie réelle mais un calendrier
    saisonnier commun à toutes les campagnes).
    """
    if not fraie_res:
        return None
    sous = [s for s in fraie_res.get("sous_indicateurs", []) if s.get("evalue")]
    if not sous:
        return None

    from .core import segments_valides

    n = len(sous)
    fig, axes = plt.subplots(n, 1, figsize=(9.5, 5.9 * n), squeeze=False)
    fig.patch.set_facecolor("white")

    for i, s in enumerate(sous):
        ax = axes[i][0]
        ax.set_facecolor("#f8f9fa")
        sub = s["sub"].sort_values("date_dt").reset_index(drop=True)
        phases = s["phases"]
        mois_debut = _mois_debut_saison(phases)

        segs = segments_valides(sub["date_dt"], sub["Tmh_norm_fraie"], seuil_pas=3)
        campagnes = []
        for dates_seg, _ in segs:
            if len(dates_seg) == 0:
                continue
            d0, d1 = pd.Timestamp(dates_seg.min()), pd.Timestamp(dates_seg.max())
            camp = sub[(sub["date_dt"] >= d0) & (sub["date_dt"] <= d1)]
            if len(camp) >= 2:
                campagnes.append(camp)
        if not campagnes:
            campagnes = [sub]
        if periode:
            y0, y1 = periode[0].year, periode[1].year
            filtrees = [c for c in campagnes
                       if y0 <= int(c["date_dt"].min().year) <= y1 or
                          y0 <= int(c["date_dt"].max().year) <= y1]
            campagnes = filtrees or campagnes
        multi = len(campagnes) > 1

        # Bandes de phase — tracées une seule fois sur le calendrier
        # synthétique (elles sont invariantes d'une année sur l'autre).
        synth_axis = pd.date_range("2000-01-01", "2001-12-31", freq="D")
        deja_leg = set()
        for ph in phases:
            if not ph.get("n"):
                continue
            msk = synth_axis.month.isin(ph["mois"])
            if not msk.any():
                continue
            o0, o1 = ph["opt"]; e0, e1 = ph["elargie"]
            lab_o = "Optimum de la phase" if "o" not in deja_leg else None
            lab_e = "Tolérance élargie (non létale)" if "e" not in deja_leg else None
            lab_l = "Seuil létal / échec reproducteur" if "l" not in deja_leg else None
            deja_leg |= {"o", "e", "l"}
            ax.fill_between(synth_axis, o0, o1, where=msk, color="#27ae60",
                            alpha=0.20, zorder=0, label=lab_o, step="mid")
            ax.fill_between(synth_axis, o1, e1, where=msk, color="#F4D03F",
                            alpha=0.22, zorder=0, label=lab_e, step="mid")
            ax.fill_between(synth_axis, e0, o0, where=msk, color="#F4D03F",
                            alpha=0.22, zorder=0, step="mid")
            ax.plot(synth_axis, np.where(msk, e1, np.nan), color="#c0392b",
                    lw=1.4, ls="--", zorder=2, label=lab_l)
            ax.plot(synth_axis, np.where(msk, e0, np.nan), color="#c0392b",
                    lw=1.0, ls=":", zorder=2)

        # Une courbe par campagne, couleur = année de début de campagne.
        x0_min, x1_max = None, None
        for camp in campagnes:
            annee = int(camp["date_dt"].min().year)
            synth_dates = camp["date_dt"].apply(lambda d: _synth_date(d, mois_debut))
            lab = (f"{annee}" if not multi else
                   (f"{annee}" if camp["date_dt"].min().year == camp["date_dt"].max().year
                    else f"{annee}-{annee+1}"))
            ax.plot(synth_dates, camp["Tmh_norm_fraie"], color=_couleur_annee(annee),
                    lw=1.8, alpha=0.88, zorder=3, label=lab if multi else "T° eau normalisée")
            x0_min = synth_dates.min() if x0_min is None else min(x0_min, synth_dates.min())
            x1_max = synth_dates.max() if x1_max is None else max(x1_max, synth_dates.max())
        if x0_min is not None:
            pad = (x1_max - x0_min) * 0.03
            ax.set_xlim(x0_min - pad, x1_max + pad)

        # Repères de phase au-dessus du cadre (ne chevauchent ni courbes ni
        # légende, celle-ci étant placée sous l'axe).
        trans = ax.get_xaxis_transform()
        for ph in phases:
            if not ph.get("n"):
                continue
            mois_syn = synth_axis[synth_axis.month.isin(ph["mois"])]
            mois_syn = mois_syn[(mois_syn >= (x0_min or mois_syn.min())) &
                                (mois_syn <= (x1_max or mois_syn.max()))]
            if len(mois_syn):
                x_mid = mois_syn[len(mois_syn) // 2]
                lab_p = NOMS_PHASE.get(ph["cle"], ph["cle"])
                ax.annotate(lab_p, xy=(x_mid, 1.04), xycoords=trans,
                            fontsize=9.5, ha="center", va="bottom",
                            fontweight="bold", color="#34495E",
                            annotation_clip=False,
                            bbox=dict(boxstyle="round,pad=0.22", facecolor="#EAECEE",
                                      edgecolor="#AEB6BF", alpha=0.95))

        limitant = (s["espece"] == fraie_res.get("espece_limitante"))
        titre = (f"{s['espece'].capitalize()}  |  optimum {s['pct_optimum']:.0f}% · "
                 f"élargie {s['pct_elargie']:.0f}% · létal {s['pct_letal']:.0f}% "
                 f"→ P={s['P']} ({s['cat']})"
                 f"{'   ★ retenu' if limitant else ''}"
                 f"{f'  —  {len(campagnes)} campagnes superposées' if multi else ''}")
        ax.set_title(titre, fontsize=10.5, fontweight="bold",
                     color="#1A5276" if limitant else "#555555", pad=44)
        ax.set_xlabel("Date (calendrier saisonnier)", fontsize=9.5, labelpad=10)
        ax.set_ylabel("T° eau normalisée (°C)", fontsize=9.5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.tick_params(axis="x", labelsize=8, labelrotation=30)
        ax.tick_params(axis="y", labelsize=8.5)
        ax.grid(True, alpha=0.3)
        ncol_leg = min(len(campagnes), 6) if multi else 2
        titre_leg = "Campagne" if multi else None
        leg = ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.32),
                        ncol=ncol_leg, frameon=True, title=titre_leg, title_fontsize=8.5)
        style_legend(leg)

        info = (f"Coeff. saisonnier air→eau : {s['m_saison']:.2f}  ·  "
                f"Sévérité moyenne (/3) : {s['sev_moy']:.2f}  ·  "
                f"Froid {'bloquant (échec)' if s.get('froid_bloquant') else 'ralentissant'}  ·  "
                f"[info] % brut hors optimum : {s.get('pct_brut', float('nan')):.0f}%")
        ax.text(0.5, 1.22, info, transform=ax.transAxes, fontsize=7.8, ha="center",
               va="bottom", color="#7F8C8D")

    plt.suptitle(f"{nom} — Vulnérabilité fraie-croissance par phase\n"
                 f"{contexte['label']}", fontsize=13, fontweight="bold", y=1.0)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig3_Fraie_Croissance.png")



def fig_synthese_tableau(sens_res, vul_res, sgvt_res, contexte, nom, output_dir):
    """Tableau de synthèse SGVT, en figure autonome (voir fig_synthese_jauge
    pour la jauge, désormais séparée pour laisser de la place aux deux)."""
    from .print_style import wrap_rows, apply_row_heights, table_fontsize, col_width_chars
    sg = sgvt_res; sr = sens_res; vr = vul_res; ctx = contexte["label"]
    FIG_W = 9.5
    fig, ax_t = plt.subplots(figsize=(FIG_W, 6.2))
    fig.patch.set_facecolor("white"); ax_t.axis("off")
    pds = sg.get("poids", {"s": 0.30, "c": 0.40, "a": 0.30, "f": None})
    def _pct(w): return f"{int(round(w*100))}%" if w else "—"
    C = {k: f"#{v}" for k, v in {"h": "2C3E50", "bs": "2471A3", "bv": "1E8449",
         "bf": "B9770D", "bg": "6C3483", "bs_bg": "EBF5FB", "bv_bg": "EAFAF1",
         "bf_bg": "FEF9E7", "bg_bg": "F4ECF7", "r2": "D6EAF8", "rob": "D5F5E3"}.items()}

    # Chaque ligne porte sa couleur (fill, txt, gras) ; `section=True` marque
    # les lignes de titre (SENSIBILITÉ, VULNÉRABILITÉ...), fusionnées
    # visuellement sur toute la largeur du tableau plutôt que cantonnées à
    # la première colonne (ce qui les forçait à un retour à la ligne serré).
    ROWS = []  # (cells[5], fill, txtcolor, bold, section)
    def SEP(txt, fill): ROWS.append(([txt, "", "", "", ""], fill, "white", True, True))
    def LINE(cells, fill=None, txt=None, bold=False): ROWS.append((cells, fill, txt, bold, False))

    SEP("── SENSIBILITÉ ──", C["bs"])
    LINE(["Pente m", f'{sr["m"]:.3f}', sr["sens_cat"], str(sg["pts_s"]), _pct(pds["s"])], C["bs_bg"], "#1a5276")
    LINE(["r Pearson / ρ Spearman", f'{sr["r_pearson"]:.4f} / {sr["r_spearman"]:.4f}', "—", "—", "—"])
    LINE(["R² — Variance expliquée", f'{sg["r2"]:.4f}  →  {sg["r2_cat"]}', "—", "—", "—"], C["r2"], "#154360")
    LINE(["Indice de robustesse |ρ−r|", f'{sg["robustesse"]:.4f}  →  {sg["rob_cat"]}', "—", "—", "—"], C["rob"], "#1e8449")
    SEP(f"── VULNÉRABILITÉ ESTIVALE · {ctx} ──", C["bv"])
    LINE([f"Tmh>{vr['seuil_chr']}°C  (stress systémique)", f'{vr["pct_chr"]:.1f}%', vr["cat_chr"], str(sg["pts_c"]), _pct(pds["c"])], C["bv_bg"], "#1a5276")
    LINE([f"Tmax>{vr['seuil_aigu']}°C  (létalité systémique)", f'{vr["n_aigu"]}j', vr["cat_aigu"], str(sg["pts_a"]), _pct(pds["a"])], C["bv_bg"], "#1a5276")
    fr = sg.get("fraie")
    if fr is not None:
        SEP("── FRAIE-CROISSANCE (hors étiage) ──", C["bf"])
        disponible = fr.get("disponible", False)
        esp = fr.get("espece_limitante", "—")
        if disponible and sg.get("pts_f") is not None:
            pct_f = fr.get("pct_fraie", float("nan"))
            pct_txt = f'{pct_f:.1f}%' if pct_f == pct_f else "n/d"
            rec = fr.get("n_annees")
            val_txt = pct_txt + (f"  ({rec} an)" if rec else "")
            LINE([f"Écart optimum · repère : {esp}", val_txt, fr.get("cat_fraie", "—"),
                  str(sg["pts_f"]), _pct(pds["f"])], C["bf_bg"], "#7e5109")
        else:
            LINE(["Composante non évaluée (chronique lacunaire)", "—",
                  "SGVT sur 3 comp.", "—", "—"], "#FCF3CF", "#7e5109")
        for s in fr.get("sous_indicateurs", []):
            if disponible and s["espece"] == esp:
                continue
            if s.get("evalue"):
                rec = f'  ({s["n_annees"]} an)' if s.get("n_annees") else ""
                LINE([f"    ↳ {s['espece']}", f'{s["pct"]:.1f}%{rec}', s["cat"],
                      f'P={s["P"]}', "—"], "#FCF3CF", "#7e5109")
            else:
                motif = s.get("motif", "phases critiques non couvertes")
                LINE([f"    ↳ {s['espece']}", str(motif),
                      "non évalué", "—", "—"], "#FADBD8", "#943126")
    SEP("── SCORE GLOBAL (appoint) ──", C["bg"])
    LINE(["SGVT" + (f' ({sg.get("composantes",3)} comp.)' if sg.get("composantes") else ""),
          f'{sg["sgvt"]:.2f} / 10', sg["interp"], "—", "—"], C["bg_bg"], "#4A235A", True)

    rows_data = [r[0] for r in ROWS]
    fs_tbl_print = table_fontsize(FIG_W)  # anticipe la police d'impression
    FS_ECRAN = 10.0
    # Colonnes normales : budget calé sur leur propre largeur. Lignes de
    # section fusionnées : le texte peut utiliser la largeur TOTALE du
    # tableau (colonnes 1 à 5 réunies), d'où un wrap bien plus généreux.
    col_chars_normal = [col_width_chars(0.34, FIG_W * 0.92, fs_tbl_print),
                        col_width_chars(0.24, FIG_W * 0.92, fs_tbl_print),
                        col_width_chars(0.26, FIG_W * 0.92, fs_tbl_print), None, None]
    col_chars_section = [col_width_chars(0.98, FIG_W * 0.92, fs_tbl_print), None, None, None, None]
    rows_wrapped, counts = [], []
    for cells, (_, _, _, _, is_section) in zip(rows_data, ROWS):
        cc = col_chars_section if is_section else col_chars_normal
        w, c = wrap_rows([cells], col_chars=cc)
        rows_wrapped.append(w[0]); counts.append(c[0])

    tbl = ax_t.table(cellText=rows_wrapped,
                     colLabels=["Paramètre", "Valeur", "Catégorie", "Pts", "Poids"],
                     colWidths=[0.34, 0.24, 0.26, 0.08, 0.08], cellLoc="left",
                     loc="center", bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False); tbl.set_fontsize(FS_ECRAN)
    apply_row_heights(tbl, counts)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor("#bdc3c7")
        if row == 0:
            cell.set_facecolor(C["h"]); cell.set_text_props(color="white", fontweight="bold")
            continue
        cells, fill, txt, bold, is_section = ROWS[row - 1]
        if fill: cell.set_facecolor(fill)
        elif row % 2 == 0: cell.set_facecolor("#f5f5f5")
        props = {}
        if txt: props["color"] = txt
        if bold: props["fontweight"] = "bold"
        if props: cell.set_text_props(**props)
        if is_section:
            # Fusion visuelle : peint les bordures internes de la même
            # couleur que le fond, plutôt que de les masquer via
            # visible_edges — qui produit un rendu triangulaire défectueux
            # sur cette version de matplotlib (vérifié : la zone colorée se
            # réduit progressivement du haut vers le bas de la ligne).
            cell.set_edgecolor(fill)
            cell.set_linewidth(1.2)
    ax_t.set_title(f"Tableau de synthèse — {ctx}", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig3a_Synthese_Tableau.png")


def fig_synthese_jauge(sgvt_res, nom, output_dir):
    """Jauge SGVT en figure autonome — davantage d'espace que dans l'ancienne
    version combinée avec le tableau, pour éviter tout chevauchement de texte."""
    sg = sgvt_res
    fig, ax_g = plt.subplots(figsize=(7.5, 6.0))
    fig.patch.set_facecolor("white")
    r_out, r_in = 1.0, 0.55
    for vmin, vmax, color, label in [(0, 2, "#27ae60", "Risque\nFaible\n[0–2]"),
                                     (2, 5, "#f39c12", "Risque\nModéré\n[2–5]"),
                                     (5, 8, "#e67e22", "Risque\nÉlevé\n[5–8]"),
                                     (8, 10, "#c0392b", "Risque\nMajeur\n[8–10]")]:
        th = np.linspace(np.pi - vmin/10*np.pi, np.pi - vmax/10*np.pi, 120)
        xo, yo = r_out*np.cos(th), r_out*np.sin(th)
        xi, yi = r_in*np.cos(th[::-1]), r_in*np.sin(th[::-1])
        ax_g.fill(np.concatenate([xo, xi]), np.concatenate([yo, yi]), color=color, alpha=0.9)
        mid = np.pi - ((vmin+vmax)/2/10)*np.pi
        ax_g.text(1.20*np.cos(mid), 1.20*np.sin(mid), label,
                  ha="center", va="center", fontsize=10.5, color=color, fontweight="bold")
    ang_n = np.pi - (sg["sgvt"]/10)*np.pi
    ax_g.annotate("", xy=(r_in*1.14*np.cos(ang_n), r_in*1.14*np.sin(ang_n)), xytext=(0, 0),
                  arrowprops=dict(arrowstyle="->", color="black", lw=3))
    ax_g.plot(0, 0, "ko", ms=9)
    ax_g.text(0, -0.14, f'SGVT = {sg["sgvt"]:.1f} / 10', ha="center", fontsize=19, fontweight="bold")
    ax_g.text(0, -0.36, sg["interp"], ha="center", fontsize=13, color=sg["color"], fontweight="bold")
    ax_g.text(0, -0.58, f'R² = {sg["r2"]:.3f}  ({sg["r2_cat"]})', ha="center", fontsize=10.5, color="#154360")
    ax_g.text(0, -0.78, f'Robustesse |ρ−r| = {sg["robustesse"]:.4f}', ha="center", fontsize=10.5, color="#1e8449")
    ax_g.text(0, -0.98, sg["rob_cat"], ha="center", fontsize=10.5, color="#1e8449")
    ax_g.set_xlim(-1.5, 1.5); ax_g.set_ylim(-1.18, 1.30)
    ax_g.set_aspect("equal", adjustable="box")
    ax_g.axis("off")
    ax_g.set_title(f"{nom} — Score Global de Vulnérabilité Thermique\n"
                   "(information d'appoint)", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig3b_Synthese_Jauge.png")


# ============================================================
# MODULE DÉBITS — INFLEXION THERMIQUE (note §2.7.2) — broken-stick + AICc
# ============================================================


def fig_qc(daily_brut, rapport, df_air, nom, output_dir, periode=None):
    """Chronique T_eau brute avec surlignage des enregistrements écartés."""
    if rapport is None:
        return
    from .core import inserer_lacunes
    b = daily_brut.merge(df_air, on="date", how="left").copy()
    b["date_dt"] = pd.to_datetime(b["date"])
    b = inserer_lacunes(b, col_date="date_dt", cols_valeurs=["T_eau_max", "T_air"],
                        seuil_pas=3)
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.set_facecolor("#f8f9fa")
    ax.plot(b["date_dt"], b["T_eau_max"], color="#95a5a6", lw=0.8, alpha=0.6, label="T_eau_max brute")
    ax.plot(b["date_dt"], b["T_air"], color="#e67e22", lw=0.8, alpha=0.5, label="T_air")
    if len(rapport) > 0:
        rr = rapport.copy(); rr["date_dt"] = pd.to_datetime(rr["date"])
        # couleur par grande famille de motif
        fam = rr["motif"].str.extract(r"^([^\—(]+)")[0].fillna("autre")
        for f, sub in rr.groupby(fam):
            ax.scatter(sub["date_dt"], sub["T_eau_max"], s=22, alpha=0.8,
                       label=f"écarté : {f.strip()[:32]}", zorder=5)
    ax.set_xlabel("Date", fontsize=11); ax.set_ylabel("Température (°C)", fontsize=11)
    ax.set_title(f"{nom} — Contrôle qualité : enregistrements écartés\n"
                 f"{len(rapport)} enreg. filtrés", fontsize=12, fontweight="bold")
    leg = ax.legend(fontsize=8.5, loc="upper right")
    style_legend(leg)
    ax.grid(True, alpha=0.3)
    _locator_dates_adaptatif(ax, b["date_dt"])
    if periode:
        ax.set_xlim(periode[0], periode[1])
    plt.xticks(rotation=30); plt.tight_layout()
    return _finalise(fig, output_dir, "FigQC_Artefacts.png")


# ============================================================
# FIG 4 — INFLEXION THERMIQUE (Q_thermie_fonc, appoint)
# ============================================================


def fig_debits_inflexion(debit_res, sens_res, contexte, nom, output_dir, q_fonc=None):
    if not debit_res: return
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.6))
    fig.patch.set_facecolor("white")
    q_thermie = debit_res["q_aicc"]; valide = debit_res["valide"]

    ax1 = axes[0]; ax1.set_facecolor("#f8f9fa")
    ax1b = ax1.twinx()
    valid_mask = ~np.isinf(debit_res["scan_aicc"])
    ax1b.plot(debit_res["scan_q"][valid_mask], debit_res["scan_aicc"][valid_mask],
              color="#bdc3c7", lw=1, alpha=0.5, zorder=1)
    ax1b.set_ylabel("AICc (segmenté)", fontsize=9, color="#999999")
    ax1b.tick_params(axis="y", colors="#999999", labelsize=8)
    ax1.plot(debit_res["q_roll"], debit_res["m_roll"], color="#2980b9", lw=2.5,
             zorder=3, label="m glissant (fenêtre Q)")
    ax1.axhline(sens_res["m"], color="#e74c3c", lw=1.5, ls="--",
                label=f"m global = {sens_res['m']:.3f}", zorder=2)
    if valide and q_fonc is not None:
        ax1.axvline(q_fonc, color="#8e44ad", lw=2.5, ls="-", zorder=5,
                    label=f"Q_thermie_fonc = {q_fonc:.3f} m³/s")
        ax1.axvspan(0, q_fonc, alpha=0.07, color="#8e44ad", zorder=0)
    ax1.set_xlabel("Débit Q (m³/s)", fontsize=11)
    ax1.set_ylabel("Sensibilité thermique m", fontsize=11)
    ax1.set_title("Sensibilité m en fonction du débit\n(fenêtre glissante · juin–sept)",
                  fontsize=11, fontweight="bold")
    leg1 = ax1.legend(fontsize=8.5, loc="upper right"); style_legend(leg1)
    ax1.grid(True, alpha=0.3)
    val_c = "#1e8449" if valide else "#e74c3c"
    val_bg = "#eafaf1" if valide else "#fce4ec"
    ax1.text(0.02, 0.98, ('OK' if valide else 'X') + f"  Rupture {'validée' if valide else 'non validée'}",
             transform=ax1.transAxes, fontsize=9, va="top", ha="left",
             fontweight="bold", color=val_c,
             bbox=dict(boxstyle="round,pad=0.4", facecolor=val_bg, edgecolor=val_c, linewidth=1.5))

    ax2 = axes[1]; ax2.set_facecolor("#f8f9fa")
    df_e = debit_res["df_ete"]
    x_a = df_e["T_air"].values; y_a = df_e["T_eau_moy"].values; q_a = df_e["Q"].values
    m_lo_m = q_a <= q_thermie; m_hi_m = q_a > q_thermie
    ax2.scatter(x_a[m_lo_m], y_a[m_lo_m], c="#e74c3c", alpha=0.7, edgecolors="white",
                s=70, zorder=3, label=f"Q ≤ Q*_stat (n={m_lo_m.sum()})")
    ax2.scatter(x_a[m_hi_m], y_a[m_hi_m], c="#27ae60", alpha=0.7, edgecolors="white",
                s=70, zorder=3, label=f"Q > Q*_stat (n={m_hi_m.sum()})")
    all_t = np.linspace(x_a.min(), x_a.max(), 100)
    if valide and m_lo_m.sum() >= 4 and m_hi_m.sum() >= 4:
        sl_lo, ic_lo, *_ = stats.linregress(x_a[m_lo_m], y_a[m_lo_m])
        sl_hi, ic_hi, *_ = stats.linregress(x_a[m_hi_m], y_a[m_hi_m])
        ax2.plot(all_t, sl_lo*all_t+ic_lo, color="#c0392b", lw=2.5, label=f"Régr. bas Q (m={sl_lo:.3f})")
        ax2.plot(all_t, sl_hi*all_t+ic_hi, color="#1e8449", lw=2.5, label=f"Régr. haut Q (m={sl_hi:.3f})")
    all_vals = np.concatenate([x_a, y_a])
    pad = (all_vals.max() - all_vals.min()) * 0.07
    ax_min, ax_max = all_vals.min() - pad, all_vals.max() + pad
    ax2.set_xlim(ax_min, ax_max); ax2.set_ylim(ax_min, ax_max)
    ax2.set_aspect("equal", adjustable="box")
    ref_x = np.array([ax_min, ax_max])
    ax2.plot(ref_x, ref_x, color="#bdc3c7", lw=1.5, ls=":", zorder=1, label="Référence pente 1")
    ax2.set_xlabel("T air (°C)", fontsize=11); ax2.set_ylabel("T eau moy (°C)", fontsize=11)
    ax2.set_title(f"T air / T eau selon le régime de débit\n(Q*_stat = {q_thermie:.3f} m³/s)",
                  fontsize=11, fontweight="bold")
    leg2 = ax2.legend(fontsize=8.5, loc="upper left"); style_legend(leg2)
    ax2.grid(True, alpha=0.3)
    plt.suptitle(f"{nom} — Débit d'inflexion thermique (Q_thermie_fonc · appoint)",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig4_Debits_Inflexion.png")


# ============================================================
# FIG 5 — DÉBIT SEUIL DE VULNÉRABILITÉ (Q_thermie_bio · PRINCIPAL)
# ============================================================


def fig_vulnerabilite_debit(debit_res, contexte, nom, output_dir, q_bio_final=None):
    if not debit_res: return
    q_vuln_chr = debit_res.get("q_vuln_chr"); q_vuln_aig = debit_res.get("q_vuln_aigu")
    q_vuln_ok = debit_res.get("q_vuln_valide", False)
    seuil_vpct = debit_res.get("seuil_vuln_pct", 5.0)
    seuil_chr = contexte["seuil_chr"]; seuil_aigu = contexte["seuil_aigu"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 8.6), sharex=True)
    fig.patch.set_facecolor("white")
    ax1.set_facecolor("#f8f9fa")
    if len(debit_res.get("vuln_roll", [])) > 0:
        ax1.plot(debit_res["q_vuln_roll"], debit_res["vuln_roll"], color="#e74c3c",
                 lw=2.5, label=f"Stress chronique glissant (Tmh_norm > {seuil_chr}°C)")
    if len(debit_res.get("vuln_cum_q", [])) > 0:
        ax1.plot(debit_res["vuln_cum_q"], debit_res["vuln_cum_pct"], color="#e74c3c",
                 lw=1.5, ls="--", alpha=0.6, label="Stress cumulé (Q ≤ Q_c)")
    ax1.axhline(seuil_vpct, color="#e67e22", lw=1.5, ls="--",
                label=f"Seuil vulnérabilité = {seuil_vpct:.0f}%")
    if q_vuln_chr is not None:
        ax1.axvline(q_vuln_chr, color="#c0392b", lw=2.5, ls="-", zorder=5,
                    label=f"Q*_vuln_stress = {q_vuln_chr:.3f} m³/s")
        ax1.axvspan(0, q_vuln_chr, alpha=0.06, color="#c0392b", zorder=0)
    # Volet stress désactivé : le signaler explicitement sur la figure
    ds = debit_res.get("diag_stress", {})
    if ds and not ds.get("stress_actif", True):
        def _f(v):
            return f"{v:+.2f}" if (v is not None and v == v) else "n.d."
        txt = (f"⚠ VOLET STRESS NON RETENU\n"
               f"stress global = {ds.get('pct_stress_global', float('nan')):.1f}% "
               f"(plancher {ds.get('plancher', 0):.0f}%)\n"
               f"corr. brute Q↔T° = {_f(ds.get('r_qt'))} "
               f"(R²={ds.get('r2_qt', float('nan')):.2f})\n"
               f"corr. partielle (à air égal) = {_f(ds.get('r_partielle'))} "
               f"(R²={ds.get('r2_partielle', float('nan')):.2f})\n"
               f"→ courbe affichée à titre de diagnostic seulement")
        ax1.text(0.98, 0.97, txt, transform=ax1.transAxes, fontsize=8.5,
                 va="top", ha="right", color="#7B241C",
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="#FDEDEC",
                           edgecolor="#C0392B", alpha=0.95))
    ax1.set_ylabel(f"% jours Tmh_norm > {seuil_chr}°C", fontsize=11)
    ax1.set_title("Vulnérabilité chronique en fonction du débit (stress systémique · Tmh normalisée)",
                  fontsize=11, fontweight="bold")
    leg1 = ax1.legend(fontsize=8.5, loc="center right"); style_legend(leg1)
    ax1.grid(True, alpha=0.3); ax1.set_ylim(bottom=0)

    ax2.set_facecolor("#f8f9fa")
    if len(debit_res.get("aigu_roll", [])) > 0:
        ax2.plot(debit_res["q_aigu_roll"], debit_res["aigu_roll"], color="#8e44ad",
                 lw=2.5, label=f"Nb jours létaux glissant (Tmax_norm > {seuil_aigu}°C)")
    if len(debit_res.get("aigu_cum_q", [])) > 0:
        ax2.plot(debit_res["aigu_cum_q"], debit_res["aigu_cum_nj"], color="#8e44ad",
                 lw=1.5, ls="--", alpha=0.6, label="Nb jours létaux cumulé (Q ≤ Q_c)")
    ax2.axhline(1, color="#e67e22", lw=1.5, ls="--", label="Seuil = 1 jour")
    if q_vuln_aig is not None:
        ax2.axvline(q_vuln_aig, color="#6C3483", lw=2.5, ls="-", zorder=5,
                    label=f"Q*_vuln_létal = {q_vuln_aig:.3f} m³/s")
        ax2.axvspan(0, q_vuln_aig, alpha=0.06, color="#6C3483", zorder=0)
    ax2.set_xlabel("Débit Q (m³/s)", fontsize=11)
    ax2.set_ylabel(f"Nb jours Tmax_norm > {seuil_aigu}°C", fontsize=11)
    ax2.set_title("Vulnérabilité aiguë en fonction du débit (létalité systémique · Tmax normalisée)",
                  fontsize=11, fontweight="bold")
    leg2 = ax2.legend(fontsize=8.5, loc="center right"); style_legend(leg2)
    ax2.grid(True, alpha=0.3); ax2.set_ylim(bottom=0)

    if q_vuln_ok and q_bio_final is not None:
        comp = []
        if q_vuln_chr is not None: comp.append(f"stress={q_vuln_chr:.3f}")
        if q_vuln_aig is not None: comp.append(f"létal={q_vuln_aig:.3f}")
        fig.text(0.5, 0.01,
                 f"▶ Q_thermie_bio (PRINCIPAL) = {q_bio_final:.3f} m³/s  "
                 f"(= max({', '.join(comp)}) × 1.10)",
                 ha="center", fontsize=11, fontweight="bold", color="#1a5276",
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="#D4E6F1",
                           edgecolor="#1a5276", linewidth=2))
    plt.suptitle(f"{nom} — Débit seuil de vulnérabilité (Q_thermie_bio · PRINCIPAL)",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    return _finalise(fig, output_dir, "Fig5_Debit_Q_thermie_bio.png")


# ============================================================
# FIG 6 — COURBE DES DÉBITS CLASSÉS + PNDA (synthèse)
# ============================================================


def fig_debits_classes(cst_res, debit_res, df_q_all, contexte, nom, output_dir, base="influencé"):
    if cst_res is None or df_q_all is None or "Q" not in df_q_all.columns:
        return
    q_bio = cst_res.get("q_thermie_bio")
    q_fonc = cst_res.get("q_thermie_fonc")
    pnd_bio = _pnda(df_q_all["Q"], q_bio)
    pnd_fonc = _pnda(df_q_all["Q"], q_fonc)

    fig, ax = plt.subplots(figsize=(10, 6.2)); ax.set_facecolor("#f8f9fa")
    q_sorted = np.sort(df_q_all["Q"].dropna().values)
    pnd_x = np.arange(1, len(q_sorted)+1)/len(q_sorted)*100
    ax.plot(pnd_x, q_sorted, color="#2980b9", lw=2.0, label=f"Débit classé ({base}, toutes années)")
    ax.fill_between(pnd_x, q_sorted, alpha=0.08, color="#2980b9")

    if q_bio is not None:
        ax.axhline(q_bio, color="#c0392b", lw=2.5, ls="-",
                   label=f"★ Q_thermie_bio = {q_bio:.3f} m³/s (PNDA={pnd_bio:.0f}%)")
        ax.plot(pnd_bio, q_bio, "s", color="#c0392b", ms=12, zorder=6,
                markeredgecolor="white", markeredgewidth=2)
    if q_fonc is not None:
        ax.axhline(q_fonc, color="#8e44ad", lw=2.0, ls=":",
                   label=f"Q_thermie_fonc = {q_fonc:.3f} m³/s (PNDA={pnd_fonc:.0f}%, appoint)")
        ax.plot(pnd_fonc, q_fonc, "o", color="#8e44ad", ms=11, zorder=6,
                markeredgecolor="white", markeredgewidth=2)

    ax.set_yscale("log")
    ax.set_xlabel("Probabilité de Non-Dépassement Annuel — PNDA (%)", fontsize=12)
    ax.set_ylabel("Débit (m³/s) — échelle log", fontsize=12)
    ax.set_title(f"{nom} — Courbe des débits classés\nDébits de référence thermique · base {base}",
                 fontsize=12, fontweight="bold")
    leg = ax.legend(fontsize=9, loc="upper left"); style_legend(leg)
    ax.grid(True, alpha=0.3, which="both")
    ax.set_xlim(0, 100)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig6_Debits_Classes_PNDA.png")


# ============================================================
# EXPORT XLSX — synthèse (mise en forme approfondie = phase 2)
# ============================================================


def fig_correlations_indicateurs(correlations, nom, output_dir, cles=None,
                                 suffixe_titre=None, filename=None):
    """
    Figure des corrélations linéaires entre indicateurs thermiques (amplitude
    nycthémérale, écart Teau-Tair) et leurs variables explicatives (débit,
    température de l'eau), avec droite de régression et R². Ne trace que les
    corrélations exploitables (n ≥ 5).
    Les panneaux à débit en abscisse sont en échelle log (la gamme des
    débits s'étend typiquement sur plusieurs ordres de grandeur).

    `cles`, si fourni, restreint l'affichage à un sous-ensemble des 4
    corrélations possibles — utilisé pour répartir la figure entre les
    chapitres du rapport (indicateurs sans débit / avec débit).
    """
    dispo = [(k, c) for k, c in correlations.items() if c.get("n", 0) >= 5]
    if cles is not None:
        dispo = [(k, c) for k, c in dispo if k in cles]
    if not dispo:
        return None
    n = len(dispo)
    ncols = 2
    nrows = (n + 1) // 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(10.5, 4.3 * nrows), squeeze=False)
    fig.patch.set_facecolor("white")
    couleurs = {"ampl_vs_debit": "#2471A3", "ampl_vs_teau": "#1E8449",
                "ecart_vs_debit": "#B9770D", "ecart_vs_teau": "#7D3C98"}
    for i, (k, c) in enumerate(dispo):
        ax = axes[i // ncols][i % ncols]
        ax.set_facecolor("#f8f9fa")
        col = couleurs.get(k, "#333333")
        x, y = np.asarray(c["x"], dtype=float), np.asarray(c["y"], dtype=float)
        log_x = c.get("log_x", False)
        if log_x:
            # Échelle log : exclut les débits nuls ou négatifs (rares, mais
            # incompatibles avec un axe logarithmique).
            m = x > 0
            x, y = x[m], y[m]
        ax.scatter(x, y, s=14, alpha=0.45, color=col, edgecolors="none", zorder=2)
        if log_x and len(x):
            xs = np.geomspace(x.min(), x.max(), 100)
        else:
            xs = np.linspace(x.min(), x.max(), 100)
        # La régression est calculée sur log(x) pour les deux corrélations à
        # débit en abscisse (voir indicateurs.py) : la pente s'applique donc
        # à log(xs), pas à xs brut — sans quoi la droite tracée ne
        # correspondrait plus au modèle réellement ajusté.
        xs_reg = np.log(xs) if log_x else xs
        ax.plot(xs, c["pente"] * xs_reg + c["ordonnee"], color=col, lw=2, zorder=3)
        if log_x:
            ax.set_xscale("log")
            ax.set_xlabel(c["xlabel"] + " — échelle log", fontsize=10)
        else:
            ax.set_xlabel(c["xlabel"], fontsize=10)
        ax.set_ylabel(c["ylabel"], fontsize=10)
        pente_lbl = "pente (/log Q)" if log_x else "pente"
        ax.set_title(f"R² = {c['r2']:.3f}  |  {pente_lbl} = {c['pente']:.3f}  (n={c['n']})",
                     fontsize=10, fontweight="bold", color=col)
        ax.grid(True, alpha=0.3, which="both" if log_x else "major")
    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")
    titre = f"{nom} — Corrélations des indicateurs thermiques"
    if suffixe_titre:
        titre += f"\n{suffixe_titre}"
    plt.suptitle(titre, fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    return _finalise(fig, output_dir, filename or "Fig_Correlations_Indicateurs.png")


def fig_relation_debit_temperature(rel, nom, output_dir):
    """
    Test préalable : le débit module-t-il la température de l'eau ?
    Panneau gauche  : nuage T°eau ~ débit, coloré par la T° de l'air (rend
                      visible la confusion des deux forçages).
    Panneau droit   : résidus partiels (à T° d'air égale) avec droite de
                      régression — c'est la démonstration du lien propre au débit.
    """
    if not rel or not rel.get("disponible"):
        return None
    d = rel["data"].dropna(subset=["Q", "Teau"])
    d = d[d["Q"] > 0]  # échelle log du panneau gauche : exclut débit nul/négatif
    if len(d) < 10:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.0))
    fig.patch.set_facecolor("white")
    couleurs_verdict = {"etablie": "#1E8449", "faible": "#B9770D",
                        "absente": "#7F8C8D", "inversee": "#C0392B"}
    col = couleurs_verdict.get(rel["verdict"], "#333333")

    # --- Panneau 1 : nuage brut coloré par la température de l'air ---
    ax1.set_facecolor("#f8f9fa")
    has_air = d["T_air"].notna().sum() > 5
    if has_air:
        sc = ax1.scatter(d["Q"], d["Teau"], c=d["T_air"], cmap="coolwarm",
                         s=18, alpha=0.75, edgecolors="none")
        cb = fig.colorbar(sc, ax=ax1, pad=0.02)
        cb.set_label("T° air (°C)", fontsize=9)
    else:
        ax1.scatter(d["Q"], d["Teau"], s=18, alpha=0.6, color="#2471A3")
    for b, style, lab in [(rel["mediane"], "--", "médiane"),
                          (rel["q25"], ":", "quart inf.")]:
        ax1.axvline(b, color="#566573", lw=1.2, ls=style, alpha=0.8,
                    label=f"{lab} ({b:.3f})")
    ax1.set_xscale("log")
    # Masque les étiquettes mineures ("2×10⁰", "3×10⁰"...) qui se chevauchent
    # sur une plage de moins d'une décennie complète — ne garde que les
    # puissances de 10 majeures, nettement espacées.
    from matplotlib.ticker import NullFormatter
    ax1.xaxis.set_minor_formatter(NullFormatter())
    ax1.set_xlabel("Débit Q (m³/s) — échelle log", fontsize=10)
    ax1.set_ylabel("Température de l'eau (°C)", fontsize=10)
    ax1.set_title("Relation observée (couleur = forçage atmosphérique)",
                  fontsize=10.5, fontweight="bold")
    leg1 = ax1.legend(fontsize=8.5); style_legend(leg1)
    ax1.grid(True, alpha=0.3, which="both")

    # --- Panneau 2 : résidus partiels (à T° d'air égale) ---
    ax2.set_facecolor("#f8f9fa")
    ligne_g = rel["lignes"][0]
    rp = ligne_g["r_partielle"]
    if has_air and np.isfinite(rp):
        m = d["T_air"].notna() & (d["Q"] > 0)
        lq = np.log(d.loc[m, "Q"].values + 0.05)
        ta = d.loc[m, "T_air"].values
        tw = d.loc[m, "Teau"].values
        deg = 3 if m.sum() >= 40 else 1
        rq = lq - np.polyval(np.polyfit(ta, lq, deg), ta)
        rt = tw - np.polyval(np.polyfit(ta, tw, deg), ta)
        ax2.scatter(rq, rt, s=18, alpha=0.6, color=col, edgecolors="none")
        if len(rq) > 5:
            sl, ic = np.polyfit(rq, rt, 1)
            xs = np.linspace(rq.min(), rq.max(), 60)
            ax2.plot(xs, sl * xs + ic, color=col, lw=2.2)
        ax2.axhline(0, color="#95a5a6", lw=0.8)
        ax2.axvline(0, color="#95a5a6", lw=0.8)
        ax2.set_xlabel("Débit — résidu à T° d'air égale (log Q)", fontsize=10)
        ax2.set_ylabel("T° eau — résidu à T° d'air égale (°C)", fontsize=10)
        ax2.set_title(f"Effet propre du débit  |  r = {rp:+.3f} "
                      f"(R² = {ligne_g['r2_partielle']:.3f})",
                      fontsize=10.5, fontweight="bold", color=col)
    else:
        ax2.text(0.5, 0.5, "Température de l'air indisponible :\n"
                           "corrélation partielle non calculable",
                 ha="center", va="center", transform=ax2.transAxes, fontsize=10,
                 color="#7F8C8D")
        ax2.set_xticks([]); ax2.set_yticks([])
    ax2.grid(True, alpha=0.3)

    plt.suptitle(f"{nom} — Le débit module-t-il la température de l'eau ?\n"
                 f"{rel['libelle']}", fontsize=12.5, fontweight="bold",
                 color=col, y=1.02)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig_Relation_Debit_Temperature.png")


def fig_matrice_diagnostic(mat, nom, output_dir):
    """
    Matrice de lecture à deux entrées : « problème thermique » × « levier
    débit ». La case correspondant à la station est mise en évidence.
    Destinée à la restitution (gestionnaires, OFB) : elle explicite ce que
    l'analyse permet — ou ne permet pas — de conclure.
    """
    if not mat:
        return None
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 2); ax.set_ylim(0, 2); ax.axis("off")

    cases = {
        (0, 1): (1, "Débit thermique\npertinent",
                 "Objectif de débit fondé\net opposable", "#C0392B"),
        (1, 1): (2, "Problème réel,\nlevier autre",
                 "Ombrage, morphologie,\nrejets, nappe", "#B9770D"),
        (0, 0): (3, "Pas d'enjeu actuel,\nlevier disponible",
                 "Surveillance\n(climat, prélèvements)", "#1E8449"),
        (1, 0): (4, "Approche thermique\npeu opérante",
                 "Autres volets HMUC\nplus pertinents", "#7F8C8D"),
    }
    for (cx, cy), (num, titre, sous, coul) in cases.items():
        actif = (num == mat["case"])
        rect = plt.Rectangle((cx, cy), 1, 1,
                             facecolor=coul if actif else "#FDFEFE",
                             edgecolor=coul, lw=3.0 if actif else 1.2,
                             alpha=0.92 if actif else 0.55, zorder=1)
        ax.add_patch(rect)
        txt_col = "white" if actif else "#5D6D7E"
        ax.text(cx + 0.5, cy + 0.66, titre, ha="center", va="center",
                fontsize=12 if actif else 10.5,
                fontweight="bold" if actif else "normal", color=txt_col, zorder=2)
        ax.text(cx + 0.5, cy + 0.34, sous, ha="center", va="center",
                fontsize=9 if actif else 8.5, color=txt_col, alpha=0.95, zorder=2)
        if actif:
            ax.text(cx + 0.08, cy + 0.9, "◀ situation de la station",
                    fontsize=8.5, color="white", fontweight="bold",
                    ha="left", va="center", zorder=3)

    # Étiquettes des axes
    ax.text(-0.06, 1.5, "Problème\nthermique\navéré", ha="right", va="center",
            fontsize=10.5, fontweight="bold", color="#34495E")
    ax.text(-0.06, 0.5, "Pas de\nproblème\nthermique", ha="right", va="center",
            fontsize=10.5, fontweight="bold", color="#34495E")
    ax.text(0.5, -0.09, "Levier débit OPÉRANT", ha="center", va="top",
            fontsize=10.5, fontweight="bold", color="#34495E")
    ax.text(1.5, -0.09, "Levier débit NON opérant", ha="center", va="top",
            fontsize=10.5, fontweight="bold", color="#34495E")

    # Bandeau de justification
    just = (f"Problème thermique : {mat['motif_probleme']}\n"
            f"Levier débit : {mat['motif_levier']}")
    ax.text(1.0, -0.30, just, ha="center", va="top", fontsize=8.8,
            color="#34495E",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F4F6F7",
                      edgecolor="#AEB6BF", alpha=0.95))

    plt.suptitle(f"{nom} — Que permet de conclure l'approche thermique ?\n"
                 f"{mat['libelle']}", fontsize=13, fontweight="bold",
                 color=mat["couleur"], y=1.0)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig_Matrice_Diagnostic.png")


def fig_indicateurs_resume(table, nom, output_dir):
    """
    Synthèse visuelle des indicateurs mensuels et annuels (onglet Indicateurs) :
    Panneau gauche — Tmax / Tmin mensuelles (brutes et compensées) ;
    Panneau droit  — amplitude nycthémérale mensuelle (moyenne ± écart-type).
    Le Tmm30j (annuel) est reporté en repère horizontal sur le panneau gauche.
    """
    if table is None or len(table) == 0:
        return None
    t = table[table["Période"] != "Année"].copy()
    if len(t) == 0:
        return None
    row_an = table[table["Période"] == "Année"]
    has_comp = "Tmax comp (°C)" in t.columns

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
    fig.patch.set_facecolor("white")
    x = np.arange(len(t))
    mois = t["Période"].tolist()

    ax1.set_facecolor("#f8f9fa")
    ax1.plot(x, t["Tmax (°C)"], "o-", color="#C0392B", lw=2, ms=5, label="Tmax brute")
    ax1.plot(x, t["Tmin (°C)"], "o-", color="#2980B9", lw=2, ms=5, label="Tmin brute")
    ax1.fill_between(x, t["Tmin (°C)"], t["Tmax (°C)"], color="#AEB6BF", alpha=0.15)
    if has_comp:
        ax1.plot(x, t["Tmax comp (°C)"], "s--", color="#C0392B", lw=1.4, ms=4,
                 alpha=0.6, label="Tmax compensée")
        ax1.plot(x, t["Tmin comp (°C)"], "s--", color="#2980B9", lw=1.4, ms=4,
                 alpha=0.6, label="Tmin compensée")
    if len(row_an) and "Tmm30j brut (°C)" in row_an.columns:
        v = row_an["Tmm30j brut (°C)"].iloc[0]
        if pd.notna(v):
            ax1.axhline(v, color="#7D3C98", lw=1.6, ls=":",
                        label=f"Tmm30j annuel brut ({v:.1f}°C)")
    ax1.set_xticks(x); ax1.set_xticklabels(mois, rotation=30, ha="right")
    ax1.set_ylabel("Température (°C)", fontsize=10)
    ax1.set_title("Tmax / Tmin mensuelles", fontsize=11, fontweight="bold")
    leg1 = ax1.legend(fontsize=7.5, loc="best"); style_legend(leg1)
    ax1.grid(True, alpha=0.3)

    ax2.set_facecolor("#f8f9fa")
    moy = t["Ampl. moy (°C)"].values
    sig = t["Ampl. σ (°C)"].fillna(0).values
    ax2.bar(x, moy, yerr=sig, color="#F5B041", edgecolor="#B9770D",
           alpha=0.85, capsize=3, error_kw=dict(lw=1.2, ecolor="#7E5109"))
    ax2.set_xticks(x); ax2.set_xticklabels(mois, rotation=30, ha="right")
    ax2.set_ylabel("Amplitude nycthémérale (°C)", fontsize=10)
    ax2.set_title("Amplitude jour/nuit mensuelle\n(moyenne ± écart-type)",
                  fontsize=11, fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="y")

    plt.suptitle(f"{nom} — Indicateurs thermiques mensuels", fontsize=13,
                 fontweight="bold", y=1.03)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig_Indicateurs_Resume.png")
