# THERMIE_BIO V4.6 — Rapport d'étape 2

*Alignement du harnais, puis mesure. Aucune ligne de code applicatif modifiée.*

---

## §0 — Carnet de bord

### Ce que le contrôle avait vu, et ce qu'il faut y ajouter

Le diagnostic amont est exact : le harnais figeait `run_cli.py` + `QCConfig()`
et non l'application en service. Trois précisions le complètent, et aucune ne
l'affaiblit.

**Le détecteur n'est pas coupé, il est déréglé.** J'attendais un
`hors_eau=False` quelque part dans `app.py`. Il n'y est pas. La case
« Détection sonde hors d'eau » (`app.py:161`) reprend bien `qc.hors_eau`, donc
**vrai**. Ce sont deux *autres* widgets qui divergent, et pour une raison
mécanique : ils passent une valeur littérale au lieu de reprendre le champ du
dataclass. Détail en §1.

**Ce n'est pas « 0 écarté partout ».** `jeu_02` écarte bien **1** journée par
les bornes physiques — le 24/05/2011, `T_eau_max = 48,637 °C`. Son classeur le
dit et le harnais le retrouve. Les trois autres détecteurs sont à zéro sur les
cinq jeux ; le détecteur de bornes, lui, a tiré une fois.

**Une réserve sur quatre ne se reproduit pas.** C3 annonçait un défaut
d'agrégation de `journees_ecartees_qc`. Je l'ai cherché et il n'existe pas :
sur les deux jeux où le contrôle qualité écarte quelque chose, la somme des
lignes annuelles retombe exactement sur la ligne `annee=-1`. Vérifié ligne à
ligne contre `03_journees_ecartees.csv`. §3.

### Ce qui m'a fait changer d'approche

**La confrontation aux classeurs ne pouvait pas rester déclarative.** J'ai
d'abord voulu vérifier les cinq jeux à la main. C'est intenable : cinquante
valeurs, et une tolérance à définir pour chacune. J'ai écrit
`verifier_classeurs.py`, qui lit les classeurs, lit la référence reconstruite,
et pose la seule tolérance légitime — **l'arrondi du livrable lui-même** : `m`
y est écrit à quatre décimales, le SGVT à deux. Rien d'autre n'est toléré. Les
cinquante confrontations passent, dont trente et une au chiffre exact.

**La mesure d'aveuglement m'a donné le résultat inverse de celui annoncé.** Le
mécanisme attendu — une sonde chroniquement mal posée décale sa propre médiane
et devient invisible au critère relatif — **ne s'observe pas sur ce corpus**.
La corrélation entre la médiane propre d'un point et le fait qu'il soit perdu
vaut +0,13 à q95, +0,03 à q99, et **−0,17** à q99,5, c'est-à-dire de signe
contraire. J'ai cherché la raison et je la donne au §4 ; je n'ai pas cherché à
sauver la prédiction.

### Ce que j'ai corrigé dans mon propre code

| Défaut | Effet |
|---|---|
| `fichiers_a_manifester()` hachait tout sauf les `.py` | Les classeurs `.xlsx` et `.docx` entraient dans `MANIFEST.sha256`. Remplacé par un motif explicite `^\d{2}_....(csv\|json\|txt)$` (C1) |
| `check_reference.comparer()` diffait les fichiers entiers | Les lignes recalculées par le harnais comptaient dans le verdict. Scindées et sorties du verdict (C4, D13) |
| Le tableau A2 comptait 27 « écarts » | Dont les chemins de fichiers — `examples/eau.csv` contre le fichier téléversé — et douze champs valant `None` des deux côtés sous deux formulations. Deux catégories ajoutées : *hors comparaison* et *identique (None des deux côtés)*. Il reste **4** écarts, dont 2 sur le contrôle qualité |
| La matrice opposait `pas_eau` jeu par jeu | Cette colonne porte **la même phrase sur les six lignes** : une déclaration de portée corpus, recopiée. Cinq écarts fabriqués à partir d'un seul énoncé (C5) |

### Ce que j'ai vu et pas touché

`app.py:162-163` et `app.py:166` sont deux valeurs littérales qui prennent le
pas sur le dataclass. C'est le cœur de la divergence. Je ne les touche pas :
l'étape n'autorise aucune modification applicative, et la question de savoir
lequel des deux jeux de valeurs est le bon n'est pas la mienne. Elle est au §6.

---

## §1 — La divergence localisée (Tâche A)

### A1 — Le détecteur est-il coupé, ou jamais atteint ?

**Ni l'un ni l'autre : il est actif des deux côtés, et déréglé d'un côté.**

`app.py:156` construit bien un `QCConfig()`, donc avec tous les défauts du
dataclass. Les lignes suivantes ré-affectent chaque champ depuis un widget.
Douze de ces widgets passent `qc.<champ>` comme valeur par défaut et
reproduisent donc exactement le dataclass. **Deux passent une valeur
littérale** :

