# THERMIE_BIO V4.6 — Rapport d'étape 11

**Objet.** Refaire par empreinte ce que l'outil défaillant avait certifié,
recalculer les `t` avant de poser, puis poser le **correctif 6** — la règle de
validité du coefficient de couplage.

---

## Artefacts (D34, D54, D63) — les motifs contestés à partir de la typologie

| Artefact | Type (D63) | Déclaré | Verdict du motif | Constaté |
|---|---|---|---|---|
| `06_coefficients.csv` | dépendance propre | doit bouger | **juste** | **6/6** |
| `07_t_norm.csv` | **projection** de `res.df` | doit bouger | **juste mais INCOMPLET** — voir ci-dessous | **3/6** |
| `10_parametres.json` | **métadonnée** | doit bouger | **juste** | **6/6** |
| `08_scores.csv` | dépendance propre | peut bouger, à chiffrer | **juste**, effet nul | **FIGÉ — 0** |
| `05_anomalies.csv` | **projection** | figé — aucune colonne ne dépend de `m` | **juste** | **FIGÉ** |
| `04_normales.csv` | **projection** | figé — aucune ligne retirée | **juste** | **FIGÉ** |
| `02_effectifs.csv`, `03_journees_ecartees.csv` | dépendance propre | figés | **juste** | **FIGÉS** |
| `00`, `01` | **métadonnées** | figés — la lecture ne change pas | **juste** | **FIGÉS** |

**La prédiction falsifiable sur `05_anomalies.csv` tient** : elle porte
`T_air`, `T_normale`, `Delta_TMm`, `Delta_TMm_liss`, `T_air_std`, dont aucune
ne dépend de `m`. Figé sur les six jeux.

### Le motif de `07_t_norm.csv` était incomplet — signalé avant la pose

Il disait : « le `m` de `BLE3-0` passe de −0,010 à 0, donc `T_normalisee`
change **sur ce point** ». Vrai, mais `07_t_norm.csv` porte aussi
`Tmh_norm_fraie[espèce]`, qui dépend de `m_saisonnier`. Or la règle s'applique
aussi au saisonnier, et son garde-fou sur le R² disparaît.

Prédit avant la pose, constaté après : l'artefact bouge sur **trois** jeux.

| Jeu | Point | Cause |
|---|---|---|
| `jeu_bienne` | `BLE3-0` | `m_estival` rejeté → 0 |
| `jeu_04` | `SN 21069646 - La Canner à Vigy 1` [brème] | **cesse** de se replier : sa pente saisonnière est retenue |
| `jeu_exemples_v45` | `La Moselle à Hielle` [truite fario] | `m_saisonnier` rejeté → 0 (au lieu du repli) |

*Un motif juste sur son mécanisme peut être incomplet sur son étendue. C'est
la troisième forme de motif erroné rencontrée : faux (étape 10, `00`/`01`),
vrai du calcul et faux de l'artefact (étape 10, `04`), juste et incomplet
(ici).*

---

## §0 — Carnet de bord

### Le heredoc a de nouveau coupé une chaîne, et le rejeu a tourné pour rien

Une insertion dans `parametres.py` portait un `\\n` qui est devenu un vrai saut
de ligne au passage par un document heredoc du shell, coupant un littéral de
chaîne en deux. Le fichier ne compilait plus ; le rejeu a démarré, échoué sur
tous les jeux, et **rendu un code de sortie 0** — le harnais capturant l'échec
par jeu.

Quinze minutes perdues, aucun dommage : le dossier de sortie était vide et le
comparateur l'a dit. Mais c'est la troisième fois que ce piège se referme. La
parade existe et je ne l'avais pas appliquée ici : **écrire le script comme
fichier, jamais le composer dans une ligne de commande**, et exprimer les
caractères de contrôle par `chr(10)`.

### La certification refaite n'a rien retourné, et c'était le résultat utile

`comparer_rejeux.py` était aveugle sur `04_normales.csv` depuis l'étape 7.
Refaite par empreinte SHA-256 — qui ne dépend d'aucune clé —, la vérification
donne **une seule empreinte distincte sur sept rejeux pour cinq jeux sur
six**, et deux pour `jeu_bienne`, la seconde apparaissant à la pose 2 de
l'étape 10, mouvement déjà relevé.

