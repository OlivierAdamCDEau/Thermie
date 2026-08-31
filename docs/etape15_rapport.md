# THERMIE_BIO V4.6 — Rapport d'étape 15

**Objet.** Poser le **correctif 11** (D86) — la normale agrégée par `dayofyear`
et relue via une année bissextile — et **spécifier le correctif 12**, le critère
de complétude de journée.

**Les cinq prédictions d'artefacts tiennent**, dont la centrale :
`06_coefficients.csv` **figé**. Une seule chose n'était pas au programme, et
c'est la mesure de la pose 2 qui l'a trouvée : **mon premier critère de
complétude était faux**, et il répétait une erreur que l'étape 1 avait déjà
corrigée.

---

## §0 — Le message de commande est arrivé tronqué

Il s'interrompt sur `06_coefficients.csv —`, au milieu de la déclaration
d'artefacts. **Manquent** : le motif de cet artefact, la POSE 2 dans son détail,
et la structure du rapport.

Ce que j'ai fait, et pourquoi :

- **Le motif de `06_coefficients.csv`** : j'ai retenu celui que le chantier a
  déjà établi trois fois (étapes 6, 7 et 8) — `m` est une régression de l'eau
  **brute** sur l'air **brut** (`core.analyse_sensibilite`), aucune normale n'y
  entre. Vérifié dans le code avant la pose, constaté après.
- **La POSE 2** : D86 la définit — « le critère de complétude de journée,
  SPÉCIFIÉ à cette étape, POSÉ à la suivante ; il introduit un critère, donc il
  passe par une spécification, comme le correctif 4 ». J'ai suivi la forme de
  `SPEC_convention_unique.md`, que la commande invoque explicitement comme
  modèle.
- **La structure du rapport** : celle des étapes précédentes.

*Rien n'a été deviné sur le fond. Si la partie manquante portait des exigences
que je n'ai pas couvertes, elles restent à couvrir.*

---

## Artefacts (D34, D54, D63) — motifs et constats

| Artefact | Type (D63) | Déclaré | Verdict du motif | Constaté |
|---|---|---|---|---|
| `04_normales.csv` | projection de `res.df` | doit bouger | **juste** | **6/6 — `T_normale` seule** |
| `05_anomalies.csv` | projection | doit bouger | **juste** | **6/6** |
| `07_t_norm.csv` | projection | doit bouger | **juste** | **6/6 — `anomalie_utilisee`, `T_normalisee`** |
| `08_scores.csv` | dépendance propre | peut bouger, à chiffrer | **juste** | **1/6 — 2 valeurs** |
| `06_coefficients.csv` | dépendance propre | **figé** *(motif reconstitué, §0)* | **juste** | **FIGÉ 6/6** |
| `99_log.txt` | trace console | *(non déclaré par la commande)* | **déclaré mobile par moi avant la pose** | **6/6 — 11 lignes** |
| `02`, `03`, `00`, `01`, `10` | projections et métadonnées | figés | **juste** | **FIGÉS** |

**`99_log.txt` n'était pas dans la déclaration de commande.** Je l'ai déclaré
mobile avant la pose, pour deux raisons vérifiées : le journal imprime les
pourcentages de fraie, arrondis à l'unité, qui dépendent de `Tmh_norm_fraie` ;
et il imprime `len(ecart_by_date)`, qu'il fallait vérifier constant.

**Et il ne bouge PAS sur ses numéros de ligne** (D80bis) : le correctif ajoute
des lignes à `io_data.py`, or le cadre figé de `BIE35-5__NA` passe par
`orchestrator.py` et `core.py`, **jamais** par `io_data.py`. Vérifié avant,
constaté après.

---

## §1 — D44 et D76

**D44** — onze entrées avant, **onze après**, exactement les onze déclarées,
**aucun fichier de code en CRLF**, retour **0**. Seul
`app/thermie_debits/io_data.py` a bougé : **659 → 696 lignes**.

**D76** — les deux contrôles passent aux deux bouts : 66/66 sur les deux
références, zéro bytecode sous `ref/`. Retour **0**.

---

## §2 — Correctif 11 : la normale et l'année bissextile

### 1.1 — La mesure, avant toute correction

`tests/reference/mesure_normale_bissextile.py`. La chaîne est rejouée telle
quelle ; la version corrigée est recalculée **à côté**, à partir du même fichier
d'air, avec les fonctions de l'application. `app/` n'est pas touché.

**Contrôle de réplication** — une réplication non vérifiée ne vaut rien
(étapes 8, 9, 13) : le script recalcule d'abord la version **actuelle** par le
même chemin et vérifie qu'elle reproduit `res.df`. **Identique sur les 31
points.**

