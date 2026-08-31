"""
mesure_correctif13.py — ETAPE 20 : ce que la fenetre etendue changerait.

MESURE AVANT POSE. Ce script ne modifie rien : il rejoue chaque point deux
fois, avec `hors_eau_mois = (6,7,8,9)` puis `= (1..12)`, en passant la fenetre
par la CONFIGURATION. Aucune source applicative n'est touchee.

================================================================================
CE QUE D105 CHANGE, ET CE QU'IL NE CHANGE PAS
================================================================================
`relativiser` (qc.py:143) regroupe PAR MOIS du point traite, exige au moins
`min_jours_groupe` journees dans le mois et une dispersion superieure au
plancher, et s'abstient sinon. Les douze mois sont traites de facon identique :
etendre la fenetre ne demande aucune methode nouvelle, seulement de lever une
restriction. C'est ce que dit D105, et le code le confirme.

CE QUE L'EXTENSION NE PEUT PAS ATTRAPER, ET QU'IL FAUT DIRE
La marche 1 teste `rel1 > k` sur `e_moy = T_eau_max - T_air` : un depassement
POSITIF, c'est-a-dire une eau trop chaude par rapport a l'air. Une sonde
exondee en hiver lit au contraire TROP FROID — elle suit l'air, qui est plus
froid que l'eau. Son ecart relatif est negatif, et le test unilateral ne le voit
pas. L'extension attrape donc les artefacts de pose et d'etiage, pas les
artefacts d'hiver. Ce n'est pas une raison de ne pas l'etendre ; c'est une
limite a declarer.

================================================================================
LA REGLE D'ALERTE — ECRITE AVANT DE PRODUIRE LE MOINDRE CHIFFRE
================================================================================
Le commanditaire a tranche : le correctif 13 est pose. La mesure n'a donc pas
pour objet de decider s'il faut poser, mais de dire AVANT DE POSER si quelque
chose cloche. Voici ce qui me ferait m'arreter et le signaler plutot que
d'enchainer :

  A — VOLUME. Le detecteur marque aujourd'hui 69 journees sur environ 20 000
      journees estivales, soit 0,35 %. Si l'extension marque PLUS DE 5 % des
      journees hors juin-septembre, le critere ne se comporte pas dehors comme
      dedans, et il faut comprendre pourquoi avant de poser.

  B — CORROBORATION. Les journees nouvellement marquees sont confrontees au
      temoin scelle de l'etape 19, qui est independant du detecteur et dont la
      specificite a ete etablie (tau = 0,205 %). Si MOINS DE 20 % des journees
      nouvellement marquees et jugeables sont classees `artefact` par le temoin,
      les nouvelles marques sont de qualite inferieure aux anciennes et il faut
      le dire avant de poser.

  C — SENS DES VERDICTS. Tout deplacement de categorie est releve et nomme. Un
      deplacement qui AUGMENTE le risque publie doit etre explique : le motif du
      correctif est de retirer des artefacts, et un artefact retire ne peut pas
      aggraver un diagnostic sans raison identifiable.

  D — LES 69. Les journees deja marquees doivent le RESTER. L'extension ajoute
      des mois ; elle ne doit en retirer aucune. Si une seule des 69 disparait,
      c'est que l'extension a change le regroupement mensuel d'un mois deja
      couvert — ce qui serait un effet de bord, pas une restriction levee.

  Les quatre sont des signaux d'alerte, pas des vetos : le commanditaire a
  tranche. Ce qu'ils garantissent, c'est qu'aucun d'eux ne sera decouvert APRES
  la pose.

SORTIES, sous out/etape20/
  A_avant_apres.csv        par point : marquees avant, apres, ajoutees
  A_nouvelles.csv          les journees nouvellement marquees, une par ligne
  A_verdicts.csv           les categories publiees, avant et apres
"""
from __future__ import annotations

import contextlib
import io as _io
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
os.environ.setdefault("THERMIE_CODE", "app")

from _commun import (CODE, RACINE, RACINE_CODE, decouvrir, ecrire_csv,  # noqa: E402
                     nom_point, _f)

import build_reference                                                  # noqa: E402
import temoin_regime as TR                                              # noqa: E402
from thermie_debits import orchestrator                                 # noqa: E402

OUT = RACINE / "out" / "etape20"
ETE = (6, 7, 8, 9)
ANNEE = tuple(range(1, 13))


def _run(jeu, point_rel, mois):
    cfg = build_reference.construire_config(jeu, point_rel, "application")
    cfg.qc.hors_eau_mois = tuple(mois)
    with contextlib.redirect_stdout(_io.StringIO()), \
         contextlib.redirect_stderr(_io.StringIO()):
        return orchestrator.run(cfg, verbose=False)


