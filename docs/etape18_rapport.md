# Étape 18 — Le détecteur ne retire-t-il que des artefacts ?

Vérification demandée avant la clôture. **Aucune modification applicative n'a été
faite.** Les onze sources de `app/` sont, octet pour octet, celles de la
livraison de l'étape 17 : `out/etape18/F_aucune_pose.txt`, 11 identiques,
0 divergente, retour 0.

---

## §0 — Carnet de bord

| | |
|---|---|
| Code exécuté | `app/` (`THERMIE_CODE=app`) |
| Poses applicatives | **aucune** |
| Scripts écrits | `verifier_faux_positifs.py`, `mesure_regime_interannuel.py`, `mesure_cout_verdict.py`, `verifier_aucune_pose.py` |
| Règle de décision | scellée par empreinte SHA-256 **avant** le premier chiffre |
| Intégrité `ref/` (D77) | 0 fichier de bytecode, `ref/` propre, retour 0 |
| Rejeux effectués | 2 par point (détecteur allumé / éteint), sur tout le corpus |

**Un échec de lecture, déclaré.** `jeu_bienne/BIE35-5__NA` lève une `ValueError`
au rejeu et n'a pas pu être instruit. C'est le point déjà connu qui échoue sous
D7 ; il ne portait aucune journée marquée, donc il ne change aucun compte, mais
il n'a pas été vérifié et je ne prétends pas qu'il l'ait été.

**Une correction que je dois à l'étape 17.** J'avais lu, en pose 0, que les
69 journées marquées portaient toutes `marche_active = « marche 1 + marche 2 »`
et j'en avais tiré que la conjonction avait joué partout. C'est faux.
`qc.py:398` écrit cette mention sur **toute la fenêtre estivale** dès que la
marche 2 est *disponible* — elle dit qu'un chemin existait, pas qu'il a servi.
Le motif, lui, dit la vérité :

| motif porté par la journée | nombre |
|---|---|
| socle relatif **seul** (marche 1) | **60** |
| socle relatif *et* conjonction | 8 |
| conjonction **seule** (marche 2) | 1 |

**Soixante des soixante-neuf journées sont écartées par la marche 1 seule.** La
marche 2 — la conjonction stricte forme × niveau, celle qui exige deux
dépassements simultanés — n'intervient que dans 9 cas. C'est un fait sur
l'équilibre réel du détecteur qui n'était pas au dossier, et il conditionne
tout ce qui suit.

---

## §1 — La règle de décision, écrite d'avance

Elle est écrite en tête de
[`tests/reference/verifier_faux_positifs.py`](../tests/reference/verifier_faux_positifs.py),
dans le fichier même qui produit les chiffres, et son empreinte a été prise
avant toute exécution :

```
727a528f4e36254488bcc87a3e1454a6f249f214b3f0371cec0b4e48a293d4cf
tests/reference/verifier_faux_positifs.py   20 273 octets   scellé le 2026-08-30T15:57:15
```

(`out/etape18/REGLE_SCELLEE.txt`.)

Quatre témoins, aucun décisif seul, tous étalonnés sur **les quantiles du point
traité** — aucune valeur importée, aucune valeur commune à plusieurs points
(D15, D41).

| | témoin | conclut *sonde exondée* si | conclut *événement réel* si |
|---|---|---|---|
| T1 | amplitude `(T_eau_max−T_eau_min)/(TX−TN)` | ≥ q90 estival du point | ≤ médiane estivale |
| T2 | débit du jour | ≤ q10 estival du point | ≥ médiane estivale |
| T3 | rupture de l'écart eau–air en sortie d'épisode | ≥ q90 des variations | ≤ médiane |
| T4 | synchronie spatiale (`jeu_bienne` seul) | aucun autre point marqué | ≥ 3 autres points marqués |

**Classement, et son asymétrie assumée.**
*Exondation* exige **au moins deux** témoins concordants **et aucune
contradiction**. *Événement thermique réel* n'exige **qu'un seul** témoin, sans
contradiction. Tout le reste est *indécidable*.

Cette asymétrie n'est pas une commodité, c'est le coût des deux erreurs. Classer
à tort en « exondation » valide le retrait d'une alerte réelle d'un document
remis à un maître d'ouvrage. Classer à tort en « événement » rouvre une
instruction. Le second se répare, le premier non. La charge de la preuve pèse
donc sur « exondation ».

