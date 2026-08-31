# THERMIE_BIO V4.6 — Rapport d'étape 16

**Objet.** Poser le **correctif 12, branche A** (D86, D89) — le critère de
complétude de journée, qui marque sans exclure. Départager le facteur **sur
pièces** (D91). Chiffrer ce que la branche B aurait coûté (D90). Déclarer
l'inapplicabilité du critère là où les horodatages sont détruits (D92).

**La prédiction centrale tient** : `04`, `05`, `06`, `07`, `08`, `00` et `01`
**figés** — aucune valeur publiée ne bouge. `02`, `03`, `10` et `99` bougent, et
c'était déclaré.

**Un motif de commande a été contesté avant la pose**, et il évitait un
mouvement de `01_colonnes_retenues.json` sans rapport avec le correctif.

---

## Artefacts (D34, D54, D63) — motifs contestés avant la pose

| Artefact | Type (D63) | Déclaré | Verdict du motif | Constaté |
|---|---|---|---|---|
| `03_journees_ecartees.csv` | projection | doit bouger — statut et motif nouveaux, aucune journée écartée | **juste** | **6/6, +138 lignes, 0 valeur changée** |
| `02_effectifs.csv` | **compte** | peut bouger — un compte s'ajoute | **juste** | **6/6, 0 valeur changée** |
| `10_parametres.json` | métadonnée | peut bouger — le facteur devient-il exposé ? | **juste, et la réponse est oui** (§4.3) | **6/6** |
| `04`, `05`, `06`, `07`, `08` | valeurs | **FIGÉS — prédiction centrale** | **juste** | **FIGÉS** |
| `00`, `01` | métadonnées de lecture | figés — la lecture ne change pas | **juste, mais SEULEMENT parce que le marquage a été sorti de `res.df`** (§0) | **FIGÉS** |
| `99_log.txt` | trace console | D80bis à appliquer | **mobile — deux causes, §4.4** | **6/6** |

### `03` porte-t-il des journées qui ne sont pas écartées ?

La commande disait « `03_journees_ecartees.csv`, **ou l'artefact qui porte le
marquage** ». Le nom de l'artefact pouvait faire hésiter : y inscrire une
journée **retenue** serait un contresens du genre de celui que l'étape 7
interdisait — *« il ne dit jamais “écartées par le contrôle qualité” : le
contrôle qualité les a retenues »*.

**Le précédent existe et il est dans le même fichier** : depuis le correctif 2,
`03` porte l'étape `densite_calendaire`, dont la docstring dit *« Elles restent
dans `res.df` : elles ne sont pas supprimées, elles sont nommées »*. Les
journées de complétude s'y rangent avec le même statut, et leur motif commence
par **`RETENUE —`** pour qu'aucun lecteur ne s'y trompe.

---

## §0 — Carnet de bord

### Un motif juste qui serait devenu faux si le marquage avait suivi le chemin évident

Le chemin évident était d'ajouter le trou maximal comme **colonne de `daily`**.
Il aurait remonté jusqu'à `res.df` par la fusion — et
`build_reference.art_03` publie :

```python
    colonnes_finales_df=[str(c) for c in res.df.columns]
```

`01_colonnes_retenues.json`, déclaré **figé**, aurait bougé pour une raison
sans aucun rapport avec le correctif. Vérifié **avant** la pose, et la
conclusion a changé la conception : le marquage vit dans une **table séparée**,
`res.marques_completude`, comme `marques_fusion` (correctif 5) et
`marques_lecture` (correctif 10).

*La forme retenue par les correctifs précédents n'était pas une habitude : elle
protège les artefacts de métadonnées. Je ne l'avais pas comprise ainsi avant de
buter dessus.*

### Le compte des journées désignées ne tombait pas, et il fallait le fermer

La mesure annonçait **145** journées désignées ; les artefacts en portent
**141**. Quatre manquaient.

L'explication plausible — un effet de bord du critère — aurait été fausse. Le
compte se ferme exactement : **`BIE35-5__NA` porte 4 journées désignées**, et sa
chaîne échoue (D7), si bien qu'aucun artefact n'est produit pour lui.
**145 (mesure, 32 points) − 4 = 141 (artefacts, 31 points).**

C'est la troisième occurrence de la même leçon — *un artefact n'est pas le
périmètre d'une mesure* (étapes 8, 9) — et la règle qui l'accompagne a servi :
**fermer le compte plutôt que se contenter d'une explication plausible.**

### Mon propre relevé annonçait deux verdicts modifiés là où il n'y en avait aucun