**L'outil était aveugle, il n'a rien manqué.** Un contrôle refait qui confirme
n'est pas un contrôle inutile : c'est la différence entre « figé » et « on
n'a pas regardé ».

*Mon script de vérification a d'abord signalé cinq anomalies. C'était sa
propre logique de verdict qui était fausse — il traitait « déclaré mobile et
n'a pas bougé » comme un écart, alors que seul un **mouvement là où l'étape
déclarait figé** en est un. Corrigée, la vérification passe.*

### Le seuil de R² disparaît, et ce n'est pas une omission

L'ancien `_m_saisonnier` repliait sur `m_estival` si `R² < 0,30` **ou** si la
pente sortait du domaine. La spécification ne porte aucune condition sur le
R². Je l'ai retirée, et il faut dire pourquoi plutôt que de le faire en
silence.

Un R² faible sur un grand échantillon ne dit pas que le couplage est
indistinct de zéro : il dit que l'air explique peu de la **variance**. Ce sont
deux énoncés différents, et c'est l'IC qui répond au premier. `La Canner à
Vigy 1` [brème] l'illustre : `R² = 0,241`, mais `n = 326` et `t = 3,96`. Sa
pente est parfaitement distinguable de zéro ; l'ancien garde-fou la remplaçait
pourtant par le coefficient de l'été.

**Et le repli disparaît avec lui.** Un coefficient rejeté vaut zéro (D33), il
ne prend pas la valeur d'un autre. Se rabattre sur `m_estival` faisait
normaliser une fenêtre de reproduction hivernale avec le couplage de l'été :
une substitution silencieuse présentée comme un garde-fou.

---

## §1 — D44

**Avant** : sept entrées, exactement les sept déclarées, aucune en CRLF.
Retour **0**.
**Après** : les mêmes sept — le correctif 6 touche `core.py`, `config.py` et
`app.py`, tous déjà déclarés. Retour **0**, aucun CRLF introduit.

---

## §2 — Ce que l'outil défaillant avait certifié

`tests/reference/verifier_04_normales.py`. Sept rejeux conservés, six jeux,
**42 empreintes**.

| Jeu | Empreintes distinctes sur 7 rejeux |
|---|---|
| `jeu_02`, `jeu_03`, `jeu_04`, `jeu_05`, `jeu_exemples_v45` | **1** |
| `jeu_bienne` | **2** — la seconde à la pose 2 de l'étape 10 |

**Aucun mouvement non déclaré.** Les « figé » prononcés sur
`04_normales.csv` aux étapes 6 à 9 et à la pose 1 de l'étape 10 étaient
**justes**. Le seul mouvement de cet artefact est celui que l'étape 10 a
relevé et documenté.

*La méthode compte : la vérification est faite par empreinte du fichier
entier, qui ne dépend d'aucune clé, d'aucun appariement et d'aucune colonne —
donc d'aucune des hypothèses qui avaient rendu l'outil aveugle.*

---

## §3 — Les `t` recalculés, puis la règle et sa prédiction

### D1 — Sur l'état actuel de la chaîne, avant de poser

`tests/reference/mesure_validite_actuelle.py`, paramètres pris du rejeu de
l'étape 10 — le seul endroit où le paramétrage du détecteur relatif est écrit
tel qu'il a tourné.

**`m_estival` — 32 estimations, 1 rejet réel :**

| Point | `m` | `t` | `n` | Critère |
|---|---|---|---|---|
| **`BLE3-0`** | **−0,0100** | **−0,447** | 107 | IC contient zéro **et** pente hors domaine |
| *`BIE35-5__NA`* | *n = 0* | — | 0 | *chaîne interrompue (D7), pas un rejet* |

**`m_saisonnier` — 33 estimations, 2 sous le critère :**

| Point | Espèce | `m` | `t` | `n` |
|---|---|---|---|---|
| `BLE3-0` | ombre commun | 0,0149 | 0,219 | **7** |
| `La Moselle à Hielle` | truite fario | 0,1703 | **1,528** | 67 |

### D2 — `BLE3-0` reste seul, et la marge ne s'est pas resserrée

| | Étape 4 | Étape 11 |
|---|---|---|
| `t` de `BLE3-0` | 0,447 | **0,447** |
| `t` du suivant | 3,585 | **3,658** |
| rapport | 8,0 | **8,2** |

