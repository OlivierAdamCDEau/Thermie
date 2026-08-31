# METHODO.md — carnet de méthode

Cumulatif : jamais réécrit, seulement complété. Une section par étape.

---

## Étape 1 — corpus et harnais

Aucune ligne de code applicatif n'a été modifiée. `app/` n'a été ni lu pour
exécution, ni écrit. `ref/v4_5/` et `ref/thermie_points/` n'ont reçu aucune
écriture.

### 1.1 Ce qui n'était pas là où on l'attendait

**`ref/thermie_points/` n'est pas décompressé.** Le dossier ne contient que
`thermie_points.zip` (271 Mo) et un `desktop.ini`. D9 interdit de ré-extraire
les archives — mais il n'y a ici aucun dossier extrait à préserver. Plutôt que
de trancher à la place de l'architecte, le harnais **lit l'archive en place**
avec `zipfile`, sans écrire un seul octet dans `ref/`. C'est plus strict que
D9 : ni extraction, ni horodatage modifié. Voir
`tests/reference/restitution_documentaire.py`, classe `Archive`.

**`app_V4_5.zip` n'existe pas.** `app/` et `ref/v4_5/` ne viennent pas d'une
archive : ce sont deux clones git du même dépôt, au même commit `83ff67e`
(« V4.5 message erreur amélioré »). La comparaison SHA-256 exigée par le
pré-contrôle a donc été faite directement entre les deux arborescences.

**L'archive contient une TROISIÈME copie de V4.5**, sous
`data/ref_V4_5/` — celle contre laquelle le projet clos a écrit son registre
de correctifs. Elle diverge de `ref/v4_5/` sur six fichiers. La divergence a
été identifiée exactement : c'est le commit `bb70055` (« V4.5 barbeau »), soit
`ref/v4_5/` moins un commit. Signalée, non résolue (D9). Conséquence directe
sur la tâche D.1 : **toute référence `fichier:ligne` du registre vise cet
instantané-là**, pas `ref/v4_5/`. Le harnais vérifie chacune et dit où le même
code se trouve aujourd'hui.

### 1.2 Ce que j'ai corrigé dans mon propre code, et pourquoi

Quatre corrections ont porté sur des relevés que je croyais justes.

**Le parseur de dates.** L'inventaire utilisait d'abord un `pd.to_datetime`
générique. Il lisait `19540101` comme un compte de nanosecondes — d'où une
période « 1970-01-01 → 1970-01-01 » sur le fichier d'air de
`jeu_exemples_v45` — et `10/05/2021` en ordre américain, ce qui perdait 60 %
des lignes de trois chroniques d'eau. Un inventaire doit dire **ce que l'outil
lit**, y compris ses erreurs, jamais ce qu'un tiers croirait lire. L'inventaire
appelle désormais `io_data._parse_dates_sonde` et `io_data._parse_dates_air`
de `ref/v4_5/`, et reproduit à la lettre la règle de recomposition de la
colonne d'heure (`io_data.py:83-90`).

**Le pas de mesure.** Je ne relevais que le pas médian et le pas modal. Un pas
modal unique masque les changements de cadence en cours de chronique : la
matrice de couverture déclarait « 15 min » et « 30 min » NON COUVERTS alors
que `jeu_bienne` porte 8 031 intervalles de quart d'heure (BIE40-3), 5 224
(BIE35-5__NA) et plus de 13 000 intervalles de demi-heure sur huit fichiers.
**Un « non couvert » faux est plus nuisible qu'une matrice absente** : il fait
croire à un trou et invite à fabriquer un jeu de test pour le combler. La
colonne `pas_observes` porte désormais la distribution des intervalles, et la
matrice se lit sur les intervalles réellement présents.

**Le libellé du séparateur.** L'écriture CSV remplace le séparateur `;` par
une virgule à l'intérieur d'une cellule, pour que le diff reste ligne à ligne.
Le libellé `separateur ';'` devenait donc `separateur ','` — il disait
l'inverse de la vérité. Les libellés sont maintenant écrits en toutes lettres.

**La confrontation à `corpus.csv`.** L'égalité de chaînes comptait
« xlsx (feuille ValInstantanees) » et « xlsx ; feuille(s) : ValInstantanees »
comme un écart, et « à vérifier » comme une erreur alors que la consigne de
`corpus.csv` autorise explicitement cette réponse. Quatre statuts distincts —
*conforme*, *précisé*, *ÉCART*, *texte libre* — et une comparaison sur les mots
significatifs ont ramené 24 pseudo-écarts à 7 écarts réels.

Trois autres défauts de mon code de matrice, plus mécaniques : `str.contains`
interprétait `|` comme une alternative de motif ; la « colonne d'heure non
reconnue » comptait la colonne de date elle-même quand elle s'appelait « Date
et heure » ; et « point sans donnée exploitable » manquait les points où la
chaîne échoue, puisqu'un échec ne produit aucun fichier d'effectifs.

### 1.3 La découverte qui a fait reconstruire la référence

La chaîne ne produit pas une, ni deux, mais **six séries journalières de
température corrigée, relevant de deux familles de formules différentes** :

| Famille | Formule | Où |
|---|---|---|
| normalisation | `T − m × Delta_TMm_liss` (anomalie **lissée**, coefficient estimé) | `core.py:177`, `core.py:178`, `core.py:347` |
| compensation | `T − Delta_TMm` (anomalie **brute**, **aucun** coefficient) | `indicateurs.py:88-90` |

Les deux sont affichées, et le vocabulaire ne les distingue pas :
`figures.py:91` étiquette `Tmh_norm` « eau COMPENSÉE » tandis que la seconde
famille s'appelle « Tmax comp » dans le tableau mensuel. La première référence
que j'avais figée ne portait que la première famille. `07_t_norm.csv` a été
reconstruit avec les six séries, plus trois colonnes : `famille`,
`type_anomalie` et `source_valeur`. Cette dernière était nécessaire : la série
journalière de la seconde famille vit dans une variable **locale** de
`indicateurs.calcul_indicateurs`, qui ne retourne que des agrégats mensuels —
le harnais applique donc la formule citée et le déclare, plutôt que de laisser
croire que la valeur sort de V4.5.

### 1.4 Ce qui a été vu et volontairement pas touché

| Constat | Emplacement | Déjà au registre ? |
|---|---|---|
| Une journée écartée par deux détecteurs ne garde que le motif du premier ; la contribution du second est perdue sans trace | `qc.py:32-36` | non |
| Les mesures à date ou température non lisible sont supprimées sans compte ni motif | `io_data.py:98` | oui — I7 |
| La colonne d'heure est reconnue par `startswith`, la colonne de date par inclusion. `chmes_heure` de BLE3-0 n'est pas reconnue : ses 2 952 mesures sont toutes datées à minuit, d'où 2 828 horodatages en double. Les agrégats **journaliers** restent justes — `groupby("date")` regroupe bien les 24 mesures du jour — mais la structure infra-journalière disparaît, donc l'amplitude nycthémérale et les extrêmes horodatés de `indicateurs.py` | `io_data.py:79-82` | oui — C2 / I13 |
| `n_mesures` est calculé puis jamais relu : aucun critère de complétude de journée | `io_data.py:104` | oui — I11 |
| La normale est agrégée par `dayofyear` puis relue par (jour, mois) via l'an 2000, bissextile | `io_data.py:508`, `531`, `541-549` | oui — B1 / I3 |
| `TN` et `TX` n'apparaissent nulle part dans le code de V4.5 | tout `ref/v4_5/` | oui — I14 |

### 1.5 Déterminisme

Le harnais a été écrit dès le départ avec tri explicite, flottants à six
décimales fixes, `sort_keys` sur le JSON, et substitution des chemins absolus
par `<RACINE>` dans les journaux.

**Une source de non-déterminisme a dû être neutralisée**, et c'est le
`check_reference.py` lui-même qui l'a trouvée. Les traces d'erreur figées au
titre de D7 traversent d'abord `build_reference.py` avant d'entrer dans
`ref/v4_5/`, et elles en portaient le **numéro de ligne**. Modifier une ligne
du harnais — fût-ce un commentaire — décalait ce numéro et faisait diverger la
référence, alors que le comportement de V4.5 n'avait pas bougé d'un iota. Une
référence qui dépend de l'outil qui l'observe ne référence rien. Le numéro de
ligne du harnais est désormais masqué dans les traces
(`build_reference._nettoyer`) ; **les numéros de ligne dans `ref/v4_5/` sont
conservés**, ce sont eux qui portent l'information. Neutralisé dans le
harnais, jamais dans `app/` ni `ref/`.

**Une écriture illégitime dans `ref/` a aussi été trouvée et supprimée.**
Importer `thermie_debits` y fait écrire un `__pycache__/*.pyc`. C'est une
écriture dans un dossier déclaré en lecture seule, et elle est *silencieuse* :
le `.gitignore` du dépôt la masque à `git status`, si bien que le contrôle
habituel ne la voit pas. Le harnais pose maintenant
`sys.dont_write_bytecode = True` avant tout import (`_commun.py`,
`inventaire_corpus.py`), et le `__pycache__` déjà créé a été supprimé pour
rendre `ref/` à son état d'origine. Vérifié après coup : plus aucun `.pyc`
sous `ref/`.

Deux autres points ont demandé de l'attention :

- **la clé de tri** doit être totale. Une colonne qui mélange `None`, des
  nombres et des chaînes ne se trie pas de façon reproductible ; `_cle` range
  d'abord par type, puis par valeur ;
- **`date.today()`** figure en `livrables.py:185` et `livrables.py:452`. Le
  harnais n'appelle pas ces constructeurs de livrables. C'est noté ici pour
  que personne ne les appelle plus tard sans le savoir.

Le volet climatique est désactivé dans le harnais : il ne produit que des
figures (`orchestrator.py:283-286`) et aucune valeur de `Resultats` n'en
dépend.

### 1.6 Ce que l'étape 1 laisse ouvert

Les paramètres du rejeu sont ceux de `ref/v4_5/run_cli.py:16-24`, appliqués
uniformément. Les classeurs déjà présents dans `tests/reference/<jeu>/` avant
cette étape ont été produits avec des paramètres **différents d'un jeu à
l'autre** et non enregistrés. Voir le rapport d'étape, §6.

---

## Étape 2 — alignement du harnais, puis mesure

Aucune ligne de code applicatif n'a été modifiée. `app/` et `ref/` n'ont reçu
aucune écriture.

### 2.1 La référence de l'étape 1 ne figeait pas la version en service

Elle figeait `run_cli.py` + `QCConfig()` par défaut. L'application Streamlit
construit son contrôle qualité autrement, et deux widgets seulement en sont
la cause :

| Ligne | Ce qu'elle fait | Ce que dit le dataclass |
|---|---|---|
| `app.py:162-163` | `st.slider(..., 1.0, 15.0, **10.0**, 0.5)` — défaut **littéral** | `config.py:81` : `hors_eau_ecart_seuil = 4.0` |
| `app.py:166` | `st.checkbox(..., **False**)` — défaut **littéral** | `config.py:84` : `hors_eau_exclut_saison = True` |

Les douze autres widgets passent `qc.<champ>` comme défaut et reproduisent le
dataclass. Le détecteur de mise hors d'eau **n'est donc pas coupé** : il est
actif des deux côtés, mais cherche un écart de 10 °C au lieu de 4 °C et
n'exclut pas la saison. Il ne tire plus que 22 fois sur 23 816 points-jours,
contre 8 255.

**La valeur documentée dans `config.py` n'est jamais celle qui s'applique par
défaut dans l'application.** C'est la question ouverte n° 1 du rapport
d'étape.

### 2.2 Ce que le réalignement déplace

| | référence seconde (CLI) | référence qui fait foi (application) |
|---|---|---|
| points produisant un indicateur | 18 / 32 | 31 / 32 |
| journées écartées par le contrôle qualité | 8 565 | 91 |
| journées retenues | 34 376 | 67 101 |

Les cinquante valeurs lues dans les cinq classeurs livrables sont retrouvées :
vingt-cinq grandeurs entières au jour et à l'unité près, vingt-cinq grandeurs
flottantes à l'arrondi du livrable (écart maximal 4,7 × 10⁻⁵ sur `m`). Aucun
écart n'a été arrondi pour faire coïncider.

L'ancienne référence est conservée en `tests/reference_cli/` : elle documente
le comportement détecteur allumé, objet du correctif principal.

### 2.3 Ce que j'ai corrigé dans mon propre code

- `fichiers_a_manifester()` hachait les classeurs `.xlsx` et `.docx`. Un
  artefact est désormais reconnu au motif `^\d{2}_....(csv|json|txt)$` dans un
  dossier de jeu. Les binaires restent dans le dossier, hors du manifeste et
  hors du diff (D11).
- `check_reference.comparer()` diffait les fichiers entiers, donc comptait dans
  le verdict des lignes que le harnais calcule lui-même. Elles sont désormais
  scindées sur la colonne `sortie_v45` et sorties du verdict (D13).
- Le tableau de comparaison des deux chemins annonçait 27 écarts, dont les
  chemins de fichiers et douze champs valant `None` des deux côtés sous deux
  formulations. Deux catégories ajoutées ; il en reste 4.
- La matrice opposait `pas_eau` jeu par jeu, alors que cette colonne porte la
  **même phrase sur les six lignes** de `corpus.csv`. Cinq écarts fabriqués à
  partir d'un seul énoncé.

### 2.4 Deux résultats qui contredisent ce qui était attendu

**La réserve C3 ne se reproduit pas.** `journees_ecartees_qc` est juste : sur
les deux jeux où le contrôle qualité écarte quelque chose, la somme des lignes
annuelles retombe exactement sur `annee=-1`, vérifié ligne à ligne contre
`03_journees_ecartees.csv`. L'impression vient de la forme du fichier : quatre
jeux sur six ont la colonne à zéro partout, et sur `jeu_02` les quatre
premières lignes sont `-1 → 245` puis trois années à zéro.

**Le mécanisme d'aveuglement du critère relatif ne s'observe pas.** La
corrélation entre la médiane propre d'un point et le fait qu'il soit perdu
vaut +0,13 à q95, +0,03 à q99 et **−0,17** à q99,5 — de signe contraire à la
prédiction. La raison est vérifiable : aucun point du corpus n'a de médiane
propre dans la zone suspecte (la plus haute, `LIZ13-5`, vaut +2,80 °C contre
un seuil de 4 °C). Ce qui gouverne la perte est la longueur de la chronique,
pas le décalage de la médiane.

### 2.5 Ce qui reste noté et non touché

`BLE3-0` porte `m = −0,010` avec `R² = 0,002` : la normalisation y **ajoute**
l'anomalie d'air au lieu de la retrancher, et la chaîne va au bout. La borne
`[0 ; 1,2]` qui protège `m_saisonnier` (`core.py:258`) n'a pas d'équivalent
pour `m_estival`, et le code ne dit pas pourquoi.

Le rapport d'étape est `docs/etape2_rapport.md` (D19).

---

## Étape 3 — spécifier le détecteur par la mesure

Aucune ligne de code applicatif n'a été modifiée. `app/`, `ref/` et la
référence `tests/reference/` sont inchangés — `MANIFEST.sha256` concorde sur
ses 66 artefacts.

### 3.1 Une règle de décision écrite avant les chiffres

La question — le mécanisme d'aveuglement existe-t-il ? — appelait un critère
posé d'avance, sans quoi le verdict se choisit après. Les trois issues et
leurs seuils sont écrits **en tête de `mesure_critere_b.py`**, dans le code
même qui produit les chiffres : ≥ +20 points de pourcentage sur l'effet
médiane à durée contrôlée pour conclure qu'il existe, < 10 points ou signe
contraire pour conclure qu'il n'existe pas, cellule sous 3 points ou étendue
des médianes sous 2 °C pour conclure que le corpus ne tranche pas.

