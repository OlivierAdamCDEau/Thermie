# THERMIE_BIO V4.6 — Rapport d'étape 7

**Objet.** Installer le contrôle permanent D44, mesurer les deux suppressions
silencieuses qui subsistaient dans la chaîne, poser le **correctif 5**
(jointure gauche eau/air) et le **statut de densité** (D45), et ouvrir le
journal des verdicts modifiés (D43).

---

## Artefacts pour cette étape (D34, redéclarés)

| Artefact | Déclaré | Constaté | |
|---|---|---|---|
| `00_format_detecte.json` | figé | **figé** | |
| `01_colonnes_retenues.json` | figé | **figé** | |
| `02_effectifs.csv` | **doit bouger** | **6/6 bougent** | `journees_perdues_hors_qc` tombe de **636 à 0** ; deux colonnes nommées la remplacent |
| `03_journees_ecartees.csv` | **doit bouger** | **3/6 bougent** | les trois jeux qui portent des pertes ; +18 lignes, motifs et températures renseignés |
| `04_normales.csv` | figé | **figé** | |
| `06_coefficients.csv` | **figé** (prédiction) | **figé** | **la prédiction tient — voir §3** |
| `10_parametres.json` | figé sauf si un motif devient paramétrable | **figé** | aucun motif n'est devenu paramétrable |
| `05_anomalies.csv` | peut bouger, à chiffrer | **figé — 0 valeur** | |
| `07_t_norm.csv` | peut bouger, à chiffrer | **figé — 0 valeur** | |
| `08_scores.csv` | peut bouger, à chiffrer | **figé — 0 valeur** | témoin hors périmètre : aucun verdict ne bouge |
| `99_log.txt` | non déclaré | 1/6 bouge | **2 lignes**, deux numéros de ligne de la trace figée |

**Ma lecture du code ne contredit pas cette déclaration** — c'est la première
étape où c'est le cas, et la prédiction falsifiable en est la raison : elle
portait sur le seul point où le doute était permis, et elle a été vérifiée
plutôt que supposée.

*Les « 3/6 » et « 6/6 » se lisent par jeu. Trois jeux seulement portent des
journées effacées ; les trois autres n'ont rien à voir bouger dans `03`.*

---

## §0 — Carnet de bord

### Le harnais savait ce que l'application taisait

En ouvrant `art_03` pour y brancher le marquage, j'ai trouvé ceci, écrit à
l'étape 1 :

> `fusion_eau_air` — la jointure interne de `core.fusionner:85` supprime les
> journées absentes de la chronique d'air. **V4.5 n'en trace aucune ; le
> harnais la déduit** en comparant à `res.df_air`.

Le harnais compensait donc depuis le début une suppression que l'application
ne déclarait pas. Il la déduisait — correctement, mais par soustraction
d'ensembles, sans pouvoir dire ni la température de l'eau ce jour-là, ni le
motif autrement qu'en le devinant.

C'est exactement ce qu'un harnais ne devrait pas avoir à faire, et cela
change la nature du correctif 5 : il ne s'agit pas d'ajouter une information
nouvelle, mais de **déplacer une connaissance du harnais vers
l'application**. Le harnais cesse de déduire et lit ; les colonnes
`T_eau_moy` et `T_eau_max`, jusqu'ici vides sur ces lignes, se remplissent ;
et `origine_motif` passe de « déduction du harnais » à
« `core.fusionner_marque` — colonne motifs de la table de marquage ».

### Trois causes possibles, une seule réelle — les deux autres codées quand même

La jointure et le `dropna` qui la suit pouvaient effacer une journée pour
trois raisons distinctes. Mesurées séparément avant correction :

| Cause | Journées |
|---|---|
| aucune ligne d'air à cette date | **636** |
| ligne d'air présente, `T_air` vide | **0** |
| `T_eau_moy` vide malgré une journée retenue par le QC | **0** |

Les deux dernières n'existent pas sur ce corpus. J'ai néanmoins écrit leur
branche et leur motif propre — `MOTIF_EAU_ABSENTE` en particulier — parce
qu'une cause absente du jeu d'essai n'est pas une cause impossible, et que
l'étape 6 a montré ce que coûte une invariance qui repose sur une propriété
des données. Le motif existe, il est distinct, il est déclaré non exercé.

