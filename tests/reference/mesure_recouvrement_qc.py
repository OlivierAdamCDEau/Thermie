"""
mesure_recouvrement_qc.py — ÉTAPE 5, TÂCHE C.

CE QUE LE MARQUAGE REND MESURABLE
----------------------------------
Avant le correctif 3, une journée écartée par deux détecteurs ne portait que
le motif du premier : la contribution du second était perdue, et la question
« combien de journées deux détecteurs marquent-ils ensemble ? » n'avait aucune
réponse dans les sorties. Elle en a une maintenant.

Rien n'est corrigé ici. On compte.

La mesure est faite sur les DEUX régimes, parce qu'ils n'exercent pas les
mêmes détecteurs :
  - régime APPLICATION (10 °C, sans exclusion de saison) : 91 journées écartées ;
  - régime CLI (4 °C, avec exclusion de saison) : 8 565 journées écartées,
    et c'est là que le recouvrement a le plus de chances d'exister.

Le code exécuté est celui de `app/` — c'est lui qui porte le marquage.

Sortie :
  out/etape5/recouvrement_qc.csv          par regime, par combinaison de motifs
  out/etape5/recouvrement_qc_par_point.csv
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from itertools import combinations

import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import ICI, RACINE, decouvrir, ecrire_csv, nom_point, _f, CODE
from parametres import jeu_de_parametres
from thermie_debits import io_data, qc as qcmod

OUT = RACINE / "out" / "etape5"

# Famille d'un motif : le detecteur qui l'a produit.
FAMILLES = [
    ("hors bornes", "bornes physiques"),
    ("plateau", "plateau / sonde bloquee"),
    ("hors d'eau", "sonde hors d'eau"),
    ("outlier MAD", "outliers MAD"),
]


def famille(motif: str) -> str:
    for prefixe, nom in FAMILLES:
        if motif.startswith(prefixe):
            return nom
    return "autre"


def qc_dict(par):
    # jeu_de_parametres rend des triplets (valeur, provenance, justification) ;
    # seule la valeur nous interesse ici.
    q = {k: v[0] for k, v in par["qc"].items()}
    return {
        "bornes_physiques": q["bornes_physiques"],
        "T_eau_min": q["t_eau_min"], "T_eau_max": q["t_eau_max"],
        "hors_eau": q["hors_eau"],
        "hors_eau_ecart_seuil": q["hors_eau_ecart_seuil"],
        "hors_eau_mois": list(q["hors_eau_mois"]),
        "hors_eau_min_jours": q["hors_eau_min_jours"],
        "hors_eau_exclut_saison": q["hors_eau_exclut_saison"],
        "plateau": q["plateau"], "plateau_fenetre": q["plateau_fenetre"],
        "plateau_ecart_type_min": q["plateau_ecart_type_min"],
        "mad_outliers": q["mad_outliers"], "mad_k": q["mad_k"],
        "mad_mois": q["mad_mois"],
    }


def main():
    if CODE != "app":
        print("ERREUR : cette mesure exige le code de app/ (THERMIE_CODE=app), "
              "seul a porter le marquage.", file=sys.stderr)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)

    lignes, par_point, croises = [], [], []
    for chemin in ("application", "cli"):
        total = Counter()
        n_ecarte = n_multi = n_lues = n_nd = 0
        paires = Counter()
        for j in decouvrir():
            if not j["air"]:
                continue
            par = jeu_de_parametres(chemin, j["jeu"])
            qd = qc_dict(par)
            air = io_data.charger_air_brut(str(RACINE / j["air"]))
            for point_rel in j["points"]:
                pt = nom_point(point_rel)
                daily = io_data.charger_eau(str(RACINE / point_rel),
                                            nom=point_rel.split("/")[-1])
                marques = qcmod.marquer_qualite(daily, air, qd, verbose=False)
                n_lues += len(marques)
                nd = int((marques["statut"]
                          == qcmod.STATUT_NON_DIAGNOSTICABLE).sum())
                n_nd += nd
                ec = marques[marques["statut"] == qcmod.STATUT_ECARTE]
                n_ecarte += len(ec)
                fam = ec["motifs"].apply(
                    lambda ms: tuple(sorted({famille(m) for m in ms})))
                multi = int((fam.apply(len) > 1).sum())
                n_multi += multi
                for f in fam:
                    total[f] += 1
                    for a, b in combinations(f, 2):
                        paires[(a, b)] += 1
                par_point.append(dict(
                    regime=chemin, jeu=j["jeu"], point=pt,
                    journees_lues=int(len(marques)),
                    journees_ecartees=int(len(ec)),
                    journees_a_plusieurs_motifs=multi,
                    journees_non_diagnosticables=nd,
                    part_multi_pct=_f(100.0 * multi / max(len(ec), 1))))
                print(f"  · [{chemin}] {j['jeu']}/{pt} : {len(ec)} ecartees, "
                      f"{multi} a plusieurs motifs", flush=True)

        for combi, n in sorted(total.items(), key=lambda x: (-x[1], x[0])):
            lignes.append(dict(
                regime=chemin, n_detecteurs=len(combi),
                combinaison=" + ".join(combi), journees=n,
                part_des_ecartees_pct=_f(100.0 * n / max(n_ecarte, 1))))
        for (a, b), n in sorted(paires.items(), key=lambda x: -x[1]):
            croises.append(dict(regime=chemin, detecteur_a=a, detecteur_b=b,
                                journees_communes=n,
                                part_des_ecartees_pct=_f(100.0 * n / max(n_ecarte, 1))))
        lignes.append(dict(
            regime=chemin, n_detecteurs=-1, combinaison="TOTAL",
            journees=n_ecarte, part_des_ecartees_pct=_f(100.0)))
        print(f"\n  [{chemin}] {n_lues} journees lues, {n_ecarte} ecartees, "
              f"{n_multi} a plusieurs motifs "
              f"({100*n_multi/max(n_ecarte,1):.2f} %), "
              f"{n_nd} non diagnosticables\n", flush=True)

    ecrire_csv(OUT / "recouvrement_qc.csv",
               ["regime", "n_detecteurs", "combinaison", "journees",
                "part_des_ecartees_pct"], lignes,
               tri=["regime", "n_detecteurs", "combinaison"])
    ecrire_csv(OUT / "recouvrement_qc_croisements.csv",
               ["regime", "detecteur_a", "detecteur_b", "journees_communes",
                "part_des_ecartees_pct"], croises,
               tri=["regime", "detecteur_a", "detecteur_b"])
    ecrire_csv(OUT / "recouvrement_qc_par_point.csv",
               ["regime", "jeu", "point", "journees_lues", "journees_ecartees",
                "journees_a_plusieurs_motifs", "journees_non_diagnosticables",
                "part_multi_pct"], par_point, tri=["regime", "jeu", "point"])

    print("=== Combinaisons de detecteurs ===")
    for l in lignes:
        if l["n_detecteurs"] == -1:
            print(f"  [{l['regime']}] TOTAL ecartees : {l['journees']}")
            continue
        print(f"  [{l['regime']}] {l['n_detecteurs']} detecteur(s) : "
              f"{l['combinaison']:<52} {l['journees']:>6} "
              f"({l['part_des_ecartees_pct']:>5.2f} %)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
