"""
redaction.py — Textes d'interprétation (package thermie_debits).

SOURCE UNIQUE des formulations interprétatives (robustesse, verdicts,
conclusions, mises en garde) consommées à la fois par l'application
Streamlit et par les livrables docx/xlsx. Toute évolution de formulation se
propage ainsi partout, sans risque de divergence entre ce que l'utilisateur
lit à l'écran et ce que reçoit le destinataire du rapport.

Chaque fonction retourne soit une chaîne, soit un dict structuré
(titre / verdict / niveau / lignes) que l'appelant met en forme selon son
support (encadré Streamlit, encadré Word, cellule Excel).

`niveau` ∈ {"ok", "attention", "alerte", "neutre"} — pilote la couleur.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

NA = "non applicable"

_MOIS_ABBR = {1: "janv", 2: "févr", 3: "mars", 4: "avr", 5: "mai", 6: "juin",
              7: "juil", 8: "août", 9: "sept", 10: "oct", 11: "nov", 12: "déc"}


# ============================================================
# 1 — DONNÉES ET QUALITÉ
# ============================================================
def synthese_sources(res):
    """Récapitulatif factuel des données chargées."""
    cfg = res.config.sources
    d = res.df
    lignes = []
    if d is not None and len(d):
        dt = pd.to_datetime(d["date"])
        lignes.append(("Chronique thermique (eau)",
                       f"{dt.min():%d/%m/%Y} → {dt.max():%d/%m/%Y}  "
                       f"({len(d)} jours retenus après contrôle qualité)"))
    if res.df_air is not None and len(res.df_air):
        da = pd.to_datetime(res.df_air["date"])
        libelle_air = "Température de l'air"
        if getattr(cfg, "nom_station_meteo", ""):
            libelle_air += f" ({cfg.nom_station_meteo})"
        lignes.append((libelle_air,
                       f"{da.min():%d/%m/%Y} → {da.max():%d/%m/%Y}  "
                       f"({len(res.df_air)} jours)"))
    dn = res.diag_normales or {}
    if dn:
        ref = dn.get("ref", "1991–2020")
        if isinstance(ref, (tuple, list)) and len(ref) == 2:
            ref = f"{ref[0]}–{ref[1]}"
        lignes.append(("Normales de référence",
                       f"{ref} — {dn.get('n_annees_ref', '?')} années "
                       f"utilisées, lissage ±{dn.get('fenetre_lissage', '?')} j"))
    dd = res.diag_debit or {}
    if dd and dd.get("base") and dd.get("base") != "aucune":
        lignes.append(("Débits", dd.get("message", dd.get("base", "—"))))
    else:
        lignes.append(("Débits", "aucun fichier de débit fourni — "
                                 "les volets « relation Q–T° » et « débits de "
                                 "référence » ne sont pas produits"))
    lignes.append(("Contexte piscicole", res.contexte["label"]))
    return lignes


def synthese_qc(res):
    """Bilan du contrôle qualité, avec le détail des motifs d'exclusion."""
    rap = res.rapport_qc
    brut = res.daily_eau_brut
    n_brut = len(brut) if brut is not None else 0
    n_ecarte = len(rap) if rap is not None else 0
    pct = 100 * n_ecarte / n_brut if n_brut else 0.0

    motifs = []
    if rap is not None and len(rap):
        fam = rap["motif"].str.extract(r"^([^\—(]+)")[0].fillna("autre").str.strip()
        for m, cnt in fam.value_counts().items():
            motifs.append(f"{m} : {cnt} enregistrement(s)")

    if pct == 0:
        niveau, verdict = "ok", "Aucun enregistrement écarté"
    elif pct < 5:
        niveau, verdict = "ok", f"Filtrage marginal ({pct:.1f} % des jours)"
    elif pct < 20:
        niveau, verdict = "attention", f"Filtrage significatif ({pct:.1f} % des jours)"
    else:
        niveau, verdict = "alerte", f"Filtrage important ({pct:.1f} % des jours)"

    return dict(
        titre="Contrôle qualité de la chronique",
        verdict=verdict, niveau=niveau,
        lignes=[f"{n_brut} jours bruts, {n_ecarte} écartés, "
                f"{n_brut - n_ecarte} retenus pour l'analyse."] + motifs +
               ["Le pourcentage de dépassement de seuil est toujours rapporté aux "
                "jours effectivement mesurés, jamais à la durée calendaire."])


