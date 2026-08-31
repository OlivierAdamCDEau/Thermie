# SPÉCIFICATION — détecteur de mise hors d'eau et règle de validité

*THERMIE_BIO V4.6. Prête à implémenter. Aucune question ouverte.*

Toute valeur numérique porte sa provenance : **dérivée du jeu traité**,
**convention statistique**, ou **paramètre exposé avec son défaut**. Aucune
valeur propre à un bassin n'y figure (contrainte 5, D15).

---

## 1. Le détecteur, marche par marche

L'escalier a **deux marches** (D26). La marche 1 fonctionne avec ce que V4.5
lit déjà. La marche 2 s'ajoute dès que `TN` et `TX` sont présents, **en
conjonction** et jamais en substitution.

### 1.1 Ce qui est commun aux deux marches

**Fenêtre d'examen.** Les mois de `QCConfig.hors_eau_mois`, défaut
**`(1, …, 12)` — l'année entière**. *Provenance : paramètre exposé.*

> **Amendement d'étape 20 (D105, D111, D115) — correctif 13.** La fenêtre valait
> `(6, 7, 8, 9)`. La mesure d'étape 19 a établi que **95 des 134 journées
> d'artefact non détectées tombaient hors de ces quatre mois**, et que le mois
> le plus touché était **mai** — celui où l'on pose les sondes.
>
> L'extension seule ne suffisait pas, et la mesure l'a montré avant la pose :
> elle marquait **73 journées de saison froide sans qu'aucune soit corroborée**,
> parce qu'une vague de froid produit le même écart eau–air qu'une sonde
> émergée. Le **second membre de la marche 1**, décrit en 1.2, lève cette
> ambiguïté. Les deux sont indissociables.

**Second membre de la marche 1 — le test de signe.** `T_eau_max` doit être
**strictement au-dessus de la médiane de son groupe (point, mois)**.

```
marche 1 = (E_moy_rel > k)  ET  (T_eau_max − médiane_{mois}(T_eau_max) > 0)
```

*Ce n'est pas un second détecteur.* `E_moy = T_eau_max − T_air` est grand aussi
bien quand l'eau monte que quand l'air descend, et la marche 1 seule ne sait pas
lequel des deux termes a bougé. Le 1ᵉʳ juin 2011, l'air de LA_PESSE à 4,6 °C —
sous le 5ᵉ centile de sa propre fenêtre — a fait marquer **sept sondes de la
Bienne dont l'eau était à ou sous sa médiane de juin**. Le second membre répond
à cette seule question : *ce découplage vient-il de l'eau ou de l'air ?*

**Zéro n'est pas un seuil.** C'est la frontière du phénomène, et c'est pourquoi
ce membre ne divise pas par le MAD : il ne compare aucune magnitude. Le
`plancher_dispersion` n'y est pas repris — il protège une division qui n'a pas
lieu — et la mesure a établi qu'il ne changeait aucune journée du corpus.

**Abstention.** Le groupe doit compter au moins `min_jours_groupe` journées.
Sinon le second membre ne se prononce pas, la conjonction ne peut être
satisfaite, et l'abstention est déclarée (D100).

> **Ce membre répare un défaut du correctif 1 lui-même** (D112), découvert par
> mesure à l'étape 20 : l'inversion opérait déjà **dans** la fenêtre estivale.
> Il n'est pas une contrepartie de l'extension de fenêtre.
>
> **Une fuite déclarée et non poursuivie** (D117). Quatorze journées de saison
> froide y survivent, dont onze de signature « coup de froid marginal » —
> l'eau à un ou deux dixièmes au-dessus de sa médiane pendant que l'air
> s'effondre. Un second garde-fou pour les rattraper exigerait un seuil calibré
> sur ce corpus. **Une frontière n'est pas un filtre.**

**Relativisation.** Toute grandeur `G` est comparée à l'habitude de la sonde
traitée **au même mois** :

```
G_rel = (G − médiane_{mois}(G)) / MAD*_{mois}(G)
MAD*  = 1,4826 × médiane(|G − médiane(G)|)
```

> **Amendement d'étape 11 (D64).** La formule s'écrivait
> `médiane_{point,mois}`. C'était une notation de corpus, héritée des mesures
> du harnais qui portaient sur trente-deux points à la fois. **L'application
> traite une sonde à la fois (D41)** : le regroupement par point n'existe pas
> pour elle, il n'y a qu'un point. La formule est réécrite dans le seul cadre
> où elle se calcule. Le comportement est identique — c'est la notation qui
> était fausse, pas le code.

*Provenance du facteur 1,4826 : convention statistique — il fait de `MAD*` un
estimateur robuste de l'écart-type, de sorte que le seuil se lise comme un
nombre d'écarts-types.* La médiane et le MAD sont **dérivés du jeu traité**.

**Seuil.** `k`, en unités de `MAD*`. *Provenance : paramètre exposé, défaut
`k = 3,0` — convention statistique de l'aberration à trois écarts-types.*
Le widget qui l'expose **doit prendre son défaut du dataclass** et non d'un
littéral (correctif 7, D22).

**Diagnosticabilité.** Un couple (point, mois) est déclaré **non
diagnosticable**, et ses jours ne sont ni marqués ni déclarés sains, si :

| Condition | Seuil | Provenance |
|---|---|---|
| dispersion nulle ou quasi nulle | `MAD* ≤ plancher_dispersion` | paramètre exposé, défaut **0,05 °C** — c'est déjà le seuil d'immobilité de V4.5, `plateau_ecart_type_min` (`config.py:89`) |
| mois trop court | moins de `min_jours_groupe` jours | paramètre exposé, défaut **10** — convention : en deçà, une médiane et un MAD sur un mois ne veulent rien dire |

