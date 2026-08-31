"""
build_reference.py — ÉTAPE 1, TÂCHE B : construction de la référence figée.

Pour chaque jeu de data/, exécute la chaîne de ref/v4_5/ (D3) point par point
et fige dans tests/reference/<jeu>/ :

  00_format_detecte.json     ce que la détection a conclu
  01_colonnes_retenues.json  mapping colonne source -> rôle
  02_effectifs.csv           lignes lues / retenues, par point et par an
  03_journees_ecartees.csv   par point et par jour, la journée écartée + motif
  04_normales.csv            normales journalières
  05_anomalies.csv           anomalie brute et anomalie lissée
  06_coefficients.csv        m, R², n, p et diagnostics déjà produits
  07_t_norm.csv              températures normalisées, étiquetées par la
                             fonction qui les a produites
  08_scores.csv              témoin hors périmètre (D4)
  99_log.txt                 sortie console intégrale

puis tests/reference/MANIFEST.sha256, et — D70 — un SOURCE_CODE.txt à la
racine du dossier construit, qui dit quelle source de code (`ref` ou `app`),
quel chemin de paramètres et quelle étape ont produit ce dossier. Il n'entre
ni dans le manifeste ni dans le diff : il documente la référence, il n'en
fait pas partie.

D7 : si un point fait échouer V4.5, l'échec EST la référence. La trace complète
et le message d'erreur sont figés dans 99_log.txt et dans les artefacts, et
l'exécution se poursuit sur les autres points. Aucun contournement.

USAGE
    python tests/reference/build_reference.py            # tout le corpus
    python tests/reference/build_reference.py jeu_02     # un jeu
    python tests/reference/build_reference.py --sortie X # ailleurs (controle)
    python tests/reference/build_reference.py --est-une-reference
        D75 : DECLARE que la sortie est une reference et ecrit son
        MANIFEST.sha256. Sans ce drapeau, aucun manifeste n'est ecrit — et le
        script REFUSE de construire dans un dossier qui en porte deja un.
"""
from __future__ import annotations

import argparse
import contextlib
import io as _io
import re
import sys
import traceback
from pathlib import Path

import pandas as pd

from _commun import (RACINE, REF_V45, CODE, RACINE_CODE, Journal, decouvrir,
                     ecrire_csv, ecrire_json, ecrire_manifeste, ecrire_texte,
                     nom_point, ICI, _f, _jsonable, _relatif)

from parametres import ATTENDU_CLASSEUR, jeu_de_parametres

from thermie_debits.config import AnalyseConfig, SourcesConfig, QCConfig
from thermie_debits import orchestrator, io_data, sniff, core


# ============================================================
# Paramètres de rejeu — DEUX CHEMINS (D14 révisée)
# ============================================================
# "application" : ce que construit l'application Streamlit en service. C'est
#                 la référence QUI FAIT FOI.
# "cli"         : ce que construit run_cli.py + QCConfig() par défaut. Référence
#                 SECONDE, conservée dans tests/reference_cli/ parce qu'elle
#                 documente le comportement détecteur allumé.
# Le détail champ par champ, avec provenance, est dans parametres.py.
CHEMIN_DEFAUT = "application"


# ============================================================
# D70 — la provenance d'une reference s'ecrit DANS la reference
# ============================================================
# Une reference ne dit rien par elle-meme du code qui l'a produite. Deux
# invocations qui ne different que par THERMIE_CODE produisent des diffs
# opposes, et rien ne les distinguait : un diff massif du a une invocation
# erronee a ete pris pour une corruption du depot. Une reference non etiquetee
# ne reference rien.
#
# `SOURCE_CODE.txt` est ecrit a la racine du dossier construit. Il ne compte
# NI dans le manifeste NI dans le diff : `est_artefact` exige `<NN>_....` dans
# un sous-dossier de jeu, ce fichier est a la racine et ne porte pas de
# prefixe numerique. Il documente la reference sans en faire partie.
NOM_SOURCE_CODE = "SOURCE_CODE.txt"

# ETAPE a laquelle une reference construite MAINTENANT serait etablie. A
# mettre a jour a chaque etape. Sur un rejeu jetable, ce nombre ne sert qu'a
# rendre le rejeu lisible ; sur une reference, il dit quand elle a ete figee.
ETAPE_COURANTE = 16


def ecrire_source_code(sortie: Path, chemin: str, etape: int,
                       etape_manifeste=None) -> Path:
    """
    Ecrit `sortie/SOURCE_CODE.txt` — D70. LF, deterministe, sans horodatage.

    D75 — `etape_manifeste` dit a quelle etape le MANIFEST.sha256 du dossier a
    ete ecrit. Ce n'est pas la meme chose que l'etape des artefacts : le
    manifeste de `tests/reference_cli/` a ete ecrit a l'etape 13 sur des
    artefacts etablis a l'etape 6, parce qu'aucun chemin de code ne pouvait
    l'ecrire avant. Confondre les deux dates ferait croire a un rebasage.
    """
    lignes = [
        "# SOURCE_CODE.txt — D70 : la provenance de cette reference.",
        "#",
        "# Ecrit par tests/reference/build_reference.py au moment ou le",
        "# dossier est construit. Lu par tests/reference/check_reference.py,",
        "# qui REFUSE de comparer un rejeu a cette reference si la source de",
        "# code demandee n'est pas celle qui l'a produite, ou si le chemin de",
        "# parametres demande n'est pas le sien.",
        "#",
        "# POURQUOI CE FICHIER EXISTE",
        "# Une reference ne dit rien par elle-meme du code qui l'a produite.",
        "# Deux invocations qui ne different que par THERMIE_CODE produisent",
        "# des diffs opposes, et rien ne les distinguait : un diff massif du a",
        "# une invocation erronee a ete pris pour une corruption du depot.",
        "#",
        "# Format : CLE=valeur, une par ligne. Lignes vides et lignes",
        "# commencant par # ignorees.",
        "",
        f"SOURCE_CODE={CODE}",
        f"ETAPE={int(etape)}",
        f"CHEMIN_DE_PARAMETRES={chemin}",
    ]
    if etape_manifeste is not None:
        lignes += [
            "",
            "# D75 — etape a laquelle le MANIFEST.sha256 de ce dossier a ete",
            "# ecrit. Distincte de ETAPE, qui date les ARTEFACTS : le",
            "# manifeste peut etre ecrit plus tard sans qu'aucun artefact ne",
            "# soit reconstruit.",
            f"MANIFESTE_ECRIT_A_L_ETAPE={int(etape_manifeste)}",
        ]
    lignes += [
        "",
    ]
    cible = sortie / NOM_SOURCE_CODE
    cible.parent.mkdir(parents=True, exist_ok=True)
    ecrire_texte(cible, "\n".join(lignes))
    return cible


def lire_source_code(dossier: Path):
    """
    Lit `dossier/SOURCE_CODE.txt` — D70. Retourne un dict, ou None si absent.

    Le lecteur vit ici, a cote de l'ecrivain : un format decrit a deux
    endroits finit par diverger.
    """
    cible = Path(dossier) / NOM_SOURCE_CODE
    if not cible.is_file():
        return None
    champs = {}
    for ligne in cible.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, val = ligne.partition("=")
        champs[cle.strip()] = val.strip()
    return champs


def _valeurs(table):
    """{champ: (valeur, provenance, justification)} -> {champ: valeur}."""
    return {k: v[0] for k, v in table.items()}


def construire_config(jeu: dict, point_rel: str,
                     chemin: str = CHEMIN_DEFAUT) -> AnalyseConfig:
    """Configuration du rejeu, selon le chemin de paramètres retenu."""
    par = jeu_de_parametres(chemin, jeu["jeu"])
    eau = str(RACINE / point_rel)
    air = str(RACINE / jeu["air"]) if jeu["air"] else None
    debit = str(RACINE / jeu["debit"]) if jeu["debit"] else None

    qc = QCConfig(**_valeurs(par["qc"]))
    analyse = _valeurs(par["analyse"])
    # Le harnais n'ecrit jamais par l'application, quel que soit le chemin.
    analyse["output_dir"] = None

    return AnalyseConfig(
        sources=SourcesConfig(
            fichier_eau=eau, fichier_air=air, fichier_debit=debit,
            eau_nom_fichier=Path(point_rel).name,
            air_nom_fichier=Path(jeu["air"]).name if jeu["air"] else "",
            nom_cours_eau=nom_point(point_rel),
            localisation_sonde="", nom_station_debit="", nom_station_meteo=""),
        qc=qc,
        contexte_piscicole=par["contexte_piscicole"][0],
        espece_repere=par["espece_repere"][0],
        mode="thermie_debits" if debit else "thermie_seule",
        **analyse)


