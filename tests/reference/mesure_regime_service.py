"""
mesure_regime_service.py — ÉTAPE 4, TÂCHE A.

MESURE SEULE. Aucun code applicatif n'est modifié.

CE QUE CETTE MESURE CORRIGE
---------------------------
Les §1 et §2 de l'étape 3 opposaient les critères relatifs au détecteur à
4 °C avec exclusion de saison — le régime `tests/reference_cli/`, qui marque
3 408 jours. Ce n'est pas le détecteur à remplacer. D25 pose que le régime de
calibration est celui EN SERVICE : seuil 10 °C, SANS exclusion de saison.

La comparaison est donc rejouée contre lui, et les conclusions changent de
sens : contre 3 408 jours un critère relatif paraît sévère ; contre le régime
en service, qui ne marque presque rien, tous les réglages testés marquent
DAVANTAGE.

LE DÉTECTEUR EN SERVICE, REPRODUIT À LA LETTRE (qc.py:60-79)
-------------------------------------------------------------
Un jour est marqué si TOUTES ces conditions sont réunies :
    - il tombe dans la fenêtre `hors_eau_mois` = (6, 7, 8, 9) ;
    - `T_eau_max − T_air > 10 °C` (seuil de l'application, app.py:162-163) ;
    - `T_air` est renseignée ;
    - ET SON ANNÉE compte au moins `hors_eau_min_jours` = 5 jours suspects.

Cette dernière condition — une grille par ANNÉE, pas par jour — est facile à
oublier et change le résultat. Elle est reproduite ici.

Les trois autres détecteurs (bornes physiques, plateau, MAD) sont reproduits
eux aussi, à l'identique, et restent INCHANGÉS d'un scénario à l'autre : seul
le détecteur de mise hors d'eau est remplacé par le critère candidat. C'est la
seule façon d'attribuer l'écart au changement de détecteur et non au reste.

A3 — L'IMPACT SUR m ET SUR T_norm
----------------------------------
Changer les journées écartées change `m`, donc `T_norm`. Pour chaque candidat,
la chaîne est rejouée jusqu'au bout — `core.fusionner`, puis la pente sur
juin-septembre (`core.py:154`), puis `Tmh_norm = Tmh − m × Delta_TMm_liss`
(`core.py:177`) — et l'écart au régime en service est chiffré.

Sorties :
  out/etape4/regime_service_table.csv      A1/A2, la table par reglage
  out/etape4/regime_service_par_point.csv  A1, le detail par point
  out/etape4/impact_m_tnorm.csv            A3, l'impact sur m et T_norm
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from scipy import stats

from _commun import ICI, RACINE, decouvrir, ecrire_csv, nom_point, _f
from mesure_critere_b import PLANCHER_MAD, MIN_JOURS_GROUPE, FACTEUR_MAD, K_VALEURS
from mesure_aveuglement import QUANTILES
from thermie_debits import io_data, core

OUT = RACINE / "out" / "etape4"
MOIS_JJAS = (6, 7, 8, 9)


# ============================================================
# Les détecteurs de V4.5, reproduits masque par masque
# ============================================================
def masques_qc(df: pd.DataFrame, qc: dict):
    """
    Reproduit qc.controle_qualite (qc.py:40-99) en rendant chaque détecteur
    séparément, au lieu de les fusionner dans un drapeau unique.

    L'union est identique à celle de V4.5 : `_marque` pose le drapeau sur
    TOUT le masque (qc.py:35), l'ordre ne change donc que les motifs.
    """
    m = {}
    if qc["bornes_physiques"]:
        m["bornes"] = ((df["T_eau_moy"] < qc["t_eau_min"])
                       | (df["T_eau_moy"] > qc["t_eau_max"])
                       | (df["T_eau_max"] > qc["t_eau_max"]))
    else:
        m["bornes"] = pd.Series(False, index=df.index)

    if qc["plateau"]:
        w = qc["plateau_fenetre"]
        roll = df["T_eau_moy"].rolling(window=w, center=True, min_periods=w).std()
        m["plateau"] = (roll < qc["plateau_ecart_type_min"]).fillna(False)
    else:
        m["plateau"] = pd.Series(False, index=df.index)

    if qc["mad_outliers"]:
        base = df if not qc["mad_mois"] else df[df["month"].isin(qc["mad_mois"])]
        med = base["T_eau_moy"].median()
        mad = (base["T_eau_moy"] - med).abs().median()
        if mad > 0:
            s = qc["mad_k"] * mad
            mm = (df["T_eau_moy"] - med).abs() > s
            if qc["mad_mois"]:
                mm = mm & df["month"].isin(qc["mad_mois"])
            m["mad"] = mm
        else:
            m["mad"] = pd.Series(False, index=df.index)
    else:
        m["mad"] = pd.Series(False, index=df.index)
    return m


def masque_hors_eau(df: pd.DataFrame, seuil: float, min_j: int,
                    exclut_saison: bool, mois=MOIS_JJAS):
    """Le détecteur de mise hors d'eau, exactement qc.py:60-79."""
    ecart = df["T_eau_max"] - df["T_air"]
    susp = df["month"].isin(mois) & (ecart > seuil) & df["T_air"].notna()
    out = pd.Series(False, index=df.index)
    for yr, sub in df[df["month"].isin(mois)].groupby("year"):
        e = sub["T_eau_max"] - sub["T_air"]
        if int(((e > seuil) & sub["T_air"].notna()).sum()) >= min_j:
            if exclut_saison:
                out |= (df["year"] == yr) & df["month"].isin(mois)
            else:
                out |= (df["year"] == yr) & susp
    return out


