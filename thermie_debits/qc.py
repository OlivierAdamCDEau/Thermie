"""
qc.py — Contrôle qualité / nettoyage des artefacts (package thermie_debits).

Détecteurs paramétrables : bornes physiques, sonde hors d'eau (exondation),
plateau (sonde bloquée), outliers MAD. Chaque exclusion est tracée avec son
motif. Le paramétrage arrive via un dict (voir QCConfig.to_legacy_dict()).

CORRECTIF 3 (V4.6) — MARQUER PLUTÔT QUE SUPPRIMER
--------------------------------------------------
Le contrôle qualité produisait une chronique AMPUTÉE : les journées écartées
disparaissaient de la sortie, et seule leur trace subsistait dans un rapport
séparé. Deux conséquences, dont une bloquante pour la suite :

  1. Une journée écartée par DEUX détecteurs ne gardait que le motif du
     premier. L'ancien `_marque` n'écrivait le motif que là où le drapeau
     n'était pas encore posé ; la contribution du second détecteur était
     perdue sans trace.
  2. Un état à deux valeurs — présent ou absent — ne peut pas porter la
     distinction dont le détecteur de mise hors d'eau a besoin : un jour
     qu'on n'a PAS PU diagnostiquer n'est ni écarté ni sain.

`marquer_qualite()` produit désormais une table où CHAQUE journée lue reste
présente, avec :

    statut   'retenu' | 'ecarte' | 'non_diagnosticable'
    motifs   la LISTE de tous les motifs applicables, pas le premier seulement
    motif    le PREMIER motif — la sémantique exacte de la version antérieure

`controle_qualite()` est conservée à l'identique — même signature, même
retour — et devient l'ADAPTATEUR qui rend à l'aval la vue filtrée qu'il
attend. Aucun appelant n'a besoin de savoir que le marquage existe.

POURQUOI `motif` RESTE LE PREMIER MOTIF, ET NON LA LISTE JOINTE
---------------------------------------------------------------
Une première version joignait les motifs dans `motif`. C'était une erreur de
conception, même si aucune journée du corpus de test n'en portait deux :
`redaction.py:76` extrait la famille d'un motif par l'expression
`^([^—(]+)`, et aurait lu la chaîne jointe. L'invariance de l'adaptateur
aurait donc reposé sur une PROPRIÉTÉ DU JEU DE TEST — l'absence de journée à
deux motifs — et non sur sa construction. Un adaptateur dont l'invariance
dépend des données n'en est pas un.

La vue héritée rend donc `motif` = `motifs[0]`, ce que produisait exactement
l'ancien `_marque` : le motif du premier détecteur qui a marqué la journée,
l'ordre des détecteurs étant inchangé. La liste complète vit dans `motifs`,
que seul le périmètre lit.

Le statut 'non_diagnosticable' n'a AUCUN producteur aujourd'hui : aucun des
quatre détecteurs de la version en service ne s'abstient — chacun tranche sur
toute journée qu'il examine. Il est créé vide, et le restera jusqu'au
correctif 1, dont le détecteur relatif s'abstiendra quand la dispersion du
couple (point, mois) est nulle ou le mois trop court.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


# États possibles d'une journée. Trois valeurs, dont une sans producteur.
STATUT_RETENU = "retenu"
STATUT_ECARTE = "ecarte"
STATUT_NON_DIAGNOSTICABLE = "non_diagnosticable"

# Séparateur employé quand on veut afficher la liste complète — jamais dans
# la vue héritée, dont la colonne `motif` reste le premier motif seul.
SEP_MOTIFS = " + "

# Colonnes de travail, retirées de la vue filtrée rendue à l'aval.
_COLS_TRAVAIL = ["statut", "motifs", "motif", "date_dt", "month", "year",
                 "T_air",
                 # TN et TX viennent de la jointure avec l'air faite ici ;
                 # `fusionner` les reprend de `df_air` pour son propre compte.
                 # Les laisser passer dupliquerait des colonnes en aval.
                 "TN", "TX",
                 # D57 — valeurs de diagnostic du détecteur, publiées dans la
                 # table de marquage et dans les artefacts, jamais dans la
                 # vue héritée que l'aval consomme.
                 "E_moy_rel", "R_ampl_rel", "E_max_rel", "longueur_episode",
                 # CORRECTIF 13 — le second membre de la marche 1 (D111).
                 "T_eau_ecart_median",
                 "marche_active"]


# ------------------------------------------------------------------
# La fenêtre glissante CALENDAIRE (correctif 2, étendue à l'écart-type)
# ------------------------------------------------------------------
def fenetre_mobile_calendaire(dates, valeurs, fenetre, min_periods,
                              agregat="mean"):
    """
    Agrégat mobile centré sur une fenêtre de `fenetre` JOURS CALENDAIRES.

    `Series.rolling(window=w)` compte des LIGNES, pas des jours : une fenêtre
    de `w` lignes n'est une fenêtre de `w` jours que si la série est continue.
    Dès qu'une lacune s'ouvre, la fenêtre l'enjambe et agrège des valeurs
    séparées de plusieurs mois.

    La série est donc réindexée sur un calendrier journalier CONTINU entre sa
    première et sa dernière date. Les jours absents y occupent leur place sans
    y apporter de valeur : ce sont des NaN. La fenêtre compte alors des JOURS,
    et `min_periods` compte les jours réellement observés parmi eux. Le
    résultat est ramené sur l'index d'origine — ni ligne ajoutée, ni ligne
    perdue.

    `agregat` vaut "mean" ou "std". C'est la seule différence entre l'usage
    qu'en fait la normalisation (`core.moyenne_mobile_calendaire`) et celui
    qu'en fait le détecteur de plateau ci-dessous.

    Cette fonction vit dans `qc.py` plutôt que dans `core.py` parce que
    `core` importe `qc` : c'est le seul placement qui donne UNE implémentation
    aux deux usages sans import circulaire.
    """
    s = pd.Series(np.asarray(valeurs, dtype=float),
                  index=pd.to_datetime(pd.Series(dates).to_numpy()))
    if s.empty:
        return s.to_numpy()
    plein = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"))
    r = plein.rolling(window=fenetre, center=True, min_periods=min_periods)
    agg = r.std() if agregat == "std" else r.mean()
    return agg.reindex(s.index).to_numpy()


# ------------------------------------------------------------------
# CORRECTIF 1 — LE DÉTECTEUR DE MISE HORS D'EAU, RELATIF, À DEUX MARCHES
# ------------------------------------------------------------------
# Spécification : docs/SPEC_detecteur_et_validite.md, §1.
#
# Ce que le détecteur remplace : le critère ABSOLU `T_eau_max − T_air > seuil`
# assorti d'une grille annuelle et, le cas échéant, de l'exclusion de la
# saison estivale entière. Il supposait qu'un écart eau-air de tant de degrés
# signifie la même chose sur tous les cours d'eau et à tous les mois.
#
# Ce qui le remplace : chaque grandeur est comparée à l'habitude du MÊME point
# au MÊME mois, et le seuil `k` se lit en écarts-types robustes.

# Facteur du MAD robuste. Convention statistique : il fait de MAD* un
# estimateur de l'écart-type, de sorte que `k` se lise en écarts-types.
FACTEUR_MAD = 1.4826

MOTIF_MARCHE1 = "hors d'eau — socle relatif"
MOTIF_MARCHE2 = "hors d'eau — conjonction forme et niveau"
MOTIF_NON_DIAG_M1 = ("non diagnosticable — le socle relatif ne peut pas se "
                     "prononcer")


def relativiser(valeurs, groupes, plancher_dispersion, min_jours_groupe):
    """
    `G_rel = (G − médiane) / MAD*`, calculé PAR GROUPE (le mois du point).

    Retourne `(rel, diagnosticable)`. Un groupe est déclaré NON
    diagnosticable, et ses jours ne reçoivent alors ni valeur relative ni
    verdict, si sa dispersion est nulle ou quasi nulle (`MAD* ≤ plancher`) ou
    s'il compte moins de `min_jours_groupe` jours. Dans les deux cas, une
    médiane et un MAD ne décrivent rien : le détecteur s'abstient au lieu de
    trancher sur du bruit.

    La médiane et le MAD sont dérivés du JEU TRAITÉ, jamais importés. Le
    regroupement est par mois du point traité, jamais entre points : D41
    interdit qu'une règle dépende d'un corpus multi-points.
    """
    rel = pd.Series(np.nan, index=valeurs.index, dtype=float)
    diag = pd.Series(False, index=valeurs.index)
    utilisable = valeurs.notna()
    if not utilisable.any():
        return rel, diag
    for _cle, idx in valeurs[utilisable].groupby(groupes[utilisable]).groups.items():
        v = valeurs.loc[idx]
        if len(v) < min_jours_groupe:
            continue
        med = float(v.median())
        mad = FACTEUR_MAD * float((v - med).abs().median())
        if not (mad > plancher_dispersion):
            continue
        rel.loc[idx] = (v - med) / mad
        diag.loc[idx] = True
    return rel, diag


def ecart_a_la_mediane(valeurs, groupes, min_jours_groupe):
    """
    CORRECTIF 13, SECOND MEMBRE (D111) — `G − médiane_{groupe}(G)`, par groupe
    (le mois du point). Retourne `(ecart, se_prononce)`.

    C'est un TEST DE SIGNE, et c'est pourquoi il ne divise pas. `relativiser`
    rapporte l'écart au MAD parce qu'elle compare une magnitude à un seuil `k` ;
    ici la seule question est **de quel côté de la médiane** la journée se
    trouve. Zéro n'est pas un seuil calibré sur ce corpus : c'est la frontière
    du phénomène.

    Un seul garde-fou, et c'est le paramètre qui existe déjà : le groupe doit
    compter au moins `min_jours_groupe` journées, faute de quoi sa médiane ne
    décrit rien. Le `plancher_dispersion` n'est PAS repris (D116) — il protège
    une division qui n'a pas lieu ici, et la mesure d'étape 20 a établi qu'il
    ne changeait aucune journée du corpus.

    Quand le groupe est trop mince, le second membre NE SE PRONONCE PAS : la
    conjonction ne peut alors pas être satisfaite, et l'abstention est déclarée
    (D100).
    """
    ecart = pd.Series(np.nan, index=valeurs.index, dtype=float)
    dit = pd.Series(False, index=valeurs.index)
    utilisable = valeurs.notna()
    if not utilisable.any():
        return ecart, dit
    for _cle, idx in valeurs[utilisable].groupby(groupes[utilisable]).groups.items():
        v = valeurs.loc[idx]
        if len(v) < min_jours_groupe:
            continue
        ecart.loc[idx] = v - float(v.median())
        dit.loc[idx] = True
    return ecart, dit


def longueurs_episodes(dates, marque):
    """
    Longueur, en jours CALENDAIRES contigus, de l'épisode auquel appartient
    chaque journée marquée. 0 pour les journées non marquées.

    `min_jours_episode` vaut 1 par défaut (D38) : aucune journée n'est écartée
    sur la seule longueur de son épisode. La longueur reste calculée et
    PUBLIÉE — c'est un attribut de diagnostic (D57), pas un filtre.
    """
    n = len(dates)
    out = np.zeros(n, dtype=int)
    if n == 0:
        return out
    d = pd.to_datetime(pd.Series(dates).to_numpy())
    jours = (d - d.min()).days.to_numpy()
    m = np.asarray(marque, dtype=bool)
    i = 0
    while i < n:
        if not m[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and m[j + 1] and jours[j + 1] == jours[j] + 1:
            j += 1
        out[i:j + 1] = j - i + 1
        i = j + 1
    return out


def marquer_qualite(daily_eau, df_air, qc, verbose=True, diag=None):
    """
    Applique les détecteurs d'artefacts activés dans `qc` sur la chronique
    journalière, et MARQUE chaque journée au lieu d'en supprimer.

    D48 — `diag`, S'IL EST FOURNI, EST REMPLI DE CE QUE LES DÉTECTEURS ONT FAIT.
    Jusqu'ici, l'état du détecteur de mise hors d'eau — marche 2 disponible ou
    non, seuil d'amplitude dérivé, journées marquées par chaque marche,
    abstentions — était IMPRIMÉ puis perdu. Sur trois jeux du corpus sur six,
    aucune journée n'est écartée : `marche_active` n'apparaît alors nulle part,
    et l'écran ne peut pas distinguer « le détecteur a tourné et n'a rien
    trouvé » de « le détecteur n'a pas tourné ». Il affichait la même chose
    dans les deux cas.

    L'adaptateur habituel — une fonction enrichie et une vue héritée — ne peut
    rien ici : le diagnostic n'est pas DÉRIVABLE de la table de marquage. Un
    dictionnaire facultatif, rempli sur demande, laisse tous les appelants
    existants inchangés.

    Retourne un DataFrame de MÊME LONGUEUR que `daily_eau`, trié par date,
    portant les colonnes d'origine plus :

        statut  'retenu' | 'ecarte' | 'non_diagnosticable'
        motifs  liste des motifs applicables (vide si retenu)
        motif   les motifs joints par SEP_MOTIFS (chaîne vide si retenu)

    Les détecteurs sont volontairement conservateurs et indépendants : on
    n'invalide que ce qui est diagnostiqué, en traçant chaque exclusion. Ils
    sont appliqués dans l'ordre historique — bornes, plateau, hors d'eau,
    MAD —, ce qui fixe l'ordre des motifs dans la liste : le premier motif
    d'une journée est celui que la version antérieure lui donnait.
    """
    df = daily_eau.merge(df_air, on="date", how="left").copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df["month"]   = df["date_dt"].dt.month
    df["year"]    = df["date_dt"].dt.year
    df = df.sort_values("date_dt").reset_index(drop=True)

    df["statut"] = STATUT_RETENU
    df["motifs"] = [[] for _ in range(len(df))]

    # D48 — ce que les détecteurs auront fait, qu'ils trouvent quelque chose
    # ou non. Rempli au fil de la fonction ; les valeurs par défaut décrivent
    # un détecteur qui n'a pas tourné, ce qui est le cas quand `qc` le
    # désactive.
    _d = diag if isinstance(diag, dict) else {}
    _d.update(
        journees_lues=int(len(df)),
        air_apparie=int(df["T_air"].notna().sum()) if "T_air" in df.columns else 0,
        bornes_actif=bool(qc.get("bornes_physiques")),
        plateau_actif=bool(qc.get("plateau")),
        mad_actif=bool(qc.get("mad_outliers")),
        hors_eau_actif=bool(qc.get("hors_eau")),
        hors_eau_execute=False,
        marche2_disponible=False,
        motif_marche2="",
        signe_actif=False, n_signe_muet=0, n_bloquees_par_signe=0,
        mois_signe_muet=[],
        n_marche1=0, n_marche2=0, n_non_diagnosticables=0,
        n_diagnosticables=0, seuil_amplitude_air=None,
        structure_infra_journaliere=bool(
            "T_eau_min" in df.columns and "T_eau_max" in df.columns
            and (df["T_eau_max"] - df["T_eau_min"]).abs().gt(0).any()))

    def _marque(mask, motif):
        """
        Marque `mask` comme écarté et AJOUTE `motif` à la liste de chaque
        journée concernée — y compris celles qu'un détecteur précédent avait
        déjà marquées. C'est là que le correctif porte.

        Retourne le nombre de journées NOUVELLEMENT écartées : c'est ce
        décompte, et non le total du détecteur, que le journal a toujours
        affiché. Le conserver garde la sortie console inchangée.
        """
        mask = mask.fillna(False) if hasattr(mask, "fillna") else mask
        nouveau = int((mask & (df["statut"] == STATUT_RETENU)).sum())
        for i in df.index[mask]:
            df.at[i, "motifs"] = df.at[i, "motifs"] + [motif]
        df.loc[mask, "statut"] = STATUT_ECARTE
        return nouveau

    log = []

    # 1) Bornes physiques
    if qc.get("bornes_physiques"):
        m = (df["T_eau_moy"] < qc["T_eau_min"]) | (df["T_eau_moy"] > qc["T_eau_max"]) \
            | (df["T_eau_max"] > qc["T_eau_max"])
        n = _marque(m, f"hors bornes [{qc['T_eau_min']};{qc['T_eau_max']}]°C")
        log.append(("Bornes physiques", n))

    # 2) Plateau / sonde bloquée (écart-type glissant ~nul)
    #
    # POSE 1 DU CORRECTIF 1 (D46) — index CALENDAIRE.
    # Cet écart-type glissant portait sur un index POSITIONNEL : une fenêtre
    # de `w` lignes n'est une fenêtre de `w` jours que si la série est
    # continue. Une sonde immobile de part et d'autre d'une lacune de six mois
    # pouvait ainsi être déclarée « bloquée » sur la foi de journées sans
    # rapport, et l'inverse aussi bien.
    #
    # `fenetre` et `min_periods` sont inchangés : `min_periods = w` exige
    # désormais `w` jours réellement observés dans la fenêtre calendaire, ce
    # qui est le sens que cette exigence avait toujours voulu avoir.
    #
    # Mesuré à l'étape 6 avant correction, sans l'appliquer
    # (`out/etape6/C4_plateau_hors_perimetre.csv`) : sur les 32 points du
    # corpus, AUCUN verdict de plateau ne change. Le défaut est réel dans le
    # code et n'était pas exercé par ce corpus.
    if qc.get("plateau"):
        w = qc["plateau_fenetre"]
        roll_std = pd.Series(
            fenetre_mobile_calendaire(df["date"], df["T_eau_moy"], w, w, "std"),
            index=df.index)
        m = roll_std < qc["plateau_ecart_type_min"]
        # ne pas flaguer les périodes hivernales stables proches de 0°C par gel
        n = _marque(m.fillna(False),
                    f"plateau σ<{qc['plateau_ecart_type_min']}°C/{w}j (sonde bloquée)")
        log.append(("Plateau/sonde bloquée", n))

    # 3) Sonde hors d'eau — DÉTECTEUR RELATIF À DEUX MARCHES (correctif 1)
    #    Spécification §1. Les deux marches s'unissent : la marche 2 n'est pas
    #    une substitution de la marche 1, c'est un second chemin.
    df["E_moy_rel"] = np.nan
    df["R_ampl_rel"] = np.nan
    df["E_max_rel"] = np.nan
    df["T_eau_ecart_median"] = np.nan
    df["longueur_episode"] = 0
    df["marche_active"] = ""
    if qc.get("hors_eau"):
        mois = list(qc["hors_eau_mois"])
        k = qc["k"]
        plancher = qc["plancher_dispersion"]
        min_groupe = qc["min_jours_groupe"]
        min_episode = qc["min_jours_episode"]
        dans_fenetre = df["month"].isin(mois)

        # ---- Marche 1 — LE SOCLE. Toujours active : elle ne demande que
        # `T_eau_max`, que V4.5 calcule déjà, et `TM`, que la station d'air
        # fournit. C'est la marche qui ne peut pas manquer.
        e_moy = (df["T_eau_max"] - df["T_air"]).where(
            dans_fenetre & df["T_air"].notna())
        rel1, diag1 = relativiser(e_moy, df["month"], plancher, min_groupe)
        df["E_moy_rel"] = rel1

        # CORRECTIF 13, SECOND MEMBRE (D111, D112, D115) — L'ÉCART NE DIT PAS
        # LEQUEL DES DEUX TERMES A BOUGÉ.
        # `e_moy = T_eau_max − T_air` est grand aussi bien quand l'eau monte
        # que quand l'air descend. Le 1er juin 2011, l'air à 4,6 °C — sous le
        # 5e centile de sa propre fenêtre — a fait marquer SEPT sondes de la
        # Bienne dont l'eau était à ou sous sa médiane de juin. Le second
        # membre tranche cette ambiguïté, et rien d'autre : il ne détecte pas,
        # il répond à « ce découplage vient-il de l'eau ou de l'air ».
        #
        # Il répare donc un défaut du CORRECTIF 1 lui-même, découvert par
        # mesure ; il n'est pas une contrepartie de l'extension de fenêtre.
        ecart_med, dit_signe = ecart_a_la_mediane(
            df["T_eau_max"].where(dans_fenetre), df["month"], min_groupe)
        df["T_eau_ecart_median"] = ecart_med
        _d["signe_actif"] = True
        _d["n_signe_muet"] = int((dans_fenetre & ~dit_signe).sum())
        # D121 — les MOIS ou le second membre ne se prononce pas. L'ecran doit
        # pouvoir les nommer : « il s'abstient » sans dire ou n'apprend rien.
        _d["mois_signe_muet"] = sorted(
            {int(m) for m in df.loc[dans_fenetre & ~dit_signe, "month"]})
        _d["n_bloquees_par_signe"] = int(
            (diag1 & (rel1 > k) & ~(dit_signe & (ecart_med > 0))).fillna(False).sum())
        marche1 = (diag1 & dit_signe & (rel1 > k)
                   & (ecart_med > 0)).fillna(False)

        # ---- Marche 2 — LA CONJONCTION forme ET niveau. Disponible seulement
        # si `TN`, `TX` et `T_eau_min` le sont. Son indisponibilité est
        # DÉCLARÉE, jamais silencieuse : `marche_active` le dit journée par
        # journée, et le journal le dit une fois pour la chronique.
        a_tn_tx = ("TN" in df.columns and "TX" in df.columns
                   and df["TN"].notna().any() and df["TX"].notna().any())
        a_min = "T_eau_min" in df.columns and df["T_eau_min"].notna().any()
        marche2_disponible = bool(a_tn_tx and a_min)
        _d["hors_eau_execute"] = True
        _d["marche2_disponible"] = marche2_disponible
        if not marche2_disponible:
            _manque = []
            if not a_tn_tx:
                _manque.append("TN et TX (station d'air)")
            if not a_min:
                _manque.append("T_eau_min (structure infra-journalière)")
            _d["motif_marche2"] = " et ".join(_manque) + " absents"
        marche2 = pd.Series(False, index=df.index)
        seuil_ampl = np.nan
        if marche2_disponible:
            ampl_air = df["TX"] - df["TN"]
            ampl_eau = df["T_eau_max"] - df["T_eau_min"]
            # Garde-fou d'amplitude d'air : un rapport dont le dénominateur
            # tend vers zéro n'a rien à comparer. Le seuil est DÉRIVÉ du jeu
            # traité — quantile `q_ampl` de l'amplitude d'air de la station —
            # et non importé d'un bassin (D15).
            a = ampl_air.dropna()
            seuil_ampl = float(a.quantile(qc["q_ampl"])) if len(a) else np.nan
            assez = ampl_air >= seuil_ampl
            r_ampl = (ampl_eau / ampl_air.replace(0, np.nan)).where(
                dans_fenetre & assez)
            e_max = (df["T_eau_max"] - df["TX"]).where(dans_fenetre)
            relR, diagR = relativiser(r_ampl, df["month"], plancher, min_groupe)
            relE, diagE = relativiser(e_max, df["month"], plancher, min_groupe)
            df["R_ampl_rel"], df["E_max_rel"] = relR, relE
            # La conjonction est STRICTE (D56) : les deux membres doivent
            # dépasser. Une journée dont un seul membre dépasse n'est ni
            # marquée ni signalée — la mesure d'étape 9 a établi que ces
            # journées se rangent, sur le témoin indépendant `E_moy_rel`, du
            # côté des journées ordinaires.
            marche2 = (diagR & diagE & (relR > k) & (relE > k)).fillna(False)

        marque_hors_eau = marche1 | marche2

        # ---- Épisodes. `min_jours_episode` vaut 1 par défaut : rien n'est
        # écarté sur la longueur. La longueur est calculée et publiée (D57).
        longueurs = longueurs_episodes(df["date"], marque_hors_eau)
        df["longueur_episode"] = longueurs
        if min_episode > 1:
            marque_hors_eau = marque_hors_eau & (longueurs >= min_episode)

        # ---- Ce que chaque journée doit à chaque marche (D57).
        df.loc[dans_fenetre, "marche_active"] = (
            "marche 1" + (" + marche 2" if marche2_disponible
                          else " (marche 2 indisponible : TN, TX ou "
                               "T_eau_min absents)"))

        n1 = int((marche1 & marque_hors_eau).sum())
        n2 = int((marche2 & ~marche1 & marque_hors_eau).sum())
        _d["n_marche1"] = n1
        _d["n_marche2"] = n2
        _d["n_diagnosticables"] = int((dans_fenetre & diag1).sum())
        _d["seuil_amplitude_air"] = (float(seuil_ampl)
                                     if np.isfinite(seuil_ampl) else None)
        n = _marque(marque_hors_eau, MOTIF_MARCHE1)
        # Le motif exact, marche par marche, remplace le motif générique.
        for i in df.index[marque_hors_eau & marche2 & ~marche1]:
            df.at[i, "motifs"] = [MOTIF_MARCHE2 if x == MOTIF_MARCHE1 else x
                                  for x in df.at[i, "motifs"]]
        for i in df.index[marque_hors_eau & marche1 & marche2]:
            df.at[i, "motifs"] = [
                MOTIF_MARCHE1 + " et " + MOTIF_MARCHE2.split("— ")[1]
                if x == MOTIF_MARCHE1 else x for x in df.at[i, "motifs"]]
        log.append(("Sonde hors d'eau", n))

        # ---- L'abstention. Une journée de la fenêtre que la marche 1 ne sait
        # pas juger n'est ni marquée ni déclarée saine : elle est
        # NON DIAGNOSTICABLE. Elle reste dans la chronique — elle n'a rien de
        # défectueux —, mais l'écran doit pouvoir le dire.
        abstenu = dans_fenetre & ~diag1 & ~marque_hors_eau
        _d["n_non_diagnosticables"] = int(abstenu.sum())
        if abstenu.any():
            for i in df.index[abstenu]:
                df.at[i, "motifs"] = df.at[i, "motifs"] + [MOTIF_NON_DIAG_M1]
            df.loc[abstenu & (df["statut"] == STATUT_RETENU), "statut"] = \
                STATUT_NON_DIAGNOSTICABLE

        if verbose:
            print(f"    ↳ marche 1 : {n1} journee(s) ; marche 2 : {n2} "
                  f"journee(s) supplementaire(s)")
            if not marche2_disponible:
                print("    ↳ marche 2 INDISPONIBLE : TN, TX ou T_eau_min "
                      "absents de la chronique")
            elif np.isfinite(seuil_ampl):
                print(f"    ↳ garde-fou d'amplitude d'air : "
                      f"{seuil_ampl:.2f} degC (quantile {qc['q_ampl']:.0%} "
                      f"du jeu traite)")
            if int(abstenu.sum()):
                print(f"    ↳ {int(abstenu.sum())} journee(s) non "
                      f"diagnosticable(s) par le socle relatif")

    # 4) Outliers MAD sur T_eau_moy
    if qc.get("mad_outliers"):
        base = df.copy()
        if qc.get("mad_mois"):
            base = base[base["month"].isin(qc["mad_mois"])]
        med = base["T_eau_moy"].median()
        mad = (base["T_eau_moy"] - med).abs().median()
        if mad > 0:
            seuil = qc["mad_k"] * mad
            m = (df["T_eau_moy"] - med).abs() > seuil
            if qc.get("mad_mois"):
                m = m & df["month"].isin(qc["mad_mois"])
            n = _marque(m, f"outlier MAD (>{qc['mad_k']}×MAD, |Δméd|>{seuil:.2f}°C)")
            log.append(("Outliers MAD", n))
        else:
            # Le garde-fou du MAD nul : ecrit, documente, et jamais declenche
            # sur ce corpus. Le diagnostic le dit plutot que de le taire.
            log.append(("Outliers MAD", 0))
            _d["mad_nul"] = True

    # `motif` = le PREMIER motif, et lui seul : c'est ce que produisait
    # l'ancien `_marque`, qui n'ecrivait le motif que la ou le drapeau n'etait
    # pas encore pose. La vue heritee est ainsi identique PAR CONSTRUCTION,
    # sans rien devoir au contenu du jeu traite.
    df["motif"] = df["motifs"].apply(lambda ms: ms[0] if ms else "")
    _d["par_detecteur"] = {nom_d: int(n) for nom_d, n in log}
    _d["journees_ecartees"] = int((df["statut"] == STATUT_ECARTE).sum())

    if verbose:
        n_ecarte = int((df["statut"] == STATUT_ECARTE).sum())
        print("  ── Contrôle qualité ──")
        for nom_d, n in log:
            print(f"    {nom_d:28s} : {n:5d} enreg. écartés")
        print(f"    {'TOTAL écarté':28s} : {n_ecarte:5d} / {len(df)} "
              f"({100*n_ecarte/max(len(df),1):.1f}%)")

    return df


# ============================================================
# ADAPTATEUR — la vue que l'aval attend, inchangée
# ============================================================
def vue_retenue(marques):
    """
    La chronique journalière filtrée, telle que l'aval l'a toujours reçue :
    les seules journées retenues, sans aucune colonne de travail, index
    réinitialisé.
    """
    # Le filtre porte sur « NON ÉCARTÉE », et non sur « retenue ».
    # Tant que `non_diagnosticable` n'avait aucun producteur, les deux
    # prédicats coïncidaient. Depuis le correctif 1, le socle relatif peut
    # s'abstenir : une journée dont il ne sait rien dire n'est pas
    # défectueuse et n'a aucune raison de quitter la chronique. La retirer
    # reviendrait à traiter une abstention comme une exclusion.
    cols = [c for c in _COLS_TRAVAIL if c in marques.columns]
    return (marques[marques["statut"] != STATUT_ECARTE]
            .drop(columns=cols)
            .reset_index(drop=True))


def rapport_ecartes(marques):
    """
    Le rapport des journées écartées, tel que l'aval l'a toujours reçu :
    mêmes cinq colonnes, même ordre, même nom de colonne `motif`, et le MÊME
    CONTENU — `motif` y est le premier motif, comme avant le correctif.

    L'enrichissement n'est pas ici : il est dans la colonne `motifs` de la
    table de marquage, que seul le périmètre lit. Cette fonction ne doit rien
    apporter de nouveau, c'est tout son objet.
    """
    return marques[marques["statut"] == STATUT_ECARTE][
        ["date", "T_eau_moy", "T_eau_max", "T_air", "motif"]]


def rapport_ecartes_detaille(marques):
    """
    Le même rapport, augmenté de ce que le marquage a rendu possible :
    la liste complète des motifs et leur nombre.

    Cette vue est destinée au PÉRIMÈTRE — le détecteur du correctif 1 et les
    mesures du harnais. Aucun appelant historique ne la reçoit : ils reçoivent
    `rapport_ecartes`, inchangée.
    """
    d = marques[marques["statut"] == STATUT_ECARTE].copy()
    d["motifs_complets"] = d["motifs"].apply(lambda ms: SEP_MOTIFS.join(ms))
    d["n_motifs"] = d["motifs"].apply(len)
    cols = ["date", "T_eau_moy", "T_eau_max", "T_air", "motif",
            "motifs_complets", "n_motifs"]
    # D57 — les valeurs de diagnostic accompagnent chaque journée marquée.
    cols += [c for c in ("E_moy_rel", "R_ampl_rel", "E_max_rel",
                         "longueur_episode", "T_eau_ecart_median",
                         "marche_active")
             if c in d.columns]
    return d[cols]


def non_diagnosticables(marques):
    """
    Les journées qu'aucun détecteur n'a pu trancher.

    Vide aujourd'hui : les quatre détecteurs de la version en service
    tranchent sur toute journée qu'ils examinent. La fonction existe pour que
    le correctif 1 ait où déposer ses abstentions, et pour que leur absence
    actuelle soit vérifiable plutôt que supposée.
    """
    return marques[marques["statut"] == STATUT_NON_DIAGNOSTICABLE]


def controle_qualite(daily_eau, df_air, qc, verbose=True):
    """
    ADAPTATEUR — signature et valeur de retour inchangées.

    Applique les détecteurs d'artefacts activés dans `qc` sur la chronique
    journalière de température d'eau (déjà fusionnée avec l'air pour le
    diagnostic hors d'eau). Retourne (daily_propre, rapport) où `rapport`
    est un DataFrame des enregistrements écartés avec le motif.

    Les détecteurs sont volontairement conservateurs et indépendants : on
    n'invalide que ce qui est diagnostiqué, en traçant chaque exclusion.

    Le marquage complet — statut à trois valeurs et liste de motifs — est
    obtenu par `marquer_qualite()`, dont cette fonction n'est qu'une vue.
    """
    marques = marquer_qualite(daily_eau, df_air, qc, verbose=verbose)
    return vue_retenue(marques), rapport_ecartes(marques)