def art_10(jeu: dict, chemin: str) -> dict:
    """
    10_parametres.json — tous les paramètres appliqués, chacun avec sa
    PROVENANCE : "code" (lu dans ref/v4_5), "classeur" (lu dans le livrable
    présent dans tests/reference/<jeu>/), "defaut" (choisi faute de trace).
    """
    par = jeu_de_parametres(chemin, jeu["jeu"])
    def _d(table):
        return {k: dict(valeur=v[0], provenance=v[1], justification=v[2])
                for k, v in table.items()}
    return dict(
        jeu=jeu["jeu"],
        chemin_de_parametres=chemin,
        ce_que_ce_chemin_represente=(
            "l'application Streamlit en service, telle qu'elle construit son "
            "AnalyseConfig quand l'operateur ne touche a aucun reglage avance "
            "(D14 revisee : reference qui fait foi)"
            if chemin == "application" else
            "run_cli.py + QCConfig() par defaut (reference SECONDE, "
            "detecteur hors d'eau a 4 C avec exclusion de saison)"),
        contexte_piscicole=dict(valeur=par["contexte_piscicole"][0],
                                provenance=par["contexte_piscicole"][1],
                                justification=par["contexte_piscicole"][2]),
        espece_repere=dict(valeur=par["espece_repere"][0],
                           provenance=par["espece_repere"][1],
                           justification=par["espece_repere"][2]),
        mode=("thermie_debits" if jeu["debit"] else "thermie_seule"),
        mode_provenance=("code" if jeu["debit"] else "defaut"),
        mode_justification=(
            "app.py:95-99, radio index=1 ; AnalyseConfig.avec_debits "
            "(config.py) exige en outre un fichier de debit"
            if jeu["debit"] else
            "aucun fichier de debit dans le jeu : avec_debits est faux quel "
            "que soit le mode (config.py, propriete avec_debits)"),
        qc=_d(par["qc"]),
        analyse=_d(par["analyse"]),
        attendu_classeur=ATTENDU_CLASSEUR.get(jeu["jeu"]),
        attendu_classeur_note=(
            "valeurs lues dans Donnees_Thermie_*.xlsx, feuilles 01_Donnees_QC "
            "et 02_Thermie_SGVT — critere d'acceptation de l'etape 2"
            if jeu["jeu"] in ATTENDU_CLASSEUR else
            "aucun classeur pour ce jeu : aucune valeur attendue, donc aucune "
            "verification possible contre un livrable"))


# ============================================================
# Extraction des artefacts depuis un Resultats
# ============================================================
def art_00(journal: Journal, jeu: dict, point: str) -> dict:
    return dict(
        point=point,
        source_eau=_relatif(str(RACINE / [p for p in jeu["points"]
                                          if nom_point(p) == point][0])),
        source_air=jeu["air"], source_debit=jeu["debit"],
        mode="thermie_debits" if jeu["debit"] else "thermie_seule",
        appels_lire_brut=journal.formats,
        chargement_eau=journal.eau,
        chargement_air=journal.air,
        format_meteo_france_detecte=journal_mf(jeu),
        stations_air_detectees=journal_stations(jeu))


def journal_mf(jeu: dict):
    """Ce que io_data._colonnes_meteo_france conclut sur le fichier d'air."""
    if not jeu["air"]:
        return None
    return _jsonable(io_data._colonnes_meteo_france(str(RACINE / jeu["air"])))


def journal_stations(jeu: dict):
    """Ce que io_data.stations_air conclut ([] = mono-station ou hors format)."""
    if not jeu["air"]:
        return None
    return _jsonable(io_data.stations_air(str(RACINE / jeu["air"])))


def art_01(journal: Journal, res) -> dict:
    """
    Mapping colonne source -> rôle, tel que la chaîne l'a effectivement retenu.

    Ce que le harnais peut observer sans toucher app/ : les propositions de
    sniff.deviner_colonnes (journalisées à chaque appel) et les colonnes
    présentes en sortie. La colonne finalement retenue par charger_eau n'est
    PAS retournée par V4.5 : elle est reconstruite ici en rejouant la règle de
    io_data.charger_eau:55-68 sur la même lecture brute, ce qui est une
    déduction du harnais et non une sortie de l'application. Le champ
    `origine` le dit pour chaque valeur.
    """
    return dict(
        propositions_deviner_colonnes=journal.colonnes,
        eau=_mapping_eau(journal),
        air=_mapping_air(journal, res),
        debit=dict(
            origine="parseur dedie io_data.charger_debit:161-176 — aucune "
                    "detection de colonne : la 1re position est la date, la "
                    "2e la valeur, par construction",
            colonne_date="position 0", colonne_valeur="position 1")
        if getattr(res, "df_q_all", None) is not None else None,
        colonnes_finales_df=[str(c) for c in res.df.columns]
        if getattr(res, "df", None) is not None else None)


def _mapping_eau(journal: Journal):
    if not journal.eau:
        return None
    appel = journal.eau[0]
    src = RACINE / appel["source"]
    df_w, meta = _lire_brut_original(str(src), nom=src.name)
    dev_date, dev_temp = _deviner_original(df_w)
    cand = [c for c in df_w.columns
            if any(m in str(c).lower() for m in
                   ["date", "heure", "time", "timestamp", "horodat"])
            or any(m in str(c).lower() for m in ["dtana", "dtprel"])]
    col_date = None
    for dc in cand:
        nn = df_w[dc].dropna()
        samp = str(nn.iloc[0]) if len(nn) else ""
        if len(samp) > 8 and not str(dc).lower().startswith(("heure", "hr")):
            col_date = dc
            break
    if col_date is None:
        col_date = dev_date or (cand[0] if cand else None)
    col_h = next((c for c in df_w.columns
                  if (str(c).lower().startswith("heure")
                      or str(c).lower().startswith("hrana")
                      or str(c).lower().startswith("hrprel"))
                  and c != col_date), None)
    dt = io_data._parse_dates_sonde(df_w[col_date]) if col_date is not None else None
    heure_utilisee = bool(col_h is not None and dt is not None
                          and dt.notna().any() and (dt.dt.hour == 0).all())
    return dict(
        origine="rejeu de la regle io_data.charger_eau:55-90 par le harnais "
                "(V4.5 ne retourne pas ce mapping)",
        meta_lecture=_jsonable(meta),
        colonnes_disponibles=[str(c) for c in df_w.columns],
        candidates_date=[str(c) for c in cand],
        colonne_date="" if col_date is None else str(col_date),
        colonne_temperature="" if dev_temp is None else str(dev_temp),
        colonne_heure_separee_detectee="" if col_h is None else str(col_h),
        colonne_heure_separee_utilisee=heure_utilisee,
        motif_heure_non_utilisee=(
            "" if col_h is None or heure_utilisee
            else "la colonne de date porte deja une heure non nulle "
                 "(condition io_data.charger_eau:83)"),
        colonnes_ignorees=[str(c) for c in df_w.columns
                           if c not in {col_date, dev_temp, col_h}],
        n_lignes_brutes=int(len(df_w)))


