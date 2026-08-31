# THERMIE_BIO V4.6 — Rapport d'étape 3

*Spécifier le détecteur par la mesure. Aucune ligne de code applicatif modifiée.*

---

## §0 — Carnet de bord

### Trois résultats vont contre ce qui était attendu

Cette étape produit trois mesures dont aucune ne confirme l'hypothèse qui la
motivait. Elles sont livrées telles quelles.

**Le critère pleinement relatif n'est pas moins aveugle — il est beaucoup plus
sévère.** Le critère B ne corrige pas le défaut du critère A : à k = 3, il ne
marque plus que 68 jours sur les 3 408 que le détecteur absolu marque, et perd
12 points sur 30. À k = 4 il en perd 26 sur 30. Le passage à la dispersion
propre ne rééquilibre pas la mesure, il la resserre.

**Le mécanisme d'aveuglement n'existe pas sur ce corpus, et la mesure le dit
maintenant sans ambiguïté.** À durée contrôlée, la médiane propre d'un point
n'explique rien : sa corrélation avec la perte vaut **+0,006**. La durée, elle,
corrèle à **−0,402**. La stratification 2×2 le confirme sur les quatre seuils
informatifs. §2.

**Le maximum d'air n'apporte pas de marge — il en retire.** Rapportée à sa
propre dispersion, la marge de `T_eau_max − TX` est **inférieure** à celle de
`T_eau_max − TM` sur **31 points sur 31**. En degrés les deux marges sont
quasi identiques (+4,74 contre +4,79 °C) ; c'est la dispersion du maximum qui
est plus grande (MAD* 3,59 contre 2,82 °C) et mange l'avantage. §3.

### Ce que j'ai corrigé dans mon propre code

| Défaut | Effet |
|---|---|
| `defauts_litteraux.py` comparait `espece_repere` à `None` | `None` **résout** vers `espece_defaut` (`config.py`, `contexte():52`). Comparer la valeur brute fabriquait un faux écart. Comparaison faite après résolution |
| Même script : `periode_affichage` | La valeur écrite « False → None » n'était pas interprétée. Deux faux positifs sur quatre |
| `mesure_marche2.py` rapportait `part_TN_manquante_pct` sur **toutes** les lignes du fichier d'air | Y compris les décennies sans aucune température. Elle mesurait le vide du fichier, pas celui de TN : 91,6 % annoncés pour `jeu_04` alors que **0** jour porte TM sans TN. Recalculée parmi les jours où TM existe |
| Premier balayage des seuils de validité | Sept valeurs conventionnelles dont **quatre n'écartaient rien** : la distribution observée est bien plus resserrée. Rebalayé sur ses propres déciles |

### Un choix de méthode qu'il faut assumer

Le critère B divise par le MAD. J'ai retenu le **MAD mis à l'échelle**
(`1,4826 × MAD`), qui estime l'écart-type de façon robuste, pour que `k` se
lise comme un nombre d'écarts-types et que `k = 3` soit le seuil d'aberration
usuel. Sans ce facteur, `k` ne serait comparable à rien. C'est écrit dans
`mesure_critere_b.py`, en tête.

Le garde-fou du MAD nul est en place et **n'a jamais servi** : sur les 124
couples (point, mois) du corpus, **aucun** n'a un MAD sous le plancher, et
aucun n'a moins de dix jours. Le cas est traité et non exercé — il faut le
dire, sinon la robustesse annoncée n'est qu'une intention.

### Ce que je n'ai pas fait

Je n'ai pas cherché à sauver le mécanisme d'aveuglement après avoir vu qu'il
ne se manifestait pas. La règle de décision qui départage les trois issues est
écrite **dans le code qui produit les chiffres**, en tête de
`mesure_critere_b.py`, et reproduite intégralement au §2 avant tout résultat.

Je n'ai touché ni `app/`, ni `ref/`, ni la référence : `MANIFEST.sha256`
concorde sur ses 66 artefacts, sans divergence.

---

## §1 — Critère B, et les deux critères côte à côte (Tâche A)

