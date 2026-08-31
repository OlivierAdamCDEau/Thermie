# Conventions de calcul de l'outil V4.5 (`thermie_debits`)

Document de référence établi par **lecture seule** du package décompressé dans
`data/ref_V4_5/thermie_debits/`. Aucun fichier du référentiel n'a été modifié ni
exécuté. Toutes les références sont données sous la forme `fichier.py:ligne`.

Objet : figer noir sur blanc la chaîne de normalisation de V4.5, afin que le
nouvel outil (`thermie_points`) produise des valeurs **identiques** sur les
mêmes entrées, et qu'aucune contradiction n'apparaisse entre les deux livrables
remis au maître d'ouvrage.

Version du référentiel : `data/ref_V4_5/VERSION.txt` = **4.5**.

---

## 1. Vue d'ensemble de la chaîne

```
fichier sonde --charger_eau--------> daily (T_eau_moy/max/min, n_mesures)
                                 \-> sub   (datetime, date, T_eau)

fichier air ---charger_air_brut---> df_air (date, T_air, [RR])
                     |
                     \-calculer_normales_ecarts-> normale(jour calendaire)
                                                  Delta_TMm = T_air - normale

daily + df_air --controle_qualite--> daily_propre
daily_propre + df_air + Delta_TMm --fusionner--> df
                                     |- Tmh            = moy. mobile 7 j de T_eau_moy
                                     \- Delta_TMm_liss = moy. mobile 7 j de Delta_TMm

df (juin-sept.) --analyse_sensibilite--> m = pente OLS de T_eau_moy ~ T_air

df + m --analyse_vulnerabilite--> Tmh_norm  = Tmh       - m x Delta_TMm_liss
                                  Tmax_norm = T_eau_max - m x Delta_TMm_liss
```

---

## 2. Lecture des fichiers

### 2.1 Détection de format — `sniff.py`

| Élément | Valeur | Référence |
|---|---|---|
| Encodages testés, dans l'ordre | `utf-8-sig`, `utf-8`, `latin-1`, `cp1252` ; repli `utf-8` avec `errors="replace"` | `sniff.py:19`, `sniff.py:148-154` |
| Séparateurs testés | point-virgule, virgule, tabulation, barre verticale | `sniff.py:20` |
| Choix du séparateur | celui qui donne le nombre de colonnes le plus **régulier** (mode le plus fréquent sur 40 lignes), puis à égalité le plus grand nombre de colonnes ; **pas** `csv.Sniffer` | `sniff.py:35-66` |
| Détection Excel | par extension `.xls` / `.xlsx` / `.xlsm` ; moteur `xlrd` pour `.xls`, `openpyxl` sinon | `sniff.py:69-72`, `sniff.py:126` |
| Feuille Excel retenue | la feuille demandée si elle existe, **sinon la première** | `sniff.py:129` |
| Ligne d'en-tête | balayage des 15 premières lignes, score = nb de cellules contenant un mot du vocabulaire date/température, avec exclusion des lignes à plus de 50 % de valeurs purement numériques ; **0 par défaut** | `sniff.py:90-106` |
| Vocabulaire date | `date, heure, time, timestamp, horodat, jour, aaaammjj, aaaa, datetime, cet, cest, gmt` | `sniff.py:22-23` |
| Vocabulaire température | `temp, °c, degr, tw, t_eau, teau, water, eau, valeur, value, tm, t (, t(, , °c, temp,` | `sniff.py:24-25` |
| Choix de la colonne valeur | premier candidat du vocabulaire dont plus de 50 % des valeurs sont numériques après remplacement virgule vers point ; à défaut, le premier candidat quel qu'il soit | `sniff.py:179-186` |

### 2.2 Chronique d'eau — `charger_eau` (`io_data.py:34-101`)

- **Colonne date** : premier nom contenant `date/heure/time/timestamp/horodat` dont
  le premier échantillon non nul fait plus de 8 caractères ; à défaut, le premier
  candidat (`io_data.py:54-63`).
