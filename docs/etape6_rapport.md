# THERMIE_BIO V4.6 — Rapport d'étape 6

**Objet.** Lever la réserve R13 sur l'adaptateur du correctif 3, rebaser les
deux références sous protocole, implémenter le **correctif 2** (index
calendaire des fenêtres glissantes), et amender la spécification sur trois
points.

---

## Artefacts figés pour cette étape (D34, redéclarés)

La commande d'étape déclare ce qui doit bouger et ce qui doit rester figé. Je
redéclare la liste **avant** de montrer les chiffres, et je signale
immédiatement le seul point où ma lecture du code diffère de la déclaration.

| Artefact | Déclaré | Constaté | |
|---|---|---|---|
| `00_format_detecte.json` | figé | **0/6 bougent** — conforme | |
| `01_colonnes_retenues.json` | figé | **0/6 bougent** — conforme | |
| `02_effectifs.csv` | figé | **0/6 bougent** — conforme | compte des LIGNES par année ; le correctif 2 ne retire aucune ligne de `df`, il change des valeurs de colonnes |
| `03_journees_ecartees.csv` | figé | **0/6 bougent** — conforme | |
| `04_normales.csv` | figé | **0/6 bougent** — conforme | |
| `05_anomalies.csv` | **doit bouger** | **3/6 bougent** — conforme | porte `anomalie_lissee` = `Delta_TMm_liss` |
| `06_coefficients.csv` | **doit bouger** | **0/6 — NE PEUT PAS BOUGER** | **désaccord motivé, voir §0** |
| `07_t_norm.csv` | **doit bouger** | **3/6 bougent** — conforme | porte `T_base`, `anomalie_utilisee`, `T_normalisee` |
| `08_scores.csv` | **doit bouger** (ricochet) | **1/6 bouge** — conforme | ricochet réel mais étroit, voir §3 |
| `10_parametres.json` | figé sauf si `min_periods` devient un paramètre | **0/6 bougent** — conforme | `min_periods` **n'est pas** devenu un paramètre |
| `99_log.txt` | — | 1/6 bouge | numéro de ligne de la trace figée, et trois pourcentages de fraie |

Les « 3/6 » et « 1/6 » ne sont pas des demi-conformités : **les trois jeux dont
`05_anomalies.csv` et `07_t_norm.csv` bougent sont exactement les trois qui
portent des journées affectées** (jeu_02 : 39, jeu_03 : 6, jeu_bienne : 1 086 ;
jeu_04, jeu_05 et jeu_exemples_v45 : **0**). Un jeu sans lacune enjambée ne
peut pas bouger, et il serait inquiétant qu'il bouge.

---

## §0 — Carnet de bord

### `06_coefficients.csv` est déclaré mobile, et il ne peut pas l'être

La commande range `06_coefficients.csv` parmi les artefacts qui **doivent**
bouger. Le code dit le contraire, et je le signale avant de rebaser plutôt
qu'après.

`06_coefficients.csv` porte trois grandeurs :

| Grandeur | Produite par | Entrées |
|---|---|---|
| `m_estival` | `core.analyse_sensibilite` (`core.py:134` avant correctif, `core.py:194` après) | `stats.linregress(x, y)` avec `x, y = df_ete["T_air"], df_ete["T_eau_moy"]` — **brutes** |
| `m_saisonnier_fraie` | `core._m_saisonnier` (`core.py:243` avant, `core.py:303` après) | `stats.linregress(sub["T_air"], sub["T_eau_moy"])` (`core.py:316`) — **brutes** |
| `normales` | `io_data.calculer_normales_ecarts` | en **amont** de `fusionner` |

Ni `Tmh` ni `Delta_TMm_liss` n'entre dans aucune des trois. Le correctif 2
n'agit que sur ces deux colonnes : il ne retire ni n'ajoute une seule ligne à
`df`, et les `dropna(subset=["T_eau_moy", "T_air"])` qui constituent `df_ete`
et `sub` ne les regardent pas. **Le coefficient de couplage air–eau ne dépend
pas du lissage** — c'est une régression de l'eau brute sur l'air brut.

Je n'ai donc pas cherché à faire bouger `06_coefficients.csv`, et le §2
constate ce qu'il en est. Si l'intention derrière la déclaration était que
`m` dépende de la série lissée, c'est une **modification de méthode** et non
un effet du correctif 2 : elle ne relève pas de cette étape.

### R13 — l'invariance de l'adaptateur reposait sur une propriété du corpus

L'étape 5 livrait un adaptateur dont la colonne `motif` joignait tous les
motifs. Le diff était vide, et il l'était pour une mauvaise raison : **aucune
journée du corpus ne porte plus d'un motif**. Une invariance qui tient parce
que le cas critique est absent des données n'est pas une invariance.

