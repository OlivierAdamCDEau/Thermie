"""
config.py — Paramètres de l'analyse thermie & débits (package thermie_debits).

Toute la configuration « en dur » de l'ancien script monolithique est ici
regroupée en dataclasses typées. Chaque champ est destiné à devenir un widget
dans l'application Streamlit ; les valeurs par défaut reproduisent exactement
le comportement validé de la v6.2.

Aucun I/O, aucune dépendance lourde : ce module est importable partout.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# 1. ENTRÉES / SORTIES ET MÉTADONNÉES
# ============================================================
@dataclass
class SourcesConfig:
    """Chemins des fichiers d'entrée et métadonnées descriptives."""
    fichier_eau:          Optional[str] = None   # CSV sonde thermique
    fichier_air:          Optional[str] = None   # CSV air brut (T° journalières)
    fichier_normales:     Optional[str] = None   # (hérité) EcartNormales pré-calculé
    fichier_debit:        Optional[str] = None   # CSV Vigicrues/Hub'eau (influencé)
    fichier_debit_desinf: Optional[str] = None   # (optionnel) désinfluencé

    # Mapping manuel optionnel (override auto-détection) — renseigné par l'app
    eau_col_date:  Optional[str] = None
    eau_col_temp:  Optional[str] = None
    air_col_date:  Optional[str] = None
    air_col_temp:  Optional[str] = None
    # Excel / en-tête décalé (renseignés par l'app selon le fichier)
    eau_nom_fichier:  str = ""            # nom original (détection extension)
    eau_feuille:      Optional[str] = None
    eau_ligne_entete: Optional[int] = None
    air_nom_fichier:  str = ""
    air_feuille:      Optional[str] = None
    air_ligne_entete: Optional[int] = None

    nom_cours_eau:      str = "Cours d'eau"
    localisation_sonde: str = ""
    nom_station_debit:  str = ""
    periode_normales:   str = "1991-2020"        # traçabilité (note §2.3)


# ============================================================
# 2. CONTRÔLE QUALITÉ (nettoyage souple des artefacts)
# ============================================================
@dataclass
class QCConfig:
    """
    Paramètres du contrôle qualité. Chaque détecteur est activable
    indépendamment ; les seuils sont réglables station par station.
    """
    # -- Bornes physiques --
    bornes_physiques: bool = True
    t_eau_min: float = -0.5     # °C (sous 0 : gel/erreur)
    t_eau_max: float = 35.0     # °C (au-dessus : capteur exposé)

    # -- Sonde hors d'eau (diagnostic type Heymonrupt) --
    hors_eau: bool = True
    hors_eau_ecart_seuil: float = 4.0            # °C (T_eau_max − T_air médian)
    hors_eau_mois: tuple = (6, 7, 8, 9)          # fenêtre de diagnostic (JJAS)
    hors_eau_min_jours: int = 5                  # nb min de jours suspects
    hors_eau_exclut_saison: bool = True          # exclut la saison JJAS entière

    # -- Plateau / sonde bloquée --
    plateau: bool = True
    plateau_fenetre: int = 7                     # jours
    plateau_ecart_type_min: float = 0.05         # °C (σ glissant sous ce seuil)

    # -- Outliers MAD --
    mad_outliers: bool = True
    mad_k: float = 50.0                          # seuil = k × MAD
    mad_mois: Optional[tuple] = None             # None = toute l'année

    def to_legacy_dict(self) -> dict:
        """Compat : dict au format attendu par l'ancien `controle_qualite`."""
        return {
            "bornes_physiques": self.bornes_physiques,
            "T_eau_min": self.t_eau_min, "T_eau_max": self.t_eau_max,
            "hors_eau": self.hors_eau,
            "hors_eau_ecart_seuil": self.hors_eau_ecart_seuil,
            "hors_eau_mois": list(self.hors_eau_mois),
            "hors_eau_min_jours": self.hors_eau_min_jours,
            "hors_eau_exclut_saison": self.hors_eau_exclut_saison,
            "plateau": self.plateau, "plateau_fenetre": self.plateau_fenetre,
            "plateau_ecart_type_min": self.plateau_ecart_type_min,
            "mad_outliers": self.mad_outliers, "mad_k": self.mad_k,
            "mad_mois": list(self.mad_mois) if self.mad_mois else None,
        }