- **Parsing des dates** (`_parse_dates_sonde`, `io_data.py:16-31`) : essai des
  formats `%d/%m/%Y %H:%M`, `%d/%m/%Y %H:%M:%S`, `%d/%m/%Y`, `%Y-%m-%d %H:%M:%S`,
  `%Y-%m-%dT%H:%M:%S`, `%Y-%m-%d`, et **conservation du format qui produit le plus
  de dates valides** ; repli `format="mixed", dayfirst=True` seulement si aucun
  format ne produit une seule date valide. Convention explicite : les formats
  jour/mois sont testés **avant** le repli, pour éviter l'inversion jour/mois sur
  les dates ambiguës (`io_data.py:18-20`).
- **Colonne heure séparée** : si une colonne dont le nom commence par `heure`
  existe et que **toutes** les heures parsées valent 00:00, cette colonne est
  ajoutée comme `Timedelta` (`io_data.py:72-82`). Une valeur d'heure non
  reconnaissable est silencieusement remplacée par `Timedelta(0)`
  (`io_data.py:80-81`) — voir §9, point I7. La colonne n'est de surcroît
  reconnue que si son nom **commence** par « heure », et non s'il le contient :
  voir §9, point I13.
- **Température** : conversion en texte, suppression des espaces, virgule
  remplacée par point, `to_numeric(errors="coerce")` (`io_data.py:86-88`).
- **Jour civil** : `date = datetime.dt.date` (`io_data.py:89`), donc en heure
  locale du fichier, sans décalage ni fuseau. Les lignes sans date **ou** sans
  température sont supprimées (`io_data.py:90`).
- **Agrégat journalier** (`io_data.py:92-96`) :
  - `T_eau_moy` = moyenne **arithmétique non pondérée** de toutes les mesures du jour ;
  - `T_eau_max`, `T_eau_min` = max/min des mesures du jour ;
  - `n_mesures` = nombre de mesures du jour.

  **Aucun seuil minimal de mesures** n'est imposé : un jour à une seule mesure
  produit une moyenne journalière au même titre qu'un jour à 48 mesures.
- **Retour infra-journalier** (`retour_sous_quotidien=True`, `io_data.py:98-100`) :
  `sub` = `[datetime, date, T_eau]`, sans dédoublonnage des horodatages.

### 2.3 Chronique d'air — deux loaders coexistants

| | `charger_air` (`io_data.py:104-118`) | `charger_air_brut` (`io_data.py:316-346`) |
|---|---|---|
| Séparateur | point-virgule **codé en dur** | auto-détecté (`sniff`) |
| Encodage | défaut pandas | auto-détecté (`sniff`) |
| Colonne date | `AAAAMMJJ` obligatoire | `AAAAMMJJ` sinon vocabulaire |
| Colonne temp. | `TM` obligatoire | `TM` sinon vocabulaire |
| `RR` conservé | oui si présent | oui si présent |
| `TN` / `TX` | **jamais lus** | **jamais lus** |

Dans les deux cas la sortie est `[date, T_air, (RR)]` : **V4.5 n'utilise que la
moyenne journalière `TM`**. Les minimales et maximales journalières `TN`/`TX`,
même présentes dans le fichier source, sont écartées à la lecture. Le fichier
d'exemple du référentiel (`data/ref_V4_5/examples/air.csv`) ne contient
d'ailleurs que les colonnes `AAAAMMJJ`, `TM`, `RR`.

---

## 3. Normales 1991-2020 et anomalie d'air `Delta_TMm`

**Deux voies mutuellement exclusives** cohabitent, arbitrées dans
`orchestrator.py:95-107` : si un fichier `EcartNormales` pré-calculé est fourni,
c'est lui qui prime ; sinon les normales sont recalculées depuis l'air brut.

### 3.1 Voie A — normales pré-calculées, `charger_normales` (`io_data.py:121-144`)

