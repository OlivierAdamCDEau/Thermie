"""
comparer_chemins.py — ÉTAPE 2, TÂCHE A2.

Tableau complet des champs de AnalyseConfig, SourcesConfig et QCConfig, avec
la valeur côté application Streamlit et la valeur côté run_cli.py, écart
signalé. Les valeurs ne sont pas devinées : chaque ligne porte le
fichier:ligne d'où elle est lue.

Sortie : out/etape2/chemins_de_parametres.csv
"""
from __future__ import annotations

import sys
from dataclasses import fields
from pathlib import Path

from _commun import RACINE, ecrire_csv

from thermie_debits.config import AnalyseConfig, SourcesConfig, QCConfig

OUT = RACINE / "out" / "etape2"

# --- Ce que l'application affecte, champ par champ -------------------------
# (valeur, fichier:ligne). "= dataclass" signifie que le widget reprend la
# valeur du dataclass comme défaut, donc pas d'écart possible.
APP_QC = {
    "bornes_physiques": ("True", "app.py:157", "= dataclass"),
    "t_eau_min": ("-0.5", "app.py:159", "= dataclass"),
    "t_eau_max": ("35.0", "app.py:160", "= dataclass"),
    "hors_eau": ("True", "app.py:161", "= dataclass"),
    "hors_eau_ecart_seuil": ("10.0", "app.py:162-163", "LITTERAL, ignore le dataclass"),
    "hors_eau_mois": ("(1, ..., 12)", "non expose",
                      "= dataclass — CORRECTIF 13 (D105)"),
    "hors_eau_min_jours": ("5", "app.py:164-165", "= dataclass"),
    "hors_eau_exclut_saison": ("False", "app.py:166", "LITTERAL, ignore le dataclass"),
    "plateau": ("True", "app.py:167", "= dataclass"),
    "plateau_fenetre": ("7", "non expose", "= dataclass"),
    "plateau_ecart_type_min": ("0.05", "non expose", "= dataclass"),
    "mad_outliers": ("True", "app.py:168", "= dataclass"),
    "mad_k": ("50.0", "app.py:169", "= dataclass"),
    "mad_mois": ("None", "non expose", "= dataclass"),
}
CLI_QC = {c: ("QCConfig() par defaut", "run_cli.py:16", "") for c in APP_QC}

APP_ANALYSE = {
    "contexte_piscicole": ("'intermediaire' (defaut d'interface) ; "
                           "'salmonicole' / 'cyprinicole' selon les classeurs",
                           "app.py:70-72 (selectbox index=1)"),
    "espece_repere": ("'ombre commun' en intermediaire (radio index=0) ; "
                      "'barbeau' pour jeu_05 d'apres son classeur",
                      "app.py:78-79 / app.py:85"),
    "mode": ("'thermie_debits'", "app.py:95-99 (radio index=1)"),
    "faire_volet_climatique": ("False", "app.py:146"),
    "output_dir": ("None", "app.py:340"),
    "seuil_comblement_desinf": ("0.10", "app.py:116"),
    "normales_fenetre_lissage": ("10", "app.py:105"),
    "normales_min_annees": ("20", "app.py:106"),
    "normalisation_lissage_delta": ("7", "app.py:107-108"),
    "stress_plancher_pct": ("10.0", "app.py:135-136"),
    "stress_corr_r2_min": ("0.10", "app.py:139-140"),
    "periode_affichage": ("None", "app.py:199"),
}
CLI_ANALYSE = {
    "contexte_piscicole": ("'intermediaire'", "run_cli.py:16"),
    "espece_repere": ("None -> 'ombre commun' (config.py contexte():52)", "run_cli.py:18"),
    "mode": ("'thermie_debits'", "run_cli.py:19"),
    "faire_volet_climatique": ("True", "run_cli.py:20"),
    "output_dir": ("str(_ICI/'outputs')+'/'", "run_cli.py:24"),
    "seuil_comblement_desinf": ("0.10", "run_cli.py:20"),
    "normales_fenetre_lissage": ("10", "run_cli.py:21"),
    "normales_min_annees": ("20", "run_cli.py:21"),
    "normalisation_lissage_delta": ("7", "run_cli.py:22"),
    "stress_plancher_pct": ("10.0", "run_cli.py:23"),
    "stress_corr_r2_min": ("0.10", "run_cli.py:23"),
    "periode_affichage": ("None (non renseigne)", "config.py:403"),
}

