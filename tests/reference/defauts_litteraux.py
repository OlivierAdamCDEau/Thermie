"""
defauts_litteraux.py — ÉTAPE 3, TÂCHE D (correctif 7, D22).

Revue de TOUS les widgets d'app.py qui alimentent un champ de AnalyseConfig,
SourcesConfig ou QCConfig. Pour chacun : la valeur par défaut est-elle DÉRIVÉE
du dataclass, ou écrite en LITTÉRAL dans l'appel au widget ?

Un littéral n'est pas fautif en soi ; il l'est parce qu'il rompt le lien. Le
jour où le dataclass change, le défaut de l'interface ne suit pas, et la
valeur documentée cesse d'être la valeur appliquée — sans qu'aucun test ne le
dise. Deux occurrences ont déjà divergé de cette façon.

ÉTAPE 13 — RELEVÉ REFAIT SUR L'ÉTAT ACTUEL
-------------------------------------------
Le relevé de l'étape 3 décrivait un `app.py` qui n'existe plus. Les DEUX
littéraux qui divergeaient du dataclass — `hors_eau_ecart_seuil` (10,0 contre
4,0) et `hors_eau_exclut_saison` (False contre True) — portaient sur des
champs que le correctif 1 (étape 10) puis D61 (étape 11) ont retirés de
`QCConfig`. ILS ONT DISPARU AVEC L'ANCIEN DÉTECTEUR, et non parce qu'on les
aurait corrigés : la divergence s'est éteinte d'elle-même.

Les widgets qui les remplacent — `k`, `plancher_dispersion`,
`min_jours_groupe`, `min_jours_episode`, `q_ampl` — prennent tous leur défaut
du dataclass. Le correctif 1 avait appliqué la règle du correctif 7 d'emblée à
ses widgets neufs.

Trois catégories :
    derive      le widget passe `qc.<champ>` ou `config.<champ>` en defaut ;
    litteral    le defaut est ecrit en dur dans l'appel ;
    detecte     le defaut vient d'une detection sur le fichier (sniff, station
                d'air) et non du dataclass — legitime, mais a nommer.

Sortie : out/etape3/defauts_litteraux.csv
"""
from __future__ import annotations

import dataclasses
import sys
from dataclasses import fields

from _commun import RACINE, ecrire_csv

from thermie_debits.config import (AnalyseConfig, SourcesConfig, QCConfig,
                                   CONTEXTES, especes_disponibles)

OUT = RACINE / "out" / "etape3"

