# THERMIE_BIO V4.6 — Rapport d'étape 14

**Objet.** Poser le **correctif 4, voie B** : la famille *compensation*
disparaît. `docs/SPEC_convention_unique.md` fait foi ; cette étape l'exécute.

**La prédiction centrale tient.** 60 artefacts sur 66 figés au bit près,
`08_scores.csv` compris — c'est lui qui vérifie l'exhaustivité de l'inventaire.
`07_t_norm.csv` seul bouge, par **suppression de lignes uniquement**, toutes
`sortie_v45 = non`, donc hors verdict (D13). **Aucune valeur ne change nulle
part.**

**Deux motifs ont été contestés avant la pose**, l'un dans la commande, l'autre
dans mon propre code. Le premier a rendu `99_log.txt` figé au lieu de mobile ;
le second a évité de changer silencieusement le nombre de corrélations
publiées.

---

## Artefacts (D34, D54, D63) — motifs redéclarés, et contestés avant la pose

| Artefact | Type (D63) | Déclaré par la commande | Verdict du motif | Constaté |
|---|---|---|---|---|
| `07_t_norm.csv` | projection de `res.df` **+ recalcul du harnais** | doit bouger, **hors verdict seulement** | **juste** | **6/6, −201 162 lignes, 0 valeur changée** |
| `99_log.txt` | trace console | *peut* bouger, sur numéros de ligne (D80bis) | **CONTESTÉ AVANT LA POSE — figé** | **FIGÉ 6/6** |
| `08_scores.csv` | dépendance propre | **figé** — la famille est terminale | **juste** | **FIGÉ** |
| `02`, `03`, `04`, `05`, `06`, `00`, `01`, `10` | projections et métadonnées | **figés** — rien ne passe par `indicateurs.py` | **juste** | **FIGÉS** |

### `99_log.txt` : le cadre figé ne passe pas par `indicateurs.py`

D80bis demande de déclarer `99_log.txt` mobile quand un correctif insère ou
retire des lignes **en amont d'un point d'appel figé dans une trace**. La
commande demandait de vérifier si c'est le cas ici. **Ce ne l'est pas**, et
pour deux raisons cumulées.

La seule trace figée du corpus est celle de `BIE35-5__NA` (D7). Elle porte
trois cadres :

```
  File "<RACINE>\tests\reference\build_reference.py", line <ligne du harnais, masquee>
  File "<CODE>/thermie_debits\orchestrator.py", line 193, in run
  File "<CODE>/thermie_debits\core.py", line 522, in analyse_sensibilite
```

1. **Aucun cadre ne passe par `indicateurs.py`**, et le point échoue à
   l'« Étape 1 — Sensibilité », donc **avant** l'étape 6bis où
   `calcul_indicateurs` est appelé. Il n'atteint jamais ce module.
2. Le correctif ne retire aucune ligne **en amont** des deux cadres
   applicatifs : `core.py` n'est pas touché, et dans `orchestrator.py` seule
   une ligne de commentaire change, **en aval** de la ligne 193.

Le seul message que `calcul_indicateurs` imprime — « Indicateurs : N lignes, K
corrélations exploitables » — est **inchangé** : la voie B retire des colonnes,
pas des lignes, et ne touche à aucune corrélation (voir §2).

**Déclaré figé, constaté figé sur les six jeux.**

---

## §0 — Carnet de bord

### `has_delta` avait un second consommateur, et le retirer aurait changé les corrélations

`has_delta` semblait n'exister que pour la famille compensation :

```python
    has_delta = "Delta_TMm" in d.columns
    if has_delta:
        d["T_moy_comp"] = ...      # les trois séries
```

Il a un **second consommateur**, soixante-dix lignes plus bas :

```python
    if has_delta and has_air:
        d["ecart_eau_air"] = d["T_eau_moy"] - d["T_air"]
```

`ecart_eau_air` alimente **deux des quatre corrélations publiées**, et **ne lit
pas `Delta_TMm`** — mais sa condition de calcul, si. Supprimer `has_delta` avec
la famille aurait fait apparaître deux corrélations sur tout point ayant un
`T_air` sans `Delta_TMm`, **silencieusement**, dans un livrable.

C'est la famille de défaut retenue au registre à l'étape 13 — *la liste des
appelants ne suffit pas, il faut celle des observateurs* — mais d'une variante
qu'il faut nommer : ici l'observateur n'est pas une enveloppe, c'est **une
condition partagée**. Une variable booléenne dont le nom décrit une chose et
qui en garde une autre est un observateur invisible.

