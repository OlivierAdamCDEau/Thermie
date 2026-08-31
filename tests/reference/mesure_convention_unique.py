"""
mesure_convention_unique.py — ETAPE 12, TACHE C : chiffrer l'alternative C4.

CE QUE CE MODULE MESURE, ET CE QU'IL NE FAIT PAS
-------------------------------------------------
Il ne modifie RIEN dans `app/`. Il rejoue la chaine telle qu'elle est
(`THERMIE_CODE=app`, `orchestrator.run`, le meme constructeur de configuration
que `build_reference.py`), puis recalcule le tableau mensuel une SECONDE fois
en substituant a l'anomalie brute `Delta_TMm` la quantite `m x Delta_TMm_liss`.

C'est exactement la VOIE A de l'alternative C4 : les colonnes de compensation
subsistent, recalculees a la convention de la famille normalisation. La voie B
— les colonnes disparaissent — ne demande aucun calcul : elle se lit sur
l'inventaire des colonnes.

POURQUOI LA SUBSTITUTION D'UNE COLONNE SUFFIT
----------------------------------------------
`indicateurs.calcul_indicateurs` n'emploie `Delta_TMm` qu'aux lignes 86-90,
pour construire `T_moy_comp`, `T_max_comp` et `T_min_comp`. Aucun autre calcul
du module ne la lit — `ecart_eau_air` est bati sur `T_air`, pas sur l'anomalie.
Substituer la colonne en entree produit donc exactement la table de la voie A,
sans reecrire une ligne de l'application. C'est la methode de l'etape 6 :
calculer les DEUX versions cote a cote plutot que de corriger puis mesurer.

CE QUE LA MESURE DOIT ETABLIR
------------------------------
  C1  les six series et leur etat courant (fichier:ligne, coefficient) ;
  C3  les colonnes du tableau mensuel, dans l'ordre, et lesquelles des six
      premieres — celles que `livrables.py:257` retient — sont concernees ;
  C4  combien de valeurs bougent en voie A, combien de colonnes disparaissent
      en voie B, et sur quels artefacts ;
  C5  ce que la famille compensation porte que la famille normalisation ne
      porte pas ;
  E   D67 — combien de coefficients saisonniers sont replies faute d'effectif
      sur l'etat ACTUEL de la chaine. Prediction falsifiable.

SORTIES
  out/etape12/C1_series.csv
  out/etape12/C3_colonnes_tableau_mensuel.csv
  out/etape12/C4_valeurs_deplacees.csv
  out/etape12/C4_resume.csv
  out/etape12/E_d67_m_saisonnier.csv
"""
from __future__ import annotations

import contextlib
import io as _io
import os
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import (CODE, RACINE, RACINE_CODE, Journal, decouvrir,  # noqa: E402
                     ecrire_csv, nom_point, _f)

import build_reference                                              # noqa: E402
from thermie_debits import orchestrator, indicateurs as indmod      # noqa: E402

OUT = RACINE / "out" / "etape12"

# Les trois colonnes publiees que la famille compensation alimente. Ecrites
# ici plutot que devinees : une liste devinee sur les colonnes presentes
# manquerait celle qu'un point sans `Delta_TMm` ne produit pas.
COLS_COMP = ["Tmax comp (°C)", "Tmin comp (°C)", "Tmm30j comp (°C)"]

# `livrables.py:257` : `cols = [c for c in t.columns][:6]`.
N_COLS_DOCX = 6


def table_option_a(res):
    """
    Le tableau mensuel de la VOIE A : `T − m × Delta_TMm_liss` au lieu de
    `T − Delta_TMm`, obtenu en substituant la seule colonne que
    `calcul_indicateurs` lit pour construire la famille compensation.
    """
    df = res.df
    if df is None or not len(df) or "Delta_TMm" not in df.columns:
        return None
    m = (res.sensibilite or {}).get("m")
    if m is None:
        return None
    d2 = df.copy()
    anomalie = (d2["Delta_TMm_liss"] if "Delta_TMm_liss" in d2.columns
                else d2["Delta_TMm"])
    d2["Delta_TMm"] = m * anomalie
    with contextlib.redirect_stdout(_io.StringIO()):
        out = indmod.calcul_indicateurs(d2, res.sub_eau, verbose=False)
    return out["table_mensuelle"]


