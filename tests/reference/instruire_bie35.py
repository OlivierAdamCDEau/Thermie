"""
instruire_bie35.py — ETAPE 19, tache D (D99) : BIE35-5__NA, instruit HORS CHAINE.

AUCUNE MODIFICATION APPLICATIVE. Ce script n'ecrit rien dans `app/` et ne
contourne aucun controle : il rejoue l'amont de la chaine tel quel, avec les
memes fonctions applicatives et les memes parametres, et S'ARRETE AVANT
l'etape qui echoue.

POURQUOI CE POINT ECHOUE, EXACTEMENT
-------------------------------------
    orchestrator.run -> core.analyse_sensibilite (core.py:522)
    ValueError : « Donnees estivales (juin-sept.) insuffisantes pour la
    regression de sensibilite : 0 jour(s) valide(s) apres controle qualite. »

L'echec est EN AVAL du controle qualite, pas en amont. Les journees marquees
existent donc bel et bien : elles sont produites, puis la chaine s'arrete parce
qu'il ne reste aucun ete a regresser. C'est ce qui rend l'instruction hors
chaine possible — et c'est aussi, en soi, un renseignement sur le point.

CE QUI EST REJOUE, ET CE QUI NE L'EST PAS
------------------------------------------
Rejoue, a l'identique : lecture de l'eau (`marquer_lecture`), lecture de l'air
et calcul des normales, controle qualite (`marquer_qualite`), fusion
(`fusionner_marque`). C'est tout ce dont le temoin a besoin.
Non rejoue : sensibilite, vulnerabilite, fraie, SGVT. Aucune de ces etapes
n'entre dans le temoin, et c'est la premiere qui echoue.

CONSEQUENCE A DECLARER : sans coefficient de sensibilite, ce point n'a NI
temperature normalisee NI seuil franchi calculable. La question « ces journees
coutaient-elles un verdict ? » n'a donc pas de reponse ici — non parce qu'elle
est negative, mais parce que le point ne produit aucun verdict du tout.

Le temoin applique est celui de `temoin_regime.py`, scelle, importe et non
reecrit.
"""
from __future__ import annotations

import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
os.environ.setdefault("THERMIE_CODE", "app")

from _commun import RACINE, decouvrir, ecrire_csv, nom_point, _f      # noqa: E402

import build_reference                                                # noqa: E402
import temoin_regime as TR                                            # noqa: E402
from thermie_debits import core, io_data as io, qc as qcmod           # noqa: E402

