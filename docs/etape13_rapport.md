# THERMIE_BIO V4.6 — Rapport d'étape 13

**Objet.** Cinq poses séparées : **D73** (une table de paramètres par source de
code), **D75** (le manifeste sur déclaration), **D74** (le vocabulaire),
**correctif 10** (D60, `io_data.py:98`), **correctif 7** (D22 et D78, les
défauts littéraux).

**Une prédiction a échoué**, celle de la pose 1. Elle a échoué pour une raison
qui n'est pas celle que la commande redoutait, et §2 l'établit avant de
continuer. Les quatre autres prédictions tiennent ; l'une de mes déclarations
d'artefacts était fausse sur une ligne, et §5 le dit.

**D72 tenu** : le correctif 4 n'est pas posé.

---

## Artefacts déclarés (D34, D54, D63), pose par pose

| Pose | Artefact | Type (D63) | Déclaré | Verdict du motif | Constaté |
|---|---|---|---|---|---|
| **1 — D73** | tous | — | **66 figés** côté `app` — `parametres.py` appartient au harnais | **juste** | **66/66 figés** |
| **2 — D75** | tous | — | **aucun** — `MANIFEST.sha256` et `SOURCE_CODE.txt` sont hors de l'ensemble haché | **juste** | **132 artefacts intacts** |
| **3 — D74** | tous | — | **66 figés** — aucune étiquette n'entre dans un artefact | **juste** | **66/66 figés** |
| **4 — corr. 10** | `02_effectifs.csv` | **compte** | doit bouger — une colonne s'ajoute | **juste** | **6/6, 0 valeur changée** |
| | `03_journees_ecartees.csv` | projection | **figé** — zéro mesure écartée sur le corpus | **juste** | **FIGÉ** |
| | `04`, `05`, `06`, `07`, `08` | **valeurs** | **figés** | **juste** | **FIGÉS** |
| | `00`, `01`, `10` | métadonnées | **figés** | **juste** | **FIGÉS** |
| | `99_log.txt` | trace console | **figé** | **FAUX sur 1 ligne** — voir §5 | **1/6 bouge** |
| **5 — corr. 7** | tous | — | **66 figés** — 17 littéraux, 0 divergent, vérifié avant la pose | **juste** | **66/66 figés** |

**Un seul motif était faux, et il l'était de la troisième manière connue :
juste sur ce que le correctif AJOUTE au journal, incomplet sur ce qu'il y
DÉPLACE.** §5.

---

## §0 — Carnet de bord

### La prédiction 1.2 a échoué, et j'aurais dû la contester avant de poser

La commande annonçait : `THERMIE_CODE=ref` contre `tests/reference/` **rend
DIFF VIDE sur les 66 artefacts**, et « si le diff n'est pas vide, ARRÊTE-TOI ».
Il n'est pas vide : **18 artefacts divergent**.

Cette prédiction ne pouvait pas être vraie, et c'est **mon rapport d'étape 12
qui l'établissait déjà** — il notait que la référence figée ne porte pas les
colonnes de validité du correctif 6. La référence date de l'étape 6 ; le
schéma du harnais a grossi aux étapes 7, 10, 11 et 12. Un diff de fichiers ne
peut pas être vide entre deux schémas différents.

La règle du chantier est de **contester une déclaration de commande AVANT la
pose** — elle a servi trois fois (étapes 6, 8 et 10). Je ne l'ai pas appliquée
ici : j'ai posé, puis constaté. Le résultat est le même, le procédé non.

*Ce que cela coûte : rien cette fois, parce que la pose était juste. Ce que
cela aurait coûté si elle ne l'était pas : on ne saurait pas distinguer « la
prédiction était impossible » de « la pose est fausse ».*

### Ce que la commande redoutait n'a pas eu lieu, et il fallait le prouver

La commande donnait la raison de son arrêt : « ce serait la première indication
réelle que quelque chose a bougé dans `ref/v4_5/` ou dans le corpus ». J'ai
donc établi le contraire, par la méthode de la tâche B4 de l'étape 6 —
comparer **colonne par colonne, sur les seules colonnes communes aux deux
schémas** :

