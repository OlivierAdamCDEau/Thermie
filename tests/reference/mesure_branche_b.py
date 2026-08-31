"""
mesure_branche_b.py — ETAPE 16, TACHE B (D90) : ce que la branche B couterait,
mesure SANS ETRE POSEE.

D89 retient la branche A — marquer sans exclure. D90 demande neanmoins de
CHIFFRER la branche B, et le motif est le bon : le critere designe des journees
dont les mesures sont GROUPEES, et le caractere exploitable d'une journee
groupee depend de l'endroit ou le groupe tombe dans le cycle nycthemeral — ce
que le trou maximal ne mesure pas. Exclure sur cette base seule serait exclure
sur un indicateur indirect.

CE QUI EST MESURE
------------------
En retirant les journees designees de `propre` AVANT la fusion — c'est-a-dire
exactement ce que la branche B ferait :

  · l'ecart sur `m` ;
  · l'ecart sur `Tmh_norm`, mediane et p95, sur les journees communes ;
  · les verdicts susceptibles de basculer : `pct_chr`, `cat_chr`, `n_aigu`,
    `cat_aigu` ;
  · le tout sur DEUX perimetres : les 36 journees de juin-septembre seules
    (celles qui atteignent `m`), et l'ensemble des journees designees.

METHODE
--------
La chaine est reconstruite avec les fonctions de l'application elles-memes —
`qcmod.marquer_qualite`, `core.fusionner_marque`, `core.analyse_sensibilite`,
`core.analyse_vulnerabilite` — puis rejouee une seconde fois sur un `propre`
ampute. `app/` n'est pas touche.

CONTROLE DE REPLICATION : la version SANS retrait doit reproduire ce que
`orchestrator.run` produit. La colonne `replication` porte le verdict, et un
point dont la replication echoue voit ses chiffres marques NON FIABLES.

SORTIE
  out/etape16/B_branche_b.csv
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
from thermie_debits import orchestrator, core, io_data, qc as qcmod     # noqa: E402

from mesure_completude_journee import trous_par_journee                 # noqa: E402

OUT = RACINE / "out" / "etape16"
FACTEUR = 2.0            # celui que la tache A a retenu sur pieces (D91)
MOIS_ETE = (6, 7, 8, 9)


def chaine(propre, df_air, ecart, normales, ctx, ctx_key, lissage_delta):
    """Le tronçon `fusion -> m -> vulnerabilite`, avec les fonctions de app/."""
    df, _marques = core.fusionner_marque(propre, df_air, ecart, normales,
                                         df_debits=None,
                                         lissage_delta=lissage_delta)
    sens = core.analyse_sensibilite(df)
    vul = core.analyse_vulnerabilite(df, sens["m"], ctx, ctx_key)
    return df, sens, vul


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print("=" * 74)
    print("TACHE B (D90) — CE QUE LA BRANCHE B COUTERAIT, SANS LA POSER")
    print("=" * 74)

    lignes = []
    for jeu in decouvrir():
        if not jeu["air"]:
            continue
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            try:
                cfg = build_reference.construire_config(jeu, point_rel,
                                                        "application")
                with contextlib.redirect_stdout(_io.StringIO()), \
                     contextlib.redirect_stderr(_io.StringIO()):
                    res_ref = orchestrator.run(cfg, verbose=False)
            except Exception as exc:
                lignes.append(dict(jeu=jeu["jeu"], point=pt,
                                   replication=f"CHAINE EN ECHEC "
                                               f"({type(exc).__name__})"))
                print(f"  · {jeu['jeu']}/{pt} : chaine en echec")
                continue
            finally:
                try:
                    import matplotlib.pyplot as plt
                    plt.close("all")
                except Exception:
                    pass

            # --- reconstruire le troncon, puis le rejouer ampute
            with contextlib.redirect_stdout(_io.StringIO()):
                daily, sub, _ml = io_data.marquer_lecture(
                    cfg.sources.fichier_eau,
                    col_date=cfg.sources.eau_col_date,
                    col_temp=cfg.sources.eau_col_temp,
                    nom=cfg.sources.eau_nom_fichier,
                    feuille=cfg.sources.eau_feuille,
                    ligne_entete=cfg.sources.eau_ligne_entete,
                    retour_sous_quotidien=True)
                df_air = res_ref.df_air
                ecart, normales, _dg = io_data.calculer_normales_ecarts(
                    df_air, fenetre_lissage=cfg.normales_fenetre_lissage,
                    min_annees=cfg.normales_min_annees, verbose=False)
                mq = qcmod.marquer_qualite(daily, df_air,
                                           cfg.qc.to_legacy_dict(),
                                           verbose=False)
                propre = qcmod.vue_retenue(mq)
                ctx = cfg.contexte()
                try:
                    df0, s0, v0 = chaine(propre, df_air, ecart, normales, ctx,
                                         cfg.contexte_piscicole,
                                         cfg.normalisation_lissage_delta)
                except Exception as exc:
                    lignes.append(dict(jeu=jeu["jeu"], point=pt,
                                       replication=f"TRONCON EN ECHEC "
                                                   f"({type(exc).__name__})"))
                    print(f"  · {jeu['jeu']}/{pt} : troncon en echec")
                    continue

            # --- CONTROLE DE REPLICATION
            m_ref = (res_ref.sensibilite or {}).get("m")
            repl = ("identique"
                    if (m_ref is not None
                        and abs(float(s0["m"]) - float(m_ref)) < 5e-9)
                    else "DIVERGENTE")

            # --- les journees designees, au facteur retenu
            tr = trous_par_journee(sub)
            trou = tr["trou_max_h"].to_numpy(dtype=float)
            if not np.isfinite(trou).any():
                continue
            med = float(np.nanmedian(trou))
            seuil = FACTEUR * med
            tr["designee"] = np.where(np.isfinite(trou), trou > seuil, False)
            dates_des = set(tr.loc[tr["designee"], "date"].tolist())
            mois = pd.to_datetime(pd.Series(sorted(dates_des))).dt.month \
                if dates_des else pd.Series([], dtype=int)
            dates_ete = {d for d in dates_des
                         if pd.Timestamp(d).month in MOIS_ETE}

            resultats = {}
            for etiquette, aretirer in (("toutes", dates_des),
                                        ("ete", dates_ete)):
                if not aretirer:
                    resultats[etiquette] = None
                    continue
                propre2 = propre[~propre["date"].isin(aretirer)].copy()
                try:
                    with contextlib.redirect_stdout(_io.StringIO()):
                        df1, s1, v1 = chaine(propre2, df_air, ecart, normales,
                                             ctx, cfg.contexte_piscicole,
                                             cfg.normalisation_lissage_delta)
                except Exception as exc:
                    resultats[etiquette] = dict(echec=f"{type(exc).__name__}")
                    continue
                a = df0[["date", "Tmh_norm"]].dropna()
                b = df1[["date", "Tmh_norm"]].dropna()
                j = a.merge(b, on="date", suffixes=("_0", "_1"))
                e = np.abs(j["Tmh_norm_1"] - j["Tmh_norm_0"]).to_numpy()
                resultats[etiquette] = dict(
                    n_retirees=len(aretirer),
                    dm=float(s1["m"]) - float(s0["m"]),
                    e_med=float(np.median(e)) if len(e) else 0.0,
                    e_p95=float(np.percentile(e, 95)) if len(e) else 0.0,
                    e_max=float(e.max()) if len(e) else 0.0,
                    pct0=float(v0["pct_chr"]), pct1=float(v1["pct_chr"]),
                    cat0=str(v0["cat_chr"]), cat1=str(v1["cat_chr"]),
                    aig0=int(v0["n_aigu"]), aig1=int(v1["n_aigu"]),
                    cata0=str(v0["cat_aigu"]), cata1=str(v1["cat_aigu"]))

            t, e_ = resultats.get("toutes"), resultats.get("ete")
            lignes.append(dict(
                jeu=jeu["jeu"], point=pt, replication=repl,
                trou_median_h=_f(med), seuil_h=_f(seuil),
                journees_designees=len(dates_des),
                journees_designees_ete=len(dates_ete),
                m_reference=_f(s0["m"]),
                delta_m_toutes=_f((t or {}).get("dm")),
                delta_m_ete=_f((e_ or {}).get("dm")),
                Tmh_norm_median_toutes=_f((t or {}).get("e_med")),
                Tmh_norm_p95_toutes=_f((t or {}).get("e_p95")),
                Tmh_norm_max_toutes=_f((t or {}).get("e_max")),
                Tmh_norm_median_ete=_f((e_ or {}).get("e_med")),
                Tmh_norm_p95_ete=_f((e_ or {}).get("e_p95")),
                pct_chr_avant=_f((t or {}).get("pct0")),
                pct_chr_apres=_f((t or {}).get("pct1")),
                cat_chr_change=("oui" if t and t.get("cat0") != t.get("cat1")
                                else "non" if t else ""),
                n_aigu_avant=(t or {}).get("aig0"),
                n_aigu_apres=(t or {}).get("aig1"),
                cat_aigu_change=("oui" if t and t.get("cata0") != t.get("cata1")
                                 else "non" if t else "")))
            n_t = len(dates_des)
            print(f"  · {jeu['jeu']}/{pt} : {n_t} designee(s) "
                  f"({len(dates_ete)} en ete)  dm="
                  f"{(t or {}).get('dm', 0.0):+.6f}  [{repl}]", flush=True)

    ecrire_csv(OUT / "B_branche_b.csv",
               ["jeu", "point", "replication", "trou_median_h", "seuil_h",
                "journees_designees", "journees_designees_ete", "m_reference",
                "delta_m_toutes", "delta_m_ete", "Tmh_norm_median_toutes",
                "Tmh_norm_p95_toutes", "Tmh_norm_max_toutes",
                "Tmh_norm_median_ete", "Tmh_norm_p95_ete", "pct_chr_avant",
                "pct_chr_apres", "cat_chr_change", "n_aigu_avant",
                "n_aigu_apres", "cat_aigu_change"],
               lignes, tri=["jeu", "point"])

    d = pd.DataFrame([l for l in lignes if l.get("m_reference") is not None])
    print("\n" + "=" * 74)
    print("CE QUE LA BRANCHE B COUTERAIT")
    print("=" * 74)
    ok = (d.replication == "identique").sum() if len(d) else 0
    print(f"  replication controlee identique : {ok} / {len(d)} points")
    if len(d):
        av = d[d.journees_designees > 0]
        print(f"  points portant des journees designees : {len(av)} / {len(d)}")
        for lib, col in (("|delta m|, retrait de TOUTES", "delta_m_toutes"),
                         ("|delta m|, retrait de l'ETE seul", "delta_m_ete")):
            v = d[col].dropna().abs()
            if len(v):
                print(f"\n  {lib} :")
                print(f"     mediane {v.median():.6f}   p95 {v.quantile(.95):.6f}"
                      f"   MAXIMUM {v.max():.6f}"
                      f"   ({d.loc[d[col].abs().idxmax(), 'point']})")
        for lib, col in (("Tmh_norm, mediane", "Tmh_norm_median_toutes"),
                         ("Tmh_norm, p95", "Tmh_norm_p95_toutes"),
                         ("Tmh_norm, maximum", "Tmh_norm_max_toutes")):
            v = d[col].dropna()
            if len(v):
                print(f"  {lib:<24} : mediane {v.median():.4f}  "
                      f"MAXIMUM {v.max():.4f} degC")
        nc = (d.cat_chr_change == "oui").sum()
        na = (d.cat_aigu_change == "oui").sum()
        print(f"\n  VERDICTS QUI BASCULENT :")
        print(f"     categorie de stress chronique : {nc} point(s)")
        print(f"     categorie de vulnerabilite aigue : {na} point(s)")
        bougent = d[(d.n_aigu_avant != d.n_aigu_apres)]
        print(f"     n_jours_aigus modifie : {len(bougent)} point(s)")
        for _, r in bougent.iterrows():
            print(f"        {r['point']:<32} {r['n_aigu_avant']} -> "
                  f"{r['n_aigu_apres']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
