# THERMIE_BIO V4.6 — Rapport d'étape 9

**Objet.** Poser le **correctif 9** (D51) — `Delta_TMm_liss` est lissée sur le
calendrier de la station d'air —, trancher le choix du support, vérifier la
prédiction, détailler le journal des verdicts, et instruire **D55** sans rien
implémenter.

---

## Artefacts pour cette étape (D34, D54) — motifs contestés puis confirmés

D54 demande de contester le **motif**, pas seulement le verdict. Les huit
motifs déclarés ont été vérifiés dans le code avant la pose. **Aucun n'est
faux** — c'est la première étape où c'est le cas.

| Artefact | Déclaré | Motif déclaré | Motif vérifié | Constaté |
|---|---|---|---|---|
| `05_anomalies.csv` | doit bouger | porte `Delta_TMm_liss` | **oui** — colonne `anomalie_lissee`, `art_05` | **6/6 bougent** |
| `07_t_norm.csv` | doit bouger | `T_normalisee = T − m × Delta_TMm_liss` | **oui** — `core.py:450`, pour `Tmh_norm` **et** `Tmax_norm` | **6/6 bougent** |
| `08_scores.csv` | peut bouger | seuils franchis par des `T_norm` déplacés | **oui** | **1/6 bouge**, 2 valeurs |
| `02_effectifs.csv` | figé | aucune journée retenue ni écartée différemment | **oui** — l'exploitabilité dépend de `T_air`/`T_eau_moy`, la densité de `Tmh` ; ni l'une ni l'autre ne dépend de `Delta_TMm_liss` | **figé** |
| `03_journees_ecartees.csv` | figé | idem | **oui** | **figé** |
| `04_normales.csv` | figé | calculée en amont de `fusionner` | **oui** — `io_data.calculer_normales_ecarts`, appelée avant | **figé** |
| `06_coefficients.csv` | figé | `m` régresse l'eau brute sur l'air brut (D42) | **oui** | **figé** |
| `00`, `01`, `10` | figés | — | — | **figés** |

*`99_log.txt` n'était pas déclaré : 2 jeux sur 6 bougent, sur des lignes de
diagnostic imprimées par la chaîne.*

**Une nuance sur le motif de `08_scores.csv`.** Il annonçait qu'« un
basculement est ATTENDU ici ». Le motif est juste — les `T_norm` se déplacent
bien jusqu'à 1,94 °C — mais **le basculement n'a pas eu lieu au seuil aigu**,
et le §3 dit pourquoi. Un motif exact ne garantit pas la conséquence attendue.

---

## §0 — Carnet de bord

### Le support du lissage : une question qui avait l'air évidente et méritait d'être chiffrée

La commande demandait de trancher entre deux supports et de chiffrer l'écart
« si la réponse n'est pas évidente ». Elle l'était — le même argument que D51
lui-même — mais je l'ai chiffrée quand même, et c'était utile : les deux
supports diffèrent sur **189 valeurs**, jusqu'à **4,276 °C**, soit 22 % de ce
que corrige le correctif 9. Une réponse évidente sur un écart de 22 % n'aurait
pas dû être donnée sans le savoir.

### Un chiffre d'artefact qui n'est pas le chiffre de la prédiction

L'artefact `05_anomalies.csv` montre **824** valeurs déplacées ; la prédiction
en annonçait **854**, et la vérification en trouve **854**. L'écart est de 30,
et il s'explique entièrement : `BIE35-5__NA` est **absent des artefacts** —
sa chaîne échoue et l'échec est la référence (D7) — et ce point porte
exactement **30** des 854 valeurs déplacées.

C'est le même piège qu'à l'étape 8, où 488 avait été requalifié en 473 : un
artefact n'est pas le périmètre d'une mesure. La différence est qu'ici je
l'ai cherché avant de le trouver, et vérifié que le compte fermait au lieu de
me contenter d'une explication plausible : sur les 67 101 lignes communes,
**824 diffèrent et aucune de moins de 5·10⁻⁷** — l'arrondi à six décimales
n'y est pour rien.

### D55, telle qu'elle est écrite, désigne mille journées

La décision pose qu'une journée dont un membre dépasse quand l'autre ne
dépasse pas est signalée sans être exclue. Appliquée à la lettre, elle
désigne **1 002 journées sur 30 points** — trente et une journées par point en
moyenne — contre **9** journées exclues par la conjonction.

Et la mesure dit que ces mille journées ne ressemblent pas aux exclues. Le §4
le détaille. Je n'ai rien implémenté, conformément à la Tâche D ; je remonte
le fait, parce qu'une règle de signalement qui produit cent fois plus de
signalements que d'exclusions n'est pas un garde-fou, c'est un bruit de fond.

