# THERMIE_BIO V4.6 — Rapport d'étape 4

*Arrêter la spécification. Dernière étape sans modification de code applicatif.*

**Livrable principal : [`docs/SPEC_detecteur_et_validite.md`](SPEC_detecteur_et_validite.md).**

---

## §0 — Carnet de bord

### La correction de cadre change le sens du résultat, et il faut le dire net

Le contrôle amont a raison : opposer les critères relatifs au détecteur à
4 °C était le mauvais cadre. Rejoué contre le régime **en service**, tout
s'inverse.

| | jours marqués | rapport au régime en service |
|---|---|---|
| **régime en service** (10 °C, sans exclusion) | **22** | ×1 |
| A poolé q = 0,90 | 2 382 | **×108** |
| B dispersion k = 3 | 68 | **×3,1** |
| B dispersion k = 4 | 10 | ×0,45 |

La phrase de l'étape 3 — « le critère B est beaucoup plus sévère » — était
vraie contre 3 408 jours et **fausse comme jugement sur le détecteur à
remplacer**. Contre 22 jours, presque tout marque davantage. La question
ouverte n° 2 de l'étape 3 se dissout, exactement comme le contrôle l'annonçait.

Une précision s'ajoute, que je n'avais pas vue : les 3 408 jours de l'étape 3
n'étaient **pas** le détecteur CLI non plus. C'était le critère brut
`ecart > 4 °C` sur la fenêtre estivale, **sans la grille annuelle à 5 jours et
sans l'exclusion de saison**. Le vrai détecteur CLI marque **17 025** jours sur
ce corpus. J'avais comparé à un troisième objet, qui n'était ni l'un ni
l'autre.

### La conjonction demandée par D26 se comporte à l'envers de son intention

Mesurée, la conjonction `E_moy ET E_max` **sélectionne les journées de faible
amplitude d'air** — exactement le profil d'artefact que `thermie_points`
identifie. À `k = 2`, les jours qu'elle **retire** ont une amplitude d'air
médiane de 10,4 °C et ceux qu'elle **garde**, de 5,0 °C, avec 60 % sous 6 °C.
Elle retire les régimes installés et garde le bruit isolé.

La raison est mécanique et se démontre sans données : `E_moy` et `E_max`
diffèrent exactement de `TX − TM`. Ils ne franchissent leur seuil ensemble que
lorsque l'air varie peu. **La conjonction sélectionne pour `TX − TN` petit,
par construction.**

J'ai donc mesuré la conjonction de `thermie_points`, qui n'est pas celle-là :
elle oppose une **forme** (`R_ampl`) à un **niveau** (`E_max`), deux signatures
différentes. Elle donne le profil inverse et il est excellent. §2.

### Ce que j'ai corrigé dans mon propre code

| Défaut | Effet |
|---|---|
| Le premier script de conjonction ne chargeait pas `T_eau_min` | `socle()` ne le rapportait pas ; `R_ampl` était incalculable. Rechargé depuis `charger_eau` |
| Le garde-fou d'amplitude d'air était sur le point d'être repris à 6 °C | C'est une valeur du bassin de la Bienne. Remplacée par une **dérivation du jeu traité** — premier décile de l'amplitude d'air. Elle retombe entre 5,00 et 6,62 °C selon le jeu, ce qui corrobore le 6 °C sans l'importer |
| La dérivation de l'effectif minimal tirait d'abord des sous-échantillons **aléatoires** | Cela détruit l'autocorrélation que Newey-West est précisément là pour corriger, et surestime la significativité. Remplacé par des **fenêtres contiguës** |

### Ce que je n'ai pas fait

Je n'ai pas conservé la conjonction `E_moy ET E_max` en la présentant comme
défendable. Elle est mesurée, le résultat est donné, et la spécification retient
l'autre. D26 disait « conjonction dès que TN et TX sont là » — l'esprit est
tenu ; c'est le second membre qui change.

Je n'ai touché ni `app/`, ni `ref/`, ni la référence.

---

## §1 — Comparaison au régime en service (Tâche A)

### A1 — Le détecteur en service, reproduit à la lettre

`qc.py:60-79`, avec les paramètres de l'application : un jour est marqué s'il
tombe en juin-septembre, si `T_eau_max − TM > 10 °C`, si `TM` est renseignée,
**et si son année compte au moins 5 jours suspects**. Cette dernière condition,
une grille par *année*, est facile à oublier.

