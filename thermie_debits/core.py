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
                     FRAIE_MIN_JOURS_CENTRAL, SGVT_POIDS_4, SGVT_POIDS_3,
                     FRAIE_SCORE_ELARGIE, FRAIE_SCORE_LETAL,
                     FRAIE_FROID_PLAFOND_INTERMEDIAIRE,
                     FRAIE_SEUILS_SEV, FRAIE_SEUILS_LETAL,
                     STRESS_PLANCHER_PCT, STRESS_CORR_R2_MIN,
                     STRESS_CORR_SIGNE_NEG)


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


def cat_fraie_sev(sev_moy, pct_letal):
    """
    Classe fraie combinant la sévérité moyenne (pondération 3 paliers) et le
    temps passé en zone létale. La sévérité ∈ [0, 3] : 0 = tout dans l'optimum,
    1 = tout dans la fenêtre élargie, 3 = tout en zone létale.

    Calibration « médiane » (validée) : la zone élargie traduit un simple
    ralentissement du développement, tandis que la létalité embryonnaire est un
    événement grave — quelques jours au mauvais stade peuvent compromettre une
    cohorte. La classe finale est donc le MAXIMUM entre le classement par
    sévérité et celui par létalité, pour que la létalité ne puisse jamais être
    diluée par une bonne moyenne.

    Repères : 100 % optimum → P0 ; ≥ 75 % optimum → P0 ; 100 % en fenêtre
    élargie sans létalité → P1 ; ≥ 6 % de létalité → P2 ; ≥ 15 % → P3.
    """
    # Classement par sévérité moyenne
    if   sev_moy < FRAIE_SEUILS_SEV[0]: c_sev = 0
    elif sev_moy < FRAIE_SEUILS_SEV[1]: c_sev = 1
    elif sev_moy < FRAIE_SEUILS_SEV[2]: c_sev = 2
    else:                               c_sev = 3
    # Classement par temps en zone létale (plancher, non dilutable)
    if   pct_letal < FRAIE_SEUILS_LETAL[0]: c_let = 0
    elif pct_letal < FRAIE_SEUILS_LETAL[1]: c_let = 1
    elif pct_letal < FRAIE_SEUILS_LETAL[2]: c_let = 2
    else:                                   c_let = 3

    P = max(c_sev, c_let)
    libelles = {0: "Faible vulnérabilité fraie",
                1: "Vulnérabilité fraie modérée",
                2: "Forte vulnérabilité fraie",
                3: "Vulnérabilité fraie critique"}
    return libelles[P], P


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