Le récapitulatif de la tâche B imprimait :

```
     n_jours_aigus modifie : 2 point(s)
        BIE46-5    nan -> nan
        BLE3-0     nan -> nan
```

Ces deux points n'ont **aucune** journée désignée : leurs colonnes sont vides,
donc `NaN`, et `NaN != NaN`. Le comparateur comptait une différence là où il
n'y avait pas de valeur. **Zéro point voit son `n_jours_aigus` changer.**

C'est la famille de défaut relevée trois fois déjà — *le zéro est un résultat,
l'absence de résultat n'en est pas un* —, cette fois dans un récapitulatif que
je venais d'écrire. Un outil de contrôle se contrôle aussi, y compris quand il
a dix minutes d'existence.

### D69, D71, D77 tenus

Cinq scripts, tous écrits comme fichiers, lisant et écrivant en octets, fins de
ligne relevées et restituées, chaque ancre assertée, rien d'écrit avant qu'elles
soient toutes trouvées. Aucun CRLF introduit. Aucun script sondé, `--sortie`
toujours explicite. Aucun import de `ref/` hors du harnais ; le contrôle de
clôture confirme **zéro bytecode**.

---

## §1 — D44 et D76

**D44** — onze entrées avant, **onze après**, exactement les onze déclarées,
aucun fichier de code en CRLF, retour **0**. Trois fichiers de `app/` ont bougé :
`config.py`, `io_data.py`, `orchestrator.py`.

**D76** — les deux contrôles passent aux deux bouts : 66/66 sur les deux
références, zéro bytecode sous `ref/`. Retour **0**.

---

## §2 — D91 : le facteur, départagé sur pièces

`tests/reference/mesure_facteur_completude.py`. La règle de décision est écrite
**en tête du fichier**, avant les chiffres : un facteur plus permissif est
retenu si la séparation du témoin indépendant reste **≥ 2,0** et la part
désignée **≤ 1 %** ; entre deux facteurs qui passent, on retient **le plus
permissif**.

| Facteur | Journées | Part | Points | Témoin — désignées | Témoin — autres | **Séparation** | Règle |
|---|---|---|---|---|---|---|---|
| **2×** | **145** | 0,213 % | **30** | 0,5659 °C | 0,2183 °C | **× 2,59** | passe |
| 3× | 143 | 0,210 % | 30 | 0,5659 | 0,2183 | × 2,59 | passe |
| 4× | 142 | 0,208 % | 29 | 0,5715 | 0,2183 | × 2,62 | passe |

**Les trois passent. Le facteur retenu est donc 2×**, par la règle écrite
d'avance.

### Pourquoi ils se ressemblent autant, et ce que cela révèle

La distribution du trou maximal sur le corpus est **quantifiée** :

| Trou maximal | Journées | Part |
|---|---|---|
| 0,2 h | 143 | 0,210 % |
| 0,5 h | 1 997 | 2,931 % |
| **1,0 h** | **65 506** | **96,143 %** |
| 2,0 h | 14 | 0,021 % |
| **6,0 h** | **200** | 0,294 % |
| 7,0 h et au-delà | ~150 | |

**Aucune journée du corpus n'a un trou strictement compris entre 2 h et 4 h.**
Sur les 31 points horaires, les trois facteurs désignent donc **exactement le
même ensemble**. La différence entre 145, 143 et 142 vient d'un seul point.

### Le point qui départage, et l'argument décisif

`La Moselle à Hielle` a un trou médian de **6,00 h** — sa sonde a mesuré toutes
les six heures pendant deux tiers de sa chronique.

| Facteur | Seuil pour ce point | Journées désignées |
|---|---|---|
| 2× | 12,0 h | **3** |
| 3× | 18,0 h | 1 |
| **4×** | **24,0 h** | **0** |

**À 4×, le seuil vaut la journée entière — que rien ne peut dépasser.** Le
critère y devient aveugle **par construction**, reproduisant sur un point
parfaitement légitime la cécité que `BLE3-0` subit d'un vrai défaut
d'horodatage.

**2× n'est donc pas retenu parce qu'il désigne trois journées de plus, mais
parce qu'un facteur plus large rend le critère inapplicable aux sondes de
cadence large.** La spécification retenait 4× par argument plausible ; elle est
amendée à l'endroit même où sa conclusion changeait.

---

## §3 — D90 : ce que la branche B aurait coûté

