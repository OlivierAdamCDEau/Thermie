# Journal des verdicts modifiés

**Décision D43.** Ce document est **cumulatif** et n'est **jamais réécrit**.
Chaque correctif y ajoute sa section ; les sections antérieures restent en
l'état, même si un correctif ultérieur revient sur leurs valeurs — auquel cas
il l'écrit dans la sienne.

## Ce qui entre ici, et ce qui n'y entre pas

Y entre **toute conclusion publiée qui change** : SGVT, points de
vulnérabilité, pourcentages de fraie, seuils franchis, statut de
normalisation. C'est-à-dire tout ce qu'un lecteur du rapport aurait pu citer.

N'y entre pas ce qui bouge sans se publier — une valeur intermédiaire, une
colonne d'artefact du harnais, un décompte de journées. Ces mouvements sont
chiffrés dans les rapports d'étape ; ils ne changent aucune conclusion.

Chaque ligne porte l'**avant**, l'**après**, et la **cause en une phrase**.

---

## Correctif 2 — index calendaire des fenêtres glissantes (étape 6)

*Section ouverte rétroactivement à l'étape 7, en application de D43.*

**Ce que le correctif a changé dans la chaîne.** Les moyennes mobiles de
`core.fusionner` s'appliquaient sur un index positionnel : une fenêtre de sept
lignes n'est une fenêtre de sept jours que si la série est continue. Sur le
corpus, 1 131 journées (1,68 %, 26 points sur 32) portaient une fenêtre qui
enjambait une lacune, la plus longue de 1 716 jours.

### Verdicts de vulnérabilité

| Point | Indicateur | Avant | Après | Cause |
|---|---|---|---|---|
| **`BIE5-9`** | `n_jours_aigus` | **1 j** | **0 j** | Sa seule journée aiguë, le 31/07/2022, était à `Tmax_norm` = 23,365 °C pour un seuil de 23,000 : son anomalie d'air lissée avait été moyennée sur une fenêtre enjambant une lacune de 600 jours ; corrigée, elle tombe à 22,946 °C et repasse sous le seuil. |
| **`BIE5-9`** | `pts_aigu` | **1 /3** | **0 /3** | Conséquence directe de la ligne ci-dessus. |
| **`BIE5-9`** | **`sgvt`** | **3,167 /10** | **2,500 /10** | Conséquence directe : la composante aiguë passe de 1 à 0. La catégorie reste « Risque Modéré ». |

**C'est le seul changement de conclusion de tout le correctif 2.**

### Pourcentages de stress chronique

| Point | Avant | Après | Cause |
|---|---|---|---|
| `BIE40-3` | 4,605 % | 4,762 % | `Tmh_norm` corrigé sur les journées dont la fenêtre enjambait une lacune ; l'effectif `n_jours_tmh` passe de 1 303 à 1 302. |
| `BIE42-7` | 10,865 % | 10,999 % | idem, effectif inchangé. |
| `BIE51-0` | 8,815 % | 8,540 % | idem. |
| `BIE6-8` | 0,691 % | 0,846 % | idem ; `n_jours_tmh` passe de 1 302 à 1 300. |

Aucune de ces quatre variations ne fait changer de catégorie : les quatre
points restent dans la classe de vulnérabilité chronique qu'ils avaient.

### Pourcentages de fraie

Sept lignes de fraie sur les vingt et une du jeu `jeu_bienne` changent. **Le
score `P` reste identique dans les sept cas** : ce sont les pourcentages
publiés qui bougent, pas la note.

| Point | Espèce | Avant (optimum / élargie / létal) | Après |
|---|---|---|---|
| `BIE0-3` | ombre commun | 42 % / 50 % / 8 % → P=2 | **41 % / 51 %** / 8 % → P=2 |
| `BIE32-4` | ombre commun | 62 % / 31 % / 7 % → P=2 | **63 % / 30 %** / 7 % → P=2 |
| `BIE5-2` | ombre commun | 52 % / 45 % / 3 % → P=1 | **51 % / 46 %** / 3 % → P=1 |
| `BIE5-9` | ombre commun | 50 % / 43 % / 7 % → P=2 | **51 % / 42 %** / 7 % → P=2 |
| `BIE50-5` | ombre commun | 57 % / 37 % / 7 % → P=2 | 57 % / **36 %** / 7 % → P=2 |
| `BIE6-8` | ombre commun | 56 % / 44 % / 0 % → P=1 | 56 % / **43 %** / 0 % → P=1 |
| **`TAC16-4`** | ombre commun | 83 % / 17 % / 0 % → P=0 | **80 % / 20 %** / 0 % → P=0 |

*Cause commune :* la fenêtre de fraie est évaluée sur `Tmh` ; les journées dont
la moyenne mobile enjambait une lacune changent de valeur, et la répartition
entre optimum, plage élargie et létal se déplace d'un ou deux points.
`TAC16-4` porte le plus grand écart, trois points de pourcentage.

*L'étape 6 mentionnait trois de ces lignes sans les détailler, son diff étant
tronqué à l'affichage. Le relevé complet en compte sept.*

### Ce qui n'a pas changé

`06_coefficients.csv` : **aucun `m` ne bouge**, sur aucun des 32 points. Le
coefficient de couplage air–eau est une régression de l'eau **brute** sur
l'air **brut** ; le lissage n'y entre pas (D42). Aucun statut de normalisation
ne change donc, et aucune pente ne franchit un seuil de validité.

---

## Correctif 5 — jointure gauche eau/air, et statut de densité (étape 7)

**Ce que le correctif a changé dans la chaîne.** La jointure eau/air de
`core.fusionner` était INTERNE : elle effaçait, sans motif ni compte, toute
journée d'eau que la station d'air ne couvre pas. Mesuré avant correction :
**636 journées sur 68 028 (0,93 %), sur 23 des 32 points**, dont
`La Moselle à Hielle` qui perdait **102 de ses 303 journées — 33,7 %, d'un
seul tenant, du 6 juillet au 15 octobre 2012** — et
`LA PLAINE A RAON-SUR-PLAINE` **330 sur 1 545 (21,4 %)**, dont l'année 2008
entière. Ces journées sont désormais conservées et marquées
`non_diagnosticable`, avec leur motif.

### Aucun verdict publié ne change