`has_delta` reste, la condition est conservée telle quelle, et deux
commentaires disent pourquoi — l'un à sa définition, l'autre à son second
usage.

### Un outil de contrôle a conclu sur rien, et il a fallu qu'il refuse

Mon premier essai de la pose a fait échouer le rejeu dès le premier jeu :
`set(getattr(table, "columns", []) or [])` force un test de vérité sur un
`Index` pandas, qui lève. Le dossier de sortie est resté quasi vide.

`comparer_rejeux.py` a alors répondu :

```
  artefacts compares : 0
  figes              : 0
  qui bougent        : 0
```

et **rendu 0**. C'est exactement le défaut corrigé à l'étape 10 **sur ce même
fichier** — « le zéro est un résultat, l'absence de résultat n'en est pas un » —
mais d'un cran au-dessus : la garde posée alors protégeait d'une **clé absente
dans un artefact**, pas d'un **corpus absent**. Un outil de contrôle qui répond
« rien n'a bougé » quand il n'a rien lu est pire qu'un outil qui échoue.

Il refuse désormais de conclure quand il n'a comparé aucun artefact — **retour
2**, vérifié sur le dossier vide qui l'avait pris en défaut.

*La leçon se généralise : **une garde protège au niveau où elle est posée**.
Corriger un silence dans une boucle ne protège pas de son homologue dans la
fonction qui l'appelle.*

### Deux assertions ont arrêté deux scripts avant qu'ils n'écrivent

Un accent manquant dans une ancre (`l'oppose` pour `l'opposé`), et le script de
pose s'est arrêté **avant** sa première écriture — alors que six fichiers
étaient déjà modifiés en mémoire. Rien n'a été laissé à moitié posé. C'est la
règle de l'étape 7, et c'est la troisième fois qu'elle sert.

### Une restructuration inutile, écartée avant d'être écrite

Ma première version du patch du harnais découpait `art_07` en trois fonctions
pour y placer une condition. C'était une réindentation de vingt lignes et deux
`return` insérés au milieu d'une fonction de cent — pour poser un `if`.

Remplacé par quatre lignes : la liste des séries itérées devient vide quand la
famille n'est plus publiée. **Le risque d'une modification n'est pas
proportionnel à ce qu'elle obtient, mais à ce qu'elle déplace.**

### D69, D71, D77 tenus

Quatre scripts, tous écrits comme fichiers, lisant et écrivant en octets, fins
de ligne relevées et restituées — LF pour `app/`, CRLF pour le harnais —, chaque
ancre assertée, rien d'écrit avant que toutes soient trouvées. Aucun CRLF
introduit ; D44 le vérifie. Aucun script sondé, `--sortie` toujours explicite.
Aucun import de `ref/` : le contrôle de clôture confirme **zéro bytecode**.

---

## §1 — D44 et D76

### D44

**Avant** : dix entrées, exactement les dix de l'étape 13, aucune en CRLF,
retour **0**.
**Après** : **onze** — `app/thermie_debits/indicateurs.py` rejoint la liste,
comme la commande l'annonçait. Retour **0**, aucun fichier de code en CRLF.

| Fichier | Rôle dans cette étape |
|---|---|
| `app/thermie_debits/indicateurs.py` | **nouveau dans la liste** — la famille retirée |
| `app/thermie_debits/figures.py` | les deux courbes retirées |
| `app/app.py` | l'onglet Indicateurs |
| `app/thermie_debits/orchestrator.py` | le commentaire d'étape 6bis |
| `app/thermie_debits/exports.py`, `livrables.py` | deux commentaires qui citaient la formule retirée |
| `app.py`, `config.py`, `core.py`, `io_data.py`, `qc.py`, `LISEZ-MOI.md` | inchangés ici, joints pour la complétude |

### D76

Les deux contrôles passent, avant et après : **66/66 sur les deux
références**, **zéro bytecode sous `ref/`**. Retour **0**.

---

## §2 — Le correctif, et l'exhaustivité

### Ce qui a été retiré

| | |
|---|---|
| séries journalières | `T_moy_comp`, `T_max_comp`, `T_min_comp` (`indicateurs.py:88-90`) |
| colonnes publiées | `Tmax comp (°C)`, `Tmin comp (°C)`, `Tmm30j comp (°C)` — positions 8, 9 et 11 |
| courbes | deux, en tirets, de `Fig_Indicateurs_Resume.png` |
| phrases | les deux abus « ramenée aux conditions normales » (D84), le sous-titre de l'onglet, trois docstrings et deux commentaires |

Le tableau mensuel passe de **onze à huit colonnes** : `Période`, `Tmax (°C)`,
`Tmax date`, `Tmin (°C)`, `Tmin date`, `Ampl. moy (°C)`, `Ampl. σ (°C)`,
`Tmm30j brut (°C)`.