`tests/reference/mesure_branche_b.py`. Les journées désignées sont retirées de
`propre` **avant** la fusion — exactement ce que la branche B ferait — et la
chaîne est rejouée avec les fonctions de l'application.

**Contrôle de réplication : identique sur les 31 points** qui aboutissent.

| | |
|---|---|
| points portant des journées désignées | **29 / 31** |
| \|Δ`m`\|, retrait de toutes | médiane **0,000158**, p95 0,001174, **max 0,001436** (`GRO9-1`) |
| \|Δ`m`\|, retrait de l'été seul | médiane 0,000188, **max 0,001436** |
| Δ`Tmh_norm`, médiane par point | médiane **0,0003 °C**, max 0,0034 |
| Δ`Tmh_norm`, maximum par point | médiane 0,2783 °C, **max 0,7303 °C** |
| **catégories de stress chronique qui basculent** | **0** |
| **catégories de vulnérabilité aiguë qui basculent** | **0** |
| **`n_jours_aigus` modifiés** | **0** |

**L'effet est négligeable, et la branche A est justifiée sur pièces.** Pour
comparaison, le correctif 1 avait déplacé `m` jusqu'à **0,042** — trente fois
davantage.

**Un chiffre se lit à l'envers, et il est le plus instructif.** Le maximum de
**0,7303 °C** sur `Tmh_norm` ne tombe pas sur une journée désignée — celles-là
sortent de la comparaison — mais sur ses **voisines**, dont la moyenne mobile
calendaire de sept jours a perdu une valeur.

> **La branche B ne se contente pas de retirer des journées suspectes : elle
> perturbe celles qui les entourent.** La branche A n'en perturbe aucune.

C'est un argument que la spécification n'avait pas, et que seule la mesure
pouvait produire.

---

## §4 — Le correctif et ses artefacts

### 4.1 Ce qui a été posé

| Fichier | Ce qui change |
|---|---|
| `config.py` | `completude_facteur: float = 2.0` dans `QCConfig` |
| `io_data.py` | `trou_maximal_par_journee` et `marquer_completude` ; trois statuts et leur motif |
| `orchestrator.py` | `res.marques_completude`, et l'appel |
| `parametres.py` (harnais) | le facteur déclaré dans les deux tables `app` |
| `build_reference.py` (harnais) | `art_02` gagne un compte, `art_03` lit la table |

### 4.2 Le seuil se dérive, et il survit à un changement de cadence

Une journée est signalée si son trou maximal dépasse **`completude_facteur`
fois le trou médian du point traité**. Le repère est la sonde elle-même : le
critère fonctionne à l'heure comme aux six heures, et **survit à un changement
de cadence en cours de chronique** — ce qui était précisément l'écueil du
premier critère. Aucune valeur importée (D15, D41).

### 4.3 Le facteur est un paramètre déclaré, non un widget

**Oui, il devient un paramètre**, et `10_parametres.json` le porte sur les six
jeux. **Non, il n'est pas exposé par un widget** — comme `m_domaine` et
`m_niveau_ic` du correctif 6.

**Le motif est de méthode** : le seuil se dérive du point traité, et seul le
multiplicateur est fixe. L'exposer inviterait à régler station par station un
critère que D41 veut uniforme. Il est dans le dataclass, donc documenté et
déclaré ; il n'est pas dans l'interface, donc non réglable au coup par coup.

### 4.4 `99_log.txt` — D80bis, et deux causes

**Le cadre figé de `BIE35-5__NA` passe par le fichier modifié : oui.** Il porte
`orchestrator.py`, et l'appel à `marquer_completude` est inséré **en amont** du
point d'appel figé.

```
- File "<CODE>/thermie_debits\orchestrator.py", line 193, in run
+ File "<CODE>/thermie_debits\orchestrator.py", line 203, in run
```

**D80bis appliquée : `99_log.txt` est déclaré mobile sur numéros de ligne**, et
il l'est. Une seconde cause s'y ajoute, prévue elle aussi : le message de
complétude, dont celui de `BLE3-0` —
*« structure infra-journalière illisible (124 journée(s)) — critère non
applicable »*.

### 4.5 Ce que le rejeu constate

```
  artefacts compares : 66
  figes              : 42        (dont 04, 05, 06, 07, 08, 00, 01)
  qui bougent        : 24        (02, 03, 10, 99 — six jeux chacun)
```

| Artefact | Lignes retirées | Lignes ajoutées | **Valeurs changées** |
|---|---|---|---|
| `02_effectifs.csv` | 0 | 0 | **0** — une colonne s'ajoute |
| `03_journees_ecartees.csv` | 0 | +138 | **0** |
| `10_parametres.json` | 0 | +5 | le champ nouveau |
| `04`, `05`, `06`, `07`, `08` | — | — | **FIGÉS** |