| | |
|---|---|
| artefacts comparés | **60 sur 60 identiques** |
| **valeurs confrontées** | **5 113 270** |
| **valeurs divergentes** | **0** |
| colonnes disparues | **0** |
| colonnes ajoutées | 14, toutes attribuables aux correctifs 5, 1 et 6 |
| **`99_log.txt`** | **6 sur 6 identiques au bit près** |

Les six journaux identiques au bit près sont le témoin décisif : le journal
console est intégral, il porte tout ce que la chaîne imprime, et il n'a pas de
schéma de harnais. **Rien n'a bougé dans `ref/v4_5/` ni dans le corpus.** Le
contrôle que D73 devait rétablir l'est ; c'est sa forme littérale, le diff de
fichiers, qui est inatteignable sans rebaser la référence — ce que B4 et D72
interdisent. §7, alternative 1.

*Un outil est né de là : `comparer_schemas.py`, la méthode B4 généralisée à
deux dossiers quelconques. Elle n'existait qu'en dur pour l'étape 6.*

### J'ai failli déclarer une régression en comparant au mauvais témoin

Au premier essai de la pose 4, `02_effectifs.csv` de `jeu_02` annonçait
`journees_ecartees_qc = 17` et `journees_retenues = 1199`, là où j'avais en
tête 1 et 1215. J'ai cru un instant que le correctif 10 déplaçait des valeurs.

Les chiffres que j'avais en tête venaient de la **référence V4.5**. Le témoin
valide est le rejeu de `app/` d'avant la pose, qui portait déjà 17 et 1199 —
le détecteur relatif du correctif 1 écarte plus de journées que celui de V4.5.
Vérifié : les deux rejeux `app` sont identiques sur ces colonnes.

C'est la leçon de l'étape 7 — « comparer au bon témoin » — et je l'ai retrouvée
en la manquant. **Un chiffre mémorisé n'a pas de provenance ; c'est ce qui le
rend dangereux.**

### Un piège évité par le raisonnement, faute de mesure qui l'aurait vu

Le correctif 10 fait appeler à l'orchestrateur `marquer_lecture` au lieu de
`charger_eau`. Or `_commun.Journal` enveloppe `charger_eau` pour journaliser ce
que la lecture a vu : sans enveloppe sur la nouvelle fonction, `journal.eau`
serait resté **vide**, et le bloc `eau` de `01_colonnes_retenues.json` aurait
disparu. Un artefact déclaré FIGÉ se serait mis à bouger, pour une raison sans
rapport avec le correctif.

Aucune mesure ne l'aurait signalé **avant** : il aurait fallu poser, rejouer
quinze minutes, et lire un diff surprenant. Il a été vu en relisant qui appelle
quoi. **Quand un correctif remplace un point d'entrée, la question à poser
n'est pas « qui l'appelle » mais « qui l'observe ».**

### Une assertion a arrêté un script avant qu'il n'écrive

Le script d'inventaire des littéraux a échoué sur une ancre de docstring dont
j'avais mal relevé l'indentation. Il a échoué **avant** la ligne d'écriture, et
n'a rien laissé derrière lui. C'est la contrepartie utile de la règle posée à
l'étape 7 : toute substitution est assertée, et rien n'est écrit tant que
toutes les ancres n'ont pas été trouvées.

### Deux points où la commande était inexacte, vérification à l'appui

**Le seuil de vingt jours n'était pas écrit deux fois, mais trois.** D78 dit
« désormais écrit deux fois depuis D67 ». Relevé : le garde-fou
`if len(sub) < 20`, **le message du journal** — qui le portait déjà avant D67 —
et le motif ajouté par D67. Deux avant, trois après. Les trois citent
désormais `N_MIN_M_SAISONNIER`.

**« Le harnais le consigne comme NON_RECUPERABLE depuis l'étape 1 »** est vrai
du chemin de code et faux de sa sortie : **zéro ligne `lecture_sonde`, zéro
`NON_RECUPERABLE`**, ni dans la référence V4.5 figée, ni dans le rejeu de
`app/`. La branche existe, elle n'a jamais rien produit — parce que la
suppression qu'elle décrit ne supprime rien sur ce corpus (§5).