APP_SOURCES = {
    "fichier_eau": ("chemin du fichier televerse", "app.py:318"),
    "fichier_air": ("chemin du fichier televerse", "app.py:318"),
    "fichier_normales": ("None, EXPLICITEMENT", "app.py:319"),
    "fichier_debit": ("televerse, ou None si mode thermie_seule", "app.py:320"),
    "fichier_debit_desinf": ("televerse, ou None", "app.py:321"),
    "eau_col_date": ("None tant que l'expander de mapping n'est pas ouvert", "app.py:210, 322"),
    "eau_col_temp": ("idem", "app.py:210, 322"),
    "air_col_date": ("idem", "app.py:210, 323"),
    "air_col_temp": ("idem", "app.py:210, 323"),
    "air_station_code": ("None sauf export multi-stations", "app.py:211, 324"),
    "air_station_nom": ("non renseigne -> None", "config.py:49"),
    "eau_nom_fichier": ("nom du fichier televerse", "app.py:325"),
    "eau_feuille": ("None sauf Excel multi-feuilles", "app.py:212, 326"),
    "eau_ligne_entete": ("None sauf reglage manuel", "app.py:213, 326"),
    "air_nom_fichier": ("nom du fichier televerse", "app.py:327"),
    "air_feuille": ("None sauf Excel multi-feuilles", "app.py:328"),
    "air_ligne_entete": ("None sauf reglage manuel", "app.py:328"),
    "nom_cours_eau": ("'Cours d'eau' (defaut de saisie)", "app.py:149, 329"),
    "localisation_sonde": ("'' (defaut de saisie)", "app.py:150, 329"),
    "nom_station_debit": ("'' (defaut de saisie)", "app.py:151, 330"),
    "nom_station_meteo": ("'' (defaut de saisie)", "app.py:152, 330"),
    "periode_normales": ("non renseigne -> '1991-2020'", "config.py:62"),
}
CLI_SOURCES = {
    "fichier_eau": ("examples/eau.csv", "run_cli.py:9"),
    "fichier_air": ("examples/air.csv", "run_cli.py:10"),
    "fichier_normales": ("non renseigne -> None", "config.py:37"),
    "fichier_debit": ("examples/debit.csv", "run_cli.py:11"),
    "fichier_debit_desinf": ("examples/debit_desinfluence.csv", "run_cli.py:12"),
    "eau_col_date": ("non renseigne -> None", "config.py:42"),
    "eau_col_temp": ("non renseigne -> None", "config.py:43"),
    "air_col_date": ("non renseigne -> None", "config.py:44"),
    "air_col_temp": ("non renseigne -> None", "config.py:45"),
    "air_station_code": ("non renseigne -> None", "config.py:48"),
    "air_station_nom": ("non renseigne -> None", "config.py:49"),
    "eau_nom_fichier": ("non renseigne -> ''", "config.py:51"),
    "eau_feuille": ("non renseigne -> None", "config.py:52"),
    "eau_ligne_entete": ("non renseigne -> None", "config.py:53"),
    "air_nom_fichier": ("non renseigne -> ''", "config.py:54"),
    "air_feuille": ("non renseigne -> None", "config.py:55"),
    "air_ligne_entete": ("non renseigne -> None", "config.py:56"),
    "nom_cours_eau": ("'Cours d'eau'", "run_cli.py:13"),
    "localisation_sonde": ("'Localisation'", "run_cli.py:13"),
    "nom_station_debit": ("'Station hydrometrique'", "run_cli.py:14"),
    "nom_station_meteo": ("'Station meteo'", "run_cli.py:15"),
    "periode_normales": ("non renseigne -> '1991-2020'", "config.py:62"),
}

# Champs qui DÉSIGNENT LE JEU et non un réglage : les comparer n'a pas de sens,
# run_cli pointe sur examples/ et l'application sur le fichier téléversé.
HORS_COMPARAISON = {
    "fichier_eau", "fichier_air", "fichier_debit", "fichier_debit_desinf",
}

# Champs dont les deux chemins produisent la MÊME valeur effective, quelle que
# soit la formulation ("None, explicitement" et "non renseigné → None" sont le
# même None).
EFFECTIVEMENT_NULS = {
    "fichier_normales", "eau_col_date", "eau_col_temp", "air_col_date",
    "air_col_temp", "air_station_code", "air_station_nom", "eau_feuille",
    "eau_ligne_entete", "air_feuille", "air_ligne_entete", "periode_affichage",
}

