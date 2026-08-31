"""
mesure_conjonction_rampl.py — ÉTAPE 4, TÂCHE B, second membre correct.

POURQUOI CETTE SECONDE MESURE
------------------------------
La conjonction demandée par D26 — écart à la MOYENNE d'air ET écart au MAXIMUM
d'air — a été mesurée par `mesure_conjonction.py`. Elle se comporte à l'envers
de son intention, et la raison est mécanique :

    E_max = T_eau_max − TX  et  E_moy = T_eau_max − TM

diffèrent exactement de `TX − TM`, c'est-à-dire de la moitié de l'amplitude
diurne de l'air. Quand cette amplitude est FAIBLE, les deux écarts se
confondent et franchissent leur seuil ensemble ; quand elle est FORTE, `E_max`
reste loin derrière et la conjonction échoue. **La conjonction sélectionne donc
les journées de faible amplitude d'air** — précisément le profil que
`thermie_points` identifie comme fabriquant des faux positifs
(`qualite.py`, `AMPL_AIR_MIN = 6 °C`).

Or ce n'est pas la conjonction de `thermie_points`. La sienne oppose deux
signatures DIFFÉRENTES (`criteres.py`, CANDIDATS) :

    R_ampl = (T_eau_max − T_eau_min) / (TX − TN)      une forme
    E_max_rel = E_max − médiane_{point,mois}(E_max)   un niveau

C'est cette conjonction-là qui est mesurée ici, transposée à ce que V4.5
possède : `T_eau_min` et `T_eau_max` existent déjà (`io_data.py:102-103`) ;
`TX` et `TN` sont lus par le harnais. Le garde-fou d'amplitude d'air est
repris parce qu'il conditionne le SENS du rapport, pas parce qu'il vient du
projet clos : un rapport dont le dénominateur tend vers zéro n'a pas de valeur
à comparer.

Le seuil de 6 °C est en revanche une valeur du bassin de la Bienne. Il n'est
PAS importé (D15) : le garde-fou est ici dérivé du jeu traité — quantile de
l'amplitude d'air du jeu — et le 6 °C ne figure que comme repère.

Sorties :
  out/etape4/conjonction_rampl_table.csv
  out/etape4/conjonction_rampl_profils.csv
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f
from mesure_critere_b import PLANCHER_MAD, MIN_JOURS_GROUPE, FACTEUR_MAD, K_VALEURS
from mesure_aveuglement import MOIS
from mesure_conjonction import socle, relativiser, episodes

OUT = RACINE / "out" / "etape4"

# Garde-fou d'amplitude d'air : quantile de l'amplitude du JEU TRAITE, et non
# une valeur de bassin. Le 6 degC de thermie_points est un repere.
QUANTILE_AMPL_MIN = 0.10
REPERE_BIENNE = 6.0

# Seuils explores pour R_ampl relativise, en MAD* comme le reste.
K_RAMPL = K_VALEURS


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Construction du socle...", flush=True)
    d = socle()
    d["T_eau_min"] = np.nan          # complete ci-dessous
    # socle() ne rapporte pas T_eau_min : on le recharge.
    from thermie_debits import io_data
    mins = []
    for j in decouvrir():
        if not j["air"]:
            continue
        for point_rel in j["points"]:
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            daily = daily.assign(point=nom_point(point_rel))
            mins.append(daily[["point", "date", "T_eau_min"]])
    d = d.drop(columns=["T_eau_min"]).merge(
        pd.concat(mins, ignore_index=True), on=["point", "date"], how="left")

    d["ampl_eau"] = d["T_eau_max"] - d["T_eau_min"]
    d["ampl_air"] = d["TX"] - d["TN"]

    # Garde-fou derive du jeu traite.
    seuils_ampl = {}
    for jeu, sub in d.groupby("jeu"):
        s = float(sub["ampl_air"].dropna().quantile(QUANTILE_AMPL_MIN))
        seuils_ampl[jeu] = s
        print(f"  garde-fou d'amplitude d'air, {jeu} : "
              f"quantile {QUANTILE_AMPL_MIN:.0%} = {s:.2f} degC "
              f"(repere Bienne : {REPERE_BIENNE} degC)")
    d["seuil_ampl"] = d["jeu"].map(seuils_ampl)
    d["diagnosticable_ampl"] = d["ampl_air"] >= d["seuil_ampl"]
    d["R_ampl"] = np.where(d["diagnosticable_ampl"],
                           d["ampl_eau"] / d["ampl_air"].replace(0, np.nan),
                           np.nan)

    d = relativiser(d, "E_moy")
    d = relativiser(d, "E_max")
    d = relativiser(d, "R_ampl")

    dd = d[d["E_moy_diag"] & d["E_max_diag"] & d["R_ampl_diag"]].copy()
    print(f"\n{len(d)} points-jours ; {len(dd)} diagnosticables par les trois "
          f"({100*len(dd)/max(len(d),1):.1f} %).")

    lignes, profils = [], []
    for k in K_RAMPL:
        dd[f"socle_{k}"] = dd["E_moy_rel"] > k
        dd[f"rampl_{k}"] = dd["R_ampl_rel"] > k
        dd[f"emax_{k}"] = dd["E_max_rel"] > k
        dd[f"conj_tp_{k}"] = dd[f"rampl_{k}"] & dd[f"emax_{k}"]     # thermie_points
        dd[f"conj_dm_{k}"] = dd[f"socle_{k}"] & dd[f"emax_{k}"]     # D26

        for libelle, col in (
                ("socle seul : E_moy relativise", f"socle_{k}"),
                ("D26 : E_moy ET E_max", f"conj_dm_{k}"),
                ("thermie_points : R_ampl ET E_max", f"conj_tp_{k}"),
                ("R_ampl relativise seul", f"rampl_{k}")):
            lignes.append(dict(
                k=k, regle=libelle, jours_marques=int(dd[col].sum()),
                points_marques=int(dd.groupby("point")[col].any().sum())))

        # profil des jours marques, par regle
        dd[f"_ep_{k}"] = pd.concat(
            [episodes(s, f"socle_{k}") for _, s in dd.groupby("point")])
        for libelle, col in (("socle seul", f"socle_{k}"),
                             ("D26 : E_moy ET E_max", f"conj_dm_{k}"),
                             ("thermie_points : R_ampl ET E_max", f"conj_tp_{k}")):
            sel = dd[dd[col]]
            if not len(sel):
                continue
            sync = sel.groupby(["jeu", "date_dt"]).size()
            profils.append(dict(
                k=k, regle=libelle, n_jours=int(len(sel)),
                amplitude_air_mediane=_f(float(sel["ampl_air"].median())),
                part_amplitude_air_sous_repere_pct=_f(
                    100.0 * float((sel["ampl_air"] < REPERE_BIENNE).mean())),
                R_ampl_median=_f(float(sel["R_ampl"].median())),
                longueur_episode_mediane=_f(float(sel[f"_ep_{k}"].median())),
                synchronisation_max=int(sync.max()) if len(sync) else 0,
                dates_avec_5_points_et_plus=int((sync >= 5).sum()) if len(sync) else 0))

    ecrire_csv(OUT / "conjonction_rampl_table.csv",
               ["k", "regle", "jours_marques", "points_marques"],
               lignes, tri=["k", "regle"])
    ecrire_csv(OUT / "conjonction_rampl_profils.csv",
               ["k", "regle", "n_jours", "amplitude_air_mediane",
                "part_amplitude_air_sous_repere_pct", "R_ampl_median",
                "longueur_episode_mediane", "synchronisation_max",
                "dates_avec_5_points_et_plus"], profils, tri=["k", "regle"])

    print("\n=== Les trois regles, cote a cote ===")
    for l in lignes:
        print(f"  k={l['k']:<4} {l['regle']:<38} jours={l['jours_marques']:>5} "
              f"points={l['points_marques']:>2}")
    print("\n=== Profil des jours marques (l'artefact de faible amplitude) ===")
    for l in profils:
        print(f"  k={l['k']:<4} {l['regle']:<36} n={l['n_jours']:>4} "
              f"| ampl air med={l['amplitude_air_mediane']:>5.2f} degC "
              f"(sous {REPERE_BIENNE} : {l['part_amplitude_air_sous_repere_pct']:>5.1f} %) "
              f"| R_ampl med={l['R_ampl_median']:>5.2f} "
              f"| episode med={l['longueur_episode_mediane']:>4.1f} j "
              f"| sync max={l['synchronisation_max']:>2} "
              f"| dates a 5+ pts={l['dates_avec_5_points_et_plus']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
