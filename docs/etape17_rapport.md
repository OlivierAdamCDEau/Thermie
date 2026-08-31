# THERMIE_BIO V4.6 — Rapport d'étape 17

**Objet.** Rassembler toute la dégradation déclarée en un bloc unique (D48),
porter le statut de validité dans les livrables (D68), et fermer I11 (D93).

**Ce qui a rendu l'étape possible n'était pas prévu par la commande.** L'état
du détecteur de mise hors d'eau était **imprimé et perdu** : sur trois jeux du
corpus sur six, aucune journée n'est écartée, `marche_active` n'apparaît alors
nulle part, et l'écran affichait « Aucun artefact détecté » — exactement ce
qu'il aurait affiché si le détecteur n'avait pas tourné. **Le contrôle qualité
retourne désormais ce qu'il a fait.**

---

## Artefacts (D34, D54, D63) — motifs et constats

| Pose | Artefact | Type (D63) | Déclaré | Verdict du motif | Constaté |
|---|---|---|---|---|---|
| **1 — D93** | `03_journees_ecartees.csv` | projection | doit bouger — une colonne | **juste** | **6/6, 0 valeur changée** |
| | `01_colonnes_retenues.json` | **métadonnée** | **FIGÉ** — le marquage reste hors de `res.df` | **juste** | **FIGÉ** |
| | `02`, `04`, `05`, `06`, `07`, `08`, `10`, `00` | valeurs et métadonnées | figés | **juste** | **FIGÉS** |
| | `99_log.txt` | trace | *(non déclaré — §0)* | **manqué** | **1/6 bouge** |
| **2 et 3** | tous sauf `99_log.txt` | — | **FIGÉS** — l'affichage ne touche aucun calcul | **juste** | **65/66 FIGÉS** |
| | `99_log.txt` | trace | **mobile, numéros de ligne (D80bis)** — déclaré avant la pose | **juste** | **1/6, 1 ligne** |

**Le motif des livrables, vérifié avant la pose.** La pose 3 touche
`livrables.py`, que le harnais n'appelle pas — relevé de l'étape 1, §1.5.
Vérifié : **aucun appel** à `construire_docx_bytes` ni
`construire_xlsx_bytes` dans `tests/reference/` ni dans `orchestrator.py`, et
`date.today()` reste confiné à `livrables.py:185` et `:478`, jamais atteints.
La pose 3 **ne peut pas** déplacer un artefact.

---

## §0 — Carnet de bord

### Le détecteur ne pouvait pas dire qu'il avait tourné

`marquer_qualite` calcule si le second niveau d'examen est disponible, combien
de journées chaque marche marque, le seuil d'amplitude d'air dérivé, et
combien de journées elle s'abstient de juger. Puis elle **imprime tout cela et
le perd**. Rien ne le retourne.

Mesuré sur le rejeu de l'étape 16 :

| Jeu | Lignes de contrôle qualité | `marche_active` lisible ? |
|---|---|---|
| `jeu_02`, `jeu_04`, `jeu_bienne` | 17, 1, 120 | oui |
| **`jeu_03`, `jeu_05`, `jeu_exemples_v45`** | **0** | **AUCUNE — le détecteur est invisible** |

**Sur la moitié du corpus, l'écran ne pouvait pas distinguer « le détecteur a
tourné et n'a rien trouvé » de « le détecteur n'a pas tourné ».** Il affichait
`st.success("Aucun artefact détecté.")` dans les deux cas — une attestation là
où il fallait, dans un cas, une alerte.

C'est très exactement ce que le principe de l'étape interdit, et la commande
avait raison de le poser comme l'exigence la plus importante. Sans cette
correction, le bloc D48 aurait été rédigé sur des données qui n'existaient pas.