Une précision a dû être ajoutée en cours de mesure, et elle n'affaiblit pas la
règle : **un seuil qui perd tout le monde, ou personne, ne porte aucun
contraste**. Les seuils dont le taux de perte global vaut 0 % ou dépasse 80 %
sont déclarés non informatifs. Le verdict se lit sur les quatre autres.

### 3.2 Trois mesures qui vont contre ce qu'on en attendait

**Le critère pleinement relatif est beaucoup plus sévère, pas moins aveugle.**
À k = 3 écarts-types robustes, il marque 68 jours quand le détecteur absolu en
marque 3 408. À k = 4 il perd 26 points sur 30. La raison est arithmétique :
le MAD* médian de l'écart vaut 2,8 °C, donc un jour à +4 °C absolu se situe à
environ 1,4 MAD* de l'habitude d'un point centré — le seuil de 4 °C de V4.5
est en réalité **plus permissif** que « trois écarts-types ».

**Le mécanisme d'aveuglement n'existe pas sur ce corpus.** À durée contrôlée,
la médiane propre d'un point corrèle à **+0,006** avec sa perte ; la durée
corrèle à **−0,402**. Les trois points aux médianes les plus hautes sont
conservés, trois des quatre aux médianes les plus basses sont perdus. C'est le
mécanisme exactement à l'envers.

**Le maximum d'air n'apporte pas de marge.** En degrés les deux marges sont
quasi identiques (+4,74 contre +4,79 °C) ; en unités de dispersion — la seule
unité comparable — `T_eau_max − TX` a **moins** de marge que `T_eau_max − TM`
sur **31 points sur 31**, parce que sa dispersion est plus grande (MAD* 3,59
contre 2,82 °C). Réserve à retenir : le projet clos oppose `E_max` à `E_min`,
pas à `E_moy` ; cette mesure ne contredit pas son argument, elle en mesure un
autre.

### 3.3 Ce que j'ai corrigé dans mon propre code

- `defauts_litteraux.py` comparait `espece_repere` à `None` sans le résoudre,
  et n'interprétait pas la valeur écrite « False → None ». Deux faux écarts
  sur quatre.
- `mesure_marche2.py` rapportait la part de TN manquante sur **toutes** les
  lignes du fichier d'air, décennies sans température comprises : elle
  mesurait le vide du fichier et non celui de TN. 91,6 % annoncés pour
  `jeu_04` alors que **zéro** jour porte TM sans TN.
- Le premier balayage des seuils de validité plaçait sept valeurs
  conventionnelles dont **quatre n'écartaient rien**. Rebalayé sur les déciles
  de la distribution observée.

### 3.4 Ce que la mesure établit sur la règle de validité

La demi-largeur d'IC à 95 % (Newey-West) a une médiane de **0,044** et un
maximum de **0,126** sur `m_estival`. Le repère de 0,15 du projet clos est
**au-dessus du maximum observé** : il n'écarterait rien.

`BLE3-0` — `m = −0,010`, `R² = 0,002` — a une demi-largeur de **0,044**,
c'est-à-dire **sous la médiane du corpus** : la pente la plus dépourvue de
sens est l'une des plus précisément estimées. Aucun seuil de précision ne le
sépare du reste sans écarter 18 points sur 31. Les deux critères qui
l'attrapent sont ceux qui existent déjà pour le seul coefficient saisonnier
(`core.py:258`) : `R² < 0,30` — 4 points sur 31 — et pente hors `[0 ; 1,2]` —
**1 seul point, lui**.

### 3.5 Le correctif 7, en chiffres

50 champs revus : 8 dérivés du dataclass, **19 littéraux**, 9 détectés sur le
fichier, 14 non exposés. Deux littéraux divergent aujourd'hui. **Dix-sept
coïncident — et c'est le risque** : un littéral qui coïncide ne se voit pas,
il diverge le jour où le dataclass change.

Trois d'entre eux sont d'une nature particulière, les **défauts par
position** : `contexte_piscicole` (`index=1`), `espece_repere` (`index=0`) et
`mode` (`index=1`) ne dépendent pas du dataclass mais de l'**ordre** d'un dict
ou d'une liste. Réordonner `CONTEXTES` changerait le défaut de l'interface
sans qu'aucun test ne le dise.

### 3.6 Ce que le corpus n'exerce toujours pas

Le garde-fou du MAD nul, écrit et documenté, ne se déclenche **jamais** :
zéro couple (point, mois) sur 124. À ajouter à la liste ouverte depuis
l'étape 1 — débit désinfluencé, normales pré-calculées, export d'air
multi-stations.

Le rapport d'étape est `docs/etape3_rapport.md`.

---

## Étape 4 — arrêter la spécification

Dernière étape sans modification de code applicatif. `app/`, `ref/` et la
référence `tests/reference/` sont inchangés.

### 4.1 Le cadre de lecture était faux, et le corriger inverse la conclusion

Les §1 et §2 de l'étape 3 opposaient les critères relatifs au détecteur à
4 °C. Ce n'est pas celui à remplacer. Contre le régime **en service** — 10 °C,
sans exclusion de saison, **22 jours marqués sur 23 816** —, tout s'inverse :

| | jours | rapport |
|---|---|---|
| régime en service | 22 | ×1 |
| A poolé q = 0,90 | 2 382 | ×108 |
| B dispersion k = 3 | 68 | ×3,1 |
| B dispersion k = 4 | 10 | ×0,45 |

« Le critère B est beaucoup plus sévère » était vrai contre 3 408 jours et faux
comme jugement sur le détecteur à remplacer.

**Une précision que je n'avais pas vue :** les 3 408 jours de l'étape 3
n'étaient pas non plus le détecteur CLI. C'était le critère brut
`ecart > 4 °C`, sans la grille annuelle à 5 jours ni l'exclusion de saison. Le
vrai détecteur CLI marque **17 025** jours. J'avais comparé à un troisième
objet.

Deux propriétés utiles ressortent du bon cadre : les six réglages qui marquent
davantage sont des **sur-ensembles stricts** du détecteur en service — ils n'en
perdent aucun jour —, et **aucun réglage candidat ne casse un point**, quand le
régime CLI en tue 14.

### 4.2 La conjonction demandée se comporte à l'envers

`E_moy ET E_max` **sélectionne les journées de faible amplitude d'air** —
exactement le profil d'artefact. À k = 2, les jours retirés ont une amplitude
d'air médiane de 10,4 °C, ceux gardés de 5,0 °C dont 60 % sous 6 °C. Elle
retire les épisodes installés et garde le bruit isolé.

La raison se démontre sans données : `E_moy` et `E_max` diffèrent exactement de
`TX − TM`. Ils ne franchissent leur seuil ensemble que si l'air varie peu.

La conjonction de `thermie_points` n'est pas celle-là : elle oppose une
**forme** (`R_ampl`) à un **niveau** (`E_max`). Mesurée, elle donne le profil
inverse — amplitude d'air médiane 12,05 °C, `R_ampl` médian **1,03**, épisodes
de 4 jours, **aucune synchronisation entre points**. Et elle retrouve
`BIE40-3` en 2015, le point que le `MANIFESTE.md` du projet clos place sous
réserve d'implantation, **sans qu'aucun seuil de ce projet n'ait été importé**.

### 4.3 Ce que j'ai corrigé dans mon propre code

- Le script de conjonction ne chargeait pas `T_eau_min` : `R_ampl` était
  incalculable.
- Le garde-fou d'amplitude d'air allait être repris à 6 °C — une valeur du
  bassin de la Bienne. Remplacé par une **dérivation du jeu traité** (premier
  décile), qui retombe entre 5,00 et 6,62 °C et corrobore le 6 °C sans
  l'importer.
- La dérivation de l'effectif minimal tirait des sous-échantillons
  **aléatoires**, ce qui détruit l'autocorrélation que Newey-West corrige et
  surestime la significativité. Remplacé par des **fenêtres contiguës**.

### 4.4 La règle de validité, vérifiée

Le calcul amont est confirmé au chiffre près : sur `m_estival`, l'IC95 contient
zéro pour **un seul point réel**, `BLE3-0`, `t = −0,447` ; le suivant est à
`t = 3,58`. Étendue par espèce à `m_saisonnier`, la règle écarte deux
estimations, toutes deux **déjà** repliées par V4.5 pour `R² < 0,30`.

L'effectif minimal est **dérivé** et non conventionné : sur des fenêtres
contiguës, 96,0 % restent significatives à `n' = 60`, contre 94,5 % à 50. Donc
`n_min = 60`. La dérivation ne fait entrer aucun nombre nouveau — elle réutilise
le niveau de 95 % déjà présent dans la règle.

En aval d'un rejet, **`m = 0` est possible sans modifier V4.5** (le coefficient
est un argument, `core.py:174`) et le refus ne l'est pas — bien que les
consommateurs aval soient déjà écrits pour tolérer l'absence de la colonne, ce
qui est exactement ce que `m = 0` produit.

### 4.5 Le livrable

`docs/SPEC_detecteur_et_validite.md` : le détecteur en deux marches, la règle
de validité, la provenance des onze valeurs numériques, les six fichiers de
`app/` touchés avec l'effet attendu artefact par artefact, et les points dont
le comportement changera. Trois décisions qui ne se déduisent pas de la mesure
sont écrites comme des alternatives fermées au §5 du rapport d'étape.

Le rapport d'étape est `docs/etape4_rapport.md`.

---

## Étape 5 — correctif 3, le marquage

Première modification de code applicatif. **Un seul fichier :
`app/thermie_debits/qc.py`** — 138 lignes ajoutées, 20 retirées.
`ref/v4_5/` reste intact et la référence n'a pas été reconstruite.

### 5.1 Le harnais devait apprendre à exécuter `app/`

D3 attache la **référence** au code figé : les 66 artefacts viennent de
`ref/v4_5/`, et cela ne change pas. Mais un harnais de non-régression doit
pouvoir **rejouer** le corpus avec le code modifié. Variable d'environnement
`THERMIE_CODE` — `ref` par défaut, `app` pour vérifier —, et chaque exécution
annonce quel code elle exécute et à quelle référence elle se compare.

### 5.2 Le correctif, et ce qu'il ne change pas

`marquer_qualite()` produit une table où **chaque journée lue reste présente**,
avec un statut à trois valeurs et la **liste** de ses motifs.
`controle_qualite()` conserve signature et retour, et devient l'adaptateur.
Un seul appelant (`orchestrator.py:155`), six consommateurs indirects, aucun
touché.

Un détail qui n'en est pas un : `_marque` continue de retourner le nombre de
journées **nouvellement** écartées, et non le total du détecteur. C'est ce
décompte que le journal affiche depuis toujours ; le changer aurait fait bouger
`99_log.txt` sur les 32 points.

`config.py` n'a eu besoin de rien, et je préfère le dire plutôt que d'y ajouter
du paramètre inutile. Il bougera au correctif 1.

Le statut `non_diagnosticable` n'a **aucun producteur** : les quatre détecteurs
de V4.5 tranchent tous. Vérifié — 0 sur 68 134 journées, dans les deux régimes.

### 5.3 Un artefact bouge, et je ne l'ai pas rebasé

`jeu_bienne/99_log.txt` diffère de deux lignes, qui disent
`<RACINE>\ref\v4_5\…` au lieu de `<RACINE>\app\…`. Numéros de ligne, messages,
comportement : identiques. Le harnais enregistre **l'endroit du disque** où le
code se trouve — la même faute que celle corrigée à l'étape 1 pour ses propres
numéros de ligne.

La consigne interdit de rebaser, et elle a raison. Rien n'a été touché ;
l'arbitrage est demandé au §5 du rapport d'étape.

Pour répondre malgré tout à la question qui compte, un **diagnostic A/B** a été
construit : deux rejeux complets par régime, l'un avec `ref/v4_5/`, l'autre
avec `app/`, comparés **entre eux** après neutralisation de la racine du code.

| Régime | identiques au bit près | chemin seul | **divergents** |
|---|---|---|---|
| application | 65 / 66 | 1 | **0** |
| CLI (17 025 journées écartées) | 63 / 66 | 3 | **0** |

### 5.4 `tests/reference_cli/` n'a pas pu servir de témoin

Le contrôle demandé a été lancé ; son résultat est ininterprétable, et pas à
cause du correctif : ce dossier a été figé **avant** que le harnais ne gagne
`10_parametres.json` et la colonne `sortie_v45`. Le comparer aujourd'hui
mélange un changement de code et un changement de schéma du harnais. C'est
signalé plutôt que présenté comme une régression, et le A/B fournit le témoin
valide.

### 5.5 Ce que le marquage révèle, et une mesure d'étape 4 qui était fausse

**Zéro journée n'est écartée par plus d'un détecteur**, sur 68 134 journées et
dans les deux régimes. Les détecteurs sont parfaitement disjoints. Le défaut de
`qc.py:32-36` est donc **réel dans le code et jamais exercé sur ce corpus** :
le correctif est de robustesse, pas de résultat — ce qui explique que
`03_journees_ecartees.csv` n'ait pas bougé.

**R10 (b) a révélé une erreur de ma mesure d'étape 4.** La longueur d'épisode
médiane de la marche 2 était annoncée à 4,0 ; elle vaut **1,5**. Je calculais
les épisodes sur le masque du **socle**, puis lisais cette longueur pour les
lignes de chaque règle. Corrigé.

La mesure de ce que `min_jours_episode` exclut confirme et aggrave R10 : à 3,
la marche 2 n'exclut pas « rien », elle **annule tout** (0 jour, 0 point sur 2),
et la marche 1 perd 14 de ses 16 points. Valeur proposée : **1**, la longueur
d'épisode devenant un attribut diagnostique et non un filtre.

**R11** : `n_min` dérivé séparément vaut 60 pour l'estival — le transfert était
juste — mais 40 pour l'ombre commun, 10 pour la truite fario, 25 pour le
brochet, 75 pour la brème et le barbeau. Trois espèces sur cinq reposent sur
**un seul point support** : leur valeur décrit une chronique, elle ne dérive
rien.

Le rapport d'étape est `docs/etape5_rapport.md`.

---

## Étape 6 — R13, le rebasage, et le correctif 2

### Une invariance qui dépend des données n'en est pas une

L'adaptateur livré en étape 5 rendait, dans la colonne héritée `motif`, tous
les motifs joints. Le diff était vide — mais parce qu'**aucune journée du
corpus ne porte plus d'un motif**. `redaction.py:76` extrait la famille d'un
motif par `^([^—(]+)` et aurait lu la chaîne jointe le jour où une journée en
porterait deux.

La vue héritée rend désormais `motifs[0]`, ce que produisait exactement
l'ancien `_marque`. La liste complète vit dans `motifs`, que seul le périmètre
lit, et `rapport_ecartes_detaille()` l'expose sans toucher aux cinq colonnes
historiques.

**La preuve est fabriquée, pas cueillie.** `tests/test_adaptateur_qc.py`
construit des chroniques synthétiques — dans `tests/`, jamais dans `data/` —
dont des journées déclenchent deux puis trois détecteurs, exécute V4.5 et
`app/` dans deux interpréteurs séparés (les deux modules portent le même nom)
et compare console, `propre` et `rapport` colonne par colonne. Ce que le
corpus ne peut pas dire, un cas construit le dit.

### On ne mesure pas l'état d'avant en modifiant le code pendant la mesure

J'ai posé le correctif 2 pendant que le diagnostic A/B tournait. Ses rejeux
restants auraient porté la correction. Pire : le processus que je croyais
arrêté ne l'était pas — `ps -W` sous Git Bash affiche le PID MSYS, `taskkill`
attend le PID Windows — et il écrivait toujours dans le fichier de sortie que
le nouveau rejeu venait de tronquer. La sortie lue mélangeait deux exécutions.

**Règle retenue : rien n'est écrit dans `app/` tant qu'une mesure qui le lit
n'est pas terminée, et l'arrêt d'un processus se vérifie, il ne se suppose
pas.**

### Un patch qui change les fins de ligne détruit un moyen de contrôle

