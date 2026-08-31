# Étape 20 — Correctif 13 : la fenêtre du détecteur, et le test de signe

Le correctif 13 est **posé** dans sa forme définitive : fenêtre étendue à l'année
entière (D105), second membre de la marche 1 en test de signe (D111, D115).

---

## §0 — Carnet de bord

| | |
|---|---|
| Code exécuté | `app/` (`THERMIE_CODE=app`) |
| Sources applicatives modifiées | **2 sur 16** — `qc.py`, `config.py` |
| Harnais modifié | `build_reference.py`, `parametres.py`, `comparer_chemins.py` |
| Spécification amendée | `docs/SPEC_detecteur_et_validite.md` |
| Règles scellées avant mesure | 4 — dont le test de signe et ses quatre prédictions |
| Journées marquées | **69 → 151** |

### Trois choses qui ont mal tourné, et ce que j'en ai fait

**1. Le contrôle d'intégrité s'appuyait sur un fichier destiné à être emporté.**
`verifier_aucune_pose.py` confrontait `app/` à l'exemplaire scellé dans
`out/livraison_etape17.zip`. Les archives de livraison sont retirées de `out/`
une fois remises : le témoin avait disparu, et le contrôle a échoué au premier
appel. Remplacé par `empreintes_app.py`, dont le relevé vit dans
`tests/reference/empreintes/`.

Le remplacement a mis au jour autre chose : **le contrôle couvrait 11 sources
sur 16.** Cinq modules — `run_cli.py`, `__init__.py`, `climatique.py`,
`print_style.py`, `sniff.py` — n'étaient sous la surveillance d'aucun témoin,
parce qu'ils ne figuraient pas dans l'archive. La nouvelle liste est
**découverte, pas déclarée**.

**2. Le script scellé de mesure lisait la mauvaise table.** Il cherchait les
journées nouvellement marquées dans `res.df` — d'où les journées marquées sont
précisément retirées. Les signaux A et B ont été calculés sur un ensemble vide,
et la console a imprimé « +0 nouvellement marquées » en face de « 69 → 232 ». La
contradiction est visible dans la trace livrée ; elle n'a pas été effacée.

Le fichier scellé **n'a pas été modifié** — son empreinte
`a93be1d7…` reste vérifiable. La reprise est un fichier distinct qui **copie les
deux seuils mot pour mot**. Un sceau garantit qu'un critère n'a pas été choisi
après coup ; il ne garantit pas qu'un script soit exempt de défaut.

**3. J'ai écrasé quatre artefacts de l'étape 19.** `eprouver_temoin.py` porte
son chemin de sortie **en dur** vers `out/etape19/`. L'étape 20 demandait de le
rejouer inchangé, même sceau — la bonne exigence : un témoin qu'on retouche
entre deux épreuves ne compare plus rien. Mais rejouer un script au chemin figé
le fait écrire dans l'étape précédente.

Réparé, et la réparation est vérifiée : `B_populations.csv` avait été copié
avant le rejeu, les trois autres fichiers en dérivent par filtres, et les
chiffres reconstruits sont confrontés à `99_console_epreuve.txt`, qui a survécu.
**Huit chiffres indépendants concordent** — τ = 0,205 %, 186 faux négatifs, 13
artefacts sur 6 339 journées de contrôle, 15 points. Les résultats d'étape 20
sont à l'abri dans `out/etape20/temoin/`.

*Le chemin en dur n'est pas corrigé* : le modifier romprait le sceau qui donne
sa valeur à la comparaison. Le danger est déclaré et la correction renvoyée à la
clôture.

---

## §1 — D44 et D76

**D76 — intégrité des références** (`out/etape20/F_integrite.txt`, retour 0) :

| | |
|---|---|
| `tests/reference` | 66 artefacts, 66 lignes au manifeste, **0 empreinte divergente** |
| `tests/reference_cli` | 66 artefacts, 66 lignes, **0 divergente** |
| bytecode sous `ref/` (D1, D77) | **0 fichier, 0 dossier** |

**D44 côté application : refusé, et c'est le comportement voulu.** D70 arrête la
comparaison — *« la référence a été produite par `ref`, le rejeu demandé est
`app` »*. La référence figée décrit V4.5 ; lui opposer le code corrigé n'a pas de
sens sans le déclarer.

