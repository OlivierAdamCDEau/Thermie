"""run_cli.py — Point d'entrée ligne de commande (package thermie_debits)."""
from pathlib import Path
from thermie_debits.config import AnalyseConfig, SourcesConfig, QCConfig
from thermie_debits.orchestrator import run
from thermie_debits.livrables import construire_docx_bytes, construire_xlsx_bytes
_ICI = Path(__file__).parent
CONFIG = AnalyseConfig(
    sources=SourcesConfig(
        fichier_eau   = str(_ICI / "examples" / "eau.csv"),
        fichier_air   = str(_ICI / "examples" / "air.csv"),
        fichier_debit = str(_ICI / "examples" / "debit.csv"),
        fichier_debit_desinf = str(_ICI / "examples" / "debit_desinfluence.csv"),
        nom_cours_eau = "Cours d'eau", localisation_sonde = "Localisation",
        nom_station_debit = "Station hydrométrique",
        nom_station_meteo = "Station météo"),
    qc=QCConfig(), contexte_piscicole="intermediaire",
    # Zone intermédiaire : "ombre commun" (défaut) ou "barbeau".
    espece_repere=None,
    mode="thermie_debits",
    faire_volet_climatique=True, seuil_comblement_desinf=0.10,
    normales_fenetre_lissage=10, normales_min_annees=20,
    normalisation_lissage_delta=7,
    stress_plancher_pct=10.0, stress_corr_r2_min=0.10,
    output_dir=str(_ICI / "outputs") + "/")
if __name__ == "__main__":
    res = run(CONFIG, verbose=True)
    out = Path(CONFIG.output_dir)
    (out / "Rapport_Thermie.docx").write_bytes(construire_docx_bytes(res))
    (out / "Donnees_Thermie.xlsx").write_bytes(construire_xlsx_bytes(res))
    print("✅ Rapport_Thermie.docx")
    print("✅ Donnees_Thermie.xlsx")