### D77, D69, D71 tenus

**D77** : `pose1_d73.py` avait besoin des champs du `QCConfig` de `ref/v4_5/`.
Il les lit **par AST**, sans jamais importer le module — donc sans possibilité
d'écrire un `.pyc` sous `ref/`. Le contrôle de clôture le confirme : **zéro
bytecode**.

**D69** : neuf scripts, tous écrits comme fichiers. Chacun lit et écrit en
octets, relève les fins de ligne à l'entrée et les restitue à la sortie — CRLF
pour le harnais, LF pour `app/` et `docs/` —, assertit chaque ancre, et n'écrit
rien tant qu'elles ne sont pas toutes trouvées. Aucun CRLF introduit ; D44 le
vérifie après coup.

**D71** : aucun script sondé. `build_reference.py` a toujours été invoqué avec
`--sortie` explicite — et il refuse désormais de lui-même de construire dans un
dossier qui porte un manifeste sans qu'on l'ait déclaré (§3).

---

## §1 — D44 et D76

### D44

**Avant** : sept entrées, exactement les sept déclarées, **aucune en CRLF**,
retour **0**.

**Après** : **dix** entrées, exactement les dix déclarées, retour **0**, aucun
CRLF introduit. Les trois nouvelles viennent de la pose 3.

| Fichier | Avant | Après | Pose |
|---|---|---|---|
| `app/LISEZ-MOI.md` | 10 lignes | 10 | — |
| `app/app.py` | 895 | **940** | 3, 5 |
| `app/thermie_debits/config.py` | 481 | 481 | — |
| `app/thermie_debits/core.py` | 1597 | **1609** | 5 (D78) |
| `app/thermie_debits/exports.py` | *identique à ref* | **312** | 3 |
| `app/thermie_debits/figures.py` | *identique à ref* | **1196** | 3 |
| `app/thermie_debits/io_data.py` | 576 | **659** | 4 |
| `app/thermie_debits/livrables.py` | *identique à ref* | **601** | 3 |
| `app/thermie_debits/orchestrator.py` | 308 | **319** | 4 |
| `app/thermie_debits/qc.py` | 515 | 515 | — |

### D76 — le contrôle permanent entre en service

`verifier_integrite_references.py` tourne désormais au début et à la fin de
chaque étape, aux côtés de `diff_app_ref.py`.

| | Avant | Après |
|---|---|---|
| `tests/reference` | 66/66, 0 divergence | 66/66, 0 divergence |
| `tests/reference_cli` | **60 lignes au manifeste, 6 hors manifeste, 12 empreintes divergentes** | **66/66, 0 divergence** |
| bytecode sous `ref/` | 0 | **0** |
| **retour** | **1** | **0** |

**C'est la première fois que ce contrôle passe.** Il n'existait pas avant
l'étape 12, et il a échoué dès sa première exécution.

---

## §2 — Pose 1 : D73, la reproductibilité de la référence

### 1.1 — La table `ref` est lue, jamais reconstituée

`parametres.py` porte désormais quatre tables de contrôle qualité, indexées par
`(source de code, chemin de paramètres)` :

```
QC_REF_APPLICATION / QC_REF_CLI    le QCConfig de ref/v4_5 — 14 champs
QC_APP_APPLICATION / QC_APP_CLI    le QCConfig de app/     — 18 champs
```

**La table `ref` n'a pas été écrite de mémoire.** Chaque référence porte, dans
ses six `10_parametres.json`, la table qui l'a produite — valeur, provenance et
justification comprises. C'est la seule source qui ne puisse pas diverger de la
référence, puisqu'elle en fait partie. Le script la lit, vérifie qu'elle est
**unanime sur les six jeux** de chaque dossier, puis vérifie que son jeu de
champs est **exactement** celui du `QCConfig` de
`ref/v4_5/thermie_debits/config.py` — lu par AST, jamais importé (D77) — et
n'émet le littéral qu'après.