*Mesuré sur le corpus : ce garde-fou ne se déclenche jamais — 0 couple sur
124. Il reste, et se déclare non exercé (D29).*

**Regroupement en épisodes.** Les jours marqués sont regroupés en séquences
**calendaires** contiguës. Un épisode de moins de `min_jours_episode` jours
est **signalé sans exclure**. *Provenance : paramètre exposé, défaut **1** —
c'est-à-dire aucun épisode écarté sur sa seule longueur.*

> **Amendement d'étape 6 — le défaut passe de 3 à 1.**
>
> **Raison de droit.** Le défaut de 3 était « repris de la règle de séquence
> de `thermie_points` (`qualite.py:177`) ». C'est une importation de seuil
> depuis le projet clos, que **D15** interdit. La formule « convention de
> détection et non valeur de bassin » habillait l'importation ; elle ne
> l'annulait pas.
>
> **Raison de fait.** La correction de R10 (étape 5) a établi que la longueur
> médiane d'épisode de la marche 2 vaut **1,5 jour**, et non 4,0 comme
> l'annonçait l'étape 4 — les épisodes y étaient comptés sur le masque du
> socle puis relus règle par règle. Le balayage
> (`out/etape5/r10_filtre_episode.csv`) donne alors :
>
> | `min_jours_episode` | marche 1 : jours conservés | marche 2 : jours conservés |
> |---|---|---|
> | 1 | 40/40 (0 % exclus) | 4/4 (0 % exclus) |
> | 2 | 21/40 (47,5 % exclus) | 2/4 (50 % exclus) |
> | **3** | **17/40 (57,5 % exclus)** | **0/4 (100 % exclus)** |
> | 4 | 11/40 (72,5 % exclus) | 0/4 (100 % exclus) |
>
> À 3, le plancher ne raffine pas la marche 2 : il la **supprime
> intégralement**, sur les deux seuls points où elle se déclenche. Un
> garde-fou qui annule le détecteur qu'il garde n'est pas un garde-fou.
>
> Le défaut de 1 ne retire aucune capacité : le paramètre reste exposé, et un
> opérateur qui veut un plancher l'écrit pour son jeu. Quand la mesure ne
> désigne aucune valeur, le neutre est le bon défaut.

### 1.2 Marche 1 — le socle relatif

| | |
|---|---|
| **Grandeur** | `E_moy = T_eau_max − TM` |
| **Relativisation** | `E_moy_rel`, formule de 1.1 |
| **Déclenchement** | `E_moy_rel > k` |
| **Données exigées** | `T_eau_max` journalier ; `TM` de la station d'air |
| **Si `TM` manque un jour** | jour non diagnosticable — comportement déjà celui de V4.5 (`qc.py:65`, `T_air.notna()`) |
| **Si la chronique d'eau est journalière** | la marche fonctionne : `T_eau_max` existe, même agrégé sur une seule mesure. Sa **signification** se dégrade, et l'écran le dit |

**Rien de plus que ce que V4.5 lit déjà.** Cette marche est toujours
disponible.

### 1.3 Marche 2 — la conjonction, dès que `TN` et `TX` sont présents

**Ce n'est pas une substitution.** La mesure d'étape 3 a établi que
`T_eau_max − TX` n'apporte **aucune marge** : rapportée à sa propre
dispersion, elle est inférieure à celle de `T_eau_max − TM` sur **31 points
sur 31**. `TX` ne remplace donc rien.

**Ce n'est pas non plus la conjonction `E_moy ET E_max`.** Mesurée, elle se
comporte à l'envers de son intention : elle sélectionne les journées de
**faible amplitude d'air**, précisément le profil d'artefact. La raison est
mécanique — `E_moy` et `E_max` diffèrent exactement de `TX − TM`, donc ils ne
franchissent leur seuil ensemble que lorsque l'air varie peu. Les chiffres
sont au §2 du rapport d'étape.

**La conjonction retenue oppose deux signatures DIFFÉRENTES** — une forme et
un niveau :

| | |
|---|---|
| **Premier membre — la forme** | `R_ampl = (T_eau_max − T_eau_min) / (TX − TN)`, relativisé |
| **Second membre — le niveau** | `E_max = T_eau_max − TX`, relativisé |
| **Déclenchement** | `R_ampl_rel > k` **ET** `E_max_rel > k` |
| **Données exigées** | `T_eau_min` et `T_eau_max` journaliers — V4.5 les calcule déjà (`io_data.py:102-103`) — plus `TN` et `TX` |

**Garde-fou d'amplitude d'air.** `R_ampl` est un rapport ; son dénominateur
`TX − TN` doit être assez grand pour que le rapport ait un sens. Un jour dont
l'amplitude d'air est sous `amplitude_air_min` est **non diagnosticable par la
marche 2** — ni marqué, ni déclaré sain.

> *Provenance : **dérivée du jeu traité**. `amplitude_air_min` = quantile
> `q_ampl` de l'amplitude d'air du jeu, `q_ampl` étant un paramètre exposé de
> défaut **0,10** (convention : le premier décile). Sur le corpus, cette
> dérivation donne 5,00 à 6,62 °C selon le jeu — le 6 °C de `thermie_points`
> n'est **pas** importé, il se trouve seulement corroboré.*

**Pourquoi cette conjonction et pas l'autre**, mesuré à `k = 3` :

| Règle | jours | points | ampl. air médiane | `R_ampl` médian | épisode médian | sync. max | dates à ≥ 5 points |
|---|---|---|---|---|---|---|---|
| socle seul | 40 | 16 | 10,90 °C | 0,47 | 2,0 j | 6 | 1 |
| `E_moy` ET `E_max` | 8 | 7 | **6,80 °C** | 0,53 | 1,0 j | 5 | 1 |
| **`R_ampl` ET `E_max`** | **4** | **2** | **12,05 °C** | **1,03** | **4,0 j** | **1** | **0** |

