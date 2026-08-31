"""
instruire_r10_r11.py — ÉTAPE 5, TÂCHE D. Instruction seule, rien n'est implémenté.

R10 — LE FILTRE D'ÉPISODE
-------------------------
Deux questions, et la seconde révèle un défaut de ma mesure d'étape 4.

  (a) La table d'impact du §5 de la spécification a-t-elle été calculée avec
      ou sans le filtre d'épisode ? — SANS. `mesure_regime_service.py` applique
      un masque JOURNALIER (`masque_candidat`) et ne contient nulle part de
      `min_jours_episode`. La table d'impact chiffre donc le détecteur SANS
      regroupement en épisodes.

  (b) Pourquoi `conjonction_rampl_profils.csv` annonce-t-il une longueur
      d'épisode médiane de 4,0 jours quand les quatre jours retenus forment
      des épisodes de 2, 1 et 1 ? — PARCE QUE LA MESURE ÉTAIT FAUSSE.
      `mesure_conjonction_rampl.py` calculait les épisodes sur le masque du
      SOCLE, puis lisait cette longueur pour les lignes retenues par chaque
      règle. Le chiffre publié était donc la longueur de l'épisode du socle
      CONTENANT le jour, et non celle de l'épisode de la règle elle-même.
      Le présent module recalcule la longueur sur le masque de CHAQUE règle.

Puis : ce que `min_jours_episode` exclut réellement, marche par marche, pour
une gamme de valeurs.

R11 — L'EFFECTIF MINIMAL, PAR COEFFICIENT ET PAR ESPÈCE
--------------------------------------------------------
La dérivation d'étape 4 tournait sur les pentes ESTIVALES et sa valeur était
appliquée au coefficient saisonnier : c'est un transfert, pas une dérivation.
Elle est refaite ici séparément — `m_estival` sur juin-septembre,
`m_saisonnier` sur la fenêtre de reproduction de CHAQUE espèce.

Sorties :
  out/etape5/r10_episodes.csv        la longueur d'episode, recalculee
  out/etape5/r10_filtre_episode.csv  ce que min_jours_episode exclut
  out/etape5/r11_effectif_minimal.csv
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import ICI, RACINE, decouvrir, ecrire_csv, nom_point, _f
from mesure_critere_b import PLANCHER_MAD, MIN_JOURS_GROUPE, FACTEUR_MAD, K_VALEURS
from mesure_aveuglement import MOIS
from mesure_conjonction import socle, relativiser
from mesure_validite_m import newey_west, fenetres_fraie, MOIS_ESTIVAUX
from verifier_validite import significatif, series_du_point
from thermie_debits import io_data

OUT = RACINE / "out" / "etape5"

QUANTILE_AMPL_MIN = 0.10
VALEURS_MIN_EPISODE = [1, 2, 3, 4, 5]
K_RETENU = 3.0                     # le defaut de la specification

# R11
TAILLES = [10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 150, 200]
NIVEAU = 0.95
PAS_FENETRE = 5


# ============================================================
# R10
# ============================================================
def episodes_du_masque(sub, masque):
    """
    Longueur de l'épisode CALENDAIRE auquel chaque jour marqué appartient,
    calculée sur le masque passé — et non sur un autre.
    """
    s = sub.sort_values("date_dt")
    m = masque.reindex(s.index).fillna(False).to_numpy()
    jours = (s["date_dt"] - s["date_dt"].iloc[0]).dt.days.to_numpy()
    longueur = np.zeros(len(s), dtype=int)
    i = 0
    while i < len(s):
        if not m[i]:
            i += 1
            continue
        j = i + 1
        while j < len(s) and m[j] and jours[j] - jours[j - 1] == 1:
            j += 1
        longueur[i:j] = j - i
        i = j
    return pd.Series(longueur, index=s.index).reindex(sub.index)


def r10():
    print("R10 — construction du socle...", flush=True)
    d = socle()
    mins = []
    for j in decouvrir():
        if not j["air"]:
            continue
        for p in j["points"]:
            dd = io_data.charger_eau(str(RACINE / p),
                                     nom=p.split("/")[-1]).assign(point=nom_point(p))
            mins.append(dd[["point", "date", "T_eau_min"]])
    d = d.merge(pd.concat(mins, ignore_index=True), on=["point", "date"], how="left")
    d["ampl_air"] = d["TX"] - d["TN"]
    seuils = {jeu: float(s["ampl_air"].dropna().quantile(QUANTILE_AMPL_MIN))
              for jeu, s in d.groupby("jeu")}
    d["ok_ampl"] = d["ampl_air"] >= d["jeu"].map(seuils)
    d["R_ampl"] = np.where(d["ok_ampl"],
                           (d["T_eau_max"] - d["T_eau_min"])
                           / d["ampl_air"].replace(0, np.nan), np.nan)
    for c in ("E_moy", "E_max", "R_ampl"):
        d = relativiser(d, c)
    dd = d[d["E_moy_diag"] & d["E_max_diag"] & d["R_ampl_diag"]].copy()

    k = K_RETENU
    dd["marche1"] = dd["E_moy_rel"] > k
    dd["marche2"] = (dd["R_ampl_rel"] > k) & (dd["E_max_rel"] > k)

    # --- (b) la longueur d'episode, recalculee sur le BON masque ---
    lignes = []
    for nom_regle, col in (("marche 1 — socle relatif", "marche1"),
                           ("marche 2 — conjonction R_ampl ET E_max", "marche2")):
        longueurs = []
        for pt, sub in dd.groupby("point"):
            ep = episodes_du_masque(sub, sub[col])
            longueurs.append(ep[sub[col]])
        v = pd.concat(longueurs) if longueurs else pd.Series(dtype=int)
        # comparaison avec la mesure fautive d'etape 4 : episodes du SOCLE
        faux = []
        for pt, sub in dd.groupby("point"):
            ep = episodes_du_masque(sub, sub["marche1"])
            faux.append(ep[sub[col]])
        vf = pd.concat(faux) if faux else pd.Series(dtype=int)
        lignes.append(dict(
            k=k, regle=nom_regle, jours_marques=int(len(v)),
            episodes=int(sum(1 for _, s in dd.groupby("point")
                             for _ in _bornes(s, s[col]))),
            longueur_episode_mediane_CORRIGEE=_f(float(v.median()) if len(v) else np.nan),
            longueur_episode_max_CORRIGEE=int(v.max()) if len(v) else 0,
            longueur_episode_mediane_ETAPE4_FAUSSE=_f(
                float(vf.median()) if len(vf) else np.nan),
            explication=("l'etape 4 lisait la longueur de l'episode du SOCLE "
                         "contenant le jour, pas celle de l'episode de la regle")))
    ecrire_csv(OUT / "r10_episodes.csv",
               ["k", "regle", "jours_marques", "episodes",
                "longueur_episode_mediane_CORRIGEE",
                "longueur_episode_max_CORRIGEE",
                "longueur_episode_mediane_ETAPE4_FAUSSE", "explication"],
               lignes, tri=["k", "regle"])

    # --- ce que min_jours_episode exclut, marche par marche ---
    filtre = []
    for nom_regle, col in (("marche 1 — socle relatif", "marche1"),
                           ("marche 2 — conjonction R_ampl ET E_max", "marche2")):
        eps = []
        for pt, sub in dd.groupby("point"):
            for a, b in _bornes(sub, sub[col]):
                eps.append(dict(point=pt, longueur=b - a))
        e = pd.DataFrame(eps)
        n_j = int(dd[col].sum())
        n_p = int(dd.groupby("point")[col].any().sum())
        for v in VALEURS_MIN_EPISODE:
            gardes = e[e["longueur"] >= v] if len(e) else e
            j_gardes = int(gardes["longueur"].sum()) if len(gardes) else 0
            filtre.append(dict(
                regle=nom_regle, min_jours_episode=v,
                episodes_total=int(len(e)),
                episodes_gardes=int(len(gardes)),
                jours_marques_sans_filtre=n_j,
                jours_gardes=j_gardes,
                jours_exclus_par_le_filtre=n_j - j_gardes,
                part_exclue_pct=_f(100.0 * (n_j - j_gardes) / max(n_j, 1)),
                points_sans_filtre=n_p,
                points_gardes=int(gardes["point"].nunique()) if len(gardes) else 0))
    ecrire_csv(OUT / "r10_filtre_episode.csv",
               ["regle", "min_jours_episode", "episodes_total",
                "episodes_gardes", "jours_marques_sans_filtre", "jours_gardes",
                "jours_exclus_par_le_filtre", "part_exclue_pct",
                "points_sans_filtre", "points_gardes"],
               filtre, tri=["regle", "min_jours_episode"])

    print("\n=== R10 (b) — longueur d'episode, corrigee ===")
    for l in lignes:
        print(f"  {l['regle']:<42} jours={l['jours_marques']:>4} "
              f"episodes={l['episodes']:>4} "
              f"mediane CORRIGEE={l['longueur_episode_mediane_CORRIGEE']} "
              f"(etape 4 annoncait {l['longueur_episode_mediane_ETAPE4_FAUSSE']})")
    print("\n=== R10 — ce que min_jours_episode exclut ===")
    for l in filtre:
        print(f"  {l['regle']:<42} min={l['min_jours_episode']} : "
              f"{l['episodes_gardes']:>4}/{l['episodes_total']:<4} episodes, "
              f"{l['jours_gardes']:>4}/{l['jours_marques_sans_filtre']:<4} jours "
              f"({l['part_exclue_pct']:>5.1f} % exclus), "
              f"{l['points_gardes']}/{l['points_sans_filtre']} points")
    return dd


def _bornes(sub, masque):
    s = sub.sort_values("date_dt")
    m = masque.reindex(s.index).fillna(False).to_numpy()
    jours = (s["date_dt"] - s["date_dt"].iloc[0]).dt.days.to_numpy()
    i = 0
    while i < len(s):
        if not m[i]:
            i += 1
            continue
        j = i + 1
        while j < len(s) and m[j] and jours[j] - jours[j - 1] == 1:
            j += 1
        yield i, j
        i = j


# ============================================================
# R11
# ============================================================
def r11():
    print("\nR11 — derivation separee de n_min...", flush=True)
    brut = []
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
        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            df = series_du_point(j["jeu"], point_rel, ctx)
            if df is None:
                continue
            fen = [("m_estival", "", list(MOIS_ESTIVAUX))]
            for esp, mois in fenetres_fraie(par["contexte_piscicole"]["valeur"],
                                            par["espece_repere"]["valeur"]).items():
                fen.append(("m_saisonnier", esp, mois))
            for coef, esp, mois in fen:
                s = (df[df["month"].isin(mois)]
                     .dropna(subset=["T_eau_moy", "T_air"]).sort_values("date"))
                p, se, t, exclut, r2, n = significatif(s["T_air"], s["T_eau_moy"])
                if not exclut or n < 60:
                    continue
                x, y = s["T_air"].to_numpy(), s["T_eau_moy"].to_numpy()
                for taille in TAILLES:
                    if taille > n:
                        break
                    ok = tot = 0
                    for deb in range(0, n - taille + 1, PAS_FENETRE):
                        *_, ex, _r, _n = significatif(x[deb:deb + taille],
                                                      y[deb:deb + taille])
                        tot += 1
                        ok += int(ex)
                    brut.append(dict(coefficient=coef, espece=esp, point=pt,
                                     taille=taille, tot=tot, ok=ok))
            print(f"  · {j['jeu']}/{pt}", flush=True)

    t = pd.DataFrame(brut)
    lignes, resume = [], []
    groupes = ([("m_estival", "")]
               + sorted({(c, e) for c, e in zip(t["coefficient"], t["espece"])
                         if c == "m_saisonnier"}))
    for coef, esp in groupes:
        sub = t[(t["coefficient"] == coef) & (t["espece"] == esp)]
        if not len(sub):
            continue
        agg = sub.groupby("taille").agg(pts=("point", "nunique"),
                                        tot=("tot", "sum"),
                                        ok=("ok", "sum")).reset_index()
        agg["part"] = agg["ok"] / agg["tot"]
        atteint = agg[agg["part"] >= NIVEAU]
        n_min = int(atteint["taille"].min()) if len(atteint) else None
        for r in agg.itertuples():
            lignes.append(dict(
                coefficient=coef, espece=esp, taille_fenetre=int(r.taille),
                n_points=int(r.pts), n_fenetres=int(r.tot),
                n_significatives=int(r.ok), part_significative=_f(float(r.part)),
                atteint_le_niveau=bool(r.part >= NIVEAU)))
        resume.append(dict(coefficient=coef, espece=esp,
                           n_points_supports=int(sub["point"].nunique()),
                           n_min_derive=n_min,
                           n_min_etape4_transfere=60,
                           ecart=(n_min - 60) if n_min else None))
    ecrire_csv(OUT / "r11_effectif_minimal.csv",
               ["coefficient", "espece", "taille_fenetre", "n_points",
                "n_fenetres", "n_significatives", "part_significative",
                "atteint_le_niveau"], lignes,
               tri=["coefficient", "espece", "taille_fenetre"])
    ecrire_csv(OUT / "r11_resume.csv",
               ["coefficient", "espece", "n_points_supports", "n_min_derive",
                "n_min_etape4_transfere", "ecart"], resume,
               tri=["coefficient", "espece"])

    print("\n=== R11 — n_min derive separement ===")
    for r in resume:
        print(f"  {r['coefficient']:<14} {r['espece'] or '(estival)':<16} "
              f"supports={r['n_points_supports']:>2}  "
              f"n_min DERIVE={r['n_min_derive']}  "
              f"(etape 4 transferait 60, ecart {r['ecart']:+})"
              if r["n_min_derive"] else
              f"  {r['coefficient']:<14} {r['espece']:<16} "
              f"n_min NON DERIVABLE — aucune fenetre n'atteint le niveau")
    return resume


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    r10()
    r11()
    return 0


if __name__ == "__main__":
    sys.exit(main())
