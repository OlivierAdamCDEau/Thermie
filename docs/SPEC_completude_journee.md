# SPEC — Le critère de complétude de journée (correctif 12, D86)

**Objet.** `io_data.marquer_lecture` produit, pour chaque journée,
`n_mesures=("T_eau", "size")`. **Ce nombre n'est relu nulle part** — recherche
exhaustive sur tout `app/`, une seule occurrence, celle qui le produit. Une
journée d'**une** mesure pèse donc autant qu'une journée de vingt-quatre dans
`T_eau_moy`, donc dans `Tmh`, donc dans `m`, donc dans `T_norm`.

Une asymétrie rend le défaut visible : l'amplitude nycthémérale, elle, **a** un
critère — `out.loc[out["n"] < 3, "ampl"] = np.nan`, `indicateurs.py`. Le même
projet exige trois mesures pour publier une amplitude et n'en exige aucune pour
publier une moyenne.

**Statut.** Spécification livrée à l'étape 15 ; le correctif est posé à
l'étape 16 (D86). Une question de conception reste ouverte au §4 : elle porte
sur ce qu'il faut faire des journées désignées, et cela n'appartient pas à la
mesure.

Toutes les mesures citées viennent de
`tests/reference/mesure_completude_journee.py`, sorties `out/etape15/P2_*`.

---

## §1 — Ce que la première mesure a établi, et pourquoi elle était fausse

**Il faut commencer par là, parce que le premier critère essayé était le
critère évident, et qu'il ne tient pas.**

