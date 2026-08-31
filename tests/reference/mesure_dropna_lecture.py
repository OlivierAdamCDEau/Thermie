"""
mesure_dropna_lecture.py — ETAPE 13, POSE 4 (4.1) : ce que io_data.py:98
supprime, mesure AVANT correction.

    df_w = df_w.dropna(subset=["date", "T_eau"])          io_data.py:98

Cette ligne ecarte des mesures INFRA-JOURNALIERES avant l'agregation, sans
compte, sans date, sans cause. C'est la derniere suppression silencieuse du
perimetre (D60), et le harnais la consigne comme NON_RECUPERABLE depuis
l'etape 1.

CETTE MESURE NE SE REFAIT PAS APRES
------------------------------------
Une fois la cause tracee par l'application, la ligne ne supprimera plus rien
en silence — et l'etat d'avant deviendra inobservable. C'est la methode de
l'etape 6 : mesurer le defaut pendant qu'il existe encore.

COMMENT ELLE EST OBTENUE, ET COMMENT ELLE SE VERIFIE
-----------------------------------------------------
`charger_eau` ne retourne rien de ce qui precede la ligne 98 : il faut donc
rejouer les lignes 46-97 pour voir la trame AVANT le filtre. Le rejeu appelle
les fonctions de l'application elles-memes — `sniff.lire_brut`,
`sniff.deviner_colonnes`, `io_data._parse_dates_sonde` — et reproduit a la
lettre la regle de choix des colonnes.

Une replication non verifiee ne vaut rien (etapes 8 et 9). Chaque point est
donc CONTROLE : la table journaliere reconstruite ici est confrontee, ligne a
ligne et colonne a colonne, a celle que `charger_eau` retourne reellement. La
colonne `replication` porte le verdict, et un point dont la replication
echoue voit ses comptes marques NON FIABLES plutot que rapportes.

CE QUE LA MESURE DOIT ETABLIR (4.1)
------------------------------------
  - combien de mesures sont ecartees, par jeu et par point ;
  - quelle part du fichier lu cela represente ;
  - la cause, distinguee : date illisible / temperature illisible / les deux ;
  - si les pertes se concentrent sur des periodes particulieres — plus longue
    serie continue de journees touchees, mois et annees concernes, et
    journees ENTIEREMENT perdues.

SORTIES
  out/etape13/P4_dropna_par_point.csv
  out/etape13/P4_dropna_par_periode.csv
  out/etape13/P4_journees_entierement_perdues.csv
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("THERMIE_CODE", "app")

from _commun import (CODE, RACINE, RACINE_CODE, decouvrir, ecrire_csv,  # noqa: E402
                     nom_point, _f)
from thermie_debits import io_data, sniff                              # noqa: E402

OUT = RACINE / "out" / "etape13"


def colonnes_retenues(df_w):
    """La regle de io_data.charger_eau:52-68, reproduite a la lettre."""
    _dev_date, _dev_temp = sniff.deviner_colonnes(df_w)
    col_temp = _dev_temp
    cand = [c for c in df_w.columns
            if any(m in c.lower() for m in
                   ["date", "heure", "time", "timestamp", "horodat"])
            or any(m in c.lower() for m in ["dtana", "dtprel"])]
    col_date = None
    for dc in cand:
        nn = df_w[dc].dropna()
        samp = str(nn.iloc[0]) if len(nn) else ""
        if len(samp) > 8 and not dc.lower().startswith(("heure", "hr")):
            col_date = dc
            break
    if col_date is None:
        col_date = _dev_date or (cand[0] if cand else None)
    return col_date, col_temp


def trame_avant_filtre(chemin_rel: str):
    """
    La trame telle qu'elle est juste AVANT `io_data.py:98`, avec ses colonnes
    `datetime`, `T_eau` et `date`. Reproduit io_data.charger_eau:46-97.
    """
    src = str(RACINE / chemin_rel)
    df_w, _meta = sniff.lire_brut(src, nom=chemin_rel.split("/")[-1])
    col_date, col_temp = colonnes_retenues(df_w)
    if col_date is None or col_temp is None:
        return None, None, None

    dt = io_data._parse_dates_sonde(df_w[col_date])
    col_h = next((c for c in df_w.columns
                  if (c.lower().startswith("heure")
                      or c.lower().startswith("hrana")
                      or c.lower().startswith("hrprel"))
                  and c != col_date), None)
    if col_h is not None and dt.notna().any() and (dt.dt.hour == 0).all():
        def _td(h):
            try:
                h = str(h).strip()
                return pd.Timedelta(h) if ":" in h else pd.Timedelta(0)
            except Exception:
                return pd.Timedelta(0)
        dt = dt + df_w[col_h].apply(_td)

    df_w = df_w.copy()
    df_w["datetime"] = dt
    df_w["T_eau"] = pd.to_numeric(
        df_w[col_temp].astype(str).str.replace(",", ".").str.replace(" ", ""),
        errors="coerce")
    df_w["date"] = df_w["datetime"].dt.date
    return df_w, col_date, col_temp


def journalier(df_apres):
    """L'agregation de io_data.charger_eau:100-104."""
    return df_apres.groupby("date").agg(
        T_eau_moy=("T_eau", "mean"), T_eau_max=("T_eau", "max"),
        T_eau_min=("T_eau", "min"), n_mesures=("T_eau", "size")).reset_index()