def _mapping_air(journal: Journal, res):
    if not journal.air:
        return None
    appel = journal.air[0]
    src = RACINE / appel["source"]
    mf = io_data._colonnes_meteo_france(str(src))
    if mf is not None:
        return dict(
            origine="chemin Meteo-France io_data.charger_air_brut:415-466",
            colonne_date="AAAAMMJJ", colonne_temperature="TM",
            colonne_pluie="RR (si presente)",
            colonnes_lues="usecols = NUM_POSTE, NOM_USUEL, AAAAMMJJ, TM, RR "
                          "(io_data.py:432)",
            TN_TX_lus=False,
            motif_TN_TX="TN et TX ne figurent pas dans usecols : ils ne sont "
                        "jamais lus, donc jamais transmis (io_data.py:432)",
            station_retenue=_jsonable(res.diag_air_station),
            colonnes_retournees=appel["colonnes_retournees"])
    df, meta = _lire_brut_original(str(src))
    col_date = next((c for c in df.columns if str(c).upper() == "AAAAMMJJ"), None)
    col_temp = next((c for c in df.columns if str(c).upper() == "TM"), None)
    return dict(
        origine="chemin generique io_data.charger_air_brut:468-492",
        meta_lecture=_jsonable(meta),
        colonnes_disponibles=[str(c) for c in df.columns],
        colonne_date="" if col_date is None else str(col_date),
        colonne_temperature="" if col_temp is None else str(col_temp),
        colonne_pluie="RR" if any(str(c).upper() == "RR" for c in df.columns) else "",
        TN_TX_presents_dans_le_fichier=bool(
            any(str(c).upper() == "TN" for c in df.columns)
            and any(str(c).upper() == "TX" for c in df.columns)),
        TN_TX_lus=False,
        motif_TN_TX="charger_air_brut ne construit que date, T_air et RR "
                    "(io_data.py:484-491) : TN et TX sont abandonnes a la lecture",
        colonnes_retournees=appel["colonnes_retournees"])


def _non_diag_par_date(res):
    """
    Les journees non diagnosticables de la fusion, date -> liste de motifs.

    Vide tant que l'application ne produit pas de table de marquage — c'etait
    le cas avant le correctif 5, et le harnais deduisait alors ce qu'il
    pouvait. Le dictionnaire vide fait retomber le harnais sur cette
    deduction, sans branche supplementaire.
    """
    m = getattr(res, "marques_fusion", None)
    if m is None or not len(m):
        return {}
    nd = m[m["statut"] == "non_diagnosticable"]
    return {str(r["date"]): list(r["motifs"]) for _, r in nd.iterrows()}


def _compte_motifs(motifs_par_date, dates, fragment):
    """Combien de ces dates portent un motif contenant `fragment`."""
    return sum(1 for d in dates
               if any(fragment in x for x in motifs_par_date.get(d, [])))


def art_02(res, point: str):
    """Lignes lues / retenues, par point et par an."""
    lignes = []
    brut = res.daily_eau_brut
    sub = res.sub_eau
    df = res.df
    ecartees = res.rapport_qc
    non_diag = _non_diag_par_date(res)
    an = lambda s: pd.to_datetime(pd.Series(s)).dt.year

    annees = set()
    for s in (brut["date"] if brut is not None and len(brut) else [],
              df["date"] if df is not None and len(df) else []):
        annees |= set(an(s).tolist()) if len(s) else set()
    for a in sorted(annees):
        n_infra = int((an(sub["date"]) == a).sum()) if sub is not None and len(sub) else 0
        n_brut = int((an(brut["date"]) == a).sum()) if brut is not None and len(brut) else 0
        n_qc = (int((an(ecartees["date"]) == a).sum())
                if ecartees is not None and len(ecartees) else 0)
        n_final = int((an(df["date"]) == a).sum()) if df is not None and len(df) else 0

        # CORRECTIF 5 / D45 — ce que la fusion n'a pas pu exploiter, nomme.
        # Les journees sans air ne sont PAS dans res.df ; celles qui manquent
        # de densite y sont, avec un Tmh vide. Seules les premieres doivent
        # donc etre retranchees du compte des pertes.
        d_an = [d for d in non_diag
                if pd.to_datetime(d).year == a]
        n_air = _compte_motifs(non_diag, d_an, "air absente")
        n_dens = _compte_motifs(non_diag, d_an, "densité calendaire")
        lignes.append(dict(
            point=point, annee=int(a),
            mesures_infra_journalieres=n_infra,
            journees_lues=n_brut,
            journees_ecartees_qc=n_qc,
            journees_retenues_apres_fusion=n_final,
            journees_non_diag_air_absent=n_air,
            journees_non_diag_densite=n_dens,
            mesures_ecartees_a_la_lecture=_n_ecartees_lecture(res, a),
            journees_signalees_completude=_n_signalees_completude(res, a),
            journees_perdues_hors_qc=n_brut - n_qc - n_final - n_air))
    lignes.append(dict(
        point=point, annee=-1,                      # -1 = total du point
        mesures_infra_journalieres=int(len(sub)) if sub is not None else 0,
        journees_lues=int(len(brut)) if brut is not None else 0,
        journees_ecartees_qc=int(len(ecartees)) if ecartees is not None else 0,
        journees_retenues_apres_fusion=int(len(df)) if df is not None else 0,
        journees_non_diag_air_absent=_compte_motifs(
            non_diag, list(non_diag), "air absente"),
        journees_non_diag_densite=_compte_motifs(
            non_diag, list(non_diag), "densité calendaire"),
        mesures_ecartees_a_la_lecture=_n_ecartees_lecture(res, None),
        journees_signalees_completude=_n_signalees_completude(res, None),
        journees_perdues_hors_qc=(
            (len(brut) if brut is not None else 0)
            - (len(ecartees) if ecartees is not None else 0)
            - (len(df) if df is not None else 0)
            - _compte_motifs(non_diag, list(non_diag), "air absente"))))
    return lignes


COLS_02 = ["point", "annee", "mesures_infra_journalieres", "journees_lues",
           "journees_ecartees_qc", "journees_retenues_apres_fusion",
           "journees_non_diag_air_absent", "journees_non_diag_densite",
           # CORRECTIF 10 (D60) — les mesures que la LECTURE ecarte, comptees
           # par l'application et non plus deduites. Un cran plus bas que les
           # colonnes ci-dessus, qui travaillent a la journee.
           "mesures_ecartees_a_la_lecture",
           # CORRECTIF 12 (D86) — les journees SIGNALEES incompletes. Elles ne
           # sont PAS ecartees : elles restent dans la chronique, et ce compte
           # ne se retranche de rien.
           "journees_signalees_completude",
           "journees_perdues_hors_qc"]


def _n_signalees_completude(res, annee):
    """
    Combien de journees la completude a SIGNALEES — pour une annee, ou pour
    tout le point si `annee` vaut None.

    Trois valeurs possibles, et elles ne se confondent pas :
      un entier   le critere s'est prononce ;
      "n/a"       le critere s'est declare INAPPLICABLE (D92) — horodatages
                  detruits, il ne peut rien voir ;
      ""          l'application ne produit pas la table (on rejoue ref/v4_5).
    Ecrire zero dans les deux derniers cas serait le mensonge que ce correctif
    retire.
    """
    m = getattr(res, "marques_completude", None)
    if m is None:
        return ""
    if not len(m):
        return 0
    if (m["statut"] == "indeterminable").all():
        return "n/a"
    s = m[m["statut"] == "signalee"]
    if annee is None:
        return int(len(s))
    if not len(s):
        return 0
    d = pd.to_datetime(pd.Series(list(s["date"])), errors="coerce")
    return int((d.dt.year == annee).sum())


def _n_ecartees_lecture(res, annee):
    """
    Combien de mesures la LECTURE a ecartees — pour une annee, ou pour tout le
    point si `annee` vaut None.

    CORRECTIF 10 : le nombre est LU dans `res.marques_lecture`. Avant le
    correctif, et lorsqu'on rejoue `ref/v4_5`, cette table n'existe pas :
    la colonne vaut alors la chaine vide, qui dit « l'application ne le
    declare pas » et non « zero ». Ecrire zero la ou rien n'est mesure serait
    le meme mensonge que celui que ce correctif retire.

    ASYMETRIE DES CAUSES : une mesure dont la DATE est illisible n'a pas de
    journee, donc pas d'annee. Elle compte dans le total du point (annee=-1)
    et dans aucune ligne annuelle. La somme des lignes annuelles peut donc
    etre inferieure au total, et c'est exact.
    """
    m = getattr(res, "marques_lecture", None)
    if m is None:
        return ""
    if annee is None:
        return int(len(m))
    if not len(m):
        return 0
    d = pd.to_datetime(pd.Series(list(m["date"])), errors="coerce")
    return int((d.dt.year == annee).sum())