### Un patch a de nouveau buté sur les fins de ligne — et cette fois l'ancre l'a arrêté

`tests/reference/build_reference.py` est en **CRLF**, contrairement aux
fichiers de `app/`. Mon script de correctif a échoué à trouver son ancre :
il cherchait `\n` là où le fichier porte `\r\n`.

Il a échoué **avant** d'écrire quoi que ce soit, parce que chaque
substitution est précédée d'une assertion sur son ancre. C'est la
contrepartie utile de l'incident CRLF de l'étape 6 : depuis, mes patchs ne
remplacent rien sans avoir vérifié qu'ils remplacent la bonne chose, et un
fichier dont les fins de ligne diffèrent de ce que j'attends fait tomber
l'assertion au lieu de produire un fichier à moitié modifié. Le script
normalise maintenant les fins de ligne à l'entrée et les restitue à la
sortie.

*(Deux tentatives de réparation du script ont elles-mêmes été abîmées par le
traitement des `\r\n` dans les documents heredoc du shell. C'est un piège
connu de cet environnement ; la parade est d'écrire le script comme fichier
plutôt que de le composer dans une ligne de commande, et d'exprimer les
caractères de contrôle par `chr(13)` et `chr(10)` plutôt que par des
échappements.)*

### Ce que je n'ai pas fait, et pourquoi

Le correctif 5 conserve toutes les journées d'eau, mais la chaîne de calcul
continue de tourner sur les seules journées **exploitables**. Une journée
d'eau sans air reste donc, pour le lissage de `Tmh`, un trou dans le
calendrier — alors que `Tmh` est une moyenne de température d'**eau** et ne
dépend pas de l'air.

C'est discutable, et c'est discuté : la question est mesurée et posée en
alternative fermée au §6, pas tranchée ici. La lisser sur la chronique d'eau
complète serait un **troisième correctif déguisé en effet du cinquième**, et
la méthode de ce chantier est qu'un correctif fait une chose.

---

## §1 — D44 : le contrôle permanent, et son verdict

`tests/reference/diff_app_ref.py`. Diff **octet** de `app/` contre
`ref/v4_5/`, avec pour chaque fichier le nombre de lignes et la **nature** de
la différence : contenu, fins de ligne, ou les deux. La liste constatée est
confrontée à la liste que l'étape déclare ; **un fichier qui diffère sans être
déclaré arrête l'étape** (code de retour 1).

La distinction contenu / fins de ligne n'est pas un ornement : à l'étape 6,
`qc.py` et `core.py` étaient en CRLF depuis l'étape 5 sans que rien ne le
signale. Aucune valeur n'en dépendait, mais `app/` avait cessé d'être
comparable octet pour octet à `ref/v4_5/` — un moyen de contrôle avait disparu
en silence, ce qui est pire qu'un contrôle qui échoue.

### Lancé AVANT toute modification de cette étape

```
  app/LISEZ-MOI.md                 ABSENT DE ref/v4_5
  app/thermie_debits/core.py       DIFFERENT   nature : CONTENU
  app/thermie_debits/qc.py         DIFFERENT   nature : CONTENU

  CONFORME — la liste constatee est exactement la liste declaree.
```

**Trois fichiers, et trois seulement** : `qc.py` (correctif 3 + R13),
`core.py` (correctif 2), et le `LISEZ-MOI.md` ajouté à l'étape 1 — absent de
`ref/v4_5/`, non exécutable, mais déclaré pour qu'il ne puisse pas se cacher.
**Aucun fichier n'est en CRLF.**

### Relancé à la fin

```
  app/LISEZ-MOI.md                 ABSENT DE ref/v4_5
  app/thermie_debits/core.py       DIFFERENT   nature : CONTENU
  app/thermie_debits/orchestrator.py  DIFFERENT   nature : CONTENU
  app/thermie_debits/qc.py         DIFFERENT   nature : CONTENU

  CONFORME — la liste constatee est exactement la liste declaree.
```

Un fichier de plus, `orchestrator.py`, déclaré : il appelle désormais
`fusionner_marque` et range la table de marquage dans `Resultats`. **Code de
retour 0.** Aucun CRLF n'a été introduit.

---

## §2 — Les deux mesures d'avant

