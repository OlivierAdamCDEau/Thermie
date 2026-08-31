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
        "Espèce repère": res.contexte.get("espece_repere", "—"),
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


# ============================================================
# 7 — LES ÉTATS DÉCLARÉS (D48)
# ============================================================
# Un seul bloc, rassemblant tout ce que la chaîne sait de ses propres limites
# sur ce point de mesure.
#
# LE PRINCIPE, et il commande toute la rédaction qui suit :
#
#   Chaque contrôle annonce ce dont il a besoin, s'active si les données le
#   permettent, et DIT à quelle marche il se trouve et ce qu'il ne voit pas.
#   Un contrôle silencieusement désactivé sur un jeu pauvre est plus dangereux
#   qu'un contrôle absent : il produit une attestation au lieu d'une alerte.
#
# Conséquence directe : UN CONTRÔLE QUI N'A RIEN TROUVÉ DOIT SE VOIR.
# « Rien à signaler » et « contrôle non exécuté » ne produisent jamais la même
# ligne. C'est pourquoi chaque contrôle rend un bloc même quand son compte
# vaut zéro, et pourquoi trois valeurs cohabitent sans se confondre : un
# nombre, « sans objet », et « non vérifiable ».
#
# Aucun seuil n'est introduit ici. Le niveau d'un bloc ne dépend jamais du
# franchissement d'une valeur conventionnelle : il dépend de FAITS —
# un contrôle n'a pas pu tourner, une année civile est absente, un
# coefficient a été rejeté. Ces conditions se lisent sur les données et ne se
# calibrent pas.

NIVEAU_VERIFIE = "verifie"     # le contrôle a tourné et n'a rien à signaler
NIVEAU_RESERVE = "reserve"     # le contrôle a trouvé quelque chose à dire
NIVEAU_ALERTE = "alerte"       # le contrôle n'a pas pu se prononcer, ou un
                               # résultat publié doit être lu autrement


def _bloc(niveau, titre, lignes):
    return dict(niveau=niveau, titre=titre,
                lignes=[l for l in lignes if l])


def _pc(n, total):
    return f"{100.0 * n / total:.1f} %" if total else "—"


_MOIS_FR = {1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai",
            6: "juin", 7: "juillet", 8: "août", 9: "septembre",
            10: "octobre", 11: "novembre", 12: "décembre"}