Le défaut était concret : `redaction.py:76` extrait la famille d'un motif par
`^([^—(]+)` et aurait lu la chaîne jointe. Corrigé en A1, prouvé en A3 par des
cas synthétiques qui portent jusqu'à trois motifs.

### Mes scripts de correctif réécrivaient `app/` en CRLF

En revenant sur `core.py` pour re-séquencer le travail (voir ci-dessous), j'ai
comparé `app/thermie_debits/core.py` à `ref/v4_5/thermie_debits/core.py` : ils
devaient être identiques octet pour octet, le correctif 2 n'étant pas encore
posé. Ils ne l'étaient pas — **1 145 lignes de différence**, et aucune
différence de contenu.

Mes scripts de correctif lisaient avec `read_text()` et écrivaient avec
`write_text()`. Sous Windows, cela retraduit `\n` en `\r\n` : le fichier
entier changeait de fins de ligne. `app/thermie_debits/qc.py` était dans cet
état **depuis l'étape 5**.

Aucune conséquence sur les valeurs — le diff vide de l'étape 5 tient — mais
une conséquence réelle sur la vérifiabilité : `app/` cessait d'être comparable
octet pour octet à `ref/v4_5/` en dehors des corrections voulues, et une
comparaison de fichiers ne pouvait plus servir de contrôle. Les deux fichiers
sont revenus en LF, `core.py` est de nouveau **identique octet pour octet** à
celui de `ref/v4_5/`, et les scripts de correctif écrivent désormais des
octets.

### J'ai contaminé un diagnostic A/B en modifiant `app/` pendant qu'il tournait

Le A/B de B2 construit quatre rejeux complets en sous-processus, chacun
relisant `app/` sur le disque. J'ai posé le correctif 2 pendant qu'il tournait.
Les rejeux non encore lancés auraient donc porté le correctif, dans un
diagnostic censé mesurer l'état d'**avant**.

Deux fautes s'ajoutaient : le processus que je croyais avoir arrêté ne l'était
pas — `ps -W` sous Git Bash affiche le PID MSYS, `taskkill` attend le PID
Windows — et il continuait d'écrire dans le fichier de sortie que le nouveau
rejeu venait de tronquer. La sortie que j'ai lue mélangeait deux exécutions,
dont une contaminée. Elle affichait une divergence dont la trace montrait
`core.py:137` pointant sur `fusionner` — la géométrie du fichier **avec**
correctif 2.

Tout a été arrêté, le correctif 2 mis de côté, `app/` ramené à l'état d'avant
et vérifié octet pour octet, le fichier de sortie effacé, et le A/B relancé
seul. **Règle que j'applique désormais : rien n'est écrit dans `app/` tant
qu'une mesure qui le lit n'est pas terminée.**

### Ce que j'ai corrigé d'autre dans mon propre code

- `mesure_index_positionnel.py` (C1) et `mesure_correctif2.py` (C3/C4)
  recalculent les deux versions **dans le harnais**, sans toucher `app/` :
  c'est ce qui a permis de mesurer le défaut avant de le corriger, et de
  mesurer le détecteur de plateau sans le corriger.
- L'inventaire des fenêtres glissantes (C3) n'est pas rédigé à la main : le
  script relit `app/` et vérifie que le nombre d'occurrences de `.rolling(`
  correspond au nombre de lignes déclarées. **6 et 6.**

---

## §1 — Tâche A : la réserve R13

### A1 — La vue héritée rend le PREMIER motif

`app/thermie_debits/qc.py` :

```python
    # `motif` = le PREMIER motif, et lui seul : c'est ce que produisait
    # l'ancien `_marque`, qui n'ecrivait le motif que la ou le drapeau
    # n'etait pas encore pose. La vue heritee est ainsi identique PAR
    # CONSTRUCTION, sans rien devoir au contenu du jeu traite.
    df["motif"] = df["motifs"].apply(lambda ms: ms[0] if ms else "")
```

L'ancien `_marque` de V4.5 n'écrivait le motif que là où le drapeau n'était
pas encore posé : le motif rendu était donc celui du **premier détecteur** à
avoir marqué la journée, l'ordre des détecteurs étant inchangé. `motifs[0]`
reproduit cela exactement, quel que soit le nombre de motifs.

### A2 — La liste complète vit dans une colonne distincte

| Fonction | Colonnes rendues | Qui la lit |
|---|---|---|
| `rapport_ecartes(marques)` | `date`, `T_eau_moy`, `T_eau_max`, `T_air`, `motif` — **les cinq colonnes héritées, inchangées** | tout l'aval historique, via `controle_qualite` |
| `rapport_ecartes_detaille(marques)` | les cinq mêmes **plus** `motifs_complets` et `n_motifs` | le **périmètre seul** — détecteur du correctif 1, mesures du harnais |
| `marquer_qualite(...)` | table de marquage complète, colonne `motifs` = liste | le périmètre |

