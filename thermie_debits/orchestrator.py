"""
orchestrator.py — Enchaînement de l'analyse (package thermie_debits).

Point d'entrée unique appelé par la CLI (run_cli.py) et par l'app Streamlit.
Prend une AnalyseConfig, exécute la chaîne selon le mode, et retourne un
objet Resultats structuré (dataclass) — sans dépendre de l'affichage.

Deux modes (config.mode) :
  - "thermie_seule"  : QC → sensibilité → vulnérabilité → fraie → SGVT
  - "thermie_debits" : idem + débits de référence (si fichier débit fourni)

Le SGVT est toujours produit (il ne dépend jamais du débit). Les débits,
eux, dépendent du SGVT (modulation α_fonc).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path

from .config import AnalyseConfig
from . import io_data as io
from . import qc as qcmod
from . import core
from . import figures as figmod
from . import exports as expmod
from . import climatique as climmod


@dataclass
class Resultats:
    """Conteneur de tous les résultats d'une analyse (pour CLI et app)."""
    config: AnalyseConfig
    contexte: dict
    # données
    daily_eau_brut: Any = None
    sub_eau: Any = None
    indicateurs: Any = None
    relation_debit_temp: Any = None
    matrice: Any = None
    df_air: Any = None
    df: Any = None
    rapport_qc: Any = None
    # D57 — le rapport des journees ecartees, augmente des valeurs de
    # diagnostic du detecteur. Destine au PERIMETRE : le harnais et l'ecran.
    # `rapport_qc` reste la vue heritee, inchangee.
    rapport_qc_detaille: Any = None
    # CORRECTIF 5 — la table de marquage de la fusion. Chaque journee d'eau
    # retenue par le controle qualite y subsiste, exploitable ou non. C'est ce
    # qui permet a l'ecran de declarer la degradation au lieu de la taire.
    marques_fusion: Any = None
    # CORRECTIF 10 — la table des mesures que la LECTURE ecarte, une ligne par
    # mesure, avec sa cause distinguee. Un cran plus bas que `marques_fusion`,
    # qui travaille a la journee : ici on est encore a la mesure.
    marques_lecture: Any = None
    # CORRECTIF 12 — la table de completude de journee. Chaque journee
    # observee y figure avec son trou maximal, son statut et son motif.
    # AUCUNE journee n'en sort : c'est un marquage, pas un filtre.
    marques_completude: Any = None
    # D48 — ce que les detecteurs du controle qualite ont fait, qu'ils aient
    # trouve quelque chose ou non. Sans lui, un jeu sans journee ecartee ne
    # porte aucune trace du detecteur, et l'ecran ne peut pas distinguer
    # « rien a signaler » de « controle non execute ».
    diag_detecteur: dict = field(default_factory=dict)
    diag_debit: dict = field(default_factory=dict)
    diag_normales: dict = field(default_factory=dict)
    diag_air_station: dict = field(default_factory=dict)
    # résultats de calcul
    sensibilite: Any = None
    vulnerabilite: Any = None
    fraie: Any = None
    sgvt: Any = None
    debits_inflexion: Any = None
    debits_reference: Any = None
    debits_sorties: dict = field(default_factory=dict)
    df_q_all: Any = None
    # figures (objets matplotlib, clé -> Figure)
    figures: dict = field(default_factory=dict)
    figures_climatiques: list = field(default_factory=list)
    # métadonnées
    base_debit: str = "aucune"
    avertissements: list = field(default_factory=list)

    @property
    def entete_base_debit(self) -> str:
        """Indicateur global de traçabilité (note : décisions projet)."""
        return self.diag_debit.get("message", "Aucun débit chargé.")


