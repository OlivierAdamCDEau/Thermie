"""
temoin_regime.py — D96 : LA REGLE DU TEMOIN « LE POINT COMPARE A LUI-MEME ».

CE FICHIER NE MESURE RIEN ET N'ECRIT RIEN. Il ne contient que la regle, sous
forme de fonctions pures, pour qu'elle puisse etre scellee par empreinte et
eprouvee ensuite sur des populations qu'elle n'a pas vues. Les scripts de
mesure l'importent ; ils ne la reecrivent pas.

AUCUNE MODIFICATION APPLICATIVE N'EN DECOULE. Ce temoin n'entre pas dans
`app/`. Il sert a verifier le detecteur, pas a le remplacer.

================================================================================
D'OU VIENT CETTE REGLE, ET POURQUOI IL FAUT L'EPROUVER AILLEURS
================================================================================
A l'etape 18, une regle de decision scellee a classe six journees en
« evenement thermique reel ». Un temoin construit APRES avoir vu ces journees
— le point compare a lui-meme — les a toutes refutees. Ce temoin a ete publie
comme post hoc et n'a reclasse aucune ligne : c'etait la seule facon honnete de
le presenter, et cela laisse la conclusion VALIDE ET NON PROUVEE.

Le formaliser ici ne suffit pas a la prouver. Une regle ajustee sur les cas
qu'elle doit expliquer les explique toujours. La preuve viendra de son
comportement sur TROIS POPULATIONS QU'ELLE N'A PAS VUES — et surtout sur un
temoin de controle de journees NON marquees, ou elle n'a aucune raison de
sonner. C'est ce test-la qui compte, et il peut echouer.

================================================================================
CE QUE LA REGLE MESURE
================================================================================
Pour une journee J d'un point P, l'ensemble de reference R est constitue des
journees de la chronique de P situees a +/- FENETRE jours calendaires du meme
jour de l'annee, DANS LES AUTRES ANNEES que celle de J. Le point ne se compare
qu'a lui-meme, a la meme saison : aucun autre point n'intervient, aucune valeur
n'est importee (D15, D41).

Deux grandeurs, toutes deux relatives a R :

  EXCURSION      exc = T_eau_moy(J) - max(T_eau_moy sur R)
                 Positive, elle dit que la journee est plus chaude que TOUT ce
                 que le point a jamais montre a cette saison.

  DECOUPLAGE     dec = ecart(J) - q95(ecart sur R),  ecart = T_eau_moy - T_air
                 Positif, il dit que l'eau s'ecarte de l'air plus que dans 95 %
                 de ce que le point a jamais montre a cette saison.

CONTAMINATION DE LA REFERENCE, ET SON SENS. R n'exclut pas les journees que le
detecteur a marquees dans les autres annees. Si un point porte des artefacts a
la meme saison plusieurs annees de suite, son maximum de reference est gonfle
et le temoin SOUS-DETECTE. Le biais va donc vers « compatible », c'est-a-dire
vers l'innocence de la journee examinee. C'est le sens prudent, et il est
declare plutot que corrige : le corriger demanderait de decider quelles
journees de reference sont fausses, ce qui est precisement la question posee.

================================================================================
LA REGLE, ET SES TROIS ISSUES
================================================================================
    artefact        exc > 0  ET  dec > 0
                    La journee est a la fois plus chaude que tout precedent
                    saisonnier du point ET plus decouplee de l'air que 95 % de
                    ses precedents. Aucune des deux conditions ne suffit seule :
                    une annee reellement chaude eleve l'eau ET l'air ensemble,
                    et laisse le decouplage dans son enveloppe habituelle.

    compatible      exc <= 0  OU  dec <= 0
                    La journee tient dans l'histoire thermique du point.

    indeterminable  moins de MIN_ANNEES autres annees, ou moins de MIN_JOURS
                    journees de reference, ou T_air absente.
                    Le temoin s'abstient et le DIT (D100). Un point d'une seule
                    annee ne peut rien en tirer, et il ne doit pas faire semblant.

LE DEBIT N'Y FIGURE PAS (D98). Il dit ou est la riviere, pas ou est la sonde.
L'etape 18 l'avait pris pour un temoin d'exondation et il a produit cinq des six
verdicts faux. Il est retire.

================================================================================
LES DEUX MORPHOLOGIES (D97) — CLASSEES, JAMAIS EXIGEES
================================================================================
R_ampl = (T_eau_max - T_eau_min) / (TX - TN), rapportee aux quantiles estivaux
du point.

    haute amplitude   R_ampl >= q90 du point
                      La sonde nue suit l'air et gagne de l'amplitude.
                      Cas BIE40-3, ou R_ampl depasse 1 : l'eau oscille plus que
                      l'air.

    basse amplitude   R_ampl <= q10 du point
                      La sonde immobilisee en milieu tamponne — chaud, calme,
                      inerte. Cas LA PLAINE : R_ampl 0,13 a 0,20 quand la
                      mediane du point est 0,21.

    intermediaire / inconnue   le reste, ou TN, TX ou T_eau_min absents.

LA MORPHOLOGIE NE PARTICIPE PAS AU VERDICT, et c'est le coeur de la lecon de
l'etape 18. R_ampl POINTE A L'ENVERS sur la seconde morphologie : la meme
valeur basse signifie « riviere inerte, donc vraie » ou « sonde immobilisee,
donc fausse » selon un contexte que R_ampl ne porte pas. Un temoin qui change
de signe selon le cas ne peut pas voter. Il est donc mesure et publie a cote du
verdict, pour decrire ce que le verdict a trouve — jamais pour l'etablir.

Consequence pour le detecteur applicatif, consignee et non posee : la marche 1
(socle relatif sur l'ecart eau-air) capte les deux morphologies, la marche 2
(conjonction sur l'amplitude) ne capte que la premiere. La marche 2 etant
ADDITIVE — `marque = marche1 | marche2`, qc.py:388 — elle ne peut pas masquer
ce que la marche 1 voit. Le desequilibre 60/9 mesure a l'etape 18 est donc
attendu, et sans consequence sur ce qui est ecarte.

================================================================================
CE QUI ME FERAIT CONCLURE QUE LE TEMOIN EST SPECIFIQUE — ECRIT AVANT DE REGARDER
================================================================================
L'epreuve decisive est le TEMOIN DE CONTROLE : des journees NON marquees par le
detecteur, appariees aux 69 marquees par point et par saison. Le temoin n'a
aucune raison d'y sonner. Soit `tau` la proportion de journees de controle qu'il
classe `artefact` :

    tau <= 5 %          SPECIFIQUE. Le temoin ne sonne pas au hasard, et sa
                        refutation des six journees de l'etape 18 tient.

    5 % < tau < 20 %    PARTIELLEMENT SPECIFIQUE. La refutation ne tient que
                        pour les journees a forte marge — celles dont
                        l'excursion depasse largement ce que le temoin produit
                        sur le controle. Les journees a faible marge
                        redeviennent indecidables.

    tau >= 20 %         NON SPECIFIQUE. Le temoin sonne sur des journees
                        ordinaires ; il ne prouve rien des six, et LA CONCLUSION
                        DE L'ETAPE 18 S'AFFAIBLIT. Il faudra le dire ainsi.

Un second signe, subordonne au premier : sur les 42 journees marquees et non
instruites a l'etape 18, un temoin specifique doit classer `artefact` une
proportion NETTEMENT SUPERIEURE a `tau`. Si les deux proportions se rejoignent,
le temoin ne distingue pas les journees marquees des autres, et le premier
critere l'aura deja dit.

LES TROIS ISSUES SONT ACCEPTABLES. Une seule ne l'est pas : deplacer ces seuils
apres avoir vu les proportions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# --- parametres de la regle, fixes ici et nulle part ailleurs
FENETRE = 7          # jours calendaires de part et d'autre
MIN_ANNEES = 2       # autres annees exigees
MIN_JOURS = 10       # journees de reference exigees
Q_DECOUPLAGE = 0.95  # quantile de l'ecart eau-air servant de reference

ARTEFACT, COMPATIBLE, INDETERMINABLE = "artefact", "compatible", "indeterminable"
HAUTE, BASSE, INTER, INCONNUE = ("haute amplitude", "basse amplitude",
                                 "intermediaire", "inconnue")


def reference(df, doy, annee):
    """
    Les journees du point situees a +/- FENETRE jours du jour `doy`, dans les
    annees autres que `annee`. `df` porte les colonnes doy, an, T_eau_moy,
    T_air.
    """
    d = (df["doy"] - doy).abs()
    d = np.minimum(d, 365 - d)
    return df[(d <= FENETRE) & (df["an"] != annee)]


def juger(jour, ref):
    """
    La regle. Rend (verdict, exc, dec, n_annees, n_jours).

    `jour` : dict/Series portant T_eau_moy et T_air.
    `ref`  : DataFrame rendu par `reference`.
    """
    r = ref.dropna(subset=["T_eau_moy", "T_air"])
    n_an, n_j = int(r["an"].nunique()), int(len(r))
    if (n_an < MIN_ANNEES or n_j < MIN_JOURS
            or pd.isna(jour.get("T_eau_moy")) or pd.isna(jour.get("T_air"))):
        return INDETERMINABLE, np.nan, np.nan, n_an, n_j
    exc = float(jour["T_eau_moy"]) - float(r["T_eau_moy"].max())
    ecarts = r["T_eau_moy"] - r["T_air"]
    dec = (float(jour["T_eau_moy"]) - float(jour["T_air"])
           - float(ecarts.quantile(Q_DECOUPLAGE)))
    verdict = ARTEFACT if (exc > 0 and dec > 0) else COMPATIBLE
    return verdict, exc, dec, n_an, n_j


def morphologie(r_ampl, q10, q90):
    """
    D97 — decrit la forme, ne vote pas. Voir l'en-tete : R_ampl pointe a
    l'envers sur la seconde morphologie, donc il ne peut pas etablir un verdict.
    """
    if r_ampl is None or not np.isfinite(r_ampl) or not np.isfinite(q90):
        return INCONNUE
    if r_ampl >= q90:
        return HAUTE
    if np.isfinite(q10) and r_ampl <= q10:
        return BASSE
    return INTER


def verdict_specificite(tau):
    """
    Le critere ecrit d'avance, applique tel quel. `tau` en proportion (0-1).
    """
    if tau <= 0.05:
        return ("SPECIFIQUE",
                "le temoin ne sonne pas au hasard ; sa refutation des six "
                "journees de l'etape 18 tient")
    if tau < 0.20:
        return ("PARTIELLEMENT SPECIFIQUE",
                "la refutation ne tient que pour les journees a forte marge ; "
                "celles a faible marge redeviennent indecidables")
    return ("NON SPECIFIQUE",
            "le temoin sonne sur des journees ordinaires : il ne prouve rien "
            "des six, et la conclusion de l'etape 18 s'affaiblit")