| | |
|---|---|
| journées du corpus | **67 054** |
| **journées à normale décalée** | **60 116 — 89,65 %** |
| couples (jour, mois) dont la normale change | **1 758 / 2 196**, sur 6 stations d'air |

Écart absolu, sur les 31 points :

| Grandeur | médiane des médianes | max des p95 | **maximum** |
|---|---|---|---|
| `T_normale` | 0,0642 °C | 0,2524 | **0,3429** (`La Canner à Vigy 1`) |
| `Delta_TMm` | 0,0642 °C | 0,2524 | **0,3429** |
| `Delta_TMm_liss` | 0,0662 °C | 0,2099 | **0,2986** (`Gorze`) |
| **`T_norm`** | **0,0294 °C** | 0,1090 | **0,1249** (`La Moselle à Hielle`) |

*`T_norm` est amorti par `m`, dont la médiane vaut 0,43 : l'écart sur la normale
n'atteint la température normalisée qu'à hauteur du coefficient.*

**Le profil confirme le mécanisme sans avoir besoin des données pour être
prédit** :

| Période | Couples | Médiane | Maximum |
|---|---|---|---|
| **1 jan → 29 fév** | 360 | **0,0000 °C** — 245 sur 360 inchangés | 0,3378 |
| **1 mars → 31 déc** | 1 836 | **0,0748 °C** | 0,3429 |

Du 1ᵉʳ mars au 31 décembre, le décalage de lecture s'applique. Avant le
1ᵉʳ mars, seuls **115 couples** changent : ceux que la fenêtre de lissage de
±10 jours atteint depuis la frontière, et ceux que le caractère **circulaire**
du lissage atteint depuis la fin décembre. C'est la réponse mesurée au §1.4.

### 1.2 — Le 29 février

| | Avant | Après |
|---|---|---|
| ce qu'il reçoit | la valeur du doy 60, lequel **mélange** à l'agrégation le 29 février des années bissextiles et le 1ᵉʳ mars des années communes | la moyenne des 29 février observés dans la période de référence, lissée avec ses **voisins calendaires** |
| journées du corpus concernées | **43**, sur **22 points** | idem |
| écart constaté | | de **−0,058** à **+0,094 °C** |

Il reçoit une normale dans les deux cas — la table `(jour, mois)` a toujours
porté une ligne (29, 2). Ce qui change est **ce que cette ligne moyenne**.

### 1.3 — La convention retenue, et sa provenance

1. La normale brute est agrégée par **identité calendaire `(mois, jour)`**, et
   non par numéro de jour dans l'année. Le 1ᵉʳ mars est le 1ᵉʳ mars dans toutes
   les années ; le 29 février forme son propre groupe.
2. Le lissage circulaire porte sur **l'axe des 366 jours calendaires** — le
   29 février y est entre le 28 février et le 1ᵉʳ mars, ce qui est sa place.
3. La lecture par `(jour, mois)` **ne change pas**. Elle interroge désormais le
   **même axe** que l'agrégation, et c'est tout ce que le correctif fait.

**Provenance.** `fenetre_lissage` et la période de référence sont ceux de la
version antérieure, repris sans modification. Le nombre **366** n'est pas une
valeur nouvelle : c'est le nombre de jours calendaires distincts, et il était
déjà écrit **trois fois** dans la fonction. **Aucune valeur propre à un bassin
n'entre ici.**

*Vérifié après la pose : la fonction posée reproduit la version corrigée de la
mesure à **0,00 × 10⁰ °C** sur les 366 couples. Les chiffres de 1.1
s'appliquent donc à la pose, et non à une approximation d'elle.*

### 1.4 — Le lissage circulaire

`io_data.py:636-639` — `w = 2 × fenetre + 1`, triple concaténation, moyenne
mobile centrée, tiers du milieu.

**Il ne souffre d'aucun décalage propre.** Il opère sur l'axe qu'on lui donne,
et la reprise du tiers central (`liss.iloc[366:366*2]`) est exacte.

**Mais il propageait le défaut, et cela se mesure.** Parce que la série
agrégée mélangeait deux jours calendaires par `doy` à partir du doy 60, la
fenêtre de ±10 jours reportait ce mélange **en arrière** jusqu'à la mi-février,
et, par circularité, jusqu'au début janvier. **115 couples antérieurs au
1ᵉʳ mars changent, avec un maximum de 0,3378 °C** — le plus grand écart de tout
janvier. Le lissage n'était pas la cause ; il en était le véhicule, et
l'affirmer sans le chiffrer aurait été une supposition.