**Une neutralisation, écrite d'avance elle aussi.** La marche 2 du détecteur
teste exactement `amplitude_eau / amplitude_air` (`qc.py:375`). Sur une journée
que la marche 2 a déclenchée, T1 ne serait pas un témoin : il redirait le
détecteur, et sa concordance serait une tautologie. La règle le neutralise donc
dès que le motif porte la marche 2.

> **Ce garde-fou n'a jamais mordu** : sur les 27 journées instruites, la marche 2
> n'a déclenché aucune fois (`T1_neutralise = non` sur 27/27). Je l'avais écrit
> pour me protéger d'une circularité qui, sur ce corpus, ne s'est pas présentée.
> C'est de la chance, pas de la conception : je n'avais pas mesuré la répartition
> des marches avant d'écrire la règle.

---

## §2 — Le sous-ensemble qui coûte un verdict

Une journée marquée qui ne franchissait aucun seuil piscicole ne coûte rien.
Le sous-ensemble à instruire a été établi en rejouant la chaîne **détecteur
éteint** (`cfg.qc.hors_eau = False`) : ce que la journée valait *avant* d'être
retirée.

**69 journées marquées → 27 franchissaient un seuil.** Les 42 autres ne
déplacent aucun verdict et ne sont pas instruites.

| point | journées marquées | dont franchissant un seuil |
|---|---:|---:|
| **LA PLAINE A RAON-SUR-PLAINE** | 16 | **13** |
| BIE40-3 | 8 | 7 |
| BIE6-8 | 17 | 5 |
| LIZ13-5 | 1 | 1 |
| SN 21069646 – La Canner à Vigy 1 | 1 | 1 |
| 13 autres points | 26 | 0 |

### Ce que le marquage a réellement déplacé

| point | jours aigus | catégorie aiguë | chronique | SGVT | verdict déplacé |
|---|---|---|---|---|---|
| **LA PLAINE** | 10 → **2** | sévère → **ponctuelle** | 3,15 % modérée → **0,47 % faible** | 2,33 → **1,50** | **Risque Modéré → Risque Faible (Zone Refuge)** |
| **La Canner à Vigy 1** | 1 → **0** | ponctuelle → **absence** | 0 % → 0 % | 3,17 → 2,50 | catégorie aiguë déplacée |
| BIE40-3 | 39 → 33 | létale → létale | 5,09 % → 5,13 % | 5,5 → 5,5 | non |
| BIE6-8 | 0 → 0 | absence | 1,14 % → 0,70 % | 0,83 → 0,83 | non |
| LIZ13-5 | 0 → 0 | absence | 3,45 % → 3,14 % | 3,5 → 3,5 | non |

**Les huit journées de LA PLAINE, nommément.** Le compte se ferme exactement :
10 jours aigus détecteur éteint, 2 détecteur allumé, soit **8 retirés**, et ce
sont précisément les 8 journées marquées qui franchissaient le seuil aigu :

| date | Tmax_norm | seuil aigu | marge |
|---|---:|---:|---:|
| 2011-06-05 | 28,21 | 24 | +4,21 |
| 2011-06-06 | 24,86 | 24 | +0,86 |
| 2011-06-08 | 25,55 | 24 | +1,55 |
| 2011-06-11 | 26,80 | 24 | +2,80 |
| 2011-06-12 | 27,85 | 24 | +3,85 |
| 2011-06-14 | 25,98 | 24 | +1,98 |
| 2012-06-21 | 29,79 | 24 | +5,79 |
| 2012-06-23 | 27,11 | 24 | +3,11 |

Cinq autres journées de ce point (2011-06-01, 06-07, 06-09, 06-10, 06-13) ne
franchissaient que le seuil chronique ; ce sont elles qui font passer la
vulnérabilité chronique de 3,15 % à 0,47 %.

**Un second point que la commande ne nommait pas.** `SN 21069646 – La Canner à
Vigy 1` perd son unique journée aiguë (2021-06-01, Tmax_norm 30,27 pour un seuil
de 30) et passe de « Vulnérabilité aiguë ponctuelle » à « Absence de
vulnérabilité aiguë ». Deux points, et non un seul, ont un verdict déplacé par
le détecteur.

