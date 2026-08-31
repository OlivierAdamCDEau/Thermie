"""
mesure_support_delta.py — ÉTAPE 9, TÂCHES B1 et B3.

MESURE AVANT CORRECTION.

B1 — LE SUPPORT EXISTE-T-IL, ET JUSQU'OÙ S'ÉTEND-IL ?
------------------------------------------------------
L'étape 8 note que `ecart_by_date` couvre toutes les dates de la station
d'air. Il faut le vérifier plutôt que le répéter : ce module compare, jeu par
jeu, l'étendue de la série d'anomalies d'air à celle de chaque chronique
d'eau, et dit de combien la première déborde la seconde de part et d'autre.

B3 — DEUX SUPPORTS SE DÉFENDENT, ILS NE DONNENT PAS LE MÊME LISSAGE
--------------------------------------------------------------------
    (b) TOUTES les dates de la station d'air ;
    (c) les seules dates d'air qui RECOUVRENT la chronique d'eau du point.

Les deux ne diffèrent qu'aux **bords** de la chronique d'eau : à moins de
`fenetre // 2` jours de son premier et de son dernier jour, la fenêtre du
support (c) est tronquée là où celle du support (b) est pleine.

Ce module chiffre l'écart entre les deux, et le compare à l'écart que corrige
le correctif 9 lui-même — c'est ce rapport qui dit si le choix est de
conséquence ou de principe.

Sortie :
  out/etape9/B1_etendue_support.csv
  out/etape9/B3_deux_supports.csv
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

OUT = RACINE / "out" / "etape9"


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
    etendue, supports = [], []

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

        e = ecart.dropna(subset=["Delta_TMm"]).sort_values("date")
        d_air = pd.to_datetime(e["date"].to_numpy())
        a0, a1 = d_air.min(), d_air.max()

        # (b) support COMPLET : tout le calendrier de la station.
        liss_b = pd.Series(
            core.moyenne_mobile_calendaire(e["date"], e["Delta_TMm"],
                                           lissage, 1), index=d_air)

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
            d_eau = pd.to_datetime(df["date"].to_numpy())
            e0, e1 = d_eau.min(), d_eau.max()

            etendue.append(dict(
                jeu=j["jeu"], point=pt,
                air_debut=str(a0.date()), air_fin=str(a1.date()),
                air_n_dates=int(len(e)),
                eau_debut=str(e0.date()), eau_fin=str(e1.date()),
                eau_n_journees=int(len(df)),
                air_deborde_avant_j=int((e0 - a0).days),
                air_deborde_apres_j=int((a1 - e1).days),
                air_couvre_toute_l_eau="oui" if (a0 <= e0 and a1 >= e1) else "NON"))

            # (c) support RESTREINT au recouvrement de la chronique d'eau.
            masque = (d_air >= e0) & (d_air <= e1)
            sub = e.loc[masque]
            liss_c = pd.Series(
                core.moyenne_mobile_calendaire(sub["date"], sub["Delta_TMm"],
                                               lissage, 1),
                index=pd.to_datetime(sub["date"].to_numpy()))

            vb = liss_b.reindex(d_eau).to_numpy()
            vc = liss_c.reindex(d_eau).to_numpy()
            va = df["Delta_TMm_liss"].to_numpy()      # (a) l'existant

            def compte(x, y):
                ch = ~((np.isnan(x) & np.isnan(y))
                       | np.isclose(x, y, equal_nan=False))
                d = np.abs(x - y)
                f = np.isfinite(d) & ch
                return (int(ch.sum()),
                        float(np.median(d[f])) if f.any() else np.nan,
                        float(d[f].max()) if f.any() else np.nan)

            n_bc, med_bc, max_bc = compte(vb, vc)
            n_ab, med_ab, max_ab = compte(va, vb)
            # les journees concernees par (b) vs (c) sont-elles aux bords ?
            demi = lissage // 2
            bord = ((d_eau - e0).days <= demi) | ((e1 - d_eau).days <= demi)
            ch_bc = ~((np.isnan(vb) & np.isnan(vc))
                      | np.isclose(vb, vc, equal_nan=False))

            supports.append(dict(
                jeu=j["jeu"], point=pt, n_journees=int(len(df)),
                ecart_b_contre_c_n=n_bc,
                ecart_b_contre_c_hors_bords=int((ch_bc & ~bord).sum()),
                ecart_b_contre_c_median=_f(med_bc),
                ecart_b_contre_c_max=_f(max_bc),
                correctif9_n=n_ab,
                correctif9_median=_f(med_ab),
                correctif9_max=_f(max_ab)))
            print(f"  · {j['jeu']}/{pt} : correctif9 {n_ab} valeurs ; "
                  f"support b vs c {n_bc} valeurs "
                  f"(dont {int((ch_bc & ~bord).sum())} hors bords)", flush=True)

    ecrire_csv(OUT / "B1_etendue_support.csv",
               ["jeu", "point", "air_debut", "air_fin", "air_n_dates",
                "eau_debut", "eau_fin", "eau_n_journees",
                "air_deborde_avant_j", "air_deborde_apres_j",
                "air_couvre_toute_l_eau"],
               etendue, tri=["jeu", "point"])
    ecrire_csv(OUT / "B3_deux_supports.csv",
               ["jeu", "point", "n_journees", "ecart_b_contre_c_n",
                "ecart_b_contre_c_hors_bords", "ecart_b_contre_c_median",
                "ecart_b_contre_c_max", "correctif9_n", "correctif9_median",
                "correctif9_max"],
               supports, tri=["jeu", "point"])

    print("\n=== B1 — L'ETENDUE DU SUPPORT ===")
    print(f"  {len(etendue)} points")
    print(f"  l'air couvre toute la chronique d'eau : "
          f"{sum(1 for l in etendue if l['air_couvre_toute_l_eau']=='oui')}"
          f"/{len(etendue)}")
    av = [l["air_deborde_avant_j"] for l in etendue]
    ap = [l["air_deborde_apres_j"] for l in etendue]
    if av:
        print(f"  l'air commence avant l'eau de : {min(av)} a {max(av)} jours")
        print(f"  l'air finit apres l'eau de   : {min(ap)} a {max(ap)} jours")
    print("\n=== B3 — LES DEUX SUPPORTS ===")
    tb = sum(l["ecart_b_contre_c_n"] for l in supports)
    hb = sum(l["ecart_b_contre_c_hors_bords"] for l in supports)
    tc = sum(l["correctif9_n"] for l in supports)
    print(f"  correctif 9 (a -> b) : {tc} valeurs deplacees")
    print(f"  support b contre c   : {tb} valeurs, dont {hb} hors des bords")
    m = [l["ecart_b_contre_c_max"] for l in supports if l["ecart_b_contre_c_max"]]
    if m:
        print(f"  ecart maximal b contre c : {max(m):.3f} degC")
    print(f"  soit {100*tb/max(tc,1):.2f} % de ce que corrige le correctif 9")
    return 0


if __name__ == "__main__":
    sys.exit(main())