La règle de décision avait été écrite **avant** les chiffres, en tête du script
(méthode de l'étape 3), et elle définissait une journée « maigre » comme une
journée portant **moins du quart de l'effectif attendu du point**, l'effectif
attendu étant dérivé du **pas de mesure modal** du point.

Résultat : **209 journées sur 68 134 (0,307 %)**. Et une concentration
anormale :

| Point | Journées maigres | Sur | Part |
|---|---|---|---|
| **`La Moselle à Hielle`** | **201** | 303 | **66,3 %** |
| 8 autres points | **1 chacun** | 1 164 à 5 007 | 0,02 à 0,09 % |

Un point portait **96 % de tout ce que le critère trouvait**. Sa distribution
d'effectifs le dit :

| `n_mesures` | Journées |
|---|---|
| 1 | 1 |
| 3 | 1 |
| **4** | **199** |
| 8 | 1 |
| 10 | 1 |
| **24** | **100** |

**Ce n'est pas une journée tronquée 199 fois. C'est une sonde qui a mesuré
toutes les six heures, puis toutes les heures.** Le « pas modal » de 60 minutes
ne décrit que la seconde moitié de la chronique ; rapporté à lui, un jour
parfaitement régulier à six heures paraît amputé des trois quarts.

**C'est exactement l'erreur que l'étape 1 avait corrigée** sur la matrice de
couverture : *« Un pas modal unique masque les changements de cadence en cours
de chronique »*, et la matrice déclarait alors « 15 min » et « 30 min » non
couverts alors que `jeu_bienne` porte des milliers d'intervalles de ce pas. La
parade retenue à l'étape 1 — porter la **distribution** des intervalles, jamais
un pas unique — n'avait pas été appliquée ici.

**Conséquence pour la spécification : un critère de complétude bâti sur
« fraction de l'effectif attendu » est faux par construction**, parce que
l'effectif attendu n'est pas une propriété du point mais de la **période**.

---

## §2 — Le critère qui ne dépend d'aucune cadence

La grandeur retenue est le **trou maximal de la journée** : le plus long
intervalle non observé, bornes de minuit comprises.

```
journée horaire régulière        → trou max  1 h
journée à six heures régulière   → trou max  6 h
quatre mesures groupées le matin → trou max ~18 h
```

Elle ne demande aucune cadence de référence : elle dit directement **ce que la
moyenne journalière ignore**. Une cadence plus large et une journée tronquée
cessent d'être confondues.

### 2.1 Le seuil, dérivé et non conventionné

> **Amendement d'étape 16 (D91) — le facteur opérant est 2×, non 4×.** Ce §2.1
> et le §2.2 gardent les chiffres de l'étape 15, où le facteur avait été
> **choisi** et non départagé. Le §4 porte la mesure aux trois facteurs et la
> décision. **Ne pas appliquer le 4× de ce paragraphe.**

Une journée est **trouée** si son trou maximal dépasse **quatre fois le trou
maximal médian de son propre point**. Le repère est donc la cadence ordinaire
du point lui-même, quelle qu'elle soit et qu'elle change ou non.

**Aucune valeur n'est importée.** Le facteur 4 est du même ordre que le
`n < 3` déjà présent dans `indicateurs.py` — trois mesures sur vingt-quatre —
mais il n'en est pas tiré : il est le seul nombre nouveau de ce critère, et
c'est lui que le §4 met en alternative.

Sur le corpus, le trou médian d'une journée ordinaire vaut **1,00 h sur les 31
points horaires**, donc un seuil de **4,00 h partout** — dérivé, pas fixé.

### 2.2 Ce que le critère désigne

| | |
|---|---|
| journées du corpus | **68 134** |
| **journées trouées** | **142  (0,208 %)** |
| points concernés | **29 sur 32** |
| part par point | de **0,08 %** à **1,56 %** — aucune concentration |
| trou maximal de ces journées | médiane **13,0 h**, maximum **24,0 h** |
| `n_mesures` de ces journées | de **1** à **26**, médiane **12** |

**La médiane de `n_mesures` vaut 12 sur 24.** Une journée trouée n'est donc pas
une journée pauvre en mesures : c'est une journée dont les mesures sont
**groupées**. Le critère d'effectif ne pouvait pas les voir.

### 2.3 Les deux critères ne mesurent pas la même chose

| | Journées |
|---|---|
| désignées par le **seul** critère d'effectif | **201** — dont **201** sur `La Moselle à Hielle` |
| désignées par le **seul** critère de trou | **134** |
| désignées par **les deux** | **8** |

**Huit journées en commun sur 343.** Le recouvrement est marginal, et tout ce
que le critère d'effectif ajoute est le changement de cadence d'un seul point.

### 2.4 Le témoin indépendant

Comparer les journées désignées aux autres sur `T_eau_moy` serait **circulaire**
— c'est la grandeur que le critère protège. Le témoin retenu lui est extérieur :
**l'écart de la journée à la moyenne de ses voisines calendaires** (J−1, J+1).

| | Écart absolu aux voisines, médiane des médianes par point |
|---|---|
| journées **trouées** | **0,5715 °C** |
| autres journées | **0,2185 °C** |
| **rapport** | **× 2,6** |

*Pour mémoire, le critère d'effectif donnait 0,3292 contre 0,2185, soit × 1,5 —
et ce contraste-là était porté par le changement de cadence d'un seul point.*

Sur les 142 journées trouées prises une à une : écart médian **0,472 °C**,
p95 **1,517 °C**, **maximum 3,131 °C**.

**Le critère de trou sépare ; le critère d'effectif séparait moins, et pour une
mauvaise raison.**

### 2.5 Le point que le critère ne peut pas juger, et il le dit

`BLE3-0` a un trou maximal **médian de 24,00 h** — sur toutes ses journées. Sa
colonne d'heure n'est pas reconnue (`io_data`, registre C2 / I13, D88) : ses
mesures sont toutes datées à minuit, et l'outil ne sait rien de leur
répartition dans la journée.

Son seuil dérivé vaut donc 96 h, et **aucune de ses 124 journées n'est
désignée**. Ce n'est pas un raté : c'est le comportement juste. Un critère
fondé sur les horodatages **ne peut pas juger un point dont les horodatages
sont détruits**, et il vaut mieux qu'il s'abstienne visiblement que de
prononcer un verdict sans fondement.

**C'est un lien direct entre le correctif 12 et D88** : tant que le n° 3 n'est
pas corrigé, `BLE3-0` reste hors de portée de ce critère, et cela doit être
déclaré à l'écran, pas déduit.

---

## §3 — L'aval : ce qui dépend des journées désignées

`T_eau_moy`, `T_eau_max` et `T_eau_min` d'une journée trouée entrent aujourd'hui
dans toute la chaîne, sans distinction :

| Consommateur | Ce qui en dépend |
|---|---|
| `core.fusionner_marque` → `Tmh` | moyenne mobile calendaire de 7 jours sur `T_eau_moy` |
| `core.analyse_sensibilite` | **`m`** — régression de `T_eau_moy` sur `T_air`, juin–septembre |
| `core.analyse_vulnerabilite` | `Tmh_norm`, `Tmax_norm` → `pct_chr`, `n_aigu` → SGVT |
| `core.analyse_fraie_croissance` | `Tmh_norm_fraie` → `P_fraie` |
| `core.analyse_debits_inflexion` | débits de référence |
| `indicateurs.calcul_indicateurs` | extrêmes mensuels, amplitude, `Tmm30j brut` |

**Le chiffre qui gouverne l'ampleur** : sur les 142 journées trouées,
**36 tombent entre juin et septembre** — la fenêtre où `m` est estimé. Les 106
autres n'atteignent `m` par aucun chemin.

Répartition mensuelle : avril **42**, octobre **28**, juin 16, mai 14,
juillet 14, décembre 7, janvier 6, novembre 5, septembre 4, mars 3, août 2,
février 1. **Les deux mois les plus touchés sont ceux des relevés de terrain
d'inter-saison** — avril et octobre —, ce qui est cohérent avec des journées de
maintenance de sonde plutôt qu'avec un aléa de mesure.

---

## §4 — La question de conception, en alternative fermée

La mesure établit **ce que le critère désigne**. Elle n'établit pas **ce qu'il
faut en faire**, et c'est une décision.

### Alternative 1 — Que fait-on des journées désignées ?

| Branche | **A — marquer sans exclure** | **B — exclure de la chaîne** | **C — exclure de la seule régression** |
|---|---|---|---|
| ce qui se passe | la journée reste, avec un statut et son trou | la journée sort de `res.df`, comme le contrôle qualité le fait | la journée reste partout sauf dans l'estimation de `m` |
| journées concernées | 142 | 142 | **36** |
| effet sur les valeurs publiées | **aucun** | `Tmh`, `m`, `T_norm`, SGVT, débits — à chiffrer à la pose | `m` seul, et tout ce qui en découle |
| cohérence avec le chantier | c'est la forme des correctifs 3, 5 et 10 : **nommer sans supprimer** | c'est la forme du contrôle qualité | forme nouvelle, sans précédent ici |
| ce que ça suppose | qu'une journée groupée reste une information | qu'une moyenne sur un tiers de journée n'est pas une moyenne journalière | que le défaut ne gêne que là où il biaise une pente |
| risque | l'écran signale, personne n'agit | 142 journées perdues sur un corpus où l'étape 7 a montré ce que coûtent des pertes concentrées | deux définitions de `T_eau_moy` coexistent selon l'usage |

**Ce qui les départage.** Si le critère est un **diagnostic**, c'est A — et
c'est la forme que le chantier a retenue trois fois (correctifs 3, 5, 10 :
marquer, compter, déclarer, ne rien supprimer). Si c'est un **contrôle
qualité**, c'est B — et il faut alors assumer qu'une journée dont on ignore
treize heures n'est pas une journée mesurée. C n'a aucun précédent dans le
chantier et ferait dépendre la définition d'une grandeur de son consommateur.