C'était nécessaire, pas scrupuleux : `10_parametres.json` est un artefact, et
une virgule différente dans une justification y est une divergence. Une
justification retapée de mémoire aurait fait échouer le contrôle pour une
raison sans rapport avec ce qu'on voulait mesurer.

**Le coût que je prêtais à cette branche n'existe pas, et D73 avait raison de
le dire** : `ref/v4_5/` est en lecture seule (D1), donc son `QCConfig` ne
bougera plus. La table `ref` s'écrit une fois. Seule la table `app` suit les
correctifs.

**`AnalyseConfig` et `SourcesConfig` n'ont pas bougé** entre les deux sources —
14 et 22 champs de part et d'autre, vérifié par AST. Les tables `ANALYSE_*`
restent donc **communes**, et ce module ne les duplique pas : dupliquer ce qui
ne diverge pas fabrique deux vérités là où il n'y en a qu'une.

### 1.2 — La prédiction, et ce qu'elle a réellement établi

**Prédiction : DIFF VIDE sur 66. Constat : 18 artefacts divergents.**

Les 18 sont trois artefacts × six jeux — `02_effectifs.csv`,
`03_journees_ecartees.csv`, `06_coefficients.csv` — et chacun affiche **autant
de lignes retirées qu'ajoutées** : ce sont des en-têtes, pas des valeurs.

**Ce qui a été rétabli, et qui est le fond de D73** : `THERMIE_CODE=ref`
**s'exécute à nouveau**. Avant la pose, 32 points sur 32 échouaient sur
`TypeError: QCConfig.__init__() got an unexpected keyword argument 'k'`, et le
code de retour valait 0. Après, 31 points OK et un seul échec — celui de
`BIE35-5__NA`, qui **est** la référence (D7).

**Ce que la comparaison à schémas différents établit** (§0) : 5 113 270 valeurs
confrontées, **0 divergente**, 6 journaux identiques au bit près, 0 colonne
disparue. Les 14 colonnes ajoutées sont toutes attribuables :

| Colonnes ajoutées | Origine |
|---|---|
| `journees_non_diag_air_absent`, `journees_non_diag_densite` | correctif 5 (D45), étape 7 |
| `E_moy_rel`, `R_ampl_rel`, `E_max_rel`, `longueur_episode`, `marche_active` | D57, étape 10 |
| `m_estime`, `validite_ic95_demi_largeur`, `validite_erreur_type_nw`, `validite_t`, `validite_lag_nw`, `validite_critere_rejetant` | correctif 6, étape 11 |
| `validite_statut` | correctif 6, étape 11 ; troisième valeur `replie` à l'étape 12 (D67) |

### 1.3 — Aucun artefact ne bouge du côté `app`

Rejeu `THERMIE_CODE=app` d'avant contre celui d'après, à corpus et paramètres
identiques : **66 artefacts sur 66 figés au bit près**, `10_parametres.json`
compris. `parametres.py` appartient bien au harnais.

---

## §3 — Pose 2 : D75, le manifeste sur déclaration

### 2.1 — La condition de chemin disparaît

```python
    if not args.sans_manifeste and sortie == ICI:      # avant
        ecrire_manifeste()
```
```python
    if args.est_une_reference and not args.sans_manifeste:   # après
        n = ecrire_manifeste(sortie)
```

`ecrire_manifeste(sortie)` écrit **là où l'on construit**, et non dans un
dossier fixé d'avance.

**Une garde qui n'était pas demandée.** Sans elle, D75 remplacerait un
manifeste qu'on ne *pouvait pas* écrire par un manifeste qu'on peut *oublier*
d'écrire — le même silence, déplacé. `build_reference.py` refuse donc de
construire dans un dossier qui porte déjà un `MANIFEST.sha256` si
`--est-une-reference` n'est pas passé, et il refuse **avant** de construire.

Les deux chemins ont été essayés, sur des dossiers jetables pour ne pas risquer
la vraie référence :

| Essai | Verdict | Retour |
|---|---|---|
| dossier portant un manifeste, drapeau absent | **ARRÊT**, aucun jeu construit | **2** |
| dossier neuf, drapeau présent | manifeste écrit, 11 artefacts | 0 |