def couverture_calendaire(res):
    """Mois couverts par la chronique — conditionne l'évaluabilité des phases
    de reproduction, et donc la disponibilité de la composante fraie."""
    d = res.df
    if d is None or not len(d):
        return dict(titre="Couverture calendaire", verdict="chronique vide",
                    niveau="alerte", lignes=[])
    dt = pd.to_datetime(d["date"])
    mois_couverts = sorted(dt.dt.month.unique())
    annees = sorted(dt.dt.year.unique())
    manquants = [m for m in range(1, 13) if m not in mois_couverts]
    libelle_mois = ", ".join(_MOIS_ABBR[m] for m in mois_couverts)

    if not manquants:
        niveau, verdict = "ok", "Année complète couverte"
    elif len(manquants) <= 3:
        niveau, verdict = "attention", f"{len(manquants)} mois non couverts"
    else:
        niveau, verdict = "alerte", f"{len(manquants)} mois non couverts"

    lignes = [f"Années présentes : {', '.join(str(a) for a in annees)}.",
              f"Mois couverts : {libelle_mois}."]
    if manquants:
        lignes.append("Mois absents : " +
                      ", ".join(_MOIS_ABBR[m] for m in manquants) +
                      " — une phase de reproduction dont le mois central tombe "
                      "dans cette plage ne pourra pas être évaluée.")
    return dict(titre="Couverture calendaire", verdict=verdict,
                niveau=niveau, lignes=lignes)


def validite_modele_air_eau(res):
    """
    Validation du modèle de transfert air→eau — pierre angulaire de la
    méthode, puisque la normalisation climatique (et donc l'ensemble des
    indicateurs de vulnérabilité) en dépend directement.
    """
    s = res.sensibilite
    if not s:
        return dict(titre="Validité du modèle air–eau", verdict="non calculé",
                    niveau="alerte", lignes=[])
    r2, rob, n = s["r2"], s["robustesse"], s["n"]

    # Verdict croisé : variance expliquée ET linéarité de la relation.
    if r2 >= 0.50 and rob <= 0.10:
        niveau = "ok"
        verdict = "Modèle valide — normalisation fiable"
    elif r2 >= 0.30 and rob <= 0.20:
        niveau = "attention"
        verdict = "Modèle acceptable — résultats à nuancer"
    else:
        niveau = "alerte"
        verdict = "Modèle peu fiable — interprétation prudente requise"

    lignes = [
        f"Coefficient de sensibilité m = {s['m']:.3f} ({s['sens_cat']}) — "
        f"pente de la régression T_eau ~ T_air sur juin–septembre.",
        f"Variance expliquée R² = {r2:.3f} ({s['r2_cat']}) sur {n} jours.",
        f"Indice de robustesse |ρ−r| = {rob:.4f} ({s['rob_cat']}) — un écart "
        f"faible entre corrélations de Pearson et Spearman confirme que la "
        f"relation est bien linéaire sur la plage observée.",
        f"Test de normalité retenu : {s['test_used']} "
        f"(p = {s['p_reg']:.5f} pour la régression).",
    ]
    if niveau != "ok":
        lignes.append("Conséquence : la température normalisée — et donc les "
                      "pourcentages de dépassement de seuil qui en découlent — "
                      "porte une incertitude accrue sur cette station.")
    return dict(titre="Validité du modèle air–eau (fondement de la méthode)",
                verdict=verdict, niveau=niveau, lignes=lignes)