def art_03(res, point: str):
    """
    Journées écartées, par point et par jour, avec motif.

    Trois étapes distinctes, dont une seule produit un motif exploitable :

      controle_qualite   motif restitué par qc.controle_qualite (colonne
                         `motif` du rapport). RÉCUPÉRABLE.
      fusion_eau_air     la jointure eau/air. AVANT le correctif 5 elle était
                         INTERNE et supprimait les journées absentes de la
                         chronique d'air : V4.5 n'en traçait aucune, et le
                         harnais devait la DÉDUIRE en comparant à res.df_air.
                         DEPUIS le correctif 5 elle est à gauche et
                         l'application marque elle-même ces journées : le
                         harnais LIT `res.marques_fusion` et cesse de déduire.
                         La colonne `origine_motif` dit laquelle des deux
                         voies a servi.
      densite_calendaire journées exploitables que le correctif 2 laisse sans
                         `Tmh`, faute d'assez de jours observés dans leur
                         fenêtre (D45). Elles restent dans `res.df` : elles ne
                         sont pas supprimées, elles sont nommées.
      lecture_sonde      journées entièrement perdues avant l'agrégation
                         journalière (dropna sur date ou température,
                         io_data.py:98). V4.5 ne conserve AUCUNE trace de ces
                         lignes : ni compte, ni date, ni cause.
                         motif = NON_RECUPERABLE.
    """
    lignes = []
    qc = res.rapport_qc
    if qc is not None and len(qc):
        for _, r in qc.iterrows():
            lignes.append(dict(
                point=point, date=str(r["date"]), etape="controle_qualite",
                motif=str(r["motif"]),
                origine_motif="qc.controle_qualite — colonne motif du rapport",
                T_eau_moy=_f(r.get("T_eau_moy")), T_eau_max=_f(r.get("T_eau_max")),
                T_air=_f(r.get("T_air"))))
    # D57 — les valeurs de diagnostic du detecteur, par journee. Elles
    # viennent de la vue detaillee du perimetre, jamais de la vue heritee.
    det = getattr(res, "rapport_qc_detaille", None)
    if det is not None and len(det):
        par_date = {str(r["date"]): r for _, r in det.iterrows()}
        for l in lignes:
            r = par_date.get(l["date"])
            if r is None:
                continue
            l["E_moy_rel"] = _f(r.get("E_moy_rel"))
            l["R_ampl_rel"] = _f(r.get("R_ampl_rel"))
            l["E_max_rel"] = _f(r.get("E_max_rel"))
            l["longueur_episode"] = (int(r["longueur_episode"])
                                     if pd.notna(r.get("longueur_episode"))
                                     else None)
            l["marche_active"] = r.get("marche_active")
            l["T_eau_ecart_median"] = _f(r.get("T_eau_ecart_median"))
            l["motifs_complets"] = r.get("motifs_complets")

    brut = res.daily_eau_brut
    marques = getattr(res, "marques_fusion", None)
    if marques is not None and len(marques):
        # CORRECTIF 5 — l'application trace elle-meme. Le harnais lit, et les
        # temperatures cessent d'etre vides : la table de marquage les porte.
        nd = marques[marques["statut"] == "non_diagnosticable"]
        for _, r in nd.sort_values("date").iterrows():
            motifs = list(r["motifs"])
            densite = any("densité calendaire" in x for x in motifs)
            lignes.append(dict(
                point=point, date=str(r["date"]),
                etape="densite_calendaire" if densite else "fusion_eau_air",
                motif=SEP_MOTIFS_H.join(motifs),
                origine_motif=("core.fusionner_marque — colonne motifs de la "
                               "table de marquage (correctif 5)"),
                T_eau_moy=_f(r.get("T_eau_moy")), T_eau_max=_f(r.get("T_eau_max")),
                T_air=_f(r.get("T_air"))))
    elif brut is not None and len(brut):
        # Avant le correctif 5 : aucune trace dans l'application, le harnais
        # deduit ce qu'il peut. Branche conservee pour rejouer ref/v4_5.
        d_brut = set(brut["date"].tolist())
        d_qc = set(qc["date"].tolist()) if qc is not None and len(qc) else set()
        d_fin = set(res.df["date"].tolist()) if res.df is not None and len(res.df) else set()
        d_air = set(res.df_air["date"].tolist()) if res.df_air is not None else set()
        for d in sorted(d_brut - d_qc - d_fin):
            if d not in d_air:
                motif = ("absente de la chronique d'air — supprimee par la "
                         "jointure interne core.fusionner:85")
                origine = ("deduction du harnais par comparaison a res.df_air "
                           "(V4.5 ne trace pas cette perte)")
            else:
                motif = "NON_RECUPERABLE"
                origine = ("journee presente dans l'air et hors rapport QC, "
                           "pourtant absente du resultat : V4.5 n'en conserve "
                           "aucune trace")
            lignes.append(dict(point=point, date=str(d), etape="fusion_eau_air",
                               motif=motif, origine_motif=origine,
                               T_eau_moy=None, T_eau_max=None, T_air=None))

    # CORRECTIF 12 — les journees SIGNALEES incompletes. Elles ne sont PAS
    # ecartees : elles restent dans res.df et dans tous les calculs. Elles
    # figurent ici parce que cet artefact porte deja des journees nommees sans
    # etre supprimees — c'est le cas de `densite_calendaire` depuis le
    # correctif 2. L'etape le dit, et le motif aussi.
    mc = getattr(res, "marques_completude", None)
    if mc is not None and len(mc):
        for _, r in mc[mc["statut"] == "signalee"].sort_values("date").iterrows():
            lignes.append(dict(
                point=point, date=str(r["date"]), etape="completude_journee",
                motif=f"RETENUE — {r['motif']}",
                origine_motif=("io_data.marquer_completude — colonne motif de "
                               "la table de completude (correctif 12) ; la "
                               "journee reste dans la chronique"),
                n_mesures=(int(r["n_mesures"])
                           if pd.notna(r.get("n_mesures")) else None),
                T_eau_moy=None, T_eau_max=None, T_air=None))
        if (mc["statut"] == "indeterminable").all():
            lignes.append(dict(
                point=point, date="", etape="completude_journee",
                motif="CRITERE INAPPLICABLE — "
                      + str(mc["motif"].iloc[0]),
                origine_motif=("io_data.marquer_completude — le critere se "
                               "declare inapplicable plutot que de rendre "
                               "« aucune journee signalee » (D92)"),
                T_eau_moy=None, T_eau_max=None, T_air=None))

    # Mesures ecartees avant l'agregation journaliere.
    ml = getattr(res, "marques_lecture", None)
    if ml is not None:
        # CORRECTIF 10 — l'application trace elle-meme. Le harnais LIT, et
        # cesse de deduire. Une ligne par journee touchee, avec le compte et
        # les causes distinguees ; les mesures dont la DATE est illisible
        # n'appartiennent a aucune journee et sont regroupees a part.
        if len(ml):
            avec_date = ml[ml["date"].notna()]
            for d, g in avec_date.groupby("date"):
                motifs = SEP_MOTIFS_H.join(sorted(set(g["motif"])))
                lignes.append(dict(
                    point=point, date=str(d), etape="lecture_sonde",
                    motif=f"{len(g)} mesure(s) — {motifs}",
                    origine_motif=("io_data.marquer_lecture — colonne motif "
                                   "de la table de marquage (correctif 10)"),
                    T_eau_moy=None, T_eau_max=None, T_air=None))
            sans_date = ml[ml["date"].isna()]
            if len(sans_date):
                motifs = SEP_MOTIFS_H.join(sorted(set(sans_date["motif"])))
                lignes.append(dict(
                    point=point, date="", etape="lecture_sonde",
                    motif=f"{len(sans_date)} mesure(s) sans journee "
                          f"attribuable — {motifs}",
                    origine_motif=("io_data.marquer_lecture — une mesure dont "
                                   "la date est illisible ne s'impute a aucune "
                                   "journee (correctif 10)"),
                    T_eau_moy=None, T_eau_max=None, T_air=None))
    else:
        # Avant le correctif 10, et pour rejouer ref/v4_5 : aucune trace dans
        # l'application, le harnais deduit ce qu'il peut — et il ne peut voir
        # que les journees ENTIEREMENT perdues.
        perdues = _journees_perdues_a_la_lecture(res, brut)
        for d, n in perdues:
            lignes.append(dict(
                point=point, date=str(d), etape="lecture_sonde",
                motif="NON_RECUPERABLE",
                origine_motif=(f"{n} mesure(s) de cette journee ecartee(s) par le "
                               f"dropna de io_data.py:98 ; V4.5 ne produit ni "
                               f"compte, ni date, ni cause"),
                T_eau_moy=None, T_eau_max=None, T_air=None))
    return lignes