def _etat_detecteur(res):
    """Le détecteur de mise hors d'eau : à quelle marche, et ce qu'il ne voit pas."""
    d = getattr(res, "diag_detecteur", None) or {}
    if not d:
        return _bloc(NIVEAU_ALERTE, "Détection de sonde hors d'eau",
                     ["L'état de ce contrôle n'a pas été enregistré. "
                      "Son résultat ne peut pas être interprété."])
    if not d.get("hors_eau_actif"):
        return _bloc(NIVEAU_ALERTE, "Détection de sonde hors d'eau",
                     ["**Contrôle désactivé** dans les réglages. Aucune journée "
                      "n'a été examinée à ce titre.",
                      "Une absence de signalement ne signifie donc pas qu'aucune "
                      "sonde n'est sortie de l'eau : personne n'a regardé."])
    if not d.get("hors_eau_execute"):
        return _bloc(NIVEAU_ALERTE, "Détection de sonde hors d'eau",
                     ["**Contrôle non exécuté** : aucune température d'air "
                      "exploitable sur la période de la sonde.",
                      "Aucune journée n'est écartée à ce titre — ce qui n'est "
                      "**pas** un constat d'absence d'exondation."])

    n1, n2 = d.get("n_marche1", 0), d.get("n_marche2", 0)
    ndiag = d.get("n_diagnosticables", 0)
    nnd = d.get("n_non_diagnosticables", 0)
    m2 = d.get("marche2_disponible")

    lignes = [
        f"*Ce qu'il lui faut :* la température maximale journalière de l'eau "
        f"et la température moyenne de l'air. Un second niveau d'examen "
        f"s'ajoute si le fichier d'air porte aussi les températures minimale "
        f"et maximale du jour.",
        f"*Ce qu'il a examiné :* **{ndiag} journées**, sur toute l'année.",
        (f"*Ce qu'il a trouvé :* **{n1 + n2} journée(s) marquée(s)** "
         f"({n1} au premier niveau"
         + (f", {n2} ajoutée(s) par le second" if m2 else "")
         + ")." if (n1 + n2) else
         "*Ce qu'il a trouvé :* **aucune journée suspecte.** Le contrôle a "
         "bien tourné : ce zéro est un résultat, pas une absence de contrôle."),
    ]
    if nnd:
        lignes.append(
            f"*Ce sur quoi il s'abstient :* **{nnd} journée(s)** qu'il ne sait "
            f"pas juger — trop peu de jours dans le mois, ou une dispersion "
            f"nulle. Elles restent dans la chronique : elles n'ont rien de "
            f"défectueux, mais rien n'est affirmé à leur sujet.")

    # D121 — LE SECOND MEMBRE DU PREMIER NIVEAU.
    # Il ne detecte rien ; il repond a « ce decouplage vient-il de l'eau qui
    # monte ou de l'air qui descend ». Sans lui, une vague de froid produit la
    # meme signature qu'une sonde emergee. L'ecran ne le nommait pas : un
    # lecteur ne pouvait pas savoir combien de journees il ecartait, ni ou il
    # se taisait.
    if d.get("signe_actif"):
        _bloq = d.get("n_bloquees_par_signe", 0)
        lignes.append(
            "*Comment il distingue l'eau de l'air :* le premier niveau compare "
            "la température de l'eau à celle de l'air. Un tel écart grandit "
            "aussi bien quand l'eau monte que quand l'air descend, et la "
            "différence seule ne dit pas lequel des deux a bougé. Une seconde "
            "condition est donc exigée : **l'eau doit être plus chaude que "
            "d'habitude à cette station et à ce mois-là**. Un coup de froid, "
            "qui fait plonger l'air sans que l'eau bouge, ne passe plus pour "
            "une sonde sortie de l'eau.")
        lignes.append(
            f"*Ce que cette seconde condition a écarté :* "
            + (f"**{_bloq} journée(s)** que la seule différence eau-air aurait "
               f"fait marquer, et où l'eau n'était pourtant pas plus chaude "
               f"que d'ordinaire."
               if _bloq else
               "**aucune journée.** Sur cette chronique, les deux conditions "
               "ont toujours été d'accord."))
        _mois = d.get("mois_signe_muet") or []
        if _mois:
            _noms = ", ".join(_MOIS_FR[m] for m in _mois)
            lignes.append(
                f"*Là où cette condition ne se prononce pas :* **{_noms}** — "
                f"trop peu de journées mesurées dans ce ou ces mois pour "
                f"savoir ce qui y est habituel. Le contrôle ne marque alors "
                f"aucune journée de ces mois, et cela ne vaut pas quitus : "
                f"il n'a pas pu regarder.")
    if not m2:
        lignes.append(
            f"⚠ *Ce qu'il ne voit pas :* **le second niveau d'examen est "
            f"indisponible** — {d.get('motif_marche2') or 'données manquantes'}. "
            f"Sans lui, le contrôle ne distingue pas une sonde sortie de l'eau "
            f"d'une journée simplement chaude : il dispose du niveau de "
            f"température, pas de la forme du signal sur la journée.")
        if not d.get("structure_infra_journaliere"):
            lignes.append(
                "La chronique ne porte qu'une mesure par jour, ou son heure "
                "n'a pas été reconnue. Le second niveau ne peut pas se "
                "prononcer, par construction.")
    elif not d.get("structure_infra_journaliere"):
        # Cas prevu par la specification : les donnees du second niveau sont
        # PRESENTES mais vides de sens. La chronique ne porte qu'une mesure par
        # jour, ou son heure n'a pas ete reconnue : le minimum et le maximum du
        # jour sont alors le meme point, et le rapport de formes vaut zero par
        # construction. Le declarer « disponible » serait faux.
        lignes.append(
            "⚠ **Contrôle dégradé — le second niveau ne peut pas se "
            "prononcer.** La chronique ne porte qu'une mesure par jour, ou "
            "l'heure de ses mesures n'a pas été reconnue : le minimum et le "
            "maximum du jour sont le même point, et la forme du signal "
            "journalier est nulle par construction. Le premier niveau reste "
            "actif ; sa lecture est celle d'un niveau de température, pas "
            "d'une forme.")
    else:
        s = d.get("seuil_amplitude_air")
        lignes.append(
            "*Ce qu'il ne voit pas :* une sonde sortie de l'eau en permanence "
            "— sa propre habitude serait alors celle d'une sonde exondée — et "
            "l'émersion hivernale, dont la signature est inverse."
            + (f" Le second niveau s'abstient quand l'amplitude de l'air du "
               f"jour est inférieure à {s:.2f} °C, valeur tirée de ce jeu de "
               f"données." if s else ""))
    degrade = not d.get("structure_infra_journaliere")
    niveau = (NIVEAU_ALERTE if (not m2 or degrade)
              else NIVEAU_RESERVE if (n1 + n2 or nnd) else NIVEAU_VERIFIE)
    return _bloc(niveau, "Détection de sonde hors d'eau", lignes)


