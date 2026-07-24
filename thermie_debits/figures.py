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


def _finalise(fig, output_dir, filename):
    """Sauvegarde optionnelle (mode CLI) puis retourne la figure (mode app)."""
    if output_dir:
        fig.savefig(f"{output_dir}{filename}", dpi=150, bbox_inches="tight")
        print(f"✅ {filename}")
    return fig


def fig_chronique(df, nom, output_dir):
    from .core import inserer_lacunes
    # Couper la courbe de T° eau (Tmh) aux lacunes de mesure pour ne pas
    # relier des points de part et d'autre d'un trou (point 2 des retours).
    # Si la normalisation a été calculée, on trace aussi l'eau compensée pour
    # que l'écart entre observé et « année standard » soit lisible d'un coup
    # d'œil (c'est cet écart qui matérialise l'anomalie climatique de la période).
    cols_coupe = ["Tmh"] + (["Tmh_norm"] if "Tmh_norm" in df.columns else [])
    df = inserer_lacunes(df, col_date="date_dt", cols_valeurs=cols_coupe,
                         seuil_pas=3)
    fig, ax = plt.subplots(figsize=(15, 7))
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
    ax.set_xlabel("Date", fontsize=12); ax.set_ylabel("Température (°C)", fontsize=12)
    ax.set_title(f"{nom} — Chronique thermique\nNormales 1991–2020, T air et Tmh",
                 fontsize=13, fontweight="bold", pad=15)
    ax.legend(fontsize=9, framealpha=0.9, loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=30)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig0_Chronique.png")


# ============================================================
# ÉTAPE 1 — SENSIBILITÉ (note §2.4)
# ============================================================


def fig_sensibilite(res, nom, output_dir):
    df_ete = res["df_ete"]
    x, y = df_ete["T_air"].values, df_ete["T_eau_moy"].values
    slope, intercept, r2 = res["m"], res["intercept"], res["r2"]

    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
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
    ax1.legend(fontsize=8.5, loc="upper left", framealpha=0.85)
    ax1.grid(True, alpha=0.3)
    textstr = (f"m = {slope:.3f}   |   R² = {r2:.3f}\n"
               f"ρ_Spearman = {res['r_spearman']:.4f}\n"
               f"Robustesse |ρ−r| = {res['robustesse']:.4f}\n"
               f"p (régr.) = {res['p_reg']:.5f}\n{res['sens_cat']}")
    ax1.text(0.98, 0.03, textstr, transform=ax1.transAxes, fontsize=8.5,
             va="bottom", ha="right",
             bbox=dict(boxstyle="round", facecolor="#ecf0f1", alpha=0.88))

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
    tbl = ax2.table(cellText=rows, colLabels=["Paramètre", "Valeur"],
                    cellLoc="left", loc="center", bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False); tbl.set_fontsize(9.5)
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


