"""
parametres.py — ÉTAPE 2 : les deux chemins de paramètres, et leur provenance.

CE QUE CE MODULE RÈGLE
----------------------
L'étape 1 figeait le chemin `run_cli.py` + `QCConfig()` par défaut. Ce n'est
PAS le comportement de la version en service : l'application Streamlit
construit son `QCConfig` autrement. D14 (révisée) fait de la configuration de
l'APPLICATION la référence qui fait foi, et de celle de la CLI une référence
seconde, explicitement étiquetée.

LA DIVERGENCE, EN DEUX LIGNES
-----------------------------
`app.py:156` part bien de `QCConfig()`, puis ré-affecte chaque champ depuis un
widget. Deux widgets ne reprennent PAS la valeur du dataclass comme défaut :

    app.py:162-163  hors_eau_ecart_seuil -> slider de defaut LITTERAL 10.0
                    (le dataclass dit 4.0, config.py:81)
    app.py:166      hors_eau_exclut_saison -> checkbox de defaut LITTERAL False
                    (le dataclass dit True, config.py:84)

Tous les autres widgets passent `qc.<champ>` comme défaut et reproduisent donc
le dataclass. Le détecteur « hors d'eau » n'est pas coupé : il est ACTIF des
deux côtés, mais avec un seuil de 10 °C au lieu de 4 °C et sans exclusion de
saison.

PROVENANCE
----------
Chaque valeur porte l'une des trois étiquettes exigées :
    "code"      lue dans le code de ref/v4_5 (widget ou dataclass) ;
    "classeur"  lue dans le livrable déjà présent dans tests/reference/<jeu>/ ;
    "defaut"    choisie par défaut faute de trace, et le motif est écrit.

D73 — UNE TABLE PAR SOURCE DE CODE (étape 13)
----------------------------------------------
Ce module ne décrivait qu'un `QCConfig` : celui de `app/`. Il a suivi les
correctifs 1 (étape 10) et 6 (étape 11), qui ont ajouté sept champs et en ont
retiré trois. Conséquence, restée invisible deux étapes durant :
`THERMIE_CODE=ref` échouait sur les 32 points du corpus, sur

    TypeError: QCConfig.__init__() got an unexpected keyword argument 'k'

et `tests/reference/` — la référence qui fait foi — ne pouvait plus être
reproduite depuis la source qui l'a produite. Le harnais figeant chaque échec
comme référence (D7), le code de retour restait 0.

Il y a donc maintenant DEUX jeux de tables de contrôle qualité, indexés par la
source de code exécutée (`THERMIE_CODE`) :

    QC_REF_APPLICATION / QC_REF_CLI    le QCConfig de ref/v4_5 — 14 champs
    QC_APP_APPLICATION / QC_APP_CLI    le QCConfig de app/     — 18 champs

**La table `ref` est FIGÉE par construction.** D1 interdit d'écrire dans
`ref/`, donc le `QCConfig` qu'elle décrit ne bougera plus jamais : elle
s'écrit une fois et ne se maintient pas. Seule la table `app` suit les
correctifs.

Elle n'a pas été reconstituée de mémoire : elle est **lue dans les six
`10_parametres.json` de chaque référence**, qui portent la table qui a
réellement produit ces artefacts — valeur, provenance et justification
comprises. C'est la seule source qui ne puisse pas diverger de la référence,
puisqu'elle en fait partie. Le jeu de champs a été confronté au `QCConfig` de
`ref/v4_5/thermie_debits/config.py`, lu par AST.

`AnalyseConfig` et `SourcesConfig`, eux, n'ont pas bougé entre les deux
sources — 14 et 22 champs de part et d'autre, vérifié. Les tables `ANALYSE_*`
restent donc communes, et ce module ne les duplique pas : dupliquer ce qui ne
diverge pas fabrique deux vérités là où il n'y en a qu'une.
"""
from __future__ import annotations