# ============================================================
# 2 — THERMIE, VULNÉRABILITÉ, SGVT
# ============================================================
def interpretation_vulnerabilite(res):
    v = res.vulnerabilite
    ctx = res.contexte
    if not v:
        return dict(titre="Vulnérabilité estivale", verdict=NA,
                    niveau="neutre", lignes=[])
    pct, n_aigu = v["pct_chr"], v["n_aigu"]
    if pct < 3 and n_aigu == 0:
        niveau, verdict = "ok", "Aucune contrainte thermique estivale marquée"
    elif n_aigu > 0:
        niveau, verdict = "alerte", "Létalité thermique observée"
    elif pct >= 20:
        niveau, verdict = "alerte", "Stress chronique important"
    else:
        niveau, verdict = "attention", "Stress chronique modéré"

    return dict(
        titre=f"Vulnérabilité estivale — {ctx['label']}",
        verdict=verdict, niveau=niveau,
        lignes=[
            f"Stress chronique : {pct:.1f} % des jours de juin à septembre "
            f"au-dessus de {v['seuil_chr']} °C (Tmh normalisée) → {v['cat_chr']}.",
            f"Létalité aiguë : {n_aigu} jour(s) au-dessus de {v['seuil_aigu']} °C "
            f"(Tmax normalisée) → {v['cat_aigu']}.",
            "Le stress chronique traduit une perturbation métabolique cumulée ; "
            "la létalité aiguë un risque de mortalité à court terme.",
        ])


def interpretation_sgvt(res):
    sg = res.sgvt
    if not sg:
        return dict(titre="SGVT", verdict=NA, niveau="neutre", lignes=[])
    val = sg["sgvt"]
    niveau = ("ok" if val < 2 else "attention" if val < 5
              else "alerte" if val < 8 else "alerte")
    ncomp = sg.get("composantes", 4)
    lignes = [
        f"SGVT = {val:.2f} / 10 → {sg['interp']}.",
        f"Score agrégé sur {ncomp} composante(s) pondérée(s) : sensibilité "
        f"({sg['pts_s']}/3), stress chronique ({sg['pts_c']}/3), létalité aiguë "
        f"({sg['pts_a']}/3)" +
        (f", fraie-croissance ({sg['pts_f']}/3)." if sg.get("pts_f") is not None
         else " — composante fraie non évaluable, repli sur 3 composantes."),
        "Le SGVT est une information d'appoint : il contextualise les débits de "
        "référence sans s'y substituer, et module le coefficient de sécurité de "
        "Q_thermie_fonc.",
    ]
    return dict(titre="Score Global de Vulnérabilité Thermique",
                verdict=sg["interp"], niveau=niveau, lignes=lignes)


# ============================================================
# 3 — FRAIE-CROISSANCE
# ============================================================
def interpretation_fraie(res):
    fr = res.fraie
    if not fr:
        return dict(titre="Fraie-croissance", verdict=NA, niveau="neutre",
                    lignes=["Composante non définie pour ce contexte piscicole."])
    if not fr.get("disponible"):
        motifs = [f"{s['espece']} : {s.get('motif', 'non évalué')}"
                  for s in fr.get("sous_indicateurs", [])]
        return dict(
            titre="Fraie-croissance", verdict="non évaluable", niveau="attention",
            lignes=["La chronique ne couvre pas les phases critiques (ponte ou "
                    "incubation) des espèces repères de ce contexte."] + motifs +
                   ["Le SGVT bascule automatiquement sur 3 composantes."])
    P = fr["P_fraie"]
    niveau = "ok" if P <= 1 else "attention" if P == 2 else "alerte"
    lignes = [
        f"Espèce la plus contrainte : {fr['espece_limitante']} → P = {P}/3 "
        f"({fr['cat_fraie']}).",
        "Chaque espèce est évaluée sur trois phases successives (pré-frai, "
        "ponte, incubation) aux tolérances thermiques distinctes ; la classe "
        "retenue est le maximum entre la sévérité moyenne et le temps passé en "
        "zone létale, afin qu'un épisode létal ne soit jamais dilué.",
    ]
    for s in fr.get("sous_indicateurs", []):
        if s.get("evalue"):
            lignes.append(
                f"{s['espece']} : optimum {s['pct_optimum']:.0f} %, tolérance "
                f"élargie {s['pct_elargie']:.0f} %, zone létale "
                f"{s['pct_letal']:.0f} % → P = {s['P']} ({s['cat']}).")
        else:
            lignes.append(f"{s['espece']} : non évalué — {s.get('motif', '')}")
    return dict(titre="Vulnérabilité de la reproduction", verdict=fr["cat_fraie"],
                niveau=niveau, lignes=lignes)


