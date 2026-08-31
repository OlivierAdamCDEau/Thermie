# SPEC — La convention unique (correctif 4, D18)

**Objet.** La chaîne produit **six séries journalières de température
corrigée**, relevant de **deux familles de formules** qui ne diffèrent ni par
un détail d'implémentation ni par un arrondi, mais par leur **définition** :
l'une pondère l'anomalie d'air par un coefficient estimé et la lisse, l'autre
la retranche brute et sans coefficient. Les deux sont publiées. Le vocabulaire
qui les nomme ne les distingue pas — il les intervertit.

Le correctif 4 pose que la convention est **unique** :

> `T_corrigée = T − m × Delta_TMm_liss`

Cette spécification établit l'état du code, l'aval complet de chaque série, le
vocabulaire employé et ce qui en est faux, puis **instruit sans la trancher**
la seule question qui ne se déduit pas de la mesure : la famille compensation
alimente un tableau mensuel publié — ses colonnes doivent-elles **subsister
recalculées** ou **disparaître** ?

**Statut.** Spécification livrée à l'étape 12. **Aucune modification
applicative n'a été posée au titre du correctif 4.** La question de conception
§4 reste ouverte ; la commande d'étape la subordonnait explicitement à un
arbitrage, et §4.5 dit pourquoi elle n'est pas tranchable par la mesure.

Toutes les références `fichier:ligne` visent l'état de `app/` **à l'étape 12**,
c'est-à-dire après les correctifs 1, 2, 3, 5, 6, 8 et 9. Elles diffèrent de
celles de l'inventaire d'étape 4, qui visaient `ref/v4_5/`.

---

## §1 — Les six séries

### 1.1 Les deux familles

| | famille **normalisation** | famille **compensation** |
|---|---|---|
| Où | `core.py` | `indicateurs.py` |
| Formule | `T − m × Delta_TMm_liss` | `T − Delta_TMm` |
| Coefficient | `m`, **estimé** par régression | **aucun** — `m` implicitement égal à 1 |
| Anomalie | **lissée** sur `normalisation_lissage_delta` jours (défaut 7, `config.py:432`) | **brute**, journalière |
| Support du lissage | tout le calendrier de la station d'air (correctif 9, `core.py:317-325`) | sans objet |
| Vit dans | `res.df` — colonnes retournées par la chaîne | une variable **locale** de `calcul_indicateurs` ; seuls des **agrégats mensuels** sortent |
| Alimente | vulnérabilité, fraie, SGVT, débits de référence, 4 figures | un tableau mensuel, une figure, une feuille de classeur, l'écran |

**Deux écarts séparent les familles, et non un :** le coefficient, et la nature
de l'anomalie. Les confondre en un seul (« l'une pondère, l'autre pas »)
sous-estime l'écart : sur le corpus, remplacer `Delta_TMm` par
`m × Delta_TMm_liss` déplace **777 valeurs publiées sur 777**, d'un écart
médian de **3,96 °C** (§4.2).

### 1.2 Les six séries, une par une

| # | Série | Formule exacte | Coefficient | Fenêtre d'estimation | Calcul |
|---|---|---|---|---|---|
| 1 | `Tmh_norm` | `Tmh − m × Delta_TMm_liss` | `m` **estival** | juin–sept., en dur `core.py:520` | `core.py:579` |
| 2 | `Tmax_norm` | `T_eau_max − m × Delta_TMm_liss` | `m` **estival** | idem | `core.py:580` |
| 3 | `Tmh_norm_fraie` | `Tmh − m_s × Delta_TMm_liss` | `m` **saisonnier** | union des mois de phase de l'espèce, `core.py:764` | `core.py:779` |
| 4 | `T_moy_comp` | `T_eau_moy − Delta_TMm` | **aucun** (`m ≡ 1`) | sans objet | `indicateurs.py:88` |
| 5 | `T_max_comp` | `T_eau_max − Delta_TMm` | **aucun** | sans objet | `indicateurs.py:89` |
| 6 | `T_min_comp` | `T_eau_min − Delta_TMm` | **aucun** | sans objet | `indicateurs.py:90` |

Deux précisions que le tableau ne porte pas.

**Les séries 1 à 3 ne partagent pas leur coefficient.** `m` estival est estimé
sur juin–septembre (`core.analyse_sensibilite`, `core.py:519-520`) ; `m_s` est
ré-estimé sur la fenêtre de reproduction de chaque espèce
(`core._m_saisonnier`, `core.py:645`), avec un repli sur `m` estival en deçà
de vingt jours (`core.py:657`) et un rejet à zéro si la règle de validité du
correctif 6 le refuse (`core.py:682-690`). Une même chronique peut donc porter
trois coefficients différents selon la fenêtre de l'année considérée.

**La série 3 n'est pas une projection de `res.df`.** Elle vit dans le
sous-DataFrame `sub` de chaque sous-indicateur d'espèce
(`core.py:766, 779`), retourné dans `res.fraie["sous_indicateurs"]`. Les
séries 4 à 6 ne vivent nulle part : `calcul_indicateurs` les construit dans sa
copie locale `d` et ne retourne que des agrégats. C'est pourquoi
`07_t_norm.csv` porte pour elles `sortie_v45= non` — le harnais applique la
formule citée et le déclare, plutôt que de laisser croire que la valeur sort
de la chaîne.