En re-séquençant, j'ai découvert que mes scripts de correctif, lisant avec
`read_text()` et écrivant avec `write_text()`, retraduisaient tout le fichier
en CRLF sous Windows. `app/thermie_debits/qc.py` était dans cet état depuis
l'étape 5. Aucune valeur n'en dépendait, mais `app/` cessait d'être comparable
octet pour octet à `ref/v4_5/` en dehors des corrections voulues — c'est-à-dire
qu'un contrôle disparaissait sans que rien ne le signale.

Les scripts de correctif écrivent désormais des **octets**, refusent un fichier
qui n'est pas en LF, et vérifient qu'ils n'en introduisent pas.

### Une empreinte prouve ce qu'un diff ne montre pas

Pour établir qu'un artefact n'a bougé **que** sur les lignes attendues, un diff
ne suffit pas : il montre ce qu'il montre. La méthode retenue est la
**substitution inverse** — remettre dans le fichier reconstruit ce que la
neutralisation en a retiré, puis vérifier que le sha256 retombe sur celui
d'avant. Si l'empreinte retombe, aucune autre différence n'existe. Employée en
B3 (deux lignes de chemin) et en B4 (chemin plus volet climatique), elle a
conclu les deux fois.

### Mesurer un défaut avant de le corriger, parce qu'après c'est impossible

`core.fusionner` lissait sur un index **positionnel**. Une fenêtre de sept
lignes n'est une fenêtre de sept jours que si la série est continue. Sur le
corpus : **1 131 journées (1,68 %) sur 26 points**, la plus longue lacune
enjambée atteignant **1 716 jours**, pour des écarts de **6,10 °C sur `Tmh`** et
**6,77 °C sur `Delta_TMm_liss`**.

Cette mesure ne se refait pas après correction : une fois la série réindexée,
aucune fenêtre n'enjambe plus rien. Le harnais recalcule donc les **deux**
versions côte à côte, sans toucher `app/` — méthode qui a servi aussi à
chiffrer le détecteur de plateau **sans le corriger**.

### Corriger le support, pas le lissage

`fenetre` et `min_periods` sont ceux de V4.5, repris sans modification et avec
leur provenance déclarée à chaque appel. `min_periods` reste un littéral :
`10_parametres.json` n'a pas à bouger.

Ce qui change est son **sens**. Sur un index positionnel, `min_periods` est une
commodité de démarrage ; sur un calendrier, c'est une exigence de **densité**.
Conséquence chiffrée avant d'être assumée : **18 journées sur 67 392** perdent
`Tmh`, **toutes** au voisinage d'une lacune, **aucune** en extrémité de
chronique — et les valeurs abandonnées incluent des « moyennes sur sept jours »
calculées à partir d'**une seule** journée observée.

### Une déclaration d'artefacts se confronte au code, pas seulement aux résultats

La commande déclarait `06_coefficients.csv` parmi les artefacts devant bouger.
Le code dit le contraire : `m` est une régression de l'eau **brute** sur l'air
**brut** (`core.analyse_sensibilite`, `core._m_saisonnier`), et le correctif 2
ne touche que `Tmh` et `Delta_TMm_liss` sans retirer une seule ligne. Le
désaccord a été signalé **avant** le rebasage, puis constaté : 0/6.

Le reste est conforme — 8 artefacts bougent, 58 restent figés — et les trois
jeux dont les artefacts bougent sont exactement les trois qui portent des
journées affectées.

### Un correctif se juge à ce qu'il change de conclusion

Le seul changement de verdict de tout le correctif 2 : `BIE5-9` avait une
journée de vulnérabilité aiguë, le 31 juillet 2022, à `Tmax_norm` = 23,365 °C
pour un seuil de 23,000. Son anomalie d'air lissée avait été moyennée sur une
fenêtre enjambant une lacune de 600 jours. Corrigée, la journée tombe à
22,946 °C, le point perd son point aigu, et son SGVT passe de 3,17 à 2,50 sur
10.

### D15 et D41 se vérifient ligne à ligne, pas en principe

Les trois amendements de la spécification tiennent aux deux mêmes décisions.

`min_jours_episode = 3` était importé de `thermie_points` — D15 l'interdit — et
la mesure l'enfonce : à 3, la marche 2 perd **100 %** de ses épisodes. Défaut
ramené à **1**, le neutre, faute de valeur désignée par la mesure.

`n_min` se dérivait en mettant en commun les fenêtres de tous les points du
corpus — D41 l'interdit, l'application traitant une sonde à la fois. Retiré. Le
retrait n'est pas gratuit et n'est pas présenté comme tel : cinq estimations
qui sortaient entrent. Mais leurs `t` de Newey-West vont de **4,21 à 9,06** —
le critère qui connaît déjà `n` les accepte toutes, et c'est lui qui a raison.

D41 a ensuite été appliqué **ligne à ligne** au tableau de provenance. Il fait
sortir `n_min`, et rien d'autre.

Le rapport d'étape est `docs/etape6_rapport.md`.

---

## Étape 7 — le contrôle permanent, et les suppressions silencieuses

### Un contrôle qui disparaît en silence est pire qu'un contrôle qui échoue

L'incident CRLF de l'étape 6 n'avait fait bouger aucune valeur. Il avait fait
bien pire : il avait retiré un moyen de vérification sans que rien ne le
signale. `app/` avait cessé d'être comparable octet pour octet à `ref/v4_5/`
en dehors des corrections voulues, et personne ne l'aurait su.

D44 en fait une procédure. `diff_app_ref.py` compare les deux arbres **octet
par octet**, distingue une différence de CONTENU d'une différence de FINS DE
LIGNE — la seconde étant traitée comme une anomalie au même titre que la
première — et confronte la liste constatée à la liste que l'étape déclare. Un
fichier qui diffère sans être déclaré arrête l'étape.

Il tourne **avant** et **après** chaque étape. Avant, il établit d'où l'on
part ; après, que l'on n'a touché que ce qu'on a annoncé.

### Une assertion sur l'ancre vaut mieux qu'un patch qui réussit à moitié

`build_reference.py` est en CRLF, contrairement aux fichiers de `app/`. Mon
script de correctif a échoué à trouver son ancre — et il a échoué **avant**
d'écrire quoi que ce soit, parce que chaque substitution est précédée d'une
assertion sur son ancre.

C'est la contrepartie utile de l'incident précédent. Un patch qui remplace
sans vérifier produit un fichier à moitié modifié ; un patch qui vérifie
d'abord produit une erreur lisible. Les scripts normalisent désormais les fins
de ligne à l'entrée et les restituent à la sortie, et expriment les caractères
de contrôle par `chr(13)` et `chr(10)` — les échappements ne survivent pas au
passage par un document heredoc du shell.

### Quand le harnais compense, c'est l'application qui a un défaut

`03_journees_ecartees.csv` portait depuis l'étape 1 cette mention : « V4.5
n'en trace aucune ; **le harnais la déduit** en comparant à `res.df_air` ». Le
harnais compensait donc, depuis le début, une suppression que l'application ne
déclarait pas — correctement, mais par soustraction d'ensembles, sans pouvoir
dire la température de l'eau ce jour-là.

Cela change la nature du correctif : il ne s'agissait pas d'ajouter une
information nouvelle, mais de **déplacer une connaissance du harnais vers
l'application**. Une compensation du harnais est un symptôme, et il vaut la
peine de relire les siennes en se demandant ce qu'elles cachent.

### Distinguer les causes avant de les nommer

La jointure et le `dropna` qui la suivait pouvaient effacer une journée pour
trois raisons. Mesurées séparément : **636** journées sans aucune ligne d'air,
**0** avec `T_air` vide, **0** avec `T_eau_moy` vide. Une seule cause existe.

Les deux autres branches ont néanmoins été écrites, avec leur motif propre et
la mention explicite qu'elles ne sont pas exercées. L'étape 6 a montré ce que
coûte une invariance qui repose sur une propriété du jeu d'essai : une cause
absente du corpus n'est pas une cause impossible.

### La moyenne cache le cas que l'écran doit dire

0,93 % des journées effacées, sur l'ensemble du corpus. Le chiffre est
rassurant et il est trompeur : `La Moselle à Hielle` perdait **102 de ses 303
journées, d'un seul tenant, du 6 juillet au 15 octobre 2012** — tout son été,
et l'unique année civile de sa chronique ; `LA PLAINE A RAON-SUR-PLAINE`
perdait **l'année 2008 en entier**, 220 journées lues et 0 retenue.

Une mesure de dégradation ne se résume pas par sa moyenne. Il faut la part par
point, la plus longue série continue, et le fait booléen — « une année civile
est-elle entièrement absente ? » — qui se lit sans seuil.

### Un texte d'écran s'écrit sans introduire de seuil

Le bloc de dégradation déclarée est **toujours affiché**, y compris quand rien
n'est retiré : un bloc qui n'apparaît qu'en cas de problème apprend au lecteur
que son absence signifie « rien à signaler », alors qu'elle peut aussi
signifier « personne n'a regardé ».

Et il ne se durcit pas au franchissement d'une valeur conventionnelle : il
s'enrichit de phrases dont la condition est un **fait constaté** — une année
entièrement retirée, des journées retirées entre juin et septembre. Deux
booléens qui se lisent sur les données et ne se calibrent pas. C'est ainsi
qu'on écrit un texte adaptatif sans réintroduire par la porte de l'affichage
les seuils que D15 interdit ailleurs.

Enfin, il ne dit **jamais** « écartées par le contrôle qualité ». Le contrôle
qualité les a retenues : elles sont saines. Les confondre imputerait à la
sonde d'eau un manque qui vient de la station d'air.

### Une prédiction falsifiable est le bon usage d'une lecture de code

L'étape annonçait que la jointure gauche ne devait PAS déplacer
`06_coefficients.csv`, et disait ce qu'il faudrait conclure dans le cas
contraire. Elle tient : `06` est figé sur les six jeux, et avec lui `05`, `07`
et `08` — **0 valeur changée**, 65 artefacts sur 66 identiques au bit près.

L'intérêt de la forme n'est pas la confirmation, c'est qu'elle rendait
l'échec informatif : si `06` avait bougé, la jointure interne aurait fait
autre chose que ce qu'on croyait, et il aurait fallu le comprendre avant
d'aller plus loin.

### Un correctif de visibilité doit ne rien changer

Correctif 5 : **aucun verdict publié ne bouge**, et c'est le résultat
attendu. Les journées que la jointure effaçait n'entraient dans aucun calcul —
c'est ce qu'« effacer » voulait dire. Les conserver ne les y fait pas entrer :
elles restent hors de la chaîne, mais **nommées**.

Le chiffre qui ferme la boucle est la colonne `journees_perdues_hors_qc` de
`02_effectifs.csv`, qui mesurait exactement les suppressions silencieuses :
elle passe de **636 à 0**.

### Comparer au bon témoin

Depuis l'étape 6, `app/` porte plusieurs correctifs. Comparer un rejeu à
`tests/reference/`, qui est l'état V4.5, mesure leur effet **cumulé** — jamais
celui du dernier. Pour isoler un correctif, il faut comparer le rejeu d'après
au rejeu d'avant, à harnais identique des deux côtés.

Et quand le harnais change aussi, il faut deux comparaisons distinctes : l'une
à harnais constant qui mesure le code, l'autre à code constant qui mesure le
harnais. Les mélanger produit un diff dont on ne peut rien conclure — la leçon
de B4 à l'étape 6, appliquée ici d'emblée.

### Un journal des verdicts se relit en appariant, pas en lisant la fin d'un diff

L'étape 6 annonçait trois pourcentages de fraie modifiés. En les appariant
point par point plutôt qu'en lisant la fin d'un diff tronqué à l'affichage, il
y en a **sept**. Aucun ne change le score `P` — mais sept lignes publiées
avaient bougé, et trois seulement avaient été rapportées.

D43 donne à cette vérification un endroit où vivre : `VERDICTS_MODIFIES.md`,
cumulatif, jamais réécrit, où chaque correctif consigne l'avant, l'après et la
cause en une phrase.

Le rapport d'étape est `docs/etape7_rapport.md`.

---

## Étape 8 — le correctif 8, et une table d'impact qui a tenu

### Un argument symétrique se retourne, et il faut le dire

Le correctif 8 pose que `Tmh`, moyenne de température d'**eau**, ne doit pas
dépendre de la complétude de la série d'**air**. L'argument vaut dans l'autre
sens et ne s'arrête pas à la porte du mandat : `Delta_TMm_liss` est une
moyenne d'**air** calculée sur les seules journées ayant de l'**eau**.

Mesuré sans être appliqué : **854 valeurs, 32 points, jusqu'à 1,94 °C
répercutés sur `T_norm`** — plus large que le correctif qu'on venait de poser.

Il n'a pas été corrigé, parce qu'un correctif fait une chose et que le mandat
portait sur `Tmh`. Mais il est **nommé dans le code, à l'endroit exact où il
se produit, avec ses chiffres**. Un défaut connu qui n'est écrit nulle part
est un défaut qui sera redécouvert ; écrit à sa ligne, il attend son étape.

### Vérifier une prédiction sur son propre périmètre

La prédiction annonçait 473 valeurs déplacées. Ma première vérification, faite
en comparant deux rejeux sur l'artefact `07_t_norm.csv`, en trouvait **488**.

L'écart ne venait pas du correctif : l'artefact ne contient que les journées
dont `Tmh_norm` n'est pas vide, et mon décompte y traitait comme « changées »
des lignes dont un côté était vide. La prédiction portait sur les 67 392
journées **exploitables**, pas sur les 67 101 **lignes de l'artefact**.
Rejouée sur son périmètre, elle tombe à 473 exactement — points, écart maximal
et journées récupérées compris.

La leçon n'est pas qu'il fallait arrondir : c'est qu'un écart entre prédiction
et constat oblige d'abord à vérifier que les deux comptent **la même chose**.
Le 488 est consigné dans le rapport plutôt qu'effacé.

### Un `str.replace` sans assertion échoue en silence

Trois substitutions d'un script de mesure n'ont pas trouvé leur ancre, et
`str.replace` ne dit rien quand il ne remplace rien : le script a tourné,
produit ses fichiers, affiché l'ancien texte.

C'est le contraste qui instruit. Mes patchs de code passent par un `rep()` qui
**assert** sur l'ancre — c'est lui qui avait arrêté un patch avant l'écriture à
l'étape 7. Le même geste manquait ici. **Toute substitution dans un fichier
doit être assertée, y compris dans un script jetable** : le coût est d'une
ligne, l'absence de coût est un silence.

### Un recalcul dont le résultat est « rien n'a bougé » n'est pas un recalcul inutile

La table d'impact du détecteur était déclarée périmée par trois correctifs.
Elle ne l'était pas : sur 30 des 31 points, `Δm` et `ΔTmh_norm` sont
identiques à la **sixième décimale**.

La raison est structurelle, et elle méritait d'être formulée : les colonnes de
cette table sont des **différences entre deux rejeux de la même chaîne**. Un
correctif qui déplace les deux côtés du même montant ne déplace pas leur
différence. Pour `Δm`, c'est plus fort encore — `m` régresse l'eau brute sur
l'air brut, donc aucun correctif touchant `Tmh` ne peut l'atteindre.

Le recalcul restait justifié : il fallait le vérifier, pas le supposer. Et il
a produit un résultat utile — le seul point qui varie, `BIE40-3`, varie parce
que l'étape 4 mesurait le **socle seul** là où la spécification retient
**l'union des deux marches**. Un écart qu'on croyait dû aux correctifs
s'expliquait par une différence de définition.

### Nommer six journées vaut mieux que les compter

L'étape 4 signalait « six journées que le socle ne marque pas ». Nommées,
elles disent beaucoup plus : toutes sur le même point, toutes en juillet,
toutes avec un `E_moy` relativisé entre **2,04 et 2,86** pour un seuil à 3,0.
Le socle ne les manque pas par aveuglement — il les manque **de peu**, parce
qu'elles ressemblent aux autres journées chaudes de juillet de ce point.