Le `R_ampl` médian de **1,03** est la signature physique recherchée :
l'amplitude de l'eau **égale** celle de l'air, ce qu'une sonde immergée ne fait
pas. Les épisodes durent 4 jours — un régime, pas du bruit. Et **aucun jour
n'est marqué simultanément sur deux points**, donc aucun artefact
météorologique régional.

**Les quatre jours retenus, en clair.** Ils se lisent sans statistique :

| Point | Date | `T_eau_max` | `TX` | **eau − air max** | `T_eau_min` | ampl. eau | ampl. air | `R_ampl` |
|---|---|---|---|---|---|---|---|---|
| `LA PLAINE A RAON` | 11/06/2011 | 26,18 °C | 19,3 °C | **+6,88** | 19,39 | 6,79 | 9,3 | 0,73 |
| `LA PLAINE A RAON` | 12/06/2011 | 27,43 °C | 21,3 °C | **+6,13** | 19,67 | 7,76 | 15,7 | 0,49 |
| `BIE40-3` | 08/07/2015 | 25,42 °C | 16,4 °C | **+9,02** | 16,81 | 8,61 | 6,5 | **1,32** |
| `BIE40-3` | 07/09/2015 | 25,90 °C | 15,8 °C | **+10,10** | 5,04 | 20,87 | 14,8 | **1,41** |

Le maximum de l'eau dépasse le maximum de l'air de 6 à 10 °C : de l'eau
immergée ne fait pas cela. Sur `BIE40-3`, l'amplitude de l'eau **dépasse**
celle de l'air (`R_ampl > 1`) — le capteur suit l'air plus fidèlement que
l'air ne se suit lui-même à la station de référence.

> **Corroboration indépendante.** `BIE40-3` est précisément le point que le
> `MANIFESTE.md` du projet clos place sous « réserve d'implantation », avec des
> épisodes d'exondation relevés **en 2015**, 2018 et 2023. La conjonction
> spécifiée ici le retrouve en 2015 **sans qu'aucun seuil de ce projet n'ait
> été importé** — les seuils sont dérivés du jeu traité ou conventionnels.
> Ce n'est pas une validation, faute de vérité terrain sur ce corpus ; c'est
> la seule concordance externe dont on dispose, et elle va dans le bon sens.

### 1.4 Ce que l'écran affiche, marche par marche

La dégradation est **déclarée**, jamais silencieuse. À chaque marche, trois
lignes : ce dont le contrôle a besoin, ce qu'il voit, ce qu'il ne voit pas.

#### Marche 1 active, marche 2 indisponible

> **Détecteur de mise hors d'eau — socle relatif (marche 1 sur 2)**
> *Besoin :* température maximale journalière de l'eau, température moyenne
> de l'air.
> *Vu :* `N` jours marqués sur `M` diagnosticables, en `E` épisodes.
> `P` jours non diagnosticables (dispersion nulle, ou mois de moins de 10 jours).
> *Non vu :* **la marche 2 est indisponible — le fichier d'air ne porte pas
> `TN` et `TX`.** Sans elle, le détecteur ne distingue pas une sonde sortie de
> l'eau d'une journée simplement chaude : il ne dispose que du niveau, pas de
> la forme du signal. Une sonde exondée en permanence reste invisible, sa
> propre médiane étant contaminée.

#### Les deux marches actives

> **Détecteur de mise hors d'eau — socle relatif + conjonction (2 marches sur 2)**
> *Besoin :* extrêmes journaliers de l'eau ; `TM`, `TN` et `TX` de la station d'air.
> *Vu :* `N₁` jours au socle, dont `N₂` confirmés par la conjonction
> forme × niveau, en `E` épisodes.
> `P` jours non diagnosticables par la marche 2 (amplitude d'air sous
> `X,XX °C`, dérivée du 1ᵉʳ décile de ce jeu).
> *Non vu :* l'émersion **hivernale**, dont la signature est **inverse** — elle
> écrase l'amplitude au lieu de la rapprocher de celle de l'air — et qui relève
> des bornes physiques et du détecteur de plateau. Et une sonde exondée en
> permanence, pour la même raison qu'à la marche 1.

#### Chronique d'eau sans structure infra-journalière

> ⚠ **Détecteur dégradé.** La chronique ne porte qu'une mesure par jour, ou
> son horodatage n'a pas été reconnu. `T_eau_max`, `T_eau_min` et leur
> amplitude sont alors calculés sur un seul point : `R_ampl` vaut zéro par
> construction et **la marche 2 ne peut pas se prononcer**. Le socle reste
> actif ; sa lecture est celle d'un niveau, pas d'une forme.

*Ce cas existe dans le corpus : `BLE3-0`, dont la colonne d'heure n'est pas
reconnue (`io_data.py:79-82`, correctif C2 du registre).*

#### Aucune marche disponible

> ⛔ **Détecteur inactif.** Aucune chronique d'air exploitable sur la période
> de la sonde. Aucune journée n'est écartée à ce titre — ce qui **n'est pas**
> un constat d'absence d'exondation.


### 1.5 Le bloc de dégradation déclarée

*Ajouté à l'étape 7, en application de D45 et du correctif 5.*

**Pourquoi ce bloc existe.** Deux mécanismes retiraient des journées de la
chaîne **sans le dire** : la jointure eau/air, qui était interne et effaçait
toute journée d'eau que la station d'air ne couvre pas, et l'exigence de
densité calendaire du correctif 2, qui laisse sans `Tmh` les journées trop
isolées. Mesuré avant correction sur le corpus de référence :

