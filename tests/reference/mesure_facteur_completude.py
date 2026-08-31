"""
mesure_facteur_completude.py — ETAPE 16, TACHE A (D91) : le facteur du critere
de completude, DEPARTAGE SUR PIECES.

D91 refuse qu'un nombre soit choisi par argument plausible dans un chantier qui
a mesure quinze etapes durant. La specification retenait 4x « parce que le
temoin separe d'un facteur 2,6 » — sans avoir verifie ce que 2x et 3x
donnaient. C'est exactement l'erreur de forme que le chantier s'interdit.

CE QUE CE MODULE MESURE
------------------------
Pour chaque facteur k dans {2, 3, 4} : les journees designees, les points
concernes, la separation du temoin independant, et l'effet sur BLE3-0.

LA REGLE DE DECISION, ECRITE AVANT LES CHIFFRES (methode de l'etape 3)
-----------------------------------------------------------------------
Le temoin independant est l'ECART DE LA JOURNEE A LA MOYENNE DE SES VOISINES
calendaires (J-1, J+1). Il ne regarde pas les horodatages, donc pas le critere.
On note S(k) le RAPPORT entre la mediane de cet ecart sur les journees
designees et sa mediane sur les autres.

  UN FACTEUR PLUS PERMISSIF (k plus petit, donc plus de journees designees)
  EST RETENU si, en descendant a ce facteur :
      · la separation S(k) reste >= 2,0 — le critere continue de designer des
        journees qui se distinguent reellement ; ET
      · la part designee reste sous 1 % des journees du corpus — au-dela, le
        critere cesse d'etre un signalement et devient une description de
        l'ordinaire.

  IL EST ECARTE si S(k) tombe sous 2,0, ou si la part depasse 1 %. Un seuil
  qui designe davantage n'est pas plus prudent s'il designe des journees
  ordinaires : il dilue le signalement.

  ENTRE DEUX FACTEURS QUI PASSENT TOUS DEUX, on retient LE PLUS PERMISSIF —
  celui qui designe le plus —, parce qu'un critere de signalement doit
  privilegier la sensibilite tant que sa specificite tient. Ce choix est ecrit
  ici, avant les chiffres, pour ne pas se decider apres.

  PRECISION AJOUTEE D'AVANCE : un point dont le trou median vaut 24 h — ses
  horodatages sont detruits — ne porte aucun contraste et est rapporte a part,
  quel que soit k.

SORTIE
  out/etape16/A_facteur.csv
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import (CODE, RACINE, RACINE_CODE, decouvrir, ecrire_csv,  # noqa: E402
                     nom_point, _f)
from thermie_debits import io_data                                      # noqa: E402

from mesure_completude_journee import trous_par_journee, ecart_aux_voisines  # noqa: E402

OUT = RACINE / "out" / "etape16"

FACTEURS = (2.0, 3.0, 4.0)
SEPARATION_MIN = 2.0     # rapport des medianes, en deca : facteur ecarte
PART_MAX_PCT = 1.0       # % des journees du corpus, au-dela : facteur ecarte
TROU_HORODATAGE_CASSE = 23.9   # h — au-dela, les horodatages ne disent rien


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print("=" * 74)
    print("TACHE A (D91) — LE FACTEUR, DEPARTAGE SUR PIECES")
    print("Regle de decision ecrite en tete de ce fichier, avant les chiffres.")
    print("=" * 74)

    # Un seul passage de lecture ; les trois facteurs se calculent dessus.
    donnees = []
    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            try:
                daily, sub, _m = io_data.marquer_lecture(
                    str(RACINE / point_rel), nom=point_rel.split("/")[-1],
                    retour_sous_quotidien=True)
            except Exception:
                continue
            if not len(daily):
                continue
            d = ecart_aux_voisines(daily)
            d = d.merge(trous_par_journee(sub), on="date", how="left")
            trou = d["trou_max_h"].to_numpy(dtype=float)
            if not np.isfinite(trou).any():
                continue
            donnees.append(dict(jeu=jeu["jeu"], point=pt, d=d, trou=trou,
                                med=float(np.nanmedian(trou))))
            print(f"  · {jeu['jeu']}/{pt}", flush=True)

    lignes = []
    print()
    for k in FACTEURS:
        n_des = n_tot = 0
        pts = set()
        e_des, e_aut = [], []
        ble = None
        for r in donnees:
            d, trou, med = r["d"], r["trou"], r["med"]
            seuil = k * med
            des = np.where(np.isfinite(trou), trou > seuil, False)
            e = np.abs(d["ecart_voisines"].to_numpy(dtype=float))
            fini = np.isfinite(e)
            md = e[fini & des]
            ma = e[fini & ~des]
            if len(md):
                e_des.append(float(np.median(md)))
            if len(ma):
                e_aut.append(float(np.median(ma)))
            n_des += int(des.sum())
            n_tot += len(d)
            if des.any():
                pts.add(r["point"])
            if med >= TROU_HORODATAGE_CASSE:
                ble = dict(point=r["point"], med=med, seuil=seuil,
                           designees=int(des.sum()), journees=len(d))
        s_des = float(np.median(e_des)) if e_des else np.nan
        s_aut = float(np.median(e_aut)) if e_aut else np.nan
        sep = s_des / s_aut if s_aut else np.nan
        part = 100.0 * n_des / n_tot if n_tot else 0.0
        retenu_possible = (sep >= SEPARATION_MIN) and (part <= PART_MAX_PCT)
        lignes.append(dict(
            facteur=k, journees_designees=n_des, journees_corpus=n_tot,
            part_pct=_f(part), points_concernes=len(pts),
            ecart_median_designees=_f(s_des), ecart_median_autres=_f(s_aut),
            separation=_f(sep),
            passe_la_regle="oui" if retenu_possible else "NON",
            motif_si_ecarte=("" if retenu_possible else
                             ("separation < 2,0" if sep < SEPARATION_MIN
                              else "part > 1 %")),
            horodatages_casses_point=(ble or {}).get("point", ""),
            horodatages_casses_seuil_h=_f((ble or {}).get("seuil")),
            horodatages_casses_designees=(ble or {}).get("designees")))
        print(f"  k = {k:.0f}x  ->  {n_des:>4} journees ({part:.3f} %), "
              f"{len(pts):>2} points, separation x{sep:.2f}  "
              f"[{'passe' if retenu_possible else 'ECARTE'}]")

    ecrire_csv(OUT / "A_facteur.csv",
               ["facteur", "journees_designees", "journees_corpus", "part_pct",
                "points_concernes", "ecart_median_designees",
                "ecart_median_autres", "separation", "passe_la_regle",
                "motif_si_ecarte", "horodatages_casses_point",
                "horodatages_casses_seuil_h", "horodatages_casses_designees"],
               lignes, tri=["facteur"])

    print("\n" + "=" * 74)
    print("LE DETAIL, FACTEUR PAR FACTEUR")
    print("=" * 74)
    for l in lignes:
        print(f"\n  facteur {l['facteur']:.0f}x")
        print(f"     journees designees   : {l['journees_designees']} "
              f"({l['part_pct']:.3f} % du corpus)")
        print(f"     points concernes     : {l['points_concernes']} / "
              f"{len(donnees)}")
        print(f"     temoin — designees   : {l['ecart_median_designees']:.4f} degC")
        print(f"     temoin — autres      : {l['ecart_median_autres']:.4f} degC")
        print(f"     SEPARATION           : x{l['separation']:.2f}")
        print(f"     regle                : {l['passe_la_regle']}"
              + (f"  ({l['motif_si_ecarte']})" if l['motif_si_ecarte'] else ""))
        if l["horodatages_casses_point"]:
            print(f"     horodatages detruits : {l['horodatages_casses_point']} "
                  f"— seuil derive {l['horodatages_casses_seuil_h']:.1f} h, "
                  f"{l['horodatages_casses_designees']} journee(s) designee(s)")

    passent = [l for l in lignes if l["passe_la_regle"] == "oui"]
    print("\n" + "-" * 74)
    print("  VERDICT SELON LA REGLE ECRITE AVANT LES CHIFFRES :")
    if not passent:
        print("     AUCUN facteur ne passe. Le critere ne se derive pas du")
        print("     corpus, et l'alternative doit etre rouverte.")
    else:
        # « Entre deux facteurs qui passent, on retient LE PLUS PERMISSIF »,
        # c'est-a-dire le plus PETIT facteur.
        retenu = min(passent, key=lambda l: l["facteur"])
        print(f"     facteurs qui passent : "
              f"{[f'{l['facteur']:.0f}x' for l in passent]}")
        print(f"     RETENU : {retenu['facteur']:.0f}x — le plus permissif "
              f"parmi ceux qui passent")
        print(f"     {retenu['journees_designees']} journees "
              f"({retenu['part_pct']:.3f} %), separation "
              f"x{retenu['separation']:.2f}")
    print("-" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