def _etat_journees_non_exploitables(res):
    """Journées retenues par le contrôle qualité mais inexploitables."""
    m = getattr(res, "marques_fusion", None)
    total = int(len(m)) if m is not None else 0
    if m is None or not total:
        return _bloc(NIVEAU_VERIFIE, "Journées entrées dans le calcul",
                     ["L'état de ce contrôle n'est pas disponible."])
    nd = m[m["statut"] == "non_diagnosticable"]
    n_air = sum(1 for ms in nd["motifs"]
                if any("air absente" in x for x in ms))
    n_dens = sum(1 for ms in nd["motifs"]
                 if any("densité calendaire" in x for x in ms))
    n = len(nd)
    if not n:
        return _bloc(NIVEAU_VERIFIE, "Journées entrées dans le calcul",
                     [f"Les **{total} journées** retenues par le contrôle "
                      f"qualité sont **toutes** entrées dans le calcul. Aucune "
                      f"n'a été retirée faute de température d'air, ni faute "
                      f"de voisines assez proches dans le calendrier."])
    lignes = [f"**{n} journée(s) sur {total} ({_pc(n, total)}) n'ont pas pu "
              f"être exploitées.**"]
    if n_air:
        lignes.append(
            f"· **{n_air}** faute de température d'air à cette date. Ces "
            f"journées d'eau ont bien été mesurées et le contrôle qualité les "
            f"a retenues : elles ne sont ni écartées ni défectueuses, il leur "
            f"manque une donnée qui ne vient pas de la sonde. Vérifier la "
            f"station météo retenue — une autre station couvrant la période "
            f"les rendrait au calcul.")
    if n_dens:
        lignes.append(
            f"· **{n_dens}** faute de voisines : la température moyenne "
            f"hebdomadaire est une moyenne sur sept jours *calendaires*, et "
            f"ces journées-là sont trop isolées pour qu'une telle moyenne ait "
            f"un sens.")
    lignes.append(
        "*Ce que cela retire :* ces journées ne reçoivent pas de température "
        "corrigée du climat, n'entrent pas dans les pourcentages de "
        "dépassement de seuil et ne comptent pas parmi les journées de "
        "vulnérabilité. Elles restent visibles, avec leur motif.")

    # Faits — jamais des seuils.
    try:
        import pandas as _pd
        an = _pd.to_datetime(_pd.Series(list(nd["date"]))).dt.year
        an_tot = _pd.to_datetime(_pd.Series(list(m["date"]))).dt.year
        for a in sorted(set(an)):
            if int((an == a).sum()) == int((an_tot == a).sum()):
                lignes.append(
                    f"⚠ **L'année {a} est entièrement absente du calcul.** Les "
                    f"résultats ne décrivent pas cette année-là ; toute lecture "
                    f"pluriannuelle porte sur les autres années uniquement.")
        mois = _pd.to_datetime(_pd.Series(list(nd["date"]))).dt.month
        n_ete = int(mois.isin([6, 7, 8, 9]).sum())
        if n_ete:
            lignes.append(
                f"⚠ **{n_ete} de ces journées tombent entre juin et "
                f"septembre**, la période sur laquelle est estimée la relation "
                f"entre la température de l'air et celle de l'eau. Cette "
                f"relation repose donc sur un échantillon estival réduit.")
    except Exception:
        pass
    return _bloc(NIVEAU_RESERVE, "Journées entrées dans le calcul", lignes)