### Une corroboration indépendante, et une nuance à ne pas manquer

`docs/VERDICTS_MODIFIES.md` portait déjà ces deux points depuis l'étape 1.
Les chiffres retrouvés ici par une **autre voie** — extinction du détecteur
dans la configuration, et non comparaison au régime en service — coïncident au
chiffre près : 10 → 2 journées aiguës, 3,146 % → 0,467 %, SGVT 2,333 → 1,500,
et **les huit mêmes dates**. Le journal des verdicts se vérifie dix-sept étapes
après avoir été écrit.

Une seule ligne diffère, et il faut dire pourquoi. Le journal note pour
`BIE40-3` une vulnérabilité aiguë passant de **29** à 33 jours ; je mesure ici
**39** → 33. Les deux « avant » ne sont pas le même : celui du journal est le
**régime en service de V4.5** — un détecteur à seuil absolu, qui écartait déjà
des journées —, celui de cette étape est **l'absence totale de détecteur**. Les
deux « après » sont identiques (33). Ce n'est pas une contradiction, c'est deux
contrefactuels distincts, et le confondre ferait lire une régression là où il
n'y en a pas.

---

## §3 — Les quatre témoins

`out/etape18/B_temoins.csv`, une ligne par journée instruite.

| témoin | exondation | événement | muet | où il est muet |
|---|---:|---:|---:|---|
| T1 amplitude | 18 | 7 | 2 | `T_eau_min` ou `TN`/`TX` absents |
| T2 débit | 0 | 8 | **19** | **`jeu_bienne` n'a aucun débit** (13 j.) ; ailleurs, valeur intermédiaire (6 j.) |
| T3 forme | 3 | 2 | **22** | ne parle qu'en fin d'épisode : 5 journées sur 27 en sont |
| T4 synchronie | 9 | 0 | **18** | n'existe que sur `jeu_bienne` : muet sur LA PLAINE (13 j.) et La Canner (1 j.) |

**Ce qui manque, dit franchement.** Le témoin du débit — celui que la commande
désignait comme la plus forte alerte, « un débit normal sous une journée
marquée, l'eau était là » — est **structurellement absent de `jeu_bienne`** :
aucun des 27 points de ce jeu n'a de chronique de débit. Il ne s'est donc
prononcé que sur LA PLAINE et La Canner. Le témoin de synchronie, lui, est
l'exact complément : il n'existe **que** sur `jeu_bienne`. **Aucune journée
instruite n'a bénéficié des deux à la fois.** Cette complémentarité en creux
est la faiblesse principale de la vérification.

---

## §4 — Le verdict journée par journée

### 4.1 Ce que rend la règle scellée

| verdict | journées |
|---|---:|
| exondation | **6** |
| **événement thermique réel** | **6** |
| indécidable | **15** |

**Six journées tombent en « événement thermique réel », et je le dis fort.**

| point | date | T1 | T2 | T3 | T4 |
|---|---|---|---|---|---|
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-06 | événement | **événement** | muet | muet |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-07 | événement | **événement** | muet | muet |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-09 | muet | **événement** | muet | muet |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-10 | événement | **événement** | muet | muet |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-13 | événement | muet | muet | muet |
| BIE6-8 | 2017-09-03 | événement | muet | muet | muet |

Prise au mot, la règle scellée dit que **la conclusion du chantier sur LA PLAINE
serait à reprendre**. Le débit y était de 2,6 à 2,9 m³/s — soit **deux fois la
médiane estivale du point (1,31)** — pendant que la journée était écartée pour
mise hors d'eau. Sur ces journées, l'eau était là, en abondance.

### 4.1 bis — Les 27 journées, une ligne chacune

La colonne « post hoc » n'appartient pas à la règle scellée ; elle est
expliquée au §4.2 et **ne participe à aucun classement**.