**C'est le résultat, et il est voulu.** Rejeu du code corrigé contre le rejeu
du correctif 2, harnais identique des deux côtés : **65 artefacts sur 66 sont
figés au bit près**, `08_scores.csv` compris. Le seul écart tient à deux
numéros de ligne dans une trace d'erreur figée, que l'ajout de code a
déplacés :

| Artefact | Avant | Après |
|---|---|---|
| `jeu_bienne/99_log.txt` l. 298 | `orchestrator.py", line 166, in run` | `orchestrator.py", line 175, in run` |
| `jeu_bienne/99_log.txt` l. 300 | `core.py", line 197, in analyse_sensibilite` | `core.py", line 371, in analyse_sensibilite` |

Même fichier, même fonction, même message : aucune conclusion n'en dépend.

**Pourquoi aucun verdict ne bouge.** Les journées que la jointure effaçait
n'entraient dans aucun calcul — c'est précisément ce que « effacer » voulait
dire. Les conserver ne les fait pas entrer : elles restent hors de la chaîne,
mais **nommées**. Le correctif ne change pas ce qui est calculé, il change ce
qui est **dit** de ce qui ne l'est pas.

C'est ce qu'un correctif de visibilité doit produire. S'il avait déplacé un
SGVT, c'est qu'il aurait fait autre chose que ce qu'il annonce.

### Ce qui change, et qui n'est pas un verdict

Pour mémoire, hors journal : `02_effectifs.csv` voit sa colonne
`journees_perdues_hors_qc` tomber à **0 partout** — les pertes ne sont plus
anonymes, elles sont réparties entre `journees_non_diag_air_absent` et
`journees_non_diag_densite`. `03_journees_ecartees.csv` cesse d'être une
déduction du harnais et devient une lecture de la trace produite par
l'application. Ces mouvements sont chiffrés au §3 du rapport d'étape 7 ; ils
ne changent aucune conclusion publiée.

---

## Correctif 8 — lissage de `Tmh` sur la chronique d'eau complète (étape 8)

**Ce que le correctif a changé dans la chaîne.** `Tmh` est une moyenne mobile
de température d'**eau** ; elle était pourtant lissée sur les seules journées
appariées à une température d'air. Une journée d'eau bien mesurée mais privée
d'air y faisait un trou, et ce trou déplaçait la moyenne de ses voisines.
Mesuré : **473 valeurs de `Tmh` déplacées (0,70 %) sur 22 des 32 points**,
écart maximal **1,099 °C**, **3 journées** qui n'avaient pas de `Tmh` en
reçoivent une, **0** qui en perd une.

### Verdicts de vulnérabilité

**Aucun.** Ni SGVT, ni `n_jours_aigus`, ni `pts_aigu`, ni score de fraie, ni
statut de normalisation ne change sur aucun des 32 points.

### Pourcentages de stress chronique

Trois valeurs publiées se déplacent, toutes dans `jeu_bienne` :

| Point | Avant | Après | Cause |
|---|---|---|---|
| `BIE42-7` | 10,999 % | 11,066 % | `Tmh` recalculée sur la chronique d'eau complète ; quelques journées franchissent le seuil chronique dans un sens ou dans l'autre. |
| `BIE51-0` | 8,540 % | 8,264 % | idem. |
| `BIE56-1` | 9,722 % | 9,783 % | idem. |

**Aucune ne change de catégorie** : les trois points restent dans la classe de
vulnérabilité chronique qu'ils avaient. L'effectif `n_jours_tmh` ne bouge sur
aucun point.

### Trois journées cessent d'être non diagnosticables

`LA PLAINE A RAON-SUR-PLAINE`, les **29, 30 et 31 décembre 2009**. Leur
fenêtre calendaire ne contenait que trois journées *appariées à l'air*, pour
quatre exigées — mais le point porte 330 journées d'eau privées d'air, dont
plusieurs dans cette fenêtre. Une fois le lissage porté sur l'eau complète, la
densité est atteinte : elles reçoivent un `Tmh`, perdent le statut
`non_diagnosticable` et le motif de densité, et entrent dans `07_t_norm.csv`.

Ce n'est pas un verdict publié qui change, c'est une abstention qui cesse.
Elle est consignée ici parce qu'elle modifie ce que l'écran dira du point.

### Ce qui n'a pas changé

`06_coefficients.csv` : **aucun `m` ne bouge**, prédiction P1 vérifiée — `m`
régresse l'eau brute sur l'air brut, `Tmh` n'y entre pas (D42).
`05_anomalies.csv` non plus : `Tmh` n'y figure pas.

---

## Correctif 9 — `Delta_TMm_liss` sur le calendrier de la station d'air (étape 9)

**Ce que le correctif a changé dans la chaîne.** `Delta_TMm_liss` est une
moyenne mobile de l'anomalie d'**air** ; elle était pourtant lissée sur les
seules journées ayant **aussi** une température d'eau. Elle est désormais
lissée sur tout le calendrier de la station. Mesuré : **854 valeurs déplacées
(1,27 %) sur les 32 points**, écart maximal **4,790 °C** sur l'anomalie et
**1,939 °C** répercutés sur `T_norm`.

C'est le premier correctif dont un déplacement de verdict était attendu :
`Delta_TMm_liss` entre directement dans `Tmh_norm = Tmh − m × Delta_TMm_liss`.

### Verdicts de vulnérabilité aiguë

**Aucun.** `n_jours_aigus`, `pts_aigu`, `sgvt` : inchangés sur les 32 points.
Les franchissements du seuil aigu par `Tmax_norm` restent à **101 avant, 101
après**, et **aucun point** ne voit son compte changer.

### Pourcentages de stress chronique

Deux points bougent, et **aucun ne change de catégorie**.

| Point | Avant | Après | Franchissements du seuil |
|---|---|---|---|
| `BIE40-3` | **4,762 %** | **4,992 %** | 62 → **65** journées |
| `BIE6-8` | **0,846 %** | **1,077 %** | 11 → **14** journées |

Les six journées qui franchissent, avec leur marge — seuil chronique
**18,0 °C** pour les deux points :