def comparer_tables(point, t_now, t_a):
    """
    Cellule par cellule, sur les seules colonnes de la famille compensation.

    Une cellule « bouge » si les deux valeurs different apres l'arrondi que
    `indicateurs.py` applique lui-meme (2 decimales). Comparer avant arrondi
    compterait comme deplacees des valeurs que le livrable affiche a
    l'identique — l'erreur symetrique de celle de l'etape 8, ou un artefact
    avait ete pris pour le perimetre d'une mesure.
    """
    lignes = []
    if t_now is None or t_a is None:
        return lignes
    par_periode_a = {r["Période"]: r for _, r in t_a.iterrows()}
    for _, r in t_now.iterrows():
        per = r["Période"]
        ra = par_periode_a.get(per)
        if ra is None:
            continue
        for col in COLS_COMP:
            if col not in t_now.columns:
                continue
            v0, v1 = r.get(col), ra.get(col)
            n0, n1 = pd.notna(v0), pd.notna(v1)
            if not n0 and not n1:
                continue
            if n0 and n1:
                bouge = round(float(v0), 2) != round(float(v1), 2)
                ecart = float(v1) - float(v0)
            else:
                bouge, ecart = True, None
            lignes.append(dict(
                point=point, periode=per, colonne=col,
                valeur_actuelle=_f(v0) if n0 else None,
                valeur_voie_A=_f(v1) if n1 else None,
                ecart=_f(ecart) if ecart is not None else None,
                bouge="oui" if bouge else "non"))
    return lignes


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")

    c1, c3, c4, e67 = [], [], [], []
    resume = dict(points_traites=0, points_en_echec=0,
                  points_avec_compensation=0, points_m_nul=0,
                  cellules_comparees=0, cellules_deplacees=0,
                  cellules_apparues_ou_disparues=0)
    ecart_max, ecart_max_ou = 0.0, ""
    colonnes_vues = {}

    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            point = nom_point(point_rel)
            print(f"  · {jeu['jeu']} / {point}", flush=True)
            journal = Journal()
            originaux = journal.installer()
            tampon = _io.StringIO()
            res, erreur = None, ""
            try:
                cfg = build_reference.construire_config(jeu, point_rel,
                                                        "application")
                with contextlib.redirect_stdout(tampon), \
                     contextlib.redirect_stderr(tampon):
                    res = orchestrator.run(cfg, verbose=True)
            except Exception as exc:                        # D7 : l'echec est
                erreur = f"{type(exc).__name__}: {exc}"     # une donnee
                tampon.write("\n" + traceback.format_exc())
            finally:
                Journal.restaurer(originaux)
                try:
                    import matplotlib.pyplot as plt
                    plt.close("all")
                except Exception:
                    pass

            if res is None:
                resume["points_en_echec"] += 1
                c1.append(dict(jeu=jeu["jeu"], point=point, statut="ECHEC",
                               erreur=erreur))
                continue
            resume["points_traites"] += 1

            m = (res.sensibilite or {}).get("m")
            m_est = (res.sensibilite or {}).get("m_estime")
            validite = (res.sensibilite or {}).get("validite")
            if m is not None and float(m) == 0.0:
                resume["points_m_nul"] += 1
            c1.append(dict(
                jeu=jeu["jeu"], point=point, statut="OK", erreur="",
                m_applique=_f(m), m_estime=_f(m_est),
                validite=("" if validite is None
                          else "valide" if validite else "REJETE"),
                n_journees=int(len(res.df)) if res.df is not None else 0,
                a_delta_brute=("oui" if (res.df is not None
                                         and "Delta_TMm" in res.df.columns)
                               else "non"),
                a_delta_lissee=("oui" if (res.df is not None
                                          and "Delta_TMm_liss" in res.df.columns)
                                else "non")))

            # ---- E / D67 : la source du coefficient saisonnier -------------
            for sous in ((res.fraie or {}).get("sous_indicateurs") or []):
                info = sous.get("m_info") or {}
                e67.append(dict(
                    jeu=jeu["jeu"], point=point,
                    espece=str(sous.get("espece") or ""),
                    source=str(info.get("source") or ""),
                    n=info.get("n"), m_retenu=_f(sous.get("m_saison")),
                    m_regresse=_f(info.get("m")),
                    validite=("" if info.get("validite") is None
                              else "valide" if info.get("validite")
                              else "REJETE"),
                    critere_rejetant=str(info.get("critere_rejetant") or ""),
                    statut_artefact_aujourdhui=(
                        "" if info.get("validite") is None
                        else "valide" if info.get("validite") else "REJETE")))

            # ---- C3 : les colonnes du tableau mensuel, dans l'ordre --------
            ind = res.indicateurs or {}
            t_now = ind.get("table_mensuelle")
            if t_now is None or not len(t_now):
                continue
            for i, col in enumerate(t_now.columns):
                cle = (i, str(col))
                colonnes_vues.setdefault(cle, set()).add(point)
            if any(c in t_now.columns for c in COLS_COMP):
                resume["points_avec_compensation"] += 1

            # ---- C4 : la voie A, calculee a cote ---------------------------
            t_a = table_option_a(res)
            lignes = comparer_tables(point, t_now, t_a)
            c4 += lignes
            for l in lignes:
                resume["cellules_comparees"] += 1
                if l["bouge"] == "oui":
                    if l["ecart"] is None:
                        resume["cellules_apparues_ou_disparues"] += 1
                    else:
                        resume["cellules_deplacees"] += 1
                        if abs(l["ecart"]) > abs(ecart_max):
                            ecart_max = l["ecart"]
                            ecart_max_ou = f"{point} / {l['periode']} / {l['colonne']}"

    # ---------------- ecriture ----------------
    ecrire_csv(OUT / "C1_series.csv",
               ["jeu", "point", "statut", "erreur", "m_applique", "m_estime",
                "validite", "n_journees", "a_delta_brute", "a_delta_lissee"],
               c1, tri=["jeu", "point"])

    for (i, col), points in sorted(colonnes_vues.items()):
        c3.append(dict(
            position=i + 1, colonne=col,
            dans_le_docx=("oui" if i < N_COLS_DOCX else "NON"),
            famille=("compensation (indicateurs.py:88-90)"
                     if col in COLS_COMP else "brute / amplitude"),
            n_points=len(points)))
    ecrire_csv(OUT / "C3_colonnes_tableau_mensuel.csv",
               ["position", "colonne", "dans_le_docx", "famille", "n_points"],
               c3, tri=["position"])

    ecrire_csv(OUT / "C4_valeurs_deplacees.csv",
               ["point", "periode", "colonne", "valeur_actuelle",
                "valeur_voie_A", "ecart", "bouge"],
               c4, tri=["point", "colonne", "periode"])

    ecrire_csv(OUT / "E_d67_m_saisonnier.csv",
               ["jeu", "point", "espece", "source", "n", "m_retenu",
                "m_regresse", "validite", "critere_rejetant",
                "statut_artefact_aujourdhui"],
               e67, tri=["jeu", "point", "espece"])

    lignes_resume = [dict(grandeur=k, valeur=v) for k, v in resume.items()]
    lignes_resume.append(dict(grandeur="ecart_max_voie_A_degC", valeur=ecart_max))
    lignes_resume.append(dict(grandeur="ecart_max_ou", valeur=ecart_max_ou))
    ecrire_csv(OUT / "C4_resume.csv", ["grandeur", "valeur"], lignes_resume,
               tri=["grandeur"])

    # ---------------- console ----------------
    d4 = pd.DataFrame(c4)
    print("\n" + "=" * 74)
    print("C4 — VOIE A : LES COLONNES SUBSISTENT, RECALCULEES")
    print("=" * 74)
    for k, v in resume.items():
        print(f"  {k:<36} : {v}")
    print(f"  {'ecart_max_voie_A_degC':<36} : {ecart_max:+.3f}  ({ecart_max_ou})")
    if len(d4):
        b = d4[d4.bouge == "oui"]
        print(f"\n  par colonne :")
        for col in COLS_COMP:
            s = d4[d4.colonne == col]
            sb = b[b.colonne == col]
            if not len(s):
                continue
            print(f"    {col:<22} {len(sb):>5} / {len(s):<5} cellules deplacees")
        print(f"\n  points dont AU MOINS une cellule bouge : "
              f"{b['point'].nunique()} / {d4['point'].nunique()}")

    print("\n" + "=" * 74)
    print("C3 — LES COLONNES DU TABLEAU MENSUEL, DANS L'ORDRE")
    print("=" * 74)
    for l in sorted(c3, key=lambda r: r["position"]):
        marque = "  [DOCX]" if l["dans_le_docx"] == "oui" else "        "
        print(f"  {l['position']:>2}.{marque} {l['colonne']:<24} "
              f"{l['famille']}  (n_points={l['n_points']})")

    print("\n" + "=" * 74)
    print("E / D67 — LE COEFFICIENT SAISONNIER, SOURCE PAR SOURCE")
    print("=" * 74)
    d6 = pd.DataFrame(e67)
    if len(d6):
        for src, n in d6["source"].value_counts().items():
            print(f"  {src:<24} : {n}")
        repli = d6[d6.source == "estival_repli"]
        print(f"\n  PREDICTION D67 : {len(repli)} ligne(s) de "
              f"06_coefficients.csv passeront d'un statut VIDE a `replie`.")
        for _, r in repli.iterrows():
            print(f"     {r['point']:<32} [{r['espece']}]  n={r['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