# ============================================================
# Les critères relatifs, calibrés sur le corpus
# ============================================================
def ajouter_relatifs(d: pd.DataFrame):
    """ecart, sa version centrée (A) et sa version normalisée (B)."""
    d = d.copy()
    d["ecart"] = d["T_eau_max"] - d["T_air"]
    jjas = d["month"].isin(MOIS_JJAS) & d["T_air"].notna() & d["ecart"].notna()
    d["_jjas"] = jjas
    g = d[jjas].groupby(["point", "month"])["ecart"]
    ref = g.median().rename("ecart_ref")
    taille = g.size().rename("n_groupe")
    d = d.merge(ref, left_on=["point", "month"], right_index=True, how="left")
    d = d.merge(taille, left_on=["point", "month"], right_index=True, how="left")
    d["ecart_centre"] = d["ecart"] - d["ecart_ref"]
    mad = (d[jjas].assign(_a=(d.loc[jjas, "ecart"] - d.loc[jjas, "ecart_ref"]).abs())
           .groupby(["point", "month"])["_a"].median().rename("mad") * FACTEUR_MAD)
    d = d.merge(mad, left_on=["point", "month"], right_index=True, how="left")
    d["diag_B"] = (d["mad"] > PLANCHER_MAD) & (d["n_groupe"] >= MIN_JOURS_GROUPE)
    d["ecart_rel_B"] = np.where(d["diag_B"] & jjas,
                                d["ecart_centre"] / d["mad"].replace(0, np.nan),
                                np.nan)
    return d