def plus_longue_serie(jours):
    """Plus longue suite de journees calendairement contigues."""
    if not jours:
        return 0, None, None
    j = sorted(set(jours))
    best, cur, deb, best_deb, best_fin = 1, 1, j[0], j[0], j[0]
    for a, b in zip(j, j[1:]):
        if (pd.Timestamp(b) - pd.Timestamp(a)).days == 1:
            cur += 1
        else:
            if cur > best:
                best, best_deb, best_fin = cur, deb, a
            cur, deb = 1, b
    if cur > best:
        best, best_deb, best_fin = cur, deb, j[-1]
    return best, best_deb, best_fin


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Code execute : {CODE}  "
          f"({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print("=" * 74)
    print("POSE 4 / 4.1 — CE QUE io_data.py:98 SUPPRIME, AVANT CORRECTION")
    print("=" * 74)

    par_point, par_periode, entierement = [], [], []
    tot_lues = tot_perdues = 0
    n_repl_ok = n_repl_ko = 0

    for jeu in decouvrir():
        for point_rel in jeu["points"]:
            pt = nom_point(point_rel)
            try:
                df_w, col_date, col_temp = trame_avant_filtre(point_rel)
            except Exception as exc:
                par_point.append(dict(
                    jeu=jeu["jeu"], point=pt, replication="LECTURE IMPOSSIBLE",
                    erreur=f"{type(exc).__name__}: {exc}"))
                n_repl_ko += 1
                print(f"  · {jeu['jeu']}/{pt} : LECTURE IMPOSSIBLE")
                continue
            if df_w is None:
                par_point.append(dict(jeu=jeu["jeu"], point=pt,
                                      replication="COLONNES NON DETECTEES",
                                      erreur=""))
                n_repl_ko += 1
                continue

            n_lues = int(len(df_w))
            date_ko = df_w["date"].isna()
            temp_ko = df_w["T_eau"].isna()
            n_date_seule = int((date_ko & ~temp_ko).sum())
            n_temp_seule = int((~date_ko & temp_ko).sum())
            n_les_deux = int((date_ko & temp_ko).sum())
            n_perdues = int((date_ko | temp_ko).sum())

            df_apres = df_w[~(date_ko | temp_ko)]
            daily_recons = journalier(df_apres)

            # --- CONTROLE DE REPLICATION : la chaine elle-meme fait-elle pareil ?
            try:
                daily_vrai = io_data.charger_eau(str(RACINE / point_rel),
                                                 nom=point_rel.split("/")[-1])
                a = daily_recons.sort_values("date").reset_index(drop=True)
                b = daily_vrai.sort_values("date").reset_index(drop=True)
                identique = (list(a.columns) == list(b.columns)
                             and len(a) == len(b)
                             and bool(np.all([
                                 a[c].astype(str).equals(b[c].astype(str))
                                 for c in a.columns])))
                repl = "identique" if identique else "DIVERGENTE"
            except Exception as exc:
                repl = f"CONTROLE IMPOSSIBLE ({type(exc).__name__})"
            n_repl_ok += repl == "identique"
            n_repl_ko += repl != "identique"

            # --- ou les pertes tombent-elles ?
            perdues = df_w[date_ko | temp_ko]
            jours_perdus = sorted({d for d in perdues["date"].dropna().tolist()})
            gardees = set(df_apres["date"].tolist())
            jours_entierement = [d for d in jours_perdus if d not in gardees]
            n_serie, serie_deb, serie_fin = plus_longue_serie(jours_entierement)

            tot_lues += n_lues
            tot_perdues += n_perdues
            par_point.append(dict(
                jeu=jeu["jeu"], point=pt, replication=repl, erreur="",
                colonne_date=str(col_date), colonne_temperature=str(col_temp),
                mesures_lues=n_lues, mesures_perdues=n_perdues,
                part_pct=_f(100.0 * n_perdues / n_lues) if n_lues else None,
                cause_date_seule=n_date_seule,
                cause_temperature_seule=n_temp_seule,
                cause_les_deux=n_les_deux,
                journees_touchees=len(jours_perdus),
                journees_entierement_perdues=len(jours_entierement),
                plus_longue_serie_continue=n_serie if jours_entierement else 0,
                serie_debut=str(serie_deb) if jours_entierement else "",
                serie_fin=str(serie_fin) if jours_entierement else "",
                journees_retenues=int(len(daily_recons))))

            for d in jours_entierement:
                sub = perdues[perdues["date"] == d]
                entierement.append(dict(
                    jeu=jeu["jeu"], point=pt, date=str(d),
                    mesures=int(len(sub)),
                    cause_date=int(sub["date"].isna().sum()),
                    cause_temperature=int(sub["T_eau"].isna().sum())))

            if n_perdues:
                p = perdues.copy()
                p["annee"] = pd.to_datetime(p["date"], errors="coerce").dt.year
                p["mois"] = pd.to_datetime(p["date"], errors="coerce").dt.month
                for (an, mo), g in p.groupby(["annee", "mois"], dropna=False):
                    par_periode.append(dict(
                        jeu=jeu["jeu"], point=pt,
                        annee=int(an) if pd.notna(an) else -1,
                        mois=int(mo) if pd.notna(mo) else -1,
                        mesures_perdues=int(len(g))))
            print(f"  · {jeu['jeu']}/{pt} : {n_perdues}/{n_lues} perdue(s) "
                  f"[{repl}]", flush=True)

    ecrire_csv(OUT / "P4_dropna_par_point.csv",
               ["jeu", "point", "replication", "erreur", "colonne_date",
                "colonne_temperature", "mesures_lues", "mesures_perdues",
                "part_pct", "cause_date_seule", "cause_temperature_seule",
                "cause_les_deux", "journees_touchees",
                "journees_entierement_perdues", "plus_longue_serie_continue",
                "serie_debut", "serie_fin", "journees_retenues"],
               par_point, tri=["jeu", "point"])
    ecrire_csv(OUT / "P4_dropna_par_periode.csv",
               ["jeu", "point", "annee", "mois", "mesures_perdues"],
               par_periode, tri=["jeu", "point", "annee", "mois"])
    ecrire_csv(OUT / "P4_journees_entierement_perdues.csv",
               ["jeu", "point", "date", "mesures", "cause_date",
                "cause_temperature"],
               entierement, tri=["jeu", "point", "date"])

    d = pd.DataFrame([l for l in par_point if l.get("mesures_lues")])
    print("\n" + "=" * 74)
    print("CE QUE io_data.py:98 SUPPRIME")
    print("=" * 74)
    print(f"  replication controlee identique : {n_repl_ok} point(s)")
    print(f"  replication NON identique       : {n_repl_ko} point(s)")
    print(f"  mesures lues (total corpus)     : {tot_lues}")
    print(f"  mesures supprimees              : {tot_perdues}"
          f"  ({100.0 * tot_perdues / tot_lues:.4f} %)" if tot_lues else "")
    if len(d):
        touches = d[d.mesures_perdues > 0]
        print(f"  points touches                  : {len(touches)} / {len(d)}")
        print(f"\n  par cause :")
        print(f"    date illisible seule          : "
              f"{int(d.cause_date_seule.sum())}")
        print(f"    temperature illisible seule   : "
              f"{int(d.cause_temperature_seule.sum())}")
        print(f"    les deux                      : "
              f"{int(d.cause_les_deux.sum())}")
        print(f"\n  journees ENTIEREMENT perdues    : "
              f"{int(d.journees_entierement_perdues.sum())}")
        if len(touches):
            print(f"\n  les points touches, du plus atteint au moins :")
            for _, r in touches.sort_values("mesures_perdues",
                                            ascending=False).iterrows():
                print(f"    {r['point']:<34} {r['mesures_perdues']:>6} / "
                      f"{r['mesures_lues']:<7} ({r['part_pct']:.3f} %)  "
                      f"journees entieres perdues : "
                      f"{r['journees_entierement_perdues']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