# ============================================================
# 3. RÉFÉRENTIEL DES CONTEXTES PISCICOLES (note §2.5 et §2.7)
# ============================================================
# Paramètres fraie-croissance par espèce (note §2.7.2). Chaque espèce :
#   fenetre : mois de reproduction/incubation
#   mois_central : cœur d'incubation (critère de couverture, note §2.7.3)
#   opt : [Topt_min, Topt_max]  |  res : borne de résistance haute
#   T_fraie : T° de fraie de référence (garde-fou Rombough)
#   pente : sévérité de pénalisation ('forte' sténotherme, 'moderee', 'faible')
FRAIE_PARAMS = {
    "salmonicole": {
        "truite fario": dict(fenetre=[10, 11, 12], mois_central=11,
                             opt=[6, 8], elargie=[4, 10], res=10.0,
                             T_fraie=8.0, pente="forte",
                             src="Réalis-Doyelle & Teletchea 2016"),
    },
    "intermediaire": {
        "ombre commun": dict(fenetre=[3, 4, 5], mois_central=4,
                             opt=[6, 8], elargie=[6, 10], res=10.0,
                             T_fraie=8.0, pente="forte",
                             src="Rosenau 2025"),
    },
    "cyprinicole": {
        "brochet": dict(fenetre=[2, 3, 4], mois_central=3,
                        opt=[8, 14], elargie=[8, 15], res=22.0,
                        T_fraie=11.0, pente="faible",
                        src="Souchon & Tissot 2012 ; Réalis-Doyelle & Teletchea 2022"),
        "brème":   dict(fenetre=[5, 6], mois_central=6,
                        opt=[12, 21], elargie=[12, 23], res=23.0,
                        T_fraie=20.0, pente="moderee",
                        src="Souchon & Tissot 2012 ; Kucharczyk 2013"),
    },
}

CONTEXTES = {
    "salmonicole": {
        "label":     "Salmonicole (truite fario — espèce repère DCE)",
        "seuil_chr": 18, "seuil_aigu": 24,
        "fraie":     FRAIE_PARAMS["salmonicole"],
    },
    "intermediaire": {
        "label":     "Intermédiaire (ombre commun — espèce repère thermique)",
        "seuil_chr": 18, "seuil_aigu": 23,
        "fraie":     FRAIE_PARAMS["intermediaire"],
    },
    "cyprinicole": {
        "label":     "Cyprinicole (brème commune — espèce repère DCE)",
        "seuil_chr": 26, "seuil_aigu": 30,
        "fraie":     FRAIE_PARAMS["cyprinicole"],
    },
}


# ============================================================
# 4. CONSTANTES MÉTHODOLOGIQUES (note §2.7)
# ============================================================
# Pente de pénalisation par classe de sensibilité (°C⁻¹) — modulée par espèce.
PENTE_SEVERITE = {"forte": 0.60, "moderee": 0.35, "faible": 0.20}
FACTEUR_RESISTANCE = 2.0          # renfort au-delà de la borne de résistance
ROMBOUGH_DELTA = 6.0              # garde-fou ±6°C (sténothermes uniquement)
FRAIE_MIN_JOURS_CENTRAL = 10      # couverture min du mois central (note §2.7.3)