```
app.py:161   qc.hors_eau = st.checkbox("Détection sonde hors d'eau", qc.hors_eau)
                                                                     ^^^^^^^^^^^
                                                     le detecteur est ACTIF

app.py:162   qc.hors_eau_ecart_seuil = st.slider("Écart hors d'eau seuil (°C)",
app.py:163                                       1.0, 15.0, 10.0, 0.5)
                                                             ^^^^
                        defaut LITTERAL 10.0 — config.py:81 dit 4.0

app.py:166   qc.hors_eau_exclut_saison = st.checkbox(
                 "Exclure la saison JJAS entière", False)
                                                  ^^^^^
                        defaut LITTERAL False — config.py:84 dit True
```

Le détecteur tourne donc dans l'application, mais il cherche un écart
`T_eau_max − T_air > 10 °C` au lieu de `> 4 °C`, et lorsqu'il déclenche il
n'écarte que les jours suspects au lieu de la saison entière. Sur ce corpus,
un écart de plus de 10 °C ne se produit presque jamais en été : le détecteur
ne tire que **22 fois** sur 23 816 points-jours, contre 8 255 avec le seuil
de 4 °C et l'exclusion de saison.

L'asymétrie mérite d'être nommée précisément : le seuil `4.0` du dataclass
n'est atteignable par l'interface que si l'opérateur *déplace* le curseur.
La valeur documentée dans `config.py` n'est donc jamais celle qui s'applique
par défaut dans l'application.

### A2 — Tous les autres paramètres

Tableau complet des 50 champs des trois dataclasses :
`out/etape2/chemins_de_parametres.csv`. Synthèse :

| Statut | Champs | Ce que cela veut dire |
|---|---|---|
| identique | 22 | même valeur des deux côtés |
| identique (None des deux côtés) | 12 | deux formulations, un seul `None` |
| hors comparaison | 4 | `fichier_eau`, `fichier_air`, `fichier_debit`, `fichier_debit_desinf` — ils désignent le jeu, pas un réglage |
| **ÉCART** | **12** | dont **4** peuvent changer un calcul |

Les douze écarts, et pourquoi huit d'entre eux ne changent rien :

| Champ | Application | run_cli | Effet |
|---|---|---|---|
| `QCConfig.hors_eau_ecart_seuil` | **10,0** | **4,0** | **OUI** |
| `QCConfig.hors_eau_exclut_saison` | **faux** | **vrai** | **OUI** |
| `AnalyseConfig.contexte_piscicole` | selon le classeur | `intermediaire` | **OUI**, mais en aval de `T_norm` — voir A3 |
| `AnalyseConfig.espece_repere` | selon le classeur | `None` → ombre commun | **OUI**, en aval de `T_norm` — voir A3 |
| `AnalyseConfig.faire_volet_climatique` | faux | vrai | aucun — ne produit que des figures (`orchestrator.py:283-286`) |
| `AnalyseConfig.output_dir` | `None` | `examples/outputs/` | aucun — ne pilote que l'écriture (`orchestrator.py:272-280`) |
| `AnalyseConfig.periode_affichage` | `None` | `None` | aucun — n'agit que sur l'axe des figures |
| `SourcesConfig.nom_cours_eau` | `Cours d'eau` | `Cours d'eau` | aucun — titre |
| `SourcesConfig.localisation_sonde` | `''` | `Localisation` | aucun — métadonnée de livrable |
| `SourcesConfig.nom_station_debit` | `''` | `Station hydrométrique` | aucun — métadonnée |
| `SourcesConfig.nom_station_meteo` | `''` | `Station météo` | aucun — métadonnée |
| `SourcesConfig.eau_nom_fichier` / `air_nom_fichier` | nom téléversé | `''` | aucun — sert à deviner l'extension quand la source est un flux d'octets, sans effet quand c'est un chemin (`io_data.py:47-48`) |

**Deux paramètres, et deux seulement, expliquent la divergence de la chaîne
lecture → T_norm.**

### A3 — Le contexte piscicole agit-il en amont de T_norm ?

**Non pour `Tmh_norm` et `Tmax_norm`. Oui pour `Tmh_norm_fraie`.**

Le contexte résolu `ctx` est construit à `orchestrator.py:70` mais n'est passé
à aucune fonction avant `orchestrator.py:170`. Or la chaîne lecture → T_norm
s'achève avant :