### 2.2 — Le manifeste de la référence seconde, et pourquoi ce n'est pas un rebasage

Aucun artefact n'est reconstruit. Les 66 fichiers de `tests/reference_cli/`
sont ceux de l'étape 6 ; on enregistre ce qui est là. Vérifié plutôt que
supposé : les 66 empreintes sont **identiques avant et après** l'écriture du
manifeste, dans les deux dossiers.

Pour que la distinction ne se perde pas, `SOURCE_CODE.txt` porte désormais
**deux dates** :

| | `ETAPE` (artefacts) | `MANIFESTE_ECRIT_A_L_ETAPE` |
|---|---|---|
| `tests/reference` | 6 | **6** |
| `tests/reference_cli` | 6 | **13** |

Confondre les deux ferait lire un rebasage là où il n'y en a pas eu.

### 2.3 — Le but de la pose

`verifier_integrite_references.py` : **66/66 sur les deux références, zéro
divergence, retour 0.**

---

## §4 — Pose 3 : D74, le vocabulaire

### 3.1 et 3.2 — Six réparées, deux laissées, et une correction de mon compte

**Une inexactitude de mon rapport d'étape 12, qu'il faut corriger.** Il
annonçait « six étiquettes fausses » et en listait **sept**, dont
`figures.py:68-70` qui est un **commentaire de code**, pas une étiquette. D74 a
lu « six » et demandé d'en réparer cinq, la sixième dépendant de l'arbitrage.

Le relevé refait donne autre chose : **les six étiquettes fausses portent
toutes sur la famille normalisation**, et **aucune ne dépend de l'arbitrage**.
Les deux qui en dépendent ne sont pas des étiquettes fausses mais les deux
**abus** relevés au C2.

**Réparées — six étiquettes, plus le commentaire :**

| Emplacement | Avant | Après |
|---|---|---|
| `figures.py:91` | « Tmh — eau **COMPENSÉE** (année standard) » | « eau **NORMALISÉE** » |
| `figures.py:94` | « Écart brut ↔ **compensé** » | « ↔ **normalisé** » |
| `figures.py:68-70` | commentaire « l'eau **compensée** » | « l'eau **NORMALISÉE** » |
| `livrables.py:212` | Word §1.4 : « brute puis **compensée** » | « brute puis **normalisée** » |
| `exports.py:163` | classeur fraie : « **non compensées** » | « **non normalisées** » |
| `app.py:108-109` | « pour **la compensation** » / « **La compensation** retranche m × … » | « pour **la normalisation** » / « **La normalisation** retranche m × … » |
| `app.py:569` | « Températures brutes **non compensées** » | « Températures brutes, **non normalisées** » |

*`app.py:569` contredisait `app.py:573` — « sans normalisation climatique » —
trois lignes plus bas. Les deux concordent désormais.*

**Laissées, et c'est dit** — `indicateurs.py:85` et `app.py:604`, les deux abus
« ramenée aux conditions normales ». **Les deux portent sur les colonnes
compensées du tableau mensuel**, c'est-à-dire sur l'objet même de l'alternative
en arbitrage. Toute formulation écrite aujourd'hui serait à réécrire dans les
deux voies : la voie A rendrait la phrase vraie, la voie B ferait disparaître
ce qu'elle décrit. 3.2 le prévoyait ; les deux y tombent.

### 3.3 — La prédiction

**66 artefacts sur 66 figés.** Aucune étiquette n'entre dans un artefact.

---

## §5 — Pose 4 : le correctif 10, mesure puis pose

### 4.1 — La mesure, et ce qu'elle contredit

`tests/reference/mesure_dropna_lecture.py`. La trame telle qu'elle est **juste
avant** `io_data.py:98` n'est retournée par rien : il faut rejouer les lignes
46-97. Le rejeu appelle les fonctions de l'application elles-mêmes, et —
puisqu'une réplication non vérifiée ne vaut rien (étapes 8 et 9) — **chaque
point est contrôlé** : la table journalière reconstruite est confrontée à celle
que `charger_eau` retourne réellement.