# Le separateur employe pour joindre les motifs multiples dans l'artefact.
# Ecrit ici plutot qu'importe de thermie_debits.qc : le harnais rejoue deux
# codes differents qui portent le meme nom de module.
SEP_MOTIFS_H = " + "

COLS_03 = ["point", "date", "etape", "motif", "origine_motif",
           "T_eau_moy", "T_eau_max", "T_air",
           # D93 — l'effectif de la journee, a cote de son motif. Renseigne
           # pour les lignes de completude ; vide ailleurs, ou il ne
           # signifierait rien.
           "n_mesures",
           # D57 — valeurs de diagnostic du detecteur, par journee.
           "E_moy_rel", "R_ampl_rel", "E_max_rel", "longueur_episode",
           # CORRECTIF 13 — le second membre de la marche 1 (D111).
           "T_eau_ecart_median",
           "marche_active",
           # ETAPE 20 — la chaine COMPLETE des motifs.
           # `motif` ci-dessus vient de la vue HERITEE : une journee n'y porte
           # que son PREMIER motif. Compter les journees marquees hors d'eau en
           # filtrant cette colonne SOUS-ESTIME le total de celles qu'un
           # detecteur anterieur avait deja touchees — c'est l'erreur commise
           # aux etapes 18, 19 et 20. Ces journees etaient ecartees dans les
           # deux cas : c'est le compte qui etait faux, pas l'analyse.
           "motifs_complets"]


def _journees_perdues_a_la_lecture(res, brut):
    """
    Journées qui existent dans le fichier source mais n'atteignent jamais
    daily_eau_brut. Reconstruit avec les fonctions de ref/v4_5 elles-mêmes —
    aucune ré-implémentation de la logique de lecture.
    """
    appel = res.config.sources.fichier_eau
    if not appel:
        return []
    try:
        src = Path(appel)
        df_w, _ = _lire_brut_original(str(src), nom=src.name)
        dev_date, dev_temp = _deviner_original(df_w)
        cand = [c for c in df_w.columns
                if any(m in str(c).lower() for m in
                       ["date", "heure", "time", "timestamp", "horodat"])
                or any(m in str(c).lower() for m in ["dtana", "dtprel"])]
        col_date = None
        for dc in cand:
            nn = df_w[dc].dropna()
            samp = str(nn.iloc[0]) if len(nn) else ""
            if len(samp) > 8 and not str(dc).lower().startswith(("heure", "hr")):
                col_date = dc
                break
        if col_date is None:
            col_date = dev_date or (cand[0] if cand else None)
        if col_date is None or dev_temp is None:
            return []
        dt = io_data._parse_dates_sonde(df_w[col_date])
        col_h = next((c for c in df_w.columns
                      if str(c).lower().startswith(("heure", "hrana", "hrprel"))
                      and c != col_date), None)
        if col_h is not None and dt.notna().any() and (dt.dt.hour == 0).all():
            def _td(h):
                try:
                    h = str(h).strip()
                    return pd.Timedelta(h) if ":" in h else pd.Timedelta(0)
                except Exception:
                    return pd.Timedelta(0)
            dt = dt + df_w[col_h].apply(_td)
        t = pd.to_numeric(df_w[dev_temp].astype(str).str.replace(",", ".")
                          .str.replace(" ", ""), errors="coerce")
        jour = dt.dt.date
        perdu = jour.notna() & t.isna()
        if not perdu.any():
            return []
        gardees = set(brut["date"].tolist()) if brut is not None and len(brut) else set()
        c = jour[perdu].value_counts()
        return sorted((d, int(n)) for d, n in c.items() if d not in gardees)
    except Exception as exc:
        # Un « aucune journee perdue » obtenu en avalant une exception dirait
        # le contraire de la verite. L'echec du diagnostic est donc restitue
        # comme une ligne, pas comme un silence.
        return [(f"DIAGNOSTIC IMPOSSIBLE ({type(exc).__name__}: {exc})", 0)]


def art_04(res, point: str):
    """Normales journalières : la table (jour, mois) -> T_normale."""
    lignes = []
    df = res.df
    if df is None or "T_normale" not in df.columns:
        return lignes
    n = (df[["day", "month", "T_normale"]].drop_duplicates(["day", "month"])
         .sort_values(["month", "day"]))
    for _, r in n.iterrows():
        lignes.append(dict(point=point, mois=int(r["month"]), jour=int(r["day"]),
                           T_normale=_f(r["T_normale"])))
    return lignes


COLS_04 = ["point", "mois", "jour", "T_normale"]


def art_05(res, point: str):
    """Anomalie brute (Delta_TMm) et anomalie lissée (Delta_TMm_liss)."""
    lignes = []
    df = res.df
    if df is None or not len(df):
        return lignes
    for _, r in df.iterrows():
        lignes.append(dict(
            point=point, date=str(r["date"]),
            T_air=_f(r.get("T_air")), T_normale=_f(r.get("T_normale")),
            anomalie_brute=_f(r.get("Delta_TMm")),
            anomalie_lissee=_f(r.get("Delta_TMm_liss")),
            T_air_std=_f(r.get("T_air_std"))))
    return lignes


COLS_05 = ["point", "date", "T_air", "T_normale", "anomalie_brute",
           "anomalie_lissee", "T_air_std"]


def _statut_validite(info):
    """
    D67 — le statut de validite d'un coefficient, a TROIS valeurs et non deux.

    `valide` / `REJETE` se lisent sur le booleen `validite`, produit par la
    regle du correctif 6. `replie` se lit sur le champ `statut`, que
    l'application pose quand elle se rabat sur un autre coefficient faute
    d'effectif : le coefficient n'a pas ete juge, il n'a pas ete estime.

    Le vide subsiste, et il garde un sens precis : la grandeur n'est pas un
    coefficient de couplage (ligne `normales`), ou la chaine n'a rien produit.
    """
    if info.get("statut"):
        return info["statut"]
    v = info.get("validite")
    return "" if v is None else "valide" if v else "REJETE"


