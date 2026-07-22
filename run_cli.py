"""
run_cli.py — Point d'entrée ligne de commande (package thermie_debits).

Alternative à l'application Streamlit pour un usage script/batch : on édite
la CONFIG ci-dessous puis on lance `python run_cli.py`. Les figures, CSV et
XLSX sont écrits dans le dossier `output_dir`.
"""
from pathlib import Path
from thermie_debits.config import AnalyseConfig, SourcesConfig, QCConfig
from thermie_debits.orchestrator import run

_ICI = Path(__file__).parent

# ============================================================
# ██  CONFIGURATION — à adapter  ██
# ============================================================
CONFIG = AnalyseConfig(
    sources=SourcesConfig(
        fichier_eau          = str(_ICI / "examples" / "eau.csv"),
        fichier_air          = str(_ICI / "examples" / "air.csv"),
        fichier_normales     = str(_ICI / "examples" / "EcartNormales.csv"),
        fichier_debit        = str(_ICI / "examples" / "debit.csv"),   # ou None
        fichier_debit_desinf = None,                                   # optionnel
        nom_cours_eau        = "Cours d'eau",
        localisation_sonde   = "Localisation",
        nom_station_debit    = "Station hydrométrique",
    ),
    qc=QCConfig(),                                # seuils par défaut (ajustables)
    contexte_piscicole     = "intermediaire",     # salmonicole | intermediaire | cyprinicole
    mode                   = "thermie_debits",    # ou "thermie_seule"
    faire_volet_climatique = False,
    seuil_comblement_desinf= 0.10,
    output_dir             = str(_ICI / "outputs") + "/",
)

if __name__ == "__main__":
    run(CONFIG, verbose=True)