# (champ, bloc, ligne, categorie, valeur_ecrite, commentaire)
# Relevé exhaustif fait à la main sur app.py, widget par widget, puis confronté
# aux défauts du dataclass par le code ci-dessous.
WIDGETS = [
    # ---- AnalyseConfig — CORRECTIF 7 pose a l'etape 13 -------------------
    ("contexte_piscicole", "AnalyseConfig", "app.py:89-92", "derive",
     "list(CONTEXTES).index(_DEFAUTS.contexte_piscicole)",
     "le defaut par POSITION est devenu un defaut par VALEUR : l'index se "
     "calcule depuis le dataclass. Reordonner CONTEXTES ne change plus rien"),
    ("espece_repere", "AnalyseConfig", "app.py:101-105", "derive",
     "_especes.index(CONTEXTES[k]['espece_defaut'])",
     "le dataclass dit None, qui RESOUT vers espece_defaut : c'est cette "
     "resolution qu'on indexe, et non la position 0"),
    ("mode", "AnalyseConfig", "app.py:121-125", "derive",
     "_MODES.index(_DEFAUTS.mode)",
     "les options sont nommees pour que le defaut s'y indexe"),
    ("normales_fenetre_lissage", "AnalyseConfig", "app.py:131-132", "derive",
     "_DEFAUTS.normales_fenetre_lissage", ""),
    ("normales_min_annees", "AnalyseConfig", "app.py:133-134", "derive",
     "_DEFAUTS.normales_min_annees", ""),
    ("normalisation_lissage_delta", "AnalyseConfig", "app.py:135-137", "derive",
     "_DEFAUTS.normalisation_lissage_delta", ""),
    ("seuil_comblement_desinf", "AnalyseConfig", "app.py:145", "derive",
     "_DEFAUTS.seuil_comblement_desinf",
     "l'affectation directe ET le slider app.py:158-160 derivent tous deux"),
    ("stress_plancher_pct", "AnalyseConfig", "app.py:165-166", "derive",
     "_DEFAUTS.stress_plancher_pct",
     "le slider ET le repli app.py:174 derivent tous deux"),
    ("stress_corr_r2_min", "AnalyseConfig", "app.py:169-170", "derive",
     "_DEFAUTS.stress_corr_r2_min",
     "le slider ET le repli app.py:175 derivent tous deux"),
    ("faire_volet_climatique", "AnalyseConfig", "app.py:177-178", "derive",
     "_DEFAUTS.faire_volet_climatique", ""),
    ("periode_affichage", "AnalyseConfig", "app.py:251-253", "derive",
     "_DEFAUTS.periode_affichage is not None",
     "la case est cochee si et seulement si le dataclass porte une fenetre"),
    ("output_dir", "AnalyseConfig", "app.py:403", "litteral",
     "None",
     "INVARIANT DECLARE, et non un defaut : l'application n'ecrit jamais sur "
     "disque. Le deriver la ferait ecrire le jour ou le dataclass porterait "
     "un chemin. Argument de construction, hors widget : D22 vise les defauts "
     "d'interface"),

    # ---- SourcesConfig ---------------------------------------------------
    ("nom_cours_eau", "SourcesConfig", "app.py:181", "derive",
     "_SOURCES.nom_cours_eau", ""),
    ("localisation_sonde", "SourcesConfig", "app.py:182-183", "derive",
     "_SOURCES.localisation_sonde", ""),
    ("nom_station_debit", "SourcesConfig", "app.py:184-185", "derive",
     "_SOURCES.nom_station_debit", ""),
    ("nom_station_meteo", "SourcesConfig", "app.py:186-187", "derive",
     "_SOURCES.nom_station_meteo", ""),
    ("fichier_normales", "SourcesConfig", "app.py:378", "litteral",
     "None",
     "INVARIANT DECLARE : le chemin application calcule toujours ses normales "
     "depuis l'air brut. Argument de construction, hors widget. La branche "
     "EcartNormales pre-calcule reste atteignable par la CLI, et AUCUN jeu du "
     "corpus ne l'exerce — signale (5.5), non corrige"),

    # ---- SourcesConfig : defauts DETECTES sur le fichier ------------------
    ("eau_feuille", "SourcesConfig", "app.py:279", "detecte",
     "1re feuille du classeur",
     "selectbox sans index -> position 0. lire_brut retient deja feuilles[0] "
     "quand feuille vaut None : meme resultat"),
    ("air_feuille", "SourcesConfig", "app.py:330", "detecte",
     "1re feuille du classeur", "idem"),
    ("eau_ligne_entete", "SourcesConfig", "app.py:286-287", "detecte",
     "ligne d'en-tete detectee par sniff",
     "st.number_input(..., int(_meta['ligne_entete'])). Le dataclass dit "
     "None ; l'interface transmet un ENTIER egal a la detection"),
    ("air_ligne_entete", "SourcesConfig", "app.py:333", "detecte",
     "ligne d'en-tete detectee par sniff", "idem"),
    ("eau_col_date", "SourcesConfig", "app.py:294-295", "detecte",
     "proposition de deviner_colonnes, ou 'auto' -> None", ""),
    ("eau_col_temp", "SourcesConfig", "app.py:296-297", "detecte",
     "proposition de deviner_colonnes, ou 'auto' -> None", ""),
    ("air_col_date", "SourcesConfig", "app.py:337-338", "detecte",
     "colonne AAAAMMJJ si presente, sinon 'auto' -> None", ""),
    ("air_col_temp", "SourcesConfig", "app.py:339-340", "detecte",
     "colonne TM si presente, sinon 'auto' -> None", ""),
    ("air_station_code", "SourcesConfig", "app.py:317-325", "detecte",
     "station la mieux couverte",
     "selectbox sans index -> position 0 de stations_air(), deja triee par "
     "couverture"),

    # ---- QCConfig : deja derive depuis le correctif 1 ---------------------
    ("bornes_physiques", "QCConfig", "app.py:192", "derive", "qc.bornes_physiques", ""),
    ("t_eau_min", "QCConfig", "app.py:194", "derive", "value=qc.t_eau_min", ""),
    ("t_eau_max", "QCConfig", "app.py:195", "derive", "value=qc.t_eau_max", ""),
    ("hors_eau", "QCConfig", "app.py:196", "derive", "qc.hors_eau", ""),
    ("k", "QCConfig", "app.py:201", "derive", "qc.k",
     "CORRECTIF 1 — remplace hors_eau_ecart_seuil, occurrence divergente n.1 "
     "de l'etape 3"),
    ("plancher_dispersion", "QCConfig", "app.py:205-206", "derive",
     "value=qc.plancher_dispersion", ""),
    ("min_jours_groupe", "QCConfig", "app.py:208-209", "derive",
     "value=qc.min_jours_groupe", ""),
    ("min_jours_episode", "QCConfig", "app.py:211-212", "derive",
     "value=qc.min_jours_episode", ""),
    ("q_ampl", "QCConfig", "app.py:215-216", "derive", "qc.q_ampl", ""),
    ("plateau", "QCConfig", "app.py:220", "derive", "qc.plateau", ""),
    ("mad_outliers", "QCConfig", "app.py:221", "derive", "qc.mad_outliers", ""),
    ("mad_k", "QCConfig", "app.py:222", "derive", "qc.mad_k", ""),
]