| Étape | Ligne | Reçoit `ctx` ? |
|---|---|---|
| `io.charger_eau` | `orchestrator.py:83` | non |
| `io.charger_air_brut` | `orchestrator.py:101` | non |
| `io.calculer_normales_ecarts` | `orchestrator.py:108` | non |
| `qcmod.controle_qualite` | `orchestrator.py:155` | non |
| `core.fusionner` | `orchestrator.py:160` | non |
| `core.analyse_sensibilite` → **m** | `orchestrator.py:166` | non |
| `core.analyse_vulnerabilite` → **Tmh_norm, Tmax_norm** | `orchestrator.py:170` | **oui**, mais seulement pour les seuils |

`analyse_vulnerabilite` reçoit `ctx` et le lit à `core.py:180` — `seuil_chr`,
`seuil_aigu`, `plancher_faible` — après avoir calculé `Tmh_norm` et
`Tmax_norm` aux lignes 177-178, qui n'utilisent que `m` et `Delta_TMm_liss`.
La fenêtre estivale de `m` est écrite en dur `[6, 7, 8, 9]` à `core.py:135`.

**La seule voie par laquelle le contexte remonte dans une température
normalisée** est `core.analyse_fraie_croissance` (`orchestrator.py:174`) : la
fenêtre de reproduction de l'espèce détermine les mois passés à
`core._m_saisonnier` (`core.py:344`), donc le coefficient de `Tmh_norm_fraie`
(`core.py:347`). Et cette fenêtre n'est pas la même selon l'espèce :

| Contexte | Espèce | Mois |
|---|---|---|
| salmonicole | truite fario | 1, 2, 3, 10, 11, 12 |
| intermédiaire | ombre commun *(défaut)* | 3, 4, 5 |
| intermédiaire | barbeau | 4, 5, 6, 7 |
| cyprinicole | brochet | 2, 3, 4 |
| cyprinicole | brème | 4, 5, 6, 7 |

Conséquence à noter pour D16 : la fenêtre **mars-avril-mai** est celle de
l'ombre commun seul. Et la zone cyprinicole évalue **deux** espèces, donc
produit **deux** `m_saisonnier` et **deux** séries `Tmh_norm_fraie` — c'est
observé sur `jeu_04` (`Tmh_norm_fraie[brochet]`, 178 jours, et
`Tmh_norm_fraie[brème]`, 327 jours).

---

## §2 — La référence reconstruite (Tâche B)

### Ce qui a été fait

L'ancienne référence est déplacée en `tests/reference_cli/`, avec son
`LISEZ-MOI.md` et son manifeste régénéré (60 artefacts). Elle documente le
comportement détecteur allumé, et c'est sur elle que porte la mesure du §4.

`tests/reference/` est reconstruit avec le paramétrage de l'application. Un
onzième artefact y apparaît, `10_parametres.json`, qui porte **chaque
paramètre avec sa provenance** — `code`, `classeur`, ou `defaut` — et sa
justification en clair.

### Ce que le changement de paramétrage déplace

| | référence seconde (CLI) | **référence qui fait foi** (application) |
|---|---|---|
| points produisant un indicateur | 18 / 32 | **31 / 32** |
| journées écartées par le contrôle qualité | 8 565 | **91** |
| journées retenues après jointure | 34 376 | **67 101** |
| points en échec `ValueError` | 14 | **1** |

Le seul échec restant est `BIE35-5__NA`, et il n'a rien à voir avec le
contrôle qualité : sa chronique s'arrête le **24 mai 2012** et ne couvre donc
aucun jour de juin à septembre. `analyse_sensibilite` lève sur 0 jour estival
(`core.py:137`). L'échec est figé comme référence (D7).

### Le critère d'acceptation

`out/etape2/verification_classeurs.csv` — **50 confrontations, 50 retrouvées,
0 écart.**

| Jeu | Jours bruts | Écartés QC | Retenus | m | R² | n été | SGVT |
|---|---|---|---|---|---|---|---|
| jeu_02 | 1546 = | 1 = | 1215 = | 0,292779 *(livrable 0,2928)* | 0,205933 | 445 = | 2,333 |
| jeu_03 | 1164 = | 0 = | 1164 = | 0,408173 *(0,4082)* | 0,515040 | 477 = | 2,500 |
| jeu_04 | 855 = | 0 = | 855 = | 0,229455 *(0,2295)* | 0,211228 | 347 = | 3,167 |
| jeu_05 | 1121 = | 0 = | 1121 = | 0,442153 *(0,4422)* | 0,495936 | 369 = | 1,667 |
| jeu_exemples_v45 | 303 = | 0 = | 201 = | 0,519531 *(0,5195)* | 0,872844 | 122 = | 3,667 |

Les vingt-cinq grandeurs entières — jours bruts, écartés, retenus, jours
estivaux, composantes du SGVT — sont retrouvées **au jour près et à l'unité
près**. Les vingt-cinq grandeurs flottantes sont retrouvées à l'arrondi du
livrable, l'écart maximal étant de **4,7 × 10⁻⁵** sur `m` (jeu_05) et de
3,3 × 10⁻³ sur le SGVT — soit exactement le demi-dernier chiffre affiché.
Aucun écart n'a été arrondi : la tolérance appliquée est écrite dans
`verifier_classeurs.py` et vaut 5 × 10⁻⁵ sur les grandeurs à quatre décimales.