*Ces mesures cessent d'être possibles une fois les correctifs posés : les
suppressions deviennent des marquages.*

### B1 — La jointure interne

`tests/reference/mesure_suppressions.py` →
`out/etape7/B1_jointure_par_point.csv`.

| | |
|---|---|
| points, journées retenues par le contrôle qualité | **32 points, 68 028 journées** |
| effacées sans trace par la jointure | **636 (0,93 %)** |
| points concernés | **23 sur 32** |
| points totalement épargnés | 9 sur 32 |

**La moyenne est trompeuse, et c'est tout le problème :**

| Point | Effacées | Part | Plus longue série continue | Années entièrement effacées |
|---|---|---|---|---|
| **`La Moselle à Hielle`** | **102 / 303** | **33,66 %** | **102 j** | **1** (2012) |
| **`LA PLAINE A RAON-SUR-PLAINE`** | **330 / 1 545** | **21,36 %** | **308 j** | **1** (2008) |
| `BLE3-0` | 7 / 121 | 5,79 % | 4 j | 0 |
| `FLU8-4` | 3 / 331 | 0,91 % | 3 j | 0 |
| `BIE46-5` | 8 / 1 180 | 0,68 % | 4 j | 0 |
| `BIE31-4` | 18 / 4 111 | 0,44 % | 5 j | 0 |

Les deux premiers cas méritent d'être lus en clair.

> **`La Moselle à Hielle`** perdait 102 de ses 303 journées **d'un seul
> tenant, du 6 juillet au 15 octobre 2012** : **tout son été**, et l'unique
> année civile que sa chronique couvre. C'est le point du jeu d'exemples de
> V4.5.
>
> **`LA PLAINE A RAON-SUR-PLAINE`** perdait **l'année 2008 en entier** — 220
> journées lues, 220 effacées, 0 retenue — puis 101 journées de 2009.

Répartition par année, pour ces deux points :

| Point | Année | Lues | Effacées | Part |
|---|---|---|---|---|
| `LA PLAINE` | **2008** | 220 | **220** | **100 %** |
| `LA PLAINE` | 2009 | 365 | 101 | 27,67 % |
| `LA PLAINE` | 2010 | 134 | 4 | 2,99 % |
| `LA PLAINE` | 2012 | 366 | 2 | 0,55 % |
| `LA PLAINE` | 2013 | 233 | 3 | 1,29 % |
| `La Moselle à Hielle` | **2012** | 102 | **102** | **100 %** |

Rien, nulle part, ne disait à l'utilisateur que son résultat portait sur les
deux tiers de sa chronique.

### B2 — La densité (D45)

`out/etape7/B2_densite_journees.csv`. **18 journées, 5 points.** Leur fenêtre
calendaire de sept jours contient de **1 à 3** jours réellement observés, là
où quatre sont exigés. La mesure reproduit celle de l'étape 6 après pose du
correctif 2, et donne le même compte.

---

## §3 — Le correctif 5, et la prédiction

### C1 — La jointure passe à gauche

`app/thermie_debits/core.py` :

```python
    complet = daily_eau_propre.merge(df_air, on="date", how="left",
                                     indicator="_jointure")
    dans_air = (complet["_jointure"] == "both").to_numpy()
```

`dans_air` reproduit ce que la jointure interne voyait, **sans avoir eu besoin
de l'exécuter** : le message d'erreur « aucun jour commun », figé comme
référence par D7, est ainsi conservé au caractère près. Le `dropna` qui
suivait devient un masque, `exploitable`, au lieu d'une suppression.

### C2 — Une journée sans air n'est pas une journée saine

Trois motifs, distincts entre eux et distincts de ceux du contrôle qualité :

| Constante | Motif | Exercé sur le corpus |
|---|---|---|
| `MOTIF_AIR_ABSENTE` | « température d'air absente à cette date (station air) » | **636 journées** |
| `MOTIF_EAU_ABSENTE` | « température d'eau absente malgré une journée retenue » | **0 — déclaré non exercé** |
| `motif_densite(7, 4)` | « densité calendaire insuffisante (< 4 jours observés sur 7) » | **18 journées** |