### L'exhaustivité de l'inventaire du §1.3, vérifiée

Après suppression, recherche sur tout `app/` :

| Cherché | Occurrences restantes |
|---|---|
| `T_moy_comp`, `T_max_comp`, `T_min_comp` | **aucune** |
| `Tmax comp (°C)`, `Tmin comp (°C)`, `Tmm30j comp (°C)` | **aucune** |
| `has_comp` | **aucune** |

Aucune phrase orpheline ne subsiste. Les huit occurrences du mot
« compensation » qui restent sont soit **historiques et au passé** — elles
disent que la formule a existé et que le correctif 4 l'a retirée —, soit
étrangères au sujet : `core.py:682` emploie « compensation du harnais » au sens
de l'étape 7, un harnais qui compense un défaut de l'application.

**Le juge d'exhaustivité n'est pas cette recherche, c'est `08_scores.csv`.**
La spécification affirmait que la famille est *terminale* : aucun score, seuil,
débit ni composante du SGVT ne la lit. Si l'inventaire avait été incomplet,
cet artefact aurait bougé. **Il est figé sur les six jeux.**

### Ce que le rejeu constate

Rejeu de `app/` d'avant contre celui d'après, corpus et paramètres identiques :

```
  artefacts compares : 66
  figes              : 60
  qui bougent        : 6      (les six 07_t_norm.csv)
  nouveaux           : 0
```

| | avant | après |
|---|---|---|
| lignes de `07_t_norm.csv`, corpus entier | **352 474** | **151 312** |
| **lignes retirées** | | **201 162** |
| lignes ajoutées | | **0** |
| valeurs changées sur les lignes conservées | | **0** |

Les 201 162 lignes retirées se décomposent en **trois fois 67 054**, une par
série, et **toutes portaient `sortie_v45 = non`** : aucune ligne du verdict
n'a été touchée. Après la pose, `07_t_norm.csv` ne porte plus qu'une famille,
`normalisation (core.py)`, et **chaque ligne conservée est identique champ par
champ**.

*C'est la forme demandée : les lignes **disparaissent**, elles ne deviennent
pas vides.*

---

## §3 — Le côté `ref`

`ref/v4_5/` produit toujours la famille compensation. Le harnais doit continuer
de la figer pour lui : **la référence de V4.5 ne change pas parce que `app/` a
changé.**

### Comment le harnais décide, et ce qu'il ne fait pas

Il ne demande **ni la version, ni `THERMIE_CODE`**. Il demande au code exécuté
ce qu'il **publie** : les colonnes du tableau mensuel, seul endroit d'où cette
famille sorte de `calcul_indicateurs`. Un harnais qui devinerait la source de
code se tromperait le jour où l'on rejoue autre chose ; un harnais qui lit ce
que l'application déclare ne se trompe pas. C'est le principe des étapes 7
et 13.

### Vérifié deux fois, sur deux jeux

**(a) contre le rejeu `ref` d'avant la pose**, à schéma identique — c'est la
comparaison qui isole le changement de harnais :

```
  artefacts compares : 22
  figes              : 22
  qui bougent        : 0
```

**(b) contre `tests/reference`** (D83, branche A — `comparer_schemas.py` fait
foi) : **116 522 valeurs confrontées, 0 divergente**, 0 colonne disparue,
**2 `99_log.txt` sur 2 identiques au bit près**.

Et le contenu, pour que ce ne soit pas un simple « figé » :

| `jeu_02/07_t_norm.csv` | famille compensation | famille normalisation |
|---|---|---|
| côté **`ref`** | **3 645 lignes** | 2 963 |
| côté **`app`** | **0** | 2 931 |

*Le même harnais, sur le même corpus, fige deux familles pour `ref/v4_5` et une
seule pour `app/`. C'est exactement ce que la voie B demande.*

---

## §4 — Journal des verdicts

**Aucun verdict ne change**, et c'est le résultat attendu : la famille était
terminale. Aucun SGVT, aucun point de vulnérabilité, aucun pourcentage de
fraie, aucun seuil franchi, aucun débit de référence ne bouge — `08_scores.csv`
figé sur les six jeux le certifie.

**Mais trois livrables changent de forme**, et c'est cela que le commanditaire
devra pouvoir dire à un maître d'ouvrage :