# ============================================================
# Rejeu de la chaîne pour un jeu de journées écartées
# ============================================================
def rejouer(daily, air, ecart_air, normales, exclues, lissage_delta):
    """
    Reconstruit `propre` sans les journées `exclues`, puis rejoue
    core.fusionner et la régression de sensibilité. Retourne le dict des
    grandeurs, ou None si la chaîne s'interrompt.
    """
    propre = daily[~daily["date"].isin(exclues)].copy()
    propre = propre[["date", "T_eau_moy", "T_eau_max", "T_eau_min", "n_mesures"]]
    try:
        df = core.fusionner(propre, air, ecart_air, normales, df_debits=None,
                            lissage_delta=lissage_delta)
    except ValueError as exc:
        return dict(statut=f"chaine interrompue : {exc.args[0][:70]}")
    e = df[df["month"].isin(MOIS_JJAS)].dropna(subset=["T_eau_moy", "T_air"])
    if len(e) < 10:
        return dict(statut=f"regression impossible : {len(e)} jour(s) estivaux")
    m, ic, r, p, _ = stats.linregress(e["T_air"].values, e["T_eau_moy"].values)
    _delta = df["Delta_TMm_liss"] if "Delta_TMm_liss" in df else df["Delta_TMm"]
    tmh_norm = df["Tmh"] - m * _delta
    ete = df["month"].isin(MOIS_JJAS)
    v = tmh_norm[ete].dropna()
    return dict(statut="OK", m=float(m), r2=float(r ** 2), n_ete=int(len(e)),
                n_retenues=int(len(df)),
                tmh_norm_mediane=float(v.median()) if len(v) else np.nan,
                tmh_norm_p95=float(v.quantile(0.95)) if len(v) else np.nan,
                tmh_norm_max=float(v.max()) if len(v) else np.nan)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------- 1. Le socle, point par point ----------
    blocs, contextes = [], {}
    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((ICI / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        qc = {k: v["valeur"] for k, v in par["qc"].items()}
        an = {k: v["valeur"] for k, v in par["analyse"].items()}
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        ecart_air, normales, _ = io_data.calculer_normales_ecarts(
            air, fenetre_lissage=an["normales_fenetre_lissage"],
            min_annees=an["normales_min_annees"], verbose=False)
        contextes[j["jeu"]] = dict(qc=qc, an=an, air=air,
                                   ecart_air=ecart_air, normales=normales)
        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            d = daily.merge(air, on="date", how="left")
            d["date_dt"] = pd.to_datetime(d["date"])
            d["month"] = d["date_dt"].dt.month
            d["year"] = d["date_dt"].dt.year
            d = d.sort_values("date_dt").reset_index(drop=True)
            d["jeu"] = j["jeu"]
            d["point"] = pt
            blocs.append(d)
            print(f"  · {j['jeu']}/{pt} : {len(d)} journees", flush=True)
    socle = pd.concat(blocs, ignore_index=True)
    socle = ajouter_relatifs(socle)

    # ---------- 2. Les scenarios ----------
    # Le detecteur EN SERVICE est la colonne de reference (D25).
    scenarios = [("REGIME EN SERVICE — T_eau_max - TM > 10 degC, sans exclusion "
                  "de saison, grille annuelle a 5 jours (qc.py:60-79)", "service")]
    # Seuils poolés du critère A, calibrés sur la fenêtre JJAS du corpus.
    jj = socle[socle["_jjas"]]
    seuils_A = {q: float(jj["ecart_centre"].quantile(q)) for q in QUANTILES}
    for q in QUANTILES:
        scenarios.append((f"A poole, q={q} (seuil {seuils_A[q]:.3f} degC)", ("A", q)))
    for k in K_VALEURS:
        scenarios.append((f"B dispersion propre, k={k} MAD*", ("B", k)))
    # Reference documentaire : le regime CLI, pour memoire (jamais la cible).
    scenarios.append(("REGIME CLI (documentaire) — 4 degC avec exclusion de "
                      "saison", "cli"))

    def masque_candidat(d, spec):
        if spec == "service":
            return masque_hors_eau(d, 10.0, 5, False)
        if spec == "cli":
            return masque_hors_eau(d, 4.0, 5, True)
        genre, val = spec
        if genre == "A":
            return d["_jjas"] & (d["ecart_centre"] > seuils_A[val])
        return d["_jjas"] & (d["ecart_rel_B"] > val).fillna(False)

    # ---------- 3. Table par reglage et par point ----------
    lignes, par_point, impacts = [], [], []
    ref_par_point = {}

    for libelle, spec in scenarios:
        tot = dict(jours=0, points=set(), jours_ref=0, points_ref=set(),
                   deux=0, perdus=0, gagnes=0)
        for (jeu, pt), d in socle.groupby(["jeu", "point"]):
            ctx = contextes[jeu]
            ref = masque_hors_eau(d, 10.0, 5, False)
            cand = masque_candidat(d, spec)
            tot["jours"] += int(cand.sum())
            tot["jours_ref"] += int(ref.sum())
            tot["deux"] += int((ref & cand).sum())
            tot["perdus"] += int((ref & ~cand).sum())
            tot["gagnes"] += int((~ref & cand).sum())
            if cand.any():
                tot["points"].add(pt)
            if ref.any():
                tot["points_ref"].add(pt)
            par_point.append(dict(
                reglage=libelle, jeu=jeu, point=pt, n_journees=int(len(d)),
                jours_regime_service=int(ref.sum()),
                jours_du_reglage=int(cand.sum()),
                jours_communs=int((ref & cand).sum()),
                jours_perdus_vs_service=int((ref & ~cand).sum()),
                jours_gagnes_vs_service=int((~ref & cand).sum())))

            # ---- A3 : impact sur m et T_norm ----
            autres = masques_qc(d, ctx["qc"])
            flag = autres["bornes"] | autres["plateau"] | autres["mad"] | cand
            exclues = set(d.loc[flag, "date"])
            res = rejouer(d, ctx["air"], ctx["ecart_air"], ctx["normales"],
                          exclues, ctx["an"]["normalisation_lissage_delta"])
            enr = dict(reglage=libelle, jeu=jeu, point=pt,
                       journees_ecartees_total=int(flag.sum()),
                       journees_ecartees_hors_eau=int(cand.sum()), **res)
            if spec == "service":
                ref_par_point[pt] = res
            else:
                r = ref_par_point.get(pt, {})
                for cle in ("m", "tmh_norm_mediane", "tmh_norm_p95",
                            "n_ete", "n_retenues"):
                    a, b = res.get(cle), r.get(cle)
                    enr[f"ecart_{cle}"] = (a - b if isinstance(a, (int, float))
                                           and isinstance(b, (int, float))
                                           else None)
            impacts.append(enr)

        n_ref, n_cand = tot["jours_ref"], tot["jours"]
        lignes.append(dict(
            reglage=libelle,
            jours_regime_service=n_ref, jours_du_reglage=n_cand,
            rapport_au_regime_service=(_f(n_cand / n_ref) if n_ref else None),
            ordre_de_grandeur=_ordre(n_cand, n_ref),
            jours_communs=tot["deux"],
            jours_perdus_vs_service=tot["perdus"],
            jours_gagnes_vs_service=tot["gagnes"],
            points_regime_service=len(tot["points_ref"]),
            points_du_reglage=len(tot["points"]),
            points_perdus_vs_service=len(tot["points_ref"] - tot["points"]),
            liste_points_perdus=", ".join(sorted(tot["points_ref"] - tot["points"])) or "aucun"))
        print(f"  {libelle[:56]:<56} jours={n_cand:>5} (service={n_ref}) "
              f"pts={len(tot['points']):>2}", flush=True)

    ecrire_csv(OUT / "regime_service_table.csv",
               ["reglage", "jours_regime_service", "jours_du_reglage",
                "rapport_au_regime_service", "ordre_de_grandeur",
                "jours_communs", "jours_perdus_vs_service",
                "jours_gagnes_vs_service", "points_regime_service",
                "points_du_reglage", "points_perdus_vs_service",
                "liste_points_perdus"], lignes, tri=["reglage"])
    ecrire_csv(OUT / "regime_service_par_point.csv",
               ["reglage", "jeu", "point", "n_journees", "jours_regime_service",
                "jours_du_reglage", "jours_communs", "jours_perdus_vs_service",
                "jours_gagnes_vs_service"], par_point,
               tri=["reglage", "jeu", "point"])

    cols_i = ["reglage", "jeu", "point", "statut", "journees_ecartees_total",
              "journees_ecartees_hors_eau", "n_retenues", "n_ete", "m", "r2",
              "tmh_norm_mediane", "tmh_norm_p95", "tmh_norm_max",
              "ecart_m", "ecart_tmh_norm_mediane", "ecart_tmh_norm_p95",
              "ecart_n_ete", "ecart_n_retenues"]
    for l in impacts:
        for c in cols_i:
            if c in l and isinstance(l[c], float):
                l[c] = _f(l[c])
    ecrire_csv(OUT / "impact_m_tnorm.csv", cols_i, impacts,
               tri=["reglage", "jeu", "point"])
    return 0


def _ordre(n, ref):
    if ref == 0:
        return "le regime en service ne marque rien : rapport indefini"
    r = n / ref
    if r >= 100:
        return f"x{r:.0f} — DEUX ORDRES DE GRANDEUR DE PLUS"
    if r >= 10:
        return f"x{r:.0f} — un ordre de grandeur de plus"
    if r > 1.5:
        return f"x{r:.1f} — plus"
    if r >= 0.67:
        return f"x{r:.2f} — comparable"
    return f"x{r:.2f} — MOINS"


if __name__ == "__main__":
    sys.exit(main())