from _commun import CODE

# ============================================================
# 1. Le contrôle qualité, tel que chaque chemin le construit
# ============================================================
# ------------------------------------------------------------------
# 1a. Le QCConfig de app/ — 18 champs. C'est cette table qui suit les
#     correctifs ; elle est la seule des quatre à évoluer.
# ------------------------------------------------------------------
QC_APP_APPLICATION = {
    "bornes_physiques": (True, "code", "app.py:157 — defaut = qc.bornes_physiques (config.py:75)"),
    "t_eau_min": (-0.5, "code", "app.py:159 — defaut = qc.t_eau_min (config.py:76)"),
    "t_eau_max": (35.0, "code", "app.py:160 — defaut = qc.t_eau_max (config.py:77)"),
    "hors_eau": (True, "code", "app.py:161 — defaut = qc.hors_eau (config.py:80)"),
    "hors_eau_mois": ((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), "code",
                      "non expose par l'interface — dataclass (config.py). "
                      "CORRECTIF 13 (D105) : l'annee entiere"),
    "k": (3.0, "code", "app.py — slider, defaut = qc.k (config.py). "
                       "CORRECTIF 1 : remplace hors_eau_ecart_seuil"),
    "m_domaine": ((0.0, 1.2), "code", "QCConfig — CORRECTIF 6, domaine deja applique par V4.5 au seul saisonnier"),
    "m_niveau_ic": (0.95, "code", "QCConfig — CORRECTIF 6, convention"),
    "plancher_dispersion": (0.05, "code", "app.py — defaut = qc.plancher_dispersion"),
    "min_jours_groupe": (10, "code", "app.py — defaut = qc.min_jours_groupe"),
    "min_jours_episode": (1, "code", "app.py — defaut = qc.min_jours_episode (D38)"),
    "q_ampl": (0.10, "code", "app.py — slider, defaut = qc.q_ampl"),
    "plateau": (True, "code", "app.py:167 — defaut = qc.plateau (config.py:87)"),
    "plateau_fenetre": (7, "code", "non expose — dataclass (config.py:88)"),
    "plateau_ecart_type_min": (0.05, "code", "non expose — dataclass (config.py:89)"),
    "mad_outliers": (True, "code", "app.py:168 — defaut = qc.mad_outliers (config.py:92)"),
    "mad_k": (50.0, "code", "app.py:169 — defaut = qc.mad_k (config.py:93)"),
    "mad_mois": (None, "code", "non expose — dataclass (config.py:94)"),
    "completude_facteur": (2.0, "code",
                           "non expose par l'interface — dataclass. "
                           "CORRECTIF 12 : departage sur pieces (D91)"),
}

QC_APP_CLI = {
    "bornes_physiques": (True, "code", "QCConfig() (config.py:75)"),
    "t_eau_min": (-0.5, "code", "QCConfig() (config.py:76)"),
    "t_eau_max": (35.0, "code", "QCConfig() (config.py:77)"),
    "hors_eau": (True, "code", "QCConfig() (config.py:80)"),
    "hors_eau_mois": ((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), "code",
                      "QCConfig() — CORRECTIF 13 (D105)"),
    "k": (3.0, "code", "QCConfig() — CORRECTIF 1"),
    "m_domaine": ((0.0, 1.2), "code", "QCConfig() — CORRECTIF 6"),
    "m_niveau_ic": (0.95, "code", "QCConfig() — CORRECTIF 6"),
    "plancher_dispersion": (0.05, "code", "QCConfig()"),
    "min_jours_groupe": (10, "code", "QCConfig()"),
    "min_jours_episode": (1, "code", "QCConfig() (D38)"),
    "q_ampl": (0.10, "code", "QCConfig()"),
    "plateau": (True, "code", "QCConfig() (config.py:87)"),
    "plateau_fenetre": (7, "code", "QCConfig() (config.py:88)"),
    "plateau_ecart_type_min": (0.05, "code", "QCConfig() (config.py:89)"),
    "mad_outliers": (True, "code", "QCConfig() (config.py:92)"),
    "mad_k": (50.0, "code", "QCConfig() (config.py:93)"),
    "mad_mois": (None, "code", "QCConfig() (config.py:94)"),
    "completude_facteur": (2.0, "code", "QCConfig() — CORRECTIF 12"),
}

