"""
mesure_suppressions.py — ÉTAPE 7, TÂCHES B1 et B2.

MESURE AVANT CORRECTION. Les deux suppressions disparaissent en tant que
suppressions dès que les correctifs sont posés : elles deviennent des
marquages. On les compte donc pendant qu'elles suppriment encore.

B1 — LA JOINTURE (registre C6)
-------------------------------
`core.fusionner` ouvre par une jointure INTERNE :

    df = daily_eau_propre.merge(df_air, on="date", how="inner")

puis, quelques lignes plus bas :

    df = df.dropna(subset=["T_eau_moy", "T_air"])

Ces deux lignes effacent des journées d'eau LUES ET RETENUES par le contrôle
qualité, sans trace, sans motif et sans compte. Trois causes distinctes s'y
mêlent, et les distinguer est tout l'objet de la mesure :

  1. aucune ligne d'air à cette date — la station d'air ne couvre pas le jour ;
  2. une ligne d'air existe, mais `T_air` y est vide ;
  3. `T_eau_moy` est vide alors que la journée a été retenue par le QC.

Les causes 1 et 2 sont le défaut C6. La cause 3, si elle existe, est autre
chose et ne doit pas être rangée sous le même motif.

Pour chaque point : combien, quelle part, comment elles se distribuent dans le
temps, et si elles se concentrent. Une chronique d'eau dont un tiers disparaît
parce que la station d'air a une lacune est un cas que l'écran doit dire.

B2 — LA DENSITÉ (D45)
----------------------
Les journées que le correctif 2 laisse sans `Tmh`, faute d'assez de jours
observés dans leur fenêtre calendaire. Par point, par date, avec le nombre de
jours réellement observés dans la fenêtre.

Sortie :
  out/etape7/B1_jointure_par_point.csv
  out/etape7/B1_jointure_par_annee.csv
  out/etape7/B1_jointure_journees.csv
  out/etape7/B2_densite_journees.csv
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import ICI, RACINE, decouvrir, ecrire_csv, nom_point, _f
from thermie_debits import io_data, core, qc as qcmod

OUT = RACINE / "out" / "etape7"

FENETRE_TMH = 7
MIN_PERIODS_TMH = 4


def qc_dict(par):
    q = {k: v["valeur"] for k, v in par["qc"].items()}
    return {"bornes_physiques": q["bornes_physiques"],
            "T_eau_min": q["t_eau_min"], "T_eau_max": q["t_eau_max"],
            "hors_eau": q["hors_eau"],
            "hors_eau_ecart_seuil": q["hors_eau_ecart_seuil"],
            "hors_eau_mois": list(q["hors_eau_mois"]),
            "hors_eau_min_jours": q["hors_eau_min_jours"],
            "hors_eau_exclut_saison": q["hors_eau_exclut_saison"],
            "plateau": q["plateau"], "plateau_fenetre": q["plateau_fenetre"],
            "plateau_ecart_type_min": q["plateau_ecart_type_min"],
            "mad_outliers": q["mad_outliers"], "mad_k": q["mad_k"],
            "mad_mois": q["mad_mois"]}


def plus_longue_serie(dates):
    """La plus longue suite de journées CALENDAIREMENT consécutives."""
    if len(dates) == 0:
        return 0
    d = pd.to_datetime(pd.Series(sorted(dates))).reset_index(drop=True)
    jours = (d - d.iloc[0]).dt.days.to_numpy()
    meilleur = courant = 1
    for i in range(1, len(jours)):
        courant = courant + 1 if jours[i] == jours[i - 1] + 1 else 1
        meilleur = max(meilleur, courant)
    return int(meilleur)


def densite_fenetre(dates):
    """Nombre de jours observés dans la fenêtre calendaire centrée de 7 jours."""
    d = pd.to_datetime(pd.Series(dates).to_numpy())
    s = pd.Series(1.0, index=d)
    plein = s.reindex(pd.date_range(d.min(), d.max(), freq="D"))
    dens = plein.rolling(window=FENETRE_TMH, center=True, min_periods=1).count()
    return dens.reindex(d).to_numpy()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    par_point, par_annee, journees, densite = [], [], [], []

    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((ICI / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        an = {k: v["valeur"] for k, v in par["analyse"].items()}
        lissage = an["normalisation_lissage_delta"]
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        ecart, normales, _ = io_data.calculer_normales_ecarts(
            air, fenetre_lissage=an["normales_fenetre_lissage"],
            min_annees=an["normales_min_annees"], verbose=False)
        qd = qc_dict(par)
        dates_air = set(pd.to_datetime(pd.Series(air["date"])).dt.date)

        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            propre, _rap = qcmod.controle_qualite(daily, air, qd, verbose=False)
            if not len(propre):
                continue

            # ---------- B1 : ce que la jointure interne efface
            p = propre.copy()
            p["date_dt"] = pd.to_datetime(p["date"])
            # la jointure gauche donne exactement ce que l'interne aurait vu,
            # plus ce qu'elle aurait efface.
            g = p.merge(air, on="date", how="left")
            sans_ligne_air = ~pd.Series(
                [d.date() in dates_air for d in p["date_dt"]]).to_numpy()
            air_vide = (g["T_air"].isna().to_numpy() & ~sans_ligne_air)
            eau_vide = g["T_eau_moy"].isna().to_numpy()
            efface = sans_ligne_air | air_vide | eau_vide
            n = len(p)

            annees = pd.to_datetime(pd.Series(p["date"])).dt.year.to_numpy()
            mois = pd.to_datetime(pd.Series(p["date"])).dt.month.to_numpy()
            d_eff = p["date"].to_numpy()[efface]

            # concentration : part de l'effacement portee par l'annee la pire
            if efface.any():
                cnt = pd.Series(annees[efface]).value_counts()
                pire_annee = int(cnt.index[0])
                part_pire = _f(100.0 * cnt.iloc[0] / efface.sum())
                mois_cnt = pd.Series(mois[efface]).value_counts()
                pire_mois = int(mois_cnt.index[0])
            else:
                pire_annee, part_pire, pire_mois = 0, 0.0, 0

            par_point.append(dict(
                jeu=j["jeu"], point=pt,
                journees_retenues_par_qc=n,
                effacees_par_la_jointure=int(efface.sum()),
                part_effacee_pct=_f(100.0 * efface.sum() / max(n, 1)),
                cause_aucune_ligne_air=int(sans_ligne_air.sum()),
                cause_T_air_vide=int(air_vide.sum()),
                cause_T_eau_moy_vide=int(eau_vide.sum()),
                plus_longue_serie_effacee_j=plus_longue_serie(d_eff),
                annee_la_plus_touchee=pire_annee,
                part_de_l_effacement_sur_cette_annee_pct=part_pire,
                mois_le_plus_touche=pire_mois,
                annees_entierement_effacees=int(sum(
                    1 for a in set(annees.tolist())
                    if efface[annees == a].all()))))

            for a in sorted(set(annees.tolist())):
                m = annees == a
                if not efface[m].any():
                    continue
                par_annee.append(dict(
                    jeu=j["jeu"], point=pt, annee=int(a),
                    journees_retenues_par_qc=int(m.sum()),
                    effacees=int(efface[m].sum()),
                    part_pct=_f(100.0 * efface[m].sum() / max(m.sum(), 1)),
                    annee_entierement_effacee="oui" if efface[m].all() else "non"))

            for i in np.nonzero(efface)[0]:
                cause = ("aucune ligne d'air" if sans_ligne_air[i]
                         else "T_air vide" if air_vide[i] else "T_eau_moy vide")
                journees.append(dict(
                    jeu=j["jeu"], point=pt, date=str(p["date"].iloc[i]),
                    cause=cause,
                    T_eau_moy=_f(float(g["T_eau_moy"].iloc[i])
                                 if pd.notna(g["T_eau_moy"].iloc[i]) else np.nan)))

            # ---------- B2 : les journees sans Tmh, faute de densite
            try:
                df = core.fusionner(propre, air, ecart, normales,
                                    df_debits=None, lissage_delta=lissage)
            except ValueError:
                print(f"  · {j['jeu']}/{pt} : {int(efface.sum())}/{n} effacees "
                      f"— chaine interrompue ensuite", flush=True)
                continue
            df = df.sort_values("date").reset_index(drop=True)
            manque = df["Tmh"].isna().to_numpy()
            if manque.any():
                dens = densite_fenetre(df["date"])
                for i in np.nonzero(manque)[0]:
                    densite.append(dict(
                        jeu=j["jeu"], point=pt, date=str(df["date"].iloc[i]),
                        jours_observes_dans_la_fenetre=int(dens[i]),
                        min_periods_exige=MIN_PERIODS_TMH,
                        T_eau_moy=_f(float(df["T_eau_moy"].iloc[i]))))
            print(f"  · {j['jeu']}/{pt} : {int(efface.sum())}/{n} effacees par "
                  f"la jointure, {int(manque.sum())} sans Tmh", flush=True)

    ecrire_csv(OUT / "B1_jointure_par_point.csv",
               ["jeu", "point", "journees_retenues_par_qc",
                "effacees_par_la_jointure", "part_effacee_pct",
                "cause_aucune_ligne_air", "cause_T_air_vide",
                "cause_T_eau_moy_vide", "plus_longue_serie_effacee_j",
                "annee_la_plus_touchee",
                "part_de_l_effacement_sur_cette_annee_pct",
                "mois_le_plus_touche", "annees_entierement_effacees"],
               par_point, tri=["jeu", "point"])
    ecrire_csv(OUT / "B1_jointure_par_annee.csv",
               ["jeu", "point", "annee", "journees_retenues_par_qc",
                "effacees", "part_pct", "annee_entierement_effacee"],
               par_annee, tri=["jeu", "point", "annee"])
    ecrire_csv(OUT / "B1_jointure_journees.csv",
               ["jeu", "point", "date", "cause", "T_eau_moy"],
               journees, tri=["jeu", "point", "date"])
    ecrire_csv(OUT / "B2_densite_journees.csv",
               ["jeu", "point", "date", "jours_observes_dans_la_fenetre",
                "min_periods_exige", "T_eau_moy"],
               densite, tri=["jeu", "point", "date"])

    tot_q = sum(l["journees_retenues_par_qc"] for l in par_point)
    tot_e = sum(l["effacees_par_la_jointure"] for l in par_point)
    print("\n=== B1 — LA JOINTURE INTERNE ===")
    print(f"  {len(par_point)} points, {tot_q} journees retenues par le QC")
    print(f"  effacees sans trace par la jointure : {tot_e} "
          f"({100*tot_e/max(tot_q,1):.2f} %)")
    print(f"    dont aucune ligne d'air : "
          f"{sum(l['cause_aucune_ligne_air'] for l in par_point)}")
    print(f"    dont T_air vide         : "
          f"{sum(l['cause_T_air_vide'] for l in par_point)}")
    print(f"    dont T_eau_moy vide     : "
          f"{sum(l['cause_T_eau_moy_vide'] for l in par_point)}")
    print(f"  points concernes : "
          f"{sum(1 for l in par_point if l['effacees_par_la_jointure'] > 0)}")
    pires = sorted(par_point, key=lambda l: -l["part_effacee_pct"])[:6]
    print("  les plus touches :")
    for l in pires:
        if l["effacees_par_la_jointure"] == 0:
            continue
        print(f"    {l['point']:<32} {l['effacees_par_la_jointure']:>5} / "
              f"{l['journees_retenues_par_qc']:>5} ({l['part_effacee_pct']:.2f} %), "
              f"serie la plus longue {l['plus_longue_serie_effacee_j']} j, "
              f"{l['annees_entierement_effacees']} annee(s) entierement effacee(s)")
    print(f"\n=== B2 — LA DENSITE ===")
    print(f"  journees sans Tmh : {len(densite)}")
    print(f"  points concernes  : {len(set(d['point'] for d in densite))}")
    if densite:
        mini = min(d["jours_observes_dans_la_fenetre"] for d in densite)
        print(f"  jours observes dans la fenetre : de {mini} a "
              f"{max(d['jours_observes_dans_la_fenetre'] for d in densite)} "
              f"(exige : {MIN_PERIODS_TMH})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
