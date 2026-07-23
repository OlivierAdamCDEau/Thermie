"""run_cli.py — Point d'entrée ligne de commande (package thermie_debits)."""
from pathlib import Path
from thermie_debits.config import AnalyseConfig, SourcesConfig, QCConfig
from thermie_debits.orchestrator import run
_ICI = Path(__file__).parent
CONFIG = AnalyseConfig(
    sources=SourcesConfig(
        fichier_eau   = str(_ICI / "examples" / "eau.csv"),
        fichier_air   = str(_ICI / "examples" / "air.csv"),
        fichier_debit = str(_ICI / "examples" / "debit.csv"),
        fichier_debit_desinf = None,
        nom_cours_eau = "Cours d'eau", localisation_sonde = "Localisation",
        nom_station_debit = "Station hydrométrique"),
    qc=QCConfig(), contexte_piscicole="intermediaire", mode="thermie_debits",
    faire_volet_climatique=False, seuil_comblement_desinf=0.10,
    normales_fenetre_lissage=10, normales_min_annees=20,
    stress_plancher_pct=10.0, stress_corr_r2_min=0.10,
    output_dir=str(_ICI / "outputs") + "/")
if __name__ == "__main__":
    run(CONFIG, verbose=True)
