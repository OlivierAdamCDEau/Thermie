"""
chiffrer_correctif13.py — ETAPE 20 : les trois chiffrages demandes, apres pose.

AUCUNE MODIFICATION APPLICATIVE. Ce script lit les artefacts des deux rejeux
— `out/etape17/rejeu_final` (avant) et `out/etape20/rejeu_apres` (apres) — et
les confronte. Il ne rejoue rien : les artefacts sont la mesure.

  1  L'effet des journees estivales qui RENTRENT dans l'analyse : par point,
     ecart sur `m_estival`, sur la mediane et le p95 de `Tmh_norm`, et
     verdicts. C'est le SEUL endroit ou le correctif 13 peut degrader ce que
     les etapes 18 et 19 ont valide (D118).

  2  L'effet des journees qui S'AJOUTENT sur `m_saisonnier_fraie`, par point ET
     PAR ESPECE. C'est le premier correctif du chantier a atteindre le
     coefficient de fraie.

  3  Les journees de coup de froid marginal retenues : touchent-elles une
     fenetre de fraie ? C'est le cout de la fuite declaree par D117, et il doit
     etre ecrit, pas estime.

UNE CORRECTION DE COMPTAGE, APPLIQUEE ICI
Les journees marquees sont comptees sur `motifs_complets`, la chaine COMPLETE
des motifs, et non sur `motif`, la vue heritee ou une journee ne porte que son
PREMIER motif. Compter sur `motif` sous-estime le total des journees qu'un
detecteur anterieur avait deja touchees — c'est l'erreur des etapes 18, 19 et
20, corrigee a la source dans `build_reference.py`. Le compte « avant » est
donc lui aussi recalcule sur la meme base, faute de quoi les deux cotes ne
seraient pas comparables.

SORTIES, sous out/etape20/
  R1_journees_estivales.csv   les journees estivales qui changent d'etat
  R1_m_estival.csv            m_estival, Tmh_norm mediane et p95, par point
  R2_m_saisonnier.csv         m_saisonnier par point et par espece
  R3_fuite_fraie.csv          les journees de la fuite, et leur fenetre de fraie
  R4_marquees.csv             le compte des journees marquees, des deux cotes
"""
from __future__ import annotations

import glob
import sys

import numpy as np
import pandas as pd

from _commun import RACINE, ecrire_csv, _f

OUT = RACINE / "out" / "etape20"
AVANT = RACINE / "out" / "etape17" / "rejeu_final"
APRES = OUT / "rejeu_apres"
ETE = (6, 7, 8, 9)

# Fenetres de reproduction, telles que `config.py` les porte.
FRAIE = {"truite fario": [1, 2, 3, 10, 11, 12], "ombre commun": [3, 4, 5],
         "barbeau": [4, 5, 6, 7], "brochet": [2, 3, 4], "brème": [4, 5, 6, 7]}


def lire(dossier, nom):
    fs = sorted(glob.glob(str(dossier / "*" / nom)))
    if not fs:
        return pd.DataFrame()
    d = []
    for f in fs:
        x = pd.read_csv(f, sep=";", encoding="utf-8")
        x["jeu"] = f.replace("\\", "/").split("/")[-2]
        d.append(x)
    return pd.concat(d, ignore_index=True)


def marquees(d):
    """Les journees marquees hors d'eau, comptees sur la chaine COMPLETE."""
    if not len(d):
        return set()
    col = "motifs_complets" if "motifs_complets" in d.columns else "motif"
    m = d[d[col].astype(str).str.contains("hors d", na=False)]
    return set(zip(m["point"], m["date"].astype(str).str.slice(0, 10)))