Sur le corpus : **22 jours, 2 points** — `BIE40-3` (13 jours) et `BIE6-8` (9).

### A1/A2 — La table

| Réglage | jours | rapport au service | ordre de grandeur | communs | perdus | gagnés | points | pts perdus |
|---|---|---|---|---|---|---|---|---|
| **RÉGIME EN SERVICE** | **22** | ×1,00 | — | 22 | 0 | 0 | **2** | 0 |
| A poolé q = 0,90 | 2 382 | ×108 | **deux ordres de grandeur de plus** | 22 | **0** | 2 360 | 31 | 0 |
| A poolé q = 0,95 | 1 191 | ×54 | un ordre de grandeur de plus | 22 | **0** | 1 169 | 28 | 0 |
| A poolé q = 0,99 | 239 | ×11 | un ordre de grandeur de plus | 22 | **0** | 217 | 25 | 0 |
| A poolé q = 0,995 | 120 | ×5,5 | plus | 22 | **0** | 98 | 16 | 0 |
| B dispersion k = 2 | 470 | ×21 | un ordre de grandeur de plus | 22 | **0** | 448 | 31 | 0 |
| B dispersion k = 3 | 68 | ×3,1 | plus | 16 | 6 | 52 | 18 | 0 |
| B dispersion k = 4 | 10 | ×0,45 | **MOINS** | 1 | 21 | 9 | 4 | 1 |
| B dispersion k = 5 | 3 | ×0,14 | **MOINS** | 0 | 22 | 3 | 2 | 2 |
| B dispersion k = 6 | 0 | ×0,00 | **MOINS** | 0 | 22 | 0 | 0 | 2 |
| *régime CLI (documentaire)* | *17 025* | *×774* | *deux ordres de grandeur* | 22 | 0 | 17 003 | 24 | 0 |

**Deux propriétés méritent d'être relevées.**

Les six réglages qui marquent davantage — A à tous ses quantiles, B à k = 2 —
sont des **sur-ensembles stricts** du détecteur en service : `jours perdus = 0`.
Ils ne perdent **rien** de ce que l'application écarte aujourd'hui. À partir de
`k = 3`, B cesse d'être un sur-ensemble : il perd 6 des 22 jours.

**Aucun réglage candidat ne casse un point.** Les 31 points exploitables le
restent, sous chacun des neuf réglages. Le régime CLI, lui, en tue 14.

### A3 — L'impact sur `m` et sur `T_norm`

Chaîne rejouée jusqu'au bout pour chaque réglage : `core.fusionner`, puis la
pente sur juin-septembre, puis `Tmh_norm = Tmh − m × Delta_TMm_liss`. Seul le
détecteur de mise hors d'eau change ; les trois autres détecteurs restent
identiques.

| Réglage | \|Δ`m`\| médian | \|Δ`m`\| max | \|Δ`Tmh_norm` méd.\| médian | max | \|Δ`Tmh_norm` p95\| max | Δ retenues médian |
|---|---|---|---|---|---|---|
| A q = 0,90 | 0,0301 | 0,0953 | 0,1400 | 0,7645 | 3,9040 | −47 j |
| A q = 0,95 | 0,0178 | 0,0707 | 0,0730 | 0,5052 | 3,6413 | −25 j |
| A q = 0,99 | 0,0034 | 0,0482 | 0,0116 | 0,1178 | 3,0653 | −2 j |
| A q = 0,995 | 0,0000 | 0,0428 | 0,0011 | 0,0514 | 2,4119 | −1 j |
| **B k = 2** | 0,0082 | 0,0471 | 0,0349 | 0,2118 | 2,9146 | −11 j |
| **B k = 3** | **0,0010** | **0,0420** | **0,0030** | **0,0453** | **1,0501** | **−1 j** |
| B k = 4 | 0,0000 | 0,0228 | 0,0000 | 0,0205 | 0,9468 | 0 j |
| *régime CLI* | *0,0077* | *0,3304* | *0,1001* | *3,6129* | *5,4168* | *−118 j* |

`B k = 3` est le réglage qui marque plus que le service tout en déplaçant le
moins : \|Δ`m`\| médian de **0,0010**, et **deux points seulement** bougent de
façon lisible. Le détail nominatif est au §5 de la spécification.