- Lecture : `sep=None` (sniffer pandas), `encoding="latin-1"` (`io_data.py:128-129`).
- Colonnes attendues : `Date` (`%d/%m/%Y`), `TMm`, `TM`, `Delta_TMm` — décimale
  virgule convertie (`io_data.py:130-134`).
- `Delta_TMm` est **repris tel quel du fichier**, jamais recalculé : la
  définition de la normale sous-jacente est externe à l'outil.
- `normales_lkp` = moyenne de `TMm` par couple (jour, mois), **sans aucun
  lissage** (`io_data.py:140-142`).

### 3.2 Voie B — normales recalculées, `calculer_normales_ecarts` (`io_data.py:349-412`)

Période de référence : **1991-2020**, constante `REF_NORMALES` (`io_data.py:298`),
sélection `year >= 1991 & year <= 2020` (`io_data.py:365`).

1. **Normale brute par jour de l'année** : moyenne de `T_air` groupée par
   `dayofyear`, sur les seules années de référence (`io_data.py:385`).
2. **Complétion** : réindexation sur 1..366 puis
   `interpolate(limit_direction="both")` — les jours de l'année absents des
   données de référence sont **interpolés linéairement** (`io_data.py:386-388`).
3. **Lissage circulaire** : fenêtre `w = 2 x fenetre_lissage + 1` soit
   **21 jours** par défaut (`fenetre_lissage = 10`, `io_data.py:349` et
   `config.py:385`). La série est triplée bout à bout, lissée par
   `rolling(window=21, center=True, min_periods=1).mean()`, puis on ne conserve
   que le tiers central — c'est ce triplement qui rend le lissage circulaire et
   évite l'effet de bord au 1er janvier (`io_data.py:389-392`).
4. **Table de correspondance** : la normale lissée est reportée sur le calendrier
   de l'an **2000** (année bissextile, 366 jours) et indexée par (jour, mois)
   (`io_data.py:395-401`).
5. **Anomalie** : jointure sur (jour, mois) puis
   **`Delta_TMm = T_air - T_normale`** (`io_data.py:403-404`), calculée pour
   **tous** les jours observés, y compris hors 1991-2020 (`io_data.py:405`).
6. **Garde-fous** : erreur si aucune année de référence (`io_data.py:374-377`) ;
   simple avertissement si moins de `min_annees = 20` années disponibles sur
   1991-2020 (`io_data.py:378-383`, `config.py:386`).

> **Convention à retenir pour le nouvel outil** : la normale d'un jour calendaire
> est la moyenne inter-annuelle 1991-2020 de ce jour de l'année, **lissée sur
> ±10 jours de façon circulaire**, et non la moyenne brute du jour.

---

## 4. Lissages et fusion — `fusionner` (`core.py:75-110`)

| Grandeur | Formule exacte | Référence |
|---|---|---|
| Jointure eau x air | `merge(..., how="inner")` — un jour sans air est **supprimé de l'analyse** | `core.py:85` |
| Jointure x anomalie | `merge(ecart_by_date, how="left")` — `Delta_TMm` peut rester `NaN` | `core.py:86` |
| `T_air_std` | `T_air - Delta_TMm` (= la normale, par construction) | `core.py:91` |
| **`Tmh`** | `T_eau_moy.rolling(window=7, min_periods=4, center=True).mean()` | `core.py:93-94` |
| **`Delta_TMm_liss`** | `Delta_TMm.rolling(window=7, min_periods=1, center=True).mean()` | `core.py:102-104` |

Fenêtre de lissage de l'anomalie : `lissage_delta = 7` par défaut
(`core.py:76`), piloté par `normalisation_lissage_delta = 7` (`config.py:391`).

**Justification consignée dans le référentiel** (`core.py:95-101`) : la
normalisation retranche `m x anomalie` à une température de l'eau déjà moyennée
sur 7 jours ; soustraire une anomalie journalière bruitée d'un signal
hebdomadaire injecterait du bruit sans fondement physique, l'eau répondant à
l'air avec inertie. Les deux échelles de temps sont donc alignées. La
documentation précise que « la moyenne de la série est inchangée ».

---