# Champs dont l'écart ne peut RIEN changer au calcul, et pourquoi.
SANS_EFFET = {
    "output_dir": "ne pilote que l'ecriture de fichiers (orchestrator.py:272-280)",
    "nom_cours_eau": "titre de figure et de livrable seulement",
    "localisation_sonde": "metadonnee de livrable (orchestrator.py:277)",
    "nom_station_debit": "metadonnee de livrable",
    "nom_station_meteo": "metadonnee de livrable",
    "faire_volet_climatique": "ne produit que des figures (orchestrator.py:283-286) ; "
                              "aucune valeur de Resultats n'en depend",
    "fichier_debit_desinf": "hors perimetre lecture -> T_norm ; n'entre ni dans "
                            "la jointure eau/air ni dans m",
    "eau_nom_fichier": "sert a deviner l'extension quand la source est un flux "
                       "d'octets ; sans effet quand elle est un chemin (io_data.py:47-48)",
    "air_nom_fichier": "idem",
    "periode_affichage": "ne restreint que l'axe des figures (config.py:397-401)",
    "periode_normales": "declare 'tracabilite' ; aucune autre occurrence dans le code",
}


def _bloc(nom_bloc, dc, app, cli):
    lignes = []
    connus = {f.name for f in fields(dc)}
    for champ in [f.name for f in fields(dc)]:
        va, la = (app.get(champ, ("?", "?"))[0], app.get(champ, ("?", "?"))[1])
        vc, lc = (cli.get(champ, ("?", "?"))[0], cli.get(champ, ("?", "?"))[1])
        note = ""
        if nom_bloc == "QCConfig":
            va, la, note = app[champ][0], app[champ][1], app[champ][2]
            vc = _valeur_dataclass(dc, champ)
            lc = "run_cli.py:16 — QCConfig() par defaut"
        if champ in HORS_COMPARAISON:
            ecart = "hors comparaison"
        elif champ in EFFECTIVEMENT_NULS:
            ecart = "identique (None des deux cotes)"
        elif str(va) == str(vc):
            ecart = "identique"
        else:
            ecart = "ECART"
        lignes.append(dict(
            bloc=nom_bloc, champ=champ,
            valeur_application=va, source_application=la,
            valeur_run_cli=vc, source_run_cli=lc,
            ecart=ecart,
            effet_possible_sur_la_chaine=(
                "aucun — " + SANS_EFFET[champ] if champ in SANS_EFFET
                else ("designe le jeu de donnees, pas un reglage"
                      if champ in HORS_COMPARAISON
                      else ("OUI" if ecart == "ECART" else ""))),
            remarque=note))
    inconnus = set(app) - connus
    for champ in sorted(inconnus):
        lignes.append(dict(bloc=nom_bloc, champ=champ, valeur_application=app[champ][0],
                           source_application=app[champ][1], valeur_run_cli="",
                           source_run_cli="", ecart="CHAMP INCONNU DU DATACLASS",
                           effet_possible_sur_la_chaine="", remarque=""))
    return lignes


def _valeur_dataclass(dc, champ):
    import dataclasses
    for f in fields(dc):
        if f.name == champ:
            if f.default is not dataclasses.MISSING:
                return str(f.default)
            if f.default_factory is not dataclasses.MISSING:      # type: ignore
                return str(f.default_factory())                    # type: ignore
    return "?"


COLS = ["bloc", "champ", "valeur_application", "source_application",
        "valeur_run_cli", "source_run_cli", "ecart",
        "effet_possible_sur_la_chaine", "remarque"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lignes = (_bloc("QCConfig", QCConfig, APP_QC, CLI_QC)
              + _bloc("AnalyseConfig", AnalyseConfig, APP_ANALYSE, CLI_ANALYSE)
              + _bloc("SourcesConfig", SourcesConfig, APP_SOURCES, CLI_SOURCES))
    ecrire_csv(OUT / "chemins_de_parametres.csv", COLS, lignes,
               tri=["bloc", "champ"])
    ecarts = [l for l in lignes if l["ecart"] == "ECART"]
    reels = [l for l in ecarts if l["effet_possible_sur_la_chaine"] == "OUI"]
    print(f"chemins_de_parametres.csv : {len(lignes)} champs, "
          f"{len(ecarts)} ecart(s), dont {len(reels)} pouvant changer un calcul")
    for l in reels:
        print(f"   {l['bloc']}.{l['champ']} : app={l['valeur_application']} "
              f"| cli={l['valeur_run_cli']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