**Aucune valeur publiée ne bouge**, et aucune ligne n'est retirée nulle part.
C'est la signature de la branche A.

**Les deux artefacts se recoupent** — ce qui n'allait pas de soi :

| Jeu | `03` : signalées | `03` : inapplicable | `02` : colonne |
|---|---|---|---|
| `jeu_02` | 4 | 0 | **4** |
| `jeu_03` | 2 | 0 | **2** |
| `jeu_04` | 2 | 0 | **2** |
| `jeu_05` | 2 | 0 | **2** |
| `jeu_bienne` | 128 | **1** (`BLE3-0`) | **128**, et `n/a` pour `BLE3-0` |
| `jeu_exemples_v45` | 3 | 0 | **3** |
| **total** | **141** | 1 | **141** |

*Les +138 lignes du diff contre 141 rangées ne se contredisent pas : le
comparateur apparie sur `(point, date)`, et trois dates désignées portaient déjà
une ligne d'une autre étape.*

### 4.6 D92 — l'inapplicabilité est écrite, pas déduite

`BLE3-0` a un trou médian de **24,00 h** : toutes ses mesures portent le même
horodatage, et l'outil ne sait rien de leur répartition. Le critère **ne peut
pas le juger**, et il l'écrit :

- statut `indeterminable` sur ses 124 journées, avec son motif ;
- une ligne dédiée dans `03` : *« CRITERE INAPPLICABLE — structure
  infra-journalière illisible… »* ;
- **`n/a`** dans la colonne de `02`, distinct de `0` et distinct du vide.

**Trois valeurs qui ne se confondent pas** : un entier (le critère s'est
prononcé), `n/a` (il s'est déclaré inapplicable), et vide (l'application ne
produit pas la table — on rejoue `ref/v4_5`). Écrire zéro dans les deux
derniers cas serait le mensonge que ce correctif retire.

### 4.7 Le côté `ref` survit

`comparer_schemas.py`, `tests/reference` contre un rejeu `ref` sur deux jeux :
**116 522 valeurs confrontées, 0 divergente**, 0 colonne disparue, **2
`99_log.txt` sur 2 identiques au bit près**.

Et le contenu le confirme : côté `ref`, la colonne de complétude est **vide** et
`03` porte **0 ligne** de complétude — `ref/v4_5` ne produit pas la table, et le
harnais ne l'invente pas.

---

## §5 — L'asymétrie avec l'amplitude (C.4)

`indicateurs._amplitude_journaliere` masque l'amplitude d'une journée portant
moins de trois mesures. Le critère de complétude ne regarde pas l'effectif.
**Faut-il les unifier ?**

**Non — ils répondent à deux questions distinctes, et le code le dit :**

- `n < 3` protège une **étendue** (`max − min`). Avec deux points on obtient une
  corde, pas une amplitude : c'est une condition d'**existence** de la
  statistique.
- Le trou maximal protège une **localisation** (la moyenne journalière). Il
  demande si la journée **couvre le cycle**, ce qui ne dépend pas du nombre de
  points.

**Mais la mesure ajoute un fait que cette distinction ne donne pas :**

| | |
|---|---|
| journées désignées par le critère de trou | **145** |
| dont `n_mesures ≥ 3` — **l'amplitude est publiée** | **141** |
| dont `n_mesures < 3` — l'amplitude est déjà masquée | **4** |

**141 journées publient aujourd'hui une amplitude nycthémérale calculée sur des
mesures groupées sur une partie de la journée.** Une amplitude jour-nuit qui
ignore la nuit n'est pas une amplitude nycthémérale : **`n < 3` est le plus
faible des deux critères pour son propre objet.**

**Conclusion.** Les deux ne s'unifient pas — l'un conditionne l'existence,
l'autre la représentativité —, mais le critère de trou **améliorerait**
`indicateurs.py` s'il y était appliqué **en plus** de `n < 3`.

**Rien n'a été posé sur `indicateurs.py`.** Ce module est en aval de `T_norm`,
donc hors du périmètre du mandat. C'est une entrée pour le chantier aval, à
ranger avec D87 et D88.

---

## §6 — Journal des verdicts

**Aucun verdict ne change, et aucune valeur publiée non plus.** C'est la
définition de la branche A, et elle est vérifiée : `04`, `05`, `06`, `07` et
`08` figés sur les six jeux.

