"""
mesure_marges_seuils.py — ÉTAPE 9, TÂCHE C.

POURQUOI CE MODULE
-------------------
La commande d'étape attendait un basculement de verdict : `Delta_TMm_liss`
entre directement dans `T_norm`, et l'écart atteint 1,94 °C. Constaté :
**aucune catégorie ne change**, et deux pourcentages seulement se déplacent.

Une attente déçue n'est pas un résultat tant qu'on ne sait pas pourquoi. Ce
module mesure la **marge** — la distance qui sépare chaque journée du seuil
qu'elle aurait pu franchir — avant et après le correctif 9, pour dire si le
non-basculement tient à la petitesse des déplacements ou à leur emplacement.

CE QUI EST MESURÉ
------------------
Pour chaque point, et pour chacun des deux seuils que V4.5 publie :

  · `seuil_aigu`     franchi par `Tmax_norm` — il donne `n_jours_aigus` ;
  · `seuil_chronique` franchi par `Tmh_norm`  — il donne `pct_stress_chronique`.

  n_franchissements avant et après ; la journée la PLUS PROCHE du seuil sans
  le franchir, sa marge avant et après ; et le déplacement médian et maximal
  subi par les journées proches du seuil, comparé au déplacement d'ensemble.

C'est ce dernier rapport qui répond : si les journées proches du seuil ont
bougé beaucoup moins que la moyenne, le non-basculement est un fait de
répartition, pas de magnitude.

Sortie :
  out/etape9/C_marges_seuils.csv
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


def seuils_du_point(jeu, point):
    """Les seuils que le harnais a figés dans 08_scores.csv."""
    f = ICI / jeu / "08_scores.csv"
    if not f.exists():
        return None, None
    d = pd.read_csv(f, sep=";")
    d = d[d["point"] == point]
    def v(nom):
        s = d[d["indicateur"] == nom]["valeur"]
        return float(s.iloc[0]) if len(s) and pd.notna(s.iloc[0]) else None
    return v("seuil_aigu"), v("seuil_chronique")


def bloc(serie_av, serie_ap, seuil, prefixe):
    """Franchissements, marge du plus proche, et deplacement pres du seuil."""
    r = {}
    if seuil is None:
        return r
    a = np.asarray(serie_av, dtype=float)
    b = np.asarray(serie_ap, dtype=float)
    fini = np.isfinite(a) & np.isfinite(b)
    a, b = a[fini], b[fini]
    if not len(a):
        return r
    r[prefixe + "_seuil"] = _f(seuil)
    r[prefixe + "_franchis_avant"] = int((a > seuil).sum())
    r[prefixe + "_franchis_apres"] = int((b > seuil).sum())
    # la journee la plus proche du seuil SANS le franchir, avant correctif
    sous = a[a <= seuil]
    r[prefixe + "_marge_plus_proche_avant"] = _f(
        float(seuil - sous.max()) if len(sous) else np.nan)
    sous_b = b[b <= seuil]
    r[prefixe + "_marge_plus_proche_apres"] = _f(
        float(seuil - sous_b.max()) if len(sous_b) else np.nan)
    # deplacement, d'ensemble et pres du seuil
    d = np.abs(b - a)
    r[prefixe + "_deplacement_median"] = _f(float(np.median(d)))
    r[prefixe + "_deplacement_max"] = _f(float(d.max()))
    # « pres du seuil » = a moins d'un demi-degre, sans seuil nouveau : c'est
    # l'ordre de grandeur du deplacement maximal annonce (1,94 degC), divise
    # par quatre. Il ne sert qu'a decrire, jamais a decider.
    proche = np.abs(a - seuil) <= 0.5
    r[prefixe + "_n_journees_a_moins_de_0_5_degC"] = int(proche.sum())
    r[prefixe + "_deplacement_median_pres_du_seuil"] = _f(
        float(np.median(d[proche])) if proche.any() else np.nan)
    r[prefixe + "_deplacement_max_pres_du_seuil"] = _f(
        float(d[proche].max()) if proche.any() else np.nan)
    return r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lignes = []
    n_bie35 = 0

    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((ICI / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        an = {k: v["valeur"] for k, v in par["analyse"].items()}
        L = an["normalisation_lissage_delta"]
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
                df, _m = core.fusionner_marque(propre, air, ecart, normales,
                                               df_debits=None, lissage_delta=L)
            except ValueError:
                continue
            if not len(df):
                continue
            df = df.sort_values("date").reset_index(drop=True)

            # AVANT le correctif 9 : l'anomalie lissee sur la vue exploitable.
            delta_av = core.moyenne_mobile_calendaire(df["date"],
                                                      df["Delta_TMm"], L, 1)
            delta_ap = df["Delta_TMm_liss"].to_numpy()
            if pt == "BIE35-5__NA":
                c = ~((np.isnan(delta_av) & np.isnan(delta_ap))
                      | np.isclose(delta_av, delta_ap, equal_nan=False))
                n_bie35 = int(c.sum())

            try:
                m = float(core.analyse_sensibilite(df)["m"])
            except Exception:
                continue

            tmh = df["Tmh"].to_numpy()
            tmax = df["T_eau_max"].to_numpy()
            s_aigu, s_chr = seuils_du_point(j["jeu"], pt)

            l = dict(jeu=j["jeu"], point=pt, n_journees=int(len(df)),
                     m=_f(m),
                     delta_liss_deplaces=int((~(
                         (np.isnan(delta_av) & np.isnan(delta_ap))
                         | np.isclose(delta_av, delta_ap, equal_nan=False))).sum()))
            l.update(bloc(tmax - m * delta_av, tmax - m * delta_ap,
                          s_aigu, "aigu"))
            l.update(bloc(tmh - m * delta_av, tmh - m * delta_ap,
                          s_chr, "chronique"))
            lignes.append(l)
            print(f"  · {j['jeu']}/{pt} : {l['delta_liss_deplaces']} anomalies "
                  f"deplacees", flush=True)

    cols = ["jeu", "point", "n_journees", "m", "delta_liss_deplaces"]
    for p in ("aigu", "chronique"):
        cols += [f"{p}_seuil", f"{p}_franchis_avant", f"{p}_franchis_apres",
                 f"{p}_marge_plus_proche_avant", f"{p}_marge_plus_proche_apres",
                 f"{p}_deplacement_median", f"{p}_deplacement_max",
                 f"{p}_n_journees_a_moins_de_0_5_degC",
                 f"{p}_deplacement_median_pres_du_seuil",
                 f"{p}_deplacement_max_pres_du_seuil"]
    ecrire_csv(OUT / "C_marges_seuils.csv", cols, lignes, tri=["jeu", "point"])

    print("\n=== C — LES MARGES AUX SEUILS ===")
    print(f"  points mesures : {len(lignes)}")
    print(f"  BIE35-5__NA : {n_bie35} anomalies deplacees "
          f"(ce point est ABSENT des artefacts, sa chaine echoue — D7)")
    for p, nom in (("aigu", "SEUIL AIGU (Tmax_norm -> n_jours_aigus)"),
                   ("chronique", "SEUIL CHRONIQUE (Tmh_norm -> pct_stress)")):
        av = sum(l.get(f"{p}_franchis_avant", 0) for l in lignes)
        ap = sum(l.get(f"{p}_franchis_apres", 0) for l in lignes)
        ch = [l for l in lignes
              if l.get(f"{p}_franchis_avant") != l.get(f"{p}_franchis_apres")]
        dm = [l[f"{p}_deplacement_median"] for l in lignes
              if l.get(f"{p}_deplacement_median")]
        dp = [l[f"{p}_deplacement_median_pres_du_seuil"] for l in lignes
              if l.get(f"{p}_deplacement_median_pres_du_seuil")]
        mg = [l[f"{p}_marge_plus_proche_avant"] for l in lignes
              if l.get(f"{p}_marge_plus_proche_avant")]
        print(f"\n  {nom}")
        print(f"    franchissements : {av} avant -> {ap} apres")
        print(f"    points dont le compte change : {len(ch)}")
        for l in ch:
            print(f"       {l['point']} : {l[f'{p}_franchis_avant']} -> "
                  f"{l[f'{p}_franchis_apres']}")
        if dm:
            print(f"    deplacement median, ensemble  : "
                  f"{np.median(dm):.4f} degC")
        if dp:
            print(f"    deplacement median, pres du seuil : "
                  f"{np.median(dp):.4f} degC")
        if mg:
            print(f"    marge de la journee la plus proche : mediane "
                  f"{np.median(mg):.3f} degC, minimum {min(mg):.3f} degC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
