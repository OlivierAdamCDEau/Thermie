# THERMIE_BIO V4.6 — Rapport d'étape 5

*Correctif 3 : marquer plutôt que supprimer. Première modification applicative.*

---

## Artefacts figés pour ce correctif (D34)

**Les 66 artefacts de `tests/reference/` sont figés, sans exception.**

| Artefact | Statut pour le correctif 3 | Pourquoi |
|---|---|---|
| `00_format_detecte.json` | **figé** | la lecture n'est pas touchée |
| `01_colonnes_retenues.json` | **figé** | idem |
| `02_effectifs.csv` | **figé** | l'adaptateur rend la même vue filtrée : mêmes effectifs |
| `03_journees_ecartees.csv` | **peut gagner des motifs** — seule exception autorisée | une journée écartée par deux détecteurs porte désormais les deux |
| `04_normales.csv` | **figé** | en amont du contrôle qualité |
| `05_anomalies.csv` | **figé** | *(le correctif 2 le fera bouger ; ce sera attendu alors, pas ici)* |
| `06_coefficients.csv` | **figé** | `m` dépend des journées retenues, qui ne changent pas |
| `07_t_norm.csv` | **figé** | idem |
| `08_scores.csv` | **figé** | témoin hors périmètre |
| `10_parametres.json` | **figé** | `config.py` n'est pas modifié |
| `99_log.txt` | **figé** | la sortie console est reproduite au caractère près |

**Résultat obtenu : 65 des 66 artefacts identiques au bit près.** Le seul qui
bouge est `jeu_bienne/99_log.txt`, et il ne bouge pas pour une raison de
comportement. §2.

`03_journees_ecartees.csv` **n'a pas bougé non plus** — et c'est un résultat,
pas un manquement : aucune journée du corpus n'est écartée par plus d'un
détecteur. §3.

---

## §0 — Carnet de bord

### Le harnais devait apprendre à exécuter `app/`

D3 attache la **référence** au code figé de `ref/v4_5/`, et cela ne change pas :
les 66 artefacts en viennent. Mais un harnais de non-régression doit pouvoir
**rejouer** le corpus avec le code modifié pour le comparer à cette référence.
J'ai ajouté une variable d'environnement `THERMIE_CODE` — `ref` par défaut,
`app` pour vérifier —, et chaque exécution annonce désormais quel code elle
exécute et à quelle référence elle se compare. Rien d'implicite.

### Un artefact bouge, et je ne l'ai pas rebasé

`jeu_bienne/99_log.txt` diffère de deux lignes. Elles disent ceci :

```
-  File "<RACINE>\ref\v4_5\thermie_debits\orchestrator.py", line 166, in run
+  File "<RACINE>\app\thermie_debits\orchestrator.py", line 166, in run
-  File "<RACINE>\ref\v4_5\thermie_debits\core.py", line 137, in analyse_sensibilite
+  File "<RACINE>\app\thermie_debits\core.py", line 137, in analyse_sensibilite
```

Numéros de ligne identiques, message identique, comportement identique. Ce qui
change est **l'endroit du disque où le code se trouve**, inscrit dans une trace
figée par D7.

Je pense que le harnais a tort d'enregistrer cela — c'est la même faute que
celle corrigée à l'étape 1 pour ses propres numéros de ligne, et le remède
serait de neutraliser la racine du code comme on neutralise `<RACINE>`. **Je
ne l'ai pas fait, et je n'ai pas reconstruit la référence.** La consigne est
explicite et elle a raison : à ce stade, tout artefact qui bouge se remonte, il
ne s'absorbe pas. La décision est au §5, en alternative fermée.

Pour ne pas laisser la question en suspens, j'ai construit un **diagnostic A/B**
qui ne touche à rien : deux rejeux complets, l'un avec `ref/v4_5/`, l'autre avec
`app/`, comparés **entre eux** après neutralisation de la seule chose qui les
sépare par construction. Il répond à la question qui compte — « quelque chose
d'autre a-t-il bougé ? » — sans modifier un octet de `tests/reference/`.

### `tests/reference_cli/` ne pouvait pas servir de témoin tel quel

