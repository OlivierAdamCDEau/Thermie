"""
verifier_test_de_signe.py — ETAPE 20 : D111, le second membre comme TEST DE SIGNE.

RIEN N'EST POSE PAR CE SCRIPT. Il mesure, sur l'etat actuel de `app/`, ce que
le second membre ferait. La pose n'a lieu que si le test SEPARE les deux
populations ; sinon on s'arrete et on remonte, sans chercher un seuil qui
separerait.

================================================================================
LE SECOND MEMBRE, ET POURQUOI IL N'A PAS DE SEUIL
================================================================================
D111 : `T_eau_max` STRICTEMENT AU-DESSUS de la mediane propre du point ET du
mois. Zero n'est pas un seuil calibre — c'est la frontiere du phenomene.

Le second membre n'a pas a detecter. Il repond a une seule question :

    ce decouplage vient-il de l'eau qui monte, ou de l'air qui descend ?

La marche 1 mesure `T_eau_max - T_air` et ne sait pas lequel des deux termes a
bouge. En juillet l'ambiguite est sans effet ; le 1er juin 2011, avec l'air a
4,6 degC sous le 5e centile de sa fenetre, elle a marque sept sondes d'un meme
bassin dont l'eau etait a ou sous sa mediane de juin. Le second membre tranche
cette ambiguite, et rien d'autre.

D112 : ce membre REPARE UN DEFAUT DU CORRECTIF 1, decouvert par mesure. Il
n'est pas un ajout lie a l'extension de fenetre.

================================================================================
CE QUI SERT DE GROUPE, ET CE QUI SE PASSE QUAND IL EST TROP MINCE
================================================================================
Le groupe est le couple (point, mois), le meme que `relativiser` emploie deja.

GARDE-FOU RETENU, DECLARE AVANT DE MESURER : le groupe doit compter au moins
`min_jours_groupe` journees — le parametre existant, aucun nouveau. Le garde-fou
de DISPERSION (`plancher_dispersion`) n'est PAS repris : il existe parce que
`relativiser` DIVISE par le MAD, et un MAD nul fait exploser le quotient. Un
test de signe ne divise pas. Exiger une dispersion minimale pour comparer a une
mediane ajouterait une condition que la question ne demande pas.

La variante « garde-fou de dispersion repris » est calculee A COTE, comme
sensibilite, et NE SERT PAS A DECIDER.

Quand le groupe est trop mince, le second membre NE SE PRONONCE PAS. La
conjonction ne peut alors pas etre evaluee : ces journees sont relevees et
nommees (D100), et le present script dit combien il y en a et ou.

================================================================================
LES QUATRE PREDICTIONS — ECRITES AVANT LES CHIFFRES
================================================================================
  P1  Les journees de coup de froid disparaissent, l'eau y etant a ou sous sa
      mediane. Le 1er juin 2011, LA PLAINE (rel 3,29) SURVIT ; les sept sondes
      de la Bienne non. UNE EXCEPTION EST ATTENDUE : BIE37-9 est a +0,10, donc
      au-dessus de zero, et devrait survivre. Une fuite d'une journee sur sept
      est un resultat, pas un echec.

  P2  Les 73 journees de saison froide disparaissent : l'excursion du temoin
      d'etape 19 y est negative sur les 65 mesurables.

  P3  Les 15 journees de mai corroborees survivent — Gorze, La Canner, la
      Flotte. Leur bloc contamine sa propre mediane et reduit leur ecart, mais
      il ne devrait pas le rendre negatif. C'EST LA PREDICTION LA PLUS
      INCERTAINE DES TROIS. Si elle tombe, D114 mord plus fort que prevu et il
      faut le dire.

  P4  Les 31 journees estivales corroborees par le temoin survivent toutes.

Un ecart entre prediction et constat est un resultat a comprendre. Il ne sera
ni arrondi, ni rattrape apres coup.

================================================================================
LE CRITERE DE POSE
================================================================================
    les coups de froid tombent, ET les corroborees survivent.

Si le signe ne separe pas ces deux populations, le script le dit et NE PROPOSE
AUCUN SEUIL DE REMPLACEMENT. Calibrer un nombre sur ce corpus est precisement
ce que tout le chantier a corrige.

SORTIES, sous out/etape20/
  S_69.csv            les 69 journees estivales, test de signe et temoin
  S_nouvelles.csv     les 163 ajoutees par l'extension
  S_nommees.csv       les journees nommees par l'arbitrage
  S_abstentions.csv   les (point, mois) ou le second membre ne se prononce pas
"""
from __future__ import annotations