`controle_qualite(daily_eau, df_air, qc, verbose)` conserve signature et
retour : `(vue_retenue(marques), rapport_ecartes(marques))`. Aucun appelant
historique n'a besoin de savoir que le marquage existe.

### A3 — La preuve que le corpus ne donne pas

`tests/test_adaptateur_qc.py`. Chroniques **synthétiques**, dans `tests/`,
jamais dans `data/` : ce ne sont pas des données d'étude et elles n'ont pas à
entrer dans le corpus.

| Cas | Ce qu'il fabrique |
|---|---|
| `deux_motifs` | une journée déclenche **bornes physiques ET plateau** — le cas que le corpus ne porte pas |
| `trois_motifs` | une journée déclenche **bornes, plateau et hors d'eau** |
| `corpus_type` | chronique ordinaire, un seul détecteur par journée — le cas nominal ne doit pas régresser non plus |

Pour chaque cas, le contrôle qualité de `ref/v4_5/` et celui de `app/` sont
exécutés dans **deux interpréteurs séparés** — les deux modules s'appellent
`thermie_debits.qc` et ne peuvent pas coexister dans un même processus — puis
comparés : sortie console caractère par caractère, `propre` et `rapport`
colonne par colonne.

```
SUCCES : sur les trois cas, dont deux que le corpus ne porte pas,
la vue rendue par l'adaptateur est IDENTIQUE a celle de V4.5,
tandis que la table de marquage conserve tous les motifs.
```

Les cas synthétiques produisent jusqu'à **3 motifs** pour une même journée, et
la colonne `motif` y est vérifiée égale au premier motif. **L'invariance ne
doit plus rien au contenu du jeu traité.**

---

## §2 — Tâche B : le rebasage des deux références

**Ordre d'exécution.** Le A/B (B2) précède le rebasage ; le rebasage (B3, B4)
précède `check_reference` (B5) ; et l'ensemble de la tâche B précède la pose du
correctif 2. Les rejeux de B2 et de B5 sont construits avec
`THERMIE_CODE=ref` : ils valident que la référence est **reproductible**, ce
qui n'a de sens qu'avant d'introduire une modification volontaire.

### B1 — La racine du code est neutralisée à l'écriture

`build_reference._nettoyer`, troisième neutralisation :

```python
    # D36 — la racine du code execute est neutralisee. Le chemin du module et
    # son numero de ligne sont conserves : ce sont eux qui portent
    # l'information. Seul l'endroit du disque disparait.
    t = re.sub(r'<RACINE>[\\/](?:ref[\\/]v4_5|app)[\\/]', "<CODE>/", t)
```

Le **module** et le **numéro de ligne** sont conservés — ce sont eux qui
portent l'information. Seul l'endroit du disque disparaît.

### B2 — Le A/B, relancé AVANT toute reconstruction

`out/etape6/B2_ab_avant_rebase.txt`. Quatre rejeux complets, les deux régimes.

```
########## REGIME APPLICATION — ref/v4_5 contre app ##########
66 artefact(s) compare(s).
  identiques au bit pres                       : 66
  DIVERGENTS APRES NEUTRALISATION DU CHEMIN    : 0

########## REGIME CLI — ref/v4_5 contre app (8 565 journees ecartees) ##########
66 artefact(s) compare(s).
  identiques au bit pres                       : 66
  DIVERGENTS APRES NEUTRALISATION DU CHEMIN    : 0
```

**0 divergence sur les deux régimes**, et mieux que la condition posée :
les artefacts ne sont pas seulement « équivalents après neutralisation », ils
sont **identiques au bit près**, la neutralisation opérant désormais à
l'écriture. Le rebasage est donc autorisé.

*Ce résultat a demandé deux tentatives : la première a été contaminée, voir
§0.*

### B3 — `tests/reference/` reconstruite : 65 artefacts sur 66 intacts

Empreintes avant (`out/etape6_empreintes_avant.sha256`) contre après
(`out/etape6_empreintes_apres.sha256`), 66 lignes de part et d'autre :

| | |
|---|---|
| artefacts identiques, octet pour octet | **65** |
| artefacts qui bougent | **1 — `jeu_bienne/99_log.txt`** |

**C'est exactement la condition d'acceptation.** Reste à établir que celui-là
n'a bougé que sur les lignes de chemin. Un diff ne prouve que ce qu'il montre ;
j'ai donc fait la substitution **inverse** — remettre dans le fichier
reconstruit le chemin que la neutralisation a retiré — et vérifié que
l'empreinte retombe :