def _marquees(res):
    rq = res.rapport_qc
    if rq is None or not len(rq):
        return {}
    return {str(x["date"])[:10]: str(x.get("motif", ""))
            for _, x in rq.iterrows() if "hors d" in str(x.get("motif", ""))}


def _cats(res):
    v = res.vulnerabilite or {}
    sg = res.sgvt or {}
    fr = res.fraie or {}
    return dict(cat_aigu=v.get("cat_aigu"), n_aigu=v.get("n_aigu"),
                cat_chr=v.get("cat_chr"), pct_chr=v.get("pct_chr"),
                P_fraie=fr.get("P_fraie"), sgvt=sg.get("sgvt"),
                classe=sg.get("interp"), m=(res.sensibilite or {}).get("m"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print("=" * 78)
    print("ETAPE 20 — CE QUE LA FENETRE ETENDUE CHANGERAIT (mesure avant pose)")
    print("regle d'alerte ecrite en tete de ce fichier")
    print("=" * 78)

    lignes, nouvelles, verdicts, echecs = [], [], [], []
    n_hors_ete_total = 0
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            try:
                av = _run(jeu, point_rel, ETE)
                ap = _run(jeu, point_rel, ANNEE)
            except Exception as exc:
                echecs.append((jeu["jeu"], pt, type(exc).__name__))
                print(f"  · {jeu['jeu']}/{pt} : ECHEC ({type(exc).__name__})",
                      flush=True)
                continue
            m_av, m_ap = _marquees(av), _marquees(ap)
            perdues = sorted(set(m_av) - set(m_ap))
            ajoutees = sorted(set(m_ap) - set(m_av))

            d = ap.df.copy()
            d["ds"] = d["date"].astype(str).str.slice(0, 10)
            dt = pd.to_datetime(d["ds"])
            d["an"], d["doy"] = dt.dt.year, dt.dt.dayofyear
            n_hors_ete_total += int((~d["month"].isin(ETE)).sum())
            par_date = {r["ds"]: r for _, r in d.iterrows()}

            for ds in ajoutees:
                r = par_date.get(ds)
                if r is None:
                    continue
                ref = TR.reference(d, r["doy"], r["an"])
                verdict, exc, dec, n_an, n_j = TR.juger(r, ref)
                nouvelles.append(dict(
                    jeu=jeu["jeu"], point=pt, date=ds,
                    mois=int(r["month"]), motif=m_ap[ds],
                    temoin=verdict, exc=_f(exc), dec=_f(dec),
                    n_annees=n_an, n_jours_ref=n_j,
                    T_eau_moy=_f(r.get("T_eau_moy")), T_air=_f(r.get("T_air"))))

            c_av, c_ap = _cats(av), _cats(ap)
            bouge = [k for k in ("cat_aigu", "cat_chr", "P_fraie", "classe")
                     if c_av[k] != c_ap[k]]
            verdicts.append(dict(
                jeu=jeu["jeu"], point=pt,
                n_aigu_avant=c_av["n_aigu"], n_aigu_apres=c_ap["n_aigu"],
                cat_aigu_avant=c_av["cat_aigu"], cat_aigu_apres=c_ap["cat_aigu"],
                pct_chr_avant=_f(c_av["pct_chr"]), pct_chr_apres=_f(c_ap["pct_chr"]),
                cat_chr_avant=c_av["cat_chr"], cat_chr_apres=c_ap["cat_chr"],
                P_fraie_avant=_f(c_av["P_fraie"]), P_fraie_apres=_f(c_ap["P_fraie"]),
                m_avant=_f(c_av["m"]), m_apres=_f(c_ap["m"]),
                sgvt_avant=_f(c_av["sgvt"]), sgvt_apres=_f(c_ap["sgvt"]),
                classe_avant=c_av["classe"], classe_apres=c_ap["classe"],
                ce_qui_bouge=(", ".join(bouge) if bouge else "rien")))
            lignes.append(dict(
                jeu=jeu["jeu"], point=pt, marquees_avant=len(m_av),
                marquees_apres=len(m_ap), ajoutees=len(ajoutees),
                PERDUES=len(perdues),
                dates_perdues=(" ".join(perdues) if perdues else ""),
                journees_hors_ete=int((~d["month"].isin(ETE)).sum())))
            print(f"  · {jeu['jeu']}/{pt} : {len(m_av)} -> {len(m_ap)} "
                  f"(+{len(ajoutees)}"
                  + (f", -{len(perdues)} PERDUES" if perdues else "") + ")",
                  flush=True)

    ecrire_csv(OUT / "A_avant_apres.csv",
               ["jeu", "point", "marquees_avant", "marquees_apres", "ajoutees",
                "PERDUES", "dates_perdues", "journees_hors_ete"],
               lignes, tri=["jeu", "point"])
    ecrire_csv(OUT / "A_nouvelles.csv",
               ["jeu", "point", "date", "mois", "temoin", "exc", "dec",
                "n_annees", "n_jours_ref", "T_eau_moy", "T_air", "motif"],
               nouvelles, tri=["jeu", "point", "date"])
    ecrire_csv(OUT / "A_verdicts.csv",
               ["jeu", "point", "ce_qui_bouge", "n_aigu_avant", "n_aigu_apres",
                "cat_aigu_avant", "cat_aigu_apres", "pct_chr_avant",
                "pct_chr_apres", "cat_chr_avant", "cat_chr_apres",
                "P_fraie_avant", "P_fraie_apres", "m_avant", "m_apres",
                "sgvt_avant", "sgvt_apres", "classe_avant", "classe_apres"],
               verdicts, tri=["ce_qui_bouge", "jeu", "point"])

    n_av = sum(l["marquees_avant"] for l in lignes)
    n_ap = sum(l["marquees_apres"] for l in lignes)
    n_perdues = sum(l["PERDUES"] for l in lignes)
    nv = pd.DataFrame(nouvelles)
    jug = nv[nv.temoin != TR.INDETERMINABLE] if len(nv) else nv
    n_cor = int((jug.temoin == TR.ARTEFACT).sum()) if len(jug) else 0
    taux_cor = (n_cor / len(jug)) if len(jug) else np.nan
    taux_vol = (len(nv) / n_hors_ete_total) if n_hors_ete_total else np.nan

    print("\n" + "=" * 78)
    print("LES QUATRE SIGNAUX D'ALERTE, APPLIQUES TELS QU'ECRITS")
    print("=" * 78)
    print(f"  journees marquees   : {n_av} -> {n_ap}  (+{len(nv)})")
    print(f"\n  A — VOLUME")
    print(f"      journees hors juin-septembre : {n_hors_ete_total}")
    print(f"      nouvellement marquees        : {len(nv)}  "
          f"({100*taux_vol:.3f} %)")
    print(f"      seuil d'alerte : 5 %  ->  "
          f"{'ALERTE' if taux_vol > 0.05 else 'sous le seuil'}")
    print(f"\n  B — CORROBORATION par le temoin scelle de l'etape 19")
    print(f"      nouvelles jugeables : {len(jug)} / {len(nv)}")
    print(f"      classees artefact   : {n_cor}  ({100*taux_cor:.1f} %)")
    print(f"      seuil d'alerte : 20 %  ->  "
          f"{'ALERTE' if taux_cor < 0.20 else 'au-dessus du seuil'}")
    if len(nv):
        print(f"      repartition du temoin : "
              f"{nv.temoin.value_counts().to_dict()}")
    print(f"\n  C — SENS DES VERDICTS")
    bg = [v for v in verdicts if v["ce_qui_bouge"] != "rien"]
    print(f"      points dont une categorie bouge : {len(bg)}")
    for v in bg:
        print(f"        {v['point']:<34} {v['ce_qui_bouge']}")
        print(f"           aigu  {v['n_aigu_avant']}j « {v['cat_aigu_avant']} »"
              f"  ->  {v['n_aigu_apres']}j « {v['cat_aigu_apres']} »")
        print(f"           SGVT  {v['sgvt_avant']} « {v['classe_avant']} »"
              f"  ->  {v['sgvt_apres']} « {v['classe_apres']} »")
        print(f"           fraie {v['P_fraie_avant']} -> {v['P_fraie_apres']}")
    print(f"\n  D — LES 69 DOIVENT RESTER")
    print(f"      journees perdues : {n_perdues}  ->  "
          f"{'ALERTE' if n_perdues else 'aucune'}")
    if n_perdues:
        for l in lignes:
            if l["PERDUES"]:
                print(f"        {l['point']} : {l['dates_perdues']}")
    if len(nv):
        print(f"\n  Les nouvelles marques, par mois :")
        for m, n in nv.groupby("mois").size().items():
            print(f"     mois {int(m):>2} : {n}")
    if echecs:
        print("\n  ECHECS DE REJEU (declares) :")
        for j, p, e in echecs:
            print(f"     {j}/{p} : {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
