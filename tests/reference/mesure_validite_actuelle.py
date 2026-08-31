"""
mesure_validite_actuelle.py — ÉTAPE 11, TÂCHE D1/D2.

LA PRÉDICTION EST À REFAIRE, PAS À REPRENDRE
---------------------------------------------
Les chiffres connus — 1 rejet estival sur 31 (`BLE3-0`, `t = 0,45`, le suivant
à 3,58) et 2 sur 33 en saisonnier — datent de l'étape 4. Ils ont été calculés
AVANT les correctifs 1, 2, 5, 8 et 9. Le correctif 1 a déplacé `m` jusqu'à
0,042, et les correctifs 2, 8 et 9 ont déplacé la chronique sur laquelle il
est estimé.

Ce module recalcule les `t` et les IC sur l'état ACTUEL de la chaîne, **avant**
que la règle ne soit posée dans le code. Le rejet constaté après la pose devra
être celui que cette mesure annonce.

D'OÙ VIENNENT LES PARAMÈTRES
-----------------------------
Du rejeu de l'étape 10 (`out/etape10/rejeu_pose2/*/10_parametres.json`), et
non de `tests/reference/`, qui fige encore le paramétrage de V4.5. C'est le
seul endroit où le paramétrage du détecteur relatif est écrit tel qu'il a
réellement tourné.

Sortie :
  out/etape11/D1_validite_actuelle.csv
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f
from thermie_debits import io_data, core, qc as qcmod
from mesure_validite_m import newey_west, fenetres_fraie, MOIS_ESTIVAUX

OUT = RACINE / "out" / "etape11"
PARAMS = RACINE / "out" / "etape10" / "rejeu_pose2"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lignes = []

    for j in decouvrir():
        if not j["air"]:
            continue
        par = json.loads((PARAMS / j["jeu"] / "10_parametres.json")
                         .read_text(encoding="utf-8"))
        qc = {k: v["valeur"] for k, v in par["qc"].items()}
        an = {k: v["valeur"] for k, v in par["analyse"].items()}
        qd = {k: (list(v) if isinstance(v, (list, tuple)) else v)
              for k, v in qc.items()}
        # `to_legacy_dict` emploie T_eau_min / T_eau_max en majuscules.
        qd["T_eau_min"] = qd.pop("t_eau_min")
        qd["T_eau_max"] = qd.pop("t_eau_max")
        air = io_data.charger_air_brut(str(RACINE / j["air"]))
        ecart, normales, _ = io_data.calculer_normales_ecarts(
            air, fenetre_lissage=an["normales_fenetre_lissage"],
            min_annees=an["normales_min_annees"], verbose=False)
        ctx_key = par["contexte_piscicole"]["valeur"]
        espece = par["espece_repere"]["valeur"]

        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            propre, _r = qcmod.controle_qualite(daily, air, qd, verbose=False)
            if not len(propre):
                continue
            try:
                df = core.fusionner(propre, air, ecart, normales,
                                    df_debits=None,
                                    lissage_delta=an["normalisation_lissage_delta"])
            except ValueError:
                continue
            if not len(df):
                continue

            fenetres = [("m_estival", "", MOIS_ESTIVAUX)]
            for esp, mois in fenetres_fraie(ctx_key, espece).items():
                fenetres.append(("m_saisonnier", esp, mois))

            for coef, esp, mois in fenetres:
                s = df[df["month"].isin(mois)].dropna(
                    subset=["T_eau_moy", "T_air"])
                p, _i, demi, r2, n, lag = newey_west(s["T_air"], s["T_eau_moy"])
                se = demi / 1.96 if (demi is not None
                                     and np.isfinite(demi)) else np.nan
                t = p / se if (np.isfinite(se) and se > 0) else np.nan
                exclut_zero = bool(np.isfinite(demi) and abs(p) > demi)
                dans_domaine = bool(np.isfinite(p) and 0.0 <= p <= 1.2)
                lignes.append(dict(
                    jeu=j["jeu"], point=pt, coefficient=coef, espece=esp,
                    mois="-".join(str(m) for m in mois), n=int(n),
                    pente=_f(p), demi_largeur_ic95=_f(demi),
                    erreur_type_newey_west=_f(se), t=_f(t), lag=int(lag),
                    r2=_f(r2),
                    ic95_exclut_zero="oui" if exclut_zero else "NON",
                    pente_dans_0_1_2="oui" if dans_domaine else "NON",
                    valide="oui" if (exclut_zero and dans_domaine) else "NON",
                    critere_rejetant=("" if (exclut_zero and dans_domaine)
                                      else " et ".join(
                                          ([] if exclut_zero
                                           else ["IC95 contient zero"])
                                          + ([] if dans_domaine
                                             else ["pente hors [0 ; 1,2]"])))))
            print(f"  · {j['jeu']}/{pt}", flush=True)

    ecrire_csv(OUT / "D1_validite_actuelle.csv",
               ["jeu", "point", "coefficient", "espece", "mois", "n", "pente",
                "demi_largeur_ic95", "erreur_type_newey_west", "t", "lag",
                "r2", "ic95_exclut_zero", "pente_dans_0_1_2", "valide",
                "critere_rejetant"],
               lignes, tri=["coefficient", "jeu", "point", "espece"])

    d = pd.DataFrame(lignes)
    print("\n" + "=" * 74)
    print("D1 — LES t ET LES IC, SUR L'ETAT ACTUEL DE LA CHAINE")
    print("=" * 74)
    for coef in ("m_estival", "m_saisonnier"):
        s = d[d.coefficient == coef]
        rej = s[s.valide == "NON"]
        print(f"\n  {coef} : {len(s)} estimations, {len(rej)} rejet(s)")
        for _, r in rej.iterrows():
            nom = r["point"] + (f" [{r['espece']}]" if r["espece"] else "")
            print(f"     {nom:<40} m={r['pente']:>8.4f}  t={r['t']:>7.3f}  "
                  f"n={r['n']:>4}  -> {r['critere_rejetant']}")
        ok = s[s.valide == "oui"].copy()
        ok["abs_t"] = ok["t"].abs()
        ok = ok.sort_values("abs_t")
        if len(ok):
            print(f"     les trois |t| les plus faibles parmi les VALIDES :")
            for _, r in ok.head(3).iterrows():
                nom = r["point"] + (f" [{r['espece']}]" if r["espece"] else "")
                print(f"        {nom:<40} t={r['t']:>7.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