Le statut est `non_diagnosticable` : **ni retenue, ni écartée par le contrôle
qualité**. Le contrôle qualité les a *retenues* — elles sont saines. Les
ranger parmi les journées écartées imputerait à la sonde d'eau un manque qui
vient de la station d'air.

**Le troisième état créé vide au correctif 3 a donc ses premiers producteurs**
— et, comme D45 l'annonçait, ce ne sont pas des détecteurs.

### C3 — Ce que voit l'aval hors périmètre : rien de nouveau

Audit des consommateurs :

| Consommateur | Ce qu'il reçoit |
|---|---|
| `core.fusionner` | **conservée, signature et retour inchangés**, devenue l'adaptateur qui rend la première moitié du retour de `fusionner_marque` |
| `orchestrator.py:167` | **seul appelant de la fusion dans tout `app/`**. Appelle désormais `fusionner_marque` et range la table dans `res.marques_fusion` |
| `res.df` → `analyse_sensibilite`, `analyse_vulnerabilite`, `calcul_indicateurs`, figures | **mêmes lignes, mêmes colonnes, mêmes valeurs** |
| `app.py:438` → `figmod.fig_chronique(res.df, …)` | idem |

**Aucun consommateur ne reçoit de ligne à `T_air` vide.** La vérification n'est
pas une lecture de code : c'est le rejeu ci-dessous.

### La preuve : rejeu du correctif 5 contre le rejeu du correctif 2

Comparer à `tests/reference/` mesurerait l'effet **cumulé** des correctifs 2,
3 et 5, jamais celui du dernier. `tests/reference/comparer_rejeux.py` compare
donc le rejeu d'après au rejeu d'avant, **harnais identique des deux côtés**,
lignes appariées par leur clé.

```
  artefacts compares : 66
  figes              : 65
  qui bougent        : 1

    jeu_bienne/99_log.txt : -0 / +0 ligne(s), 2 valeur(s)
```

Les deux lignes :

| Avant | Après |
|---|---|
| `orchestrator.py", line 166, in run` | `orchestrator.py", line 175, in run` |
| `core.py", line 197, in analyse_sensibilite` | `core.py", line 371, in analyse_sensibilite` |

Même fichier, même fonction, même message : ce sont les numéros de ligne d'une
trace d'erreur figée, déplacés par le code ajouté. D36 les conserve
délibérément — c'est l'information, pas le bruit.

### La prédiction falsifiable : **elle tient**

> *« La jointure gauche ne doit PAS déplacer `06_coefficients.csv` : `df_ete`
> écarte déjà les lignes sans `T_air` par `dropna`, donc l'échantillon de
> régression est inchangé. »*

**`06_coefficients.csv` est figé sur les six jeux, au bit près.** Et avec lui
`05_anomalies.csv`, `07_t_norm.csv` et `08_scores.csv` — **0 valeur changée**.

La prédiction était plus forte que ce qu'elle affirmait, et le résultat le
confirme : l'échantillon de régression n'est pas seulement inchangé, c'est
**toute la chronique exploitable** qui l'est. Les journées que la jointure
effaçait n'entraient dans aucun calcul — c'est précisément ce qu'« effacer »
voulait dire. Les conserver ne les y fait pas entrer : elles restent hors de
la chaîne, mais **nommées**.

*Si `06` avait bougé, la jointure interne aurait fait autre chose que ce
qu'on croyait, et il aurait fallu le comprendre avant d'aller plus loin. Elle
ne faisait que ce qu'on croyait.*

### Ce que les artefacts disent maintenant

Le harnais lit la trace au lieu de la déduire. Même code des deux côtés, seul
le harnais change (`out/etape7/D_effet_harnais.txt`) :

| Artefact | Mouvement |
|---|---|
| `02_effectifs.csv` | **6/6** — deux colonnes ajoutées ; `journees_perdues_hors_qc` recalculée |
| `03_journees_ecartees.csv` | **3/6** — +18 lignes ; `motif`, `origine_motif`, `T_eau_moy`, `T_eau_max` |
| tout le reste | **figé** |

**Le chiffre qui ferme la boucle** : la colonne `journees_perdues_hors_qc`,
qui mesurait exactement les suppressions silencieuses, passe de **636 à 0**.

| | Avant | Après |
|---|---|---|
| `journees_perdues_hors_qc` (tous points) | **636** | **0** |
| `journees_non_diag_air_absent` | — | **636** |
| `journees_non_diag_densite` | — | **18** |