| Livrable | Ce qui change |
|---|---|
| **Classeur**, feuille `05_Indicateurs` | passe de **11 à 8 colonnes** |
| **Word**, §2.2 — la **figure** `Fig_Indicateurs_Resume` | perd **deux courbes** en tirets et deux entrées de légende |
| **Word**, §2.2 — le **tableau** | **inchangé** : il ne prenait que les six premières colonnes |
| **Écran**, onglet Indicateurs, et son **export CSV** | perdent **trois colonnes** |

**777 valeurs publiées supprimées, zéro verdict déplacé.**

**Ce qui disparaît et n'a d'équivalent nulle part**, nommément :

1. **La couverture de janvier à décembre.** La famille normalisation n'agrège
   rien hors de ses fenêtres — juin-septembre pour la vulnérabilité, les mois
   de phase de l'espèce pour la reproduction. Le tableau mensuel était **le
   seul endroit de l'outil où une température corrigée était publiée pour
   janvier ou novembre**.
2. **Le minimum corrigé.** `T_min_comp` était la seule série corrigée bâtie sur
   `T_eau_min` ; la famille normalisation ne produit **aucun** minimum.
3. **La moyenne mobile de trente jours corrigée.** `Tmm30j comp` n'avait
   d'équivalent nulle part. Son pendant brut, `Tmm30j brut`, subsiste.

*Et ce qui ne disparaît pas, quoique l'on puisse le croire : l'**information**
que ces colonnes portaient n'était pas une correction climatique estimée. Elles
retranchaient l'anomalie d'air **brute, sans coefficient**, c'est-à-dire ce
qu'on obtiendrait si l'eau suivait l'air un pour un. Le `m` médian du corpus
vaut **0,432** : elles corrigeaient plus du double de ce que la réponse mesurée
du cours d'eau justifie, et deux textes de l'outil les présentaient comme une
« ramenée aux conditions normales ». Ces deux textes disparaissent avec elles
(D84).*

Le détail est consigné dans `docs/VERDICTS_MODIFIES.md`.

---

## §5 — État des lieux avant clôture

Votre liste est exacte : **D48** (affichage de la dégradation déclarée),
**D68** (statut de validité dans les livrables), **D83** (rebasage de clôture),
et les cinq comportements que le corpus n'exerce pas.

**Je vois quatre choses de plus dans le périmètre `lecture → T_norm`**, toutes
relevées et vérifiées sur l'état actuel du code. Trois sont au registre depuis
l'étape 1 et n'ont jamais été traitées ; la quatrième change de statut à cause
de cette étape.

### 1. `n_mesures` est calculé puis jamais relu — aucun critère de complétude de journée

`io_data.py:153` produit `n_mesures=("T_eau", "size")` par journée. **La
recherche sur tout `app/` ne trouve aucune autre occurrence.** Une journée
d'une seule mesure pèse donc autant qu'une journée de vingt-quatre dans
`T_eau_moy`, donc dans `Tmh`, donc dans `m`, donc dans `T_norm`.

**C'est le plus amont des quatre**, et le seul directement dans le périmètre du
mandat. Au registre depuis l'étape 1 (I11).

*Une asymétrie le rend plus visible : l'amplitude nycthémérale, elle, **a** un
critère — `out.loc[out["n"] < 3, "ampl"] = np.nan` (`indicateurs.py`). Le même
module exige trois mesures pour publier une amplitude et n'en exige aucune pour
publier une moyenne.*

### 2. La normale agrégée par `dayofyear`, relue par (jour, mois) via une année bissextile

`io_data.py:609` agrège par `doy` ; `io_data.py:642` reconstruit la table de
correspondance sur `date_range("2000-01-01", "2000-12-31")` — **2000 est
bissextile**. À partir du 1ᵉʳ mars, le `doy` d'une année commune et celui de
l'an 2000 diffèrent d'un jour.

C'est **directement dans `Delta_TMm`, donc dans `T_norm`**. Au registre depuis
l'étape 1 (B1 / I3), jamais chiffré. Il serait raisonnable de le mesurer avant
de clore : l'ordre de grandeur est celui d'un décalage d'un jour sur une
normale lissée à ±10 jours, donc probablement faible — **mais « probablement
faible » n'est pas une mesure**, et c'est la règle du chantier.

### 3. La colonne d'heure reconnue par `startswith` — et sa portée vient de changer

`chmes_heure` de `BLE3-0` n'est pas reconnue : ses 2 952 mesures sont toutes
datées à minuit, d'où 2 828 horodatages en double. Les agrégats **journaliers**
restent justes ; ce qui disparaît est la structure infra-journalière, donc
l'amplitude nycthémérale et les extrêmes horodatés.

