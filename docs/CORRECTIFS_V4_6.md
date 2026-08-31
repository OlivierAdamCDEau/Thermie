# Registre des correctifs — thermie_points face à V4.5

Une entrée par écart assumé entre le nouvel outil et le référentiel V4.5 (`data/ref_V4_5/thermie_debits`).

**Règle d'architecture.** Le nouvel outil reproduit les valeurs de V4.5 à l'identique. Il y ajoute des colonnes de traçabilité et des variantes de diagnostic, qui ne réalimentent jamais le calcul principal. Toute divergence de valeur doit être justifiable comme un **correctif de bug**, jamais comme un choix méthodologique alternatif. Aucune divergence n'existe hors de ce registre.

**Le registre est le cahier des charges de la V4.6, pas un journal des dégâts.** Chaque entrée porte une colonne « à porter en V4.6 » (D22) : *oui* lorsque le portage est sans discussion, *à discuter* lorsqu'il engage un choix de méthode qui n'est pas le nôtre.

Les quatorze incohérences relevées dans `docs/CONVENTIONS_V4_5.md` §9 sont classées ci-dessous en trois familles, plus une quatrième pour celles que les décisions D1 à D11 règlent directement.


## Tableau de classement

| Incohérence | Famille | Traitement | À porter en V4.6 (D22) | Motif |
|---|---|---|---|---|
| I1 | réglée par décision | D4 — `T − m × Delta_TMm_liss` retenue | **oui** | D4 tranche : `T − m × Delta_TMm_liss` |
| I2 | réglée par décision | D3 — voie B (recalcul depuis l'air brut) | **oui** | D3 tranche : voie B |
| I3 | B — reproduite + quantifiée | variante de diagnostic, tâche 6b | **à discuter** | écart maximal 0,22 °C, au-dessus du seuil de signalement mais faible devant la variabilité |
| I4 | A — reproduite + tracée | colonne `n_jours_delta_liss` | **oui** | colonne de traçabilité, sans effet sur les valeurs |
| I5 | B — reproduite + quantifiée | variante de diagnostic, tâche 6b | **à discuter** | aucune des deux formulations n'est tranchée |
| I6 | B — reproduite + quantifiée | `m_max` estimé en parallèle, tâche 6b | **à discuter** | estimer `m_max` séparément est un changement de méthode, pas un correctif |
| I7 | réglée par décision | D7 — comptage des heures non parsables | **oui** | comptage seul, comportement inchangé |
| I8 | A — reproduite + tracée | colonne `delta_comble` | **oui** | colonne de traçabilité, sans effet sur les valeurs |
| I9 | C — corrigée comme bug | `T_eau_min` testé contre la borne basse | **oui** | bug caractérisé, asymétrie sans justification |
| I10 | C — corrigée comme bug | motif « gel probable » distinct | **oui** | écart entre l'intention documentée et le code |
| I11 | réglée par décision | D5 — validité fondée sur les trous horaires | **oui** | D5 tranche : validité par les trous horaires |
| I12 | A — reproduite + tracée | tests de Shapiro affichés, sans effet | **oui** | affichage seul, aucun calcul modifié |
| I13 | C — corrigée comme bug | D7 — règle d'heure élargie | **oui** | perte silencieuse d'information, bug caractérisé |
| I14 | réglée par décision | D2 — TN et TX lus et conservés | **oui** | lecture de TN et TX, sans effet sur les calculs repris |

---

## Famille C — corrigées comme bugs (divergence de valeur assumée)


### C1 — Lissage à travers les lacunes (décision D10) — **priorité 1**

| | |
|---|---|
| Référence V4.5 | `core.py:93-94` (Tmh), `core.py:102-104` (`Delta_TMm_liss`), `indicateurs.py:50-55` (Tmm30j), `qc.py:48-56` (détecteur de plateau) |
| Comportement actuel | La série journalière ne contient que les jours **présents**. `rolling(window=N)` s'applique sur cet index **positionnel** : une fenêtre de 7 lignes qui enjambe une lacune de 427 jours moyenne des valeurs séparées de plus d'un an. |
| Comportement retenu | La série est **réindexée sur un calendrier continu** (une ligne par jour, NaN sur les jours absents) avant tout `rolling`. Les paramètres `window` et `min_periods` restent **exactement ceux de V4.5** : on ne change pas le lissage, on change le support sur lequel il s'applique. |
| Justification | Une fenêtre de 7 lignes n'est une fenêtre de 7 jours que si la série est continue. 20 des 27 points ont au moins une interruption de plus de 24 h et 10 ont des lacunes de plus de 390 jours : la condition n'est pas remplie. Ce n'est pas un choix méthodologique — les deux versions prétendent calculer la même chose, et une seule y parvient. |
| Impact chiffré | **444 jours-points** où `Tmh` diffère et **444** où `Delta_TMm_liss` diffère, sur 63 147 jours comparés. Écart absolu médian sur `Tmh` : 0,331 °C ; p95 : 4,778 °C ; maximum : **4,811 °C**. Sur `Delta_TMm_liss` : médiane 0,875 °C, p95 4,430 °C, maximum **6,173 °C**. |
| Condition d'acceptabilité | **Vérifiée** : sur le plus long segment continu de chaque point, hors bords de fenêtre, les deux lissages coïncident au bit près pour 27 des 27 points testables. Le correctif ne change rien là où V4.5 était juste. |

### C2 — Colonne d'heure non reconnue (I13, décision D7)

| | |
|---|---|
| Référence V4.5 | `io_data.py:73-74` |
| Comportement actuel | La colonne d'heure séparée n'est retenue que si son nom **commence** par « heure » (`startswith`), alors que la colonne de date est détectée deux lignes plus haut par simple **inclusion** (`io_data.py:54-57`). Asymétrie non documentée. |
| Comportement retenu | Une colonne est reconnue comme colonne d'heure si son nom **contient** « heure », « hour », « time » ou « hms », en position autre que la colonne de date. La conversion en `Timedelta` reste celle de V4.5 (`io_data.py:76-81`, recopiée sans modification). |
| Justification | Bug caractérisé : la perte est **silencieuse** (aucune erreur, aucun avertissement) et rend inexploitable toute grandeur infra-journalière du point concerné, alors que le fichier contient bien l'information. |
| Impact chiffré | **BLE3-0** : colonne « chmes_heure » désormais lue. 2 952 heures distinctes restituées là où V4.5 datait les 2 952 mesures à minuit. Les moyennes, maxima et minima **journaliers** sont inchangés (agrégats par jour civil, jour correct) ; seule la structure infra-journalière change. |

### C3 — Borne basse jamais testée sur `T_eau_min` (I9)

| | |
|---|---|
| Référence V4.5 | `qc.py:42-43` |
| Comportement actuel | Le détecteur de bornes teste `T_eau_moy` contre les deux bornes et `T_eau_max` contre la borne haute, mais **jamais `T_eau_min` contre la borne basse**. Un jour dont le minimum infra-journalier descend à −3 °C alors que la moyenne reste positive n'est pas signalé, tandis que le cas symétrique en borne haute l'est. |
| Comportement retenu | `T_eau_min < −0,5 °C` est testé, avec le motif distinct « T_eau_min < −0,5°C (correctif I9) » pour que l'écart reste isolable et le résultat de V4.5 reconstituable. Le seuil n'est pas modifié. |
| Justification | Asymétrie sans justification dans le référentiel. Une température d'eau négative est physiquement impossible en régime liquide : c'est un défaut de sonde, qu'elle apparaisse sur la moyenne ou sur le seul minimum. |
| Impact chiffré | Aucun jour supplémentaire marqué. |

### C4 — Plateau de gel non distingué d'une sonde bloquée (I10)

| | |
|---|---|
| Référence V4.5 | `qc.py:48-56`, commentaire ligne 53 |
| Comportement actuel | Le commentaire annonce « ne pas flaguer les périodes hivernales stables proches de 0 °C par gel ». **Aucune exclusion de ce type n'est implémentée** : le détecteur signale indifféremment une sonde bloquée et un plateau de gel hivernal réel. |
| Comportement retenu | Un plateau dont la température moyenne sur la fenêtre est inférieure à 1 °C reçoit le motif « plateau — gel probable » au lieu de « sonde bloquée ». **`qc_ok` est inchangé** : les deux restent marqués, seul le motif diffère. |
| Justification | Correctif d'un écart entre l'intention documentée et le code. Le choix de ne PAS modifier `qc_ok` est délibéré : requalifier un motif est une amélioration de lisibilité, requalifier une exclusion serait un changement de méthode. |
| Impact chiffré | Aucun plateau sous le seuil de gel. |

### C5 — Le contrôle qualité ne supprime plus de lignes

| | |
|---|---|
| Référence V4.5 | `qc.py:101-106` |
| Comportement actuel | `controle_qualite` retourne une série **amputée** des enregistrements écartés. |
| Comportement retenu | Aucune ligne n'est supprimée. Deux colonnes `qc_ok` (booléen) et `qc_motif` (texte) portent l'information. |
| Justification | Un filtre est réversible, une suppression ne l'est pas. On doit pouvoir recalculer n'importe quel indicateur avec et sans contrôle qualité et mesurer l'écart — ce que la version amputée interdit. **Aucune divergence de valeur** : filtrer sur `qc_ok` reproduit exactement la série de V4.5, aux quatre correctifs près listés ici. |
| Impact chiffré | Nul par construction sur les valeurs ; +2 colonnes. |

### C6 — Jointure eau × air à gauche et non interne

| | |
|---|---|
| Référence V4.5 | `core.py:85` |
| Comportement actuel | `merge(..., how="inner")` : un jour d'eau sans air est supprimé de l'analyse. |
| Comportement retenu | Jointure à gauche : le jour reste présent, les colonnes d'air sont vides, et une colonne `air_disponible` le signale. |
| Justification | Conséquence directe de C1. Avec une jointure interne, l'index positionnel de la série dépend de la couverture du fichier d'air — le défaut même que la réindexation corrige. Les calculs qui exigent l'air écartent explicitement ces jours ; le résultat est identique, la traçabilité meilleure. |
| Impact chiffré | **204 jours-points** conservés qui auraient été supprimés, tous hors couverture du fichier d'air. |

---

## Famille A — reproduites telles quelles, tracées (aucune divergence de valeur)


### A1 — I4 : `min_periods` divergents entre `Tmh` et `Delta_TMm_liss`

`Tmh` exige 4 valeurs sur 7 (`core.py:93`) ; `Delta_TMm_liss` se contente d'une seule (`core.py:102-104`). En bord de chronique et de part et d'autre d'une lacune, l'anomalie lissée peut ne reposer que sur 1 ou 2 jours. Sans effet sur `Tmh_norm` (que le NaN de `Tmh` propage), mais `Tmax_norm` s'appuie sur `T_eau_max`, toujours défini.

**Classement en famille A** : les deux valeurs de `min_periods` sont des paramètres, pas des erreurs de code. Les modifier changerait les résultats sans qu'on puisse dire lequel des deux réglages est « juste » — ce serait un choix méthodologique, précisément ce que l'architecture interdit. On reproduit et on trace.

**Trace ajoutée** : colonne `n_jours_delta_liss`, nombre de jours réellement contributifs au lissage de l'anomalie.

**Constat** : 100 jours-points où `Delta_TMm_liss` repose sur moins de 4 jours, soit 0,2 % des jours renseignés.

### A2 — I8 : comblement implicite de l'anomalie manquante

`Delta_TMm` est joint en `how="left"` (`core.py:86`) et peut donc être NaN. Le lissage `min_periods=1` ignore les NaN : un jour sans anomalie se voit attribuer la moyenne de ses voisins. C'est un comblement de lacune, non documenté comme tel et non tracé.

**Classement en famille A** : supprimer ce comblement supprimerait des valeurs que V4.5 produit, donc changerait les résultats. On reproduit et on compte.

**Trace ajoutée** : colonne `delta_comble`, vraie lorsque l'anomalie du jour est absente mais que la valeur lissée existe quand même.

**Constat** : 204 jours-points concernés.

### A3 — I12 : tests de normalité sans effet sur le calcul

`core.py:128-134` choisit Pearson ou Spearman selon les tests de Shapiro, mais la pente `m` — seule grandeur qui alimente la normalisation — reste la pente OLS dans tous les cas (`core.py:136`). Le test conditionne l'affichage, pas le calcul.

**Classement en famille A** : ce n'est pas un bug, c'est un défaut de présentation. Le corriger consisterait à substituer une régression robuste à l'OLS quand la normalité est rejetée — un changement de méthode, hors périmètre.

**Trace ajoutée** : les tests sont affichés avec la mention explicite qu'ils **ne conditionnent aucun calcul**, et l'intervalle de confiance de `m` est publié avec des écarts-types robustes à l'autocorrélation (Newey-West), qui répondent à la vraie question — l'incertitude sur la pente — que les tests de normalité ne traitent pas.

---

## Famille B — reproduites telles quelles, quantifiées par une variante de diagnostic


Pour chacune, la version V4.5 **est celle qui alimente le socle**. La version corrigée n'est calculée que pour chiffrer l'enjeu, et ne réalimente rien.


### B1 — I3 : décalage d'un jour dans les normales des années bissextiles

Normale agrégée par `dayofyear` (`io_data.py:385`) puis reportée sur le calendrier bissextile de l'an 2000 (`io_data.py:395`), contre agrégation directe par couple (jour, mois).

**Écart mesuré sur les 366 jours calendaires** : médiane 0,0641 °C, p95 0,1418 °C, maximum **0,2243 °C** (le 07/11).

> **Signalement** : le maximum dépasse 0,1 °C. Le lissage à ±10 jours n'absorbe donc pas entièrement le décalage, contrairement à ce que l'on pouvait attendre. À reverser à l'arbitrage.

### B2 — I5 : anomalie hebdomadaire retranchée d'un maximum journalier

La justification de `core.py:95-101` — aligner les échelles de temps des deux termes — vaut pour `Tmh`, moyenne sur 7 jours. Elle est ensuite appliquée à l'identique à `T_eau_max` (`core.py:160`), valeur journalière instantanée.

**Écart mesuré** entre `T_eau_max − m×Delta_TMm_liss` (V4.5) et `T_eau_max − m×Delta_TMm` (cohérente avec la justification écrite), sur 26 points : médiane des médianes 0,595 °C, plus fort maximum **4,520 °C** (BIE42-7).

### B3 — I6 : coefficient estimé sur une grandeur, appliqué à une autre

`m` est la pente de `T_eau_moy ~ T_air` (`core.py:126-136`), puis appliqué à `Tmh` et à `T_eau_max` (`core.py:159-160`).

**Mesure** : `m_max`, pente de `T_eau_max ~ T_air` sur la même fenêtre, comparé à `m_moy`. Rapport `m_max / m_moy` sur 25 points : médiane **1,226**, étendue de 1,031 à 1,495. Les intervalles de confiance à 95 % des deux pentes sont disjoints sur **8 points sur 26**.

Ce rapport n'est pas qu'un contrôle : au-dessus de 1, il signale un point dont les pointes se dégradent plus vite que la moyenne quand l'air se réchauffe. C'est un résultat en soi, à reprendre à l'étape 4.

---

## Incohérences réglées par les décisions D1 à D11

Ces quatre incohérences ne donnent lieu à aucun correctif : la décision arbitrée les rend sans objet.

- **I2** (deux définitions de la normale) — réglée par **D3** : voie B, recalcul depuis l'air brut, lissage circulaire ±10 j. La voie A (`EcartNormales` pré-calculé) est abandonnée.
- **I7** (heure non parsable silencieusement mise à zéro) — réglée par **D7** : le comportement de V4.5 est conservé à l'identique, mais les cas sont désormais **comptés** et publiés.
- **I11** (seuils minimaux de mesures journalières incohérents) — réglée par **D5** : la validité d'un jour ne repose plus sur un nombre de mesures mais sur l'absence de trou supérieur à 6 h après rééchantillonnage horaire, critère unique appliqué à toutes les grandeurs journalières.
- **I14** (`TN`/`TX` jamais lus) — réglée par **D2** : ils sont lus et conservés. Ils n'entrent dans **aucun** calcul repris de V4.5 et servent au diagnostic de sonde exondée, puis à la normalisation de l'amplitude.

---

## Code recopié du référentiel

Deux règles de V4.5 ne sont pas des fonctions isolées et ne sont donc pas importables. Elles sont **recopiées sans modification de logique** ; toute évolution de V4.5 sur ces lignes devra y être répercutée.

- charger_eau / choix de la colonne de date (io_data.py:54-63)
- charger_eau / conversion d'une valeur d'heure en Timedelta (io_data.py:76-81)

---

## Famille D — divergences de méthode assumées

Cette famille est créée à l'étape 3A. Elle se distingue des trois autres par
une propriété qu'il faut énoncer clairement : **ce ne sont pas des correctifs
de bug**. Le code de V4.5 fait ce que son auteur a voulu qu'il fasse. C'est
notre contexte d'emploi qui rend son résultat non transposable.

Les ranger en famille C aurait été confortable et faux, et le registre y aurait
perdu sa valeur : si tout écart devient un « bug », le registre ne distingue
plus ce qui corrige d'une erreur de ce qui assume un choix, et il cesse de
pouvoir servir de cahier des charges.

### D1 — Le détecteur « hors d'eau » ne pilote plus le contrôle qualité

| | |
|---|---|
| Référence V4.5 | `qc.py:60-82`, seuils `config.py:77-80` |
| Comportement actuel | Sur juin-septembre, un jour est suspect si `T_eau_max − TM > 4 °C` ; à partir de 5 jours suspects, **la saison JJAS entière est exclue**. |
| Comportement retenu | Le détecteur est **conservé et calculé** dans les colonnes `qc_hors_eau_v45`, `qc_hors_eau_v45_annee` et `qc_hors_eau_v45_n_jours`, plus une colonne `qc_ok_v45` qui reconstitue exactement le tri de V4.5. **Il ne pilote plus `qc_ok`.** |

**Justification, telle que le maître d'ouvrage l'a formulée et qu'elle doit
être consignée.** Le seuil de 4 °C n'a de sens que si la station d'air est
proche et à altitude comparable des points d'eau — hypothèse implicite jamais
écrite, mais sur laquelle repose son calibrage. La décision D1 (poste unique à
1 133 m pour un réseau de fond de vallée) viole cette hypothèse. Reproduire
fidèlement le code produit donc ici un résultat que V4.5 lui-même ne produirait
pas : lancé avec un poste local, il n'exclurait pas ces saisons. La fidélité au
code et la fidélité aux résultats divergent, et c'est la seconde qui fonde le
contrat de non-contradiction. Conserver l'exclusion reviendrait à publier un
artefact de notre propre décision d'architecture en le présentant comme un
résultat du référentiel.

**Impact chiffré.** Sur juin-septembre, V4.5 marquait
16 293 jours sur
22 150 observés. Le détecteur d'exondation qui
le remplace en marque 146.
Recouvrement : 123 jours communs.

**À porter en V4.6 : à discuter.** Mon avis, argumenté. Le portage ne doit pas
consister à supprimer le détecteur, qui reste utile lorsque la station d'air
est locale. Il devrait consister à **rendre l'hypothèse explicite et
vérifiable** : que V4.5 refuse de lancer ce détecteur, ou émette un
avertissement bloquant, lorsque l'écart d'altitude entre le poste et la station
d'eau dépasse un seuil — ou plus simplement lorsque cet écart n'est pas
renseigné. Un détecteur dont la validité dépend d'une hypothèse non vérifiée
est un piège pour son prochain utilisateur, et c'est exactement ce qui nous est
arrivé.

### D2 — Un épisode d'exondation n'exclut plus la saison entière

| | |
|---|---|
| Référence V4.5 | `qc.py:73-77`, `config.py:80` (`hors_eau_exclut_saison = True`) |
| Comportement actuel | Cinq jours suspects suffisent à écarter les 122 jours de la fenêtre estivale. |
| Comportement retenu | Une **séquence** d'au moins 3 jours suspects consécutifs marque cette séquence, plus une marge d'un jour de part et d'autre. Un jour suspect isolé est signalé sans exclure. **On exclut l'épisode, pas la saison.** |
| Justification | La règle de V4.5 est disproportionnée indépendamment du seuil retenu : une canicule réelle de six jours efface un été entier de mesures valides. La marge d'un jour couvre l'entrée et la sortie progressives du régime exondé, où la signature est encore ambiguë. |
| Impact chiffré | 146 jours marqués « exondation » au total, contre 16 293 pour la règle de V4.5. |

**À porter en V4.6 : à discuter.** Mon avis : oui sur le principe. L'exclusion
saisonnière était un moyen commode de se prémunir contre une détection
journalière peu fiable ; dès lors qu'on dispose d'un détecteur travaillant sur
la forme du signal et non sur son niveau, elle n'a plus de justification.

### D3 — Deux détecteurs au lieu d'un

| | |
|---|---|
| Référence V4.5 | `qc.py:60-82` |
| Comportement actuel | Un détecteur unique, journalier, censé couvrir aussi bien la sortie d'eau de quelques minutes pour la relève que l'exondation de plusieurs semaines. |
| Comportement retenu | Deux détecteurs : un **infra-journalier** pour le pic de manipulation, corrigeant à l'heure ; un **journalier** pour l'exondation prolongée, corrigeant par épisode. |
| Justification | Les deux phénomènes n'ont ni la même durée, ni la même signature, ni la même correction appropriée. Une sonde sortie cinq minutes produit une ou deux valeurs isolées qu'un critère journalier ne verra jamais ; une sonde exondée trois semaines produit un régime que la correction horaire ne saurait traiter. |
| Impact chiffré | Détecteur de manipulation : 11 heures retirées. Détecteur d'exondation : 146 jours marqués. |

**À porter en V4.6 : à discuter.** Mon avis : oui pour le détecteur
d'exondation fondé sur la forme, qui corrige un défaut de conception réel. Non
pour le détecteur de manipulation en l'état — l'étape 3A établit que sa
signature n'est **pas détectable** sur ces données (§4 du rapport), et porter
un détecteur qui ne détecte rien n'apporterait qu'une complexité.

---

## Étape 3B — entrées complémentaires

### D4 — La normalisation devient conditionnelle à la précision de la pente

| | |
|---|---|
| Référence V4.5 | `core.py:156-175` |
| Comportement actuel | `Tmh_norm` et `Tmax_norm` sont calculés **inconditionnellement**, avec la pente OLS quelle qu'elle soit. Aucun test de significativité ni de précision ne conditionne l'application. |
| Comportement retenu | Trois statuts, portés par la colonne `statut_m` : *normalisation appliquée* (25 points), *normalisation appliquée avec m = 0* (1 point), *sensibilité indéterminée* (0 point, colonnes L2 vides). |
| Justification | Normaliser avec une pente dont l'intervalle de confiance est plus large qu'un demi-palier de la grille de classement, c'est propager une incertitude non mesurée dans tous les indicateurs qui suivent, sans que le lecteur puisse le savoir. Le seuil de 0.15 sur la demi-largeur d'IC95 est calé sur cette grille, dont les bornes sont 0,3 / 0,6 / 0,8. |
| Impact chiffré | 0 point sur 27 sort de la normalisation ; 1 point reçoit `m = 0`. |

**À porter en V4.6 : oui.** Le statut *m = 0* mérite une mention particulière :
ne rien corriger est le comportement **juste** pour un point physiquement
découplé de l'air, dont la température ne suit pas l'anomalie atmosphérique. Ce
n'est pas un échec de l'estimation, c'est un résultat. V4.5 appliquerait
aujourd'hui une correction proportionnelle à une pente indistinguable de zéro.

### D5 — Extensions de la normalisation à T_moy et T_min

| | |
|---|---|
| Référence V4.5 | `core.py:159-160` |
| Comportement actuel | Seuls `Tmh_norm` et `Tmax_norm` sont produits. |
| Comportement retenu | `T_eau_moy_norm` et `T_eau_min_norm` sont produits en plus, par la même formule. |
| Justification | Ce sont des **extensions**, pas des divergences : V4.5 ne produisant aucune valeur concurrente pour ces deux grandeurs, aucune contradiction n'est possible. C'est précisément ce qui distingue une extension d'un correctif, et pourquoi celle-ci ne pose aucun risque. |
| Impact chiffré | +2 colonnes, aucune valeur existante modifiée. |

**À porter en V4.6 : oui.**

### D6 — L'amplitude n'est pas normalisable par la couche L2

Ce n'est pas une divergence mais un **constat**, consigné ici pour qu'il ne
soit pas redécouvert à contretemps. `Delta_TMm_liss` étant constant à
l'intérieur d'une journée, la même quantité est retranchée au maximum et au
minimum : `T_eau_max_norm − T_eau_min_norm` est **rigoureusement égal** à
l'amplitude brute.

Vérifié numériquement sur 62 841 jours : écart
maximal 3.6e-15 °C, soit la précision du calcul
flottant.

**Conséquence opérationnelle** : aucune « amplitude normalisée » ne doit être
produite à partir de L2 — elle serait identique à l'amplitude brute tout en
portant un nom qui laisse croire le contraire. La normalisation de l'amplitude
passera par le coefficient `a_ampl`, produit à cette étape et appliqué à
l'étape 4.

**À porter en V4.6 : sans objet** — c'est un avertissement, pas un correctif.
Mais il mérite de figurer dans la documentation de V4.6, car l'erreur est
naturelle à commettre et indétectable à la lecture du résultat.

---

## Étape 3C — entrées complémentaires

### D7 — Le détecteur d'exondation change de grandeur

| | |
|---|---|
| Référence V4.5 | `qc.py:60-82` — remplacé dès l'étape 3A (famille D, entrée D1) |
| Comportement de l'étape 3A | Critère `R_ampl > 0,5` **et** `E_min_rel < −2`. |
| Comportement retenu | Critère `R_ampl_rel × E_max_rel`, seuils 1,5 et 1. |
| Justification | Le critère de 3A était **arithmétiquement inatteignable** sur onze points. `E_min_rel < −2` s'écrit `E_min < médiane − 2` ; or sous exondation `E_min` tend vers `TN_local − TN_référence`, quantité positive. Le critère est donc hors d'atteinte dès que la médiane du point est inférieure à environ 2 °C — ce qui est le cas de onze points, dont la médiane va de 0,04 à 2,06, quand les quinze détectants vont de 2,81 à 5,47. La coupure est arithmétique, pas statistique. |
| Impact chiffré | Couverture portée de 15 à **26 points sur 26**. Jours marqués : 339 contre 70 avec le critère de 3A. Spécificité 99,62 % sur les négatifs terrain. |

**À porter en V4.6 : à discuter.** Mon avis : oui, mais avec la déclaration de
couverture qui l'accompagne. Le correctif ne dispense pas de dire, point par
point, si la détection est opérante — c'est ce que le critère précédent ne
faisait pas et qui l'a rendu trompeur pendant deux étapes.

### D8 — Déclaration de couverture du détecteur, point par point

Ce n'est pas une divergence mais une **obligation de restitution**, ajoutée à
tous les livrables : une colonne `detection_exondation_operante`, établie
**analytiquement** à partir de la marge disponible sur les grandeurs du critère,
et non par simulation.

*Pourquoi analytiquement* : la simulation dépend de la forme d'air synthétique
retenue, de l'échantillon de jours et du générateur aléatoire. La marge
disponible se lit directement dans la médiane du point — c'est une propriété du
jeu de données, pas d'une expérience.

**À porter en V4.6 : oui.** La formule qui la motive vaut d'être reprise telle
quelle : *un détecteur dont on ne dit pas où il est aveugle est plus dangereux
qu'un détecteur absent.*

### D9 — Le coefficient d'amplitude reçoit la même règle de validité que `m`

| | |
|---|---|
| Référence V4.5 | sans objet — `a_ampl` n'existe pas dans le référentiel |
| Comportement retenu | Colonne `statut_a_ampl`, trois niveaux identiques à ceux de `m` : appliqué, appliqué avec `a_ampl = 0`, indéterminé. |
| Justification | Même question que pour `m` : la correction est-elle assez déterminée pour être appliquée ? Le critère est l'intervalle de confiance, **jamais le R²**. |
| Impact chiffré | normalisation d'amplitude appliquée : 25, non estimable — aucune donnée sur la fenêtre de régression : 1, normalisation d'amplitude appliquée avec a_ampl = 0 : 1. |

**Point de méthode à ne pas confondre, et qui vaut pour les deux
coefficients** : le R² mesure le **pouvoir explicatif**, l'intervalle de
confiance mesure à quel point la **correction est déterminée**. Pour une
correction de biais, seul le second compte. Un coefficient de 0,05 ± 0,02
corrige peu, mais il le corrige bien : il n'ajoute pas de bruit. Six points ont
un R² sur `a_ampl` inférieur à 0,20 avec des intervalles serrés — ils ne doivent
pas être écartés à ce titre.

**À porter en V4.6 : oui**, en même temps que `a_ampl` lui-même.

### D10 — Q6 close : `m_moy` reste seul dans la chaîne de normalisation

`m_max` est publié comme **indicateur** (« amplification des pointes ») et
n'entre pas dans la normalisation. Chiffrage définitif de l'écart : avec
`m = 0,5`, une amplification de 1,23 et une anomalie de 2 °C, l'écart sur
`Tmax_norm` vaut **0,23 °C** — inférieur à la demi-largeur des intervalles de
confiance sur `m`. La comparabilité avec V4.5 vaut davantage.

**À porter en V4.6 : à discuter**, sans urgence. La question est tranchée pour
notre livrable ; elle reste ouverte pour une version future du référentiel qui
voudrait normaliser les extrêmes correctement.

### Réserve nommée — robustesse du maximum estival au seuil

Ce n'est pas une entrée de correctif mais une **réserve à porter au livrable
final**, établie par l'analyse de robustesse (tâche 1).

Le coefficient de sensibilité `m` est **robuste** au choix du seuil : écart
médian nul, écart maximal 0,91 fois
la demi-largeur de son intervalle de confiance, aucun point non robuste.

Le **maximum estival ne l'est pas**, et c'était attendu : les jours d'exondation
sont précisément les jours anormalement chauds. 4 points portent
une réserve nommée — **BIE21-7, BIE5-2, BIE51-0, LIZ5-5** — sur
5 couples
point-année dont le maximum varie de plus d'un écart-type interannuel selon le
scénario retenu.

---

## Étape 4 — entrées complémentaires

### D11 — Garde-fou d'amplitude sur le critère d'exondation

| | |
|---|---|
| Référence | critère d'étape 3C, `R_ampl_rel > 1,5` et `E_max_rel > 1,5` |
| Défaut constaté | `R_ampl_rel` se développe en (amplitude d'eau / sa médiane) × (médiane d'amplitude d'air / amplitude d'air). Le second facteur est un **inverse** d'amplitude d'air : une journée couverte gonfle le rapport même si l'eau est normale. Et sur cette même journée `TX` est déprimée, donc `E_max_rel` monte aussi. **Les deux conditions se déclenchent ensemble sur une journée fraîche et couverte** : la conjonction n'y protège pas, elle amplifie. |
| Comportement retenu | Troisième condition : `R_ampl > 0,67`, plancher **absolu**. |
| Justification du niveau | Le plancher est le quantile 99 de `R_ampl` mesuré sur les négatifs terrain, c'est-à-dire sur les seules journées dont on sache qu'une sonde y était immergée. Il n'est donc pas choisi : il est mesuré. La règle de sélection de 3C n'est **pas révisée** — ses deux contraintes restent vérifiées après ajout (100.0 % de spécificité, 26 points opérants sur 26). |
| Impact chiffré | Points marqués le même jour : de 13 à 9. Dates portant au moins cinq points : de 59 à 7. Rapport des amplitudes d'air médianes : de 0,70 à 0,78. Jours marqués après propagation : 89. |

*Valeur d'alors. Le plancher a été recalibré à 0,62 à l'étape 5, le domaine de calage ayant été étendu à l'année entière — voir les entrées D21 et D22.*

**À porter en V4.6 : oui**, indissociablement du critère lui-même. Un rapport
dont le dénominateur peut devenir petit exige un garde-fou sur son numérateur ;
c'est vrai de ce critère comme de tout indicateur normalisé par une amplitude.

### D12 — Contiguïté calendaire des épisodes

| | |
|---|---|
| Référence | `qualite.marquer_episodes`, introduit à l'étape 3A |
| Défaut constaté | Les signatures ne sont calculées que sur les jours de juin à septembre de niveau « complet ». Deux lignes consécutives de la série pouvaient donc être séparées de huit mois, et une séquence de « trois jours consécutifs » enjamber un hiver entier. Un épisode était ainsi daté « du 29/09/2014 au 05/06/2015, 6 jours ». |
| Comportement retenu | La contiguïté est vérifiée sur le **calendrier** : une rupture de plus d'un jour interrompt la séquence. |
| Justification | On ne peut pas affirmer la continuité d'un épisode à travers une lacune, encore moins à travers une saison. C'est un bug, présent depuis l'étape 3A et corrigé ici. |
| Impact chiffré | Le nombre d'épisodes passe de 22 à 34 pour un nombre de jours quasi inchangé : ce sont des épisodes distincts qui étaient fusionnés à tort. |

**À porter en V4.6 : oui.** Bug caractérisé.

### D13 — Normalisation de l'amplitude : anomalie non lissée

| | |
|---|---|
| Référence V4.5 | sans objet — la normalisation d'amplitude n'existe pas dans le référentiel |
| Comportement retenu | `ampl_norm = ampl_eau − a_ampl × (amplitude d'air − sa normale)`, anomalie d'amplitude d'air **non lissée**, là où la chaîne en température emploie `Delta_TMm_liss`. |
| Justification de l'asymétrie | Le coefficient et l'anomalie doivent provenir de la **même** régression. `a_ampl` a été estimé sur l'amplitude d'air journalière non lissée : il doit être appliqué à cette même grandeur. Pour la température, la convention de V4.5 impose l'anomalie lissée et nous nous y tenons au titre de la non-contradiction ; pour l'amplitude, aucune convention n'existe et c'est la cohérence estimation/application qui prime. L'asymétrie est assumée et expliquée, non subie. |
| Vérification | Contrairement à la normalisation en température, celle-ci **n'est pas invariante** — c'est tout son objet. Écart médian 0,265 °C, p95 1,26 °C, maximum 4,33 °C sur 62 278 jours. Un écart nul aurait signalé une erreur. |

**À porter en V4.6 : oui**, avec `a_ampl`.

### D14 — Comparaison entre points : jamais sur un extrême cumulé

Ce n'est pas une divergence mais une **règle de restitution**, qui gouverne tous
les tableaux de synthèse.

Le maximum de tous les temps d'un point dépend de la **longueur** de sa
chronique : un point suivi quinze ans a mécaniquement plus de chances d'avoir
rencontré une canicule qu'un point suivi deux ans. Comparer des maxima cumulés
compare des durées d'observation, pas des cours d'eau.

Toute grandeur de synthèse par point est donc la **médiane des valeurs annuelles
de classe A**, accompagnée du nombre d'années retenues et de l'écart
interquartile. En dessous de trois années, la synthèse porte la mention
« valeur ponctuelle, non représentative ». Le maximum cumulé est restitué dans
une colonne distincte, explicitement étiquetée non comparable.

**À porter en V4.6 : à discuter.** V4.5 ne produit pas de synthèse
inter-points ; la règle deviendra nécessaire dès qu'il en produira une.

---

## Étape 4bis — entrées complémentaires

### D15 — Marge d'épisode : calendaire et non positionnelle

| | |
|---|---|
| Référence | `qualite.marquer_episodes`, correctif D12 de l'étape 4 |
| Défaut constaté | D12 avait rendu **calendaire** la détection des séquences de jours suspects, mais **pas la marge** d'un jour ajoutée de part et d'autre. Les signatures n'existant que de juin à septembre, la ligne précédant le 1er juin est le 30 septembre antérieur : la marge d'un épisode ouvert le 01/06/2015 marquait le 29/09/2014, huit mois plus tôt. Ces jours étaient réellement écartés du socle, et aucune de leurs valeurs ne franchissait le moindre seuil. |
| Comportement retenu | Dates, marge et fusion sont ramenées à un même numéro de jour. La marge n'est ajoutée que si la ligne voisine est bien le jour calendaire voisin. |
| Justification | Un correctif partiel donne l'apparence d'un correctif complet et ferme la question : c'est la raison pour laquelle ce défaut a survécu à l'étape 4, dont tous les contrôles automatiques étaient au vert. |
| Impact chiffré | Épisodes d'un seul jour : 0 → 0. Jours écartés du socle : 89 → 105. |

**À porter en V4.6 : oui.** Bug caractérisé, de la même famille que D12 et
indissociable de lui.

### D16 — Détection d'exondation à hystérésis

| | |
|---|---|
| Référence V4.5 | V4.5 exclut la saison entière au-delà de cinq jours suspects ; il n'a pas de notion d'épisode. |
| Défaut constaté | Un déclenchement sec fragmente un régime exondé unique en épisodes courts séparés de quelques jours, dès que la signature faiblit une journée. Une sonde sortie de l'eau n'y retourne pas parce qu'une journée a été couverte. |
| Comportement retenu | Déclenchement par le critère strict tenu 3 jours consécutifs **en dates** ; prolongation de part et d'autre tant que `R_ampl_rel > 1,0`, `E_max_rel > 0,5` et `R_ampl > 0,51` ; fusion des épisodes séparés de moins de 5 jours. |
| Justification du niveau de prolongation | Le plancher de prolongation est le **quantile 95** de `R_ampl` sur les négatifs terrain, là où celui de déclenchement en est le quantile 99. Les deux sont mesurés sur la même distribution : « une journée immergée sur cent franchit le premier, une sur vingt le second ». Le relâchement n'est acceptable que parce que la prolongation ne peut pas **ouvrir** un épisode. |
| Limite de la validation | La contrainte de spécificité de l'étape 3C est respectée (100,0 %) mais **ne discrimine pas** : sur 1 313 négatifs terrain, 0 sont adjacents à un épisode, seul voisinage que la prolongation puisse atteindre. Le seuil n'est donc pas validé par ce test, il est calé sur la distribution des négatifs. À reprendre si des négatifs terrain datés en période d'épisode deviennent disponibles. |
| Impact chiffré | Épisodes du socle 13 → 10 ; jours marqués 89 → 105 ; durée médiane 6 → 8 jours. |

**À porter en V4.6 : oui**, avec le critère et son garde-fou. Un détecteur à
seuil unique appliqué à un régime qui dure est structurellement fragmentant.

### D17 — Effet marginal et effet cumulé d'un retrait

| | |
|---|---|
| Référence | fiches d'épisode, étape 4 |
| Défaut constaté | L'effet d'un épisode sur le maximum estival était mesuré **épisode par épisode**. Sur un point-année portant plusieurs épisodes, chacun affichait un effet nul, un autre portant encore le maximum. Sur BIE51-0 en 2025, quatre fiches annonçaient « 0,00 °C » là où le retrait cumulé fait passer le maximum de 30,76 à 24,11 °C. |
| Comportement retenu | Deux colonnes : effet marginal (ce seul épisode) et effet cumulé (tous les épisodes du couple point × année). Les fiches sont ordonnées par effet cumulé décroissant. |
| Justification | Un effet marginal nul dans un jeu d'épisodes redondants ne signifie pas « sans conséquence » mais « masqué par les autres ». Publier le seul effet marginal conduit le relecteur à la conclusion inverse de celle que portent les données. Le défaut est général : il concerne toute mesure d'influence par retrait unitaire dans un ensemble redondant. |

**À porter en V4.6 : oui**, dès que V4.6 restituera l'effet d'un tri.

### D18 — Extrême cumulé : le sens suit la nature de l'indicateur

| | |
|---|---|
| Référence | `indicateurs.synthese_par_point`, étape 4 |
| Défaut constaté | Les indicateurs de **minimum** portaient une colonne « maximum cumulé toutes années », calculée comme un maximum. L'intitulé et le calcul étaient faux : l'extrême remarquable d'un minimum est le plus bas. La colonne donnait la valeur la moins notable de la chronique sous l'étiquette la plus alarmante. |
| Comportement retenu | Le sens de l'extrême cumulé est déduit de la nature de l'indicateur ; l'intitulé suit. L'avertissement de non-comparabilité de D14 est inchangé. |

**À porter en V4.6 : oui.** Bug caractérisé.

### D19 — Réserve d'implantation, distincte de la réserve de seuil

Ce n'est pas une divergence de calcul mais une **règle de restitution**.

Deux réserves peuvent porter sur les indicateurs d'extrêmes d'un point, et
elles n'appellent pas la même action :

- **réserve de robustesse au seuil** (étape 3C, quatre points) — le résultat
  dépend d'un choix de seuil du détecteur ; elle appelle la publication d'une
  fourchette ;
- **réserve d'implantation** (D43, BIE40-3) — la sonde n'est pas fiablement
  dans l'eau à cet endroit ; elle appelle une visite de terrain, et aucune
  fourchette ne la lève.

Les réunir dans une colonne unique perdrait l'action à entreprendre. Elles
occupent donc deux colonnes distinctes dans toutes les tables de synthèse.

**À porter en V4.6 : à discuter.** V4.5 ne porte aucune réserve ; la règle
deviendra nécessaire dès qu'il en portera.

---

## Étape 5 — entrées complémentaires

### D20 — Une règle de sélection doit être rejouée après toute modification d'un candidat

| | |
|---|---|
| Référence | règle de sélection de l'étape 3C, garde-fou de l'étape 4 |
| Défaut constaté | Le garde-fou a été ajouté au seul candidat retenu, **après** que la règle l'eut désigné, sans que la sélection soit rejouée. Le candidat appliqué au socle n'était donc plus celui qui avait été sélectionné. Conséquence observable : une règle demandant « le plus permissif des couples admissibles » avait fini par retenir le plus strict des deux candidats en présence. |
| Comportement retenu | Tout candidat reçoit le même diagnostic d'artefact et, s'il est confirmé, son propre garde-fou calé sur le même quantile des négatifs terrain. La règle est ensuite rejouée sur les candidats **dans leur état d'emploi**. |
| Résultat | Vainqueur : `R_ampl > 0,62` et `E_max_rel > 1,0` — forme canonique de cinq écritures équivalentes de la grille, le garde-fou absorbant tout seuil `R_ampl` inférieur à lui. 52 couples sur 126 satisfont les deux contraintes. |
| Impact chiffré | Jours écartés du socle : 105 → 188. Une année quitte la publication (BIE0-3 × 2018, classe A → C). |

**À porter en V4.6 : oui**, comme règle de procédure. Fixer un critère de
sélection avant de voir les résultats ne protège que de l'arbitraire *au moment*
de la sélection ; il ne protège pas d'une dérive introduite après elle.

### D21 — Un seuil quantile se publie avec son intervalle de confiance

| | |
|---|---|
| Référence | plancher `R_ampl` de D11 et de D16 |
| Défaut constaté | Le plancher de déclenchement était publié comme `0,67`, quatre chiffres significatifs, alors qu'il s'agit du quantile 99 d'un échantillon de quelques milliers d'observations : il repose sur quelques dizaines de valeurs de queue. Une journée rejetée à 0,0002 du seuil était présentée comme rejetée, alors que la mesure ne distingue pas ces deux valeurs. |
| Comportement retenu | Le seuil est estimé par bootstrap (2 000 rééchantillonnages) et **publié avec son IC95** : déclenchement 0,62 [0,573 ; 0,651] ; prolongation 0,47 [0,460 ; 0,484]. |
| Modalité ajoutée | « Cas limite » : journée dont toutes les autres conditions sont remplies et dont `R_ampl` tombe à l'intérieur de l'IC. 168 journées, 11 épisodes. La modalité qualifie la décision, elle ne la change pas. |
| Vérification | Le socle recalculé aux deux bornes de l'IC ne déplace **aucune classe de validité** et aucun indicateur publiable. |

**À porter en V4.6 : oui.** Vaut pour tout seuil calé sur un quantile empirique.

### D22 — Le contrôle qualité s'exerce sur l'année, la fenêtre estivale n'appartient qu'à la régression

| | |
|---|---|
| Référence | `qualite.calculer_signatures`, fenêtre juin–septembre depuis l'étape 3A |
| Défaut constaté | Les signatures n'étaient calculées que de juin à septembre, fenêtre héritée de la régression de sensibilité. Or les indicateurs publiés couvrent l'année : minimum hivernal, amplitudes de printemps, d'automne et d'hiver étaient calculés sur des journées **jamais examinées** pour l'exondation. La fenêtre estivale a une raison d'être pour l'estimation de `m` ; elle n'en a aucune pour le contrôle qualité. |
| Comportement retenu | Signatures calculées sur les douze mois, médianes de référence conservées par point ET par mois. Domaine d'examen : 18 758 → 45 838 journées. |
| Réserve 1, mesurée | Le garde-fou d'amplitude d'air à 6 °C rend non diagnosticables 27,3 % des journées sur l'année, contre 15,2 % en été, et près de la moitié des journées de janvier et de décembre. Un examen annuel n'est pas un examen complet ; la part non examinée est publiée par mois. |
| Réserve 2, mesurée | Le détecteur est **arithmétiquement inopérant en hiver** sur 20 des 25 points renseignés : `E_max_rel > 1,0` exige une médiane de `E_max` inférieure à −1,0, or elle vaut +0,08 en hiver. Même mécanisme d'aveuglement que celui établi sur `E_min_rel` à l'étape 3C. La capacité de détection est désormais déclarée **par point et par saison** (`data/socle/detection_par_saison.csv`). |
| Contrôle croisé | Échoue, et son échec est concluant : les 70 journées à eau nettement négative ont un `R_ampl` médian de 0,10. Une sonde prise dans la glace **écrase** son amplitude au lieu de l'amplifier ; le détecteur cherche la signature inverse. Ces journées sont néanmoins toutes déjà écartées par les bornes physiques du contrôle qualité. |
| Apport réel | Les épisodes de printemps et d'automne, jusqu'ici jamais examinés. |

**À porter en V4.6 : oui.** Le domaine de contrôle doit couvrir le domaine de
publication ; toute restriction du premier est une hypothèse tacite sur le
second.

### D23 — Deux phénomènes de signatures opposées ne se détectent pas d'un seul détecteur

Ce n'est pas une divergence mais une **règle de conception**, tirée de D22.

L'exondation estivale et l'émersion hivernale sont toutes deux des sorties
d'eau, et leurs signatures sont **inverses** : la première rapproche l'amplitude
de l'eau de celle de l'air, la seconde l'écrase par isolation thermique. Un
détecteur calé sur l'une est aveugle à l'autre par construction, et aucun
réglage de seuil n'y change rien.

La couverture du second cas repose donc sur d'autres contrôles — bornes
physiques et détecteur de plateau — et cette répartition doit être **déclarée**,
faute de quoi l'absence de détection hivernale se lit comme une absence de
phénomène.

**À porter en V4.6 : à discuter.** V4.5 confond les deux dans un détecteur
unique ; la séparation est déjà actée depuis l'étape 3A.

---

## Étape 5bis — entrées complémentaires

### D24 — Un test de notabilité ne porte que sur ce qui est publié

| | |
|---|---|
| Référence | règle de notabilité posée à l'étape 4bis, déclenchée à l'étape 5 |
| Défaut constaté | La règle jugeait tout écart d'indicateur supérieur à un écart-type interannuel du point, sans distinguer les couples publiés des autres, et sans exiger d'effectif minimal pour estimer cet écart-type. À l'étape 5 elle s'est déclenchée sur cinq valeurs appartenant toutes à un couple de classe C — absent de tout livrable — jugées contre un σ estimé sur deux millésimes, dont l'un valait 0,01 °C. |
| Comportement retenu | Le test ne porte que sur les couples **publiables** (classes A et B). L'écart-type de référence n'est celui du point qu'à partir de quatre années de classe A ; en deçà, on prend l'écart-type interannuel médian du réseau pour le même indicateur, et l'origine du σ est publiée ligne par ligne. |
| Vérification | Sous la règle corrigée, 0 indicateur publiable dépasse le seuil, contre 5 sous la règle littérale. La substitution de l'écart-type, à elle seule, n'aurait pas changé le verdict : c'est la restriction aux couples publiables qui est décisive. |

**À porter en V4.6 : oui**, comme règle de restitution. Un contrôle de
stabilité qui se déclenche sur une valeur non publiée mesure autre chose que ce
qu'il prétend mesurer.

### D25 — Un arrondi de mise en forme ne doit pas pouvoir détruire une valeur

| | |
|---|---|
| Référence | `etape3b._tableau_md`, utilisé par tous les rapports |
| Défaut constaté | La fonction arrondit les flottants au nombre de décimales demandé par l'appelant. Un appel à zéro décimale a transformé un plancher de 0,6122 en « 1 » et un quantile de 0,99 en « 1 », dans un tableau dont le texte voisin — formaté par un autre chemin — donnait les valeurs justes. Un lecteur s'arrêtant au tableau lisait des chiffres faux. |
| Comportement retenu | L'appel fautif est corrigé, et la fonction ajoute des décimales tant que l'arrondi s'écarte de plus de 1 % de la valeur. |
| Justification | Le garde-fou ne dispense pas d'appeler correctement : il empêche qu'une erreur d'appel devienne une erreur publiée. La leçon générale est qu'une même valeur mise en forme par deux chemins finira par diverger — mieux vaut un chemin unique et sûr. |

**À porter en V4.6 : oui**, pour toute fonction de mise en forme de tableau.

### D26 — Les libellés d'étape se dérivent, ils ne se recopient pas

| | |
|---|---|
| Défaut constaté | Les en-têtes « Avant (étape 4) / Après (étape 4bis) » ont survécu **trois fois** à un changement d'étape, parce qu'ils étaient écrits en dur dans le tableau, dans le rapport et dans le résumé console. |
| Comportement retenu | `comparer_avant_apres` reçoit les libellés en paramètre, produit les noms de colonnes et les publie dans `colonnes` ; les trois modules consommateurs les y lisent. |
| Justification | Un libellé écrit en dur ne se met pas à jour, et relire un en-tête pour vérifier qu'il est encore vrai est une tâche que personne ne fait. La récidive triple est la preuve que la discipline ne suffit pas et qu'il fallait un mécanisme. |

**À porter en V4.6 : oui.**

### D27 — Complémentarité saisonnière des deux critères d'exondation — DIAGNOSTIC

Cette entrée **n'est pas un correctif appliqué** : c'est une mesure, portée au
registre parce qu'elle prépare un correctif propre pour l'étape suivante.

L'étape 5 a établi que `E_max_rel` est arithmétiquement inatteignable en hiver,
la médiane de `E_max` y valant 0,08.
Le même calcul appliqué à `E_min` donne l'inverse : médiane hivernale de
9,38, marge de
7,38 contre
0,90 en été.

| Saison | `E_max_rel` opérant | `E_min_rel` opérant |
|---|---|---|
| hiver | 5 / 25 | 25 / 25 |
| printemps | 27 / 27 | 25 / 27 |
| été | 26 / 26 | 15 / 26 |
| automne | 26 / 26 | 26 / 26 |

**Les deux critères sont complémentaires par saison, non concurrents.** L'étape
3C les avait mis en concurrence parce qu'elle ne regardait que l'été.

**Rendement mesuré : nul.** Aucune journée d'hiver ne serait marquée par un
critère `R_ampl × E_min_rel`, à aucun des cinq seuils testés. Et le verrou
n'est pas `E_min_rel` — 2 669 journées d'hiver le
franchissent — mais le **plancher d'amplitude**, franchi par
2 journées d'hiver seulement sur
8 598. Ce qui est cohérent : une sonde hivernale hors
d'eau est le plus souvent isolée par la glace ou la neige, donc d'amplitude
écrasée.

Le cas décrit par la décision — sonde émergée en hiver mais **non gelée**,
invisible aux bornes physiques et hors d'atteinte d'`E_max_rel` — existe et
compte **1 journée** non couverte par un contrôle actuel.

**À porter en V4.6 : à instruire.** Le correctif est propre — critère saisonnier,
`E_max_rel` d'avril à novembre, `E_min_rel` de décembre à mars — et ne demande
aucune donnée nouvelle. Son rendement sur ce jeu est d'une journée : ce que le
diagnostic établit surtout, c'est que le minimum hivernal publié n'est pas
biaisé par des émersions non détectées.

### D28 — Une charte graphique se centralise, et ses dimensions sont définitives

Ce n'est pas une divergence mais une **règle de production**.

Les figures sont construites à **16,0 cm**, largeur utile d'une page A4 à marges
de 2,5 cm, et ne doivent jamais être redimensionnées à l'insertion : un
redimensionnement met à l'échelle les textes en même temps que les traits. Le
SVG est le format principal, avec les textes convertis en tracés
(`svg.fonttype = "path"`), de sorte que l'apparence ne dépende pas des polices
installées chez le lecteur.

Toute information portée par la couleur l'est **aussi** par la forme, le trait
ou la trame, et la règle est **vérifiée** par une planche en niveaux de gris et
non supposée.

Enfin, le titre d'une figure énonce le **résultat**. Cette exigence transforme
une maladresse de formulation en erreur de fait : deux titres ont dû être
corrigés à cette étape parce qu'ils énonçaient un résultat que leur propre
figure contredisait. C'est le prix de la règle, et il vaut d'être payé.

**À porter en V4.6 : oui**, dès que V4.6 produira des livrables graphiques.

---

## Étape 6 — entrées complémentaires

### D29 — Un coefficient s'estime sur le domaine où il s'applique

| | |
|---|---|
| Référence V4.5 | sans objet : V4.5 ne produit aucune normalisation d'amplitude. Il s'agit d'une **extension**, non d'une divergence. |
| Défaut constaté | `a_ampl` était estimé sur la seule fenêtre juin-septembre — héritée de la régression de `m`, où elle est justifiée par la convention de V4.5 — puis appliqué aux quatre saisons. C'est structurellement l'incohérence **I6** relevée dans V4.5, un coefficient estimé sur une grandeur et appliqué à une autre, transposée d'une grandeur à une saison. |
| Preuve du défaut | Le coefficient médian vaut 0,021 en hiver contre 0,179 en été : un rapport de huit. La normalisation ÉLARGISSAIT en conséquence l'écart interquartile hivernal, de 0,20 à 0,29 °C — on retranchait huit fois trop, et ce qu'on retranche en trop est du bruit ajouté. |
| Comportement retenu | `a_ampl` estimé PAR POINT ET PAR SAISON (DJF, MAM, JJA, SON), même estimateur, mêmes écarts-types Newey-West, même règle de statut à trois niveaux appliquée saison par saison. Une saison indéterminée ne prive pas les trois autres de leur normalisation. |
| Vérification | L'écart interquartile hivernal passe désormais de 0,20 à 0,19 °C : la normalisation resserre les quatre saisons. |

**À porter en V4.6 : oui**, avec `a_ampl`. Et la règle générale mérite d'être
retenue au-delà de ce cas : **un coefficient s'estime sur le domaine où il
s'applique**, faute de quoi il transporte les conditions de son estimation dans
un contexte qui ne les vérifie pas.

### D30 — Une règle d'exclusion doit vivre là où elle s'applique

| | |
|---|---|
| Défaut constaté | GRO9-1 est écarté des comparaisons inter-points depuis l'étape 2 — 193 journées mesurées sur cinq ans d'étendue, avec une lacune de plus de quatre ans. La règle vivait dans une constante de `socle.py` et n'avait jamais été appliquée aux figures, où le point figurait comme les autres. |
| Comportement retenu | `figures.comparables()`, appelée par toute figure comparant des points. Le point reste visible là où il ne fausse rien — classes, réserves, schéma de situation — et y porte un marqueur distinct. |
| Justification | Une règle écrite dans un module et appliquée dans un autre ne se maintient pas : rien ne signale, au moment d'écrire une figure, qu'elle existe. |

**À porter en V4.6 : oui.**

### D31 — Un même objet porte un même nombre

| | |
|---|---|
| Défaut constaté | Le même ensemble était décrit par trois nombres différents selon la figure : « 173 années-points », « 242 couples point-année », « 228 comparables ». Les trois étaient exacts et ne désignaient pas la même chose ; aucun ne le disait. |
| Comportement retenu | Une fonction unique produit la cascade complète, chaque étage nommé : 63 147 journées mesurées → 242 couples point × année → 241 portant des indicateurs → 220 classés → 156 publiables. |
| Retrait | « 173 années-points » était une division du nombre de journées par 365. Cela ne désigne aucun objet du jeu de données : le chiffre est retiré. |
| Règle associée | Une figure de couverture publie **deux** chiffres — la part de journées écartées par le contrôle qualité (0,5 %) et la part de couples non publiables faute de couverture (64 sur 220). Le premier décrit le tri, le second décide du livrable. |

**À porter en V4.6 : oui**, comme règle de restitution.

### D32 — La représentativité s'affiche là où l'œil se pose

Ce n'est pas une divergence mais une **règle de restitution**.

Un point à une seule année de classe A et un point à treize portaient le même
marqueur sur la même figure. Rien n'empêchait de les lire comme deux mesures
équivalentes, et une note de bas de figure n'y aurait rien changé : on ne lit
pas une note avant de comparer deux points, on la lit après.

L'étiquette porte donc le code, le cours d'eau, le point kilométrique et le
nombre d'années de classe A — « ABI3-6 · Abîme · PK 3,6 · 1 an » — **dans
l'axe**, au moment où la comparaison se fait.

**À porter en V4.6 : oui**, dès que V4.6 comparera des points.

### D33 — Le cours d'eau récepteur reste vide, le regroupement se fait par cours d'eau

| | |
|---|---|
| Besoin | Regrouper les points par unité hydrographique dans les tableaux. |
| Source examinée | `chsta_sousbassin` du référentiel. **Mesure faite** : renseignée sur 2 de nos 27 points, et n'y prenant qu'une seule valeur. Un regroupement à une classe unique ne regroupe rien. |
| Comportement retenu | Regroupement par `cours_eau` — renseigné sur les 27 points, dix valeurs distinctes, et porteur de sa propre traçabilité depuis l'étape 3B. Les tableaux sont groupés par cours d'eau puis par PK croissant. |
| `cours_eau_recepteur` | Reste **vide** là où aucune source du dossier ne l'établit. Huit préfixes sur douze sont dans ce cas. Aucune valeur n'est devinée. |

**À porter en V4.6 : sans objet** — V4.5 ne regroupe pas les points.

---

## Étape 7 — entrées complémentaires

### D34 — Écart mesuré avec la convention V4.5, et ce qu'il autorise à conclure

Ce n'est pas un correctif mais la **quantification** de ceux qui existent.

Les deux versions sont calculées dans la même chaîne, à partir des mêmes
colonnes de la couche L2 : `qc_ok` pour thermie_points, `qc_ok_v45` pour la
convention V4.5. L'écart isole donc exactement les familles **D1 et D2** — le
détecteur « hors d'eau » ne pilote plus le contrôle qualité, un épisode
d'exondation n'exclut plus la saison entière. Les familles A, B et C sont
communes aux deux branches.

| Grandeur | Valeur |
|---|---|
| Journées estivales retenues par thermie_points | 21 952 |
| Journées estivales retenues par la convention V4.5 | 5 836 |
| Écartées par le seul détecteur « hors d'eau » de V4.5 | 16 116 |
| Écartées par le détecteur d'exondation de thermie_points | 161 |
| Part de l'été écartée par V4.5 | 73,4 % |
| Points sans aucun jour retenu par V4.5 | 10 sur 26 |

**Conclusion, et elle n'est pas celle qu'on espérait.** L'écart n'est pas petit
devant la distance des indicateurs aux seuils de la grille de vulnérabilité de
V4.5 : sur Tmh_norm, un point se tient à 0,03 °C du seuil de 18 °C quand
l'écart de convention atteint 5,13 °C. **On ne peut donc pas affirmer que le
classement du § 7.3 est inchangé.** Le classement n'est pas recalculé pour
autant — ce serait disproportionné et hors du champ demandé.

**Mais la cause est instructive.** Sur les points où V4.5 conserve l'été
entier, l'écart de `m` est **exactement nul**. Les deux outils ne divergent pas
sur le calcul : ils divergent sur les journées qu'ils acceptent. Les deux points
qui changent de classe de sensibilité le font sur des estimations V4.5 reposant
sur 122 et 41 journées, contre plus de mille pour les nôtres.

**À porter en V4.6 : sans objet** — c'est une mesure. Elle établit en revanche
que les familles D1 et D2 sont, de loin, les correctifs les plus lourds de
conséquence.

### D35 — L'impact du réchauffement s'estime par décomposition, non par tendance directe

| | |
|---|---|
| Référence V4.5 | sans objet : V4.5 ne produit aucune estimation d'impact climatique. Extension. |
| Problème | Estimer l'impact par une tendance directe sur la température de l'eau est le mauvais estimateur : huit à quinze valeurs annuelles par point, sept points seulement comptant onze années de classe A. |
| Comportement retenu | `impact = m × forçage`. Le forçage est la pente de Sen sur la température d'air estivale (30 années) ; la transmission est `m`, estimé sur un millier de journées par point. Les deux incertitudes sont propagées par produit des bornes. |
| Résultat | Forçage 0,92 °C/décennie [0,57 ; 1,34], Mann-Kendall p = 6.0e-05. Impact par point de 0,00 à 0,51 °C/décennie. |
| Justification a posteriori | Le contrôle croisé sur les sept points éligibles donne des intervalles de tendance directe larges de 7,0 °C par décennie : ils ne permettent de rien estimer. |

**À porter en V4.6 : à discuter**, si V4.6 doit produire un volet prospectif.

### D36 — Une agrégation saisonnière exige un contrôle de couverture

| | |
|---|---|
| Défaut constaté | La moyenne juin-septembre de l'air était calculée sur toutes les années disponibles, y compris l'année en cours arrêtée fin juillet. La « moyenne estivale » de cette année-là était en réalité une moyenne de juin-juillet, structurellement plus chaude. |
| Impact chiffré | La pente de Sen passait de 0,865 à 1,024 °C par décennie, soit +18 %, sans qu'aucun avertissement ne le signale. |
| Comportement retenu | Une année n'entre dans l'agrégation que si sa saison est complète à 94 % ; la liste des années écartées est publiée avec le résultat. |
| Portée | Vaut pour toute agrégation sur une fenêtre saisonnière, non pour la seule température d'air. |

**À porter en V4.6 : oui.**

### D37 — La borne basse de `m` : ce que le contrôle croisé révèle

Ce n'est pas un correctif mais une **limite d'interprétation**, mesurée.

`m` est estimé sur la variabilité **journalière** de l'été. L'extrapoler à une
tendance décennale suppose un transfert identique aux deux échelles de temps, ce
qui n'est pas exact : à l'échelle du jour, l'apport souterrain est un tampon
froid de température à peu près fixe ; à l'échelle de la décennie, la nappe se
réchauffe elle aussi et l'amortissement perd de son efficacité.

`m` au pas journalier est donc probablement une **borne basse** de la
sensibilité à long terme, et d'autant plus que le point est tamponné.

Le contrôle croisé va dans ce sens, à condition de comparer la tendance de
l'eau à un forçage mesuré sur la MÊME période. Sur 7 points
comptant au moins onze années de classe A, la tendance observée sur l'eau —
série **brute**, jamais normalisée — est supérieure à `m × forçage` sur
**6 points sur 7**, dans un rapport médian de
1,91 sur la période commune. 6 restent
compatibles dans leur intervalle, ce qui valide l'ordre de grandeur de la
décomposition.

**Conséquence à écrire dans toute restitution** : un point tamponné n'est pas
protégé pour toujours. BIE6-8, avec m = 0,20, doit son statut de refuge à la
thermie de sa nappe, qui dérive plus lentement — mais qui dérive.

**À porter en V4.6 : oui**, comme réserve accompagnant toute lecture
prospective de `m`.

---

## Étape 7bis — entrées complémentaires

### D38 — Une comparaison de tendances exige une période commune

| | |
|---|---|
| Référence | contrôle croisé de l'étape 7 (D62f) |
| Défaut constaté | La tendance observée sur l'eau était estimée sur les seules années de classe A du point — onze à treize années récentes — et comparée à `m × forçage` où le forçage portait sur trente ans, 1996-2025. Le réchauffement n'étant pas linéaire, la comparaison produisait un excédent **mécaniquement**, sans qu'aucun phénomène physique ait à intervenir. |
| Preuve du défaut | Sur les périodes communes, l'air s'est réchauffé de 1,73 °C par décennie contre 0,92 sur 1996-2025 — presque le double. Le rapport médian observé sur attendu tombe de 4,13 à 1,91. |
| Comportement retenu | Le forçage est réestimé, point par point, exactement sur les années de classe A de ce point. Le forçage trentenaire reste celui qui sert au calcul de l'impact publié : c'est la période de la normale et la seule qui ait la puissance nécessaire. |
| Conclusion révisée | Le contrôle croisé conclut à la **compatibilité** de l'estimation par décomposition avec l'observation directe, et à rien de plus. La réserve sur le réchauffement de la nappe redevient une hypothèse physique fondée, que ce jeu ne permet ni de confirmer ni d'infirmer. |

**Deux signaux auraient dû alerter avant la mesure**, et ils sont consignés
parce qu'ils se généralisent :

- une tendance sur l'eau de 2 à 3,5 °C par décennie signifiait que l'eau se
  réchauffait deux à quatre fois plus vite que l'air ; **rien ne transmet plus
  de 100 % d'un forçage**, et un résultat qui viole une borne physique doit
  faire suspecter le protocole avant la physique ;
- six intervalles sur sept contenaient déjà la valeur attendue : **un test qui
  ne peut rien rejeter ne démontre rien**. Ce raisonnement avait déjà été tenu
  à l'étape 4bis à propos d'une spécificité sans pouvoir discriminant ; savoir
  formuler une règle ne suffit pas à la reconnaître dans un autre habillage.

**À porter en V4.6 : oui**, comme règle de méthode.

### D39 — Des séries non indépendantes ne se comptent pas comme des observations

Ce n'est pas un correctif de calcul mais une **règle de lecture**.

Le contrôle croisé porte sur sept points d'un même bassin, sur les mêmes années,
soumis aux mêmes épisodes météorologiques. Les sept tendances ne sont donc pas
indépendantes : **sept résultats concordants comptent pour une seule observation
vue sept fois**, non pour sept confirmations.

La formulation « 7 sur 7 » avait été employée comme un argument de force. Elle
ne l'est pas, et aucun décompte de ce type ne doit servir d'appui tant que
l'indépendance des séries n'est pas établie.

**À porter en V4.6 : oui.**

### D40 — Une figure dérivée d'une autre par un scalaire doit le déclarer

| | |
|---|---|
| Référence | troisième panneau du profil longitudinal (D62c) |
| Constat | Le forçage climatique étant commun à tous les points, le panneau d'impact est le panneau de sensibilité multiplié par un scalaire. |
| Ce qu'il apporte | L'unité qui parle à un décideur — des degrés par décennie plutôt qu'un rapport sans dimension — et des barres élargies par la propagation des deux incertitudes. |
| Ce qu'il n'apporte pas | Aucune information nouvelle sur la forme du profil. |
| Comportement retenu | La légende le dit explicitement. Sans cette mention, un lecteur y verrait une confirmation indépendante de la sensibilité. |

**À porter en V4.6 : oui**, dès que V4.6 produira des figures dérivées.

### D41 — La cohérence des nombres se contrôle sur les livrables produits

Ce n'est pas une divergence mais une **procédure de vérification**.

Trois fois au cours de ce travail, un même ensemble a été décrit par deux
nombres différents dans deux livrables — « 173 années-points » contre
« 242 couples », « 1 313 négatifs terrain » contre « 2 885 », des en-têtes
d'étape survivant au changement d'étape. Chaque fois les deux nombres étaient
exacts et ne désignaient pas la même chose ; chaque fois, rien ne le disait.

La vigilance ayant échoué trois fois, la parade n'est pas la vigilance. Un
contrôle relit désormais **le texte réellement écrit** dans la note, les annexes
et le classeur, et le compare aux valeurs de référence calculées une seule fois.
Lire les fichiers plutôt que les variables est la seule façon de détecter un
nombre recopié à la main.

Une seconde liste nomme les valeurs dont on **sait** qu'elles ont été
remplacées, et vérifie qu'elles ne subsistent nulle part.

**À porter en V4.6 : oui**, pour toute production documentaire.

---

## Étape 8 — entrées complémentaires

### D42 — Deux décomptes d'un même objet doivent nommer leur périmètre

| | |
|---|---|
| Défaut constaté | Le classement de validité compte 228 couples point × année, la table des indicateurs 220 ; la classe C compte 72 dans l'un et 64 dans l'autre. Les quatre nombres sont exacts et décrivent deux ensembles différents, mais aucun livrable ne le disait. |
| Cause | Le classement de validité est **estival** ; les indicateurs sont calculés sur **toute l'année**. 8 couples reçoivent une classe sans produire d'indicateur — aucun jour utilisable — et 21 produisent des indicateurs sans classe estivale, leurs seuls jours utilisables étant hors été. |
| Comportement retenu | La réconciliation est publiée dans la note méthodologique (§2.5) et dans le classeur. Tout décompte publié nomme désormais l'ensemble qu'il compte. |
| Constat associé | Les 21 couples sans classe estivale publient pourtant des indicateurs annuels — minimum hivernal, amplitudes — sans que rien n'indique ce que vaut leur chronique. Ce n'est pas une erreur de calcul mais un trou de restitution, désormais nommé. |

**À porter en V4.6 : oui**, comme règle de restitution.

### D43 — La cohérence se contrôle aussi dans le temps

| | |
|---|---|
| Référence | contrôle de cohérence de l'étape 7bis (D41) |
| Défaut constaté | Ce contrôle comparait les livrables **entre eux à une date donnée**. Il ne comparait pas un même objet **à deux dates**, et c'est exactement par là que l'écart 228 / 220 est passé inaperçu entre l'étape 5 et l'étape 7bis. |
| Comportement retenu | Les valeurs de référence de chaque étape sont enregistrées dans `data/socle/historique_decomptes.json`. L'étape courante est confrontée aux précédentes, et tout écart doit porter une explication ; à défaut il est signalé « À EXPLIQUER ». |
| Justification | Les étapes antérieures ne sont pas rejouées : leurs valeurs ne peuvent donc pas être retrouvées par le calcul. Sans trace écrite, un décompte qui change est invisible. |

**À porter en V4.6 : oui.**

### D44 — Une source unique, et des renvois

Ce n'est pas une divergence mais une **règle de production documentaire**.

La note méthodologique et les annexes de la note d'expertise se recouvraient
largement. **Deux rédactions du même contenu divergent toujours** — ce projet
en a fait trois fois l'expérience sur de simples décomptes.

La note méthodologique porte donc la méthode ; les annexes de la note
d'expertise renvoient à ses sections par numéro et ne conservent en propre que
ce qui est spécifique au réseau étudié : tableaux de résultats, fiches
d'épisode, réconciliation avec le référentiel.

**À porter en V4.6 : oui**, dès que V4.6 produira plus d'un document.

### D45 — Un logigramme qui renvoie à sa justification

Ce n'est pas une divergence mais une **règle de restitution graphique**.

Deux logigrammes plutôt qu'un, parce que deux publics : le simplifié se
comprend sans commentaire et ne porte ni sigle, ni seuil, ni formule ; le
complet répond à la question « comment savez-vous que ce chiffre est bon ».

Trois exigences commandent le second :

- les trois branches de la règle de statut **aboutissent**, y compris
  « sensibilité indéterminée » — une branche qui ne mène nulle part laisserait
  croire que ces points sortent du jeu ;
- les boucles d'exclusion montrent que rien n'est supprimé : une journée
  écartée est marquée, motivée, conservée ;
- **chaque étape renvoie par un numéro vers la section qui la justifie**. C'est
  ce renvoi qui distingue un logigramme d'un schéma décoratif.

**À porter en V4.6 : à discuter.**

### D46 — Publier le coût d'un choix en même temps que le choix

Ce n'est pas une divergence mais une **règle de rédaction**, dont l'application
a produit un effet mesurable.

Chaque choix méthodologique de la note est écrit en trois temps : ce que l'on
cherche à obtenir, la règle, puis **ce que ce choix coûte**. Une règle énoncée
seule se subit ; une règle précédée de son intention et suivie de son coût se
discute, et un lecteur en désaccord peut dire lequel des trois il conteste.

La forme a obligé à formuler des coûts qui n'avaient jamais été écrits, bien
qu'ils fussent implicites dans le code : l'agrégation horaire atténue les
extrêmes très brefs ; le détecteur de pic de manipulation n'agit que là où une
date de visite est renseignée ; le classement de validité écarte des années
entières sans regarder les valeurs. **Un coût implicite ne se discute pas.**

**À porter en V4.6 : oui.**

---

## Étape 9 — entrées complémentaires

### D47 — La nomenclature d'un livrable n'est pas celle du développement

Ce n'est pas une divergence mais une **règle de restitution**.

Les versions internes d'un outil ne sont pas des versions officielles. Devant un
maître d'ouvrage, « V4.5 » soulève des questions hors sujet et donne à des
étapes de développement l'apparence d'un référentiel ; un nom de fichier ou une
référence `module.py:118` donnent à lire le chantier au lieu du résultat.

Deux noms dans la liasse : **thermie_bio** pour l'outil du volet biologique,
**thermie_points** pour celui du volet thermique. Les documents internes — ce
registre, le carnet de méthode, les rapports d'étape — conservent la
nomenclature de développement : les renommer rendrait ce registre illisible, et
ils ne sont pas remis.

**La substitution est une passe de SORTIE**, appliquée au document au moment de
l'écrire et vérifiée ensuite sur le fichier produit. Renommer à la source aurait
contaminé le code et les documents internes.

**À porter en V4.6 : oui**, dès qu'un livrable sort de l'atelier.

### D48 — Une démonstration d'une page vaut mieux qu'un registre de trente

Ce registre est un cahier des charges de développement : il cite des numéros de
ligne et qualifie des comportements de bugs. Il n'a pas sa place sous les yeux
d'un maître d'ouvrage.

Il est remplacé, dans la liasse, par une annexe d'**une page** qui dit ceci et
rien d'autre : les deux outils traitent le même jeu de données ; leur cohérence
a été vérifiée point par point ; **là où les deux retiennent les mêmes journées,
les coefficients sont rigoureusement identiques** — 5 points, écart nul
à la quatrième décimale ; les écarts observés ailleurs proviennent du nombre de
journées retenues (21 952 contre
5 836 sur
22 116), non du calcul ; les deux volets
reposent donc sur la même convention.

**Ce que cette réduction a appris.** Le fait qui compte pour un lecteur — l'écart
nul là où les données sont les mêmes — tenait en une ligne dans un registre de
trente pages, où personne ne l'aurait cherché. Réduire a obligé à trouver
laquelle des trente pages portait la démonstration.

**À porter en V4.6 : oui.**

### D49 — Une figure porte les mentions de sa nature, pas celles d'une autre

Les trois logigrammes portaient la note générique des figures de données :
« 27 points représentés — exclus : aucun ». Cette mention n'a aucun sens sur un
schéma de chaîne de traitement.

**Une mention qui ne veut rien dire décrédibilise celles qui en ont un** : un
lecteur qui voit une note absurde cesse de lire les notes. La charte porte donc
une note propre aux schémas — objet, renvoi vers ce qui les justifie, source —
distincte de celle des figures de données.

**À porter en V4.6 : oui.**

### D50 — Un trait ne traverse jamais un texte

Trois défauts de tracé relevés en relecture des images exportées, non des
coordonnées :

- un connecteur descendait à travers un titre de colonne, qui se lisait
  « p_c » — les titres sont désormais au-dessus du point de branchement ;
- deux étiquettes d'issue chevauchaient le bord d'un losange et une flèche —
  elles occupent le sommet opposé au renvoi de section ;
- un chemin était tracé en deux traits avec une pointe intermédiaire qui
  n'aboutissait à rien — un chemin, un coude, une pointe.

S'y ajoute un défaut d'alignement : des blocs de largeurs et de centres
différents produisaient un escalier involontaire, **qui se lit comme une
hiérarchie qui n'existe pas**.

La règle de vérification est la même que partout ailleurs dans ce travail :
**relire l'image produite, jamais les coordonnées**.

**À porter en V4.6 : oui**, dès que V4.6 produira des schémas.

---

*thermie_points 0.9 — CORRECTIFS_V4_6.md — révision étape 9.*