*Je ne tranche pas. Mais je signale que A est la seule branche dont l'effet est
connu d'avance — il est nul —, et que B et C demandent une mesure
supplémentaire avant la pose, pas après.*

### Alternative 2 — Le facteur 4

C'est le seul nombre nouveau du critère.

| Branche | **A — 4 × la médiane du point** | **B — 2 × la médiane** | **C — un seuil absolu en heures** |
|---|---|---|---|
| journées désignées | **142 (0,208 %)** | à chiffrer — nettement davantage | dépend de la valeur |
| dérivé du jeu traité | **oui** | oui | **non** — c'est une convention importée |
| effet sur `BLE3-0` | s'abstient (seuil 96 h) | s'abstient (48 h) | **le désignerait entièrement** |
| tenu par | la cadence du point | idem | rien |

**Ce qui les départage.** A et B sont des dérivations, C ne l'est pas — et D15
interdit d'importer un seuil. Entre A et B, la mesure donne un argument : à
4 × la médiane, le témoin indépendant sépare d'un facteur **2,6** ; à 2 ×, il
faudrait le vérifier, et rien ne dit qu'il séparerait autant. **Un seuil qui
désigne davantage n'est pas plus prudent s'il désigne des journées ordinaires.**

*La spécification retenait **A** — et c'était un argument plausible, non une
mesure.*

