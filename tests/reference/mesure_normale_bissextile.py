"""
mesure_normale_bissextile.py — ETAPE 15, POSE 1 (1.1, 1.2, 1.4) : ce que le
decalage bissextile de la normale produit, mesure AVANT correction.

LE DEFAUT, LIGNE A LIGNE
-------------------------
`io_data.calculer_normales_ecarts` :

  io_data.py:609   df["doy"] = df["date_dt"].dt.dayofyear
                   -> le doy REEL de chaque journee du fichier d'air
  io_data.py:631   brute = df_ref.groupby("doy")["T_air"].mean()
                   -> la normale brute est agregee sur cet axe. Le doy 60
                      melange donc le 29 FEVRIER des annees bissextiles et le
                      1er MARS des annees communes.
  io_data.py:642   ref_dates = date_range("2000-01-01", "2000-12-31")
                   -> 2000 est BISSEXTILE. La table (jour, mois) -> doy est
                      donc celle d'une annee a 366 jours.
  io_data.py:650   df.merge(normales_lkp, on=["day", "month"])
  core.py:237      idem, pour T_normale dans la chronique

Consequence : une journee du 1er mars d'une annee COMMUNE a un doy reel de 60,
mais recoit la normale du doy 61. Du 1er mars au 31 decembre, toute journee
d'une annee commune recoit la normale du jour SUIVANT.

CE QUE CETTE MESURE ETABLIT (1.1)
----------------------------------
Combien de journees recoivent une normale decalee, sur quelle part de l'annee,
et l'ecart que cela produit sur T_normale, Delta_TMm, Delta_TMm_liss et
T_norm — mediane, p95, maximum, par point.

Elle ne se refait pas apres : une fois la correspondance corrigee, l'etat
d'avant devient inobservable. C'est la methode de l'etape 6.

COMMENT LES DEUX VERSIONS SONT CALCULEES COTE A COTE
------------------------------------------------------
La chaine est rejouee telle quelle (`orchestrator.run`). La version corrigee
est recalculee A COTE, a partir du meme fichier d'air, avec les memes
fonctions de l'application (`core.moyenne_mobile_calendaire`). `app/` n'est pas
touche.

Une replication non verifiee ne vaut rien (etapes 8, 9, 13) : le script
recalcule d'abord la version ACTUELLE par le meme chemin et verifie qu'elle
reproduit `res.df` a l'identique. La colonne `replication` porte le verdict.

SORTIES
  out/etape15/P1_normales_par_point.csv
  out/etape15/P1_normales_par_jour.csv
  out/etape15/P1_29fevrier.csv
"""
from __future__ import annotations

import contextlib
import io as _io
import os
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import (CODE, RACINE, RACINE_CODE, decouvrir, ecrire_csv,  # noqa: E402
                     nom_point, _f)

import build_reference                                                  # noqa: E402
from thermie_debits import orchestrator, core, io_data                  # noqa: E402

OUT = RACINE / "out" / "etape15"

# L'axe calendaire : les 366 jours distincts d'une annee. `date_range` sur une
# annee bissextile est le seul gabarit qui les porte tous, 29 fevrier compris.
# Ce n'est PAS un remapping de doy : c'est la liste des jours calendaires.
AXE = pd.to_datetime(pd.Series(pd.date_range("2000-01-01", "2000-12-31")))
POSITION = {(int(d.month), int(d.day)): i for i, d in enumerate(AXE)}


def _lisser_circulaire(valeurs: np.ndarray, fenetre: int) -> np.ndarray:
    """Le lissage circulaire de io_data.py:632-636, sur l'axe fourni."""
    s = pd.Series(valeurs).interpolate(limit_direction="both")
    w = 2 * fenetre + 1
    triple = pd.concat([s, s, s], ignore_index=True)
    liss = triple.rolling(window=w, center=True, min_periods=1).mean()
    n = len(s)
    return liss.iloc[n:2 * n].to_numpy()