| | |
|---|---|
| réplication contrôlée **identique** | **32 points sur 32** |
| mesures lues sur le corpus | **1 694 252** |
| **mesures supprimées** | **0** |
| points touchés | **0 / 32** |
| journées entièrement perdues | **0** |

**Cette ligne ne supprime rien sur ce corpus.** Corroboré indépendamment :
**zéro ligne `lecture_sonde`** et **zéro `NON_RECUPERABLE`** dans les
artefacts, ni dans la référence V4.5 figée ni dans le rejeu d'aujourd'hui.

Le défaut est donc **réel dans le code et jamais exercé sur ce corpus** —
exactement le cas de `qc.py:32-36` à l'étape 5. **Le correctif est de
robustesse, pas de résultat.** Il est posé quand même : l'étape 7 a établi
qu'une cause absente du corpus n'est pas une cause impossible.

### 4.2 — La pose

`marquer_lecture()` produit une table où chaque mesure écartée est nommée, avec
sa cause distinguée — date illisible, température illisible, les deux.
`charger_eau()` conserve signature et retour et devient l'adaptateur : aucun de
ses appelants ne bouge. C'est la forme du correctif 3 et du correctif 5.

**Une asymétrie qu'il fallait dire.** Une mesure dont la **température** est
illisible garde sa date : elle s'impute à une journée. Une mesure dont la
**date** est illisible ne s'impute à rien. La table porte donc une date qui
peut être nulle, et **le total n'est pas la somme des comptes annuels**. Taire
cela produirait un total qui ne se recoupe pas.

**Un défaut d'alignement pandas, corrigé avant la pose.** Ma première écriture
construisait la table en mélangeant un `Index` et des `Series` dans un
constructeur de `DataFrame` : pandas aurait aligné les uns sur les autres, et
les motifs se seraient retrouvés sur les mauvaises lignes **sans que rien ne le
signale**. Tout est construit en listes, positionnellement.

**Le harnais lit, et cesse de déduire.** `art_03` lit `res.marques_lecture` ; la
branche de déduction est conservée pour rejouer `ref/v4_5`, qui ne produit pas
la table. `art_02` gagne `mesures_ecartees_a_la_lecture`, qui vaut `0` côté
`app` et **la chaîne vide** côté `ref` : écrire zéro là où rien n'est mesuré
serait le même mensonge que celui que ce correctif retire.

### 4.3 — La prédiction, et la ligne que j'avais déclarée figée à tort

| Artefact | Déclaré | Constaté |
|---|---|---|
| `02_effectifs.csv` | doit bouger — une colonne | **6/6, 0 valeur changée** |
| `03`, `04`, `05`, `06`, `07`, `08`, `00`, `01`, `10` | figés | **FIGÉS** |
| `99_log.txt` | figé | **1/6 bouge — 1 ligne** |

**Aucune valeur n'a changé** : c'est la prédiction 4.3, et elle tient. Les six
`02_effectifs.csv` bougent d'une colonne et de zéro valeur.

**La ligne de `99_log.txt` :**

```
- File "<CODE>/thermie_debits\orchestrator.py", line 182, in run
+ File "<CODE>/thermie_debits\orchestrator.py", line 193, in run
```

C'est un **numéro de ligne dans la trace d'erreur figée** de `BIE35-5__NA`, que
D7 conserve comme référence. Le correctif ajoute onze lignes au-dessus du point
d'appel, qui descend de 182 à 193.

Mon motif — « le `print` n'est émis que si des mesures sont écartées, donc
jamais » — était **juste sur ce que le correctif AJOUTE au journal, et
incomplet sur ce qu'il y DÉPLACE**. C'est la troisième forme de motif erroné du
chantier, rencontrée pour la deuxième fois.

Et le mouvement est **légitime** : l'étape 1 a décidé de masquer les numéros de
ligne du **harnais** dans ces traces, et de **conserver ceux de l'application**
— « ce sont eux qui portent l'information ». Un correctif qui déplace du code
déplace donc ce numéro, par construction.

### 4.4 — Le côté `ref` survit