**L'adaptateur habituel ne pouvait rien.** Les correctifs 3, 5, 10 et 12 ont
tous séparé une fonction enrichie d'une vue héritée. Ici le diagnostic **n'est
pas dérivable** de la table de marquage : « le second niveau est-il
disponible ? » ne se lit pas dans un tableau de journées, et un jeu sans
journée marquée n'en porte aucune trace. `marquer_qualite` reçoit donc un
dictionnaire **facultatif** qu'elle remplit — aucun appelant existant ne
change, et celui qui veut le diagnostic le demande.

### J'ai manqué D80bis sur la pose 1, après l'avoir appliquée deux fois

La commande ne déclarait pas `99_log.txt` pour la pose 1, et je ne l'ai pas
ajouté. Il a bougé : la trace figée de `BIE35-5__NA` est passée de la ligne 203
à la ligne 204, parce que l'appel modifié dans `orchestrator.py` a gagné une
ligne.

Le motif est **mécanique** — toute insertion en amont d'un point d'appel figé
déplace son numéro — et je l'avais correctement appliqué aux étapes 15 et 16.
Il n'y a pas d'excuse : **une règle mécanique doit être appliquée
mécaniquement, surtout quand la déclaration de commande ne la rappelle pas.**

Pour les poses 2 et 3, je l'ai déclarée **avant** : la trace est passée de 204
à **211**, et c'est le seul mouvement de tout l'artefact.

### Deux contrats rompus, tous deux attrapés par le vrai test

**Le premier** : `_encadre` et `_xl_bloc` de `livrables.py` attendent un
**dictionnaire** `{titre, verdict, niveau, lignes}`, pas une liste. Je leur ai
passé des listes.

**Le second** : `statut_normalisation` rendait une chaîne, alors que les deux
constructeurs ont besoin du **niveau** pour choisir une couleur.

Les deux ont été trouvés en **construisant réellement le Word et le classeur**
sur deux points contrastés, pas en relisant. Ni `ast.parse`, ni le harnais — qui
n'appelle jamais ces constructeurs — ne pouvaient les voir.

**La leçon vaut au-delà du cas :** cette étape est la première à toucher du
code que le harnais de non-régression **ne couvre pas**. Le rejeu aurait rendu
« 66 artefacts figés » sur une application dont le Word plantait. Un périmètre
non couvert exige son propre test, et l'écrire fait partie de la pose.

### Le bloc a été relu sur ses cas, pas sur son code

Rendu sur trois points choisis pour être contrastés — un sans rien à signaler,
un dont les horodatages sont détruits, un dont un tiers de la chronique est
perdue. C'est cette lecture, et non la relecture du code, qui a montré qu'un
cas de la spécification manquait : le **détecteur dégradé**.

`BLE3-0` porte `TN`, `TX` et `T_eau_min` : le second niveau se déclarait donc
**disponible**. Mais toutes ses mesures sont datées à minuit, si bien que son
minimum et son maximum du jour sont le même point et que la forme du signal
journalier vaut zéro par construction. La spécification prévoyait ce cas ;
mon premier jet ne le rendait pas. Ajouté, et le point passe de « réserve » à
« point d'attention ».

---

## §1 — D44 et D76

**D44** — onze entrées avant, **douze après** : `redaction.py` rejoint la
liste, au titre de l'extension de périmètre de D68. Exactement les douze
déclarées, aucun fichier de code en CRLF, retour **0**.

**D76** — les deux contrôles passent aux deux bouts. Retour **0**.

---

## §2 — D93 : `n_mesures` cesse d'être une valeur morte

`n_mesures` était produit à chaque lecture depuis l'étape 1 et **relu nulle
part** — c'est I11 au registre. Il rejoint la table de complétude, **à côté du
trou maximal**.

**Pourquoi à côté du trou, et non seul.** La spécification du correctif 12 a
établi que l'effectif et le trou mesurent des choses différentes, et que le
trou est le bon critère. Elle a aussi établi que les journées signalées portent
**12 mesures sur 24** en médiane — un fait qu'on ne peut énoncer *que* si
l'effectif est lisible à côté du trou. Deux journées de même trou et
d'effectifs très différents cessent d'être indiscernables.

