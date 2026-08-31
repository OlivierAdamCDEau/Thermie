# THERMIE_BIO V4.6 — Rapport d'étape 10

**Objet.** Poser le **correctif 1** — le détecteur de mise hors d'eau — en deux
poses séparées, chacune avec son rejeu : le détecteur de plateau sur index
calendaire (D46), puis le détecteur relatif à deux marches.

C'est le seul correctif du chantier qui **substitue** un comportement au lieu
d'en révéler un.

---

## Artefacts (D34, D54) — les motifs, contestés avant la pose

### Pose 1 — tout figé

| Déclaré | Motif | Constaté |
|---|---|---|
| tout figé | 0 verdict de plateau ne change (mesure d'étape 6) | **65/66 figés** ; seul `jeu_bienne/99_log.txt` bouge, sur **un numéro de ligne** d'une trace figée |

**Motif vérifié.** `02`, `03` et `06` sont figés comme annoncé.

### Pose 2 — deux motifs contestés, un troisième trouvé faux après coup

| Artefact | Déclaré | Motif | Verdict du motif | Constaté |
|---|---|---|---|---|
| `02_effectifs.csv` | doit bouger | les journées écartées changent de nombre | **juste** | **3/6** |
| `03_journees_ecartees.csv` | doit bouger | nouveaux motifs, nouvelles journées, colonnes de D57 | **juste** | **6/6** |
| `06_coefficients.csv` | doit bouger | l'échantillon de régression perd les journées écartées | **juste** | **3/6** |
| `05_anomalies.csv`, `07_t_norm.csv` | doivent bouger | `m` change, donc `T_norm` | **juste** | **3/6** chacun |
| `08_scores.csv` | doit bouger | ricochet | **juste** | **3/6** |
| `10_parametres.json` | doit bouger | deux paramètres disparaissent, ceux des marches apparaissent | **juste** | **6/6** |
| `00_format_detecte.json` | **figé** | — | **FAUX — signalé avant la pose** | **6/6 bougent** |
| `01_colonnes_retenues.json` | **figé** | — | **FAUX — signalé avant la pose** | **6/6 bougent** |
| `04_normales.csv` | **figé** | calculée en amont de `fusionner` | **FAUX — non vu avant la pose** | **1/6 bouge** |

**Bilan : 20 artefacts figés, 46 bougent.**

### `00` et `01` : la contradiction, signalée avant de poser

La marche 2 a besoin de `TN` et `TX`. Or `io_data.charger_air_brut` ne les
lisait **jamais** : `usecols` retenait `NUM_POSTE, NOM_USUEL, AAAAMMJJ, TM,
RR`. Sans eux, la marche 2 serait perpétuellement indisponible et la
prédiction Q1 — 9 journées par la marche 2 — serait inatteignable.

`01_colonnes_retenues.json` enregistre littéralement ce fait :

```json
"TN_TX_lus": false,
"motif_TN_TX": "TN et TX ne figurent pas dans usecols : ils ne sont jamais
                lus, donc jamais transmis (io_data.py:432)"
```

Les lire **fait donc nécessairement bouger `00` et `01`** — c'est précisément
ce que ces deux artefacts consignent. Et la **spécification l'avait écrit** :
son §4 déclare `io_data.py` parmi les fichiers touchés, avec l'effet
« `00_format_detecte.json` et `01_colonnes_retenues.json` bougeront — deux
colonnes de plus ».

La commande d'étape pose que la spécification fait foi. J'ai donc suivi la
spécification et signalé la contradiction plutôt que de renoncer à la
marche 2.

### `04_normales.csv` : le motif que je n'ai pas contesté, et j'aurais dû

Le motif — « calculée en amont de `fusionner` » — est **vrai du calcul et faux
de l'artefact**. `art_04` ne recopie pas la table des normales : il projette
`res.df[["day", "month", "T_normale"]].drop_duplicates()`, c'est-à-dire les
seuls couples (jour, mois) que la chronique **retenue** contient encore.

Le détecteur retirant des journées, quatre couples disparaissent :

| Point | Couple perdu |
|---|---|
| `ABI3-6` | 1er juin |
| `GRO9-1` | 28 juin |
| `LGV11-8` | 1er juin |
| `LGV11-8` | 18 septembre |

**Aucune valeur de normale ne change** — le motif a raison sur ce point. Mais
l'artefact rétrécit. J'ai vérifié les sept autres motifs contre le code et
accepté celui-ci sur sa vraisemblance : c'est exactement l'erreur que D54 vise.

---

## §0 — Carnet de bord

### Mon outil de comparaison a caché ce mouvement

`comparer_rejeux.py` déclarait pour `04_normales.csv` la clé
`["point", "doy"]` — une colonne qui n'existe pas dans ce fichier, dont les
colonnes sont `point, mois, jour`. La clé absente faisait retomber la
comparaison en appariement positionnel ; les longueurs différant, la boucle de
colonnes était sautée ; et l'outil rapportait **« 0 valeur changée »** sur un
artefact qui avait perdu quatre lignes.

C'est la même famille que le `str.replace` muet de l'étape 8 : **un outil qui
ne trouve pas ce qu'il cherche doit le dire, pas retourner zéro.** L'outil
refuse désormais le silence — clé absente et lignes non appariables sont
rapportées comme telles. C'est en corrigeant l'outil que le mouvement de `04`
est devenu visible.

### Deux poses valaient mieux qu'une

Séparer la pose 1 de la pose 2 a coûté un rejeu complet et a rapporté deux
choses. La prédiction de la pose 1 — « aucun verdict de plateau ne change » —
a pu être **vérifiée seule** : 65 artefacts sur 66 figés, la mesure d'étape 6
confirmée trois étapes plus tard. Et l'effet du détecteur a pu être mesuré
contre un état où seul le plateau avait bougé, sans que les deux se
confondent.

Si la pose 1 avait déplacé un verdict, la consigne était de s'arrêter. Elle ne
l'a pas fait, et l'on sait maintenant que la mesure de l'étape 6 était juste.

### Ce que le détecteur trouve sur `LA PLAINE`

Le régime en service ne marquait **aucune** journée hors d'eau sur ce point.
Le détecteur relatif en marque **16**, et **huit d'entre elles étaient
comptées comme journées de vulnérabilité aiguë**. Le point passe de « Risque
Modéré » à « Risque Faible (Zone Refuge) ».

C'est le résultat que tout le chantier visait, et il tient en une phrase : ce
point était publié avec dix journées de vulnérabilité aiguë sévère, et huit de
ces dix journées étaient la sonde hors de l'eau.

---

## §1 — D44

**Avant** : quatre entrées — `LISEZ-MOI.md`, `core.py`, `orchestrator.py`,
`qc.py` —, exactement les quatre déclarées, aucune en CRLF. Retour **0**.

**Après** : **sept** entrées. Trois fichiers s'ajoutent, tous déclarés par la
spécification §4 : `io_data.py` (lecture de `TN`/`TX`), `config.py` (les
paramètres des deux marches), `app.py` (leurs widgets). Retour **0**, aucun
CRLF introduit.

---

## §2 — Pose 1 : le détecteur de plateau, et sa prédiction

`qc.py` — l'écart-type glissant passe sur index calendaire. `fenetre` et
`min_periods` inchangés : `min_periods = w` exige désormais `w` jours
**réellement observés** dans la fenêtre, ce qui est le sens que cette exigence
avait toujours voulu avoir.

**Une seule implémentation pour deux usages.** La machinerie calendaire
descend dans `qc.fenetre_mobile_calendaire(dates, valeurs, fenetre,
min_periods, agregat)`, et `core.moyenne_mobile_calendaire` — nom, signature
et docstring conservés — délègue. `core` importe `qc`, jamais l'inverse : c'est
le seul placement qui évite la duplication sans import circulaire.

### La prédiction : **elle tient**

```
  artefacts compares : 66
  figes              : 65
  qui bougent        : 1
    jeu_bienne/99_log.txt : 1 valeur(s)
```

`02`, `03` et `06` sont **figés**, comme annoncé. La seule ligne qui bouge est
un numéro de ligne dans une trace d'erreur figée — `core.py:432` devient
`core.py:429`, la délégation ayant raccourci la fonction.

**La mesure de l'étape 6 était juste** : le défaut d'index du détecteur de
plateau est réel dans le code et n'était exercé par aucune journée du corpus.

---

## §3 — Pose 2 : le détecteur, les trois prédictions, les écarts

### Ce qui a été écrit

| Fichier | Ce qui change |
|---|---|
| `io_data.py` | `TN` et `TX` cessent d'être jetés à la lecture — conservés **quand ils existent**, jamais exigés |
| `config.py` | `hors_eau_ecart_seuil` et `hors_eau_exclut_saison` **disparaissent** ; `k`, `plancher_dispersion`, `min_jours_groupe`, `min_jours_episode`, `q_ampl` apparaissent |
| `qc.py` | le détecteur à deux marches, `relativiser()`, `longueurs_episodes()`, et les cinq colonnes de diagnostic de D57 |
| `app.py` | les widgets des nouveaux paramètres, **défauts pris du dataclass** |
| `orchestrator.py` | `res.rapport_qc_detaille` pour le périmètre ; `rapport_qc` reste la vue héritée |

**Ce qui remplace les deux paramètres disparus dans `10_parametres.json`** :
`k = 3,0`, `plancher_dispersion = 0,05`, `min_jours_groupe = 10`,
`min_jours_episode = 1`, `q_ampl = 0,10`. Le seuil absolu en °C et l'exclusion
de saison n'ont pas de successeur : ils n'avaient pas de fonction, ils avaient
une valeur.

### P2.2 — la marche 2 est déclarée, jamais silencieuse

`marche_active` porte, par journée, soit `marche 1 + marche 2`, soit
`marche 1 (marche 2 indisponible : TN, TX ou T_eau_min absents)`. Le journal le
dit aussi une fois par chronique. Sur le corpus, `TN` et `TX` étant désormais
lus, la marche 2 est disponible partout où le fichier d'air les porte.

### P2.4 — les valeurs de diagnostic (D57)

`E_moy_rel`, `R_ampl_rel`, `E_max_rel`, `longueur_episode` et `marche_active`
sont écrits **par journée** dans la table de marquage, remontés dans
`03_journees_ecartees.csv`, et **exclus de la vue héritée** — l'aval hors
périmètre ne voit rien de nouveau.

Extrait de `jeu_02/03_journees_ecartees.csv` :

```
2011-06-05 ; hors d'eau — socle relatif                            ; 4,068 ; ep.10 ; marche 1 + marche 2
2011-06-08 ; hors d'eau — socle relatif et conjonction forme et... ; 4,923 ; ep.10 ; marche 1 + marche 2
```

### Q1 — 69 marquées, 68 par la marche 1, 9 par la marche 2, 8 en recouvrement

| | Prédit | Constaté |
|---|---|---|
| total | **69** | **69** |
| marche 1 | **68** | **68** |
| marche 2 | **9** | **9** |
| recouvrement | **8** | **8** |

**Les quatre nombres, pas seulement le total.**

### Q2 — |Δ`m`| médiane 0,0009, maximum 0,0420

| | Prédit | Constaté |
|---|---|---|
| médiane | **0,0009** | **0,0009** |
| maximum | **0,0420** | **0,0420** |
| point du maximum | `LA PLAINE A RAON-SUR-PLAINE` | **`LA PLAINE A RAON-SUR-PLAINE`** |

### Q3 — 52 gagnées, 5 perdues, et les cinq nommées

| | Prédit | Constaté |
|---|---|---|
| journées gagnées | **52** | **52** |
| journées perdues | **5** | **5** |

Les cinq, toutes sur `BIE40-3` : **2015-07-09, 2015-07-28, 2015-07-30,
2023-07-20, 2023-07-22**. Ce sont **exactement** les cinq de
`out/etape8/C2_journees_perdues_vs_service.csv` — la sixième, le 8 juillet
2015, étant celle que la marche 2 rattrape, comme la mesure d'étape 8 l'avait
annoncé nommément.

**Les trois prédictions tiennent, sur les neuf nombres qu'elles portent.**

### P2.5 — les écarts entre la spécification et le code

Chaque valeur de la spécification a été confrontée au code écrit. Trois écarts
sont à signaler ; aucun n'est une valeur de bassin codée en dur.

**1. `hors_eau_min_jours` survit sans être lu.** La commande fait disparaître
`hors_eau_ecart_seuil` et `hors_eau_exclut_saison`, et ne dit rien du
troisième paramètre de l'ancien détecteur. Il portait la grille annuelle —
« au moins 5 jours suspects dans l'année » — que le détecteur relatif
n'utilise pas. Je l'ai **conservé dans le dataclass et dans
`10_parametres.json`**, avec un commentaire disant qu'il n'est plus lu, plutôt
que de le supprimer sans mandat. **C'est de la configuration morte**, et elle
est déclarée comme telle.

**2. La vue héritée filtre désormais sur « non écartée ».** `vue_retenue`
filtrait sur `statut == retenu`. Le socle relatif pouvant s'abstenir, une
journée non diagnosticable serait sortie de la chronique — traitée comme une
exclusion alors qu'elle n'a rien de défectueux. Le prédicat devient
`statut != ecarte`. Tant que `non_diagnosticable` n'avait aucun producteur,
les deux coïncidaient : le changement est sans effet sur tout ce qui précède.

**3. La relativisation groupe par mois seul, non par (point, mois).** La
spécification écrit `médiane_{point,mois}`. Le code traite **une sonde à la
fois** (D41) : le groupement par mois du point traité est la même chose,
exprimée dans le seul cadre où l'application peut la calculer. C'est un écart
de formulation, pas de comportement.

---

## §4 — Journal des verdicts, et section D59

`docs/VERDICTS_MODIFIES.md`, section « correctif 1 ».

### La ligne qui intéresse le maître d'ouvrage

| | |
|---|---|
| points dont une valeur publiée bouge | **18 sur 32** |
| **points dont une CATÉGORIE change** | **2 sur 32** |
| SGVT qui bougent | **2**, tous deux **à la baisse** |
| sens général | la vulnérabilité **diminue**, sauf sur `BIE40-3` |

### `LA PLAINE A RAON-SUR-PLAINE` — trois catégories sur trois

| Indicateur | Avant | Après | Catégorie |
|---|---|---|---|
| `n_jours_aigus` | 10 j | **2 j** | aiguë **sévère** → **ponctuelle** |
| `pct_stress_chronique` | 3,146 % | **0,467 %** | chronique **modérée** → **faible** |
| **`sgvt`** | 2,333 /10 | **1,500 /10** | **Risque Modéré → Risque Faible (Zone Refuge)** |

Seuil aigu **24,0 °C**. Huit journées cessent d'être aiguës, toutes **retirées
de la chronique** par le détecteur : 2011-06-05, 06-06, 06-08, 06-11, 06-12,
06-14, puis 2012-06-21 et 06-23.

*Cause :* leur écart eau-air dépassait de loin l'habitude du point au même
mois — jusqu'à **4,9 MAD\*** — sans jamais franchir le seuil absolu de 10 °C
qui les aurait fait voir.

### `SN 21069646 - La Canner à Vigy 1` — une catégorie

`n_jours_aigus` 1 → 0, « Vulnérabilité aiguë ponctuelle » → « Absence de
vulnérabilité aiguë ». La journée est le **1er juin 2021**, seuil 30,0 °C,
retirée par le détecteur. Le SGVT passe de 3,167 à 2,500 sans changer de
catégorie.

### Section D59 — les cinq journées que le détecteur ne marque plus

Conséquence **assumée** du passage au relatif, toutes sur `BIE40-3`, toutes en
juillet :

| Journée | `T_eau_max − T_air` | `E_moy_rel` | `R_ampl_rel` | `E_max_rel` |
|---|---|---|---|---|
| 2015-07-09 | 10,57 °C | 2,192 | 3,837 | 1,961 |
| 2015-07-28 | 11,74 °C | 2,499 | 8,512 | 2,773 |
| 2015-07-30 | 13,10 °C | 2,855 | 4,425 | 2,540 |
| 2023-07-20 | 10,01 °C | 2,045 | 2,988 | 1,697 |
| 2023-07-22 | 10,91 °C | 2,280 | 3,314 | 1,771 |

Leur écart, rapporté à ce que `BIE40-3` fait habituellement en juillet, reste
**entre 2,0 et 2,9 écarts-types robustes**, sous le seuil de 3,0. Le seuil
absolu les voyait parce qu'il ignore l'habitude du point — c'est exactement ce
qu'on lui reproche. *Sur ce même point, le détecteur marque 33 journées contre
13 pour le régime en service : il ne le manque pas, il le voit autrement.*

---

## §5 — Ce qui reste à faire

La liste de la commande est exacte : **correctif 6** (règle de validité, D27,
D39), **correctif 4** (convention unique `T − m × Delta_TMm_liss`, D18),
**correctif 7** (défauts littéraux, D22), et **l'affichage de la dégradation
déclarée** (D48).

**Ce que je vois d'autre dans le périmètre `lecture → T_norm`**, sans rien
corriger :

| `fichier:ligne` | Ce que c'est | Pourquoi je le signale |
|---|---|---|
| **`io_data.py:98`** | `df_w.dropna(subset=["date", "T_eau"])` | **La dernière suppression silencieuse du périmètre.** Des mesures infra-journalières sont écartées avant l'agrégation journalière, sans compte, sans date, sans cause. Le harnais le consigne depuis l'étape 1 comme `NON_RECUPERABLE` : « V4.5 ne conserve aucune trace de ces lignes ». C'est le même défaut que le correctif 5 a traité pour la jointure, un cran plus haut dans la chaîne |
| `io_data.py:151` et `io_data.py:569` | `ecart_by_date = df[["date","Delta_TMm"]].dropna()` | Restreint le calendrier d'air sur lequel le correctif 9 lisse, sans le dire. Effet probablement nul, non mesuré |
| `io_data.py:480` et `io_data.py:510` | `out.dropna(subset=["date","T_air"])` | Une journée d'air sans `TM` disparaît de la série. Défendable — elle n'a rien à offrir — mais non compté |
| `config.py` | `hors_eau_min_jours` | Configuration morte depuis cette étape (§3, écart 1) |
| `indicateurs.py:55` | `Tmm30j` | Hors chaîne (**D53**), porte les deux défauts — support et index |
| `core.py:1221` | `lissage_air` de `corr_partielle_air` | Hors chaîne, porte le défaut d'index |

**`io_data.py:98` est le seul élément du périmètre `lecture → T_norm` qui ne
soit ni posé, ni dans la liste de la commande.**

---

## §6 — Alternatives fermées

### Alternative 1 — Le sort de `hors_eau_min_jours`

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — le conserver, déclaré mort (retenue)** | il reste dans le dataclass et dans `10_parametres.json`, avec un commentaire disant qu'il n'est plus lu | la commande nomme deux paramètres à faire disparaître et pas celui-là. Le supprimer sans mandat retirerait de `10_parametres.json` une ligne que personne n'a demandé de retirer |
| **B — le supprimer** | `10_parametres.json` perd une ligne de plus | il faudrait l'instruction. De la configuration morte est un défaut, et il est désormais consigné |

*Je retiens A et je signale que la branche B est probablement la bonne, à votre
main.*

### Alternative 2 — L'abstention du socle sur les journées déjà écartées

Une journée que le socle ne sait pas juger reçoit le motif d'abstention même
si un autre détecteur l'a déjà écartée. Son statut reste `ecarte` — le motif
d'abstention s'ajoute sans rien changer au verdict.

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — le motif s'ajoute (retenue)** | la liste des motifs dit tout ce qui s'est passé sur la journée | c'est l'esprit du correctif 3 : conserver **tous** les motifs, pas le premier |
| **B — ne noter l'abstention que sur les journées retenues** | des listes de motifs plus courtes | on perdrait l'information que le socle n'a pas pu se prononcer, sur des journées où cela peut importer |

*Je retiens A, cohérente avec le correctif 3.*