Et la marche 2 en rattrape exactement une. Le 28 juillet 2015 a pourtant un
`R_ampl` très élevé : c'est le second membre, le niveau, qui le retient. La
conjonction fait ce pour quoi elle a été choisie — exiger deux signatures
**différentes** et ne pas se contenter de l'une. Une table de six lignes le
montre ; un décompte ne le montrait pas.

### Une déclaration d'artefacts se relit deux fois

Pour la deuxième fois, ma lecture du code a contredit la déclaration d'étape,
et pour la deuxième fois je l'ai dit **avant** de corriger : `05_anomalies.csv`
était déclaré devant bouger, mais `Tmh` n'y figure pas et le correctif 8 ne
touche que `Tmh`.

L'explication n'est pas une erreur du commanditaire : la déclaration devient
vraie si l'on corrige **aussi** `Delta_TMm_liss`, qui est bien dans cet
artefact. Le désaccord désignait donc le défaut miroir avant que je l'aie
mesuré. Une déclaration qu'on ne comprend pas mérite d'être instruite, pas
seulement signalée.

Le rapport d'étape est `docs/etape8_rapport.md`.

---

## Étape 9 — le défaut miroir, et une règle qui ne survit pas à sa mesure

### Vérifier une réponse évidente, parce que l'évidence ne dit pas l'ampleur

Le support du lissage devait-il être tout le calendrier de la station d'air,
ou seulement son recouvrement avec la chronique d'eau ? La réponse était
évidente — c'est le même argument que le correctif lui-même : une grandeur
d'air ne doit pas dépendre de la date à laquelle une sonde d'eau a commencé.

Chiffrée quand même, la différence entre les deux supports porte sur **189
valeurs, jusqu'à 4,276 °C, soit 22 % de ce que corrige le correctif**. Une
réponse évidente sur un écart de 22 % n'aurait pas dû être donnée sans le
savoir : l'évidence tranchait le **sens**, elle ne disait rien de l'**enjeu**.

### Un artefact n'est pas le périmètre d'une mesure — deuxième fois

L'artefact montrait 824 valeurs déplacées, la prédiction en annonçait 854. À
l'étape 8, le même écart s'était présenté à l'envers (488 contre 473) et avait
tenu à ce que l'artefact omet les lignes vides. Ici il tient à ce qu'il omet un
**point entier** : `BIE35-5__NA`, dont la chaîne échoue et dont l'échec est la
référence (D7), porte exactement les 30 valeurs manquantes.

La règle qui se dégage : **vérifier une prédiction sur le périmètre où elle a
été formulée**, et fermer le compte plutôt que se contenter d'une explication
plausible — ici en établissant qu'aucune des 824 différences n'était
inférieure à 5·10⁻⁷, ce qui écartait l'arrondi comme cause.

### Un motif juste ne garantit pas la conséquence attendue

D54 fait porter aux déclarations d'artefacts le motif du mouvement attendu.
Les huit motifs de cette étape ont été vérifiés dans le code avant la pose, et
**aucun n'était faux** — première fois en trois étapes.

Mais l'un d'eux annonçait qu'« un basculement est attendu ». Le motif était
exact — `Delta_TMm_liss` entre bien dans `T_norm`, l'écart atteint bien
1,94 °C — et le basculement n'a pas eu lieu au seuil aigu. **Un motif décrit
un mécanisme ; il ne prédit pas son issue.** Les deux se contestent
séparément.

### Un non-basculement s'explique par une intersection, pas par une magnitude

L'attente déçue n'est un résultat que si l'on sait pourquoi. La mesure des
**marges** l'a donné : le correctif déplace 854 journées sur 67 392, donc sur
98,7 % d'entre elles le déplacement est **exactement nul** ; et seules **54**
journées de tout le corpus se tiennent à moins d'un demi-degré du seuil aigu.
Les deux ensembles se croisent à peine.

Le cas limite le dit mieux qu'une moyenne : la journée la plus proche du seuil
aigu, à 0,022 °C, n'était pas parmi les déplacées, et sa marge est identique
avant et après. Pour qu'un verdict bascule, il ne suffit pas qu'un correctif
soit ample — il faut qu'il touche là où c'est serré.

**Mesurer la marge, et pas seulement le déplacement**, est ce qui permet de
distinguer « le correctif est trop faible » de « le correctif ne touche pas
les journées critiques ».

### Une règle se mesure avant d'être écrite, même quand elle vient d'en haut

D55 posait qu'une journée dont un membre dépasse quand l'autre ne dépasse pas
soit signalée sans être exclue. Instruite, elle désigne **1 002 journées sur
30 points, contre 9 exclues** — cent onze signaux pour une exclusion.

Et le profil est sans appel : 992 de ces journées ont un `E_moy_rel` médian de
0,84 contre 4,62 pour les exclues, et ne sont marquées par la marche 1 qu'à
**1,6 %** contre 88,9 %. Sur le témoin indépendant, elles se rangent du côté
des journées ordinaires.

Le choix des grandeurs de comparaison décidait de la valeur de la réponse :
comparer sur les deux membres eux-mêmes aurait été **circulaire**, puisque ce
sont eux qui définissent les groupes. Les grandeurs retenues sont extérieures
à la règle — le critère de l'autre marche, et l'amplitude d'air par laquelle
l'étape 4 avait déjà départagé deux conjonctions.

### La synchronie instruit une spécification sans pouvoir y entrer

Six des dix journées où le niveau dépasse seul tombent **le même jour** — le
1er juin 2011 — sur six points différents. Une sonde sortie de l'eau est une
défaillance locale ; six cours d'eau ne s'exondent pas ensemble. C'est un
épisode météorologique, et c'est le critère par lequel l'étape 4 avait rejeté
une conjonction candidate.

Mais **D41 interdit que ce critère devienne une règle** : l'application traite
une sonde à la fois et ne peut pas savoir ce qu'un autre point a marqué le
même jour. La synchronie **instruit** la spécification sans pouvoir entrer
dans le code — une distinction qu'il faut tenir, sous peine d'écrire une règle
incalculable au moment où elle sert.

### Remonter qu'une décision ne tient pas, sans la trancher

La tâche demandait d'instruire D55 sans rien implémenter. L'instruction conclut
que la règle, telle qu'écrite, ne survit pas à la mesure — et qu'une
restriction naturelle, sans nombre nouveau, manque précisément le cas qui l'a
motivée.

Ce n'est pas à moi d'arbitrer : D55 porte sur ce que l'écran doit dire. Le
travail consiste à remonter les deux branches avec leurs chiffres, et à dire
laquelle manque quoi. Une décision qu'on applique sans la mesurer produit un
écran que personne ne lira.

Le rapport d'étape est `docs/etape9_rapport.md`.

---

## Étape 10 — le détecteur, et ce qu'il trouve

### Poser en deux fois ce qui pouvait se poser en une

Le détecteur de plateau et le détecteur de mise hors d'eau vivent dans le même
fichier et déplacent les mêmes artefacts. Les poser ensemble aurait coûté un
rejeu de moins et rendu chaque effet illisible.

Séparés, ils ont rapporté deux choses. La prédiction de la première pose —
« aucun verdict de plateau ne change » — a pu être vérifiée **seule** : 65
artefacts sur 66 figés, la mesure d'étape 6 confirmée quatre étapes plus tard.
Et l'effet du détecteur s'est mesuré contre un état où seul le plateau avait
bougé.

**Quand deux changements touchent les mêmes artefacts, les séparer n'est pas
une précaution, c'est la condition pour que la mesure veuille dire quelque
chose.**

### Un outil qui ne trouve pas ce qu'il cherche doit le dire

`comparer_rejeux.py` déclarait pour `04_normales.csv` une colonne de clé qui
n'existe pas dans ce fichier. Clé absente, appariement positionnel, longueurs
différentes, boucle de colonnes sautée : l'outil rapportait **« 0 valeur
changée »** sur un artefact qui avait perdu quatre lignes.

C'est la même famille que le `str.replace` muet de l'étape 8. La règle se
généralise : **le zéro est un résultat, l'absence de résultat n'en est pas
un**, et un outil doit les distinguer. L'outil refuse désormais le silence, et
c'est en le corrigeant que le mouvement de `04_normales.csv` est devenu
visible.

### Un motif vrai du calcul peut être faux de l'artefact

`04_normales.csv` était déclaré figé au motif que les normales sont calculées
en amont de `fusionner`. C'est vrai, et aucune valeur de normale n'a changé.
Mais `art_04` ne recopie pas la table des normales : il en projette les seuls
couples (jour, mois) que la chronique **retenue** contient encore. Le détecteur
retirant des journées, quatre couples ont disparu.

J'ai vérifié sept motifs contre le code et accepté celui-là sur sa
vraisemblance. **Un motif se conteste contre ce que l'artefact CONTIENT, pas
contre ce que la grandeur SIGNIFIE.**

### Une spécification qui fait foi tranche les contradictions de commande

La marche 2 exige `TN` et `TX`, que le lecteur d'air ne lisait jamais. Les lire
fait bouger `00` et `01` — que l'étape déclarait figés, et que la
spécification déclarait mobiles depuis l'étape 4.

Quand la commande dit que la spécification fait foi, une contradiction entre
les deux se tranche en faveur de la spécification, et se **signale** avant la
pose. Renoncer à lire `TN` et `TX` pour préserver deux artefacts aurait rendu
la marche 2 perpétuellement indisponible et une prédiction inatteignable.

### Vérifier une prédiction sur tous ses nombres, pas sur son total

`69 journées marquées` se décompose en `68` par la marche 1, `9` par la
marche 2, `8` en recouvrement. Un total juste peut recouvrir une décomposition
fausse — deux marches mal réparties donneraient le même 69.

Les trois prédictions de cette étape portaient **neuf nombres**. Les neuf sont
tombés justes, y compris l'identité nominale des cinq journées perdues et
celle, unique, que la marche 2 rattrape. C'est la contrepartie de mesures
faites deux étapes plus tôt sur la chaîne exacte où le code serait posé.

### Ce qu'un détecteur relatif trouve qu'un seuil absolu ne voit pas

Sur `LA PLAINE A RAON-SUR-PLAINE`, le régime en service ne marquait **aucune**
journée hors d'eau. Le détecteur relatif en marque **16**, et huit d'entre
elles étaient comptées comme journées de vulnérabilité aiguë. Le point passe de
« Risque Modéré » à « Risque Faible (Zone Refuge) ».

L'écart eau-air de ces journées dépassait de loin l'habitude du point au même
mois — jusqu'à 4,9 écarts-types robustes — sans jamais franchir les 10 °C d'un
seuil absolu. **Un seuil absolu ne manque pas ces journées par erreur de
réglage : il les manque parce qu'il ignore ce que ce cours d'eau fait
d'habitude.**

### Documenter ce qu'on perd aussi bien que ce qu'on gagne

Le passage au relatif fait perdre cinq journées que le régime en service
écartait, toutes sur un point, toutes en juillet. Leur écart relatif tient
entre 2,0 et 2,9 écarts-types, sous le seuil de 3,0 : elles ressemblent aux
autres journées chaudes de ce point.

Les nommer, avec leurs valeurs de diagnostic, plutôt que de les résumer par un
« 5 journées perdues », est ce qui permet au lecteur de juger si le change est
bon. **Un correctif qui ne documente que ses gains ne se laisse pas
contredire.**

Le rapport d'étape est `docs/etape10_rapport.md`.

---

## Étape 11 — la règle de validité, et un contrôle refait

### Refaire un contrôle qui confirme n'est pas du temps perdu

`comparer_rejeux.py` certifiait les « figé » depuis l'étape 7, et il était
aveugle sur un artefact. Tout ce qu'il avait prononcé sur celui-là devait être
refait — **et refait autrement** : par empreinte du fichier entier, qui ne
dépend d'aucune clé, d'aucun appariement, d'aucune colonne, donc d'aucune des
hypothèses qui l'avaient rendu aveugle.

Résultat : une seule empreinte distincte sur sept rejeux, cinq jeux sur six.
L'outil n'avait rien manqué. **C'est la différence entre « figé » et « on n'a
pas regardé », et elle ne se comble qu'en refaisant.**

*Mon script de vérification a d'abord crié cinq anomalies : sa propre logique
de verdict confondait « déclaré mobile et n'a pas bougé » avec un écart. Un
outil de contrôle se contrôle aussi.*

### Une prédiction se refait, elle ne se reprend pas

Les chiffres de validité dataient de l'étape 4 — avant cinq correctifs, dont
un qui a déplacé `m` jusqu'à 0,042. Les reprendre aurait été commode et faux.

Recalculés sur l'état actuel : `BLE3-0` reste le seul rejet estival, `t` =
0,447, et le suivant passe de 3,585 à **3,658**. La séparation s'est très
légèrement **élargie**. C'était l'information demandée — un resserrement aurait
signifié que les correctifs rapprochaient un point aberrant du reste, et
aurait mérité d'être compris avant de poser quoi que ce soit.

### Un motif peut être juste et incomplet

Trois formes de motif erroné ont maintenant été rencontrées : **faux** (`00`
et `01` à l'étape 10, que la spécification déclarait mobiles), **vrai du
calcul et faux de l'artefact** (`04_normales`, projection de `res.df`), et
**juste mais incomplet** (ici : `07_t_norm` bouge bien à cause de `BLE3-0`,
mais aussi sur deux autres points par le coefficient saisonnier).

La typologie de D63 sert exactement à cela : demander d'abord *de quoi cet
artefact est-il une fonction*, avant de demander *ce que ce correctif change*.

### Retirer un garde-fou est une décision, et elle se dit

L'ancien coefficient saisonnier se repliait sur l'estival si `R² < 0,30`. La
spécification ne porte pas ce seuil. Le retirer était donc une conséquence de
la spécification — mais un retrait silencieux aurait été un changement de
comportement non déclaré.

L'argument mérite d'être écrit parce qu'il est général : **un R² faible sur un
grand échantillon ne dit pas qu'un couplage est indistinct de zéro ; il dit
que la variable explique peu de la variance.** Ce sont deux énoncés
différents, et c'est l'intervalle de confiance qui répond au premier. Un point
du corpus l'illustre : `R² = 0,241`, mais `n = 326` et `t = 3,96`.

### Un repli silencieux n'est pas un garde-fou

Se rabattre sur le coefficient estival quand le saisonnier paraît douteux,
c'est normaliser une fenêtre de reproduction hivernale avec le couplage de
l'été. Ce n'est pas une précaution, c'est une **substitution** — et elle ne se
voyait nulle part dans les sorties.

Un coefficient rejeté vaut zéro. Zéro se déclare ; la valeur d'un autre
coefficient se confond avec une mesure.

### Publier la valeur imposée ET la valeur estimée

`m` est le coefficient **appliqué** — zéro en cas de rejet. `m_estime` est la
pente **estimée**. Publier le seul zéro laisserait croire que le couplage a
été mesuré nul ; publier la seule pente laisserait croire qu'elle a été
appliquée. Les deux colonnes existent pour que la différence soit lisible, et
la catégorie de sensibilité continue de décrire la pente estimée — dire
« Résilience Élevée » parce qu'on a imposé zéro serait un contresens.

### Un correctif peut ne rien changer aux chiffres et tout changer à leur portée

`BLE3-0` normalisait à l'envers : son coefficient négatif faisait **ajouter**
l'anomalie d'air au lieu de la retrancher. Corrigé, l'écart est de **0,016 °C
en médiane** et aucun indicateur du point ne bouge.

Ce qui change n'est pas le chiffre, c'est son statut. Le point publiait une
température *normalisée* — avec l'autorité que ce mot porte : comparable à un
autre point, à une autre année. Cette autorité reposait sur un coefficient
dont le signe était faux et dont l'IC contenait zéro.

**Le chiffre était déjà à peu près juste ; c'est ce qu'on avait le droit d'en
conclure qui était faux.** Un journal des verdicts qui ne relèverait que les
valeurs déplacées manquerait ce cas entièrement.

### Le piège du heredoc s'est refermé une troisième fois

Un `\n` inséré dans un fichier source est devenu un vrai saut de ligne au
passage par un document heredoc, coupant un littéral de chaîne. Le rejeu a
tourné quinze minutes, échoué sur tous les jeux, et **rendu un code de sortie
0** — le harnais capturant les échecs par jeu.

Aucun dommage, le dossier de sortie était vide et le comparateur l'a dit. Mais
la parade était connue et je ne l'avais pas appliquée : **écrire le script
comme fichier, jamais le composer dans une ligne de commande.**

Le rapport d'étape est `docs/etape11_rapport.md`.

---

## Reprise après déplacement — contrôle d'intégrité

Le dossier `Documents` a été redirigé par OneDrive, ce qui a fait paraître le
projet effacé. Il ne l'était pas. Avant de reprendre à l'étape 12, un contrôle
d'intégrité a vérifié que le déplacement n'avait rien altéré.

### D71 — on ne sonde plus un script, on lit sa source

Les scripts du harnais n'utilisent pas argparse, ignorent les arguments
inconnus et écrivent sur des chemins de sortie codés en dur. Sonder l'un
d'eux avec `--help` l'exécute pour de bon. On ne sonde plus un script : on lit
son en-tête ou sa source.

### Un incident a servi de contrôle

Sonder `inventaire_corpus.py` avec `--help` l'a exécuté pour de bon (D71) et
a réécrit `out/etape1/inventaire_corpus.csv` et `docs/etape1_extraits_bruts.md`
— hors du périmètre d'écriture autorisé pour ce contrôle. Le script n'a pas
été modifié depuis l'étape 1, il ne lit que `data/` et `ref/v4_5/`, et D5 le
rend déterministe : la réexécution accidentelle a donc reproduit sa sortie
d'étape 1 à l'octet près (SHA-256 vérifiés contre l'exemplaire détenu hors
machine) et prouvé, mieux qu'une commande délibérée ne l'aurait fait, que les
46 fichiers du corpus ont traversé le déplacement sans altération.

La confirmation fonctionnelle de bout en bout a suivi délibérément :
`mesure_validite_actuelle.py`, rejoué avec `THERMIE_CODE=app`, a reproduit
`out/etape11/D1_validite_actuelle.csv` à l'octet près (même empreinte
SHA-256 que l'exemplaire d'étape 11). La chaîne complète — lecture des
fichiers, contrôle qualité, normales, anomalies, régression, coefficients —
reproduit avec le code V4.6 et le corpus entier ce qu'elle produisait avant
le déplacement. L'intégrité est établie.

