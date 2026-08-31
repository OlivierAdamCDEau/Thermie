"""
verifier_faux_positifs.py — ETAPE 18 : le detecteur ne retire-t-il que des
artefacts ?

AUCUNE MODIFICATION APPLICATIVE. Ce module lit, mesure et classe. Il ne pose
rien, ne corrige rien, n'ajoute aucune regle a l'application.

LA QUESTION
------------
Le detecteur vise un DECOUPLAGE entre l'eau et l'air, pas une temperature
elevee : pendant une canicule les deux montent ensemble et la journee n'est pas
marquee. Mais un cours d'eau reduit a quelques flaques se decouple aussi — et
c'est une vraie journee de vulnerabilite aigue.

Le SENS DE L'ERREUR a change. V4.5 ratait des exondations sans en inventer ;
V4.6 peut en inventer, et un faux positif RETIRE UNE ALERTE REELLE d'un
document remis a un maitre d'ouvrage.

LA REDUCTION
-------------
Une journee marquee qui ne franchissait aucun seuil piscicole ne coute aucun
verdict. Le sous-ensemble a instruire est celui des journees marquees qui EN
FRANCHISSAIENT un — etabli en rejouant la chaine DETECTEUR ETEINT
(`cfg.qc.hors_eau = False`), ce qui donne exactement le verdict que le marquage
a retire.

================================================================================
LA REGLE DE DECISION — ECRITE AVANT DE PRODUIRE LE MOINDRE CHIFFRE
================================================================================

Quatre temoins, aucun decisif seul. Chacun rend `exondation`, `evenement` ou
`indecidable`. Tous les seuils sont des QUANTILES DU POINT TRAITE : aucune
valeur importee, aucune valeur commune a plusieurs points (D15, D41).

  TEMOIN 1 — L'AMPLITUDE.  R_ampl = (T_eau_max - T_eau_min) / (TX - TN)
      Une sonde a l'air libre suit l'amplitude de l'air ; une flaque garde une
      part de l'inertie de l'eau.
        R_ampl >= q90 des journees estivales du point   -> exondation
        R_ampl <= mediane des journees estivales        -> evenement
        entre les deux, ou TN/TX/T_eau_min manquants    -> indecidable

      NEUTRALISATION OBLIGATOIRE, ecrite ici avant tout chiffre. La marche 2 du
      detecteur teste `ampl_eau / ampl_air` relativise par mois (qc.py, l. 375).
      Sur une journee que la marche 2 a effectivement declenchee, ce temoin ne
      serait pas un temoin : il redirait le detecteur, et sa concordance serait
      une tautologie. Il rend donc `indecidable` des que le motif de la journee
      porte la marche 2. Il ne temoigne que la ou la marche 1 a marque SEULE.
      Le prix de cette honnetete est un nombre d'indecidables plus eleve ; il
      est assume.

  TEMOIN 2 — LE DEBIT.
      Un vrai etiage thermique et une sonde exondee ont tous deux un debit bas :
      le debit ne separe pas seul. Mais un debit NORMAL sous une journee marquee
      est une alerte forte — l'eau etait la.
        Q <= q10 des journees estivales du point        -> exondation
        Q >= mediane des journees estivales             -> evenement
        entre les deux, ou aucun debit                  -> indecidable

  TEMOIN 3 — LA FORME DE LA SORTIE D'EPISODE.
      Une sonde qui retrouve l'eau produit une RUPTURE ; un evenement thermique
      redescend avec l'air. On mesure la variation de l'ecart eau-air entre le
      dernier jour de l'episode et le lendemain, rapportee a l'habitude du
      point. Ce temoin ne se prononce qu'en FIN d'episode : ailleurs il n'a rien
      a lire, et il le dit.
        |variation| >= q90 des variations journalieres    -> exondation
        |variation| <= mediane                            -> evenement
        entre les deux, journee interne, lendemain absent -> indecidable

  TEMOIN 4 — LA SYNCHRONIE SPATIALE, sur jeu_bienne seulement (27 points).
      Un evenement meteorologique ou hydrologique touche un bassin ; une sonde
      mal posee est une sonde. VERIFICATION, jamais regle : D41 interdit qu'une
      REGLE depende d'un corpus multi-points, il n'interdit pas de s'en servir
      pour controler. Rien n'est pose dans l'application.
        aucun autre point marque le meme jour           -> exondation
        3 autres points ou plus marques le meme jour    -> evenement
        1 ou 2 autres, ou point hors jeu_bienne         -> indecidable

  CLASSEMENT FINAL, ET SON ASYMETRIE ASSUMEE
        exondation  : au moins DEUX temoins disent exondation
                      ET aucun ne dit evenement.
        evenement   : au moins UN temoin dit evenement
                      ET aucun ne dit exondation.
        indecidable : tout le reste.

      L'asymetrie est deliberee et se justifie par le COUT DES DEUX ERREURS.
      Classer a tort une journee en « exondation » revient a valider le retrait
      d'une alerte reelle d'un document remis a un maitre d'ouvrage. Classer a
      tort en « evenement » revient a rouvrir une instruction. Le second cout
      est reparable, le premier ne l'est pas. La charge de la preuve pese donc
      sur « exondation ».

  CE QUI EST ACCEPTABLE, ET CE QUI NE L'EST PAS
      Les trois issues sont acceptables, y compris « toutes indecidables ».
      La seule chose qui ne l'est pas serait de choisir le critere apres avoir
      vu les journees. C'est pourquoi cette regle est ecrite ici, dans le
      fichier qui produit les chiffres, et livree avec eux.

SORTIES
  out/etape18/A_toutes_marquees.csv   les journees marquees, seuils franchis ou non
  out/etape18/A_sous_ensemble.csv     celles qui coutent un verdict
  out/etape18/B_temoins.csv           les quatre temoins, journee par journee
  out/etape18/C_verdict.csv           le classement
  out/etape18/B3_episodes.csv         la forme des episodes, jour par jour
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
from thermie_debits import orchestrator                                 # noqa: E402

OUT = RACINE / "out" / "etape18"
MOIS_ETE = (6, 7, 8, 9)

EXO, EVT, IND = "exondation", "evenement", "indecidable"


def _q(serie, q):
    s = pd.Series(serie, dtype="float64").dropna()
    return float(s.quantile(q)) if len(s) else np.nan


def temoin_amplitude(jour, ref):
    """T1 — l'amplitude de l'eau rapportee a celle de l'air."""
    if jour.get("marche2_a_marque"):
        return IND, jour.get("R_ampl")          # neutralise : cf. en-tete
    r = jour.get("R_ampl")
    if r is None or not np.isfinite(r) or not np.isfinite(ref.get("R_q90", np.nan)):
        return IND, None
    if r >= ref["R_q90"]:
        return EXO, r
    if r <= ref["R_med"]:
        return EVT, r
    return IND, r


