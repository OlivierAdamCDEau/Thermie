"""
mesure_conjonction.py — ÉTAPE 4, TÂCHE B : la conjonction (D26).

MESURE SEULE. Aucun code applicatif n'est modifié. TN et TX sont lus par le
harnais lui-même, comme à l'étape 3.

D26 supprime la marche 2 comme substitution — `TX` n'apporte pas de marge — et
la réintroduit en CONJONCTION : un jour n'est marqué que si l'écart à la
MOYENNE d'air ET l'écart au MAXIMUM d'air dépassent tous deux leur seuil,
chacun relativisé par sa PROPRE dispersion.

    marque = (E_moy − médiane_{p,m}(E_moy)) / MAD*_{p,m}(E_moy) > k
         ET (E_max − médiane_{p,m}(E_max)) / MAD*_{p,m}(E_max) > k

B2 — CE QUE LA CONJONCTION RETIRE, SANS VÉRITÉ TERRAIN
-------------------------------------------------------
Il n'existe aucune étiquette d'exondation sur ce corpus : on ne peut pas dire
si un jour retiré était un faux positif. On rapporte donc ce qui est
OBSERVABLE, et rien de plus :

  - l'excursion du jour, en MAD*, sur chacune des deux grandeurs ;
  - la longueur de l'épisode auquel il appartient — un jour isolé et un jour
    au milieu d'une séquence de six ne se ressemblent pas ;
  - son isolement : nombre de jours marqués dans la fenêtre de ±3 jours ;
  - l'amplitude d'air du jour. C'est le seul indice d'artefact météorologique
    dont on dispose sans étiquette : `thermie_points` établit qu'une faible
    amplitude d'air fabrique des faux positifs (criteres.py, AMPL_AIR_MIN) ;
  - la synchronisation entre points le même jour, quand plusieurs points
    partagent une station d'air.

Aucun de ces indices ne prouve qu'un jour est un faux positif. Ensemble, ils
disent si les jours retirés ressemblent davantage à du bruit isolé qu'à un
régime installé. C'est ce qui est rapporté, et rien de plus.

Sorties :
  out/etape4/conjonction_table.csv        B1
  out/etape4/conjonction_par_point.csv    B1
  out/etape4/conjonction_jours_retires.csv B2 — le profil des jours retires
  out/etape4/conjonction_profils.csv      B2 — la synthese des profils
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f
from mesure_critere_b import PLANCHER_MAD, MIN_JOURS_GROUPE, FACTEUR_MAD, K_VALEURS
from mesure_aveuglement import MOIS
from mesure_marche2 import lire_air_complet
from thermie_debits import io_data

OUT = RACINE / "out" / "etape4"
FENETRE_ISOLEMENT = 3        # jours de part et d'autre


def socle():
    blocs = []
    for j in decouvrir():
        if not j["air"]:
            continue
        air = lire_air_complet(str(RACINE / j["air"]))
        for point_rel in j["points"]:
            pt = nom_point(point_rel)
            daily = io_data.charger_eau(str(RACINE / point_rel),
                                        nom=point_rel.split("/")[-1])
            d = daily.merge(air, on="date", how="left")
            d["date_dt"] = pd.to_datetime(d["date"])
            d["month"] = d["date_dt"].dt.month
            d = d[d["month"].isin(MOIS)].copy()
            if not len(d):
                continue
            d["jeu"], d["point"] = j["jeu"], pt
            d["E_moy"] = d["T_eau_max"] - d["TM"]
            d["E_max"] = d["T_eau_max"] - d["TX"]
            d["ampl_air"] = d["TX"] - d["TN"]
            blocs.append(d[["jeu", "point", "date", "date_dt", "month",
                            "T_eau_max", "TM", "TN", "TX", "ampl_air",
                            "E_moy", "E_max"]])
            print(f"  · {j['jeu']}/{pt} : {len(d)} jours JJAS", flush=True)
    return pd.concat(blocs, ignore_index=True)


def relativiser(d, col):
    g = d.groupby(["point", "month"])[col]
    ref, n = g.transform("median"), g.transform("size")
    mad = (d.assign(_a=(d[col] - ref).abs())
            .groupby(["point", "month"])["_a"].transform("median") * FACTEUR_MAD)
    ok = (mad > PLANCHER_MAD) & (n >= MIN_JOURS_GROUPE) & d[col].notna()
    d[f"{col}_rel"] = np.where(ok, (d[col] - ref) / mad.replace(0, np.nan), np.nan)
    d[f"{col}_diag"] = ok
    return d


def episodes(sub, col):
    """Longueur de l'épisode calendaire auquel chaque jour marqué appartient."""
    s = sub.sort_values("date_dt")
    marque = s[col].to_numpy()
    jours = (s["date_dt"] - s["date_dt"].iloc[0]).dt.days.to_numpy()
    longueur = np.zeros(len(s), dtype=int)
    i = 0
    while i < len(s):
        if not marque[i]:
            i += 1
            continue
        j = i + 1
        while j < len(s) and marque[j] and jours[j] - jours[j - 1] == 1:
            j += 1
        longueur[i:j] = j - i
        i = j
    return pd.Series(longueur, index=s.index)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Construction du socle...", flush=True)
    d = socle()
    d = relativiser(d, "E_moy")
    d = relativiser(d, "E_max")
    dd = d[d["E_moy_diag"] & d["E_max_diag"]].copy()
    print(f"\n{len(d)} points-jours ; {len(dd)} diagnosticables par les deux "
          f"({100*len(dd)/len(d):.1f} %).")

    lignes, retires, profils, par_point = [], [], [], []
    for k in K_VALEURS:
        dd[f"socle_{k}"] = dd["E_moy_rel"] > k          # marche 1, moyenne seule
        dd[f"max_{k}"] = dd["E_max_rel"] > k            # second membre
        dd[f"conj_{k}"] = dd[f"socle_{k}"] & dd[f"max_{k}"]

        n_s = int(dd[f"socle_{k}"].sum())
        n_c = int(dd[f"conj_{k}"].sum())
        lignes.append(dict(
            k=k,
            jours_socle_moyenne_seule=n_s,
            jours_maximum_seul=int(dd[f"max_{k}"].sum()),
            jours_conjonction=n_c,
            jours_retires_par_la_conjonction=n_s - n_c,
            part_retiree_pct=_f(100.0 * (n_s - n_c) / max(n_s, 1)),
            points_socle=int(dd.groupby("point")[f"socle_{k}"].any().sum()),
            points_conjonction=int(dd.groupby("point")[f"conj_{k}"].any().sum()),
            points_perdus_par_la_conjonction=int(
                dd.groupby("point")[f"socle_{k}"].any().sum()
                - dd.groupby("point")[f"conj_{k}"].any().sum())))

        for pt, sub in dd.groupby("point"):
            par_point.append(dict(
                k=k, point=pt, n_jours=int(len(sub)),
                jours_socle=int(sub[f"socle_{k}"].sum()),
                jours_conjonction=int(sub[f"conj_{k}"].sum()),
                jours_retires=int((sub[f"socle_{k}"] & ~sub[f"conj_{k}"]).sum())))

        # ---- B2 : le profil des jours retires, et celui des jours gardes ----
        dd[f"_ep_socle_{k}"] = pd.concat(
            [episodes(s, f"socle_{k}") for _, s in dd.groupby("point")])
        sync = dd[dd[f"socle_{k}"]].groupby(["jeu", "date_dt"]).size()
        dd["_sync"] = dd.set_index(["jeu", "date_dt"]).index.map(sync).fillna(0)

        marq = dd[dd[f"socle_{k}"]].copy()
        marq["retire"] = ~marq[f"conj_{k}"]
        for _, r in marq[marq["retire"]].iterrows():
            retires.append(dict(
                k=k, jeu=r["jeu"], point=r["point"], date=str(r["date"]),
                E_moy_rel=_f(r["E_moy_rel"]), E_max_rel=_f(r["E_max_rel"]),
                E_moy=_f(r["E_moy"]), E_max=_f(r["E_max"]),
                amplitude_air=_f(r["ampl_air"]),
                longueur_episode_socle=int(r[f"_ep_socle_{k}"]),
                points_marques_le_meme_jour=int(r["_sync"])))
        for etiquette, sel in (("retires par la conjonction", marq[marq["retire"]]),
                               ("gardes par la conjonction", marq[~marq["retire"]])):
            if not len(sel):
                continue
            profils.append(dict(
                k=k, groupe=etiquette, n_jours=int(len(sel)),
                excursion_mediane_E_moy=_f(float(sel["E_moy_rel"].median())),
                excursion_mediane_E_max=_f(float(sel["E_max_rel"].median())),
                amplitude_air_mediane=_f(float(sel["ampl_air"].median())),
                part_amplitude_air_sous_6C_pct=_f(
                    100.0 * float((sel["ampl_air"] < 6.0).mean())),
                longueur_episode_mediane=_f(float(sel[f"_ep_socle_{k}"].median())),
                part_jours_isoles_pct=_f(
                    100.0 * float((sel[f"_ep_socle_{k}"] == 1).mean())),
                synchronisation_max=int(sel["_sync"].max()),
                part_synchronisation_5_et_plus_pct=_f(
                    100.0 * float((sel["_sync"] >= 5).mean()))))
        print(f"  k={k} : socle={n_s}, conjonction={n_c}, "
              f"retires={n_s - n_c}", flush=True)

    ecrire_csv(OUT / "conjonction_table.csv",
               ["k", "jours_socle_moyenne_seule", "jours_maximum_seul",
                "jours_conjonction", "jours_retires_par_la_conjonction",
                "part_retiree_pct", "points_socle", "points_conjonction",
                "points_perdus_par_la_conjonction"], lignes, tri=["k"])
    ecrire_csv(OUT / "conjonction_par_point.csv",
               ["k", "point", "n_jours", "jours_socle", "jours_conjonction",
                "jours_retires"], par_point, tri=["k", "point"])
    ecrire_csv(OUT / "conjonction_jours_retires.csv",
               ["k", "jeu", "point", "date", "E_moy_rel", "E_max_rel", "E_moy",
                "E_max", "amplitude_air", "longueur_episode_socle",
                "points_marques_le_meme_jour"], retires,
               tri=["k", "jeu", "point", "date"])
    ecrire_csv(OUT / "conjonction_profils.csv",
               ["k", "groupe", "n_jours", "excursion_mediane_E_moy",
                "excursion_mediane_E_max", "amplitude_air_mediane",
                "part_amplitude_air_sous_6C_pct", "longueur_episode_mediane",
                "part_jours_isoles_pct", "synchronisation_max",
                "part_synchronisation_5_et_plus_pct"], profils,
               tri=["k", "groupe"])

    print("\n=== B2 — profil des jours retires contre ceux gardes ===")
    for l in profils:
        print(f"  k={l['k']:<4} {l['groupe']:<28} n={l['n_jours']:>4} "
              f"| excursion E_moy={l['excursion_mediane_E_moy']:>5.2f} "
              f"| ampl air={l['amplitude_air_mediane']:>5.2f} degC "
              f"(<6 degC : {l['part_amplitude_air_sous_6C_pct']:>5.1f} %) "
              f"| episode median={l['longueur_episode_mediane']:>4.1f} j "
              f"(isoles {l['part_jours_isoles_pct']:>5.1f} %) "
              f"| sync max={l['synchronisation_max']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