### A1 — Ce qui est mesuré

| | Formule | Ce qu'il relativise |
|---|---|---|
| **Critère A** *(étape 2)* | `ecart − médiane_{point,mois}` > q, q quantile poolé | la **position** seulement |
| **Critère B** *(étape 3)* | `(ecart − médiane_{point,mois}) / MAD*_{point,mois}` > k | la position **et la dispersion** |

`MAD* = 1,4826 × médiane(|ecart − médiane|)`. Le facteur d'échelle est retenu
pour que `k` se lise comme un nombre d'écarts-types robustes.

**Le cas du MAD nul ou quasi nul**, traité explicitement et par avance :

1. `MAD* ≤ 0,05 °C` → le couple (point, mois) est déclaré **non
   diagnosticable** par B. Le plancher n'est pas inventé ni importé du projet
   clos : c'est le seuil que V4.5 utilise déjà pour dire qu'un signal est
   immobile, `plateau_ecart_type_min` (`config.py:89`).
2. moins de **10 jours** dans le couple (point, mois) → médiane et MAD n'y ont
   pas de sens, couple non diagnosticable.

Les points-jours ainsi écartés ne sont ni marqués ni déclarés sains.

**Résultat du garde-fou : il ne se déclenche jamais.** Sur les **124** couples
(point, mois) du corpus, **0** est non diagnosticable, soit **0 point-jour sur
23 816**. Le MAD médian par couple est de 2,2 à 3,7 °C selon les points. Le
traitement est en place ; ce corpus ne l'exerce pas.

### A2 — La même table qu'au §4 de l'étape 2, pour les deux critères

Même régime : `tests/reference_cli/`, détecteur allumé à 4 °C. 23 816
points-jours, 31 points, dont 30 marqués par le critère absolu.

| Critère | seuil | jours abs. | jours rel. | les deux | **perdus** | gagnés | **pts perdus** |
|---|---|---|---|---|---|---|---|
| A poolé | q = 0,90 → 3,453 °C | 3 408 | 2 382 | 1 881 | 1 527 | 501 | **0** |
| A poolé | q = 0,95 → 4,460 °C | 3 408 | 1 191 | 1 042 | 2 366 | 149 | **2** |
| A poolé | q = 0,99 → 6,498 °C | 3 408 | 239 | 234 | 3 174 | 5 | **5** |
| A poolé | q = 0,995 → 7,565 °C | 3 408 | 120 | 120 | 3 288 | 0 | **14** |
| **B dispersion** | k = 2 MAD* | 3 408 | 470 | 423 | 2 985 | 47 | **0** |
| **B dispersion** | k = 3 MAD* | 3 408 | 68 | 67 | 3 341 | 1 | **12** |
| **B dispersion** | k = 4 MAD* | 3 408 | 10 | 10 | 3 398 | 0 | **26** |
| **B dispersion** | k = 5 MAD* | 3 408 | 3 | 3 | 3 405 | 0 | **28** |
| **B dispersion** | k = 6 MAD* | 3 408 | 0 | 0 | 3 408 | 0 | **30** |

**Le critère B est beaucoup plus sévère que le critère A.** À k = 3, valeur
usuelle de l'aberration, il marque **68** jours contre 3 408 pour l'absolu et
1 191 pour A à q = 0,95. À partir de k = 4 il perd 26 points sur 30, et à
k = 6 il ne marque plus rien du tout.

Normaliser par la dispersion propre n'a donc pas l'effet qu'on en attendait.
L'explication mécanique tient en un chiffre : le MAD* médian de l'écart vaut
**2,8 °C**. Un jour à +4 °C absolu se situe, pour un point de médiane nulle,
à 4/2,8 ≈ **1,4 MAD*** de son habitude — bien en deçà de tout seuil
d'aberration. Le critère absolu de V4.5, avec ses 4 °C, est en réalité **plus
permissif** que « trois écarts-types robustes ».

Un seul régime rend B comparable à A : **k = 2**, où il marque 470 jours,
perd zéro point et en gagne 47. C'est le seul point de la grille où la
dispersion propre ajoute quelque chose sans tout détruire.

