# THERMIE_BIO V4.6 — Rapport d'étape 8

**Objet.** Poser le **correctif 8** (D47) — le lissage de `Tmh` porte sur la
chronique d'eau complète —, vérifier deux prédictions falsifiables, recalculer
la table d'impact du détecteur périmée par les correctifs (D50), et compléter
le journal des verdicts.

---

## Artefacts pour cette étape (D34, redéclarés)

| Artefact | Déclaré | Constaté | |
|---|---|---|---|
| `05_anomalies.csv` | **doit bouger** | **FIGÉ — 0 valeur** | **désaccord signalé avant correction, voir §0** |
| `07_t_norm.csv` | **doit bouger** | **2/6 bougent** | jeu_02 (+3 lignes, 76 valeurs), jeu_bienne (961 valeurs) |
| `03_journees_ecartees.csv` | **doit bouger** | **1/6 bouge** | jeu_02, **−3 lignes** : les trois journées de densité |
| `08_scores.csv` | peut bouger, à chiffrer | **1/6 bouge** | 3 `pct_stress_chronique`, aucun verdict |
| `02_effectifs.csv` | peut bouger, à chiffrer | **1/6 bouge** | jeu_02, `journees_non_diag_densite` 3 → 0 |
| `00_format_detecte.json` | figé | **figé** | |
| `01_colonnes_retenues.json` | figé | **figé** | |
| `04_normales.csv` | figé | **figé** | |
| `06_coefficients.csv` | **figé (P1)** | **figé** | **P1 tient** |
| `10_parametres.json` | figé | **figé** | |
| `99_log.txt` | non déclaré | 1/6 bouge | 2 numéros de ligne d'une trace figée |

**60 artefacts figés sur 66, 6 bougent.**

### Le désaccord : `05_anomalies.csv` ne peut pas bouger

Signalé **avant** de corriger, comme à l'étape 6 pour `06_coefficients.csv`.

`art_05` construit ses lignes à partir de `res.df` avec les colonnes `T_air`,
`T_normale`, `Delta_TMm`, `Delta_TMm_liss`, `T_air_std`
(`build_reference.py`, `COLS_05`). **`Tmh` n'y figure pas.** Or le correctif 8
ne touche que `Tmh` : il ne change ni le jeu de lignes de `df` — les trois
journées récupérées y étaient déjà, avec un `Tmh` vide — ni aucune des cinq
colonnes ci-dessus.

`05_anomalies.csv` ne peut donc bouger que si l'on corrige **aussi**
`Delta_TMm_liss`. C'est précisément le défaut miroir décrit au §2 (B4), que
D47 ne demande pas et que je n'ai pas posé. Il est mesuré, et proposé en
alternative fermée au §5.

*Constaté : `05_anomalies.csv` est figé sur les six jeux.*

---

## §0 — Carnet de bord

### Le correctif 8 corrige un défaut dont le miroir reste en place

`Tmh` est une moyenne d'**eau** qui dépendait de la complétude de l'**air**.
C'est le défaut que D47 fait corriger. Mais l'argument se retourne
symétriquement, et il faut le dire :

> `Delta_TMm_liss` est une moyenne mobile de l'anomalie d'**air**. Elle est
> calculée sur la vue exploitable, donc sur les seules journées qui ont
> **aussi** une température d'eau. Elle dépend de la complétude de l'**eau**,
> qui ne la regarde pas.

Mesuré sans être appliqué : **854 valeurs changeraient (1,27 %), sur les
32 points**, écart maximal **4,790 °C** sur l'anomalie, jusqu'à **1,939 °C**
répercutés sur `T_norm`. C'est **plus large que le correctif 8 lui-même**.

Je ne l'ai pas corrigé : D47 porte sur `Tmh` et sur `Tmh` seulement, et un
correctif fait une chose. Le défaut est nommé dans le code, à l'endroit exact
où il se produit, avec ses chiffres. Alternative fermée au §5.

### Un `str.replace` sans assertion échoue en silence