```
lignes portant <CODE>/ : 2
   ligne  298 : File "<CODE>/thermie_debits\orchestrator.py", line 166, in run
   ligne  300 : File "<CODE>/thermie_debits\core.py", line 137, in analyse_sensibilite

sha256 apres substitution inverse : 71c43c44dba8acdc...
sha256 enregistre AVANT rebasage  : 71c43c44dba8acdc...

VERDICT : IDENTIQUE.
```

**Deux lignes, 298 et 300, et rien d'autre.** L'empreinte prouve ce qu'un diff
ne montre pas : l'absence de toute autre différence.

### B4 — `tests/reference_cli/` reconstruite, invariance colonne par colonne

Une comparaison d'empreintes n'aurait rien prouvé ici : ce dossier a été figé à
l'étape 1, avant que le harnais ne gagne `10_parametres.json` et la colonne
`sortie_v45`. Elle aurait mélangé un changement de code et un changement de
schéma du harnais. La comparaison porte donc sur les **colonnes communes aux
deux schémas** (`tests/reference/comparer_cli_avant_apres.py`).

| | |
|---|---|
| artefacts comparés (hors `99_log.txt`) | **54** |
| identiques sur les colonnes communes | **54** |
| divergents | **0** |
| **colonnes communes confrontées** | **3 187** |
| **valeurs divergentes** | **0** |
| colonnes ajoutées par le harnais | `sortie_v45` |
| colonnes disparues | **aucune** |
| artefacts nouveaux | 6 × `10_parametres.json` |

**3 187 colonnes confrontées, 0 valeur divergente.**

**Les six `99_log.txt`, eux, diffèrent** — et il fallait dire pourquoi plutôt
que les exempter. Deux causes, et deux seulement :

1. la neutralisation D36 (28 lignes de chemin au total) ;
2. le **volet climatique**. `parametres.py:96` donne
   `faire_volet_climatique = True` pour le chemin CLI (provenance
   `run_cli.py:20`), contre `False` pour le chemin application
   (`app.py:146`). `tests/reference_cli/` a été figé à l'étape 1, **avant que
   le harnais ne sache cela** : il lui manquait une section que `run_cli.py`
   produit réellement. Le dossier reconstruit est donc plus fidèle à
   `run_cli.py` que celui qu'il remplace.

Preuve, par la même méthode qu'en B3 — retirer le bloc du volet climatique,
remettre le chemin, comparer les empreintes :

```
jeu_02           chemin=  0 ligne(s)  volet climatique=   6 ligne(s)  -> IDENTIQUE
jeu_03           chemin=  0 ligne(s)  volet climatique=   6 ligne(s)  -> IDENTIQUE
jeu_04           chemin=  0 ligne(s)  volet climatique=   7 ligne(s)  -> IDENTIQUE
jeu_05           chemin=  2 ligne(s)  volet climatique=   0 ligne(s)  -> IDENTIQUE
jeu_bienne       chemin= 24 ligne(s)  volet climatique= 105 ligne(s)  -> IDENTIQUE
jeu_exemples_v45 chemin=  2 ligne(s)  volet climatique=   0 ligne(s)  -> IDENTIQUE

VERDICT : la neutralisation D36 et le volet climatique expliquent
  la TOTALITE de l'ecart sur les six logs. Aucune autre difference.
```

### B5 — `check_reference` sur les deux références

| Référence | Artefacts | Verdict | Code de retour |
|---|---|---|---|
| `tests/reference/` | 66 | **DIFF VIDE — la reference est reproductible** | **0** |
| `tests/reference_cli/` | 66 | **DIFF VIDE — la reference est reproductible** | **0** |

`tests/reference_cli/` compte désormais 66 artefacts comme l'autre, ayant gagné
ses six `10_parametres.json`.

---

## §3 — Tâche C : le correctif 2

### C1 — Le défaut, mesuré AVANT correction

`core.fusionner` appliquait ses moyennes mobiles sur un index **positionnel**.
Une fenêtre de sept **lignes** n'est une fenêtre de sept **jours** que si la
série est continue. La chronique journalière ne contient que les jours
présents : dès qu'une lacune s'ouvre, la fenêtre l'enjambe et moyenne des
valeurs séparées de plusieurs mois.

`tests/reference/mesure_index_positionnel.py` → `out/etape6/C1_*.csv`.

| | |
|---|---|
| points, journées | **32 points, 67 392 journées** |
| journées de `T_norm` affectées | **1 131 (1,68 %)** |
| points concernés | **26 sur 32** |
| plus longue lacune enjambée | **1 716 jours** |
| écart maximal sur `Tmh` | **6,105 °C** |
| écart maximal sur `Delta_TMm_liss` | **6,766 °C** |

Les points les plus touchés :