# Champs de QCConfig qu'aucun widget n'expose : ils gardent le dataclass.
NON_EXPOSES = {
    "QCConfig": ["hors_eau_mois", "plateau_fenetre", "plateau_ecart_type_min",
                 "mad_mois", "m_domaine", "m_niveau_ic"],
    "SourcesConfig": ["fichier_eau", "fichier_air", "fichier_debit",
                      "fichier_debit_desinf", "air_station_nom",
                      "eau_nom_fichier", "air_nom_fichier", "periode_normales"],
    "AnalyseConfig": ["sources", "qc"],
}

BLOCS = {"AnalyseConfig": AnalyseConfig, "SourcesConfig": SourcesConfig,
         "QCConfig": QCConfig}

# Ce qu'un écart de ce champ peut changer dans la chaîne lecture -> T_norm.
EFFET = {
    "k": "OUI — seuil du detecteur relatif, donc les journees retenues, "
         "donc m et T_norm",
    "plancher_dispersion": "OUI — decide quand le detecteur s'abstient",
    "min_jours_groupe": "OUI — effectif minimal d'un groupe mensuel",
    "min_jours_episode": "OUI — longueur minimale d'un episode marque",
    "q_ampl": "OUI — garde-fou d'amplitude d'air de la marche 2",
    "m_domaine": "OUI — domaine de validite de la pente (correctif 6)",
    "m_niveau_ic": "OUI — niveau de l'intervalle de confiance (correctif 6)",
    "normales_fenetre_lissage": "oui en principe — largeur du lissage des "
                                "normales, donc Delta_TMm",
    "normalisation_lissage_delta": "oui en principe — largeur du lissage de "
                                   "l'anomalie, donc T_norm",
    "normales_min_annees": "non — seuil d'avertissement seul (io_data.py:524), "
                           "aucune exclusion",
    "contexte_piscicole": "en aval de T_norm, sauf pour Tmh_norm_fraie",
    "espece_repere": "en aval de T_norm, sauf pour Tmh_norm_fraie",
    "mode": "hors perimetre — n'active que le volet debits",
    "seuil_comblement_desinf": "hors perimetre — comblement du desinfluence",
    "stress_plancher_pct": "hors perimetre — declenchement du volet stress",
    "stress_corr_r2_min": "hors perimetre — declenchement du volet stress",
    "faire_volet_climatique": "non — ne produit que des figures",
    "periode_affichage": "non — n'agit que sur l'axe des figures",
    "output_dir": "non — ne pilote que l'ecriture de fichiers",
    "fichier_normales": "oui en principe — bascule vers la branche "
                        "EcartNormales pre-calcule (orchestrator.py:96)",
    "eau_ligne_entete": "oui en principe — ligne d'en-tete retenue a la lecture",
    "air_ligne_entete": "oui en principe — idem",
    "eau_col_date": "oui en principe — colonne de date retenue",
    "eau_col_temp": "oui en principe — colonne de temperature retenue",
    "air_col_date": "oui en principe — colonne de date retenue",
    "air_col_temp": "oui en principe — colonne de temperature retenue",
    "eau_feuille": "oui en principe — feuille Excel retenue",
    "air_feuille": "oui en principe — feuille Excel retenue",
    "air_station_code": "oui en principe — station d'air retenue",
}


