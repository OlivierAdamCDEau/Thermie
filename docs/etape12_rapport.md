# THERMIE_BIO V4.6 — Rapport d'étape 12

**Objet.** Poser **D70** — une référence dit désormais quel code l'a produite,
et le harnais refuse de la comparer à un autre. Écrire **la spécification du
correctif 4**, le seul du chantier à n'en avoir jamais eu. Poser **D67**, le
statut `replie`.

**Ce que l'étape n'a pas fait, et c'était prévu.** Le correctif 4 n'est pas
posé. La commande le subordonnait à l'arbitrage de la question de conception
C4 ; §5 dit pourquoi cette question n'est **pas** sans ambiguïté, et §6 la
remonte comme alternative fermée.

---

## Artefacts déclarés (D34, D54, D63)

Deux poses distinctes dans cette étape. Une seule touche `app/`.

| Pose | Artefact | Type (D63) | Déclaré | Verdict du motif | Constaté |
|---|---|---|---|---|---|
| **D70** | *aucun* | — | aucun artefact ne bouge : le fichier de provenance n'est ni un artefact ni une entrée du manifeste | **juste** | **66 figés** |
| **D67** | `06_coefficients.csv` | **dépendance propre** | doit bouger — deux colonnes se remplissent | **juste** | **1/6 — `jeu_bienne` seul** |
| **D67** | `99_log.txt` | trace console | **figé** — le `print` du repli n'est pas touché | **juste** | **FIGÉ 6/6** |
| **D67** | `07_t_norm.csv` | projection de `res.df` | **figé** — `m_saisonnier` est retourné à l'identique | **juste** | **FIGÉ** |
| **D67** | `08_scores.csv` | dépendance propre | **figé** — aucun score ne lit un statut | **juste** | **FIGÉ** |
| **D67** | `00`, `01`, `02`, `03`, `04`, `05`, `10` | métadonnées et projections | **figés** | **juste** | **FIGÉS** |

**Aucun motif n'était faux, et aucun n'était incomplet.** C'est la deuxième
fois en cinq étapes. La raison n'est pas du mérite : D67 est une pose dont
l'effet a été mesuré **avant** sur la chaîne exacte où elle serait posée, et
dont le périmètre — un dictionnaire de diagnostic qui ne retourne pas dans le
calcul — se lit dans le code sans dépendre des données.

---

## §0 — Carnet de bord

### Ce que la tâche B a trouvé en la vérifiant : la référence n'est plus reproductible

D70 demandait d'écrire la provenance et de refuser une comparaison qui ne
concorde pas. Le refus fonctionne. Mais en vérifiant que **l'invocation
concordante**, elle, passe bien — `THERMIE_CODE=ref` contre
`tests/reference/`, la seule que le fichier de provenance autorise —, le rejeu
a rendu **66 artefacts divergents sur 66**.

Ce n'est pas une corruption. C'est un `TypeError` unique, répété **32 fois sur
32 points** :

```
TypeError: QCConfig.__init__() got an unexpected keyword argument 'k'
```

`tests/reference/parametres.py` décrit le `QCConfig` de `app/`. Depuis le
correctif 1 (étape 10) puis le correctif 6 (étape 11), celui-ci porte **sept
champs que `ref/v4_5/` n'a pas** — `k`, `plancher_dispersion`,
`min_jours_groupe`, `min_jours_episode`, `q_ampl`, `m_domaine`,
`m_niveau_ic` — et en a perdu trois. `construire_config` échoue donc avant
d'avoir lu un seul fichier, et le harnais fige chaque échec comme référence
(D7). **Le code de retour est 0.** C'est le piège de l'étape 11, à nouveau :
un harnais qui capture les échecs par point rend zéro quand tout a échoué.

**Depuis l'étape 10, `tests/reference/` ne peut plus être reproduite depuis la
source qui l'a produite, et rien ne le signalait** — parce que depuis
l'étape 7 la méthode compare deux rejeux de `app/` entre eux, et que plus
personne n'invoquait `check_reference` avec `THERMIE_CODE=ref`.

Un rejeu `ref` produit aujourd'hui un diff total sur les 66 artefacts. **C'est
très exactement ce à quoi ressemble une corruption de dépôt**, et c'est la
raison la plus vraisemblable pour laquelle une invocation erronée a pu être
lue comme telle. Le fichier de provenance ne répare pas cela : il documente
une source qui ne réplique plus. C'est remonté au §6, alternative 2, sans être
tranché — décider quel `QCConfig` `parametres.py` décrit est un choix de
méthode, pas une correction.

*La leçon générale : **un contrôle qu'on n'exécute plus ne tombe pas en panne,
il disparaît**. Celui-ci était en panne depuis deux étapes, et il a fallu
vouloir en poser un autre pour s'en apercevoir.*

### Une preuve d'intégrité qui n'était pas cherchée

Le D44 « avant » de cette étape est **identique au bit près** au D44 « après »
de l'étape 11 — même SHA-256 sur le CSV entier,
`1f204ef0fd1a2c9e109fa8bc736f696faa42d8e304832055d591c5219837f50c`. Les sept
fichiers de `app/` qui diffèrent de `ref/v4_5/` le font aux mêmes octets, aux
mêmes lignes, avec les mêmes empreintes.

Le déplacement OneDrive n'a rien altéré dans `app/`. Ce contrôle-là n'était
pas demandé ; il est tombé gratuitement parce que D44 écrit ses empreintes et
qu'un fichier écrit à l'étape 11 était encore là pour être comparé. **Un
contrôle qui laisse une trace chiffrée sert deux fois.**

