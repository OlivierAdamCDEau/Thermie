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
            label="Tmh — Moy. mobile 7j eau")
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
    Figure de restitution de la composante fraie-croissance : pour chaque
    espèce/sous-indicateur, chronique Tmh_norm sur la fenêtre de fraie avec
    bande optimale, borne de résistance et zones d'écart pénalisées.
    """
    if not fraie_res:
        return
    sous = [s for s in fraie_res["sous_indicateurs"] if "sub" in s]
    if not sous:
        print("  (fraie : aucune donnée à tracer)")
        return
    n = len(sous)
    fig, axes = plt.subplots(n, 1, figsize=(14, 5.2 * n), squeeze=False)
    fig.patch.set_facecolor("white")
    mois_noms = {1:"Jan",2:"Fév",3:"Mar",4:"Avr",5:"Mai",6:"Juin",
                 7:"Juil",8:"Aoû",9:"Sep",10:"Oct",11:"Nov",12:"Déc"}
    for i, s in enumerate(sous):
        ax = axes[i][0]; ax.set_facecolor("#f8f9fa")
        sub = s["sub"].sort_values("date_dt")
        opt_min, opt_max = s["opt"]; res = s["res"]
        limitant = (s["espece"] == fraie_res["espece_limitante"])
        # bande optimale
        ax.axhspan(opt_min, opt_max, alpha=0.15, color="#27ae60", zorder=0,
                   label=f"Optimum {opt_min}–{opt_max}°C")
        ax.axhline(res, color="#c0392b", lw=1.8, ls="--", zorder=2,
                   label=f"Résistance haute {res:.0f}°C")
        # chronique normalisée
        ax.plot(sub["date_dt"], sub["Tmh_norm_fraie"], color="#2471A3", lw=1.6,
                zorder=3, label="Tmh normalisée (m_saison)")
        # zones d'écart (chaud et froid)
        ax.fill_between(sub["date_dt"], opt_max, sub["Tmh_norm_fraie"],
                        where=sub["Tmh_norm_fraie"] > opt_max, alpha=0.30,
                        color="#e67e22", zorder=1, label="Écart chaud (pénalisé)")
        ax.fill_between(sub["date_dt"], opt_min, sub["Tmh_norm_fraie"],
                        where=sub["Tmh_norm_fraie"] < opt_min, alpha=0.30,
                        color="#5DADE2", zorder=1, label="Écart froid (pénalisé)")
        fen = " ".join(mois_noms[m] for m in s["fenetre"])
        src_m = s["m_info"]["source"]
        titre = (f"{s['espece'].capitalize()} — fenêtre {fen}"
                 f"  |  {s['pct']:.1f}% hors optimum → P={s['P']} ({s['cat']})"
                 f"{'  ★ retenu' if limitant else ''}")
        ax.set_title(titre, fontsize=11, fontweight="bold",
                     color="#1A5276" if limitant else "#555555")
        ax.set_ylabel("Tmh normalisée (°C)", fontsize=10)
        ax.legend(fontsize=8, loc="upper right", ncol=2, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        info = (f"m_saison={s['m_saison']:.3f} ({src_m})\n"
                f"pente sévérité : {s['pente']}\nsévérité moy. = {s['sev_moy']:.2f}")
        ax.text(0.01, 0.97, info, transform=ax.transAxes, fontsize=8,
                va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEF9E7",
                          edgecolor="#F9E79F"))
    plt.suptitle(f"{nom} — Vulnérabilité fraie-croissance (composante SGVT)\n"
                 f"{contexte['label']}", fontsize=13, fontweight="bold", y=1.005)
    plt.tight_layout()
    return _finalise(fig, output_dir, "Fig2bis_Fraie_Croissance.png")


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
                LINE([f"    ↳ {s['espece']}", f'central {s["n_central"]}j',
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