> **Amendement d'étape 16 (D91) — le facteur retenu est 2×, pas 4×.**
>
> D91 a refusé qu'un nombre soit choisi par argument dans un chantier qui a
> mesuré quinze étapes durant, et a fait calculer le témoin indépendant aux
> trois facteurs. Résultat :
>
> | Facteur | Journées | Part | Points | Séparation |
> |---|---|---|---|---|
> | **2×** | **145** | 0,213 % | **30** | **× 2,59** |
> | 3× | 143 | 0,210 % | 30 | × 2,59 |
> | 4× | 142 | 0,208 % | 29 | × 2,62 |
>
> **Les trois passent la règle** écrite avant les chiffres — séparation ≥ 2,0
> et part ≤ 1 %. La règle prévoyait ce cas : entre deux facteurs qui passent,
> on retient **le plus permissif**.
>
> **Et la raison profonde de leur ressemblance est structurelle :** sur les
> 68 134 journées du corpus, **aucune** n'a un trou maximal strictement compris
> entre 2 h et 4 h. La distribution est quantifiée — 96,1 % des journées ont
> exactement 1,0 h, puis 14 journées à 2,0 h, puis un saut direct à 6,0 h. Sur
> les 31 points horaires, les trois facteurs désignent **exactement le même
> ensemble**.
>
> **Le seul point que le facteur départage est `La Moselle à Hielle`**, dont le
> trou médian vaut 6,00 h — la sonde y a mesuré toutes les six heures pendant
> deux tiers de sa chronique. Le facteur y désigne 3 journées à 2×, 1 à 3×,
> **0 à 4×**. Et la raison en est décisive : **à 4×, son seuil vaudrait 24 h,
> soit la journée entière, que rien ne peut dépasser.** Le critère y
> deviendrait aveugle **par construction**, reproduisant sur un point
> parfaitement légitime la cécité que `BLE3-0` subit d'un vrai défaut
> d'horodatage.
>
> **Le facteur retenu est donc 2×**, et il l'est sur pièces : non parce qu'il
> désigne trois journées de plus, mais parce qu'un facteur plus large rend le
> critère inapplicable aux points de cadence large.

---

## §5 — Ce qu'il reste à mesurer avant la pose

> **Amendement d'étape 16 (D90) — ce que la branche B coûterait est mesuré.**
>
> D89 retient la branche A, mais D90 a fait chiffrer B avant de clore, au motif
> que le critère désigne des journées dont les mesures sont **groupées**, et
> que le caractère exploitable d'une journée groupée dépend de l'endroit où le
> groupe tombe dans le cycle nycthéméral — ce que le trou maximal ne mesure
> pas. Exclure sur cette base seule serait exclure sur un indicateur indirect.
>
> Mesuré en retirant les journées désignées de `propre` **avant** la fusion,
> c'est-à-dire exactement ce que B ferait. Réplication contrôlée identique sur
> les **31 points**.
>
> | | |
> |---|---|
> | \|Δ`m`\|, retrait de toutes les journées | médiane **0,000158**, p95 0,001174, **maximum 0,001436** (`GRO9-1`) |
> | \|Δ`m`\|, retrait des seules journées d'été | médiane 0,000188, **maximum 0,001436** |
> | Δ`Tmh_norm`, médiane par point | médiane **0,0003 °C**, maximum 0,0034 |
> | Δ`Tmh_norm`, maximum par point | médiane 0,2783 °C, **maximum 0,7303 °C** |
> | catégories de stress chronique qui basculent | **0** |
> | catégories de vulnérabilité aiguë qui basculent | **0** |
> | `n_jours_aigus` modifiés | **0** |
>
> **L'effet est négligeable, et la branche A est justifiée sur pièces.** Pour
> comparaison, le correctif 1 avait déplacé `m` jusqu'à **0,042** — trente fois
> davantage.
>
> **Un chiffre mérite d'être lu à l'envers** : le maximum de 0,7303 °C sur
> `Tmh_norm` ne tombe pas sur une journée désignée — celles-là sortent de la
> comparaison — mais sur ses **voisines**, dont la moyenne mobile calendaire de
> sept jours a perdu une valeur. **La branche B ne se contente pas de retirer
> des journées suspectes : elle perturbe celles qui les entourent.** La
> branche A n'en perturbe aucune.

### Ce que la spécification demandait, et qui est fait