### Ce qui n'a pas été livré, et pourquoi

`out/etape12/A_diff_app_ref_avant.txt` n'existe pas. La sortie console du D44
« avant » n'a pas été redirigée vers un fichier au moment où elle a été
produite, et `core.py` a bougé depuis : la reproduire aujourd'hui donnerait la
sortie d'après en la datant d'avant. Le CSV, lui, a bien été écrit, et il
porte l'information intégrale — c'est lui qui fait foi. **Un fichier
reconstitué après coup et présenté comme un relevé est un faux ; l'absence se
signale.**

### Deux contrôles qui n'existaient pas, et ce qu'ils ont trouvé

Après la pose, deux vérifications ont été faites qui n'étaient pas au
programme : les deux `MANIFEST.sha256` décrivent-ils leur dossier, et reste-t-il
du bytecode sous `ref/` ? Elles vivent désormais dans
`tests/reference/verifier_integrite_references.py`, et
`out/etape12/F_integrite_references.txt` porte leur sortie.

**Constat 1 — j'ai écrit dans `ref/`, et c'est D1.** Un script de diagnostic de
cette étape, écrit pour comparer les champs de `QCConfig` entre `ref/v4_5/` et
`app/`, a chargé `ref/v4_5/thermie_debits/config.py` par `importlib`. Le
chargement a **échoué**, et il a tout de même laissé
`ref/v4_5/thermie_debits/__pycache__/config.cpython-314.pyc` — 15 719 octets,
horodaté 11:05:21.

C'est exactement l'écriture silencieuse identifiée à l'étape 1 : le
`.gitignore` du dépôt la masque à `git status`, si bien que le contrôle habituel
ne la voit pas. La parade existait — `_commun.py` pose
`sys.dont_write_bytecode = True` avant tout import — **et elle ne protège que
ce qui passe par `_commun.py`**. Mon script n'y passait pas.

Le fichier a été supprimé et `ref/` rendu à son état d'origine ; le contrôle
rejoué dit **0 fichier de bytecode, 0 dossier `__pycache__`**. Les seize
sources de `ref/v4_5/` sont vérifiées intactes par empreinte, et les six qui
apparaissent dans D44 portent les mêmes `sha_ref` qu'à l'étape 11.

*La deuxième leçon est la plus utile : la protection était en place et j'ai
écrit à côté d'elle. **Une garde posée dans un module ne protège pas le
projet, elle protège ses appelants.***

**Constat 2 — `tests/reference_cli/MANIFEST.sha256` est périmé depuis
l'étape 6, et la cause est dans le code.**

| | |
|---|---|
| artefacts sur disque | **66** |
| lignes au manifeste | **60** |
| hors manifeste | **6** — les six `10_parametres.json` |
| empreintes divergentes | **12** — `07_t_norm.csv` et `99_log.txt`, sur les six jeux |

Ce sont **exactement** les artefacts que l'étape 6 avait fait bouger en B4 : le
dossier y a gagné ses six `10_parametres.json` et sa colonne `sortie_v45`, et
ses journaux ont gagné le volet climatique. Le manifeste, lui, n'a pas suivi —
et il ne pouvait pas suivre :

```python
    if not args.sans_manifeste and sortie == ICI:      # ICI = tests/reference
        ecrire_manifeste()
```

`build_reference.main` n'écrit le manifeste que si la sortie est
`tests/reference`. **`tests/reference_cli/` n'est donc jamais remanifestée,
quoi qu'on y reconstruise.** Ce n'est pas un oubli d'exécution, c'est une
condition dans le code, et elle rend le manifeste de la référence seconde
structurellement incapable de suivre ses rebasages.

**Rien n'a été corrigé.** Réécrire le manifeste d'une référence est adjacent à
la rebaser, ce que B4 interdit, et le geste engage une décision : voir §6,
alternative 4. `tests/reference/`, elle, est vérifiée **conforme — 66 sur 66,
zéro divergence**.

*Ces deux constats ont la même forme que celui du §0 précédent : un contrôle
qui n'existe pas ne se signale jamais comme manquant. Trois en une étape, dont
deux trouvés parce qu'on en posait un autre.*

### Trois écritures, trois scripts, aucune ligne de commande

D69 tenu sans exception : `patch_B_d70.py`, `patch_E_d67.py`,
`ajouter_verdicts.py`, `patch_livraison.py`. Chacun lit et écrit en **octets**,
relève les fins de ligne du fichier à l'entrée et les restitue à la sortie —
CRLF pour le harnais, LF pour `app/` et `docs/` —, **assertit chaque ancre**,
et n'écrit rien tant que toutes les ancres n'ont pas été trouvées. Aucun CRLF
n'a été introduit ; D44 le vérifie après coup.

*Une nuance sur D69, qui ne m'absout pas : les quatre scripts de pose ont bien
été écrits comme fichiers. Le script de diagnostic qui a écrit dans `ref/`,
lui, était un `python - <<'PY'` — un document heredoc. D69 vise le piège du
`\n`, et ce n'est pas celui qui s'est refermé ; mais s'il avait été un fichier
posé à côté des autres, l'import de `ref/v4_5/` s'y serait vu.*

D71 tenu : aucun script n'a été sondé. `check_reference.py` et
`build_reference.py` ont été exécutés pour de bon, avec `--sortie` explicite à
chaque fois — **jamais sans**, puisque `build_reference.py` sans `--sortie`
écrit dans `tests/reference/` et rebaserait la référence que B4 interdit de
toucher.