| Mécanisme | Journées retirées | Points concernés |
|---|---|---|
| jointure eau/air | **636 sur 68 028 (0,93 %)** | **23 sur 32** |
| densité calendaire | **18 sur 67 392 (0,03 %)** | 5 sur 32 |

La moyenne est trompeuse et c'est tout le problème : `La Moselle à Hielle`
perdait **102 de ses 303 journées — 33,7 %, d'un seul tenant, du 6 juillet au
15 octobre 2012**, c'est-à-dire tout son été ; `LA PLAINE A RAON-SUR-PLAINE`
en perdait **330 sur 1 545 (21,4 %)**, dont l'année 2008 en entier. Un
résultat calculé sur les deux tiers d'une chronique n'est pas faux : il est
**dégradé**, et l'utilisateur doit l'apprendre de l'écran plutôt que de ne
jamais le savoir.

**Le bloc est TOUJOURS affiché**, y compris quand rien n'est retiré. Un bloc
qui n'apparaît qu'en cas de problème apprend à l'utilisateur que son absence
signifie « rien à signaler » — alors qu'elle peut aussi signifier « personne
n'a regardé ».

**Aucun seuil n'est introduit.** Le texte ne se durcit pas au franchissement
d'une valeur conventionnelle : il s'enrichit de phrases dont la condition est
un **fait constaté** — une année civile entièrement retirée, ou des journées
retirées dans la fenêtre estivale qui sert à estimer `m`. Ces deux conditions
sont booléennes et se lisent sur les données, elles ne se calibrent pas.

#### Aucune journée retirée

> **Complétude — aucune dégradation.**
> Les `N` journées retenues par le contrôle qualité sont toutes entrées dans
> le calcul. Aucune n'a été retirée faute de température d'air, ni faute de
> voisines assez proches dans le calendrier.

#### Journées retirées faute de température d'air

> **Dégradation déclarée — `K` journées non diagnosticables sur `N`
> (`P` %).**
> *Motif :* température d'air absente à cette date (station air) — `K`
> journées.
> *La plus longue interruption continue :* `L` jours, du `d1` au `d2`.
> *Ce que cela retire :* ces journées d'eau ont bien été mesurées et le
> contrôle qualité les a retenues. Elles ne sont **ni écartées, ni
> défectueuses** : il leur manque une donnée qui ne vient pas de la sonde.
> Faute d'anomalie climatique, elles ne reçoivent pas de température
> normalisée, n'entrent pas dans le pourcentage de dépassement de seuil, et
> ne comptent pas dans les journées de vulnérabilité.
> *Ce qu'il faut en faire :* vérifier la station météo retenue. Une autre
> station couvrant la période rendrait ces journées au calcul.

#### Une année civile entièrement retirée

*Phrase ajoutée à la précédente, sous condition de fait.*

> ⚠ **L'année `A` est entièrement absente du calcul** : ses `M` journées
> d'eau ont toutes été retirées faute d'air. Les résultats ne décrivent pas
> cette année-là. Toute lecture pluriannuelle — tendance, comparaison
> interannuelle, année de référence — porte sur les autres années
> uniquement.

#### Des journées d'été retirées

*Phrase ajoutée, sous condition de fait.*

> ⚠ **`J` de ces journées tombent entre juin et septembre**, la fenêtre sur
> laquelle le coefficient de couplage air–eau `m` est estimé. Le coefficient
> repose donc sur un échantillon estival réduit à `n` jours. Si la règle de
> validité le rejette, la normalisation n'est pas appliquée et
> `T_norm = T` — l'écran le dit alors séparément (§2.3).

#### Journées retirées faute de densité calendaire

> **Dégradation déclarée — `K` journées non diagnosticables sur `N`
> (`P` %).**
> *Motif :* densité calendaire insuffisante (< 4 jours observés sur 7) —
> `K` journées.
> *Ce que cela retire :* la température moyenne hebdomadaire `Tmh` est une
> moyenne sur sept jours **calendaires**. Ces journées-là sont trop isolées
> pour qu'une telle moyenne ait un sens : leur fenêtre ne contient que `k`
> jours réellement observés. Elles ne reçoivent donc pas de température
> normalisée et sortent du pourcentage de dépassement.
> *Pourquoi c'est voulu :* avant le correctif 2, ces journées recevaient
> quand même une valeur, calculée sur des jours parfois distants de plusieurs
> mois. L'une d'elles reposait sur **une seule** journée observée. Ne rien
> afficher est ici plus juste qu'afficher un nombre.

#### Les deux motifs à la fois

> **Dégradation déclarée — `K` journées non diagnosticables sur `N`
> (`P` %).**
> *Répartition par motif :*
> · température d'air absente à cette date (station air) — `K1` journées ;
> · densité calendaire insuffisante (< 4 jours observés sur 7) — `K2`
> journées.
> *Ce que cela retire :* ces journées n'ont **pas** de température
> normalisée. Elles sortent du pourcentage de dépassement de seuil et du
> décompte des journées de vulnérabilité. Elles restent visibles dans le
> tableau de marquage, avec leur motif : elles ne disparaissent pas.

**Ce que le bloc ne dit jamais.** Il ne présente pas ces journées comme
« écartées par le contrôle qualité ». Le contrôle qualité les a **retenues** —
elles sont saines. Les confondre reviendrait à imputer à la sonde d'eau un
manque qui vient de la station d'air ou du calendrier, et à laisser croire à un
défaut de matériel là où il n'y en a pas.


---

## 2. La règle de validité

Elle s'applique à **`m_estival` et à `m_saisonnier` avec le même critère**
(D21), et **par espèce** pour `m_saisonnier` (D28) : chaque espèce produit sa
propre fenêtre de reproduction, donc sa propre pente, donc sa propre
`Tmh_norm_fraie`.

### 2.1 Les trois conditions, en conjonction

Une pente est **valide** si les trois sont réunies :