## 5. Sensibilité et formule de normalisation

### 5.1 Coefficient de sensibilité `m` — `analyse_sensibilite` (`core.py:116-148`)

- **Fenêtre** : mois 6, 7, 8, 9 (juin-septembre), lignes avec `T_eau_moy` et
  `T_air` renseignés (`core.py:117`).
- **Effectif minimal** : 10 jours, sinon `ValueError` (`core.py:118-125`).
- **Variables** : `x = T_air` (journalier brut), `y = T_eau_moy` (journalier brut).
  Ni l'un ni l'autre n'est lissé (`core.py:126`).
- **`m` = pente de la régression linéaire OLS** `stats.linregress(T_air, T_eau_moy)`,
  `r2 = r_value au carré` (`core.py:136-137`).
- Tests de Shapiro sur x et y, puis Pearson **ou** Spearman selon normalité
  (`core.py:128-134`) : ces tests ne servent qu'à la **corrélation reportée**
  (`r_main`, `p_main`) et à la qualification ; **la pente `m` reste dans tous les
  cas la pente OLS**.
- `robustesse = |r_spearman - r_pearson|` (`core.py:138`).

### 5.2 Formule de normalisation — `analyse_vulnerabilite` (`core.py:156-175`)

Le delta employé est `Delta_TMm_liss` **s'il existe**, `Delta_TMm` sinon
(`core.py:157-158`) :

```
Tmh_norm  = Tmh       - m x Delta_TMm_liss      (core.py:159)
Tmax_norm = T_eau_max - m x Delta_TMm_liss      (core.py:160)
```

Lecture : on retire de la température observée la part attribuable à l'anomalie
d'air de la période, convertie en degrés d'eau par le coefficient de couplage
`m`. Le résultat est la température qu'aurait eue le cours d'eau sous une année
climatiquement normale.

Fenêtre d'exploitation : juin-septembre (`core.py:161`) ; les taux de
dépassement se calculent sur les lignes non nulles de la colonne concernée
(`core.py:164-168`).

### 5.3 Variante fraie-croissance (`core.py:225-247`, `core.py:326-329`)

Sur les fenêtres de reproduction, `m` est **recalculé** sur les mois de l'espèce
(`_m_saisonnier`) avec trois garde-fous cumulatifs, tous conduisant au repli sur
le `m` estival : `n < 20` (`core.py:233`), `R2 < 0,30`, ou pente hors `[0 ; 1,2]`
(`core.py:239`). La formule reste de même forme :
`Tmh_norm_fraie = Tmh - m_saison x Delta_TMm_liss` (`core.py:329`).

---

## 6. Contrôle qualité — `qc.py` (référence, non appliqué à l'étape 1)

Ordre d'application, chaque exclusion étant tracée avec son motif ; un
enregistrement déjà signalé conserve le **premier** motif rencontré
(`qc.py:32-36`) :

1. **Bornes physiques** (`qc.py:41-44`) :
   `T_eau_moy < -0,5` **ou** `T_eau_moy > 35` **ou** `T_eau_max > 35`.
   Bornes : `t_eau_min = -0,5 °C` (`config.py:72`), `t_eau_max = 35,0 °C`
   (`config.py:73`).
2. **Plateau / sonde bloquée** (`qc.py:48-56`) : écart-type glissant sur 7 jours
   (`min_periods = 7`, centré) inférieur à `0,05 °C` (`config.py:84-85`).
3. **Sonde hors d'eau** (`qc.py:60-82`) : sur juin-septembre, un jour est suspect
   si `T_eau_max - T_air > 4 °C` ; si une année compte au moins 5 jours suspects,
   **toute la saison JJAS de cette année est exclue** (`config.py:77-80`).
4. **Outliers MAD** (`qc.py:85-99`) : `|T_eau_moy - médiane| > 50 x MAD`
   (`config.py:89`), détecteur volontairement très large.

**Aucun de ces traitements n'est appliqué à l'étape 1.** Les seuils sont
rappelés ici uniquement pour que les signaux d'alerte de l'inventaire soient
lisibles au regard de ce que V4.5 écarterait.