### 1.5 — Ce que le rejeu constate

```
  artefacts compares : 66
  figes              : 41
  qui bougent        : 25
```

| Artefact | Valeurs déplacées | Colonnes |
|---|---|---|
| `04_normales.csv` | 327 · 327 · 324 · 327 · 7 723 · 90 | `T_normale` |
| `05_anomalies.csv` | jusqu'à **225 479** (`jeu_bienne`) | `T_normale`, `anomalie_brute`, `anomalie_lissee`, `T_air_std` |
| `07_t_norm.csv` | jusqu'à **258 536** | `anomalie_utilisee`, `T_normalisee` |
| `08_scores.csv` | **2** (`jeu_bienne` seul) | `valeur` |
| `99_log.txt` | **11 lignes** au total | (texte) |
| **`06_coefficients.csv`** | **0** | **FIGÉ** |

**`T_air_std` bouge aussi**, et c'était prévisible sans être prédit :
`core.py` la définit comme `T_air − Delta_TMm`, c'est-à-dire exactement
`T_normale`. Elle appartient au même motif.

**Aucune ligne n'est ajoutée ni retirée nulle part** — `-0 / +0` sur les 25
artefacts. Le correctif déplace des valeurs, il ne change aucun périmètre.

---

## §3 — Le ricochet, chiffré

`08_scores.csv` bouge sur **deux valeurs**, toutes deux `pct_stress_chronique` :

| Point | Avant | Après | Δ |
|---|---|---|---|
| `BIE31-4` | 2,172390 % | 2,312544 % | +0,140 |
| `BIE40-3` | 5,049732 % | 5,126243 % | +0,077 |

**Vérification systématique sur les six jeux** — aucune autre valeur, et
surtout aucune catégorie :

| Indicateur | Valeurs modifiées |
|---|---|
| `sgvt`, `pts_chronique`, `pts_aigu`, `pts_fraie`, `pts_sensibilite` | **0** |
| `n_jours_aigus`, `P_fraie` | **0** |
| `q_thermie_bio`, `q_thermie_fonc` | **0** |
| `seuil_chronique`, `seuil_aigu`, `sgvt_composantes` | **0** |
| catégories et interprétations (colonnes `valeur_texte`, `detail`) | **AUCUNE** |

**Aucun seuil ne bascule.** Le correctif 9 en avait fait la théorie : pour
qu'un verdict change, il ne suffit pas qu'un correctif soit ample, il faut
qu'il touche là où c'est serré. Ici l'amplitude sur `T_norm` est de 0,029 °C en
médiane, et les 54 journées du corpus qui se tiennent à moins d'un demi-degré
d'un seuil ne sont pas celles qui bougent le plus.

**Le journal, lui, publie onze lignes modifiées** : sept pourcentages de fraie
sur `jeu_bienne` et un par jeu ailleurs, tous déplacés d'**un point de
pourcentage** par l'arrondi à l'unité. Aucun `P` ne change. Ils entrent au
journal des verdicts — l'étape 7 avait établi que des pourcentages publiés qui
bougent s'y consignent, même quand le score ne bouge pas.

---

## §4 — Correctif 12 : la spécification, et une mesure qui s'est trouvée fausse

`docs/SPEC_completude_journee.md`. Ce qui suit en est le résumé ; la
spécification fait foi.

### Le critère évident est faux, et le corpus l'a dit