Trois de mes substitutions dans un script de mesure n'ont pas trouvé leur
ancre — les `\n` d'un motif étaient à nouveau mangés par le passage en
document heredoc du shell — et `str.replace` ne dit rien quand il ne remplace
rien. Le script a tourné, produit ses fichiers, et affiché l'ancien texte.

L'incident est bénin : il ne touchait qu'un affichage de console, et le CSV
portait bien les colonnes voulues. Mais il montre par contraste pourquoi mes
patchs de code fonctionnent : ils passent par un `rep()` qui **assert** sur
l'ancre. Le contrôle qui a arrêté un patch à l'étape 7 est exactement celui
qui manquait ici.

*Deux commentaires d'un script du harnais ont par ailleurs été amputés par
l'interprétation des accents graves dans une ligne de commande ; ils sont
restaurés.*

### Ce que la Tâche C a révélé sur la Tâche C elle-même

La table d'impact devait être périmée par les correctifs. **Elle ne l'était
pas** : sur 30 des 31 points, `Δm` et `ΔTmh_norm` sont identiques à la sixième
décimale. La raison est structurelle et vaut d'être écrite : ce sont des
**différences entre deux rejeux de la même chaîne**, et un correctif qui
déplace les deux côtés du même montant ne déplace pas leur différence. Pour
`Δm`, c'est même plus fort : `m` régresse l'eau brute sur l'air brut (D42),
donc les correctifs 2 et 8 ne peuvent pas l'atteindre du tout.

Le seul point qui varie, `BIE40-3`, ne varie **pas** à cause des correctifs :
il varie parce que l'étape 4 mesurait le socle seul là où la spécification
retient l'union des deux marches. Le recalcul était justifié — il fallait
vérifier —, mais son résultat est que la table tenait.

---

## §1 — D44 : le contrôle permanent

### Avant toute modification

```
  app/LISEZ-MOI.md                    ABSENT DE ref/v4_5
  app/thermie_debits/core.py          DIFFERENT   nature : CONTENU
  app/thermie_debits/orchestrator.py  DIFFERENT   nature : CONTENU
  app/thermie_debits/qc.py            DIFFERENT   nature : CONTENU

  CONFORME — la liste constatee est exactement la liste declaree.
```

**Quatre entrées, exactement celles attendues, aucune en CRLF.** Code de
retour 0.

### À la fin

Même liste — le correctif 8 ne touche que `core.py`, déjà déclaré. **Code de
retour 0**, aucun CRLF introduit. La sortie complète est
`out/etape8/A_diff_app_ref_apres.txt`.

---

## §2 — Le correctif 8, et les deux prédictions

### B1 — Le lissage porte sur l'eau complète

`app/thermie_debits/core.py:275-285` :

```python
    eau_complete = (complet.loc[complet["T_eau_moy"].notna(),
                                ["date", "T_eau_moy"]]
                    .sort_values("date"))
    tmh_eau = pd.Series(
        moyenne_mobile_calendaire(eau_complete["date"],
                                  eau_complete["T_eau_moy"],
                                  fenetre=7, min_periods=4),
        index=pd.to_datetime(eau_complete["date"].to_numpy()))
    df["Tmh"] = tmh_eau.reindex(
        pd.to_datetime(df["date"].to_numpy())).to_numpy()
```

`complet` est la table de toutes les journées retenues par le contrôle
qualité, appariées ou non — c'est le correctif 5 qui l'a rendue disponible.
`fenetre` et `min_periods` sont inchangés ; seul le **support** change, comme
au correctif 2. Aucune ligne n'est ajoutée à `df`.

### B2 — Les trois journées récupérées, nommément

| Point | Date | Avant | Après |
|---|---|---|---|
| `LA PLAINE A RAON-SUR-PLAINE` | **2009-12-29** | `non_diagnosticable`, motif de densité | `retenu`, `Tmh` calculé |
| `LA PLAINE A RAON-SUR-PLAINE` | **2009-12-30** | idem | idem |
| `LA PLAINE A RAON-SUR-PLAINE` | **2009-12-31** | idem | idem |