| point | date | seuil franchi | T1 ampl. | T2 débit | T3 forme | T4 synchr. | **classement** | post hoc |
|---|---|---|---|---|---|---|---|---|
| BIE6-8 | 2017-09-03 | chron. | **événement** | muet | muet | muet | **ÉVÉNEMENT** | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-06 | aigu+chron. | **événement** | **événement** | muet | muet | **ÉVÉNEMENT** | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-07 | chron. | **événement** | **événement** | muet | muet | **ÉVÉNEMENT** | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-09 | chron. | muet | **événement** | muet | muet | **ÉVÉNEMENT** | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-10 | chron. | **événement** | **événement** | muet | muet | **ÉVÉNEMENT** | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-13 | chron. | **événement** | muet | muet | muet | **ÉVÉNEMENT** | **hors de tout précédent** |
| BIE40-3 | 2015-09-09 | aigu | **exondation** | muet | muet | **exondation** | exondation | dans l’enveloppe |
| BIE40-3 | 2023-06-27 | aigu | **exondation** | muet | muet | **exondation** | exondation | dans l’enveloppe |
| BIE40-3 | 2023-06-28 | aigu | **exondation** | muet | muet | **exondation** | exondation | dans l’enveloppe |
| BIE40-3 | 2023-06-29 | aigu | **exondation** | muet | **exondation** | **exondation** | exondation | dans l’enveloppe |
| BIE6-8 | 2017-09-09 | chron. | **exondation** | muet | muet | **exondation** | exondation | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-14 | aigu+chron. | **exondation** | muet | **exondation** | muet | exondation | **hors de tout précédent** |
| BIE40-3 | 2015-07-08 | aigu brut | **exondation** | muet | muet | muet | indécidable | dans l’enveloppe |
| BIE40-3 | 2015-09-07 | aigu | **exondation** | muet | **événement** | **exondation** | indécidable | dans l’enveloppe |
| BIE40-3 | 2015-09-10 | aigu | **exondation** | muet | **événement** | **exondation** | indécidable | dans l’enveloppe |
| BIE6-8 | 2017-09-02 | chron. | muet | muet | muet | muet | indécidable | **hors de tout précédent** |
| BIE6-8 | 2017-09-07 | chron. | **événement** | muet | muet | **exondation** | indécidable | **hors de tout précédent** |
| BIE6-8 | 2017-09-08 | chron. | **événement** | muet | muet | **exondation** | indécidable | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-01 | chron. | **exondation** | **événement** | **exondation** | muet | indécidable | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-05 | aigu+chron. | **exondation** | **événement** | muet | muet | indécidable | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-08 | aigu+chron. | **exondation** | **événement** | muet | muet | indécidable | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-11 | aigu+chron. | **exondation** | muet | muet | muet | indécidable | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2011-06-12 | aigu+chron. | **exondation** | muet | muet | muet | indécidable | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2012-06-21 | aigu | **exondation** | muet | muet | muet | indécidable | **hors de tout précédent** |
| LA PLAINE A RAON-SUR-PLAINE | 2012-06-23 | aigu | **exondation** | muet | muet | muet | indécidable | **hors de tout précédent** |
| LIZ13-5 | 2015-07-08 | chron.+aigu brut | **exondation** | muet | muet | muet | indécidable | **hors de tout précédent** |
| SN 21069646 - La Canner à Vigy 1 | 2021-06-01 | aigu | **exondation** | **événement** | muet | muet | indécidable | **hors de tout précédent** |

**Ce que révèle la colonne des indécidables.** Onze des quinze journées
indécidables le sont pour la même raison : **T1 dit exondation et T2 dit
événement**, sur la même journée. Deux témoins que j'ai conçus indépendants se
contredisent systématiquement sur LA PLAINE et sur `BIE6-8`. Une contradiction
aussi régulière n'est pas du bruit : c'est le signe qu'au moins un des deux
mesure autre chose que ce que je lui prêtais. Le §4.3 dit lequel — les deux.

### 4.2 Ce que le corpus oppose à ce verdict

Je devais chercher la réfutation la plus sévère possible. Elle existe, et elle
est écrasante — mais elle repose sur un témoin qui **n'était pas dans la règle
scellée** et qui a été construit **après** avoir vu les journées. Je le publie
comme tel : `mesure_regime_interannuel.py` porte cette déclaration en tête, et
**il ne reclasse aucune ligne**.

Ce témoin compare le point **à lui-même**, aux mêmes dates calendaires (± 7 j)
des autres années de sa propre chronique. Aucun autre point n'intervient.

**20 des 27 journées instruites sont hors de tout précédent saisonnier du
point** — et les 6 classées « événement » en font toutes partie :