| # | Condition | Seuil | Provenance |
|---|---|---|---|
| 1 | **significativité** — l'IC à 95 % de la pente, avec écarts-types robustes à l'autocorrélation (Newey-West), **exclut zéro** | *aucun seuil* | **convention statistique**. Le niveau de 95 % est celui de tout intervalle de confiance ; le noyau de Bartlett et le décalage `L = ⌊4 (n/100)^(2/9)⌋` sont la règle usuelle de la littérature |
| 2 | **domaine** — la pente est dans `[0 ; 1,2]` | `[0 ; 1,2]` | **paramètre exposé**, défaut repris de la règle déjà écrite dans V4.5 pour le seul coefficient saisonnier (`core.py:258`). D21 l'étend à l'estival |

*Il n'y a plus de troisième condition. La condition d'effectif `n ≥ n_min`,
qui figurait ici en étape 4, est **retirée** — voir 2.2.*

**Pourquoi la significativité et non la largeur de l'IC.** Mesuré : la
demi-largeur médiane vaut 0,044 et le maximum 0,126. Tout seuil de largeur
au-dessus de 0,13 n'écarte rien ; tout seuil qui attrape le point aberrant du
corpus en écarte 18 sur 31. La largeur ne sépare pas. La significativité, si :
un seul point a un IC contenant zéro, et le suivant en est huit fois plus
loin.

### 2.2 Pourquoi la condition d'effectif est retirée

**Amendement d'étape 6.** L'étape 4 posait une troisième condition,
`n ≥ n_min`, avec `n_min = 60`. Elle est retirée. Deux raisons, l'une de
principe, l'autre de mesure.

**De principe : la dérivation exige un corpus multi-points, ce que D41
interdit.** La procédure écrite en étape 4 était celle-ci :

> Pour chaque point dont la pente est significative sur sa chronique complète,
> la pente est ré-estimée sur des **fenêtres contiguës** de longueur `n'`
> croissante. On mesure la part des fenêtres qui concluent encore
> « significatif ». `n_min` est le plus petit `n'` pour lequel cette part
> atteint **95 %**.

« Pour chaque point », puis « la part des fenêtres » : cette part est calculée
en mettant en commun les fenêtres de **tous les points du corpus**. Sur les 31
points, elle donnait 73,5 % à `n' = 10`, 85,1 % à 20, 91,0 % à 30, 94,5 % à
50, 96,0 % à 60 — d'où `n_min = 60`.

**Or l'application traite une sonde à la fois (D41).** Sur une seule
chronique, cette procédure ne s'exécute pas : la « part des fenêtres qui
concluent significatif », mesurée sur un point unique dont on sait déjà que la
pente est significative, n'est pas une propriété de l'effectif — c'est une
propriété de ce point. La valeur de 60 n'était donc pas « dérivée du jeu
traité » comme l'affirmait le tableau de la §3 : elle était dérivée du
**corpus de développement**. L'y laisser revenait à figer un nombre de bassin
sous l'apparence d'une dérivation — ce que **D15** et **D41** interdisent
l'un et l'autre.

**De mesure : la condition 1 connaît déjà `n`, et la condition 3 la
contredit.** L'écart-type de Newey-West croît quand `n` décroît, l'IC à 95 %
s'élargit, et une pente estimée sur peu de jours cesse d'elle-même d'être
significative. Le mécanisme existe et il fonctionne : `BLE3-0`, `n = 7`, sort
par la condition 1 avec `t = 0,22`.

Les cinq estimations que la condition d'effectif écartait **en plus** de la
condition 1 sont celles-ci (`m_saisonnier`, ombre commun) :

| Point | `n` | pente | `t` de Newey-West |
|---|---|---|---|
| `GRO9-1` | 14 | 0,293 | **6,09** |
| `ABI3-6` | 23 | 0,098 | **4,21** |
| `LGV11-8` | 35 | 0,334 | **5,16** |
| `HRI7-7` | 36 | 0,289 | **5,01** |
| `FLU8-4` | 51 | 0,146 | **9,06** |

Aucune n'est marginale : le plus faible `t` vaut 4,21, soit plus du double du
seuil de 1,96, sur des écarts-types qui ont **déjà** payé le prix du petit
effectif. La condition 3 ne rattrapait donc pas une faiblesse statistique que
la condition 1 aurait laissée passer : elle **écrasait le verdict de la
condition 1** au nom d'un effectif calibré ailleurs.

**Effet du retrait sur le corpus.** Sur `m_estival`, aucun : le seul point que
l'effectif écartait, `BIE35-5__NA`, l'est déjà par les deux autres conditions.
Sur `m_saisonnier`, les estimations rejetées passent de **7 sur 33 à 2 sur
33** (`BLE3-0` et `La Moselle à Hielle`, toutes deux par la significativité).

*Le retrait n'est pas gratuit et n'est pas présenté comme tel : cinq
estimations qui sortaient entrent. L'argument n'est pas qu'elles seraient sans
importance — c'est que rien dans la statistique ne justifie de les sortir, et
que le nombre qui les sortait ne peut pas se calculer sur une sonde seule.*

### 2.3 Ce qui se passe en aval d'un rejet

**La normalisation n'est pas refusée : le coefficient est mis à zéro.**

```
m_retenu = m estimé      si la pente est valide
m_retenu = 0,0           sinon        →   T_norm = T
```

**Pourquoi ce comportement et pas le refus.** Les deux existent dans le
registre ; un seul est possible sans modifier V4.5 :