---

## §2 — Durée ou médiane ? Et le cas Château-Voue (A3, A4)

### La règle de décision, écrite avant d'avoir regardé

Elle figure en tête de `mesure_critere_b.py`, dans le code même qui produit
les chiffres. Reproduite ici sans retouche :

> **CONCLUSION « LE MÉCANISME EXISTE »** si, à durée contrôlée, le taux de
> perte des points à médiane haute dépasse celui des points à médiane basse
> d'au moins **20 points de pourcentage**, dans le même sens, pour au moins
> deux des valeurs de k testées.
>
> **CONCLUSION « LE MÉCANISME N'EXISTE PAS »** si cet écart est inférieur à
> **10 points de pourcentage**, ou de signe contraire, pour la majorité des
> valeurs de k testées.
>
> **CONCLUSION « LE CORPUS NE PERMET PAS DE TRANCHER »** si l'une au moins de
> ces conditions est remplie : une cellule de la stratification compte moins de
> **3 points** ; le signe de l'écart change avec k sans régularité ; ou
> l'étendue des médianes propres parmi les points marqués est inférieure à
> **2 °C**.

Une précision devenue nécessaire en cours de mesure, et qui n'affaiblit pas la
règle : **un seuil qui perd tous les points, ou aucun, ne porte aucun
contraste**. Un taux de perte global de 0 % ou supérieur à 80 % rend la
comparaison entre strates vide de sens. Ces seuils sont déclarés
**non informatifs** et le tableau le dit ; le verdict se lit sur les autres.

### La stratification

Points marqués par l'absolu (30), coupés à leur médiane : durée **450 jours**,
médiane propre **+0,73 °C**. Les quatre cellules comptent 7 ou 8 points.

| Seuil | pts perdus | taux | informatif ? | **effet DURÉE** | **effet MÉDIANE** |
|---|---|---|---|---|---|
| A q = 0,90 | 0 | 0 % | non — rien perdu | +0,0 | +0,0 |
| A q = 0,95 | 2 | 7 % | **oui** | **+13,4** | +0,9 |
| A q = 0,99 | 5 | 17 % | **oui** | **+19,6** | −5,4 |
| A q = 0,995 | 14 | 47 % | **oui** | **+38,4** | −24,1 |
| B k = 2 | 0 | 0 % | non — rien perdu | +0,0 | +0,0 |
| B k = 3 | 12 | 40 % | **oui** | **+26,8** | +1,8 |
| B k = 4 | 26 | 87 % | non — saturé | −13,4 | −0,9 |
| B k = 5 | 28 | 93 % | non — saturé | −12,5 | +12,5 |
| B k = 6 | 30 | 100 % | non — saturé | +0,0 | +0,0 |

*Effet DURÉE = (taux de perte des courts − taux des longs), moyenné sur les
deux strates de médiane. Effet MÉDIANE = (taux des médianes hautes − taux des
basses), moyenné sur les deux strates de durée. En points de pourcentage.*

**Sur les quatre seuils informatifs :**

- l'effet **DURÉE** vaut **+13,4 · +19,6 · +38,4 · +26,8** — toujours positif,
  toujours large, croissant avec la sévérité ;
- l'effet **MÉDIANE** vaut **+0,9 · −5,4 · −24,1 · +1,8** — jamais au-dessus
  de +10, négatif deux fois sur quatre.

### Le verdict, obtenu en appliquant la règle telle qu'elle était écrite

- « **Le mécanisme existe** » exige ≥ +20 points sur l'effet médiane, deux
  fois. Le maximum observé sur les seuils informatifs est **+1,8**. **Non
  atteint.**
- « **Le mécanisme n'existe pas** » exige < 10 points ou signe contraire pour
  la majorité. Vérifié sur **4 seuils informatifs sur 4**. **Atteint.**
