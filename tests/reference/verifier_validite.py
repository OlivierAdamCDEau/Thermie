"""
verifier_validite.py — ÉTAPE 4, TÂCHE C : vérifier la règle de validité (D27).

MESURE SEULE.

D27 déplace la règle : elle ne porte plus sur la LARGEUR de l'intervalle de
confiance — l'étape 3 a montré qu'aucun seuil de largeur ne sépare `BLE3-0` du
corpus — mais sur la SIGNIFICATIVITÉ de la pente, c'est-à-dire :

    l'IC95 de Newey-West exclut-il zéro ?

C'est un critère conventionnel, sans nombre à calibrer : il n'importe aucune
valeur d'un autre bassin (D15, contrainte 5).

C1 confirme le calcul amont sur `m_estival` et l'étend à `m_saisonnier`, par
espèce (D28).

C2 croise les trois critères en conjonction, et DÉRIVE un effectif minimal du
corpus au lieu d'en conventionner un. La dérivation :

    Pour chaque point dont la pente est significative sur sa chronique
    complète, on ré-estime la pente sur des FENÊTRES CONTIGUËS de longueur n'
    croissante — contiguës, pour préserver l'autocorrélation que Newey-West
    est là pour corriger ; un tirage aléatoire la détruirait et surestimerait
    la significativité. On mesure, pour chaque n', la part des fenêtres qui
    concluent encore « significatif ».

    L'effectif minimal est le plus petit n' à partir duquel cette part atteint
    le niveau de confiance déjà retenu par la règle, soit 95 %. En deçà, le
    test perd sa puissance SUR CE TYPE DE DONNÉES — et c'est le corpus qui le
    dit, pas une convention.

C3 lit dans le code ce que V4.5 rend possible en aval d'un rejet.

Sorties :
  out/etape4/validite_significativite.csv   C1
  out/etape4/validite_conjonction.csv       C2 — les trois criteres croises
  out/etape4/validite_effectif_minimal.csv  C2 — la derivation de n minimal
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from _commun import ICI, RACINE, decouvrir, ecrire_csv, nom_point, _f
from mesure_validite_m import newey_west, fenetres_fraie, MOIS_ESTIVAUX
from thermie_debits import io_data, core, qc as qcmod

OUT = RACINE / "out" / "etape4"

# Longueurs de fenêtre explorées pour la dérivation de l'effectif minimal.
TAILLES = [10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 150, 200]
NIVEAU = 0.95            # le meme que celui de l'IC : aucune convention nouvelle
PAS_FENETRE = 5          # decalage entre deux fenetres contigues successives


def series_du_point(jeu, point_rel, ctx):
    """(T_air, T_eau_moy) sur la fenêtre estivale, après le contrôle qualité
    du régime en service — exactement l'assiette sur laquelle V4.5 estime m."""
    daily = io_data.charger_eau(str(RACINE / point_rel),
                                nom=point_rel.split("/")[-1])
    propre, _ = qcmod.controle_qualite(daily, ctx["air"], ctx["qc_dict"],
                                       verbose=False)
    try:
        df = core.fusionner(propre, ctx["air"], ctx["ecart"], ctx["normales"],
                            df_debits=None,
                            lissage_delta=ctx["an"]["normalisation_lissage_delta"])
    except ValueError:
        return None
    return df