Le harnais a changé ; `ref/v4_5` doit continuer d'être rejouable. Vérifié sur
`jeu_02` : **100 710 valeurs confrontées, 0 divergente**, une seule colonne
ajoutée — la colonne déclarée —, `99_log.txt` identique au bit près.

---

## §6 — Pose 5 : le correctif 7 (D22, D78)

### 5.1 — L'inventaire, refait plutôt que repris

Le relevé de l'étape 3 décrivait un `app.py` qui n'existe plus.

| | Étape 3 | Étape 13 |
|---|---|---|
| dérivés du dataclass | 8 | **12** |
| **littéraux** | **19** | **17** |
| détectés sur fichier | 9 | 9 |
| non exposés | 14 | 16 |

**Les deux littéraux divergents ont disparu avec l'ancien détecteur, et non
parce qu'on les aurait corrigés** — vérifié, non supposé.
`hors_eau_ecart_seuil` (10,0 contre 4,0) et `hors_eau_exclut_saison` (False
contre True) portaient sur des champs que le correctif 1 (étape 10) puis D61
(étape 11) ont retirés de `QCConfig`. Les widgets qui les remplacent — `k`,
`plancher_dispersion`, `min_jours_groupe`, `min_jours_episode`, `q_ampl` —
prennent **tous** leur défaut du dataclass : le correctif 1 avait appliqué la
règle du correctif 7 d'emblée à ses widgets neufs.

### 5.4 — La coïncidence, vérifiée AVANT la pose

**17 littéraux, 0 divergent.** Les dix-sept coïncident avec le dataclass, à la
résolution de `None` près pour `espece_repere`. La pose ne peut donc rien
changer aux valeurs appliquées : c'est de l'hygiène, et cela se vérifie avant
plutôt que se constate après.

### 5.2 — Quinze dérivés, deux invariants déclarés

**Dérivés (15).** Deux instances, `_DEFAUTS = AnalyseConfig()` et
`_SOURCES = SourcesConfig()`, sont les seules références de défaut de
l'interface. Les trois défauts **par position** — `contexte_piscicole`,
`espece_repere`, `mode` — cessent d'être des positions : l'index se **calcule**
depuis le dataclass. Réordonner `CONTEXTES` ne change plus rien.

*Pour `espece_repere`, le dataclass dit `None`, qui **résout** vers
`espece_defaut`. C'est cette résolution qu'on indexe, et non la position 0 —
laquelle coïncidait seulement parce que `especes_disponibles` place l'espèce par
défaut en tête. Une coïncidence tenue par une convention est devenue une
référence.*

**Laissés littéraux, et déclarés comme tels (2).** `output_dir=None` et
`fichier_normales=None` ne sont pas des défauts de widget : ce sont des
**arguments de construction**, et ce qu'ils expriment est un **invariant de
l'application**. Les dériver ferait suivre au comportement de l'application un
changement du dataclass : le jour où `output_dir` porterait un chemin,
l'application se mettrait à écrire sur disque sans que personne ne l'ait voulu.
5.2 vise les défauts de widget ; ces deux-là n'en sont pas, et portent
désormais un commentaire qui le dit.

### 5.3 — D78, et une correction du compte

**Le seuil n'était pas écrit deux fois, mais trois** : le garde-fou
`if len(sub) < 20`, le message du journal — qui le portait **avant** D67 — et
le motif ajouté par D67. Une seule origine, `N_MIN_M_SAISONNIER`, citée par les
trois. Le texte rendu par le journal est **inchangé** (« 20 » reste « 20 ») :
`99_log.txt` ne devait pas bouger, et il n'a pas bougé.

### 5.5 — La note demandée, sans action

`app.py:378` passe un littéral `None` à `fichier_normales`. Ce `None` bascule
l'orchestrateur vers la branche qui **calcule** les normales depuis l'air brut ;
la branche opposée — `EcartNormales` pré-calculé — reste atteignable par la CLI
et **aucun jeu du corpus ne l'exerce**. Un défaut littéral qui ouvre une branche
non testée mérite d'être dit : il l'est ici, et rien n'a été fait.