# Pondération fraie à 3 niveaux (score journalier de sévérité) :
#   - dans l'optimum strict           → 0 (pas de pénalité)
#   - fenêtre élargie (hors optimum)  → pénalité intermédiaire
#   - au-delà de l'élargie (létal)    → pénalité forte
# Côté froid, on plafonne à la pénalité intermédiaire (le froid ralentit
# l'incubation sans létalité massive ; la létalité forte est réservée au chaud).
FRAIE_SCORE_ELARGIE = 1.0         # palier intermédiaire (fenêtre élargie)
FRAIE_SCORE_LETAL   = 3.0         # palier fort (au-delà de l'élargie, côté chaud)
FRAIE_FROID_PLAFOND_INTERMEDIAIRE = True  # côté froid : max = intermédiaire

# Calibration fraie : conversion sévérité/létalité → classe (variante médiane).
# Seuils de sévérité moyenne (P0<[0] ; P1<[1] ; P2<[2] ; sinon P3)
FRAIE_SEUILS_SEV = (0.22, 1.05, 1.75)
# Seuils de % de temps en zone létale (plancher non dilutable)
FRAIE_SEUILS_LETAL = (2.0, 6.0, 15.0)


# --- Déclenchement du volet STRESS de Q_thermie_bio (note révisée) ---
# Le volet létal reste le déclencheur principal (fiable). Le volet stress
# chronique n'est calculé QUE si DEUX conditions cumulatives sont réunies :
#   (1) matérialité : le % de jours estivaux stressés dépasse un plancher ;
#   (2) causalité  : la relation débit→température est réellement négative
#       (corrélation Q↔Tmh < 0) et significative (R² ≥ seuil).
# Sinon, agir sur le débit ne réduirait pas le stress : volet désactivé.
STRESS_PLANCHER_PCT = 10.0        # plancher de matérialité (% jours stressés)
STRESS_CORR_R2_MIN = 0.10         # R² minimal de la relation Q↔Tmh
STRESS_CORR_SIGNE_NEG = True      # exiger une corrélation négative (physique)

# Pondérations du SGVT (note §2.6)
SGVT_POIDS_4 = dict(s=0.25, c=0.30, a=0.20, f=0.25)   # 4 composantes
SGVT_POIDS_3 = dict(s=0.30, c=0.40, a=0.30, f=None)   # repli 3 composantes


# ============================================================
# 5. CONFIG GLOBALE (agrège tout)
# ============================================================
@dataclass
class AnalyseConfig:
    """Configuration complète d'une analyse. Passée à l'orchestrateur."""
    sources: SourcesConfig = field(default_factory=SourcesConfig)
    qc:      QCConfig = field(default_factory=QCConfig)
    contexte_piscicole: str = "intermediaire"    # clé de CONTEXTES
    # Mode : "thermie_seule" (pas de débit) ou "thermie_debits"
    mode: str = "thermie_debits"
    faire_volet_climatique: bool = False
    output_dir: Optional[str] = None             # None = pas d'écriture disque
    # Seuil d'écart relatif médian sous lequel on comble les trous du
    # désinfluencé par l'influencé ; au-dessus, bascule tout en influencé.
    seuil_comblement_desinf: float = 0.10        # 10 % (note : paramétrable)
    normales_fenetre_lissage: int = 10           # ±N jours (lissage circulaire)
    normales_min_annees: int = 20                # seuil d'alerte sur 1991-2020
    # Déclenchement du volet stress de Q_thermie_bio (2 verrous cumulatifs)
    stress_plancher_pct: float = 10.0            # matérialité (% jours stressés)
    stress_corr_r2_min: float = 0.10             # causalité (R² min Q↔Tmh)

    def contexte(self) -> dict:
        if self.contexte_piscicole not in CONTEXTES:
            raise ValueError(
                f"Contexte inconnu : '{self.contexte_piscicole}'. "
                f"Possibles : {list(CONTEXTES.keys())}")
        return CONTEXTES[self.contexte_piscicole]

    @property
    def avec_debits(self) -> bool:
        """True si l'analyse doit produire les débits de référence."""
        return (self.mode == "thermie_debits"
                and self.sources.fichier_debit is not None)