1. **Si la branche B ou C de l'alternative 1 est retenue** : l'effet de
   l'exclusion sur `m`, `Tmh`, `T_norm`, le SGVT et les débits de référence,
   mesuré **avant** de poser. Les 36 journées estivales sont le sous-ensemble
   qui compte.
2. **Si la branche B de l'alternative 2 est envisagée** : le témoin indépendant
   à 2 × la médiane, pour savoir s'il sépare encore.
3. **Rien d'autre.** La branche A de l'alternative 1 ne demande aucune mesure
   supplémentaire : son effet sur les valeurs est nul par construction.

---

## §6 — Les fichiers touchés, en typologie D63

### 6.1 `app/`

| Fichier | Branche A | Branches B et C |
|---|---|---|
| `io_data.py` | `marquer_lecture` calcule le **trou maximal** par journée et le joint à `daily` ; `n_mesures` cesse d'être produit puis oublié | idem |
| `core.py` | — | `fusionner_marque` pose un statut et un motif sur les journées désignées, comme au correctif 5 |
| `orchestrator.py` | — | — |
| `qc.py` | — | à discuter : le critère est-il un détecteur du contrôle qualité, ou un marquage de lecture ? |
| `config.py` | **un paramètre** — le facteur, exposé et dérivé | idem |

**`config.py` bouge, et c'est la différence avec les correctifs 3, 5 et 10** :
ceux-là ne portaient aucune valeur réglable. Celui-ci introduit un critère, donc
un nombre, donc un champ de `QCConfig` et son widget — **dérivé du dataclass**,
correctif 7 oblige.

### 6.2 Les artefacts du harnais