**La prédiction tient**, y compris son point le plus délicat :

| | |
|---|---|
| `03_journees_ecartees.csv` | 6/6 bougent, **0 valeur changée** — une colonne |
| **`01_colonnes_retenues.json`** | **FIGÉ** |
| tous les artefacts de valeurs | **FIGÉS** |

`01` est figé **parce que** la table de complétude vit hors de `res.df` — c'est
le piège du §0 de l'étape 16, pris dans l'autre sens. Les quatre journées
signalées de `jeu_02` portent désormais 12, 10, 14 et 15 mesures : elles ne
sont pas pauvres, elles sont groupées, et l'artefact le dit.

---

## §3 — L'inventaire des états déclarés, et l'écran

### L'inventaire, refait sur les sources

Recensé dans les trois spécifications et dans `METHODO.md`, et non repris de
l'aide-mémoire.

| État déclaré | Où il était spécifié | Rendu |
|---|---|---|
| Détecteur — marche active, marche 2 indisponible | `SPEC_detecteur_et_validite.md` §1.4 | **oui** |
| Détecteur — **dégradé**, sans structure infra-journalière | §1.4, 3ᵉ cas | **oui — manquait à mon premier jet** |
| Détecteur — **inactif**, aucun air exploitable | §1.4, 4ᵉ cas | **oui** |
| Journées sans température d'air | §1.5 | **oui** |
| Journées sans densité calendaire | §1.5 | **oui** |
| Année civile entièrement absente | §1.5, condition de fait | **oui** |
| Journées d'été retirées | §1.5, condition de fait | **oui** |
| Rejet du coefficient estival | §2.4 | **oui** |
| Rejet du coefficient saisonnier, par espèce | §2.4 | **oui** |
| **Repli du coefficient faute d'effectif** | D67, étape 12 | **oui** |
| Mesures écartées à la lecture | correctif 10 | **oui — zéro sur ce corpus, et ce zéro se voit** |
| Complétude, et l'indéterminable | `SPEC_completude_journee.md` §6 bis | **oui** |
| Normales calculées sur trop peu d'années | `diag_normales` | **oui — n'était dans aucune spécification** |
| Note sur la moyenne mobile de 30 jours | D87 | **oui** |

**Deux entrées ne figuraient dans aucune des trois spécifications** et sont
venues de la relecture : l'avertissement sur le nombre d'années de normales, et
le repli du coefficient. L'aide-mémoire de la commande ne les portait pas non
plus.

### Ce que l'écran fait, et ce qu'il ne fait pas

Un onglet dédié, **« Ce qui a été vérifié »**, placé en deuxième position —
juste après la synthèse, avant les résultats. Il porte :

- **une ligne de résumé** en tête, colorée selon le pire niveau, pour qu'un
  lecteur qui n'ouvrira jamais le détail sache s'il devrait l'ouvrir ;
- **les sept blocs, toujours tous les sept**, dans un ordre fixe, chacun avec
  son niveau : `✓ vérifié`, `○ réserve`, `⛔ point d'attention`.

**Un contrôle qui n'a rien trouvé rend un bloc `✓` qui le dit** :

> *Ce qu'il a trouvé :* **aucune journée suspecte.** Le contrôle a bien tourné :
> ce zéro est un résultat, pas une absence de contrôle.

**Un contrôle qui n'a pas pu se prononcer rend un bloc `⛔` qui le dit
autrement** :

> ⚠ **Contrôle non applicable — sans objet, et non « rien à signaler ».**
> […] **Une absence de signalement ne vaut pas quitus ici** : elle signifie que
> personne n'a pu regarder.

Les trois cas rendus sur des points réels :

| Point | Résumé |
|---|---|
| `Gorze` | 3 réserves, 4 contrôles sans rien à signaler. **Aucun point d'attention.** |
| `BLE3-0` | **2 points d'attention**, 3 réserves, 2 contrôles sans rien à signaler |
| `La Moselle à Hielle` | **1 point d'attention**, 5 réserves, 1 contrôle sans rien à signaler |