---

## §2 — La conjonction (Tâche B)

### B1 — La conjonction demandée par D26

`E_moy_rel > k` **ET** `E_max_rel > k`, chacun relativisé par sa dispersion.

| k | socle seul | maximum seul | **conjonction** | retirés | part retirée | pts socle | pts conj. |
|---|---|---|---|---|---|---|---|
| 2 | 470 | 652 | 293 | 177 | 37,7 % | 31 | 29 |
| 3 | 68 | 42 | 18 | 50 | 73,5 % | 18 | 13 |
| 4 | 10 | 3 | 1 | 9 | 90,0 % | 4 | 1 |
| 5 | 3 | 0 | 0 | 3 | 100 % | 2 | 0 |

### B2 — Ce qu'elle retire, et ce que cela dit

Aucune vérité terrain n'existe sur ce corpus. Sont donc rapportés les seuls
indices observables : l'amplitude d'air du jour — le seul indice d'artefact
météorologique dont on dispose —, la longueur de l'épisode, l'isolement, et la
synchronisation entre points.

| k | groupe | n | ampl. air médiane | sous 6 °C | épisode médian | isolés | sync. max |
|---|---|---|---|---|---|---|---|
| 2 | **retirés** | 177 | **10,40 °C** | 6,8 % | 1,0 j | 59,3 % | 13 |
| 2 | **gardés** | 293 | **5,00 °C** | **59,7 %** | 1,0 j | 56,3 % | 13 |
| 3 | **retirés** | 50 | **10,30 °C** | 14,0 % | **3,0 j** | 36,0 % | 7 |
| 3 | **gardés** | 18 | **5,85 °C** | **50,0 %** | 1,0 j | 61,1 % | 7 |

**La conjonction retire les journées à forte amplitude d'air et garde celles à
faible amplitude.** À `k = 3`, elle retire des épisodes de 3 jours et garde des
jours isolés à 61 %. C'est l'inverse de ce qu'un garde-fou doit faire :
`thermie_points` établit qu'une faible amplitude d'air fabrique des faux
positifs, et que 13 points marqués le même jour sont la signature d'un
phénomène météorologique, pas de 13 exondations.

Les jours retirés ne ressemblent donc **pas** davantage à du bruit que ceux
gardés — c'est le contraire.

### B2 bis — La conjonction de `thermie_points`, qui n'est pas celle-là

`thermie_points` ne conjoint pas deux niveaux, mais une **forme** et un
**niveau** : `R_ampl` (rapport des amplitudes) et `E_max_rel`. Mesurée sur le
même socle, avec un garde-fou d'amplitude d'air **dérivé du jeu traité**
(premier décile : 5,00 à 6,62 °C selon le jeu) :

| k = 3 | jours | points | ampl. air méd. | `R_ampl` méd. | épisode méd. | sync. max | dates à ≥ 5 pts |
|---|---|---|---|---|---|---|---|
| socle seul | 40 | 16 | 10,90 °C | 0,47 | 2,0 j | 6 | 1 |
| `E_moy` ET `E_max` (D26) | 8 | 7 | 6,80 °C | 0,53 | 1,0 j | 5 | 1 |
| **`R_ampl` ET `E_max`** | **4** | **2** | **12,05 °C** | **1,03** | **4,0 j** | **1** | **0** |

Tous les indicateurs basculent du bon côté : forte amplitude d'air, `R_ampl`
médian à **1,03** — l'eau varie autant que l'air —, épisodes de 4 jours, et
**aucun jour marqué sur deux points à la fois**.

Les quatre jours, en clair :

| Point | Date | `T_eau_max` | `TX` | **eau − air max** | ampl. eau | ampl. air | `R_ampl` |
|---|---|---|---|---|---|---|---|
| `LA PLAINE A RAON` | 11/06/2011 | 26,18 | 19,3 | **+6,88** | 6,79 | 9,3 | 0,73 |
| `LA PLAINE A RAON` | 12/06/2011 | 27,43 | 21,3 | **+6,13** | 7,76 | 15,7 | 0,49 |
| `BIE40-3` | 08/07/2015 | 25,42 | 16,4 | **+9,02** | 8,61 | 6,5 | **1,32** |
| `BIE40-3` | 07/09/2015 | 25,90 | 15,8 | **+10,10** | 20,87 | 14,8 | **1,41** |