def run(config: AnalyseConfig, verbose: bool = True) -> Resultats:
    """Exécute l'analyse complète et retourne les résultats."""
    ctx = config.contexte()
    out = config.output_dir
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        # Les chemins de sortie sont construits par concaténation : on garantit
        # le séparateur final, sinon un output_dir sans "/" préfixe les noms de
        # fichiers au lieu de les ranger dans le dossier.
        out = str(Path(out)) + "/"
    nom = config.sources.nom_cours_eau
    res = Resultats(config=config, contexte=ctx)

    # ---- 1. Chargement ----
    if verbose: print(f"\n{'='*60}\n  {nom} — {ctx['label']}\n  Mode : {config.mode}\n{'='*60}")
    # CORRECTIF 10 (D60) — `marquer_lecture` rend la meme chronique que
    # `charger_eau` rendait, PLUS la table des mesures que la lecture ecarte.
    # La chronique, elle, est inchangee.
    daily_eau, sub_eau, marques_lecture = io.marquer_lecture(
        config.sources.fichier_eau,
        col_date=config.sources.eau_col_date,
        col_temp=config.sources.eau_col_temp,
        nom=config.sources.eau_nom_fichier,
        feuille=config.sources.eau_feuille,
        ligne_entete=config.sources.eau_ligne_entete,
        retour_sous_quotidien=True)
    res.daily_eau_brut = daily_eau
    res.sub_eau = sub_eau
    res.marques_lecture = marques_lecture
    # CORRECTIF 12 (D86, D89) — le marquage vit dans une table SEPAREE et
    # n'entre pas dans `daily_eau` : le faire remonterait jusqu'a `res.df` par
    # la fusion, et changerait les colonnes que le harnais publie pour une
    # raison sans rapport avec ce correctif.
    res.marques_completude = io.marquer_completude(
        sub_eau, daily=daily_eau, facteur=config.qc.completude_facteur,
        verbose=verbose)
    if verbose and len(marques_lecture):
        print(f"  {len(marques_lecture)} mesure(s) ecartee(s) a la lecture "
              f"(date ou temperature illisible)")

    # Air : nouvelle logique (air brut → normales + écarts calculés), avec
    # repli sur l'ancien EcartNormales pré-calculé si fourni (compatibilité).
    if config.sources.fichier_normales:
        df_air = io.charger_air(config.sources.fichier_air)
        ecart, normales = io.charger_normales(config.sources.fichier_normales)
        res.diag_normales = dict(source="pré-calculé (EcartNormales)")
    else:
        df_air = io.charger_air_brut(config.sources.fichier_air,
                                     col_date=config.sources.air_col_date,
                                     col_temp=config.sources.air_col_temp,
                                     station_code=config.sources.air_station_code,
                                     station_nom=config.sources.air_station_nom,
                                     nom_fichier=config.sources.air_nom_fichier)
        if df_air.attrs.get("station"):
            res.diag_air_station = df_air.attrs["station"]
        ecart, normales, diag_norm = io.calculer_normales_ecarts(
            df_air, fenetre_lissage=config.normales_fenetre_lissage,
            min_annees=config.normales_min_annees, verbose=verbose)
        res.diag_normales = diag_norm
        for av in diag_norm.get("avertissements", []):
            res.avertissements.append(av)
    res.df_air = df_air

    # ---- 2. Débits (selon mode) ----
    df_debits = None
    if config.avec_debits:
        df_debits, diag = io.fusionner_debits(
            config.sources.fichier_debit, config.sources.fichier_debit_desinf,
            seuil_comblement=config.seuil_comblement_desinf, verbose=verbose)
        res.diag_debit = diag
        res.base_debit = diag["base"]
        if diag.get("desinfluence_disponible") and not diag.get("comble"):
            ej = diag.get("ecart_jjas")
            ea = diag.get("ecart_annuel")
            if ej is not None and ej == ej:
                res.avertissements.append(
                    f"Débit désinfluencé disponible mais ses trous n'ont pas "
                    f"été comblés par l'influencé (écart médian JJAS "
                    f"{ej*100:.1f}% ≥ seuil {diag['seuil_comblement']*100:.0f}%) "
                    f"— sa distribution reste donc partielle pour la lecture "
                    f"PNDA.")
            elif ea is not None and ea == ea:
                res.avertissements.append(
                    f"Débit désinfluencé disponible mais ses trous n'ont pas "
                    f"été comblés par l'influencé (pas assez de jours communs "
                    f"en JJAS pour évaluer cet écart ; écart médian annuel "
                    f"{ea*100:.1f}% ≥ seuil {diag['seuil_comblement']*100:.0f}%) "
                    f"— sa distribution reste donc partielle pour la lecture "
                    f"PNDA.")
            else:
                res.avertissements.append(
                    "Débit désinfluencé disponible mais son écart avec "
                    "l'influencé n'a pas pu être évalué (trop peu de jours "
                    "communs, annuel comme JJAS) — ses trous n'ont donc pas "
                    "été comblés et sa distribution reste partielle pour la "
                    "lecture PNDA.")
    else:
        res.diag_debit = dict(base="aucune",
                              message="Mode thermie seule — pas de débits de référence.")

    # ---- 3. Contrôle qualité ----
    if verbose: print("\nContrôle qualité...")
    res.diag_detecteur = {}
    _marques_qc = qcmod.marquer_qualite(
        daily_eau, df_air, config.qc.to_legacy_dict(), verbose=verbose,
        diag=res.diag_detecteur)
    propre = qcmod.vue_retenue(_marques_qc)
    rapport = qcmod.rapport_ecartes(_marques_qc)
    res.rapport_qc = rapport
    res.rapport_qc_detaille = qcmod.rapport_ecartes_detaille(_marques_qc)

    # ---- 4. Fusion + normalisation ----
    # CORRECTIF 5 — `fusionner_marque` rend la meme chronique exploitable que
    # `fusionner` rendait, PLUS la table des journees que la fusion n'a pas pu
    # exploiter. La chronique, elle, est inchangee.
    df, marques = core.fusionner_marque(
        propre, df_air, ecart, normales, df_debits=df_debits,
        lissage_delta=getattr(config, 'normalisation_lissage_delta', 7))
    res.df = df
    res.marques_fusion = marques

    # ---- 5. Chaîne de calcul thermique ----
    if verbose: print("\nÉtape 1 — Sensibilité...")
    sens = core.analyse_sensibilite(df); res.sensibilite = sens
    if verbose: print(f"  m={sens['m']:.3f} ({sens['sens_cat']})")

    if verbose: print("\nÉtape 2 — Vulnérabilité...")
    vul = core.analyse_vulnerabilite(df, sens["m"], ctx, config.contexte_piscicole)
    res.vulnerabilite = vul

    if verbose: print("\nÉtape 2bis — Fraie-croissance...")
    fraie = core.analyse_fraie_croissance(df, sens["m"], ctx,
                                          config.contexte_piscicole, verbose=verbose)
    res.fraie = fraie

    if verbose: print("\nÉtape 3 — SGVT...")
    sgvt = core.calcul_sgvt(sens, vul, fraie); res.sgvt = sgvt
    if verbose: print(f"  SGVT = {sgvt['sgvt']:.2f}/10 ({sgvt['composantes']} comp.) → {sgvt['interp']}")

    # ---- 6. Figures thermiques (toujours) ----
    F = res.figures
    F["chronique"]     = figmod.fig_chronique(df, nom, out, periode=config.periode_affichage)
    F["qc"]            = figmod.fig_qc(daily_eau, rapport, df_air, nom, out, periode=config.periode_affichage)
    F["sensibilite"]   = figmod.fig_sensibilite(sens, nom, out)
    F["vulnerabilite"] = figmod.fig_vulnerabilite(vul, ctx, nom, out, periode=config.periode_affichage)
    if fraie:
        F["fraie"]     = figmod.fig_fraie_croissance(fraie, ctx, nom, out, periode=config.periode_affichage)
    F["synthese_tableau"] = figmod.fig_synthese_tableau(sens, vul, sgvt, ctx, nom, out)
    F["synthese_jauge"]   = figmod.fig_synthese_jauge(sgvt, nom, out)

    # ---- 6bis. Indicateurs bruts + corrélations ----
    from . import indicateurs as indmod
    res.indicateurs = indmod.calcul_indicateurs(df, sub_eau, verbose=verbose)
    F["correlations"] = figmod.fig_correlations_indicateurs(
        res.indicateurs["correlations"], nom, out)
    F["indicateurs_resume"] = figmod.fig_indicateurs_resume(
        res.indicateurs["table_mensuelle"], nom, out)

    # ---- 6ter. Test PRÉALABLE : le débit module-t-il la température ? ----
    # Postulat fondateur de toute l'approche « débits thermiques ». Le verdict
    # est informatif : il n'interrompt aucun calcul, mais une réserve est
    # affichée en aval si la relation n'est pas établie.
    if config.avec_debits:
        res.relation_debit_temp = core.analyse_relation_debit_temperature(
            df, r2_min=getattr(config, "stress_corr_r2_min", 0.10),
            verbose=verbose)
        F["relation_debit_temp"] = figmod.fig_relation_debit_temperature(
            res.relation_debit_temp, nom, out)
        rdt = res.relation_debit_temp
        if rdt.get("disponible") and rdt.get("verdict") in ("faible", "absente",
                                                            "inversee"):
            res.avertissements.append(
                f"Relation débit–température : {rdt['libelle'].lower()}. "
                f"{rdt['commentaire']}")

        # Matrice de lecture : « problème thermique » × « levier débit »
        res.matrice = core.matrice_diagnostic(
            vul, rdt, plancher_stress=getattr(config, "stress_plancher_pct", None))
        F["matrice"] = figmod.fig_matrice_diagnostic(res.matrice, nom, out)
        if verbose:
            print(f"  Diagnostic d'ensemble : {res.matrice['libelle']}")

    # ---- 7. Débits de référence (si mode + fichier) ----
    if config.avec_debits:
        if verbose: print("\nÉtape 4 — Débits de référence...")
        dinf = core.analyse_debits_inflexion(
            df, sens, ctx, config.contexte_piscicole,
            stress_plancher_pct=getattr(config, "stress_plancher_pct", None),
            stress_corr_r2_min=getattr(config, "stress_corr_r2_min", None),
            relation=res.relation_debit_temp)
        res.debits_inflexion = dinf
        if dinf and dinf.get("valide"):
            q_vuln = dinf.get("q_vuln") if dinf.get("q_vuln_valide") else None
            cst = core.calcul_debits_thermie(
                sgvt["sgvt"], q_stat=dinf["q_aicc"], q_marquee=dinf["q_seuil"],
                q_seuil_vuln=q_vuln, df=df)
            res.debits_reference = cst

            # Charger les DEUX distributions disponibles pour les PNDA — et
            # pour la figure, qui montre désormais les deux courbes quand le
            # désinfluencé est disponible (plutôt qu'une seule « base »).
            q_inf_series = q_des_series = None
            if config.sources.fichier_debit:
                q_inf_series = io.charger_debit(config.sources.fichier_debit)["Q"]
            if config.sources.fichier_debit_desinf:
                q_des_series = io.charger_debit(config.sources.fichier_debit_desinf)["Q"]
            # df_q_all = distribution d'analyse (toujours l'influencé).
            res.df_q_all = io.charger_debit(config.sources.fichier_debit)

            # Sorties : chaque débit de référence exprimé (valeur brute unique)
            # avec son PNDA sur chaque courbe (désinfluencé prioritaire).
            res.debits_sorties = dict(
                base_calcul=res.base_debit,
                desinfluence_disponible=(q_des_series is not None),
                q_thermie_bio=core.pnda_multi_base(
                    cst.get("q_thermie_bio"), q_inf_series, q_des_series),
                q_thermie_fonc=core.pnda_multi_base(
                    cst.get("q_thermie_fonc"), q_inf_series, q_des_series),
            )

            F["debits_inflexion"] = figmod.fig_debits_inflexion(
                dinf, sens, ctx, nom, out, q_fonc=cst["q_thermie_fonc"])
            F["debits_vuln"] = figmod.fig_vulnerabilite_debit(
                dinf, ctx, nom, out, q_bio_final=cst["q_thermie_bio"])
            F["debits_classes"] = figmod.fig_debits_classes(
                cst, dinf, q_inf_series, ctx, nom, out, q_desinf=q_des_series)
        elif dinf:
            F["debits_inflexion"] = figmod.fig_debits_inflexion(dinf, sens, ctx, nom, out)

    # ---- 8. Exports (mode CLI uniquement) ----
    if out:
        expmod.exporter_base(df, out)
        expmod.exporter_rapport_qc(rapport, out)
        expmod.exporter_synthese_xlsx(
            sens, vul, sgvt, ctx, nom, config.sources.localisation_sonde, out,
            debit_res=res.debits_inflexion, cst_res=res.debits_reference,
            df_q_all=res.df_q_all, base=res.base_debit)
        expmod.exporter_fraie_xlsx(fraie, nom, out)

    # ---- 9. Volet climatique (bonus) ----
    if config.faire_volet_climatique:
        res.figures_climatiques = climmod.volet_climatique(
            daily_eau, df_air, df, ctx, nom, out,
            fichier_debit=config.sources.fichier_debit)

    if verbose:
        print(f"\n{'='*60}\nANALYSE TERMINÉE" +
              (f" — sorties : {out}" if out else " (mode app, pas d'écriture)") +
              f"\n{'='*60}")
    return res