def _etat_lecture(res):
    """Mesures écartées à la lecture du fichier de sonde."""
    ml = getattr(res, "marques_lecture", None)
    if ml is None:
        return _bloc(NIVEAU_VERIFIE, "Lecture du fichier de sonde",
                     ["L'état de ce contrôle n'est pas disponible."])
    n = int(len(ml))
    if not n:
        return _bloc(NIVEAU_VERIFIE, "Lecture du fichier de sonde",
                     ["**Aucune mesure n'a été écartée à la lecture.** Toutes "
                      "les lignes du fichier portaient une date et une "
                      "température lisibles. Ce contrôle a bien tourné : le "
                      "zéro est un résultat."])
    causes = {}
    for x in ml["motif"]:
        cle = ("date illisible" if "date illisible" in x
               else "température illisible" if "temperature" in x or "température" in x
               else "date et température illisibles")
        causes[cle] = causes.get(cle, 0) + 1
    detail = " ; ".join(f"{v} pour {k}" for k, v in sorted(causes.items()))
    return _bloc(NIVEAU_RESERVE, "Lecture du fichier de sonde",
                 [f"**{n} mesure(s) écartée(s)** avant tout calcul : {detail}.",
                  "Une mesure dont la date est illisible ne s'impute à aucune "
                  "journée ; le total peut donc dépasser la somme des comptes "
                  "journaliers."])