OUT = RACINE / "out" / "etape19"
MOIS_ETE = (6, 7, 8, 9)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jeu = [j for j in decouvrir() if j["jeu"] == "jeu_bienne"][0]
    pr = [p for p in jeu["points"] if "BIE35-5" in p]
    if not pr:
        print("BIE35-5__NA introuvable dans le corpus")
        return 2
    pr = pr[0]
    pt = nom_point(pr)
    cfg = build_reference.construire_config(jeu, pr, "application")

    print("=" * 78)
    print(f"TACHE D (D99) — {pt}, INSTRUIT HORS CHAINE")
    print("=" * 78)

    # ---- amont, a l'identique
    daily, sub, marq_lecture = io.marquer_lecture(
        cfg.sources.fichier_eau, col_date=cfg.sources.eau_col_date,
        col_temp=cfg.sources.eau_col_temp, nom=cfg.sources.eau_nom_fichier,
        feuille=cfg.sources.eau_feuille,
        ligne_entete=cfg.sources.eau_ligne_entete,
        retour_sous_quotidien=True)
    df_air = io.charger_air_brut(cfg.sources.fichier_air,
                                 col_date=cfg.sources.air_col_date,
                                 col_temp=cfg.sources.air_col_temp,
                                 station_code=cfg.sources.air_station_code,
                                 station_nom=cfg.sources.air_station_nom)
    ecart, normales, _ = io.calculer_normales_ecarts(
        df_air, fenetre_lissage=cfg.normales_fenetre_lissage,
        min_annees=cfg.normales_min_annees, verbose=False)

    diag = {}
    marques = qcmod.marquer_qualite(daily, df_air, cfg.qc.to_legacy_dict(),
                                    verbose=False, diag=diag)
    rapport = qcmod.rapport_ecartes(marques)
    propre = qcmod.vue_retenue(marques)

    # La fusion, pour disposer de T_air journee par journee.
    df, _ = core.fusionner_marque(
        daily, df_air, ecart, normales, df_debits=None,
        lissage_delta=getattr(cfg, "normalisation_lissage_delta", 7))

    print(f"  journees lues                : {len(daily)}")
    print(f"  journees apres fusion air    : {len(df)}")
    print(f"  journees retenues par le QC  : {len(propre)}")
    print(f"  journees estivales retenues  : "
          f"{int(propre['date'].apply(lambda d: pd.Timestamp(d).month in MOIS_ETE).sum()) if len(propre) else 0}")
    print(f"  detecteur hors d'eau execute : {diag.get('hors_eau_execute')}")
    print(f"  marche 2 disponible          : {diag.get('marche2_disponible')}"
          f"  {diag.get('motif_marche2') or ''}")
    print(f"  marche 1 : {diag.get('n_marche1')} journee(s) ; "
          f"marche 2 : {diag.get('n_marche2')}")

    marquees = {}
    if rapport is not None and len(rapport):
        for _, x in rapport.iterrows():
            if "hors d" in str(x.get("motif", "")):
                marquees[str(x["date"])[:10]] = str(x.get("motif", ""))
    print(f"\n  JOURNEES MARQUEES HORS D'EAU : {len(marquees)}")
    if rapport is not None and len(rapport):
        print("  (tous motifs confondus, le QC en ecarte "
              f"{len(rapport)} :)")
        for mot, n in rapport["motif"].value_counts().items():
            print(f"     {n:>4}  {mot}")

    # ---- LES QUATRE JOURNEES DE L'ETAPE 16 : elles ne sont PAS des journees
    # marquees hors d'eau. Ce sont des journees DESIGNEES PAR LE CRITERE DE
    # COMPLETUDE (correctif 12) — un tout autre controle, qui mesure le plus
    # grand trou infra-journalier. La commande d'etape 19 les appelle
    # « journees marquees » ; le releve montre que ce n'en sont pas, et c'est
    # cette confusion qu'il faut lever avant de repondre.
    completude = io.marquer_completude(sub, daily=daily,
                                       facteur=cfg.qc.completude_facteur,
                                       verbose=False)
    designees = {}
    if completude is not None and len(completude):
        sig = completude[completude["statut"] != "retenue"]
        for _, x in sig.iterrows():
            designees[str(x["date"])[:10]] = (
                f"completude/{x['statut']} — {x['motif']}")
    print(f"\n  JOURNEES DESIGNEES PAR LA COMPLETUDE : {len(designees)}")
    for ds, mo in sorted(designees.items()):
        print(f"     {ds}  {mo}")

    # ---- le temoin scelle, sur la serie brute
    d = df.copy()
    d["ds"] = d["date"].astype(str).str.slice(0, 10)
    dt = pd.to_datetime(d["ds"])
    d["an"], d["doy"] = dt.dt.year, dt.dt.dayofyear
    couverture = (f"{d['ds'].min()} -> {d['ds'].max()}, "
                  f"{d['an'].nunique()} annee(s) civiles")
    print(f"  couverture de la chronique   : {couverture}")

    ete = d[d["month"].isin(MOIS_ETE)] if "month" in d.columns else d.iloc[:0]
    if {"TX", "TN", "T_eau_min"} <= set(d.columns):
        aa = (d["TX"] - d["TN"]).replace(0, np.nan)
        d["R_ampl"] = (d["T_eau_max"] - d["T_eau_min"]) / aa
        re_ = d.loc[ete.index, "R_ampl"].dropna()
        q10 = float(re_.quantile(0.10)) if len(re_) else np.nan
        q90 = float(re_.quantile(0.90)) if len(re_) else np.nan
    else:
        d["R_ampl"] = np.nan
        q10 = q90 = np.nan

    a_instruire = ([(ds, "hors d'eau", mo) for ds, mo in marquees.items()]
                   + [(ds, "completude", mo) for ds, mo in designees.items()])
    lignes = []
    for ds, origine, motif in sorted(a_instruire):
        jr = d[d.ds == ds]
        if not len(jr):
            lignes.append(dict(point=pt, date=ds, origine=origine, motif=motif,
                               verdict="journee absente apres fusion air"))
            continue
        jr = jr.iloc[0]
        ref = TR.reference(d, jr["doy"], jr["an"])
        verdict, exc, dec, n_an, n_j = TR.juger(jr, ref)
        lignes.append(dict(
            point=pt, date=ds, origine=origine, motif=motif, verdict=verdict,
            exc=_f(exc), dec=_f(dec), n_annees=n_an, n_jours_ref=n_j,
            T_eau_moy=_f(jr.get("T_eau_moy")), T_eau_max=_f(jr.get("T_eau_max")),
            T_eau_min=_f(jr.get("T_eau_min")), T_air=_f(jr.get("T_air")),
            R_ampl=_f(jr.get("R_ampl")),
            morphologie=TR.morphologie(jr.get("R_ampl"), q10, q90),
            seuil_franchi="INCALCULABLE — pas de coefficient de sensibilite "
                          "sur ce point, donc pas de temperature normalisee"))

    ecrire_csv(OUT / "D_bie35.csv",
               ["point", "date", "origine", "motif", "verdict", "exc", "dec",
                "n_annees",
                "n_jours_ref", "T_eau_moy", "T_eau_max", "T_eau_min", "T_air",
                "R_ampl", "morphologie", "seuil_franchi"],
               lignes, tri=["date"])

    print("\n  LE TEMOIN SCELLE, JOURNEE PAR JOURNEE")
    print("  " + "-" * 74)
    for r in lignes:
        print(f"  {r['date']}  [{r.get('origine')}]  {r.get('verdict'):<16} "
              f"exc={r.get('exc')}  dec={r.get('dec')}  "
              f"({r.get('n_annees')} annee(s), {r.get('n_jours_ref')} j. ref)")
        print(f"     T_eau {r.get('T_eau_moy')}  T_air {r.get('T_air')}  "
              f"R_ampl {r.get('R_ampl')}  [{r.get('morphologie')}]")
    n_art = sum(1 for r in lignes if r.get("verdict") == TR.ARTEFACT)
    n_ind = sum(1 for r in lignes if r.get("verdict") == TR.INDETERMINABLE)
    print("\n  " + "-" * 74)
    print(f"  artefact {n_art} | compatible "
          f"{len(lignes) - n_art - n_ind} | indeterminable {n_ind}")
    print("\n  CE QUI MANQUE, ET QUI NE PEUT PAS ETRE SUPPLEE :")
    print("     ce point ne produit AUCUN verdict — pas de coefficient de")
    print("     sensibilite, donc pas de temperature normalisee, donc pas de")
    print("     seuil piscicole calculable. Le marquage n'y retire aucune")
    print("     alerte, puisqu'il n'y a aucune alerte a retirer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