**D44 côté référence** : retour 1, et les écarts sont ceux, déjà catalogués, que
le harnais a accumulés depuis l'étape 6 — colonnes `validite_*`, `m_estime`,
`n_mesures`. Aucune valeur ne bouge.

**Le contrôle décisif : le côté ref survit-il à ma pose ?** Rejeu `ref` de
maintenant contre celui de l'étape 16 :

| artefact | lignes différentes | valeurs différentes | colonnes ajoutées |
|---|---:|---:|---|
| 02, 04, 05, 06, 07, 08 | **0** | **0** | — |
| 03_journees_ecartees | **0** | **0** | `T_eau_ecart_median`, `motifs_complets`, `n_mesures` |

**Pas une valeur déplacée.** Les deux colonnes que j'ajoute restent vides côté
V4.5, qui ne produit pas de vue détaillée.

---

## §2 — La pose et ses artefacts

### Ce qui est posé

**Fenêtre.** `hors_eau_mois` passe de `(6, 7, 8, 9)` à l'année entière.

**Second membre de la marche 1** — `qc.ecart_a_la_mediane` :

```
marche 1 = (E_moy_rel > k)  ET  (T_eau_max − médiane_{mois}(T_eau_max) > 0)
```

Ce n'est pas un second détecteur. `E_moy = T_eau_max − T_air` est grand aussi
bien quand l'eau monte que quand l'air descend, et la marche 1 seule ne sait pas
lequel des deux termes a bougé. Le second membre répond à cette seule question.

**Zéro n'est pas un seuil** : c'est la frontière du phénomène. C'est pourquoi ce
membre ne divise pas par le MAD — il ne compare aucune magnitude — et pourquoi
le `plancher_dispersion` n'y est pas repris (D116) : il protège une division qui
n'a pas lieu, et la mesure a établi qu'il ne changeait aucune journée.

`k` reste à 3,0. Le code de détection de la marche 2 est inchangé au caractère
près.

### Les artefacts, déclarés puis constatés

| artefact | déclaré | constaté | |
|---|---|---|---|
| `00_format_detecte.json` | figé | **6 figés, 0 bouge** | ✅ |
| `01_colonnes_retenues.json` | figé | **6 figés, 0 bouge** | ✅ |
| `02_effectifs.csv` | doit bouger | 6 jeux | ✅ |
| `03_journees_ecartees.csv` | doit bouger | 6 jeux | ✅ |
| **`04_normales.csv`** | **devait rester figé** | **bouge sur 2 jeux** | ⚠ |
| `05_anomalies.csv` | doit bouger | 6 jeux | ✅ |
| `06_coefficients.csv` | doit bouger | 4 jeux | ✅ |
| `07_t_norm.csv` | doit bouger | 6 jeux | ✅ |
| `08_scores.csv` | peut bouger | 2 jeux | ✅ |
| `10_parametres.json` | peut bouger | 6 jeux | ✅ |
| `99_log.txt` | D80bis | +8 et +9 lignes | ✅ |

### `04_normales.csv` : la déclaration était fausse, pas le correctif

Il **bouge**, et il devait. `art_04` (`build_reference.py:782`) lit `res.df` et
en tire les couples `(jour, mois)` distincts : **c'est une projection de la
chronique retenue**, pas un artefact d'air. Il se range dans la même famille que
`05` et `07`, non dans celle de `00` et `01`. La normale elle-même ne dépend que
de l'air et n'a pas bougé d'un millième.

Cinq lignes se déplacent, **aucune valeur** :

| point | couple | mouvement | cause |
|---|---|---|---|
| ABI3-6 | (6, 1) | ajouté | 2011-06-01 cesse d'être marquée |
| LGV11-8 | (6, 1) | ajouté | 2011-06-01 cesse d'être marquée |
| HRI7-7 | (1, 6) | retiré | 2012-01-06 devient marquée |
| TAC16-4 | (12, 12) | retiré | 2015-12-12 devient marquée |
| La Moselle à Hielle | (11, 11) | retiré | 2022-11-11 devient marquée |

### Le compte

| | |
|---|---:|
| journées marquées avant | 69 |
| journées marquées après | **151** |
| sortent de l'analyse | 88 |
| **rentrent dans l'analyse** | **6** |

### Un défaut de comptage que je corrige à la source

La colonne `motif` de `03_journees_ecartees.csv` vient de la **vue héritée**, où
une journée ne porte que son **premier** motif. Compter les journées marquées en
filtrant cette colonne sous-estime celles qu'un détecteur antérieur avait déjà
touchées.