**La séparation s'est très légèrement élargie.** Les cinq correctifs — qui ont
déplacé `m` jusqu'à 0,042 et la chronique sur laquelle il est estimé — n'ont
pas rapproché `BLE3-0` du reste du corpus. Le suivant est
`SN 21069646 - La Canner à Vigy 1`, à `t = 3,658`.

### D3 — La règle posée, et le rejet constaté

**Deux rejets, et ce sont les prédits :**

| Point | Grandeur | `m` retenu | pente estimée | `t` | Critère |
|---|---|---|---|---|---|
| `BLE3-0` | `m_estival` | **0,0** | −0,0100 | −0,447 | IC contient zéro **et** hors domaine |
| `La Moselle à Hielle` | `m_saisonnier` | **0,0** | 0,1703 | 1,528 | IC contient zéro |

**Une différence entre la prédiction et le constat, et elle est attendue.**
D1 comptait `BLE3-0 [ombre commun]` parmi les estimations sous le critère.
Elle ne figure pas parmi les rejets, parce que son `n = 7 < 20` fait jouer
**d'abord** le repli conservé par C3. Son `m_saisonnier` vaut donc
`m_estival`, lui-même mis à zéro : le résultat est le même, par un autre
chemin. Le repli précède la règle, et c'est ce que C3 demande.

Répartition finale des statuts : **59 valides, 2 rejetés**, 33 sans statut —
ce sont les lignes `normales` et les saisonniers repliés faute d'effectif.

---

## §4 — Le correctif et ses artefacts

### C1 — Newey-West dans le code applicatif

`core.ic95_newey_west(x, y)` rend `(pente, demi_largeur, erreur_type, t, n,
lag)`. **La pente reste strictement celle de l'OLS** — la même que
`stats.linregress` : le correctif ne change aucune estimation, il estime
autrement l'incertitude autour d'elle.

**La règle de décalage retenue** est `L = ⌊4 (n/100)^(2/9)⌋`, avec le noyau de
Bartlett. *Provenance : convention statistique usuelle de la littérature
économétrique pour le choix automatique du décalage. Elle ne dépend que de `n`
et ne se calibre sur aucun jeu de données.* Le niveau de 95 % est celui de
tout intervalle de confiance.

*Pourquoi Newey-West et non l'écart-type ordinaire : les résidus d'une
régression sur chronique journalière sont autocorrélés — une journée chaude
suit une journée chaude. L'OLS les traite comme indépendants et sous-estime
l'incertitude.*

### C2 et C3 — le rejet, et le seul repli qui subsiste

Rejet → `m = 0`, donc `T_norm = T` (D33). La chaîne continue de tourner ; la
normalisation est **neutralisée**, non refusée.

Le repli de `_m_saisonnier` sur `m_estival` pour `n < 20` est **conservé
inchangé** (C3) : en deçà de vingt jours, il n'y a pas de quoi estimer une
incertitude, donc pas de quoi appliquer la règle. C'est le seul repli qui
subsiste — celui sur le R² disparaît (§0).

### C4 — le statut de validité, propagé

`06_coefficients.csv` gagne sept colonnes : `m_estime`, `validite_statut`,
`validite_ic95_demi_largeur`, `validite_erreur_type_nw`, `validite_t`,
`validite_lag_nw`, `validite_critere_rejetant`.

**`m` et `m_estime` sont distincts, et c'est délibéré.** `m` est le
coefficient **appliqué** — zéro en cas de rejet. `m_estime` est la pente
**estimée**. Publier le seul zéro laisserait croire que le couplage a été
mesuré nul ; publier la seule pente laisserait croire qu'elle a été appliquée.

*La catégorie de sensibilité continue de décrire la pente **estimée** : dire
« Résilience Élevée » parce qu'on a imposé zéro serait un contresens.*

### C5 — le texte de dégradation déclarée

Rédigé en **§2.4** de la spécification, dans l'idiome du §1.5. **Non affiché**
(D48). Il dit les trois choses demandées :