def temoin_debit(jour, ref):
    """T2 — le debit du jour, rapporte a l'etiage habituel du point."""
    q = jour.get("Q")
    if q is None or not np.isfinite(q) or not np.isfinite(ref.get("Q_q10", np.nan)):
        return IND, None
    if q <= ref["Q_q10"]:
        return EXO, q
    if q >= ref["Q_med"]:
        return EVT, q
    return IND, q


def temoin_forme(jour, ref):
    """T3 — la brutalite de la sortie d'episode."""
    v = jour.get("variation_sortie")
    if v is None or not np.isfinite(v) or not np.isfinite(ref.get("V_q90", np.nan)):
        return IND, None
    if abs(v) >= ref["V_q90"]:
        return EXO, abs(v)
    if abs(v) <= ref["V_med"]:
        return EVT, abs(v)
    return IND, abs(v)


def temoin_synchronie(jour):
    """T4 — combien d'AUTRES points du meme bassin sont marques ce jour-la."""
    n = jour.get("n_autres_points")
    if n is None:
        return IND, None
    if n == 0:
        return EXO, 0
    if n >= 3:
        return EVT, n
    return IND, n


def classer(verdicts):
    """La regle finale, telle qu'ecrite en tete de ce fichier."""
    n_exo = sum(1 for v in verdicts if v == EXO)
    n_evt = sum(1 for v in verdicts if v == EVT)
    if n_exo >= 2 and n_evt == 0:
        return EXO
    if n_evt >= 1 and n_exo == 0:
        return EVT
    return IND