| Point | journées affectées | part | plus longue lacune enjambée | écart max `Tmh` |
|---|---|---|---|---|
| `LA PLAINE A RAON-SUR-PLAINE` | 39 / 1 215 | 3,21 % | 368 j | **6,105 °C** |
| `BIE35-5__NA` | 24 / 291 | **8,25 %** | 186 j | 4,811 °C |
| `BIE32-4` | 60 / 4 031 | 1,49 % | 272 j | 4,781 °C |
| `BIE0-3` | 84 / 4 385 | 1,92 % | 427 j | 4,016 °C |
| `BIE10-8` | 65 / 3 512 | 1,85 % | 435 j | 3,781 °C |

**Cette mesure n'est plus possible après correction** : une fois la série
réindexée, aucune fenêtre n'enjambe plus rien.

### C2 — La correction, et la provenance de `min_periods`

`app/thermie_debits/core.py`, nouvelle fonction `moyenne_mobile_calendaire` :

```python
    s = pd.Series(np.asarray(valeurs, dtype=float),
                  index=pd.to_datetime(pd.Series(dates).to_numpy()))
    if s.empty:
        return s.to_numpy()
    plein = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"))
    liss = plein.rolling(window=fenetre, center=True,
                         min_periods=min_periods).mean()
    return liss.reindex(s.index).to_numpy()
```

La série est réindexée sur un calendrier journalier **continu**. Les jours
absents y occupent leur place sans y apporter de valeur : ce sont des NaN. La
fenêtre compte alors des jours, et `min_periods` compte les jours réellement
observés parmi eux. Le résultat est ramené sur l'index d'origine — **ni ligne
ajoutée, ni ligne perdue**.

**`min_periods` retenu, et sa provenance :**

| Série | `fenetre` | `min_periods` | Provenance |
|---|---|---|---|
| `Tmh` | 7 | **4** | **valeur de la version antérieure**, `core.py:111` de V4.5, reprise sans modification |
| `Delta_TMm_liss` | `lissage_delta` (7) | **1** | **valeur de la version antérieure**, `core.py:121` de V4.5, reprise sans modification |

**Aucune valeur nouvelle n'est introduite.** Ce correctif change le *support*
du lissage, pas le lissage. `min_periods` reste un littéral du code et **ne
devient pas un paramètre** : `10_parametres.json` reste donc figé, comme la
commande le prévoit dans ce cas.

Ce qui change en revanche, c'est le **sens** de `min_periods`. Sur un index
positionnel, c'est une commodité de démarrage : les premières lignes ont moins
de voisins. Sur un calendrier, c'est une exigence de **densité** — une journée
dont la fenêtre calendaire ne contient pas 4 jours observés ne reçoit plus de
`Tmh`. C'est le comportement recherché, et le C4 le chiffre.

### C3 — Toutes les fenêtres glissantes de la chaîne, et leur statut

`out/etape6/C3_inventaire_fenetres.csv`. Le script relit `app/` : **6
occurrences de `.rolling(`, 6 lignes d'inventaire.**

| `fichier:ligne` | Ce que c'est | Dans la chaîne `lecture → T_norm` | Statut |
|---|---|---|---|
| `core.py:111` | `fusionner` → `Tmh` | **oui** | **CORRIGÉE** |
| `core.py:121` | `fusionner` → `Delta_TMm_liss` | **oui** | **CORRIGÉE** |
| `qc.py:129` | détecteur de plateau (écart-type glissant) | oui, **en amont** | **NON corrigée — hors périmètre**, voir ci-dessous |
| `io_data.py:537` | lissage des normales d'air | oui | **SANS OBJET — déjà continue** |
| `core.py:948` | `corr_partielle_air` → lissage d'air | non | hors chaîne |
| `indicateurs.py:55` | `Tmm30j` | non | hors chaîne, en aval de `T_norm` |

**`io_data.py:537` n'a pas besoin d'être corrigée.** Elle s'applique à un index
jour-de-l-année reconstruit **complet** sur `range(1, 367)` puis interpolé
(`io_data.py:532-534`), et triplé pour la circularité. Aucune lacune n'est
possible : l'index positionnel **est** le calendrier.

**`qc.py:129` porte le même défaut et n'est pas corrigée ici.** Le détecteur de
plateau décide des journées **écartées** : le corriger déplacerait
`02_effectifs.csv`, `03_journees_ecartees.csv` et `06_coefficients.csv`, que la
commande d'étape déclare **figés**. La déclaration d'artefacts tranche donc :
il relève d'un correctif propre, pas de celui-ci.

J'ai mesuré ce que sa correction changerait, sans l'appliquer
(`out/etape6/C4_plateau_hors_perimetre.csv`) :

> **0 verdict change** sur les 32 points. Aucune journée ne cesserait d'être
> marquée, aucune ne le serait en plus.

Le défaut est donc réel dans le code et **non exercé par ce corpus** — même
forme que le défaut de `qc.py:32-36` relevé en étape 5. Rien n'oblige à le
corriger dans l'urgence, et rien n'autorise à l'oublier : il est consigné ici.