def _etat_completude(res):
    """Complétude des journées : le trou maximal, et l'indéterminable."""
    mc = getattr(res, "marques_completude", None)
    if mc is None or not len(mc):
        return _bloc(NIVEAU_VERIFIE, "Complétude des journées de mesure",
                     ["L'état de ce contrôle n'est pas disponible."])
    if (mc["statut"] == "indeterminable").all():
        return _bloc(
            NIVEAU_ALERTE, "Complétude des journées de mesure",
            ["⚠ **Contrôle non applicable — sans objet, et non « rien à "
             "signaler ».**",
             "Toutes les mesures de cette sonde portent le même horodatage : "
             "l'heure de la journée n'a pas été reconnue dans le fichier. "
             "L'outil ne sait donc rien de la répartition des mesures dans la "
             "journée et **ne peut pas juger** leur complétude.",
             "**Une absence de signalement ne vaut pas quitus ici** : elle "
             "signifie que personne n'a pu regarder. Les moyennes "
             "journalières restent calculées et utilisées ; c'est leur "
             "représentativité qui n'est pas vérifiable."])
    sig = mc[mc["statut"] == "signalee"]
    total = int(len(mc))
    if not len(sig):
        return _bloc(NIVEAU_VERIFIE, "Complétude des journées de mesure",
                     [f"**Aucune journée signalée sur {total}.** Chaque journée "
                      f"a été examinée : son plus long intervalle sans mesure "
                      f"reste dans l'ordinaire de cette sonde. Ce contrôle a "
                      f"bien tourné."])
    lignes = [
        f"**{len(sig)} journée(s) sur {total} ({_pc(len(sig), total)}) "
        f"reposent sur des mesures groupées.**",
        "*Ce qui est mesuré :* le plus long intervalle de la journée pendant "
        "lequel la sonde n'a rien enregistré. Sont signalées les journées dont "
        "cet intervalle dépasse **deux fois** celui d'une journée ordinaire de "
        "cette sonde — le repère est la sonde elle-même, quelle que soit sa "
        "cadence de mesure.",
    ]
    try:
        t = sig["trou_max_h"].astype(float)
        lignes.append(f"*Ampleur :* de **{t.min():.0f} h** à **{t.max():.0f} h** "
                      f"sans mesure ; médiane **{t.median():.0f} h**.")
        if "n_mesures" in sig.columns and sig["n_mesures"].notna().any():
            nm = sig["n_mesures"].astype(float)
            lignes.append(
                f"*Ce ne sont pas des journées pauvres :* elles portent "
                f"**{nm.median():.0f} mesures** en médiane. Leurs mesures sont "
                f"**groupées**, pas rares.")
    except Exception:
        pass
    lignes += [
        "*Ce que cela veut dire :* la moyenne de ces journées ne couvre pas le "
        "cycle jour-nuit et peut être décalée vers les heures effectivement "
        "mesurées.",
        "**Ces journées ne sont pas écartées** : elles entrent dans tous les "
        "calculs. Le signalement est un avertissement de lecture, pas un "
        "filtre.",
        "*Ce que ce signalement ne dit pas :* qu'une journée signalée est "
        "fausse, ni qu'une journée non signalée est complète. Une journée dont "
        "les mesures sont régulièrement espacées mais rares n'est pas "
        "signalée.",
        "*Réserve connue :* l'amplitude jour-nuit publiée pour ces journées "
        "est calculée sur les mêmes mesures groupées. Une amplitude qui ignore "
        "une partie de la nuit n'est pas une amplitude jour-nuit.",
    ]
    return _bloc(NIVEAU_RESERVE, "Complétude des journées de mesure", lignes)