# ============================================================
# 2. Le reste de AnalyseConfig
# ============================================================
ANALYSE_APPLICATION = {
    "faire_volet_climatique": (False, "code", "app.py:146 — checkbox, defaut False"),
    "seuil_comblement_desinf": (0.10, "code", "app.py:116 — 0.10 tant que la case « ajuster » reste decochee (app.py:118)"),
    "normales_fenetre_lissage": (10, "code", "app.py:105 — slider, defaut 10"),
    "normales_min_annees": (20, "code", "app.py:106 — number_input, defaut 20"),
    "normalisation_lissage_delta": (7, "code", "app.py:107-108 — slider, defaut 7"),
    "stress_plancher_pct": (10.0, "code", "app.py:135-136 — slider, defaut 10.0"),
    "stress_corr_r2_min": (0.10, "code", "app.py:139-140 — slider, defaut 0.10"),
    "periode_affichage": (None, "code", "app.py:199 — None tant qu'aucune fenetre n'est saisie"),
    "output_dir": (None, "code", "app.py:340 — output_dir=None, l'app n'ecrit rien sur disque"),
}

ANALYSE_CLI = {
    "faire_volet_climatique": (True, "code", "run_cli.py:20"),
    "seuil_comblement_desinf": (0.10, "code", "run_cli.py:20"),
    "normales_fenetre_lissage": (10, "code", "run_cli.py:21"),
    "normales_min_annees": (20, "code", "run_cli.py:21"),
    "normalisation_lissage_delta": (7, "code", "run_cli.py:22"),
    "stress_plancher_pct": (10.0, "code", "run_cli.py:23"),
    "stress_corr_r2_min": (0.10, "code", "run_cli.py:23"),
    "periode_affichage": (None, "code", "non renseigne par run_cli — dataclass (config.py:403)"),
    "output_dir": (None, "defaut",
                   "run_cli.py:24 ecrit dans examples/outputs/ ; le harnais force "
                   "None pour qu'aucune execution n'ecrive hors de tests/"),
}

# ============================================================
# 3. Le contexte piscicole, jeu par jeu
# ============================================================
# Lu dans la feuille « 00_Fiche station » du classeur livrable de chaque jeu.
# C'est la seule trace du choix fait par l'opérateur : ni le code, ni data/,
# ni corpus.csv ne le portent.
CONTEXTE_PAR_JEU = {
    "jeu_02": ("salmonicole", None, "classeur",
               "00_Fiche station : « Salmonicole (truite fario — espece repere DCE) »"),
    "jeu_03": ("salmonicole", None, "classeur",
               "00_Fiche station : « Salmonicole (truite fario — espece repere DCE) »"),
    "jeu_04": ("cyprinicole", None, "classeur",
               "00_Fiche station : « Cyprinicole (breme commune — espece repere DCE) »"),
    "jeu_05": ("intermediaire", "barbeau", "classeur",
               "00_Fiche station : « Intermediaire (barbeau commun — espece repere "
               "thermique) » — le libelle nomme l'espece, donc espece_repere='barbeau'"),
    "jeu_exemples_v45": ("salmonicole", None, "classeur",
                         "00_Fiche station : « Salmonicole (truite fario — espece repere DCE) »"),
    # jeu_bienne ne porte aucun classeur : rien n'atteste d'un choix.
    "jeu_bienne": ("intermediaire", None, "defaut",
                   "aucun classeur pour ce jeu, donc aucune trace du choix de "
                   "l'operateur. On retient le DEFAUT DE L'INTERFACE : selectbox "
                   "app.py:70-72 index=1 -> 'intermediaire', radio app.py:78-79 "
                   "index=0 -> 'ombre commun' (espece_repere=None y est "
                   "equivalent, config.py contexte():52). C'est aussi le defaut du "
                   "dataclass (config.py:AnalyseConfig.contexte_piscicole) et celui "
                   "de run_cli.py:16 : les deux chemins coincident ici"),
}