Ce qui entre au journal est donc d'une autre nature : **141 journées de la
chronique portent désormais un signalement**, et un point entier — `BLE3-0` —
porte une déclaration d'inapplicabilité. Le détail est dans
`docs/VERDICTS_MODIFIES.md`.

---

## §7 — État des lieux

**Il reste D48, D68 et D83 — et une chose de plus, dans le périmètre.**

### Ce qui reste dans le périmètre `lecture → T_norm`

**`n_mesures` est produit et n'est toujours relu nulle part.**
`io_data.py:153` — recherche exhaustive sur tout `app/`, **une seule
occurrence**, celle qui le produit.

Le **défaut que j'avais nommé** à l'étape 14 — « aucun critère de complétude de
journée » — est corrigé : le critère existe, et il est meilleur que celui que
`n_mesures` aurait permis (§2 de la spécification). Mais la **valeur morte**
subsiste : une colonne calculée à chaque lecture, transportée dans `daily`, et
lue par personne.

Ce n'est plus un défaut de méthode, c'est un reste. Il se traite en deux lignes
et je ne l'ai pas fait, parce que le supprimer changerait les colonnes de
`daily`, donc de `res.df`, donc `01_colonnes_retenues.json` — le piège du §0,
dans l'autre sens. **Cela mérite une pose déclarée, pas un nettoyage en
passant.**

### Ce qui reste hors périmètre, déjà placé

- **D87** — `_tmm30j` lisse sur un index positionnel ; la note entre au bloc
  D48 à l'étape 17.
- **D88** — la colonne d'heure non reconnue. **Le correctif 12 lui ajoute une
  raison** : le critère de complétude est structurellement inapplicable à
  `BLE3-0` tant que ses horodatages ne sont pas réparés, et cela se lit
  désormais dans deux artefacts.
- **141 journées publient une amplitude sur des mesures groupées** (§5).
- **Les cinq comportements que le corpus n'exerce pas** — débit désinfluencé,
  normales pré-calculées, export d'air multi-stations, garde-fou du MAD nul,
  branche `EcartNormales`.

### Ce qui reste au mandat

**D48** (l'affichage de toute la dégradation déclarée — trois textes
l'attendent désormais), **D68** (le statut de validité dans les livrables),
**D83** (le rebasage de clôture).

---

## §8 — Alternatives fermées

### Alternative — `n_mesures`, valeur morte : la retirer ou la relier ?

| Branche | **A — la retirer** | **B — la publier dans la table de complétude** | **C — ne rien faire** |
|---|---|---|---|
| ce qu'on écrit | deux lignes de moins dans `io_data` | une colonne de plus dans `marques_completude` | rien |
| effet sur `res.df` | **les colonnes changent** → `01` bouge | aucun | aucun |
| ce que le lecteur y gagne | rien | l'effectif à côté du trou : deux journées de même trou et d'effectifs très différents cessent d'être indiscernables | rien |
| coût | une pose déclarée pour une valeur morte | une pose déclarée pour une information | nul |

**Ce qui les départage.** La spécification a montré que l'effectif et le trou
mesurent des choses différentes, et que le trou est le bon critère. Mais elle a
aussi montré que la médiane de `n_mesures` des journées désignées vaut **12 sur
24** — un fait qu'on ne peut énoncer que si l'effectif est **à côté** du trou.

*Je penche pour **B** : `n_mesures` cesse d'être une valeur morte sans que
`res.df` change, et le signalement gagne la seule information qui manque pour
le lire. Je ne tranche pas — c'est une pose, et elle se déclare.*

### Alternative — Le critère de trou doit-il s'appliquer à l'amplitude ?

| Branche | **A — non, `n < 3` suffit** | **B — oui, en plus de `n < 3`** |
|---|---|---|
| journées dont l'amplitude serait masquée | 4 aujourd'hui | **145** |
| ce que ça suppose | une amplitude sur mesures groupées reste une amplitude | une amplitude jour-nuit doit couvrir le jour et la nuit |
| périmètre | — | **`indicateurs.py`, en aval de `T_norm`** |
| effet sur les verdicts | — | **aucun** — l'amplitude n'entre dans aucun score |

**Ce qui les départage** : B est plus juste sur le fond, et ne coûte aucun
verdict — l'amplitude est publiée, jamais calculée. Mais elle sort du périmètre
du mandat, et l'étape 14 a montré ce que retirer des colonnes fait au poids des
autres.

*Signalé, non posé, conformément à C.4.*