def _defaut_dataclass(bloc, champ):
    for f in fields(BLOCS[bloc]):
        if f.name == champ:
            if f.default is not dataclasses.MISSING:
                return f.default
            return "(factory)"
    return "(champ inconnu)"


def _valeur_effective(champ, ecrite):
    """Valeur que l'interface applique réellement, pour les défauts par index."""
    if champ == "contexte_piscicole":
        return list(CONTEXTES)[1]
    if champ == "espece_repere":
        # Comparaison APRES resolution : le dataclass dit None, mais None
        # resout vers base["espece_defaut"] (config.py, contexte():52). Comparer
        # 'ombre commun' a None ferait un faux ecart.
        return CONTEXTES[list(CONTEXTES)[1]].get("espece_defaut")
    if champ == "mode":
        return "thermie_debits"
    if ecrite == "False -> None":
        return None
    if ecrite in ("None", "False", "''"):
        return {"None": None, "False": False, "''": ""}[ecrite]
    if ecrite == "\"Cours d'eau\"":
        return "Cours d'eau"
    try:
        return eval(ecrite, {}, {})            # 10.0, 7, 0.10, 20...
    except Exception:
        return ecrite


COLS = ["bloc", "champ", "ligne", "categorie", "valeur_par_defaut_de_l_interface",
        "valeur_du_dataclass", "coincidence", "effet_si_les_deux_divergent",
        "commentaire"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lignes = []
    for champ, bloc, ligne, cat, ecrite, com in WIDGETS:
        dflt = _defaut_dataclass(bloc, champ)
        if cat == "derive":
            coincidence = "par construction — le widget LIT le dataclass"
        elif cat == "detecte":
            coincidence = ("sans objet — le defaut vient du fichier, pas du "
                           "dataclass")
        else:
            eff = _valeur_effective(champ, ecrite)
            if champ == "espece_repere":
                coincidence = ("identique apres resolution de None"
                               if eff == CONTEXTES[list(CONTEXTES)[1]]
                               .get("espece_defaut")
                               else f"DIVERGENT ({eff!r})")
            else:
                coincidence = ("identique" if eff == dflt
                               else f"DIVERGENT ({eff!r} != {dflt!r})")
        lignes.append(dict(
            bloc=bloc, champ=champ, ligne=ligne, categorie=cat,
            valeur_par_defaut_de_l_interface=ecrite,
            valeur_du_dataclass=repr(dflt), coincidence=coincidence,
            effet_si_les_deux_divergent=EFFET.get(champ, ""),
            commentaire=com))

    for bloc, champs in NON_EXPOSES.items():
        for champ in champs:
            lignes.append(dict(
                bloc=bloc, champ=champ, ligne="non expose",
                categorie="non expose",
                valeur_par_defaut_de_l_interface="(aucun widget)",
                valeur_du_dataclass=repr(_defaut_dataclass(bloc, champ)),
                coincidence="par construction — le dataclass s'applique",
                effet_si_les_deux_divergent="", commentaire=""))

    ecrire_csv(OUT / "defauts_litteraux.csv", COLS, lignes,
               tri=["bloc", "champ"])

    litt = [l for l in lignes if l["categorie"] == "litteral"]
    div = [l for l in litt if l["coincidence"].startswith("DIVERGENT")]
    print(f"defauts_litteraux.csv : {len(lignes)} champs")
    print(f"   derives du dataclass : "
          f"{sum(1 for l in lignes if l['categorie'] == 'derive')}")
    print(f"   LITTERAUX            : {len(litt)}, dont {len(div)} divergents")
    print(f"   detectes sur fichier : "
          f"{sum(1 for l in lignes if l['categorie'] == 'detecte')}")
    print(f"   non exposes          : "
          f"{sum(1 for l in lignes if l['categorie'] == 'non expose')}")
    print()
    for l in litt:
        marque = "  ***" if l["coincidence"].startswith("DIVERGENT") else "     "
        print(f"{marque} {l['ligne']:<16} {l['champ']:<28} "
              f"interface={l['valeur_par_defaut_de_l_interface']:<32} "
              f"dataclass={l['valeur_du_dataclass']:<20} {l['coincidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