| Point | Journée | `Tmh_norm` avant | après | Marge avant | Déplacement |
|---|---|---|---|---|---|
| `BIE40-3` | **2015-07-06** | 16,839 °C | **18,582 °C** | 1,161 °C sous le seuil | **+1,743 °C** |
| `BIE40-3` | **2015-07-07** | 16,715 °C | **18,264 °C** | 1,285 °C sous le seuil | **+1,549 °C** |
| `BIE40-3` | **2015-07-10** | 17,740 °C | **18,671 °C** | 0,260 °C sous le seuil | +0,931 °C |
| `BIE6-8` | **2017-08-30** | 17,858 °C | **18,184 °C** | 0,142 °C sous le seuil | +0,326 °C |
| `BIE6-8` | **2017-09-05** | 17,984 °C | **18,249 °C** | 0,016 °C sous le seuil | +0,265 °C |
| `BIE6-8` | **2017-09-08** | 17,979 °C | **18,141 °C** | 0,021 °C sous le seuil | +0,162 °C |

*Cause, en une phrase :* l'anomalie d'air lissée de ces journées était
calculée en sautant les jours où la sonde d'eau ne mesurait pas ; rétablie sur
le calendrier de la station, elle est plus froide, donc `m × Delta_TMm_liss`
retranche moins, donc `Tmh_norm` monte et franchit le seuil.

Aucune journée ne cesse de franchir : le mouvement est **à sens unique** sur
ces deux points.

### Synthèse

**Sur 32 points, 2 voient une conclusion publiée changer** — `BIE40-3` et
`BIE6-8` — et dans le **même sens** : le pourcentage de stress chronique
**augmente**. Aucune catégorie de vulnérabilité, chronique ou aiguë, ne change
sur aucun point.

### Pourquoi le seuil aigu n'a pas bougé, alors qu'on l'attendait

Ce n'est pas une affaire de magnitude, c'est une affaire d'**intersection**.
Le correctif déplace **854 journées sur 67 392** — sur les 98,7 % restantes,
le déplacement est exactement nul. Or seules **54 journées** de tout le corpus
se tiennent à moins de 0,5 °C du seuil aigu. Les deux ensembles se croisent à
peine : la médiane du déplacement au voisinage du seuil aigu est **0,000 °C**.

Le cas limite le dit mieux qu'une moyenne : la journée la plus proche du seuil
aigu de tout le corpus est sur `BIE40-3`, à **0,022 °C** sous 23,0 °C. Elle
n'est pas au nombre des 854 déplacées, et sa marge est identique avant et
après. À l'inverse, `BIE5-9` — le point qui avait basculé au correctif 2 —
voit sa journée la plus proche **s'éloigner** du seuil, de 0,054 à 0,206 °C.

Le seuil chronique, lui, a bougé parce qu'il est franchi par **743 journées**
et qu'**839** se tiennent à moins de 0,5 °C de lui : la cible y est bien plus
large.

---

## Correctif 1 — le détecteur de mise hors d'eau, relatif, à deux marches (étape 10)

**Ce que le correctif a changé dans la chaîne.** C'est le seul correctif du
chantier qui **substitue** un comportement au lieu d'en révéler un. Le
détecteur absolu — `T_eau_max − T_air > 10 °C`, grille annuelle à 5 jours — est
remplacé par deux marches relativisées à l'habitude du point au même mois. Les
journées écartées par le contrôle qualité passent de **91 à 138** sur le
corpus ; le détecteur en marque **69** là où le régime en service en marquait
**22**.

### Synthèse — ce qui intéresse le maître d'ouvrage

| | |
|---|---|
| points dont une valeur publiée bouge | **18 sur 32** |
| points dont une **CATÉGORIE** change | **2 sur 32** |
| SGVT qui bougent | **2**, tous deux **à la baisse** |
| sens du mouvement | la vulnérabilité **diminue**, sauf sur `BIE40-3` |

**Le sens est celui qu'on attendait d'un détecteur d'exondation qui
fonctionne** : il retire des journées où la sonde mesurait de l'air, donc des
journées artificiellement chaudes. Les compteurs de vulnérabilité baissent
parce qu'ils comptaient des artefacts.

### Les deux points qui changent de catégorie

#### `LA PLAINE A RAON-SUR-PLAINE` — trois catégories sur trois

| Indicateur | Avant | Après | Catégorie avant | Catégorie après |
|---|---|---|---|---|
| `n_jours_aigus` | **10 j** | **2 j** | Vulnérabilité aiguë **sévère** | Vulnérabilité aiguë **ponctuelle** |
| `pct_stress_chronique` | **3,146 %** | **0,467 %** | Vulnérabilité chronique **modérée** | **Faible** vulnérabilité chronique |
| **`sgvt`** | **2,333 /10** | **1,500 /10** | **Risque Modéré** | **Risque Faible (Zone Refuge)** |

**Le régime en service ne marquait AUCUNE journée hors d'eau sur ce point. Le
détecteur relatif en marque 16.** Huit d'entre elles étaient comptées comme
journées de vulnérabilité aiguë, seuil **24,0 °C** :

| Journée | Devenue |
|---|---|
| 2011-06-05, 06-06, 06-08, 06-11, 06-12, 06-14 | retirées de la chronique |
| 2012-06-21, 2012-06-23 | retirées de la chronique |

*Cause, en une phrase :* ces journées de juin présentaient un écart eau-air
très au-dessus de l'habitude du point au même mois — jusqu'à **4,9 MAD\*** —
sans jamais franchir le seuil absolu de 10 °C qui les aurait fait voir ; elles
étaient donc comptées comme des journées d'eau chaude alors que la sonde
mesurait de l'air.

*Ce point était publié « Risque Modéré » avec dix journées de vulnérabilité
aiguë sévère. Huit de ces dix journées étaient la sonde hors de l'eau.*

#### `SN 21069646 - La Canner à Vigy 1` — une catégorie

| Indicateur | Avant | Après | Catégorie avant | Catégorie après |
|---|---|---|---|---|
| `n_jours_aigus` | **1 j** | **0 j** | Vulnérabilité aiguë **ponctuelle** | **Absence** de vulnérabilité aiguë |
| `sgvt` | 3,167 /10 | 2,500 /10 | Risque Modéré | Risque Modéré *(inchangée)* |

La journée en cause est le **1er juin 2021**, seuil aigu **30,0 °C**, retirée
par le détecteur. *Cause :* même mécanisme, sur une seule journée.

### Les autres mouvements, sans changement de catégorie

`BIE37-9` : `n_jours_aigus` 6 → 5. **`BIE40-3` : `n_jours_aigus` 29 → 33** —
le seul point où la vulnérabilité **augmente**, le détecteur y marquant des
journées que le régime en service laissait passer, ce qui refroidit `m` et
relève les températures normalisées des autres journées. Onze
`pct_stress_chronique` bougent sans franchir de catégorie ; dix-huit points
voient `n_jours_tmh` ou `n_jours_tmax` changer d'effectif.