import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
os.environ.setdefault("THERMIE_CODE", "app")

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f       # noqa: E402

import build_reference                                                 # noqa: E402
from thermie_debits import io_data as io, qc as qcmod                  # noqa: E402

OUT = RACINE / "out" / "etape20"
ETE = (6, 7, 8, 9)
FROIDS = (10, 11, 12, 1, 2, 3, 4)

# Les journees que l'arbitrage nomme.
COUPS_DE_FROID = {"2011-06-01": 8, "2017-06-29": 6, "2019-06-06": 2}
MAI_CORROBOREES = [
    ("Le ruisseau de Gorze à Gorze", d) for d in
    ("2021-05-13", "2021-05-14", "2021-05-15", "2021-05-17", "2021-05-26")
] + [
    ("SN 21069646 - La Canner à Vigy 1", d) for d in
    ("2021-05-13", "2021-05-15", "2021-05-16")
] + [
    ("Le ruisseau de la Flotte à Château-Voue", d) for d in
    ("2021-05-10", "2021-05-18", "2021-05-19", "2021-05-22", "2021-05-23",
     "2021-05-24")
] + [("BIE46-5", "2017-05-19")]


def table_qc(cfg):
    """La table de `marquer_qualite`, reproduite a l'identique (qc.py:238)."""
    daily, _s, _m = io.marquer_lecture(
        cfg.sources.fichier_eau, col_date=cfg.sources.eau_col_date,
        col_temp=cfg.sources.eau_col_temp, nom=cfg.sources.eau_nom_fichier,
        feuille=cfg.sources.eau_feuille,
        ligne_entete=cfg.sources.eau_ligne_entete,
        retour_sous_quotidien=True)
    air = io.charger_air_brut(cfg.sources.fichier_air,
                              col_date=cfg.sources.air_col_date,
                              col_temp=cfg.sources.air_col_temp,
                              station_code=cfg.sources.air_station_code,
                              station_nom=cfg.sources.air_station_nom)
    df = daily.merge(air, on="date", how="left").copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df["month"] = df["date_dt"].dt.month
    return df.sort_values("date_dt").reset_index(drop=True)