Un contrôle croisé confirme que rien n'a bougé en amont : le hachage de
`jeu_02/00_format_detecte.json` est **identique** à celui de l'étape 1
(`75d35fee1b39…`). La détection de format et le chargement ne dépendent pas du
contrôle qualité, et ne bougent pas.

### jeu_bienne — quels paramètres, et pourquoi

`jeu_bienne` ne porte aucun classeur : **rien n'atteste d'un choix de
l'opérateur**. Les paramètres appliqués, et leur provenance telle qu'écrite
dans `10_parametres.json` :

| Paramètre | Valeur | Provenance | Motif |
|---|---|---|---|
| tout le bloc `qc` | celui de l'application | `code` | les widgets d'`app.py` sont les mêmes quel que soit le jeu |
| `contexte_piscicole` | `intermediaire` | **`defaut`** | défaut de l'interface : `selectbox` `app.py:70-72` `index=1`. C'est aussi le défaut du dataclass et celui de `run_cli.py:16` — les deux chemins coïncident ici, ce qui rend le choix moins arbitraire qu'il n'en a l'air |
| `espece_repere` | `None` → ombre commun | **`defaut`** | `radio` `app.py:78-79` `index=0` ; `None` y est équivalent (`config.py`, `contexte():52`) |
| `mode` | `thermie_seule` | `defaut` | aucun fichier de débit dans le jeu : `avec_debits` est faux quel que soit le mode |

Le contexte retenu n'a **aucun effet** sur `m`, `Tmh_norm` ni `Tmax_norm`
(§1, A3). Il n'agit que sur `Tmh_norm_fraie` et sur les grilles aval, hors
périmètre. Le choix par défaut est donc sans conséquence sur ce que l'étape
cherche à figer, et cela doit être dit plutôt que masqué.

---

## §3 — Réserves levées (Tâche C)

### C1 — Manifeste sans binaires

`_commun.est_artefact()` reconnaît désormais un artefact au motif
`^\d{2}_....(csv|json|txt)$` dans un dossier de jeu. `MANIFEST.sha256` compte
**66 lignes** (6 jeux × 11 artefacts) et **zéro** `.xlsx` ou `.docx`.
`check_reference.artefacts()` applique le même filtre.

Les classeurs **restent dans le dossier** (D11) : `tests/reference/jeu_02/`
contient toujours ses deux binaires. Ils ne sont ni hachés, ni diffés.

### C2 — Sortie du déterminisme livrée

`out/etape2/determinisme.txt`, sortie intégrale de `check_reference.py` après
reconstruction complète, code de retour inclus. Les 32 points sont rejoués et
comparés un à un. Fin du fichier :

```
66 artefact(s) compare(s).
DIFF VIDE — la reference est reproductible.
code de retour : 0
```

Le fichier n'est pas un extrait : il porte la trace des 32 points rejoués, la
liste des divergences hors verdict s'il y en avait, et le code de retour.

### C3 — `journees_ecartees_qc` par année : le défaut ne se reproduit pas

**Ce n'est ni un défaut du harnais ni un comportement de V4.5 : la colonne est
juste.** Vérifié en recalculant les effectifs annuels depuis
`03_journees_ecartees.csv` et en les confrontant ligne à ligne :

```
jeu_02     : 245 journées QC, lignes annuelles divergentes : 0
jeu_bienne : 8320 journées QC, lignes annuelles divergentes : 0
```

Sur `tests/reference_cli/jeu_02/02_effectifs.csv`, la ventilation est
`2011 → 123` et `2012 → 122`, dont la somme fait bien les 245 de la ligne
`annee=-1`.

L'origine probable de l'observation est la **forme du fichier**, et elle est
réelle : sur quatre jeux sur six la colonne est à zéro *partout*, ligne
`annee=-1` comprise, parce que le contrôle qualité n'y écarte rien ; et sur
`jeu_02` les quatre premières lignes du fichier sont `-1 → 245`, puis
`2008 → 0`, `2009 → 0`, `2010 → 0`. Lire le début du fichier donne exactement
l'impression décrite. Les deux années non nulles sont en cinquième et sixième
position.

Le code responsable est `build_reference.art_02` (`build_reference.py`, boucle
`for a in sorted(annees)`), qui filtre `res.rapport_qc` par année avec le même
`pd.to_datetime(...).dt.year` que pour les autres colonnes. Rien à corriger.

### C4 — Colonne `sortie_v45`