def art_06(res, journal: Journal, point: str):
    """m, R², n, p et tout diagnostic déjà produit par la chaîne."""
    s = res.sensibilite or {}
    lignes = [dict(
        point=point, grandeur="m_estival",
        fonction="core.analyse_sensibilite (core.py:134)",
        m=_f(s.get("m")), intercept=_f(s.get("intercept")),
        r2=_f(s.get("r2")), n=s.get("n"),
        p=_f(s.get("p_reg")),
        test_utilise=s.get("test_used"),
        r_pearson=_f(s.get("r_pearson")), p_pearson=_f(s.get("p_pearson")),
        r_spearman=_f(s.get("r_spearman")), p_spearman=_f(s.get("p_spearman")),
        p_shapiro_x=_f(s.get("p_x")), p_shapiro_y=_f(s.get("p_y")),
        robustesse=_f(s.get("robustesse")),
        categorie=s.get("sens_cat"), categorie_r2=s.get("r2_cat"),
        categorie_robustesse=s.get("rob_cat"), diagnostic="",
        # CORRECTIF 6 (C4) — le statut de validite est une donnee de sortie.
        m_estime=_f(s.get("m_estime")),
        validite_statut=_statut_validite(s),
        validite_ic95_demi_largeur=_f(s.get("ic95_demi_largeur")),
        validite_erreur_type_nw=_f(s.get("erreur_type_newey_west")),
        validite_t=_f(s.get("t_newey_west")),
        validite_lag_nw=s.get("lag_newey_west"),
        validite_critere_rejetant=s.get("validite_critere_rejetant"))]
    for ms in journal.m_saisonnier:
        info = ms.get("info") or {}
        lignes.append(dict(
            point=point, grandeur="m_saisonnier_fraie",
            fonction="core._m_saisonnier (core.py:243)",
            m=_f(ms.get("m_retenu")), intercept=None,
            r2=_f(info.get("r2")), n=info.get("n"), p=None,
            test_utilise="linregress", r_pearson=None, p_pearson=None,
            r_spearman=None, p_spearman=None, p_shapiro_x=None,
            p_shapiro_y=None, robustesse=None, categorie=None,
            categorie_r2=None, categorie_robustesse=None,
            m_estime=_f(info.get("m")),
            validite_statut=_statut_validite(info),
            validite_ic95_demi_largeur=_f(info.get("ic95_demi_largeur")),
            validite_erreur_type_nw=_f(info.get("erreur_type_newey_west")),
            validite_t=_f(info.get("t_newey_west")),
            validite_lag_nw=info.get("lag_newey_west"),
            validite_critere_rejetant=info.get("critere_rejetant"),
            diagnostic=(f"source={info.get('source')} ; mois="
                        f"{'-'.join(str(m) for m in ms.get('mois', []))} ; "
                        f"m_estival={_f(ms.get('m_estival')):.6f} ; "
                        f"m_regresse={_f(info.get('m')):.6f}"
                        if _f(info.get('m')) is not None else
                        f"source={info.get('source')} ; mois="
                        f"{'-'.join(str(m) for m in ms.get('mois', []))} ; "
                        f"m_estival={_f(ms.get('m_estival')):.6f} ; "
                        f"m_regresse=")))
    dn = res.diag_normales or {}
    lignes.append(dict(
        point=point, grandeur="normales",
        fonction="io_data.calculer_normales_ecarts (io_data.py:495)",
        m=None, intercept=None, r2=None, n=dn.get("n_annees_ref"), p=None,
        test_utilise=None, r_pearson=None, p_pearson=None, r_spearman=None,
        p_spearman=None, p_shapiro_x=None, p_shapiro_y=None, robustesse=None,
        categorie=None, categorie_r2=None, categorie_robustesse=None,
        m_estime=None, validite_statut=None,
        validite_ic95_demi_largeur=None, validite_erreur_type_nw=None,
        validite_t=None, validite_lag_nw=None,
        validite_critere_rejetant=None,
        diagnostic=(f"ref={dn.get('ref')} ; periode_totale="
                    f"{dn.get('periode_totale')} ; fenetre_lissage="
                    f"{dn.get('fenetre_lissage')} ; min_annees="
                    f"{dn.get('min_annees')} ; avertissements="
                    f"{dn.get('avertissements')}")))
    return lignes


COLS_06 = ["point", "grandeur", "fonction", "m", "intercept", "r2", "n", "p",
           "test_utilise", "r_pearson", "p_pearson", "r_spearman",
           "p_spearman", "p_shapiro_x", "p_shapiro_y", "robustesse",
           "categorie", "categorie_r2", "categorie_robustesse", "diagnostic",
           # CORRECTIF 6 (C4) — le statut de validite, sa pente estimee, son
           # IC, son t, son decalage, et le critere qui a rejete.
           # D67 — `validite_statut` prend une TROISIEME valeur, `replie`,
           # pour les coefficients que l'effectif n'a pas permis d'estimer.
           "m_estime", "validite_statut", "validite_ic95_demi_largeur",
           "validite_erreur_type_nw", "validite_t", "validite_lag_nw",
           "validite_critere_rejetant"]


def art_07(res, point: str):
    """
    Températures normalisées. La chaîne en produit SIX séries journalières,
    relevant de DEUX FAMILLES de formules distinctes.

    FAMILLE 1 — « normalisation », dans core.py : on retranche m fois
    l'anomalie d'air LISSÉE.

      Tmh_norm        = Tmh       - m_estival    x Delta_TMm_liss
                        core.analyse_vulnerabilite (core.py:177)
      Tmax_norm       = T_eau_max - m_estival    x Delta_TMm_liss
                        core.analyse_vulnerabilite (core.py:178)
      Tmh_norm_fraie  = Tmh       - m_saisonnier x Delta_TMm_liss
                        core.analyse_fraie_croissance (core.py:347)

    FAMILLE 2 — « compensation », dans indicateurs.py : on retranche
    l'anomalie d'air BRUTE, SANS coefficient (donc m implicitement égal à 1).

      T_moy_comp      = T_eau_moy - Delta_TMm    indicateurs.py:88
      T_max_comp      = T_eau_max - Delta_TMm    indicateurs.py:89
      T_min_comp      = T_eau_min - Delta_TMm    indicateurs.py:90

    Les deux familles sont affichées : la première pilote la grille de
    vulnérabilité et les figures de chronique ; la seconde alimente le tableau
    mensuel d'indicateurs (colonnes « Tmax comp », « Tmin comp », « Tmm30j
    comp ») et sa figure.

    Chaque ligne porte la fonction qui l'a produite, et deux colonnes de
    provenance :
      `sortie_v45`    booleen. Vrai = la valeur sort telle quelle d'une
                      structure retournee par V4.5. Faux = le harnais l'a
                      recalculee faute que V4.5 l'expose. D13 : les lignes a
                      faux sont EXCLUES du verdict de non-regression — elles
                      controlent le harnais, pas l'application.
      `source_valeur` la phrase qui dit d'ou vient exactement la valeur.
    """
    lignes = []
    df = res.df
    if df is None or not len(df):
        return lignes
    m = (res.sensibilite or {}).get("m")
    for col, fonc, coef in (
            ("Tmh_norm", "core.analyse_vulnerabilite (core.py:177)", "m_estival"),
            ("Tmax_norm", "core.analyse_vulnerabilite (core.py:178)", "m_estival")):
        if col not in df.columns:
            continue
        base = "Tmh" if col == "Tmh_norm" else "T_eau_max"
        for _, r in df.iterrows():
            lignes.append(dict(
                point=point, date=str(r["date"]), grandeur=col,
                famille="normalisation (core.py)",
                fonction=fonc, coefficient_applique=coef, m=_f(m),
                T_base=_f(r.get(base)),
                anomalie_utilisee=_f(r.get("Delta_TMm_liss")),
                type_anomalie="lissee (Delta_TMm_liss)",
                T_normalisee=_f(r.get(col)), sortie_v45=True,
                source_valeur="colonne de res.df, produite par V4.5"))

    # FAMILLE 2 — compensation. indicateurs.calcul_indicateurs construisait
    # ces trois colonnes dans une variable LOCALE et ne retournait que des
    # agregats mensuels : la serie journaliere n'etait pas exposee. Le harnais
    # appliquait donc la formule citee, telle quelle, sur res.df — et le
    # disait (sortie_v45 = faux, donc hors verdict par D13).
    #
    # CORRECTIF 4, VOIE B (etape 14) — `app/` ne produit plus cette famille.
    # Le harnais cesse de la figer POUR `app/` et continue de la figer POUR
    # `ref/v4_5`, qui la produit toujours : la reference de V4.5 ne change pas
    # parce que `app/` a change. Les lignes DISPARAISSENT du fichier ; elles
    # ne deviennent pas vides.
    for col, ligne_src, base in (_SERIES_COMPENSATION
                                 if _famille_compensation_publiee(res) else ()):
        if "Delta_TMm" not in df.columns or base not in df.columns:
            continue
        for _, r in df.iterrows():
            tb, da = r.get(base), r.get("Delta_TMm")
            val = (tb - da) if (pd.notna(tb) and pd.notna(da)) else None
            lignes.append(dict(
                point=point, date=str(r["date"]), grandeur=col,
                famille="compensation (indicateurs.py)",
                fonction=f"indicateurs.calcul_indicateurs ({ligne_src})",
                coefficient_applique="aucun (m implicitement egal a 1)",
                m=None, T_base=_f(tb), anomalie_utilisee=_f(da),
                type_anomalie="brute (Delta_TMm)",
                T_normalisee=_f(val), sortie_v45=False,
                source_valeur="recalcul par le harnais de la formule citee — "
                              "V4.5 ne l'expose qu'agregee au mois"))

    # Troisieme serie : la normalisation de la fenetre de fraie, produite avec
    # un AUTRE coefficient (m saisonnier) par une AUTRE fonction. Elle vit dans
    # le sous-DataFrame `sub` de chaque sous-indicateur, jamais dans res.df.
    fr = res.fraie
    if fr:
        for sous in (fr.get("sous_indicateurs") or []):
            sub = sous.get("sub")
            if sub is None or "Tmh_norm_fraie" not in getattr(sub, "columns", []):
                continue
            ms = sous.get("m_saison")
            espece = str(sous.get("espece") or "")
            anomalie = ("Delta_TMm_liss" if "Delta_TMm_liss" in sub.columns
                        else "Delta_TMm")
            for _, r in sub.iterrows():
                lignes.append(dict(
                    point=point, date=str(r["date"]),
                    grandeur=f"Tmh_norm_fraie[{espece}]",
                    famille="normalisation (core.py)",
                    fonction="core.analyse_fraie_croissance (core.py:347)",
                    coefficient_applique=f"m_saisonnier ({(sous.get('m_info') or {}).get('source')})",
                    m=_f(ms), T_base=_f(r.get("Tmh")),
                    anomalie_utilisee=_f(r.get(anomalie)),
                    type_anomalie=("lissee (Delta_TMm_liss)"
                                   if anomalie == "Delta_TMm_liss"
                                   else "brute (Delta_TMm)"),
                    T_normalisee=_f(r.get("Tmh_norm_fraie")), sortie_v45=True,
                    source_valeur="colonne du sous-DataFrame retourne par "
                                  "core.analyse_fraie_croissance"))
    return lignes