Et `03_journees_ecartees.csv` répartit désormais ses lignes ainsi :
`fusion_eau_air` **636**, `controle_qualite` **91**, `densite_calendaire`
**18**. Sur `LA PLAINE A RAON-SUR-PLAINE`, l'année 2008 apparaît enfin pour ce
qu'elle est : **220 journées lues, 0 retenue, 220 nommées** — au lieu de
disparaître.

---

## §4 — Le statut de densité, et les textes d'écran

### D45 dans le code

Les journées que le correctif 2 laisse sans `Tmh` prennent
`non_diagnosticable` avec `motif_densite(7, 4)`. Elles **restent dans la vue
exploitable** — elles y étaient déjà, avec leur `Tmh` vide.

Ce point mérite d'être justifié plutôt que subi : **les retirer déplacerait
`06_coefficients.csv`**. Trois des dix-huit tombent en septembre
(`BIE40-3` 2015-09-08, `BIE6-8` 2017-09-13 et 09-14), donc dans la fenêtre
juin–septembre sur laquelle `m` est estimé. Les sortir de `df` changerait
l'échantillon de régression, et l'étape déclare `06` figé. Leur statut est une
information **ajoutée**, pas une suppression de plus — ce que D45 demande
exactement : « elles restent dans la table de marquage et cessent de
disparaître sans trace ».

### Le bloc de dégradation déclarée

Rédigé dans la spécification, nouvelle **§1.5**, dans l'idiome des textes du
§1.4. Trois principes le gouvernent :

**1. Il est toujours affiché**, y compris quand rien n'est retiré. Un bloc qui
n'apparaît qu'en cas de problème apprend à l'utilisateur que son absence
signifie « rien à signaler » — alors qu'elle peut aussi signifier « personne
n'a regardé ».

**2. Il n'introduit aucun seuil.** Le texte ne se durcit pas au franchissement
d'une valeur conventionnelle : il s'enrichit de phrases dont la condition est
un **fait constaté** — une année civile entièrement retirée, des journées
retirées entre juin et septembre. Deux booléens qui se lisent sur les données
et ne se calibrent pas.

**3. Il ne dit jamais « écartées par le contrôle qualité ».**

Extrait — le cas de l'air absent :

> **Dégradation déclarée — `K` journées non diagnosticables sur `N` (`P` %).**
> *Motif :* température d'air absente à cette date (station air) — `K`
> journées.
> *La plus longue interruption continue :* `L` jours, du `d1` au `d2`.
> *Ce que cela retire :* ces journées d'eau ont bien été mesurées et le
> contrôle qualité les a retenues. Elles ne sont **ni écartées, ni
> défectueuses** : il leur manque une donnée qui ne vient pas de la sonde.
> Faute d'anomalie climatique, elles ne reçoivent pas de température
> normalisée, n'entrent pas dans le pourcentage de dépassement de seuil, et ne
> comptent pas dans les journées de vulnérabilité.
> *Ce qu'il faut en faire :* vérifier la station météo retenue. Une autre
> station couvrant la période rendrait ces journées au calcul.

Et la phrase que `LA PLAINE` et `La Moselle` auraient déclenchée :

> ⚠ **L'année `A` est entièrement absente du calcul** : ses `M` journées d'eau
> ont toutes été retirées faute d'air. Les résultats ne décrivent pas cette
> année-là. Toute lecture pluriannuelle — tendance, comparaison
> interannuelle, année de référence — porte sur les autres années uniquement.

Les cinq cas — aucune dégradation, air absent, année entière, journées d'été,
densité, les deux motifs — sont écrits en §1.5 de
`docs/SPEC_detecteur_et_validite.md`.

---

## §5 — Le journal des verdicts (D43)

`docs/VERDICTS_MODIFIES.md`, **cumulatif, jamais réécrit**, ouvert
rétroactivement.

