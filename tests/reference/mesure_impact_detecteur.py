"""
mesure_impact_detecteur.py — ÉTAPE 8, TÂCHE C (D50).

LA TABLE D'IMPACT DU §5 DE LA SPÉCIFICATION EST PÉRIMÉE
--------------------------------------------------------
Elle a été calculée à l'étape 4, donc AVANT les correctifs 2 (index
calendaire), 5 (jointure gauche) et 8 (lissage sur l'eau complète). Ce que le
détecteur du correctif 1 déplacerait ne se lit plus sur la chaîne d'alors.

CE QUI SE RECALCULE, ET CE QUI NE SE RECALCULE PAS (D50)
---------------------------------------------------------
Le **marquage du détecteur** est inchangé : il repose sur `T_eau_max`,
`T_air`, `TN`, `TX` et `T_eau_min`, qu'aucun correctif posé n'a touchés. Ni le
choix de `k`, ni la mesure d'aveuglement ne sont donc à refaire — et ce module
ne les refait pas.

Ce qui se recalcule est l'**aval** : `m`, puis `Tmh_norm = Tmh − m ×
Delta_TMm_liss`. `Tmh` a changé deux fois (correctifs 2 et 8),
`Delta_TMm_liss` une fois (correctif 2), et la chronique retenue une fois
(correctif 5). L'impact du détecteur se mesure donc sur une chaîne différente.

LE RÉGLAGE MESURÉ EST CELUI QUE LA SPÉCIFICATION RETIENT
---------------------------------------------------------
  · marche 1 — socle relatif, `E_moy_rel > k` avec **k = 3,0** ;
  · marche 2 — conjonction `R_ampl_rel > k` **ET** `E_max_rel > k`, dès que
    `TN` et `TX` sont présents et que l'amplitude d'air dépasse le garde-fou
    dérivé du jeu (quantile `q_ampl` = 0,10).

Les deux marches s'unissent : la marche 2 n'est pas une substitution (§1.3 de
la spécification).

Le détecteur EN SERVICE reste la référence de comparaison (D25) :
`T_eau_max − T_air > 10 °C`, sans exclusion de saison, grille annuelle à
5 jours.

AUCUN CODE DE DÉTECTION N'EST ÉCRIT. Les critères sont reproduits ici, dans le
harnais, comme aux étapes 3 et 4.

Sorties :
  out/etape8/C1_impact_par_point.csv
  out/etape8/C2_journees_perdues_vs_service.csv
  out/etape8/C3_comparaison_etape4.csv
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from _commun import ICI, RACINE, decouvrir, ecrire_csv, nom_point, _f
from thermie_debits import io_data
from mesure_regime_service import (masque_hors_eau, ajouter_relatifs, rejouer,
                                   masques_qc, MOIS_JJAS)
from mesure_conjonction import relativiser
from mesure_marche2 import lire_air_complet

OUT = RACINE / "out" / "etape8"

K = 3.0                 # le reglage retenu par la specification
QUANTILE_AMPL_MIN = 0.10


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------- 1. Le socle point-jour, avec TN/TX ----------
    blocs, contextes = [], {}
    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((ICI / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        qc = {k: v["valeur"] for k, v in par["qc"].items()}
        an = {k: v["valeur"] for k, v in par["analyse"].items()}
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        air_complet = lire_air_complet(str(RACINE / j["air"]))
        ecart_air, normales, _ = io_data.calculer_normales_ecarts(
            air, fenetre_lissage=an["normales_fenetre_lissage"],
            min_annees=an["normales_min_annees"], verbose=False)
        contextes[j["jeu"]] = dict(qc=qc, an=an, air=air, ecart_air=ecart_air,
                                   normales=normales)
        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            # charger_air_brut donne T_air (= TM) ; lire_air_complet donne
            # TN et TX. Les deux sont necessaires : la marche 1 lit T_air,
            # la marche 2 lit TN et TX.
            tntx = [c for c in ["date", "TN", "TX"] if c in air_complet.columns]
            d = daily.merge(air, on="date", how="left")
            d = d.merge(air_complet[tntx], on="date", how="left")
            d["date_dt"] = pd.to_datetime(d["date"])
            d["month"] = d["date_dt"].dt.month
            d["year"] = d["date_dt"].dt.year
            d = d.sort_values("date_dt").reset_index(drop=True)
            d["jeu"], d["point"] = j["jeu"], pt
            blocs.append(d)
    socle = pd.concat(blocs, ignore_index=True)
    socle = ajouter_relatifs(socle)

    # ---------- 2. La marche 2 : R_ampl ET E_max ----------
    socle["E_max"] = socle["T_eau_max"] - socle["TX"]
    socle["ampl_eau"] = socle["T_eau_max"] - socle["T_eau_min"]
    socle["ampl_air"] = socle["TX"] - socle["TN"]
    seuils = {}
    for jeu, sub in socle.groupby("jeu"):
        a = sub["ampl_air"].dropna()
        seuils[jeu] = float(a.quantile(QUANTILE_AMPL_MIN)) if len(a) else np.nan
    socle["seuil_ampl"] = socle["jeu"].map(seuils)
    socle["ampl_ok"] = socle["ampl_air"] >= socle["seuil_ampl"]
    socle["R_ampl"] = np.where(socle["ampl_ok"],
                               socle["ampl_eau"] / socle["ampl_air"].replace(0, np.nan),
                               np.nan)
    socle = relativiser(socle, "E_max")
    socle = relativiser(socle, "R_ampl")

    socle["marche1"] = (socle["_jjas"]
                        & (socle["ecart_rel_B"] > K).fillna(False))
    socle["marche2"] = (socle["_jjas"]
                        & socle["R_ampl_diag"].fillna(False)
                        & socle["E_max_diag"].fillna(False)
                        & (socle["R_ampl_rel"] > K).fillna(False)
                        & (socle["E_max_rel"] > K).fillna(False))
    socle["detecteur"] = socle["marche1"] | socle["marche2"]
    print(f"  marche 1 : {int(socle['marche1'].sum())} jours ; "
          f"marche 2 : {int(socle['marche2'].sum())} jours ; "
          f"union : {int(socle['detecteur'].sum())} jours")
    for jeu, s in seuils.items():
        print(f"  garde-fou d'amplitude d'air, {jeu} : {s:.2f} degC")

    # ---------- 3. Rejeu de la chaine, par point ----------
    lignes, perdues = [], []
    for (jeu, pt), d in socle.groupby(["jeu", "point"]):
        ctx = contextes[jeu]
        qc = ctx["qc"]
        autres = masques_qc(d, qc)
        base = autres["bornes"] | autres["plateau"] | autres["mad"]
        ref = masque_hors_eau(d, 10.0, 5, False)          # regime en service
        cand = d["detecteur"]

        daily = d[["date", "T_eau_moy", "T_eau_max", "T_eau_min",
                   "n_mesures"]].copy()
        r_ref = rejouer(daily, ctx["air"], ctx["ecart_air"], ctx["normales"],
                        set(d.loc[base | ref, "date"]),
                        ctx["an"]["normalisation_lissage_delta"])
        r_can = rejouer(daily, ctx["air"], ctx["ecart_air"], ctx["normales"],
                        set(d.loc[base | cand, "date"]),
                        ctx["an"]["normalisation_lissage_delta"])

        def g(r, cle):
            return r.get(cle) if r and r.get("statut") == "OK" else None

        m_ref, m_can = g(r_ref, "m"), g(r_can, "m")
        med_ref, med_can = g(r_ref, "tmh_norm_mediane"), g(r_can, "tmh_norm_mediane")
        p95_ref, p95_can = g(r_ref, "tmh_norm_p95"), g(r_can, "tmh_norm_p95")

        lignes.append(dict(
            jeu=jeu, point=pt, n_journees=int(len(d)),
            statut=(r_can or {}).get("statut", "?"),
            jours_regime_service=int(ref.sum()),
            jours_marche1=int(d["marche1"].sum()),
            jours_marche2=int(d["marche2"].sum()),
            jours_detecteur=int(cand.sum()),
            jours_communs=int((ref & cand).sum()),
            jours_perdus_vs_service=int((ref & ~cand).sum()),
            jours_gagnes_vs_service=int((~ref & cand).sum()),
            m_service=_f(m_ref), m_detecteur=_f(m_can),
            ecart_m=_f(None if m_ref is None or m_can is None else m_can - m_ref),
            tmh_norm_mediane_service=_f(med_ref),
            tmh_norm_mediane_detecteur=_f(med_can),
            ecart_tmh_norm_mediane=_f(
                None if med_ref is None or med_can is None else med_can - med_ref),
            tmh_norm_p95_service=_f(p95_ref),
            tmh_norm_p95_detecteur=_f(p95_can),
            ecart_tmh_norm_p95=_f(
                None if p95_ref is None or p95_can is None else p95_can - p95_ref)))

        # C2 — les journees que le service ecarte et que le SOCLE ne marque pas.
        # C'est la definition de l'etape 4, qui mesurait la marche 1 SEULE ;
        # on note pour chacune si la marche 2 la rattrape, ce qui explique
        # l'ecart entre les deux comptes.
        for i in d.index[ref & ~d["marche1"]]:
            r = d.loc[i]
            perdues.append(dict(
                jeu=jeu, point=pt, date=str(r["date"]),
                T_eau_max=_f(r.get("T_eau_max")), T_air=_f(r.get("T_air")),
                ecart_T_eau_max_moins_T_air=_f(
                    r.get("T_eau_max") - r.get("T_air")
                    if pd.notna(r.get("T_air")) else np.nan),
                E_moy_relativise=_f(r.get("ecart_rel_B")),
                seuil_k=K,
                R_ampl_relativise=_f(r.get("R_ampl_rel")),
                E_max_relativise=_f(r.get("E_max_rel")),
                marche2_diagnosticable=("oui" if bool(r.get("R_ampl_diag"))
                                        and bool(r.get("E_max_diag")) else "non"),
                rattrapee_par_la_marche2=("oui" if bool(r.get("marche2"))
                                          else "non"),
                pourquoi_non_marquee=(
                    "E_moy relativise sous le seuil"
                    if pd.notna(r.get("ecart_rel_B")) else
                    "non diagnosticable par la marche 1 (dispersion nulle "
                    "ou mois trop court)")))
        print(f"  · {jeu}/{pt} : service {int(ref.sum())}, detecteur "
              f"{int(cand.sum())}, perdues {int((ref & ~cand).sum())}",
              flush=True)

    ecrire_csv(OUT / "C1_impact_par_point.csv",
               ["jeu", "point", "n_journees", "statut", "jours_regime_service",
                "jours_marche1", "jours_marche2", "jours_detecteur",
                "jours_communs", "jours_perdus_vs_service",
                "jours_gagnes_vs_service", "m_service", "m_detecteur",
                "ecart_m", "tmh_norm_mediane_service",
                "tmh_norm_mediane_detecteur", "ecart_tmh_norm_mediane",
                "tmh_norm_p95_service", "tmh_norm_p95_detecteur",
                "ecart_tmh_norm_p95"],
               lignes, tri=["jeu", "point"])
    ecrire_csv(OUT / "C2_journees_perdues_vs_service.csv",
               ["jeu", "point", "date", "T_eau_max", "T_air",
                "ecart_T_eau_max_moins_T_air", "E_moy_relativise", "seuil_k",
                "R_ampl_relativise", "E_max_relativise",
                "marche2_diagnosticable", "rattrapee_par_la_marche2",
                "pourquoi_non_marquee"],
               perdues, tri=["jeu", "point", "date"])

    # ---------- 4. C3 — la comparaison a l'etape 4 ----------
    comp = []
    anc = RACINE / "out" / "etape4" / "impact_m_tnorm.csv"
    if anc.exists():
        a = pd.read_csv(anc, sep=";")
        a = a[a["reglage"].str.contains("B dispersion propre, k=3.0", na=False)]
        idx = {(r["jeu"], r["point"]): r for _, r in a.iterrows()}
        for l in lignes:
            v = idx.get((l["jeu"], l["point"]))
            if v is None:
                continue
            comp.append(dict(
                jeu=l["jeu"], point=l["point"],
                ecart_m_etape4=_f(v.get("ecart_m")),
                ecart_m_etape8=l["ecart_m"],
                variation_ecart_m=_f(
                    None if l["ecart_m"] is None or pd.isna(v.get("ecart_m"))
                    else l["ecart_m"] - float(v["ecart_m"])),
                ecart_tmh_p95_etape4=_f(v.get("ecart_tmh_norm_p95")),
                ecart_tmh_p95_etape8=l["ecart_tmh_norm_p95"],
                variation_ecart_p95=_f(
                    None if l["ecart_tmh_norm_p95"] is None
                    or pd.isna(v.get("ecart_tmh_norm_p95"))
                    else l["ecart_tmh_norm_p95"]
                    - float(v["ecart_tmh_norm_p95"]))))
    ecrire_csv(OUT / "C3_comparaison_etape4.csv",
               ["jeu", "point", "ecart_m_etape4", "ecart_m_etape8",
                "variation_ecart_m", "ecart_tmh_p95_etape4",
                "ecart_tmh_p95_etape8", "variation_ecart_p95"],
               comp, tri=["jeu", "point"])

    ok = [l for l in lignes if l["ecart_m"] is not None]
    print("\n=== C1 — IMPACT DU DETECTEUR, CHAINE APRES CORRECTIFS 2/3/5/8 ===")
    print(f"  points : {len(lignes)} ; avec m comparable : {len(ok)}")
    print(f"  jours marques — regime en service : "
          f"{sum(l['jours_regime_service'] for l in lignes)}")
    print(f"  jours marques — detecteur (k={K}) : "
          f"{sum(l['jours_detecteur'] for l in lignes)}"
          f"  (marche 1 : {sum(l['jours_marche1'] for l in lignes)}, "
          f"marche 2 : {sum(l['jours_marche2'] for l in lignes)})")
    print(f"  CONTROLE D50 — marche 1 seule : "
          f"{sum(l['jours_marche1'] for l in lignes)} jours "
          f"(l'etape 4 en comptait 68 ; le marquage doit etre inchange)")
    print(f"  jours perdus vs service : "
          f"{sum(l['jours_perdus_vs_service'] for l in lignes)}")
    print(f"  jours gagnes vs service : "
          f"{sum(l['jours_gagnes_vs_service'] for l in lignes)}")
    if ok:
        em = sorted(abs(l["ecart_m"]) for l in ok)
        print(f"  |ecart m| : mediane {em[len(em)//2]:.4f}, maximum {em[-1]:.4f}")
    print(f"\n=== C2 — {len(perdues)} journee(s) ecartee(s) par le service et "
          f"non marquee(s) par le detecteur ===")
    for p in perdues:
        print(f"  {p['point']:<32} {p['date']}  "
              f"T_eau_max-T_air={p['ecart_T_eau_max_moins_T_air']:>6.2f}  "
              f"E_moy_rel={p['E_moy_relativise']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