> *Ce que l'écran publie donc :* les **températures brutes**. `T_norm = T`.
> *Ce que cela n'autorise pas à conclure :* les pourcentages décrivent
> **l'année observée**, avec la météo qu'elle a eue — pas une année standard.
> Deux points ainsi traités ne sont **pas comparables entre eux**, ni le même
> point d'une année sur l'autre.
> *Ce que cela n'autorise pas non plus :* conclure que ce cours d'eau est
> **insensible** à l'air. Un couplage non distinguable de zéro n'est pas un
> couplage nul ; c'est un couplage que **ces données** ne permettent pas
> d'établir.

Deux variantes : rejet estival, rejet saisonnier par espèce — le statut étant
par espèce (D28), l'écran l'affiche par espèce.

### D61 et D64

`hors_eau_min_jours` est **supprimé** du dataclass, de `to_legacy_dict`, du
widget et de `10_parametres.json` : une configuration morte publiée dans un
livrable est un énoncé faux.

La spécification écrit désormais la relativisation **« par mois de la sonde
traitée »**. Le comportement est identique — c'est la notation qui était
fausse, pas le code.

---

## §5 — Journal des verdicts

`docs/VERDICTS_MODIFIES.md`, section « correctif 6 ». **Aucun verdict publié
ne change**, aucune catégorie, sur aucun des 32 points. `08_scores.csv` est
figé.

### `BLE3-0` — le point qui normalisait à l'envers

Avec `m = −0,010`, la normalisation calculait
`Tmh_norm = Tmh + 0,010 × Delta_TMm_liss` : elle **ajoutait** l'anomalie d'air
au lieu de la retrancher. Une année plus chaude que la normale rendait la
température « normalisée » **plus chaude** que la brute.

L'écart de valeur est négligeable — `Tmh_norm` bouge de **0,016 °C en
médiane, 0,066 °C au maximum** — et aucun indicateur du point ne change : il
affichait déjà 0 journée aiguë, 0 % de stress chronique, SGVT 0.

**Ce qui change n'est pas le chiffre, c'est son statut.** Le point publiait
une température *normalisée*, avec l'autorité que ce mot porte — débarrassée
de l'effet du climat, donc comparable à un autre point et à une autre année.
Cette autorité reposait sur un coefficient dont le signe était faux et dont
l'IC contenait zéro. Le point publie désormais des températures brutes **en le
disant**.

*Le chiffre était déjà à peu près juste ; c'est ce qu'on avait le droit d'en
conclure qui était faux.*

---

## §6 — Alternatives fermées

### Alternative 1 — Le sort du seuil de R² sur le saisonnier

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — le retirer (retenue)** | `La Canner à Vigy 1` [brème] retrouve sa pente propre ; `07_t_norm` bouge sur ce jeu | la spécification ne porte pas ce seuil, et C3 pose que le repli sur l'effectif est **le seul qui subsiste**. Un R² faible ne dit pas qu'un couplage est indistinct de zéro |
| **B — le conserver en plus des deux conditions** | trois conditions au lieu de deux | il faudrait justifier un seuil de 0,30 que rien ne dérive, et D15 l'interdirait comme toute valeur non dérivée |

*Je retiens A. Le retrait est une conséquence de la spécification, pas une
initiative — mais il déplace un coefficient et méritait d'être dit.*

### Alternative 2 — La catégorie de sensibilité en cas de rejet

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — la calculer sur la pente ESTIMÉE (retenue)** | `BLE3-0` garde sa catégorie descriptive | la catégorie décrit le cours d'eau, pas la décision de la règle. La calculer sur le zéro imposé afficherait « Résilience Élevée » pour un point dont on vient de dire qu'on ne sait rien de son couplage |
| **B — la calculer sur le `m` retenu** | catégorie cohérente avec le `m` publié | elle deviendrait un contresens : un zéro imposé faute d'information se lirait comme une mesure de résilience |

*Je retiens A, et l'écran devra afficher la catégorie **à côté** du statut de
rejet, jamais à sa place.*

---

## §7 — Ce qui reste

**Correctif 4** (convention unique `T − m × Delta_TMm_liss`, D18),
**correctif 7** (défauts littéraux, D22), **correctif 10** (`io_data.py:98`,
D60, programmé étape 13), et **l'affichage** de toute la dégradation déclarée
(D48, étape 14).

Rien de nouveau n'est apparu dans le périmètre `lecture → T_norm` à cette
étape.