### C4 — Les bords : ce que l'exigence de densité retire

`out/etape6/C4_bords.csv` et `C4_bords_journees.csv`.

| | |
|---|---|
| journées qui **perdent** `Tmh` | **18 sur 67 392 — 0,03 %**, sur 5 points |
| dont à une **extrémité** de chronique | **0** |
| dont au **voisinage d'une lacune** | **18** |
| journées **gagnées** | 0 |
| `Delta_TMm_liss` perdues (`min_periods=1`) | **0** |

**Aucune journée n'est perdue en début ou en fin de chronique.** Quand la série
est continue, une fenêtre calendaire centrée contient exactement autant de
jours observés qu'une fenêtre positionnelle : les bords se comportent à
l'identique. Les 18 pertes sont **toutes** au voisinage d'une lacune interne —
exactement là où le correctif doit mordre.

Et ce qui est abandonné mérite de l'être :

| Point | Date | Jours observés dans la fenêtre de 7 j | `Tmh` positionnel abandonné |
|---|---|---|---|
| `BIE10-8` | 2019-01-27 | **1** | 0,030 °C |
| `BIE6-8` | 2012-04-01 | **1** | 6,857 °C |
| `BIE6-8` | 2012-03-28 | **2** | 6,827 °C |
| `LA PLAINE A RAON-SUR-PLAINE` | 2009-12-29 → 12-31 | 3 | 4,57 / 4,45 / 4,47 °C |
| `BIE40-3` | 2015-09-08 | 3 | 13,480 °C |
| *(11 autres)* | | 3 | |

Les deux premières lignes se lisent seules : une « moyenne sur sept jours »
calculée à partir d'**une seule** journée observée. Ce n'était pas une mesure.

`Delta_TMm_liss` ne perd rien, et ne pouvait rien perdre : `min_periods=1`, et
la journée est toujours dans sa propre fenêtre.

---

### C5 — Ce que le correctif 2 change, artefact par artefact

Rejeu du code corrigé contre la référence rebasée
(`out/etape6/C_artefacts_bilan.csv`, `C_ecarts_valeurs.csv`).

**8 artefacts bougent sur 66. 58 restent figés.** La liste correspond à la
déclaration, à l'exception de `06_coefficients.csv` traitée au §0.

| Artefact | Lignes retirées | Valeurs changées | Colonnes touchées |
|---|---|---|---|
| `jeu_02/05_anomalies.csv` | 0 | 39 | `anomalie_lissee` |
| `jeu_02/07_t_norm.csv` | **3** | 213 | `T_base`, `anomalie_utilisee`, `T_normalisee` |
| `jeu_03/05_anomalies.csv` | 0 | 6 | `anomalie_lissee` |
| `jeu_03/07_t_norm.csv` | 0 | 39 | idem |
| `jeu_bienne/05_anomalies.csv` | 0 | 1 062 | `anomalie_lissee` |
| `jeu_bienne/07_t_norm.csv` | **3** | 6 052 | idem |
| `jeu_bienne/08_scores.csv` | 0 | 10 | `valeur`, `detail` |
| `jeu_bienne/99_log.txt` | — | — | n° de ligne de la trace figée, 3 pourcentages de fraie |

**Ampleur des écarts** — jamais des broutilles, jamais un séisme :

| Colonne | Valeurs changées | Part | Écart médian | Écart max |
|---|---|---|---|---|
| `jeu_02` `anomalie_lissee` | 39 | 3,21 % | 0,637 °C | **6,766 °C** |
| `jeu_02` `T_normalisee` | 84 | 1,27 % | 0,126 °C | 5,061 °C |
| `jeu_bienne` `anomalie_lissee` | 1 062 | 1,70 % | 0,622 °C | 5,404 °C |
| `jeu_bienne` `T_normalisee` | 2 367 | 0,72 % | 0,275 °C | 4,120 °C |
| `jeu_bienne` `T_base` | 1 318 | 0,40 % | 0,194 °C | 4,781 °C |

**Le compte des valeurs vidées ferme la boucle avec C4.** `T_base` et
`T_normalisee` perdent **3 valeurs sur `jeu_02` et 15 sur `jeu_bienne`, soit
18** — exactement les 18 journées que C4 annonçait, prédites avant ce rejeu et
retrouvées après. Les lignes correspondantes disparaissent de `07_t_norm.csv`.

#### Le ricochet sur `08_scores.csv`, en clair

Neuf valeurs changent, sur un seul jeu. Elles se lisent :