Le maximum de l'eau dépasse celui de l'air de 6 à 10 °C. Et `BIE40-3` est
**exactement** le point que le `MANIFESTE.md` du projet clos place sous
« réserve d'implantation », avec des épisodes relevés **en 2015**. La règle le
retrouve sans qu'aucun seuil de ce projet n'ait été importé.

### B3 — Ce que la machinerie de `thermie_points` exige, et ce qui est transposable

| Élément | Entrées exigées au-delà de `TN` et `TX` | Transposable sans infra-journalier ? |
|---|---|---|
| `R_ampl`, `E_max`, `E_min` | `T_eau_min` et `T_eau_max` journaliers | **oui** — V4.5 les calcule déjà (`io_data.py:102-103`). Mais leur **sens** exige de l'infra-journalier : un extrême sur une mesure n'est pas un extrême |
| relativisation par (point, mois) | l'historique du point | **oui** |
| conjonction `appliquer_couple` | rien | **oui** |
| `marquer_episodes` — déclenchement, marge calendaire | une série booléenne datée | **oui** |
| hystérésis (prolongation par critère relâché) | un second jeu de seuils | **oui** |
| fusion des épisodes séparés de moins de `FUSION_JOURS` | rien | **oui** |
| niveau de jour « complet » (`socle.py`) | **rééchantillonnage horaire**, puis aucun trou > 3 h et ≥ 20 h renseignées | **NON** — exige de l'infra-journalier dense, et un rééchantillonnage horaire que V4.5 ne fait pas : il agrège les mesures natives (`io_data.py:100-104`) |
| garde-fou `plancher_r_ampl`, `garde_fou` | **des négatifs terrain** — jours dont on sait par le suivi de terrain que la sonde était immergée | **NON** — donnée d'étude absente du harnais, et qui doit le rester |
| `diagnostiquer_artefact`, volet synchronisation | **un réseau de points partageant une station d'air** | **NON dans le modèle d'usage de l'application**, qui traite une sonde à la fois |
| `GROUPES_RELECTURE`, `POINTS_RESERVE` | un **jugement humain** attaché à des codes de points | **NON**, et interdit par la contrainte 5 |

**Trois dépendances bloquantes**, donc : les négatifs terrain, le réseau
multi-points, et le jugement de relecture. Aucune n'entre dans la
spécification. Le rééchantillonnage horaire est une quatrième dépendance, de
nature différente : elle serait implémentable, mais changerait les agrégats
journaliers de V4.5 et sortirait du périmètre.

---

## §3 — La règle de validité (Tâche C)

### C1 — Le calcul amont est confirmé, au chiffre près

| t = m / SE | Point | m | R² | n | IC95 exclut zéro |
|---|---|---|---|---|---|
| **−0,447** | `BLE3-0` | −0,0100 | 0,0017 | 107 | **non** |
| 3,585 | `SN 21069646 - La Canner à Vigy` | 0,2295 | 0,2112 | 347 | oui |
| 8,676 | `LA PLAINE A RAON-SUR-PLAINE` | 0,2928 | 0,2059 | 445 | oui |
| … | | | | | |
| 30,63 | `BIE0-3` | 0,3811 | 0,6326 | 1621 | oui |

**Sur `m_estival`, l'IC95 contient zéro pour un seul point réel : `BLE3-0`.**
Le suivant est huit fois plus loin. Les t des significatives vont de 3,58 à
30,63, de médiane 17,71. La séparation est totale.