# ============================================================
# 4. Valeurs attendues, lues dans les classeurs (critère d'acceptation)
# ============================================================
# Feuille « 01_Donnees_QC » pour les effectifs, feuille « 02_Thermie_SGVT »
# pour m et R². Ce sont les cibles que la reconstruction doit retrouver.
ATTENDU_CLASSEUR = {
    "jeu_02": dict(journees_lues=1546, journees_ecartees_qc=1,
                   journees_propres=1545, journees_retenues=1215,
                   m=0.2928, r2=0.2059, n_ete=445, robustesse=0.2899,
                   sgvt=2.33, composantes=4),
    "jeu_03": dict(journees_lues=1164, journees_ecartees_qc=0,
                   journees_propres=1164, journees_retenues=1164,
                   m=0.4082, r2=0.5150, n_ete=477, robustesse=0.0380,
                   sgvt=2.50, composantes=4),
    "jeu_04": dict(journees_lues=855, journees_ecartees_qc=0,
                   journees_propres=855, journees_retenues=855,
                   m=0.2295, r2=0.2112, n_ete=347, robustesse=0.1832,
                   sgvt=3.17, composantes=4),
    "jeu_05": dict(journees_lues=1121, journees_ecartees_qc=0,
                   journees_propres=1121, journees_retenues=1121,
                   m=0.4422, r2=0.4959, n_ete=369, robustesse=0.0774,
                   sgvt=1.67, composantes=4),
    "jeu_exemples_v45": dict(journees_lues=303, journees_ecartees_qc=0,
                             journees_propres=303, journees_retenues=201,
                             m=0.5195, r2=0.8728, n_ete=122, robustesse=0.0454,
                             sgvt=3.67, composantes=3),
}


# ------------------------------------------------------------------
# 1b. Le QCConfig de ref/v4_5 — 14 champs. FIGE : D1 interdit d'ecrire
#     dans ref/, donc ce dataclass ne bougera plus. Table lue dans les
#     six 10_parametres.json de chaque reference, jamais reconstituee.
# ------------------------------------------------------------------
QC_REF_APPLICATION = {
    'bornes_physiques': (True, 'code',
                        'app.py:157 — defaut = qc.bornes_physiques (config.py:75)'),
    'hors_eau': (True, 'code',
                'app.py:161 — defaut = qc.hors_eau (config.py:80)'),
    'hors_eau_ecart_seuil': (10.0, 'code',
                            'app.py:162-163 — DEFAUT LITTERAL 10.0, et non qc.hors_eau_ecart_seuil = 4.0 (config.py:81). PREMIERE DIVERGENCE'),
    'hors_eau_exclut_saison': (False, 'code',
                              'app.py:166 — DEFAUT LITTERAL False, et non qc.hors_eau_exclut_saison = True (config.py:84). SECONDE DIVERGENCE'),
    'hors_eau_min_jours': (5, 'code',
                          'app.py:164-165 — defaut = qc.hors_eau_min_jours (config.py:83)'),
    'hors_eau_mois': ((6, 7, 8, 9), 'code',
                     "non expose par l'interface — dataclass (config.py:82)"),
    'mad_k': (50.0, 'code',
             'app.py:169 — defaut = qc.mad_k (config.py:93)'),
    'mad_mois': (None, 'code',
                'non expose — dataclass (config.py:94)'),
    'mad_outliers': (True, 'code',
                    'app.py:168 — defaut = qc.mad_outliers (config.py:92)'),
    'plateau': (True, 'code',
               'app.py:167 — defaut = qc.plateau (config.py:87)'),
    'plateau_ecart_type_min': (0.05, 'code',
                              'non expose — dataclass (config.py:89)'),
    'plateau_fenetre': (7, 'code',
                       'non expose — dataclass (config.py:88)'),
    't_eau_max': (35.0, 'code',
                 'app.py:160 — defaut = qc.t_eau_max (config.py:77)'),
    't_eau_min': (-0.5, 'code',
                 'app.py:159 — defaut = qc.t_eau_min (config.py:76)'),
}