**Ce défaut change d'importance à cause de cette étape.** Avant, le tableau
mensuel portait onze colonnes dont trois compensées ; après, il en porte huit,
et **la totalité de ce que publie `indicateurs.py` repose désormais sur les
extrêmes horodatés et l'amplitude** — exactement ce que ce défaut corrompt.
Retirer une famille de colonnes a augmenté le poids relatif de celles qui
restent. Au registre depuis l'étape 1 (C2 / I13).

### 4. `_tmm30j` lisse sur un index **positionnel** — le défaut du correctif 2, survivant

```python
    return float(s.rolling(30, min_periods=25).mean().max())
```

`s` est la série journalière **après `dropna`**. Une fenêtre de trente
**lignes** n'est une fenêtre de trente **jours** que si la série est continue —
c'est mot pour mot le défaut que le correctif 2 a corrigé dans
`core.fusionner`, et il subsit ici. Sur le corpus, l'étape 6 a mesuré 1 131
journées voisines d'une lacune sur 26 points.

`Tmm30j brut (°C)` **est publié** — dans le classeur, et en repère horizontal
sur la figure du Word. Signalé hors chaîne à l'étape 10 (D53) ; il reste hors
chaîne, mais il n'est pas hors livrable.

### Ce que je ne vois pas

Rien de nouveau n'est apparu dans le périmètre `lecture → T_norm` à cette
étape : le correctif 4 n'a touché qu'un module terminal. Les quatre points
ci-dessus étaient tous connus ; ce qui est neuf est le changement de portée
du n° 3.

---

## §6 — Alternatives fermées

### Alternative 1 — Les quatre points du §5, avant ou après la clôture ?

| Branche | **A — clore, puis reprendre** | **B — traiter les n° 1 et 2 avant de clore** |
|---|---|---|
| ce qu'on clôt | un outil dont quatre défauts connus sont **documentés et non corrigés** | un outil dont le périmètre `lecture → T_norm` est traité |
| coût | nul maintenant | deux étapes, dont une mesure sur les normales |
| risque | D83 rebase la référence **sur un état porteur de ces défauts** : le point de comparaison de la V4.7 les figera | le rebasage de clôture fige un état plus propre |
| argument contraire | les n° 1 et 2 sont au registre depuis l'étape 1 et n'ont jamais bloqué personne | on ne mesure pas ce qu'on n'a pas décidé de corriger |

**Ce qui les départage.** Le rebasage de clôture (D83) n'est pas un geste
neutre : il fait de l'état d'aujourd'hui **la référence contre laquelle la
suite sera mesurée**. Un défaut non corrigé avant lui devient un comportement
attendu. Les n° 1 et 2 sont les seuls des quatre à être **directement dans le
périmètre du mandat** — les n° 3 et 4 sont en aval de `T_norm`.

*Je penche pour B restreinte aux n° 1 et 2, et je ne tranche pas : c'est une
décision de portée du mandat.*

### Alternative 2 — `Tmm30j brut` : le corriger, ou le déclarer hors chaîne dans le livrable ?

| Branche | **A — corriger l'index** | **B — le déclarer dans le livrable** |
|---|---|---|
| ce qu'on fait | `_tmm30j` passe à `moyenne_mobile_calendaire`, comme `core.fusionner` | une note dit que cet indicateur lisse sur les lignes, pas sur les jours |
| effet sur les valeurs | à mesurer — non nul sur les chroniques lacunaires | **aucun** |
| cohérence | la même grandeur ne se calcule plus de deux façons dans le même outil | deux conventions coexistent, l'une déclarée |
| coût | un correctif de plus, avec sa mesure | une phrase |

**Ce qui les départage.** Si `Tmm30j brut` est un indicateur publié, il doit
obéir à la même convention de fenêtre que le reste de la chaîne, et c'est A.
S'il est un repère descriptif d'appoint, B suffit — **à condition que la note
soit écrite**, faute de quoi le lecteur croira lire trente jours.

*Je n'ai rien posé : la correction sort du mandat de l'étape.*

---

## §7 — Ce qui reste

**D48** — l'affichage de toute la dégradation déclarée, dont les textes
s'accumulent dans les deux spécifications depuis l'étape 7. **D68** — l'entrée
du statut de validité dans les livrables. **D83** — le rebasage de clôture, sur
décision explicite. **Les cinq comportements que le corpus n'exerce pas** —
débit désinfluencé, normales pré-calculées, export d'air multi-stations,
garde-fou du MAD nul, branche `EcartNormales` — à nommer dans les limites du
livrable. Et **les quatre points du §5**, dont deux sont dans le périmètre du
mandat.

**Le correctif 4 était le dernier des dix correctifs du registre.** Tous sont
posés.