---

## §1 — D44

**Avant** : sept entrées, exactement les sept déclarées, **aucune en CRLF**.

| Fichier | État | Nature | Lignes app / ref |
|---|---|---|---|
| `app/LISEZ-MOI.md` | absent de `ref/v4_5` | — | 10 / 0 |
| `app/app.py` | différent | CONTENU | 895 / 877 |
| `app/thermie_debits/config.py` | différent | CONTENU | 481 / 444 |
| `app/thermie_debits/core.py` | différent | CONTENU | 1577 / 1145 |
| `app/thermie_debits/io_data.py` | différent | CONTENU | 576 / 558 |
| `app/thermie_debits/orchestrator.py` | différent | CONTENU | 308 / 292 |
| `app/thermie_debits/qc.py` | différent | CONTENU | 515 / 115 |

*`app/LISEZ-MOI.md` porte 10 CRLF ; c'est son état depuis l'étape 7, et il n'a
pas de contrepartie dans `ref/v4_5/` — la colonne `nature` ne le compare à
rien. Aucun fichier de code n'est en CRLF, ni avant ni après.*

**Après** : les mêmes sept, **CONFORME**, retour **0**. Seul
`app/thermie_debits/core.py` a bougé — 1577 → **1597** lignes, 77 003 → 78 261
octets — au titre de D67. Aucun CRLF introduit.

`out/etape12/D44_avant.csv`, `out/etape12/D44_apres.csv`,
`out/etape12/A_diff_app_ref_apres.txt`.

---

## §2 — D70 : la provenance d'une référence

### B1 — `build_reference.py` écrit `SOURCE_CODE.txt`

À la racine du dossier construit, référence **ou rejeu jetable** :

```
SOURCE_CODE=ref
ETAPE=6
CHEMIN_DE_PARAMETRES=application
```

**Le fichier n'entre ni dans le manifeste ni dans le diff**, et ce n'est pas
un aménagement : `est_artefact` (`_commun.py:380`) exige un nom
`<NN>_….{csv,json,txt}` dans un **sous-dossier de jeu**. `SOURCE_CODE.txt` est
à la racine et ne porte pas de préfixe numérique. Il documente la référence
sans en faire partie — condition pour qu'ajouter la provenance ne déplace pas
les 66 artefacts qu'elle sert à protéger. Vérifié : les deux `MANIFEST.sha256`
sont inchangés.

**Il est écrit pour les rejeux aussi**, pas seulement pour les références. Un
rejeu non étiqueté est le premier pas vers une référence non étiquetée : les
deux rejeux de la tâche E portent `source=app etape=12 chemin=application`,
et c'est la première fois qu'un dossier de sortie du harnais dit de lui-même
ce qui l'a produit.

**Deux champs, et non un.** La commande demandait la source et l'étape. Le
**chemin de paramètres** a été ajouté, et il se justifie de la même manière :
`application` et `cli` produisent des diffs massifs l'un contre l'autre — la
référence seconde documente le détecteur allumé, 17 025 journées écartées
contre 91 — et rien ne les distinguait davantage que la source de code. Le
mécanisme de refus les traite à égalité.

### B2 — `check_reference.py` refuse, et nomme les deux

Le contrôle a lieu **avant tout rejeu**. Un rejeu de vingt minutes lancé
contre la mauvaise référence coûte vingt minutes **et** une conclusion fausse ;
le refus coûte une lecture de fichier.

```
D70 — tests/reference : source=ref, chemin=application, etablie a l'etape 6.
  REFUS (D70) — comparaison arretee :
    source de code : la reference a ete produite par 'ref', le rejeu demande est 'app'
  Si le desaccord est voulu, le declarer avec --source-differente-assumee.
```

Retour **3**, distinct de 1 (divergence) et de 2 (usage). Les quatre cas
vérifiés :

| Invocation | Verdict | Retour |
|---|---|---|
| `THERMIE_CODE=app` contre `tests/reference` | **REFUS** — source `ref` ≠ `app` | **3** |
| `THERMIE_CODE=ref --chemin cli` contre `tests/reference` | **REFUS** — chemin `application` ≠ `cli` | **3** |
| `THERMIE_CODE=ref` contre `tests/reference` | **concordance**, le rejeu démarre | 0/1 selon le diff |
| référence sans `SOURCE_CODE.txt` | **REFUS** — une référence non étiquetée ne référence rien | **3** |

**Le désaccord n'est pas interdit : il est rendu explicite.** Comparer un
rejeu de `app/` à la référence V4.5 est un usage légitime — c'est la mesure de
l'effet cumulé des correctifs. Ce qui ne l'est pas, c'est de le faire **sans
le savoir** : le diff est alors massif, et rien ne distingue « les correctifs
ont bougé » de « le dépôt est corrompu ». `--source-differente-assumée` laisse
passer, et l'exécution répète le désaccord en tête de sa sortie.

### B3 — Le fichier des deux références existantes, et la vérification demandée

**La commande demandait de ne pas la croire sur parole. Elle avait raison sur
les deux points, et il faut le dire précisément.**

*L'étape.* METHODO.md, section « Étape 6 », §2 : « Le A/B (B2) précède le
rebasage ; le rebasage (B3, B4) précède `check_reference` (B5) […] Les rejeux
de B2 et de B5 sont construits avec **`THERMIE_CODE=ref`** ». B3 reconstruit
`tests/reference/`, B4 reconstruit `tests/reference_cli/`, et B5 vérifie les
deux — **DIFF VIDE des deux côtés**. Les deux références ont donc bien été
établies à **l'étape 6**, depuis **`ref`**. La commande est exacte.