---

## 7. Détection du pas et des lacunes — `core.py:833-907`

| Élément | Convention V4.5 | Référence |
|---|---|---|
| Pas d'échantillonnage | **médiane** des écarts entre horodatages **triés et dédoublonnés** | `core.py:838-842` |
| Repli si moins de 3 horodatages | `Timedelta(days=1)` — valeur par défaut silencieuse | `core.py:839-840` |
| Définition d'une lacune | écart supérieur à `seuil_pas x pas médian`, avec `seuil_pas = 3` par défaut | `core.py:848-849`, `core.py:885-886` |
| Usage | insertion de lignes `NaN` au milieu du trou pour ne pas relier les points de part et d'autre (`inserer_lacunes`), ou découpage en segments (`segments_valides`) | `core.py:848-907` |

> Note : ce seuil « 3 x pas médian » est un seuil **de tracé**, pas un seuil
> d'analyse. Le critère « interruption supérieure à 1 jour » demandé pour
> l'inventaire est donc un critère différent, et volontairement plus lisible pour
> le maître d'ouvrage ; les deux ne doivent pas être confondus.

---

## 8. Indicateurs — `indicateurs.py` (référence, non appliqué à l'étape 1)

- **Amplitude nycthémérale journalière** = `max - min` des mesures
  infra-journalières du jour, **mise à `NaN` si le jour compte moins de
  3 mesures** (`indicateurs.py:26-39`, seuil ligne 37).
- **Tmm30j** = maximum de la moyenne mobile 30 jours, `min_periods = 25`
  (`indicateurs.py:50-55`).
- **Extrema horodatés** = `idxmax`/`idxmin` sur la série infra-journalière
  (`indicateurs.py:42-47`).
- **Température « compensée »** : `T - Delta_TMm` (`indicateurs.py:85-90`).
- Corrélations : régression sur `log(Q)` pour les deux corrélations à débit en
  abscisse (`indicateurs.py:135-155`).

---

## 9. Incohérences internes constatées

Constats de lecture, **aucune correction n'a été apportée**. Ils sont classés du
plus structurant au plus mineur. Chacun appelle une décision explicite du maître
d'ouvrage avant l'étape suivante, car le nouvel outil ne peut pas reproduire
simultanément deux conventions divergentes.

### I1 — Deux définitions incompatibles de la température normalisée

`indicateurs.py:88-90` définit la température « compensée » comme
`T - Delta_TMm` : anomalie **non lissée** et coefficient de couplage
**implicitement égal à 1**. `core.py:159-160` définit la température
« normalisée » comme `T - m x Delta_TMm_liss` : anomalie **lissée sur 7 jours**
et coefficient `m` **estimé par régression**. Les deux grandeurs sont produites
par le même pipeline et présentées côte à côte dans les livrables. Sauf à ce que
`m` vaille exactement 1, elles ne coïncident pas — l'écart est d'autant plus
grand que le couplage air-eau est faible (site tamponné, source, forte
profondeur). **C'est l'incohérence la plus lourde de conséquences pour la
cohérence des deux outils.**

### I2 — Deux définitions de la normale selon la voie d'entrée

Voie A (`charger_normales`, `io_data.py:140-142`) : normale = moyenne brute par
(jour, mois), **sans lissage**, et `Delta_TMm` importé tel quel d'un fichier
externe. Voie B (`calculer_normales_ecarts`, `io_data.py:385-404`) : normale
lissée sur ±10 jours, `Delta_TMm` recalculé. L'arbitrage se fait sur la seule
présence d'un fichier `EcartNormales` (`orchestrator.py:95-97`). Deux exécutions
sur la même station peuvent donc reposer sur deux normales différentes sans que
le livrable le signale autrement que par la mention `source="pré-calculé"`.

### I3 — Décalage d'un jour dans les normales des années bissextiles