def fig_vulnerabilite(vul, contexte, nom, output_dir):
    df_e = vul["df_ete"]
    fig, axes = plt.subplots(2, 1, figsize=(15, 12), sharex=True)
    fig.patch.set_facecolor("white")
    ax1 = axes[0]; ax1.set_facecolor("#f8f9fa")
    ax1.plot(df_e["date_dt"], df_e["Tmh"], color="#3498db", lw=2, alpha=0.5, ls="--", label="Tmh brute")
    ax1.plot(df_e["date_dt"], df_e["Tmh_norm"], color="#2980b9", lw=2.5, label="Tmh normalisée")
    ax1.axhline(vul["seuil_chr"], color="#e67e22", lw=2, ls="--",
                label=f"Seuil de stress systémique {vul['seuil_chr']}°C")
    ax1.fill_between(df_e["date_dt"], vul["seuil_chr"], df_e["Tmh_norm"],
                     where=df_e["Tmh_norm"] > vul["seuil_chr"], alpha=0.35, color="#e67e22",
                     label=f"Dépassement {vul['seuil_chr']}°C ({vul['pct_chr']:.1f}%)")
    ax1.set_ylabel("Température (°C)", fontsize=11)
    ax1.set_title(f"Vulnérabilité Chronique — Tmh normalisée (juin–sept)\nStress systémique · [{contexte['label']}]",
                  fontsize=11, fontweight="bold")
    ax1.legend(fontsize=9, loc="upper right"); ax1.grid(True, alpha=0.3)

    ax2 = axes[1]; ax2.set_facecolor("#f8f9fa")
    ax2.plot(df_e["date_dt"], df_e["T_eau_max"], color="#9b59b6", lw=2, alpha=0.5, ls="--", label="Tmax brute")
    ax2.plot(df_e["date_dt"], df_e["Tmax_norm"], color="#8e44ad", lw=2.5, label="Tmax normalisée")
    ax2.axhline(vul["seuil_aigu"], color="#e74c3c", lw=2, ls="--",
                label=f"Seuil de létalité systémique {vul['seuil_aigu']}°C")
    ax2.fill_between(df_e["date_dt"], vul["seuil_aigu"], df_e["Tmax_norm"],
                     where=df_e["Tmax_norm"] > vul["seuil_aigu"], alpha=0.4, color="#e74c3c",
                     label=f"Dépassement {vul['seuil_aigu']}°C ({vul['n_aigu']}j)")
    ax2.set_xlabel("Date", fontsize=11); ax2.set_ylabel("Température (°C)", fontsize=11)
    ax2.set_title(f"Vulnérabilité Aiguë — Tmax normalisée (juin–sept)\nLétalité systémique · [{contexte['label']}]",
                  fontsize=11, fontweight="bold")
    ax2.legend(fontsize=9, loc="upper right"); ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    plt.xticks(rotation=30)
    plt.suptitle(f"{nom} — Vulnérabilité thermique\n{contexte['label']}",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig2_Vulnerabilite.png")


# ============================================================
# ÉTAPE 3 — SGVT (note §2.6) — information d'appoint
# ============================================================


def fig_fraie_croissance(fraie_res, contexte, nom, output_dir):
    """
    Vulnérabilité fraie-croissance, par espèce repère et par PHASE.
    Les bandes colorées (optimum en vert, tolérance élargie en jaune) se
    déplacent au fil de la saison : chaque phase — pré-frai, ponte,
    incubation — a sa propre fenêtre thermique.
    """
    if not fraie_res:
        return None
    sous = [s for s in fraie_res.get("sous_indicateurs", []) if s.get("evalue")]
    if not sous:
        return None

    n = len(sous)
    fig, axes = plt.subplots(n, 1, figsize=(15, 5.2 * n), squeeze=False)
    fig.patch.set_facecolor("white")

    for i, s in enumerate(sous):
        ax = axes[i][0]
        ax.set_facecolor("#f8f9fa")
        sub = s["sub"].sort_values("date_dt")
        from .core import inserer_lacunes
        sub = inserer_lacunes(sub, col_date="date_dt",
                              cols_valeurs=["Tmh_norm_fraie"], seuil_pas=3)
        dates = sub["date_dt"].values
        mois = pd.to_datetime(sub["date_dt"]).dt.month.values

        # Bandes thermiques par phase (elles se déplacent dans le temps)
        deja_leg = set()
        for ph in s["phases"]:
            if not ph.get("n"):
                continue
            msk = np.isin(mois, ph["mois"])
            if not msk.any():
                continue
            o0, o1 = ph["opt"]; e0, e1 = ph["elargie"]
            lab_o = "Optimum de la phase" if "o" not in deja_leg else None
            lab_e = "Tolérance élargie" if "e" not in deja_leg else None
            lab_l = "Seuil de létalité / échec" if "l" not in deja_leg else None
            deja_leg |= {"o", "e", "l"}
            ax.fill_between(dates, o0, o1, where=msk, color="#27ae60",
                            alpha=0.20, zorder=0, label=lab_o, step="mid")
            ax.fill_between(dates, o1, e1, where=msk, color="#F4D03F",
                            alpha=0.22, zorder=0, label=lab_e, step="mid")
            ax.fill_between(dates, e0, o0, where=msk, color="#F4D03F",
                            alpha=0.22, zorder=0, step="mid")
            ax.plot(dates, np.where(msk, e1, np.nan), color="#c0392b",
                    lw=1.6, ls="--", zorder=2, label=lab_l)
            ax.plot(dates, np.where(msk, e0, np.nan), color="#c0392b",
                    lw=1.2, ls=":", zorder=2)

        ax.plot(dates, sub["Tmh_norm_fraie"], color="#1A5276", lw=1.7,
                zorder=3, label="T° eau normalisée")

        # Repères de phases en haut du panneau
        ymax = np.nanmax(sub["Tmh_norm_fraie"].values)
        for ph in s["phases"]:
            if not ph.get("n"):
                continue
            msk = np.isin(mois, ph["mois"])
            if msk.any():
                idx = np.where(msk)[0]
                x_mid = dates[idx[len(idx) // 2]]
                ax.annotate(ph["cle"], xy=(x_mid, ymax), fontsize=7.5,
                            ha="center", va="bottom", color="#566573",
                            annotation_clip=True)

        limitant = (s["espece"] == fraie_res.get("espece_limitante"))
        titre = (f"{s['espece'].capitalize()}  |  optimum {s['pct_optimum']:.0f}% · "
                 f"élargie {s['pct_elargie']:.0f}% · létal {s['pct_letal']:.0f}% "
                 f"→ P={s['P']} ({s['cat']})"
                 f"{'   ★ retenu' if limitant else ''}")
        ax.set_title(titre, fontsize=10.5, fontweight="bold",
                     color="#1A5276" if limitant else "#555555")
        ax.set_ylabel("T° eau normalisée (°C)", fontsize=10)
        ax.legend(fontsize=8, loc="upper left", ncol=4, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

        info = (f"m_saison = {s['m_saison']:.3f}\n"
                f"sévérité moyenne = {s['sev_moy']:.2f}\n"
                f"[info] brut hors optimum = {s.get('pct_brut', float('nan')):.0f}%\n"
                f"froid {'bloquant' if s.get('froid_bloquant') else 'ralentissant'}")
        ax.text(0.005, 0.03, info, transform=ax.transAxes, fontsize=7.5,
                va="bottom", ha="left", color="#34495E",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FDFEFE",
                          edgecolor="#AEB6BF", alpha=0.9))

    plt.suptitle(f"{nom} — Vulnérabilité fraie-croissance par phase\n"
                 f"{contexte['label']}", fontsize=13, fontweight="bold", y=1.005)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig3_Fraie_Croissance.png")

def fig_synthese(sens_res, vul_res, sgvt_res, contexte, nom, output_dir):
    sg = sgvt_res; sr = sens_res; vr = vul_res; ctx = contexte["label"]
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), gridspec_kw={"width_ratios": [2.2, 1]})
    fig.patch.set_facecolor("white")
    ax_t = axes[0]; ax_t.axis("off")
    pds = sg.get("poids", {"s": 0.30, "c": 0.40, "a": 0.30, "f": None})
    def _pct(w): return f"{int(round(w*100))}%" if w else "—"
    C = {k: f"#{v}" for k, v in {"h": "2C3E50", "bs": "2471A3", "bv": "1E8449",
         "bf": "B9770D", "bg": "6C3483", "bs_bg": "EBF5FB", "bv_bg": "EAFAF1",
         "bf_bg": "FEF9E7", "bg_bg": "F4ECF7", "r2": "D6EAF8", "rob": "D5F5E3"}.items()}

    # Construction dynamique : chaque ligne porte sa propre couleur (fill, txt, gras)
    ROWS = []  # (cells[5], fill, txtcolor, bold)
    def SEP(txt, fill): ROWS.append(([txt, "", "", "", ""], fill, "white", True))
    def LINE(cells, fill=None, txt=None, bold=False): ROWS.append((cells, fill, txt, bold))

    SEP("── SENSIBILITÉ ──", C["bs"])
    LINE(["Pente m", f'{sr["m"]:.3f}', sr["sens_cat"], str(sg["pts_s"]), _pct(pds["s"])], C["bs_bg"], "#1a5276")
    LINE(["r Pearson / ρ Spearman", f'{sr["r_pearson"]:.4f} / {sr["r_spearman"]:.4f}', "—", "—", "—"])
    LINE(["R² — Variance expliquée", f'{sg["r2"]:.4f}  →  {sg["r2_cat"]}', "—", "—", "—"], C["r2"], "#154360")
    LINE(["Indice de robustesse |ρ−r|", f'{sg["robustesse"]:.4f}  →  {sg["rob_cat"]}', "—", "—", "—"], C["rob"], "#1e8449")
    SEP(f"── VULNÉRABILITÉ ESTIVALE · {ctx} ──", C["bv"])
    LINE([f"Tmh>{vr['seuil_chr']}°C  (stress systémique)", f'{vr["pct_chr"]:.1f}%', vr["cat_chr"], str(sg["pts_c"]), _pct(pds["c"])], C["bv_bg"], "#1a5276")
    LINE([f"Tmax>{vr['seuil_aigu']}°C  (létalité systémique)", f'{vr["n_aigu"]}j', vr["cat_aigu"], str(sg["pts_a"]), _pct(pds["a"])], C["bv_bg"], "#1a5276")
    # Composante fraie-croissance (affichée même si non évaluée, pour transparence)
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
        # Détail de tous les sous-indicateurs (évalués et non évalués)
        for s in fr.get("sous_indicateurs", []):
            if disponible and s["espece"] == esp:
                continue
            if s.get("evalue"):
                rec = f'  ({s["n_annees"]} an)' if s.get("n_annees") else ""
                LINE([f"    ↳ {s['espece']}", f'{s["pct"]:.1f}%{rec}', s["cat"],
                      f'P={s["P"]}', "—"], "#FCF3CF", "#7e5109")
            else:
                # Espèce non évaluable : le motif est porté par la nouvelle
                # structure à phases (les champs de l'ancien modèle à fenêtre
                # unique, comme n_central, n'existent plus à ce niveau).
                motif = s.get("motif", "phases critiques non couvertes")
                LINE([f"    ↳ {s['espece']}", str(motif)[:38],
                      "non évalué", "—", "—"], "#FADBD8", "#943126")
    SEP("── SCORE GLOBAL (appoint) ──", C["bg"])
    LINE(["SGVT" + (f' ({sg.get("composantes",3)} comp.)' if sg.get("composantes") else ""),
          f'{sg["sgvt"]:.2f} / 10', sg["interp"], "—", "—"], C["bg_bg"], "#4A235A", True)

    rows_data = [r[0] for r in ROWS]
    tbl = ax_t.table(cellText=rows_data,
                     colLabels=["Paramètre", "Valeur", "Catégorie", "Pts", "Poids"],
                     colWidths=[0.36, 0.22, 0.26, 0.08, 0.08], cellLoc="left",
                     loc="center", bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False); tbl.set_fontsize(10.5)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor("#bdc3c7")
        if row == 0:
            cell.set_facecolor(C["h"]); cell.set_text_props(color="white", fontweight="bold", fontsize=11)
            continue
        cells, fill, txt, bold = ROWS[row - 1]
        if fill: cell.set_facecolor(fill)
        elif row % 2 == 0: cell.set_facecolor("#f5f5f5")
        props = {}
        if txt: props["color"] = txt
        if bold: props["fontweight"] = "bold"
        if props: cell.set_text_props(**props)
    ax_t.set_title(f"Tableau de synthèse — {ctx}", fontsize=13, fontweight="bold", pad=15)

    ax_g = axes[1]; ax_g.axis("off")
    r_out, r_in = 1.0, 0.72
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
                  ha="center", va="center", fontsize=9, color=color, fontweight="bold")
    ang_n = np.pi - (sg["sgvt"]/10)*np.pi
    ax_g.annotate("", xy=(0.82*np.cos(ang_n), 0.82*np.sin(ang_n)), xytext=(0, 0),
                  arrowprops=dict(arrowstyle="->", color="black", lw=2.5))
    ax_g.plot(0, 0, "ko", ms=9)
    ax_g.text(0, -0.08, f'SGVT = {sg["sgvt"]:.1f} / 10', ha="center", fontsize=17, fontweight="bold")
    ax_g.text(0, -0.22, sg["interp"], ha="center", fontsize=11, color=sg["color"], fontweight="bold")
    ax_g.text(0, -0.34, f'R² = {sg["r2"]:.3f}  ({sg["r2_cat"]})', ha="center", fontsize=9, color="#154360")
    ax_g.text(0, -0.44, f'Robustesse |ρ−r| = {sg["robustesse"]:.4f}', ha="center", fontsize=9, color="#1e8449")
    ax_g.text(0, -0.53, sg["rob_cat"], ha="center", fontsize=9, color="#1e8449")
    ax_g.set_xlim(-1.5, 1.5); ax_g.set_ylim(-0.65, 1.30)
    ax_g.set_title("Score Global de\nVulnérabilité Thermique\n(information d'appoint)",
                   fontsize=12, fontweight="bold", pad=8)
    plt.suptitle(f"{nom} — Synthèse thermique\n{ctx}", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig3_Synthese_SGVT.png")


# ============================================================
# MODULE DÉBITS — INFLEXION THERMIQUE (note §2.7.2) — broken-stick + AICc
# ============================================================


def fig_qc(daily_brut, rapport, df_air, nom, output_dir):
    """Chronique T_eau brute avec surlignage des enregistrements écartés."""
    if rapport is None:
        return
    b = daily_brut.merge(df_air, on="date", how="left").copy()
    b["date_dt"] = pd.to_datetime(b["date"])
    fig, ax = plt.subplots(figsize=(15, 6))
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
    ax.set_xlabel("Date"); ax.set_ylabel("Température (°C)")
    ax.set_title(f"{nom} — Contrôle qualité : enregistrements écartés\n"
                 f"{len(rapport)} enreg. filtrés", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right"); ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30); plt.tight_layout()
    return _finalise(fig, output_dir, "FigQC_Artefacts.png")


# ============================================================
# FIG 4 — INFLEXION THERMIQUE (Q_thermie_fonc, appoint)
# ============================================================


def fig_debits_inflexion(debit_res, sens_res, contexte, nom, output_dir, q_fonc=None):
    if not debit_res: return
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
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
    ax1.legend(fontsize=8, loc="upper right"); ax1.grid(True, alpha=0.3)
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
    ax2.legend(fontsize=8, loc="upper left"); ax2.grid(True, alpha=0.3)
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

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
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
    ax1.legend(fontsize=8, loc="center right"); ax1.grid(True, alpha=0.3); ax1.set_ylim(bottom=0)

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
    ax2.legend(fontsize=8, loc="center right"); ax2.grid(True, alpha=0.3); ax2.set_ylim(bottom=0)

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

    fig, ax = plt.subplots(figsize=(12, 7)); ax.set_facecolor("#f8f9fa")
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
    ax.legend(fontsize=9, loc="upper left"); ax.grid(True, alpha=0.3, which="both")
    ax.set_xlim(0, 100)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig6_Debits_Classes_PNDA.png")


# ============================================================
# EXPORT XLSX — synthèse (mise en forme approfondie = phase 2)
# ============================================================


def fig_correlations_indicateurs(correlations, nom, output_dir):
    """
    Figure des 4 corrélations linéaires (amplitude/débit, amplitude/Teau,
    écart Teau-Tair/débit, écart Teau-Tair/Teau) avec droite de régression
    et R². Ne trace que les corrélations exploitables (n ≥ 5).
    """
    dispo = [(k, c) for k, c in correlations.items() if c.get("n", 0) >= 5]
    if not dispo:
        return None
    n = len(dispo)
    ncols = 2
    nrows = (n + 1) // 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(13, 4.6 * nrows), squeeze=False)
    fig.patch.set_facecolor("white")
    couleurs = {"ampl_vs_debit": "#2471A3", "ampl_vs_teau": "#1E8449",
                "ecart_vs_debit": "#B9770D", "ecart_vs_teau": "#7D3C98"}
    for i, (k, c) in enumerate(dispo):
        ax = axes[i // ncols][i % ncols]
        ax.set_facecolor("#f8f9fa")
        col = couleurs.get(k, "#333333")
        x, y = np.asarray(c["x"]), np.asarray(c["y"])
        ax.scatter(x, y, s=14, alpha=0.45, color=col, edgecolors="none", zorder=2)
        xs = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs, c["pente"] * xs + c["ordonnee"], color=col, lw=2, zorder=3)
        ax.set_xlabel(c["xlabel"], fontsize=10)
        ax.set_ylabel(c["ylabel"], fontsize=10)
        ax.set_title(f"R² = {c['r2']:.3f}  |  pente = {c['pente']:.3f}  (n={c['n']})",
                     fontsize=10, fontweight="bold", color=col)
        ax.grid(True, alpha=0.3)
    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")
    plt.suptitle(f"{nom} — Corrélations des indicateurs thermiques",
                 fontsize=13, fontweight="bold", y=1.005)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig_Correlations_Indicateurs.png")


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
    if len(d) < 10:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.6))
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
    ax1.set_xlabel("Débit Q (m³/s)", fontsize=10)
    ax1.set_ylabel("Température de l'eau (°C)", fontsize=10)
    ax1.set_title("Relation observée (couleur = forçage atmosphérique)",
                  fontsize=10.5, fontweight="bold")
    ax1.legend(fontsize=8); ax1.grid(True, alpha=0.3)

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