---

## Étape 12 — la provenance d'une référence, et la convention unique

### Un contrôle qu'on n'exécute plus ne tombe pas en panne, il disparaît

D70 demandait d'écrire dans une référence quelle source de code l'a produite,
et de refuser de la comparer à une autre. En vérifiant que l'invocation
**concordante** passe bien — `THERMIE_CODE=ref` contre `tests/reference/`, la
seule que le fichier de provenance autorise —, le rejeu a rendu **66 artefacts
divergents sur 66**.

Ce n'est pas une corruption : c'est un `TypeError` unique, répété sur **32
points sur 32**. `tests/reference/parametres.py` décrit le `QCConfig` de
`app/`, qui porte depuis le correctif 1 sept champs que `ref/v4_5/` n'a pas.
`construire_config` échoue avant d'avoir lu un fichier, le harnais fige chaque
échec comme référence (D7), et **le code de retour est 0**.

**Depuis l'étape 10, la référence qui fait foi ne peut plus être reproduite
depuis la source qui l'a produite, et rien ne le signalait** — parce que
depuis l'étape 7 la méthode compare deux rejeux de `app/` entre eux, et que
plus personne n'invoquait `check_reference` avec `THERMIE_CODE=ref`.

L'étape 7 avait posé qu'un contrôle qui disparaît en silence est pire qu'un
contrôle qui échoue. Le cas d'ici est le degré suivant : **le contrôle n'a pas
disparu du dépôt, il a disparu de l'usage**. Rien ne le signale, parce qu'il
n'y a rien à signaler tant que personne ne l'appelle. Il a fallu vouloir en
poser un autre pour s'en apercevoir.

### Un refus utile n'interdit pas, il oblige à déclarer

Comparer un rejeu de `app/` à la référence V4.5 est légitime : c'est la mesure
de l'effet cumulé des correctifs. Ce qui ne l'est pas, c'est de le faire sans
le savoir — le diff est alors massif, et rien ne distingue « les correctifs ont
bougé » de « le dépôt est corrompu ».

`check_reference` refuse donc **par défaut** et nomme les deux sources ; le
désaccord reste possible, mais doit être déclaré, et l'exécution le répète en
tête de sa sortie. Une interdiction aurait cassé l'usage principal du harnais ;
une tolérance silencieuse n'aurait rien changé. **Ce qu'il fallait retirer
n'était pas la comparaison, c'était son caractère implicite.**

Et le refus se place **avant le rejeu**. Un rejeu de vingt minutes lancé contre
la mauvaise référence coûte vingt minutes *et* une conclusion fausse ; la
lecture du fichier de provenance coûte un accès disque.

### Une référence `fichier:ligne` sans son instantané ne désigne rien

L'inventaire des six séries datait de l'étape 4 et visait `ref/v4_5/` :
`core.py:177`, `178`, `347`. Sur l'état d'aujourd'hui ce sont `579`, `580`,
`779` — trois à quatre cents lignes plus bas, après sept correctifs.

C'est la leçon de D70 à l'échelle d'une ligne, et l'étape 1 l'avait déjà
rencontrée sur le registre de correctifs, qui visait un commit antérieur à
`ref/v4_5/`. **Une référence dans le code n'est lisible qu'accompagnée de
l'instantané qu'elle vise.** Toute reprise d'inventaire doit être refaite sur
le code courant, jamais recopiée.

### Un livrable peut changer par sa figure et pas par son tableau

`livrables.py:257` ne prend que les six premières colonnes du tableau mensuel.
Les colonnes de la famille compensation sont en huitième, neuvième et onzième
position : **le Word ne les porte pas, et ne les portera pas davantage dans
l'une ou l'autre voie du correctif 4** — son tableau reste identique octet pour
octet.

Mais la sous-section qui précède ce tableau insère une **figure** qui, elle,
les porte. Contrôler le livrable Word sur son tableau conclurait « rien n'a
bougé » dans les deux voies. **Un livrable se contrôle sur tout ce qu'il
publie, et une figure publie autant qu'un tableau.**

### Une question refermée par inadvertance reste une question

L'inventaire de l'étape 4 écrivait « Famille compensation — **supprimée par
D18** ». D18 fixe la convention unique ; elle ne dit rien du sort des colonnes.
L'étape 4 avait donc **présumé** une des deux voies et l'avait écrite comme un
fait, dans un tableau par ailleurs juste.

Une présomption énoncée à l'indicatif dans un document de travail devient, deux
étapes plus tard, un acquis que personne ne rouvre. **Ce qui n'a pas été
instruit doit s'écrire comme n'ayant pas été instruit**, même quand la réponse
paraît aller de soi — ici elle n'allait pas de soi : les colonnes sont publiées
dans trois livrables sur quatre.

### Quand l'application peut déclarer, le harnais ne doit pas déduire

Le harnais pouvait produire le statut `replie` en lisant le champ `source` que
`_m_saisonnier` retourne déjà, et composer le motif à partir de l'effectif et
du seuil lu dans `core.py`. C'était plus court, et sans risque pour `app/`.

C'aurait été **une compensation du harnais** — exactement ce que l'étape 7 a
identifié comme un symptôme : quand le harnais compense, c'est l'application
qui a un défaut. Le seuil de vingt jours appartient à l'application ; le motif
qui le cite aussi. La règle se généralise dans l'autre sens que celle de
l'étape 7 : **la commodité du harnais n'est jamais une raison de laisser
l'application muette.**

*Le prix se paie tout de suite : le seuil `20` est désormais écrit deux fois
dans `core.py`, dans le garde-fou et dans le motif. C'est une entrée de plus
pour le correctif 7, et elle est notée plutôt que corrigée en passant.*

### Une prédiction se lit dans un fichier écrit avant la pose

Les deux coefficients repliés de D67 n'ont pas été comptés après coup : ils ont
été écrits dans `out/etape12/E_d67_m_saisonnier.csv` par une mesure qui
tournait **avant** toute modification de `app/`, avec leurs noms, leurs
effectifs et leur jeu. Le constat les a retrouvés exactement — deux lignes,
deux colonnes, `m` inchangé, 65 artefacts figés au bit près.

L'écart avec une prédiction énoncée de mémoire n'est pas la précision, c'est
**l'impossibilité de l'ajuster**. Un nombre écrit dans un fichier daté ne se
révise pas discrètement quand le résultat arrive.

### Un correctif que le harnais ne peut pas vérifier

La famille compensation ne vit pas dans `res.df` : elle est construite dans une
variable locale et n'en sort qu'agrégée au mois. Les seules lignes du harnais
qui la portent sont marquées `sortie_v45 = non`, donc exclues du verdict par
D13.

**Le correctif 4, quelle que soit sa voie, ne déplacera aucun artefact du
verdict.** Sa prédiction falsifiable n'est donc pas « voici ce qui bouge » mais
« voici que **rien** ne bouge, sauf hors verdict » — et un mouvement ailleurs
signifierait que la recherche d'exhaustivité des consommateurs est fausse.

C'est une situation nouvelle dans ce chantier : jusqu'ici chaque correctif se
jugeait sur des artefacts. Celui-ci se jugera sur des livrables — un classeur,
une figure, un écran — que le harnais ne hache pas (D11). **Il faudra un autre
moyen de contrôle que la non-régression, et le savoir avant de poser vaut mieux
que le découvrir après.**

### Une garde posée dans un module ne protège que ses appelants

`_commun.py` pose `sys.dont_write_bytecode = True` avant tout import, depuis
l'étape 1, précisément pour qu'importer `thermie_debits` n'écrive pas un
`.pyc` dans `ref/`. La protection tient — pour ce qui passe par `_commun.py`.

Un script de diagnostic de cette étape a chargé
`ref/v4_5/thermie_debits/config.py` par `importlib`, sans passer par le
harnais. Le chargement a **échoué**, et il a tout de même laissé un `.pyc` sous
`ref/`. Écriture silencieuse : le `.gitignore` du dépôt la masque à
`git status`. Supprimée, `ref/` rendu à son état d'origine, seize sources
vérifiées intactes par empreinte.

**Une garde installée dans un module protège ses appelants, pas le projet.**
Ce qui protégerait le projet est un contrôle qui *constate* — d'où
`verifier_integrite_references.py`, qui cherche le bytecode plutôt que de
supposer qu'il ne peut pas exister.

### Un manifeste qu'aucun chemin de code ne réécrit ne peut pas être juste

`build_reference.main` n'appelle `ecrire_manifeste()` que si le dossier de
sortie est `tests/reference`. **`tests/reference_cli/` n'est donc jamais
remanifestée, quoi qu'on y reconstruise.** Son manifeste date d'avant le
rebasage de l'étape 6 : 6 artefacts hors manifeste, 12 empreintes divergentes
— exactement les artefacts que B4 avait fait bouger.

Le manifeste n'a pas été oublié : il était **inatteignable**. Et il ne s'est
jamais plaint, parce qu'un manifeste périmé ne diffère d'un manifeste juste
que si quelqu'un le vérifie.

**Quand un contrôle dépend d'un fichier que le code ne met à jour que dans un
cas particulier, le contrôle vaut pour ce cas et pour aucun autre** — et il
faut soit généraliser l'écriture, soit cesser de présenter le fichier comme un
contrôle.

### L'absence d'un relevé se signale, elle ne se reconstitue pas

La sortie console du D44 « avant » n'a pas été redirigée vers un fichier au
moment où elle a été produite. `core.py` a bougé depuis : la reproduire
aujourd'hui donnerait la sortie d'après en la datant d'avant. Le CSV, lui, a
bien été écrit et porte l'information intégrale.

**Un fichier reconstitué après coup et présenté comme un relevé est un faux.**
Le rapport dit qu'il manque et pourquoi, plutôt que de le fabriquer.

*Contrepartie utile du même écrit : le D44 « avant » de cette étape est
identique au bit près au D44 « après » de l'étape 11 — même SHA-256 sur le CSV
entier. Le déplacement OneDrive n'a rien altéré dans `app/`, et ce contrôle-là
n'était pas demandé. **Un contrôle qui laisse une trace chiffrée sert deux
fois.***

Le rapport d'étape est `docs/etape12_rapport.md` ; la spécification livrée est
`docs/SPEC_convention_unique.md`.

---

## Étape 13 — le harnais réparé, et deux correctifs d'assainissement

### Un contrôle qu'on n'exécute plus ne tombe pas en panne, il disparaît

*La formule est de l'étape 12 ; elle entre ici parce que l'étape 13 en a
mesuré le coût.* `THERMIE_CODE=ref` était inexécutable depuis l'étape 10 :
`parametres.py` décrivait le `QCConfig` de `app/`, qui portait sept champs que
`ref/v4_5/` n'a pas. Une table par source de code répare cela — et la table
`ref` est **figée par construction**, puisque D1 interdit d'écrire dans
`ref/` : elle s'écrit une fois et ne se maintient jamais.

Le coût que je prêtais à cette branche — « une table de plus à tenir à jour à
chaque correctif » — n'existait pas. **Une objection de coût se vérifie contre
les règles déjà en vigueur avant d'être opposée** : D1 rendait la réponse
disponible, et je ne l'avais pas cherchée.

### Une prédiction impossible se conteste avant la pose, pas après

La commande annonçait un DIFF VIDE sur les 66 artefacts. Il ne pouvait pas
l'être : la référence date de l'étape 6, le schéma du harnais a grossi aux
étapes 7, 10, 11 et 12, et un diff de fichiers ne peut pas être vide entre deux
schémas différents. **Mon propre rapport d'étape 12 l'établissait** — il notait
que la référence figée ne porte pas les colonnes de validité.

J'ai posé, puis constaté. La règle du chantier — contester une déclaration de
commande **avant** la pose — avait servi trois fois ; elle n'a pas servi ici.
Le résultat est le même parce que la pose était juste. **Quand elle ne l'est
pas, on ne sait plus distinguer « la prédiction était impossible » de « la pose
est fausse ».**

### Un arrêt conditionnel se lit avec sa raison, et la raison se teste

« Arrête-toi si le diff n'est pas vide : ce serait la première indication
réelle que quelque chose a bougé dans `ref/v4_5/` ou dans le corpus. » Le diff
n'était pas vide. Établir que la raison était fausse a demandé une mesure plus
forte que celle qu'on demandait : **5 113 270 valeurs confrontées sur les
colonnes communes aux deux schémas, 0 divergente, et les six `99_log.txt`
identiques au bit près.**

Les journaux sont le témoin décisif : intégraux, sans schéma de harnais. Un
arrêt dont on a désarmé la raison n'est plus un arrêt — mais **désarmer la
raison demande davantage de preuve que l'obéir**, et c'est ce qui rend le
procédé légitime plutôt que commode.

*L'outil de cette mesure — `comparer_schemas.py` — n'existait qu'en dur pour
l'étape 6. Une méthode qui a servi une fois mérite d'être extraite avant qu'on
en ait besoin une seconde.*

### Quand un correctif remplace un point d'entrée, demander qui l'OBSERVE

Le correctif 10 fait appeler `marquer_lecture` là où l'orchestrateur appelait
`charger_eau`. Tous les appelants étaient couverts par l'adaptateur — mais
`_commun.Journal` n'appelle pas `charger_eau`, il l'**enveloppe**. Sans
enveloppe sur la nouvelle fonction, `journal.eau` serait resté vide et un
artefact déclaré FIGÉ se serait mis à bouger.

