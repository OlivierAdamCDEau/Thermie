"""
mesure_correctif2.py — ÉTAPE 6, TÂCHES C3 et C4.

C1 a mesuré le défaut : une fenêtre de sept LIGNES n'est pas une fenêtre de
sept JOURS. Ce module traite les deux questions qui restent.

C3 — L'INVENTAIRE
-----------------
Toutes les fenêtres glissantes de `app/`, chacune avec son `fichier:ligne`,
sa position dans la chaîne `lecture → T_norm`, et son statut : corrigée par le
correctif 2, hors chaîne, ou déjà immunisée par construction. L'inventaire est
produit ici plutôt que rédigé à la main pour qu'il se refasse à l'identique.

C4 — LES BORDS
--------------
Sur un calendrier, `min_periods` cesse d'être une commodité de démarrage pour
devenir une exigence de DENSITÉ. `Tmh` demande 4 jours observés dans sa
fenêtre de 7 : une journée isolée au milieu d'une lacune n'en reçoit plus.
C'est le comportement voulu, mais il retire des valeurs, et ce qu'il retire se
compte :

  · combien de journées perdent `Tmh`, et donc `Tmh_norm` ;
  · où elles se trouvent — extrémités de chronique ou voisinage de lacune ;
  · ce que cela change à l'effectif sur lequel `pct_chr` est calculé.

`Delta_TMm_liss` (`min_periods=1`) est traité aussi, pour établir qu'il ne
perd rien : la journée est toujours dans sa propre fenêtre.

LE DÉTECTEUR DE PLATEAU
-----------------------
`qc.py:129` porte le même défaut. Il n'est PAS corrigé par le correctif 2 —
il décide des journées écartées, donc de `02_effectifs.csv` et de
`03_journees_ecartees.csv`, que la commande d'étape déclare FIGÉS. Ce module
mesure donc ce que sa correction changerait, sans l'appliquer : c'est ce
chiffre qui permettra de décider s'il fait l'objet d'un correctif à part.

Ce module ne modifie aucun fichier de `app/`. Il relit les séries et refait
les deux versions côte à côte, comme `mesure_index_positionnel.py`.

Sortie :
  out/etape6/C3_inventaire_fenetres.csv
  out/etape6/C4_bords.csv
  out/etape6/C4_bords_journees.csv
  out/etape6/C4_plateau_hors_perimetre.csv
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import ICI, RACINE, APP, decouvrir, ecrire_csv, nom_point, _f
from thermie_debits import io_data, core, qc as qcmod

OUT = RACINE / "out" / "etape6"

FENETRE_TMH = 7
MIN_PERIODS_TMH = 4


# ============================================================
# C3 — l'inventaire des fenêtres glissantes
# ============================================================
# Statut de chaque fenêtre, décidé sur le code et non sur une impression.
# `chaine` : la fenêtre est-elle dans le chemin lecture → T_norm, celui dont
# le correctif 2 est responsable.
INVENTAIRE = [
    dict(fichier="thermie_debits/core.py", symbole="fusionner → Tmh",
         fenetre="7", min_periods="4", index_avant="positionnel",
         dans_chaine_T_norm="oui", statut="CORRIGEE",
         justification="Tmh entre directement dans Tmh_norm = Tmh - m x "
                       "Delta_TMm_liss (core.py). C'est le coeur du correctif."),
    dict(fichier="thermie_debits/core.py", symbole="fusionner → Delta_TMm_liss",
         fenetre="lissage_delta (7)", min_periods="1", index_avant="positionnel",
         dans_chaine_T_norm="oui", statut="CORRIGEE",
         justification="Second terme de Tmh_norm, et de Tmax_norm. "
                       "Meme defaut, meme correction."),
    dict(fichier="thermie_debits/qc.py", symbole="marquer_qualite → plateau",
         fenetre="qc.plateau_fenetre (5)", min_periods="= fenetre",
         index_avant="positionnel",
         dans_chaine_T_norm="oui (en amont)", statut="NON CORRIGEE — hors perimetre",
         justification="Porte le meme defaut, mais decide des journees ECARTEES. "
                       "La corriger deplace 02_effectifs.csv, 03_journees_ecartees.csv "
                       "et 06_coefficients.csv, que la commande d'etape declare FIGES. "
                       "Effet mesure ci-dessous, correction laissee a un correctif propre."),
    dict(fichier="thermie_debits/io_data.py", symbole="calculer_normales_ecarts → lissage des normales",
         fenetre="2 x fenetre_lissage + 1", min_periods="1",
         index_avant="positionnel",
         dans_chaine_T_norm="oui", statut="SANS OBJET — deja continue",
         justification="S'applique a un index jour-de-l-annee 1..366 reconstruit "
                       "complet puis interpole (io_data.py, `idx` sur range(1,367)), "
                       "et triple pour la circularite. Aucune lacune possible : "
                       "l'index positionnel EST le calendrier."),
    dict(fichier="thermie_debits/core.py", symbole="corr_partielle_air → lissage_air",
         fenetre="lissage_air", min_periods="1", index_avant="positionnel",
         dans_chaine_T_norm="non", statut="NON CORRIGEE — hors chaine",
         justification="Analyse de la relation aux debits, en AVAL de T_norm. "
                       "Hors du chemin dont le correctif 2 repond, et hors perimetre."),
    dict(fichier="thermie_debits/indicateurs.py", symbole="Tmm30j",
         fenetre="30", min_periods="25", index_avant="positionnel",
         dans_chaine_T_norm="non", statut="NON CORRIGEE — hors chaine",
         justification="Indicateur calcule APRES T_norm, sur la serie deja "
                       "normalisee. Hors du chemin lecture → T_norm."),
]


def verifier_inventaire():
    """
    L'inventaire ci-dessus est écrit à la main ; on vérifie qu'il ne rate
    aucune fenêtre du code. Toute occurrence de `.rolling(` dans `app/` doit
    y correspondre.
    """
    trouvees = []
    for chemin in sorted(APP.rglob("*.py")):
        rel = chemin.relative_to(APP).as_posix()
        for n, ligne in enumerate(
                chemin.read_text(encoding="utf-8").splitlines(), 1):
            if ".rolling(" in ligne:
                trouvees.append((rel, n, ligne.strip()))
    return trouvees


# ============================================================
# outils communs
# ============================================================
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


def _calendrier(dates, valeurs):
    s = pd.Series(np.asarray(valeurs, dtype=float),
                  index=pd.to_datetime(pd.Series(dates).to_numpy()))
    plein = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"))
    return s, plein


def rolling_calendaire(dates, valeurs, fenetre, min_periods, fonction="mean"):
    s, plein = _calendrier(dates, valeurs)
    r = plein.rolling(window=fenetre, center=True, min_periods=min_periods)
    liss = r.std() if fonction == "std" else r.mean()
    return liss.reindex(s.index).to_numpy()


def distance_au_bord(dates):
    """Nombre de jours observés dans la fenêtre calendaire de +/- 3 jours."""
    d = pd.to_datetime(pd.Series(dates).to_numpy())
    s = pd.Series(1.0, index=d)
    plein = s.reindex(pd.date_range(d.min(), d.max(), freq="D"))
    dens = plein.rolling(window=FENETRE_TMH, center=True, min_periods=1).count()
    return dens.reindex(d).to_numpy()


# ============================================================
def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------- C3
    ecrire_csv(OUT / "C3_inventaire_fenetres.csv",
               ["fichier", "symbole", "fenetre", "min_periods", "index_avant",
                "dans_chaine_T_norm", "statut", "justification"],
               INVENTAIRE, tri=["fichier", "symbole"])
    trouvees = verifier_inventaire()
    print(f"C3 — {len(trouvees)} occurrence(s) de `.rolling(` dans app/, "
          f"{len(INVENTAIRE)} ligne(s) d'inventaire.")
    for rel, n, ligne in trouvees:
        print(f"    {rel}:{n}  {ligne[:78]}")
    if len(trouvees) != len(INVENTAIRE):
        print("    ATTENTION : l'inventaire ne couvre pas exactement le code.")

    # ---------------------------------------------------- C4
    bords, journees, plateau = [], [], []

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

            # --- le detecteur de plateau, AVANT le controle qualite
            dd = daily.sort_values("date").reset_index(drop=True)
            w = qd["plateau_fenetre"]
            std_pos = dd["T_eau_moy"].rolling(window=w, center=True,
                                              min_periods=w).std()
            std_cal = rolling_calendaire(dd["date"], dd["T_eau_moy"], w, w,
                                         fonction="std")
            seuil = qd["plateau_ecart_type_min"]
            m_pos = (std_pos < seuil).fillna(False).to_numpy()
            m_cal = pd.Series(std_cal < seuil).fillna(False).to_numpy()
            plateau.append(dict(
                jeu=j["jeu"], point=pt, n_journees=len(dd),
                marquees_index_positionnel=int(m_pos.sum()),
                marquees_index_calendaire=int(m_cal.sum()),
                verdicts_changes=int((m_pos != m_cal).sum()),
                perdues_si_corrige=int((m_pos & ~m_cal).sum()),
                gagnees_si_corrige=int((~m_pos & m_cal).sum())))

            propre, _rap = qcmod.controle_qualite(daily, air, qd, verbose=False)
            try:
                df = core.fusionner(propre, air, ecart, normales,
                                    df_debits=None, lissage_delta=lissage)
            except ValueError:
                bords.append(dict(jeu=j["jeu"], point=pt, statut="chaine interrompue",
                                  n_journees=0))
                continue
            df = df.sort_values("date").reset_index(drop=True)
            n = len(df)

            tmh_pos = df["T_eau_moy"].rolling(window=FENETRE_TMH,
                                              min_periods=MIN_PERIODS_TMH,
                                              center=True).mean().to_numpy()
            tmh_cal = rolling_calendaire(df["date"], df["T_eau_moy"],
                                         FENETRE_TMH, MIN_PERIODS_TMH)
            dl_pos = df["Delta_TMm"].rolling(window=lissage, min_periods=1,
                                             center=True).mean().to_numpy()
            dl_cal = rolling_calendaire(df["date"], df["Delta_TMm"], lissage, 1)

            perdues = np.isfinite(tmh_pos) & ~np.isfinite(tmh_cal)
            gagnees = ~np.isfinite(tmh_pos) & np.isfinite(tmh_cal)
            dens = distance_au_bord(df["date"])

            # Une journee perdue est-elle a l'extremite de la chronique, ou au
            # voisinage d'une lacune interne ? On tranche par la position.
            pos = np.arange(n)
            extremite = (pos < FENETRE_TMH) | (pos >= n - FENETRE_TMH)

            bords.append(dict(
                jeu=j["jeu"], point=pt, statut="OK", n_journees=n,
                Tmh_defini_positionnel=int(np.isfinite(tmh_pos).sum()),
                Tmh_defini_calendaire=int(np.isfinite(tmh_cal).sum()),
                journees_perdues=int(perdues.sum()),
                part_perdue_pct=_f(100.0 * perdues.sum() / max(n, 1)),
                perdues_en_extremite=int((perdues & extremite).sum()),
                perdues_pres_dune_lacune=int((perdues & ~extremite).sum()),
                journees_gagnees=int(gagnees.sum()),
                delta_liss_defini_positionnel=int(np.isfinite(dl_pos).sum()),
                delta_liss_defini_calendaire=int(np.isfinite(dl_cal).sum()),
                delta_liss_perdues=int((np.isfinite(dl_pos)
                                        & ~np.isfinite(dl_cal)).sum())))

            for i in np.nonzero(perdues)[0]:
                journees.append(dict(
                    jeu=j["jeu"], point=pt, date=str(df["date"].iloc[i]),
                    jours_observes_dans_la_fenetre=int(dens[i]),
                    en_extremite_de_chronique=bool(extremite[i]),
                    Tmh_positionnel_abandonne=_f(float(tmh_pos[i]))))

            print(f"  · {j['jeu']}/{pt} : {int(perdues.sum())}/{n} journees "
                  f"perdent Tmh, {int((m_pos != m_cal).sum())} verdicts de "
                  f"plateau changeraient", flush=True)

    ecrire_csv(OUT / "C4_bords.csv",
               ["jeu", "point", "statut", "n_journees",
                "Tmh_defini_positionnel", "Tmh_defini_calendaire",
                "journees_perdues", "part_perdue_pct", "perdues_en_extremite",
                "perdues_pres_dune_lacune", "journees_gagnees",
                "delta_liss_defini_positionnel", "delta_liss_defini_calendaire",
                "delta_liss_perdues"],
               bords, tri=["jeu", "point"])
    ecrire_csv(OUT / "C4_bords_journees.csv",
               ["jeu", "point", "date", "jours_observes_dans_la_fenetre",
                "en_extremite_de_chronique", "Tmh_positionnel_abandonne"],
               journees, tri=["jeu", "point", "date"])
    ecrire_csv(OUT / "C4_plateau_hors_perimetre.csv",
               ["jeu", "point", "n_journees", "marquees_index_positionnel",
                "marquees_index_calendaire", "verdicts_changes",
                "perdues_si_corrige", "gagnees_si_corrige"],
               plateau, tri=["jeu", "point"])

    ok = [b for b in bords if b["statut"] == "OK"]
    tot = sum(b["n_journees"] for b in ok)
    perd = sum(b["journees_perdues"] for b in ok)
    print("\n=== C4 — SYNTHESE DES BORDS ===")
    print(f"  {len(ok)} points, {tot} journees")
    print(f"  journees qui perdent Tmh : {perd} ({100*perd/max(tot,1):.2f} %)")
    print(f"    dont en extremite de chronique : "
          f"{sum(b['perdues_en_extremite'] for b in ok)}")
    print(f"    dont au voisinage d'une lacune : "
          f"{sum(b['perdues_pres_dune_lacune'] for b in ok)}")
    print(f"  journees gagnees          : {sum(b['journees_gagnees'] for b in ok)}")
    print(f"  Delta_TMm_liss perdues    : "
          f"{sum(b['delta_liss_perdues'] for b in ok)} (min_periods=1)")
    print(f"  points concernes          : "
          f"{sum(1 for b in ok if b['journees_perdues'] > 0)}")
    print("\n=== DETECTEUR DE PLATEAU (hors perimetre du correctif 2) ===")
    print(f"  verdicts qui changeraient si on le corrigeait : "
          f"{sum(p['verdicts_changes'] for p in plateau)}")
    print(f"    journees qui cesseraient d'etre marquees : "
          f"{sum(p['perdues_si_corrige'] for p in plateau)}")
    print(f"    journees qui seraient marquees en plus   : "
          f"{sum(p['gagnees_si_corrige'] for p in plateau)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