# Les trois series de la famille compensation, avec la ligne qui les produit
# dans le code qui les produit encore. Ecrites ici plutot qu'en litteral dans
# la boucle : c'est la liste que `_famille_compensation_publiee` gouverne.
_SERIES_COMPENSATION = (
    ("T_moy_comp", "indicateurs.py:88", "T_eau_moy"),
    ("T_max_comp", "indicateurs.py:89", "T_eau_max"),
    ("T_min_comp", "indicateurs.py:90", "T_eau_min"),
)


def _famille_compensation_publiee(res) -> bool:
    """
    Le code EXECUTE publie-t-il encore la famille compensation ?

    La question se pose au tableau mensuel, seul endroit ou cette famille
    sorte de `calcul_indicateurs`. Si ses colonnes n'y sont plus, la famille
    n'existe plus dans le code execute et le harnais n'a plus rien a figer.

    On ne demande NI la version NI `THERMIE_CODE` : on demande au code ce
    qu'il declare. Un harnais qui devinerait la source se tromperait le jour
    ou l'on rejoue autre chose.
    """
    ind = getattr(res, "indicateurs", None) or {}
    table = ind.get("table_mensuelle")
    if table is None:
        return False
    # `set(... or [])` leverait ici : un Index pandas n'a pas de valeur de
    # verite. Le cas « pas de table » se dit en clair, au-dessus.
    colonnes = set(table.columns)
    return bool(colonnes & {"Tmax comp (°C)", "Tmin comp (°C)",
                            "Tmm30j comp (°C)"})


COLS_07 = ["point", "date", "grandeur", "famille", "fonction",
           "coefficient_applique", "m", "T_base", "anomalie_utilisee",
           "type_anomalie", "T_normalisee", "sortie_v45", "source_valeur"]


def art_08(res, point: str):
    """Témoin hors périmètre (D4) : scores bio et débits. Capturés, jamais
    discutés."""
    lignes = []
    v = res.vulnerabilite or {}
    g = res.sgvt or {}
    f = res.fraie or {}
    d = res.debits_inflexion or {}
    c = res.debits_reference or {}
    dd = res.diag_debit or {}

    def add(indic, val, unite="", detail=""):
        lignes.append(dict(point=point, indicateur=indic,
                           valeur=_f(val) if isinstance(val, (int, float))
                           and not isinstance(val, bool) else None,
                           valeur_texte="" if isinstance(val, (int, float))
                           and not isinstance(val, bool) else str(val),
                           unite=unite, detail=detail))

    add("sgvt", g.get("sgvt"), "/10", str(g.get("interp") or ""))
    add("sgvt_composantes", g.get("composantes"), "nb")
    add("pts_sensibilite", g.get("pts_s"), "/3")
    add("pts_chronique", g.get("pts_c"), "/3")
    add("pts_aigu", g.get("pts_a"), "/3")
    add("pts_fraie", g.get("pts_f"), "/3")
    add("pct_stress_chronique", v.get("pct_chr"), "%", str(v.get("cat_chr") or ""))
    add("n_jours_aigus", v.get("n_aigu"), "j", str(v.get("cat_aigu") or ""))
    add("seuil_chronique", v.get("seuil_chr"), "degC")
    add("seuil_aigu", v.get("seuil_aigu"), "degC")
    add("espece_repere", v.get("espece_repere") or "")
    add("n_jours_tmh", v.get("n_total_tmh"), "j")
    add("n_jours_tmax", v.get("n_total_tmax"), "j")
    add("P_fraie", f.get("P_fraie") if f else None, "/3",
        str((f or {}).get("espece_limitante") or ""))
    add("base_debit", res.base_debit or "")
    add("debit_message", dd.get("message") or "")
    add("q_thermie_bio", c.get("q_thermie_bio"), "m3/s")
    add("q_thermie_fonc", c.get("q_thermie_fonc"), "m3/s")
    add("q_aicc", d.get("q_aicc"), "m3/s")
    add("q_seuil", d.get("q_seuil"), "m3/s")
    add("avertissements", " || ".join(res.avertissements or []))
    return lignes


COLS_08 = ["point", "indicateur", "valeur", "valeur_texte", "unite", "detail"]


# --- fonctions originales, conservees avant installation des wrappers --------
_lire_brut_original = None
_deviner_original = None