**Pourquoi ce point et pas un autre :** `LA PLAINE` porte 330 journées d'eau
privées d'air, dont plusieurs dans la fenêtre de fin décembre 2009. Leur
fenêtre calendaire ne comptait que trois journées *appariées*, pour quatre
exigées ; elle en compte assez dès qu'on regarde l'eau.

**Le statut ne survit pas par inertie**, et ce n'est pas une vérification
après coup : le marquage de densité est calculé **après** `Tmh`
(`core.py:345`, `sans_tmh = set(df.loc[df["Tmh"].isna(), "date"])`). Une
journée qui reçoit un `Tmh` ne peut pas être marquée. Constaté dans les
artefacts :

| Artefact | Avant | Après |
|---|---|---|
| `jeu_02/02_effectifs.csv`, `journees_non_diag_densite` (total) | **3** | **0** |
| `jeu_02/03_journees_ecartees.csv`, étape `densite_calendaire` | **3 lignes** | **0** |
| `jeu_02/07_t_norm.csv` | — | **+3 lignes** |

Sur l'ensemble du corpus, les journées de densité passent de **18 à 15**.

### B3 — Aucune journée n'en perd

**0**, comme la mesure ALT le prédisait. Le contrôle est direct : `Tmh perdus`
= 0 dans `out/etape8/B_verification_P2.txt`. C'était attendu — élargir le
support d'un lissage ne peut qu'ajouter des voisines, jamais en retirer.

### B4 — Les autres fenêtres glissantes, une par une

La question posée est précise : *dépendre d'une complétude qui ne la regarde
pas*. Ce n'est pas la même que celle du correctif 2, qui portait sur l'index.

