"""
mesure_validite_m.py — ÉTAPE 3, TÂCHE C : ce que la règle de validité écarterait.

MESURE SEULE. Rien n'est appliqué, aucun seuil n'est recommandé.

D21 étend la règle de validité aux DEUX coefficients avec le même critère.
L'asymétrie actuelle — borne `[0 ; 1,2]` sur `core.py:258` pour le saisonnier,
rien pour l'estival — n'est justifiée nulle part dans le code.

CE QUI EST ESTIMÉ, ET POURQUOI NEWEY-WEST
------------------------------------------
La pente est celle de `T_eau ~ T_air` sur la fenêtre du coefficient. L'écart-
type ordinaire de `stats.linregress` suppose des résidus indépendants. Ils ne
le sont pas : deux jours consécutifs d'une chronique thermique se ressemblent,
et l'autocorrélation gonfle mécaniquement la précision apparente. Des
écarts-types robustes à l'autocorrélation (Newey-West, HAC) corrigent cela ;
ils élargissent l'intervalle sans déplacer la pente.

Le décalage maximal retenu suit la règle usuelle de Newey-West,
`L = floor(4 (n/100)^(2/9))`, écrite ici plutôt qu'importée : elle ne vient
d'aucun projet, c'est la convention de la littérature.

CE QUI EST RESPECTÉ
-------------------
D15 : le seuil de 0,15 du projet clos n'est PAS importé. Il figure dans le
balayage comme repère, au même titre que les autres valeurs, et n'est jamais
retenu.

D3 : les données rejouées sont celles de la référence qui fait foi
(`tests/reference/`), donc le chemin de paramètres de l'application.

Sorties :
  out/etape3/validite_m_par_point.csv    pente, IC, R2, n, pour les deux coefficients
  out/etape3/validite_m_balayage.csv     combien de points sortent, par seuil
  out/etape3/validite_m_distribution.csv la distribution de la demi-largeur
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _commun import ICI, RACINE, decouvrir, ecrire_csv, nom_point, _f
from thermie_debits import io_data, core
from thermie_debits.config import CONTEXTES

OUT = RACINE / "out" / "etape3"

# Seuils balayés sur la demi-largeur d'IC à 95 %. Choisis pour couvrir la
# distribution observée, du très permissif au très strict. 0,15 y figure comme
# REPÈRE du projet clos, jamais comme valeur retenue (D15).
SEUILS = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00]
REPERE_PROJET_CLOS = 0.15

MOIS_ESTIVAUX = (6, 7, 8, 9)


def newey_west(x, y):
    """
    Pente OLS et demi-largeur d'IC à 95 % avec écarts-types HAC (Newey-West).

    Retourne (pente, intercept, demi_largeur, r2, n, lag). La pente est
    strictement celle de l'OLS — donc celle que V4.5 calcule
    (`stats.linregress`, `core.py:154`) : seul l'écart-type change.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(x)
    if n < 3 or np.ptp(x) == 0:
        return np.nan, np.nan, np.nan, np.nan, n, 0

    X = np.column_stack([np.ones(n), x])
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta
    sst = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - (resid ** 2).sum() / sst if sst > 0 else np.nan

    # Regle usuelle de Newey-West pour le decalage maximal.
    lag = int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))
    lag = max(lag, 0)

    u = X * resid[:, None]
    S = u.T @ u
    for l in range(1, lag + 1):
        w = 1.0 - l / (lag + 1.0)              # noyau de Bartlett
        G = u[l:].T @ u[:-l]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    se_pente = float(np.sqrt(max(V[1, 1], 0.0)))
    demi = 1.96 * se_pente
    return float(beta[1]), float(beta[0]), demi, float(r2), n, lag