B3 demandait de vérifier aussi le régime CLI contre `tests/reference_cli/`. Je
l'ai fait, et le résultat est ininterprétable : 18 artefacts divergents, dont
six `10_parametres.json` **absents de la référence**.

La raison n'a rien à voir avec le correctif. `tests/reference_cli/` a été figé
à l'étape 2, **avant** que le harnais ne gagne `10_parametres.json` et la
colonne `sortie_v45`. Le comparer aujourd'hui mélange un changement de code et
un changement de schéma du harnais — exactement le genre de confusion qu'une
référence est censée empêcher. Je le signale plutôt que de le présenter comme
une régression, et le diagnostic A/B fournit le témoin valide que B3 cherchait :
deux constructions faites à l'instant, avec le même harnais, sur le régime CLI.

### Une mesure d'étape 4 était fausse, et R10 l'a révélée

`conjonction_rampl_profils.csv` annonçait une longueur d'épisode médiane de
**4,0 jours** pour la marche 2. La valeur correcte est **1,5**. La cause est
identifiée : je calculais les épisodes sur le masque du **socle**, puis je
lisais cette longueur pour les lignes retenues par chaque règle. Le chiffre
publié était donc la longueur de l'épisode du socle *contenant* le jour, pas
celle de l'épisode de la règle. Corrigé et recalculé au §4.

### Ce que j'ai corrigé d'autre dans mon propre code

`mesure_recouvrement_qc.py` lisait `par["qc"][champ]["valeur"]` alors que
`jeu_de_parametres` rend des triplets `(valeur, provenance, justification)` —
la forme en dictionnaire n'existe que dans `10_parametres.json`.

---

## §1 — Le correctif et l'adaptateur

### A1 — Ce qui est modifié

**Un seul fichier : `app/thermie_debits/qc.py`** (138 lignes ajoutées, 20
retirées). Les noms de modules sont conservés (contrainte 2).

**`config.py` n'a besoin de rien**, et je préfère le dire que d'y ajouter du
paramètre inutile : le correctif 3 ne fait entrer aucun réglage. Les trois
statuts sont des constantes de `qc.py`, et `QCConfig.to_legacy_dict()` continue
d'alimenter les mêmes détecteurs. `config.py` bougera au correctif 1, qui
apporte `k`, le plancher de dispersion et les autres.

**La structure produite** — `qc.marquer_qualite()` — porte, pour chaque journée
lue et non plus seulement pour les rescapées :

| Colonne | Contenu |
|---|---|
| `statut` | `retenu` \| `ecarte` \| `non_diagnosticable` |
| `motifs` | la **liste** de tous les motifs applicables |
| `motif` | ces motifs joints par ` + `, pour l'affichage |

**Le défaut de `qc.py:32-36` disparaît.** L'ancien `_marque` n'écrivait le
motif que là où le drapeau n'était pas encore posé : la contribution du second
détecteur était perdue. Le nouveau **ajoute** le motif à la liste de chaque
journée concernée, y compris déjà marquée.

Un détail qui n'en est pas un : `_marque` continue de retourner le nombre de
journées **nouvellement** écartées, et non le total du détecteur. C'est ce
décompte-là que le journal affiche depuis toujours ; le changer aurait fait
bouger `99_log.txt` sur les 32 points. Le comportement du journal est donc
inchangé alors que celui du motif change.

### A2 — L'adaptateur, et qui le consomme

`controle_qualite(daily_eau, df_air, qc, verbose)` conserve **exactement** sa
signature et son retour `(daily_propre, rapport)`. Elle est devenue une vue :

```python
def controle_qualite(daily_eau, df_air, qc, verbose=True):
    marques = marquer_qualite(daily_eau, df_air, qc, verbose=verbose)
    return vue_retenue(marques), rapport_ecartes(marques)
```

`vue_retenue()` rend les journées `retenu`, sans colonne de travail, index
réinitialisé — mêmes colonnes, même ordre, mêmes types qu'avant, `RR` compris.
`rapport_ecartes()` rend les mêmes cinq colonnes qu'avant ; seul le **contenu**
de `motif` s'enrichit.

**Un seul appelant** de `controle_qualite`, et il n'est pas touché :