### Section D59 — les cinq journées que le détecteur ne marque plus

Conséquence **assumée** du passage au relatif : cinq journées que le régime en
service écartait ne sont plus marquées. Toutes sur `BIE40-3`, toutes en
juillet.

| Journée | `T_eau_max − T_air` | `E_moy_rel` | `R_ampl_rel` | `E_max_rel` |
|---|---|---|---|---|
| 2015-07-09 | 10,57 °C | 2,192 | 3,837 | 1,961 |
| 2015-07-28 | 11,74 °C | 2,499 | 8,512 | 2,773 |
| 2015-07-30 | 13,10 °C | 2,855 | 4,425 | 2,540 |
| 2023-07-20 | 10,01 °C | 2,045 | 2,988 | 1,697 |
| 2023-07-22 | 10,91 °C | 2,280 | 3,314 | 1,771 |

**Pourquoi c'est assumé.** Ces journées franchissaient le seuil absolu de
10 °C, mais leur écart eau-air, rapporté à ce que ce point fait
habituellement en juillet, reste **entre 2,0 et 2,9 écarts-types robustes** —
sous le seuil de 3,0. Elles ressemblent aux autres journées chaudes de juillet
de `BIE40-3`. Le seuil absolu les voyait parce qu'il ignore l'habitude du
point ; c'est précisément ce qu'on lui reproche.

*Une sixième journée, le 8 juillet 2015, était dans le même cas : la marche 2
la rattrape, ses deux membres — forme et niveau — dépassant tous deux le
seuil. C'est la seule fois du corpus où la conjonction ajoute ce que le socle
laisse.*

*`BIE40-3` est le point que le `MANIFESTE.md` du projet clos place sous
réserve d'implantation. Le détecteur y marque 33 journées contre 13 pour le
régime en service : il ne le manque pas, il le voit autrement.*

---

## Correctif 6 — la règle de validité du coefficient de couplage (étape 11)

**Ce que le correctif a changé dans la chaîne.** Le coefficient de couplage
air-eau était retenu quel qu'il soit. Il doit désormais satisfaire deux
conditions : son IC à 95 %, avec écarts-types robustes à l'autocorrélation,
doit **exclure zéro**, et la pente doit être dans `[0 ; 1,2]`. Un rejet met le
coefficient à **zéro**, donc `T_norm = T`.

### Synthèse

| | |
|---|---|
| estimations examinées | **61** (28 estivales aboutissant, 33 saisonnières) |
| **rejets** | **2** |
| points dont un verdict publié change | **0** |
| points dont une catégorie change | **0** |

**Aucun verdict ne bouge, et c'est explicable point par point.**

### `BLE3-0` — le point qui normalisait à l'envers

| | Avant | Après |
|---|---|---|
| `m_estival` retenu | **−0,010** | **0,0** |
| pente estimée | −0,010 | −0,010 *(publiée à part)* |
| `t` de Newey-West | — | **−0,447** |
| statut | *(aucun)* | **REJETÉ** |
| critère | — | l'IC à 95 % contient zéro **et** la pente sort de `[0 ; 1,2]` |

**Ce qu'il publiait.** Avec `m = −0,010`, la normalisation calculait
`Tmh_norm = Tmh − (−0,010) × Delta_TMm_liss`, c'est-à-dire qu'elle
**ajoutait** l'anomalie d'air au lieu de la retrancher. Une année plus chaude
que la normale rendait la température « normalisée » **plus chaude** que la
température brute. La correction climatique fonctionnait dans le mauvais sens.

**Ce qu'il publiera.** `m = 0`, donc `T_norm = T` : les températures publiées
sont les températures brutes, et l'écran déclare que le couplage air-eau n'a
pas pu être établi sur cette chronique.

**Ce qui change dans ce qu'on peut en dire.** L'écart de valeur est
négligeable — `Tmh_norm` bouge de **0,016 °C en médiane, 0,066 °C au
maximum**, et **aucun indicateur de ce point ne change** : il affichait déjà
0 journée aiguë, 0 % de stress chronique et un SGVT de 0.

Ce qui change n'est pas le chiffre, c'est **son statut**. Avant, le point
publiait une température normalisée, avec l'autorité que ce mot porte : une
température débarrassée de l'effet du climat de l'année, donc comparable à
celle d'un autre point et d'une autre année. Cette autorité reposait sur un
coefficient dont le signe était faux et dont l'intervalle de confiance
contenait zéro — autrement dit sur **rien**.

Après, le point publie des températures brutes en le disant. Les
pourcentages qu'il affiche décrivent l'année observée, avec la météo qu'elle a
eue, et ne sont comparables ni à un autre point ni à une autre année. **Le
chiffre était déjà à peu près juste ; c'est ce qu'on avait le droit d'en
conclure qui était faux.**

### `La Moselle à Hielle` [truite fario] — le couplage saisonnier

| | Avant | Après |
|---|---|---|
| `m_saisonnier` retenu | **replié sur `m_estival`** (R² = 0,062 < 0,30) | **0,0** |
| pente estimée | 0,170 | 0,170 *(publiée à part)* |
| `t` de Newey-West | — | **1,528** |
| statut | *(repli silencieux)* | **REJETÉ** |

*Cause :* la pente n'est pas distinguable de zéro sur la fenêtre de
reproduction de la truite fario. Auparavant, le garde-fou sur le R² faisait
**se replier sur le coefficient estival** — c'est-à-dire normaliser la fenêtre
de reproduction hivernale avec le couplage de l'été. Une substitution
silencieuse, présentée comme un garde-fou. Le score de fraie de ce point ne
change pas.

### Ce qui bouge sans être un verdict

`SN 21069646 - La Canner à Vigy 1` [brème] **cesse** de se replier sur le
coefficient estival : sa pente saisonnière, R² = 0,241 mais `t` = 3,96, est
désormais **retenue** à 0,297. La disparition du seuil de R² — que la
spécification ne porte pas — lui rend son propre coefficient. Son
`Tmh_norm_fraie[brème]` change sur 978 valeurs ; son score de fraie, non.

*Un R² faible sur un grand échantillon ne dit pas que le couplage est
indistinct de zéro : il dit que l'air explique peu de la variance. C'est ce
que l'IC mesure, et lui seul.*

---