### Le cas qui motive D55 est un outlier dans une population qui ne la justifie pas

Le 28 juillet 2015 sur `BIE40-3` porte `R_ampl_rel = 8,51` et
`E_max_rel = 2,77`. Il appartient au groupe « la forme dépasse seule », qui
compte **992** des 1 002 journées discordantes — et ce groupe, pris comme
tel, ressemble aux journées **ordinaires** bien plus qu'aux exclues :
`E_moy_rel` médian **0,84** contre 4,62 pour les exclues et −0,06 pour les
ordinaires, et **1,6 %** de ses journées marquées par la marche 1 contre
**88,9 %** des exclues.

Le cas est réel — il fait partie des six journées que le régime en service
écarte et que le socle ne marque pas — mais il est atypique **dans son propre
groupe**. Généraliser depuis lui conduirait à signaler mille journées pour en
attraper une.

---

## §1 — D44 : le contrôle permanent

**Avant toute modification** : quatre entrées — `LISEZ-MOI.md` (absent de
`ref/v4_5`), `core.py`, `orchestrator.py`, `qc.py` —, exactement les quatre
déclarées, **aucune en CRLF**. Code de retour **0**.

**À la fin** : même liste, le correctif 9 ne touchant que `core.py`, déjà
déclaré. Code de retour **0**, aucun CRLF introduit.

*Le script de correctif de cette étape porte un `rep()` qui **assert** sur
chaque ancre — la leçon de l'étape 8, où trois `str.replace` avaient échoué en
silence dans un script de mesure.*

---

## §2 — Le correctif 9, le choix du support, la prédiction

### B1 — Le support existe, et il déborde largement

`out/etape9/B1_etendue_support.csv`.

