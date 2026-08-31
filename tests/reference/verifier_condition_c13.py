"""
verifier_condition_c13.py — ETAPE 20 : LA PREDICTION QUI AUTORISE D108.

RIEN N'EST POSE PAR CE SCRIPT. Il calcule la condition de D108 sur les
journees deja marquees, AVANT toute modification applicative, et repond a une
seule question :

    les 69 journees estivales marquees et validees aux etapes 18 et 19
    satisfont-elles toutes la condition « eau anormalement chaude » ?

Si une seule ne la satisfait pas, la conjonction n'est plus une extension mais
un detecteur different, et il faut rouvrir la validation des etapes 18 et 19.
Le script le dit et s'arrete la.

================================================================================
LA CONDITION, ET LE CHOIX DE GRANDEUR — DECLARE AVANT DE REGARDER
================================================================================
D108 : le detecteur marque en CONJONCTION — ecart relatif depasse ET eau
anormalement chaude pour son point et son mois, avec la relativisation DEJA EN
PLACE.

  ecart      e_moy  = T_eau_max - T_air        deja calcule (qc.py:340)
  eau        t_eau  = T_eau_max                  <- LA GRANDEUR RETENUE
  condition  relativiser(t_eau, mois) > k        meme fonction, meme k

POURQUOI `T_eau_max` ET NON `T_eau_moy`. C'est la grandeur qui figure DEJA dans
l'ecart. La reprendre telle quelle n'introduit aucune seconde grandeur, aucun
second estimateur, aucune seconde famille de seuils : c'est exactement ce que
D108 exige. Prendre `T_eau_moy` reviendrait a faire entrer une variable de plus
dans la regle.

`T_eau_moy` est neanmoins CALCULE et publie a cote, comme sensibilite. Il ne
sert pas a decider : si la condition sur `T_eau_max` echoue, le script s'arrete
et publie les deux chiffres SANS choisir. Substituer la seconde grandeur parce
que la premiere echoue serait choisir le critere apres avoir vu le resultat.

LA RELATIVISATION EST CELLE DE L'APPLICATION. `qc.relativiser` est importee et
appelee, jamais reecrite. Ses garde-fous s'appliquent donc tels quels : un
point-mois de moins de `min_jours_groupe` journees, ou de dispersion inferieure
au plancher, n'est PAS diagnosticable — le detecteur s'abstient et le declare
(D100). Ces cas sont releves et nommes.

UN POINT DE MECANIQUE, VERIFIE PLUTOT QUE SUPPOSE
`relativiser` regroupe PAR MOIS. Etendre la fenetre ajoute des groupes, elle ne
modifie pas la composition du groupe « juin ». La condition calculee sur les
journees estivales est donc la MEME sous l'ancienne et sous la nouvelle
fenetre. Le script le verifie au lieu de l'affirmer.

SORTIES, sous out/etape20/
  C_condition_69.csv       les 69 journees deja marquees, condition par condition
  C_condition_nouvelles.csv les journees ajoutees par la fenetre etendue
  C_abstentions.csv        les point-mois ou la condition ne peut pas se calculer
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
ANNEE = tuple(range(1, 13))


def table_qc(cfg):
    """
    La table que `marquer_qualite` construit, reproduite a l'identique
    (qc.py:238-241) : jointure GAUCHE de l'eau journaliere sur l'air.
    """
    daily, _sub, _ml = io.marquer_lecture(
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


def conditions(df, qc, mois):
    """relativiser appliquee a T_eau_max et a T_eau_moy, fenetre `mois`."""
    dans = df["month"].isin(list(mois))
    out = {}
    for nom, col in (("max", "T_eau_max"), ("moy", "T_eau_moy")):
        v = df[col].where(dans & df[col].notna())
        rel, diag = qcmod.relativiser(v, df["month"], qc["plancher_dispersion"],
                                      qc["min_jours_groupe"])
        out[nom] = (rel, diag)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("ETAPE 20 — LA PREDICTION QUI AUTORISE D108")
    print("Rien n'est pose. La condition est calculee sur l'etat actuel.")
    print("=" * 78)

    a18 = pd.read_csv(RACINE / "out" / "etape18" / "A_toutes_marquees.csv",
                      sep=";", encoding="utf-8")
    deja = {(r.point, str(r.date)[:10]) for r in a18.itertuples()}
    bn = OUT / "B_nouvelles.csv"
    nouvelles = (pd.read_csv(bn, sep=";", encoding="utf-8") if bn.exists()
                 else pd.DataFrame(columns=["point", "date", "mois", "temoin"]))
    nv = {(r.point, str(r.date)[:10]): r.temoin for r in nouvelles.itertuples()}
    print(f"  journees deja marquees   : {len(deja)}")
    print(f"  journees ajoutees par C13 : {len(nv)}")

    l69, lnv, labs, ecarts_fenetre = [], [], [], []
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            cibles = {d for (p, d) in deja if p == pt} | {d for (p, d) in nv
                                                          if p == pt}
            cfg = build_reference.construire_config(jeu, point_rel,
                                                    "application")
            qc = cfg.qc.to_legacy_dict()
            k = qc["k"]
            try:
                df = table_qc(cfg)
            except Exception as exc:
                print(f"  · {jeu['jeu']}/{pt} : ECHEC ({type(exc).__name__})",
                      flush=True)
                continue
            df["ds"] = df["date"].astype(str).str.slice(0, 10)
            c_ete = conditions(df, qc, ETE)
            c_an = conditions(df, qc, ANNEE)

            # -- les point-mois ou la condition ne peut pas se calculer
            for m, sub in df.groupby("month"):
                d_an = bool(c_an["max"][1].loc[sub.index].any())
                if not d_an:
                    v = df.loc[sub.index, "T_eau_max"].dropna()
                    med = float(v.median()) if len(v) else np.nan
                    mad = (qcmod.FACTEUR_MAD * float((v - med).abs().median())
                           if len(v) else np.nan)
                    labs.append(dict(
                        jeu=jeu["jeu"], point=pt, mois=int(m),
                        n_journees=int(len(v)),
                        min_requis=qc["min_jours_groupe"],
                        mad_etoile=_f(mad),
                        plancher=qc["plancher_dispersion"],
                        motif=("effectif insuffisant"
                               if len(v) < qc["min_jours_groupe"]
                               else "dispersion sous le plancher")))

            for _, r in df.iterrows():
                ds = r["ds"]
                if ds not in cibles:
                    continue
                i = r.name
                rmax_e = c_ete["max"][0].loc[i]
                dmax_e = bool(c_ete["max"][1].loc[i])
                rmax_a = c_an["max"][0].loc[i]
                dmax_a = bool(c_an["max"][1].loc[i])
                rmoy_a = c_an["moy"][0].loc[i]
                dmoy_a = bool(c_an["moy"][1].loc[i])
                if int(r["month"]) in ETE and dmax_e != dmax_a:
                    ecarts_fenetre.append((pt, ds, "diagnosticabilite"))
                elif (int(r["month"]) in ETE and np.isfinite(rmax_e)
                      and np.isfinite(rmax_a) and abs(rmax_e - rmax_a) > 1e-9):
                    ecarts_fenetre.append((pt, ds, "valeur relative"))
                ligne = dict(
                    jeu=jeu["jeu"], point=pt, date=ds, mois=int(r["month"]),
                    T_eau_max=_f(r.get("T_eau_max")),
                    T_eau_moy=_f(r.get("T_eau_moy")), T_air=_f(r.get("T_air")),
                    rel_T_eau_max=_f(rmax_a), diagnosticable=("oui" if dmax_a
                                                              else "NON"),
                    satisfait=("oui" if (dmax_a and np.isfinite(rmax_a)
                                         and rmax_a > k) else "NON"),
                    k=k,
                    rel_T_eau_moy=_f(rmoy_a),
                    satisfait_variante_moy=("oui" if (dmoy_a
                                                      and np.isfinite(rmoy_a)
                                                      and rmoy_a > k) else "NON"))
                if (pt, ds) in deja:
                    l69.append(ligne)
                else:
                    ligne["temoin_etape19"] = nv.get((pt, ds), "")
                    lnv.append(ligne)
            print(f"  · {jeu['jeu']}/{pt}", flush=True)

    cols = ["jeu", "point", "date", "mois", "T_eau_max", "T_eau_moy", "T_air",
            "rel_T_eau_max", "k", "diagnosticable", "satisfait",
            "rel_T_eau_moy", "satisfait_variante_moy"]
    ecrire_csv(OUT / "C_condition_69.csv", cols, l69,
               tri=["jeu", "point", "date"])
    ecrire_csv(OUT / "C_condition_nouvelles.csv",
               cols + ["temoin_etape19"], lnv, tri=["jeu", "point", "date"])
    ecrire_csv(OUT / "C_abstentions.csv",
               ["jeu", "point", "mois", "n_journees", "min_requis",
                "mad_etoile", "plancher", "motif"], labs,
               tri=["jeu", "point", "mois"])

    d69 = pd.DataFrame(l69)
    print("\n" + "=" * 78)
    print("LA FENETRE NE DEPLACE PAS LA RELATIVISATION ESTIVALE")
    print("=" * 78)
    print(f"  journees estivales dont la condition differe entre les deux "
          f"fenetres : {len(ecarts_fenetre)}")
    for e in ecarts_fenetre[:10]:
        print(f"     {e}")

    print("\n" + "=" * 78)
    print("PREDICTION 1 — LES 69 DOIVENT TOUTES SATISFAIRE LA CONDITION")
    print("=" * 78)
    n_ok = int((d69.satisfait == "oui").sum()) if len(d69) else 0
    n_non = int((d69.satisfait == "NON").sum()) if len(d69) else 0
    print(f"  journees retrouvees : {len(d69)} / {len(deja)}")
    print(f"  satisfont la condition sur T_eau_max : {n_ok}")
    print(f"  NE LA SATISFONT PAS                  : {n_non}")
    if n_non:
        print("\n  *** ARRET — LA PREDICTION EST DEMENTIE ***")
        print("  Les journees en defaut :")
        for _, r in d69[d69.satisfait == "NON"].iterrows():
            print(f"     {r['point']:<34} {r['date']}  mois {r['mois']:>2}  "
                  f"T_eau_max {r['T_eau_max']}  rel {r['rel_T_eau_max']}  "
                  f"(diagnosticable {r['diagnosticable']})")
            print(f"        variante T_eau_moy : rel {r['rel_T_eau_moy']}, "
                  f"satisfait {r['satisfait_variante_moy']}")
        n_moy = int((d69.satisfait_variante_moy == "oui").sum())
        print(f"\n  Pour information SEULEMENT, sans que cela vaille choix :")
        print(f"     la variante T_eau_moy en satisferait {n_moy} / {len(d69)}")
        print("  Le script ne choisit pas. Il remonte les deux chiffres.")
    else:
        print("  PREDICTION CONFIRMEE : la condition ne retire aucune des 69.")

    if len(lnv):
        dn = pd.DataFrame(lnv)
        print("\n" + "=" * 78)
        print("PREDICTION 2 — LES 73 FROIDES TOMBENT, LES 55 DE MAI RESTENT")
        print("=" * 78)
        dn["froide"] = ~dn.mois.isin(ETE + (5,))
        for lab, sub in (("mai", dn[dn.mois == 5]),
                         ("saison froide (oct-avr)", dn[dn.froide]),
                         ("autres", dn[(dn.mois != 5) & (~dn.froide)])):
            if not len(sub):
                continue
            ok = int((sub.satisfait == "oui").sum())
            cor = int((sub.temoin_etape19 == "artefact").sum())
            print(f"  {lab:<26} {len(sub):>4} ajoutees | "
                  f"{ok:>3} survivent a la condition | "
                  f"{cor:>3} corroborees par le temoin")
        surv = dn[dn.satisfait == "oui"]
        print(f"\n  au total : {len(dn)} ajoutees -> {len(surv)} survivent")
        print(f"  dont corroborees par le temoin : "
              f"{int((surv.temoin_etape19 == 'artefact').sum())}")
        cro = dn[(dn.satisfait == "oui") & (dn.temoin_etape19 != "artefact")]
        if len(cro):
            print(f"\n  survivent SANS corroboration du temoin : {len(cro)}")
            for m, n in cro.groupby("mois").size().items():
                print(f"     mois {int(m):>2} : {n}")
        perdues = dn[(dn.satisfait == "NON") & (dn.temoin_etape19 == "artefact")]
        if len(perdues):
            print(f"\n  CORROBOREES MAIS ECARTEES PAR LA CONDITION : "
                  f"{len(perdues)}")
            for _, r in perdues.iterrows():
                print(f"     {r['point']:<34} {r['date']}  "
                      f"rel {r['rel_T_eau_max']}  diag {r['diagnosticable']}")

    print("\n" + "=" * 78)
    print("LES ABSTENTIONS — POINT-MOIS OU LA CONDITION NE SE CALCULE PAS")
    print("=" * 78)
    da = pd.DataFrame(labs)
    print(f"  couples (point, mois) concernes : {len(da)}")
    if len(da):
        print(f"  par motif : {da.motif.value_counts().to_dict()}")
        print(f"  points concernes : {da.point.nunique()}")
        for p, sub in list(da.groupby("point"))[:12]:
            print(f"     {p:<34} mois {sorted(sub.mois.tolist())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