| Artefact | Type D63 | Branche A | Branches B / C |
|---|---|---|---|
| `02_effectifs.csv` | **compte** | bouge — une colonne de compte s'ajoute | bouge |
| `03_journees_ecartees.csv` | projection | bouge — les journées désignées y entrent avec leur motif | bouge |
| `04_normales.csv` | projection de `res.df` | **figé** | **peut bouger** — si des journées sortent, des couples (jour, mois) peuvent disparaître (leçon de l'étape 10) |
| `05_anomalies.csv` | projection | **figé** | bouge — des lignes disparaissent |
| `06_coefficients.csv` | dépendance propre | **figé** | **bouge** — `m` est estimé sur moins de journées |
| `07_t_norm.csv` | projection | **figé** | bouge |
| `08_scores.csv` | dépendance propre | **figé** | bouge |
| `10_parametres.json` | métadonnée | **bouge** — le paramètre nouveau | bouge |
| `99_log.txt` | trace | **bouge** — le compte s'imprime | bouge |
| `00`, `01` | métadonnées de lecture | **figés** | figés |

**Prédiction falsifiable de la branche A** : `04`, `05`, `06`, `07`, `08`, `00`
et `01` **figés** ; `02`, `03`, `10` et `99` bougent, et **aucune valeur de
température, de coefficient ou de score ne change**. C'est la forme exacte des
correctifs 3, 5 et 10.

---

## §6 bis — Le texte de dégradation déclarée (C.3)

Rédigé ici, **non affiché** : D48 rassemble tout l'affichage à l'étape 17. Il
suit l'idiome des deux autres spécifications — toujours affiché, jamais durci
au franchissement d'un seuil, et énonçant ce qu'il **interdit** de conclure.

> **Complétude des journées de mesure.**
>
> Chaque journée de la chronique porte un *trou maximal* : le plus long
> intervalle pendant lequel la sonde n'a rien enregistré, les bornes de minuit
> comprises. Une journée mesurée toutes les heures a un trou d'une heure ; une
> journée mesurée toutes les six heures, de six heures ; une journée dont les
> mesures se groupent sur une demi-journée, de douze heures ou davantage.
>
> Sont **signalées** les journées dont le trou dépasse **deux fois le trou
> habituel de cette sonde**. Le repère est la sonde elle-même : le critère
> fonctionne à l'heure comme aux six heures, et survit à un changement de
> cadence en cours de chronique.
>
> **Ces journées ne sont pas écartées.** Elles entrent dans tous les calculs,
> comme avant. Le signalement dit seulement que leur moyenne journalière ne
> couvre pas le cycle jour-nuit, et qu'elle peut donc être décalée vers les
> heures effectivement mesurées.
>
> **Ce que ce signalement ne dit pas** : il ne dit pas qu'une journée signalée
> est fausse, ni qu'une journée non signalée est complète. Une journée dont les
> mesures sont régulièrement espacées mais rares est **non signalée** et
> pourtant pauvre ; une journée dense mais interrompue une demi-journée est
> **signalée** et pourtant fondée sur beaucoup de mesures.
>
> **Quand le critère ne peut pas se prononcer, il le dit.** Si toutes les
> mesures d'une sonde portent le même horodatage — cas d'un fichier dont la
> colonne d'heure n'a pas été reconnue —, l'outil ne sait rien de la
> répartition des mesures dans la journée. Le critère **s'abstient** et
> l'affiche : *« structure infra-journalière illisible — le critère de
> complétude ne peut rien voir »*. **Une absence de signalement ne vaut alors
> pas quitus** ; elle signifie que personne n'a pu regarder.

---

## §6 ter — L'asymétrie avec l'amplitude (C.4)

`indicateurs._amplitude_journaliere` masque l'amplitude d'une journée portant
**moins de trois mesures** (`out.loc[out["n"] < 3, "ampl"] = np.nan`). Le
critère de complétude, lui, ne regarde pas l'effectif. **Faut-il unifier les
deux ?**

**Non : ils répondent à deux questions distinctes, et le code le montre.**

- `n < 3` protège une **étendue** — `max − min`. Avec deux points on obtient une
  corde, pas une amplitude ; c'est une condition d'**existence** de la
  statistique.
- Le trou maximal protège une **localisation** — la moyenne journalière. Il
  demande si la journée **couvre le cycle**, ce qui n'a rien à voir avec le
  nombre de points.

**Mais la mesure ajoute un fait qui ne se déduit pas de cette distinction :**

| | |
|---|---|
| journées désignées par le critère de trou | **145** |
| dont `n_mesures ≥ 3` — **l'amplitude est publiée** | **141** |
| dont `n_mesures < 3` — l'amplitude est déjà masquée | **4** |

**141 journées publient aujourd'hui une amplitude nycthémérale calculée sur des
mesures groupées sur une partie de la journée.** Une amplitude jour-nuit qui
ignore la nuit n'est pas une amplitude nycthémérale : le critère `n < 3` est
donc le plus faible des deux **pour son propre objet**.

**Conclusion.** Les deux critères ne s'unifient pas — l'un conditionne
l'existence, l'autre la représentativité —, mais le critère de trou
**améliorerait** `indicateurs.py` s'il y était appliqué en plus de `n < 3`.

**Rien n'a été posé sur `indicateurs.py`.** Ce module est en aval de `T_norm`,
donc hors du périmètre du mandat, et le dire sans le faire est ce que la
commande demandait. C'est une entrée pour le chantier aval, à ranger avec D87
et D88.

---

## §7 — Résumé pour le commanditaire

1. Le critère évident — « trop peu de mesures » — **est faux** : il confond une
   cadence plus large avec une journée tronquée, et 96 % de ce qu'il trouvait
   sur ce corpus était le changement de cadence d'un seul point.
2. Le critère retenu est le **trou maximal de la journée**, qui ne dépend
   d'aucune cadence de référence.
3. Il désigne **142 journées sur 68 134 (0,208 %)**, réparties sur **29 points**,
   dont **36 en juin–septembre**.
4. Ces journées se distinguent des autres d'un **facteur 2,6** sur un témoin
   indépendant du critère.
5. `BLE3-0` reste **hors de portée** du critère tant que ses horodatages ne sont
   pas réparés (D88), et le critère s'en abstient visiblement.
6. ~~**Deux décisions attendent un arbitrage**~~ — **tranchées à l'étape 16.**
   D89 retient **marquer sans exclure** ; D91 fait départager le facteur sur
   pièces, et la mesure retient **2×**, parce qu'un facteur plus large rend le
   critère inapplicable aux sondes de cadence large.
7. **Ce que la branche B aurait coûté est mesuré** et non supposé :
   \|Δ`m`\| ≤ 0,0014, **aucun verdict ne bascule**, et l'exclusion perturberait
   les journées **voisines** de celles qu'elle retire jusqu'à 0,73 °C.
8. **141 des 145 journées désignées publient aujourd'hui une amplitude
   nycthémérale** calculée sur des mesures groupées. Signalé, non corrigé :
   `indicateurs.py` est en aval de `T_norm`.
