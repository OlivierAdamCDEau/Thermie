"""
livrer_etape.py — D20 : l'archive de livraison d'une étape.

Construit `out/livraison_etape<N>.zip` contenant TOUT ce que l'étape a produit
ou modifié, plus un `MANIFESTE_LIVRAISON.md` qui liste chaque fichier avec une
ligne disant ce qu'il est et s'il est nouveau ou modifié.

Rien n'est livré hors de cette archive.

La liste des fichiers et leur description sont déclarées explicitement dans
`CONTENU`, jamais devinées : une archive qui se remplit toute seule embarque un
jour un fichier que personne n'a voulu livrer.

USAGE
    python tests/reference/livrer_etape.py 3
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from _commun import RACINE, sha256

OUT = RACINE / "out"

# ------------------------------------------------------------------
# Contenu déclaré, étape par étape.
#   chemin relatif à la racine -> (statut, ce que c'est)
# ------------------------------------------------------------------
CONTENU = {
    21: {
        "docs/etape21_rapport.md": (
            "nouveau",
            "Rapport de CLOTURE. Les trois dettes reglees, la reference "
            "rebasee et l'ancienne conservee, les controles finaux. "
            "Prediction de la pose 1 confirmee : 66 artefacts, 0 bouge."),
        "docs/BILAN_V4_6.md": (
            "nouveau",
            "LIVRABLE POUR LE MAITRE D'OUVRAGE. Sans jargon, sans numero de "
            "decision, sans nom de fonction. Ce que l'outil faisait et ce "
            "qu'il fait ; les treize correctifs ordonnes par importance pour "
            "le lecteur ; le bilan des verdicts station par station ; les "
            "limites sans les adoucir ; ce qu'il faudrait pour lever les "
            "doutes."),
        "docs/CHANTIER_AVAL.md": (
            "nouveau",
            "LIVRABLE POUR LE CHANTIER SUIVANT. Neuf points transmis, chacun "
            "avec sa reference fichier:ligne, la mesure deja faite, et la "
            "decision qui reste a prendre. Que le prochain chantier commence "
            "avec des chiffres et non avec une intuition."),
        "docs/METHODO.md": (
            "modifie",
            "Carnet cumulatif, CLOS. Section de cloture : l'etat final, les "
            "trois references et ce que chacune atteste, et les douze regles "
            "de methode que le chantier a produites."),

        "app/thermie_debits/qc.py": (
            "modifie",
            "D121 — le second membre publie les MOIS ou il s'abstient. "
            "`ecart_a_la_mediane` n'est pas modifiee d'un caractere : le "
            "rejeu a zero artefact deplace le prouve."),
        "app/thermie_debits/redaction.py": (
            "modifie",
            "D121 — le second membre atteint l'ecran, dans l'idiome du bloc "
            "des etats declares. Corrige au passage « periode estivale », "
            "devenu faux au correctif 13."),

        "tests/reference/balayer_chemins_sortie.py": (
            "nouveau",
            "Tache 1.3. Le critere n'est pas « le chemin est-il fige » — "
            "cinquante scripts sur soixante-quatre le sont — mais « le script "
            "peut-il etre rejoue plus tard, et sa sortie est-elle alors "
            "redirigeable ». Ainsi pose : AUCUN script n'ecrit dans une etape "
            "anterieure a la sienne."),
        "tests/reference/rebaser_cloture.py": (
            "nouveau",
            "Le rebasage (D83, branche B). La copie de l'ancienne reference "
            "est VERIFIEE empreinte par empreinte AVANT toute reconstruction "
            "— 78 fichiers, 0 divergence. On ne detruit pas un temoin sur une "
            "copie non verifiee."),
        "tests/reference/eprouver_temoin.py": (
            "modifie",
            "SCEAU ROMPU, DELIBEREMENT ET PAR ECRIT (D121). L'empreinte "
            "d'origine e78f370e... est reproduite en tete du fichier et reste "
            "au dossier de l'etape 19. Seul le chemin de sortie change : "
            "`--sortie`, defaut inchange. La regle et les populations sont "
            "intactes."),
        "tests/reference/verifier_integrite_references.py": (
            "modifie",
            "La TROISIEME reference entre au controle. C'est le seul controle "
            "qui ait un sens sur un temoin fige."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Entree 21 declaree."),

        "tests/reference/SOURCE_CODE.txt": (
            "modifie",
            "D70. La reference decrit desormais V4.6 — source app, etape 21 — "
            "et sa provenance porte la mention des deux temoins V4.5 "
            "conserves a cote."),
        "tests/reference_v4_5/SOURCE_CODE.txt": (
            "nouveau",
            "L'ancienne reference, deplacee telle quelle : V4.5, source ref, "
            "etape 6. C'est contre elle que les treize correctifs ont ete "
            "mesures."),
        "tests/reference_v4_5/MANIFEST.sha256": (
            "nouveau",
            "Le manifeste de l'ancienne reference, copie sans retouche. "
            "66 artefacts, 0 empreinte divergente."),

        "out/etape21/A_empreintes.txt": (
            "nouveau",
            "Les seize sources applicatives, avant et apres : 14 identiques, "
            "2 modifiees et declarees."),
        "out/etape21/B_chemins_sortie.csv": (
            "nouveau",
            "Ou chaque script du harnais ecrit, et le risque de rejeu. "
            "64 scripts, 50 ecrivent dans une etape, 0 dans une etape "
            "anterieure a la sienne."),
        "out/etape21/C_schemas_v45.txt": (
            "nouveau",
            "L'ancienne reference contre un rejeu d'aujourd'hui : 60 "
            "artefacts identiques sur les colonnes communes, 19 colonnes "
            "ajoutees, 0 valeur modifiee. C'est ce qui explique le retour 1 "
            "de check_reference sur les deux temoins V4.5."),
        "out/etape21/D_check_reference_v46.txt": (
            "nouveau", "DIFF VIDE — la reference V4.6 est reproductible."),
        "out/etape21/D_check_reference_v4_5.txt": (
            "nouveau", "Trois artefacts divergent, tous par ajout de colonne."),
        "out/etape21/D_check_reference_cli.txt": (
            "nouveau", "Les memes trois, ce qui confirme la cause unique."),
        "out/etape21/D_check_D70_refus.txt": (
            "nouveau",
            "D70 refuse la comparaison de sources croisees, et le dit avec la "
            "nouvelle provenance : « produite par app, rejeu demande ref »."),
        "out/etape21/F_integrite.txt": (
            "nouveau",
            "Les TROIS manifestes decrivent leurs dossiers : 66 + 66 + 66 "
            "artefacts, 0 empreinte divergente, ref/ propre."),
        "out/etape21/99_console_chemins.txt": (
            "nouveau", "Trace du balayage des chemins de sortie."),
        "out/etape21/99_console_rejeu_pose1.txt": (
            "nouveau",
            "Trace du rejeu qui confirme la prediction de la pose 1."),
        "out/etape21/99_console_temoin_final.txt": (
            "nouveau",
            "Le temoin scelle, une derniere fois, produit via --sortie : la "
            "reparation verifiee par l'usage."),
    },
    20: {
        "docs/etape20_rapport.md": (
            "nouveau",
            "Rapport d'etape 20. CORRECTIF 13 POSE : fenetre etendue a l'annee "
            "entiere (D105) et second membre de la marche 1 en TEST DE SIGNE "
            "(D111, D115). 69 -> 151 journees marquees, 88 sortent, 6 "
            "rentrent, AUCUN VERDICT DEPLACE. Le temoin scelle rejoue sans "
            "modification : tau 0,205 % -> 0,135 %, faux negatifs 186 -> 131."),
        "docs/METHODO.md": (
            "modifie", "Carnet cumulatif. Section « Etape 20 » ajoutee."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Section « correctif 13 ». Aucune categorie deplacee, 17 "
            "valeurs sur 652. Le coefficient de fraie bouge pour la premiere "
            "fois du chantier : +39 % sur La Canner. Trois points nommes, "
            "trois raisons distinctes de ne pas bouger."),
        "docs/SPEC_detecteur_et_validite.md": (
            "modifie",
            "La fenetre passe a l'annee entiere ; le second membre de la "
            "marche 1 est specifie, avec sa justification, son abstention et "
            "sa fuite declaree."),

        "app/thermie_debits/qc.py": (
            "modifie",
            "CORRECTIF 13 — `ecart_a_la_mediane` : un TEST DE SIGNE, qui ne "
            "divise pas. La marche 1 devient une conjonction : ecart relatif "
            "depasse ET eau au-dessus de la mediane de son mois. Repare un "
            "defaut du correctif 1 lui-meme (D112) : un ecart ne dit pas "
            "lequel de ses deux termes a bouge."),
        "app/thermie_debits/config.py": (
            "modifie",
            "`hors_eau_mois` passe de (6,7,8,9) a l'annee entiere (D105). "
            "Seule valeur applicative modifiee."),

        "tests/reference/empreintes_app.py": (
            "nouveau",
            "Remplace `verifier_aucune_pose.py`, dont le temoin etait "
            "l'archive de livraison de l'etape 17 — retiree une fois remise. "
            "Le releve vit dans le harnais, et la liste des sources est "
            "DECOUVERTE : 16, la ou l'ancien controle en suivait 11."),
        "tests/reference/mesure_correctif13.py": (
            "nouveau",
            "La mesure avant pose, SCELLEE, avec ses quatre signaux d'alerte. "
            "Porte un defaut — elle lisait `res.df`, d'ou les journees "
            "marquees sont retirees — declare et non efface."),
        "tests/reference/mesure_correctif13_bis.py": (
            "nouveau",
            "La reprise des signaux A et B, avec les seuils REPRIS MOT POUR "
            "MOT. Le fichier scelle n'est pas modifie ; son empreinte reste "
            "verifiable."),
        "tests/reference/verifier_condition_c13.py": (
            "nouveau",
            "La condition en magnitude, mesuree avant pose. La prediction a "
            "ete DEMENTIE — 37 des 69 echouaient — et le script s'est arrete "
            "sans choisir de variante."),
        "tests/reference/verifier_test_de_signe.py": (
            "nouveau",
            "Le test de signe et ses QUATRE PREDICTIONS, scelles avant "
            "mesure. P1, P3 et P4 tenues ; P2 tenue a 81 %, l'ecart instruit "
            "et non arrondi."),
        "tests/reference/chiffrer_correctif13.py": (
            "nouveau",
            "Les trois chiffrages : les six journees qui rentrent, le "
            "coefficient de fraie par point et par espece, le cout de la "
            "fuite."),
        "tests/reference/reparer_etape19.py": (
            "nouveau",
            "Repare quatre artefacts d'etape 19 que le rejeu du temoin — dont "
            "le chemin de sortie est fige — avait ecrases. La reparation "
            "n'est acceptee qu'apres confrontation a la trace console "
            "survivante, sur huit chiffres."),
        "tests/reference/build_reference.py": (
            "modifie",
            "Deux colonnes a 03 : `T_eau_ecart_median` (D57) et "
            "`motifs_complets`. Cette derniere repare un defaut de comptage : "
            "`motif` est la vue HERITEE, ou une journee ne porte que son "
            "premier motif."),
        "tests/reference/parametres.py": (
            "modifie",
            "Les DEUX tables du cote application passent a l'annee entiere. "
            "Les deux tables QC_REF_* restent a (6,7,8,9) : elles decrivent "
            "V4.5 (D73)."),
        "tests/reference/comparer_chemins.py": (
            "modifie", "La valeur declaree du chemin application suit."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Entree 20 declaree."),

        "out/etape20/REGLE_SCELLEE.txt": (
            "nouveau",
            "Les quatre empreintes, prises avant chaque mesure, et leurs "
            "contre-verifications apres production."),
        "out/etape20/F_integrite.txt": (
            "nouveau", "D76 : 66 + 66 artefacts, 0 divergente, ref/ propre."),
        "out/etape20/D44_ref.txt": (
            "nouveau",
            "D44 cote reference. Cote application, D70 refuse la comparaison "
            "— comportement voulu."),
        "out/etape20/A_avant_apres.csv": (
            "nouveau", "La fenetre nue, par point : marquees avant et apres."),
        "out/etape20/A_verdicts.csv": (
            "nouveau", "Les categories publiees sous la fenetre nue."),
        "out/etape20/B_nouvelles.csv": (
            "nouveau",
            "Les 163 journees de l'extension nue, et leur corroboration par "
            "le temoin scelle de l'etape 19."),
        "out/etape20/C_condition_69.csv": (
            "nouveau",
            "La condition en magnitude sur les 69 : 32 la satisfont, 37 non. "
            "C'est ce fichier qui a arrete la pose."),
        "out/etape20/C_condition_nouvelles.csv": (
            "nouveau", "La meme condition sur les 163 ajoutees."),
        "out/etape20/S_69.csv": (
            "nouveau",
            "Le test de signe sur les 69 : 63 survivent, 6 tombent, toutes du "
            "1er juin 2011, aucune corroboree."),
        "out/etape20/S_nouvelles.csv": (
            "nouveau",
            "Le test de signe sur les 163 : 72 de mai survivent dont les 55 "
            "corroborees, 59 des 73 froides tombent."),
        "out/etape20/S_nommees.csv": (
            "nouveau",
            "Les journees que l'arbitrage nommait, journee par journee."),
        "out/etape20/S_abstentions.csv": (
            "nouveau",
            "Les six couples (point, mois) ou le second membre ne se prononce "
            "pas, tous pour effectif insuffisant (D100)."),
        "out/etape20/R1_journees_estivales.csv": (
            "nouveau", "Les six journees estivales qui rentrent."),
        "out/etape20/R1_m_estival.csv": (
            "nouveau",
            "Leur effet : m_estival, Tmh_norm mediane et p95, verdicts. Ecart "
            "maximal 0,002 sur m ; aucun verdict ne bouge."),
        "out/etape20/R2_m_saisonnier.csv": (
            "nouveau",
            "Le coefficient de fraie, par point et par espece. Huit points "
            "bougent, La Canner de 39 %. P_fraie ne bouge nulle part."),
        "out/etape20/R3_fuite_fraie.csv": (
            "nouveau",
            "Le cout de la fuite : une seule des 14 journees tombe dans une "
            "fenetre de fraie, et c'est une vraie anomalie d'eau."),
        "out/etape20/R4_marquees.csv": (
            "nouveau", "Les 88 qui sortent, les 6 qui rentrent."),
        "out/etape20/temoin/B_synthese.csv": (
            "nouveau",
            "Le temoin rejoue, INCHANGE, meme sceau : tau 0,205 % -> 0,135 %."),
        "out/etape20/temoin/C_faux_negatifs.csv": (
            "nouveau",
            "Les faux negatifs apres pose : 186 -> 131. Sur LA PLAINE, 16 -> "
            "3, et ces trois sont exactement les 2, 3 et 4 juin 2011 que D106 "
            "a nommees."),
        "out/etape20/temoin/C_par_point.csv": (
            "nouveau", "Leur repartition par point, avant et apres."),
        "out/etape20/99_console_mesure.txt": (
            "nouveau",
            "Trace de la mesure scellee, AVEC sa contradiction : « +0 "
            "nouvellement marquees » en face de « 69 -> 232 »."),
        "out/etape20/99_console_mesure_bis.txt": (
            "nouveau", "Trace de la reprise des signaux A et B."),
        "out/etape20/99_console_condition.txt": (
            "nouveau", "Trace de la condition en magnitude, et de son arret."),
        "out/etape20/99_console_signe.txt": (
            "nouveau", "Trace du test de signe et des quatre predictions."),
        "out/etape20/99_console_rejeu_apres.txt": (
            "nouveau", "Trace de la construction des artefacts apres pose."),
        "out/etape20/99_console_rejeu_ref.txt": (
            "nouveau",
            "Trace du rejeu cote V4.5, qui survit sans une valeur deplacee."),
        "out/etape20/99_console_chiffrage.txt": (
            "nouveau", "Trace des trois chiffrages."),
        "out/etape20/99_console_temoin_rejoue.txt": (
            "nouveau", "Trace du temoin rejoue."),
    },
    19: {
        "docs/etape19_rapport.md": (
            "nouveau",
            "Rapport d'etape 19. VERIFICATION SANS POSE. Le temoin « le point "
            "compare a lui-meme » est formalise, scelle, et eprouve sur des "
            "populations qu'il n'a pas vues : tau = 0,205 % sur 6 339 journees "
            "NON marquees contre 42 % sur 42 journees marquees inedites, soit "
            "SPECIFIQUE sous le seuil scelle. La conclusion de l'etape 18 "
            "cesse d'etre valide et non prouvee. La question retournee — les "
            "faux negatifs — met au jour une limite structurelle : plus de la "
            "moitie des journees signalees sont HORS de la fenetre "
            "juin-septembre du detecteur."),
        "docs/METHODO.md": (
            "modifie", "Carnet cumulatif. Section « Etape 19 » ajoutee."),

        "tests/reference/temoin_regime.py": (
            "nouveau",
            "D96 — LA REGLE DU TEMOIN, et rien d'autre : des fonctions pures, "
            "pour qu'elle puisse etre scellee et eprouvee. Excursion ET "
            "decouplage, tous deux relatifs aux autres annees du meme point "
            "(D15, D41). Le debit en est RETIRE (D98). Les deux morphologies "
            "(D97) sont classees, jamais exigees : une grandeur qui change de "
            "signe selon un contexte qu'elle ne porte pas ne peut pas voter. "
            "Le critere de specificite est ecrit dans le fichier scelle."),
        "tests/reference/eprouver_temoin.py": (
            "nouveau",
            "Le PROTOCOLE, scelle au meme titre que la regle : un seuil ecrit "
            "d'avance ne garantit rien si la population qu'il juge est choisie "
            "apres. Definit les quatre populations, dont le temoin de controle "
            "et l'exclusion des journees voisines d'une marquee."),
        "tests/reference/mesure_impact_faux_negatifs.py": (
            "nouveau",
            "Ce que le retrait des journees signalees changerait, MESURE et "
            "non conjecture : les fonctions applicatives sont rappelees telles "
            "quelles sur une chronique filtree. Aucune pose, aucune "
            "proposition d'en faire."),
        "tests/reference/instruire_bie35.py": (
            "nouveau",
            "D99 — BIE35-5__NA instruit hors chaine. L'amont est rejoue a "
            "l'identique et s'arrete avant l'etape qui echoue. Etablit que ce "
            "point ne porte AUCUNE journee marquee hors d'eau : sa chronique "
            "ne contient aucun jour de juin a septembre."),
        "tests/reference/revue_journal_verdicts.py": (
            "nouveau",
            "Tache E — le journal des verdicts confronte a quatorze rejeux "
            "conserves, etapes 10 a 17, 32 points chacun. Controle symetrique : "
            "un point qui bouge sans etre cite, comme un point cite qui ne "
            "bouge pas."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Entree 19 declaree."),

        "out/etape19/REGLE_SCELLEE.txt": (
            "nouveau",
            "Les deux empreintes — regle et protocole — prises avant tout "
            "chiffre, et leur contre-verification apres production."),
        "out/etape19/F_aucune_pose.txt": (
            "nouveau", "11 sources applicatives identiques, 0 divergente."),
        "out/etape19/B_populations.csv": (
            "nouveau",
            "Une ligne par journee jugee du corpus, avec sa population, son "
            "verdict, son excursion, son decouplage et sa morphologie."),
        "out/etape19/B_synthese.csv": (
            "nouveau",
            "Les proportions par population. C'est la ligne B2_controle qui "
            "porte le test : tau = 0,205 %."),
        "out/etape19/C_faux_negatifs.csv": (
            "nouveau",
            "Les 186 journees signalees par le temoin et non marquees par le "
            "detecteur. 95 sont hors de sa fenetre."),
        "out/etape19/C_par_point.csv": (
            "nouveau", "Leur repartition par point, rapportee au taux de fond."),
        "out/etape19/C_impact.csv": (
            "nouveau",
            "Sur quinze points chiffres, un seul verrait un indicateur bouger "
            "— LA PLAINE, dont les deux journees aigues encore publiees sont "
            "du meme bloc artefactuel que les huit deja retirees."),
        "out/etape19/D_bie35.csv": (
            "nouveau",
            "Les quatre journees de BIE35-5__NA, qui relevent du critere de "
            "completude et non du detecteur. Toutes indeterminables : une "
            "seule autre annee disponible, la regle en exige deux."),
        "out/etape19/E_mouvements.csv": (
            "nouveau",
            "Quatre mouvements de categorie, deux points, tous a la pose du "
            "correctif 1, tous deja cites au journal. Les etapes 11 a 17 n'en "
            "deplacent aucun."),
        "out/etape19/99_console_epreuve.txt": (
            "nouveau", "Sortie console integrale de eprouver_temoin.py."),
        "out/etape19/99_console_impact.txt": (
            "nouveau",
            "Sortie console integrale de mesure_impact_faux_negatifs.py."),
        "out/etape19/99_console_bie35.txt": (
            "nouveau", "Sortie console integrale de instruire_bie35.py."),
        "out/etape19/99_console_journal.txt": (
            "nouveau", "Sortie console integrale de revue_journal_verdicts.py."),
    },
    18: {
        "docs/etape18_rapport.md": (
            "nouveau",
            "Rapport d'etape 18. VERIFICATION SANS POSE : le detecteur de mise "
            "hors d'eau ne retire-t-il que des artefacts ? 69 journees "
            "marquees, 27 franchissaient un seuil piscicole, deux points ont "
            "un verdict deplace. La regle de decision, scellee par empreinte "
            "avant le premier chiffre, a classe SIX journees en « evenement "
            "thermique reel » ; le regime propre des points les refute toutes. "
            "L'echec du protocole est la principale information de l'etape."),
        "docs/METHODO.md": (
            "modifie", "Carnet cumulatif. Section « Etape 18 » ajoutee."),

        "tests/reference/verifier_faux_positifs.py": (
            "nouveau",
            "LA REGLE DE DECISION EST EN TETE DE CE FICHIER, et son empreinte "
            "a ete prise avant la premiere execution. Quatre temoins "
            "— amplitude, debit, forme de sortie d'episode, synchronie "
            "spatiale —, tous etalonnes sur les quantiles du point traite "
            "(D15, D41). Le temoin d'amplitude est neutralise la ou la marche "
            "2 a marque, faute de quoi il redirait le detecteur."),
        "tests/reference/mesure_regime_interannuel.py": (
            "nouveau",
            "TEMOIN POST HOC, DECLARE COMME TEL EN TETE DU FICHIER. Construit "
            "APRES avoir vu les journees, il ne reclasse aucune ligne. Le "
            "point se compare a lui-meme, aux memes dates des autres annees "
            "de sa propre chronique."),
        "tests/reference/mesure_cout_verdict.py": (
            "nouveau",
            "Detecteur allume contre detecteur eteint, sur les grandeurs "
            "publiees. Chiffre ce que le marquage a retire au verdict."),
        "tests/reference/verifier_aucune_pose.py": (
            "nouveau",
            "La preuve, octet par octet, qu'aucune source applicative n'a "
            "bouge : chaque fichier de app/ confronte a l'exemplaire scelle "
            "dans livraison_etape17.zip. Un rapport qui se contente "
            "d'affirmer qu'il n'a rien pose ne vaut rien."),
        "tests/reference/livrer_etape.py": (
            "modifie",
            "Entree 18 declaree. La ligne du manifeste qui nomme le fichier "
            "portant la regle de decision etait codee en dur sur "
            "mesure_critere_b.py : elle mentait pour toute etape ulterieure. "
            "Elle est desormais declaree par etape."),

        "out/etape18/REGLE_SCELLEE.txt": (
            "nouveau",
            "L'empreinte SHA-256 de la regle, prise avant le premier chiffre. "
            "Ecrire la regle d'avance ne prouve rien si elle a pu etre "
            "retouchee ensuite."),
        "out/etape18/F_aucune_pose.txt": (
            "nouveau", "11 sources applicatives identiques, 0 divergente."),
        "out/etape18/A_toutes_marquees.csv": (
            "nouveau", "Les 69 journees marquees, seuils franchis ou non."),
        "out/etape18/A_sous_ensemble.csv": (
            "nouveau", "Les 27 qui coutent un verdict."),
        "out/etape18/B_temoins.csv": (
            "nouveau",
            "Les quatre temoins journee par journee, avec les quantiles du "
            "point qui les etalonnent."),
        "out/etape18/B3_episodes.csv": (
            "nouveau",
            "Eau, air, ecart et debit a plus ou moins trois jours de chaque "
            "journee instruite."),
        "out/etape18/C_verdict.csv": (
            "nouveau",
            "Le classement de la regle scellee : 6 exondation, 6 evenement "
            "thermique reel, 15 indecidable."),
        "out/etape18/D_regime_interannuel.csv": (
            "nouveau",
            "Le temoin post hoc. 20 des 27 journees sont hors de tout "
            "precedent saisonnier de leur propre point."),
        "out/etape18/E_cout_verdict.csv": (
            "nouveau",
            "LA PLAINE : Risque Modere -> Risque Faible, huit journees aigues "
            "retirees. La Canner a Vigy 1 : vulnerabilite aigue ponctuelle -> "
            "absence."),
        "out/etape18/99_console_temoins.txt": (
            "nouveau",
            "Sortie console integrale de verifier_faux_positifs.py."),
        "out/etape18/99_console_posthoc.txt": (
            "nouveau",
            "Sortie console integrale de mesure_regime_interannuel.py."),
        "out/etape18/99_console_cout.txt": (
            "nouveau", "Sortie console integrale de mesure_cout_verdict.py."),
    },
    17: {
        "docs/etape17_rapport.md": (
            "nouveau",
            "Rapport d'etape 17. D48, D68 et D93. Le controle qualite RETOURNE "
            "desormais ce qu'il a fait : sur trois jeux sur six, l'ecran ne "
            "pouvait pas distinguer « rien a signaler » de « controle non "
            "execute ». 65 artefacts figes sur 66. Deux contrats rompus "
            "attrapes en construisant reellement les livrables — le premier "
            "perimetre que le harnais ne couvre pas."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Aucun verdict, aucune valeur. Ce qui change est ce que les "
            "livrables DISENT : un point aux temperatures brutes cesse d'etre "
            "typographiquement identique a un point normalise. Ce qui reste "
            "dit nulle part est consigne."),
        "docs/METHODO.md": (
            "modifie", "Carnet cumulatif. Section « Etape 17 » ajoutee."),

        "app/thermie_debits/redaction.py": (
            "modifie",
            "D48 — `etats_declares` : les sept blocs, dans un ordre fixe, "
            "chacun rendu MEME quand il n'a rien trouve. `resume_etats` pour "
            "la synthese, `etats_declares_texte` pour les livrables, "
            "`statut_normalisation` pour D68. Le texte est ecrit UNE fois."),
        "app/thermie_debits/qc.py": (
            "modifie",
            "D48 — `marquer_qualite` remplit un dictionnaire de diagnostic "
            "FACULTATIF. L'etat du detecteur etait imprime et perdu ; sur "
            "trois jeux sur six il n'existait nulle part. L'adaptateur "
            "habituel ne pouvait rien : le diagnostic n'est pas derivable de "
            "la table de marquage."),
        "app/thermie_debits/orchestrator.py": (
            "modifie",
            "D48 — `res.diag_detecteur`. D93 — `daily` passe a "
            "`marquer_completude`."),
        "app/thermie_debits/io_data.py": (
            "modifie",
            "D93 — `n_mesures` rejoint la table de completude, a cote du trou "
            "maximal. Il etait produit depuis l'etape 1 et relu NULLE PART "
            "(I11). La table reste hors de res.df : 01 ne bouge pas."),
        "app/thermie_debits/livrables.py": (
            "modifie",
            "D68 — chapitre 1.7 du Word entre les donnees et les resultats ; "
            "feuille 07_Etats_declares du classeur ; encadre de statut AVANT "
            "les chiffres de vulnerabilite. Rien dans 06_SYNTHESE, dont "
            "l'en-tete est invariant par construction."),
        "app/app.py": (
            "modifie",
            "D48 — un onglet « Ce qui a ete verifie » en deuxieme position, "
            "avec une ligne de resume coloree. « Aucun artefact detecte » "
            "devient « Aucun detecteur n'a ecarte d'enregistrement », suivi "
            "d'un renvoi : le premier enonce etait une conclusion, le second "
            "un constat."),
        "app/thermie_debits/config.py": (
            "inchange depuis l'etape 16", "Completude de D44."),
        "app/thermie_debits/core.py": (
            "inchange depuis l'etape 13", "Completude de D44."),
        "app/thermie_debits/indicateurs.py": (
            "inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/figures.py": (
            "inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/exports.py": (
            "inchange depuis l'etape 14",
            "NON TOUCHE, et c'est dit : il ne porte que le classeur de detail "
            "de la fraie. Le statut par espece figure dans le bloc general."),

        "tests/reference/build_reference.py": (
            "modifie", "D93 — 03_journees_ecartees gagne la colonne "
                       "n_mesures, renseignee pour les lignes de completude."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 17 declare."),

        "out/etape17/D44_avant.csv": ("nouveau", "D44 avant : onze entrees."),
        "out/etape17/D44_apres.csv": (
            "nouveau", "D44 apres : DOUZE — redaction.py rejoint la liste au "
                       "titre de D68. Retour 0, aucun CRLF."),
        "out/etape17/A_diff_app_ref_avant.txt": ("nouveau", "D44 avant, integral."),
        "out/etape17/A_diff_app_ref_apres.txt": ("nouveau", "D44 apres : CONFORME."),
        "out/etape17/F_integrite_avant.txt": ("nouveau", "D76 avant : retour 0."),
        "out/etape17/F_integrite_apres.txt": ("nouveau", "D76 apres : retour 0."),

        "out/etape17/P1_effet.txt": (
            "nouveau",
            "POSE 1 (D93) : 03 bouge d'une colonne, 0 valeur changee ; "
            "01_colonnes_retenues.json FIGE — le piege de l'etape 16 pris dans "
            "l'autre sens ; 99_log bouge d'une ligne, motif manque (D80bis)."),
        "out/etape17/P1_effet.csv": ("nouveau", "POSE 1 : detail par artefact."),
        "out/etape17/P1_console_rejeu.txt": ("nouveau", "POSE 1 : le rejeu."),

        "out/etape17/P2_bloc_exemples.txt": (
            "nouveau",
            "LE BLOC RENDU sur trois points contrastes : un sans rien a "
            "signaler, un dont les horodatages sont detruits, un dont un tiers "
            "de la chronique est perdue. C'est cette lecture qui a montre "
            "qu'un cas de la specification manquait."),
        "out/etape17/P2_effet.txt": (
            "nouveau",
            "POSES 2 et 3 : 65 artefacts figes sur 66. Le seul mouvement est "
            "un numero de ligne dans la trace figee, DECLARE avant la pose."),
        "out/etape17/P2_effet.csv": ("nouveau", "POSES 2-3 : detail."),
        "out/etape17/P2_console_rejeu.txt": ("nouveau", "POSES 2-3 : le rejeu."),
    },
    16: {
        "docs/etape16_rapport.md": (
            "nouveau",
            "Rapport d'etape 16. LE CORRECTIF 12, BRANCHE A. 04, 05, 06, 07, "
            "08, 00 et 01 FIGES — aucune valeur publiee ne bouge. Le facteur "
            "departage sur pieces : les trois se valent, et c'est un cas "
            "limite qui commande. Le compte 145 vs 141 ferme exactement."),
        "docs/SPEC_completude_journee.md": (
            "modifie",
            "Trois amendements d'etape 16, ecrits a l'endroit ou la conclusion "
            "changeait : le facteur retenu est 2x et non 4x (D91) ; ce que la "
            "branche B aurait coute (D90) ; le texte de degradation declaree "
            "et la reponse a l'asymetrie avec l'amplitude."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Aucun verdict, aucune valeur publiee. 141 journees portent "
            "un signalement ; un point entier est declare NON JUGEABLE."),
        "docs/METHODO.md": (
            "modifie", "Carnet cumulatif. Section « Etape 16 » ajoutee."),

        "app/thermie_debits/io_data.py": (
            "modifie",
            "LE CORRECTIF 12 (D86, D89). `trou_maximal_par_journee` et "
            "`marquer_completude` : le plus long intervalle non observe, "
            "bornes de minuit comprises, compare a DEUX FOIS le trou median du "
            "point traite. Trois statuts, dont `indeterminable` quand les "
            "horodatages ne disent rien (D92)."),
        "app/thermie_debits/config.py": (
            "modifie",
            "`completude_facteur = 2.0` dans QCConfig. Departage sur pieces "
            "(D91), NON expose par un widget — le seuil se derive du point "
            "traite, et D41 veut le multiplicateur uniforme."),
        "app/thermie_debits/orchestrator.py": (
            "modifie",
            "`res.marques_completude`. Le marquage vit dans une table SEPAREE "
            "et n'entre pas dans daily : le faire remonterait jusqu'a res.df "
            "et ferait bouger 01_colonnes_retenues.json."),
        "app/app.py": ("inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/core.py": (
            "inchange depuis l'etape 13", "Completude de D44."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 10", "Completude de D44."),
        "app/thermie_debits/indicateurs.py": (
            "inchange depuis l'etape 14",
            "RIEN N'Y EST POSE. L'asymetrie avec le critere n<3 est instruite "
            "au §5 du rapport et laissee : ce module est en aval de T_norm."),
        "app/thermie_debits/figures.py": (
            "inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/livrables.py": (
            "inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/exports.py": (
            "inchange depuis l'etape 14", "Completude de D44."),

        "tests/reference/mesure_facteur_completude.py": (
            "nouveau",
            "TACHE A (D91). Le temoin independant aux trois facteurs, regle de "
            "decision ecrite EN TETE du fichier. Les trois passent ; c'est un "
            "cas limite — la sonde a six heures — qui departage."),
        "tests/reference/mesure_branche_b.py": (
            "nouveau",
            "TACHE B (D90). Ce que la branche B aurait coute, sans la poser. "
            "Replication controlee identique sur 31 points. |delta m| <= "
            "0,0014, zero verdict qui bascule — et le maximum de 0,73 degC "
            "tombe sur les VOISINES des journees retirees."),
        "tests/reference/build_reference.py": (
            "modifie",
            "art_02 gagne `journees_signalees_completude` — entier, `n/a` ou "
            "vide, trois valeurs qui ne se confondent pas. art_03 LIT la table "
            "de completude ; le motif commence par RETENUE, l'artefact portant "
            "deja des journees nommees sans etre supprimees."),
        "tests/reference/parametres.py": (
            "modifie", "`completude_facteur` declare dans les deux tables app."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 16 declare."),

        "out/etape16/D44_avant.csv": ("nouveau", "D44 avant : onze entrees."),
        "out/etape16/D44_apres.csv": (
            "nouveau", "D44 apres : les memes onze. Retour 0, aucun CRLF."),
        "out/etape16/A_diff_app_ref_avant.txt": ("nouveau", "D44 avant, integral."),
        "out/etape16/A_diff_app_ref_apres.txt": ("nouveau", "D44 apres : CONFORME."),
        "out/etape16/F_integrite_avant.txt": ("nouveau", "D76 avant : retour 0."),
        "out/etape16/F_integrite_apres.txt": ("nouveau", "D76 apres : retour 0."),

        "out/etape16/A_facteur.csv": (
            "nouveau",
            "TACHE A : 2x/3x/4x -> 145/143/142 journees, separations x2,59 / "
            "x2,59 / x2,62. Les trois passent la regle."),
        "out/etape16/A_console_facteur.txt": (
            "nouveau", "TACHE A, sortie integrale, regle de decision comprise."),
        "out/etape16/B_branche_b.csv": (
            "nouveau",
            "TACHE B : par point, delta m, delta Tmh_norm, et les verdicts "
            "susceptibles de basculer. Aucun ne bascule."),
        "out/etape16/B_console_branche_b.txt": (
            "nouveau", "TACHE B, sortie integrale."),

        "out/etape16/C_effet.txt": (
            "nouveau",
            "LA PREDICTION CENTRALE. 42 artefacts figes dont 04, 05, 06, 07, "
            "08, 00, 01 ; 02, 03, 10 et 99 bougent. ZERO valeur changee, zero "
            "ligne retiree."),
        "out/etape16/C_effet.csv": ("nouveau", "Le detail par artefact."),
        "out/etape16/C_console_rejeu.txt": ("nouveau", "Le rejeu de app/."),

        "out/etape16/R_schemas_ref.txt": (
            "nouveau",
            "COTE REF : 116 522 valeurs confrontees, 0 divergente, deux "
            "journaux identiques au bit pres. La colonne de completude y est "
            "VIDE et 03 porte zero ligne — ref/v4_5 ne produit pas la table."),
        "out/etape16/R_schemas_ref.csv": ("nouveau", "COTE REF : le detail."),
        "out/etape16/R_console_rejeu_ref.txt": ("nouveau", "Le rejeu de ref/v4_5."),
    },
    15: {
        "docs/etape15_rapport.md": (
            "nouveau",
            "Rapport d'etape 15. CORRECTIF 11 pose : 60 116 journees sur "
            "67 054 recevaient la normale du lendemain. 06_coefficients FIGE "
            "— la prediction centrale. Le ricochet chiffre : 2 valeurs, aucune "
            "categorie. §0 signale que le message de commande est arrive "
            "TRONQUE et dit ce qui a ete reconstitue."),
        "docs/SPEC_completude_journee.md": (
            "nouveau",
            "LA SPECIFICATION DU CORRECTIF 12. Le critere evident — « trop peu "
            "de mesures » — est FAUX : il confond une cadence plus large avec "
            "une journee tronquee, et 96 % de ce qu'il trouvait etait le "
            "changement de cadence d'un seul point. Le critere retenu est le "
            "TROU MAXIMAL de la journee : 142 journees sur 68 134, 29 points, "
            "separation x2,6 sur un temoin independant. Deux alternatives "
            "fermees attendent un arbitrage."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Aucun verdict ne change. Deux valeurs de "
            "pct_stress_chronique et onze pourcentages de fraie se deplacent ; "
            "aucune categorie, aucun P, aucun SGVT."),
        "docs/METHODO.md": (
            "modifie", "Carnet cumulatif. Section « Etape 15 » ajoutee."),

        "app/thermie_debits/io_data.py": (
            "modifie",
            "LE CORRECTIF 11 (D86). La normale est agregee par IDENTITE "
            "CALENDAIRE (mois, jour) et lissee sur l'axe des 366 jours "
            "calendaires. La lecture par (jour, mois) ne change pas : elle "
            "interroge desormais le meme axe que l'agregation. 659 -> 696 "
            "lignes. Aucune valeur propre a un bassin."),
        "app/app.py": ("inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/config.py": (
            "inchange depuis l'etape 11", "Completude de D44."),
        "app/thermie_debits/core.py": (
            "inchange depuis l'etape 13", "Completude de D44."),
        "app/thermie_debits/orchestrator.py": (
            "inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 10", "Completude de D44."),
        "app/thermie_debits/indicateurs.py": (
            "inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/figures.py": (
            "inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/livrables.py": (
            "inchange depuis l'etape 14", "Completude de D44."),
        "app/thermie_debits/exports.py": (
            "inchange depuis l'etape 14", "Completude de D44."),

        "tests/reference/mesure_normale_bissextile.py": (
            "nouveau",
            "POSE 1 (1.1, 1.2, 1.4). Les deux versions cote a cote, sans "
            "toucher app/. Controle de replication : identique sur les 31 "
            "points."),
        "tests/reference/mesure_completude_journee.py": (
            "nouveau",
            "POSE 2. La regle de decision est ecrite EN TETE du fichier, avant "
            "les chiffres. Le module porte les DEUX criteres : celui qui s'est "
            "revele faux et celui qui le remplace — consigner ce qu'on a trouve "
            "faux plutot que l'effacer."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 15 declare."),

        "out/etape15/D44_avant.csv": ("nouveau", "D44 avant : onze entrees."),
        "out/etape15/D44_apres.csv": (
            "nouveau", "D44 apres : les memes onze, io_data 659 -> 696 "
                       "lignes. Retour 0, aucun CRLF."),
        "out/etape15/A_diff_app_ref_avant.txt": ("nouveau", "D44 avant, integral."),
        "out/etape15/A_diff_app_ref_apres.txt": ("nouveau", "D44 apres : CONFORME."),
        "out/etape15/F_integrite_avant.txt": ("nouveau", "D76 avant : retour 0."),
        "out/etape15/F_integrite_apres.txt": ("nouveau", "D76 apres : retour 0."),

        "out/etape15/P1_console_mesure.txt": (
            "nouveau",
            "POSE 1.1 : 60 116 journees sur 67 054 (89,65 %) a normale "
            "decalee ; ecart median 0,064 degC sur T_normale, 0,029 sur "
            "T_norm. Replication controlee identique sur 31 points."),
        "out/etape15/P1_normales_par_point.csv": (
            "nouveau", "POSE 1.1 : par point, mediane / p95 / max sur "
                       "T_normale, Delta_TMm, Delta_TMm_liss et T_norm."),
        "out/etape15/P1_normales_par_jour.csv": (
            "nouveau",
            "POSE 1.1 / 1.4 : la normale avant et apres pour les 366 couples "
            "(jour, mois) de chaque station. 115 couples ANTERIEURS au 1er "
            "mars changent — c'est le lissage circulaire qui les atteint."),
        "out/etape15/P1_29fevrier.csv": (
            "nouveau", "POSE 1.2 : 43 journees du corpus sur 22 points ; ecart "
                       "de -0,058 a +0,094 degC."),
        "out/etape15/P1_effet.txt": (
            "nouveau",
            "POSE 1 : 04, 05 et 07 bougent sur les six jeux ; 08 sur un seul, "
            "deux valeurs ; 99_log sur onze lignes ; 06_coefficients FIGE. "
            "Aucune ligne ajoutee ni retiree."),
        "out/etape15/P1_effet.csv": ("nouveau", "POSE 1 : detail par artefact."),
        "out/etape15/P1_effet_valeurs.csv": (
            "nouveau", "POSE 1 : detail par colonne, avec ecarts median et max."),
        "out/etape15/P1_console_rejeu.txt": ("nouveau", "POSE 1 : le rejeu."),

        "out/etape15/P2_console_mesure.txt": (
            "nouveau",
            "POSE 2 : les DEUX criteres. Effectif — 209 journees dont 201 sur "
            "un point, separation x1,5. Trou maximal — 142 journees sur 29 "
            "points, separation x2,6."),
        "out/etape15/P2_completude_par_point.csv": (
            "nouveau", "POSE 2 : par point, les deux criteres et le temoin."),
        "out/etape15/P2_completude_distribution.csv": (
            "nouveau",
            "POSE 2 : la distribution de n_mesures par point. C'est elle qui a "
            "trahi le premier critere — 199 journees a n=4 et 100 a n=24 sur "
            "La Moselle a Hielle."),
        "out/etape15/P2_journees_maigres.csv": (
            "nouveau", "POSE 2 : les 343 journees designees, avec lequel des "
                       "deux criteres les designe."),
    },
    14: {
        "docs/etape14_rapport.md": (
            "nouveau",
            "Rapport d'etape 14. LE CORRECTIF 4, VOIE B. 60 artefacts sur 66 "
            "figes, 07_t_norm seul bouge par SUPPRESSION de 201 162 lignes "
            "toutes sortie_v45=non, 0 valeur changee. 99_log DECLARE FIGE "
            "apres verification du cadre fige, et constate fige. §5 nomme "
            "quatre points du perimetre lecture -> T_norm."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Aucun verdict ne change ; 777 valeurs publiees supprimees. "
            "Trois livrables changent de FORME, et ce qui disparait est nomme : "
            "la couverture de janvier a decembre, le minimum corrige, la "
            "moyenne mobile de trente jours corrigee. Les deux phrases fausses "
            "laissees a l'etape 13 disparaissent avec ce qu'elles decrivaient "
            "(D84)."),
        "docs/METHODO.md": (
            "modifie", "Carnet cumulatif. Section « Etape 14 » ajoutee."),

        "app/thermie_debits/indicateurs.py": (
            "modifie",
            "LE CORRECTIF 4, VOIE B. Les trois series T_moy_comp / T_max_comp "
            "/ T_min_comp et les trois colonnes publiees disparaissent. "
            "`has_delta` RESTE : il gardait aussi ecart_eau_air, donc DEUX des "
            "quatre correlations. -95 lignes."),
        "app/thermie_debits/figures.py": (
            "modifie",
            "Les deux courbes en tirets de Fig_Indicateurs_Resume "
            "disparaissent, avec `has_comp`."),
        "app/app.py": (
            "modifie",
            "L'onglet Indicateurs : sous-titre et legende. La phrase « ramenee "
            "aux conditions normales » disparait (D84)."),
        "app/thermie_debits/orchestrator.py": (
            "modifie", "Le commentaire de l'etape 6bis."),
        "app/thermie_debits/exports.py": (
            "modifie",
            "Un commentaire de D74 citait la formule retiree au present."),
        "app/thermie_debits/livrables.py": (
            "modifie", "Idem — le mot « compensee » n'a plus de referent."),
        "app/thermie_debits/config.py": (
            "inchange depuis l'etape 11", "Joint pour la completude de D44."),
        "app/thermie_debits/core.py": (
            "inchange depuis l'etape 13", "Joint pour la completude de D44."),
        "app/thermie_debits/io_data.py": (
            "inchange depuis l'etape 13", "Joint pour la completude de D44."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 10", "Joint pour la completude de D44."),

        "tests/reference/build_reference.py": (
            "modifie",
            "07_t_norm.csv suit le CODE EXECUTE : la famille compensation "
            "cesse d'etre figee pour app/ et continue de l'etre pour "
            "ref/v4_5. La detection ne demande ni la version ni "
            "THERMIE_CODE — elle demande au code ce qu'il PUBLIE."),
        "tests/reference/comparer_rejeux.py": (
            "modifie",
            "L'outil REFUSE desormais de conclure quand il n'a compare aucun "
            "artefact (retour 2). Il rendait « 0 compares, 0 bougent, retour "
            "0 » sur un dossier vide — le defaut de l'etape 10, un cran plus "
            "haut : la garde protegeait d'une CLE absente, pas d'un CORPUS "
            "absent."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 14 declare."),

        "out/etape14/D44_avant.csv": (
            "nouveau", "D44 avant : DIX entrees, aucune en CRLF."),
        "out/etape14/D44_apres.csv": (
            "nouveau", "D44 apres : ONZE — indicateurs.py rejoint la liste. "
                       "Retour 0, aucun fichier de code en CRLF."),
        "out/etape14/A_diff_app_ref_avant.txt": (
            "nouveau", "D44 avant, sortie integrale."),
        "out/etape14/A_diff_app_ref_apres.txt": (
            "nouveau", "D44 apres, sortie integrale : CONFORME."),
        "out/etape14/F_integrite_avant.txt": (
            "nouveau", "D76 avant : 66/66 sur les deux references, zero "
                       "bytecode. Retour 0."),
        "out/etape14/F_integrite_apres.txt": (
            "nouveau", "D76 apres : idem. Retour 0."),

        "out/etape14/P_effet.txt": (
            "nouveau",
            "LA PREDICTION CENTRALE. 60 artefacts figes sur 66 dont "
            "08_scores.csv — c'est lui qui verifie l'exhaustivite de "
            "l'inventaire. 07_t_norm seul bouge, -201 162 lignes, +0, "
            "0 valeur changee. 99_log FIGE."),
        "out/etape14/P_effet.csv": ("nouveau", "Le detail par artefact."),
        "out/etape14/P_effet_valeurs.csv": (
            "nouveau", "Le detail par colonne — vide, aucune valeur ne bouge."),
        "out/etape14/P_console_rejeu_app.txt": (
            "nouveau", "Le rejeu de app/ apres la pose."),

        "out/etape14/R_effet_ref.csv": (
            "nouveau",
            "COTE REF (a) : contre le rejeu ref d'AVANT la pose, a schema "
            "identique — 22 artefacts sur 22 figes. La famille compensation "
            "reste figee pour ref/v4_5."),
        "out/etape14/R_schemas_ref.txt": (
            "nouveau",
            "COTE REF (b) : contre tests/reference (D83 branche A) — 116 522 "
            "valeurs confrontees, 0 divergente, 2 journaux identiques au bit "
            "pres."),
        "out/etape14/R_schemas_ref.csv": (
            "nouveau", "COTE REF (b) : le detail par artefact."),
        "out/etape14/R_console_rejeu_ref.txt": (
            "nouveau", "Le rejeu de ref/v4_5 sur deux jeux."),
    },
    13: {
        "docs/etape13_rapport.md": (
            "nouveau",
            "Rapport d'etape 13. Cinq poses separees. La prediction 1.2 a "
            "ECHOUE — 18 artefacts divergents, pas zero — et §2 etablit "
            "pourquoi la raison de l'arret etait fausse : 5 113 270 valeurs "
            "confrontees sur les colonnes communes, 0 divergente, 6 journaux "
            "identiques au bit pres."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Aucun verdict ne change. Ce qui change est ce que les "
            "livrables DISENT : six libelles publies passent de « compensee » "
            "a « normalisee ». Deux phrases fausses restent publiees, et le "
            "choix de ne pas les corriger est consigne."),
        "docs/METHODO.md": (
            "modifie", "Carnet cumulatif. Section « Etape 13 » ajoutee."),

        "app/app.py": (
            "modifie",
            "POSE 3 (D74) : deux etiquettes de vocabulaire. POSE 5 "
            "(correctif 7, D22) : quinze defauts de widget derives du "
            "dataclass, dont les trois defauts PAR POSITION. Deux litteraux "
            "subsistent, declares comme INVARIANTS et non comme defauts."),
        "app/thermie_debits/core.py": (
            "modifie",
            "POSE 5 (D78) : le seuil de vingt jours avait TROIS ecritures — "
            "le garde-fou, le journal, et le motif de D67 — et non deux. Une "
            "seule origine, N_MIN_M_SAISONNIER, citee par les trois. Le texte "
            "rendu par le journal est inchange."),
        "app/thermie_debits/io_data.py": (
            "modifie",
            "POSE 4 (CORRECTIF 10, D60) : `marquer_lecture` nomme les mesures "
            "que la lecture ecarte, cause distinguee. `charger_eau` conserve "
            "signature et retour et devient l'adaptateur. Mesure AVANT la "
            "pose : 0 mesure sur 1 694 252 — defaut reel, jamais exerce."),
        "app/thermie_debits/orchestrator.py": (
            "modifie",
            "POSE 4 : l'orchestrateur appelle `marquer_lecture` et conserve "
            "la table dans `res.marques_lecture`."),
        "app/thermie_debits/figures.py": (
            "modifie",
            "POSE 3 (D74) : trois etiquettes. `Tmh_norm` cesse d'etre "
            "etiquete « eau COMPENSEE » — c'est le nom d'une AUTRE formule "
            "dans ce code."),
        "app/thermie_debits/livrables.py": (
            "modifie",
            "POSE 3 (D74) : la legende du Word §1.4, qui contredisait le §1.5 "
            "a huit lignes d'ecart."),
        "app/thermie_debits/exports.py": (
            "modifie",
            "POSE 3 (D74) : « non compensees » dans le classeur fraie — "
            "l'oppose de ces pourcentages bruts est une NORMALISATION."),
        "app/thermie_debits/config.py": (
            "inchange depuis l'etape 11", "Joint pour la completude de D44."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 10", "Joint pour la completude de D44."),

        "tests/reference/parametres.py": (
            "modifie",
            "POSE 1 (D73) : QUATRE tables de controle qualite, indexees par "
            "(source de code, chemin). La table `ref` est LUE dans les six "
            "10_parametres.json de chaque reference, jamais reconstituee, et "
            "son jeu de champs confronte au QCConfig de ref/v4_5 lu par AST. "
            "AnalyseConfig et SourcesConfig n'ayant pas bouge, leurs tables "
            "restent communes."),
        "tests/reference/build_reference.py": (
            "modifie",
            "POSE 2 (D75) : `--est-une-reference` remplace la condition "
            "`sortie == ICI` ; garde qui refuse de construire dans un dossier "
            "portant deja un manifeste. POSE 4 : art_02 gagne un compte, "
            "art_03 LIT la table de marquage au lieu de deduire."),
        "tests/reference/_commun.py": (
            "modifie",
            "POSE 4 : enveloppe de `marquer_lecture`. Sans elle, `journal.eau` "
            "serait reste vide et 01_colonnes_retenues.json aurait bouge pour "
            "une raison sans rapport avec le correctif."),
        "tests/reference/defauts_litteraux.py": (
            "modifie",
            "POSE 5 (5.1) : le releve de l'etape 3 decrivait un app.py qui "
            "n'existe plus. Refait avant la pose (17 litteraux, 0 divergent) "
            "puis apres (27 derives, 2 litteraux)."),
        "tests/reference/comparer_schemas.py": (
            "nouveau",
            "La methode B4 de l'etape 6, generalisee : comparer deux dossiers "
            "COLONNE PAR COLONNE sur les seules colonnes communes. C'est elle "
            "qui etablit que la prediction 1.2 a echoue sans que rien n'ait "
            "bouge dans ref/v4_5 ni dans le corpus."),
        "tests/reference/mesure_dropna_lecture.py": (
            "nouveau",
            "POSE 4 (4.1) : ce que io_data.py:98 supprime, mesure AVANT "
            "correction, avec CONTROLE DE REPLICATION point par point."),
        "tests/reference/SOURCE_CODE.txt": (
            "modifie",
            "D75 : gagne MANIFESTE_ECRIT_A_L_ETAPE=6, distinct de ETAPE=6."),
        "tests/reference_cli/SOURCE_CODE.txt": (
            "modifie",
            "D75 : artefacts etablis a l'etape 6, manifeste ecrit a "
            "l'etape 13. Confondre les deux dates ferait lire un rebasage."),
        "tests/reference_cli/MANIFEST.sha256": (
            "nouveau",
            "POSE 2 (2.2) : 66 artefacts, ecrit sur l'etat actuel. Aucun "
            "artefact reconstruit — les 66 empreintes sont identiques avant "
            "et apres. Ce n'est pas un rebasage."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 13 declare."),

        "out/etape13/D44_avant.csv": (
            "nouveau", "D44 avant : sept entrees, aucune en CRLF."),
        "out/etape13/D44_apres.csv": (
            "nouveau", "D44 apres : DIX entrees, exactement les dix "
                       "declarees. Retour 0, aucun CRLF."),
        "out/etape13/A_diff_app_ref_avant.txt": (
            "nouveau", "D44 avant, sortie integrale."),
        "out/etape13/A_diff_app_ref_apres.txt": (
            "nouveau", "D44 apres, sortie integrale : CONFORME."),
        "out/etape13/F_integrite_avant.txt": (
            "nouveau",
            "D76 avant : tests/reference_cli en defaut (6 hors manifeste, 12 "
            "empreintes divergentes). Retour 1."),
        "out/etape13/F_integrite_apres.txt": (
            "nouveau",
            "D76 apres : 66/66 sur les DEUX references, zero bytecode sous "
            "ref/. Retour 0 — la premiere fois que ce controle passe."),

        "out/etape13/P1_check_reference_ref.txt": (
            "nouveau",
            "POSE 1 : la prediction 1.2, ECHOUEE. 18 artefacts divergents, "
            "trois artefacts x six jeux, autant de lignes retirees "
            "qu'ajoutees — des en-tetes, pas des valeurs."),
        "out/etape13/P1_schemas.txt": (
            "nouveau",
            "POSE 1 : la preuve que rien n'a bouge dans ref/v4_5 ni dans le "
            "corpus. 5 113 270 valeurs confrontees, 0 divergente, 6 journaux "
            "identiques au bit pres, 0 colonne disparue."),
        "out/etape13/P1_schemas.csv": (
            "nouveau", "POSE 1 : le detail par artefact."),
        "out/etape13/P1_effet_app.txt": (
            "nouveau",
            "POSE 1.3 : 66 artefacts sur 66 figes cote app. parametres.py "
            "appartient au harnais."),
        "out/etape13/P1_console_rejeu_ref.txt": (
            "nouveau",
            "POSE 1 : le rejeu THERMIE_CODE=ref REDEVIENT EXECUTABLE — 31 "
            "points OK, un seul echec, celui qui EST la reference (D7). Avant "
            "la pose : 32 echecs sur 32, et un code de retour 0."),

        "out/etape13/P2_integrite_apres.txt": (
            "nouveau", "POSE 2.3 : 66/66 sur les deux references."),

        "out/etape13/P3_effet.txt": (
            "nouveau",
            "POSE 3 : 66 artefacts sur 66 figes. Aucune etiquette n'entre "
            "dans un artefact."),
        "out/etape13/P3_effet.csv": ("nouveau", "POSE 3 : le detail."),

        "out/etape13/P4_console_mesure.txt": (
            "nouveau",
            "POSE 4.1 : 0 mesure supprimee sur 1 694 252, 32 points sur 32, "
            "replication controlee identique sur les 32."),
        "out/etape13/P4_dropna_par_point.csv": (
            "nouveau",
            "POSE 4.1 : par point, les mesures lues et perdues, la cause "
            "distinguee, les journees entierement perdues, et le verdict de "
            "replication."),
        "out/etape13/P4_dropna_par_periode.csv": (
            "nouveau", "POSE 4.1 : la repartition par annee et par mois."),
        "out/etape13/P4_journees_entierement_perdues.csv": (
            "nouveau", "POSE 4.1 : les journees entierement perdues — aucune."),
        "out/etape13/P4_effet.txt": (
            "nouveau",
            "POSE 4 : 02_effectifs bouge d'une colonne et de ZERO valeur sur "
            "les six jeux ; 03 figé ; 99_log bouge d'UNE ligne, un numero de "
            "ligne dans une trace figee — motif declare a tort."),
        "out/etape13/P4_effet.csv": ("nouveau", "POSE 4 : le detail."),
        "out/etape13/P4_ref_intact.csv": (
            "nouveau",
            "POSE 4 : le cote ref survit au changement de harnais — 100 710 "
            "valeurs confrontees, 0 divergente."),

        "out/etape13/P5_defauts_avant.txt": (
            "nouveau",
            "POSE 5.4 : la coincidence VERIFIEE AVANT la pose — 17 litteraux, "
            "0 divergent. Les deux qui divergeaient a l'etape 3 ont disparu "
            "avec l'ancien detecteur."),
        "out/etape13/P5_defauts_apres.txt": (
            "nouveau",
            "POSE 5 : 27 derives, 2 litteraux, 0 divergent. Les deux "
            "restants sont des invariants declares."),
        "out/etape13/P5_effet.txt": (
            "nouveau",
            "POSE 5 : 66 artefacts sur 66 figes, 99_log compris — le texte du "
            "journal est inchange par D78."),
        "out/etape13/P5_effet.csv": ("nouveau", "POSE 5 : le detail."),

        "out/etape13/Z_schemas_final.txt": (
            "nouveau",
            "CLOTURE : apres les cinq poses, ref/v4_5 reproduit encore la "
            "reference — 5 113 270 valeurs, 0 divergente, 6 journaux "
            "identiques au bit pres, 15 colonnes ajoutees toutes "
            "attribuables, 0 disparue."),
        "out/etape13/Z_schemas_final.csv": (
            "nouveau", "CLOTURE : le detail par artefact."),
    },
    12: {
        "docs/SPEC_convention_unique.md": (
            "nouveau",
            "LA SPECIFICATION DU CORRECTIF 4. Les six series a jour avec leurs "
            "consommateurs fichier:ligne ; le vocabulaire des deux familles et "
            "les SIX etiquettes fausses ; ce que le Word montre avant et "
            "apres ; l'alternative C4 chiffree (voie A : 777 valeurs sur 777, "
            "ecart median 3,96 degC ; voie B : 3 colonnes sur 11) ; ce que la "
            "suppression retire ; les fichiers touches en typologie D63. "
            "AUCUN CORRECTIF N'EST POSE : la question de conception attend un "
            "arbitrage."),
        "docs/etape12_rapport.md": (
            "nouveau",
            "Rapport d'etape 12. D44, D70, la specification, D67, et pourquoi "
            "la tache D n'a PAS eu lieu."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Section « D67 » : aucun verdict ne change. Deux coefficients "
            "saisonniers repliés faute d'effectif passent d'un statut VIDE a "
            "`replie` ; le coefficient publie est inchange. BLE3-0 publiait un "
            "zero muet que deux mecanismes differents pouvaient produire."),
        "docs/METHODO.md": (
            "modifie", "Carnet de methode cumulatif. Section « Etape 12 » "
                       "ajoutee ; les sections anterieures sont inchangees."),

        "app/thermie_debits/core.py": (
            "modifie",
            "D67. `_m_saisonnier` : la branche de repli faute d'effectif pose "
            "`statut=\"replie\"` et le motif qui cite l'effectif. Aucune "
            "valeur ne change — `m_estival` est retourne a l'identique et le "
            "journal console n'est pas touche. +20 lignes, -0."),
        "app/app.py": (
            "inchange depuis l'etape 11", "Joint pour la completude de D44."),
        "app/thermie_debits/config.py": (
            "inchange depuis l'etape 11", "Joint pour la completude de D44."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 10", "Joint pour la completude de D44."),
        "app/thermie_debits/io_data.py": (
            "inchange depuis l'etape 10", "Joint pour la completude de D44."),
        "app/thermie_debits/orchestrator.py": (
            "inchange depuis l'etape 10", "Joint pour la completude de D44."),

        "tests/reference/build_reference.py": (
            "modifie",
            "D70 (B1) : ecrit SOURCE_CODE.txt a la racine du dossier "
            "construit — source de code, chemin de parametres, etape. "
            "D67 : `_statut_validite` donne a la colonne de statut une "
            "TROISIEME valeur, `replie`."),
        "tests/reference/check_reference.py": (
            "modifie",
            "D70 (B2) : lit SOURCE_CODE.txt AVANT tout rejeu et REFUSE de "
            "comparer si la source demandee en differe, en nommant les deux. "
            "Retour 3. Le desaccord reste possible, mais doit etre declare "
            "par --source-differente-assumee."),
        "tests/reference/SOURCE_CODE.txt": (
            "nouveau",
            "D70 (B3). Provenance de la reference qui fait foi : source=ref, "
            "chemin=application, etablie a l'etape 6. Verifie dans METHODO.md "
            "et dans les six 10_parametres.json."),
        "tests/reference_cli/SOURCE_CODE.txt": (
            "nouveau",
            "D70 (B3). Provenance de la reference seconde : source=ref, "
            "chemin=cli, etablie a l'etape 6."),
        "tests/reference/mesure_convention_unique.py": (
            "nouveau",
            "TACHE C. Rejoue la chaine puis recalcule le tableau mensuel une "
            "seconde fois a la convention unique, SANS modifier app/. Produit "
            "l'inventaire des colonnes, les valeurs deplacees de la voie A et "
            "la prediction D67."),
        "tests/reference/verifier_integrite_references.py": (
            "nouveau",
            "CONTROLE FINAL, non demande. Deux verifications qui n'existaient "
            "nulle part : chaque MANIFEST.sha256 decrit-il son dossier, et "
            "reste-t-il du bytecode sous ref/ ? Elles ont trouve deux choses "
            "— voir le rapport, §0."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 12 declare."),

        "out/etape12/D44_avant.csv": (
            "nouveau",
            "D44 avant : sept entrees, aucune en CRLF — et IDENTIQUE AU BIT "
            "PRES a out/etape11/D44_apres.csv, ce qui etablit que le "
            "deplacement OneDrive n'a rien altere dans app/."),
        "out/etape12/D44_apres.csv": (
            "nouveau", "D44 apres : les memes sept, seul core.py a bouge "
                       "(1577 -> 1597 lignes). Retour 0, aucun CRLF."),
        "out/etape12/A_diff_app_ref_apres.txt": (
            "nouveau", "D44 apres, sortie integrale : CONFORME."),

        "out/etape12/B_reference_non_reproductible.txt": (
            "nouveau",
            "D70, ce que le fichier de provenance ne suffit pas a reparer : "
            "check_reference avec THERMIE_CODE=ref — l'invocation CONCORDANTE "
            "— rend 66 artefacts divergents sur 66. Ce n'est pas une "
            "corruption."),
        "out/etape12/B_rejeu_ref_echecs.txt": (
            "nouveau",
            "La cause, isolee : 32 points sur 32 en echec sur "
            "TypeError QCConfig 'k'. parametres.py decrit le QCConfig de app/, "
            "qui porte sept champs que ref/v4_5 n'a pas depuis le correctif 1 "
            "(etape 10). Code de retour 0 — le harnais capture l'echec par "
            "point (D7)."),

        "out/etape12/C_console_mesure.txt": (
            "nouveau", "TACHE C, sortie integrale de la mesure."),
        "out/etape12/C1_series.csv": (
            "nouveau",
            "TACHE C1. Par point : m applique, m estime, statut de validite, "
            "presence des deux anomalies."),
        "out/etape12/C3_colonnes_tableau_mensuel.csv": (
            "nouveau",
            "TACHE C3. Les onze colonnes du tableau mensuel, dans l'ordre, "
            "avec celles que livrables.py:257 retient."),
        "out/etape12/C4_valeurs_deplacees.csv": (
            "nouveau",
            "TACHE C4, voie A. Les 777 cellules publiees, valeur actuelle "
            "contre valeur recalculee, cellule par cellule."),
        "out/etape12/C4_resume.csv": (
            "nouveau", "TACHE C4. Les totaux et l'ecart maximal."),

        "out/etape12/E_d67_m_saisonnier.csv": (
            "nouveau",
            "TACHE E. Les 32 coefficients saisonniers du corpus, avec leur "
            "source : 29 saisonnier, 2 estival_repli, 1 rejet_validite. La "
            "PREDICTION est lue ici, AVANT la pose."),
        "out/etape12/E_console_rejeu_avant.txt": (
            "nouveau", "TACHE E. Rejeu avant la pose."),
        "out/etape12/E_console_rejeu_apres.txt": (
            "nouveau", "TACHE E. Rejeu apres la pose."),
        "out/etape12/E_effet_d67.txt": (
            "nouveau",
            "TACHE E. Le verdict : 65 artefacts figes sur 66, "
            "jeu_bienne/06_coefficients.csv seul bouge, sur deux lignes et "
            "deux colonnes. Prediction verifiee."),
        "out/etape12/E_effet_d67.csv": (
            "nouveau", "TACHE E. Le detail par artefact."),
        "out/etape12/E_effet_d67_valeurs.csv": (
            "nouveau", "TACHE E. Le detail par colonne."),
        "out/etape12/F_integrite_references.txt": (
            "nouveau",
            "CONTROLE FINAL. tests/reference : 66/66, zero divergence. "
            "tests/reference_cli : 6 artefacts hors manifeste, 12 empreintes "
            "divergentes, depuis l'etape 6 — build_reference ne remanifeste "
            "que tests/reference. ref/ : zero bytecode apres suppression du "
            ".pyc ecrit par un script de diagnostic de cette etape."),
    },
    5: {
        "docs/etape5_rapport.md": (
            "nouveau",
            "Rapport d'etape 5. Liste des artefacts figes redeclaree (D34), "
            "carnet de bord, le correctif et l'adaptateur, la preuve de "
            "non-regression, ce que le marquage revele, R10 et R11 instruits, "
            "et trois alternatives fermees."),
        "docs/METHODO.md": (
            "modifie",
            "Carnet de methode cumulatif. Section « Etape 5 » ajoutee ; les "
            "sections des etapes 1 a 4 sont inchangees."),

        "app/thermie_debits/qc.py": (
            "modifie",
            "LE CORRECTIF 3. marquer_qualite() rend une table ou chaque "
            "journee lue reste presente, avec un statut a trois valeurs et la "
            "LISTE de ses motifs. controle_qualite() conserve signature et "
            "retour et devient l'adaptateur. +138 lignes, -20."),

        "tests/reference/_commun.py": (
            "modifie",
            "Variable d'environnement THERMIE_CODE : le harnais peut executer "
            "ref/v4_5 (defaut, pour construire la reference) ou app (pour "
            "verifier une modification)."),
        "tests/reference/build_reference.py": (
            "modifie", "Annonce quel code il execute."),
        "tests/reference/check_reference.py": (
            "modifie",
            "Annonce le code rejoue et la reference comparee ; options "
            "--reference et --chemin pour verifier la reference seconde."),
        "tests/reference/diff_ref_app.py": (
            "nouveau",
            "DIAGNOSTIC A/B. Construit deux rejeux — ref/v4_5 et app — et les "
            "compare ENTRE EUX apres neutralisation de la racine du code. "
            "Repond a « quelque chose d'autre a-t-il bouge ? » SANS toucher la "
            "reference."),
        "tests/reference/mesure_recouvrement_qc.py": (
            "nouveau",
            "TACHE C. Combien de journees sont ecartees par plusieurs "
            "detecteurs, et lesquels se recouvrent. Mesure impossible avant le "
            "correctif 3."),
        "tests/reference/instruire_r10_r11.py": (
            "nouveau",
            "TACHE D. R10 — la longueur d'episode recalculee sur le BON masque, "
            "et ce que min_jours_episode exclut aux deux marches. R11 — n_min "
            "derive separement par coefficient et par espece."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Construit la presente archive (D20)."),

        "out/etape5/determinisme.txt": (
            "nouveau",
            "B1/B3. Sortie integrale de check_reference.py sur les deux "
            "regimes, codes de retour inclus. 65 des 66 artefacts identiques "
            "au bit pres."),
        "out/etape5/diff_ref_app.txt": (
            "nouveau",
            "B2. Le diagnostic A/B : 0 divergence de comportement sur les deux "
            "regimes."),
        "out/etape5/recouvrement_qc.csv": (
            "nouveau", "C. Les combinaisons de detecteurs, par regime."),
        "out/etape5/recouvrement_qc_croisements.csv": (
            "nouveau", "C. Les croisements deux a deux — vide : il n'y en a aucun."),
        "out/etape5/recouvrement_qc_par_point.csv": (
            "nouveau", "C. Le detail par point et par regime."),
        "out/etape5/console_recouvrement.txt": (
            "nouveau", "Sortie console de mesure_recouvrement_qc.py."),
        "out/etape5/r10_episodes.csv": (
            "nouveau",
            "D1. La longueur d'episode CORRIGEE, face a celle que l'etape 4 "
            "annoncait, avec l'explication de l'erreur."),
        "out/etape5/r10_filtre_episode.csv": (
            "nouveau",
            "D1. Ce que min_jours_episode exclut reellement, valeur par valeur "
            "et marche par marche."),
        "out/etape5/r11_effectif_minimal.csv": (
            "nouveau", "D2. La derivation de n_min, fenetre par fenetre."),
        "out/etape5/r11_resume.csv": (
            "nouveau", "D2. Les valeurs obtenues et leur ecart au 60 transfere."),
        "out/etape5/console_r10_r11.txt": (
            "nouveau", "Sortie console de instruire_r10_r11.py."),
    },
    11: {
        "docs/etape11_rapport.md": (
            "nouveau",
            "Rapport d'etape 11. Le CORRECTIF 6 — regle de validite. La "
            "certification de 04_normales refaite PAR EMPREINTE : l'outil "
            "etait aveugle, il n'a rien manque. Les t recalcules avant la "
            "pose : BLE3-0 reste seul, la marge passe de 3,585 a 3,658. Deux "
            "rejets constates, les deux predits. Un motif juste mais "
            "INCOMPLET, signale avant la pose."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Section « correctif 6 » : aucun verdict ne change. BLE3-0 "
            "normalisait A L'ENVERS — coefficient negatif, l'anomalie d'air "
            "ajoutee au lieu d'etre retranchee. L'ecart vaut 0,016 degC en "
            "mediane ; ce qui change est le STATUT de ce que le point publie, "
            "pas son chiffre."),
        "docs/SPEC_detecteur_et_validite.md": (
            "modifie",
            "D64 : la relativisation s'ecrit « par mois de la sonde traitee », "
            "et non « par (point, mois) » — l'application traite une sonde a "
            "la fois. Nouvelle §2.4 : le texte de degradation declaree du "
            "rejet, qui dit ce que l'ecran publie et surtout ce que cela "
            "INTERDIT de conclure. Non affiche (D48)."),
        "docs/METHODO.md": (
            "modifie", "Section « Etape 11 » ajoutee."),

        "app/thermie_debits/core.py": (
            "modifie",
            "CORRECTIF 6. `ic95_newey_west` et `verdict_validite` portent la "
            "regle dans le code applicatif. La pente reste celle de l'OLS : "
            "seule son incertitude est estimee autrement. Rejet -> m = 0 "
            "(D33). Le repli sur n < 20 est conserve inchange (C3) ; le "
            "garde-fou sur le R2 disparait, avec son repli silencieux."),
        "app/thermie_debits/config.py": (
            "modifie",
            "m_domaine et m_niveau_ic apparaissent. D61 : hors_eau_min_jours "
            "est SUPPRIME — une configuration morte publiee dans un livrable "
            "est un enonce faux."),
        "app/app.py": (
            "modifie", "Le widget de hors_eau_min_jours disparait avec le "
                       "parametre (D61)."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 10", "Joint pour la completude de D44."),
        "app/thermie_debits/io_data.py": (
            "inchange depuis l'etape 10", "Joint pour la completude de D44."),
        "app/thermie_debits/orchestrator.py": (
            "inchange depuis l'etape 10", "Joint pour la completude de D44."),

        "tests/reference/verifier_04_normales.py": (
            "nouveau",
            "TACHE B. Refait par EMPREINTE SHA-256 ce que l'outil defaillant "
            "avait certifie sur 04_normales.csv, sur les sept rejeux "
            "conserves. Aucun mouvement non declare."),
        "tests/reference/mesure_validite_actuelle.py": (
            "nouveau",
            "TACHE D1/D2. Recalcule les t et les IC sur l'etat ACTUEL de la "
            "chaine, AVANT la pose. Parametres pris du rejeu de l'etape 10."),
        "tests/reference/build_reference.py": (
            "modifie",
            "06_coefficients.csv gagne les sept colonnes de statut de "
            "validite (C4), dont m_estime distinct de m."),
        "tests/reference/parametres.py": (
            "modifie",
            "hors_eau_min_jours retire (D61) ; m_domaine et m_niveau_ic "
            "declares."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 11 declare."),

        "out/etape11/A_diff_app_ref_avant.txt": (
            "nouveau", "D44 avant : sept entrees, aucune en CRLF."),
        "out/etape11/A_diff_app_ref_apres.txt": (
            "nouveau", "D44 apres : les memes sept. Retour 0."),
        "out/etape11/D44_avant.csv": ("nouveau", "D44, detail avant."),
        "out/etape11/D44_apres.csv": ("nouveau", "D44, detail apres."),

        "out/etape11/B_verification_04.txt": (
            "nouveau",
            "TACHE B. Une seule empreinte distincte sur sept rejeux pour cinq "
            "jeux sur six ; deux pour jeu_bienne, la seconde etant le "
            "mouvement deja releve a l'etape 10."),
        "out/etape11/B_empreintes_04_normales.csv": (
            "nouveau", "TACHE B. Les 42 empreintes, une par rejeu et par jeu."),

        "out/etape11/D1_validite_actuelle.csv": (
            "nouveau",
            "TACHE D1. Par point et par coefficient : n, pente, demi-largeur "
            "d'IC95, erreur-type Newey-West, t, decalage, verdict et critere "
            "rejetant — sur l'etat de la chaine AVANT la pose."),
        "out/etape11/console_D1.txt": (
            "nouveau",
            "TACHE D1/D2. BLE3-0 reste le seul rejet estival ; le suivant "
            "passe de 3,585 (etape 4) a 3,658."),

        "out/etape11/C_effet_correctif6.txt": (
            "nouveau",
            "TACHE C. L'effet du correctif 6 : 06 et 10 bougent sur les six "
            "jeux, 07 sur trois, et 02, 03, 04, 05, 08, 00, 01 restent FIGES "
            "— dont 05_anomalies, prediction falsifiable verifiee."),
        "out/etape11/C_effet_correctif6.csv": (
            "nouveau", "TACHE C. Le detail par artefact."),
        "out/etape11/C_effet_correctif6_valeurs.csv": (
            "nouveau", "TACHE C. Le detail par colonne."),
        "out/etape11/C_console_rejeu.txt": (
            "nouveau", "TACHE C. Sortie du rejeu."),
    },
    10: {
        "docs/etape10_rapport.md": (
            "nouveau",
            "Rapport d'etape 10. Le CORRECTIF 1 pose en deux fois. Artefacts "
            "redeclares avec leur motif : deux motifs faux signales AVANT la "
            "pose (00 et 01, que la specification declarait mobiles), un "
            "troisieme trouve faux apres (04_normales). Les quatre predictions "
            "tiennent sur neuf nombres. Etat des lieux du reste du perimetre."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43 + D59. Section « correctif 1 » : 18 points sur 32 voient une "
            "valeur publiee bouger, 2 changent de CATEGORIE. LA PLAINE passe "
            "de Risque Modere a Risque Faible — huit de ses dix journees de "
            "vulnerabilite aigue etaient la sonde hors de l'eau. Et les cinq "
            "journees que le detecteur ne marque plus, nommees."),
        "docs/METHODO.md": (
            "modifie", "Section « Etape 10 » ajoutee ; les precedentes sont "
                       "inchangees."),

        "app/thermie_debits/qc.py": (
            "modifie",
            "POSE 1 : le detecteur de plateau passe sur index calendaire "
            "(D46), via `fenetre_mobile_calendaire` — une seule "
            "implementation, que core delegue. POSE 2 : le DETECTEUR A DEUX "
            "MARCHES remplace le detecteur absolu. Cinq colonnes de "
            "diagnostic par journee (D57). La vue heritee filtre desormais "
            "sur « non ecartee » : une abstention n'est pas une exclusion."),
        "app/thermie_debits/io_data.py": (
            "modifie",
            "TN et TX cessent d'etre jetes a la lecture. Conserves QUAND ILS "
            "EXISTENT, jamais exiges : un fichier d'air qui ne les porte pas "
            "reste lisible et la marche 2 se declare indisponible."),
        "app/thermie_debits/config.py": (
            "modifie",
            "hors_eau_ecart_seuil et hors_eau_exclut_saison DISPARAISSENT. "
            "k, plancher_dispersion, min_jours_groupe, min_jours_episode et "
            "q_ampl apparaissent, chacun avec la provenance de son defaut."),
        "app/app.py": (
            "modifie",
            "Les widgets des deux parametres disparus sont remplaces par ceux "
            "du detecteur relatif, chacun prenant son defaut du DATACLASS et "
            "non d'un litteral."),
        "app/thermie_debits/orchestrator.py": (
            "modifie",
            "res.rapport_qc_detaille expose les valeurs de diagnostic au "
            "perimetre. res.rapport_qc reste la vue heritee, inchangee."),
        "app/thermie_debits/core.py": (
            "modifie",
            "moyenne_mobile_calendaire delegue a qc.fenetre_mobile_calendaire."),

        "tests/reference/build_reference.py": (
            "modifie",
            "03_journees_ecartees.csv porte les cinq colonnes de diagnostic "
            "de D57."),
        "tests/reference/parametres.py": (
            "modifie",
            "Les deux parametres disparus sont remplaces par ceux des deux "
            "marches, dans les deux chemins."),
        "tests/reference/comparer_rejeux.py": (
            "modifie",
            "La cle de 04_normales.csv etait fausse — une colonne inexistante "
            "— et l'outil rapportait « 0 valeur changee » sur un artefact qui "
            "perdait quatre lignes. Cle corrigee, et le silence est desormais "
            "impossible : cle absente et lignes non appariables sont "
            "rapportees."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 10 declare."),

        "out/etape10/A_diff_app_ref_avant.txt": (
            "nouveau", "D44 avant : quatre entrees, aucune en CRLF."),
        "out/etape10/A_diff_app_ref_apres.txt": (
            "nouveau",
            "D44 apres : SEPT entrees, exactement les sept declarees. Les "
            "trois fichiers ajoutes sont ceux que la specification §4 "
            "annoncait. Retour 0."),
        "out/etape10/D44_avant.csv": ("nouveau", "D44, le detail avant."),
        "out/etape10/D44_apres.csv": ("nouveau", "D44, le detail apres."),

        "out/etape10/P1_effet.txt": (
            "nouveau",
            "POSE 1, rejeu isole : 65 artefacts sur 66 figes. 02, 03 et 06 "
            "figes comme predit — la mesure d'etape 6 etait juste."),
        "out/etape10/P1_effet.csv": ("nouveau", "POSE 1, le detail."),
        "out/etape10/P1_preuve_99_log.txt": (
            "nouveau",
            "POSE 1 : la seule ligne qui bouge est un numero de ligne dans une "
            "trace figee."),
        "out/etape10/P1_console_rejeu.txt": (
            "nouveau", "POSE 1, sortie du rejeu."),

        "out/etape10/P2_effet.txt": (
            "nouveau",
            "POSE 2 : 20 artefacts figes, 46 bougent. 00 et 01 bougent — "
            "contradiction signalee avant la pose ; 04_normales bouge sur un "
            "jeu — motif trouve faux apres."),
        "out/etape10/P2_effet.csv": ("nouveau", "POSE 2, le detail par artefact."),
        "out/etape10/P2_effet_valeurs.csv": (
            "nouveau", "POSE 2, le detail par colonne."),
        "out/etape10/P2_console_rejeu.txt": (
            "nouveau", "POSE 2, sortie du rejeu."),
    },
    9: {
        "docs/etape9_rapport.md": (
            "nouveau",
            "Rapport d'etape 9. Artefacts redeclares avec leur MOTIF (D54), "
            "verifie un a un dans le code avant la pose : aucun n'est faux. "
            "Carnet de bord, D44, le correctif 9 et le choix du support, la "
            "prediction verifiee sur cinq grandeurs, le journal des verdicts "
            "detaille, D55 instruit, deux alternatives fermees."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Section « correctif 9 » : 2 points sur 32 voient une "
            "conclusion changer, dans le meme sens ; les six journees qui "
            "franchissent le seuil chronique sont nommees avec leur marge ; et "
            "le non-basculement du seuil aigu est explique par l'intersection "
            "entre journees deplacees et journees proches d'un seuil."),
        "docs/METHODO.md": (
            "modifie",
            "Carnet de methode cumulatif. Section « Etape 9 » ajoutee ; les "
            "sections des etapes 1 a 8 sont inchangees."),

        "app/thermie_debits/core.py": (
            "modifie",
            "CORRECTIF 9 (D51). Delta_TMm_liss est lissee sur le calendrier de "
            "la station d'air, independamment de la completude de l'eau. "
            "fenetre et min_periods inchanges : seul le SUPPORT change. Le "
            "support retenu est TOUT le calendrier de la station, et la raison "
            "du choix est ecrite a la ligne."),
        "app/thermie_debits/orchestrator.py": (
            "inchange depuis l'etape 7",
            "Joint pour que la liste des fichiers de app/ qui different de "
            "ref/v4_5 soit complete (D44)."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 6", "Joint pour la meme raison (D44)."),

        "tests/reference/mesure_support_delta.py": (
            "nouveau",
            "TACHES B1 et B3. Verifie que la serie d'air couvre la chronique "
            "d'eau (32 points sur 32) et chiffre l'ecart entre les deux "
            "supports candidats : 189 valeurs, TOUTES aux bords, jusqu'a "
            "4,276 degC."),
        "tests/reference/mesure_marges_seuils.py": (
            "nouveau",
            "TACHE C. Mesure la MARGE qui separe chaque journee du seuil "
            "qu'elle aurait pu franchir, avant et apres. C'est elle qui "
            "explique pourquoi le seuil aigu n'a pas bascule."),
        "tests/reference/mesure_d55_discordance.py": (
            "nouveau",
            "TACHE D. Instruit D55 sans rien implementer : combien de journees "
            "discordantes, de combien les deux membres s'ecartent, et si ces "
            "journees ressemblent aux exclues ou aux ordinaires. Les grandeurs "
            "de comparaison sont choisies HORS de la regle, pour ne pas etre "
            "circulaires."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 9 declare."),

        "out/etape9/A_diff_app_ref_avant.txt": (
            "nouveau", "TACHE A. D44 avant : quatre entrees, aucune en CRLF."),
        "out/etape9/A_diff_app_ref_apres.txt": (
            "nouveau", "TACHE A. D44 apres : meme liste, retour 0."),
        "out/etape9/D44_avant.csv": ("nouveau", "TACHE A. Le detail, avant."),
        "out/etape9/D44_apres.csv": ("nouveau", "TACHE A. Le detail, apres."),

        "out/etape9/B1_etendue_support.csv": (
            "nouveau",
            "TACHE B1. Par point : etendue de la serie d'air contre celle de "
            "la chronique d'eau. L'air couvre l'eau sur 32 points sur 32, "
            "debordant de 0 a 10 398 jours avant et de 58 a 5 306 apres."),
        "out/etape9/B3_deux_supports.csv": (
            "nouveau",
            "TACHE B3. Les deux supports candidats, compares par point : 189 "
            "valeurs different, dont AUCUNE hors des bords de la chronique "
            "d'eau, jusqu'a 4,276 degC — 22 % de ce que corrige le correctif."),
        "out/etape9/console_B1_B3.txt": (
            "nouveau", "TACHES B1/B3. Sortie console."),
        "out/etape9/B_effet_correctif9.txt": (
            "nouveau",
            "TACHE B. L'effet du correctif 9 SEUL, harnais identique des deux "
            "cotes : 05 et 07 bougent sur les six jeux, 02, 03, 04, 06 et 10 "
            "restent figes — les huit motifs declares sont verifies."),
        "out/etape9/B_effet_correctif9.csv": (
            "nouveau", "TACHE B. Le detail par artefact."),
        "out/etape9/B_effet_correctif9_valeurs.csv": (
            "nouveau", "TACHE B. Le detail par colonne."),
        "out/etape9/B_verification_prediction.txt": (
            "nouveau",
            "LA PREDICTION, verifiee sur son propre perimetre : 854 valeurs, "
            "32 points, 4,790 degC sur l'anomalie, 1,939 degC sur T_norm. "
            "Exactement les quatre chiffres predits."),
        "out/etape9/B_console_rejeu.txt": (
            "nouveau", "TACHE B. Sortie de la construction du rejeu."),

        "out/etape9/C_marges_seuils.csv": (
            "nouveau",
            "TACHE C. Par point et par seuil : franchissements avant et apres, "
            "marge de la journee la plus proche, et deplacement subi au "
            "voisinage du seuil."),
        "out/etape9/C_journees_franchissantes.txt": (
            "nouveau",
            "TACHE C. Les SIX journees qui franchissent le seuil chronique, "
            "avec leur Tmh_norm avant et apres et leur marge."),
        "out/etape9/console_C.txt": (
            "nouveau",
            "TACHE C. Sortie console : seuil aigu 101 -> 101, seuil chronique "
            "743 -> 749 sur deux points."),

        "out/etape9/D1_discordance_par_point.csv": (
            "nouveau",
            "TACHE D1. Par point : exclues, discordantes de forme, "
            "discordantes de niveau, ordinaires."),
        "out/etape9/D1_distribution_ecart.csv": (
            "nouveau",
            "TACHE D1. Distribution de l'ecart entre les deux membres, par "
            "groupe. L'ecart median des discordantes de forme (3,73) est du "
            "meme ordre que celui des exclues (4,42) : il ne separe pas."),
        "out/etape9/D2_journees_signalees.csv": (
            "nouveau",
            "TACHE D2. Les 1 002 journees que D55 signalerait, sur 30 points, "
            "contre 9 exclues."),
        "out/etape9/D3_profils_compares.csv": (
            "nouveau",
            "TACHE D3. Les quatre groupes compares sur des grandeurs choisies "
            "HORS de la regle. Les 992 discordantes de forme se rangent du "
            "cote des journees ordinaires ; les 10 de niveau ressemblent aux "
            "exclues mais six tombent le meme jour sur six points."),
        "out/etape9/console_D.txt": (
            "nouveau", "TACHE D. Sortie console."),
    },
    8: {
        "docs/etape8_rapport.md": (
            "nouveau",
            "Rapport d'etape 8. Artefacts redeclares et confrontes au constat "
            "(desaccord sur 05_anomalies signale AVANT correction), carnet de "
            "bord, D44, le correctif 8 et les deux predictions falsifiables "
            "— elles tiennent toutes deux —, l'inventaire B4 des fenetres "
            "glissantes, la table d'impact recalculee, le journal des "
            "verdicts, deux alternatives fermees."),
        "docs/VERDICTS_MODIFIES.md": (
            "modifie",
            "D43. Section « correctif 8 » ajoutee : aucun verdict de "
            "vulnerabilite ne bouge, trois pourcentages de stress chronique se "
            "deplacent sans changer de categorie, et trois journees de "
            "LA PLAINE cessent d'etre non diagnosticables. Les sections des "
            "correctifs 2 et 5 sont inchangees."),
        "docs/SPEC_detecteur_et_validite.md": (
            "modifie",
            "D50 — la table d'impact du §5 est RECALCULEE sur la chaine "
            "d'apres les correctifs 2, 3, 5 et 8. Le reglage est nomme pour ce "
            "qu'il est (union des deux marches), la mediane de |Delta m| passe "
            "de 0,0010 a 0,0009, et les SIX journees que le socle ne marque "
            "pas sont desormais listees. Les sections 1 a 4 sont inchangees."),
        "docs/METHODO.md": (
            "modifie",
            "Carnet de methode cumulatif. Section « Etape 8 » ajoutee ; les "
            "sections des etapes 1 a 7 sont inchangees."),

        "app/thermie_debits/core.py": (
            "modifie",
            "CORRECTIF 8 (D47). Le lissage de Tmh porte sur la chronique d'eau "
            "COMPLETE — toutes les journees retenues par le controle qualite, "
            "appariees ou non — puis le resultat est ramene sur la vue "
            "exploitable. fenetre et min_periods sont inchanges : seul le "
            "SUPPORT change. Le defaut MIROIR sur Delta_TMm_liss est nomme a "
            "sa ligne, chiffre, et NON corrige."),
        "app/thermie_debits/orchestrator.py": (
            "inchange depuis l'etape 7",
            "Joint pour que la liste des fichiers de app/ qui different de "
            "ref/v4_5 soit complete (D44)."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 6",
            "Joint pour la meme raison (D44)."),

        "tests/reference/mesure_alternative_delta.py": (
            "nouveau",
            "TACHE B4 — le defaut MIROIR, chiffre sans etre applique : "
            "Delta_TMm_liss est une grandeur d'AIR lissee sur les seules "
            "journees ayant de l'EAU. 854 valeurs changeraient (1,27 %), sur "
            "les 32 points, jusqu'a 1,939 degC repercutes sur T_norm."),
        "tests/reference/mesure_impact_detecteur.py": (
            "nouveau",
            "TACHE C (D50). Recalcule ce que le detecteur du correctif 1 "
            "deplacerait, sur la chaine d'APRES les correctifs 2/3/5/8, au "
            "reglage retenu par la specification. Verifie que le marquage est "
            "inchange (68 jours, comme a l'etape 4) et nomme les six journees "
            "que le socle ne marque pas. Aucun code de detection n'est ecrit."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 8 declare."),

        "out/etape8/A_diff_app_ref_avant.txt": (
            "nouveau",
            "TACHE A. D44 lance AVANT toute modification : quatre entrees, "
            "exactement les quatre attendues, aucune en CRLF."),
        "out/etape8/A_diff_app_ref_apres.txt": (
            "nouveau",
            "TACHE A. D44 relance a la fin : meme liste, code de retour 0."),
        "out/etape8/D44_avant.csv": (
            "nouveau", "TACHE A. Le detail, avant modification."),
        "out/etape8/D44_apres.csv": (
            "nouveau", "TACHE A. Le detail, apres."),

        "out/etape8/B_effet_correctif8.txt": (
            "nouveau",
            "TACHE B. L'effet du correctif 8 SEUL, harnais identique des deux "
            "cotes : 60 artefacts figes sur 66. 06_coefficients fige (P1) et "
            "05_anomalies fige (desaccord signale avant correction)."),
        "out/etape8/B_effet_correctif8.csv": (
            "nouveau", "TACHE B. Le detail par artefact."),
        "out/etape8/B_effet_correctif8_valeurs.csv": (
            "nouveau", "TACHE B. Le detail par colonne."),
        "out/etape8/B_verification_P2.txt": (
            "nouveau",
            "PREDICTION P2, verifiee sur son propre perimetre — les 67 392 "
            "journees exploitables, et non les lignes de l'artefact : 473 "
            "valeurs, 22 points, ecart maximal 1,099 degC, 3 recuperees, "
            "0 perdue. Exactement la prediction."),
        "out/etape8/B_console_rejeu.txt": (
            "nouveau", "TACHE B. Sortie de la construction du rejeu."),
        "out/etape8/ALT_delta_calendrier_air.csv": (
            "nouveau",
            "TACHE B4 / §5 alternative 1. Par point : ce que corrigerait le "
            "lissage de Delta_TMm_liss sur le calendrier de la station d'air."),
        "out/etape8/console_ALT_delta.txt": (
            "nouveau", "TACHE B4. Sortie console de la mesure du miroir."),

        "out/etape8/C1_impact_par_point.csv": (
            "nouveau",
            "TACHE C1. Par point : jours marques par chaque marche et par le "
            "regime en service, ecart sur m, sur Tmh_norm mediane et p95."),
        "out/etape8/C2_journees_perdues_vs_service.csv": (
            "nouveau",
            "TACHE C2. Les SIX journees que le socle ne marque pas alors que "
            "le regime en service les ecarte — toutes sur BIE40-3, toutes en "
            "juillet — avec leurs criteres relatifs et la mention de celle que "
            "la marche 2 rattrape."),
        "out/etape8/C3_comparaison_etape4.csv": (
            "nouveau",
            "TACHE C3. Table d'etape 8 contre table d'etape 4, point par "
            "point. Identiques a la sixieme decimale sur 30 des 31 points."),
        "out/etape8/console_C.txt": (
            "nouveau", "TACHE C. Sortie console, dont le controle D50 : le "
                       "socle marque 68 jours, comme a l'etape 4."),
    },
    7: {
        "docs/etape7_rapport.md": (
            "nouveau",
            "Rapport d'etape 7. Artefacts redeclares et confrontes au constat, "
            "carnet de bord, le controle permanent D44 et son verdict, les "
            "deux mesures d'avant correction, le correctif 5 et la prediction "
            "falsifiable sur 06 (elle tient), le statut de densite et les "
            "textes d'ecran, le journal des verdicts, deux alternatives "
            "fermees."),
        "docs/VERDICTS_MODIFIES.md": (
            "nouveau",
            "D43 — JOURNAL DES VERDICTS MODIFIES, cumulatif, jamais reecrit. "
            "Ouvert retroactivement sur le correctif 2 (BIE5-9 SGVT 3,167 -> "
            "2,500, quatre pct_stress_chronique, SEPT lignes de fraie et non "
            "trois), puis la section du correctif 5 : aucun verdict ne change, "
            "et c'est le resultat attendu."),
        "docs/SPEC_detecteur_et_validite.md": (
            "modifie",
            "Nouvelle section 1.5 : LE BLOC DE DEGRADATION DECLAREE. Toujours "
            "affiche, sans aucun seuil introduit — ses phrases conditionnelles "
            "reposent sur des faits booleens (annee entierement retiree, "
            "journees d'ete retirees). Six cas rediges. Les sections 1.1 a 1.4 "
            "et 2 a 5 sont inchangees."),
        "docs/METHODO.md": (
            "modifie",
            "Carnet de methode cumulatif. Section « Etape 7 » ajoutee ; les "
            "sections des etapes 1 a 6 sont inchangees."),

        "app/thermie_debits/core.py": (
            "modifie",
            "CORRECTIF 5 + D45. La jointure eau/air passe a GAUCHE : aucune "
            "journee d'eau n'est plus effacee. `fusionner_marque()` rend la "
            "chronique exploitable INCHANGEE plus la table de marquage ; "
            "`fusionner()` devient l'adaptateur, signature et retour "
            "identiques. Trois motifs propres a la fusion, dont un declare non "
            "exerce. Les journees sans Tmh prennent non_diagnosticable (D45)."),
        "app/thermie_debits/orchestrator.py": (
            "modifie",
            "CORRECTIF 5. Seul appelant de la fusion dans tout app/ : appelle "
            "`fusionner_marque` et range la table dans `res.marques_fusion`. "
            "`res.df` est inchange, donc tous les consommateurs aussi."),
        "app/thermie_debits/qc.py": (
            "inchange depuis l'etape 6",
            "Joint pour que la liste des fichiers de app/ qui different de "
            "ref/v4_5 soit complete (D44)."),

        "tests/reference/diff_app_ref.py": (
            "nouveau",
            "D44 — LE CONTROLE PERMANENT. Diff octet de app/ contre ref/v4_5/, "
            "distinguant une difference de CONTENU d'une difference de FINS DE "
            "LIGNE, et confrontant la liste constatee a la liste declaree par "
            "l'etape. Retour 1 si un fichier differe sans etre declare."),
        "tests/reference/mesure_suppressions.py": (
            "nouveau",
            "TACHES B1 et B2. Mesure AVANT correction des deux suppressions "
            "silencieuses : la jointure interne (trois causes distinguees) et "
            "la densite calendaire. Ces mesures cessent d'etre possibles une "
            "fois les correctifs poses."),
        "tests/reference/comparer_rejeux.py": (
            "nouveau",
            "Compare DEUX rejeux entre eux. Comparer a tests/reference/ mesure "
            "l'effet CUMULE des correctifs ; pour isoler le dernier il faut "
            "comparer le rejeu d'apres au rejeu d'avant, a harnais identique. "
            "Lignes appariees par leur CLE, jamais par leur rang."),
        "tests/reference/mesure_alternative_lissage.py": (
            "nouveau",
            "Alternative 1 du §6, chiffree sans etre appliquee : lisser Tmh "
            "sur la chronique d'eau COMPLETE plutot que sur les seules "
            "journees exploitables."),
        "tests/reference/build_reference.py": (
            "modifie",
            "Le harnais LIT le marquage de la fusion au lieu de le DEDUIRE. "
            "02_effectifs.csv gagne journees_non_diag_air_absent et "
            "journees_non_diag_densite ; 03_journees_ecartees.csv porte les "
            "motifs produits par l'application et les temperatures, jusqu'ici "
            "vides. La branche de deduction est conservee pour rejouer "
            "ref/v4_5."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 7 declare."),

        "out/etape7/A_diff_app_ref_avant.txt": (
            "nouveau",
            "TACHE A. D44 lance AVANT toute modification : trois fichiers "
            "different, exactement les trois declares, aucun en CRLF."),
        "out/etape7/A_diff_app_ref_apres.txt": (
            "nouveau",
            "TACHE A. D44 relance a la fin : quatre fichiers, exactement les "
            "quatre declares. Code de retour 0."),
        "out/etape7/D44_diff_app_ref.csv": (
            "nouveau", "TACHE A. Le detail, avant modification."),
        "out/etape7/D44_diff_app_ref_apres.csv": (
            "nouveau", "TACHE A. Le detail, apres."),

        "out/etape7/B1_jointure_par_point.csv": (
            "nouveau",
            "TACHE B1. Par point : journees effacees par la jointure, part, "
            "trois causes distinguees, plus longue serie continue, annee la "
            "plus touchee, annees entierement effacees. 636 journees sur "
            "68 028 (0,93 %), 23 points sur 32."),
        "out/etape7/B1_jointure_par_annee.csv": (
            "nouveau",
            "TACHE B1. Par point et par annee. LA PLAINE 2008 : 220 lues, 220 "
            "effacees. La Moselle a Hielle 2012 : 102 sur 102."),
        "out/etape7/B1_jointure_journees.csv": (
            "nouveau", "TACHE B1. Les 636 journees, avec leur cause."),
        "out/etape7/B2_densite_journees.csv": (
            "nouveau",
            "TACHE B2. Les 18 journees sans Tmh, avec le nombre de jours "
            "reellement observes dans leur fenetre : de 1 a 3, pour 4 exiges."),
        "out/etape7/console_B.txt": (
            "nouveau", "TACHES B1/B2. Sortie console."),

        "out/etape7/C_effet_correctif5.txt": (
            "nouveau",
            "TACHE C. L'effet du correctif 5 SEUL, harnais identique des deux "
            "cotes : 65 artefacts sur 66 figes au bit pres. 06_coefficients "
            "fige — LA PREDICTION TIENT."),
        "out/etape7/C_effet_correctif5.csv": (
            "nouveau", "TACHE C. Le detail par artefact."),
        "out/etape7/C_effet_correctif5_valeurs.csv": (
            "nouveau", "TACHE C. Le detail par colonne."),
        "out/etape7/C_preuve_99_log.txt": (
            "nouveau",
            "TACHE C. Les deux seules lignes qui bougent : deux numeros de "
            "ligne d'une trace figee, meme fichier, meme fonction, meme "
            "message."),

        "out/etape7/D_effet_harnais.txt": (
            "nouveau",
            "TACHE D. Ce que le harnais ajoute, code identique des deux cotes : "
            "02 bouge sur les six jeux, 03 sur les trois qui portent des "
            "pertes, tout le reste fige."),
        "out/etape7/D_effet_harnais.csv": (
            "nouveau", "TACHE D. Le detail par artefact."),
        "out/etape7/D_effet_harnais_valeurs.csv": (
            "nouveau", "TACHE D. Le detail par colonne."),

        "out/etape7/ALT_lissage_eau_complete.csv": (
            "nouveau",
            "§6, alternative 1 chiffree sans etre appliquee : 473 Tmh "
            "changeraient (0,70 %) sur 22 points, ecart maximal 1,099 degC, "
            "3 des 18 journees de densite recuperees, 0 perdue."),
        "out/etape7/console_ALT.txt": (
            "nouveau", "§6. Sortie console de la mesure d'alternative."),
    },
    6: {
        "docs/etape6_rapport.md": (
            "nouveau",
            "Rapport d'etape 6. Liste d'artefacts redeclaree et confrontee au "
            "constat, carnet de bord (dont trois fautes de methode de ma "
            "part), la reserve R13 levee, le rebasage des deux references "
            "sous protocole, le correctif 2 mesure avant et apres, les trois "
            "amendements de la specification, et deux alternatives fermees."),
        "docs/SPEC_detecteur_et_validite.md": (
            "modifie",
            "Specification amendee sur TROIS points et trois seulement : "
            "min_jours_episode ramene de 3 a 1 (D15 + mesure R10), condition "
            "d'effectif n_min RETIREE de la regle de validite (D41), et D41 "
            "applique ligne a ligne au tableau de provenance de la section 3. "
            "La section 5 est mise en coherence."),
        "docs/METHODO.md": (
            "modifie",
            "Carnet de methode cumulatif. Section « Etape 6 » ajoutee ; les "
            "sections des etapes 1 a 5 sont inchangees."),

        "app/thermie_debits/core.py": (
            "modifie",
            "CORRECTIF 2. Nouvelle fonction `moyenne_mobile_calendaire`, et "
            "les deux moyennes mobiles de `fusionner` (Tmh, Delta_TMm_liss) "
            "qui s'y adossent. La serie est reindexee sur un calendrier "
            "journalier continu avant lissage. `fenetre` et `min_periods` "
            "sont ceux de V4.5, repris sans modification, provenance declaree "
            "a chaque appel : le correctif change le SUPPORT du lissage, pas "
            "le lissage."),
        "app/thermie_debits/qc.py": (
            "modifie",
            "RESERVE R13 LEVEE. La vue heritee rend `motifs[0]` — le premier "
            "motif, ce que produisait exactement l'ancien `_marque` — et non "
            "plus les motifs joints. L'invariance de l'adaptateur ne depend "
            "donc plus de l'absence de journees a plusieurs motifs dans le "
            "corpus. Nouvelle fonction `rapport_ecartes_detaille()` pour le "
            "seul perimetre. Fins de ligne revenues en LF."),

        "tests/test_adaptateur_qc.py": (
            "nouveau",
            "TACHE A3. La preuve que le corpus ne donne pas : chroniques "
            "SYNTHETIQUES (dans tests/, jamais dans data/) dont des journees "
            "declenchent deux puis trois detecteurs. Execute V4.5 et app/ "
            "dans deux interpreteurs separes et compare console, `propre` et "
            "`rapport` colonne par colonne."),
        "tests/reference/build_reference.py": (
            "modifie",
            "TACHE B1. Troisieme neutralisation (D36) dans `_nettoyer` : la "
            "racine du code executee disparait des traces figees, le module "
            "et le numero de ligne sont conserves."),
        "tests/reference/mesure_index_positionnel.py": (
            "nouveau",
            "TACHE C1. Mesure du defaut AVANT correction — elle n'est plus "
            "possible apres. Recalcule les deux versions cote a cote dans le "
            "harnais, sans toucher app/."),
        "tests/reference/mesure_correctif2.py": (
            "nouveau",
            "TACHES C3 et C4. Inventaire verifie des fenetres glissantes de "
            "app/ (6 occurrences de .rolling, 6 lignes declarees), effet de "
            "l'exigence de densite sur les bords, et mesure de ce que la "
            "correction du detecteur de plateau changerait SANS l'appliquer."),
        "tests/reference/comparer_cli_avant_apres.py": (
            "nouveau",
            "TACHE B4. Invariance du regime CLI colonne par colonne sur les "
            "colonnes communes aux deux schemas — une comparaison "
            "d'empreintes aurait melange changement de code et changement de "
            "schema du harnais."),
        "tests/reference/mesurer_effet_correctif2.py": (
            "nouveau",
            "TACHE C. Confronte l'effet mesure du correctif 2 a la liste "
            "d'artefacts declaree par la commande d'etape. Les lignes sont "
            "appariees par leur CLE, jamais par leur rang."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Contenu de l'archive de l'etape 6 declare."),
        "tests/reference/MANIFEST.sha256": (
            "modifie",
            "Manifeste de la reference qui fait foi, rebasee en B3. Un seul "
            "artefact bouge sur 66 : jeu_bienne/99_log.txt, sur ses deux "
            "lignes de chemin."),
        "tests/reference_cli/MANIFEST.sha256": (
            "modifie",
            "Manifeste de la reference seconde, rebasee en B4. Elle compte "
            "desormais 66 artefacts (elle a gagne ses six 10_parametres.json) "
            "et porte le volet climatique que run_cli.py produit reellement."),

        "out/etape6_empreintes_avant.sha256": (
            "nouveau", "TACHE B3. Empreintes des 66 artefacts AVANT rebasage."),
        "out/etape6_empreintes_apres.sha256": (
            "nouveau", "TACHE B3. Les memes APRES rebasage. 65 identiques."),
        "out/etape6_empreintes_cli_avant.sha256": (
            "nouveau", "TACHE B4. Empreintes de tests/reference_cli/ avant "
                       "reconstruction."),

        "out/etape6/B2_ab_avant_rebase.txt": (
            "nouveau",
            "TACHE B2. Le A/B relance AVANT toute reconstruction : 0 "
            "divergence sur les deux regimes, 66/66 artefacts identiques au "
            "bit pres. C'est ce qui autorise le rebasage."),
        "out/etape6/B3_console_rebuild.txt": (
            "nouveau", "TACHE B3. Sortie de la reconstruction."),
        "out/etape6/B3_preuve_99_log.txt": (
            "nouveau",
            "TACHE B3. La preuve par substitution INVERSE : on remet le "
            "chemin retire et l'empreinte retombe sur celle d'avant. Deux "
            "lignes, 298 et 300, et rien d'autre."),
        "out/etape6/B4_console_rebuild.txt": (
            "nouveau", "TACHE B4. Sortie de la reconstruction du regime CLI."),
        "out/etape6/B4_invariance_cli.csv": (
            "nouveau",
            "TACHE B4. Un artefact par ligne : colonnes communes, nouvelles, "
            "disparues, et valeurs divergentes. 3 187 colonnes confrontees, "
            "0 valeur divergente."),
        "out/etape6/B4_invariance_console.txt": (
            "nouveau", "TACHE B4. Synthese de la comparaison."),
        "out/etape6/B4_logs_cli.csv": (
            "nouveau", "TACHE B4. Les six 99_log.txt, traites a part."),
        "out/etape6/B4_preuve_logs.txt": (
            "nouveau",
            "TACHE B4. Ce que le chemin seul n'explique pas dans les logs — "
            "124 lignes, qui ont conduit au volet climatique."),
        "out/etape6/B4_preuve_volet_climatique.txt": (
            "nouveau",
            "TACHE B4. La preuve que la neutralisation D36 et le volet "
            "climatique expliquent la TOTALITE de l'ecart sur les six logs. "
            "Le volet vient de parametres.py:96 (run_cli.py:20), que le gel "
            "d'etape 1 ignorait."),
        "out/etape6/B5_check_reference.txt": (
            "nouveau",
            "TACHE B5. check_reference sur les deux references : DIFF VIDE, "
            "code de retour 0, 66 artefacts chacune."),

        "out/etape6/C1_index_positionnel.csv": (
            "nouveau",
            "TACHE C1. Par point : fenetres enjambantes, journees de T_norm "
            "affectees, plus longue lacune enjambee, ecarts. 1 131 journees "
            "(1,68 %) sur 26 points, lacune jusqu'a 1 716 jours, ecart "
            "jusqu'a 6,105 degC sur Tmh."),
        "out/etape6/C1_index_positionnel_journees.csv": (
            "nouveau", "TACHE C1. Le detail des journees affectees."),
        "out/etape6/console_C1.txt": (
            "nouveau", "TACHE C1. Sortie console."),
        "out/etape6/C3_inventaire_fenetres.csv": (
            "nouveau",
            "TACHE C3. Les six fenetres glissantes de app/, chacune avec son "
            "fichier:ligne, sa position dans la chaine lecture -> T_norm et "
            "son statut. L'inventaire est verifie contre le code, pas "
            "redige."),
        "out/etape6/C4_bords.csv": (
            "nouveau",
            "TACHE C4. Par point : ce que l'exigence de densite retire. 18 "
            "journees sur 67 392, toutes au voisinage d'une lacune, aucune en "
            "extremite de chronique."),
        "out/etape6/C4_bords_journees.csv": (
            "nouveau",
            "TACHE C4. Les 18 journees, avec le nombre de jours REELLEMENT "
            "observes dans leur fenetre — une en compte un seul."),
        "out/etape6/C4_plateau_hors_perimetre.csv": (
            "nouveau",
            "TACHE C3. Ce que la correction du detecteur de plateau "
            "(qc.py:129) changerait, mesure SANS l'appliquer : 0 verdict sur "
            "32 points. Defaut reel dans le code, non exerce par ce corpus."),
        "out/etape6/console_C3_C4.txt": (
            "nouveau", "TACHES C3/C4. Sortie console."),
        "out/etape6/C_effet_correctif2.txt": (
            "nouveau",
            "TACHE C. Le diff de check_reference apres pose du correctif 2 : "
            "8 artefacts bougent sur 66."),
        "out/etape6/C_artefacts_bilan.csv": (
            "nouveau",
            "TACHE C. Un artefact par ligne : ce que la commande declare, ce "
            "qui est constate, lignes retirees et valeurs changees."),
        "out/etape6/C_ecarts_valeurs.csv": (
            "nouveau",
            "TACHE C. Par colonne : combien de valeurs changent, de combien, "
            "et combien se vident. Les 18 valeurs videes correspondent "
            "exactement aux 18 journees annoncees par C4."),
        "out/etape6/C_bilan_console.txt": (
            "nouveau", "TACHE C. Synthese de l'effet du correctif 2."),
    },
    4: {
        "docs/etape4_rapport.md": (
            "nouveau",
            "Rapport d'etape 4. Carnet de bord, comparaison au regime en "
            "service, conjonction, regle de validite, renvoi a la "
            "specification, et trois alternatives fermees."),
        "docs/SPEC_detecteur_et_validite.md": (
            "nouveau",
            "LIVRABLE PRINCIPAL. La specification, prete a implementer : le "
            "detecteur en deux marches, la regle de validite, la provenance "
            "de chaque valeur numerique, les fichiers de app/ touches avec "
            "l'effet attendu sur chaque artefact, et les points dont le "
            "comportement changera."),
        "docs/METHODO.md": (
            "modifie",
            "Carnet de methode cumulatif. Section « Etape 4 » ajoutee ; les "
            "sections des etapes 1 a 3 sont inchangees."),

        "tests/reference/mesure_regime_service.py": (
            "nouveau",
            "TACHE A. Rejoue la comparaison contre le detecteur EN SERVICE "
            "(D25), reproduit a la lettre y compris sa grille annuelle a "
            "5 jours, et chiffre l'impact sur m et T_norm."),
        "tests/reference/mesure_conjonction.py": (
            "nouveau",
            "TACHE B1/B2. La conjonction E_moy ET E_max demandee par D26, et "
            "le profil des jours qu'elle retire."),
        "tests/reference/mesure_conjonction_rampl.py": (
            "nouveau",
            "TACHE B, second membre correct. La conjonction R_ampl ET E_max "
            "de thermie_points, avec un garde-fou d'amplitude d'air DERIVE du "
            "jeu traite et non importe."),
        "tests/reference/verifier_validite.py": (
            "nouveau",
            "TACHE C. Significativite de la pente (IC95 excluant zero), par "
            "espece, et derivation de l'effectif minimal sur fenetres "
            "contigues."),

        "out/etape4/regime_service_table.csv": (
            "nouveau", "A1/A2. La table par reglage, contre le regime en service."),
        "out/etape4/regime_service_par_point.csv": (
            "nouveau", "A1. Le detail par point et par reglage."),
        "out/etape4/impact_m_tnorm.csv": (
            "nouveau",
            "A3. L'impact de chaque reglage sur m, Tmh_norm mediane et p95, "
            "point par point. C'est la mesure d'impact de la contrainte 4."),
        "out/etape4/conjonction_table.csv": (
            "nouveau", "B1. La conjonction E_moy ET E_max, par k."),
        "out/etape4/conjonction_par_point.csv": ("nouveau", "B1. Le detail par point."),
        "out/etape4/conjonction_jours_retires.csv": (
            "nouveau", "B2. Chaque jour retire par la conjonction, avec son profil."),
        "out/etape4/conjonction_profils.csv": (
            "nouveau",
            "B2. La synthese : jours retires contre jours gardes, amplitude "
            "d'air, longueur d'episode, isolement, synchronisation."),
        "out/etape4/conjonction_rampl_table.csv": (
            "nouveau", "B. Les quatre regles cote a cote, par k."),
        "out/etape4/conjonction_rampl_profils.csv": (
            "nouveau",
            "B. Le profil des jours marques par chaque regle. C'est la table "
            "qui departage les deux conjonctions."),
        "out/etape4/validite_significativite.csv": (
            "nouveau",
            "C1. Pente, erreur-type Newey-West, t, R2, n, IC95 excluant zero, "
            "domaine — pour les deux coefficients, par espece."),
        "out/etape4/validite_effectif_minimal.csv": (
            "nouveau", "C2. La derivation de n_min sur fenetres contigues."),
        "out/etape4/validite_conjonction.csv": (
            "nouveau", "C2. Les trois criteres croises, et leur union."),
        "out/etape4/console_regime.txt": ("nouveau", "Sortie console de mesure_regime_service.py."),
        "out/etape4/console_conjonction.txt": ("nouveau", "Sortie console de mesure_conjonction.py."),
        "out/etape4/console_conjonction_rampl.txt": ("nouveau", "Sortie console de mesure_conjonction_rampl.py."),
        "out/etape4/console_validite.txt": ("nouveau", "Sortie console de verifier_validite.py."),
        "tests/reference/livrer_etape.py": (
            "modifie", "Construit la presente archive (D20). Le contenu de "
                       "l'etape 4 y est declare."),
    },
    3: {
        # --- Le rapport et le carnet ---
        "docs/etape3_rapport.md": (
            "nouveau",
            "Rapport d'etape 3. Les six sections exigees : carnet de bord, "
            "critere B et comparaison, dissociation duree/mediane et cas "
            "Chateau-Voue, marche 2, regle de validite, defauts litteraux, "
            "questions ouvertes."),
        "docs/METHODO.md": (
            "modifie",
            "Carnet de methode cumulatif. Section « Etape 3 » ajoutee ; les "
            "sections des etapes 1 et 2 sont inchangees."),

        # --- Scripts de mesure, tous nouveaux ---
        "tests/reference/mesure_critere_b.py": (
            "nouveau",
            "TACHE A. Critere B (dispersion propre), stratification duree x "
            "mediane, cas Chateau-Voue. LA REGLE DE DECISION DES TROIS ISSUES "
            "EST ECRITE EN TETE DE CE FICHIER, avant les chiffres."),
        "tests/reference/mesure_marche2.py": (
            "nouveau",
            "TACHE B. Lit TN et TX directement dans le harnais — aucun code "
            "applicatif modifie — et compare l'ecart au maximum d'air a "
            "l'ecart a la moyenne."),
        "tests/reference/mesure_marche2_marges.py": (
            "nouveau",
            "TACHE B, complement. Corrige la part de TN manquante (rapportee "
            "aux jours ou TM existe) et mesure la MARGE de chaque ecart, en "
            "degres et en unites de dispersion."),
        "tests/reference/mesure_validite_m.py": (
            "nouveau",
            "TACHE C. Intervalles de confiance Newey-West sur les deux "
            "coefficients, pour les 31 points de la reference qui fait foi."),
        "tests/reference/balayage_validite.py": (
            "nouveau",
            "TACHE C2/C3, complement. Rebalaye les seuils sur les deciles de "
            "la distribution observee et croise les criteres de validite."),
        "tests/reference/defauts_litteraux.py": (
            "nouveau",
            "TACHE D (correctif 7, D22). Revue des 50 champs des trois "
            "dataclasses, widget par widget."),
        "tests/reference/livrer_etape.py": (
            "nouveau", "Construit la presente archive (D20)."),

        # --- Artefacts de mesure ---
        "out/etape3/critere_b_par_quantile.csv": (
            "nouveau",
            "A2. Jours et points marques, perdus, gagnes — criteres A et B "
            "cote a cote, sur tous les points-jours puis sur le sous-ensemble "
            "que B sait diagnostiquer."),
        "out/etape3/critere_b_par_point.csv": (
            "nouveau", "A2. Le meme detail, point par point et seuil par seuil."),
        "out/etape3/critere_b_stratification.csv": (
            "nouveau",
            "A3. Stratification 2x2 duree x mediane propre, taux de perte par "
            "cellule, pour chaque seuil."),
        "out/etape3/critere_b_chateau_voue.csv": (
            "nouveau", "A4. Le cas nomme, pour chacun des neuf seuils testes."),
        "out/etape3/critere_b_diagnosticabilite.csv": (
            "nouveau",
            "A1. Ce que les garde-fous du MAD ecartent — en l'occurrence rien : "
            "0 couple (point, mois) sur 124."),
        "out/etape3/marche2_disponibilite.csv": (
            "nouveau",
            "B3. TN et TX sur les six jeux : couverture, jours perdus et "
            "gagnes, coherence TN <= TM <= TX."),
        "out/etape3/marche2_croisement.csv": (
            "nouveau",
            "B2. Qui marque quoi : les deux ensemble, chacun seul, indice de "
            "Jaccard, pour chaque k."),
        "out/etape3/marche2_par_quantile.csv": (
            "nouveau", "B1/B2. Les deux ecarts, seuil par seuil."),
        "out/etape3/marche2_par_point.csv": (
            "nouveau", "B1/B2. Le detail, point par point."),
        "out/etape3/marche2_marges.csv": (
            "nouveau",
            "B2. LA MARGE de chaque ecart, en degres et en MAD*, point par "
            "point. C'est la table qui porte le resultat contre-intuitif."),
        "out/etape3/validite_m_par_point.csv": (
            "nouveau",
            "C1. Pente, demi-largeur d'IC 95 % (Newey-West), R2, n, decalage "
            "retenu, appartenance a [0 ; 1,2] — pour les deux coefficients."),
        "out/etape3/validite_m_distribution.csv": (
            "nouveau", "C2. Distribution de la demi-largeur d'IC sur le corpus."),
        "out/etape3/validite_m_balayage.csv": (
            "nouveau",
            "C2. Combien de points sortiraient, seuil par seuil, sur les "
            "deciles de la distribution observee. Le 0,15 du projet clos y "
            "figure comme REPERE, jamais retenu (D15)."),
        "out/etape3/validite_m_criteres_croises.csv": (
            "nouveau",
            "C3. Ce que chaque critere de validite ecarterait isolement, et "
            "lequel attrape BLE3-0."),
        "out/etape3/defauts_litteraux.csv": (
            "nouveau",
            "TACHE D. Les 50 champs, leur categorie, la valeur de l'interface, "
            "celle du dataclass, et si l'ecart change un calcul."),
        "out/etape3/console_marche2.txt": (
            "nouveau", "Sortie console integrale de mesure_marche2.py."),
        "out/etape3/console_marges.txt": (
            "nouveau", "Sortie console integrale de mesure_marche2_marges.py."),
        "out/etape3/console_validite.txt": (
            "nouveau", "Sortie console integrale de mesure_validite_m.py."),
    },
}

# Quel script porte la règle de décision, étape par étape.
#
# Cette ligne du manifeste nommait `mesure_critere_b.py` en dur. Elle était
# juste pour l'étape où elle a été écrite et fausse pour toutes les suivantes :
# un manifeste qui dit où lire une règle doit dire où elle est vraiment.
_SANS_REGLE = "aucun script : cette étape ne pose pas de règle de décision"
PORTEUR_DE_LA_REGLE = {
    20: "tests/reference/verifier_test_de_signe.py",
    19: "tests/reference/temoin_regime.py",
    18: "tests/reference/verifier_faux_positifs.py",
    16: "tests/reference/mesure_facteur_completude.py",
    3: "tests/reference/mesure_critere_b.py",
}

# Ce que l'étape n'a PAS modifié, et qu'il faut dire.
NON_MODIFIE = {
    21: [
        ("app/ hors qc.py et redaction.py",
         "DEUX sources applicatives modifiees sur SEIZE, et aucune ne touche "
         "un calcul. La prediction — aucun artefact ne bouge — est confirmee "
         "sur les 66"),
        ("qc.ecart_a_la_mediane",
         "INCHANGEE AU CARACTERE PRES. Seul son ETAT est desormais publie"),
        ("tests/reference_v4_5/ et tests/reference_cli/",
         "FIGEES. Elles ne rendent pas 0 a check_reference, et on ne les y "
         "force pas : les reconstruire effacerait les artefacts contre "
         "lesquels treize correctifs ont ete mesures. 0 valeur modifiee, "
         "19 colonnes ajoutees par le harnais depuis l'etape 6"),
        ("les trois journees de La Plaine (2, 3, 4 juin 2011)",
         "TOUJOURS PUBLIEES, dont deux comme vulnerabilite aigue. Les "
         "corriger demande de promouvoir en detecteur un temoin de "
         "verification, avec son propre cycle de validation. Transmis"),
        ("la feuille 06_SYNTHESE du classeur",
         "NON TOUCHEE. Deux lignes empilees, l'une normalisee et l'autre non, "
         "s'y lisent encore comme comparables. Transmis"),
        ("temoin_regime.py",
         "SCEAU INTACT — ef98c126... La regle du temoin n'a pas ete touchee"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode (D77) ; horodatages intacts"),
        ("data/", "aucune ecriture"),
        ("les trois specifications",
         "non amendees : l'etape 21 ne pose aucune regle nouvelle (D122)"),
    ],
    20: [
        ("app/ hors qc.py et config.py",
         "DEUX sources applicatives modifiees sur SEIZE. Le nouveau releve "
         "d'empreintes couvre les seize, la ou l'ancien controle en suivait "
         "onze : cinq modules n'etaient sous aucun temoin"),
        ("app/thermie_debits/redaction.py, livrables.py, app.py",
         "NON TOUCHES. L'ecran nomme le detecteur mais PAS son second membre. "
         "C'est un ecart a D100, declare plutot que repare sans mandat, et "
         "une ligne a ecrire a la cloture"),
        ("le code de la marche 2",
         "INCHANGE au caractere pres. Le correctif ne touche que la marche 1"),
        ("k = 3,0, plancher_dispersion, min_jours_groupe, q_ampl",
         "valeurs inchangees. Le second membre n'introduit AUCUN seuil : zero "
         "est la frontiere du phenomene, pas une valeur calibree"),
        ("les deux tables QC_REF_* de parametres.py",
         "restent a (6, 7, 8, 9) : elles decrivent V4.5, et les figer est "
         "tout leur objet (D73)"),
        ("le cote reference",
         "SURVIT SANS UNE VALEUR DEPLACEE. Rejeu ref de maintenant contre "
         "celui de l'etape 16 : 0 ligne differente, 0 valeur differente sur "
         "les sept artefacts"),
        ("00_format_detecte.json et 01_colonnes_retenues.json",
         "FIGES sur les six jeux, comme declare"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode (D77) ; horodatages intacts"),
        ("data/", "aucune ecriture"),
        ("les deux fichiers scelles de l'etape 19",
         "eprouver_temoin.py et temoin_regime.py rejoues SANS MODIFICATION, "
         "empreintes verifiees. Leur chemin de sortie fige a ecrase quatre "
         "artefacts d'etape 19 : repare et verifie, le chemin renvoye a la "
         "cloture"),
        ("les trois journees de D106",
         "LA PLAINE, 2, 3 et 4 juin 2011. NON VISEES, NON TOUCHEES. Deux "
         "d'entre elles sont encore publiees comme journees de vulnerabilite "
         "aigue. Le correctif les laisse desormais SEULES sur ce point"),
    ],
    19: [
        ("app/ — LES ONZE FICHIERS",
         "AUCUNE POSE. Chaque source confrontee octet par octet a "
         "l'exemplaire scelle dans livraison_etape17.zip : 11 identiques, 0 "
         "divergente, 0 absente, retour 0"),
        ("le detecteur de mise hors d'eau",
         "NON TOUCHE, y compris apres avoir etabli que sa fenetre "
         "juin-septembre le rend aveugle aux artefacts de mai, et qu'il a un "
         "mode de silence identifiable quand l'air monte. Ces deux faits sont "
         "CONSIGNES, pas corriges : la commande interdisait toute regle "
         "nouvelle"),
        ("les deux journees aigues de LA PLAINE (3 et 4 juin 2011)",
         "TOUJOURS PUBLIEES. Elles appartiennent selon toute vraisemblance au "
         "meme bloc artefactuel que les huit deja retirees ; rien n'est change "
         "sans arbitrage du commanditaire"),
        ("le temoin de regime interannuel",
         "N'ENTRE PAS DANS app/. Il sert a verifier le detecteur, pas a le "
         "remplacer ni a le completer"),
        ("docs/VERDICTS_MODIFIES.md",
         "NON MODIFIE, et c'est le resultat de la tache E : la lacune "
         "supposee n'existe pas. La Canner a Vigy 1 y figure deja sous le "
         "correctif 1. Completer un journal complet y introduirait un doublon"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode (D77) ; horodatages intacts"),
        ("tests/reference/ et tests/reference_cli/",
         "AUCUNE REFERENCE N'A ETE REBASEE. Aucun artefact fige n'a bouge"),
        ("data/", "aucune ecriture"),
        ("les trois specifications",
         "non amendees. L'etape 19 ne pose aucune regle applicative"),
        ("les deux fichiers scelles",
         "NON RETOUCHES entre le scellement et la publication, empreintes "
         "contre-verifiees. Le protocole s'est revele lent — pres d'une heure "
         "— et a tourne tel quel"),
    ],
    18: [
        ("app/ — LES ONZE FICHIERS",
         "AUCUNE POSE. Chaque source confrontee octet par octet a "
         "l'exemplaire scelle dans livraison_etape17.zip : 11 identiques, 0 "
         "divergente, 0 absente (out/etape18/F_aucune_pose.txt, retour 0). "
         "L'etape 18 est une verification, et cela se prouve"),
        ("le detecteur de mise hors d'eau",
         "NON TOUCHE, y compris apres avoir etabli que 60 de ses 69 journees "
         "sont marquees par la marche 1 SEULE. Le fait est consigne, pas "
         "corrige : la commande interdisait toute regle nouvelle"),
        ("app/thermie_debits/indicateurs.py",
         "NON TOUCHE. Le desequilibre entre les deux marches y aurait invite ; "
         "rien n'y est pose"),
        ("la synchronie spatiale (temoin 4)",
         "VERIFICATION, JAMAIS REGLE. D41 interdit qu'une regle dependent d'un "
         "corpus multi-points ; il n'interdit pas de s'en servir pour "
         "controler. Rien n'entre dans l'application"),
        ("le temoin post hoc (regime interannuel)",
         "NE RECLASSE AUCUNE LIGNE. Construit apres avoir vu les journees, il "
         "porte cette declaration en tete de son propre script. Les verdicts "
         "publies restent ceux de la regle scellee, y compris les six qu'il "
         "refute"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode (D77) ; horodatages intacts"),
        ("tests/reference/ et tests/reference_cli/",
         "AUCUNE REFERENCE N'A ETE REBASEE. Aucun artefact fige n'a bouge : "
         "rien n'a ete pose qui puisse les faire bouger"),
        ("data/", "aucune ecriture"),
        ("les trois specifications",
         "non amendees. Une specification consigne une regle ; l'etape 18 "
         "n'en produit aucune"),
        ("jeu_bienne/BIE35-5__NA",
         "NON INSTRUIT : leve une ValueError au rejeu (point deja connu sous "
         "D7). Il ne portait aucune journee marquee, donc aucun compte ne "
         "change — mais il n'a pas ete verifie, et ce n'est pas pretendu"),
    ],
    17: [
        ("app/ hors les six fichiers declares",
         "D44 : onze entrees avant, DOUZE apres — redaction.py rejoint la "
         "liste. Aucun fichier de code en CRLF"),
        ("app/thermie_debits/exports.py",
         "NON TOUCHE. L'extension de perimetre de D68 l'autorisait ; il n'y "
         "avait pas lieu — il ne porte que le classeur de detail de la fraie"),
        ("la feuille 06_SYNTHESE du classeur",
         "NON TOUCHEE, et c'est un choix declare : son en-tete est INVARIANT "
         "par construction, pour que les lignes de plusieurs stations "
         "s'empilent telles quelles. C'est pourtant la seule feuille destinee "
         "a la comparaison — le trou y reste ouvert, et il est consigne"),
        ("tout calcul, toute grille, tout score",
         "D68 restreint l'extension a la DECLARATION. 65 artefacts figes sur "
         "66 le verifient"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode (D77) ; horodatages intacts"),
        ("tests/reference/ et tests/reference_cli/",
         "AUCUNE REFERENCE N'A ETE REBASEE (D83 branche A)"),
        ("data/", "aucune ecriture"),
        ("les trois specifications",
         "non amendees : cette etape RASSEMBLE des textes qu'elles portaient "
         "deja, elle n'en ecrit pas de nouveaux"),
    ],
    16: [
        ("app/ hors config.py, io_data.py et orchestrator.py",
         "trois fichiers applicatifs modifies. D44 : onze entrees avant, les "
         "memes onze apres, aucun fichier de code en CRLF"),
        ("app/thermie_debits/indicateurs.py",
         "RIEN N'Y EST POSE, et c'est dit : 141 des 145 journees designees y "
         "publient une amplitude nycthemerale calculee sur des mesures "
         "groupees. Le module est en aval de T_norm — signale, non corrige"),
        ("res.df et ses colonnes",
         "INTACTS. Le marquage vit dans une table separee, faute de quoi "
         "01_colonnes_retenues.json aurait bouge pour une raison sans rapport "
         "avec le correctif"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode (D77) ; horodatages intacts"),
        ("tests/reference/ et tests/reference_cli/",
         "AUCUNE REFERENCE N'A ETE REBASEE (D83 branche A)"),
        ("data/", "aucune ecriture"),
        ("docs/SPEC_convention_unique.md, docs/SPEC_detecteur_et_validite.md",
         "non amendees"),
    ],
    15: [
        ("app/ hors io_data.py",
         "un seul fichier applicatif modifie. D44 : onze entrees avant, les "
         "memes onze apres, aucun fichier de code en CRLF"),
        ("app/thermie_debits/config.py",
         "LE CORRECTIF 11 N'INTRODUIT AUCUN PARAMETRE. La fenetre de lissage "
         "et la periode de reference sont celles d'avant, reprises sans "
         "modification. Le correctif 12, lui, en introduira un — c'est la "
         "difference entre corriger un axe et poser un critere"),
        ("LE CORRECTIF 12", "SPECIFIE, NON POSE (D86). Deux alternatives "
                            "fermees attendent un arbitrage"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode (D77) ; horodatages intacts"),
        ("tests/reference/ et tests/reference_cli/",
         "AUCUNE REFERENCE N'A ETE REBASEE (D83 branche A). Le rebasage reste "
         "une pose de cloture"),
        ("data/", "aucune ecriture"),
        ("docs/SPEC_convention_unique.md, docs/SPEC_detecteur_et_validite.md",
         "non amendees"),
    ],
    14: [
        ("app/ hors les six fichiers declares",
         "aucun autre fichier applicatif modifie. D44 le verifie octet par "
         "octet : dix entrees avant, ONZE apres, exactement les onze "
         "declarees, aucun fichier de code en CRLF"),
        ("app/thermie_debits/core.py, io_data.py, qc.py, config.py",
         "le correctif 4 ne touche pas la chaine lecture -> T_norm : il ne "
         "retire qu'un module TERMINAL, dont aucun score ni seuil ne depend"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode (D77) ; horodatages intacts"),
        ("tests/reference/ et tests/reference_cli/",
         "AUCUNE REFERENCE N'A ETE REBASEE (D83 branche A). Le rebasage est "
         "une pose de CLOTURE, sur decision explicite. comparer_schemas.py "
         "fait foi : 116 522 valeurs confrontees cote ref, 0 divergente"),
        ("data/", "aucune ecriture"),
        ("docs/SPEC_convention_unique.md",
         "la specification n'est pas amendee : cette etape l'EXECUTE. Son §4 "
         "instruisait les deux voies ; le commanditaire a retenu la voie B"),
        ("docs/SPEC_detecteur_et_validite.md", "non amendee"),
    ],
    13: [
        ("app/ hors les six fichiers declares",
         "aucun autre fichier applicatif modifie. D44 le verifie octet par "
         "octet : sept entrees avant, DIX apres, exactement les dix "
         "declarees, aucune en CRLF"),
        ("app/thermie_debits/indicateurs.py",
         "LE CORRECTIF 4 N'EST PAS POSE (D72). Ses deux abus de vocabulaire — "
         "indicateurs.py:85 et app.py:604 — portent sur les colonnes en "
         "arbitrage et restent en l'etat, ce qui est dit au journal des "
         "verdicts"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode — D77 tenu, le QCConfig de "
         "ref/v4_5 a ete lu par AST et jamais importe ; horodatages intacts"),
        ("tests/reference/ (les 66 artefacts)",
         "AUCUNE REFERENCE N'A ETE REBASEE. Le manifeste a ete reecrit sur "
         "l'etat existant : les 66 empreintes sont identiques avant et apres"),
        ("tests/reference_cli/ (les 66 artefacts)",
         "idem — le manifeste manquant a ete ecrit, aucun artefact "
         "reconstruit"),
        ("data/", "aucune ecriture"),
        ("docs/SPEC_convention_unique.md",
         "la specification du correctif 4 n'est pas amendee : son alternative "
         "attend l'arbitrage (D72)"),
        ("docs/SPEC_detecteur_et_validite.md",
         "non amendee"),
    ],
    12: [
        ("app/ hors thermie_debits/core.py",
         "aucun autre fichier applicatif modifie. D44 le verifie octet par "
         "octet : sept entrees avant, les memes sept apres, aucune en CRLF"),
        ("app/thermie_debits/indicateurs.py, figures.py, livrables.py, "
         "exports.py",
         "LE CORRECTIF 4 N'A PAS ETE POSE. La specification est livree ; la "
         "question de conception C4 attend un arbitrage (rapport, §5 et §6)"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode ; horodatages intacts"),
        ("tests/reference/ (les 66 artefacts et MANIFEST.sha256)",
         "AUCUNE REFERENCE N'A ETE REBASEE (B4). Les deux dossiers gagnent un "
         "SOURCE_CODE.txt, qui n'est ni un artefact ni une entree du "
         "manifeste : est_artefact exige <NN>_... dans un sous-dossier de jeu"),
        ("tests/reference_cli/ (les 66 artefacts et MANIFEST.sha256)",
         "idem — seul SOURCE_CODE.txt s'ajoute"),
        ("tests/reference_cli/MANIFEST.sha256",
         "PERIME depuis l'etape 6 et CONSTATE ici, non repare : 6 artefacts "
         "hors manifeste, 12 empreintes divergentes. La cause est dans le "
         "code — build_reference ne remanifeste que tests/reference. Voir le "
         "rapport, §0 et §6 alternative 4"),
        ("ref/v4_5/thermie_debits/__pycache__/",
         "un .pyc y a ete ecrit par un script de diagnostic de cette etape, "
         "CONSTATE et SUPPRIME. ref/ est rendu a son etat d'origine : zero "
         "bytecode, seize sources verifiees intactes par empreinte"),
        ("data/", "aucune ecriture"),
        ("docs/SPEC_detecteur_et_validite.md",
         "la specification du detecteur n'est pas amendee ici ; le correctif 4 "
         "a sa specification propre, docs/SPEC_convention_unique.md"),
    ],
    5: [
        ("app/ hors thermie_debits/qc.py",
         "aucun autre fichier applicatif modifie — app.py, core.py, io_data.py, "
         "config.py, orchestrator.py et les autres sont intacts"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode ; horodatages intacts"),
        ("tests/reference/ (les 66 artefacts et MANIFEST.sha256)",
         "LA REFERENCE N'A PAS ETE REBASEE. Verifie — MANIFEST.sha256 concorde "
         "sans divergence. L'artefact qui bouge au rejeu est remonte, pas "
         "absorbe"),
        ("tests/reference_cli/",
         "inchangee — et inutilisable comme temoin en l'etat, voir §2 B3"),
        ("data/", "aucune ecriture"),
        ("docs/SPEC_detecteur_et_validite.md",
         "la specification n'est pas amendee ici ; R10 et R11 l'affectent et "
         "seront traitees a l'etape 6"),
    ],
    4: [
        ("app/", "aucun fichier applicatif modifie, cree ou supprime — c'est "
                 "la derniere etape dans ce cas"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode ; horodatages intacts"),
        ("tests/reference/ (les 66 artefacts et MANIFEST.sha256)",
         "la reference qui fait foi n'a pas ete reconstruite : aucun parametre "
         "n'a change. Verifie — MANIFEST.sha256 concorde sans divergence"),
        ("tests/reference_cli/", "reference seconde, inchangee"),
        ("data/", "aucune ecriture"),
        ("docs/etape1_*.md, docs/etape2_rapport.md, docs/etape3_rapport.md",
         "rapports des etapes precedentes, inchanges"),
    ],
    3: [
        ("app/", "aucun fichier applicatif modifie, cree ou supprime"),
        ("ref/v4_5/ et ref/thermie_points/",
         "aucune ecriture ; aucun bytecode ; horodatages intacts"),
        ("tests/reference/ (les 66 artefacts et MANIFEST.sha256)",
         "la reference qui fait foi n'a pas ete reconstruite a cette etape : "
         "aucun parametre n'a change. Verifie — MANIFEST.sha256 concorde sans "
         "divergence"),
        ("tests/reference_cli/", "reference seconde, inchangee"),
        ("data/", "aucune ecriture"),
    ],
}


def main():
    if len(sys.argv) < 2:
        print("usage : python livrer_etape.py <numero d'etape>", file=sys.stderr)
        return 2
    n = int(sys.argv[1])
    if n not in CONTENU:
        print(f"etape {n} : aucun contenu declare", file=sys.stderr)
        return 2

    contenu = CONTENU[n]
    manquants = [f for f in contenu if not (RACINE / f).exists()]
    if manquants:
        print("FICHIERS DECLARES MAIS ABSENTS :", file=sys.stderr)
        for f in manquants:
            print(f"   {f}", file=sys.stderr)
        return 1

    # --- MANIFESTE_LIVRAISON.md ---
    nouveaux = sum(1 for s, _ in contenu.values() if s == "nouveau")
    modifies = sum(1 for s, _ in contenu.values() if s == "modifie")
    lignes = [
        f"# Livraison — étape {n}",
        "",
        f"{len(contenu)} fichiers : **{nouveaux} nouveaux**, "
        f"**{modifies} modifiés**.",
        "",
        "Cette archive contient tout ce que l'étape a produit ou modifié. "
        "Rien n'est livré en dehors d'elle (D20).",
        "",
        "## Ce que contient l'archive",
        "",
        "| Fichier | Statut | Ce que c'est | SHA-256 (16 car.) |",
        "|---|---|---|---|",
    ]
    for chemin in sorted(contenu):
        statut, quoi = contenu[chemin]
        h = sha256(RACINE / chemin)[:16]
        marque = "**nouveau**" if statut == "nouveau" else "*modifié*"
        lignes.append(f"| `{chemin}` | {marque} | {quoi} | `{h}` |")

    lignes += ["", "## Ce que l'étape n'a PAS touché", "",
               "| Emplacement | État |", "|---|---|"]
    for ou, quoi in NON_MODIFIE.get(n, []):
        lignes.append(f"| `{ou}` | {quoi} |")

    lignes += ["", "## Comment relire cette livraison", "",
               f"1. `docs/etape{n}_rapport.md` — le rapport, dans l'ordre "
               "des tâches. Le §0 porte le carnet de bord.",
               "2. La règle de décision est écrite **en tête de "
               f"`{PORTEUR_DE_LA_REGLE.get(n, _SANS_REGLE)}`**, dans le code "
               "qui produit les chiffres, et reproduite dans le rapport.",
               "3. Les `console_*.txt` portent les sorties intégrales des "
               "mesures, pour qui veut vérifier un chiffre sans rejouer.",
               "4. Chaque script est exécutable seul depuis "
               "`tests/reference/`.", ""]

    dest_md = OUT / f"MANIFESTE_LIVRAISON_etape{n}.md"
    dest_md.write_text("\n".join(lignes) + "\n", encoding="utf-8", newline="\n")

    # --- l'archive ---
    dest = OUT / f"livraison_etape{n}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(dest_md, "MANIFESTE_LIVRAISON.md")
        for chemin in sorted(contenu):
            z.write(RACINE / chemin, chemin)
    dest_md.unlink()

    taille = dest.stat().st_size
    print(f"{dest.relative_to(RACINE).as_posix()} : {len(contenu) + 1} fichiers, "
          f"{taille/1024:.0f} Ko")
    print(f"   {nouveaux} nouveaux, {modifies} modifies, "
          f"plus MANIFESTE_LIVRAISON.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