def _severite_fraie(tmh, opt_min, opt_max, elargie_min, elargie_max,
                    froid_bloquant=False):
    """
    Score de sévérité journalier à 3 PALIERS, pour une phase donnée.

      - dans l'optimum strict [opt_min, opt_max]        → 0
      - dans la tolérance élargie, hors optimum          → FRAIE_SCORE_ELARGIE
      - au-delà de l'élargie côté CHAUD (létalité)       → FRAIE_SCORE_LETAL
      - au-delà de l'élargie côté FROID :
          * froid_bloquant=False (truite, pondeur automnal) → plafonné au
            palier intermédiaire : le froid ralentit l'incubation sans
            mortalité massive ;
          * froid_bloquant=True (ombre, brochet, brème) → palier fort : chez
            les pondeurs printaniers et estivaux le froid empêche la ponte
            (refus de frayer, atrésie folliculaire), soit un échec
            reproducteur complet.

    Températures attendues : NORMALISÉES (année standard).
    """
    x = np.asarray(tmh, dtype=float)
    sev = np.full_like(x, np.nan)
    sev[(x >= opt_min) & (x <= opt_max)] = 0.0
    sev[(x > opt_max) & (x <= elargie_max)] = FRAIE_SCORE_ELARGIE
    sev[(x < opt_min) & (x >= elargie_min)] = FRAIE_SCORE_ELARGIE
    sev[x > elargie_max] = FRAIE_SCORE_LETAL
    if froid_bloquant:
        sev[x < elargie_min] = FRAIE_SCORE_LETAL
    else:
        sev[x < elargie_min] = (FRAIE_SCORE_ELARGIE
                                if FRAIE_FROID_PLAFOND_INTERMEDIAIRE
                                else FRAIE_SCORE_LETAL)
    return sev


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
    Composante fraie-croissance P_fraie (score /3), évaluée sur TROIS PHASES
    successives (pré-frai, ponte, incubation) aux tolérances thermiques
    distinctes. Un jour appartenant à deux phases qui se chevauchent reçoit le
    score le plus contraignant.

    Le score global d'une espèce est calculé sur l'ensemble des jours de sa
    fenêtre de reproduction, chaque jour étant évalué avec les seuils de sa
    phase ; le détail par phase est conservé pour l'interprétation.

    Zone cyprinicole : deux sous-indicateurs (brochet + brème), le plus
    contraignant alimente P_fraie ; les deux sont affichés.

    Retourne un dict (P_fraie, sous_indicateurs, espece_limitante…) ou None.
    """
    params = contexte.get("fraie")
    if not params:
        return None

    sous = []
    for espece, pr in params.items():
        phases = pr["phases"]
        froid_bloquant = pr.get("froid_bloquant", False)
        mois_tous = sorted({m for ph in phases for m in ph["mois"]})

        sub = df[df["month"].isin(mois_tous)].dropna(
            subset=["Tmh", "Delta_TMm"]).copy()
        if len(sub) == 0:
            sous.append(dict(espece=espece, evalue=False, P=None,
                             motif="aucune donnée sur la fenêtre de reproduction",
                             phases=[], src=pr.get("src", ""),
                             froid_bloquant=froid_bloquant))
            continue

        # coefficient de couplage saisonnier propre à la fenêtre de l'espèce
        m_s, m_info = _m_saisonnier(df, mois_tous, m_estival, verbose)
        sub["Tmh_norm_fraie"] = sub["Tmh"] - (m_s * sub["Delta_TMm"])

        # ---- Score journalier : le plus contraignant des phases actives ----
        sev_glob = np.full(len(sub), np.nan)
        sev_brut_glob = np.full(len(sub), np.nan)
        detail_phases = []
        mois_arr = sub["month"].values
        tnorm = sub["Tmh_norm_fraie"].values
        tbrut = sub["Tmh"].values

        for ph in phases:
            masque = np.isin(mois_arr, ph["mois"])
            n_ph = int(masque.sum())
            # couverture du mois central de la phase
            n_central = int((mois_arr == ph["mois_central"]).sum())
            annees_c = sorted(sub.loc[mois_arr == ph["mois_central"],
                                      "date_dt"].dt.year.unique().tolist()) \
                       if n_central else []
            couvert = n_central >= FRAIE_MIN_JOURS_CENTRAL

            if n_ph == 0:
                detail_phases.append(dict(
                    cle=ph["cle"], nom=ph["nom"], evaluee=False, n=0,
                    n_central=0, n_annees=0, couvert=False,
                    opt=ph["opt"], elargie=ph["elargie"], critique=ph["critique"],
                    note=ph.get("note", ""), mois=ph["mois"]))
                continue

            # Le froid n'est « bloquant » (échec reproducteur) que sur les
            # phases critiques : en pré-frai, une eau trop froide décale
            # simplement le frai (plasticité phénologique) sans le compromettre.
            froid_bloq_ph = froid_bloquant and ph["critique"]
            sev_ph = _severite_fraie(tnorm[masque], ph["opt"][0], ph["opt"][1],
                                     ph["elargie"][0], ph["elargie"][1],
                                     froid_bloquant=froid_bloq_ph)
            sev_ph_brut = _severite_fraie(tbrut[masque], ph["opt"][0], ph["opt"][1],
                                          ph["elargie"][0], ph["elargie"][1],
                                          froid_bloquant=froid_bloq_ph)
            # chevauchement : on retient le score le plus contraignant
            anciens = sev_glob[masque]
            sev_glob[masque] = np.where(np.isnan(anciens), sev_ph,
                                        np.maximum(anciens, sev_ph))
            anciens_b = sev_brut_glob[masque]
            sev_brut_glob[masque] = np.where(np.isnan(anciens_b), sev_ph_brut,
                                             np.maximum(anciens_b, sev_ph_brut))

            detail_phases.append(dict(
                cle=ph["cle"], nom=ph["nom"], evaluee=couvert, n=n_ph,
                n_central=n_central, n_annees=len(annees_c), couvert=couvert,
                opt=ph["opt"], elargie=ph["elargie"], critique=ph["critique"],
                note=ph.get("note", ""), mois=ph["mois"],
                pct_optimum=100 * (sev_ph == 0).sum() / n_ph,
                pct_elargie=100 * (sev_ph == FRAIE_SCORE_ELARGIE).sum() / n_ph,
                pct_letal=100 * (sev_ph == FRAIE_SCORE_LETAL).sum() / n_ph,
                sev_moy=float(np.nanmean(sev_ph)),
                pct_optimum_brut=100 * (sev_ph_brut == 0).sum() / n_ph,
                pct_elargie_brut=100 * (sev_ph_brut == FRAIE_SCORE_ELARGIE).sum() / n_ph,
                pct_letal_brut=100 * (sev_ph_brut == FRAIE_SCORE_LETAL).sum() / n_ph))

        # ---- Évaluabilité : au moins une phase CRITIQUE couverte ----
        critiques_ok = [d for d in detail_phases
                        if d["critique"] and d.get("couvert")]
        if not critiques_ok:
            manquantes = ", ".join(d["nom"] for d in detail_phases
                                   if d["critique"])
            sous.append(dict(espece=espece, evalue=False, P=None,
                             motif=f"phases critiques non couvertes ({manquantes})",
                             phases=detail_phases, src=pr.get("src", ""),
                             froid_bloquant=froid_bloquant, m_saison=m_s,
                             m_info=m_info, sub=sub))
            continue

        # ---- Agrégation globale (tous les jours de la fenêtre) ----
        valides = ~np.isnan(sev_glob)
        n_tot = int(valides.sum())
        sev = sev_glob[valides]; sev_b = sev_brut_glob[valides]
        pct_optimum = 100 * (sev == 0).sum() / n_tot
        pct_elargie = 100 * (sev == FRAIE_SCORE_ELARGIE).sum() / n_tot
        pct_letal = 100 * (sev == FRAIE_SCORE_LETAL).sum() / n_tot
        sev_moy = float(np.mean(sev))
        pct_optimum_brut = 100 * (sev_b == 0).sum() / n_tot
        pct_elargie_brut = 100 * (sev_b == FRAIE_SCORE_ELARGIE).sum() / n_tot
        pct_letal_brut = 100 * (sev_b == FRAIE_SCORE_LETAL).sum() / n_tot
        cat, P = cat_fraie_sev(sev_moy, pct_letal)

        sub = sub.copy()
        sub["sev_fraie"] = sev_glob
        sous.append(dict(
            espece=espece, evalue=True, P=P, cat=cat, n=n_tot,
            pct=pct_elargie + pct_letal, sev_moy=sev_moy,
            pct_optimum=pct_optimum, pct_elargie=pct_elargie, pct_letal=pct_letal,
            pct_optimum_brut=pct_optimum_brut, pct_elargie_brut=pct_elargie_brut,
            pct_letal_brut=pct_letal_brut,
            pct_brut=pct_elargie_brut + pct_letal_brut,
            phases=detail_phases, froid_bloquant=froid_bloquant,
            src=pr.get("src", ""), m_saison=m_s, m_info=m_info,
            fenetre=mois_tous, sub=sub, sev=sev_glob,
            n_central=max((d["n_central"] for d in detail_phases), default=0),
            n_annees=max((d["n_annees"] for d in detail_phases), default=0)))

        if verbose:
            print(f"    {espece} : optimum {pct_optimum:.0f}% / élargie "
                  f"{pct_elargie:.0f}% / létal {pct_letal:.0f}% → P={P}")

    evalues = [s for s in sous if s.get("evalue")]
    if not evalues:
        return dict(disponible=False, sous_indicateurs=sous, P_fraie=None,
                    espece_limitante=None)

    limitant = max(evalues, key=lambda s: s["P"])
    return dict(disponible=True, sous_indicateurs=sous,
                P_fraie=limitant["P"], pct_fraie=limitant["pct"],
                cat_fraie=limitant["cat"], espece_limitante=limitant["espece"],
                n_annees=limitant.get("n_annees", 0))

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


def analyse_debits_inflexion(df, sens_res, contexte, contexte_key="cyprinicole",
                             stress_plancher_pct=None, stress_corr_r2_min=None,
                             relation=None):
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

    # ========================================================
    # VOLET LÉTAL — déclencheur PRINCIPAL (fiable, bas débits)
    # ========================================================
    aigu_roll, q_aigu_roll = [], []
    for i in range(len(df_s) - win + 1):
        sub = df_s.iloc[i:i+win]
        aigu_roll.append(int((sub[tmax_col] > seuil_aigu).sum()))
        q_aigu_roll.append(sub["Q"].median())
    q_vuln_aigu = None
    for i in range(len(aigu_roll) - 1, -1, -1):
        if aigu_roll[i] >= 1:
            q_vuln_aigu = q_aigu_roll[i]; break

    # ========================================================
    # VOLET STRESS — CONDITIONNEL (2 verrous cumulatifs)
    # ========================================================
    # Verrou 1 — matérialité : % de jours estivaux stressés global
    plancher = (STRESS_PLANCHER_PCT if stress_plancher_pct is None
                else float(stress_plancher_pct))
    r2_min = (STRESS_CORR_R2_MIN if stress_corr_r2_min is None
              else float(stress_corr_r2_min))
    pct_stress_global = 100 * (df_ete[tmh_col] > seuil_chr).mean()
    materiel = pct_stress_global >= plancher

    # Verrou 2 — causalité : relation débit→température.
    # SOURCE UNIQUE : on consomme le test préalable (analyse_relation_debit_
    # temperature) plutôt que de recalculer, afin qu'un seul et même chiffre
    # soit affiché partout (l'onglet Relation et le diagnostic du volet stress
    # ne peuvent plus se contredire). Repli sur un calcul local uniquement si
    # la relation n'a pas été fournie.
    if relation is not None and relation.get("disponible"):
        globale = relation["lignes"][0]
        r_qt = globale["r_brute"]; r2_qt = globale["r2_brute"]
        r_part = globale["r_partielle"]; r2_part = globale["r2_partielle"]
        source_correl = "test préalable (source unique)"
    else:
        qv = df_ete["Q"].values
        tv = df_ete[tmh_col].values
        mask_ok = np.isfinite(qv) & np.isfinite(tv)
        r_qt = (np.corrcoef(qv[mask_ok], tv[mask_ok])[0, 1]
                if mask_ok.sum() >= 10 else np.nan)
        r2_qt = r_qt ** 2 if np.isfinite(r_qt) else np.nan
        r_part = (corr_partielle_air(df_ete["Q"], df_ete[tmh_col], df_ete["T_air"])
                  if "T_air" in df_ete.columns else np.nan)
        r2_part = r_part ** 2 if np.isfinite(r_part) else np.nan
        source_correl = "calcul local (test préalable non fourni)"

    def _concluant(r, r2):
        if not np.isfinite(r) or not np.isfinite(r2):
            return False
        signe = (r < 0) if STRESS_CORR_SIGNE_NEG else True
        return signe and r2 >= r2_min

    causal_brut = _concluant(r_qt, r2_qt)
    causal_part = _concluant(r_part, r2_part)
    causal = causal_brut or causal_part
    signe_ok = (r_qt < 0) if STRESS_CORR_SIGNE_NEG else True

    stress_actif = materiel and causal
    if not materiel:
        raison_stress = (f"stress insuffisant ({pct_stress_global:.1f}% < "
                         f"{plancher:.0f}% requis)")
    elif not causal:
        def _fmt(r, r2):
            return f"{r:+.2f}" if np.isfinite(r) else "n.d."
        raison_stress = (f"pas de lien débit→température concluant "
                         f"(brute {_fmt(r_qt, r2_qt)}, "
                         f"partielle/air {_fmt(r_part, r2_part)} ; "
                         f"il faut une corrélation négative avec R² ≥ {r2_min:.2f})")
    else:
        raison_stress = None

    # Courbe de stress vs débit : TOUJOURS calculée (diagnostic/affichage),
    # mais on n'en extrait un débit seuil que si les deux verrous sont réunis.
    vuln_roll, q_vuln_roll = [], []
    for i in range(len(df_s) - win + 1):
        sub = df_s.iloc[i:i+win]
        vuln_roll.append(100 * (sub[tmh_col] > seuil_chr).sum() / len(sub))
        q_vuln_roll.append(sub["Q"].median())

    q_vuln_chr = None
    if stress_actif:
        # premier franchissement en venant des bas débits (plus stable que le
        # « dernier franchissement en descendant », qui capturait le bruit)
        for i in range(len(vuln_roll)):
            if vuln_roll[i] > SEUIL_VULN_PCT:
                q_vuln_chr = q_vuln_roll[i]; break

    # ========================================================
    # Q*_vuln final : max(létal, stress si actif)
    # ========================================================
    q_vuln_candidates = [v for v in [q_vuln_chr, q_vuln_aigu] if v is not None]
    q_vuln = max(q_vuln_candidates) if q_vuln_candidates else None
    q_vuln_valide = q_vuln is not None
    diag_stress = dict(pct_stress_global=pct_stress_global,
                       plancher=plancher, r2_min=r2_min, materiel=materiel,
                       r_qt=r_qt, r2_qt=r2_qt,
                       r_partielle=r_part, r2_partielle=r2_part,
                       causal_brut=causal_brut, causal_partielle=causal_part,
                       causal=causal, stress_actif=stress_actif,
                       raison=raison_stress, source_correl=source_correl)

    base = df.attrs.get("base_debit", "influencé")
    print(f"  Base de débit            : {base}")
    print(f"  Q*_stat (AICc opt.)      : {q_aicc:.3f} m³/s  → base Q_thermie_fonc (appoint)")
    print(f"    ΔAICc                  : {delta_aicc:.2f}  → {'Validée ✅' if valide_aicc else 'Non validée ⚠️'}")
    print(f"  Q*_marquée (max |Δm|)    : {q_ecol:.3f} m³/s  |Δm|={best_dm:.3f} (info)")
    print(f"  Interprétation           : {interp}")
    if q_vuln_chr is not None:
        print(f"  Q*_vuln_stress           : {q_vuln_chr:.3f} m³/s (stress > {SEUIL_VULN_PCT}%)")
    elif stress_actif:
        print(f"  Q*_vuln_stress           : non détecté (conditions réunies mais pas de seuil)")
    else:
        print(f"  Q*_vuln_stress           : désactivé — {raison_stress}")
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
        diag_stress=diag_stress,
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


# ============================================================
# TEST PRÉALABLE — le débit module-t-il la température de l'eau ?
# ============================================================
def corr_partielle_air(q, teau, tair, deg=3, n_min=15):
    """
    Corrélation partielle entre débit et température de l'eau, à température
    de l'AIR égale : on retire de chaque variable l'effet du forçage
    atmosphérique (ajustement polynomial), puis on corrèle les résidus.

    Répond à : « à forçage atmosphérique égal, le débit module-t-il la
    température de l'eau ? » — c'est le mécanisme d'inertie thermique.
    Contrôler l'air plutôt que le calendrier rend la mesure robuste même sur
    une seule saison (pas besoin de répétitions inter-annuelles pour estimer
    une normale saisonnière).
    """
    q = np.asarray(q, dtype=float)
    teau = np.asarray(teau, dtype=float)
    tair = np.asarray(tair, dtype=float)
    m = np.isfinite(q) & np.isfinite(teau) & np.isfinite(tair) & (q > 0)
    if m.sum() < n_min:
        return np.nan
    try:
        lq = np.log(q[m] + 0.05)
        d = deg if m.sum() >= 40 else 1
        rq = lq - np.polyval(np.polyfit(tair[m], lq, d), tair[m])
        rt = teau[m] - np.polyval(np.polyfit(tair[m], teau[m], d), tair[m])
        if np.std(rq) < 1e-9 or np.std(rt) < 1e-9:
            return np.nan
        return float(np.corrcoef(rq, rt)[0, 1])
    except Exception:
        return np.nan


def _corr_brute(q, teau, n_min=10):
    q = np.asarray(q, dtype=float); t = np.asarray(teau, dtype=float)
    m = np.isfinite(q) & np.isfinite(t)
    if m.sum() < n_min:
        return np.nan
    return float(np.corrcoef(q[m], t[m])[0, 1])


def analyse_relation_debit_temperature(df, tmh_col=None, r2_min=0.10,
                                       mois_estivaux=(6, 7, 8, 9), verbose=True):
    """
    Test PRÉALABLE à tous les débits de référence : vérifie que le postulat
    fondateur de l'approche (le débit module la température de l'eau) est
    vérifié sur la station.

    La relation est mesurée de deux façons — corrélation BRUTE (inclut l'effet
    structurel du régime d'étiage) et corrélation PARTIELLE à température d'air
    égale (isole le rôle propre du débit) — et déclinée par gamme de débit
    (toute la gamme, sous la médiane, quart inférieur) afin de détecter les
    effets de seuil : l'inertie thermique peut ne se perdre qu'en étiage
    prononcé, l'effet saturant aux débits plus élevés.

    Retourne un dict avec le tableau par gamme, le verdict et les données
    nécessaires aux graphiques. Aucun calcul n'est bloqué : le verdict est
    informatif (une réserve est affichée en aval si la relation est faible).
    """
    if tmh_col is None:
        tmh_col = "Tmh_norm" if "Tmh_norm" in df.columns else "Tmh"
    if "Q" not in df.columns or df["Q"].notna().sum() == 0:
        return dict(disponible=False,
                    message="Aucune donnée de débit : test non réalisable.")

    d = df[df["month"].isin(list(mois_estivaux))].copy()
    d = d.dropna(subset=["Q", tmh_col])
    if "T_air" not in d.columns:
        d["T_air"] = np.nan
    if len(d) < 20:
        return dict(disponible=False,
                    message=f"Données estivales insuffisantes ({len(d)} jours) "
                            f"pour tester la relation débit–température.")

    med = float(d["Q"].median()); q25 = float(d["Q"].quantile(0.25))
    gammes = [("Toute la gamme", d, None),
              (f"Sous la médiane (Q < {med:.3f})", d[d["Q"] < med], med),
              (f"Quart inférieur (Q < {q25:.3f})", d[d["Q"] < q25], q25)]

    lignes = []
    for label, sub, borne in gammes:
        rb = _corr_brute(sub["Q"], sub[tmh_col])
        rp = corr_partielle_air(sub["Q"], sub[tmh_col], sub["T_air"])
        lignes.append(dict(
            gamme=label, n=len(sub), borne=borne,
            r_brute=rb, r2_brute=rb**2 if np.isfinite(rb) else np.nan,
            r_partielle=rp, r2_partielle=rp**2 if np.isfinite(rp) else np.nan,
            concluante=bool(np.isfinite(rp) and rp < 0 and rp**2 >= r2_min)
                       or bool(np.isfinite(rb) and rb < 0 and rb**2 >= r2_min)))

    # --- Verdict gradué ---
    globale = lignes[0]
    rp_g, r2p_g = globale["r_partielle"], globale["r2_partielle"]
    if any(l["concluante"] for l in lignes):
        verdict = "etablie"
        libelle = "Relation débit–température établie"
        commentaire = ("Le débit module effectivement la température de l'eau : "
                       "le postulat de l'approche thermique est vérifié.")
    elif np.isfinite(rp_g) and rp_g > 0 and r2p_g >= r2_min:
        verdict = "inversee"
        libelle = "Relation inversée (anormale)"
        commentaire = ("La température augmente avec le débit, ce qui est "
                       "physiquement inattendu. Causes possibles : rejet ou "
                       "plan d'eau à l'amont, soutien d'étiage, apport de nappe, "
                       "ou artefact de données. Les débits thermiques sont à "
                       "interpréter avec une forte réserve.")
    elif np.isfinite(rp_g) and rp_g < 0:
        verdict = "faible"
        libelle = "Relation faible"
        commentaire = ("Le sens est physiquement cohérent mais le lien est trop "
                       "ténu pour être considéré comme établi. Les débits "
                       "thermiques restent calculés, mais leur portée est "
                       "limitée : agir sur le débit n'aurait qu'un effet "
                       "marginal sur la température.")
    else:
        verdict = "absente"
        libelle = "Relation absente"
        commentaire = ("Aucun lien détectable entre débit et température : le "
                       "milieu est thermiquement tamponné (nappe, ombrage, "
                       "morphologie). Les débits thermiques ne constituent pas "
                       "un levier de gestion pertinent sur cette station.")

    res = dict(disponible=True, verdict=verdict, libelle=libelle,
               commentaire=commentaire, r2_min=r2_min, lignes=lignes,
               mediane=med, q25=q25, tmh_col=tmh_col,
               data=d[["Q", tmh_col, "T_air"]].rename(columns={tmh_col: "Teau"}))
    if verbose:
        print(f"  Relation débit–température : {libelle} "
              f"(partielle globale = {rp_g:+.2f})" if np.isfinite(rp_g)
              else f"  Relation débit–température : {libelle}")
    return res


# ============================================================
# MATRICE DE DIAGNOSTIC — cadre de lecture à deux entrées
# ============================================================
def matrice_diagnostic(vul_res, relation, debits_inflexion=None,
                       plancher_stress=None):
    """
    Croise les DEUX questions que l'approche thermique pose, et qu'il ne faut
    pas confondre :

      axe 1 — « Y a-t-il un problème thermique ? »
              (stress chronique au-dessus du plancher, ou létalité observée)
      axe 2 — « Le débit est-il un levier opérant ? »
              (relation débit→température établie)

    Le croisement donne quatre situations, chacune appelant une conduite
    différente. C'est ce cadre — et non la mécanique interne des verrous — qui
    doit être présenté aux gestionnaires et à l'OFB.

    Retourne un dict : axes, case (1-4), libellé, conduite à tenir, couleur.
    """
    plancher = plancher_stress if plancher_stress is not None else STRESS_PLANCHER_PCT

    # --- Axe 1 : problème thermique avéré ? ---
    pct_chr = vul_res.get("pct_chr", 0.0) if vul_res else 0.0
    n_aigu = vul_res.get("n_aigu", 0) if vul_res else 0
    probleme = (pct_chr >= plancher) or (n_aigu >= 1)
    motif_probleme = []
    if pct_chr >= plancher:
        motif_probleme.append(f"stress chronique {pct_chr:.1f}% (≥ {plancher:.0f}%)")
    if n_aigu >= 1:
        motif_probleme.append(f"{n_aigu} jour(s) de dépassement létal")
    if not motif_probleme:
        motif_probleme.append(f"stress chronique {pct_chr:.1f}% et aucune létalité")

    # --- Axe 2 : levier débit opérant ? ---
    dispo_rel = bool(relation and relation.get("disponible"))
    verdict = relation.get("verdict") if dispo_rel else None
    levier = (verdict == "etablie")
    motif_levier = relation.get("libelle", "test non réalisable") if dispo_rel \
        else "test non réalisable (débit absent ou données insuffisantes)"

    # --- Croisement ---
    if probleme and levier:
        case, cle = 1, "agir_debit"
        libelle = "Débit thermique pertinent"
        conduite = ("Le milieu présente un problème thermique ET le débit en est "
                    "un levier effectif : les débits de référence thermique sont "
                    "fondés et peuvent être portés en arbitrage.")
        couleur = "#C0392B"
    elif probleme and not levier:
        case, cle = 2, "autre_levier"
        libelle = "Problème réel, mais levier autre que le débit"
        conduite = ("Le problème thermique est avéré, mais la température ne "
                    "répond pas au débit. Agir sur l'hydrologie serait peu "
                    "efficace : orienter vers l'ombrage rivulaire, la "
                    "morphologie, la réduction des rejets thermiques ou les "
                    "apports de nappe. Les débits calculés restent indicatifs.")
        couleur = "#B9770D"
    elif (not probleme) and levier:
        case, cle = 3, "veille"
        libelle = "Pas d'enjeu thermique actuel, levier disponible"
        conduite = ("Aucun problème thermique constaté sur la chronique, alors "
                    "même que le débit influence la température. Il n'y a pas "
                    "lieu de fixer un objectif contraignant, mais le milieu "
                    "reste sensible à une baisse future des débits : situation "
                    "à surveiller (changement climatique, nouveaux prélèvements).")
        couleur = "#1E8449"
    else:
        case, cle = 4, "hors_champ"
        libelle = "Approche thermique peu opérante"
        conduite = ("Ni problème thermique constaté, ni lien entre débit et "
                    "température. L'approche « débits thermiques » n'apporte pas "
                    "d'élément de gestion sur cette station ; d'autres volets "
                    "de l'étude HMUC sont plus pertinents.")
        couleur = "#7F8C8D"

    return dict(case=case, cle=cle, libelle=libelle, conduite=conduite,
                couleur=couleur, probleme=probleme, levier=levier,
                motif_probleme=" · ".join(motif_probleme),
                motif_levier=motif_levier, plancher=plancher,
                pct_chr=pct_chr, n_aigu=n_aigu, verdict_relation=verdict)