| Comportement | Possible sans modifier V4.5 ? |
|---|---|
| `m = 0` | **oui** — `core.analyse_vulnerabilite(df, m, …)` reçoit `m` en argument (`core.py:174`). Lui passer `0.0` donne `Tmh_norm = Tmh` et `Tmax_norm = T_eau_max` (`core.py:177-178`), sans toucher une ligne |
| refus (ne pas créer les colonnes) | **non** — `analyse_vulnerabilite` crée toujours `Tmh_norm` et s'en sert immédiatement pour `pct_chr` et `n_aigu` (`core.py:182-186`). Il faudrait une branche qui n'existe pas |

Les consommateurs en aval sont d'ailleurs **déjà écrits pour tolérer
l'absence** de la colonne — `core.py:613-614`, `core.py:992`, `figures.py:71`,
`figures.py:88` retombent tous sur `Tmh` et `T_eau_max`. Or c'est exactement
ce que produit `m = 0`. **Les deux comportements coïncident numériquement**,
et un seul est atteignable sans modification.

**Ce que l'écran affiche en cas de rejet :**

> ⚠ **Normalisation climatique non appliquée sur ce point.** Le coefficient de
> couplage air–eau n'est pas distinguable de zéro *(ou : sort du domaine
> `[0 ; 1,2]`)*. Les températures
> normalisées sont donc égales aux températures brutes : `T_norm = T`.
> *Conséquence :* les pourcentages de dépassement de seuil portent sur la
> chronique **non corrigée** de l'anomalie climatique. Ils décrivent l'année
> observée, pas une année standard.

Sur `m_saisonnier`, le rejet **ne déclenche pas** le repli sur `m_estival`
existant (`core.py:251`, `core.py:258`) : la règle de validité s'applique
d'abord ; si la pente saisonnière est rejetée, `m_saisonnier = 0`. *Alternative
fermée si cette lecture ne convient pas : voir §5 du rapport d'étape.*

### 2.4 Le texte de dégradation déclarée du rejet

*Rédigé à l'étape 11, dans l'idiome du §1.5. **Non affiché** : D48 diffère
tout l'affichage à l'étape 14.*

Le §2.3 dit ce que la chaîne fait d'un rejet — `m = 0`, donc `T_norm = T`. Il
reste à dire ce que l'écran en dit, et **ce que cela interdit de conclure**.
C'est le point qui compte : une température brute présentée sans avertissement
se lit comme une température normalisée.

#### Rejet du coefficient estival

> **Dégradation déclarée — le couplage air-eau n'a pas pu être établi sur
> cette chronique.**
> *Ce qui a été tenté :* la pente reliant la température de l'eau à celle de
> l'air, estimée sur les `n` journées de juin à septembre.
> *Ce qui a été obtenu :* pente `m` = `p`, intervalle de confiance à 95 %
> `[b ; h]`, `t` = `t`. *Critère qui rejette :* `C`.
> *Ce que l'écran publie donc :* les **températures brutes**. `T_norm = T`.
> Le coefficient est mis à zéro, la normalisation n'est pas appliquée.
> *Ce que cela n'autorise pas à conclure :* les pourcentages de dépassement
> de seuil et les journées de vulnérabilité décrivent **l'année observée**,
> avec la météo qu'elle a eue — pas une année standard. Deux points ainsi
> traités ne sont **pas comparables entre eux**, ni le même point d'une année
> sur l'autre. Un été chaud produira des dépassements sans qu'on puisse dire
> s'ils viennent du cours d'eau ou du climat de cette année-là.
> *Ce que cela n'autorise pas non plus :* conclure que ce cours d'eau est
> **insensible** à l'air. Un couplage non distinguable de zéro sur cette
> chronique n'est pas un couplage nul ; c'est un couplage que **ces données**
> ne permettent pas d'établir. La cause peut être une chronique trop courte,
> une station d'air trop éloignée, ou une alimentation par nappe qui
> découplerait réellement l'eau de l'air — l'écran ne les distingue pas.

#### Rejet du coefficient saisonnier, pour une espèce

> **Dégradation déclarée — couplage non établi sur la fenêtre de
> reproduction de `espèce`.**
> *Fenêtre :* mois `M`, `n` journées. *Obtenu :* `m` = `p`, `t` = `t`.
> *Critère qui rejette :* `C`.
> *Ce que l'écran publie donc :* pour cette espèce, les températures de la
> fenêtre de reproduction sont les **températures brutes**.
> *Ce que cela n'autorise pas à conclure :* le diagnostic de reproduction de
> cette espèce porte sur l'année observée. Les autres espèces du même point
> peuvent avoir, elles, un couplage établi : **le statut est par espèce**, et
> l'écran l'affiche par espèce.

#### Ce que le texte ne dit jamais

Il ne dit pas que la normalisation a « échoué », ni que la chronique est
« mauvaise ». Il dit qu'une **relation n'a pas pu être établie** et il en tire
les conséquences sur la lecture. La chronique peut être excellente et la
relation indistincte : ce sont deux choses.

Il ne présente pas non plus `m = 0` comme un résultat. Zéro n'est pas la
valeur estimée du couplage — c'est la valeur **imposée** faute d'en avoir une.
L'écran affiche la pente estimée à côté, précisément pour que la différence
soit lisible.

---

## 3. Provenance de chaque valeur numérique

Aucune valeur codée en dur propre à un bassin.

**D41 — aucune valeur de ce tableau ne peut dépendre d'un corpus
multi-points.** L'application traite **une sonde à la fois** : une valeur qui
ne se calcule qu'en mettant plusieurs points en commun n'est pas calculable au
moment où elle sert. Le critère a été appliqué ligne à ligne au tableau
ci-dessous. Il a fait sortir `n_min` (§2.2), et rien d'autre.

Ce qui reste se calcule sur ce dont l'application dispose au moment du
traitement :

- les **conventions statistiques** (`1,4826`, le niveau de `95 %`, le décalage
  `L`) ne dépendent d'aucune donnée ;