- « **Ne permet pas de trancher** » : aucune cellule sous 3 points (elles en
  comptent 7 ou 8) ; l'étendue des médianes propres est de **6,49 °C**
  (−3,69 à +2,80), très au-dessus des 2 °C exigés ; et sur les seuils
  informatifs le signe de l'effet médiane ne fait qu'osciller autour de zéro,
  sans jamais s'écarter dans le sens attendu. **Aucune condition remplie.**

> **Le mécanisme d'aveuglement par décalage de la médiane propre n'existe pas
> sur ce corpus. Ce qui gouverne la perte est la durée de la chronique.**

Les corrélations sur les 30 points marqués, à k = 3, disent la même chose sans
stratification :

| | corrélation avec la perte |
|---|---|
| durée de la chronique | **−0,402** |
| **médiane propre du point** | **+0,006** |
| MAD* du point | −0,104 |
| nombre de jours marqués par l'absolu | −0,287 |

La médiane propre a une corrélation **nulle au troisième chiffre**.

### Le contre-exemple, point par point

Dans la strate des chroniques courtes, à k = 3 :

| Point | durée | médiane propre | perdu ? |
|---|---|---|---|
| `LIZ13-5` | 319 j | **+2,80 °C** *(la plus haute du corpus)* | **non** |
| `BIE46-5` | 443 j | +2,12 °C | **non** |
| `LGV11-8` | 122 j | +1,94 °C | **non** |
| `Le ruisseau de la Flotte` | 369 j | +1,59 °C | **oui** |
| `BLE3-0` | 110 j | **−3,35 °C** | **oui** |
| `FLU8-4` | 214 j | −2,55 °C | **oui** |
| `BCH5-7` | 446 j | −2,47 °C | **oui** |

Les trois points aux médianes les plus hautes sont **conservés** ; trois des
quatre points aux médianes les plus basses sont **perdus**. C'est le mécanisme
attendu, exactement à l'envers.

### A4 — Le ruisseau de la Flotte à Château-Voue

C'est bien le meilleur candidat du corpus au profil « sonde chroniquement mal
posée », et il est perdu par les deux critères.

| | |
|---|---|
| jours de juin à septembre | **369** |
| médiane propre de l'écart | **+1,590 °C** |
| MAD* propre | **1,898 °C** *(le 2ᵉ plus faible de la strate courte)* |
| jours au-dessus de +4 °C absolu | **35**, soit **9,49 %** |
| excursion maximale, critère A | **+4,160 °C** au-dessus de sa médiane |
| excursion maximale, critère B | **+2,087 MAD*** |

| Critère | perdu ? |
|---|---|
| A q = 0,90 (3,453 °C) | non — 6 jours marqués |
| A q = 0,95 (4,460 °C) | **oui** — son excursion maximale, 4,160 °C, passe juste sous le seuil |
| A q = 0,99 et 0,995 | **oui** |
| B k = 2 | non — 1 jour marqué |
| B k = 3, 4, 5, 6 | **oui** — son excursion maximale plafonne à 2,087 MAD* |

**Sa perte s'explique-t-elle par sa durée, par sa médiane, ou les deux ?**
Par **ni l'une ni l'autre prise seule** — par la compression de sa
distribution.

Le calcul est direct : un jour à exactement +4 °C absolu se situe, pour ce
point, à `(4 − 1,590) / 1,898 = **1,27 MAD***` de sa propre habitude. Ses
35 jours « suspects » au sens absolu sont, de son point de vue à lui, des
journées à peine au-dessus de l'ordinaire. Sa médiane haute y contribue — elle
rapproche le seuil absolu de son centre — mais son MAD* faible y contribue
autant, en dilatant la mesure de l'écart.

Et la démonstration que la médiane seule n'explique rien tient dans la
comparaison : `LGV11-8` a une médiane **plus haute** (+1,94 contre +1,59) et
n'est pas perdu, parce que son excursion maximale est plus franche. La perte
tient au **rapport** entre l'excursion et la dispersion, pas au niveau.

---

## §3 — Marche 2 : ce que TX apporterait (Tâche B)