Sur l'état après pose : **150 par la vue héritée, 151 par la chaîne complète.**
La journée manquée est LA PLAINE 2011-05-24, dont le motif hérité est
« hors bornes ».

*Le compte de 69 publié aux étapes 18 et 19 n'en souffre pas* : la journée en
cause est en mai, hors de l'ancienne fenêtre, donc elle ne pouvait pas être
marquée alors. Je ne peux pas le re-vérifier sur l'artefact figé, qui ne porte
pas encore la colonne — je le déduis, et je le dis.

`03` gagne donc deux colonnes : `T_eau_ecart_median` (D57, la valeur de
diagnostic du nouveau membre) et `motifs_complets` (la chaîne entière). La vue
héritée est inchangée.

---

## §3 — Les six journées qui rentrent (D118)

`m_estival` n'est plus figé. Les six journées sont **toutes le 1ᵉʳ juin 2011**,
sur six points de la Bienne — la journée où l'air de LA_PESSE est descendu à
4,6 °C, sous le 5ᵉ centile de sa propre fenêtre.

| point | `m_estival` | Tmh_norm médiane | écart p95 |
|---|---|---|---:|
| ABI3-6 | 0,121790 → 0,120469 | 9,2632 → 9,2773 | −0,0005 |
| BIE10-8 | 0,369379 → 0,368707 | 7,6349 → 7,6357 | +0,0041 |
| BIE21-7 | 0,513132 → 0,512223 | 8,1135 → 8,1131 | +0,0006 |
| BIE27-9 | 0,550406 → 0,549087 | 8,8823 → 8,8798 | +0,0014 |
| BIE56-1 | 0,485750 → 0,484736 | 10,0647 → 10,0669 | −0,0035 |
| LGV11-8 | 0,341657 → 0,343728 | 11,6011 → 11,6649 | +0,0020 |

> **Aucun verdict ne bouge sur ces six points.** L'écart maximal sur `m_estival`
> est de **0,002**, sur le p95 de **0,004 °C**.

C'est le seul endroit où le correctif 13 pouvait dégrader ce que les étapes 18
et 19 ont validé. **Il ne le dégrade pas.**

---

## §4 — Le coefficient de fraie

Premier correctif du chantier à atteindre `m_saisonnier`. **Huit points sur 31**
bougent ; deux seulement de façon substantielle.

| point | espèce | `m_saisonnier` | écart | n | journées ajoutées |
|---|---|---|---:|---|---:|
| **SN 21069646 – La Canner à Vigy 1** | **brème** | 0,296513 → **0,411870** | **+0,115** | 326 → 306 | +20 |
| **Le ruisseau de la Flotte à Château-Voue** | **barbeau** | 0,536354 → **0,575136** | **+0,039** | 391 → 379 | +13 |
| BIE46-5 | ombre commun | 0,308050 → 0,310046 | +0,002 | 276 → 274 | +6 |
| BIE42-7 | ombre commun | 0,396897 → 0,397881 | +0,001 | 1014 → 1012 | +2 |
| BIE31-4 | ombre commun | 0,349267 → 0,350149 | +0,001 | 1003 → 1001 | +3 |
| BIE40-3 | ombre commun | 0,340274 → 0,339503 | −0,001 | 1107 → 1105 | +3 |
| BIE51-0 | ombre commun | 0,347278 → 0,347981 | +0,001 | 257 → 256 | +1 |
| BIE27-9 | ombre commun | 0,398332 → 0,398210 | −0,000 | 1048 → 1045 | +3 |

**La Canner gagne 39 % sur son coefficient de fraie** — le retrait de vingt
journées du bloc de pose de mai 2021, où la sonde lisait 19 à 23 °C hors de
l'eau pendant sa fenêtre de reproduction.

> **`P_fraie` ne bouge sur aucun point.**

**Gorze n'y figure pas**, et c'est instructif : son espèce repère est la truite
fario, dont la fraie court d'octobre à mars. Son bloc de mai, pourtant le plus
massif du corpus, **ne touche pas sa fenêtre de reproduction**. Le correctif le
retire de la chronique sans que l'indicateur de fraie s'en aperçoive.

---

## §5 — Le coût de la fuite (D117)

Quatorze journées de saison froide survivent au test de signe. **Une seule tombe
dans une fenêtre de fraie.**