def significatif(x, y):
    """(pente, SE, t, IC95 exclut-il zero, r2, n)."""
    p, _i, demi, r2, n, lag = newey_west(x, y)
    if not np.isfinite(p) or not np.isfinite(demi) or demi == 0:
        return p, np.nan, np.nan, False, r2, n
    se = demi / 1.96
    t = p / se if se > 0 else np.nan
    exclut_zero = bool((p - demi) > 0 or (p + demi) < 0)
    return p, se, t, exclut_zero, r2, n


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lignes, effectifs = [], []

    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((ICI / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        qc = {k: v["valeur"] for k, v in par["qc"].items()}
        an = {k: v["valeur"] for k, v in par["analyse"].items()}
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        ecart, normales, _ = io_data.calculer_normales_ecarts(
            air, fenetre_lissage=an["normales_fenetre_lissage"],
            min_annees=an["normales_min_annees"], verbose=False)
        ctx = dict(air=air, ecart=ecart, normales=normales, an=an, qc_dict={
            "bornes_physiques": qc["bornes_physiques"],
            "T_eau_min": qc["t_eau_min"], "T_eau_max": qc["t_eau_max"],
            "hors_eau": qc["hors_eau"],
            "hors_eau_ecart_seuil": qc["hors_eau_ecart_seuil"],
            "hors_eau_mois": list(qc["hors_eau_mois"]),
            "hors_eau_min_jours": qc["hors_eau_min_jours"],
            "hors_eau_exclut_saison": qc["hors_eau_exclut_saison"],
            "plateau": qc["plateau"], "plateau_fenetre": qc["plateau_fenetre"],
            "plateau_ecart_type_min": qc["plateau_ecart_type_min"],
            "mad_outliers": qc["mad_outliers"], "mad_k": qc["mad_k"],
            "mad_mois": qc["mad_mois"]})
        ctx_key = par["contexte_piscicole"]["valeur"]
        espece = par["espece_repere"]["valeur"]

        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            df = series_du_point(j["jeu"], point_rel, ctx)
            if df is None:
                print(f"  · {j['jeu']}/{pt} : chaine interrompue", flush=True)
                continue

            fenetres = [("m_estival", "", list(MOIS_ESTIVAUX))]
            for esp, mois in fenetres_fraie(ctx_key, espece).items():
                fenetres.append(("m_saisonnier", esp, mois))

            for coef, esp, mois in fenetres:
                s = df[df["month"].isin(mois)].dropna(subset=["T_eau_moy", "T_air"])
                s = s.sort_values("date")
                p, se, t, exclut, r2, n = significatif(s["T_air"], s["T_eau_moy"])
                lignes.append(dict(
                    jeu=j["jeu"], point=pt, coefficient=coef, espece=esp,
                    mois="-".join(str(m) for m in mois), n=n, pente=_f(p),
                    erreur_type_newey_west=_f(se), t=_f(t), r2=_f(r2),
                    ic95_exclut_zero=bool(exclut),
                    pente_dans_0_1_2=bool(np.isfinite(p) and 0.0 <= p <= 1.2)))

                # --- derivation de l'effectif minimal, sur les points ---
                # significatifs et assez longs pour porter la mesure.
                if coef == "m_estival" and exclut and n >= max(TAILLES[0], 60):
                    x = s["T_air"].to_numpy()
                    y = s["T_eau_moy"].to_numpy()
                    for taille in TAILLES:
                        if taille > n:
                            break
                        ok = tot = 0
                        for deb in range(0, n - taille + 1, PAS_FENETRE):
                            _p, _se, _t, _ex, _r2, _n = significatif(
                                x[deb:deb + taille], y[deb:deb + taille])
                            tot += 1
                            ok += int(_ex)
                        if tot:
                            effectifs.append(dict(
                                point=pt, n_complet=n, taille_fenetre=taille,
                                n_fenetres=tot, n_significatives=ok,
                                part_significative=_f(ok / tot)))
            print(f"  · {j['jeu']}/{pt}", flush=True)

    ecrire_csv(OUT / "validite_significativite.csv",
               ["jeu", "point", "coefficient", "espece", "mois", "n", "pente",
                "erreur_type_newey_west", "t", "r2", "ic95_exclut_zero",
                "pente_dans_0_1_2"], lignes,
               tri=["coefficient", "jeu", "point", "espece"])

    t = pd.DataFrame(lignes)

    # ---------- C2 : les trois criteres croises ----------
    eff = pd.DataFrame(effectifs)
    if len(eff):
        agg = (eff.groupby("taille_fenetre")
               .agg(n_points=("point", "nunique"),
                    n_fenetres=("n_fenetres", "sum"),
                    n_significatives=("n_significatives", "sum")).reset_index())
        agg["part_significative"] = agg["n_significatives"] / agg["n_fenetres"]
        atteint = agg[agg["part_significative"] >= NIVEAU]
        n_min = int(atteint["taille_fenetre"].min()) if len(atteint) else None
        agg["atteint_le_niveau"] = agg["part_significative"] >= NIVEAU
        ecrire_csv(OUT / "validite_effectif_minimal.csv",
                   ["taille_fenetre", "n_points", "n_fenetres",
                    "n_significatives", "part_significative",
                    "atteint_le_niveau"],
                   [dict(taille_fenetre=int(r.taille_fenetre),
                         n_points=int(r.n_points), n_fenetres=int(r.n_fenetres),
                         n_significatives=int(r.n_significatives),
                         part_significative=_f(float(r.part_significative)),
                         atteint_le_niveau=bool(r.atteint_le_niveau))
                    for r in agg.itertuples()], tri=["taille_fenetre"])
    else:
        n_min = None

    croise = []
    for coef, sub in t.groupby("coefficient"):
        n = len(sub)
        c_sig = ~sub["ic95_exclut_zero"].astype(bool)
        c_dom = ~sub["pente_dans_0_1_2"].astype(bool)
        c_eff = sub["n"] < (n_min if n_min else 0)
        union = c_sig | c_dom | c_eff
        for libelle, masque in (
                ("IC95 contient zero (pente non significative)", c_sig),
                ("pente hors [0 ; 1,2]", c_dom),
                (f"effectif n < {n_min} (derive du corpus)", c_eff),
                ("UNION des trois", union)):
            pts = sorted(set(sub.loc[masque, "point"]
                             + np.where(sub.loc[masque, "espece"] != "",
                                        " [" + sub.loc[masque, "espece"] + "]", "")))
            croise.append(dict(
                coefficient=coef, critere=libelle, n_estimations=n,
                n_ecartees=int(masque.sum()),
                part_ecartee_pct=_f(100.0 * masque.mean()),
                estimations=", ".join(pts)[:400] or "aucune"))
    ecrire_csv(OUT / "validite_conjonction.csv",
               ["coefficient", "critere", "n_estimations", "n_ecartees",
                "part_ecartee_pct", "estimations"], croise,
               tri=["coefficient", "critere"])

    # ---------- Restitution ----------
    print("\n=== C1 — significativite de la pente ===")
    for coef, sub in t.groupby("coefficient"):
        ns = int((~sub["ic95_exclut_zero"].astype(bool)).sum())
        print(f"  {coef:<14} : {ns} estimation(s) sur {len(sub)} dont l'IC95 "
              f"CONTIENT zero")
        for _, r in sub[~sub["ic95_exclut_zero"].astype(bool)].iterrows():
            print(f"       {r['point']} {r['espece']} : m={r['pente']} "
                  f"t={r['t']} r2={r['r2']} n={r['n']}")
        v = sub[sub["ic95_exclut_zero"].astype(bool)]["t"].astype(float)
        if len(v):
            print(f"       t des significatives : min={v.min():.2f}, "
                  f"median={v.median():.2f}, max={v.max():.2f}")

    if n_min:
        print(f"\n=== C2 — effectif minimal DERIVE du corpus : n = {n_min} ===")
        for r in agg.itertuples():
            marque = "  <- premier a atteindre le niveau" if (
                r.atteint_le_niveau and int(r.taille_fenetre) == n_min) else ""
            print(f"     n'={int(r.taille_fenetre):>4} : "
                  f"{100*r.part_significative:>5.1f} % des "
                  f"{int(r.n_fenetres)} fenetres restent significatives{marque}")

    print("\n=== C2 — les trois criteres croises ===")
    for l in croise:
        print(f"  {l['coefficient']:<14} {l['critere']:<46} "
              f"{l['n_ecartees']:>2}/{l['n_estimations']} "
              f"({l['part_ecartee_pct']:>5.1f} %)  {l['estimations'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
