"""
run_cli.py — Point d'entrée ligne de commande (package thermie_debits).

Éditer la CONFIG ci-dessous puis lancer `python run_cli.py`. Les figures,
CSV et XLSX sont écrits dans `output_dir`.
"""
from pathlib import Path
from thermie_debits.config import AnalyseConfig, SourcesConfig, QCConfig
from thermie_debits.orchestrator import run

_ICI = Path(__file__).parent

CONFIG = AnalyseConfig(
    sources=SourcesConfig(
        fichier_eau   = str(_ICI / "examples" / "eau.csv"),
        fichier_air   = str(_ICI / "examples" / "air.csv"),   # air brut
        fichier_debit = str(_ICI / "examples" / "debit.csv"), # ou None
        fichier_debit_desinf = None,
        nom_cours_eau = "Cours d'eau",
        localisation_sonde = "Localisation",
    ),
    qc=QCConfig(),
    contexte_piscicole     = "intermediaire",     # salmonicole | intermediaire | cyprinicole
    mode                   = "thermie_debits",    # ou "thermie_seule"
    faire_volet_climatique = False,
    seuil_comblement_desinf= 0.10,
    normales_fenetre_lissage = 10,                # ± jours (lissage normales)
    normales_min_annees      = 20,                # seuil alerte sur 1991-2020
    output_dir             = str(_ICI / "outputs") + "/",
)

if __name__ == "__main__":
    run(CONFIG, verbose=True)