def normales_actuelles(df_air, ref, fenetre):
    """Reproduit io_data.calculer_normales_ecarts — l'etat AVANT."""
    df = df_air.copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df["year"] = df["date_dt"].dt.year
    df["month"] = df["date_dt"].dt.month
    df["day"] = df["date_dt"].dt.day
    df["doy"] = df["date_dt"].dt.dayofyear
    d_ref = df[(df["year"] >= ref[0]) & (df["year"] <= ref[1])]
    brute = d_ref.groupby("doy")["T_air"].mean()
    idx = pd.Series(index=range(1, 367), dtype=float)
    idx.loc[brute.index] = brute.values
    normale_doy = pd.Series(_lisser_circulaire(idx.to_numpy(), fenetre),
                            index=range(1, 367))
    lkp = pd.DataFrame({"day": AXE.dt.day.values, "month": AXE.dt.month.values,
                        "doy": AXE.dt.dayofyear.values})
    lkp["T_normale"] = lkp["doy"].map(normale_doy)
    return lkp[["day", "month", "T_normale"]]


def normales_calendaires(df_air, ref, fenetre):
    """
    LA CONVENTION RETENUE — l'etat APRES.

    1. La normale brute est agregee par IDENTITE CALENDAIRE (mois, jour), et
       non par numero de jour dans l'annee. Le 1er mars est le 1er mars dans
       toutes les annees ; le 29 fevrier forme son propre groupe, alimente par
       les seules annees bissextiles.
    2. Le lissage circulaire porte sur l'AXE DES 366 JOURS CALENDAIRES, donc
       sur des voisins calendaires : le 29 fevrier y est entre le 28 fevrier
       et le 1er mars, ce qui est sa place.
    3. La lecture par (jour, mois) est INCHANGEE — mais elle interroge
       desormais le meme axe que celui de l'agregation.

    PROVENANCE. `fenetre` et la periode de reference sont ceux de la version
    anterieure, repris sans modification. Le nombre 366 n'est pas une valeur
    nouvelle : c'est le nombre de jours calendaires distincts. Aucune valeur
    propre a un bassin n'entre ici.
    """
    df = df_air.copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df["year"] = df["date_dt"].dt.year
    df["month"] = df["date_dt"].dt.month
    df["day"] = df["date_dt"].dt.day
    d_ref = df[(df["year"] >= ref[0]) & (df["year"] <= ref[1])]
    brute = d_ref.groupby(["month", "day"])["T_air"].mean()

    vals = np.full(len(AXE), np.nan)
    for (m, j), v in brute.items():
        p = POSITION.get((int(m), int(j)))
        if p is not None:
            vals[p] = v
    liss = _lisser_circulaire(vals, fenetre)
    return pd.DataFrame({"day": AXE.dt.day.values,
                         "month": AXE.dt.month.values,
                         "T_normale": liss})


def delta_lisse(ecart: pd.DataFrame, dates, lissage_delta: int):
    """Le lissage de l'anomalie d'air, sur TOUT le calendrier de la station —
    core.py:317-325, reproduit avec la fonction de l'application."""
    a = ecart.dropna(subset=["Delta_TMm"]).drop_duplicates("date")
    a = a.sort_values("date")
    if not len(a):
        return np.full(len(dates), np.nan)
    s = pd.Series(core.moyenne_mobile_calendaire(a["date"], a["Delta_TMm"],
                                                 fenetre=lissage_delta,
                                                 min_periods=1),
                  index=pd.to_datetime(a["date"].to_numpy()))
    return s.reindex(pd.to_datetime(pd.Series(dates).to_numpy())).to_numpy()