La normale brute est agrégée par `dayofyear` (`io_data.py:385`), alors que la
table de correspondance finale est construite sur le calendrier **bissextile** de
l'an 2000 (`io_data.py:395`). Pour une année non bissextile, `dayofyear = 60`
correspond au 1er mars, alors que dans la table 2000 il correspond au 29 février.
Après le 28 février, les années non bissextiles de la période de référence
contribuent donc à la normale du **jour calendaire suivant**. Le lissage à
±10 jours atténue fortement l'effet (il devient négligeable devant la variance
inter-annuelle), mais l'anomalie n'est pas rigoureusement centrée sur le jour
calendaire annoncé.

### I4 — `min_periods` divergents entre `Tmh` et `Delta_TMm_liss`

`Tmh` exige 4 valeurs sur 7 (`core.py:93`) ; `Delta_TMm_liss` se contente d'une
seule (`core.py:102-104`). Aux extrémités de chronique et de part et d'autre
d'une lacune, `Delta_TMm_liss` est donc défini alors qu'il ne repose parfois que
sur 1 ou 2 jours. Sans effet sur `Tmh_norm` (que le `NaN` de `Tmh` propage), mais
`Tmax_norm` (`core.py:160`) s'appuie sur `T_eau_max`, toujours défini : en bord
de lacune, `Tmax_norm` est normalisé par une anomalie de qualité très inégale
sans qu'aucune trace n'en soit conservée.

### I5 — La justification du lissage ne couvre pas `Tmax_norm`

L'argument consigné en `core.py:95-101` — aligner les échelles de temps des deux
termes de la soustraction — vaut pour `Tmh` (moyenne 7 jours). Il est ensuite
appliqué à l'identique à `T_eau_max` (`core.py:160`), qui est une valeur
**journalière instantanée**. On retranche donc une anomalie hebdomadaire d'une
valeur journalière, ce que la justification écrite exclut explicitement.

### I6 — `m` estimé sur une grandeur, appliqué à trois autres

`m` est la pente de `T_eau_moy ~ T_air` sur données journalières brutes
(`core.py:126-136`). Il est ensuite appliqué à `Tmh` (série lissée), à
`T_eau_max` (maximum journalier) et, en fraie, à une autre fenêtre saisonnière.
Le coefficient de couplage d'un maximum journalier n'a aucune raison d'égaler
celui d'une moyenne journalière. Le référentiel ne documente pas ce transfert.

### I7 — Valeurs par défaut silencieuses dans la lecture des heures

`io_data.py:76-81` : toute valeur d'heure non parsable est remplacée par
`Timedelta(0)`, sans compteur ni avertissement. Une colonne heure partiellement
corrompue produit donc des mesures faussement datées à minuit, indiscernables de
mesures réellement prises à minuit. Même logique en `core.py:839-840` où un pas
d'échantillonnage indéterminable vaut d'office 1 jour.

### I8 — Comblement implicite de l'anomalie manquante

`Delta_TMm` est joint en `how="left"` (`core.py:86`) et peut donc être `NaN`. Le
lissage `min_periods=1` (`core.py:102-104`) ignore les `NaN` : un jour sans
anomalie se voit attribuer la moyenne de ses voisins. C'est un comblement de
lacune, non documenté comme tel et non tracé.

### I9 — Bornes physiques asymétriques dans le contrôle qualité

`qc.py:42-43` teste `T_eau_moy` contre les deux bornes et `T_eau_max` contre la
borne haute, mais **jamais `T_eau_min` contre la borne basse**. Un jour dont le
minimum infra-journalier descend à -3 °C alors que la moyenne reste positive
n'est pas signalé, tandis que le cas symétrique en borne haute l'est.

### I10 — Commentaire de code non tenu (détecteur plateau)

`qc.py:53` annonce « ne pas flaguer les périodes hivernales stables proches de
0 °C par gel ». **Aucune exclusion de ce type n'est implémentée** : le détecteur
signale indifféremment une sonde bloquée et un plateau de gel hivernal réel.

### I11 — Seuils minimaux de mesures journalières incohérents