*Il rejoint la liste ouverte depuis l'étape 1 — débit désinfluencé, normales
pré-calculées, export d'air multi-stations — et le garde-fou du MAD nul, qui ne
se déclenche jamais.*

### 5.4 bis — La prédiction

**66 artefacts sur 66 figés**, `99_log.txt` compris. L'inventaire refait après
la pose : **27 dérivés, 2 littéraux, 0 divergent**.

---

## §7 — Alternatives fermées

### Alternative 1 — Le DIFF VIDE littéral est-il un objectif ?

Le contrôle de reproductibilité passe **sur les colonnes communes** : 5 113 270
valeurs, 0 divergente, six journaux identiques au bit près. Il ne passera
jamais **sur les fichiers entiers** tant que la référence datera de l'étape 6 et
que le harnais aura grossi.

| Branche | **A — laisser** | **B — rebaser à la clôture** | **C — figer le schéma du harnais** |
|---|---|---|---|
| ce qu'il faut faire | rien ; `comparer_schemas.py` fait foi | reconstruire les deux références en fin de chantier | interdire l'ajout de colonnes sans rebasage |
| `check_reference` rend DIFF VIDE | **non, jamais** | **oui** | oui |
| point de comparaison avec V4.5 | conservé | **conservé, mais redaté** | conservé |
| coût | un outil de plus à savoir lancer | un rejeu, et la perte de la datation « étape 6 » | fige la capacité du harnais à observer davantage |
| risque | un lecteur pressé lit « 18 divergents » et conclut mal | aucun, si c'est fait **après** le dernier correctif | le harnais cesse de pouvoir suivre les correctifs |

**Ce qui les départage.** Si `tests/reference/` doit rester **l'état V4.5 tel
qu'observé à l'étape 6**, c'est A, et il faut accepter que le diff de fichiers
ne soit plus le bon outil. Si elle doit rester **rejouable par
`check_reference`**, c'est B — et B4 dit que ce n'est pas un geste de milieu de
chantier. **C est à écarter** : elle échange un contrôle contre un autre, et
c'est la capacité d'observation qu'elle sacrifie.

*Je penche pour A jusqu'à la clôture, puis B au moment de clore. Je ne
tranche pas : rebaser est la décision que B4 réserve au commanditaire.*

### Alternative 2 — Les deux abus de vocabulaire, quand ?

`indicateurs.py:85` et `app.py:604` — « ramenée aux conditions normales » —
décrivent les colonnes compensées, objet de l'arbitrage D72.

| Branche | **A — attendre l'arbitrage** | **B — écrire une phrase vraie aujourd'hui** |
|---|---|---|
| ce qu'on écrit | rien | « l'anomalie brute d'air est retranchée, sans pondération » |
| durée de vie | jusqu'à l'arbitrage | **jusqu'à l'arbitrage aussi** — la voie A la rendrait fausse, la voie B ferait disparaître son objet |
| ce qui reste publié entre-temps | une phrase fausse | une phrase juste |
| risque | l'écran affirme une exactitude qu'il n'a pas | deux réécritures au lieu d'une |

**Ce qui les départage** : la phrase actuelle n'est pas seulement imprécise,
elle est **fausse** — la ramenée n'est exacte que si l'eau suit l'air un pour
un, et le `m` médian du corpus vaut 0,432. Publier une phrase fausse en
attendant une décision de forme est un choix, pas une neutralité.

*J'ai retenu A, parce que 3.2 le demandait explicitement. Je signale que A
laisse une phrase fausse à l'écran, et que ce n'est pas gratuit.*

---

## §8 — Ce qui reste

**Correctif 4** — la spécification est écrite, l'alternative attend son
arbitrage (D72). **L'affichage** de toute la dégradation déclarée (D48, étape
14). **L'alternative 1 du §7** — le sort du diff littéral, à la clôture.
**La liste ouverte depuis l'étape 1** — débit désinfluencé, normales
pré-calculées, export d'air multi-stations, garde-fou du MAD nul, et désormais
la branche `EcartNormales` (5.5) : cinq comportements que le corpus n'exerce
pas.