## D67 — le statut `replie` (étape 12)

**Aucun verdict publié ne change, et c'était la prédiction.** Aucun SGVT,
aucun point de vulnérabilité, aucun pourcentage de fraie, aucun seuil franchi,
aucun débit de référence ne bouge. `_m_saisonnier` retourne `m_estival` à
l'identique ; seul le dictionnaire de diagnostic gagne deux champs.

**Ce qui change n'est donc pas une valeur, c'est un énoncé** — et l'étape 11
a établi qu'un journal des verdicts qui ne relèverait que les valeurs
déplacées manquerait exactement ce cas.

| | Avant | Après |
|---|---|---|
| `validite_statut` des coefficients repliés | *(vide)* | **`replie`** |
| `validite_critere_rejetant` | *(vide)* | « effectif insuffisant sur la fenetre (n=… < 20) — repli sur m_estival » |
| coefficient publié | `m_estival` | `m_estival` — **inchangé** |

**Les deux lignes concernées**, les seules du corpus :

| Point | Espèce | `n` sur la fenêtre | Coefficient publié |
|---|---|---|---|
| `BLE3-0` | ombre commun | **7** | `m_estival` = 0,000 *(lui-même rejeté, correctif 6)* |
| `GRO9-1` | ombre commun | **14** | `m_estival` = 0,240 |

**Ce qu'un statut vide laissait croire.** La colonne `validite_statut` porte
`valide` ou `REJETE` pour tous les coefficients que la règle du correctif 6 a
jugés. Elle était vide pour ceux-ci — et un lecteur qui voit une colonne de
statut vide conclut « rien à signaler ». Or il y a quelque chose à signaler :
**le coefficient publié pour la fenêtre de reproduction de l'ombre commun
n'est pas celui de cette fenêtre, c'est celui de l'été.** C'est exactement la
substitution silencieuse que le correctif 6 a retirée dans l'autre branche —
celle du R² — et qui subsiste, légitimement, dans celle-ci : sept jours ne
permettent pas d'estimer une incertitude, donc pas d'appliquer la règle de
validité.

**Le cas de `BLE3-0` mérite d'être lu deux fois.** Son coefficient saisonnier
se replie sur son coefficient estival, lequel a été **rejeté** par le
correctif 6 et vaut donc zéro. Le point publiait ainsi un coefficient
saisonnier de zéro sans qu'aucune colonne ne dise pourquoi : ni « rejeté »
— il ne l'a pas été —, ni « replié » — la colonne était vide. Deux mécanismes
différents produisaient le même zéro muet. Ils se distinguent désormais.

*Le repli lui-même n'est pas remis en cause : D67 demande qu'il se déclare,
pas qu'il disparaisse.*

---

## Étape 13 — cinq poses, aucun verdict

**Aucune conclusion publiée ne change.** Sur les cinq poses de l'étape, quatre
laissent les 66 artefacts figés au bit près, et la cinquième — le correctif 10 —
ajoute une colonne de compte dont la valeur est **zéro sur les 289 lignes** du
corpus. Aucun SGVT, aucun point de vulnérabilité, aucun pourcentage de fraie,
aucun seuil franchi, aucun débit de référence ne bouge.

**Ce qui change malgré tout, et qui a sa place ici.** L'étape 11 a établi qu'un
journal des verdicts qui ne relèverait que les valeurs déplacées manquerait les
cas où c'est le STATUT d'un chiffre qui bouge. L'étape 13 en offre une variante :
ce ne sont pas les chiffres qui changent, c'est **ce que les livrables disent
d'eux**.

### Six libellés publiés changent de mot

Les six appelaient « compensée » une série de la famille **normalisation** —
`Tmh − m × Delta_TMm_liss`, coefficient estimé, anomalie lissée — alors que
« compensée » désigne dans ce code une **autre formule**, `T − Delta_TMm`, sans
coefficient. Un lecteur qui appliquait la définition de l'un à l'autre lisait
les colonnes « comp » du tableau mensuel comme des températures normalisées.
Elles ne le sont pas.

| Où le lecteur le voit | Avant | Après |
|---|---|---|
| `Fig0_Chronique.png`, légende | « Tmh — eau **COMPENSÉE** (année standard) » | « Tmh — eau **NORMALISÉE** (année standard) » |
| `Fig0_Chronique.png`, légende de l'aire | « Écart brut ↔ **compensé** » | « Écart brut ↔ **normalisé** » |
| **Word, §1.4** — légende de figure | « … température de l'eau brute puis **compensée**. » | « … brute puis **normalisée**. » |
| **Classeur fraie**, colonne d'appoint | « **non compensées** » | « **non normalisées** » |
| **Écran**, réglage avancé | « Lissage de l'anomalie d'air pour **la compensation** » · « **La compensation** retranche m × … » | « pour **la normalisation** » · « **La normalisation** retranche m × … » |
| **Écran**, encart fraie | « Températures brutes **non compensées** » | « Températures brutes, **non normalisées** » |

*Le Word §1.4 se contredisait à huit lignes d'écart : sa légende disait
« compensée », son §1.5 définissait « la normalisation climatique […] pondérée
par le coefficient de sensibilité ». Les deux concordent désormais.*

*L'écran se contredisait à trois lignes d'écart : l'encart fraie disait « non
compensées », sa légende « sans normalisation climatique ». Les deux concordent
désormais.*

### Deux phrases fausses restent publiées, et c'est un choix déclaré

`indicateurs.py:85` et `app.py:604` écrivent que la série compensée est
« ramenée aux conditions normales ». **C'est faux** : la ramenée n'est exacte
que si l'eau suit l'air un pour un, et le `m` médian du corpus vaut **0,432** —
la soustraction corrige donc plus du double de ce que la réponse mesurée du
cours d'eau justifie.

Elles portent sur les colonnes compensées du tableau mensuel, objet de
l'alternative en arbitrage (D72), et la commande d'étape demandait de laisser
ce qui en dépend. Elles restent donc à l'écran, fausses, jusqu'à l'arbitrage.
**Un choix de ne pas corriger est un choix, et il se consigne au même titre
qu'une correction.**

---

## Correctif 4 — la convention unique, voie B (étape 14)

**Aucun verdict publié ne change.** Aucun SGVT, aucun point de vulnérabilité,
aucun pourcentage de fraie, aucun seuil franchi, aucun débit de référence.
`08_scores.csv` est figé sur les six jeux, et c'est lui qui le certifie : la
spécification affirmait que la famille compensation est **terminale**, et un
inventaire incomplet aurait fait bouger cet artefact.