# ============================================================
# 4 — RELATION Q–T° ET DÉBITS
# ============================================================
def interpretation_relation(res):
    rel = res.relation_debit_temp
    if not rel or not rel.get("disponible"):
        return dict(titre="Relation débit–température", verdict=NA,
                    niveau="neutre",
                    lignes=["Test non réalisable : débit absent ou effectif "
                            "insuffisant."])
    verdict = rel["verdict"]
    niveau = {"etablie": "ok", "faible": "attention",
              "absente": "attention", "inversee": "alerte"}.get(verdict, "neutre")
    g = rel["lignes"][0]
    lignes = [
        rel["commentaire"],
        f"Sur l'ensemble de la gamme (n = {g['n']}) : corrélation brute "
        f"r = {g['r_brute']:+.3f}, corrélation partielle à température d'air "
        f"égale r = {g['r_partielle']:+.3f} (R² = {g['r2_partielle']:.3f}).",
        "La corrélation partielle isole l'effet propre du débit en retirant le "
        "forçage atmosphérique (air lissé, pour tenir compte de l'inertie "
        "thermique du milieu) — c'est elle qui répond réellement à la question.",
    ]
    return dict(titre="Le débit module-t-il la température ?",
                verdict=rel["libelle"], niveau=niveau, lignes=lignes)


def interpretation_matrice(res):
    """Tableau de décision : validité de la démarche « débits thermiques »."""
    m = res.matrice
    if not m:
        return dict(titre="Diagnostic d'ensemble", verdict=NA, niveau="neutre",
                    lignes=[])
    niveau = {1: "alerte", 2: "attention", 3: "ok", 4: "neutre"}.get(m["case"], "neutre")
    return dict(
        titre="Diagnostic d'ensemble — que permet de conclure l'approche ?",
        verdict=f"Cas {m['case']} — {m['libelle']}", niveau=niveau,
        lignes=[
            m["conduite"],
            f"Problème thermique : {'avéré' if m['probleme'] else 'non constaté'} "
            f"({m['motif_probleme']}).",
            f"Levier débit : {'opérant' if m['levier'] else 'non opérant'} "
            f"({m['motif_levier']}).",
        ])


def interpretation_debits(res):
    ds = res.debits_sorties or {}
    dinf = res.debits_inflexion
    bio = ds.get("q_thermie_bio") or {}
    fonc = ds.get("q_thermie_fonc") or {}
    if not dinf:
        return dict(titre="Débits de référence thermique", verdict=NA,
                    niveau="neutre",
                    lignes=["Non calculés : aucun fichier de débit fourni."])
    lignes = []
    if bio.get("valeur") is not None:
        niveau, verdict = "alerte", "Q_thermie_bio déterminé"
        lignes.append(
            f"Q_thermie_bio = {bio['valeur']:.3f} m³/s — débit en-deçà duquel la "
            f"vulnérabilité biologique devient mesurable (résultat principal).")
        if bio.get("pnda_desinf") is not None:
            lignes.append(f"PNDA désinfluencé : {bio['pnda_desinf']:.1f} %.")
        if bio.get("pnda_inf") is not None:
            lignes.append(f"PNDA influencé : {bio['pnda_inf']:.1f} % (information).")
    else:
        niveau, verdict = "neutre", "Q_thermie_bio non applicable"
        diag = (dinf.get("diag_stress") or {})
        lignes.append("Aucun seuil de vulnérabilité biologique n'a pu être "
                      "déterminé sur cette station.")
        if diag.get("raison"):
            lignes.append(f"Volet stress : {diag['raison']}.")
        lignes.append("Le volet létal, déclencheur principal, n'est pas non plus "
                      "activé (aucun dépassement du seuil de létalité).")
    if fonc.get("valeur") is not None:
        lignes.append(
            f"Q_thermie_fonc = {fonc['valeur']:.3f} m³/s — rupture de régime "
            f"thermique (information d'appoint, ne se substitue pas au résultat "
            f"principal).")
    dd = res.diag_debit or {}
    lignes.append("Base d'analyse (recherche du seuil, test de causalité) : "
                  "toujours l'influencé — c'est l'eau réellement présente qui "
                  "gouverne la température observée cette année-là.")
    if dd.get("desinfluence_disponible"):
        ea, ej = dd.get("ecart_annuel"), dd.get("ecart_jjas")
        if ea is not None and ej is not None and ea == ea and ej == ej:
            lignes.append(
                f"Écart médian influencé/désinfluencé : {ea*100:.1f}% sur "
                f"l'année, {ej*100:.1f}% en juin–septembre — un écart JJAS "
                f"élevé signale une pression anthropique concentrée en "
                f"période d'étiage, précisément la période qui compte ici.")
        lignes.append("Comblement des trous du désinfluencé par l'influencé : "
                      + ("appliqué." if dd.get("comble") else
                         "non appliqué (écart trop marqué) — sa distribution "
                         "PNDA reste partielle."))
    return dict(titre="Débits de référence thermique", verdict=verdict,
                niveau=niveau, lignes=lignes)