| | |
|---|---|
| points où la série d'air couvre toute la chronique d'eau | **32 sur 32** |
| l'air commence avant l'eau de | **0 à 10 398 jours** (jusqu'à 28 ans) |
| l'air finit après l'eau de | **58 à 5 306 jours** |

Le support ne manque nulle part, et il n'est jamais juste suffisant.

### B3 — Deux supports, et pourquoi je retiens le complet

**La question.** Faut-il lisser sur *toutes* les dates de la station d'air
**(b)**, ou seulement sur celles qui *recouvrent* la chronique d'eau **(c)** ?

**La raison de principe est celle de D51 elle-même.** `Delta_TMm_liss` au jour
`d` est une propriété de l'air au jour `d`. La faire dépendre de la date à
laquelle une sonde d'**eau** a commencé ou cessé d'enregistrer, c'est
réintroduire aux bords exactement la dépendance que le correctif retire. Le
support **(b)** est donc le seul cohérent avec la décision qui l'ordonne.

**Le fait le confirme, et l'écart n'est pas négligeable**
(`out/etape9/B3_deux_supports.csv`) :

| | |
|---|---|
| valeurs où (b) et (c) diffèrent | **189** |
| dont **hors** des bords de la chronique d'eau | **0** |
| écart maximal | **4,276 °C** |
| rapporté à ce que corrige le correctif 9 | **22,1 %** |

Les 189 différences sont **toutes** aux bords, comme le mécanisme le
prédisait. Et `min_periods = 1` n'y protège de rien : au bord, le support (c)
rend une « moyenne de sept jours » calculée sur une seule, **sans le
signaler** — la pathologie même que le correctif 2 avait refusée.

*Un écart de 22 % ne se tranche pas au flair. La réponse était évidente ; la
vérifier ne l'était pas.*

### B2 — Ce qui ne change pas

`fenetre` = `lissage_delta` (7) et `min_periods` = **1**, valeurs de V4.5
reprises sans modification. **Seul le support change**, comme aux correctifs 2
et 8. Aucune valeur nouvelle n'entre dans le code.

### La prédiction : **elle tient, sur les cinq grandeurs**

Vérifiée sur son propre périmètre — les 67 392 journées exploitables, et non
les lignes d'un artefact (`out/etape9/B_verification_prediction.txt`) :

| | Prédit à l'étape 8 | Constaté à l'étape 9 |
|---|---|---|
| valeurs déplacées | **854** | **854** |
| points concernés | **32** | **32** |
| écart maximal sur l'anomalie | **4,790 °C** | **4,790 °C** |
| écart maximal sur `T_norm` | **1,939 °C** | **1,939 °C** |

*L'artefact en montre 824 : les 30 manquantes appartiennent à `BIE35-5__NA`,
absent des artefacts parce que sa chaîne échoue (D7). Vérifié : ce point porte
exactement 30 valeurs déplacées, et sur les 67 101 lignes communes, aucune des
824 différences n'est inférieure à 5·10⁻⁷.*

### Ce que le correctif déplace, artefact par artefact

| Artefact | Jeux | Valeurs | Colonnes |
|---|---|---|---|
| `05_anomalies.csv` | **6/6** | 824 | `anomalie_lissee` |
| `07_t_norm.csv` | **6/6** | 3 821 | `anomalie_utilisee`, `T_normalisee` |
| `08_scores.csv` | 1/6 | 2 | `valeur` |
| `99_log.txt` | 2/6 | 5 lignes | diagnostics de la chaîne |
| **tout le reste** | — | **0** | **figé** |

Aucune ligne n'est ajoutée ni retirée nulle part.

---

## §3 — Le journal des verdicts, détaillé

`docs/VERDICTS_MODIFIES.md`, section « correctif 9 ».

### Synthèse

**Sur 32 points, 2 voient une conclusion publiée changer** — `BIE40-3` et
`BIE6-8` — et **dans le même sens** : le pourcentage de stress chronique
augmente. **Aucune catégorie ne change**, ni chronique ni aiguë. Aucun SGVT,
aucun `n_jours_aigus`, aucun `pts_aigu`, aucun score de fraie ne bouge.

| Point | Indicateur | Avant | Après | Franchissements |
|---|---|---|---|---|
| `BIE40-3` | `pct_stress_chronique` | 4,762 % | **4,992 %** | 62 → **65** |
| `BIE6-8` | `pct_stress_chronique` | 0,846 % | **1,077 %** | 11 → **14** |

### Les six journées, une par une

Seuil chronique **18,0 °C** sur les deux points.

| Point | Journée | `Tmh_norm` avant | après | Marge avant | Déplacement |
|---|---|---|---|---|---|
| `BIE40-3` | 2015-07-06 | 16,839 | **18,582** | 1,161 °C | **+1,743** |
| `BIE40-3` | 2015-07-07 | 16,715 | **18,264** | 1,285 °C | **+1,549** |
| `BIE40-3` | 2015-07-10 | 17,740 | **18,671** | 0,260 °C | +0,931 |
| `BIE6-8` | 2017-08-30 | 17,858 | **18,184** | 0,142 °C | +0,326 |
| `BIE6-8` | 2017-09-05 | 17,984 | **18,249** | **0,016 °C** | +0,265 |
| `BIE6-8` | 2017-09-08 | 17,979 | **18,141** | **0,021 °C** | +0,162 |

**La cause, en une phrase :** l'anomalie d'air lissée de ces journées était
calculée en sautant les jours où la sonde d'eau ne mesurait pas ; rétablie sur
le calendrier de la station, elle est plus froide, `m × Delta_TMm_liss`
retranche moins, et `Tmh_norm` monte.

Les trois journées de `BIE6-8` étaient à **2 centièmes à 14 centièmes** du
seuil : elles ont basculé pour un déplacement de deux à trois dixièmes. Les
deux premières de `BIE40-3`, à l'inverse, étaient à plus d'un degré et ont été
déplacées de plus d'un degré et demi. **Aucune journée ne cesse de franchir :
le mouvement est à sens unique.**

### Pourquoi le seuil aigu n'a pas bougé, alors que l'étape l'attendait

Ce n'est pas une affaire de magnitude, c'est une affaire d'**intersection**.

| | |
|---|---|
| journées déplacées | **854 sur 67 392 (1,27 %)** |
| journées à moins de 0,5 °C du **seuil aigu** | **54** sur tout le corpus |
| déplacement médian au voisinage du seuil aigu | **0,000 °C** |
| franchissements du seuil aigu | **101 → 101** |

Sur 98,7 % des journées, le déplacement est **exactement nul**. Pour qu'un
verdict bascule, il faut qu'une journée déplacée soit **aussi** proche d'un
seuil — et les deux ensembles se croisent à peine.

Le cas limite le dit mieux qu'une moyenne : la journée la plus proche du seuil
aigu de tout le corpus est sur `BIE40-3`, à **0,022 °C** sous 23,0 °C. Elle
n'est pas au nombre des 854, et sa marge est **identique** avant et après. À
l'inverse `BIE5-9`, le point qui avait basculé au correctif 2, voit sa journée
la plus proche **s'éloigner** du seuil, de 0,054 à 0,206 °C.

Le seuil chronique, lui, a bougé parce que sa cible est bien plus large :
**743 journées** le franchissent déjà et **839** se tiennent à moins de
0,5 °C.

---

## §4 — D55 instruit

`tests/reference/mesure_d55_discordance.py`. **Aucun code de détection n'est
écrit.** Aucun seuil nouveau : tout se lit au même `k` = 3,0.

### D1 — Combien de journées discordantes, et de combien

Sur **20 502** journées où la marche 2 sait se prononcer :

| Groupe | Journées |
|---|---|
| **exclues** — les deux membres au-dessus de `k` | **9** |
| **discordantes** — un seul membre au-dessus | **1 002** |
| · dont la **forme** (`R_ampl`) dépasse seule | **992** |
| · dont le **niveau** (`E_max`) dépasse seul | **10** |
| ordinaires — aucun membre au-dessus | 19 491 |

La discordance est donc **presque toujours une discordance de forme** : 99 %
des cas.

**Distribution de l'écart entre les deux membres :**

| Groupe | n | médiane | q90 | max | Membre haut (méd.) | Membre bas (méd.) |
|---|---|---|---|---|---|---|
| forme au-dessus | 992 | 3,73 | 7,99 | **21,87** | — | — |
| niveau au-dessus | 10 | 1,59 | 2,88 | 4,54 | — | — |
| les deux (exclues) | 9 | 4,42 | 6,70 | 11,06 | — | — |

L'écart médian des discordantes de forme (3,73) est **du même ordre** que
celui des exclues (4,42) : la seule grandeur de l'écart ne sépare pas les deux
populations. Un sous-critère fondé sur « dépasse largement » ne trouverait pas
sa coupure ici.

### D2 — Combien seraient signalées, et où

**1 002 journées, sur 30 points sur 32.** Les plus concernés : `BIE40-3`
(113), `BIE0-3` (81), `BIE6-8` (74), `BIE42-7` (67), `BIE37-9` (66),
`BIE21-7` (65), `BIE56-1` (64), `BIE27-9` (64).

**C'est 111 fois le nombre de journées exclues** (9). Une règle de signalement
qui produit cent fois plus de signaux que la règle d'exclusion qu'elle
accompagne ne qualifie plus rien.

### D3 — À quoi ces journées ressemblent-elles

**Les grandeurs de comparaison, et pourquoi celles-là.** Comparer sur
`R_ampl_rel` ou `E_max_rel` serait circulaire : ce sont eux qui définissent
les groupes. Les grandeurs retenues sont extérieures à la règle :

- **`E_moy_rel`** — le critère de la **marche 1**, témoin indépendant du même
  phénomène. C'est la plus informative : si les discordantes étaient des
  exondations, la marche 1 devrait les voir monter aussi ;
- **la part marquée par la marche 1** — la même chose, en verdict plutôt qu'en
  valeur ;
- **`ampl_air` (`TX − TN`)** — c'est par elle que l'étape 4 a départagé les
  deux conjonctions candidates ; le vocabulaire est déjà établi ;
- **`R_ampl` brut**, non relativisé — dit si la forme est anormale dans
  l'absolu ou seulement par rapport au mois du point.

| Groupe | n | `E_moy_rel` méd. | marqué marche 1 | `ampl_air` méd. | `R_ampl` brut méd. |
|---|---|---|---|---|---|
| **exclues** | 9 | **4,618** | **88,9 %** | 4,9 °C | 0,781 |
| **discordantes — forme seule** | 992 | **0,839** | **1,6 %** | 6,2 °C | 0,683 |
| **discordantes — niveau seul** | 10 | **3,301** | **70,0 %** | 6,7 °C | 0,381 |
| ordinaires | 19 491 | −0,058 | 0,1 % | 11,0 °C | 0,243 |

**La réponse est nette, et elle est double.**

**Les 992 discordantes de forme ressemblent aux journées ordinaires.** Leur
`E_moy_rel` médian, 0,84, est neuf fois plus faible que celui des exclues, et
**1,6 %** seulement sont marquées par la marche 1 contre 88,9 % des exclues.
Elles ne sont pas identiques aux ordinaires — leur `R_ampl` brut, 0,68, est
proche de celui des exclues, 0,78, et loin des ordinaires, 0,24 — mais sur le
témoin indépendant, elles se rangent du côté ordinaire.

**Les 10 discordantes de niveau ressemblent aux exclues** — `E_moy_rel` médian
3,30, au-dessus de `k`, et 70 % marquées par la marche 1. **Mais six d'entre
elles tombent le même jour, le 1er juin 2011, sur six points différents**
(`BIE10-8`, `BIE21-7`, `BIE27-9`, `BIE37-9`, `BIE56-1`,
`LA PLAINE A RAON-SUR-PLAINE`).

Cette synchronie est décisive. Une sonde sortie de l'eau est une défaillance
**locale** : elle n'a aucune raison de se produire le même jour sur six cours
d'eau. C'est le critère par lequel l'étape 4 avait rejeté la conjonction
`E_moy ET E_max` — sa synchronie maximale de 5 contre 1 pour la conjonction
retenue. **Ces six journées sont un épisode météorologique, pas six
exondations.**

### Ce que la mesure dit de D55

D55, appliquée à la lettre, désigne 1 002 journées dont 992 se rangent, sur le
témoin indépendant, du côté des journées ordinaires, et dont l'essentiel du
reliquat est un épisode météorologique synchrone. **La règle telle qu'elle est
écrite ne survit pas à la mesure.**

Une restriction se présente naturellement et n'introduit **aucun nombre
nouveau** : ne signaler que les discordantes **également marquées par la
marche 1**, c'est-à-dire au même `k`, sur l'autre critère. Elle ramènerait le
compte à **23 journées sur 10 points**. Mais elle a deux défauts que la mesure
révèle aussi : elle **admet** les six journées du 1er juin 2011, qui sont
météorologiques, et elle **exclut** le cas qui motive D55 — le 28 juillet 2015
sur `BIE40-3`, dont l'`E_moy_rel` vaut 2,499 et que la marche 1 ne marque pas.

*Ces éléments sont remontés pour le correctif 1, sans arbitrage de ma part :
la décision porte sur ce que l'écran doit dire, et elle appartient au
commanditaire. Deux alternatives fermées au §5.*

---

## §5 — Alternatives fermées

### Alternative 1 — Le périmètre du signalement de D55

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — D55 à la lettre** | 1 002 journées signalées sur 30 points, contre 9 exclues | c'est la décision telle qu'elle est écrite. Mais 992 des 1 002 ont un `E_moy_rel` médian de 0,84 et ne sont marquées par la marche 1 qu'à 1,6 % : l'écran signalerait trente et une journées par point sans que rien d'indépendant ne les corrobore |
| **B — discordantes ET marquées par la marche 1** | 23 journées sur 10 points ; aucun seuil nouveau, `k` est réutilisé sur l'autre critère | corrobore le signal par un témoin indépendant. Mais admet les 6 journées synchrones du 1er juin 2011, qui sont météorologiques, et **exclut le cas qui motive D55** |
| **C — ne rien signaler** | la conjonction reste stricte, sans accompagnement | contredit D55, qui a été prise en connaissance du cas `BIE40-3` |

*Je n'arbitre pas : D55 est une décision du commanditaire et la Tâche D
demande de l'instruire, pas de la trancher. Je remonte que la branche A, telle
qu'écrite, produit 111 signaux pour 1 exclusion, et que la branche B manque
précisément le cas qui l'a motivée.*

### Alternative 2 — La synchronie comme garde-fou

Les 6 journées du 1er juin 2011 sont détectées par la même règle sur six
points. L'étape 4 avait établi que la synchronie inter-points distingue
l'épisode météorologique de l'exondation.

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — ne pas s'en servir (retenue)** | la synchronie reste un outil de diagnostic du harnais, pas une règle | **D41** : aucune règle de V4.6 ne peut dépendre d'un corpus multi-points. L'application traite **une sonde à la fois** ; elle ne peut pas savoir qu'un autre point a marqué le même jour |
| **B — en faire une règle** | les épisodes synchrones seraient écartés du signalement | il faudrait lever D41, ce qui n'est pas envisageable : la règle serait incalculable au moment où elle sert |

*Je retiens A. La synchronie **instruit** la spécification — elle a servi à
choisir la conjonction à l'étape 4, et elle sert ici à qualifier les dix
journées de niveau — mais elle ne peut pas **entrer** dans le code.*

---

## §6 — Ce qui reste ouvert

- **`Tmm30j`** (`indicateurs.py:55`) porte les deux défauts — support et index
  — et reste en aval de `T_norm`. **D53** : branche A confirmée, hors
  périmètre, non mesuré.
- **Le détecteur de plateau** (`qc.py:129`) porte le défaut d'index ; **D46**
  le rattache au correctif 1.
- **Le défaut de `qc.py:32-36`** relevé à l'étape 5 reste dans le même état.
- **`MOTIF_EAU_ABSENTE`** reste déclaré non exercé.
- **L'affichage de la dégradation déclarée reste différé (D48)** ; ses textes
  sont écrits, §1.5 de la spécification.
- **D55 attend un arbitrage** (§5, alternative 1).
- **Le correctif 1 et la règle de validité restent à écrire.** La mesure de
  cette étape les alimente.