def _etat_couplage(res):
    """Le statut de la relation air-eau, estivale puis par espèce."""
    s = res.sensibilite or {}
    lignes, niveau = [], NIVEAU_VERIFIE
    val = s.get("validite")
    m_app, m_est = s.get("m"), s.get("m_estime")
    if val is False:
        niveau = NIVEAU_ALERTE
        lignes += [
            "⛔ **La relation entre la température de l'air et celle de l'eau "
            "n'a pas pu être établie sur cette chronique.**",
            f"*Ce qui a été tenté :* la pente reliant les deux, estimée sur "
            f"**{s.get('n', '—')} journées** de juin à septembre.",
            (f"*Ce qui a été obtenu :* une pente estimée de "
             f"**{m_est:.4f}**"
             + (f", dont l'intervalle de confiance à 95 % vaut "
                f"± {s['validite_ic95_demi_largeur']:.4f}"
                if s.get("validite_ic95_demi_largeur") is not None else "")
             + "." if m_est is not None else ""),
            f"*Pourquoi elle est écartée :* {s.get('validite_critere_rejetant') or '—'}.",
            "*Ce que l'outil publie donc :* les **températures brutes**. La "
            "correction du climat n'est pas appliquée.",
            "⚠ *Ce que cela interdit de conclure :* les pourcentages de "
            "dépassement et les journées de vulnérabilité décrivent **l'année "
            "observée, avec la météo qu'elle a eue** — pas une année standard. "
            "Ce point **n'est comparable ni à un autre point, ni à lui-même "
            "d'une année sur l'autre**. Un été chaud produira des dépassements "
            "sans qu'on puisse dire s'ils viennent du cours d'eau ou du climat.",
            "⚠ *Ce que cela n'autorise pas non plus :* conclure que ce cours "
            "d'eau est insensible à l'air. Une relation qu'on ne peut pas "
            "distinguer de zéro n'est pas une relation nulle : la cause peut "
            "être une chronique trop courte, une station d'air trop éloignée, "
            "ou une alimentation par nappe. L'outil ne les distingue pas.",
            "*La valeur affichée à côté est la pente estimée* — elle n'a pas "
            "été appliquée. Zéro n'est pas une mesure du couplage, c'est la "
            "valeur retenue faute d'en avoir une.",
        ]
    elif val is True:
        lignes.append(
            f"**Relation air-eau établie** sur {s.get('n', '—')} journées "
            f"estivales ; pente **{m_app:.4f}**. Les températures publiées sont "
            f"corrigées du climat de l'année.")
    else:
        niveau = NIVEAU_RESERVE
        lignes.append(
            "Le statut de la relation air-eau n'a pas été évalué sur cette "
            "chronique.")

    fr = res.fraie or {}
    for sous in (fr.get("sous_indicateurs") or []):
        info = sous.get("m_info") or {}
        esp = sous.get("espece") or "espèce"
        if info.get("statut") == "replie":
            niveau = NIVEAU_ALERTE if niveau != NIVEAU_ALERTE else niveau
            lignes.append(
                f"⚠ **{esp} — la relation n'a pas été ré-estimée sur la "
                f"période de reproduction** : {info.get('n', '—')} journées "
                f"seulement, trop peu pour l'établir. La période de "
                f"reproduction est donc corrigée avec la relation de **l'été**, "
                f"ce qui n'est pas la même saison.")
        elif info.get("validite") is False:
            niveau = NIVEAU_ALERTE
            lignes.append(
                f"⛔ **{esp} — relation non établie sur la période de "
                f"reproduction** ({info.get('n', '—')} journées ; "
                f"{info.get('critere_rejetant') or '—'}). Pour cette espèce, "
                f"les températures de cette période sont les **températures "
                f"brutes**. Le diagnostic de reproduction porte sur l'année "
                f"observée. **Le statut est par espèce** : une autre espèce du "
                f"même point peut avoir une relation établie.")
    return _bloc(niveau, "Relation entre la température de l'air et celle de "
                         "l'eau", lignes)


def _etat_normales(res):
    """Les normales de référence."""
    dn = res.diag_normales or {}
    av = dn.get("avertissements") or []
    n = dn.get("n_annees_ref")
    if av:
        return _bloc(NIVEAU_RESERVE, "Normales de référence",
                     [f"**{a}**" for a in av]
                     + ["Les anomalies climatiques, et donc les températures "
                        "corrigées, reposent sur ces normales."])
    return _bloc(NIVEAU_VERIFIE, "Normales de référence",
                 [f"Normales calculées sur **{n} années** de la période de "
                  f"référence." if n else
                  "Normales calculées sur la période de référence."])


def _etat_indicateurs_descriptifs(res):
    """Ce que l'outil publie sans l'avoir vérifié."""
    return _bloc(
        NIVEAU_RESERVE, "Indicateurs descriptifs — une réserve de lecture",
        ["La **température moyenne maximale sur 30 jours** publiée dans les "
         "indicateurs mensuels est calculée sur **trente mesures journalières "
         "consécutives dans le fichier**, et non sur trente jours du "
         "calendrier. Là où la chronique présente des interruptions, la "
         "fenêtre les enjambe : elle peut donc couvrir une période bien plus "
         "longue que trente jours.",
         "Cet indicateur est **descriptif** : il n'entre dans aucun score, "
         "dans aucun seuil et dans aucun débit de référence. Mais un lecteur "
         "croira lire trente jours si on ne le lui dit pas."])


def etats_declares(res):
    """
    TOUS les états déclarés de ce point de mesure, dans un ordre fixe.

    L'ordre ne change jamais : le lecteur apprend où regarder. Chaque contrôle
    rend un bloc **même quand il n'a rien trouvé**, avec son niveau —
    `verifie`, `reserve` ou `alerte`. Un contrôle absent de la liste serait un
    contrôle dont on ne saurait pas s'il a tourné.
    """
    return [
        _etat_detecteur(res),
        _etat_journees_non_exploitables(res),
        _etat_lecture(res),
        _etat_completude(res),
        _etat_couplage(res),
        _etat_normales(res),
        _etat_indicateurs_descriptifs(res),
    ]