def main():
    a03_av, a03_ap = lire(AVANT, "03_journees_ecartees.csv"), lire(APRES, "03_journees_ecartees.csv")
    a06_av, a06_ap = lire(AVANT, "06_coefficients.csv"), lire(APRES, "06_coefficients.csv")
    a07_av, a07_ap = lire(AVANT, "07_t_norm.csv"), lire(APRES, "07_t_norm.csv")
    a08_av, a08_ap = lire(AVANT, "08_scores.csv"), lire(APRES, "08_scores.csv")

    print("=" * 78)
    print("ETAPE 20 — CHIFFRAGE DU CORRECTIF 13, APRES POSE")
    print("=" * 78)

    # ---------------- 0 : le compte, sur base comparable
    mav, map_ = marquees(a03_av), marquees(a03_ap)
    mav_h = marquees(a03_av.assign(**{"motifs_complets": a03_av["motif"]}))
    print(f"\n  journees marquees AVANT (chaine complete) : {len(mav)}")
    print(f"  journees marquees AVANT (vue heritee)     : {len(mav_h)}"
          f"   <- le compte publie aux etapes 18-20")
    print(f"  ecart de comptage                         : "
          f"{len(mav) - len(mav_h)}")
    print(f"  journees marquees APRES                   : {len(map_)}")
    rentrent = sorted(mav - map_)
    sortent = sorted(map_ - mav)
    print(f"  cessent d'etre marquees (RENTRENT)        : {len(rentrent)}")
    print(f"  nouvellement marquees (SORTENT)           : {len(sortent)}")
    ecrire_csv(OUT / "R4_marquees.csv",
               ["point", "date", "mouvement", "mois"],
               [dict(point=p, date=d, mouvement="rentre dans l'analyse",
                     mois=int(d[5:7])) for p, d in rentrent]
               + [dict(point=p, date=d, mouvement="sort de l'analyse",
                       mois=int(d[5:7])) for p, d in sortent],
               tri=["mouvement", "point", "date"])

    # ---------------- 1 : les journees ESTIVALES qui rentrent
    print("\n" + "=" * 78)
    print("1 — LES JOURNEES ESTIVALES QUI RENTRENT (D118)")
    print("=" * 78)
    est = [(p, d) for p, d in rentrent if int(d[5:7]) in ETE]
    print(f"  journees estivales concernees : {len(est)}")
    for p, d in est:
        print(f"     {p:<34} {d}")
    pts = sorted({p for p, _ in est})

    def coef(d, grandeur):
        x = d[d.grandeur == grandeur]
        return {r["point"]: r for _, r in x.iterrows()}

    ce_av, ce_ap = coef(a06_av, "m_estival"), coef(a06_ap, "m_estival")

    def tmh(d, point):
        x = d[(d.point == point) & (d.grandeur == "Tmh_norm")]["T_normalisee"]
        x = pd.to_numeric(x, errors="coerce").dropna()
        return (float(x.median()), float(x.quantile(0.95)), int(len(x))) if len(x) else (np.nan, np.nan, 0)

    l1 = []
    for p in pts:
        ra, rb = ce_av.get(p), ce_ap.get(p)
        m_av = float(ra["m"]) if ra is not None and pd.notna(ra["m"]) else np.nan
        m_ap = float(rb["m"]) if rb is not None and pd.notna(rb["m"]) else np.nan
        n_av = int(ra["n"]) if ra is not None and pd.notna(ra["n"]) else 0
        n_ap = int(rb["n"]) if rb is not None and pd.notna(rb["n"]) else 0
        med_av, p95_av, k_av = tmh(a07_av, p)
        med_ap, p95_ap, k_ap = tmh(a07_ap, p)
        s_av = a08_av[a08_av.point == p]
        s_ap = a08_ap[a08_ap.point == p]

        def det(s, ind):
            x = s[s.indicateur == ind]
            return (x.iloc[0]["detail"] if len(x) else None)
        l1.append(dict(
            point=p, journees_qui_rentrent=sum(1 for q, _ in est if q == p),
            m_estival_avant=_f(m_av), m_estival_apres=_f(m_ap),
            ecart_m=_f(m_ap - m_av), n_avant=n_av, n_apres=n_ap,
            Tmh_norm_median_avant=_f(med_av), Tmh_norm_median_apres=_f(med_ap),
            ecart_median=_f(med_ap - med_av),
            Tmh_norm_p95_avant=_f(p95_av), Tmh_norm_p95_apres=_f(p95_ap),
            ecart_p95=_f(p95_ap - p95_av),
            cat_aigu_avant=det(s_av, "n_jours_aigus"),
            cat_aigu_apres=det(s_ap, "n_jours_aigus"),
            cat_chr_avant=det(s_av, "pct_stress_chronique"),
            cat_chr_apres=det(s_ap, "pct_stress_chronique"),
            sgvt_avant=det(s_av, "sgvt"), sgvt_apres=det(s_ap, "sgvt")))
    ecrire_csv(OUT / "R1_m_estival.csv",
               ["point", "journees_qui_rentrent", "m_estival_avant",
                "m_estival_apres", "ecart_m", "n_avant", "n_apres",
                "Tmh_norm_median_avant", "Tmh_norm_median_apres",
                "ecart_median", "Tmh_norm_p95_avant", "Tmh_norm_p95_apres",
                "ecart_p95", "cat_aigu_avant", "cat_aigu_apres",
                "cat_chr_avant", "cat_chr_apres", "sgvt_avant", "sgvt_apres"],
               l1, tri=["point"])
    ecrire_csv(OUT / "R1_journees_estivales.csv",
               ["point", "date", "mois"],
               [dict(point=p, date=d, mois=int(d[5:7])) for p, d in est],
               tri=["point", "date"])
    print(f"\n  {'point':<34}{'m_estival':>22}{'Tmh_norm mediane':>22}{'p95':>16}")
    for r in l1:
        print(f"  {r['point']:<34}"
              f"{r['m_estival_avant']:>10} -> {r['m_estival_apres']:<9}"
              f"{r['Tmh_norm_median_avant']:>10} -> {r['Tmh_norm_median_apres']:<9}"
              f"{r['ecart_p95']:>16}")
    bouge = [r for r in l1 if (r["cat_aigu_avant"] != r["cat_aigu_apres"]
                               or r["cat_chr_avant"] != r["cat_chr_apres"]
                               or r["sgvt_avant"] != r["sgvt_apres"])]
    print(f"\n  points dont un verdict bouge : {len(bouge)}")
    for r in bouge:
        print(f"     {r['point']} : aigu « {r['cat_aigu_avant']} » -> "
              f"« {r['cat_aigu_apres']} » ; chronique « {r['cat_chr_avant']} » "
              f"-> « {r['cat_chr_apres']} » ; SGVT « {r['sgvt_avant']} » -> "
              f"« {r['sgvt_apres']} »")

    # ---------------- 2 : m_saisonnier, par point et par espece
    print("\n" + "=" * 78)
    print("2 — LE COEFFICIENT DE FRAIE (m_saisonnier), PAR POINT ET PAR ESPECE")
    print("=" * 78)
    esp_av = {r["point"]: r["valeur_texte"]
              for _, r in a08_av[a08_av.indicateur == "espece_repere"].iterrows()}
    cs_av, cs_ap = coef(a06_av, "m_saisonnier_fraie"), coef(a06_ap, "m_saisonnier_fraie")
    l2 = []
    for p in sorted(set(cs_av) | set(cs_ap)):
        ra, rb = cs_av.get(p), cs_ap.get(p)
        m_av = float(ra["m"]) if ra is not None and pd.notna(ra["m"]) else np.nan
        m_ap = float(rb["m"]) if rb is not None and pd.notna(rb["m"]) else np.nan
        n_av = int(ra["n"]) if ra is not None and pd.notna(ra["n"]) else 0
        n_ap = int(rb["n"]) if rb is not None and pd.notna(rb["n"]) else 0
        ajout = sum(1 for q, d in sortent if q == p)
        rent = sum(1 for q, d in rentrent if q == p)
        esp = esp_av.get(p, "?")
        pf_av = a08_av[(a08_av.point == p) & (a08_av.indicateur == "P_fraie")]
        pf_ap = a08_ap[(a08_ap.point == p) & (a08_ap.indicateur == "P_fraie")]
        l2.append(dict(
            point=p, espece=esp, journees_ajoutees=ajout, journees_rentrees=rent,
            m_saisonnier_avant=_f(m_av), m_saisonnier_apres=_f(m_ap),
            ecart=_f(m_ap - m_av), n_avant=n_av, n_apres=n_ap,
            P_fraie_avant=(_f(pf_av.iloc[0]["valeur"]) if len(pf_av) else None),
            P_fraie_apres=(_f(pf_ap.iloc[0]["valeur"]) if len(pf_ap) else None)))
    ecrire_csv(OUT / "R2_m_saisonnier.csv",
               ["point", "espece", "journees_ajoutees", "journees_rentrees",
                "m_saisonnier_avant", "m_saisonnier_apres", "ecart",
                "n_avant", "n_apres", "P_fraie_avant", "P_fraie_apres"],
               l2, tri=["point"])
    mb = [r for r in l2 if r["ecart"] not in (None, 0.0)]
    print(f"  points dont m_saisonnier bouge : {len(mb)} / {len(l2)}")
    for r in sorted(mb, key=lambda x: -abs(x["ecart"] or 0))[:15]:
        print(f"     {r['point']:<34} [{r['espece']:<14}] "
              f"{r['m_saisonnier_avant']:>9} -> {r['m_saisonnier_apres']:<9} "
              f"ecart {r['ecart']:>9}  (n {r['n_avant']} -> {r['n_apres']}, "
              f"+{r['journees_ajoutees']} j)")
    pfb = [r for r in l2 if r["P_fraie_avant"] != r["P_fraie_apres"]]
    print(f"\n  points dont P_fraie bouge : {len(pfb)}")
    for r in pfb:
        print(f"     {r['point']:<34} [{r['espece']}] "
              f"{r['P_fraie_avant']} -> {r['P_fraie_apres']}")

    # ---------------- 3 : la fuite, et la fraie
    print("\n" + "=" * 78)
    print("3 — LE COUT DE LA FUITE (D117)")
    print("=" * 78)
    fuite = pd.read_csv(OUT / "S_nouvelles.csv", sep=";", encoding="utf-8")
    fuite = fuite[(fuite.saison == "saison froide") & (fuite.survit == "oui")]
    l3 = []
    for _, r in fuite.iterrows():
        esp = esp_av.get(r["point"], "?")
        mois_fraie = FRAIE.get(esp, [])
        dans = int(r["mois"]) in mois_fraie
        l3.append(dict(
            point=r["point"], date=r["date"], mois=int(r["mois"]),
            espece=esp, mois_de_fraie=" ".join(str(m) for m in mois_fraie),
            dans_la_fenetre_de_fraie=("OUI" if dans else "non"),
            T_eau_max=r["T_eau_max"], T_air=r["T_air"],
            ecart_a_la_mediane=r["ecart_a_la_mediane"],
            temoin_etape19=r["temoin"],
            effectivement_marquee=("oui" if (r["point"], r["date"]) in map_
                                   else "NON")))
    ecrire_csv(OUT / "R3_fuite_fraie.csv",
               ["point", "date", "mois", "espece", "mois_de_fraie",
                "dans_la_fenetre_de_fraie", "T_eau_max", "T_air",
                "ecart_a_la_mediane", "temoin_etape19",
                "effectivement_marquee"], l3, tri=["point", "date"])
    d3 = pd.DataFrame(l3)
    n_dans = int((d3.dans_la_fenetre_de_fraie == "OUI").sum()) if len(d3) else 0
    print(f"  journees de la fuite : {len(d3)}")
    print(f"  DANS une fenetre de fraie : {n_dans}")
    for _, r in d3.iterrows():
        print(f"     {r['point']:<34} {r['date']}  mois {r['mois']:>2}  "
              f"[{r['espece']:<14}] fraie {r['mois_de_fraie']:<18} "
              f"-> {r['dans_la_fenetre_de_fraie']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