**Correctif 2 (étape 6), section rétroactive.** Un seul changement de
conclusion : `BIE5-9`, `n_jours_aigus` 1 → 0, `pts_aigu` 1 → 0, **SGVT 3,167 →
2,500**. Quatre `pct_stress_chronique`, sans changement de catégorie. Et
**sept** lignes de fraie — non pas trois : l'étape 6 en mentionnait trois
parce que son diff était tronqué à l'affichage. Le relevé complet, obtenu en
appariant les lignes par point plutôt qu'en lisant la fin du diff, en donne
sept, sur `BIE0-3`, `BIE32-4`, `BIE5-2`, `BIE5-9`, `BIE50-5`, `BIE6-8` et
`TAC16-4`. **Le score `P` est identique dans les sept cas** : ce sont les
pourcentages publiés qui bougent, pas la note.

**Correctif 5 (étape 7).** **Aucun verdict publié ne change**, et c'est le
résultat attendu : un correctif de visibilité ne change pas ce qui est
calculé, il change ce qui est **dit** de ce qui ne l'est pas. S'il avait
déplacé un SGVT, c'est qu'il aurait fait autre chose que ce qu'il annonce.

---

## §6 — Alternatives fermées

### Alternative 1 — Lisser `Tmh` sur la chronique d'eau complète

`Tmh` est une moyenne de sept jours de température d'**eau**. Elle ne dépend
pas de l'air. Aujourd'hui, une journée d'eau parfaitement mesurée mais privée
d'air reste un **trou** dans le calendrier du lissage — le lissage dépend donc
de quelque chose qui ne le regarde pas, ce qui est le défaut même que le
correctif 2 a corrigé sur l'index.

Mesuré sans être appliqué (`out/etape7/ALT_lissage_eau_complete.csv`) :

| | |
|---|---|
| `Tmh` qui changeraient | **473 sur 67 392 (0,70 %)**, sur 22 points |
| écart maximal sur `Tmh` | **1,099 °C** |
| journées sans `Tmh` récupérées | **3 sur 18** |
| journées qui en perdraient un | **0** |

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — ne rien changer (retenue)** | le lissage reste sur les journées exploitables ; `05`, `07`, `08` restent figés | un correctif fait une chose. Lisser sur la chronique d'eau complète est un **changement de méthode**, pas un effet de la jointure gauche : il déplacerait 473 valeurs et trois verdicts de densité sans que l'étape 7 l'ait annoncé |
| **B — lisser sur l'eau complète** | `05`, `07`, `08` bougent ; 3 des 18 journées de densité redeviennent diagnosticables ; aucune n'est perdue | l'argument de fond est bon : `Tmh` ne devrait pas dépendre de l'air. Il mérite son propre correctif, sa propre déclaration d'artefacts et sa propre entrée au journal des verdicts |

*Je retiens A et m'y tiens jusqu'à instruction contraire. L'écart mesuré est
modeste (médiane bien au-dessous du dixième de degré, maximum 1,1 °C) mais il
n'est pas nul, et il toucherait 22 points sur 32.*

### Alternative 2 — Retirer les journées de densité de la vue exploitable

| Branche | Ce qu'elle implique | Ce qui la départage |
|---|---|---|
| **A — les garder (retenue)** | elles restent dans `df` avec un `Tmh` vide, marquées et comptées ; `06` reste figé | trois d'entre elles tombent en septembre, dans la fenêtre d'estimation de `m` : les retirer déplacerait `06_coefficients.csv`, que l'étape déclare figé |
| **B — les retirer** | `02`, `05` et `06` bougent | il faudrait que la commande lève le gel de `06` |

*Je retiens A. D45 demande qu'elles soient marquées et comptées, pas
supprimées — et c'est ce qui est fait.*

---

## §7 — Ce qui reste ouvert

- **Le détecteur de plateau** (`qc.py:129`) porte le défaut d'index du
  correctif 2. **D46 le rattache au correctif 1**, qui dégèlera `02`, `03` et
  `06`. Non exercé par ce corpus (0 verdict), consigné.
- **Le défaut de `qc.py:32-36`** relevé à l'étape 5 reste dans le même état.
- **`MOTIF_EAU_ABSENTE` est déclaré non exercé** : la branche existe, aucun
  point du corpus ne la déclenche.
- **La spécification est amendée, non implémentée.** Le correctif 1 et la
  règle de validité restent à écrire ; le bloc de dégradation déclarée est
  rédigé mais pas encore affiché par `app.py`.
- **L'alternative 1 attend un arbitrage** (§6).