*Ce qu'elle ne disait pas.* Les deux références ne partagent pas leur **chemin
de paramètres**. Il n'a pas été supposé : il a été **lu**, dans les six
`10_parametres.json` de chaque dossier, avec assertion d'unanimité —
`application` pour `tests/reference/`, `cli` pour `tests/reference_cli/`.

```
tests/reference/SOURCE_CODE.txt      SOURCE_CODE=ref  ETAPE=6  CHEMIN=application
tests/reference_cli/SOURCE_CODE.txt  SOURCE_CODE=ref  ETAPE=6  CHEMIN=cli
```

### B4 — Aucune référence n'a été rebasée

`build_reference.py` n'a jamais été invoqué sans `--sortie`. Les deux
`MANIFEST.sha256` et les 132 artefacts sont intacts. Les deux dossiers gagnent
un fichier, et ce fichier est hors du périmètre haché (B1).

### Ce que D70 ne répare pas — voir §0

Le fichier dit que `tests/reference/` a été produite depuis `ref`. Il ne peut
pas dire que **`ref` ne la reproduit plus** : 66 artefacts divergents sur 66,
32 points en échec sur 32. Le mécanisme de refus autorise donc une invocation
qui échouera. C'est signalé, pas corrigé : §6, alternative 2.

`out/etape12/B_reference_non_reproductible.txt`,
`out/etape12/B_rejeu_ref_echecs.txt`.

---

## §3 — La spécification, et l'alternative C4

`docs/SPEC_convention_unique.md`. Ce qui suit en est le résumé ; la
spécification fait foi.

### C1 — Les six séries, à jour

Deux familles, et **deux écarts** les séparent — le coefficient *et* la nature
de l'anomalie.

| Série | Formule | Coefficient | Calcul (état étape 12) |
|---|---|---|---|
| `Tmh_norm` | `Tmh − m × Delta_TMm_liss` | `m` estival | `core.py:579` |
| `Tmax_norm` | `T_eau_max − m × Delta_TMm_liss` | `m` estival | `core.py:580` |
| `Tmh_norm_fraie` | `Tmh − m_s × Delta_TMm_liss` | `m` saisonnier | `core.py:779` |
| `T_moy_comp` | `T_eau_moy − Delta_TMm` | **aucun** | `indicateurs.py:88` |
| `T_max_comp` | `T_eau_max − Delta_TMm` | **aucun** | `indicateurs.py:89` |
| `T_min_comp` | `T_eau_min − Delta_TMm` | **aucun** | `indicateurs.py:90` |

*Les lignes ont bougé de plusieurs centaines depuis l'inventaire de l'étape 4,
qui visait `ref/v4_5/` : `core.py:177` est devenu `579`, `178` → `580`,
`347` → `779`. Une référence `fichier:ligne` sans son instantané ne désigne
rien — c'est la même leçon que D70, à l'échelle d'une ligne.*

La liste complète des consommateurs, avec `fichier:ligne`, est au §1.3 de la
spécification. Le résultat qui gouverne tout le reste :

> **La famille compensation est terminale.** Aucun score, aucun seuil, aucun
> débit de référence, aucune composante du SGVT, aucune phrase de
> `redaction.py` ne la lit. Vérifié exhaustivement sur les trois noms de
> colonnes journalières, les trois libellés publiés et les deux points
> d'entrée `table_mensuelle` / `indicateurs_resume`.
>
> **La famille normalisation, elle, alimente trois des quatre composantes du
> SGVT et les débits de référence.** Le correctif 4 ne la touche pas : sa
> formule *est* la convention.

### C2 — Le vocabulaire : six étiquettes fausses, toutes dans le même sens

`figures.py:91` appelle `Tmh_norm` — coefficient `m`, anomalie lissée — « eau
**COMPENSÉE** ». Le tableau mensuel appelle `T_max_comp` — sans coefficient,
anomalie brute — « Tmax **comp** ». Le même mot, deux formules.

Ce n'est pas isolé. **Le même écran donne deux définitions incompatibles du
mot :**