| point | date | T_eau_moy | max jamais observé à cette saison | dépassement | années comparées |
|---|---|---:|---:|---:|---:|
| LA PLAINE | 2011-06-06 | 23,96 | 12,47 | **+11,50** | 3 |
| LA PLAINE | 2011-06-07 | 22,88 | 12,69 | **+10,19** | 3 |
| LA PLAINE | 2011-06-09 | 20,65 | 12,81 | **+7,84** | 3 |
| LA PLAINE | 2011-06-10 | 19,80 | 13,07 | **+6,74** | 3 |
| LA PLAINE | 2011-06-13 | 21,18 | 14,24 | **+6,94** | 3 |
| BIE6-8 | 2017-09-03 | 17,00 | 11,70 | **+5,29** | **10** |

Le régime propre de LA PLAINE, mois par mois, ne laisse aucune place au doute :

| juin | 2009 | 2011 | 2012 | 2013 |
|---|---:|---:|---:|---:|
| T_eau moyenne | 12,23 | **17,23** | 13,20 | 11,13 |
| débit médian | 0,90 | **2,14** | 0,90 | 2,66 |

| mai | 2009 | 2010 | 2011 | 2012 | 2013 |
|---|---:|---:|---:|---:|---:|
| T_eau moyenne | 11,32 | 8,53 | **22,03** | 10,79 | 8,94 |

Du 20 mai au 14 juin 2011, cette sonde lit 20 à 25 °C sans discontinuer, avec un
**minimum nocturne jamais descendu sous 18,2 °C** alors que les minimales de
l'air tombaient à 1,9 – 12,5 °C, et un débit de 2,6 à 2,9 m³/s. Puis, le
15 juin, elle chute de 22,3 à 12,9 °C **en deux jours pendant que l'air
monte**, et retrouve exactement le régime des trois autres années.

Une rivière vosgienne de tête de bassin à 2,8 m³/s ne porte pas une eau à 22 °C
quand l'air descend à 5 °C la nuit. Ce bloc n'est pas une chronique de rivière.

### 4.3 Ce que cela dit de ma méthode

La règle scellée s'est trompée sur ces six journées, et je peux nommer la faute
précisément : **je n'avais anticipé qu'une seule morphologie d'exondation.**

J'ai construit T1 en supposant qu'une sonde hors d'eau suit l'air et gagne donc
de l'amplitude. C'est vrai d'une sonde nue au soleil dans une flaque — et c'est
exactement le cas de `BIE40-3`, dont les 7 journées ont un rapport d'amplitude
de 1,03 à 1,41, l'amplitude de l'eau *dépassant* celle de l'air. Ce n'est pas
vrai d'une sonde immobilisée dans un milieu chaud et tamponné, qui donne au
contraire une **faible** amplitude, une forte inertie et un découplage total.
Sur cette seconde morphologie, mon T1 pointe précisément à l'envers.

T2 est faux pour une autre raison, plus instructive. Je l'avais formulé « un
débit normal sous une journée marquée, l'eau était là ». La phrase est vraie et
la conclusion ne suit pas : **le débit dit où est la rivière, pas où est la
sonde.** Une rivière à 2,8 m³/s avec une sonde hors de l'eau produit exactement
les valeurs observées.

Le corpus a d'ailleurs signalé lui-même l'incohérence, sans que ma règle sache
la lire : T2 a dit « événement » du 1er au 10 juin (Q ≈ 2,7) puis s'est tu du 11
au 14 (Q ≈ 0,9), alors que ces quatorze jours forment un seul bloc artefactuel
continu. Un témoin qui coupe en deux un phénomène unique ne mesure pas ce
phénomène.

### 4.4 Conclusion, et son statut exact

**Sur les données disponibles, aucune des 27 journées instruites n'apparaît
comme un événement thermique réel, et la conclusion du chantier sur LA PLAINE
n'est pas à reprendre.** Les deux points dont le verdict a bougé — LA PLAINE et
La Canner — l'ont vu bouger sur des journées que la chronique de leur propre
station désigne comme impossibles.

Mais cette conclusion **ne repose pas sur la règle scellée**, qui disait le
contraire sur six journées. Elle repose sur un critère post hoc. Je ne la
présente donc pas comme le résultat de la vérification demandée : je la présente
comme le résultat d'une vérification dont **le protocole a échoué et dont
l'échec est la principale information**.