Rappel : `io_data.charger_air_brut` ne lit ni TN ni TX (`io_data.py:432`,
`usecols`). Le harnais lit donc les fichiers d'air lui-même, en parallèle,
avec le même parseur de dates et la même conversion décimale que V4.5. **Aucun
code applicatif n'est modifié**, et rien de ce qui suit n'entre dans la
référence de non-régression.

### B3 — TN et TX sont-ils exploitables ? Oui, sur les six jeux

| Jeu | jours avec TM | TM **sans** TN ou TX | TN/TX **sans** TM | incohérences `TN ≤ TM ≤ TX` | exerce la marche 2 |
|---|---|---|---|---|---|
| jeu_02 | 6 159 | **0** (0,00 %) | 49 | 5 (0,081 %) | **oui** |
| jeu_03 | 4 374 | **0** | 9 | 4 (0,091 %) | **oui** |
| jeu_04 | 2 237 | **0** | 0 | 2 (0,089 %) | **oui** |
| jeu_05 | 7 167 | **0** | 18 | 6 (0,084 %) | **oui** |
| jeu_bienne | 11 141 | **0** | 0 | 21 (0,188 %) | **oui** |
| jeu_exemples_v45 | 2 384 | **0** | 1 | 2 (0,084 %) | **oui** |

**Aucun jeu ne porte les colonnes sans les remplir.** La marche 2 ne perdrait
**aucun** jour aujourd'hui exploitable : les périodes de TM, TN et TX sont
identiques à un jour près sur les six fichiers. Elle en **gagnerait** même
quelques-uns — 49 sur `jeu_02`, 18 sur `jeu_05` — où TN et TX existent sans
TM.

Les incohérences `TN ≤ TM ≤ TX` sont marginales : **0,08 à 0,19 %** des
triplets, 40 jours au total sur 33 462. Elles ne sont pas nulles et méritent
d'être comptées, pas d'inquiéter.

### B1/B2 — Le maximum contre la moyenne, relativisés de la même façon

Les deux écarts sont relativisés par la dispersion propre — le meilleur
critère de la tâche A —, sur les points-jours que **les deux** savent
diagnostiquer.

| k | les deux | **MOYENNE seule** | **MAXIMUM seul** | pts moy. | pts max. | Jaccard |
|---|---|---|---|---|---|---|
| 2 | 293 | 177 | **359** | 31 | 30 | 35,3 % |
| 3 | 18 | 50 | 24 | 18 | 17 | 19,6 % |
| 4 | 1 | 9 | 2 | 4 | 3 | 8,3 % |
| 5 | 0 | 3 | 0 | 2 | 0 | 0,0 % |
| 6 | 0 | 0 | 0 | 0 | 0 | 0,0 % |

**Le critère au maximum n'est pas plus sévère : il est différent.** À k = 2 il
marque 359 jours que la moyenne ne voit pas, quand la moyenne en marque 177
que lui ne voit pas. Les deux ensembles ne sont emboîtés à aucun seuil, et
leur recouvrement (indice de Jaccard) ne dépasse jamais 35 %. Ils ne mesurent
pas la même chose.

Mais **plus discriminant, non**. La marge, mesurée :

| | médiane en régime immergé | limite sous exondation | **marge** | MAD* | **marge en MAD*** |
|---|---|---|---|---|---|
| `E_moy = T_eau_max − TM` | +0,59 °C | +5,40 °C *(= TX − TM)* | **+4,79 °C** | 2,82 °C | **+1,82** |
| `E_max = T_eau_max − TX` | −4,74 °C | 0 °C | **+4,74 °C** | 3,59 °C | **+1,41** |

En **degrés**, les deux marges sont presque égales, et le maximum l'emporte
sur 19 points sur 31. En **MAD***, la seule unité comparable entre deux
grandeurs de dispersions différentes, **la moyenne l'emporte sur 31 points sur
31** ; le gain médian du maximum vaut **−0,38 MAD***.

La raison est mesurable : `E_max` a une dispersion systématiquement plus
grande (MAD* 3,59 contre 2,82 °C). Le maximum d'air varie davantage d'un jour
à l'autre que sa moyenne, et cette variation supplémentaire est du bruit du
point de vue de la sonde. La marge gagnée en niveau est reperdue en
dispersion.