Ajoutée à `07_t_norm.csv`. Les trois séries de la famille *normalisation*
portent `oui` ; les trois de la famille *compensation* portent `non`, puisque
V4.5 ne les expose qu'agrégées au mois et que le harnais applique la formule
citée. Sur `jeu_04` : 2 215 lignes `oui`, 2 565 lignes `non`.

`check_reference.comparer()` renvoie désormais deux listes. Les écarts portant
sur des lignes `sortie_v45=non` sont **imprimés séparément et n'entrent pas
dans le code de retour** (D13). La mécanique est dans `_scinder_sortie_v45()`,
qui laisse intacts les artefacts dépourvus de cette colonne.

### C5 — Requalification des « écarts » de `corpus.csv`

**Confirmé pour l'un, corrigé pour l'autre. Il reste UN écart, pas deux.**

**`jeu_04/format_eau` — confirmé.** Déclaré `xlsx`, sans plus. Le fichier
porte trois feuilles : `DONNÉES`, `Données d'événement`, `Détails`. La
déclaration est muette sur un caractère que la colonne demande explicitement
(« nom de la feuille, ligne d'en-tête décalée »). Écart réel.

**`jeu_bienne/pas_eau` — corrigé, ce n'en est pas un.** La déclaration dit
« infra-journalier ». J'avais observé « 1 h **et 1 j** », le jour venant de
`BLE3-0`. Vérification faite sur la source : la colonne `chmes_heure` de
`BLE3-0.xlsx` porte **24 valeurs horaires distinctes** et **2 951 intervalles
de 3 600 s**. La source est strictement horaire. C'est V4.5 qui la rend
journalière, en ne reconnaissant pas cette colonne (`io_data.py:79-82`, règle
`startswith`). L'écart n'est donc pas entre la mémoire de l'expert et la
source — il est entre la source et sa lecture, et il est déjà au registre
(correctif C2 / I13).

**Les cinq lignes `pas_eau` n'étaient qu'un seul énoncé.** La colonne porte la
**même phrase, mot pour mot, sur les six lignes** de `corpus.csv` : c'est une
déclaration de portée corpus, recopiée par jeu. L'opposer jeu par jeu à une
distribution d'intervalles fabriquait cinq écarts à partir d'une seule
affirmation. Évaluée **une fois**, au niveau du corpus, elle est **conforme** :

> déclaré : *infra-journalier (horaire, quelques périodes à 15 et 30 min)*
> observé : 43 s, 15 min, 30 min, 3 557 s, 1 h, 6 h, 1 j

Et les « quelques périodes » sont localisées : 15 min sur `BIE32-4` (842),
`BIE35-5__NA` (5 224) et `BIE40-3` (8 031) ; 30 min sur huit fichiers de
`jeu_bienne`, de 6 487 à 13 096 intervalles chacun.

`docs/etape1_ecarts_corpus.md` passe de 7 écarts à **1**, sur 50
confrontations. La colonne « observé » de `pas_eau` est désormais préfixée
« tel que V4.5 le lit », et signale les fichiers dont la source est
infra-journalière alors que la lecture ne l'est pas.

---

## §4 — Mesure d'aveuglement (Tâche D)

### Les règles de décision, posées avant tout chiffre

1. Le régime mesuré est celui de `tests/reference_cli/`, **détecteur allumé au
   seuil absolu de 4 °C**, puisque c'est le comportement qu'un correctif
   viendrait remplacer.
2. **Critère absolu** — la condition exacte de `qc.py:64-65` : jour de juin à
   septembre, `T_air` renseignée, et `T_eau_max − T_air > 4 °C`.
3. **Critère relatif** — même fenêtre, même grandeur, comparée à la médiane du
   **même point au même mois** : `ecart_rel = ecart − médiane_{point,mois}(ecart)`,
   déclenchement si `ecart_rel > seuil`.
4. Le seuil relatif est un **quantile de la distribution poolée** de
   `ecart_rel` sur l'ensemble des points-jours de la fenêtre — c'est ce qui
   rend les points comparables entre eux, seule raison de relativiser.
5. Un **jour** est *perdu par le relatif* s'il est marqué par l'absolu et pas
   par le relatif.
6. Un **point** est *perdu par le relatif* si l'absolu le marque au moins un
   jour et le relatif aucun.
7. **Quatre** quantiles sont testés — 0,90, 0,95, 0,99, 0,995 — et tous sont
   rapportés, y compris ceux qui déplaisent.

Assiette : **23 816 points-jours** sur **31 points**. Le 32ᵉ, `BIE35-5__NA`,
n'a aucun jour de juin à septembre et sort de la mesure.

### Les chiffres

| quantile | seuil relatif | jours abs. | jours rel. | les deux | **jours perdus** | jours gagnés | pts abs. | pts rel. | **pts perdus** |
|---|---|---|---|---|---|---|---|---|---|
| 0,90 | 3,453 °C | 3 408 | 2 382 | 1 881 | 1 527 | 501 | 30 | 31 | **0** |
| 0,95 | 4,460 °C | 3 408 | 1 191 | 1 042 | 2 366 | 149 | 30 | 28 | **2** |
| 0,99 | 6,498 °C | 3 408 | 239 | 234 | 3 174 | 5 | 30 | 25 | **5** |
| 0,995 | 7,565 °C | 3 408 | 120 | 120 | 3 288 | 0 | 30 | 16 | **14** |

Points perdus, nommément :

- **q = 0,90** — aucun.
- **q = 0,95** — `La Moselle à Hielle`, `Le ruisseau de la Flotte à Château-Voue`.
- **q = 0,99** — les deux précédents, plus `FLU8-4`, `LIZ5-5`, `TAC16-4`.
- **q = 0,995** — quatorze : `ABI3-6`, `BCH5-7`, `BIE0-3`, `BIE5-2`,
  `BIE50-5`, `BIE51-0`, `BLE3-0`, `FLU8-4`, `GRO9-1`, `HRI7-7`, `LIZ5-5`,
  `La Moselle à Hielle`, `Le ruisseau de la Flotte à Château-Voue`, `TAC16-4`.

Le détail point par point est dans `out/etape2/aveuglement_par_point.csv`
(124 lignes, 31 points × 4 quantiles).

### Le mécanisme attendu ne s'observe pas

**Il faut le dire aussi nettement que si je l'avais observé : sur ce corpus,
les points perdus par le critère relatif ne sont pas ceux dont la médiane est
décalée.**

| quantile | médiane propre des points **perdus** | des points **conservés** | corrélation médiane / perte |
|---|---|---|---|
| 0,95 | +1,07 °C (n = 2) | +0,73 °C (n = 28) | **+0,127** |
| 0,99 | +0,55 °C (n = 5) | +0,86 °C (n = 25) | **+0,027** |
| 0,995 | −0,18 °C (n = 14) | +1,21 °C (n = 16) | **−0,173** |

À q = 0,995, la relation est de **signe contraire** à la prédiction : les
points perdus ont une médiane *plus basse* que ceux qui sont conservés.

**Pourquoi, et c'est vérifiable.** Le mécanisme suppose un point dont la
médiane propre est elle-même dans la zone suspecte, au point de contaminer sa
référence. **Aucun point du corpus n'est dans ce cas** : la colonne
`mediane_deja_au_dessus_du_seuil_absolu` de `out/etape2/aveuglement_medianes.csv`
vaut *non* sur les 31 points. La médiane la plus haute est celle de `LIZ13-5`
à **+2,80 °C**, contre un seuil absolu de 4 °C ; les six points aux médianes
les plus élevées — `LIZ13-5`, `BIE56-1`, `BIE50-5`, `BIE46-5`, `BIE37-9`,
`BIE40-3`, de +2,00 à +2,80 °C — ne sont perdus ni à q95 ni à q99.

Ce qui gouverne réellement la perte est autre chose : un seuil poolé est **un
seul nombre** appliqué à tous, et un point le franchit ou non selon
l'amplitude de ses propres excursions au-dessus de sa médiane. Les points
perdus sont les chroniques **courtes** — `La Moselle à Hielle` (122 jours),
`Le ruisseau de la Flotte` (369), `TAC16-4` (228), `FLU8-4` (214) —, celles
qui ont trop peu de jours pour produire une excursion extrême.

**L'effet symétrique existe aussi, et il n'était pas demandé.** À q = 0,90, le
critère relatif marque **18 jours sur `Le ruisseau de Gorze à Gorze`, que
l'absolu ne marque jamais** — ce point a une médiane de −2,25 °C et aucun jour
au-dessus de +4 °C absolu, mais 18 jours anormaux au regard de son propre
comportement. C'est précisément ce que la relativisation est censée attraper,
et c'est le miroir du mécanisme d'aveuglement.

Sur les dix points où le relatif perd le plus de jours — `BIE56-1` (409
jours perdus), `BIE37-9` (246), `BIE40-3` (244), `BIE42-7` (242),
`BIE50-5` (236) — la perte est massive et porte sur des points que l'absolu
marque abondamment : 20 à 30 % de leurs jours estivaux.

**Aucune conclusion n'est tirée sur le seuil à retenir.** La mesure est
livrée ; le choix ne relève pas de cette étape, et D15 interdit d'importer un
seuil du projet clos.

---

## §5 — Conventions et aval (Tâche E)

### Les six séries

| Série | Formule | Coefficient | Fenêtre d'estimation | Calcul |
|---|---|---|---|---|
| `Tmh_norm` | `Tmh − m × Delta_TMm_liss` | `m` estival | juin-sept., en dur `core.py:135` | `core.py:177` |
| `Tmax_norm` | `T_eau_max − m × Delta_TMm_liss` | `m` estival | idem | `core.py:178` |
| `Tmh_norm_fraie` | `Tmh − m_s × Delta_TMm_liss` | `m` **saisonnier** | fenêtre de reproduction de l'espèce (§1, A3) | `core.py:347` |
| `T_moy_comp` | `T_eau_moy − Delta_TMm` | **aucun** (m ≡ 1) | sans objet | `indicateurs.py:88` |
| `T_max_comp` | `T_eau_max − Delta_TMm` | **aucun** | sans objet | `indicateurs.py:89` |
| `T_min_comp` | `T_eau_min − Delta_TMm` | **aucun** | sans objet | `indicateurs.py:90` |

Deux écarts séparent les familles : le coefficient, et l'anomalie — **lissée**
sur `normalisation_lissage_delta` jours (7 par défaut) pour la première,
**brute** pour la seconde.

### Aval — ce que D18 fera bouger

**Famille *normalisation* — conservée par D18.**

| Série | Consommateur | Nature |
|---|---|---|
| `Tmh_norm` | `core.py:182`, `core.py:185` | **% de stress chronique** → `pct_chr`, `cat_chr` |
| | `core.py:613`, `core.py:623` | **`analyse_debits_inflexion`** — recherche de `Q*_vuln` |
| | `core.py:992`, `core.py:998` | **`analyse_relation_debit_temperature`** — verdict du levier débit |
| | `figures.py:71`, `88-92` | figure de chronique, courbe « eau COMPENSÉE » |
| | `figures.py:239`, `243` | figure de vulnérabilité, une courbe par année |
| | `figures.py:774`, `801` | stress chronique glissant |
| `Tmax_norm` | `core.py:183`, `core.py:186` | **nb de jours létaux** → `n_aigu`, `cat_aigu` |
| | `core.py:614` | `analyse_debits_inflexion` |
| | `figures.py:239`, `244` | figure de vulnérabilité |
| | `figures.py:810`, `820` | létalité glissante |
| `Tmh_norm_fraie` | `core.py:354` | **sévérité fraie** → `P_fraie` → composante du SGVT |
| | `figures.py:390`, `443` | figure fraie-croissance |

Ces deux séries alimentent donc **trois des quatre composantes du SGVT** et
**les débits de référence**. Elles ne bougeront pas.

**Famille *compensation* — supprimée par D18. Voici exactement ce qui
disparaît :**

| Série | Consommateur | Ce qui disparaît |
|---|---|---|
| `T_max_comp` | `indicateurs.py:114` | colonne **« Tmax comp (°C) »** du tableau mensuel |
| `T_min_comp` | `indicateurs.py:115` | colonne **« Tmin comp (°C) »** |
| `T_moy_comp` | `indicateurs.py:129` | ligne annuelle **« Tmm30j comp (°C) »** |
| — | `figures.py:1151`, `1163-1166` | deux courbes en tirets de `fig_indicateurs_resume` (« Tmax compensée », « Tmin compensée ») |
| — | `livrables.py:554-557` | trois colonnes de la feuille **`05_Indicateurs`** du classeur |
| — | `app.py:589-591` | trois colonnes du tableau Streamlit et de son export CSV |

**Aucune de ces trois séries n'alimente un score, un seuil ou un débit de
référence.** Vérifié par recherche exhaustive : leurs seules occurrences sont
celles listées. Les corrélations de `indicateurs.py:157-175` portent sur
`T_eau_moy` et l'amplitude brutes, jamais sur les séries compensées.

**Un point à noter pour le périmètre du portage :** le tableau du DOCX ne
prend que les **six premières colonnes** (`livrables.py:257`,
`cols = [c for c in t.columns][:6]`). Or les colonnes compensées sont en
huitième, neuvième et onzième position. **Le rapport Word ne les porte pas
aujourd'hui.** La suppression sera invisible dans le livrable Word, et visible
dans le classeur Excel, dans l'application et dans une figure.

L'ordre de grandeur du changement n'est pas cosmétique. Sur `BIE0-3` le
1ᵉʳ août 2020, le même maximum journalier de 19,30 °C vaut **18,32 °C** en
`Tmax_norm` et **12,84 °C** en `T_max_comp`. Sur `jeu_03` en janvier, le
tableau mensuel affiche `Tmax = 10,81 °C` et `Tmax comp = 17,57 °C`.

### `m_saisonnier` — repli et écart

**La règle de repli**, `core._m_saisonnier` :

| Garde-fou | Ligne | Condition |
|---|---|---|
| échantillon insuffisant | `core.py:251` | `len(sub) < 20` |
| variance expliquée trop faible | `core.py:258` | `r2 < 0.30` |
| pente aberrante | `core.py:258` | pente hors `[0 ; 1,2]` |

Dans les trois cas, retour de `m_estival` avec `source="estival_repli"`.

**Fréquence sur le corpus** (référence qui fait foi, 32 appels sur 31 points —
`jeu_04` en compte deux, une par espèce cyprinicole) :

| | nombre |
|---|---|
| `m_saisonnier` **retenu** | **28** (88 %) |
| repli sur `m_estival` | **4** (12 %) |
| ↳ pour `n < 20` | 2 — `BLE3-0` (n = 7), `GRO9-1` (n = 14) |
| ↳ pour `R² < 0,30` | 2 — `La Canner à Vigy` brème (R² = 0,238, n = 327), `La Moselle à Hielle` (R² = 0,062, n = 67) |
| ↳ pour pente aberrante | **0** |

**Écart `m_saisonnier − m_estival`, sur les 28 points où les deux existent :**

| | valeur |
|---|---|
| médiane de l'écart signé | **−0,091** |
| minimum | **−0,222** (`BIE40-3` : 0,562 → 0,340) |
| maximum | **+0,272** (`La Canner à Vigy`, brochet : 0,229 → 0,502) |
| médiane de l'écart absolu | **0,114** |

L'écart est **systématiquement négatif sur `jeu_bienne`** — 25 points sur 25,
de −0,002 à −0,222 — et positif sur les trois points hors Bienne où le
saisonnier est retenu. Le signe suit la fenêtre : la fenêtre mars-avril-mai de
l'ombre commun donne un couplage air-eau plus faible que la fenêtre estivale ;
les fenêtres qui débordent sur l'été (barbeau 4-5-6-7, brochet 2-3-4) donnent
l'inverse. C'est un constat, pas une explication mécaniste.

Rapporté à l'anomalie lissée, un écart de coefficient de 0,11 sur une anomalie
de 3 °C déplace `Tmh_norm_fraie` de 0,33 °C.

---

## §6 — Questions ouvertes

**1. Lequel des deux jeux de valeurs `hors_eau` est le bon ?**
`config.py:81` documente 4 °C avec exclusion de saison ; `app.py:162-166`
applique 10 °C sans exclusion. Ce qui les départage : la valeur du dataclass
est celle qu'un lecteur du code croit appliquée et celle que `run_cli.py`
applique réellement ; la valeur de l'interface est celle qui a produit tous
les livrables existants. Aucune des deux n'est « la valeur par défaut » sans
ambiguïté. Je ne tranche pas — mais tant que l'écart subsiste, la
documentation et le comportement se contredisent, et un correctif du détecteur
devra dire lequel il remplace.

**2. Le contexte piscicole de `jeu_bienne` reste un défaut, non une trace.**
Il est sans effet sur `m`, `Tmh_norm` et `Tmax_norm`, donc sans effet sur le
périmètre. Il en a un sur `Tmh_norm_fraie` (fenêtre mars-avril-mai de l'ombre
commun) et sur les scores témoins. Ce qui les départage : soit on accepte que
la composante fraie de `jeu_bienne` soit une convention du harnais et on
l'étiquette comme telle, soit on récupère le contexte réel du bassin de la
Bienne auprès de qui l'a étudié.

**3. `CHAUX_DES_PRES.csv` manque toujours.** Rappel de l'étape 1 : la seule
décision du manifeste qui porte sur le périmètre — le choix de la station
d'air — se justifie par comparaison de deux stations, dont une seule est dans
`data/`.

**4. Un `m` négatif traverse toute la chaîne sans réserve bloquante.**
`BLE3-0` porte `m = −0,010` avec `R² = 0,002` sur 107 jours. La normalisation
*ajoute* alors l'anomalie au lieu de la retrancher. `redaction.py:145-150`
produit un verdict « modèle peu fiable » en texte, et rien n'arrête le calcul.
D16 met la règle de validité de `m_saisonnier` dans le périmètre ; la question
symétrique — une règle de validité pour `m_estival` — n'est pas ouverte par
les décisions actuelles. Ce qui les départage : la borne `[0 ; 1,2]` existe
déjà pour le saisonnier (`core.py:258`) et pas pour l'estival, sans que le
code dise pourquoi.

**5. La mesure du §4 ne dit rien du cas qu'elle devait éclairer.** Le corpus ne
contient aucun point dont la médiane propre atteigne la zone suspecte. Ce qui
les départage : soit le mécanisme d'aveuglement n'a pas d'objet sur ce type de
réseau, soit le corpus n'en porte pas d'exemple et la question reste entière.
Trancher demanderait un point dont on sait par le terrain qu'il est
chroniquement mal posé — le jeu de la Bienne en désigne un, `BIE40-3`, sous
« réserve d'implantation » dans `MANIFESTE.md`, mais sa médiane n'est que de
+2,00 °C et il n'est perdu à aucun quantile testé.