### 1.3 L'aval, série par série

#### Famille normalisation — inchangée par le correctif 4

| Série | Consommateur | Nature de l'usage |
|---|---|---|
| `Tmh_norm` | `core.py:584`, `core.py:587` | **% de stress chronique** → `pct_chr`, `cat_chr` → composante SGVT |
| | `core.py:1045`, `1055`, `1088`, `1104`, `1109`, `1144` | `analyse_debits_inflexion` — recherche de `Q*_vuln`, corrélation partielle |
| | `core.py:1424`, `1430`, `1445`, `1446`, `1489` | `analyse_relation_debit_temperature` — verdict du levier débit |
| | `figures.py:71-72` | découpe aux lacunes, figure de chronique |
| | `figures.py:88-94` | **`Fig0_Chronique.png`** — courbe et aire d'écart |
| | `figures.py:239`, `243` | **`Fig_Vulnerabilite.png`** — panneau chronique |
| | `figures.py:774`, `801` | figure débit — stress chronique glissant |
| | `redaction.py:194` | phrase d'interprétation de la vulnérabilité |
| | `app.py:90` | bandeau des seuils retenus |
| `Tmax_norm` | `core.py:585`, `core.py:588` | **nb de jours létaux** → `n_aigu`, `cat_aigu` → composante SGVT |
| | `core.py:1046`, `1063`, `1073` | `analyse_debits_inflexion` |
| | `figures.py:239`, `244` | `Fig_Vulnerabilite.png` — panneau létalité |
| | `figures.py:810`, `820` | figure débit — létalité glissante |
| | `redaction.py:196` | phrase d'interprétation |
| | `app.py:91` | bandeau des seuils retenus |
| `Tmh_norm_fraie` | `core.py:786` | **sévérité fraie** → `P_fraie` → composante SGVT |
| | `figures.py:390`, `443` | **`Fig_Fraie_Croissance.png`** |
| | `exports.py:253`, `278` | classeur `Fraie_Croissance_Detail.xlsx` (via les `%` de phase) |
| | `livrables.py:287-289`, `505-520` | Word chapitre 3, classeur feuille `03_Fraie` |

Ces trois séries alimentent **trois des quatre composantes du SGVT** et **les
débits de référence**. Le correctif 4 ne les touche pas : leur formule *est*
la convention unique.

#### Famille compensation — le périmètre entier du correctif 4

| Série | Consommateur | Ce qui en dépend |
|---|---|---|
| `T_max_comp` | `indicateurs.py:114` | colonne **« Tmax comp (°C) »**, position 8 du tableau mensuel |
| `T_min_comp` | `indicateurs.py:115` | colonne **« Tmin comp (°C) »**, position 9 |
| `T_moy_comp` | `indicateurs.py:129` | cellule **« Tmm30j comp (°C) »**, position 11, ligne « Année » seule |
| les trois | `figures.py:1151`, `1163-1166` | **`Fig_Indicateurs_Resume.png`** — deux courbes en tirets (« Tmax compensée », « Tmin compensée »), gouvernées par le drapeau `has_comp` |
| les trois | `livrables.py:554-557` | classeur, feuille **`05_Indicateurs`** — `list(t.columns)`, **toutes** les colonnes |
| les trois | `livrables.py:255-260` | Word, tableau du §2.2 — **`[:6]`, donc AUCUNE des trois** (§3) |
| les trois | `livrables.py:252` | Word, §2.2 — la **figure** `indicateurs_resume`, qui les porte |
| les trois | `app.py:607-612` | écran, onglet « Indicateurs » : `st.dataframe(table)` et l'export CSV `indicateurs_thermiques.csv` |
| les trois | `build_reference.py:799-820` (harnais) | `07_t_norm.csv`, lignes `sortie_v45 = non` — hors verdict (D13) |

**Vérification d'exhaustivité.** Recherche sur `T_moy_comp`, `T_max_comp`,
`T_min_comp`, sur les trois libellés `« … comp (°C) »`, et sur les deux points
d'entrée `table_mensuelle` et `indicateurs_resume`, dans tout `app/`. Les
occurrences listées ci-dessus sont **les seules**. En particulier :

- **aucun score** ne les lit — `calcul_sgvt` (`core.py:894`) ne reçoit que
  `sens_res`, `vul_res`, `fraie_res` ;
- **aucun seuil**, **aucun débit de référence** ne les lit ;
- **`redaction.py` ne les lit nulle part** — ni les phrases d'interprétation,
  ni `ligne_synthese`, ni `COLONNES_SYNTHESE` (`redaction.py:464-570`) ;
- **`exports.py` ne les lit nulle part** ;
- **`climatique.py` ne les lit nulle part** ;
- les quatre corrélations de `indicateurs.py:157-175` portent sur
  `T_eau_moy`, l'amplitude et `T_air` **bruts**, jamais sur les séries
  compensées.