**Une réserve d'interprétation, qui est importante.** Le projet clos oppose
`E_max` à **`E_min`**, en montrant que le minimum n'a aucune marge avec une
station de référence haute et froide. Ce n'est pas la comparaison faite ici,
qui oppose `E_max` à `E_moy` — celle que la tâche demandait. Rien de ce qui
précède ne contredit l'argument du projet clos ; cela mesure une autre paire.

---

## §4 — Ce que la règle de validité écarterait (Tâche C)

31 points de la référence qui fait foi, **31 estimations de `m_estival`** et
**33 de `m_saisonnier`** — `jeu_04` en compte deux, une par espèce
cyprinicole. Pentes OLS strictement identiques à celles que V4.5 calcule ;
seuls les écarts-types changent.

### C1 — Newey-West

Écarts-types robustes à l'autocorrélation, noyau de Bartlett, décalage maximal
`L = ⌊4 (n/100)^(2/9)⌋` — la règle usuelle de la littérature, écrite dans le
code plutôt qu'importée. Décalage médian retenu : **5 jours**.

Détail par point : `out/etape3/validite_m_par_point.csv`.

### C2 — La distribution, et le balayage

| Coefficient | n | min | p10 | q1 | **médiane** | q3 | p90 | max |
|---|---|---|---|---|---|---|---|---|
| `m_estival` | 31 | 0,0228 | 0,0363 | 0,0387 | **0,0444** | 0,0582 | 0,0782 | **0,1255** |
| `m_saisonnier` | 33 | 0,0270 | 0,0391 | 0,0454 | **0,0498** | 0,0910 | 0,1322 | **0,2184** |

**La distribution est bien plus resserrée que le repère du projet clos.** Le
maximum observé sur `m_estival` vaut 0,1255 : **inférieur à 0,15**.

Balayage sur les déciles de la distribution observée, plus les valeurs rondes.
Le 0,15 du projet clos y figure comme **repère, jamais retenu** (D15).

| Seuil | `m_estival` sortent | `m_saisonnier` sortent |
|---|---|---|
| 0,0363 *(p10)* | 27 / 31 — 87,1 % | 30 / 33 — 90,9 % |
| 0,0427 *(p30)* | 18 / 31 — 58,1 % | 27 / 33 — 81,8 % |
| 0,0455 *(p40)* | 14 / 31 — 45,2 % | 24 / 33 — 72,7 % |
| **0,05** | 10 / 31 — 32,3 % | 16 / 33 — 48,5 % |
| 0,0607 *(p70)* | 8 / 31 — 25,8 % | 12 / 33 — 36,4 % |
| 0,0829 *(p80)* | 3 / 31 — 9,7 % | 10 / 33 — 30,3 % |
| **0,10** | 1 / 31 — 3,2 % | 7 / 33 — 21,2 % |
| **0,15** *(repère, non retenu)* | **0 / 31 — 0,0 %** | 2 / 33 — 6,1 % |
| 0,20 | 0 / 31 | 1 / 33 — 3,0 % |

**Le repère de 0,15 n'écarterait rien du tout sur `m_estival`.** Il est
au-dessus du maximum observé. C'est la démonstration la plus nette qu'un seuil
calé sur une autre grille ne se transpose pas : il ne serait pas seulement
inadapté, il serait **inopérant**.

### C3 — BLE3-0, et la borne [0 ; 1,2]

`BLE3-0` porte `m_estival = −0,010025`, `R² = 0,001711`, `n = 107` jours.

**Sa demi-largeur d'intervalle de confiance vaut 0,0440.** C'est **en dessous
de la médiane du corpus** (0,0444). Autrement dit : la pente la plus
dépourvue de sens du corpus est aussi l'une des plus **précisément** estimées.

Il sort donc **à partir d'un seuil de 0,0427** — c'est-à-dire au trentième
percentile, un seuil qui écarte simultanément **18 points sur 31**. Il ne sort
à **aucun** des seuils qui laisseraient le corpus utilisable.