# ============================================================
# 5 — CONCLUSION DE STATION
# ============================================================
def conclusion_station(res):
    """Paragraphe conclusif, articulant diagnostic et portée opérationnelle."""
    m = res.matrice
    sg = res.sgvt
    parts = []
    if sg:
        parts.append(f"La station présente un SGVT de {sg['sgvt']:.2f}/10 "
                     f"({sg['interp']}).")
    if m:
        parts.append(m["conduite"])
    else:
        parts.append("En l'absence de données de débit, l'analyse reste "
                     "descriptive : elle caractérise la vulnérabilité thermique "
                     "du milieu sans pouvoir statuer sur le levier hydrologique.")
    val = validite_modele_air_eau(res)
    if val["niveau"] != "ok":
        parts.append(f"Réserve méthodologique : {val['verdict'].lower()} — "
                     f"les valeurs normalisées portent une incertitude accrue.")
    fr = res.fraie
    if fr and not fr.get("disponible"):
        parts.append("La composante reproduction n'a pas pu être évaluée faute "
                     "de couverture calendaire suffisante ; une extension de la "
                     "chronique sur les phases critiques serait nécessaire.")
    return " ".join(parts)


def reserves_station(res):
    """Liste des réserves et limites spécifiques à cette station."""
    r = []
    val = validite_modele_air_eau(res)
    if val["niveau"] != "ok":
        r.append(f"Modèle air–eau : {val['verdict'].lower()}.")
    qc = synthese_qc(res)
    if qc["niveau"] != "ok":
        r.append(f"Contrôle qualité : {qc['verdict'].lower()}.")
    cov = couverture_calendaire(res)
    if cov["niveau"] != "ok":
        r.append(f"Couverture calendaire : {cov['verdict'].lower()}.")
    fr = res.fraie
    if fr and not fr.get("disponible"):
        r.append("Composante fraie-croissance non évaluable.")
    rel = res.relation_debit_temp
    if rel and rel.get("disponible") and rel.get("verdict") != "etablie":
        r.append(f"Relation débit–température : {rel['libelle'].lower()}.")
    for a in (res.avertissements or []):
        r.append(str(a))
    if not r:
        r.append("Aucune réserve particulière : données complètes, modèle "
                 "valide, tous les volets évaluables.")
    return r