La famille compensation est donc **terminale** : elle est publiée, et rien
n'en découle.

---

## §2 — Le vocabulaire, et ce qui en est faux

### 2.1 Le constat

Les deux familles portent **le même mot**, et pas au même endroit.

`figures.py:91` étiquette `Tmh_norm` — famille **normalisation**, coefficient
`m`, anomalie lissée — « **Tmh — eau COMPENSÉE (année standard)** ». Le
tableau mensuel appelle `T_max_comp` — famille **compensation**, sans
coefficient, anomalie brute — « **Tmax comp (°C)** ». Le même mot désigne donc
deux formules différentes, sur deux écrans du même outil.

Ce n'est pas une maladresse isolée. Le mot est employé dans les deux sens
**dans le même fichier** :

| Emplacement | Texte | Ce qu'il désigne réellement |
|---|---|---|
| `app.py:108` | « Lissage de l'anomalie d'air pour **la compensation** (jours) » | le paramètre `normalisation_lissage_delta` — famille **normalisation** |
| `app.py:109` | « **La compensation** retranche **m × (anomalie d'air)** à la température de l'eau » | famille **normalisation** — la définition est exacte, le mot est faux |
| `app.py:604` | « **Compensé** = ramené aux conditions normales (écart aux normales 1991–2020 retiré) » | famille **compensation** — sans `m` |

**Le même écran donne deux définitions incompatibles du mot « compensé » :**
avec coefficient au réglage avancé, sans coefficient à l'onglet Indicateurs.
Un lecteur qui applique la première au second lira les colonnes « comp » comme
des températures normalisées. Elles ne le sont pas.

Le livrable Word porte la même contradiction, à deux sous-sections d'écart :

| Emplacement | Texte | Ce qu'il désigne |
|---|---|---|
| `livrables.py:212` | légende de `Fig0_Chronique` : « température de l'eau brute puis **compensée** » | `Tmh_norm` — normalisation |
| `livrables.py:220` | §1.5 : « **La normalisation climatique** retranche à la température observée l'anomalie de l'air **pondérée par le coefficient de sensibilité** » | la même courbe, nommée correctement |

### 2.2 Le relevé complet

**Famille normalisation** — 21 étiquettes.

| Emplacement | Étiquette | Verdict |
|---|---|---|
| `figures.py:87` | « Tmh — eau BRUTE (moy. mobile 7 j) » | juste (série brute) |
| `figures.py:91` | « Tmh — eau **COMPENSÉE** (année standard) » | **FAUX** — c'est `Tmh_norm` |
| `figures.py:94` | « Écart brut ↔ **compensé** » | **FAUX** — l'aire est `Tmh − Tmh_norm` |
| `figures.py:68-70` | commentaire : « on trace aussi l'eau **compensée** » | **FAUX** (commentaire) |
| `figures.py:253` | « Vulnérabilité Chronique — Tmh **normalisée** » | juste |
| `figures.py:264` | « Vulnérabilité Aiguë — Tmax **normalisée** » | juste |
| `figures.py:444` | « T° eau **normalisée** » | juste |
| `figures.py:479` | « T° eau **normalisée** (°C) » | juste |
| `figures.py:774`, `801` | « Tmh_norm > seuil » | juste (nom technique) |
| `figures.py:802` | « … stress systémique · Tmh **normalisée** » | juste |
| `figures.py:810`, `820` | « Tmax_norm > seuil » | juste |
| `figures.py:821` | « … létalité systémique · Tmax **normalisée** » | juste |
| `livrables.py:194` | « la **normalisation** climatique, dont dépend l'ensemble des indicateurs » | juste |
| `livrables.py:212` | « … eau brute puis **compensée** » | **FAUX** — légende de `Fig0_Chronique` |
| `livrables.py:215`, `220` | « cette **normalisation** » / « La **normalisation** climatique retranche … pondérée par le coefficient » | juste |
| `livrables.py:247`, `283` | « Températures **normalisées** » | juste |
| `exports.py:163` | « **non compensées** » (colonne des `%` de fraie bruts) | **FAUX** — l'opposé est `Tmh_norm_fraie`, une normalisation |
| `redaction.py:144`, `163`, `194`, `196`, `382`, `456` | « **normalisée** » / « **normalisation** » | juste |
| `app.py:90-91` | « (Tmh_norm) » / « (Tmax_norm) » | juste |
| `app.py:108-109` | « pour la **compensation** » / « **La compensation** retranche m × … » | **FAUX** — c'est la normalisation |
| `app.py:516` | « **températures normalisées** » | juste |
| `app.py:569` | « Températures brutes **non compensées** (information) » | **FAUX** — l'opposé est `Tmh_norm_fraie` |
| `app.py:573` | « sans **normalisation** climatique » | juste — et contredit `app.py:569`, **trois lignes plus haut**, dans le même bloc |
| `core.py:717` | docstring : « Températures attendues : **NORMALISÉES** (année standard) » | juste — mais « (année standard) » est aussi la glose de `figures.py:91` pour « compensée » |

**Famille compensation** — 9 étiquettes.

| Emplacement | Étiquette | Verdict |
|---|---|---|
| `indicateurs.py:2` | « Indicateurs thermiques bruts et **compensés** » | cohérent en interne |
| `indicateurs.py:9` | « Versions BRUTE et **COMPENSÉE** (écart aux normales, via Delta_TMm) » | cohérent, et **le seul endroit qui nomme la formule** |
| `indicateurs.py:60` | « bruts et **compensés** » | cohérent |
| `indicateurs.py:85` | commentaire : « T **compensée** = T − Delta_TMm (**ramenée à conditions normales**) » | la formule est juste ; « ramenée à conditions normales » est un **abus** — la ramenée n'est exacte que si `m = 1` |
| `indicateurs.py:114`, `115`, `129` | « Tmax **comp** (°C) », « Tmin **comp** (°C) », « Tmm30j **comp** (°C) » | cohérent en interne |
| `figures.py:1141` | docstring : « brutes et **compensées** » | cohérent |
| `figures.py:1164`, `1166` | « Tmax **compensée** », « Tmin **compensée** » | cohérent |
| `app.py:603` | « Indicateurs thermiques — bruts et **compensés** » | cohérent |
| `app.py:604` | « **Compensé** = ramené aux conditions normales » | même abus qu'`indicateurs.py:85` |

### 2.3 Le verdict

**Six étiquettes sont fausses**, toutes du même côté : elles appellent
« compensée » une série de la famille **normalisation**.

`figures.py:91` · `figures.py:94` · `figures.py:68-70` (commentaire) ·
`livrables.py:212` · `exports.py:163` · `app.py:108-109` · `app.py:569`

Aucune étiquette de la famille compensation n'appelle sa série
« normalisée » : l'erreur est **unidirectionnelle**. Le mot « compensée » a
été employé comme synonyme populaire de « normalisée » dans les textes
destinés au lecteur, pendant que le tableau mensuel s'en servait comme d'un
**nom technique** pour une autre formule. Les deux usages ne se sont jamais
rencontrés parce qu'ils vivent dans des onglets différents.

**Deux abus, distincts des six faux.** `indicateurs.py:85` et `app.py:604`
écrivent que la série compensée est « ramenée aux conditions normales ». La
soustraction de l'anomalie brute ne ramène aux conditions normales que si
l'eau suit l'air un pour un. Sur le corpus, le `m` estimé a une médiane de
**0,432** et un maximum de **0,562** : la « ramenée » corrige donc, en
médiane, **plus du double** de ce que la réponse mesurée du cours d'eau
justifie.

**Conséquence pour la spécification.** Quelle que soit la voie retenue au §4,
le vocabulaire doit être réparé — et il doit l'être **même si les colonnes
disparaissent**, puisque cinq des six étiquettes fausses ne portent pas sur
elles mais sur la famille normalisation. Le mot « compensé » ne peut pas
désigner deux formules ; la spécification retient que **« normalisée »
désigne la convention unique**, et que « compensée » ne subsiste que s'il
désigne encore quelque chose (§4, voie A → non ; voie B → non). Dans les deux
voies, le mot disparaît du vocabulaire de l'outil.

---

## §3 — Ce que le Word montre, aujourd'hui et après

`livrables.py:257` :

```python
cols = [c for c in t.columns][:6]
```

Le tableau du Word §2.2 ne prend que les **six premières colonnes** du tableau
mensuel. Les onze colonnes, dans leur ordre de construction (mesuré sur les
31 points qui produisent une table — `out/etape12/C3_colonnes_tableau_mensuel.csv`) :

| # | Colonne | Dans le Word ? | Famille |
|---|---|---|---|
| 1 | `Période` | **oui** | — |
| 2 | `Tmax (°C)` | **oui** | brute |
| 3 | `Tmax date` | **oui** | brute |
| 4 | `Tmin (°C)` | **oui** | brute |
| 5 | `Tmin date` | **oui** | brute |
| 6 | `Ampl. moy (°C)` | **oui** | amplitude |
| 7 | `Ampl. σ (°C)` | non | amplitude |
| 8 | `Tmax comp (°C)` | non | **compensation** |
| 9 | `Tmin comp (°C)` | non | **compensation** |
| 10 | `Tmm30j brut (°C)` | non | brute (ligne « Année » seule) |
| 11 | `Tmm30j comp (°C)` | non | **compensation** (ligne « Année » seule) |

**Aujourd'hui, le tableau du Word montre : Période, Tmax, Tmax date, Tmin,
Tmin date, Ampl. moy.** Aucune colonne compensée, et pas même l'écart-type de
l'amplitude ni le Tmm30j brut.

**Après, dans les deux voies : les mêmes six colonnes, aux mêmes valeurs.**

- Voie A — les colonnes 8, 9 et 11 changent de valeur ; elles ne sont pas dans
  les six premières ; **le tableau du Word est identique octet pour octet**.
- Voie B — les colonnes 8, 9 et 11 disparaissent ; les colonnes 1 à 6 ne
  bougent pas de rang ; **le tableau du Word est identique octet pour octet**.

**Mais le Word n'est pas identique pour autant.** `livrables.py:252` insère,
juste au-dessus de ce tableau, la figure `Fig_Indicateurs_Resume.png`, qui
porte les deux courbes compensées (`figures.py:1163-1166`). En voie A ces deux
courbes se déplacent ; en voie B elles disparaissent, `has_comp`
(`figures.py:1151`) devenant faux. **Le Word change par sa figure, jamais par
son tableau** — et c'est un piège de relecture : contrôler le livrable Word sur
son tableau conclurait « rien n'a bougé » dans les deux voies.

---

## §4 — La question de conception (C4), instruite et chiffrée

### 4.1 L'énoncé

La famille compensation alimente un tableau mensuel **publié**. Deux voies.

- **Voie A — les colonnes SUBSISTENT**, recalculées à la convention unique :
  `Tmax comp = max(T_eau_max − m × Delta_TMm_liss)`, et de même pour Tmin et
  Tmm30j. Le livrable garde sa forme, ses valeurs changent.
- **Voie B — les colonnes DISPARAISSENT.** Le livrable change de forme.

### 4.2 Voie A, chiffrée

Mesurée sans modifier `app/` : la chaîne est rejouée telle quelle, puis le
tableau mensuel est recalculé une seconde fois en substituant à `Delta_TMm` la
quantité `m × Delta_TMm_liss` — la seule colonne que `calcul_indicateurs` lit
pour bâtir la famille compensation (`indicateurs.py:86-90`). Méthode de
l'étape 6 : calculer les deux versions côte à côte plutôt que corriger puis
mesurer. Script `tests/reference/mesure_convention_unique.py`, sortie
`out/etape12/C4_valeurs_deplacees.csv`.

| | |
|---|---|
| points traités | **31** (+ 1 en échec, `BIE35-5__NA`, échec figé D7) |
| points portant les colonnes compensées | **31 / 31** |
| cellules publiées comparées | **777** |
| **cellules déplacées** | **777 — la totalité** |
| cellules apparues ou disparues | 0 |
| écart médian, en valeur absolue | **3,96 °C** |
| écart moyen, en valeur absolue | **3,89 °C** |
| **écart maximal** | **−11,68 °C** — `BCH5-7`, février, `Tmax comp` |
| cellules dont l'écart dépasse 1 °C | **690 / 777** |
| cellules dont l'écart dépasse 3 °C | **485 / 777** |
| points dont au moins une cellule bouge | **31 / 31** |

Répartition : 373 cellules sur `Tmax comp (°C)`, 373 sur `Tmin comp (°C)`,
31 sur `Tmm30j comp (°C)` (une par point, ligne « Année »).

**Aucune valeur ne survit.** Ce n'est pas un raffinement : c'est un tableau
publié dont chaque cellule d'une famille change, de plusieurs degrés en
médiane. La raison est arithmétique et n'a pas besoin des données : les deux
formules diffèrent de `(1 − m) × Delta_TMm_liss` plus l'effet du lissage, et
`m` vaut 0,432 en médiane sur le corpus — le terme retranché change donc de
plus de moitié.

**L'ampleur est maximale en hiver, pas en été.** L'écart extrême tombe en
février. C'est attendu et il faut le dire : `m` est estimé sur juin–septembre
(`core.py:520`) et appliqué toute l'année par le tableau mensuel, tandis que
les anomalies d'air sont les plus grandes hors saison. Voie A **étend à douze
mois un coefficient estimé sur quatre** — ce que la famille normalisation ne
fait nulle part ailleurs : `analyse_vulnerabilite` restreint sa lecture à
juin–septembre (`core.py:581`), et la fraie ré-estime son propre coefficient
sur sa propre fenêtre (`core.py:776`).

**Le cas du coefficient rejeté.** Un point du corpus, `BLE3-0`, a son `m`
rejeté par la règle de validité du correctif 6 : `m` appliqué **= 0**, `m`
estimé = −0,010. En voie A, ses colonnes compensées deviennent
`T − 0 × Delta_TMm_liss = T`. Vérifié cellule par cellule :

| Colonne | Voie A vs colonne brute voisine |
|---|---|
| `Tmin comp (°C)` | **identique sur les 6 lignes** |
| `Tmm30j comp (°C)` | **identique** — 11,48 des deux côtés |
| `Tmax comp (°C)` | identique sur **5 lignes sur 6** (Juin : 13,36 contre 13,37 — l'écart vient de ce que `Tmax (°C)` se lit sur l'infra-journalier, `Tmax comp` sur le maximum journalier agrégé) |

**Voie A publierait donc, pour ce point, trois colonnes intitulées
« compensées » qui sont la copie des colonnes brutes d'à côté.** Une colonne
dupliquée sous un autre nom est un énoncé faux : elle affirme qu'une
correction a été appliquée là où elle a été refusée. Un point sur 31
aujourd'hui ; la règle de validité peut en désigner d'autres sur un autre jeu.

### 4.3 Voie B, chiffrée

| | |
|---|---|
| **colonnes supprimées** | **3 par point** — positions 8, 9 et 11 sur 11 |
| valeurs publiées supprimées | **777** — les mêmes 777 |
| colonnes restantes | **8** : Période, Tmax, Tmax date, Tmin, Tmin date, Ampl. moy, Ampl. σ, Tmm30j brut |
| courbes supprimées de `Fig_Indicateurs_Resume.png` | **2** (`figures.py:1163-1166`), par `has_comp = False` |
| lignes de `07_t_norm.csv` supprimées | **3 × le nombre de journées exploitables** — toutes marquées `sortie_v45 = non`, donc **hors verdict** (D13) |

### 4.4 Ce que chaque voie fait au Word et au classeur

| Artefact | Voie A | Voie B |
|---|---|---|
| **Word §2.2, tableau** (`livrables.py:255-260`) | **inchangé** — les six premières colonnes ne portent aucune valeur compensée | **inchangé** — les six premières colonnes ne changent pas de rang |
| **Word §2.2, figure** (`livrables.py:252` → `figures.py:1138`) | **change** — deux courbes en tirets se déplacent, jusqu'à 11,68 °C | **change** — deux courbes en tirets disparaissent, la légende perd deux entrées |
| **Word §1.4, légende** (`livrables.py:212`) | à corriger (§2) — mais pour une raison indépendante de la voie | idem |
| **Classeur, feuille `05_Indicateurs`** (`livrables.py:554-557`) | **change** — 3 colonnes × 13 lignes × 31 points, 777 valeurs | **change de forme** — passe de 11 à 8 colonnes |
| **Classeur, autres feuilles** | inchangées | inchangées |
| **Écran, onglet Indicateurs** (`app.py:607`) | 777 valeurs changent | 3 colonnes disparaissent |
| **Export CSV `indicateurs_thermiques.csv`** (`app.py:609-612`) | 777 valeurs changent | l'en-tête perd 3 champs |
| **Les 66 artefacts du harnais** | **aucun ne bouge au verdict** ; `07_t_norm.csv` bouge sur ses seules lignes `sortie_v45 = non` (D13) | idem |
| **Scores, seuils, débits de référence, SGVT** | **aucun** | **aucun** |

**Le correctif 4 n'est vérifiable par aucun artefact du harnais.** C'est une
conséquence directe de §1.3 : la famille compensation ne vit pas dans
`res.df`, et les seules lignes qui la portent sont exclues du verdict par D13.
La prédiction falsifiable de ce correctif, quelle que soit la voie, est donc :
**66 artefacts sur 66 identiques au verdict, et `07_t_norm.csv` divergent
uniquement hors verdict.** Un mouvement ailleurs signifierait que la famille
compensation a un consommateur que §1.3 n'a pas trouvé — et il faudrait le
comprendre avant d'aller plus loin.

### 4.5 Ce qui départage — et ce qui ne départage pas

**Ce qui ne départage pas.**

- *« L'autre voie casserait un consommateur. »* Faux dans les deux sens :
  §1.3 établit qu'aucun score, seuil, débit ou composante SGVT ne lit la
  famille compensation. Les deux voies sont sans conséquence sur les verdicts
  publiés.
- *« Les colonnes ne sont lues nulle part. »* Faux. Elles ne sont pas dans le
  tableau du Word, mais elles sont dans **la figure du Word**, dans **le
  classeur**, sur **l'écran** et dans **l'export CSV**. Trois livrables sur
  quatre les portent.

**Ce qui plaide pour A.**

- Le livrable garde sa forme ; les lignes de plusieurs stations restent
  empilables, ce que la feuille `06_SYNTHESE` du classeur érige en principe
  (`livrables.py:572-576`).
- Un maximum et un minimum mensuels corrigés à la convention unique
  n'existent nulle part ailleurs : `analyse_vulnerabilite` ne publie que des
  comptages estivaux, pas des extrêmes mensuels.
- Le `Tmin` corrigé, en particulier, **n'a aucun équivalent** dans la famille
  normalisation, qui ne produit aucune série de minimum.

**Ce qui plaide pour B.**

- Voie A applique douze mois durant un coefficient estimé sur quatre — un
  usage que le reste de la chaîne s'interdit (§4.2).
- Voie A publie, pour tout point dont le coefficient est rejeté, des colonnes
  « compensées » identiques aux colonnes brutes (§4.2). Le libellé y devient
  faux.
- La famille compensation est terminale : rien n'en découle, et sa suppression
  ne coûte aucun indicateur.
- Le mot qui la nomme disparaît de toute façon (§2.3) : maintenir les colonnes
  oblige à leur trouver un nouveau nom, ce qui est un changement de forme du
  livrable **dans les deux voies**.

**Pourquoi je n'arbitre pas.** La mesure établit ce que chaque voie coûte ;
elle n'établit pas ce qu'un tableau mensuel doit montrer. Les deux voies
laissent tous les verdicts publiés intacts, ne cassent aucun consommateur, et
changent le même nombre de valeurs — 777. Ce qui les sépare est un jugement
sur **la forme d'un livrable publié**, qui appartient au commanditaire.

---

## §5 — Ce que la suppression retire d'information (C5)

Une anomalie brute non pondérée n'est pas dénuée de sens. Il faut donc dire ce
que la famille compensation porte **que la famille normalisation ne porte
pas**, et ce que la voie B retirerait pour de bon.

**Ce qu'elle porte en propre — trois choses, et une seule est de l'information
nouvelle.**

1. **Une couverture de douze mois.** La famille normalisation n'agrège rien
   hors de ses fenêtres : `analyse_vulnerabilite` lit juin–septembre
   (`core.py:581`), la fraie lit les mois de phase de l'espèce
   (`core.py:764`). Le tableau mensuel est **le seul endroit de l'outil où une
   température corrigée est publiée pour janvier, février ou novembre**.
2. **Un minimum corrigé.** `T_min_comp` (`indicateurs.py:90`) est la seule
   série corrigée bâtie sur `T_eau_min`. La famille normalisation ne produit
   ni `Tmin_norm` ni équivalent. La supprimer retire le seul minimum corrigé de
   l'outil.
3. **Une moyenne mobile de 30 jours corrigée.** `Tmm30j comp`
   (`indicateurs.py:129`, via `_tmm30j`) n'a d'équivalent ni dans la famille
   normalisation, ni ailleurs. Son pendant brut, `Tmm30j brut`
   (`indicateurs.py:127`), subsiste dans les deux voies.

**Ce qui, en revanche, n'est pas de l'information.** La question posée était :
un consommateur s'en sert-il pour autre chose que la duplication ? **Non.**
§1.3 établit que les trois séries sont terminales — aucun score, aucun seuil,
aucun débit, aucune phrase de rédaction ne les lit. Elles sont **regardées**,
jamais **utilisées**. Aucun raisonnement de la méthode ne s'appuie sur
l'anomalie brute non pondérée.

**Ce que la voie A ne préserve pas non plus.** Il faut le dire, parce que
« A conserve l'information et B la supprime » serait faux : la voie A retire
elle aussi l'anomalie brute, puisqu'elle la remplace par l'anomalie pondérée
et lissée. Ce que A conserve est la **forme** — trois colonnes aux mêmes
places, portant des grandeurs de même nature — et les trois propriétés 1, 2 et
3 ci-dessus, qui sont des propriétés du **périmètre** (douze mois, un minimum,
une moyenne mobile), pas de la formule.

**La seule information que B retire et que A conserve est donc le périmètre :
douze mois, un minimum, une moyenne mobile de trente jours.** L'anomalie brute
elle-même, en tant que quantité, est retirée par les deux.

**Une réserve, à ne pas taire.** L'anomalie brute retranchée sans coefficient
a une lecture défendable : elle est la **borne haute** de la correction
climatique, celle qu'on obtiendrait si l'eau suivait l'air un pour un. Publiée
à côté de la version pondérée, elle encadrerait la correction. Mais elle
n'est publiée à côté de rien — c'est la seule version publiée dans ce tableau
—, et aucun texte de l'outil ne la présente ainsi : `indicateurs.py:85` et
`app.py:604` la présentent au contraire comme la ramenée aux conditions
normales (§2.2), c'est-à-dire comme une estimation et non comme une borne.
**Une borne présentée comme une estimation n'est pas une information ; c'est
une erreur de lecture organisée.** C'est ce qui empêche de compter cette
lecture au crédit de la voie B.

---

## §6 — Les fichiers touchés, artefact par artefact (C6, typologie D63)

D63 demande d'abord *de quoi cet artefact est-il une fonction*, avant de
demander *ce que ce correctif change*.

### 6.1 Les fichiers de `app/`

| Fichier | Voie A | Voie B | Commun aux deux voies |
|---|---|---|---|
| `indicateurs.py` | `88-90` : `Delta_TMm` → `m × Delta_TMm_liss` ; `m` doit **entrer** dans la signature de `calcul_indicateurs` (il n'y est pas) | `88-90`, `113-115`, `128-129` : suppression | `2`, `9`, `60`, `85` : vocabulaire |
| `orchestrator.py` | `211` : passer `sens["m"]` à `calcul_indicateurs` | — | `209` : commentaire « bruts/compensés » |
| `figures.py` | — (les courbes suivent la table) | `1151`, `1162-1166` : suppression des deux tracés | `68-70`, `91`, `94` : vocabulaire ; `1141`, `1164`, `1166` : libellés |
| `livrables.py` | — | — (`[:6]` inchangé, `list(t.columns)` suit la table) | `212` : légende fausse |
| `exports.py` | — | — | `163` : « non compensées » |
| `app.py` | — | — | `108-109`, `569`, `603-604` : vocabulaire |

**`config.py` n'a besoin de rien**, et il vaut mieux le dire que d'y ajouter
un paramètre inutile : la voie retenue n'introduit aucun réglage.
`normalisation_lissage_delta` (`config.py:432`) existe déjà et sert déjà.

**Une dépendance que la voie A crée et que la voie B ne crée pas.**
`calcul_indicateurs(df, sub, verbose)` ne reçoit pas `m` aujourd'hui : la
famille compensation était précisément celle qui n'en avait pas besoin. La
voie A fait entrer le coefficient de sensibilité dans le module des
indicateurs, donc fait dépendre le tableau mensuel de la réussite de
`analyse_sensibilite`. La voie B l'en libère. Ce n'est pas un argument
décisif — `orchestrator.py:182` calcule `sens` avant `res.indicateurs` en
toute hypothèse —, mais c'est un couplage nouveau, et il se déclare.

### 6.2 Les artefacts du harnais, par type D63

| Artefact | Type D63 | Voie A | Voie B | Motif |
|---|---|---|---|---|
| `00_format_detecte.json` | métadonnées de lecture | **figé** | **figé** | dépend de `io_data`/`sniff`, en amont de tout indicateur |
| `01_colonnes_retenues.json` | métadonnées de lecture | **figé** | **figé** | idem |
| `02_effectifs.csv` | projection de `res.daily_eau_brut`, `res.df`, `res.rapport_qc` | **figé** | **figé** | aucune journée n'est ajoutée ni retirée |
| `03_journees_ecartees.csv` | projection de `rapport_qc` + `marques_fusion` | **figé** | **figé** | le correctif ne touche ni le QC ni la fusion |
| `04_normales.csv` | **projection** de `res.df` — les couples (jour, mois) **retenus** | **figé** | **figé** | motif contesté : l'artefact ne recopie pas la table des normales, il en projette les couples que la chronique retenue contient. Aucune journée n'étant retirée, la projection ne bouge pas |
| `05_anomalies.csv` | projection de `res.df` | **figé** | **figé** | porte `Delta_TMm` et `Delta_TMm_liss` **telles quelles** ; le correctif ne change pas l'anomalie, il change qui la pondère |
| `06_coefficients.csv` | **dépendance propre** — `res.sensibilite`, `journal.m_saisonnier`, `res.diag_normales` | **figé** | **figé** | `m` est une régression de l'eau brute sur l'air brut (`core.py:519-520`) ; aucune série corrigée n'y entre |
| `07_t_norm.csv` | projection de `res.df` **+ recalcul du harnais** | **bouge hors verdict** | **bouge hors verdict** | les 3 séries de la famille compensation y sont marquées `sortie_v45 = non` (`build_reference.py:799-820`) ; D13 les exclut du verdict |
| `08_scores.csv` | **dépendance propre** — `vulnerabilite`, `sgvt`, `fraie`, débits | **figé** | **figé** | §1.3 : aucune de ces grandeurs ne lit la famille compensation |
| `10_parametres.json` | métadonnées | **figé** | **figé** | aucun paramètre nouveau (§6.1) |
| `99_log.txt` | trace console | **figé** | **figé** | `indicateurs.py:177-179` n'imprime que `len(table)` et le nombre de corrélations exploitables — ni l'un ni l'autre ne change |

**Prédiction falsifiable du correctif 4, quelle que soit la voie :**
**65 artefacts figés au bit près sur 66**, le soixante-sixième étant
`07_t_norm.csv`, divergent **uniquement** sur des lignes `sortie_v45 = non`.
Si un autre artefact bouge, la recherche d'exhaustivité de §1.3 est fausse et
il faut comprendre où avant de poser quoi que ce soit.

### 6.3 Ce qui n'est pas dans le périmètre du correctif 4

- **La famille normalisation elle-même.** Sa formule *est* la convention ;
  elle ne bouge pas.
- **`Tmm30j` de `indicateurs.py:127` (brut).** Signalé hors chaîne depuis
  l'étape 10 (D53) ; il porte ses propres défauts de support et d'index. Le
  correctif 4 ne les corrige pas et ne les aggrave pas.
- **Le seuil de vingt jours de `core.py:657`** et le domaine `[0 ; 1,2]` :
  ils appartiennent au correctif 6, déjà posé.
- **Le fait que `m` estival soit estimé sur juin–septembre et appliqué toute
  l'année.** C'est un constat de §4.2, pas un défaut que ce correctif traite.
  Il devient une question **seulement en voie A**, qui l'étendrait à un
  livrable de douze mois.

---

## §7 — Résumé pour le commanditaire

1. Six séries, deux familles, un même mot pour les deux. **Six étiquettes sont
   fausses**, toutes dans le même sens.
2. La famille compensation est **terminale** : aucun score, seuil, débit ou
   composante SGVT ne la lit. Vérifié exhaustivement.
3. Le **tableau du Word ne la montre pas** aujourd'hui et ne la montrera pas
   après, dans les deux voies. La **figure du Word** la montre, et change dans
   les deux voies.
4. **Voie A : 777 valeurs publiées sur 777 changent**, écart médian 3,96 °C,
   maximum 11,68 °C. Sur le point dont le coefficient est rejeté, les colonnes
   deviennent la copie des colonnes brutes.
5. **Voie B : 3 colonnes sur 11 disparaissent**, les mêmes 777 valeurs avec
   elles. Le classeur passe de 11 à 8 colonnes.
6. **Aucune des deux voies ne casse un consommateur.** La question est celle de
   la forme d'un livrable publié. **Elle attend un arbitrage.**
7. Le vocabulaire, lui, est faux **indépendamment de la voie** et doit être
   réparé dans les deux cas.