**777 valeurs publiées supprimées, zéro verdict déplacé.**

### Ce que trois livrables perdent

| Livrable | Avant | Après |
|---|---|---|
| **Classeur**, feuille `05_Indicateurs` | 11 colonnes | **8 colonnes** |
| **Word** §2.2, la **figure** | 6 courbes et repères | **4** — les deux tirets « Tmax / Tmin compensée » disparaissent |
| **Word** §2.2, le **tableau** | 6 colonnes | **6 colonnes — inchangé** |
| **Écran**, onglet Indicateurs | 11 colonnes | **8** |
| **Export CSV** `indicateurs_thermiques.csv` | 11 champs | **8** |

*Le tableau du Word ne portait aucune colonne compensée : il ne prend que les
six premières. Le Word change par sa **figure**, jamais par son tableau — un
contrôle mené sur le tableau conclurait « rien n'a bougé ».*

### Ce qui disparaît et n'a d'équivalent nulle part

C'est ce qu'un maître d'ouvrage doit pouvoir s'entendre dire.

1. **La couverture de janvier à décembre.** La famille normalisation n'agrège
   rien hors de ses fenêtres — juin-septembre pour la vulnérabilité, les mois
   de phase de l'espèce pour la reproduction. Le tableau mensuel était **le
   seul endroit de l'outil publiant une température corrigée pour janvier ou
   novembre**.
2. **Le minimum corrigé.** `T_min_comp` était la seule série corrigée bâtie sur
   `T_eau_min`. La famille normalisation ne produit **aucun minimum**.
3. **La moyenne mobile de trente jours corrigée.** `Tmm30j comp` n'avait
   d'équivalent nulle part. Son pendant brut, `Tmm30j brut`, subsiste.

### Ce qui ne disparaît pas, quoiqu'on puisse le croire

Ces colonnes ne portaient **pas** une correction climatique estimée. Elles
retranchaient l'anomalie d'air **brute, sans coefficient** — c'est-à-dire ce
qu'on obtiendrait si l'eau suivait l'air un pour un. Le `m` médian du corpus
vaut **0,432** : elles corrigeaient en médiane **plus du double** de ce que la
réponse mesurée du cours d'eau justifie.

Deux textes de l'outil les présentaient pourtant comme « ramenées aux
conditions normales » — `indicateurs.py:85` et `app.py:604`. **Ces deux
phrases, signalées fausses à l'étape 13 et laissées publiées en attendant
l'arbitrage, disparaissent avec ce qu'elles décrivaient** (D84).

*Le journal de l'étape 13 disait qu'un choix de ne pas corriger se consigne au
même titre qu'une correction. Celui-ci se referme ici.*

---

## Correctif 11 — la normale et l'année bissextile (étape 15)

**Aucun verdict ne change.** Aucun SGVT, aucun point de vulnérabilité aiguë,
aucune composante, aucun seuil franchi, aucun débit de référence, **aucune
catégorie ni interprétation**. Vérifié systématiquement sur les six jeux,
colonne par colonne.

**Mais des valeurs publiées bougent, sur 89,65 % des journées du corpus.**

### Ce que le correctif change dans la chaîne

La normale était agrégée par numéro de jour dans l'année, puis relue par
`(jour, mois)` sur le calendrier d'une année **bissextile**. Du 1ᵉʳ mars au
31 décembre, une journée d'une année **commune** recevait donc la normale du
jour **suivant**.

**60 116 journées sur 67 054** recevaient une normale décalée.

| Grandeur | Écart absolu médian | Maximum |
|---|---|---|
| `T_normale` | 0,064 °C | **0,343 °C** |
| `Delta_TMm` | 0,064 °C | **0,343 °C** |
| `Delta_TMm_liss` | 0,066 °C | **0,299 °C** |
| **`T_norm`** | **0,029 °C** | **0,125 °C** |

### Les deux valeurs de score qui bougent

| Point | Indicateur | Avant | Après |
|---|---|---|---|
| `BIE31-4` | `pct_stress_chronique` | **2,172 %** | **2,313 %** |
| `BIE40-3` | `pct_stress_chronique` | **5,050 %** | **5,126 %** |

**Leurs catégories ne changent pas**, ni leur SGVT, ni leur nombre de journées
aiguës. Ce sont les deux seules valeurs de `08_scores.csv` déplacées sur tout
le corpus.

### Les onze pourcentages de fraie

Le journal publie les pourcentages de fraie arrondis à l'unité. Onze lignes se
déplacent d'**un point**, sept sur `jeu_bienne` et une par jeu ailleurs :

| Point / jeu | Avant | Après |
|---|---|---|
| `jeu_02`, truite fario | optimum 80 % / élargie 20 % | optimum **79 %** / élargie **21 %** |
| `jeu_bienne`, ombre commun (7 points) | ex. optimum 40 / élargie 47 / létal 13 | optimum **39** / élargie 47 / létal **14** |

**Aucun `P` de fraie ne change**, donc aucune composante du SGVT.

*L'étape 7 avait établi que des pourcentages publiés qui bougent se consignent
ici, même quand le score ne bouge pas : sept lignes avaient alors bougé et
trois seulement avaient été rapportées. Les onze sont ici.*

### Ce qu'il faut pouvoir dire

Les températures normalisées publiées jusqu'ici étaient calculées, sur près de
neuf journées sur dix, contre la normale du **lendemain**. L'écart est petit —
trois centièmes de degré en médiane sur `T_norm` — et il était **systématique
et signé** : la normale du lendemain est plus haute au printemps et plus basse
en automne, si bien que l'anomalie était sous-estimée d'un côté et surestimée
de l'autre. Aucun verdict n'en dépendait ; la comparabilité entre années, qui
est la raison d'être de la normalisation, en dépendait un peu.

---

## Correctif 12 — la complétude de journée (étape 16)

**Aucun verdict ne change, et aucune valeur publiée non plus.** C'est la
définition de la branche A — marquer sans exclure — et elle est vérifiée :
`04_normales`, `05_anomalies`, `06_coefficients`, `07_t_norm` et `08_scores`
**figés sur les six jeux**. Aucun SGVT, aucun pourcentage, aucune catégorie,
aucun seuil, aucun débit.

**Ce qui entre ici est d'une autre nature : la chronique porte désormais des
signalements qu'elle ne portait pas.**