**Sobriété.** Aucun numéro de décision, aucun nom de fonction, aucun terme
interne. Trois niveaux et trois signes seulement. L'ancien message de l'onglet
QC, « Aucun artefact détecté », devient « Aucun détecteur n'a écarté
d'enregistrement », suivi d'un renvoi vers le bloc — parce que le premier
énoncé était une conclusion et le second un constat.

**Aucun seuil n'est introduit.** Le niveau d'un bloc dépend de **faits** — un
contrôle n'a pas pu tourner, une année civile est absente, un coefficient a été
rejeté — jamais du franchissement d'une valeur conventionnelle.

---

## §4 — Les livrables

### Le trou qu'on ferme

`BLE3-0` publiait un SGVT, des pourcentages de stress et des journées de
vulnérabilité **typographiquement identiques** à ceux d'un point normalisé,
alors que sa relation air-eau a été rejetée et que ses températures sont
**brutes**. Rien, dans le Word ni dans le classeur, ne le disait.

### Ce qui est ajouté, et où

| Livrable | Ajout | Position |
|---|---|---|
| **Word** | chapitre **1.7 « Ce qui a été vérifié, et ce qui ne l'a pas été »** — les sept blocs, en encadrés | **après** les données, **avant** les résultats |
| **Word** | encadré **« Statut de la correction climatique »** | **avant** les chiffres de vulnérabilité qu'il qualifie |
| **Classeur** | feuille **`07_Etats_declares`** — les mêmes blocs | avant la feuille de synthèse |
| **Classeur** | même encadré de statut en tête de `02_Thermie_SGVT` | avant les chiffres |

**Le texte est écrit une seule fois**, dans `redaction.py`, et rendu trois fois.
`etats_declares_texte` n'en produit pas une seconde version : elle retire les
marques d'emphase. Deux rédactions parallèles finiraient par diverger, et c'est
le livrable qui porterait la version périmée.

### Ce qui n'est pas ajouté, et pourquoi

- **Rien dans `06_SYNTHESE`.** Son en-tête est **invariant par construction** —
  la feuille annonce elle-même que « les lignes de plusieurs stations peuvent
  être empilées telles quelles ». Y ajouter une colonne casserait l'empilement
  avec des stations produites par une version antérieure. Le statut y a sa
  place, mais avec une décision sur le schéma : c'est une alternative du §6.
- **Rien dans les figures.** Un avertissement gravé dans une image ne se
  retrouve pas, et les figures sont régénérées à l'écran.
- **Rien dans `exports.py`.** Il ne porte que le classeur de détail de la
  fraie ; le statut par espèce figure déjà dans le bloc général. La commande
  autorisait à le toucher ; il n'y avait pas lieu.

