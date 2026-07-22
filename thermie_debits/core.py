"""
core.py — Cœur de calcul (package thermie_debits).

Toute la chaîne analytique de l'approche thermique (note §2.4 à §2.8) :
sensibilité, vulnérabilité, fraie-croissance, SGVT, débits de référence.

Principe : AUCUN I/O, AUCUNE variable globale. Chaque fonction reçoit ses
paramètres (dont le contexte et les constantes méthodo depuis `config`) et
retourne des objets Python. Les `print` de diagnostic sont conservés mais
contrôlés par `verbose`.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats

from .config import (PENTE_SEVERITE, FACTEUR_RESISTANCE, ROMBOUGH_DELTA,
                     FRAIE_MIN_JOURS_CENTRAL, SGVT_POIDS_4, SGVT_POIDS_3)


# ============================================================
# FONCTIONS D'INTERPRÉTATION (note §2.4 à §2.6)
# ============================================================
def interprete_r2(r2):
    if r2 < 0.10: return "Négligeable"
    if r2 < 0.30: return "Faible"
    if r2 < 0.50: return "Modérée"
    if r2 < 0.70: return "Forte"
    return "Très forte"

def interprete_robustesse(rob):
    if rob <= 0.10: return "Excellente robustesse"
    if rob <= 0.20: return "Robustesse modérée"
    return "Faible robustesse"

def interprete_sensibilite(slope):
    if slope < 0.3:  return "Résilience Élevée"
    if slope < 0.6:  return "Sensibilité Modérée"
    if slope < 0.8:  return "Sensibilité Forte"
    return "Sensibilité Critique"

def cat_chronique(pct, contexte_key="cyprinicole"):
    """Grille note §2.5 : seuil 'Faible' = 3% (salmo/interm.), 5% (cyprin.)."""
    seuil_faible = 3 if contexte_key in ("salmonicole", "intermediaire") else 5
    if pct < seuil_faible: return "Faible vulnérabilité chronique"
    if pct < 20:  return "Vulnérabilité chronique modérée"
    if pct < 50:  return "Forte vulnérabilité chronique"
    return "Vulnérabilité chronique critique"

def cat_aigue(n):
    if n == 0:    return "Absence de vulnérabilité aiguë"
    if n <= 2:    return "Vulnérabilité aiguë ponctuelle"
    if n <= 15:   return "Vulnérabilité aiguë sévère"
    return "Vulnérabilité aiguë létale"




# ============================================================
# FUSION FINALE + NORMALISATION (note §2.3, normales 1991–2020)
# ============================================================
def fusionner(daily_eau_propre, df_air, ecart_by_date, normales_lkp,
              df_debits=None):
    """
    Fusionne eau (nettoyée) + air + normales (+ débits déjà fusionnés).
    Calcule T_air_std, Tmh (moy. mobile 7j) et prépare les colonnes d'analyse.

    df_debits : DataFrame [date, Q, Q_inf, (Q_desinf)] produit par
                io_data.fusionner_debits(), ou None (mode thermie seule).
                La colonne Q y est déjà la base de calcul retenue.
    """
    df = daily_eau_propre.merge(df_air, on="date", how="inner")
    df = df.merge(ecart_by_date, on="date", how="left")
    df["day"]   = pd.to_datetime(df["date"]).dt.day
    df["month"] = pd.to_datetime(df["date"]).dt.month
    df = df.merge(normales_lkp, on=["day", "month"], how="left")
    df = df.dropna(subset=["T_eau_moy", "T_air"])
    df["T_air_std"] = df["T_air"] - df["Delta_TMm"]
    df = df.sort_values("date").reset_index(drop=True)
    df["Tmh"]     = df["T_eau_moy"].rolling(window=7, min_periods=4,
                                            center=True).mean()
    df["date_dt"] = pd.to_datetime(df["date"])

    if df_debits is not None:
        keep = [c for c in ["date", "Q", "Q_inf", "Q_desinf"] if c in df_debits.columns]
        df = df.merge(df_debits[keep], on="date", how="left")
    return df


# ============================================================
# ÉTAPE 1 — SENSIBILITÉ (note §2.4)
# ============================================================
def analyse_sensibilite(df):
    df_ete = df[df["month"].isin([6, 7, 8, 9])].dropna(subset=["T_eau_moy", "T_air"])
    if len(df_ete) < 10:
        raise ValueError(
            f"Données estivales (juin–sept.) insuffisantes pour la régression "
            f"de sensibilité : {len(df_ete)} jour(s) valide(s) après contrôle "
            f"qualité. Causes possibles : chronique trop courte, ou contrôle "
            f"qualité ayant écarté l'été (ex. sonde diagnostiquée hors d'eau). "
            f"Vérifiez les paramètres QC (seuil hors d'eau) ou la couverture "
            f"estivale de la chronique.")
    x, y = df_ete["T_air"].values, df_ete["T_eau_moy"].values

    _, p_x = stats.shapiro(x)
    _, p_y = stats.shapiro(y)
    r_pearson,  p_pearson  = stats.pearsonr(x, y)
    r_spearman, p_spearman = stats.spearmanr(x, y)
    test_used = "Pearson" if (p_x > 0.05 and p_y > 0.05) else "Spearman"
    r_main = r_pearson if test_used == "Pearson" else r_spearman
    p_main = p_pearson if test_used == "Pearson" else p_spearman

    slope, intercept, r_value, p_reg, _ = stats.linregress(x, y)
    r2 = r_value ** 2
    robustesse = abs(r_spearman - r_pearson)

    return dict(
        m=slope, intercept=intercept, r_main=r_main, p_main=p_main,
        r_pearson=r_pearson, p_pearson=p_pearson,
        r_spearman=r_spearman, p_spearman=p_spearman,
        r2=r2, p_reg=p_reg, test_used=test_used, p_x=p_x, p_y=p_y,
        sens_cat=interprete_sensibilite(slope), r2_cat=interprete_r2(r2),
        robustesse=robustesse, rob_cat=interprete_robustesse(robustesse),
        n=len(df_ete), df_ete=df_ete,
    )




# ============================================================
# ÉTAPE 2 — VULNÉRABILITÉ (note §2.5)
# ============================================================
def analyse_vulnerabilite(df, m, contexte, contexte_key="cyprinicole"):
    df["Tmh_norm"]  = df["Tmh"]       - (m * df["Delta_TMm"])
    df["Tmax_norm"] = df["T_eau_max"] - (m * df["Delta_TMm"])
    df_ete = df[df["month"].isin([6, 7, 8, 9])].copy()
    s_chr, s_aig = contexte["seuil_chr"], contexte["seuil_aigu"]
    tmh_v  = df_ete.dropna(subset=["Tmh_norm"])
    tmax_v = df_ete.dropna(subset=["Tmax_norm"])
    n_tmh, n_tmax = len(tmh_v), len(tmax_v)
    pct_chr = 100 * (tmh_v["Tmh_norm"] > s_chr).sum() / n_tmh if n_tmh else 0
    n_aigu  = int((tmax_v["Tmax_norm"] > s_aig).sum())
    return dict(df_ete=df_ete, seuil_chr=s_chr, seuil_aigu=s_aig,
                pct_chr=pct_chr, cat_chr=cat_chronique(pct_chr, contexte_key),
                n_aigu=n_aigu, cat_aigu=cat_aigue(n_aigu),
                n_total_tmh=n_tmh, n_total_tmax=n_tmax)



# ============================================================
# ÉTAPE 2bis — FRAIE-CROISSANCE (note §2.7)
# ============================================================
def cat_fraie(pct):
    """Grille de classe fraie-croissance (score /3), analogue au chronique."""
    if pct < 5:    return "Faible vulnérabilité fraie", 0
    if pct < 20:   return "Vulnérabilité fraie modérée", 1
    if pct < 50:   return "Forte vulnérabilité fraie", 2
    return "Vulnérabilité fraie critique", 3


def _m_saisonnier(df, mois, m_estival, verbose=True):
    """
    Recalcule le coefficient de couplage air-eau sur la fenêtre saisonnière
    de fraie. Garde-fous : si l'échantillon est insuffisant, le R² trop
    faible, ou la pente aberrante (hors [0, 1.2]), on se rabat sur m_estival
    avec signalement (note §2.6bis).
    """
    sub = df[df["month"].isin(mois)].dropna(subset=["T_eau_moy", "T_air"])
    if len(sub) < 20:
        if verbose:
            print(f"      ⚠️  m_saison : n={len(sub)} < 20 → repli sur m estival "
                  f"({m_estival:.3f})")
        return m_estival, dict(source="estival_repli", n=len(sub), r2=np.nan, m=m_estival)
    sl, ic, r, p, _ = stats.linregress(sub["T_air"], sub["T_eau_moy"])
    r2 = r ** 2
    if r2 < 0.30 or not (0.0 <= sl <= 1.2):
        if verbose:
            print(f"      ⚠️  m_saison={sl:.3f} (R²={r2:.2f}) non fiable "
                  f"→ repli sur m estival ({m_estival:.3f})")
        return m_estival, dict(source="estival_repli", n=len(sub), r2=r2, m=sl)
    if verbose:
        print(f"      m_saison={sl:.3f} (R²={r2:.2f}, n={len(sub)}) retenu")
    return sl, dict(source="saisonnier", n=len(sub), r2=r2, m=sl)


def _severite_fraie(tmh_norm, opt_min, opt_max, res, pente_key):
    """
    Score de sévérité journalier ∈ [0, ~3], BILATÉRAL.
    0 dans l'optimum ; croît linéairement (pente espèce) hors optimum ;
    pénalité renforcée (× FACTEUR_RESISTANCE) au-delà de la résistance haute.
    Le froid excessif (sous opt_min) comme le chaud (au-dessus opt_max) comptent.
    """
    pente = PENTE_SEVERITE.get(pente_key, 0.35)
    x = np.asarray(tmh_norm, dtype=float)
    sev = np.zeros_like(x)
    # écart au-dessus de l'optimum
    above = x > opt_max
    sev[above] = pente * (x[above] - opt_max)
    # renfort au-delà de la résistance haute
    hot = x > res
    sev[hot] += pente * FACTEUR_RESISTANCE * (x[hot] - res)
    # écart en dessous de l'optimum (bilatéral)
    below = x < opt_min
    sev[below] = pente * (opt_min - x[below])
    return np.clip(sev, 0, 3.0)


def _rombough_check(opt_min, opt_max, res, t_fraie, espece, pente_key="moderee",
                    verbose=True):
    """
    Garde-fou Rombough (1997) : pour les espèces sténothermes, la borne de
    résistance devrait tomber à ~±6°C de la T° de fraie. La règle ne s'applique
    PAS aux espèces eurythermes/tolérantes (pente 'faible' — ex. brochet), dont
    la fenêtre de tolérance est physiologiquement plus large : on ne signale
    alors rien. Pour les sténothermes, un écart marqué déclenche un avertissement
    de cohérence des bornes.
    """
    if pente_key == "faible":
        return True  # espèce tolérante : règle ±6°C non applicable
    borne_haute_attendue = t_fraie + ROMBOUGH_DELTA
    if abs(res - borne_haute_attendue) > 3.0:
        if verbose:
            print(f"      ⚠️  Rombough [{espece}] : résistance {res}°C éloignée "
                  f"de T_fraie+6={borne_haute_attendue:.0f}°C — bornes à vérifier")
        return False
    return True


def analyse_fraie_croissance(df, m_estival, contexte, contexte_key="cyprinicole",
                             verbose=True):
    """
    Calcule la composante fraie-croissance P_fraie (score /3) et ses détails.
    Pour la zone cyprinicole : deux sous-indicateurs (brochet + brème), le plus
    contraignant alimente P_fraie ; les deux sont conservés pour l'affichage.

    Retourne un dict avec :
      P_fraie (int 0-3), pct_fraie (float, sous-ind. retenu),
      sous_indicateurs (liste de dicts par espèce), espece_limitante (str).
    Si aucun paramètre fraie n'est défini, retourne None.
    """
    params = contexte.get("fraie")
    if not params:
        return None

    sous = []
    for espece, pr in params.items():
        mois = pr["fenetre"]
        mois_c = pr.get("mois_central", mois[len(mois) // 2])
        opt_min, opt_max = pr["opt"]
        res = pr["res"]
        _rombough_check(opt_min, opt_max, res, pr["T_fraie"], espece,
                        pente_key=pr["pente"], verbose=verbose)

        sub = df[df["month"].isin(mois)].dropna(subset=["Tmh", "Delta_TMm"]).copy()

        # -- Couverture du MOIS CENTRAL (cœur d'incubation) --
        sub_c = sub[sub["month"] == mois_c]
        n_central = len(sub_c)
        # récurrence : nb d'années distinctes couvrant le mois central
        annees_central = sorted(sub_c["date_dt"].dt.year.unique().tolist()) \
                         if n_central else []
        n_annees = len(annees_central)
        couvert = n_central >= FRAIE_MIN_JOURS_CENTRAL

        if not couvert:
            # Sous-indicateur NON ÉVALUÉ (chronique lacunaire sur le cœur de fraie)
            sous.append(dict(espece=espece, evalue=False, pct=np.nan, P=None, n=len(sub),
                             n_central=n_central, n_annees=n_annees,
                             cat="Non évalué (mois central lacunaire)",
                             mois_central=mois_c, opt=[opt_min, opt_max], res=res,
                             src=pr["src"], fenetre=mois, sev_moy=np.nan,
                             m_saison=np.nan, m_info=dict(source="non_calcule")))
            continue

        # m saisonnier propre à la fenêtre de cette espèce
        m_s, m_info = _m_saisonnier(df, mois, m_estival, verbose)
        sub["Tmh_norm_fraie"] = sub["Tmh"] - (m_s * sub["Delta_TMm"])
        sev = _severite_fraie(sub["Tmh_norm_fraie"].values,
                              opt_min, opt_max, res, pr["pente"])
        pct = 100 * (sev > 0).sum() / len(sev)
        sev_moy = float(np.mean(sev))
        cat, P = cat_fraie(pct)
        sous.append(dict(espece=espece, evalue=True, pct=pct, P=P, n=len(sev),
                         n_central=n_central, n_annees=n_annees, cat=cat,
                         mois_central=mois_c, m_saison=m_s, m_info=m_info,
                         opt=[opt_min, opt_max], res=res, src=pr["src"],
                         fenetre=mois, sev_moy=sev_moy, sub=sub, sev=sev,
                         pente=pr["pente"]))

    # Sous-indicateur le plus contraignant PARMI LES ÉVALUÉS (P puis pct)
    valides = [s for s in sous if s.get("evalue")]
    non_eval = [s for s in sous if not s.get("evalue")]

    if verbose:
        print(f"  Composante fraie-croissance :")
        for s in sous:
            if not s.get("evalue"):
                print(f"    {s['espece']:14s} : NON ÉVALUÉ — mois central "
                      f"({s['mois_central']}) couvert {s['n_central']}j "
                      f"< {FRAIE_MIN_JOURS_CENTRAL}j requis")

    if not valides:
        # Aucun sous-indicateur évaluable → composante fraie inopérante
        if verbose:
            print(f"    → composante fraie NON DISPONIBLE (chronique lacunaire) "
                  f"— SGVT repliera sur 3 composantes")
        return dict(P_fraie=None, pct_fraie=np.nan, sous_indicateurs=sous,
                    espece_limitante="—", cat_fraie="Non évalué",
                    disponible=False)

    limitant = max(valides, key=lambda s: (s["P"], s["pct"]))

    if verbose:
        for s in valides:
            flag = " ★" if s is limitant else ""
            rec = f", {s['n_annees']} an(s)" if s['n_annees'] else ""
            print(f"    {s['espece']:14s} : {s['pct']:5.1f}% hors optimum "
                  f"[{s['opt'][0]}–{s['opt'][1]}°C] → P={s['P']} ({s['cat']}"
                  f"{rec}){flag}")

    return dict(P_fraie=limitant["P"], pct_fraie=limitant["pct"],
                sous_indicateurs=sous, espece_limitante=limitant["espece"],
                cat_fraie=limitant["cat"], disponible=True,
                n_annees=limitant["n_annees"])


# ============================================================
# ÉTAPE 3 — SGVT (note §2.6, 4 composantes)
# ============================================================
def calcul_sgvt(sens_res, vul_res, fraie_res=None):
    """
    SGVT à 4 composantes pondérées (note §2.6 V2) :
      SGVT = (P_sens×0,25 + P_chr×0,30 + P_aiguë×0,20 + P_fraie×0,25)/3 ×10
    Le stress chronique estival conserve la dominance (0,30). Max exact = 10.

    Si fraie_res est None (aucun paramètre fraie défini), on retombe sur la
    formule historique à 3 composantes (0,30/0,40/0,30) pour compatibilité.
    """
    pts_map_sens = {"Sensibilité Critique": 3, "Sensibilité Forte": 2,
                    "Sensibilité Modérée": 1, "Résilience Élevée": 0}
    pts_map_chr = {"Vulnérabilité chronique critique": 3, "Forte vulnérabilité chronique": 2,
                   "Vulnérabilité chronique modérée": 1, "Faible vulnérabilité chronique": 0}
    pts_map_aig = {"Vulnérabilité aiguë létale": 3, "Vulnérabilité aiguë sévère": 2,
                   "Vulnérabilité aiguë ponctuelle": 1, "Absence de vulnérabilité aiguë": 0}
    p_s = pts_map_sens.get(sens_res["sens_cat"], 0)
    p_c = pts_map_chr.get(vul_res["cat_chr"], 0)
    p_a = pts_map_aig.get(vul_res["cat_aigu"], 0)

    if fraie_res is not None and fraie_res.get("disponible") and \
       fraie_res.get("P_fraie") is not None:
        p_f = fraie_res.get("P_fraie", 0)
        # Pondération V2 à 4 composantes
        w_s, w_c, w_a, w_f = 0.25, 0.30, 0.20, 0.25
        sgvt = (p_s * w_s + p_c * w_c + p_a * w_a + p_f * w_f) / 3 * 10
        composantes = 4
    else:
        # Repli 3 composantes : soit contexte sans fraie, soit chronique
        # trop lacunaire sur le mois central (fraie non évaluable).
        p_f = None
        w_s, w_c, w_a, w_f = 0.30, 0.40, 0.30, None
        sgvt = (p_s * w_s + p_c * w_c + p_a * w_a) / 3 * 10
        composantes = 3

    if sgvt >= 8:   interp, color = "Risque Majeur", "#c0392b"
    elif sgvt >= 5: interp, color = "Risque Élevé", "#e67e22"
    elif sgvt >= 2: interp, color = "Risque Modéré", "#f39c12"
    else:           interp, color = "Risque Faible (Zone Refuge)", "#27ae60"

    return dict(sgvt=sgvt, pts_s=p_s, pts_c=p_c, pts_a=p_a, pts_f=p_f,
                poids=dict(s=w_s, c=w_c, a=w_a, f=w_f), composantes=composantes,
                interp=interp, color=color,
                r2=sens_res["r2"], r2_cat=sens_res["r2_cat"],
                robustesse=sens_res["robustesse"], rob_cat=sens_res["rob_cat"],
                fraie=fraie_res)




# ============================================================
# ÉTAPE 4 — DÉBITS DE RÉFÉRENCE (note §2.8)
# ============================================================
def _aic_simple(x, y):
    n = len(x); sl, ic, *_ = stats.linregress(x, y)
    rss = np.sum((y - (sl*x + ic))**2); k = 3
    aic = n*np.log(rss/n) + 2*k
    return aic + 2*k*(k+1)/max(n-k-1, 1), sl, ic

def _aic_segmente(x, y, q, q_break):
    mask_lo = q <= q_break; mask_hi = q > q_break
    if mask_lo.sum() < 4 or mask_hi.sum() < 4: return np.inf, np.nan, np.nan
    n = len(x); k = 6
    sl_lo, ic_lo, *_ = stats.linregress(x[mask_lo], y[mask_lo])
    sl_hi, ic_hi, *_ = stats.linregress(x[mask_hi], y[mask_hi])
    rss = (np.sum((y[mask_lo] - (sl_lo*x[mask_lo] + ic_lo))**2) +
           np.sum((y[mask_hi] - (sl_hi*x[mask_hi] + ic_hi))**2))
    aic = n*np.log(rss/n) + 2*k
    return aic + 2*k*(k+1)/max(n-k-1, 1), sl_lo, sl_hi


def analyse_debits_inflexion(df, sens_res, contexte, contexte_key="cyprinicole"):
    """
    Détecte Q*_stat (AICc optimal → base Q_thermie_fonc, appoint) et le
    Q*_vuln par fenêtre glissante locale (→ base Q_thermie_bio, résultat
    principal). Voir note §2.7.
    """
    if "Q" not in df.columns:
        print("  ⚠️  Pas de données de débit.")
        return None
    df_ete = df[df["month"].isin([6, 7, 8, 9])].dropna(subset=["T_eau_moy", "T_air", "Q"]).copy()
    if len(df_ete) < 20:
        print(f"  ⚠️  Données insuffisantes ({len(df_ete)} j).")
        return None

    x, y, q = df_ete["T_air"].values, df_ete["T_eau_moy"].values, df_ete["Q"].values
    aicc_s, *_ = _aic_simple(x, y)

    q_cands = np.sort(np.unique(np.percentile(q, np.linspace(5, 95, 500))))
    scan = []
    best_aicc, q_aicc, m_lo_aicc, m_hi_aicc = np.inf, None, None, None
    best_dm,   q_ecol, m_lo_ecol, m_hi_ecol = -np.inf, None, None, None
    n_min_side = max(15, int(len(x) * 0.25))

    for qc in q_cands:
        aicc_seg, m_lo, m_hi = _aic_segmente(x, y, q, qc)
        scan.append((qc, aicc_seg))
        if np.isinf(aicc_seg): continue
        delta_qc = aicc_s - aicc_seg
        n_lo = (q <= qc).sum(); n_hi = (q > qc).sum()
        if aicc_seg < best_aicc:
            best_aicc, q_aicc = aicc_seg, qc
            m_lo_aicc, m_hi_aicc = m_lo, m_hi
        if delta_qc > 2.0 and n_lo >= n_min_side and n_hi >= n_min_side:
            dm = abs(m_lo - m_hi)
            if dm > best_dm:
                best_dm, q_ecol = dm, qc
                m_lo_ecol, m_hi_ecol = m_lo, m_hi

    scan_arr   = np.array(scan)
    delta_aicc = aicc_s - best_aicc
    if q_ecol is None:
        q_ecol, m_lo_ecol, m_hi_ecol, best_dm = q_aicc, m_lo_aicc, m_hi_aicc, abs(m_lo_aicc - m_hi_aicc)
    delta_aicc_e = aicc_s - _aic_segmente(x, y, q, q_ecol)[0]

    valide_aicc = delta_aicc   > 2.0
    valide_ecol = delta_aicc_e > 2.0
    valide      = valide_ecol
    deux_ruptures = abs(q_aicc - q_ecol) > 0.05 * q_ecol if q_ecol else False

    q_seuil = q_ecol; m_below = m_lo_ecol; m_above = m_hi_ecol
    t_eau_lo = y[q <= q_seuil].mean() if (q <= q_seuil).sum() > 0 else np.nan
    seuil_chr = contexte["seuil_chr"]

    def _interp(q_ref, m_lo, m_hi, t_lo):
        if m_hi < m_lo:
            return "Décrochage thermique à bas débit"
        return ("Effet tampon à bas débit (zone refuge)" if t_lo < seuil_chr - 2
                else "Saturation thermique à bas débit (critique)")
    interp = "Pas de seuil significatif" if not valide else _interp(q_seuil, m_below, m_above, t_eau_lo)

    # courbe m(Q) glissant
    df_s = df_ete.sort_values("Q").reset_index(drop=True)
    win = max(15, len(df_ete) // 6)
    m_roll, q_roll = [], []
    for i in range(len(df_s) - win + 1):
        sub = df_s.iloc[i:i+win]
        if len(sub) >= 5:
            sl, *_ = stats.linregress(sub["T_air"], sub["T_eau_moy"])
            m_roll.append(sl); q_roll.append(sub["Q"].median())

    # Q*_vuln — seuil de vulnérabilité directe (base Q_thermie_bio)
    SEUIL_VULN_PCT = 3.0 if contexte_key in ("salmonicole", "intermediaire") else 5.0
    n_min_vuln = max(10, int(len(df_ete) * 0.10))
    tmh_col  = "Tmh_norm"  if "Tmh_norm"  in df_ete.columns else "Tmh"
    tmax_col = "Tmax_norm" if "Tmax_norm" in df_ete.columns else "T_eau_max"
    seuil_aigu = contexte["seuil_aigu"]
    df_ete_v = df_ete

    q_vuln_cands = np.sort(np.unique(np.percentile(q, np.linspace(5, 95, 300))))
    vuln_cum_q, vuln_cum_pct = [], []
    for qc in q_vuln_cands:
        mask = df_ete_v["Q"].values <= qc; n_below = mask.sum()
        if n_below < n_min_vuln: continue
        pct_stress = 100 * (df_ete_v.loc[mask, tmh_col] > seuil_chr).sum() / n_below
        vuln_cum_q.append(qc); vuln_cum_pct.append(pct_stress)
    vuln_cum_q = np.array(vuln_cum_q); vuln_cum_pct = np.array(vuln_cum_pct)

    aigu_cum_q, aigu_cum_nj = [], []
    for qc in q_vuln_cands:
        mask = df_ete_v["Q"].values <= qc; n_below = mask.sum()
        if n_below < n_min_vuln: continue
        n_letal = int((df_ete_v.loc[mask, tmax_col] > seuil_aigu).sum())
        aigu_cum_q.append(qc); aigu_cum_nj.append(n_letal)
    aigu_cum_q = np.array(aigu_cum_q); aigu_cum_nj = np.array(aigu_cum_nj)

    # courbes glissantes (base du calcul Q*_vuln)
    vuln_roll, q_vuln_roll = [], []
    aigu_roll, q_aigu_roll = [], []
    for i in range(len(df_s) - win + 1):
        sub = df_s.iloc[i:i+win]
        vuln_roll.append(100 * (sub[tmh_col] > seuil_chr).sum() / len(sub))
        q_vuln_roll.append(sub["Q"].median())
        aigu_roll.append(int((sub[tmax_col] > seuil_aigu).sum()))
        q_aigu_roll.append(sub["Q"].median())

    q_vuln_chr = None
    for i in range(len(vuln_roll) - 1, -1, -1):
        if vuln_roll[i] > SEUIL_VULN_PCT:
            q_vuln_chr = q_vuln_roll[i]; break
    q_vuln_aigu = None
    for i in range(len(aigu_roll) - 1, -1, -1):
        if aigu_roll[i] >= 1:
            q_vuln_aigu = q_aigu_roll[i]; break

    q_vuln_candidates = [v for v in [q_vuln_chr, q_vuln_aigu] if v is not None]
    q_vuln = max(q_vuln_candidates) if q_vuln_candidates else None
    q_vuln_valide = q_vuln is not None

    base = df.attrs.get("base_debit", "influencé")
    print(f"  Base de débit            : {base}")
    print(f"  Q*_stat (AICc opt.)      : {q_aicc:.3f} m³/s  → base Q_thermie_fonc (appoint)")
    print(f"    ΔAICc                  : {delta_aicc:.2f}  → {'Validée ✅' if valide_aicc else 'Non validée ⚠️'}")
    print(f"  Q*_marquée (max |Δm|)    : {q_ecol:.3f} m³/s  |Δm|={best_dm:.3f} (info)")
    print(f"  Interprétation           : {interp}")
    if q_vuln_chr is not None:
        print(f"  Q*_vuln_stress           : {q_vuln_chr:.3f} m³/s (stress > {SEUIL_VULN_PCT}%)")
    else:
        print(f"  Q*_vuln_stress           : non détecté")
    if q_vuln_aigu is not None:
        print(f"  Q*_vuln_létal            : {q_vuln_aigu:.3f} m³/s (≥1j > {seuil_aigu}°C)")
    else:
        print(f"  Q*_vuln_létal            : non détecté")
    if q_vuln_valide:
        print(f"  Q*_vuln retenu (max)     : {q_vuln:.3f} m³/s  → base Q_thermie_bio (PRINCIPAL)")
    else:
        print(f"  Q*_vuln                  : non détecté")

    return dict(
        valide=valide,
        q_seuil=q_seuil, m_below=m_below, m_above=m_above,
        delta_aicc=delta_aicc_e, aicc_segmente=_aic_segmente(x, y, q, q_ecol)[0],
        q_aicc=q_aicc, m_lo_aicc=m_lo_aicc, m_hi_aicc=m_hi_aicc,
        delta_aicc_aicc=delta_aicc, aicc_optimal=best_aicc, deux_ruptures=deux_ruptures,
        q_vuln=q_vuln, q_vuln_chr=q_vuln_chr, q_vuln_aigu=q_vuln_aigu,
        q_vuln_valide=q_vuln_valide, seuil_vuln_pct=SEUIL_VULN_PCT,
        vuln_cum_q=vuln_cum_q, vuln_cum_pct=vuln_cum_pct,
        aigu_cum_q=aigu_cum_q, aigu_cum_nj=aigu_cum_nj,
        vuln_roll=np.array(vuln_roll), q_vuln_roll=np.array(q_vuln_roll),
        aigu_roll=np.array(aigu_roll), q_aigu_roll=np.array(q_aigu_roll),
        aicc_simple=aicc_s, dm_ecol=best_dm,
        q_roll=np.array(q_roll), m_roll=np.array(m_roll),
        scan_q=scan_arr[:, 0], scan_aicc=scan_arr[:, 1],
        df_ete=df_ete, t_eau_lo=t_eau_lo, interpretation_courte=interp,
        robustesse=sens_res["robustesse"], rob_cat=sens_res["rob_cat"],
        base_debit=base,
    )


# ============================================================
# DÉBITS DE RÉFÉRENCE (note §2.7)
#   Q_thermie_bio  = Q*_vuln × 1,10   → RÉSULTAT PRINCIPAL
#   Q_thermie_fonc = Q*_stat × (1+α_fonc) → information d'appoint


def calcul_debits_thermie(sgvt, q_stat, q_marquee, q_seuil_vuln, df):
    """
    Q_thermie_fonc = Q*_stat (AICc optimal) × (1 + α_fonc), α_fonc modulé SGVT.
    Q_thermie_bio  = Q*_vuln (glissant) × (1 + 10%)  [résultat principal].
    """
    if sgvt <= 2:
        alpha_fonc, sgvt_class = 0.10, "Faible"
    elif sgvt <= 5:
        alpha_fonc, sgvt_class = 0.15, "Modérée"
    elif sgvt <= 8:
        alpha_fonc, sgvt_class = 0.25, "Élevée"
    else:
        alpha_fonc, sgvt_class = 0.35, "Très forte"
    alpha_vuln = 0.10

    q_thermie_fonc = q_stat * (1 + alpha_fonc)
    print(f"  Classe SGVT       : {sgvt_class}")
    print(f"  Q_thermie_fonc    : Q*_stat={q_stat:.3f} × (1+{alpha_fonc*100:.0f}%) = {q_thermie_fonc:.3f} m³/s  (appoint)")
    print(f"    (Q*_marquée = {q_marquee:.3f} m³/s — info)")

    q_thermie_bio = None
    if q_seuil_vuln is not None:
        q_thermie_bio = q_seuil_vuln * (1 + alpha_vuln)
        print(f"  Q_thermie_bio     : Q*_vuln={q_seuil_vuln:.3f} × (1+{alpha_vuln*100:.0f}%) = {q_thermie_bio:.3f} m³/s  ★ PRINCIPAL")
    else:
        print(f"  Q_thermie_bio     : non applicable (Q*_vuln non détecté)")

    return dict(
        alpha_fonc=alpha_fonc, alpha_vuln=alpha_vuln, sgvt_class=sgvt_class,
        q_stat=q_stat, q_marquee=q_marquee, q_seuil_vuln=q_seuil_vuln,
        q_thermie_fonc=q_thermie_fonc, q_thermie_bio=q_thermie_bio,
    )


# ---- PNDA (utilitaire partagé figures/exports) ----
def _pnda(q_all_series, q_val):
    if q_val is None or q_all_series is None: return None
    s = q_all_series.dropna()
    if len(s) == 0: return None
    return (s <= q_val).mean() * 100


# ============================================================
# PNDA multi-base pour les débits de référence (sorties)
# ============================================================
def pnda_multi_base(valeur, q_influence=None, q_desinfluence=None):
    """
    Exprime UNE valeur de débit (m³/s, base de calcul retenue) via son PNDA
    lu sur CHAQUE distribution disponible (influencée et/ou désinfluencée).
    Le PNDA de chaque base se lit sur SA propre courbe de débits classés.

    Retourne un dict : {valeur, pnda_desinf, pnda_inf} (None si base absente).
    """
    if valeur is None:
        return dict(valeur=None, pnda_desinf=None, pnda_inf=None)
    return dict(
        valeur=valeur,
        pnda_desinf=_pnda(q_desinfluence, valeur) if q_desinfluence is not None else None,
        pnda_inf=_pnda(q_influence, valeur) if q_influence is not None else None,
    )


# ============================================================
# DÉTECTION DES LACUNES TEMPORELLES (trous de mesure)
# ============================================================
def detecter_pas(dates, verbose=False):
    """
    Détecte le pas d'échantillonnage médian d'une série de dates.
    Retourne un Timedelta (ex. 1 jour, 4h). Robuste aux valeurs isolées.
    """
    d = pd.to_datetime(pd.Series(dates)).sort_values().drop_duplicates()
    if len(d) < 3:
        return pd.Timedelta(days=1)
    deltas = d.diff().dropna()
    pas = deltas.median()
    if verbose:
        print(f"  Pas d'échantillonnage médian : {pas}")
    return pas


def inserer_lacunes(df, col_date="date_dt", cols_valeurs=None,
                    seuil_pas=3, pas=None):
    """
    Insère des lignes NaN aux emplacements de lacune pour que les tracés ne
    relient pas les points de part et d'autre d'un trou (note : point 2).

    Un trou est une interruption > seuil_pas × pas médian. Retourne une copie
    du df triée, avec des lignes NaN insérées au milieu de chaque lacune.
    cols_valeurs : colonnes à mettre à NaN (défaut : toutes sauf la date).
    """
    df = df.sort_values(col_date).reset_index(drop=True).copy()
    if len(df) < 3:
        return df
    if pas is None:
        pas = detecter_pas(df[col_date])
    seuil = seuil_pas * pas
    if cols_valeurs is None:
        cols_valeurs = [c for c in df.columns if c != col_date]

    dts = pd.to_datetime(df[col_date])
    trous = dts.diff() > seuil
    idx_trous = df.index[trous].tolist()
    if not idx_trous:
        return df

    lignes_nan = []
    for i in idx_trous:
        t0 = dts.iloc[i - 1]; t1 = dts.iloc[i]
        milieu = t0 + (t1 - t0) / 2
        ligne = {c: np.nan for c in df.columns}
        ligne[col_date] = milieu
        lignes_nan.append(ligne)
    df_nan = pd.DataFrame(lignes_nan)
    out = pd.concat([df, df_nan], ignore_index=True).sort_values(col_date)
    return out.reset_index(drop=True)


def segments_valides(dates, valeurs, seuil_pas=3, pas=None):
    """
    Découpe une série en segments continus (sans lacune > seuil_pas × pas).
    Retourne une liste de (dates_seg, valeurs_seg) pour tracer chaque segment
    séparément — alternative à inserer_lacunes pour les tracés fins.
    """
    d = pd.to_datetime(pd.Series(dates)).reset_index(drop=True)
    v = pd.Series(valeurs).reset_index(drop=True)
    if len(d) < 2:
        return [(d, v)]
    if pas is None:
        pas = detecter_pas(d)
    seuil = seuil_pas * pas
    coupures = d.diff() > seuil
    seg_id = coupures.cumsum()
    segments = []
    for _, grp in pd.DataFrame({"d": d, "v": v, "s": seg_id}).groupby("s"):
        segments.append((grp["d"].values, grp["v"].values))
    return segments