*(`BIE35-5__NA` apparaît aussi, mais il n'a `n = 0` : il n'y a pas de pente du
tout, ce n'est pas un IC contenant zéro.)*

**Étendu à `m_saisonnier`, par espèce (D28)** — 33 estimations, dont deux pour
`jeu_04` :

| Point | Espèce | m | t | R² | n | IC95 exclut zéro |
|---|---|---|---|---|---|---|
| `BLE3-0` | ombre commun | 0,0149 | 0,219 | 0,0070 | 7 | **non** |
| `La Moselle à Hielle` | truite fario | 0,1703 | 1,528 | 0,0621 | 67 | **non** |

Les t des significatives vont de 3,96 à 20,43. Les deux non significatives
sont **déjà** repliées sur `m_estival` par V4.5 (`core.py:258`, `R² < 0,30`) :
la règle de significativité retrouve les mêmes cas par une autre route.

### C2 — L'effectif minimal, dérivé du corpus

Pentes ré-estimées sur des **fenêtres contiguës** de longueur croissante — la
contiguïté préserve l'autocorrélation ; un tirage aléatoire la détruirait et
surestimerait la significativité.

| `n'` | fenêtres testées | part encore significative |
|---|---|---|
| 10 | 4 695 | 73,5 % |
| 20 | 4 635 | 85,1 % |
| 30 | 4 575 | 91,0 % |
| 50 | 4 455 | 94,5 % |
| **60** | **4 395** | **96,0 %** ← premier à atteindre 95 % |
| 100 | 4 155 | 99,0 % |
| 200 | 3 619 | 99,1 % |

**`n_min = 60`.** La dérivation ne fait entrer aucun nombre nouveau : elle
réutilise le niveau de 95 % déjà présent dans la condition de significativité.
La valeur doit être **recalculée sur chaque jeu traité**.

### C2 — Les trois critères croisés

| Coefficient | Critère | écartées | part | lesquelles |
|---|---|---|---|---|
| `m_estival` | IC95 contient zéro | 2/32 | 6,2 % | `BIE35-5__NA`, `BLE3-0` |
| `m_estival` | pente hors `[0 ; 1,2]` | 2/32 | 6,2 % | `BIE35-5__NA`, `BLE3-0` |
| `m_estival` | `n < 60` | 1/32 | 3,1 % | `BIE35-5__NA` |
| `m_estival` | **UNION** | **2/32** | 6,2 % | `BIE35-5__NA`, `BLE3-0` |
| `m_saisonnier` | IC95 contient zéro | 2/33 | 6,1 % | `BLE3-0`, `La Moselle à Hielle` |
| `m_saisonnier` | pente hors `[0 ; 1,2]` | 0/33 | 0 % | aucune |
| `m_saisonnier` | `n < 60` | **6/33** | 18,2 % | `ABI3-6`, `BLE3-0`, `FLU8-4`, `GRO9-1`, `HRI7-7`, `LGV11-8` |
| `m_saisonnier` | **UNION** | **7/33** | 21,2 % | les précédentes |

Sur l'estival, les trois critères se recouvrent presque entièrement : deux
d'entre eux attrapent `BLE3-0`, et l'union n'ajoute rien. Sur le saisonnier,
c'est **l'effectif** qui mord — les fenêtres de reproduction sont courtes. À
comparer au seuil actuel de V4.5, `n < 20` (`core.py:251`), qui n'en attrapait
que deux : la règle dérivée est nettement plus stricte, et c'est le corpus qui
le demande.

### C3 — Ce que V4.5 rend possible en aval d'un rejet

| Comportement | Possible sans modifier V4.5 ? |
|---|---|
| **`m = 0`** → `T_norm = T` | **oui.** `analyse_vulnerabilite(df, m, …)` reçoit `m` en argument (`core.py:174`) ; lui passer `0.0` donne `Tmh_norm = Tmh` et `Tmax_norm = T_eau_max` (`core.py:177-178`) sans toucher une ligne |
| **refus** — ne pas créer les colonnes | **non.** `analyse_vulnerabilite` les crée toujours et s'en sert immédiatement pour `pct_chr` et `n_aigu` (`core.py:182-186`) |

Le refus est pourtant **déjà anticipé en aval** : `core.py:613-614`,
`core.py:992`, `figures.py:71` et `figures.py:88` retombent tous sur `Tmh` et
`T_eau_max` quand la colonne manque. Or c'est exactement ce que produit
`m = 0`. **Les deux comportements coïncident numériquement**, et un seul est
atteignable sans modification. La spécification retient `m = 0`.

---

## §4 — La spécification

**[`docs/SPEC_detecteur_et_validite.md`](SPEC_detecteur_et_validite.md)**, cinq
sections :

1. **Le détecteur**, deux marches — socle relatif `E_moy` normalisé par sa
   dispersion propre, puis conjonction `R_ampl × E_max` dès que `TN` et `TX`
   sont là. Grandeurs, relativisation, seuils et leur dérivation, données
   exigées, comportement quand elles manquent, et **les quatre blocs d'écran**
   à dégradation déclarée.
2. **La règle de validité** — significativité (IC95 excluant zéro), domaine
   `[0 ; 1,2]`, effectif `n ≥ n_min` dérivé, en conjonction ; par espèce sur
   `m_saisonnier`.
3. **La provenance de chaque valeur numérique** — onze valeurs, aucune propre
   à un bassin. Deux valeurs de `thermie_points` explicitement écartées : le
   6 °C d'amplitude d'air (remplacé par une dérivation qui le retrouve) et le
   plancher `R_ampl > 0,67` (qui exige des négatifs terrain).
4. **Les six fichiers de `app/` touchés**, avec l'effet attendu artefact par
   artefact — et les deux artefacts qui **ne doivent pas bouger**,
   `04_normales.csv` et `05_anomalies.csv`, dont toute divergence signalerait
   une régression.
5. **Les points dont le comportement changera**, nommément et chiffrés.

---

## §5 — Décisions qui manquent, en alternatives fermées

Trois décisions ne se déduisent pas de la mesure. Chacune est écrite comme une
alternative à deux branches, avec ce qui les départage.

### Alternative 1 — La valeur par défaut de `k`

| Branche | `k = 3,0` | `k = 2,0` |
|---|---|---|
| jours marqués (socle) | 68, soit ×3,1 le régime en service | 470, soit ×21 |
| points marqués | 18 sur 31 | 31 sur 31 |
| est-ce un sur-ensemble du service ? | **non** — perd 6 des 22 jours | **oui** — n'en perd aucun |
| \|Δ`m`\| médian | 0,0010 | 0,0082 |
| \|Δ`Tmh_norm` p95\| max | 1,05 °C | 2,91 °C |

**Ce qui les départage :** si le détecteur doit être une **extension** du
comportement actuel — ne jamais cesser d'écarter ce qui l'était —, c'est
`k = 2`. Si le mot « aberration » doit garder son sens statistique usuel et le
détecteur rester rare, c'est `k = 3`. La spécification retient **3,0** par
défaut, parce que c'est la convention et parce que l'impact sur `m` y est dix
fois moindre ; le choix est exposé comme paramètre et se change sans toucher
au code.

### Alternative 2 — Le rejet de `m_saisonnier` : zéro, ou repli sur `m_estival` ?

V4.5 replie déjà `m_saisonnier` sur `m_estival` (`core.py:251`, `core.py:258`).
La règle de validité ajoute un troisième cas de rejet.

| Branche | `m_saisonnier = 0` | repli sur `m_estival`, s'il est valide |
|---|---|---|
| cohérence avec `m_estival` rejeté | **la même règle produit le même effet** | deux comportements différents pour un même verdict |
| continuité avec V4.5 | rompt le repli existant | **le prolonge** |
| effet sur `Tmh_norm_fraie` | pas de normalisation sur la fenêtre de fraie | normalisation avec un coefficient estimé **hors** de cette fenêtre |
| points concernés | 7 estimations sur 33 | idem |

**Ce qui les départage :** si la règle de validité dit « cette pente ne veut
rien dire », alors lui substituer une autre pente estimée sur une autre saison
est un choix de méthode, pas un correctif — et il faut l'assumer comme tel. Si
au contraire la continuité avec V4.5 prime, le repli l'emporte. La
spécification retient **zéro**, par cohérence avec le traitement de
`m_estival` ; la branche opposée est explicitement notée en §2.3.

### Alternative 3 — La conjonction quand `R_ampl` n'est pas calculable

Une chronique sans structure infra-journalière donne `T_eau_max = T_eau_min`,
donc `R_ampl = 0` : la marche 2 ne peut pas se prononcer. Le cas existe —
`BLE3-0`.

| Branche | la marche 2 se déclare **indisponible** | la marche 2 **échoue au premier membre**, donc ne marque rien |
|---|---|---|
| ce que l'écran dit | « détecteur dégradé, une seule marche » | rien de particulier |
| risque | l'opérateur sait que le contrôle est partiel | l'absence de marquage se lit comme une absence d'exondation |
| coût | un bloc d'affichage de plus | aucun |

**Ce qui les départage :** un détecteur qui ne marque rien parce qu'il ne peut
pas se prononcer, et un détecteur qui ne marque rien parce qu'il n'y a rien à
marquer, produisent le même écran et ne veulent pas dire la même chose. La
spécification retient **indisponible et déclaré**, conformément au principe de
dégradation déclarée qui gouverne tout le §1.4.