| Appelant | Ligne | Ce qu'il reçoit |
|---|---|---|
| `orchestrator.run` | `app/thermie_debits/orchestrator.py:155-157` | `propre` puis `res.rapport_qc = rapport` |

**Les consommateurs indirects de `rapport_qc`**, tous inchangés et tous hors
périmètre :

| Consommateur | Ligne | Usage |
|---|---|---|
| `exports.exporter_rapport_qc` | `orchestrator.py:275` → `exports.py:51-57` | CSV `rapport_qualite.csv` (mode CLI seulement) |
| `figures.fig_qc` | `orchestrator.py:185` → `figures.py:653-675` | figure du contrôle qualité |
| `redaction.synthese_qc` | `redaction.py:68-78` | familles de motifs de la fiche |
| `redaction` (couverture) | `redaction.py:505-507` | part écartée |
| `livrables` (XLSX) | `livrables.py:472-476` | détail des enregistrements écartés |
| `app.py` (Streamlit) | `app.py:444-450` | onglet « contrôle qualité » |

Aucun ne sait que le marquage existe. Le volet bio, le volet débit et les
figures ne sont pas touchés.

*Une conséquence à signaler, qui ne se voit pas sur ce corpus : `redaction.py:76`
extrait la famille d'un motif par `^([^—(]+)`. Sur une journée à deux motifs, il
lira désormais la chaîne jointe. Aucune journée du corpus n'est dans ce cas
(§3), donc rien ne change ici — mais un autre jeu le ferait apparaître.*

### A3 — Le statut `non_diagnosticable` est créé vide, et le reste

**Aucun détecteur de V4.5 ne s'abstient.** Les quatre — bornes physiques,
plateau, hors d'eau, MAD — tranchent sur toute journée qu'ils examinent : ils
la marquent ou la laissent passer, jamais ne renoncent. Le statut n'a donc
**aucun producteur aujourd'hui**, et la mesure le confirme : **0
non_diagnosticable** sur les 68 134 journées lues, dans les deux régimes.

Il existe pour que le correctif 1 ait où déposer ses abstentions — dispersion
nulle du couple (point, mois), mois de moins de dix jours, amplitude d'air
insuffisante pour la marche 2 — et pour que son absence actuelle soit
**vérifiable** plutôt que supposée. La fonction `non_diagnosticables(marques)`
existe et rend un DataFrame vide.

---

## §2 — Preuve de non-régression

### B1 — Le contrôle contre la référence qui fait foi

`out/etape5/determinisme.txt`, sortie intégrale, code de retour inclus.

```
Code rejoue : app  (app)
Reference comparee : tests/reference (construite depuis ref/v4_5, D3)
66 artefact(s) compare(s).
1 artefact(s) divergent(s) :
  ### jeu_bienne/99_log.txt — CONTENU DIFFERENT (2 ligne(s) retiree(s), 2 ajoutee(s))
code de retour : 1
```

**65 des 66 artefacts sont identiques au bit près.** `03_journees_ecartees.csv`
en fait partie — il n'a pas gagné de motif, faute de journée multi-motifs (§3).

### B2 — L'artefact qui bouge, chiffré, et sa ligne responsable

| | |
|---|---|
| Artefact | `tests/reference/jeu_bienne/99_log.txt` |
| Écart | **2 lignes retirées, 2 ajoutées**, sur 340 |
| Contenu | `<RACINE>\ref\v4_5\…` devient `<RACINE>\app\…`, deux fois |
| Numéros de ligne | **identiques** — `orchestrator.py:166`, `core.py:137` |
| Message d'erreur | **identique** au caractère près |
| Ligne responsable | `tests/reference/build_reference.py`, fonction `_nettoyer` : elle masque `<RACINE>` et le numéro de ligne du harnais, mais **pas la racine du code** |
| Nature | **aucun changement de comportement** — le harnais enregistre l'emplacement disque du code exécuté |

**Je ne corrige pas la référence.** La décision est au §5, alternative 1.

### B2 bis — Le diagnostic A/B, qui répond sans rien toucher

Deux rejeux complets par régime, construits à l'instant avec le **même**
harnais, comparés entre eux après neutralisation de la racine du code.
`out/etape5/diff_ref_app.txt`.

