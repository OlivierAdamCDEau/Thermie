"""
mesure_alternative_lissage.py — ÉTAPE 7, alternative fermée du §6.

LA QUESTION
------------
Le correctif 5 conserve toutes les journées d'eau, mais la chaîne de calcul
continue de tourner sur les seules journées EXPLOITABLES — celles qui ont de
l'air. Une journée d'eau sans air reste donc, pour le lissage de `Tmh`, un
trou dans le calendrier, exactement comme si elle n'avait pas été mesurée.

Or `Tmh` est une moyenne de sept jours de température d'EAU. Elle ne dépend
pas de l'air. Exclure une journée d'eau parfaitement mesurée parce que la
station météo était muette ce jour-là est le même genre de défaut que l'index
positionnel du correctif 2 : le lissage dépend de quelque chose qui ne le
regarde pas.

Faut-il donc lisser `Tmh` sur la chronique d'eau COMPLÈTE, et ne réserver la
jointure avec l'air qu'à ce qui en a besoin — `Delta_TMm_liss`, et donc
`T_norm` ?

CE MODULE NE TRANCHE PAS. Il chiffre, pour que la décision se prenne sur des
nombres. Il ne modifie rien : les deux versions sont recalculées côte à côte
dans le harnais, comme en C1 et C4 de l'étape 6.

  · combien de journées voient leur `Tmh` changer, et de combien ;
  · combien des 18 journées sans `Tmh` en retrouveraient un ;
  · l'effet sur `Tmh_norm`, donc sur les pourcentages publiés.

Sortie :
  out/etape7/ALT_lissage_eau_complete.csv
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
FENETRE, MIN_PERIODS = 7, 4


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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lignes = []

    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((ICI / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        an = {k: v["valeur"] for k, v in par["analyse"].items()}
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        ecart, normales, _ = io_data.calculer_normales_ecarts(
            air, fenetre_lissage=an["normales_fenetre_lissage"],
            min_annees=an["normales_min_annees"], verbose=False)
        qd = qc_dict(par)

        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            propre, _r = qcmod.controle_qualite(daily, air, qd, verbose=False)
            if not len(propre):
                continue
            try:
                df, marques = core.fusionner_marque(
                    propre, air, ecart, normales, df_debits=None,
                    lissage_delta=an["normalisation_lissage_delta"])
            except ValueError:
                continue
            if not len(df):
                continue

            # RETENU : Tmh lissee sur les seules journees exploitables.
            retenu = df.sort_values("date").reset_index(drop=True)
            tmh_retenu = retenu["Tmh"].to_numpy()

            # ALTERNATIVE : Tmh lissee sur la chronique d'EAU complete, puis
            # ramenee sur les journees exploitables.
            eau = (marques[["date", "T_eau_moy"]]
                   .dropna(subset=["T_eau_moy"])
                   .sort_values("date").reset_index(drop=True))
            tmh_complet = core.moyenne_mobile_calendaire(
                eau["date"], eau["T_eau_moy"], FENETRE, MIN_PERIODS)
            table = pd.Series(tmh_complet,
                              index=pd.to_datetime(eau["date"].to_numpy()))
            tmh_alt = table.reindex(
                pd.to_datetime(retenu["date"].to_numpy())).to_numpy()

            d = np.abs(tmh_alt - tmh_retenu)
            change = ~((np.isnan(tmh_alt) & np.isnan(tmh_retenu))
                       | (np.isclose(tmh_alt, tmh_retenu, equal_nan=False)))
            recuperees = int((np.isnan(tmh_retenu) & ~np.isnan(tmh_alt)).sum())
            perdues = int((~np.isnan(tmh_retenu) & np.isnan(tmh_alt)).sum())
            fini = np.isfinite(d) & change

            n_air = int((marques["statut"] == "non_diagnosticable").sum())
            lignes.append(dict(
                jeu=j["jeu"], point=pt, n_journees_exploitables=len(retenu),
                journees_d_eau_sans_air=int(
                    (~marques["exploitable"].to_numpy()).sum()),
                Tmh_changes=int(change.sum()),
                part_changee_pct=_f(100.0 * change.sum() / max(len(retenu), 1)),
                Tmh_recuperes=recuperees, Tmh_perdus=perdues,
                ecart_median=_f(float(np.median(d[fini])) if fini.any() else np.nan),
                ecart_max=_f(float(d[fini].max()) if fini.any() else np.nan)))
            print(f"  · {j['jeu']}/{pt} : {int(change.sum())} Tmh changes, "
                  f"{recuperees} recuperes", flush=True)

    ecrire_csv(OUT / "ALT_lissage_eau_complete.csv",
               ["jeu", "point", "n_journees_exploitables",
                "journees_d_eau_sans_air", "Tmh_changes", "part_changee_pct",
                "Tmh_recuperes", "Tmh_perdus", "ecart_median", "ecart_max"],
               lignes, tri=["jeu", "point"])

    tot = sum(l["n_journees_exploitables"] for l in lignes)
    ch = sum(l["Tmh_changes"] for l in lignes)
    print("\n=== ALTERNATIVE : LISSER Tmh SUR LA CHRONIQUE D'EAU COMPLETE ===")
    print(f"  {len(lignes)} points, {tot} journees exploitables")
    print(f"  Tmh qui changeraient : {ch} ({100*ch/max(tot,1):.2f} %)")
    print(f"  points concernes     : "
          f"{sum(1 for l in lignes if l['Tmh_changes'] > 0)}")
    print(f"  Tmh recuperes (etaient vides) : "
          f"{sum(l['Tmh_recuperes'] for l in lignes)} sur 18")
    print(f"  Tmh perdus                    : "
          f"{sum(l['Tmh_perdus'] for l in lignes)}")
    m = [l["ecart_max"] for l in lignes if l["ecart_max"]]
    if m:
        print(f"  ecart maximal sur Tmh : {max(m):.3f} degC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