_MARQUEURS = ("**", "*", "⚠ ", "⛔ ", "· ")


def etats_declares_texte(res):
    """
    Les mêmes blocs, sans balisage, pour les livrables qui ne savent pas le
    rendre — Word et Excel.

    Le TEXTE est écrit une seule fois, dans `etats_declares`. Cette fonction
    n'en produit pas d'autre : elle retire les marques d'emphase. Deux
    rédactions parallèles finiraient par diverger, et c'est le livrable qui
    porterait la version périmée.
    """
    sortie = []
    for b in etats_declares(res):
        lignes = []
        for l in b["lignes"]:
            for m in _MARQUEURS:
                l = l.replace(m, "")
            lignes.append(l.strip())
        sortie.append(dict(niveau=b["niveau"], titre=b["titre"],
                           lignes=lignes))
    return sortie


# Les deux tables de rendu : un verdict court et une couleur, pour les
# livrables qui attendent la forme habituelle d'un encadre. Le NIVEAU reste
# celui des etats declares ; seule sa presentation change.
VERDICT_ETAT = {NIVEAU_ALERTE: "point d'attention",
                NIVEAU_RESERVE: "réserve de lecture",
                NIVEAU_VERIFIE: "vérifié, rien à signaler"}
COULEUR_ETAT = {NIVEAU_ALERTE: "alerte", NIVEAU_RESERVE: "attention",
                NIVEAU_VERIFIE: "ok"}


def statut_normalisation(res):
    """
    Une phrase, et une seule : la température publiée est-elle corrigée du
    climat, ou brute ?

    C'est le trou que D68 ferme. Un point dont le coefficient est rejeté
    publie des scores calculés sur des températures brutes,
    typographiquement identiques à ceux d'un point normalisé.
    """
    s = res.sensibilite or {}
    v = s.get("validite")
    if v is False:
        return (NIVEAU_ALERTE, "ATTENTION — températures BRUTES. La relation air-eau n'a pas "
                "pu être établie sur cette chronique : la correction du climat "
                "n'est pas appliquée. Les pourcentages et les journées de "
                "vulnérabilité ci-dessous décrivent l'année observée, avec la "
                "météo qu'elle a eue. Ce point n'est comparable ni à un autre "
                "point, ni à lui-même d'une année sur l'autre.")
    if v is True:
        return (NIVEAU_VERIFIE, "Températures corrigées du climat de l'année (relation "
                "air-eau établie). Les valeurs sont comparables entre points "
                "et entre années.")
    return (NIVEAU_RESERVE,
            "Statut de la relation air-eau non évalué sur cette chronique.")


def resume_etats(res):
    """
    Une ligne, pour la vue de synthèse : combien d'alertes, combien de
    réserves, combien de contrôles passés sans rien à signaler.

    Elle existe pour qu'un lecteur qui n'ouvre jamais le détail sache
    néanmoins s'il devrait l'ouvrir.
    """
    b = etats_declares(res)
    a = sum(1 for x in b if x["niveau"] == NIVEAU_ALERTE)
    r = sum(1 for x in b if x["niveau"] == NIVEAU_RESERVE)
    v = sum(1 for x in b if x["niveau"] == NIVEAU_VERIFIE)
    if a:
        return (NIVEAU_ALERTE,
                f"{a} point(s) d'attention, {r} réserve(s), {v} contrôle(s) "
                f"sans rien à signaler.")
    if r:
        return (NIVEAU_RESERVE,
                f"{r} réserve(s) de lecture, {v} contrôle(s) sans rien à "
                f"signaler. Aucun point d'attention.")
    return (NIVEAU_VERIFIE,
            f"{v} contrôle(s) ont tourné et n'ont rien à signaler.")
