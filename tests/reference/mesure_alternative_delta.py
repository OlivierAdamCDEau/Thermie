"""
mesure_alternative_delta.py — ÉTAPE 8, TÂCHE B4 : le défaut MIROIR.

LA QUESTION
------------
Le correctif 8 (D47) retient que `Tmh`, moyenne de température d'EAU, ne doit
pas dépendre de la complétude de la série d'AIR. L'argument se retourne :

    `Delta_TMm_liss` est une moyenne mobile de l'ANOMALIE D'AIR.
    Elle est calculée sur la vue exploitable, c'est-à-dire sur les seules
    journées qui ont AUSSI une température d'eau.
    Elle dépend donc de la complétude de la série d'EAU, qui ne la regarde pas.

C'est le même défaut, dans l'autre sens. `core.py` le porte à la ligne où
`Delta_TMm_liss` est calculée.

CE QUE MESURE CE MODULE, ET CE QU'IL NE FAIT PAS
-------------------------------------------------
Il chiffre ce que corrigerait le lissage de `Delta_TMm_liss` sur le calendrier
propre de la station d'air — `ecart_by_date`, qui couvre toutes les dates
d'air, indépendamment de l'eau. **Il ne corrige rien.** D47 porte sur `Tmh` et
sur `Tmh` seulement ; ce défaut-ci reçoit une alternative fermée, chiffrée,
et un correctif à lui s'il est retenu.

L'enjeu est direct : `anomalie_lissee` est une colonne de `05_anomalies.csv`,
que la commande d'étape déclare devant bouger. Or le correctif 8 seul ne peut
pas la faire bouger — `Tmh` n'entre pas dans cet artefact. Cette mesure dit
donc aussi ce qu'il faudrait corriger pour que la déclaration se vérifie.

Sortie :
  out/etape8/ALT_delta_calendrier_air.csv
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

OUT = RACINE / "out" / "etape8"


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
        lissage = an["normalisation_lissage_delta"]
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        ecart, normales, _ = io_data.calculer_normales_ecarts(
            air, fenetre_lissage=an["normales_fenetre_lissage"],
            min_annees=an["normales_min_annees"], verbose=False)
        qd = qc_dict(par)

        # Le lissage sur le calendrier PROPRE de la station d'air : il ne
        # depend d'aucune sonde, il se calcule une fois par jeu.
        e = ecart.dropna(subset=["Delta_TMm"]).sort_values("date")
        delta_air = pd.Series(
            core.moyenne_mobile_calendaire(e["date"], e["Delta_TMm"],
                                           lissage, 1),
            index=pd.to_datetime(e["date"].to_numpy()))

        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            propre, _r = qcmod.controle_qualite(daily, air, qd, verbose=False)
            if not len(propre):
                continue
            try:
                df, _m = core.fusionner_marque(
                    propre, air, ecart, normales, df_debits=None,
                    lissage_delta=lissage)
            except ValueError:
                continue
            if not len(df):
                continue
            df = df.sort_values("date").reset_index(drop=True)

            retenu = df["Delta_TMm_liss"].to_numpy()
            alt = delta_air.reindex(
                pd.to_datetime(df["date"].to_numpy())).to_numpy()
            d = np.abs(alt - retenu)
            change = ~((np.isnan(alt) & np.isnan(retenu))
                       | np.isclose(alt, retenu, equal_nan=False))
            fini = np.isfinite(d) & change

            # L'effet sur T_norm passe par m : Tmh_norm = Tmh - m x Delta_liss
            m_est = None
            try:
                m_est = float(core.analyse_sensibilite(df)["m"])
            except Exception:
                pass
            ecart_tnorm = (float(np.max(d[fini])) * m_est
                           if fini.any() and m_est else np.nan)

            lignes.append(dict(
                jeu=j["jeu"], point=pt, n_journees=len(df),
                delta_liss_changes=int(change.sum()),
                part_changee_pct=_f(100.0 * change.sum() / max(len(df), 1)),
                ecart_median=_f(float(np.median(d[fini]))
                                if fini.any() else np.nan),
                ecart_max=_f(float(d[fini].max()) if fini.any() else np.nan),
                m_du_point=_f(m_est) if m_est is not None else None,
                ecart_max_repercute_sur_T_norm=_f(ecart_tnorm)))
            print(f"  · {j['jeu']}/{pt} : {int(change.sum())}/{len(df)} "
                  f"Delta_TMm_liss changes", flush=True)

    ecrire_csv(OUT / "ALT_delta_calendrier_air.csv",
               ["jeu", "point", "n_journees", "delta_liss_changes",
                "part_changee_pct", "ecart_median", "ecart_max", "m_du_point",
                "ecart_max_repercute_sur_T_norm"],
               lignes, tri=["jeu", "point"])

    tot = sum(l["n_journees"] for l in lignes)
    ch = sum(l["delta_liss_changes"] for l in lignes)
    print("\n=== ALTERNATIVE : Delta_TMm_liss SUR LE CALENDRIER DE L'AIR ===")
    print(f"  {len(lignes)} points, {tot} journees")
    print(f"  Delta_TMm_liss qui changeraient : {ch} "
          f"({100*ch/max(tot,1):.2f} %)")
    print(f"  points concernes : "
          f"{sum(1 for l in lignes if l['delta_liss_changes'] > 0)}")
    m = [l["ecart_max"] for l in lignes if l["ecart_max"]]
    if m:
        print(f"  ecart maximal sur Delta_TMm_liss : {max(m):.3f} degC")
    t = [l["ecart_max_repercute_sur_T_norm"]
         for l in lignes if l["ecart_max_repercute_sur_T_norm"]]
    if t:
        print(f"  soit au plus, sur T_norm          : {max(t):.3f} degC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