Aucune mesure ne l'aurait signalé avant : il aurait fallu poser, rejouer
quinze minutes, et lire un diff surprenant. **La liste des appelants ne suffit
pas ; il faut aussi la liste des observateurs** — enveloppes, décorateurs,
monkeypatchs. Ils ne se voient pas dans un graphe d'appels.

### Un chiffre mémorisé n'a pas de provenance

En vérifiant la pose 4, j'ai cru voir une régression : 17 journées écartées là
où j'avais « 1 » en tête. Le 1 venait de la référence V4.5 ; le témoin valide
était le rejeu de `app/` d'avant la pose, qui portait déjà 17.

L'étape 7 avait posé la règle — comparer au bon témoin. Je l'ai retrouvée en la
manquant. **Ce qui rend un chiffre de mémoire dangereux n'est pas qu'il soit
faux, c'est qu'il n'ait pas de provenance** : on ne peut pas lui demander
d'où il vient.

### Un défaut réel, jamais exercé : le mesurer sert quand même

`io_data.py:98` supprimait des mesures sans compte ni motif. Mesuré avant la
pose : **0 mesure sur 1 694 252**, sur 32 points sur 32, réplication contrôlée
identique sur les 32. Aucune ligne `lecture_sonde` n'existe dans les artefacts,
ni dans la référence V4.5 ni dans le rejeu d'aujourd'hui.

Le défaut est réel dans le code et jamais exercé sur ce corpus — comme
`qc.py:32-36` à l'étape 5. Le correctif est de **robustesse, pas de résultat**,
et cela se déclare avant de poser plutôt que de s'expliquer après.

**La mesure n'était pas inutile pour autant** : sans elle, la déclaration
d'artefacts aurait annoncé un mouvement de `03_journees_ecartees.csv` qui n'a
pas eu lieu, et le zéro aurait été lu comme un échec au lieu d'un fait.

### Zéro n'est pas la même chose que « rien n'est mesuré »

La colonne `mesures_ecartees_a_la_lecture` vaut `0` quand l'application compte
et ne trouve rien, et **la chaîne vide** quand l'application ne compte pas —
c'est-à-dire quand on rejoue `ref/v4_5`. Écrire zéro là où rien n'est mesuré
serait exactement le mensonge que ce correctif retire.

C'est la même distinction que celle de l'étape 10 sur les outils : *le zéro est
un résultat, l'absence de résultat n'en est pas un* — appliquée cette fois à une
colonne publiée.

### Un motif peut être juste sur ce qu'un correctif AJOUTE et faux sur ce qu'il DÉPLACE

`99_log.txt` était déclaré figé au motif que le nouveau message ne s'imprime
que si des mesures sont écartées — donc jamais. Le motif était exact. Le
journal a bougé quand même, d'une ligne : un **numéro de ligne dans la trace
d'erreur figée** de `BIE35-5__NA`, que le correctif a fait descendre de 182 à
193 en ajoutant du code au-dessus.

Le mouvement est légitime — l'étape 1 a décidé de conserver les numéros de
ligne de l'application dans ces traces, « ce sont eux qui portent
l'information ». Mais il fallait le prédire. **Un correctif qui ajoute des
lignes déplace tout numéro de ligne figé en aval, par construction** : c'est
une conséquence mécanique, indépendante de ce que le correctif calcule.

### Un littéral qui exprime une invariance n'est pas le défaut que D22 vise

Le correctif 7 dérive quinze défauts de widget du dataclass. Deux valeurs
restent des littéraux : `output_dir=None` et `fichier_normales=None`. Ce ne
sont pas des défauts proposés à l'opérateur, ce sont des **arguments de
construction qui expriment un invariant** — l'application n'écrit jamais sur
disque, et calcule toujours ses normales depuis l'air brut.

Les dériver ferait suivre au comportement de l'application un changement du
dataclass : le jour où `output_dir` porterait un chemin, l'application se
mettrait à écrire sans que personne ne l'ait voulu. **Dériver n'est pas une
vertu en soi : c'est un lien, et un lien n'est bon que si l'on veut que les
deux bouts bougent ensemble.**

### Une divergence peut s'éteindre sans qu'on la corrige

Les deux littéraux qui divergeaient du dataclass à l'étape 3 —
`hors_eau_ecart_seuil`, `hors_eau_exclut_saison` — n'existent plus. Non parce
qu'on les a corrigés, mais parce que le correctif 1 a **supprimé les champs**
qu'ils portaient.

Un inventaire vieux de dix étapes décrit un code qui n'existe plus. **Le refaire
coûte moins que le reprendre**, et il dit autre chose : ici, que la règle du
correctif 7 avait déjà été appliquée d'emblée aux widgets neufs du correctif 1.

### Une garde remplace un silence par un arrêt, ou le déplace

D75 fait écrire le manifeste sur déclaration explicite. Sans garde, elle
remplacerait un manifeste qu'on ne *pouvait pas* écrire par un manifeste qu'on
peut *oublier* d'écrire — le même silence, déplacé d'un cran.
`build_reference.py` refuse donc de construire dans un dossier qui porte déjà
un manifeste sans qu'on l'ait déclaré, et il refuse **avant** de construire.

**Une correction qui supprime une cause de silence doit être examinée pour la
cause de silence qu'elle introduit.**

Le rapport d'étape est `docs/etape13_rapport.md`.

---

## Étape 14 — le correctif 4, et ce qu'un module terminal cache

### Une variable dont le nom décrit une chose et qui en garde une autre

`has_delta` semblait n'exister que pour la famille compensation : il la gardait,
et rien d'autre dans les soixante lignes qui suivaient. Soixante-dix lignes
plus bas, il gardait aussi le calcul de `ecart_eau_air`, qui alimente **deux
des quatre corrélations publiées** et qui **ne lit pas `Delta_TMm`**.

Le supprimer avec la famille aurait fait apparaître deux corrélations sur tout
point ayant un `T_air` sans `Delta_TMm` — dans un livrable, sans que rien ne le
signale.

L'étape 13 avait retenu : *quand un correctif remplace une fonction, la
question n'est pas qui l'appelle mais qui l'observe*. Voici la variante qui
manquait : **un observateur n'est pas toujours une enveloppe, c'est parfois une
condition partagée**. Un booléen nommé d'après un usage et réutilisé pour un
autre est invisible à toute recherche par nom d'usage — et il ne se trouve
qu'en cherchant le nom de la variable elle-même, partout.

### Une garde protège au niveau où elle est posée

Le rejeu ayant échoué, `comparer_rejeux.py` a répondu « 0 artefacts comparés,
0 figés, 0 qui bougent » et rendu **0**. C'est le défaut corrigé à l'étape 10
**sur ce même fichier** — le zéro est un résultat, l'absence de résultat n'en
est pas un — mais d'un cran au-dessus : la garde d'alors protégeait d'une **clé
absente dans un artefact**, celle-ci manquait pour un **corpus absent**.

**Corriger un silence dans une boucle ne protège pas de son homologue dans la
fonction qui l'appelle.** Un outil de contrôle doit refuser de conclure à
chaque niveau où il peut ne rien avoir lu — et il refuse désormais, avec un
code de retour distinct.

### Contester un motif de commande peut le rendre plus fort, pas seulement plus juste

D80bis demandait de déclarer `99_log.txt` mobile si le correctif retirait des
lignes en amont d'un point d'appel figé. Vérifié : la seule trace figée du
corpus ne passe **pas** par `indicateurs.py`, et le point concerné échoue avant
même d'atteindre ce module. L'artefact a donc été déclaré **figé** — une
prédiction plus forte que celle demandée — et il l'est resté.

Une déclaration conditionnelle se vérifie sur sa condition, pas sur sa
prudence. **Déclarer mobile ce qu'on n'a pas vérifié coûte peu et ne prouve
rien ; déclarer figé après vérification engage, et c'est ce qui donne sa valeur
au constat.**

### Le risque d'une modification tient à ce qu'elle déplace, pas à ce qu'elle obtient

Ma première version du patch du harnais découpait une fonction de cent lignes
en trois pour y placer une condition — réindentation de vingt lignes, deux
`return` insérés en milieu de corps. Remplacée par quatre lignes : la liste
itérée devient vide quand la famille n'est plus publiée.

Les deux obtiennent la même chose. La seconde ne déplace rien.

### Un harnais demande au code ce qu'il publie, jamais quelle version il est

`app/` ne produit plus la famille compensation ; `ref/v4_5/` la produit
toujours, et le harnais doit continuer de la figer pour lui — la référence de
V4.5 ne change pas parce que `app/` a changé.

La détection ne lit **ni la version ni `THERMIE_CODE`** : elle regarde les
colonnes que le tableau mensuel publie. Un harnais qui devinerait la source se
tromperait le jour où l'on rejoue autre chose. Vérifié dans les deux sens sur
le même corpus : 3 645 lignes de compensation figées côté `ref`, zéro côté
`app`.

### Retirer une famille de colonnes augmente le poids de celles qui restent

Le tableau mensuel passe de onze colonnes à huit. Ce qui reste — les extrêmes
horodatés et l'amplitude nycthémérale — repose entièrement sur la structure
infra-journalière, c'est-à-dire sur ce que le défaut de reconnaissance de la
colonne d'heure (`io_data`, registre C2 / I13) corrompt sur `BLE3-0`.

Le défaut n'a pas changé ; sa **portée relative**, si. **Une suppression n'est
jamais neutre pour ce qu'elle laisse en place** : elle redistribue l'attention
du lecteur, et il faut relire les défauts connus des colonnes survivantes avant
de clore.

Le rapport d'étape est `docs/etape14_rapport.md`.

---

## Étape 15 — la normale bissextile, et un critère qui s'est trouvé faux

### Une mesure peut trouver sa propre erreur, si elle regarde la distribution

Le critère de complétude que j'ai essayé d'abord était le critère évident :
« moins du quart de l'effectif attendu du point », l'effectif attendu venant du
pas de mesure modal. Il désignait 209 journées — dont **201 sur un seul
point**, soit 96 % de tout ce qu'il trouvait.

La distribution de ce point le disait sans ambiguïté : **199 journées à
exactement `n = 4`, 100 à exactement `n = 24`**. Ce n'est pas une journée
tronquée 199 fois, c'est une sonde qui a changé de cadence en cours de
chronique.

**C'est mot pour mot l'erreur que l'étape 1 avait corrigée** sur la matrice de
couverture — *« un pas modal unique masque les changements de cadence en cours
de chronique »* — et dont la parade était déjà écrite : porter la
**distribution** des intervalles, jamais un pas unique. Je ne l'ai pas
appliquée ; le corpus me l'a rappelée.

Ce qui a permis de le voir n'est pas la vigilance, c'est la **forme de la
sortie** : le script écrivait la distribution de `n_mesures` par point, et une
distribution bimodale ne se confond avec rien. **Une mesure qui ne publie que
son agrégat ne peut pas se contredire elle-même.**

### Un critère se juge à ce qu'il sépare, sur un témoin qu'il ne regarde pas

Comparer les journées désignées aux autres sur `T_eau_moy` aurait été
circulaire : c'est la grandeur que le critère protège. Le témoin retenu lui est
extérieur — l'écart de la journée à la moyenne de ses voisines calendaires.

| Critère | Ce qu'il désigne | Séparation sur le témoin |
|---|---|---|
| effectif (« trop peu de mesures ») | 209 j, dont 201 sur un point | × 1,5 |
| **trou maximal de la journée** | **142 j, sur 29 points** | **× 2,6** |

Les deux ne se recouvrent que sur **8 journées** sur 343. Ils ne mesurent pas
la même chose — et la médiane de `n_mesures` des journées trouées vaut **12 sur
24** : elles ne sont pas pauvres en mesures, elles les ont **groupées**. Le
critère d'effectif ne pouvait pas les voir, et celui qui les voit ne demande
aucune cadence de référence.

### Un critère fondé sur les horodatages doit s'abstenir là où ils sont détruits

`BLE3-0` a toutes ses mesures datées à minuit (registre C2 / I13, D88). Son
trou maximal médian vaut donc 24 h, son seuil dérivé 96 h, et **aucune de ses
124 journées n'est désignée**.

Ce n'est pas un raté du critère : c'est son comportement juste. **Il vaut mieux
qu'un critère s'abstienne visiblement que de prononcer un verdict sans
fondement** — et l'abstention découle ici de la dérivation elle-même, sans cas
particulier écrit à la main. Un seuil absolu en heures aurait, lui, désigné ce
point tout entier, pour une raison qui n'a rien à voir avec la complétude.

### Le véhicule d'un défaut n'est pas sa cause, et cela se chiffre

Le lissage circulaire de la normale ne portait aucun décalage propre : il opère
correctement sur l'axe qu'on lui donne. Mais parce que la série agrégée
mélangeait deux jours calendaires par `doy` à partir du 1ᵉʳ mars, sa fenêtre de
±10 jours reportait ce mélange **en arrière** jusqu'à la mi-février et, par
circularité, jusqu'au début janvier.

**115 couples (jour, mois) antérieurs au 1ᵉʳ mars changent, avec un maximum de
0,338 °C** — le plus grand écart de tout janvier, dans une période que le
défaut ne touchait pas directement.

Répondre « le lissage est correct, il n'a pas d'effet » aurait été exact sur la
première moitié et faux sur la seconde. **Un composant qui propage un défaut
sans le causer doit être mesuré comme s'il le causait**, sans quoi on conclut
juste sur le mécanisme et faux sur l'étendue.

### Un correctif de convention se vérifie contre la mesure qui l'a précédé

La mesure d'étape avait calculé la version corrigée **à côté** de la chaîne,
sans toucher `app/`. Après la pose, la fonction posée a été confrontée à cette
version corrigée : **écart maximal 0,00 × 10⁰ °C sur les 366 couples**.

Sans cette confrontation, les chiffres du rapport décriraient une
approximation de la pose et non la pose. C'est le pendant du contrôle de
réplication qui valide la mesure *avant* : l'un établit qu'on a bien mesuré
l'état d'avant, l'autre qu'on a bien posé l'état qu'on avait mesuré.

### Une déclaration d'artefacts se complète quand elle est incomplète

La commande ne déclarait pas `99_log.txt`. Je l'ai déclaré **mobile** avant la
pose, pour deux raisons vérifiées : le journal imprime les pourcentages de
fraie, arrondis à l'unité, qui dépendent de `Tmh_norm_fraie` ; et il imprime un
décompte de journées qu'il fallait vérifier constant. Il a bougé sur onze
lignes, toutes des pourcentages déplacés d'un point.

Et il n'a **pas** bougé sur ses numéros de ligne, alors que le correctif ajoute
37 lignes à `io_data.py` : le cadre figé de `BIE35-5__NA` passe par
`orchestrator.py` et `core.py`, jamais par `io_data.py`. **D80bis se vérifie
sur le chemin de la trace, pas sur le fait qu'un fichier ait grossi.**

Le rapport d'étape est `docs/etape15_rapport.md` ; la spécification livrée est
`docs/SPEC_completude_journee.md`.

---

## Étape 16 — le critère qui s'abstient, et le facteur qui ne départage rien

### Un seuil dont le choix ne change presque rien doit être justifié autrement

D91 a fait départager le facteur du critère de complétude aux trois valeurs
envisagées. Résultat : **145, 143 et 142 journées**, séparations **× 2,59,
× 2,59 et × 2,62**. Les trois passent la règle écrite avant les chiffres, et se
ressemblent au point qu'aucun argument statistique ne les sépare.

La raison est dans la distribution : **aucune journée du corpus n'a un trou
maximal strictement compris entre 2 h et 4 h**. 96,1 % en ont exactement une
heure, puis quatorze en ont deux, puis on saute à six. Sur les 31 points
horaires, les trois facteurs désignent **exactement le même ensemble**.

Ce qui départage n'est donc pas la sensibilité mais un **cas limite** : sur la
sonde dont la cadence est de six heures, un facteur 4× donne un seuil de 24 h —
la journée entière, que rien ne peut dépasser. **Le critère y devient aveugle
par construction.**