| `fichier:ligne` | Ce que c'est | Même défaut ? |
|---|---|---|
| `core.py:284` | `Tmh` | **OUI — corrigé par le correctif 8** |
| `core.py:310` | `Delta_TMm_liss` | **OUI, en miroir — NON corrigé.** Grandeur d'**air** lissée sur les seules journées ayant de l'**eau**. `ecart_by_date` couvre toutes les dates de la station : le support existe. **854 valeurs (1,27 %), 32 points, jusqu'à 4,790 °C.** §5, alternative 1 |
| `qc.py:129` | détecteur de plateau, écart-type glissant | **NON** pour ce défaut : `marquer_qualite` ouvre par une jointure **gauche** (`qc.py:191`), la chronique d'eau y est donc complète. *(Il porte en revanche le défaut d'index du correctif 2, rattaché au correctif 1 par D46.)* |
| `io_data.py:537` | lissage des normales d'air | **NON.** L'index est `range(1, 367)` reconstruit complet puis interpolé, et triplé pour la circularité. Aucune complétude n'est en jeu : l'index **est** le calendrier |
| `indicateurs.py:55` | `Tmm30j` | **OUI — hors périmètre.** Moyenne maximale sur 30 jours de la température d'**eau**, calculée sur `d["T_eau_moy"]` où `d` est un sous-ensemble de `res.df`, donc des seules journées appariées à l'air. Même défaut que `Tmh`, en aval de `T_norm`. *(Il porte aussi le défaut d'index : `s.rolling(30)` après `dropna`.)* §5, alternative 2 |
| `core.py:1221` | `lissage_air` dans `corr_partielle_air` | **NON.** Grandeur d'air dans une analyse air/débit qui exige l'air par nature ; sa complétude la regarde. *(Défaut d'index, hors chaîne, déjà consigné à l'étape 6.)* |

**Deux fenêtres portent encore le défaut**, et aucune des deux n'est dans le
périmètre de D47 : `Delta_TMm_liss` en miroir, et `Tmm30j` en aval.

### P1 — `06_coefficients.csv` ne doit pas bouger : **elle tient**

**Figé sur les six jeux, au bit près.** `m` régresse `T_eau_moy` brute sur
`T_air` brute (`core.analyse_sensibilite`, `core._m_saisonnier`) ; `Tmh` n'y
entre pas. Et le correctif 8 ne change aucune ligne de `df`, donc pas
l'échantillon de régression.

### P2 — 473 valeurs, 22 points, 1,099 °C : **elle tient, au chiffre près**

Vérifiée avec la définition exacte de la mesure d'étape 7 — recalcul des deux
versions côte à côte sur les 67 392 journées exploitables
(`out/etape8/B_verification_P2.txt`) :

| | Prédit à l'étape 7 | Constaté à l'étape 8 |
|---|---|---|
| `Tmh` déplacés | **473** | **473** |
| points concernés | **22** | **22** |
| écart maximal | **1,099 °C** | **1,099 °C** |
| `Tmh` récupérés | **3** | **3** |
| `Tmh` perdus | **0** | **0** |

**Une précision de méthode, pour que le chiffre ne soit pas mal lu.** Une
première vérification, faite en comparant les deux rejeux sur
`07_t_norm.csv`, annonçait **488**. Ce n'était pas un désaccord avec la
prédiction : l'artefact ne contient **que les journées dont `Tmh_norm` n'est
pas vide**, et mon décompte y traitait comme « changées » des lignes dont l'un
des deux côtés était vide. La prédiction portait sur les 67 392 journées
exploitables, pas sur les 67 101 lignes de l'artefact. Vérifiée sur son propre
périmètre, elle tombe exactement juste.

*Le nombre à retenir est 473. Le 488 était une erreur de ma mesure, pas un
écart du correctif — je le consigne plutôt que de l'effacer.*

---

## §3 — La table d'impact recalculée (D50)

`tests/reference/mesure_impact_detecteur.py`. Réglage mesuré : celui que la
spécification retient — **union des deux marches**, socle `E_moy_rel > 3,0`
plus la conjonction `R_ampl_rel > 3,0` **ET** `E_max_rel > 3,0` là où `TN` et
`TX` existent. Référence : le régime en service (D25).

### Contrôle préalable — le marquage est bien inchangé

D50 le posait ; il fallait le vérifier plutôt que le croire.

| | Étape 4 | Étape 8 |
|---|---|---|
| socle seul, `k = 3,0` | **68 jours** | **68 jours** |
| régime en service | **22 jours** | **22 jours** |

**Identiques.** Le détecteur lit `T_eau_max`, `T_air`, `TN`, `TX`,
`T_eau_min` — qu'aucun correctif posé n'a touchés. Ni le choix de `k`, ni la
mesure d'aveuglement n'étaient à refaire, et ils ne l'ont pas été.

### C1 — L'impact, par point

| | |
|---|---|
| jours marqués, régime en service | **22** |
| jours marqués, détecteur retenu | **69** (marche 1 : 68, marche 2 : 9) |
| jours gagnés vs service | **52** |
| jours perdus vs service | **5** |
| \|Δ`m`\| | médiane **0,0009**, maximum **0,0420** |

Les points qui bougent de façon lisible :

| Point | Jours marqués | Δ`m` | Δ`Tmh_norm` médiane | Δ`Tmh_norm` p95 |
|---|---|---|---|---|
| `LA PLAINE A RAON-SUR-PLAINE` | 16 | **+0,0420** | −0,0424 | **−1,0501** |
| `BIE6-8` | 17 | **+0,0151** | +0,0053 | **−0,8371** |
| `BIE46-5` | 5 | +0,0052 | −0,0453 | −0,0717 |
| `LGV11-8` | 2 | +0,0047 | +0,0213 | +0,0118 |
| `BIE27-9` | 3 | +0,0043 | −0,0225 | −0,0008 |
| `BIE31-4` | 3 | +0,0037 | −0,0337 | −0,0145 |

### C2 — Les six journées que le socle ne marque pas

Toutes sur `BIE40-3`, toutes en juillet. L'étape 4 les signalait sans les
nommer.

| Date | `T_eau_max − T_air` | `E_moy_rel` | `R_ampl_rel` | `E_max_rel` | Marche 2 ? |
|---|---|---|---|---|---|
| **2015-07-08** | 12,42 °C | 2,676 | **7,514** | **3,090** | **rattrapée** |
| 2015-07-09 | 10,57 °C | 2,192 | 3,837 | 1,961 | non |
| 2015-07-28 | 11,74 °C | 2,499 | **8,512** | 2,773 | non |
| 2015-07-30 | 13,10 °C | 2,855 | 4,425 | 2,540 | non |
| 2023-07-20 | 10,01 °C | 2,045 | 2,988 | 1,697 | non |
| 2023-07-22 | 10,91 °C | 2,280 | 3,314 | 1,771 | non |

**Aucune n'est loin du seuil** : `E_moy_rel` va de 2,04 à 2,86 pour un seuil à
3,0. Le socle les manque de peu, non par aveuglement, mais parce qu'elles
ressemblent aux autres journées chaudes de juillet de ce point — comportement
attendu d'un critère relatif, et raison d'être de la marche 2.

**La marche 2 en rattrape une, et une seule.** Le 28 juillet 2015 a pourtant
un `R_ampl_rel` de 8,51 : c'est le **second membre**, le niveau `E_max`, qui
le retient à 2,77. La conjonction fait exactement ce pour quoi elle a été
choisie — exiger deux signatures **différentes**, une forme et un niveau, et
ne pas se contenter de l'une.

**Le détecteur complet en manque donc 5, pas 6.** L'écart entre les deux
comptes n'est pas un effet des correctifs : l'étape 4 mesurait le socle seul.

### C3 — Ce que l'écart change dans la spécification

**Aucune conclusion.** Sur 30 des 31 points, `Δm` et `ΔTmh_norm` sont
identiques à la sixième décimale entre les deux tables.

| | |
|---|---|
| variation de \|Δ`m`\| | médiane **0**, maximum **0,000401** |
| variation de \|Δ`Tmh_norm` p95\| | médiane **0**, maximum **0,0060** |
| points où `Δm` varie | **1 seul : `BIE40-3`**, de −0,001311 à −0,000910 |

Et cette variation unique ne vient **pas** des correctifs : elle vient de ce
que l'étape 4 mesurait le socle seul, tandis que cette table mesure l'union
des deux marches — la marche 2 ajoute une journée sur ce point.

**Pourquoi la table a tenu.** Ses colonnes sont des **différences entre deux
rejeux de la même chaîne**. Un correctif qui déplace les deux côtés du même
montant ne déplace pas leur différence. Pour `Δm` c'est structurel : `m` ne
dépend pas de `Tmh` (D42), donc les correctifs 2 et 8 ne peuvent pas
l'atteindre, et le correctif 5 ne change pas l'échantillon.

**Trois corrections de présentation** ont néanmoins été portées au §5 de la
spécification, qui est mis à jour :

1. le réglage est nommé pour ce qu'il est — **l'union des deux marches**, et
   non le socle seul ;
2. la médiane de \|Δ`m`\| passe de **0,0010 à 0,0009** ;
3. les **six journées** sont désormais **listées**, avec la mention de celle
   que la marche 2 rattrape.

---

## §4 — Journal des verdicts (D43)

`docs/VERDICTS_MODIFIES.md`, section « correctif 8 ».

**Aucun verdict de vulnérabilité ne bouge** : ni SGVT, ni `n_jours_aigus`, ni
`pts_aigu`, ni score de fraie, ni statut de normalisation, sur aucun des
32 points.

**Trois pourcentages de stress chronique** se déplacent, tous dans
`jeu_bienne` : `BIE42-7` 10,999 → 11,066 %, `BIE51-0` 8,540 → 8,264 %,
`BIE56-1` 9,722 → 9,783 %. **Aucun ne change de catégorie**, et `n_jours_tmh`
ne bouge sur aucun point.

**Pourquoi c'est attendu.** Le correctif 8 déplace `Tmh` de 0,275 °C en
médiane sur les journées touchées, et de 1,099 °C au maximum — sur **0,70 %**
des journées. Pour qu'un verdict change, il faut qu'une journée franchisse un
seuil : c'est ce qui s'était produit à l'étape 6 pour `BIE5-9`, dont l'unique
journée aiguë était à 0,365 °C du seuil. Ici, aucune journée ne se trouvait
assez près d'un seuil aigu pour que le déplacement l'y fasse basculer. Le
stress chronique, lui, se compte en proportion de journées : il bouge d'un
dixième de point sans changer de classe.

**Une abstention cesse**, et elle est consignée bien qu'elle ne soit pas un
verdict : les trois journées de `LA PLAINE` des 29–31 décembre 2009 perdent
leur statut `non_diagnosticable`. Ce que l'écran dira du point s'en trouve
modifié.

---

## §5 — Alternatives fermées

### Alternative 1 — `Delta_TMm_liss` sur le calendrier de la station d'air

Le défaut miroir du correctif 8, `core.py:310`.

| | |
|---|---|
| valeurs déplacées | **854 sur 67 392 (1,27 %)** |
| points concernés | **32 sur 32** |
| écart maximal sur l'anomalie | **4,790 °C** |
| écart maximal répercuté sur `T_norm` | **1,939 °C** |

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — ne rien changer (retenue)** | `05_anomalies.csv` reste figé ; le défaut est nommé dans le code, avec ses chiffres | D47 porte sur `Tmh` et sur `Tmh` seulement. Un correctif fait une chose, et celui-ci serait **plus large** que le correctif 8 : 854 valeurs contre 473, tous les points contre 22 |
| **B — corriger** | `05_anomalies.csv`, `07_t_norm.csv` et `08_scores.csv` bougent ; des verdicts peuvent changer, l'écart sur `T_norm` atteignant 1,94 °C | l'argument de fond est le même que celui de D47, et il est symétrique : une grandeur d'air ne doit pas dépendre de la complétude de l'eau |

*Je retiens A, faute de mandat, et je signale que c'est la branche B qui
rendrait vraie la déclaration d'artefacts de cette étape sur
`05_anomalies.csv`. L'écart de 1,94 °C sur `T_norm` est du même ordre que
celui qui a fait basculer `BIE5-9` à l'étape 6 : cette correction est
susceptible de déplacer des verdicts, et mérite son étape.*

### Alternative 2 — `Tmm30j` (`indicateurs.py:55`)

Moyenne maximale sur 30 jours de la température d'**eau**, calculée sur les
seules journées appariées à l'air, et sur un index **positionnel**. Deux
défauts, aucun corrigé.

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — ne rien changer (retenue)** | l'indicateur reste tel quel | il est en **aval de `T_norm`**, hors de la chaîne dont les correctifs 2, 5 et 8 répondent ; et il porte deux défauts de natures différentes, qui ne se corrigent pas du même geste |
| **B — corriger les deux défauts** | les indicateurs de `08_scores.csv` bougent | il faudrait une étape qui traite l'aval, avec sa propre déclaration d'artefacts |

*Je retiens A. Non mesuré à cette étape : la mesure appartient à l'étape qui
traitera l'aval.*

---

## §6 — Ce qui reste ouvert

- **`Delta_TMm_liss`** porte le défaut miroir du correctif 8 : 854 valeurs,
  32 points, jusqu'à 1,94 °C sur `T_norm`. Nommé dans le code, chiffré, non
  corrigé (§5, alternative 1).
- **`Tmm30j`** porte le même défaut plus celui de l'index (§5, alternative 2).
- **Le détecteur de plateau** (`qc.py:129`) porte le défaut d'index ; **D46**
  le rattache au correctif 1.
- **Le défaut de `qc.py:32-36`** relevé à l'étape 5 reste dans le même état.
- **`MOTIF_EAU_ABSENTE`** reste déclaré non exercé.
- **L'affichage de la dégradation déclarée est différé (D48)** ; ses textes
  continuent de s'écrire dans la spécification, §1.5.
- **La spécification est amendée, non implémentée.** Le correctif 1 et la
  règle de validité restent à écrire.