def debit_retenu_prominent(res):
    """
    Mise en avant du débit de référence retenu — point de sortie majeur de
    l'étude lorsque le volet débit est activé. Priorité à Q_thermie_bio
    (résultat principal) ; à défaut, repli explicite sur Q_thermie_fonc
    (information d'appoint). PNDA désinfluencé présenté en priorité,
    influencé en secondaire — convention tenue dans toute la méthode.
    """
    ds = res.debits_sorties or {}
    bio = ds.get("q_thermie_bio") or {}
    fonc = ds.get("q_thermie_fonc") or {}

    if bio.get("valeur") is not None:
        source, valeur = "Q_thermie_bio", bio["valeur"]
        pnda_d, pnda_i = bio.get("pnda_desinf"), bio.get("pnda_inf")
        niveau, nature = "alerte", "résultat principal de l'approche thermique"
    elif fonc.get("valeur") is not None:
        source, valeur = "Q_thermie_fonc", fonc["valeur"]
        pnda_d, pnda_i = fonc.get("pnda_desinf"), fonc.get("pnda_inf")
        niveau = "attention"
        nature = ("information d'appoint — Q_thermie_bio n'a pas pu être "
                  "déterminé sur cette station, ce débit de repli n'a pas la "
                  "même portée biologique directe")
    else:
        return dict(titre="Débit de référence retenu", verdict="non déterminé",
                    niveau="neutre",
                    lignes=["Aucun débit de référence n'a pu être établi sur "
                            "cette station (ni volet létal ni volet stress "
                            "activés — voir « Débits de référence thermique »)."])

    lignes = [f"{source} = {valeur:.3f} m³/s ({nature})."]
    if pnda_d is not None:
        lignes.append(f"PNDA désinfluencé (lecture prioritaire) : {pnda_d:.1f} %.")
    else:
        lignes.append("PNDA désinfluencé : non disponible — débit désinfluencé "
                      "non fourni pour cette station.")
    if pnda_i is not None:
        lignes.append(f"PNDA influencé (information secondaire) : {pnda_i:.1f} %.")
    val = validite_modele_air_eau(res)
    lignes.append(f"Fiabilité de la normalisation sous-jacente : "
                  f"{val['verdict'].lower()}.")
    return dict(titre="Débit de référence retenu",
                verdict=f"{valeur:.3f} m³/s  ({source})",
                niveau=niveau, lignes=lignes)


# ============================================================
# 6 — LIGNE DE SYNTHÈSE À SCHÉMA FIXE (comparaison inter-sites)
# ============================================================
# L'ordre et le nombre de colonnes sont INVARIANTS : une station sans débit
# produit les mêmes colonnes qu'une station complète, renseignées à
# « non applicable ». C'est la condition pour empiler les stations les unes
# sous les autres sans retraitement manuel.
COLONNES_SYNTHESE = [
    "Cours d'eau", "Localisation sonde", "Station hydrométrique", "Station météo",
    "Contexte piscicole", "Espèce repère", "Début chronique", "Fin chronique",
    "Jours exploitables", "% jours écartés (QC)", "Mois couverts",
    "Couverture annuelle complète",
    "m (sensibilité)", "R² air-eau", "|rho-r|", "Validité modèle air-eau",
    "% stress chronique", "Classe stress chronique",
    "Jours létaux", "Classe létalité",
    "Espèce limitante fraie", "P_fraie", "Classe fraie",
    "SGVT /10", "Classe SGVT", "Composantes SGVT",
    "Verdict relation Q-T°", "r brute Q-T°", "r partielle Q-T°", "R² partielle",
    "Cas matrice", "Diagnostic", "Conduite à tenir",
    "Q_thermie_bio (m³/s)", "PNDA désinf. bio (%)", "PNDA inf. bio (%)",
    "Q_thermie_fonc (m³/s)", "Base de calcul débit",
    "Désinfluencé disponible", "Écart Q inf/désinf annuel (%)",
    "Écart Q inf/désinf JJAS (%)", "Comblement désinfluencé appliqué",
    "Version outil",
]