La règle de décision avait été écrite **avant** les chiffres, en tête du script
(méthode de l'étape 3). Elle définissait une journée « maigre » comme portant
**moins du quart de l'effectif attendu du point**, l'effectif attendu étant
dérivé du **pas de mesure modal**.

Résultat : 209 journées sur 68 134 — dont **201 sur un seul point**,
`La Moselle à Hielle`, soit **96 % de tout ce que le critère trouvait**. Sa
distribution le dit : **199 journées à exactement `n = 4`** et **100 à
exactement `n = 24`**.

**Ce n'est pas une journée tronquée 199 fois. C'est une sonde qui a mesuré
toutes les six heures, puis toutes les heures.**

**C'est exactement l'erreur que l'étape 1 avait corrigée** : *« un pas modal
unique masque les changements de cadence en cours de chronique »*. La parade
retenue alors — porter la **distribution** des intervalles — n'avait pas été
appliquée ici. J'ai refait la mesure plutôt que d'écrire une spécification sur
un chiffre que je venais de montrer trompeur.

### Le critère qui ne dépend d'aucune cadence

Le **trou maximal de la journée** — le plus long intervalle non observé, bornes
de minuit comprises. Une journée horaire régulière rend 1 h, une journée à six
heures régulière rend 6 h, une journée dont les mesures sont groupées le matin
rend ~18 h. Seuil : **quatre fois le trou médian du point lui-même**, donc sa
propre cadence, dérivé et non importé.

| | Effectif | Trou maximal |
|---|---|---|
| journées désignées | 209 (0,307 %) | **142 (0,208 %)** |
| points concernés | 9, dont un à 96 % | **29, de 0,08 à 1,56 %** |
| **témoin indépendant** (écart aux voisines) | 0,329 contre 0,219 — **× 1,5** | **0,5715 contre 0,2185 — × 2,6** |

**Les deux critères se recouvrent sur 8 journées seulement**, sur 343 désignées
au total. Ils ne mesurent pas la même chose. Et la médiane de `n_mesures` des
journées trouées vaut **12 sur 24** : une journée trouée n'est pas pauvre en
mesures, elle les a **groupées** — le critère d'effectif ne pouvait pas les
voir.

### Ce que la spécification remonte

**36 des 142 journées tombent entre juin et septembre** — la seule fenêtre par
laquelle elles atteindraient `m`. Les deux mois les plus touchés sont **avril
(42)** et **octobre (28)**, ce qui ressemble à des journées de maintenance de
sonde plutôt qu'à un aléa.

**`BLE3-0` reste hors de portée du critère**, et le critère s'en abstient
visiblement : ses horodatages étant tous à minuit (D88), son trou médian vaut
24 h, son seuil dérivé 96 h, et aucune de ses 124 journées n'est désignée.
**Un critère fondé sur les horodatages ne peut pas juger un point dont les
horodatages sont détruits** — c'est un lien direct entre le correctif 12 et
D88, et il doit être déclaré à l'écran, pas déduit.

**Deux décisions attendent un arbitrage** (§4 de la spécification) : que fait-on
des journées désignées — marquer sans exclure, exclure de la chaîne, exclure de
la seule régression —, et quel facteur retient-on. Seule la première change ce
que l'outil publie ; c'est aussi la seule dont l'effet est connu d'avance, et
il est nul.

---

## §5 — État des lieux

Il reste, à ma connaissance :

- **Correctif 12** — spécifié ici, à poser à l'étape 16 après arbitrage des
  deux alternatives.
- **D48** — l'affichage de toute la dégradation déclarée, dont les textes
  s'accumulent dans **trois** spécifications désormais, et qui doit porter la
  note de D87 sur `_tmm30j`.
- **D68** — l'entrée du statut de validité dans les livrables.
- **D83** — le rebasage de clôture, sur décision explicite.
- **D88** — le n° 3, consigné au chantier aval avec sa raison. **La
  spécification du correctif 12 lui ajoute une raison** : le critère de
  complétude est structurellement inapplicable à `BLE3-0` tant que ses
  horodatages ne sont pas réparés.
- **Les cinq comportements que le corpus n'exerce pas** — débit désinfluencé,
  normales pré-calculées, export d'air multi-stations, garde-fou du MAD nul,
  branche `EcartNormales`.

**Je ne vois rien de nouveau dans le périmètre `lecture → T_norm`.** Le
correctif 11 l'a fermé du côté des normales ; le correctif 12 le fermera du côté
de la complétude. Les deux défauts qui restent — la colonne d'heure et
`_tmm30j` — sont en aval, et D87 et D88 les ont placés.

---

## §6 — Alternatives fermées

Les deux alternatives de fond appartiennent à la spécification du correctif 12
(§4) et ne sont pas reprises ici. Une seule question naît de cette étape.

### Alternative — La mesure du correctif 12 doit-elle être refaite après l'arbitrage ?

`out/etape15/P2_*` porte les deux critères, l'ancien et le nouveau. Le premier
est faux et je le dis ; il reste dans les fichiers.

| Branche | **A — garder les deux** | **B — ne livrer que le critère retenu** |
|---|---|---|
| ce que le lecteur voit | le critère faux, le juste, et ce qui les sépare | le critère juste seul |
| ce que ça permet | vérifier que le rejet du premier est fondé | rien de plus |
| risque | un chiffre faux (0,307 %) circule à côté du vrai (0,208 %) | on demande de croire que le premier était faux |

**Ce qui les départage** : le chantier a pour règle de consigner ce qu'il a
trouvé faux plutôt que de l'effacer — le 488 de l'étape 8 est resté au rapport.
**Je retiens A**, et la spécification ouvre sur le critère faux plutôt que de
le reléguer en note, pour qu'aucun lecteur ne retienne 0,307 % comme le chiffre
de la complétude.