| Régime | artefacts | identiques au bit près | ne diffèrent que par le chemin | **divergents après neutralisation** |
|---|---|---|---|---|
| application | 66 | 65 | 1 | **0** |
| **CLI** (17 025 journées écartées) | 66 | 63 | 3 | **0** |

> **Aucune divergence de comportement, sur aucun des deux régimes.** La seule
> différence entre `ref/v4_5` et `app` est le chemin du code inscrit dans les
> traces.

### B3 — Le régime CLI, et pourquoi `tests/reference_cli/` n'a pas pu servir

Le contrôle demandé a bien été lancé. Son résultat est ininterprétable, et la
cause n'est pas le correctif :

| Divergence | Cause |
|---|---|
| `10_parametres.json` — **absent de la référence**, sur les 6 jeux | cet artefact a été créé à l'étape 2 ; `reference_cli` a été figé avant |
| `07_t_norm.csv` — 166 602 lignes retirées, 72 450 ajoutées sur `jeu_bienne` | la colonne `sortie_v45` (C4 de l'étape 2) et la famille *compensation* n'existaient pas dans ce schéma |
| `99_log.txt` — 36 lignes retirées, 141 ajoutées sur `jeu_bienne` | 14 points échouaient à l'étape 1 dans ce régime ; le journal a changé de forme depuis |

**`tests/reference_cli/` est une référence d'un harnais antérieur.** La comparer
au harnais d'aujourd'hui mélange un changement de code et un changement de
schéma. Le témoin valide est le A/B ci-dessus : **0 divergence** sur le régime
CLI, celui qui écarte 17 025 journées et sollicite le plus le marquage.

*Ce que cela ouvre : soit `reference_cli` est reconstruit une fois avec le
harnais courant pour redevenir comparable, soit il est déclaré archive
documentaire et cesse d'être un témoin. §5, alternative 2.*

---

## §3 — Ce que le marquage révèle

La question était impossible hier : une journée écartée deux fois ne gardait
qu'un motif. Elle a maintenant une réponse.

**Sur 68 134 journées lues, 32 points, et dans les deux régimes : ZÉRO journée
n'est écartée par plus d'un détecteur.**

| Régime | journées lues | écartées | **à plusieurs motifs** | non diagnosticables |
|---|---|---|---|---|
| application | 68 134 | 106 | **0** (0,00 %) | 0 |
| CLI | 68 134 | 17 109 | **0** (0,00 %) | 0 |

Les détecteurs sont **parfaitement disjoints** sur ce corpus :

| Régime | bornes physiques | plateau / sonde bloquée | sonde hors d'eau | croisements |
|---|---|---|---|---|
| application | 42 (39,6 %) | 42 (39,6 %) | 22 (20,8 %) | **aucun** |
| CLI | 42 (0,25 %) | 42 (0,25 %) | 17 025 (99,5 %) | **aucun** |

*Les outliers MAD ne tirent jamais : à `k = 50 × MAD`, le seuil est hors de
portée de toute chronique du corpus.*

**Ce que cela dit du défaut corrigé.** Le défaut de `qc.py:32-36` est **réel
dans le code** — deux détecteurs qui marquent la même journée en perdent un
motif — et **jamais exercé sur ce corpus**. Le correctif est donc une
correction de robustesse, pas de résultat, et c'est exactement pourquoi
`03_journees_ecartees.csv` n'a pas bougé. Deux constats indépendants qui
disent la même chose : le diff vide de l'artefact, et cette mesure.

Le cas où les détecteurs se recouvriraient existe pourtant sans peine — une
journée à 48 °C en pleine série bloquée cocherait bornes et plateau. Ce corpus
n'en porte pas.

---

## §4 — R10 et R11 instruits

### R10 (a) — Avec ou sans le filtre d'épisode ?

**Sans.** La table d'impact du §5 de la spécification vient de
`mesure_regime_service.py`, qui applique un masque **journalier**
(`masque_candidat`) et ne contient nulle part de `min_jours_episode`. Elle
chiffre le détecteur avant tout regroupement.

### R10 (b) — La longueur d'épisode de 4,0 jours était fausse

| Règle | jours | épisodes | longueur médiane **corrigée** | annoncée à l'étape 4 |
|---|---|---|---|---|
| marche 1 — socle relatif | 40 | 25 | **2,0** | 2,0 *(juste par coïncidence)* |
| marche 2 — `R_ampl ET E_max` | 4 | 3 | **1,5** | **4,0 — faux** |

**Cause.** `mesure_conjonction_rampl.py` calculait les épisodes sur le masque
du **socle**, puis lisait cette longueur pour les lignes de chaque règle. Pour
la marche 1 le masque est le socle, d'où la coïncidence ; pour la marche 2, le
chiffre publié était la longueur de l'épisode du socle *contenant* le jour.

Les quatre jours forment bien des épisodes de **2, 1 et 1** — les deux jours
consécutifs de `LA PLAINE` en juin 2011, puis les deux jours isolés de
`BIE40-3` en juillet et septembre 2015. Médiane pondérée par jour : 1,5.

### R10 — Ce que `min_jours_episode` exclut réellement

| Valeur | marche 1 : épisodes / jours / points | marche 2 : épisodes / jours / points |
|---|---|---|
| **1** | 25/25 · 40/40 (0 % exclus) · **16/16 points** | 3/3 · 4/4 (0 %) · **2/2 points** |
| **2** | 6/25 · 21/40 (**47,5 %**) · **2/16 points** | 1/3 · 2/4 (**50 %**) · **1/2 point** |
| **3** | 4/25 · 17/40 (**57,5 %**) · **2/16 points** | 0/3 · **0/4 (100 %)** · **0/2 point** |
| 4 | 2/25 · 11/40 (72,5 %) · 1/16 point | 0/3 · 0/4 (100 %) · 0/2 point |
| 5 | 2/25 · 11/40 (72,5 %) · 1/16 point | 0/3 · 0/4 (100 %) · 0/2 point |

**R10 est confirmée et aggravée.** À 3, la marche 2 n'exclut pas « rien » : elle
**annule tout**. Et la marche 1 y perd 14 de ses 16 points.

**Valeur proposée, fondée sur ce qu'elle exclut : `min_jours_episode = 1`**,
c'est-à-dire **aucune exclusion par la longueur**, la longueur d'épisode étant
conservée comme **attribut diagnostique** de chaque journée marquée plutôt que
comme filtre.

La justification est la mesure elle-même. Toute valeur ≥ 2 retire au moins la
moitié des journées marquées et, à 3, rend la marche 2 **inerte** — donc
indistinguable d'une marche absente, ce que le principe de dégradation déclarée
de la spécification interdit précisément. Le filtre d'épisode de
`thermie_points` était calibré sur un détecteur qui marque des milliers de
jours ; celui-ci est délibérément rare, et un filtre de rareté appliqué à un
détecteur rare ne filtre pas, il éteint.

### R11 — `n_min` dérivé séparément, par coefficient et par espèce

Même procédure qu'à l'étape 4 — fenêtres contiguës, niveau 95 % — mais chacune
sur **sa propre fenêtre** au lieu d'un transfert depuis l'estival.

| Coefficient | Espèce | fenêtre | points supports | **`n_min` dérivé** | écart au 60 transféré | écarterait |
|---|---|---|---|---|---|---|
| `m_estival` | — | juin-sept. | **30** | **60** | +0 | 1 / 32 |
| `m_saisonnier` | ombre commun | 3-4-5 | **21** | **40** | −20 | 5 / 27 *(contre 6 avec 60)* |
| `m_saisonnier` | truite fario | 1-2-3-10-11-12 | 2 | **10** | −50 | 0 / 3 |
| `m_saisonnier` | brochet | 2-3-4 | 1 | **25** | −35 | 0 / 1 |
| `m_saisonnier` | brème | 4-5-6-7 | 1 | **75** | +15 | 0 / 1 |
| `m_saisonnier` | barbeau | 4-5-6-7 | 1 | **75** | +15 | 0 / 1 |

**Trois enseignements.**

Le transfert était **juste pour l'estival** — la dérivation redonne exactement
60 — et **faux pour le saisonnier** : trop strict pour l'ombre commun (40) et la
truite fario (10), trop permissif pour la brème et le barbeau (75).

L'effet pratique reste modeste : sur l'ombre commun, seule espèce à disposer
d'un vrai support, passer de 60 à 40 fait rentrer **une** estimation sur 27.

**Trois espèces sur cinq reposent sur un seul point support.** Leur `n_min` est
un nombre, pas une dérivation : avec un seul point, la procédure ne mesure plus
la puissance du test sur un type de données, elle décrit une chronique. Cela
doit être dit, et c'est une alternative fermée du §5.

---

## §5 — Décisions manquantes, en alternatives fermées

### Alternative 1 — La racine du code dans les traces figées

| Branche | **neutraliser** la racine dans `_nettoyer` | **laisser** et accepter un artefact divergent |
|---|---|---|
| ce qu'il faut faire | une ligne dans `build_reference._nettoyer`, puis **une reconstruction de la référence** avec `THERMIE_CODE=ref` | rien, mais `check_reference` renverra 1 à chaque correctif |
| ce que la référence enregistre | ce que le code **fait** | ce qu'il fait **et où il est rangé** |
| risque | une reconstruction, à faire pendant qu'aucune valeur ne bouge — c'est le cas maintenant | un verdict rouge permanent, qui finit par ne plus être lu |
| précédent | c'est le remède déjà appliqué à l'étape 1 aux numéros de ligne du harnais, et accepté | — |

**Ce qui les départage :** une référence doit dépendre du comportement, pas de
l'arborescence. Mais neutraliser exige de reconstruire, et reconstruire est
précisément ce que la consigne interdit sans accord. Le moment est favorable —
le diagnostic A/B établit que rien d'autre ne bouge —, il ne le sera plus au
correctif 2. **Je n'ai rien fait et j'attends l'arbitrage.**

### Alternative 2 — Le sort de `tests/reference_cli/`

| Branche | **reconstruire** une fois avec le harnais courant | **déclarer archive documentaire** |
|---|---|---|
| ce qu'il devient | un témoin comparable, utilisable à chaque correctif | une trace figée du comportement détecteur allumé, plus jamais rejouée |
| coût | une construction (~15 min), et la perte de l'instantané d'étape 1 | aucun |
| ce qu'on perd | rien de mesurable : ses valeurs seraient recalculées à l'identique, seul le schéma changerait | le second témoin, remplacé par le A/B à chaque fois |
| ce qu'on garde | le régime le plus exigeant reste testé automatiquement | il faut penser à lancer le A/B |

**Ce qui les départage :** si le régime CLI doit rester un test automatique,
il faut le reconstruire ; s'il n'est qu'une pièce d'archive documentant le
détecteur qu'on remplace — ce que dit son `LISEZ-MOI.md` —, le A/B suffit et
rien ne bouge.

### Alternative 3 — `n_min` pour les espèces à un seul point support

| Branche | **dériver quand même**, par espèce | **replier sur la valeur estivale** quand le support est insuffisant |
|---|---|---|
| valeurs | brochet 25, brème 75, barbeau 75, truite fario 10 | 60 pour ces quatre |
| ce que le nombre signifie | la puissance du test **sur cette chronique-là** | la puissance mesurée sur 30 points, transposée |
| effet sur le corpus | **nul** — aucune de ces quatre espèces n'a d'estimation écartée dans un cas comme dans l'autre | nul |
| risque | un `n_min` de 10 (truite fario) laisse passer des pentes estimées sur dix jours | un `n_min` de 75 exclut des fenêtres que leur propre mesure jugeait suffisantes |
| ce qu'il faut déclarer | le nombre de points supports, à côté de la valeur | le repli, et pourquoi |

**Ce qui les départage :** un seuil dérivé d'un seul point n'est pas dérivé, il
est décrit. Si la règle doit rester une propriété du **jeu**, il faut un
support minimal — trois points, par exemple — en deçà duquel on replie sur la
fenêtre la mieux fournie. Si elle doit rester une propriété de **chaque
fenêtre**, on dérive quand même et l'on publie le support. Sur ce corpus les
deux branches donnent le même résultat ; sur un autre, non.