Une règle fondée sur la seule précision de la pente ne sépare pas ce point du
reste. Les critères qui le séparent sont d'une autre nature :

| Critère | `m_estival` : combien sortent | BLE3-0 sort ? |
|---|---|---|
| précision : demi-IC > 0,05 | 10 / 31 — 32,3 % | **non** |
| précision : demi-IC > 0,10 | 1 / 31 — 3,2 % | **non** |
| précision : demi-IC > 0,15 *(repère)* | 0 / 31 | **non** |
| **variance expliquée : R² < 0,30** | 4 / 31 — 12,9 % | **oui** |
| **domaine : pente hors [0 ; 1,2]** | **1 / 31 — 3,2 %** | **oui** |
| effectif : n < 20 | 0 / 31 | non |

**Combien de points ont un `m` hors [0 ; 1,2] ?** Une seule estimation sur les
64 : `BLE3-0`, `m_estival = −0,010`. Aucune sur `m_saisonnier`.

La borne qui protège aujourd'hui le seul coefficient saisonnier
(`core.py:258`) attraperait donc, étendue à l'estival comme D21 le prévoit,
exactement le point que l'étape 2 avait signalé — et lui seul.

Aucune recommandation de seuil n'est formulée.

---

## §5 — Défauts littéraux (Tâche D, correctif 7 / D22)

Revue des **50 champs** des trois dataclasses, widget par widget.
`out/etape3/defauts_litteraux.csv`.

| Catégorie | Nombre | Ce que cela veut dire |
|---|---|---|
| **dérivé** du dataclass | 8 | le widget passe `qc.<champ>` en défaut : le lien tient |
| **littéral** | **19** | le défaut est écrit en dur dans l'appel |
| **détecté** sur le fichier | 9 | le défaut vient du sniff ou de la station d'air — légitime |
| **non exposé** | 14 | aucun widget ; le dataclass s'applique |

**Sur les 19 littéraux, 2 divergent aujourd'hui du dataclass** — les deux déjà
connus :

| Ligne | Champ | Interface | Dataclass | Effet |
|---|---|---|---|---|
| `app.py:162-163` | `hors_eau_ecart_seuil` | **10,0** | **4,0** | **OUI** — pilote le détecteur, donc les journées retenues, donc `m` et `T_norm` |
| `app.py:166` | `hors_eau_exclut_saison` | **False** | **True** | **OUI** — saison entière ou jours suspects seuls |

**Les 17 autres coïncident aujourd'hui — et c'est précisément le risque.** Un
littéral qui coïncide ne se voit pas ; il diverge le jour où le dataclass
change, sans qu'aucun test ne le dise. Les plus exposés :

| Ligne | Champ | Littéral | Effet possible sur la chaîne |
|---|---|---|---|
| `app.py:105` | `normales_fenetre_lissage` | `10` | **oui** — largeur du lissage des normales, donc `Delta_TMm` |
| `app.py:107-108` | `normalisation_lissage_delta` | `7` | **oui** — largeur du lissage de l'anomalie, donc `T_norm` |
| `app.py:106` | `normales_min_annees` | `20` | non — seuil d'avertissement seul (`io_data.py:524`) |
| `app.py:319` | `fichier_normales` | `None` | **oui** — bascule vers la branche `EcartNormales` pré-calculé |
| `app.py:116` | `seuil_comblement_desinf` | `0.10` | hors périmètre |
| `app.py:135-136` / `139-140` | `stress_plancher_pct`, `stress_corr_r2_min` | `10.0`, `0.10` | hors périmètre |

**Trois défauts littéraux d'une nature particulière : les défauts par
position.** Ils ne suivent pas le dataclass mais l'**ordre** d'une structure.

| Ligne | Champ | Littéral | Ce dont il dépend |
|---|---|---|---|
| `app.py:70-72` | `contexte_piscicole` | `index=1` | l'ordre d'insertion du dict `CONTEXTES`. Réordonner ce dict changerait le défaut de l'interface, silencieusement |
| `app.py:78-79` | `espece_repere` | `index=0` | l'ordre de `especes_disponibles()`, qui place `espece_defaut` en tête. La coïncidence avec la résolution de `None` (`config.py`, `contexte():52`) tient à une convention, pas à une référence |
| `app.py:95-99` | `mode` | `index=1` | l'ordre de la liste d'options |