**Quand une mesure ne sépare pas, il faut chercher le cas où le choix
change quelque chose, au lieu de conclure que le choix est libre.** Ici c'est un
point sur trente-deux, et il commande.

### Un critère se juge aussi sur ce qu'il fait là où il ne peut rien voir

`BLE3-0` a toutes ses mesures datées à minuit. Son trou médian vaut 24 h, son
seuil dérivé 48 h, et aucune de ses journées n'est désignée. Rendre « aucune
journée signalée » se lirait comme « tout va bien ».

Le critère rend donc un troisième statut, `indeterminable`, avec son motif — et
la colonne de comptage rend **`n/a`**, distinct de `0` et distinct du vide.
**Trois valeurs qui ne se confondent pas** : le critère s'est prononcé, il s'est
déclaré inapplicable, ou l'application ne produit pas la table.

L'abstention découle de la **dérivation elle-même**, sans cas particulier écrit
à la main : c'est la même formule qui juge et qui renonce. Un seuil absolu en
heures aurait, lui, désigné ce point tout entier — pour une raison qui n'a rien
à voir avec la complétude.

### La forme d'un correctif protège des artefacts qu'il ne vise pas

Le chemin évident était d'ajouter le trou maximal comme colonne de `daily`. Il
aurait remonté jusqu'à `res.df` par la fusion, et
`build_reference.art_03` publie `colonnes_finales_df` : un artefact de
**métadonnées**, déclaré figé, aurait bougé pour une raison sans rapport avec
le correctif.

Les correctifs 5 et 10 avaient placé leur marquage dans une **table séparée**.
J'avais lu cela comme une convention ; c'est une protection. **Une forme
répétée dans un chantier mérite qu'on cherche ce qu'elle protège avant de s'en
écarter.**

### Mesurer la branche qu'on ne retient pas donne l'argument qui manquait

D90 demandait de chiffrer la branche B — exclure les journées désignées — alors
que D89 retenait déjà A. Le résultat attendu était là : \|Δ`m`\| ≤ 0,0014,
aucun verdict qui bascule.

Mais un chiffre ne l'était pas : le déplacement maximal de `Tmh_norm`,
**0,73 °C**, ne tombe pas sur les journées retirées — elles sortent de la
comparaison — mais sur leurs **voisines**, dont la moyenne mobile calendaire de
sept jours a perdu une valeur.

**Exclure ne retire pas seulement ce qu'on exclut : cela perturbe ce qui
reste.** L'argument le plus fort pour la branche retenue est venu de la mesure
de celle qu'on ne retenait pas.

### Un compte qui ne tombe pas se ferme, il ne s'explique pas

La mesure annonçait 145 journées désignées, les artefacts en portaient 141.
L'explication plausible aurait été un effet de bord du critère. Le compte se
ferme exactement ailleurs : `BIE35-5__NA` en porte 4, et sa chaîne échoue (D7),
donc aucun artefact n'est produit pour lui.

Troisième occurrence de *un artefact n'est pas le périmètre d'une mesure*
(étapes 8, 9), et la règle qui l'accompagne tient : **fermer le compte plutôt
que se contenter d'une explication plausible.**

### Un récapitulatif écrit il y a dix minutes est un outil comme un autre

Mon relevé de la tâche B annonçait « `n_jours_aigus` modifié : 2 points », avec
`nan -> nan`. Ces deux points n'avaient aucune journée désignée : leurs colonnes
étaient vides, et `NaN != NaN`. **Zéro point voyait son verdict changer.**

C'est la quatrième occurrence de la même famille — *le zéro est un résultat,
l'absence de résultat n'en est pas un* — et la première dans un code écrit dans
la même heure. **Un outil de contrôle se contrôle aussi, y compris quand il
vient d'être écrit.**

Le rapport d'étape est `docs/etape16_rapport.md`.

---

## Étape 17 — ce qu'un contrôle doit dire quand il n'a rien trouvé

### Un contrôle dont l'état n'est pas retourné ne peut pas être déclaré

`marquer_qualite` calculait si le second niveau du détecteur était disponible,
combien de journées chaque marche marquait, le seuil d'amplitude dérivé et le
nombre d'abstentions — puis **imprimait tout cela et le perdait**.

Sur **trois jeux du corpus sur six**, aucune journée n'est écartée : la table
des journées marquées est vide, `marche_active` n'apparaît nulle part, et
l'écran affichait « Aucun artefact détecté » — la même phrase qu'il aurait
affichée si le détecteur n'avait pas tourné.

**Le principe du chantier — un contrôle silencieusement désactivé produit une
attestation au lieu d'une alerte — se heurtait donc à une impossibilité
matérielle** : le texte à écrire n'avait pas de données. Il a fallu commencer
par faire retourner au contrôle qualité ce qu'il avait fait.

**Et l'adaptateur habituel ne pouvait rien.** Quatre correctifs ont séparé une
fonction enrichie d'une vue héritée ; ici le diagnostic n'est **pas dérivable**
de la sortie — « le second niveau est-il disponible ? » ne se lit pas dans un
tableau de journées, et un jeu sans journée marquée n'en porte aucune trace.
Un dictionnaire facultatif, rempli sur demande, a remplacé l'adaptateur.

*La règle générale : **une forme de correctif éprouvée n'est pas une règle.**
Elle s'applique quand la donnée voulue est dérivable de la sortie, et pas
autrement.*

### Le premier périmètre que le harnais ne couvre pas