def fenetres_fraie(contexte_key, espece_repere):
    """Mois de la fenêtre de reproduction, par espèce — la même règle que
    `core.analyse_fraie_croissance` (core.py:329-332)."""
    base = CONTEXTES[contexte_key]
    fraie = base.get("fraie") or {}
    if "especes" in base:
        esp = espece_repere or base.get("espece_defaut")
        fraie = {esp: fraie[esp]} if esp in fraie else {}
    return {esp: sorted({m for ph in pr["phases"] for m in ph["mois"]})
            for esp, pr in fraie.items()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import json

    lignes = []
    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((ICI / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        ctx_key = par["contexte_piscicole"]["valeur"]
        espece = par["espece_repere"]["valeur"]
        qc_par = {k: v["valeur"] for k, v in par["qc"].items()}
        an_par = {k: v["valeur"] for k, v in par["analyse"].items()}

        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        ecart, normales, _ = io_data.calculer_normales_ecarts(
            air, fenetre_lissage=an_par["normales_fenetre_lissage"],
            min_annees=an_par["normales_min_annees"], verbose=False)

        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            from thermie_debits import qc as qcmod
            qc_dict = {
                "bornes_physiques": qc_par["bornes_physiques"],
                "T_eau_min": qc_par["t_eau_min"], "T_eau_max": qc_par["t_eau_max"],
                "hors_eau": qc_par["hors_eau"],
                "hors_eau_ecart_seuil": qc_par["hors_eau_ecart_seuil"],
                "hors_eau_mois": list(qc_par["hors_eau_mois"]),
                "hors_eau_min_jours": qc_par["hors_eau_min_jours"],
                "hors_eau_exclut_saison": qc_par["hors_eau_exclut_saison"],
                "plateau": qc_par["plateau"],
                "plateau_fenetre": qc_par["plateau_fenetre"],
                "plateau_ecart_type_min": qc_par["plateau_ecart_type_min"],
                "mad_outliers": qc_par["mad_outliers"], "mad_k": qc_par["mad_k"],
                "mad_mois": qc_par["mad_mois"],
            }
            propre, _rap = qcmod.controle_qualite(daily, air, qc_dict, verbose=False)
            try:
                df = core.fusionner(
                    propre, air, ecart, normales, df_debits=None,
                    lissage_delta=an_par["normalisation_lissage_delta"])
            except ValueError as exc:
                lignes.append(dict(
                    jeu=j["jeu"], point=pt, coefficient="m_estival",
                    espece="", mois="6-7-8-9", n=0, pente=None, r2=None,
                    demi_largeur_ic95=None, lag_newey_west=None,
                    dans_0_1_2=None,
                    remarque=f"chaine interrompue : {type(exc).__name__}"))
                print(f"  · {j['jeu']}/{pt} : interrompu", flush=True)
                continue

            # --- m estival : exactement la fenetre de core.py:135 ---
            e = df[df["month"].isin(MOIS_ESTIVAUX)].dropna(
                subset=["T_eau_moy", "T_air"])
            p, _i, demi, r2, n, lag = newey_west(e["T_air"], e["T_eau_moy"])
            lignes.append(dict(
                jeu=j["jeu"], point=pt, coefficient="m_estival", espece="",
                mois="6-7-8-9", n=n, pente=_f(p), r2=_f(r2),
                demi_largeur_ic95=_f(demi), lag_newey_west=lag,
                dans_0_1_2=(None if not np.isfinite(p) else bool(0.0 <= p <= 1.2)),
                remarque=""))

            # --- m saisonnier : une par espece de la fenetre de fraie ---
            for esp, mois in fenetres_fraie(ctx_key, espece).items():
                s = df[df["month"].isin(mois)].dropna(
                    subset=["T_eau_moy", "T_air"])
                p, _i, demi, r2, n, lag = newey_west(s["T_air"], s["T_eau_moy"])
                lignes.append(dict(
                    jeu=j["jeu"], point=pt, coefficient="m_saisonnier",
                    espece=esp, mois="-".join(str(m) for m in mois),
                    n=n, pente=_f(p), r2=_f(r2), demi_largeur_ic95=_f(demi),
                    lag_newey_west=lag,
                    dans_0_1_2=(None if not np.isfinite(p) else bool(0.0 <= p <= 1.2)),
                    remarque=("repli sur m_estival applique par V4.5 "
                              "(core.py:251 ou 258)"
                              if (n < 20 or (np.isfinite(r2) and r2 < 0.30)
                                  or not (np.isfinite(p) and 0.0 <= p <= 1.2))
                              else "")))
            print(f"  · {j['jeu']}/{pt}", flush=True)

    ecrire_csv(OUT / "validite_m_par_point.csv",
               ["jeu", "point", "coefficient", "espece", "mois", "n", "pente",
                "r2", "demi_largeur_ic95", "lag_newey_west", "dans_0_1_2",
                "remarque"], lignes, tri=["coefficient", "jeu", "point", "espece"])

    t = pd.DataFrame(lignes)
    t["demi_largeur_ic95"] = pd.to_numeric(t["demi_largeur_ic95"], errors="coerce")

    # ---- C2 : distribution et balayage ----------------------------------
    distrib = []
    for coef, sub in t.groupby("coefficient"):
        v = sub["demi_largeur_ic95"].dropna()
        if not len(v):
            continue
        distrib.append(dict(
            coefficient=coef, n_estimations=int(len(v)),
            minimum=_f(float(v.min())), p10=_f(float(v.quantile(0.10))),
            q1=_f(float(v.quantile(0.25))), mediane=_f(float(v.median())),
            q3=_f(float(v.quantile(0.75))), p90=_f(float(v.quantile(0.90))),
            maximum=_f(float(v.max())),
            lag_median=_f(float(sub["lag_newey_west"].dropna().median()))))
    ecrire_csv(OUT / "validite_m_distribution.csv",
               ["coefficient", "n_estimations", "minimum", "p10", "q1",
                "mediane", "q3", "p90", "maximum", "lag_median"],
               distrib, tri=["coefficient"])

    balayage = []
    for coef, sub in t.groupby("coefficient"):
        v = sub.dropna(subset=["demi_largeur_ic95"])
        for s in SEUILS:
            sortis = v[v["demi_largeur_ic95"] > s]
            balayage.append(dict(
                coefficient=coef, seuil_demi_largeur_ic95=s,
                statut_du_seuil=("REPERE du projet clos, NON retenu (D15)"
                                 if s == REPERE_PROJET_CLOS else "balayage"),
                n_estimations=int(len(v)),
                n_sortent=int(len(sortis)),
                part_sortante_pct=_f(100.0 * len(sortis) / max(len(v), 1)),
                points_sortants=", ".join(sorted(set(sortis["point"])))[:400]))
    ecrire_csv(OUT / "validite_m_balayage.csv",
               ["coefficient", "seuil_demi_largeur_ic95", "statut_du_seuil",
                "n_estimations", "n_sortent", "part_sortante_pct",
                "points_sortants"], balayage,
               tri=["coefficient", "seuil_demi_largeur_ic95"])

    # ---- Restitution -----------------------------------------------------
    print("\n=== Distribution de la demi-largeur d'IC a 95 % (Newey-West) ===")
    for l in distrib:
        print(f"  {l['coefficient']:<14} n={l['n_estimations']:>3}  "
              f"min={l['minimum']:.4f}  q1={l['q1']:.4f}  med={l['mediane']:.4f}  "
              f"q3={l['q3']:.4f}  p90={l['p90']:.4f}  max={l['maximum']:.4f}  "
              f"lag median={l['lag_median']:.0f}")

    print("\n=== Balayage : combien de points sortiraient ===")
    for coef in sorted(set(l["coefficient"] for l in balayage)):
        print(f"  -- {coef}")
        for l in balayage:
            if l["coefficient"] != coef:
                continue
            marque = " (repere, non retenu)" if l["seuil_demi_largeur_ic95"] == REPERE_PROJET_CLOS else ""
            print(f"     seuil {l['seuil_demi_largeur_ic95']:<5} : "
                  f"{l['n_sortent']:>3} / {l['n_estimations']} sortent "
                  f"({l['part_sortante_pct']:>5.1f} %){marque}")

    print("\n=== C3 — BLE3-0 et la borne [0 ; 1,2] ===")
    b = t[(t["point"] == "BLE3-0")]
    for _, r in b.iterrows():
        print(f"  {r['coefficient']:<14} pente={r['pente']} r2={r['r2']} "
              f"n={r['n']} demi-IC={r['demi_largeur_ic95']} "
              f"dans [0;1.2] = {r['dans_0_1_2']}")
    hors = t[(t["dans_0_1_2"] == False)]
    print(f"\n  pentes hors [0 ; 1,2] : {len(hors)} estimation(s)")
    for _, r in hors.iterrows():
        print(f"     {r['point']:<32} {r['coefficient']:<14} pente={r['pente']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