Les trois coïncident aujourd'hui avec le dataclass. Aucun ne le lit.

Neuf autres défauts viennent d'une **détection sur le fichier** — feuille
Excel, ligne d'en-tête, colonnes, station d'air. Ils ne relèvent pas du
correctif 7 : leur source légitime est le fichier, pas le dataclass. Un seul
mérite d'être noté, `eau_ligne_entete` (`app.py:231`) : le dataclass dit
`None` et l'interface transmet un **entier** égal à la détection. Même valeur,
autre chemin — `lire_brut` applique alors ce nombre au lieu de re-détecter.

Rien n'est corrigé.

---

## §6 — Questions ouvertes

**1. Le corpus ne porte aucun cas d'aveuglement, et il faut décider si c'en
est un résultat ou une limite.** La mesure est nette : à durée contrôlée, la
médiane propre n'explique rien (r = +0,006), et les points aux médianes les
plus hautes sont les mieux détectés. Ce qui les départage : soit le mécanisme
n'a pas d'objet sur un réseau où aucune sonde n'est mal posée en permanence —
la médiane la plus haute du corpus vaut +2,80 °C contre un seuil de 4 °C —,
soit il faudrait un point dont on sait **par le terrain** qu'il est
chroniquement exondé pour l'exercer. `BIE40-3` porte cette réserve
d'implantation au `MANIFESTE.md` du projet clos et n'est perdu à aucun seuil.

**2. Le critère B, tel qu'il est, ne remplace pas le détecteur en service.**
À aucun k il ne reproduit l'ordre de grandeur du critère absolu : k = 2 marque
470 jours contre 3 408, k = 3 en marque 68. Ce qui les départage : soit
l'objectif est de marquer **moins** — et il faut alors dire combien de jours
on accepte de ne plus écarter —, soit la dispersion propre n'est pas la bonne
échelle et il faut regarder l'écart en degrés relativisé à la seule position,
c'est-à-dire le critère A à q = 0,90, seul réglage qui perd zéro point tout en
en gagnant 501.

**3. Le maximum d'air ne gagne pas de marge, mais il voit autre chose.** Les
deux critères ne se recouvrent qu'à 35 % au mieux. Ce qui les départage :
soit la marge en unités de dispersion est le bon juge — et alors la moyenne
suffit —, soit ce que le maximum voit seul (359 jours à k = 2) mérite d'être
regardé pour ce qu'il est, et la question devient laquelle des deux erreurs on
préfère. Cette mesure ne le dit pas.

**4. Une règle de validité fondée sur la précision de la pente serait
inopérante ici.** La demi-largeur d'IC médiane vaut 0,044 et le maximum 0,126 ;
tout seuil au-dessus de 0,13 n'écarte rien, tout seuil qui attrape `BLE3-0`
écarte 18 points sur 31. Ce qui les départage : soit D21 vise la **précision**,
et il faut alors accepter qu'elle ne sépare pas `BLE3-0` du reste ; soit elle
vise la **validité** au sens de « la pente veut-elle dire quelque chose », et
les critères qui le font sont le R² et le domaine — ceux qui existent déjà à
`core.py:258` pour le seul saisonnier.

**5. `jeu_04` produit deux `m_saisonnier` et donc deux `Tmh_norm_fraie`.**
Retenu au registre à l'étape 2. La règle de validité de D21 s'appliquera-t-elle
à chaque espèce séparément, ou au couple ? La question ne se pose pas sur les
autres jeux, qui n'en ont qu'une.

**6. Le garde-fou du MAD nul n'est pas exercé.** Zéro couple (point, mois) sur
124. Il est écrit, documenté, et le corpus ne le teste pas — comme la branche
du débit désinfluencé et celle des normales pré-calculées, déjà nommées à
l'étape 1.