| point | date | mois | espèce | fenêtre de fraie | dans la fenêtre |
|---|---|---:|---|---|---|
| BCH5-7 | 2012-02-03 | 2 | ombre commun | 3-4-5 | non |
| BIE10-8, BIE21-7, BIE31-4, BIE32-4, BIE40-3, BIE56-1 | 2012-10-27 | 10 | ombre commun | 3-4-5 | non |
| BIE46-5 | 12-09, 12-12, 12-17, 12-28 (2017) | 12 | ombre commun | 3-4-5 | non |
| HRI7-7 | 2012-01-06 | 1 | ombre commun | 3-4-5 | non |
| TAC16-4 | 2015-12-12 | 12 | ombre commun | 3-4-5 | non |
| **La Moselle à Hielle** | **2022-11-11** | 11 | **truite fario** | **1-2-3-10-11-12** | **OUI** |

**Les onze journées de « coup de froid marginal » ne touchent aucune fenêtre de
reproduction.** Elles sont retirées de l'analyse à tort, mais ce tort ne se
propage nulle part : la vulnérabilité estivale ne les voit pas, et la fraie de
l'ombre commun non plus.

La seule journée qui tombe dans une fenêtre de fraie est **La Moselle à Hielle
le 11 novembre 2022** — et c'est l'une des deux qui n'appartiennent pas à la
fuite au sens strict : eau à 21,86 °C, **4,63 °C au-dessus de sa médiane de
novembre**, air à 5,4 °C. Une vraie anomalie d'eau, que le test de signe retient
à juste titre.

**Le coût de la fuite dans l'indicateur de reproduction est donc nul.**

---

## §6 — Journal des verdicts (D43)

**Aucune catégorie ne bouge.** Sur 652 valeurs publiées, **17 bougent**, toutes
des effectifs :

| indicateur | points concernés | écart maximal |
|---|---:|---:|
| `n_jours_tmh` | 7 | 2 journées |
| `n_jours_tmax` | 6 | 1 journée |
| `pct_stress_chronique` | 4 | 0,467 point de % |

### Les trois points nommés

Leurs blocs de pose de mai 2021 **sont rattrapés** — c'était l'objet du
correctif — mais **rien ne bouge dans ce qu'ils publient** :

| point | espèce | `P_fraie` | aigu | chronique | SGVT |
|---|---|---|---|---|---|
| Le ruisseau de Gorze à Gorze | truite fario | 2,0 → 2,0 | 0 → 0 | 0,629 % → 0,629 % | 2,50 → 2,50 |
| SN 21069646 – La Canner à Vigy 1 | brème | 3,0 → 3,0 | 0 → 0 | 0 % → 0 % | 2,50 → 2,50 |
| Le ruisseau de la Flotte à Château-Voue | barbeau | 1,0 → 1,0 | 0 → 0 | 0 % → 0 % | 1,67 → 1,67 |

Trois raisons distinctes, qu'il faut nommer séparément :

- **Gorze** : sa fenêtre de fraie (octobre–mars) ne recoupe pas son bloc de mai.
- **La Canner** : son `m_saisonnier` bouge de 39 %, mais son `P_fraie` est
  **saturé à 3/3** et ne peut pas monter. *Qu'un indicateur ne bouge pas parce
  qu'il est saturé n'est pas la même chose que de ne pas être affecté.* Sur un
  point moins dégradé, les mêmes vingt journées auraient pesé.
- **La Flotte** : `m_saisonnier` bouge de 7 %, insuffisant pour franchir une
  borne de classe.

**Le correctif 13 ne déplace aucun verdict publié.** Il retire 88 journées, en
rend 6, déplace deux coefficients de fraie — et ne change pas une catégorie.

---

## §7 — Le témoin rejoué

`eprouver_temoin.py` et `temoin_regime.py` **inchangés, mêmes sceaux**
(`e78f370e…`, `ef98c126…`). Le témoin n'a pas changé ; la population qu'il juge,
si.

| | étape 19 | étape 20 |
|---|---:|---:|
| **τ** (témoin de contrôle) | 0,205 % | **0,135 %** |
| verdict de spécificité | SPÉCIFIQUE | **SPÉCIFIQUE** |
| journées marquées non instruites — corroborées | 42 j, **42,1 %** | 123 j, **60,2 %** |
| voisines d'une marquée | 15,3 % | 10,4 % |
| taux de fond, reste du corpus | 0,218 % | 0,113 % |
| **faux négatifs** | **186** | **131** |