**Vérifié en construisant** : le Word et le classeur se produisent sur
`BLE3-0` (statut *point d'attention*, températures brutes) et sur `Gorze`
(statut *vérifié*, températures corrigées), et la feuille `07_Etats_declares`
est présente dans les deux.

---

## §5 — Les limites, préparées et non affichées (tâche E)

Vérifié dans le code et dans le corpus, point par point. **Une remarque de
forme d'abord** : la liste de la commande en compte cinq, mais « normales
pré-calculées » et « branche `EcartNormales` » **sont le même comportement** —
l'un nommé par son entrée, l'autre par son chemin de code. Il y en a donc
**quatre**.

| Comportement | Constat | Ce qu'on ne peut donc pas affirmer |
|---|---|---|
| **Débit désinfluencé** | aucun jeu du corpus n'en porte ; l'interface l'accepte (`app.py:381`) | Que la lecture PNDA désinfluencée est juste. Le comblement des trous du désinfluencé par l'influencé, son seuil d'écart médian et la distribution qui en résulte **n'ont jamais été exercés**. |
| **Normales pré-calculées** (`EcartNormales`) | `app.py:379` passe `None` ; la branche `orchestrator.py:131-133` n'est jamais prise | Que l'outil sait lire un fichier de normales fourni. Cette branche court-circuite le calcul des normales, **et donc le correctif 11** : un fichier pré-calculé porterait le décalage bissextile sans qu'on le sache. |
| **Export d'air multi-stations** | les **5** fichiers d'air du corpus portent **une seule station** chacune | Que la sélection de station, son tri par couverture et sa restitution fonctionnent. Sur un fichier multi-stations, **le choix de la station change tous les résultats** et n'a jamais été vérifié. |
| **Garde-fou du MAD nul** | jamais déclenché — vérifié dans le diagnostic, **0 point** | Que le comportement de l'outil est correct sur une chronique parfaitement plate. La branche existe, elle est documentée, **elle n'a jamais tourné**. |

*Ces quatre lignes sont préparées pour le document de clôture de l'étape 18.
Elles ne sont pas affichées : ce ne sont pas des états de ce point de mesure,
ce sont des limites de l'outil.*

---

## §6 — Alternatives fermées

### Alternative 1 — Le statut dans `06_SYNTHESE`

La feuille de synthèse est la seule qui serve à **comparer des stations entre
elles**. C'est donc celle où l'absence de statut est la plus dangereuse : deux
lignes empilées, l'une normalisée et l'autre non, se lisent comme comparables.

| Branche | **A — ne rien ajouter** | **B — une colonne de statut** | **C — une colonne, et le schéma versionné** |
|---|---|---|---|
| empilement avec les versions antérieures | **conservé** | **cassé** — l'en-tête n'est plus invariant | conservé, si le lecteur sait lire deux schémas |
| risque de lecture | deux stations non comparables se lisent comme comparables | aucun | aucun |
| coût | nul | nul en code, réel en compatibilité | une convention de version à définir |

**Ce qui les départage.** La feuille annonce elle-même son invariance ; la
casser sans le dire serait exactement le genre de silence que ce chantier
combat. Mais **A laisse un risque de lecture sur la seule feuille destinée à la
comparaison**, ce qui n'est pas neutre non plus.

*J'ai retenu A pour cette étape, parce que D68 restreint l'extension à la
déclaration et qu'un changement de schéma n'en est pas une. Je signale que A
laisse le trou ouvert là où il est le plus béant, et que C le fermerait au prix
d'une décision de schéma — qui a sa place à la clôture, avec D83.*

### Alternative 2 — Le bloc doit-il être affiché ailleurs qu'en onglet ?

| Branche | **A — un onglet dédié + une ligne en synthèse** | **B — un bandeau permanent en tête de page** |
|---|---|---|
| visibilité | l'alerte est résumée en synthèse, le détail à un clic | tout le monde la voit, toujours |
| sobriété | préservée | un bandeau permanent devient un décor qu'on cesse de lire |
| ce qui se perd | un lecteur pressé ne lit que le résumé | rien |

**Ce qui les départage** : la commande le dit — « un bloc que personne ne lit
ne vaut pas mieux qu'un silence ». Un bandeau toujours présent, sur un outil
où la plupart des points n'ont qu'une ou deux réserves ordinaires, cesserait
d'être lu en une semaine. **A retenue**, avec la ligne de résumé colorée en
synthèse comme garde-fou : elle change de couleur quand il y a un point
d'attention.

---

## §7 — Ce qui reste

**D83 — le rebasage de clôture**, sur décision explicite.

Et, hors mandat, déjà placés : **D87** (la moyenne mobile de 30 jours, dont la
note est **désormais affichée**), **D88** (la colonne d'heure non reconnue),
**D94** (le critère de trou appliqué à l'amplitude), les **quatre**
comportements que le corpus n'exerce pas (§5), et l'alternative 1 ci-dessus.

**D48 et D68 sont clos.** I11 aussi.
