"""
mesure_d55_discordance.py — ÉTAPE 9, TÂCHE D : instruire D55.

AUCUN CODE DE DÉTECTION N'EST ÉCRIT. Cette mesure alimente le correctif 1.

LA QUESTION
------------
La marche 2 exige `R_ampl_rel > k` **ET** `E_max_rel > k` — une forme ET un
niveau. D55 maintient la conjonction STRICTE pour l'exclusion, et pose qu'une
journée dont un membre dépasse quand l'autre ne dépasse pas doit être
**signalée sans être exclue**.

Le cas qui motive la décision est le 28 juillet 2015 sur `BIE40-3` :
`R_ampl_rel = 8,51` — un signal de forme massif — retenu par un `E_max_rel` de
2,77. `BIE40-3` est par ailleurs le point que le `MANIFESTE.md` du projet clos
place sous réserve d'implantation.

CE QUI EST MESURÉ
------------------
D1  Combien de journées ont un membre au-dessus de `k` et l'autre au-dessous,
    réparties selon lequel des deux dépasse, avec la distribution de l'écart
    entre les deux membres.
D2  Combien seraient signalées sans être exclues selon D55, et sur quels
    points elles se concentrent.
D3  Ces journées ressemblent-elles aux journées exclues par la conjonction,
    ou aux journées ordinaires ?

AUCUN SEUIL NOUVEAU (D55). La comparaison se fait au même `k` = 3,0. Le mot
« largement » de D55 n'est pas traduit par un nombre inventé : la
**distribution** de l'écart entre les deux membres est donnée, pour que la
décision d'un éventuel sous-critère se prenne sur des chiffres.

LES GRANDEURS DE COMPARAISON DE D3, ET POURQUOI CELLES-LÀ
-----------------------------------------------------------
Comparer les journées discordantes aux exclues sur `R_ampl_rel` ou
`E_max_rel` serait circulaire : ce sont les deux membres qui définissent les
groupes. Les grandeurs retenues sont donc extérieures à la règle :

  · `E_moy_rel` — le critère de la MARCHE 1, témoin indépendant du même
    phénomène. C'est la grandeur la plus informative : si les discordantes
    ressemblaient aux exclues, la marche 1 devrait aussi les voir monter.
  · `ampl_air` (`TX − TN`) — c'est par elle que l'étape 4 a départagé les deux
    conjonctions candidates : la mauvaise sélectionnait les journées de faible
    amplitude d'air, profil de l'artefact. Le vocabulaire est déjà établi.
  · `R_ampl` BRUT, non relativisé — dit si la forme est anormale dans l'absolu
    ou seulement par rapport au mois du point.
  · `T_eau_max − T_air` — la grandeur du détecteur EN SERVICE, qui permet de
    situer les journées par rapport au régime qu'on remplace.
  · la part de journées également marquées par la MARCHE 1, et le mois.

Sorties :
  out/etape9/D1_discordance_par_point.csv
  out/etape9/D1_distribution_ecart.csv
  out/etape9/D2_journees_signalees.csv
  out/etape9/D3_profils_compares.csv
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from _commun import ICI, RACINE, decouvrir, ecrire_csv, nom_point, _f
from thermie_debits import io_data
from mesure_regime_service import ajouter_relatifs, masque_hors_eau
from mesure_conjonction import relativiser
from mesure_marche2 import lire_air_complet

OUT = RACINE / "out" / "etape9"

K = 3.0
QUANTILE_AMPL_MIN = 0.10


def profil(sub, nom, n_total):
    """Le profil d'un groupe de journées, sur les grandeurs de D3."""
    def q(col, f="median"):
        s = sub[col].dropna()
        if not len(s):
            return None
        return _f(float(getattr(s, f)()))
    return dict(
        groupe=nom, n_journees=int(len(sub)),
        part_du_corpus_pct=_f(100.0 * len(sub) / max(n_total, 1)),
        E_moy_rel_median=q("ecart_rel_B"),
        E_moy_rel_p90=_f(float(sub["ecart_rel_B"].dropna().quantile(0.90))
                         if sub["ecart_rel_B"].notna().any() else np.nan),
        part_marquee_marche1_pct=_f(100.0 * float(sub["marche1"].mean())
                                    if len(sub) else np.nan),
        ampl_air_mediane=q("ampl_air"),
        R_ampl_brut_median=q("R_ampl"),
        ecart_T_eau_max_T_air_median=q("ecart"),
        mois_median=q("month"),
        part_juillet_aout_pct=_f(
            100.0 * float(sub["month"].isin([7, 8]).mean()) if len(sub) else np.nan))


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    blocs = []
    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((ICI / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        an = {k: v["valeur"] for k, v in par["analyse"].items()}
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        air_complet = lire_air_complet(str(RACINE / j["air"]))
        tntx = [c for c in ["date", "TN", "TX"] if c in air_complet.columns]
        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            d = daily.merge(air, on="date", how="left")
            d = d.merge(air_complet[tntx], on="date", how="left")
            d["date_dt"] = pd.to_datetime(d["date"])
            d["month"] = d["date_dt"].dt.month
            d["year"] = d["date_dt"].dt.year
            d = d.sort_values("date_dt").reset_index(drop=True)
            d["jeu"], d["point"] = j["jeu"], pt
            blocs.append(d)
    s = pd.concat(blocs, ignore_index=True)
    s = ajouter_relatifs(s)

    s["E_max"] = s["T_eau_max"] - s["TX"]
    s["ampl_eau"] = s["T_eau_max"] - s["T_eau_min"]
    s["ampl_air"] = s["TX"] - s["TN"]
    seuils = {jeu: float(sub["ampl_air"].dropna().quantile(QUANTILE_AMPL_MIN))
              for jeu, sub in s.groupby("jeu")
              if sub["ampl_air"].notna().any()}
    s["seuil_ampl"] = s["jeu"].map(seuils)
    s["R_ampl"] = np.where(s["ampl_air"] >= s["seuil_ampl"],
                           s["ampl_eau"] / s["ampl_air"].replace(0, np.nan),
                           np.nan)
    s = relativiser(s, "E_max")
    s = relativiser(s, "R_ampl")

    # Les deux membres, et le domaine ou la marche 2 sait se prononcer.
    s["marche1"] = s["_jjas"] & (s["ecart_rel_B"] > K).fillna(False)
    diag = (s["_jjas"] & s["R_ampl_diag"].fillna(False)
            & s["E_max_diag"].fillna(False)
            & s["R_ampl_rel"].notna() & s["E_max_rel"].notna())
    s["diagnosticable_m2"] = diag
    haut_r = (s["R_ampl_rel"] > K).fillna(False)
    haut_e = (s["E_max_rel"] > K).fillna(False)
    s["exclue"] = diag & haut_r & haut_e
    s["disc_forme"] = diag & haut_r & ~haut_e     # la forme depasse, pas le niveau
    s["disc_niveau"] = diag & ~haut_r & haut_e    # le niveau depasse, pas la forme
    s["discordante"] = s["disc_forme"] | s["disc_niveau"]
    s["ordinaire"] = diag & ~haut_r & ~haut_e
    s["ecart_membres"] = (s["R_ampl_rel"] - s["E_max_rel"]).abs()

    n_diag = int(diag.sum())
    print(f"  {len(s)} points-jours ; {n_diag} diagnosticables par la marche 2")

    # ---------- D1 : par point ----------
    lignes = []
    for (jeu, pt), d in s.groupby(["jeu", "point"]):
        lignes.append(dict(
            jeu=jeu, point=pt,
            journees_diagnosticables_m2=int(d["diagnosticable_m2"].sum()),
            exclues_par_la_conjonction=int(d["exclue"].sum()),
            discordantes_total=int(d["discordante"].sum()),
            discordantes_forme_seule=int(d["disc_forme"].sum()),
            discordantes_niveau_seul=int(d["disc_niveau"].sum()),
            ordinaires=int(d["ordinaire"].sum()),
            ecart_membres_median_discordantes=_f(
                float(d.loc[d["discordante"], "ecart_membres"].median())
                if d["discordante"].any() else np.nan),
            ecart_membres_max_discordantes=_f(
                float(d.loc[d["discordante"], "ecart_membres"].max())
                if d["discordante"].any() else np.nan)))
    ecrire_csv(OUT / "D1_discordance_par_point.csv",
               ["jeu", "point", "journees_diagnosticables_m2",
                "exclues_par_la_conjonction", "discordantes_total",
                "discordantes_forme_seule", "discordantes_niveau_seul",
                "ordinaires", "ecart_membres_median_discordantes",
                "ecart_membres_max_discordantes"],
               lignes, tri=["jeu", "point"])

    # ---------- D1 : distribution de l'ecart entre les deux membres ----------
    dist = []
    for nom, masque in (("forme au-dessus, niveau au-dessous", s["disc_forme"]),
                        ("niveau au-dessus, forme au-dessous", s["disc_niveau"]),
                        ("les deux au-dessus (exclues)", s["exclue"])):
        v = s.loc[masque, "ecart_membres"].dropna()
        if not len(v):
            dist.append(dict(groupe=nom, n=0))
            continue
        dist.append(dict(
            groupe=nom, n=int(len(v)),
            ecart_min=_f(float(v.min())), ecart_q25=_f(float(v.quantile(.25))),
            ecart_median=_f(float(v.median())),
            ecart_q75=_f(float(v.quantile(.75))),
            ecart_q90=_f(float(v.quantile(.90))),
            ecart_max=_f(float(v.max())),
            membre_haut_median=_f(float(
                s.loc[masque, ["R_ampl_rel", "E_max_rel"]].max(axis=1).median())),
            membre_bas_median=_f(float(
                s.loc[masque, ["R_ampl_rel", "E_max_rel"]].min(axis=1).median()))))
    ecrire_csv(OUT / "D1_distribution_ecart.csv",
               ["groupe", "n", "ecart_min", "ecart_q25", "ecart_median",
                "ecart_q75", "ecart_q90", "ecart_max", "membre_haut_median",
                "membre_bas_median"],
               dist, tri=["groupe"])

    # ---------- D2 : les journees signalees ----------
    sig = s[s["discordante"]].copy()
    sig = sig.sort_values(["point", "date"])
    lignes2 = []
    for _, r in sig.iterrows():
        lignes2.append(dict(
            jeu=r["jeu"], point=r["point"], date=str(r["date"]),
            membre_qui_depasse=("forme (R_ampl)" if r["disc_forme"]
                                else "niveau (E_max)"),
            R_ampl_rel=_f(r["R_ampl_rel"]), E_max_rel=_f(r["E_max_rel"]),
            ecart_entre_membres=_f(r["ecart_membres"]),
            E_moy_rel=_f(r["ecart_rel_B"]),
            marquee_par_la_marche1=("oui" if r["marche1"] else "non"),
            ampl_air=_f(r["ampl_air"]), R_ampl_brut=_f(r["R_ampl"]),
            T_eau_max_moins_T_air=_f(r["ecart"])))
    ecrire_csv(OUT / "D2_journees_signalees.csv",
               ["jeu", "point", "date", "membre_qui_depasse", "R_ampl_rel",
                "E_max_rel", "ecart_entre_membres", "E_moy_rel",
                "marquee_par_la_marche1", "ampl_air", "R_ampl_brut",
                "T_eau_max_moins_T_air"],
               lignes2, tri=["point", "date"])

    # ---------- D3 : les profils compares ----------
    profils = [
        profil(s[s["exclue"]], "exclues par la conjonction", n_diag),
        profil(s[s["disc_forme"]], "discordantes — forme seule", n_diag),
        profil(s[s["disc_niveau"]], "discordantes — niveau seul", n_diag),
        profil(s[s["ordinaire"]], "ordinaires (aucun membre au-dessus)", n_diag),
    ]
    ecrire_csv(OUT / "D3_profils_compares.csv",
               ["groupe", "n_journees", "part_du_corpus_pct",
                "E_moy_rel_median", "E_moy_rel_p90",
                "part_marquee_marche1_pct", "ampl_air_mediane",
                "R_ampl_brut_median", "ecart_T_eau_max_T_air_median",
                "mois_median", "part_juillet_aout_pct"],
               profils, tri=["groupe"])

    print("\n=== D1 — LA DISCORDANCE ===")
    print(f"  journees diagnosticables par la marche 2 : {n_diag}")
    print(f"  exclues (les deux membres au-dessus de k={K}) : "
          f"{int(s['exclue'].sum())}")
    print(f"  DISCORDANTES (un seul membre au-dessus)      : "
          f"{int(s['discordante'].sum())}")
    print(f"     dont la FORME depasse seule  : {int(s['disc_forme'].sum())}")
    print(f"     dont le NIVEAU depasse seul  : {int(s['disc_niveau'].sum())}")
    print(f"  ordinaires (aucun membre au-dessus)          : "
          f"{int(s['ordinaire'].sum())}")
    print("\n  distribution de l'ecart entre les deux membres :")
    for d in dist:
        if not d.get("n"):
            continue
        print(f"    {d['groupe']:<38} n={d['n']:>4}  median={d['ecart_median']:>6.2f}  "
              f"q90={d['ecart_q90']:>6.2f}  max={d['ecart_max']:>6.2f}")
    print(f"\n=== D2 — {len(lignes2)} journee(s) signalee(s) sans etre exclues ===")
    par_pt = pd.Series([l["point"] for l in lignes2]).value_counts()
    print(f"  reparties sur {len(par_pt)} point(s) ; les plus concernes :")
    for pt, n in par_pt.head(8).items():
        print(f"    {pt:<32} {n}")
    print("\n=== D3 — LES PROFILS ===")
    for p in profils:
        print(f"  {p['groupe']:<38} n={p['n_journees']:>5}  "
              f"E_moy_rel med={p['E_moy_rel_median']}  "
              f"marche1={p['part_marquee_marche1_pct']} %  "
              f"ampl_air={p['ampl_air_mediane']}  "
              f"R_ampl={p['R_ampl_brut_median']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