Le détecteur marque **plus** de journées et une **fraction plus élevée** d'entre
elles est corroborée : 60,2 % contre 42,1 %. Il a gagné en portée et en
précision à la fois.

### Les faux négatifs, par point

| point | étape 19 | étape 20 |
|---|---:|---:|
| **LA PLAINE A RAON-SUR-PLAINE** | 16 | **3** |
| SN 21069646 – La Canner à Vigy 1 | 34 | 14 |
| Le ruisseau de Gorze à Gorze | 25 | 10 |
| Le ruisseau de la Flotte à Château-Voue | 15 | 9 |
| BIE6-8 | 65 | 65 |

Et les **trois journées qui restent sur LA PLAINE sont exactement les 2, 3 et
4 juin 2011** — celles que D106 a nommées, où l'air était chaud et où l'écart
eau–air s'est refermé sur l'artefact. Le correctif 13 ne les visait pas, ne les
a pas touchées, et les laisse désormais **seules et parfaitement isolées**.

BIE6-8 ne bouge pas : son anomalie de 2017 s'étend sur toute une saison, dans la
fenêtre estivale, et relève d'un autre phénomène.

---

## §8 — La clôture préparée

Ce qui reste ouvert, nommé et non corrigé.

**1. Le mécanisme de D106 est intact, et maintenant isolé.** Trois journées, sur
un point, identifiées au jour près : LA PLAINE, 2, 3 et 4 juin 2011. Deux
d'entre elles sont encore publiées comme journées de vulnérabilité aiguë. Le
corriger supposerait de promouvoir le témoin en détecteur, avec son propre cycle
de validation.

**2. L'écran ne nomme pas le second membre.** `redaction.py`, `livrables.py` et
`app.py` n'ont pas été touchés — la commande disait « rien d'autre ne change ».
Le second membre produit son état dans le dictionnaire de diagnostic et le
publie dans les artefacts, mais il n'atteint pas l'écran. **C'est un écart à
D100**, déclaré plutôt que réparé sans mandat, et c'est une ligne à écrire à la
clôture.

**3. `eprouver_temoin.py` écrit dans `out/etape19/` en dur.** À corriger quand
son sceau n'aura plus à servir.

**4. La contamination de la référence par l'artefact (D114)** reste déclarée et
transmise à l'aval. Sur une chronique de trois mois de mai, un bloc de 22 jours
pèse un quart du groupe mensuel et tire la médiane vers lui.

**5. `BIE35-5__NA` échoue toujours** (D7) : sa chronique ne contient aucun jour
de juin à septembre, donc aucun été à régresser.

**6. Les six couples (point, mois) où le second membre s'abstient** (D100),
tous pour effectif insuffisant :

| point | mois | journées | requis |
|---|---:|---:|---:|
| BLE3-0 | 5 | 7 | 10 |
| FLU8-4 | 12 | 2 | 10 |
| HRI7-7 | 4 | 5 | 10 |
| LGV11-8 | 4 | 4 | 10 |
| TAC16-4 | 3 | 4 | 10 |
| La Moselle à Hielle | 12 | 6 | 10 |

---

## Artefacts

Sous `out/etape20/`.

| fichier | contenu |
|---|---|
| `REGLE_SCELLEE.txt` | les quatre empreintes, prises avant chaque mesure, et leurs contre-vérifications |
| `rejeu_apres/` | les 66 artefacts après pose (6 jeux) |
| `rejeu_ref_controle/` | le rejeu côté V4.5, pour prouver qu'il survit |
| `A_*.csv` | la mesure avant pose (fenêtre nue) |
| `B_nouvelles.csv` | les 163 journées de l'extension nue, et leur corroboration |
| `S_69.csv`, `S_nouvelles.csv`, `S_nommees.csv`, `S_abstentions.csv` | le test de signe, avant pose |
| `R1_*.csv` | les six journées qui rentrent, et leur effet |
| `R2_m_saisonnier.csv` | le coefficient de fraie, par point et par espèce |
| `R3_fuite_fraie.csv` | le coût de la fuite |
| `R4_marquees.csv` | les 88 qui sortent, les 6 qui rentrent |
| `temoin/` | le témoin rejoué, et la sauvegarde qui a permis la réparation |
| `F_integrite.txt`, `D44_ref.txt` | les contrôles |
| `99_console_*.txt` | les traces intégrales |