# ============================================================
# Exécution
# ============================================================
def construire(jeux, sortie: Path, chemin: str = CHEMIN_DEFAUT,
               etape: int = ETAPE_COURANTE, etape_manifeste=None):
    global _lire_brut_original, _deviner_original
    _lire_brut_original = sniff.lire_brut
    _deviner_original = sniff.deviner_colonnes

    resume = []
    for jeu in jeux:
        dossier = sortie / jeu["jeu"]
        dossier.mkdir(parents=True, exist_ok=True)
        a00, a01 = [], []
        a02, a03, a04, a05, a06, a07, a08 = [], [], [], [], [], [], []
        log = [f"=== JEU {jeu['jeu']} ===",
               f"air   : {jeu['air']}  ({jeu['n_air']} fichier(s))",
               f"debit : {jeu['debit']}  ({jeu['n_debit']} fichier(s))",
               f"points: {len(jeu['points'])}",
               ""]
        for point_rel in jeu["points"]:
            point = nom_point(point_rel)
            print(f"  · {jeu['jeu']} / {point}", flush=True)
            journal = Journal()
            originaux = journal.installer()
            tampon = _io.StringIO()
            statut, erreur = "OK", ""
            res = None
            try:
                cfg = construire_config(jeu, point_rel, chemin)
                with contextlib.redirect_stdout(tampon), \
                     contextlib.redirect_stderr(tampon):
                    res = orchestrator.run(cfg, verbose=True)
            except Exception as exc:                       # D7
                statut = "ECHEC"
                erreur = f"{type(exc).__name__}: {exc}"
                tampon.write("\n" + traceback.format_exc())
            finally:
                Journal.restaurer(originaux)
                try:
                    import matplotlib.pyplot as plt
                    plt.close("all")
                except Exception:
                    pass

            log.append(f"--- POINT {point} — {statut} ---")
            log.append(_nettoyer(tampon.getvalue()))
            if statut == "ECHEC":
                log.append(f"ERREUR FIGEE COMME REFERENCE (D7) : {erreur}")
            log.append("")

            a00.append(dict(art_00(journal, jeu, point), statut=statut,
                            erreur=_nettoyer(erreur)))
            if res is not None:
                a01.append(dict(point=point, **art_01(journal, res)))
                a02 += art_02(res, point)
                a03 += art_03(res, point)
                a04 += art_04(res, point)
                a05 += art_05(res, point)
                a06 += art_06(res, journal, point)
                a07 += art_07(res, point)
                a08 += art_08(res, point)
            else:
                a01.append(dict(point=point, statut="ECHEC",
                                erreur=_nettoyer(erreur),
                                propositions_deviner_colonnes=journal.colonnes))
                a08.append(dict(point=point, indicateur="statut", valeur=None,
                                valeur_texte="ECHEC", unite="",
                                detail=_nettoyer(erreur)))
            resume.append((jeu["jeu"], point, statut))

        ecrire_json(dossier / "10_parametres.json", art_10(jeu, chemin))
        ecrire_json(dossier / "00_format_detecte.json", a00)
        ecrire_json(dossier / "01_colonnes_retenues.json", a01)
        ecrire_csv(dossier / "02_effectifs.csv", COLS_02, a02, tri=["point", "annee"])
        ecrire_csv(dossier / "03_journees_ecartees.csv", COLS_03, a03,
                   tri=["point", "date", "etape", "motif"])
        ecrire_csv(dossier / "04_normales.csv", COLS_04, a04,
                   tri=["point", "mois", "jour"])
        ecrire_csv(dossier / "05_anomalies.csv", COLS_05, a05, tri=["point", "date"])
        ecrire_csv(dossier / "06_coefficients.csv", COLS_06, a06,
                   tri=["point", "grandeur", "diagnostic"])
        ecrire_csv(dossier / "07_t_norm.csv", COLS_07, a07,
                   tri=["point", "grandeur", "date"])
        ecrire_csv(dossier / "08_scores.csv", COLS_08, a08,
                   tri=["point", "indicateur"])
        ecrire_texte(dossier / "99_log.txt", "\n".join(log) + "\n")
    # D70 — la provenance, ecrite a la racine du dossier construit, qu'il
    # s'agisse d'une reference ou d'un rejeu jetable. Un rejeu non etiquete
    # est le premier pas vers une reference non etiquetee.
    ecrire_source_code(sortie, chemin, etape, etape_manifeste)
    return resume


def _nettoyer(texte: str) -> str:
    """
    Retire de la sortie console ce qui n'est pas reproductible d'un run à
    l'autre. Deux choses seulement, et elles sont nommées :

    1. **Les chemins absolus** (D5) : remplacés par `<RACINE>`.

    2. **Le numéro de ligne du harnais lui-même** dans les traces d'erreur.
       Une trace figée par D7 traverse d'abord `build_reference.py` avant
       d'entrer dans `ref/v4_5/`. Sans ce filtre, éditer une ligne du harnais —
       même un commentaire — décalerait ce numéro et ferait diverger la
       référence, alors que le comportement de V4.5 n'aurait pas bougé. La
       référence doit dépendre de V4.5, jamais de l'outil qui l'observe.
       Les numéros de ligne DANS `ref/v4_5/` sont conservés : ce sont eux qui
       portent l'information.

    Rien d'autre n'est filtré : le log reste intégral.
    """
    if not texte:
        return ""
    t = texte.replace(str(RACINE), "<RACINE>")
    t = t.replace(str(RACINE).replace("\\", "/"), "<RACINE>")
    t = t.replace(str(RACINE).replace("/", "\\"), "<RACINE>")
    t = re.sub(
        r'(File "<RACINE>[\\/]tests[\\/]reference[\\/][^"]+", line )\d+',
        r"\1<ligne du harnais, masquee>", t)
    # D36 — la racine du code execute est neutralisee. Le chemin du module et
    # son numero de ligne sont conserves : ce sont eux qui portent
    # l'information. Seul l'endroit du disque disparait.
    t = re.sub(r'<RACINE>[\\/](?:ref[\\/]v4_5|app)[\\/]', "<CODE>/", t)
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jeux", nargs="*", help="jeux a construire (defaut : tous)")
    ap.add_argument("--sortie", default=None,
                    help="dossier de sortie (defaut : tests/reference)")
    ap.add_argument("--chemin", choices=["application", "cli"],
                    default=CHEMIN_DEFAUT,
                    help="jeu de parametres a appliquer (defaut : application)")
    ap.add_argument("--etape", type=int, default=ETAPE_COURANTE,
                    help="etape a laquelle la reference est etablie (D70) ; "
                         "ecrite dans SOURCE_CODE.txt")
    ap.add_argument("--est-une-reference", action="store_true",
                    help="D75 : DECLARE que cette sortie est une reference et "
                         "merite un MANIFEST.sha256. Le manifeste ne s'ecrit "
                         "plus jamais sur comparaison de chemin.")
    ap.add_argument("--sans-manifeste", action="store_true",
                    help="retire la declaration : la sortie est construite, "
                         "aucun manifeste n'est ecrit")
    args = ap.parse_args()

    sortie = Path(args.sortie).resolve() if args.sortie else ICI

    # D75 — la garde. Une sortie qui porte deja un manifeste est une reference,
    # qu'on l'ait declaree ou non. La reconstruire sans le dire laisserait un
    # manifeste perime : c'est exactement le defaut que D75 corrige, et il
    # reviendrait par la porte de l'oubli.
    if (sortie / "MANIFEST.sha256").exists() and not args.est_une_reference:
        print(f"ARRET — {sortie.name} porte deja un MANIFEST.sha256 : c'est "
              f"une reference.\n"
              f"  La reconstruire sans --est-une-reference laisserait son "
              f"manifeste perime.\n"
              f"  Declarer l'intention : --est-une-reference "
              f"(ou --est-une-reference --sans-manifeste pour ne pas "
              f"l'ecrire).", file=sys.stderr)
        return 2
    tous = decouvrir()
    if args.jeux:
        voulus = set(args.jeux)
        jeux = [j for j in tous if j["jeu"] in voulus]
        manquants = voulus - {j["jeu"] for j in tous}
        if manquants:
            print(f"jeux inconnus : {sorted(manquants)}", file=sys.stderr)
            return 2
    else:
        jeux = tous

    print(f"Code execute : {CODE}  ({RACINE_CODE.relative_to(RACINE).as_posix()})")
    print(f"Corpus : {len(jeux)} jeu(x), "
          f"{sum(len(j['points']) for j in jeux)} point(s)")
    print(f"Chemin de parametres : {args.chemin}")
    resume = construire(jeux, sortie, args.chemin, args.etape,
                        args.etape if (args.est_une_reference
                                       and not args.sans_manifeste) else None)
    print(f"SOURCE_CODE.txt : source={CODE} etape={args.etape} "
          f"chemin={args.chemin}  (D70)")
    n_ok = sum(1 for _, _, s in resume if s == "OK")
    print(f"\n{n_ok} point(s) OK, {len(resume) - n_ok} en echec (figes comme "
          f"reference, D7)")
    for j, p, s in resume:
        if s != "OK":
            print(f"  ECHEC {j}/{p}")
    # D75 — sur DECLARATION, jamais sur comparaison de chemin, et dans le
    # dossier construit, jamais dans un autre.
    if args.est_une_reference and not args.sans_manifeste:
        n = ecrire_manifeste(sortie)
        print(f"MANIFEST.sha256 : {n} artefacts  ({sortie.name}, D75)")
    elif args.est_une_reference:
        print("MANIFEST.sha256 : non ecrit (--sans-manifeste)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