def ligne_synthese(res):
    """Dict ordonné (clé = COLONNES_SYNTHESE) décrivant la station en une
    ligne, pour empilement inter-sites."""
    from .config import __version__
    cfg = res.config.sources
    s, v, sg = res.sensibilite, res.vulnerabilite, res.sgvt
    fr, rel, m = res.fraie, res.relation_debit_temp, res.matrice
    ds = res.debits_sorties or {}
    dd = res.diag_debit or {}
    bio = ds.get("q_thermie_bio") or {}
    fonc = ds.get("q_thermie_fonc") or {}

    d = res.df
    dt = pd.to_datetime(d["date"]) if d is not None and len(d) else None
    mois_couverts = sorted(dt.dt.month.unique()) if dt is not None else []
    rap, brut = res.rapport_qc, res.daily_eau_brut
    pct_qc = (100 * len(rap) / len(brut)) if (rap is not None and brut is not None
                                              and len(brut)) else np.nan
    val_modele = validite_modele_air_eau(res)

    def _f(x, nd=3):
        return round(float(x), nd) if x is not None and x == x else NA

    vals = {
        "Cours d'eau": cfg.nom_cours_eau or "—",
        "Localisation sonde": getattr(cfg, "localisation_sonde", "") or "—",
        "Station hydrométrique": getattr(cfg, "nom_station_debit", "") or "—",
        "Station météo": getattr(cfg, "nom_station_meteo", "") or "—",
        "Contexte piscicole": res.contexte["label"],
        "Espèce repère": res.contexte.get("espece", "—"),
        "Début chronique": f"{dt.min():%d/%m/%Y}" if dt is not None else NA,
        "Fin chronique": f"{dt.max():%d/%m/%Y}" if dt is not None else NA,
        "Jours exploitables": len(d) if d is not None else 0,
        "% jours écartés (QC)": _f(pct_qc, 1),
        "Mois couverts": len(mois_couverts),
        "Couverture annuelle complète": "oui" if len(mois_couverts) == 12 else "non",
        "m (sensibilité)": _f(s["m"]) if s else NA,
        "R² air-eau": _f(s["r2"]) if s else NA,
        "|rho-r|": _f(s["robustesse"], 4) if s else NA,
        "Validité modèle air-eau": val_modele["verdict"],
        "% stress chronique": _f(v["pct_chr"], 1) if v else NA,
        "Classe stress chronique": v["cat_chr"] if v else NA,
        "Jours létaux": int(v["n_aigu"]) if v else NA,
        "Classe létalité": v["cat_aigu"] if v else NA,
        "Espèce limitante fraie": (fr.get("espece_limitante") if fr and
                                   fr.get("disponible") else NA),
        "P_fraie": (fr.get("P_fraie") if fr and fr.get("disponible") else NA),
        "Classe fraie": (fr.get("cat_fraie") if fr and fr.get("disponible")
                         else "non évaluable"),
        "SGVT /10": _f(sg["sgvt"], 2) if sg else NA,
        "Classe SGVT": sg["interp"] if sg else NA,
        "Composantes SGVT": sg.get("composantes", NA) if sg else NA,
        "Verdict relation Q-T°": (rel["libelle"] if rel and rel.get("disponible")
                                  else NA),
        "r brute Q-T°": (_f(rel["lignes"][0]["r_brute"])
                         if rel and rel.get("disponible") else NA),
        "r partielle Q-T°": (_f(rel["lignes"][0]["r_partielle"])
                             if rel and rel.get("disponible") else NA),
        "R² partielle": (_f(rel["lignes"][0]["r2_partielle"])
                         if rel and rel.get("disponible") else NA),
        "Cas matrice": m["case"] if m else NA,
        "Diagnostic": m["libelle"] if m else NA,
        "Conduite à tenir": m["conduite"] if m else NA,
        "Q_thermie_bio (m³/s)": _f(bio.get("valeur")),
        "PNDA désinf. bio (%)": _f(bio.get("pnda_desinf"), 1),
        "PNDA inf. bio (%)": _f(bio.get("pnda_inf"), 1),
        "Q_thermie_fonc (m³/s)": _f(fonc.get("valeur")),
        "Base de calcul débit": ds.get("base_calcul", res.base_debit) or NA,
        "Désinfluencé disponible": ("oui" if dd.get("desinfluence_disponible")
                                    else ("non" if dd else NA)),
        "Écart Q inf/désinf annuel (%)": (_f(dd["ecart_annuel"]*100, 1)
                                          if dd.get("ecart_annuel") is not None
                                          and dd["ecart_annuel"] == dd["ecart_annuel"] else NA),
        "Écart Q inf/désinf JJAS (%)": (_f(dd["ecart_jjas"]*100, 1)
                                        if dd.get("ecart_jjas") is not None
                                        and dd["ecart_jjas"] == dd["ecart_jjas"] else NA),
        "Comblement désinfluencé appliqué": ("oui" if dd.get("comble") else
                                             ("non" if dd.get("desinfluence_disponible") else NA)),
        "Version outil": __version__,
    }
    # Garantit l'ordre et la complétude du schéma.
    return {c: vals.get(c, NA) for c in COLONNES_SYNTHESE}