- les **défauts exposés** (`k`, `plancher_dispersion`, `min_jours_groupe`,
  `min_jours_episode`, `hors_eau_mois`, `q_ampl`, `[0 ; 1,2]`) sont des
  paramètres, non des mesures : leur valeur par défaut vient soit d'une
  convention, soit du code de V4.5 lui-même, jamais d'un corpus ;
- la seule valeur **dérivée** qui subsiste est le seuil d'amplitude d'air en
  °C, obtenu comme décile `q_ampl` de la série d'air **du jeu traité**. Un jeu
  porte une station d'air ; la dérivation s'exécute donc à l'identique sur une
  sonde seule. *(Sur le corpus, elle retrouve 5,00 à 6,62 °C selon le jeu.)*

| Valeur | Où | Provenance |
|---|---|---|
| `1,4826` | facteur du MAD | **convention statistique** |
| `k = 3,0` | seuil du détecteur | **paramètre exposé**, défaut conventionnel (trois écarts-types) |
| `plancher_dispersion = 0,05 °C` | garde-fou du MAD | **paramètre exposé**, défaut égal au `plateau_ecart_type_min` déjà présent (`config.py:89`) |
| `min_jours_groupe = 10` | garde-fou du mois | **paramètre exposé**, défaut conventionnel |
| `min_jours_episode = 1` | regroupement | **paramètre exposé**, défaut **neutre** (aucun épisode écarté sur sa seule longueur). Amendé en étape 6 : le défaut de 3, importé de `thermie_points`, excluait 100 % des épisodes de la marche 2 |
| `q_ampl = 0,10` | garde-fou d'amplitude d'air | **paramètre exposé** ; la valeur en °C qui en découle est **dérivée du jeu traité** |
| `hors_eau_mois = (1,…,12)` | fenêtre d'examen | **paramètre exposé** ; l'année entière depuis l'étape 20 (D105). Valait `(6,7,8,9)` |
| `0` | frontière du second membre | **ni convention ni paramètre** : la médiane du groupe est la frontière du phénomène. Aucune valeur n'est calibrée (D111) |
| `95 %` | niveau de l'IC | **convention statistique** |
| `L = ⌊4 (n/100)^(2/9)⌋` | décalage Newey-West | **convention statistique** |
| `[0 ; 1,2]` | domaine de la pente | **paramètre exposé**, défaut déjà dans V4.5 (`core.py:258`) |
| ~~`n_min`~~ | ~~effectif minimal~~ | **retirée en étape 6** — sa dérivation exigeait un corpus multi-points, ce que **D41** interdit. Voir 2.2 |

**Deux valeurs de `thermie_points` sont explicitement écartées** : le seuil
d'amplitude d'air de 6 °C (remplacé par une dérivation, qui le retrouve à
5,0-6,6 °C selon le jeu) et le plancher `R_ampl > 0,67`, qui se calibre sur
des **négatifs terrain** — une donnée d'étude que ce harnais ne possède pas et
ne doit pas posséder.

---

## 4. Fichiers de `app/` touchés, et effet sur la référence

| Fichier | Ce qui change | Effet sur les artefacts de `tests/reference/` |
|---|---|---|
| `app/thermie_debits/config.py` | nouveaux champs de `QCConfig` (`k`, `plancher_dispersion`, `min_jours_groupe`, `min_jours_episode`, `q_ampl`) et de la règle de validité (`m_domaine`, `m_niveau_ic`) | **`10_parametres.json` bougera** : nouveaux champs. Aucun autre artefact |
| `app/thermie_debits/qc.py` | remplacement du détecteur `hors_eau` (`qc.py:60-82`) par les deux marches | **`02_effectifs.csv`, `03_journees_ecartees.csv` bougeront** — nouveaux motifs, nouveaux effectifs. Sur les 31 points : `LA PLAINE A RAON-SUR-PLAINE` −16 journées, `BIE6-8` −17, `BIE46-5` −5, 28 autres points −3 ou moins |
| `app/thermie_debits/io_data.py` | lecture de `TN` et `TX` (`io_data.py:432`, `usecols` ; `io_data.py:484-491`, construction de `out`) | **`00_format_detecte.json` et `01_colonnes_retenues.json` bougeront** — deux colonnes de plus. `05_anomalies.csv` inchangé |
| `app/thermie_debits/core.py` | règle de validité avant `analyse_vulnerabilite` ; extension au coefficient estival | **`06_coefficients.csv` bougera** — colonnes de validité. **`07_t_norm.csv` bougera sur les points rejetés** |
| `app/app.py` | widgets des nouveaux paramètres, **défauts dérivés du dataclass** (correctif 7) ; les trois blocs d'écran du §1.4 | aucun artefact — l'interface n'est pas rejouée par le harnais |
| `app/thermie_debits/redaction.py` | verdict de validité dans la fiche | **`08_scores.csv`** peut bouger sur les points rejetés (témoin, hors périmètre) |

**Artefacts qui ne doivent PAS bouger** : `04_normales.csv` (les normales ne
dépendent ni du détecteur ni de la validité) et `05_anomalies.csv`. Toute
divergence sur ces deux-là signale une régression.

---

## 5. Points du corpus dont le comportement changera