| Point | Indicateur | Avant | Après |
|---|---|---|---|
| `BIE40-3` | `n_jours_tmh` | 1 303 j | 1 302 j |
| `BIE6-8` | `n_jours_tmh` | 1 302 j | 1 300 j |
| `BIE40-3` | `pct_stress_chronique` | 4,605 % | 4,762 % |
| `BIE42-7` | `pct_stress_chronique` | 10,865 % | 10,999 % |
| `BIE51-0` | `pct_stress_chronique` | 8,815 % | 8,540 % |
| `BIE6-8` | `pct_stress_chronique` | 0,691 % | 0,846 % |
| **`BIE5-9`** | **`n_jours_aigus`** | **1 j** | **0 j** |
| **`BIE5-9`** | **`pts_aigu`** | **1 /3** | **0 /3** |
| **`BIE5-9`** | **`sgvt`** | **3,167 /10** | **2,500 /10** |

Les trois dernières lignes sont le seul changement de **conclusion** de tout le
correctif, et il vaut d'être regardé de près.

`BIE5-9` avait **une** journée de vulnérabilité aiguë : le **31 juillet 2022**.
Le seuil aigu du point vaut **23,000 °C** (`08_scores.csv`). Ce jour-là :

| | |
|---|---|
| `T_eau_max` brute | 23,760 °C |
| `Tmax_norm` avec l'index positionnel | **23,365 °C** → au-dessus du seuil |
| `Tmax_norm` avec l'index calendaire | **22,946 °C** → au-dessous |

L'écart, 0,419 °C, vient entièrement de `Delta_TMm_liss` : l'anomalie d'air
lissée de cette journée était moyennée sur une fenêtre qui enjambait une
lacune — `BIE5-9` en porte une de **600 jours** (C1). **Cette journée était
comptée comme aiguë parce que son anomalie climatique avait été moyennée avec
des jours situés des mois plus loin.** Corrigée, elle repasse sous le seuil, le
point perd son point de vulnérabilité aiguë, et son SGVT tombe de 3,17 à 2,50
sur 10.

C'est exactement ce que le correctif 2 devait produire : non pas un
déplacement uniforme des valeurs, mais la disparition de verdicts qui
reposaient sur des moyennes fabriquées.

---

## §4 — Tâche D : les trois amendements de la spécification

`docs/SPEC_detecteur_et_validite.md`. Trois points, et trois seulement.

### D.1 — `min_jours_episode` : le défaut passe de 3 à 1

**Raison de droit.** Le défaut de 3 était « repris de la règle de séquence de
`thermie_points` (`qualite.py:177`) ». C'est une importation de seuil depuis
le projet clos, que **D15** interdit. La formule « convention de détection et
non valeur de bassin » habillait l'importation ; elle ne l'annulait pas.

**Raison de fait.** La correction de R10 (étape 5) a établi que la longueur
médiane d'épisode de la marche 2 vaut **1,5 jour**, et non 4,0 comme
l'annonçait l'étape 4. Le balayage `out/etape5/r10_filtre_episode.csv` donne :

| `min_jours_episode` | marche 1 : jours conservés | marche 2 : jours conservés |
|---|---|---|
| **1** | 40/40 (0 % exclus) | 4/4 (0 % exclus) |
| 2 | 21/40 (47,5 % exclus) | 2/4 (50 % exclus) |
| **3** | **17/40 (57,5 % exclus)** | **0/4 (100 % exclus)** |
| 4 | 11/40 (72,5 % exclus) | 0/4 (100 % exclus) |

À 3, le plancher ne raffine pas la marche 2 : il la **supprime intégralement**,
sur les deux seuls points où elle se déclenche. Un garde-fou qui annule le
détecteur qu'il garde n'est pas un garde-fou.

Le défaut de 1 ne retire aucune capacité : le paramètre reste exposé. Quand la
mesure ne désigne aucune valeur, le neutre est le bon défaut.

### D.2 — La condition d'effectif sort de la règle de validité

**De principe.** La procédure de dérivation de `n_min` écrite en étape 4
mesurait « la part des fenêtres qui concluent significatif » en mettant en
commun les fenêtres de **tous les points du corpus**. **D41** l'interdit :
l'application traite une sonde à la fois. Sur une chronique unique, cette part
n'est pas une propriété de l'effectif, c'est une propriété de ce point. La
valeur de 60 n'était donc pas « dérivée du jeu traité » comme l'affirmait le
tableau de la §3 de la spécification — elle était dérivée du **corpus de
développement**, ce que **D15** interdit aussi.

**De mesure.** L'écart-type de Newey-West croît quand `n` décroît, l'IC à 95 %
s'élargit, et une pente estimée sur peu de jours cesse d'elle-même d'être
significative. Le mécanisme fonctionne : `BLE3-0`, `n = 7`, sort par la
significativité avec `t = 0,22`.

Les cinq estimations que l'effectif écartait **en plus** de la significativité :