def stats(x):
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)])
    if not len(x):
        return None, None, None
    a = np.abs(x)
    return float(np.median(a)), float(np.percentile(a, 95)), float(a.max())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print("=" * 74)
    print("POSE 1 / 1.1 — LE DECALAGE BISSEXTILE DE LA NORMALE, AVANT CORRECTION")
    print("=" * 74)

    par_point, par_jour, fevrier = [], [], []
    vus_jour = set()
    n_repl_ok = n_repl_ko = 0
    tot_jours = tot_decales = 0

    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            tampon = _io.StringIO()
            res = None
            try:
                cfg = build_reference.construire_config(jeu, point_rel,
                                                        "application")
                with contextlib.redirect_stdout(tampon), \
                     contextlib.redirect_stderr(tampon):
                    res = orchestrator.run(cfg, verbose=False)
            except Exception as exc:
                par_point.append(dict(jeu=jeu["jeu"], point=pt,
                                      replication="ECHEC DE LA CHAINE",
                                      erreur=f"{type(exc).__name__}: {exc}"))
                print(f"  · {jeu['jeu']}/{pt} : ECHEC")
                continue
            finally:
                try:
                    import matplotlib.pyplot as plt
                    plt.close("all")
                except Exception:
                    pass

            df = res.df
            air = res.df_air
            if df is None or not len(df) or air is None:
                continue
            fen = cfg.normales_fenetre_lissage
            liss_d = cfg.normalisation_lissage_delta
            ref = io_data.REF_NORMALES

            lkp_av = normales_actuelles(air, ref, fen)
            lkp_ap = normales_calendaires(air, ref, fen)

            d = df[["date", "day", "month", "T_air", "T_normale",
                    "Delta_TMm", "Delta_TMm_liss", "Tmh", "T_eau_max"]].copy()
            d = d.merge(lkp_av.rename(columns={"T_normale": "Tn_repl"}),
                        on=["day", "month"], how="left")
            d = d.merge(lkp_ap.rename(columns={"T_normale": "Tn_ap"}),
                        on=["day", "month"], how="left")

            # --- CONTROLE DE REPLICATION : reproduit-on l'etat actuel ?
            ecart_repl = np.abs(d["Tn_repl"] - d["T_normale"])
            repl = ("identique" if float(np.nanmax(ecart_repl.values)) < 5e-9
                    else "DIVERGENTE")
            n_repl_ok += repl == "identique"
            n_repl_ko += repl != "identique"

            # --- propagation
            d["dTn"] = d["Tn_ap"] - d["T_normale"]
            d["Delta_ap"] = d["T_air"] - d["Tn_ap"]
            d["dDelta"] = d["Delta_ap"] - d["Delta_TMm"]

            a2 = air.copy()
            a2["day"] = pd.to_datetime(a2["date"]).dt.day
            a2["month"] = pd.to_datetime(a2["date"]).dt.month
            a2 = a2.merge(lkp_ap, on=["day", "month"], how="left")
            a2["Delta_TMm"] = a2["T_air"] - a2["T_normale"]
            dl_ap = delta_lisse(a2[["date", "Delta_TMm"]], d["date"], liss_d)
            d["dDelta_liss"] = dl_ap - d["Delta_TMm_liss"]

            m = (res.sensibilite or {}).get("m")
            d["dTnorm"] = (-(m or 0.0)) * d["dDelta_liss"]

            n_dec = int((d["dTn"].abs() > 1e-9).sum())
            tot_jours += len(d)
            tot_decales += n_dec

            md_n, p95_n, mx_n = stats(d["dTn"])
            md_d, p95_d, mx_d = stats(d["dDelta"])
            md_l, p95_l, mx_l = stats(d["dDelta_liss"])
            md_t, p95_t, mx_t = stats(d["dTnorm"])

            par_point.append(dict(
                jeu=jeu["jeu"], point=pt, replication=repl, erreur="",
                m_applique=_f(m), journees=len(d), journees_decalees=n_dec,
                part_pct=_f(100.0 * n_dec / len(d)) if len(d) else None,
                T_normale_median=_f(md_n), T_normale_p95=_f(p95_n),
                T_normale_max=_f(mx_n),
                Delta_TMm_median=_f(md_d), Delta_TMm_p95=_f(p95_d),
                Delta_TMm_max=_f(mx_d),
                Delta_liss_median=_f(md_l), Delta_liss_p95=_f(p95_l),
                Delta_liss_max=_f(mx_l),
                T_norm_median=_f(md_t), T_norm_p95=_f(p95_t),
                T_norm_max=_f(mx_t)))

            # --- 1.2 : le 29 fevrier
            n29 = d[(d["month"] == 2) & (d["day"] == 29)]
            if len(n29):
                fevrier.append(dict(
                    jeu=jeu["jeu"], point=pt, journees_29_fevrier=int(len(n29)),
                    T_normale_avant=_f(float(n29["T_normale"].iloc[0])),
                    T_normale_apres=_f(float(n29["Tn_ap"].iloc[0])),
                    ecart=_f(float(n29["Tn_ap"].iloc[0]
                                   - n29["T_normale"].iloc[0]))))

            # --- la table (jour, mois), une fois par station d'air
            cle_air = jeu["air"]
            if cle_air not in vus_jour:
                vus_jour.add(cle_air)
                lj = lkp_av.merge(lkp_ap.rename(
                    columns={"T_normale": "T_normale_apres"}),
                    on=["day", "month"])
                for _, r in lj.iterrows():
                    par_jour.append(dict(
                        station_air=cle_air, mois=int(r["month"]),
                        jour=int(r["day"]),
                        T_normale_avant=_f(r["T_normale"]),
                        T_normale_apres=_f(r["T_normale_apres"]),
                        ecart=_f(r["T_normale_apres"] - r["T_normale"])))
            print(f"  · {jeu['jeu']}/{pt} : {n_dec}/{len(d)} decalees "
                  f"[{repl}]", flush=True)

    ecrire_csv(OUT / "P1_normales_par_point.csv",
               ["jeu", "point", "replication", "erreur", "m_applique",
                "journees", "journees_decalees", "part_pct",
                "T_normale_median", "T_normale_p95", "T_normale_max",
                "Delta_TMm_median", "Delta_TMm_p95", "Delta_TMm_max",
                "Delta_liss_median", "Delta_liss_p95", "Delta_liss_max",
                "T_norm_median", "T_norm_p95", "T_norm_max"],
               par_point, tri=["jeu", "point"])
    ecrire_csv(OUT / "P1_normales_par_jour.csv",
               ["station_air", "mois", "jour", "T_normale_avant",
                "T_normale_apres", "ecart"],
               par_jour, tri=["station_air", "mois", "jour"])
    ecrire_csv(OUT / "P1_29fevrier.csv",
               ["jeu", "point", "journees_29_fevrier", "T_normale_avant",
                "T_normale_apres", "ecart"],
               fevrier, tri=["jeu", "point"])

    d = pd.DataFrame([l for l in par_point if l.get("journees")])
    print("\n" + "=" * 74)
    print("CE QUE LE DECALAGE PRODUIT")
    print("=" * 74)
    print(f"  replication controlee identique : {n_repl_ok} point(s)")
    print(f"  replication NON identique       : {n_repl_ko} point(s)")
    print(f"  journees du corpus              : {tot_jours}")
    print(f"  journees a normale decalee      : {tot_decales}"
          f"  ({100.0*tot_decales/tot_jours:.2f} %)" if tot_jours else "")
    if len(d):
        for lib, col in (("T_normale", "T_normale"), ("Delta_TMm", "Delta_TMm"),
                         ("Delta_TMm_liss", "Delta_liss"), ("T_norm", "T_norm")):
            print(f"\n  {lib} — ecart absolu, sur les {len(d)} points :")
            print(f"      mediane des medianes : "
                  f"{d[col+'_median'].median():.4f} degC")
            print(f"      max des p95          : "
                  f"{d[col+'_p95'].max():.4f} degC")
            print(f"      MAXIMUM              : "
                  f"{d[col+'_max'].max():.4f} degC"
                  f"   ({d.loc[d[col+'_max'].idxmax(), 'point']})")
    dj = pd.DataFrame(par_jour)
    if len(dj):
        print(f"\n  Par jour calendaire, sur {dj['station_air'].nunique()} "
              f"station(s) d'air :")
        nz = dj[dj["ecart"].abs() > 1e-9]
        print(f"      couples (jour, mois) dont la normale change : "
              f"{len(nz)} / {len(dj)}")
        if len(nz):
            print(f"      premier : {int(nz.iloc[0]['jour'])}/"
                  f"{int(nz.iloc[0]['mois'])}   dernier : "
                  f"{int(nz.iloc[-1]['jour'])}/{int(nz.iloc[-1]['mois'])}")
    df29 = pd.DataFrame(fevrier)
    print(f"\n  1.2 — le 29 fevrier : "
          f"{int(df29['journees_29_fevrier'].sum()) if len(df29) else 0} "
          f"journee(s) du corpus, sur {len(df29)} point(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