**Recalculée à l'étape 8 (D50).** La première version de cette table datait
de l'étape 4, donc d'avant les correctifs 2 (index calendaire), 5 (jointure
gauche) et 8 (lissage sur l'eau complète). Elle a été refaite sur la chaîne
telle qu'elle est aujourd'hui.

Au réglage que cette spécification retient : **union des deux marches** —
socle relatif `E_moy_rel > k` à `k = 3,0`, plus la conjonction
`R_ampl_rel > k` **ET** `E_max_rel > k` là où `TN` et `TX` sont disponibles —
par rapport au régime en service (D25).

> **Le marquage du détecteur n'a pas bougé, et c'était prévisible.** Il repose
> sur `T_eau_max`, `T_air`, `TN`, `TX` et `T_eau_min`, qu'aucun correctif posé
> n'a touchés. Le socle marque **68 jours**, exactement comme à l'étape 4. Ni
> le choix de `k` ni la mesure d'aveuglement n'étaient donc à refaire.
>
> **Les écarts non plus, à un point près.** Sur 30 des 31 points, `Δm` et
> `ΔTmh_norm` sont identiques à la sixième décimale. `Δm` l'est par
> construction : `m` régresse l'eau **brute** sur l'air **brut** (D42), et les
> correctifs 2 et 8 ne touchent que `Tmh`. Le seul point qui varie est
> `BIE40-3`, dont `Δm` passe de −0,001311 à −0,000910 — et ce n'est pas un
> effet des correctifs : c'est que l'étape 4 mesurait le **socle seul**, là où
> cette table mesure **l'union des deux marches**, et que la marche 2 ajoute
> une journée sur ce point.

| Point | Journées écartées | Δ retenues | `m` obtenu | **Δ `m`** | **Δ `Tmh_norm` médiane** | **Δ `Tmh_norm` p95** |
|---|---|---|---|---|---|---|
| `LA PLAINE A RAON-SUR-PLAINE` | 16 | −16 | 0,3348 | **+0,0420** | −0,0424 | **−1,0501** |
| `BIE6-8` | 17 | −8 | 0,2423 | **+0,0151** | +0,0053 | **−0,8371** |
| `BIE46-5` | 5 | −5 | 0,5082 | +0,0052 | −0,0453 | −0,0717 |
| `LGV11-8` | 2 | −2 | 0,3417 | +0,0047 | +0,0213 | +0,0118 |
| `BIE27-9` | 3 | −3 | 0,5504 | +0,0043 | −0,0225 | −0,0008 |
| `BIE31-4` | 3 | −3 | 0,5492 | +0,0037 | −0,0337 | −0,0145 |
| *25 autres points* | 0 à 2 | ≥ −2 | — | **< 0,004** | **< 0,05** | **< 0,05** |

Sur les 31 points, **médiane de |Δ`m`| = 0,0009**, maximum **0,0420**.
**Deux points seulement bougent de façon lisible.**

*(La médiane valait 0,0010 dans la version de l'étape 4 ; l'écart tient à la
seule journée que la marche 2 ajoute sur `BIE40-3`.)*

**Ce que le détecteur ne marque pas et que le régime en service écarte.**
Six journées, toutes sur `BIE40-3`, toutes en juillet — l'étape 4 les
signalait sans les nommer :

| Date | `T_eau_max − T_air` | `E_moy_rel` | `R_ampl_rel` | `E_max_rel` | Marche 2 la rattrape ? |
|---|---|---|---|---|---|
| 2015-07-08 | 12,42 °C | 2,676 | **7,514** | **3,090** | **oui** |
| 2015-07-09 | 10,57 °C | 2,192 | 3,837 | 1,961 | non |
| 2015-07-28 | 11,74 °C | 2,499 | **8,512** | 2,773 | non |
| 2015-07-30 | 13,10 °C | 2,855 | 4,425 | 2,540 | non |
| 2023-07-20 | 10,01 °C | 2,045 | 2,988 | 1,697 | non |
| 2023-07-22 | 10,91 °C | 2,280 | 3,314 | 1,771 | non |

Deux choses se lisent dans ce tableau.

**Aucune de ces journées n'est loin du seuil.** Leur `E_moy` relativisé va de
**2,04 à 2,86 MAD\***, pour un seuil à 3,0 : le socle les manque de peu, non
par aveuglement mais parce qu'elles ressemblent aux autres journées chaudes de
juillet de ce point. C'est le comportement attendu d'un critère relatif — et
c'est pourquoi la marche 2 existe.

**La marche 2 en rattrape une, et une seule.** Le 8 juillet 2015 franchit les
deux membres de la conjonction. Le 28 juillet a pourtant un `R_ampl` très
élevé (8,51) : c'est le second membre, le niveau `E_max`, qui le retient à
2,77. La conjonction fait ici exactement ce pour quoi elle a été choisie —
exiger **deux signatures différentes**, une forme et un niveau, et ne pas se
contenter de l'une des deux.

*Les six journées sont dans `out/etape8/C2_journees_perdues_vs_service.csv`.*

**Un point change de statut** : `BLE3-0` voit sa normalisation refusée par la
règle de validité — `m = −0,010`, IC95 contenant zéro, pente hors `[0 ; 1,2]`.
Son `m` retenu passe de `−0,010` à `0,0`, donc `Tmh_norm` passe de
`Tmh + 0,010 × Delta_TMm_liss` à `Tmh`. L'écart est de l'ordre de 0,03 °C —
négligeable en valeur, décisif en signification : la chaîne cessait
d'*ajouter* l'anomalie climatique au lieu de la retrancher.

**Sur `m_saisonnier`, deux estimations sur 33 sortent** : `BLE3-0` et
`La Moselle à Hielle`, toutes deux par la significativité.

*Amendé en étape 6.* L'étape 4 en annonçait **sept** : les cinq autres
(`ABI3-6`, `FLU8-4`, `GRO9-1`, `HRI7-7`, `LGV11-8`) sortaient par la condition
d'effectif, retirée depuis (§2.2). Leurs `t` de Newey-West vont de 4,21 à
9,06 : la significativité les retient toutes.

**`BIE35-5__NA` reste sans indicateur** : sa chronique s'arrête le 24 mai et
ne couvre aucun jour de juin à septembre. Ni le détecteur ni la règle de
validité n'y changent quoi que ce soit.