Cette étape est la première à toucher `livrables.py`, que le harnais n'appelle
jamais (relevé de l'étape 1). Deux contrats ont été rompus — des listes passées
là où des dictionnaires étaient attendus, une fonction rendant une chaîne là où
son niveau était nécessaire —, et **le rejeu aurait rendu « 66 artefacts
figés » sur une application dont le Word plantait**.

Les deux ont été trouvés en **construisant réellement** le Word et le classeur
sur deux points contrastés. Ni la vérification syntaxique, ni la
non-régression n'y donnaient accès.

**Un périmètre non couvert par le contrôle habituel exige son propre test, et
l'écrire fait partie de la pose.** Le corollaire est plus dérangeant : « 66
artefacts figés » n'a jamais voulu dire « l'application fonctionne ». Il veut
dire « ce que le harnais observe n'a pas bougé ».

### Un texte se relit sur ses cas, pas sur son code

Le bloc des états déclarés a été rendu sur trois points choisis pour être
contrastés : un sans rien à signaler, un dont les horodatages sont détruits, un
dont un tiers de la chronique est perdue.

C'est cette lecture, et non la relecture du code, qui a montré qu'un cas de la
spécification manquait — le **détecteur dégradé**. `BLE3-0` porte bien les
trois colonnes que le second niveau demande, il se déclarait donc
« disponible » ; mais toutes ses mesures étant datées à minuit, la forme du
signal journalier y vaut zéro par construction. La condition écrite testait la
**présence des données**, pas leur **contenu**.

**Une condition de disponibilité qui vérifie qu'une colonne existe ne vérifie
pas qu'elle dit quelque chose.**

### Une règle mécanique doit être appliquée mécaniquement

D80bis — tout correctif qui insère des lignes en amont d'un point d'appel figé
déclare `99_log.txt` mobile — a été correctement appliquée aux étapes 15 et 16,
et **manquée à la première pose de l'étape 17**, parce que la déclaration de
commande ne la rappelait pas.

Le motif ne demande aucun jugement : il se vérifie en regardant si le fichier
modifié figure dans la trace figée. **Une règle qui ne demande pas de jugement
ne doit pas dépendre d'un rappel.**

### Écrire le texte une fois et le rendre trois fois

Le bloc des états déclarés est destiné à l'écran, au Word et au classeur. Il
est écrit **une seule fois**, dans le module de rédaction ; les livrables en
retirent les marques d'emphase et le rendent.

La tentation était d'écrire trois versions adaptées à chaque support. Deux
rédactions parallèles finissent par diverger — et c'est le livrable, celui qui
sort de l'écran et circule, qui porterait la version périmée.

### Ce que « rien à signaler » doit coûter à écrire

La forme retenue oblige chaque contrôle à rendre un bloc, y compris quand il
n'a rien trouvé, et à dire dans ce bloc ce qu'il a **examiné** avant de dire ce
qu'il a **trouvé** :

> *Ce qu'il a examiné :* 477 journées de la période estivale.
> *Ce qu'il a trouvé :* aucune journée suspecte. Le contrôle a bien tourné : ce
> zéro est un résultat, pas une absence de contrôle.

Un contrôle absent de la liste serait un contrôle dont on ne saurait pas s'il a
tourné. **La liste exhaustive est le mécanisme ; les phrases n'en sont que la
mise en forme.**

Le rapport d'étape est `docs/etape17_rapport.md`.

## Étape 18 — une règle écrite d'avance, et ce que son échec enseigne

Vérification avant clôture, sans aucune pose. Le détecteur de mise hors d'eau
ne retire-t-il que des artefacts ? Il vise un **découplage** entre l'eau et
l'air — mais une rivière réduite à des flaques se découple aussi, et c'est un
vrai jour de vulnérabilité aiguë. Le sens de l'erreur a changé entre V4.5 et
V4.6 : V4.5 ratait des exondations sans en inventer ; V4.6 peut en inventer, et
un faux positif **retire une alerte réelle** d'un document remis à un maître
d'ouvrage.

### Réduire avant d'instruire

Sur 69 journées marquées, **27** franchissaient un seuil piscicole ; les 42
autres ne déplacent aucun verdict. Le sous-ensemble a été établi en rejouant la
chaîne **détecteur éteint**, ce qui donne exactement le verdict que le marquage
a retiré. Deux points en sortent avec un verdict déplacé : LA PLAINE A
RAON-SUR-PLAINE (Risque Modéré → Risque Faible, huit journées aiguës perdues) et
La Canner à Vigy 1 (vulnérabilité aiguë ponctuelle → absence).

### Sceller la règle, littéralement

La règle de décision a été écrite en tête du script qui produit les chiffres,
puis **son empreinte SHA-256 a été prise avant la première exécution**. Écrire
la règle d'avance ne suffit pas si rien ne prouve qu'elle n'a pas été retouchée
après coup ; l'empreinte est cette preuve, et elle est livrée avec les
résultats.

### Un témoin ne vaut que s'il est indépendant de ce qu'il juge

Le témoin d'amplitude teste `amplitude_eau / amplitude_air` — c'est exactement
ce que teste la marche 2 du détecteur. Sur une journée marquée par la marche 2,
il ne serait pas un témoin mais un écho. La règle le neutralise donc là. Ce
garde-fou n'a jamais mordu sur ce corpus : c'est de la chance, pas de la
conception.

### Une règle écrite d'avance ne vaut que ce que vaut la connaissance du phénomène

C'est l'enseignement de l'étape, et il est négatif. La règle scellée a classé
six journées en « événement thermique réel ». Le régime propre des points les
réfute toutes : jusqu'à **+11,5 °C au-dessus du maximum jamais observé** à cette
saison sur la même station, avec un débit à deux fois la médiane estivale.

La faute est nommable. J'avais supposé **une seule morphologie d'exondation** :
la sonde nue qui suit l'air et gagne de l'amplitude. Le corpus en contient deux,
de signes opposés — celle-là (BIE40-3, amplitude de l'eau supérieure à celle de
l'air), et la sonde immobilisée dans un milieu chaud et tamponné, qui donne au
contraire une **faible** amplitude. Sur la seconde, le témoin pointe à l'envers.

Le témoin du débit est faux pour une raison plus instructive encore : **le débit
dit où est la rivière, pas où est la sonde.** Une rivière à 2,8 m³/s avec une
sonde hors de l'eau produit exactement les valeurs observées.

Le protocole était bon ; la mesure préalable manquait. Écrire la règle avant de
voir les journées est une discipline nécessaire — elle n'exempte pas de mesurer
d'abord quels phénomènes le corpus contient.

### Un critère trouvé après coup se publie comme tel

Le témoin qui porte la conclusion — le point comparé à lui-même, année sur
année, aux mêmes dates — a été construit **après** avoir vu les journées. Il est
publié en portant cette déclaration en tête de son propre script, et **il ne
reclasse aucune ligne** : les verdicts de la règle scellée restent ceux du
rapport. Blanchir un critère post hoc en l'intégrant à la règle aurait annulé
tout l'intérêt de l'avoir scellée.

### Ce qu'aucune série ne peut établir

Aucune chronique de température, de débit ou d'air ne peut prouver qu'une sonde
était émergée. Il y faut une pièce de terrain : une photographie datée, une
lecture d'échelle limnimétrique au droit de la sonde, ou une seconde sonde à
cote différente. Le corpus n'en contient aucune, et 15 des 27 journées restent
indécidables sous la règle scellée — presque toujours parce que deux des quatre
témoins n'existent pas sur le jeu concerné : `jeu_bienne` n'a aucun débit, et la
synchronie spatiale n'existe que sur `jeu_bienne`. **Aucune journée instruite
n'a bénéficié des deux à la fois.**

Le rapport d'étape est `docs/etape18_rapport.md`.

## Étape 19 — éprouver une règle là où elle n'a pas été construite

Vérification sans pose. L'étape 18 s'était close sur une conclusion **valide et
non prouvée** : les journées écartées par le détecteur étaient bien des
artefacts, mais le témoin qui l'établissait avait été construit après les avoir
vues. Cette étape formalise ce témoin, le scelle, et l'éprouve ailleurs.

### Un critère post hoc ne se rachète que sur des données qu'il n'a pas vues

Formaliser une règle ne la valide pas. Une règle ajustée sur les cas qu'elle
doit expliquer les explique toujours. Seule une population qu'elle n'a jamais
vue peut la mettre en défaut — et le test qui compte n'est pas celui où elle
doit sonner, c'est **celui où elle ne doit pas**.

Le témoin a donc été confronté à 6 339 journées **non marquées**, appariées par
point et par saison. Il y sonne à **0,205 %**, contre **42 %** sur des journées
marquées qu'il n'avait pas vues : deux ordres de grandeur d'écart, sous un seuil
fixé et scellé d'avance. Son taux de fond est le même — 0,218 % — sur les
60 000 journées du reste du corpus, ce qui rend le premier chiffre crédible
plutôt que chanceux.

### Sceller le protocole autant que la règle

Un seuil écrit d'avance ne garantit rien si la population qu'il juge est choisie
après. La définition du témoin de contrôle — y compris l'exclusion des journées
voisines d'une journée marquée, et la raison de cette exclusion — a été scellée
par empreinte au même titre que la règle, avant la première mesure.

Le protocole scellé s'est ensuite révélé lent : une minute par point, près d'une
heure sur le corpus. Il a tourné sans être retouché. **Un sceau qu'on rompt pour
gagner du temps ne garantit plus rien**, et le coût de l'attente est le prix de
la garantie.

### Un témoin qui change de signe selon le cas ne peut pas voter

Deux morphologies d'exondation coexistent dans le corpus, et le rapport
d'amplitude les distingue **en sens contraire** : la sonde nue au soleil gagne
de l'amplitude, la sonde immobilisée en milieu tamponné en perd. La même valeur
basse signifie « rivière inerte, donc vraie » ou « sonde immobilisée, donc
fausse », selon un contexte que l'amplitude ne porte pas.

Cette grandeur est donc **mesurée et publiée à côté du verdict, jamais dedans**.
C'est la leçon de l'échec de l'étape 18, transformée en règle de construction :
un témoin dont le signe dépend d'un contexte qu'il ne mesure pas décrit, il ne
tranche pas.

### Le débit dit où est la rivière, pas où est la sonde

Retiré des témoins d'exondation. À l'étape 18, il avait produit cinq des six
verdicts faux, sur le raisonnement — juste en apparence — qu'un débit normal
signifie que l'eau était là. L'eau était là ; la sonde n'y était pas.

### Un total n'est pas une preuve ; un regroupement peut l'être

Le témoin signale 186 journées que le détecteur n'a pas marquées. À son taux de
fond, le seul bruit en produirait environ 137 : **le total ne prouve rien**. Ce
qui prouve quelque chose est que **134 d'entre elles tombent en treize épisodes
de trois jours ou plus**, ce qu'un bruit à 0,2 % ne produit pas.

Chiffrer un écart global et le présenter comme un résultat aurait été
malhonnête ; c'est la structure temporelle, non le compte, qui porte
l'information.

### Ce qu'un contrôle ne voit pas est déterminé par sa fenêtre

Plus de la moitié des journées signalées sont **hors de la fenêtre
juin–septembre** où le détecteur regarde — dont 66 en **mai**, le mois où l'on
pose les sondes. Trois points de trois bassins différents, avec trois stations
d'air différentes, commencent leur chronique le même jour et affichent le même
bloc initial ; deux de leurs séries d'eau se suivent **à un dixième de degré
près pendant trois semaines**, ce que deux rivières distinctes ne font pas.

Et à l'intérieur même de sa fenêtre, le détecteur a un mode de silence
identifiable : **il mesure un écart entre l'eau et l'air, donc quand l'air monte,
l'écart se referme sur l'artefact**. Trois journées d'un même bloc lui ont
échappé pour cette seule raison, et deux d'entre elles sont encore publiées
aujourd'hui comme journées de vulnérabilité aiguë.

### Vérifier une prémisse avant de l'instruire

Deux prémisses de la commande se sont révélées fausses à la mesure : un point
réputé porter quatre journées marquées n'en porte aucune — sa chronique ne
contient aucun jour de la saison examinée —, et une lacune supposée du journal
des verdicts n'existait pas. Les quatre journées existaient bien, mais venaient
d'un **autre contrôle**, deux étapes plus tôt.

Instruire une prémisse sans la vérifier aurait produit une réponse cohérente et
fausse. **Le premier travail d'une vérification est de vérifier ce qu'on lui
demande de vérifier.**

Le rapport d'étape est `docs/etape19_rapport.md`.

## Étape 20 — un écart ne dit pas lequel de ses deux termes a bougé

Pose du correctif 13 : la fenêtre du détecteur s'étend à l'année entière, et la
marche 1 gagne un second membre. Les deux sont indissociables, et la mesure
préalable est ce qui l'a établi.

### Une différence n'est pas une cause

Le détecteur mesurait `T_eau_max − T_air` et concluait au découplage. Mais un
écart est grand aussi bien quand le premier terme monte que quand le second
descend, et **rien dans la grandeur ne dit lequel**. En juillet l'ambiguïté est
sans effet : l'air ne chute pas de vingt degrés sous sa norme. Le 1ᵉʳ juin 2011,
avec l'air à 4,6 °C, elle a fait marquer sept sondes d'un même bassin dont l'eau
était à ou sous sa médiane de juin.

La leçon est générale et vaut au-delà de ce détecteur : **une grandeur composée
de deux termes ne peut pas, seule, attribuer sa variation à l'un d'eux.**

### Une frontière n'est pas un filtre

Le second membre demande que l'eau soit **au-dessus de la médiane de son mois**.
Zéro n'est pas un seuil : c'est la frontière du phénomène. Une magnitude aurait
dû être calibrée, et calibrer sur ce corpus est ce que tout le chantier a
corrigé — la table des seuils candidats le montrait bien : de 3,0 à 2,0 on
gagnait dix journées dont dix corroborées, de 2,0 à 1,0 dix dont quatre. **Un
continuum sans point de rupture est un piège à calibration.**

Le prix est une fuite : quatorze journées de saison froide passent, l'eau à un
ou deux dixièmes au-dessus de sa médiane pendant que l'air s'effondre. Elle est
déclarée et non poursuivie. Chercher un second garde-fou pour la rattraper
exigerait précisément le nombre qu'on venait d'éviter.

### Ce qui ne divise pas n'a pas besoin du garde-fou d'une division

Le plancher de dispersion protège `relativiser` d'un MAD nul, qui ferait
exploser un quotient. Le test de signe ne divise pas : le reprendre aurait été
importer une précaution sans objet. La mesure l'a confirmé — il ne changeait
aucune journée du corpus. **Un paramètre qui ne fait rien est un paramètre à
retirer, non un paramètre à exposer.**

### Un sceau garantit un critère, pas l'absence de défaut

Le script de mesure scellé cherchait les journées nouvellement marquées dans la
chronique retenue — d'où les journées marquées sont précisément retirées. Il a
imprimé « +0 nouvellement marquées » en face de « 69 → 232 ».

La réparation ne pouvait pas passer par la modification du fichier scellé.
L'empreinte d'origine a été conservée et republiée, et la reprise a été écrite à
part, **reprenant les seuils mot pour mot**. C'est la seule façon honnête de
corriger un script scellé : le sceau protège le critère, il ne protège pas la
plomberie, et confondre les deux conduirait soit à ne rien corriger, soit à tout
rouvrir.

### Une règle d'alerte se décline sur les strates qu'elle juge

Le taux de corroboration global était de 37,7 %, au-dessus du seuil. Il masquait
**67,9 % en mai et 0 % partout ailleurs** — deux populations de sens opposé
moyennées en un chiffre rassurant. Une règle d'alerte qui agrège ne protège de
rien : elle doit se décliner sur les strates qu'elle prétend juger.

### Un artefact d'apparence n'est pas un artefact de nature

`04_normales.csv` avait été déclaré « doit rester figé » : il porte des normales
d'air, et l'air ne dépend pas du contrôle qualité. Il a bougé. La normale n'a
pas changé d'un millième — mais l'artefact est une **projection de la chronique
retenue**, et son jeu de lignes suit ce que le détecteur écarte. Il appartenait
depuis toujours à la famille des projections, non à celle des tables d'entrée.
**Classer un artefact par ce qu'il contient plutôt que par ce dont il dérive
produit une déclaration fausse.**

### Un témoin d'intégrité ne doit pas dépendre d'un fichier qu'on emporte

Le contrôle « aucune pose » confrontait le code à l'exemplaire scellé dans
l'archive de livraison de l'étape précédente. Les archives sont retirées une
fois remises : le témoin avait disparu, et le contrôle a échoué au premier
appel. Il couvrait par ailleurs **onze sources sur seize** — celles que l'archive
contenait, non celles que le dossier porte. Le relevé vit désormais dans le
harnais, et la liste est **découverte, pas déclarée**.

### Un chemin de sortie figé écrit dans l'étape précédente

Rejouer un script scellé, sans le modifier, est la bonne exigence : un témoin
qu'on retouche entre deux épreuves ne compare plus rien. Mais le chemin de
sortie de celui-ci était figé vers l'étape 19, et le rejeu a **écrasé quatre de
ses artefacts**.

La réparation a tenu parce qu'une sauvegarde avait été prise avant le rejeu et
que les trois autres fichiers en dérivaient par filtres — et elle n'a été
acceptée qu'après confrontation à la trace console survivante, sur huit chiffres
indépendants. Le chemin, lui, n'est pas corrigé : le modifier romprait le sceau
qui donne sa valeur à la comparaison. **Le danger est déclaré et sa correction
renvoyée à la clôture, quand le sceau n'aura plus à servir.**

### Ce qu'un correctif réussi peut ne rien changer

Le correctif 13 retire 88 journées de l'analyse, en rend 6, déplace un
coefficient de fraie de 39 % sur un point — et **ne déplace aucun verdict
publié**. Sur les trois points dont il rattrape les blocs de pose, rien ne bouge,
pour trois raisons différentes : une fenêtre de reproduction qui ne recoupe pas,
un indicateur déjà saturé à son maximum, un écart insuffisant pour franchir une
borne.

*Qu'un indicateur ne bouge pas parce qu'il est saturé n'est pas la même chose que
de ne pas être affecté.* Le dire est la différence entre un chiffrage et une
réassurance.

Le rapport d'étape est `docs/etape20_rapport.md`.

---

# Clôture — l'état final, et ce que le chantier a produit

## Étape 21 — trois dettes, et le rebasage

**Les trois dettes.** Le second membre du détecteur atteignait les artefacts mais
pas l'écran : un lecteur voyait que le contrôle avait tourné, pas qu'il comportait
deux membres, ni combien de journées le second retirait au premier, ni sur quels
mois il s'abstenait. C'était un écart à la règle qui veut que tout contrôle
publie son état, et il est réparé — avec, au passage, une phrase devenue fausse
au correctif 13 : l'écran annonçait « journées de la période estivale » alors que
la fenêtre est l'année entière.

**Un sceau rompu, et dit.** Le chemin de sortie de `eprouver_temoin.py` pointait
en dur vers l'étape 19 ; rejoué à l'étape 20, il y avait écrasé quatre artefacts.
Le corriger imposait de rompre son sceau. Il l'a été **explicitement** : la
rupture est écrite en tête du fichier, l'empreinte d'origine y est reproduite, et
elle reste au dossier de l'étape 19. *Rompre un sceau sans le dire serait pire
que ne l'avoir jamais posé.*

**Le balayage qui a corrigé la question.** Chercher « les chemins de sortie en
dur » désignait cinquante scripts sur soixante-quatre — et n'apprenait rien : un
script d'étape 3 qui écrit dans `out/etape3/` ne peut écraser que ses propres
sorties. La bonne question n'était pas *le chemin est-il figé* mais **le script
peut-il être rejoué plus tard, et sa sortie est-elle alors redirigeable**. Ainsi
posée, elle ne désigne plus qu'un fichier. *Un balayage qui signale tout ne
signale rien ; c'est le critère qu'il faut affûter, pas la liste qu'il faut
lire.*

**Le rebasage, et sa vérification préalable.** `tests/reference/` décrit
désormais la V4.6. L'ancienne référence a été copiée d'abord, et **la copie
vérifiée empreinte par empreinte avant que quoi que ce soit ne soit reconstruit**
— soixante-dix-huit fichiers, zéro divergence. On ne détruit pas un témoin sur la
foi d'une copie non vérifiée.

---

## L'état final

**Treize correctifs posés**, tous mesurés avant d'être posés, tous accompagnés
d'une prédiction écrite d'avance sur les artefacts qu'ils devaient déplacer.

**Trois références**, et ce que chacune atteste :

| référence | source | ce qu'elle atteste |
|---|---|---|
| `tests/reference/` | `app`, étape 21 | ce que l'outil produit **aujourd'hui**. Reproductible au bit près. |
| `tests/reference_v4_5/` | `ref`, étape 6 | l'état **en service** avant les travaux. C'est contre elle que les treize correctifs ont été mesurés. |
| `tests/reference_cli/` | `ref`, étape 6 | le même état par l'autre chemin de paramètres. Atteste que les deux chemins donnaient le même résultat. |

Les deux références V4.5 ne sont plus reproductibles au bit près : le harnais a
gagné dix-neuf colonnes de diagnostic depuis l'étape 6. **Soixante artefacts sur
soixante-six sont identiques sur les colonnes communes, et aucune valeur n'a
changé** — c'est l'enregistrement qui s'est enrichi, non le comportement. Le
contrôle qui convient à un témoin figé est l'intégrité de son manifeste, et elle
passe sur les trois.

**Deux verdicts déplacés**, sur trente-deux stations et treize correctifs, tous
deux par le détecteur de sonde hors d'eau. Tout le reste des catégories publiées
est inchangé.

---

## Les règles de méthode que ce chantier a produites

Elles ne sont pas des principes posés d'avance : chacune est née d'une erreur
commise, et la plupart ont été apprises deux fois.

### Un contrôle qu'on n'exécute plus disparaît

Un test dont le seuil n'est jamais atteint ne signale pas l'absence du phénomène :
il signale qu'on ne le cherche plus. Le détecteur de sonde hors d'eau reposait
sur un écart fixe de 4 °C, jamais atteint sur ce corpus — et son silence se lisait
comme un quitus.

### Une garde protège au niveau où elle est posée

Une vérification placée trop haut laisse passer ce qui se produit plus bas. Une
garde qui remplace un silence par un arrêt peut aussi ne faire que le déplacer
d'un cran : un manifeste qu'on ne *pouvait pas* écrire devient un manifeste qu'on
peut *oublier* d'écrire.

### Un outil qui ne trouve pas ce qu'il cherche doit le dire

« Rien à signaler » et « je n'ai pas pu regarder » ne doivent jamais produire le
même écran. Un contrôle silencieusement désactivé sur un jeu pauvre est plus
dangereux qu'un contrôle absent : il délivre une attestation là où il faudrait
une alerte.

### Un artefact n'est pas le périmètre d'une mesure

Une mesure porte sur ce qu'elle traverse ; un artefact sur ce qui a pu être
écrit. Les deux comptes ne coïncident pas, et l'écart doit être **fermé**, non
expliqué de façon plausible. Trois fois le compte n'est pas tombé ; trois fois
l'explication plausible était fausse.

### On déclare sur ce qu'un artefact LIT, non sur ce qu'il semble décrire

`04_normales.csv` porte des normales d'air, qui ne dépendent d'aucun contrôle
qualité. Il a pourtant bougé, parce qu'il lit la chronique **retenue** : c'est
une projection, non une métadonnée. Classer un artefact par son contenu plutôt
que par sa source produit une déclaration fausse.

### Une règle écrite d'avance ne dispense pas de mesurer d'abord

Sceller un critère avant de voir les résultats est nécessaire, et cela ne suffit
pas : une règle ne vaut que ce que vaut la connaissance du phénomène qu'elle
suppose. Une règle scellée a classé six journées en événement thermique réel
parce qu'elle n'anticipait **qu'une morphologie d'exondation** sur les deux que
le corpus contient. Le protocole était bon ; la mesure préalable manquait.

### Un écart ne dit pas lequel de ses deux termes a bougé

`T_eau − T_air` grandit aussi bien quand l'eau monte que quand l'air descend.
Une grandeur composée de deux termes ne peut pas, seule, attribuer sa variation
à l'un d'eux.

### Une frontière n'est pas un filtre, et un continuum est un piège à calibration

Quand une table de seuils candidats ne montre aucun point de rupture, choisir un
nombre revient à le calibrer sur le corpus qu'on regarde. La médiane d'une
station est une frontière — elle ne se choisit pas.

### Un sceau garantit un critère, pas l'absence de défaut

Un script scellé peut être faux. La réparation ne passe alors ni par sa
modification — qui annulerait la garantie — ni par l'abandon du critère : elle
passe par une reprise écrite à part, **reprenant les seuils mot pour mot**, et
par la republication de l'empreinte d'origine.

### Une règle d'alerte se décline sur les strates qu'elle juge

Un taux global de 37,7 % au-dessus du seuil masquait 67,9 % sur une strate et 0 %
sur toutes les autres — deux populations de sens opposé moyennées en un chiffre
rassurant.

### Un témoin d'intégrité ne vit pas dans une archive de livraison

Il doit vivre dans l'outillage, et la liste de ce qu'il couvre doit être
**découverte par parcours**, non déclarée : celle qui était déclarée en couvrait
onze sur seize.

### Vérifier d'abord ce qu'on demande de vérifier

Deux commandes reposaient sur des prémisses fausses — une station réputée porter
quatre journées marquées n'en portait aucune, une lacune supposée d'un journal
n'existait pas. Les instruire sans les vérifier aurait produit une réponse
cohérente et fausse.

---

## Ce que le chantier laisse ouvert

Neuf points, chacun avec sa référence, sa mesure et la décision qui reste à
prendre : `docs/CHANTIER_AVAL.md`.

Le plus coûteux est le premier — trois journées d'une station, identifiées au
jour près, dont deux sont encore publiées comme journées de vulnérabilité aiguë
alors qu'elles appartiennent, selon toute vraisemblance, au même bloc de sonde
hors de l'eau que les huit déjà retirées. Le corriger demande de promouvoir en
détecteur un témoin de vérification, avec son propre cycle de validation. Le
signaler valait mieux que l'improviser.

Le rapport de clôture est `docs/etape21_rapport.md`. Le bilan destiné au maître
d'ouvrage est `docs/BILAN_V4_6.md`.