### 141 journées de la chronique sont signalées incomplètes

| | |
|---|---|
| journées signalées | **141**, sur **29 points** |
| part du corpus | **0,21 %** |
| ce qu'elles ont en commun | leur plus long intervalle sans mesure dépasse **deux fois** celui d'une journée ordinaire de leur sonde |
| leur effectif | médiane **12 mesures sur 24** — elles ne sont **pas** pauvres en mesures, elles les ont **groupées** |
| leur écart aux journées voisines | **0,57 °C** en médiane, contre **0,22 °C** pour les autres — **× 2,6** |

**Elles ne sont pas écartées.** Elles entrent dans tous les calculs, comme
avant. Ce qui change est qu'un lecteur peut désormais savoir que la moyenne de
ces journées-là ne couvre pas le cycle jour-nuit.

*Quatre journées de plus sont désignées sur `BIE35-5__NA`, dont la chaîne
échoue (D7) : elles n'apparaissent dans aucun artefact. 145 journées désignées
sur 32 points, 141 publiées sur les 31 qui aboutissent.*

### Un point entier est déclaré non jugeable

`BLE3-0` — 124 journées — porte le statut **`indeterminable`**. Toutes ses
mesures sont datées à minuit : la colonne d'heure de son fichier n'est pas
reconnue (registre C2 / I13, D88), et l'outil ne sait rien de la répartition de
ses mesures dans la journée.

| Ce que le livrable dira | |
|---|---|
| journées signalées | **`n/a`**, et non `0` |
| motif | *« structure infra-journalière illisible — le critère de complétude ne peut rien voir et s'en abstient »* |

**Une absence de signalement ne vaut pas quitus sur ce point** : elle signifie
que personne n'a pu regarder. C'est ce que D92 exigeait de déclarer plutôt que
de laisser déduire.

### Ce que le commanditaire doit pouvoir dire

1. **La chronique n'a pas changé.** Aucune journée n'a été retirée, aucune
   température n'a bougé, aucun score n'a bougé.
2. **141 journées sur 68 134 portent désormais un signalement** disant que leur
   moyenne journalière repose sur des mesures groupées sur une partie de la
   journée.
3. **Une sonde sur trente-deux ne peut pas être jugée** par ce critère, et
   l'outil le dit au lieu de la déclarer conforme.
4. **Ce que le signalement ne dit pas** : qu'une journée signalée est fausse, ni
   qu'une journée non signalée est complète. Une journée régulièrement espacée
   mais rare n'est pas signalée et reste pauvre.

### Un fait relevé, non corrigé

**141 des 145 journées désignées publient aujourd'hui une amplitude
nycthémérale** — elles passent le critère `n ≥ 3` de `indicateurs.py` et
échouent celui du trou. Une amplitude jour-nuit calculée sur des mesures
groupées sur une demi-journée n'est pas une amplitude nycthémérale.

`indicateurs.py` est en aval de `T_norm`, donc hors du périmètre du mandat.
**Signalé, non corrigé**, et rangé avec D87 et D88.

---

## D48 et D68 — ce que les livrables disent désormais (étape 17)

**Aucun verdict ne change, aucune valeur publiée non plus.** 65 artefacts sur
66 figés ; le soixante-sixième est un journal de console dont un numéro de
ligne a bougé. Aucun SGVT, aucun pourcentage, aucune catégorie, aucun seuil,
aucun débit.

**Ce qui change est ce que les livrables DISENT des chiffres qu'ils portaient
déjà.**

### Le trou qui se ferme

`BLE3-0` publiait un SGVT, un pourcentage de stress chronique et un nombre de
journées de vulnérabilité **typographiquement identiques** à ceux de n'importe
quel autre point — alors que sa relation air-eau a été rejetée et que ses
températures sont **brutes**, non corrigées du climat.

Le Word et le classeur portent désormais, **avant** ces chiffres :

> **Statut de la correction climatique — point d'attention**
> ATTENTION — températures BRUTES. La relation air-eau n'a pas pu être établie
> sur cette chronique : la correction du climat n'est pas appliquée. Les
> pourcentages et les journées de vulnérabilité ci-dessous décrivent l'année
> observée, avec la météo qu'elle a eue. Ce point n'est comparable ni à un
> autre point, ni à lui-même d'une année sur l'autre.

Un point dont la relation est établie porte la phrase inverse, et elle est
affirmative : les valeurs **sont** comparables.

### Ce que chaque livrable gagne

| Livrable | Ce qui apparaît |
|---|---|
| **Écran** | un onglet « Ce qui a été vérifié », en deuxième position, et une ligne de résumé colorée |
| **Word** | un chapitre 1.7 « Ce qui a été vérifié, et ce qui ne l'a pas été », **entre** les données et les résultats ; l'encadré de statut avant les chiffres de vulnérabilité |
| **Classeur** | une feuille `07_Etats_declares` ; le même encadré en tête de `02_Thermie_SGVT` |

### Ce qu'un lecteur voit désormais qu'il ne voyait pas

Sur trois points du corpus, pris pour leur contraste :

| Point | Ce que le livrable annonce maintenant |
|---|---|
| `Le ruisseau de Gorze à Gorze` | 3 réserves de lecture, 4 contrôles sans rien à signaler. **Aucun point d'attention.** |
| `BLE3-0` | **2 points d'attention** — la relation air-eau n'a pas pu être établie, et la complétude des journées n'est pas vérifiable faute d'horodatages |
| `La Moselle à Hielle` | **1 point d'attention** — l'année 2012 est entièrement absente du calcul |

**L'année 2012 de `La Moselle à Hielle` était absente depuis toujours** : 102
journées sur 303, tout son été, retirées faute de température d'air. Le chiffre
était mesuré depuis l'étape 7 et publié nulle part. Il l'est.

### Ce qui reste dit nulle part

La feuille de synthèse `06_SYNTHESE` — la seule destinée à **comparer des
stations entre elles**, donc celle où l'absence de statut est la plus
dangereuse — **ne porte pas le statut**. Son en-tête est invariant par
construction, pour que les lignes de plusieurs stations s'empilent telles
quelles ; y ajouter une colonne casserait l'empilement avec des stations
produites par une version antérieure.

**Deux lignes empilées, l'une normalisée et l'autre non, s'y lisent donc encore
comme comparables.** C'est consigné plutôt que corrigé, et remonté comme
alternative fermée.