Et l'inverse mérite d'être dit avec la même franchise : **ce qui, dans ma
méthode, aurait pu produire « exondation » sans que ce soit vrai**, c'est T4. Il
compte les points voisins marqués — mais les points voisins sont jugés par le
même détecteur. Si la marche 1 sous-détecte systématiquement, « aucun autre
point marqué » ne prouve rien : il enregistre le silence d'un instrument, pas
l'absence d'un phénomène. Les 9 verdicts « exondation » de T4 sont à lire sous
cette réserve.

---

## §5 — Ce que le corpus ne permet pas de vérifier

**Aucune journée n'a été tranchée par une observation de terrain, parce qu'il
n'y en a aucune dans le corpus.** Tout ce qui précède est de l'inférence sur des
séries de température, de débit et d'air. Aucune de ces séries ne peut, en
droit, établir qu'une sonde était émergée.

**15 journées sur 27 restent indécidables sous la règle scellée**, et la cause
est presque toujours la même : deux des quatre témoins n'existent pas sur le jeu
concerné.

| ce qui manque | conséquence | journées touchées |
|---|---|---:|
| aucun débit sur `jeu_bienne` | T2 muet | 13 |
| pas de multi-points hors `jeu_bienne` | T4 muet | 14 |
| journée interne à un épisode | T3 muet | 22 |
| `T_eau_min`, `TN` ou `TX` absents | T1 muet | 2 |
| `BIE35-5__NA` illisible (D7) | point non instruit | — |

**Trois années seulement pour LA PLAINE.** Le témoin post hoc, celui qui porte
la conclusion, compare 2011 à trois autres années. Sur `BIE6-8` il en compare
dix, et c'est nettement plus solide. Trois années suffisent à écarter un
dépassement de +11,5 °C ; elles ne suffiraient pas à trancher un écart de
+1 ou +2 °C.

**Ce qu'il faudrait pour décider, et que le corpus n'a pas.**

- Une **photographie de terrain** ou une fiche de tournée datée : c'est la seule
  pièce qui tranche directement, et elle tranche définitivement.
- Une **lecture d'échelle limnimétrique** au droit de la sonde, ou la cote de
  calage de la sonde rapportée à la hauteur d'eau. Le débit à la station ne le
  remplace pas : il dit où est la rivière, pas où est la sonde.
- Une **seconde sonde** au même point, à cote différente. Deux sondes qui
  divergent nomment l'artefact ; une seule ne le peut jamais.
- Pour `jeu_bienne`, une **chronique de débit**, absente pour les 27 points.

**Enfin, une limite qui tient à moi et non au corpus.** J'ai écrit la règle avant
de voir les journées, comme demandé, et c'était la bonne discipline. Mais je
l'ai écrite sans avoir mesuré au préalable **quelles morphologies d'artefact le
corpus contenait** — deux au moins, et de signes opposés sur l'amplitude. Une
règle écrite d'avance ne vaut que ce que vaut la connaissance du phénomène
qu'elle suppose. L'étape 18 n'a pas manqué de rigueur de protocole ; elle a
manqué d'une mesure préalable que rien ne m'interdisait de faire.

---

## Artefacts

Tous sous `out/etape18/`.

| fichier | contenu |
|---|---|
| `REGLE_SCELLEE.txt` | empreinte de la règle, prise avant le premier chiffre |
| `F_aucune_pose.txt` | preuve octet par octet qu'aucune source n'a bougé |
| `A_toutes_marquees.csv` | les 69 journées marquées, seuils franchis ou non |
| `A_sous_ensemble.csv` | les 27 qui coûtent un verdict |
| `B_temoins.csv` | les quatre témoins, journée par journée, avec les quantiles du point |
| `B3_episodes.csv` | eau, air, écart et débit à ± 3 jours de chaque journée |
| `C_verdict.csv` | le classement de la règle scellée |
| `D_regime_interannuel.csv` | le témoin **post hoc**, déclaré comme tel |
| `E_cout_verdict.csv` | détecteur allumé contre éteint, sur les grandeurs publiées |
| `99_console_*.txt` | traces console des trois mesures |