def test_de_signe(df, qc):
    """
    Rend (ecart_a_la_mediane, se_prononce, mediane_du_groupe) et la variante
    qui reprend le garde-fou de dispersion.

    `ecart > 0` est le test. Aucun seuil : la frontiere est zero.
    """
    n_min = qc["min_jours_groupe"]
    plancher = qc["plancher_dispersion"]
    v = df["T_eau_max"]
    ecart = pd.Series(np.nan, index=df.index, dtype=float)
    med_g = pd.Series(np.nan, index=df.index, dtype=float)
    dit = pd.Series(False, index=df.index)
    dit_var = pd.Series(False, index=df.index)
    for _m, idx in v[v.notna()].groupby(df["month"][v.notna()]).groups.items():
        x = v.loc[idx]
        if len(x) < n_min:
            continue
        med = float(x.median())
        mad = qcmod.FACTEUR_MAD * float((x - med).abs().median())
        ecart.loc[idx] = x - med
        med_g.loc[idx] = med
        dit.loc[idx] = True
        dit_var.loc[idx] = bool(mad > plancher)
    return ecart, dit, med_g, dit_var


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("ETAPE 20 — D111 : LE SECOND MEMBRE COMME TEST DE SIGNE")
    print("Rien n'est pose. Zero n'est pas un seuil : c'est la frontiere.")
    print("=" * 78)

    a18 = pd.read_csv(RACINE / "out" / "etape18" / "A_toutes_marquees.csv",
                      sep=";", encoding="utf-8")
    deja = {(r.point, str(r.date)[:10]) for r in a18.itertuples()}
    ains = pd.read_csv(RACINE / "out" / "etape18" / "A_sous_ensemble.csv",
                       sep=";", encoding="utf-8")
    c27 = {(r.point, str(r.date)[:10]) for r in ains.itertuples()}
    nouv = pd.read_csv(OUT / "B_nouvelles.csv", sep=";", encoding="utf-8")
    nv = {(r.point, str(r.date)[:10]): r.temoin for r in nouv.itertuples()}
    pop = pd.read_csv(RACINE / "out" / "etape19" / "B_populations.csv",
                      sep=";", encoding="utf-8")
    tem = {(r.point, r.date): r.verdict for r in pop.itertuples()}

    l69, lnv, labs = [], [], []
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            cibles = ({d for (p, d) in deja if p == pt}
                      | {d for (p, d) in nv if p == pt})
            cfg = build_reference.construire_config(jeu, point_rel,
                                                    "application")
            qc = cfg.qc.to_legacy_dict()
            try:
                df = table_qc(cfg)
            except Exception as exc:
                print(f"  · {jeu['jeu']}/{pt} : ECHEC ({type(exc).__name__})",
                      flush=True)
                continue
            df["ds"] = df["date"].astype(str).str.slice(0, 10)
            ecart, dit, med_g, dit_var = test_de_signe(df, qc)

            for m, sub in df.groupby("month"):
                if not bool(dit.loc[sub.index].any()):
                    labs.append(dict(
                        jeu=jeu["jeu"], point=pt, mois=int(m),
                        n_journees=int(df.loc[sub.index, "T_eau_max"].notna().sum()),
                        min_requis=qc["min_jours_groupe"],
                        motif="effectif insuffisant — le second membre ne se "
                              "prononce pas"))

            for i, r in df.iterrows():
                ds = r["ds"]
                if ds not in cibles:
                    continue
                e, d_, mg, dv = (ecart.loc[i], bool(dit.loc[i]),
                                 med_g.loc[i], bool(dit_var.loc[i]))
                survit = ("oui" if (d_ and np.isfinite(e) and e > 0)
                          else ("NON" if d_ else "ne se prononce pas"))
                ligne = dict(
                    jeu=jeu["jeu"], point=pt, date=ds, mois=int(r["month"]),
                    T_eau_max=_f(r.get("T_eau_max")),
                    mediane_du_groupe=_f(mg), ecart_a_la_mediane=_f(e),
                    T_air=_f(r.get("T_air")),
                    se_prononce=("oui" if d_ else "NON"),
                    survit=survit,
                    variante_avec_plancher=("oui" if (dv and np.isfinite(e)
                                                      and e > 0) else "NON"),
                    temoin=tem.get((pt, ds), "absent"))
                if (pt, ds) in deja:
                    ligne["groupe_etape18"] = ("les 27 instruites"
                                               if (pt, ds) in c27 else "les 42")
                    l69.append(ligne)
                else:
                    ligne["saison"] = ("mai" if int(r["month"]) == 5 else
                                       ("saison froide" if int(r["month"]) in FROIDS
                                        else "estivale"))
                    lnv.append(ligne)
            print(f"  · {jeu['jeu']}/{pt}", flush=True)

    cols = ["jeu", "point", "date", "mois", "T_eau_max", "mediane_du_groupe",
            "ecart_a_la_mediane", "T_air", "se_prononce", "survit",
            "variante_avec_plancher", "temoin"]
    ecrire_csv(OUT / "S_69.csv", cols + ["groupe_etape18"], l69,
               tri=["jeu", "point", "date"])
    ecrire_csv(OUT / "S_nouvelles.csv", cols + ["saison"], lnv,
               tri=["saison", "jeu", "point", "date"])
    ecrire_csv(OUT / "S_abstentions.csv",
               ["jeu", "point", "mois", "n_journees", "min_requis", "motif"],
               labs, tri=["jeu", "point", "mois"])

    d69, dnv = pd.DataFrame(l69), pd.DataFrame(lnv)

    def tableau(d, titre):
        print(f"\n  {titre}")
        if not len(d):
            print("     (aucune)")
            return
        t = pd.crosstab(d.survit, d.temoin)
        print("     " + t.to_string().replace("\n", "\n     "))

    print("\n" + "=" * 78)
    print("1 — LES 69 JOURNEES ESTIVALES")
    print("=" * 78)
    n_s = int((d69.survit == "oui").sum())
    print(f"  survivent au test de signe : {n_s} / {len(d69)}")
    print(f"  tombent                    : {int((d69.survit == 'NON').sum())}")
    print(f"  second membre muet         : "
          f"{int((d69.survit == 'ne se prononce pas').sum())}")
    tableau(d69, "croisement avec le temoin scelle de l'etape 19 :")
    print("\n     par groupe d'etape 18 :")
    print("     " + pd.crosstab(d69.groupe_etape18,
                                d69.survit).to_string().replace("\n", "\n     "))

    print("\n" + "=" * 78)
    print("2 — LES 163 JOURNEES AJOUTEES PAR L'EXTENSION")
    print("=" * 78)
    for sais in ("mai", "saison froide", "estivale"):
        sub = dnv[dnv.saison == sais]
        if not len(sub):
            continue
        print(f"\n  {sais.upper()} — {len(sub)} ajoutees, "
              f"{int((sub.survit == 'oui').sum())} survivent, "
              f"{int((sub.temoin == 'artefact').sum())} corroborees")
        tableau(sub, "croisement :")

    print("\n" + "=" * 78)
    print("3 — LES JOURNEES NOMMEES PAR L'ARBITRAGE")
    print("=" * 78)
    nommees = []
    for date, n_att in COUPS_DE_FROID.items():
        sub = d69[d69.date == date]
        print(f"\n  COUP DE FROID DU {date} — {len(sub)} journee(s) "
              f"(annonce : {n_att})")
        for _, r in sub.sort_values("point").iterrows():
            print(f"     {r['point']:<34} T_eau_max {r['T_eau_max']:>7} "
                  f"mediane {r['mediane_du_groupe']:>7} "
                  f"ecart {r['ecart_a_la_mediane']:>8}  air {r['T_air']:>6}  "
                  f"-> {r['survit']}")
            nommees.append(dict(r, categorie=f"coup de froid {date}"))
    print(f"\n  LES 15 JOURNEES DE MAI CORROBOREES")
    for pt, ds in MAI_CORROBOREES:
        sub = dnv[(dnv.point == pt) & (dnv.date == ds)]
        if not len(sub):
            print(f"     {pt:<40} {ds}  INTROUVABLE")
            continue
        r = sub.iloc[0]
        print(f"     {pt:<40} {ds}  ecart {r['ecart_a_la_mediane']:>8} "
              f"-> {r['survit']}")
        nommees.append(dict(r, categorie="mai corroboree"))
    froides = dnv[dnv.saison == "saison froide"]
    print(f"\n  LES {len(froides)} JOURNEES DE SAISON FROIDE : "
          f"{int((froides.survit == 'oui').sum())} survivent, "
          f"{int((froides.survit == 'NON').sum())} tombent, "
          f"{int((froides.survit == 'ne se prononce pas').sum())} sans verdict")
    if int((froides.survit == "oui").sum()):
        for _, r in froides[froides.survit == "oui"].iterrows():
            print(f"     SURVIT : {r['point']:<34} {r['date']}  "
                  f"ecart {r['ecart_a_la_mediane']}  air {r['T_air']}")
            nommees.append(dict(r, categorie="saison froide survivante"))
    ecrire_csv(OUT / "S_nommees.csv", cols + ["categorie"], nommees,
               tri=["categorie", "point", "date"])

    print("\n" + "=" * 78)
    print("LES QUATRE PREDICTIONS, CONFRONTEES")
    print("=" * 78)
    p1 = d69[d69.date == "2011-06-01"]
    p1_surv = p1[p1.survit == "oui"]
    print(f"  P1 — 1er juin 2011 : {len(p1_surv)} survivante(s) sur {len(p1)}")
    for _, r in p1_surv.iterrows():
        print(f"       {r['point']:<34} ecart {r['ecart_a_la_mediane']}")
    print(f"  P2 — saison froide : "
          f"{int((froides.survit == 'NON').sum())} / {len(froides)} tombent")
    mc = pd.DataFrame([n for n in nommees if n["categorie"] == "mai corroboree"])
    if len(mc):
        print(f"  P3 — mai corroborees : "
              f"{int((mc.survit == 'oui').sum())} / {len(mc)} survivent")
    cor = d69[d69.temoin == "artefact"]
    print(f"  P4 — estivales corroborees : "
          f"{int((cor.survit == 'oui').sum())} / {len(cor)} survivent")

    print("\n" + "=" * 78)
    print("LE CRITERE DE POSE")
    print("=" * 78)
    froid_tombe = (int((froides.survit == "NON").sum()) == len(froides)
                   if len(froides) else True)
    cor_survit = int((cor.survit == "oui").sum()) == len(cor)
    print(f"  les coups de froid tombent   : "
          f"{'OUI' if froid_tombe else 'NON'}")
    print(f"  les corroborees survivent    : "
          f"{'OUI' if cor_survit else 'NON'}")
    print(f"  -> {'LE SIGNE SEPARE : POSER' if (froid_tombe and cor_survit) else 'A INSTRUIRE AVANT DE POSER'}")

    print("\n" + "=" * 78)
    print("LES ABSTENTIONS")
    print("=" * 78)
    da = pd.DataFrame(labs)
    print(f"  couples (point, mois) : {len(da)}")
    if len(da):
        for _, r in da.iterrows():
            print(f"     {r['point']:<34} mois {r['mois']:>2} : "
                  f"{r['n_journees']} journee(s) < {r['min_requis']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