---

# Correctif 13 — la fenêtre du détecteur et le test de signe (étape 20)

**Aucun verdict n'est déplacé.** C'est le résultat, et il mérite d'être dit en
tête : un correctif qui retire 88 journées de l'analyse et en rend 6 ne change
**aucune catégorie publiée**, sur aucun des 31 points.

## Ce qui a changé dans le détecteur

Deux choses, indissociables :

1. **La fenêtre d'examen** passe de juin–septembre à l'année entière. Motif :
   95 des 134 journées d'artefact non détectées tombaient hors de ces quatre
   mois, et le mois le plus touché était mai — celui où l'on pose les sondes.
2. **La marche 1 gagne un second membre** : la température maximale de l'eau
   doit être au-dessus de la médiane de son propre mois. L'écart eau–air ne dit
   pas lequel des deux termes a bougé ; ce membre le dit.

Sans le second membre, l'extension seule marquait 73 journées de saison froide
sans qu'aucune soit corroborée — une vague de froid produit le même écart
eau–air qu'une sonde émergée.

## Ce que cela déplace, exactement

| | |
|---|---:|
| journées marquées | 69 → **151** |
| sortent de l'analyse | 88 |
| rentrent dans l'analyse | 6 |
| **catégories déplacées** | **0** |
| valeurs publiées déplacées | 17 sur 652 |

Les 17 valeurs sont toutes des effectifs :

| indicateur | points | écart maximal |
|---|---:|---:|
| `n_jours_tmh` | 7 | 2 journées |
| `n_jours_tmax` | 6 | 1 journée |
| `pct_stress_chronique` | 4 | 0,467 point de % |

## Les six journées qui rentrent

Toutes le **1ᵉʳ juin 2011**, sur six points de la Bienne : ABI3-6, BIE10-8,
BIE21-7, BIE27-9, BIE56-1, LGV11-8.

Ce jour-là, l'air de la station LA_PESSE est descendu à **4,6 °C**, sous le
5ᵉ centile de sa propre fenêtre saisonnière. Sept sondes ont été marquées « hors
d'eau » alors que leur eau était **à ou sous sa médiane de juin**. Sept sondes
d'un même bassin ne sortent pas de l'eau le même jour : c'était l'air qui était
tombé, pas l'eau qui était montée.

Elles rentrent donc dans l'analyse, et l'effet sur ce qu'elles publient est
**négligeable** : `m_estival` bouge au maximum de 0,002, le p95 de la
température normalisée de 0,004 °C, et aucune catégorie ne change.

## Le coefficient de fraie — première fois du chantier

C'est le premier correctif à atteindre `m_saisonnier`, le coefficient qui sert à
la reproduction. **Huit points sur 31** bougent, dont deux substantiellement :

| point | espèce | `m_saisonnier` | écart |
|---|---|---|---:|
| **SN 21069646 – La Canner à Vigy 1** | brème | 0,2965 → **0,4119** | **+39 %** |
| **Le ruisseau de la Flotte à Château-Voue** | barbeau | 0,5364 → **0,5751** | **+7 %** |
| six autres points | ombre commun | — | ≤ 0,002 |

Sur La Canner, ce sont **vingt journées du bloc de pose de mai 2021** qui
sortent : la sonde y lisait 19 à 23 °C hors de l'eau, pendant la fenêtre de
reproduction de la brème.

**`P_fraie` ne bouge sur aucun point.**

## Trois points nommés, trois raisons distinctes

Les blocs de pose de mai 2021 de Gorze, La Canner et la Flotte **sont
rattrapés** — c'était l'objet du correctif. Rien ne bouge pourtant dans ce
qu'ils publient, et il faut trois explications séparées :

- **Le ruisseau de Gorze à Gorze** — espèce repère : truite fario, fraie
  d'octobre à mars. Son bloc de mai, le plus massif du corpus, **ne recoupe pas
  sa fenêtre de reproduction**. Le correctif le retire sans que l'indicateur
  s'en aperçoive.
- **SN 21069646 – La Canner à Vigy 1** — son coefficient de fraie bouge de
  39 %, mais son `P_fraie` est **déjà à son maximum, 3/3**, et ne peut pas
  monter. *Qu'un indicateur ne bouge pas parce qu'il est saturé n'est pas la
  même chose que de ne pas être affecté.* Sur un point moins dégradé, les mêmes
  vingt journées auraient pesé.
- **Le ruisseau de la Flotte à Château-Voue** — son coefficient bouge de 7 %,
  insuffisant pour franchir une borne de classe.

## Une fuite déclarée, et son coût

Quatorze journées de saison froide survivent au test de signe, dont onze de
signature « coup de froid marginal » — l'eau à un ou deux dixièmes au-dessus de
sa médiane pendant que l'air s'effondre à −15 °C. Elles sont retirées de
l'analyse à tort.

**Une seule tombe dans une fenêtre de reproduction** : La Moselle à Hielle, le
11 novembre 2022, truite fario. Et celle-là n'est pas un coup de froid : l'eau y
est à 21,86 °C, **4,63 °C au-dessus de sa médiane de novembre**, l'air à 5,4 °C.
Une vraie anomalie, retenue à juste titre.

**Le coût de la fuite dans les indicateurs publiés est donc nul.** Il est
déclaré parce qu'il pourrait ne pas l'être sur un autre corpus.

## Ce qui reste dit nulle part

**Deux journées de vulnérabilité aiguë de LA PLAINE A RAON-SUR-PLAINE — les 3 et
4 juin 2011 — sont toujours publiées, et sont selon toute vraisemblance la même
sonde hors de l'eau que les huit déjà retirées.** Le détecteur ne les voit pas
parce que l'air était chaud ces jours-là (19 à 20 °C contre 10 à 15 °C le reste
du bloc), ce qui referme l'écart eau–air sous le seuil.

Le correctif 13 ne les visait pas et ne les a pas touchées. Il les laisse
désormais **seules** : après la pose, ce sont les trois seules journées que le
témoin indépendant signale encore sur ce point, contre seize avant.

**L'écran ne nomme pas encore le second membre du détecteur.** Son état est
produit et publié dans les artefacts, mais `redaction.py` n'a pas été touché :
un lecteur voit que le détecteur a tourné, pas que sa marche 1 comporte
désormais deux membres. C'est un écart à la règle qui veut que tout contrôle
publie son état, et il est consigné plutôt que corrigé sans mandat.
