"""
mesure_index_positionnel.py — ÉTAPE 6, TÂCHE C1.

MESURE AVANT CORRECTION. Elle ne sera plus possible après : une fois la série
réindexée sur un calendrier continu, aucune fenêtre n'enjambe plus rien.

LE DÉFAUT (registre C1)
------------------------
`core.fusionner` applique ses moyennes mobiles sur un index POSITIONNEL :

    core.py:111   Tmh             = T_eau_moy.rolling(7,  min_periods=4, center=True)
    core.py:121   Delta_TMm_liss  = Delta_TMm.rolling(N,  min_periods=1, center=True)

La série journalière ne contient que les jours PRÉSENTS. Une fenêtre de sept
LIGNES n'est une fenêtre de sept JOURS que si la série est continue. Quand
elle ne l'est pas, la fenêtre enjambe la lacune et moyenne des valeurs
séparées de plusieurs mois.

CE QUI EST MESURÉ, ET CE QUI NE L'EST PAS
------------------------------------------
Pour chaque point, sur la chronique telle que `core.fusionner` la construit :

  · le nombre de fenêtres qui ENJAMBENT une lacune — c'est-à-dire dont
    l'empan calendaire dépasse l'empan positionnel ;
  · la plus longue lacune enjambée ;
  · le nombre de journées de `T_norm` qui en dépendent — une journée en dépend
    si la fenêtre de `Tmh` OU celle de `Delta_TMm_liss` enjambe une lacune,
    puisque `Tmh_norm = Tmh − m × Delta_TMm_liss` ;
  · l'écart de valeur, en recalculant les deux versions côte à côte.

Le calcul de l'écart est fait ICI, dans le harnais, sans toucher au code
applicatif : on relit la série produite par `core.fusionner` et l'on refait
les deux moyennes mobiles, positionnelle et calendaire.

Sortie :
  out/etape6/C1_index_positionnel.csv          par point
  out/etape6/C1_index_positionnel_journees.csv les journees affectees
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

OUT = RACINE / "out" / "etape6"

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


def enjambement(dates: pd.Series, fenetre: int):
    """
    Pour chaque position i, l'empan CALENDAIRE de sa fenêtre positionnelle
    centrée, et la plus longue lacune qu'elle contient.

    Une fenêtre de `fenetre` lignes centrée en i couvre les positions
    [i − demi, i + demi]. Si l'empan calendaire de ces lignes dépasse
    `fenetre − 1` jours, la fenêtre enjambe au moins une lacune.
    """
    d = pd.to_datetime(pd.Series(dates)).reset_index(drop=True)
    n = len(d)
    demi = fenetre // 2
    jours = (d - d.iloc[0]).dt.days.to_numpy()
    ecarts = np.diff(jours, prepend=jours[0])          # ecart au precedent
    empan = np.zeros(n, dtype=int)
    lacune = np.zeros(n, dtype=int)
    for i in range(n):
        a, b = max(0, i - demi), min(n - 1, i + demi)
        empan[i] = jours[b] - jours[a]
        # la plus longue lacune INTERNE a la fenetre
        lacune[i] = int(ecarts[a + 1:b + 1].max() - 1) if b > a else 0
    return empan, lacune, (empan > (fenetre - 1))


def rolling_calendaire(dates, valeurs, fenetre, min_periods):
    """La même moyenne mobile, sur un calendrier journalier continu."""
    s = pd.Series(np.asarray(valeurs, dtype=float),
                  index=pd.to_datetime(pd.Series(dates)))
    plein = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"))
    liss = plein.rolling(window=fenetre, center=True,
                         min_periods=min_periods).mean()
    return liss.reindex(s.index).to_numpy()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lignes, journees = [], []

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

        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            propre, _rap = qcmod.controle_qualite(daily, air, qd, verbose=False)
            try:
                df = core.fusionner(propre, air, ecart, normales,
                                    df_debits=None, lissage_delta=lissage)
            except ValueError as exc:
                lignes.append(dict(jeu=j["jeu"], point=pt, statut="chaine interrompue",
                                   n_journees=0))
                print(f"  · {j['jeu']}/{pt} : interrompu", flush=True)
                continue
            df = df.sort_values("date").reset_index(drop=True)
            n = len(df)

            emp_t, lac_t, enj_t = enjambement(df["date"], FENETRE_TMH)
            emp_d, lac_d, enj_d = enjambement(df["date"], lissage)
            affectee = enj_t | enj_d

            # Les deux versions, cote a cote.
            tmh_pos = df["T_eau_moy"].rolling(window=FENETRE_TMH,
                                              min_periods=MIN_PERIODS_TMH,
                                              center=True).mean().to_numpy()
            tmh_cal = rolling_calendaire(df["date"], df["T_eau_moy"],
                                         FENETRE_TMH, MIN_PERIODS_TMH)
            dl_pos = df["Delta_TMm"].rolling(window=lissage, min_periods=1,
                                             center=True).mean().to_numpy()
            dl_cal = rolling_calendaire(df["date"], df["Delta_TMm"], lissage, 1)

            d_tmh = np.abs(tmh_pos - tmh_cal)
            d_dl = np.abs(dl_pos - dl_cal)
            fini_t = np.isfinite(d_tmh)
            fini_d = np.isfinite(d_dl)

            lignes.append(dict(
                jeu=j["jeu"], point=pt, statut="OK", n_journees=n,
                empan_calendaire_total_j=int(
                    (pd.to_datetime(df["date"].iloc[-1])
                     - pd.to_datetime(df["date"].iloc[0])).days),
                fenetres_Tmh_enjambantes=int(enj_t.sum()),
                fenetres_delta_enjambantes=int(enj_d.sum()),
                journees_T_norm_affectees=int(affectee.sum()),
                part_T_norm_affectee_pct=_f(100.0 * affectee.sum() / max(n, 1)),
                plus_longue_lacune_enjambee_j=int(max(lac_t.max(), lac_d.max())),
                ecart_Tmh_median=_f(float(np.median(d_tmh[fini_t]))
                                    if fini_t.any() else np.nan),
                ecart_Tmh_max=_f(float(d_tmh[fini_t].max()) if fini_t.any() else np.nan),
                ecart_delta_liss_median=_f(float(np.median(d_dl[fini_d]))
                                           if fini_d.any() else np.nan),
                ecart_delta_liss_max=_f(float(d_dl[fini_d].max())
                                        if fini_d.any() else np.nan)))

            for i in np.nonzero(affectee)[0]:
                journees.append(dict(
                    jeu=j["jeu"], point=pt, date=str(df["date"].iloc[i]),
                    fenetre_Tmh_enjambe=bool(enj_t[i]),
                    fenetre_delta_enjambe=bool(enj_d[i]),
                    empan_calendaire_Tmh_j=int(emp_t[i]),
                    plus_longue_lacune_dans_la_fenetre_j=int(max(lac_t[i], lac_d[i])),
                    Tmh_positionnel=_f(float(tmh_pos[i])),
                    Tmh_calendaire=_f(float(tmh_cal[i])),
                    ecart_Tmh=_f(float(d_tmh[i])),
                    delta_liss_positionnel=_f(float(dl_pos[i])),
                    delta_liss_calendaire=_f(float(dl_cal[i])),
                    ecart_delta_liss=_f(float(d_dl[i]))))
            print(f"  · {j['jeu']}/{pt} : {int(affectee.sum())}/{n} journees "
                  f"affectees, plus longue lacune enjambee "
                  f"{int(max(lac_t.max(), lac_d.max()))} j", flush=True)

    ecrire_csv(OUT / "C1_index_positionnel.csv",
               ["jeu", "point", "statut", "n_journees",
                "empan_calendaire_total_j", "fenetres_Tmh_enjambantes",
                "fenetres_delta_enjambantes", "journees_T_norm_affectees",
                "part_T_norm_affectee_pct", "plus_longue_lacune_enjambee_j",
                "ecart_Tmh_median", "ecart_Tmh_max",
                "ecart_delta_liss_median", "ecart_delta_liss_max"],
               lignes, tri=["jeu", "point"])
    ecrire_csv(OUT / "C1_index_positionnel_journees.csv",
               ["jeu", "point", "date", "fenetre_Tmh_enjambe",
                "fenetre_delta_enjambe", "empan_calendaire_Tmh_j",
                "plus_longue_lacune_dans_la_fenetre_j", "Tmh_positionnel",
                "Tmh_calendaire", "ecart_Tmh", "delta_liss_positionnel",
                "delta_liss_calendaire", "ecart_delta_liss"],
               journees, tri=["jeu", "point", "date"])

    ok = [l for l in lignes if l["statut"] == "OK"]
    tot_j = sum(l["n_journees"] for l in ok)
    tot_a = sum(l["journees_T_norm_affectees"] for l in ok)
    print(f"\n=== SYNTHESE ===")
    print(f"  {len(ok)} points, {tot_j} journees")
    print(f"  journees de T_norm affectees : {tot_a} "
          f"({100*tot_a/max(tot_j,1):.2f} %)")
    print(f"  points concernes             : "
          f"{sum(1 for l in ok if l['journees_T_norm_affectees'] > 0)}")
    print(f"  plus longue lacune enjambee  : "
          f"{max((l['plus_longue_lacune_enjambee_j'] for l in ok), default=0)} j")
    print(f"  ecart max sur Tmh            : "
          f"{max((l['ecart_Tmh_max'] or 0) for l in ok):.3f} degC")
    print(f"  ecart max sur Delta_TMm_liss : "
          f"{max((l['ecart_delta_liss_max'] or 0) for l in ok):.3f} degC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