| | Texte | Ce que c'est |
|---|---|---|
| `app.py:109` | « La **compensation** retranche **m × (anomalie d'air)** » | famille normalisation |
| `app.py:604` | « **Compensé** = ramené aux conditions normales (écart aux normales retiré) » | famille compensation |

Et le livrable Word le porte à deux sous-sections d'écart : `livrables.py:212`
légende la courbe `Tmh_norm` « eau brute puis **compensée** », `livrables.py:220`
la définit huit lignes plus loin comme « la **normalisation** climatique […]
pondérée par le coefficient de sensibilité ».

**Les six fausses** : `figures.py:91`, `figures.py:94`, `figures.py:68-70`
(commentaire), `livrables.py:212`, `exports.py:163`, `app.py:108-109`,
`app.py:569`. Toutes appellent « compensée » une série de la famille
**normalisation** ; **aucune étiquette de la famille compensation n'appelle sa
série « normalisée »**. L'erreur est unidirectionnelle : « compensée » a servi
de synonyme populaire de « normalisée » dans les textes destinés au lecteur,
pendant que le tableau mensuel s'en servait comme **nom technique** pour une
autre formule. Les deux usages ne se sont jamais rencontrés parce qu'ils vivent
dans des onglets différents.

**Deux abus, distincts des six.** `indicateurs.py:85` et `app.py:604` écrivent
que la série compensée est « ramenée aux conditions normales ». Cela n'est
exact que si l'eau suit l'air un pour un. Sur le corpus, le `m` estimé a une
médiane de **0,432** : la « ramenée » corrige **plus du double** de ce que la
réponse mesurée du cours d'eau justifie.

**Le vocabulaire est faux indépendamment de la voie retenue au §5**, puisque
cinq des six étiquettes fausses ne portent pas sur les colonnes en question.

### C3 — Ce que le Word montre

`livrables.py:257` : `cols = [c for c in t.columns][:6]`.

Le tableau mensuel a **onze** colonnes ; le Word en prend **six** :
`Période`, `Tmax (°C)`, `Tmax date`, `Tmin (°C)`, `Tmin date`,
`Ampl. moy (°C)`. Les colonnes compensées sont en **8ᵉ, 9ᵉ et 11ᵉ** position.

**Aujourd'hui le Word ne les porte pas. Après, dans les deux voies, il ne les
portera pas davantage, et son tableau sera identique octet pour octet.**

**Mais le Word change quand même**, par la figure `Fig_Indicateurs_Resume.png`
que `livrables.py:252` insère juste au-dessus et qui, elle, porte les deux
courbes compensées. **C'est un piège de relecture** : contrôler le livrable
Word sur son tableau conclurait « rien n'a bougé » dans les deux voies.

### C4 — L'alternative, chiffrée

`tests/reference/mesure_convention_unique.py`. La chaîne est rejouée telle
quelle, puis le tableau mensuel recalculé une seconde fois en substituant à
`Delta_TMm` la quantité `m × Delta_TMm_liss` — la seule colonne que
`calcul_indicateurs` lit pour bâtir la famille compensation. **`app/` n'est pas
touché** : c'est la méthode de l'étape 6, calculer les deux versions côte à
côte plutôt que corriger puis mesurer.

**Voie A — les colonnes subsistent, recalculées.**

| | |
|---|---|
| cellules publiées comparées | **777** (31 points) |
| **cellules déplacées** | **777 — la totalité** |
| écart médian, valeur absolue | **3,96 °C** |
| **écart maximal** | **−11,68 °C** — `BCH5-7`, février, `Tmax comp` |
| écart > 1 °C | **690 / 777** |
| écart > 3 °C | **485 / 777** |
| points touchés | **31 / 31** |

Aucune valeur ne survit, et la raison n'a pas besoin des données : les deux
formules diffèrent de `(1 − m) × Delta_TMm_liss` plus l'effet du lissage, et
`m` vaut 0,432 en médiane.

**Deux faits que le total ne montre pas.**

*L'écart extrême tombe en février.* `m` est estimé sur juin–septembre
(`core.py:520`) ; le tableau mensuel couvre douze mois, et les anomalies d'air
sont les plus grandes hors saison. **Voie A étend à douze mois un coefficient
estimé sur quatre** — ce que la chaîne s'interdit partout ailleurs :
`analyse_vulnerabilite` restreint sa lecture à juin–septembre, la fraie
ré-estime son propre coefficient sur sa propre fenêtre.

*Sur `BLE3-0`, dont le `m` est rejeté et vaut zéro, voie A rend
`T − 0 × Delta = T`.* Vérifié cellule par cellule : `Tmin comp` devient
identique à `Tmin brut` sur les six lignes, `Tmm30j comp` = `Tmm30j brut`
= 11,48, `Tmax comp` identique sur cinq lignes sur six. **Voie A publierait,
pour ce point, trois colonnes intitulées « compensées » qui sont la copie des
colonnes brutes d'à côté.**

**Voie B — les colonnes disparaissent.**

| | |
|---|---|
| **colonnes supprimées** | **3 sur 11** (positions 8, 9, 11) |
| valeurs publiées supprimées | **777** — les mêmes |
| colonnes restantes | 8 |
| courbes supprimées de la figure | **2** |

**Ce que chacune fait au Word et au classeur.**

| Artefact | Voie A | Voie B |
|---|---|---|
| Word, **tableau** §2.2 | **inchangé** | **inchangé** |
| Word, **figure** §2.2 | 2 courbes se déplacent, jusqu'à 11,68 °C | 2 courbes disparaissent |
| Classeur, `05_Indicateurs` | 777 valeurs changent | passe de 11 à 8 colonnes |
| Écran + export CSV | 777 valeurs changent | 3 colonnes en moins |
| Scores, seuils, débits, SGVT | **aucun effet** | **aucun effet** |
| Les 66 artefacts du harnais | **aucun ne bouge au verdict** | idem |

**Le correctif 4 n'est vérifiable par aucun artefact du harnais.** La famille
compensation ne vit pas dans `res.df`, et les seules lignes qui la portent
(`07_t_norm.csv`) sont exclues du verdict par D13. Sa prédiction falsifiable,
quelle que soit la voie, est donc : **65 artefacts figés sur 66, le 66ᵉ
divergent uniquement hors verdict.** Un mouvement ailleurs signifierait que la
recherche d'exhaustivité est fausse.

### C5 — Ce que la suppression retire

**Trois choses en propre, et une seule réponse à la question posée.**

1. **Douze mois de couverture.** Le tableau mensuel est le seul endroit de
   l'outil où une température corrigée est publiée pour janvier ou novembre.
2. **Un minimum corrigé.** `T_min_comp` est la seule série corrigée bâtie sur
   `T_eau_min` : la famille normalisation ne produit **aucun** minimum.
3. **Une moyenne mobile de 30 jours corrigée**, sans équivalent nulle part.

**La question posée était : un consommateur s'en sert-il pour autre chose que
la duplication ? Non.** Les trois séries sont regardées, jamais utilisées.
Aucun raisonnement de la méthode ne s'appuie sur l'anomalie brute non pondérée.

**Et la voie A ne préserve pas l'information non plus** — elle remplace elle
aussi l'anomalie brute par l'anomalie pondérée. Ce qu'elle conserve est la
**forme** et le **périmètre** (douze mois, un minimum, une moyenne mobile),
pas la formule. **La seule chose que B retire et que A garde est le
périmètre.**

**Une réserve qu'il faut nommer.** L'anomalie brute retranchée sans
coefficient a une lecture défendable : c'est la **borne haute** de la
correction climatique. Mais elle n'est publiée à côté de rien, et deux textes
de l'outil la présentent au contraire comme une estimation
(`indicateurs.py:85`, `app.py:604`). **Une borne présentée comme une
estimation n'est pas une information ; c'est une erreur de lecture
organisée.** C'est ce qui empêche de porter cette lecture au crédit de la
voie B.

### C6 — Les fichiers touchés, en typologie D63

Détail complet au §6 de la spécification. Deux points qui méritent d'être ici.

**`config.py` n'a besoin de rien**, et il vaut mieux le dire que d'y ajouter
un paramètre inutile : aucune des deux voies n'introduit de réglage.

**La voie A crée un couplage que la voie B retire.**
`calcul_indicateurs(df, sub, verbose)` ne reçoit pas `m` — la famille
compensation était précisément celle qui n'en avait pas besoin. Voie A fait
entrer le coefficient de sensibilité dans le module des indicateurs, donc fait
dépendre le tableau mensuel de la réussite de `analyse_sensibilite`. Ce n'est
pas décisif, mais c'est nouveau, et cela se déclare.

---

## §4 — D67 : le statut `replie`

### La prédiction, écrite avant la pose

Lue dans `out/etape12/E_d67_m_saisonnier.csv`, produit **avant** toute
modification de `app/` : sur les 32 coefficients saisonniers du corpus,
**29 `saisonnier`, 2 `estival_repli`, 1 `rejet_validite`**.

> **Prédiction.** Exactement **deux lignes** de `06_coefficients.csv`
> changeront — `BLE3-0` [ombre commun], n = 7, et `GRO9-1` [ombre commun],
> n = 14, toutes deux dans `jeu_bienne`. Deux colonnes se rempliront,
> `validite_statut` et `validite_critere_rejetant`. **Aucune autre valeur ne
> bougera, sur aucun des 66 artefacts**, `99_log.txt` compris.

### La pose

**Le statut est produit par l'application, pas déduit par le harnais.** Le
harnais pouvait le déduire du champ `source == "estival_repli"` que
`_m_saisonnier` retourne déjà, et composer le motif à partir de `n` et du
seuil lu à `core.py:657`. C'aurait été **une compensation du harnais** — le
défaut relevé à l'étape 7, où le harnais déduisait par soustraction
d'ensembles une perte que l'application ne traçait pas. Le seuil de vingt
jours appartient à l'application ; le motif qui le cite aussi.

- `app/thermie_debits/core.py` — la branche de repli pose `statut="replie"` et
  le motif. `m_estival` est retourné à l'identique ; **le `print` du journal
  n'est pas touché**, sans quoi `99_log.txt` bougerait et l'étape a déclaré
  `06_coefficients.csv` seul.
- `tests/reference/build_reference.py` — `_statut_validite` donne à la colonne
  une **troisième** valeur. Le vide subsiste et garde un sens précis : la
  grandeur n'est pas un coefficient de couplage (ligne `normales`).

### Le constat

`comparer_rejeux.py`, rejeu d'avant contre rejeu d'après, à corpus et
paramètres identiques.

```
  artefacts compares : 66
  figes              : 65
  qui bougent        : 1

    00_format_detecte.json       FIGE      05_anomalies.csv    FIGE
    01_colonnes_retenues.json    FIGE      06_coefficients.csv 1/6 bougent
    02_effectifs.csv             FIGE      07_t_norm.csv       FIGE
    03_journees_ecartees.csv     FIGE      08_scores.csv       FIGE
    04_normales.csv              FIGE      10_parametres.json  FIGE
                                           99_log.txt          FIGE

  jeu_bienne/06_coefficients.csv : -0 / +0 ligne(s), 4 valeur(s)
      [validite_statut validite_critere_rejetant]
```

**Les quatre valeurs, sur les 78 lignes du fichier :**

| Point | `validite_statut` | `validite_critere_rejetant` | `m` publié |
|---|---|---|---|
| `BLE3-0` [ombre commun] | `''` → **`replie`** | `''` → « effectif insuffisant sur la fenetre (n=7 < 20) — repli sur m_estival » | 0,000000 → **0,000000** |
| `GRO9-1` [ombre commun] | `''` → **`replie`** | `''` → « … (n=14 < 20) … » | 0,240294 → **0,240294** |

**La prédiction est vérifiée sur tous ses nombres** : deux lignes, les deux
points nommés, les deux effectifs, deux colonnes, zéro ligne ajoutée ou
retirée, `m` inchangé, 65 artefacts figés au bit près. C'est une colonne qui
se remplit, exactement comme annoncé.

### Ce que le vide laissait croire

La colonne portait `valide` ou `REJETE` pour tous les coefficients que la
règle du correctif 6 a jugés, et **rien** pour ceux-ci. Un lecteur qui voit une
colonne de statut vide conclut « rien à signaler ». Or il y a quelque chose à
signaler : **le coefficient publié pour la fenêtre de reproduction de l'ombre
commun n'est pas celui de cette fenêtre, c'est celui de l'été.** C'est la
substitution silencieuse que le correctif 6 a retirée dans l'autre branche —
celle du R² — et qui subsiste ici légitimement : sept jours ne permettent pas
d'estimer une incertitude, donc pas d'appliquer la règle de validité.

**`BLE3-0` mérite d'être lu deux fois.** Son coefficient saisonnier se replie
sur son coefficient estival, lequel a été **rejeté** et vaut zéro. Le point
publiait donc un coefficient saisonnier de zéro sans qu'aucune colonne ne dise
pourquoi : ni « rejeté » — il ne l'a pas été —, ni « replié » — la colonne
était vide. **Deux mécanismes différents produisaient le même zéro muet.** Ils
se distinguent désormais.

`docs/VERDICTS_MODIFIES.md`, section D67 : aucun verdict publié ne change.

---

## §5 — Le correctif 4 : pourquoi la tâche D n'a PAS eu lieu

La tâche D était conditionnelle : poser dans la même étape **si et seulement
si** l'instruction faisait apparaître qu'une seule voie est défendable, parce
que l'autre casserait un consommateur, ou parce que les colonnes ne sont lues
nulle part.

**Les deux conditions sont fausses, et la mesure le montre.**

*« L'autre voie casserait un consommateur. »* Faux dans les deux sens. §1.3 de
la spécification établit qu'aucun score, seuil, débit ou composante du SGVT ne
lit la famille compensation. **Les deux voies laissent tous les verdicts
publiés intacts.** Aucune ne casse rien.

*« Les colonnes ne sont lues nulle part. »* Faux. Elles ne sont pas dans le
tableau du Word — et c'était le fait qui pouvait le laisser croire, relevé dès
l'étape 4 — mais elles sont dans **la figure du Word**, dans **le classeur**,
sur **l'écran** et dans **l'export CSV**. Trois livrables sur quatre les
portent. La suppression serait visible.

**Ce qui reste, une fois les deux conditions écartées, est un jugement sur la
forme d'un livrable publié.** Les deux voies changent le même nombre de
valeurs — 777 —, ne touchent aucun verdict, et ont chacune un argument que la
mesure appuie sans le trancher :

- pour **A**, le `Tmin` corrigé et la moyenne mobile de trente jours n'ont
  aucun équivalent ailleurs ; le livrable garde une forme empilable entre
  stations, ce que la feuille `06_SYNTHESE` érige en principe ;
- pour **B**, la voie A étendrait à douze mois un coefficient estimé sur
  quatre, et publierait des colonnes « compensées » identiques aux colonnes
  brutes sur tout point dont le coefficient est rejeté.

**Je n'arbitre pas.** La spécification est livrée, l'alternative est chiffrée
au §6, et l'étape s'arrête là — comme la commande le demandait.

*Une note sur l'inventaire d'étape 4.* Sa tâche E écrivait « Famille
compensation — **supprimée par D18** ». D18 fixe la convention unique ; elle ne
dit pas ce qu'il advient des colonnes. L'étape 4 avait donc **présumé la voie
B** sans l'instruire, et l'a écrit comme un fait. La question rouverte ici
était bien ouverte ; elle avait été refermée par inadvertance.

---

## §6 — Alternatives fermées

### Alternative 1 — La famille compensation : subsister recalculée, ou disparaître ?

| Branche | **A — les colonnes subsistent** | **B — les colonnes disparaissent** |
|---|---|---|
| valeurs publiées touchées | **777 sur 777** déplacées | **777** supprimées |
| écart médian / maximal | 3,96 °C / **11,68 °C** | sans objet |
| colonnes du tableau mensuel | 11 → **11** | 11 → **8** |
| Word, tableau §2.2 | **inchangé** | **inchangé** |
| Word, figure §2.2 | 2 courbes se déplacent | 2 courbes disparaissent |
| classeur `05_Indicateurs` | 777 valeurs changent | 3 colonnes en moins |
| écran + export CSV | 777 valeurs changent | 3 colonnes en moins |
| scores, seuils, débits, SGVT | **aucun effet** | **aucun effet** |
| couverture de janvier et novembre | conservée | **perdue** |
| minimum corrigé, Tmm30j corrigé | conservés, à la convention unique | **perdus** |
| coefficient estival appliqué hors saison | **oui, douze mois** — la chaîne s'en abstient partout ailleurs | non |
| points dont `m` est rejeté | colonnes « compensées » = **copie des colonnes brutes** (1 point sur 31 aujourd'hui) | sans objet |
| couplage nouveau | `calcul_indicateurs` doit recevoir `m` | aucun |
| le mot « compensée » | doit être remplacé — il ne décrit plus la formule | disparaît avec les colonnes |

**Ce qui les départage.** Si le tableau mensuel doit rester un **descripteur
annuel complet** — un maximum, un minimum et une moyenne mobile corrigés,
douze mois durant —, c'est A, et il faut assumer d'appliquer hors saison un
coefficient estimé en saison. Si le tableau mensuel doit ne publier que ce
que la méthode sait établir sur la fenêtre où elle l'a établi, c'est B, et il
faut assumer que le classeur et l'écran changent de forme.

**Je n'arbitre pas** : la forme d'un livrable publié appartient au
commanditaire. La mesure est complète des deux côtés.

### Alternative 2 — `parametres.py` décrit quel `QCConfig` ?

`tests/reference/parametres.py` décrit aujourd'hui le `QCConfig` de `app/`.
Conséquence mesurée : `THERMIE_CODE=ref` échoue sur **32 points sur 32**, et
`tests/reference/` — la référence qui fait foi, construite depuis `ref/v4_5/`
— **ne peut plus être reproduite depuis sa propre source**, et ce depuis
l'étape 10.

| Branche | **A — deux tables de paramètres** | **B — la référence est rebasée sur `app/`** | **C — le refus D70 devient un refus dur** |
|---|---|---|---|
| ce qu'il faut écrire | `parametres.py` porte un jeu par source de code | rien à écrire ; une pose de clôture | trois lignes dans `check_reference` |
| `THERMIE_CODE=ref` | **redevient exécutable**, la référence redevient reproductible | reste inexécutable | reste inexécutable, mais **refusé au lieu d'échouer** |
| point de comparaison avec V4.5 | **conservé** | **détruit** — c'est ce que B4 interdit en milieu de chantier | conservé, mais inutilisable |
| coût | une table de plus à tenir à jour à chaque correctif | nul | quasi nul |
| ce que ça masque | rien | l'écart cumulé des huit correctifs | le fait que la référence n'est plus reproductible |

**Ce qui les départage.** Si la reproductibilité de la référence est un
contrôle qu'on veut conserver, c'est A — et le coût est réel, une table à
maintenir. Si `tests/reference/` n'est plus qu'une archive documentaire, c'est
C, qui rend l'impossibilité lisible sans prétendre la lever. **B est exclue en
l'état** : B4 interdit de rebaser en milieu de chantier, et rebaser détruirait
le seul point de comparaison stable avec V4.5.

*Je ne tranche pas, mais je signale que C sans A laisse le chantier sans
aucun moyen de vérifier que `ref/v4_5/` produit encore ce que la référence
dit qu'il produit.*

### Alternative 3 — Le vocabulaire, quand le réparer ?

Six étiquettes sont fausses (§3, C2), et cinq d'entre elles ne portent pas sur
les colonnes de l'alternative 1 : elles portent sur la famille normalisation,
qu'aucune voie ne touche.

| Branche | **A — réparer maintenant** | **B — réparer avec le correctif 4** |
|---|---|---|
| ce qui bouge | des chaînes de caractères dans 5 fichiers | idem, plus les colonnes |
| artefacts du harnais | **aucun** — aucune étiquette n'entre dans un artefact | idem |
| risque | une pose de plus dans une étape déjà chargée | le faux vocabulaire reste publié jusqu'à l'arbitrage de C4 |
| lisibilité de la mesure | le vocabulaire se mesure seul | les deux effets se mélangent |

**Ce qui les départage** : la leçon de l'étape 10 — quand deux changements
touchent les mêmes livrables, les séparer est la condition pour que la mesure
veuille dire quelque chose. Ici les deux changements **ne touchent pas** les
mêmes objets (des chaînes d'un côté, des colonnes de l'autre), ce qui
affaiblit l'argument de séparation. Mais rien n'oblige à attendre : le
vocabulaire est faux quelle que soit la voie retenue, et sa réparation ne
dépend d'aucun arbitrage.

*Je n'ai rien posé, parce que la commande interdisait toute modification
applicative avant l'arbitrage de C4 et que je préfère ne pas interpréter cette
interdiction à mon avantage.*

### Alternative 4 — Le manifeste de `tests/reference_cli/`

Constat au §0 : 6 artefacts hors manifeste, 12 empreintes divergentes, depuis
l'étape 6, parce que `build_reference.main` ne remanifeste que
`tests/reference`.

| Branche | **A — remanifester `reference_cli`** | **B — retirer la condition dans le code** | **C — ne rien faire, et le dire** |
|---|---|---|---|
| ce qu'il faut écrire | un appel à `ecrire_manifeste(base)` sur ce dossier | `sortie == ICI` devient « toute sortie déclarée comme référence » | rien |
| le manifeste décrit son dossier | **oui, une fois** | **oui, à chaque reconstruction** | non |
| risque | fige les empreintes actuelles sans les avoir vérifiées contre un rejeu | un rejeu jetable pourrait écrire un manifeste là où on n'en veut pas | le contrôle reste faux et on le sait |
| compatible avec B4 | discutable — écrire un manifeste n'est pas rebaser, mais c'est y toucher | oui, tant qu'aucun dossier n'est reconstruit | oui |

**Ce qui les départage.** A répare le symptôme et laisse la cause ; B répare la
cause et demande de définir ce qu'est « une référence » pour le harnais ; C est
tenable uniquement parce que `tests/reference_cli/` n'a plus servi de témoin
depuis l'étape 5, où elle avait déjà été déclarée inutilisable en l'état.

*Je penche pour B, et je ne l'ai pas posée : c'est une modification du harnais
en dehors du mandat de l'étape, et la définir demande de trancher ce qui, dans
une sortie de `build_reference`, mérite un manifeste.*

---

## §7 — Ce qui reste

**Correctif 4** — la spécification est écrite, l'alternative 1 attend son
arbitrage. **Correctif 7** (défauts littéraux, D22) — et il gagne une entrée :
le seuil de vingt jours de `core.py:657` est désormais cité par le motif de
D67, donc écrit deux fois. **Correctif 10** (`io_data.py:98`, D60,
programmé étape 13). **L'affichage** de toute la dégradation déclarée (D48,
étape 14). **L'alternative 2 du §6** — la reproductibilité de la référence.
**L'alternative 4 du §6** — le manifeste de la référence seconde.