`charger_eau` (`io_data.py:92-96`) calcule une moyenne journalière quel que soit
le nombre de mesures, y compris une seule. `indicateurs.py:37` exige au contraire
3 mesures pour valider une amplitude nycthémérale. Deux grandeurs issues du même
jour reposent donc sur deux exigences de représentativité différentes.

### I12 — Tests de normalité sans effet sur le calcul

`core.py:128-134` choisit Pearson ou Spearman selon les tests de Shapiro, mais la
pente `m` — seule grandeur qui alimente la normalisation — reste la pente OLS
dans tous les cas (`core.py:136`). Le test conditionne l'affichage, pas le
calcul. Ce n'est pas une erreur en soi, mais le livrable peut laisser croire
qu'une régression robuste a été substituée à l'OLS lorsque la normalité est
rejetée.

### I13 — La colonne d'heure n'est reconnue que si son nom commence par « heure »

`io_data.py:73-74` sélectionne la colonne d'heure séparée par
`c.lower().startswith("heure")`. Or la détection de la colonne de DATE, deux
lignes plus haut (`io_data.py:54-57`), utilise un test d'inclusion
(`"heure" in c.lower()`) et un vocabulaire bien plus large. Les deux règles
sont donc asymétriques sans raison documentée. Conséquence observée à
l'inventaire : le fichier `data/eau/BLE3-0.xlsx`, dont les colonnes sont
nommées `chmes_date` / `chmes_heure` / `chmes_valeur`, voit sa date et sa
valeur correctement reconnues mais **son heure ignorée**. Toutes ses mesures
sont datées à minuit.

Portée exacte : `T_eau_moy`, `T_eau_max`, `T_eau_min` et `n_mesures` restent
justes, puisqu'ils agrègent par jour civil et que le jour, lui, est correct.
Sont en revanche faussés le pas d'échantillonnage apparent (1 440 min au lieu
de 60), la détection des lacunes infra-journalières, et l'horodatage des
extrêmes (`indicateurs.py:42-47`, qui restituerait « 00h » pour tous les
maxima). Le nombre d'horodatages dupliqués explose mécaniquement (2 828 pour
ce seul fichier).

Aucune erreur n'est levée et aucun avertissement n'est émis : la perte est
silencieuse.

### I14 — `TN` / `TX` inexploitables en l'état

Aucun des deux loaders d'air ne lit `TN` ni `TX` (`io_data.py:112-118`,
`io_data.py:329-346`). Toute la chaîne repose sur la seule moyenne journalière
`TM`. Si le nouvel outil doit produire un indicateur adossé aux extrêmes d'air,
il sortira du périmètre conventionnel de V4.5 et devra le dire explicitement.

---

## 10. Ce que le nouvel outil devra reprendre sans discussion

Pour garantir l'absence de contradiction entre les deux livrables :

1. Période de référence des normales : **1991-2020** stricte.
2. Normale d'un jour calendaire : moyenne inter-annuelle par jour de l'année,
   **lissée ±10 jours en circulaire** (voie B), sauf décision contraire du maître
   d'ouvrage sur le point I2.
3. `Delta_TMm = T_air - normale`, sur tous les jours observés.
4. `Delta_TMm_liss` = moyenne mobile **centrée 7 jours** de `Delta_TMm`.
5. `Tmh` = moyenne mobile **centrée 7 jours, min_periods = 4** de `T_eau_moy`.
6. `m` = pente **OLS** de `T_eau_moy ~ T_air` sur **juin-septembre**, données
   journalières brutes, minimum 10 jours.
7. `T_norm = T - m x Delta_TMm_liss`, appliquée à `Tmh` et à `T_eau_max`.
8. Fenêtre estivale d'exploitation : **juin à septembre** (mois 6 à 9), soit
   **122 jours** par année civile.
9. Jour civil = jour local du fichier, sans fuseau ni décalage.
10. Moyenne journalière = moyenne **arithmétique non pondérée** des mesures du
    jour, sans seuil minimal de mesures.