QC_REF_CLI = {
    'bornes_physiques': (True, 'code',
                        'QCConfig() (config.py:75)'),
    'hors_eau': (True, 'code',
                'QCConfig() (config.py:80)'),
    'hors_eau_ecart_seuil': (4.0, 'code',
                            'QCConfig() (config.py:81)'),
    'hors_eau_exclut_saison': (True, 'code',
                              'QCConfig() (config.py:84)'),
    'hors_eau_min_jours': (5, 'code',
                          'QCConfig() (config.py:83)'),
    'hors_eau_mois': ((6, 7, 8, 9), 'code',
                     'QCConfig() (config.py:82)'),
    'mad_k': (50.0, 'code',
             'QCConfig() (config.py:93)'),
    'mad_mois': (None, 'code',
                'QCConfig() (config.py:94)'),
    'mad_outliers': (True, 'code',
                    'QCConfig() (config.py:92)'),
    'plateau': (True, 'code',
               'QCConfig() (config.py:87)'),
    'plateau_ecart_type_min': (0.05, 'code',
                              'QCConfig() (config.py:89)'),
    'plateau_fenetre': (7, 'code',
                       'QCConfig() (config.py:88)'),
    't_eau_max': (35.0, 'code',
                 'QCConfig() (config.py:77)'),
    't_eau_min': (-0.5, 'code',
                 'QCConfig() (config.py:76)'),
}


TABLES_QC = {
    ("ref", "application"): QC_REF_APPLICATION,
    ("ref", "cli"): QC_REF_CLI,
    ("app", "application"): QC_APP_APPLICATION,
    ("app", "cli"): QC_APP_CLI,
}


def jeu_de_parametres(chemin: str, jeu: str, source: str = None) -> dict:
    """
    Retourne {champ: (valeur, provenance, justification)} pour un jeu, un
    chemin ("application" ou "cli") et une SOURCE DE CODE ("ref" ou "app").

    D73 — `source` par défaut vaut `_commun.CODE`, c'est-à-dire la variable
    d'environnement `THERMIE_CODE`. Ce n'est pas un choix implicite : c'est le
    MÊME choix explicite que celui qui décide quel code est exécuté, et
    l'annoncer deux fois ferait deux endroits où il peut diverger. Un appelant
    qui veut une autre table la nomme.
    """
    source = (source or CODE).strip().lower()
    if source not in ("ref", "app"):
        raise ValueError(f"source doit valoir 'ref' ou 'app', pas {source!r}")
    if chemin not in ("application", "cli"):
        raise ValueError(f"chemin inconnu : {chemin!r}")
    qc = TABLES_QC[(source, chemin)]
    an = ANALYSE_APPLICATION if chemin == "application" else ANALYSE_CLI
    ctx, esp, prov_ctx, just_ctx = CONTEXTE_PAR_JEU[jeu]
    if chemin == "cli":
        ctx, esp = "intermediaire", None
        prov_ctx, just_ctx = "code", "run_cli.py:16-18"
    return {
        "qc": dict(qc),
        "analyse": dict(an),
        "contexte_piscicole": (ctx, prov_ctx, just_ctx),
        "espece_repere": (esp, prov_ctx, just_ctx),
    }