def episodes(dates):
    """Regroupe des dates en episodes calendairement contigus."""
    if not dates:
        return []
    d = sorted(dates)
    eps, cur = [], [d[0]]
    for a, b in zip(d, d[1:]):
        if (pd.Timestamp(b) - pd.Timestamp(a)).days == 1:
            cur.append(b)
        else:
            eps.append(cur)
            cur = [b]
    eps.append(cur)
    return eps


def _run(jeu, point_rel, hors_eau=None):
    cfg = build_reference.construire_config(jeu, point_rel, "application")
    if hors_eau is not None:
        cfg.qc.hors_eau = hors_eau
    with contextlib.redirect_stdout(_io.StringIO()), \
         contextlib.redirect_stderr(_io.StringIO()):
        return orchestrator.run(cfg, verbose=False)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print("=" * 78)
    print("ETAPE 18 — LE DETECTEUR NE RETIRE-T-IL QUE DES ARTEFACTS ?")
    print("Regle de decision ecrite en tete de ce fichier, avant les chiffres.")
    print("=" * 78)

    toutes, candidats, eps_detail = [], [], []
    marques_bienne = {}

    # ================================================================
    # PHASE 1 — repasser chaque point, relever les journees marquees,
    #           puis rejouer DETECTEUR ETEINT les points concernes.
    # ================================================================
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            try:
                ref = _run(jeu, point_rel)
            except Exception as exc:
                print(f"  · {jeu['jeu']}/{pt} : rejeu en echec "
                      f"({type(exc).__name__})", flush=True)
                continue
            rq = ref.rapport_qc
            marquees = {}
            if rq is not None and len(rq):
                for _, x in rq.iterrows():
                    mot = str(x.get("motif", ""))
                    if "hors d" in mot:
                        marquees[str(x["date"])[:10]] = mot
            if not marquees:
                continue
            if jeu["jeu"] == "jeu_bienne":
                for dt in marquees:
                    marques_bienne.setdefault(dt, set()).add(pt)

            try:
                sans = _run(jeu, point_rel, hors_eau=False)
            except Exception as exc:
                print(f"  · {pt} : contrefactuel en echec "
                      f"({type(exc).__name__})", flush=True)
                continue

            d = sans.df.copy()
            d["date_s"] = d["date"].astype(str).str.slice(0, 10)
            v = sans.vulnerabilite or {}
            s_chr, s_aig = v.get("seuil_chr"), v.get("seuil_aigu")

            ete = d[d["month"].isin(MOIS_ETE)]
            if {"TX", "TN", "T_eau_min"} <= set(d.columns):
                amp_air = (ete["TX"] - ete["TN"]).replace(0, np.nan)
                r_ete = (ete["T_eau_max"] - ete["T_eau_min"]) / amp_air
            else:
                r_ete = pd.Series(dtype="float64")
            variation = (d["T_eau_moy"] - d["T_air"]).diff().abs()
            refp = dict(
                R_q90=_q(r_ete, 0.90), R_med=_q(r_ete, 0.50),
                Q_q10=_q(ete["Q"], 0.10) if "Q" in ete.columns else np.nan,
                Q_med=_q(ete["Q"], 0.50) if "Q" in ete.columns else np.nan,
                V_q90=_q(variation, 0.90), V_med=_q(variation, 0.50))

            par_date = {r["date_s"]: r for _, r in d.iterrows()}
            fins = {e[-1] for e in episodes([m for m in marquees
                                             if m in par_date])}

            for dt, motif in sorted(marquees.items()):
                r = par_date.get(dt)
                if r is None:
                    toutes.append(dict(jeu=jeu["jeu"], point=pt, date=dt,
                                       franchit="INCONNU — journee absente du "
                                                "contrefactuel", motif=motif))
                    continue
                tmh_n, tmax_n = r.get("Tmh_norm"), r.get("Tmax_norm")
                brut = r.get("T_eau_max")
                estival = int(r.get("month", 0)) in MOIS_ETE
                fr_aigu = bool(estival and pd.notna(tmax_n) and s_aig is not None
                               and tmax_n > s_aig)
                fr_chr = bool(estival and pd.notna(tmh_n) and s_chr is not None
                              and tmh_n > s_chr)
                fr_brut = bool(pd.notna(brut) and s_aig is not None
                               and brut > s_aig)
                seuils = []
                if fr_aigu:
                    seuils.append(f"aigu {s_aig} degC (Tmax_norm {tmax_n:.2f}, "
                                  f"marge +{tmax_n - s_aig:.2f})")
                if fr_chr:
                    seuils.append(f"chronique {s_chr} degC (Tmh_norm "
                                  f"{tmh_n:.2f}, marge +{tmh_n - s_chr:.2f})")
                if fr_brut and not fr_aigu:
                    seuils.append(f"aigu sur la grandeur BRUTE (T_eau_max "
                                  f"{brut:.2f} > {s_aig})")
                ligne = dict(
                    jeu=jeu["jeu"], point=pt, date=dt, motif=motif,
                    mois=int(r.get("month", 0)),
                    franchit=" ; ".join(seuils) if seuils else "aucun seuil",
                    seuil_aigu=s_aig, seuil_chronique=s_chr,
                    T_eau_max_brut=_f(brut), Tmax_norm=_f(tmax_n),
                    Tmh_norm=_f(tmh_n),
                    marge_aigu=_f(tmax_n - s_aig) if fr_aigu else None,
                    marge_chronique=_f(tmh_n - s_chr) if fr_chr else None)
                toutes.append(ligne)
                if not (fr_aigu or fr_chr or fr_brut):
                    continue

                # ---- les quatre temoins, sur ce candidat
                aa = (float(r.get("TX")) - float(r.get("TN"))
                      if pd.notna(r.get("TX")) and pd.notna(r.get("TN"))
                      else np.nan)
                r_ampl = ((r["T_eau_max"] - r["T_eau_min"]) / aa
                          if (np.isfinite(aa) and aa != 0
                              and pd.notna(r.get("T_eau_min"))) else np.nan)
                var_sortie = np.nan
                if dt in fins:
                    suiv = str(pd.Timestamp(dt) + pd.Timedelta(days=1))[:10]
                    rs = par_date.get(suiv)
                    if rs is not None:
                        var_sortie = float((rs["T_eau_moy"] - rs["T_air"])
                                           - (r["T_eau_moy"] - r["T_air"]))
                candidats.append(dict(
                    ligne, refp=refp, R_ampl=r_ampl, Q=r.get("Q"),
                    variation_sortie=var_sortie,
                    marche2_a_marque=("marche 2" in motif
                                      or "amplitude" in motif.lower()),
                    fin_episode=("oui" if dt in fins else "non")))

                for k in (-3, -2, -1, 0, 1, 2, 3):
                    dk = str(pd.Timestamp(dt) + pd.Timedelta(days=k))[:10]
                    rk = par_date.get(dk)
                    if rk is None:
                        continue
                    eps_detail.append(dict(
                        point=pt, date_marquee=dt, decalage=k, date=dk,
                        T_eau_moy=_f(rk.get("T_eau_moy")),
                        T_air=_f(rk.get("T_air")),
                        ecart=_f(rk.get("T_eau_moy") - rk.get("T_air")),
                        T_eau_max=_f(rk.get("T_eau_max")),
                        T_eau_min=_f(rk.get("T_eau_min")),
                        Q=_f(rk.get("Q"))))
            print(f"  · {jeu['jeu']}/{pt} : {len(marquees)} marquee(s)",
                  flush=True)

    # ================================================================
    # PHASE 2 — la synchronie est connue : on classe.
    # ================================================================
    temoins = []
    for c in candidats:
        c["n_autres_points"] = (
            len(marques_bienne.get(c["date"], set()) - {c["point"]})
            if c["jeu"] == "jeu_bienne" else None)
        refp = c["refp"]
        v1, x1 = temoin_amplitude(c, refp)
        v2, x2 = temoin_debit(c, refp)
        v3, x3 = temoin_forme(c, refp)
        v4, x4 = temoin_synchronie(c)
        temoins.append(dict(
            jeu=c["jeu"], point=c["point"], date=c["date"],
            franchit=c["franchit"],
            T1_amplitude=v1, R_ampl=_f(x1),
            R_ampl_q90_du_point=_f(refp["R_q90"]),
            R_ampl_median_du_point=_f(refp["R_med"]),
            T1_neutralise=("oui — marche 2" if c["marche2_a_marque"] else "non"),
            T2_debit=v2, Q=_f(x2), Q_q10_du_point=_f(refp["Q_q10"]),
            Q_median_du_point=_f(refp["Q_med"]),
            T3_forme=v3, variation_sortie=_f(x3),
            variation_q90_du_point=_f(refp["V_q90"]),
            variation_med_du_point=_f(refp["V_med"]),
            T4_synchronie=v4, autres_points_marques=x4,
            fin_episode=c["fin_episode"],
            VERDICT=classer([v1, v2, v3, v4])))

    cols_a = ["jeu", "point", "date", "mois", "franchit", "seuil_aigu",
              "seuil_chronique", "T_eau_max_brut", "Tmax_norm", "Tmh_norm",
              "marge_aigu", "marge_chronique", "motif"]
    ecrire_csv(OUT / "A_toutes_marquees.csv", cols_a, toutes,
               tri=["jeu", "point", "date"])
    ecrire_csv(OUT / "A_sous_ensemble.csv", cols_a, candidats,
               tri=["jeu", "point", "date"])
    cols_b = ["jeu", "point", "date", "franchit", "T1_amplitude", "R_ampl",
              "R_ampl_q90_du_point", "R_ampl_median_du_point", "T1_neutralise",
              "T2_debit", "Q", "Q_q10_du_point", "Q_median_du_point",
              "T3_forme", "variation_sortie", "variation_q90_du_point",
              "variation_med_du_point", "T4_synchronie",
              "autres_points_marques", "fin_episode", "VERDICT"]
    ecrire_csv(OUT / "B_temoins.csv", cols_b, temoins,
               tri=["jeu", "point", "date"])
    ecrire_csv(OUT / "C_verdict.csv",
               ["VERDICT", "jeu", "point", "date", "franchit", "T1_amplitude",
                "T2_debit", "T3_forme", "T4_synchronie"],
               temoins, tri=["VERDICT", "jeu", "point", "date"])
    ecrire_csv(OUT / "B3_episodes.csv",
               ["point", "date_marquee", "decalage", "date", "T_eau_moy",
                "T_air", "ecart", "T_eau_max", "T_eau_min", "Q"],
               eps_detail, tri=["point", "date_marquee", "decalage"])

    print("\n" + "=" * 78)
    print("TACHE A — LE SOUS-ENSEMBLE QUI COUTE UN VERDICT")
    print("=" * 78)
    print(f"  journees marquees relevees            : {len(toutes)}")
    print(f"  dont franchissant un seuil piscicole  : {len(candidats)}")
    if candidats:
        pc = pd.DataFrame(candidats).groupby("point").size()
        for p, n in pc.sort_values(ascending=False).items():
            print(f"     {p:<36} {n}")
    plaine = [c for c in candidats if "PLAINE" in c["point"].upper()]
    print(f"\n  LA PLAINE A RAON-SUR-PLAINE : {len(plaine)} journee(s) "
          f"franchissant un seuil")
    for c in sorted(plaine, key=lambda x: x["date"]):
        print(f"     {c['date']}  {c['franchit']}")

    print("\n" + "=" * 78)
    print("TACHE C — LE VERDICT, SELON LA REGLE ECRITE D'AVANCE")
    print("=" * 78)
    t = pd.DataFrame(temoins)
    if len(t):
        for v in (EXO, EVT, IND):
            print(f"  {v:<14} : {int((t.VERDICT == v).sum())}")
        print()
        for tem in ("T1_amplitude", "T2_debit", "T3_forme", "T4_synchronie"):
            print(f"  {tem:<16} {t[tem].value_counts().to_dict()}")
        evt = t[t.VERDICT == EVT]
        if len(evt):
            print("\n  *** JOURNEES CLASSEES EVENEMENT THERMIQUE REEL ***")
            for _, r in evt.iterrows():
                print(f"     {r['point']:<34} {r['date']}  "
                      f"T1={r['T1_amplitude']} T2={r['T2_debit']} "
                      f"T3={r['T3_forme']} T4={r['T4_synchronie']}")
        else:
            print("\n  Aucune journee classee « evenement thermique reel ».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