| Point | `n` | pente | `t` de Newey-West |
|---|---|---|---|
| `GRO9-1` | 14 | 0,293 | **6,09** |
| `ABI3-6` | 23 | 0,098 | **4,21** |
| `LGV11-8` | 35 | 0,334 | **5,16** |
| `HRI7-7` | 36 | 0,289 | **5,01** |
| `FLU8-4` | 51 | 0,146 | **9,06** |

Le plus faible `t` vaut 4,21, plus du double du seuil de 1,96, sur des
écarts-types qui ont **déjà** payé le prix du petit effectif. La condition
d'effectif ne rattrapait pas une faiblesse que la significativité aurait
laissée passer : elle **écrasait son verdict** au nom d'un effectif calibré
ailleurs.

**Effet du retrait, dit sans l'adoucir.** Sur `m_estival`, aucun. Sur
`m_saisonnier`, les rejets passent de **7 sur 33 à 2 sur 33** : cinq
estimations qui sortaient entrent. L'argument n'est pas qu'elles seraient sans
importance — c'est que rien dans la statistique ne justifie de les sortir, et
que le nombre qui les sortait ne se calcule pas sur une sonde seule.

### D.3 — D41 en tête de la section 3, appliqué ligne à ligne

La section 3 de la spécification s'ouvre désormais sur D41 : aucune valeur du
tableau ne peut dépendre d'un corpus multi-points, parce qu'une valeur qui ne
se calcule qu'en mettant plusieurs points en commun n'est pas calculable au
moment où elle sert.

**Le critère a été appliqué à chaque ligne du tableau. Il fait sortir `n_min`,
et rien d'autre.**

| Catégorie | Lignes | Verdict D41 |
|---|---|---|
| conventions statistiques | `1,4826`, niveau `95 %`, décalage `L` | ne dépendent d'aucune donnée |
| défauts exposés | `k`, `plancher_dispersion`, `min_jours_groupe`, `min_jours_episode`, `hors_eau_mois`, `q_ampl`, `[0 ; 1,2]` | paramètres, non mesures ; leur défaut vient d'une convention ou du code de V4.5 |
| seule valeur dérivée subsistante | seuil d'amplitude d'air en °C = décile `q_ampl` de la série d'air **du jeu traité** | un jeu porte **une** station d'air : la dérivation s'exécute à l'identique sur une sonde seule |
| **retirée** | **`n_min`** | **exige un corpus multi-points** |

La §5 de la spécification a été mise en cohérence : « sept estimations sur 33
sortent » devient « deux sur 33 ».

---

## §5 — Décisions manquantes, en alternatives fermées

### Alternative 1 — `06_coefficients.csv`

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — la déclaration décrivait une attente, pas une contrainte** | rien à faire : `06` reste figé, le correctif 2 est complet | c'est la lecture du code : `m` régresse l'eau **brute** sur l'air **brut** |
| **B — `m` doit être estimé sur les séries lissées** | `analyse_sensibilite` et `_m_saisonnier` changent d'entrées ; `06`, `07`, `08` bougent | c'est un **changement de méthode**, pas un effet du correctif 2 ; il demande sa propre justification et sa propre étape |

*Je retiens A et je m'y tiens jusqu'à instruction contraire.*

### Alternative 2 — Le détecteur de plateau (`qc.py:129`)

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — correctif séparé, plus tard** | `02`, `03`, `06` restent figés cette étape | la déclaration d'artefacts de l'étape 6 les fige ; et **0 verdict ne change** sur ce corpus, donc rien ne presse |
| **B — l'inclure au correctif 2** | trois artefacts figés bougent, l'étape sort de son cadre | il faudrait que la commande lève le gel |

*Je retiens A. Le défaut est consigné, chiffré à 0 sur ce corpus, et non oublié.*

---

## §6 — Ce qui reste ouvert

- **Le détecteur de plateau** (`qc.py:129`) porte le même défaut d'index. Non
  exercé par ce corpus — **0 verdict changerait** — non corrigé parce qu'il
  déplacerait trois artefacts déclarés figés, consigné et chiffré.
- **Le défaut de `qc.py:32-36`** relevé en étape 5 reste dans le même état :
  réel dans le code, jamais exercé par ce corpus.
- **`06_coefficients.csv`** attend un arbitrage : la commande le déclare
  mobile, le code établit qu'il ne peut pas l'être sous ce correctif (§0 et
  §5, alternative 1).
- **La spécification est amendée, non implémentée.** Le correctif 1 (les deux
  marches du détecteur) et la règle de validité restent à écrire.
- **`tests/reference_cli/` a gagné son volet climatique** en B4. Elle décrit
  désormais fidèlement `run_cli.py`. Les mesures d'aveuglement de l'étape 2,
  qui s'appuyaient sur l'ancien dossier, portaient sur des artefacts de
  données inchangés (0 valeur divergente sur 3 187 colonnes) : elles restent
  valides. Seuls les six `99_log.txt` ont changé.
