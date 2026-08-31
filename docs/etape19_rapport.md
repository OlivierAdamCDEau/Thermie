# Étape 19 — Éprouver le témoin là où il n'a pas été construit

Vérification seule. **Aucune modification applicative** : les onze sources de
`app/` sont, octet pour octet, celles de la livraison de l'étape 17
(`out/etape19/F_aucune_pose.txt`, 11 identiques, 0 divergente, retour 0).

---

## §0 — Carnet de bord

| | |
|---|---|
| Code exécuté | `app/` (`THERMIE_CODE=app`) |
| Poses applicatives | **aucune** |
| Règle du témoin (D96) | `tests/reference/temoin_regime.py`, **scellée avant tout chiffre** |
| Protocole d'épreuve | `tests/reference/eprouver_temoin.py`, **scellé lui aussi** |
| Intégrité `ref/` (D77) | 0 fichier de bytecode, `ref/` propre, retour 0 |
| Rejeux | 2 par point (détecteur allumé / éteint), corpus entier |

**Deux prémisses de la commande se sont révélées fausses à la mesure, et je les
corrige avant de répondre.** Les deux corrections sont établies au §4 et au §5 ;
elles ne changent rien à la question posée, mais elles changent la réponse.

1. `BIE35-5__NA` ne porte **aucune** journée marquée hors d'eau, et non quatre.
   Les quatre journées existent, mais elles relèvent d'un **autre contrôle**.
2. Le second verdict déplacé — La Canner à Vigy 1 — **figure déjà** dans
   `docs/VERDICTS_MODIFIES.md`. Il n'y a pas de lacune de D43 à combler.

**Un choix de méthode, pour qu'il soit visible.** Le protocole d'épreuve, une
fois scellé, s'est révélé lent : environ une minute par point, soit près d'une
heure sur le corpus entier. Je l'ai laissé tourner sans le retoucher. Un sceau
qu'on rompt pour gagner du temps ne vaut plus rien ; le coût de l'attente est le
prix de la garantie, et il est faible.

---

## §1 — La règle scellée

### Ce qu'elle mesure

Pour une journée J d'un point P, l'ensemble de référence est constitué des
journées de la chronique de **P lui-même**, à ± 7 jours calendaires du même jour
de l'année, **dans les autres années**. Aucun autre point n'intervient, aucune
valeur n'est importée (D15, D41).

| grandeur | définition | ce qu'elle dit quand elle est positive |
|---|---|---|
| **excursion** | `T_eau_moy(J) − max(T_eau_moy sur la référence)` | la journée est plus chaude que **tout** ce que le point a montré à cette saison |
| **découplage** | `écart(J) − q95(écart sur la référence)`, écart = `T_eau_moy − T_air` | l'eau s'écarte de l'air plus que dans 95 % de ses précédents |

**Verdict :** `artefact` si **les deux** sont positives ; `compatible` sinon ;
`indéterminable` s'il y a moins de 2 autres années ou moins de 10 journées de
référence, ou si l'air manque. Le témoin s'abstient et le dit (D100).

Exiger les deux n'est pas un ornement. Une année réellement chaude élève l'eau
**et** l'air ensemble : elle produit une excursion sans découplage, et la règle
la laisse passer.

**Le débit n'y figure pas (D98).** Il dit où est la rivière, pas où est la
sonde. À l'étape 18, pris pour un témoin d'exondation, il avait produit cinq des
six verdicts faux.

### Les deux morphologies (D97), classées et jamais exigées

| morphologie | `R_ampl` | ce que c'est | cas |
|---|---|---|---|
| **haute amplitude** | ≥ q90 du point | sonde nue, suit l'air, gagne en amplitude | `BIE40-3` (`R_ampl` > 1 : l'eau oscille plus que l'air) |
| **basse amplitude** | ≤ q10 du point | sonde immobilisée en milieu chaud, calme, inerte | LA PLAINE (`R_ampl` 0,13 – 0,20) |

**La morphologie ne participe pas au verdict, et c'est le cœur de la leçon de
l'étape 18.** Une même valeur basse de `R_ampl` signifie « rivière inerte, donc
vraie » ou « sonde immobilisée, donc fausse », selon un contexte que `R_ampl` ne
porte pas. Un témoin qui change de signe selon le cas ne peut pas voter. Il est
mesuré et publié **à côté** du verdict, pour décrire ce que le verdict a trouvé,
jamais pour l'établir.

*Conséquence pour le détecteur, consignée et non posée :* la marche 1 (socle
relatif sur l'écart eau–air) capte les deux morphologies, la marche 2
(conjonction sur l'amplitude) ne capte que la première. La marche 2 étant
**additive** — `marque = marche1 | marche2`, `qc.py:388` — elle ne peut pas
masquer ce que la marche 1 voit. Le déséquilibre 60/9 mesuré à l'étape 18 est
donc attendu, et sans conséquence sur ce qui est écarté.

### Le sceau, et ce qu'il garantit

```
ef98c126f69fa935624018e4f38c388c9a670eba08b57e02180f9d9738935b76
tests/reference/temoin_regime.py    10 508 octets

e78f370e7c7cba7844e70aceb359d78c755827122bd1abf27d5656f53886187e
tests/reference/eprouver_temoin.py  14 806 octets
```

Le **protocole** est scellé au même titre que la règle. Le seuil de spécificité
sans la définition de la population qu'il juge ne garantirait rien : il suffirait
de choisir la population après coup.

### Ce qui me ferait conclure que le témoin est spécifique — écrit avant de regarder

Soit **τ** la proportion de journées **non marquées**, appariées par point et par
saison, que le témoin classe `artefact` :

| τ | conclusion |
|---|---|
| **≤ 5 %** | **spécifique** — le témoin ne sonne pas au hasard ; sa réfutation des six journées de l'étape 18 tient |
| **5 – 20 %** | **partiellement spécifique** — la réfutation ne tient que pour les journées à forte marge ; celles à faible marge redeviennent indécidables |
| **≥ 20 %** | **non spécifique** — le témoin sonne sur des journées ordinaires : il ne prouve rien des six, et **la conclusion de l'étape 18 s'affaiblit** |

---

## §2 — L'épreuve, et le témoin de contrôle

### Ce que le témoin trouve, population par population

| population | journées | jugeables | `artefact` | proportion | rapport à τ |
|---|---:|---:|---:|---:|---:|
| **B.2 — contrôle** (non marquées, appariées) | 6 428 | 6 339 | 13 | **0,205 %** | — |
| B.1 — les 42 marquées non instruites | 42 | 38 | 16 | **42,1 %** | **× 205** |
| B.2 bis — voisines d'une marquée (± 7 j) | 354 | 308 | 47 | 15,3 % | × 74 |
| B.3 — les 27 de l'étape 18 *(pour mémoire)* | 27 | 26 | 19 | 73,1 % | — |
| reste du corpus (hors appariement) | 60 272 | 57 810 | 126 | 0,218 % | ≈ τ |

### Le verdict de spécificité, appliqué tel qu'il était écrit

**τ = 0,205 %.** Le seuil scellé était : ≤ 5 % spécifique.

> **SPÉCIFIQUE** — vingt-quatre fois sous le seuil. Le témoin ne sonne pas au
> hasard, et sa réfutation des six journées de l'étape 18 tient.

Le second signe, subordonné, est atteint aussi et de très loin : sur les
42 journées marquées que le témoin n'avait jamais vues, il classe `artefact`
**42,1 %**, soit **deux cent cinq fois** son taux sur des journées ordinaires.

Un troisième chiffre, que le protocole n'exigeait pas mais qui contrôle les deux
autres : sur les 60 272 journées du reste du corpus — points sans marquage,
saisons non appariées —, le témoin sonne à **0,218 %**. Son taux de fond est le
même partout. C'est ce qu'on attend d'un témoin dont le seuil est dérivé du
point traité, et cela rend τ crédible plutôt que chanceux.

### Ce que l'épreuve établit, et ce qu'elle n'établit pas

**Elle établit** que le témoin distingue les journées marquées des journées
ordinaires par un facteur de deux ordres de grandeur, sur une population qu'il
n'avait pas vue et selon un seuil fixé d'avance. La conclusion de l'étape 18 —
les six journées classées « événement thermique réel » sont des artefacts —
cesse d'être une conclusion valide et non prouvée.

**Elle n'établit pas** que le témoin ait raison journée par journée. Un taux de
fond de 0,2 % sur 6 339 journées de contrôle laisse **treize journées** que le
témoin signale sans qu'on sache si elles sont fausses ou si le détecteur les a
manquées. Le témoin est spécifique ; il n'est pas infaillible.

**Les 27 de l'étape 18 ne prouvent rien, et je le redis ici parce que leur
chiffre est le plus élevé du tableau.** 73,1 % d'`artefact` sur la population où
le témoin est né est une tautologie. Ce chiffre est publié pour être écarté :
c'est le seul service qu'il rende.

### Une remarque sur les voisines

Les journées situées à moins de sept jours d'une journée marquée — exclues du
contrôle primaire, et pour cette raison — sont classées `artefact` à **15,3 %**,
soit soixante-quatorze fois le taux ordinaire. L'exclusion n'était donc pas un
aménagement de confort : ces journées ne sont pas ordinaires. Elles appartiennent
pour la plupart aux mêmes épisodes, et c'est la tâche C qui les reprend.

---

## §3 — Les faux négatifs

Le témoin appliqué à **toutes** les journées du corpus, marquées ou non.

| | |
|---|---:|
| journées non marquées par le détecteur | 67 054 |
| dont le témoin signale `artefact` | **186** (0,28 %) |
| points concernés | 15 |
| journées marquées par le détecteur | 69 |

### Le total ne prouve rien ; le regroupement, si

Au taux de fond mesuré au §2 (0,205 %), le seul bruit produirait **environ 137**
journées signalées sur 67 054. On en observe 186. **L'écart global n'est pas une
preuve**, et il serait malhonnête de présenter 186 comme un compte de faux
négatifs.

Ce qui prouve quelque chose est la **structure** :

| | journées |
|---|---:|
| isolées ou par deux — indiscernables du bruit | 52 |
| **en épisodes de trois jours consécutifs ou plus** | **134** *(13 épisodes)* |

Un bruit à 0,2 % ne produit pas treize épisodes multi-journaliers. **Ce sont ces
134 journées qui constituent le résultat.**

### La cause structurelle : la fenêtre du détecteur

| | journées |
|---|---:|
| **hors** de la fenêtre juin–septembre du détecteur | **95** |
| dans la fenêtre, donc examinées et non marquées | 91 |

**Plus de la moitié des journées signalées sont hors de la fenêtre où le
détecteur regarde.** Il ne les a pas manquées : il ne pouvait pas les voir. Et
le mois le plus touché est **mai, avec 66 journées** — le mois où l'on pose les
sondes.

### Ce que trois points montrent ensemble

| point | jeu | station d'air | signalées | × fond |
|---|---|---|---:|---:|
| SN 21069646 – La Canner à Vigy 1 | jeu_04 | 57465001 | 34 | × 14,4 |
| Le ruisseau de Gorze à Gorze | jeu_03 | 57039001 | 25 | × 7,7 |
| Le ruisseau de la Flotte à Château-Voue | jeu_05 | 57587003 | 15 | × 4,8 |

Trois bassins différents, trois stations d'air différentes — un défaut commun de
la chronique d'air est donc exclu. **Les trois chroniques commencent le
10 mai 2021**, et les trois épisodes commencent ce jour-là.

Les températures d'eau de La Canner et de Gorze, deux ruisseaux sans rapport
hydraulique, pendant ces trois semaines :

| date | La Canner | Gorze | écart | air (Canner) |
|---|---:|---:|---:|---:|
| 2021-05-13 | 19,58 | 19,64 | 0,06 | 10,0 |
| 2021-05-16 | 19,20 | 19,25 | 0,05 | 11,7 |
| 2021-05-19 | 20,82 | 20,73 | 0,09 | 9,4 |
| 2021-05-22 | 22,13 | 22,09 | 0,04 | 10,3 |
| 2021-05-26 | 20,31 | 20,40 | 0,09 | 9,8 |
| 2021-05-29 | 17,05 | 16,97 | 0,08 | 14,3 |

**Deux sondes placées dans deux rivières différentes ne se suivent pas à un
dixième de degré pendant trois semaines.** Elles étaient au même endroit, hors
de l'eau, pendant que l'air descendait à 9–12 °C la nuit. Puis, le 1ᵉʳ juin pour
Gorze et le 4 juin pour La Canner, les deux séries chutent à 13–14 °C et se
mettent à se comporter comme des cours d'eau.

L'hypothèse est celle d'une **période antérieure à la pose** : les sondes
enregistrant ensemble, en attente d'installation. C'est l'hypothèse que j'avais
testée sur LA PLAINE à l'étape 18 et qui y était fausse — sa chronique commence
en 2009. Ici elle est vraie, et c'est la coïncidence des trois dates de début de
chronique qui l'établit, non un raisonnement sur les températures.

### L'autre mode de non-détection : quand l'air est chaud

Sur LA PLAINE, le bloc artefactuel réel court du **18 mai au 14 juin 2011**.
Le détecteur en a marqué onze journées — le 1ᵉʳ juin, puis du 5 au 14 juin.

Il en a manqué trois **qui étaient pourtant dans sa fenêtre** : les 2, 3 et
4 juin. La raison est mécanique :

| date | T_eau_max | T_air | écart | marquée |
|---|---:|---:|---:|---|
| 2011-06-02 | 22,56 | 17,4 | 5,16 | non |
| 2011-06-03 | 24,53 | 19,2 | 5,33 | non |
| 2011-06-04 | 25,31 | 20,2 | 5,11 | non |
| *journées marquées, pour comparaison* | | | *5,9 à 9,6* | *oui* |

Ces trois jours-là, **l'air était chaud** (17 à 20 °C contre 10 à 15 °C les
autres jours du bloc). L'écart eau–air s'en trouve réduit, il passe sous le seuil
relatif, et le détecteur ne marque pas — alors que l'eau est tout aussi
impossible : 24 à 25 °C début juin sur une station dont les trois autres juins
plafonnent à 12–13 °C.

**Le détecteur mesure un écart ; quand l'air monte, l'écart se referme sur
l'artefact.** C'est son mode de non-détection à l'intérieur même de sa fenêtre.

### Ce que cela impliquerait

Mesuré, et non conjecturé : les fonctions applicatives sont rappelées telles
quelles sur une chronique dont les journées signalées ont été retirées
(`C_impact.csv`). **Rien n'est posé.**

**Sur quinze points chiffrés, un seul verrait un indicateur bouger.**

| point | indicateur | tel quel | sans les journées signalées |
|---|---|---|---|
| **LA PLAINE A RAON-SUR-PLAINE** | vulnérabilité aiguë | 2 j — **ponctuelle** | 0 j — **absence** |
| | SGVT | 1,50 | 0,83 *(classe inchangée)* |

Et les deux journées aiguës en cause sont **les 3 et 4 juin 2011** — exactement
deux des trois journées du tableau ci-dessus. La boucle se ferme : le détecteur
a retiré huit journées aiguës artefactuelles de ce point (étape 18) et **en a
laissé deux, du même bloc, du même artefact**.

Les quatorze autres points ne bougent pas, y compris ceux dont la sonde n'était
manifestement pas dans l'eau. La raison est structurelle : leurs épisodes tombent
en **mai**, hors de la fenêtre estivale où se calculent la sensibilité et la
vulnérabilité. La Canner conserve `P_fraie = 3/3` avec ou sans ses 32 journées
signalées dans sa fenêtre de reproduction — l'indicateur est déjà à son maximum
et ne peut pas monter davantage.

*Ce dernier point mérite d'être dit sans l'adoucir :* qu'un indicateur ne bouge
pas parce qu'il est **saturé** n'est pas la même chose que de ne pas être
affecté. Sur un point moins dégradé, les mêmes 32 journées auraient pu peser.

### Le sens de cette moitié de la question

Une journée d'artefact **laissée** dans l'analyse compte comme une journée d'eau
chaude qu'elle n'est pas : elle **surestime** le risque. C'est l'inverse du
danger examiné à l'étape 18, et c'est le sens le moins grave des deux — un
diagnostic trop sévère se corrige, une alerte effacée ne se retrouve pas. Il
n'en reste pas moins que sur LA PLAINE, deux des journées de vulnérabilité aiguë
encore publiées aujourd'hui sont, selon toute vraisemblance, la même sonde hors
de l'eau que les huit qui ont été retirées.

---

## §4 — `BIE35-5__NA` (D99)

### Ce qui échoue, et où exactement

    orchestrator.run → core.analyse_sensibilite (core.py:522)
    ValueError : « Données estivales (juin–sept.) insuffisantes pour la
    régression de sensibilité : 0 jour(s) valide(s) après contrôle qualité. »

**L'échec est en aval du contrôle qualité.** Le détecteur tourne bel et bien —
`hors_eau_execute = True` — et la chaîne ne s'arrête qu'ensuite. C'est ce qui
rend l'instruction hors chaîne possible : lecture de l'eau, lecture de l'air,
normales, contrôle qualité et fusion sont rejoués **à l'identique, avec les
fonctions applicatives elles-mêmes**, et le script s'arrête avant l'étape qui
casse. Rien n'est contourné.

### La prémisse à corriger

**Ce point ne porte aucune journée marquée hors d'eau.** Zéro, et non quatre.
La raison est nette et ne laisse pas de place au doute :

| mois couverts | 12 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| journées | 51 | 62 | 57 | 62 | 36 | 38 |

La chronique va du **10 décembre 2010 au 24 mai 2012** : elle ne contient
**aucun jour de juin, juillet, août ni septembre**. La fenêtre du détecteur est
précisément juin–septembre. Il a tourné, il n'avait rien à examiner, et il n'a
rien marqué. Ce n'est pas un contrôle silencieusement désactivé — il déclare son
état — c'est un contrôle sans objet.

C'est aussi, mot pour mot, la cause de l'échec en aval : zéro jour estival pour
le détecteur, zéro jour estival pour la régression.

Les 15 journées que le contrôle qualité écarte sur ce point le sont **toutes**
pour un autre motif : `hors bornes [-0,5 ; 35,0] °C`.

### D'où viennent les quatre journées

De `docs/etape16_rapport.md` : *« `BIE35-5__NA` porte 4 journées désignées »*.
Ce sont des journées **désignées par le critère de complétude** (correctif 12),
qui mesure le plus grand trou infra-journalier — un contrôle entièrement
distinct du détecteur de mise hors d'eau. Elles servaient alors à fermer le
compte 145 − 4 = 141. Je les instruis, puisque ce sont bien elles :

| date | trou maximal | T_eau_moy | T_air | `R_ampl` | témoin scellé |
|---|---|---:|---:|---:|---|
| 2011-04-06 | 16 h | 6,83 | 11,7 | 0,038 | **indéterminable** |
| 2011-05-17 | 10 h | 12,22 | 10,0 | 0,161 | **indéterminable** |
| 2011-05-30 | 13 h | 17,36 | 16,7 | 0,056 | **indéterminable** |
| 2012-05-24 | 12 h | 7,27 | 16,1 | 0,043 | **indéterminable** |

### Ce qui manque, précisément

**Une seconde année comparable à la même saison.** La règle exige au moins deux
autres années ; la chronique n'en offre qu'**une seule** pour chacune de ces
quatre dates (15, 15, 3 et 13 journées de référence, toutes d'une même année).
Le témoin s'abstient donc, et c'est le comportement correct : avec une seule
année de comparaison, « plus chaud que tout précédent » ne veut rien dire.

Deux autres manques, à dire aussi :

- **La morphologie est incalculable.** `R_ampl` est bien mesurée (0,04 – 0,16),
  mais elle se classe contre les quantiles **estivaux** du point — que ce point
  n'a pas. Le classificateur est calibré sur une saison absente.
- **Le point ne produit aucun verdict.** Sans coefficient de sensibilité, pas de
  température normalisée, donc pas de seuil piscicole calculable. La question
  « ces journées coûtaient-elles un verdict ? » n'a pas de réponse ici — non
  parce qu'elle serait négative, mais parce qu'il n'y a aucun verdict à coûter.

---

## §5 — Le journal des verdicts, revu

`revue_journal_verdicts.py` reconstitue, à partir des `08_scores.csv` de
**quatorze rejeux conservés** (étape 10 pose 1 → étape 17 final, 32 points
chacun), la suite chronologique des trois catégories publiées — vulnérabilité
aiguë, vulnérabilité chronique, classe SGVT — et relève chaque changement.

**Quatre mouvements de catégorie, sur deux points, tous au même instant.**

| point | catégorie | avant | après |
|---|---|---|---|
| LA PLAINE A RAON-SUR-PLAINE | aiguë | Vulnérabilité aiguë sévère | Vulnérabilité aiguë ponctuelle |
| LA PLAINE A RAON-SUR-PLAINE | chronique | Vulnérabilité chronique modérée | Faible vulnérabilité chronique |
| LA PLAINE A RAON-SUR-PLAINE | SGVT | Risque Modéré | Risque Faible (Zone Refuge) |
| SN 21069646 – La Canner à Vigy 1 | aiguë | Vulnérabilité aiguë ponctuelle | Absence de vulnérabilité aiguë |

Tous les quatre à la transition **étape 10 pose 1 → pose 2**, c'est-à-dire à la
pose du correctif 1 côté application.

### La réponse à la question posée

**La Canner à Vigy 1 figure déjà dans le journal**, sous le correctif 1, avec
les bons chiffres (`n_jours_aigus` 1 → 0, SGVT 3,167 → 2,500, la journée du
1ᵉʳ juin 2021 nommée). **Il n'y a pas de lacune de D43 à combler**, et je n'ajoute
rien : compléter un journal déjà complet y introduirait un doublon.

### Et aucun autre ne manque

Sur les 32 points suivis à travers quatorze rejeux, **aucun point ne déplace une
catégorie sans figurer dans le journal**. Le contrôle est symétrique : il aurait
signalé aussi bien un point qui bouge sans être cité qu'un mouvement resté hors
du texte.

**Les étapes 11 à 17 n'ont déplacé aucune catégorie.** Zéro mouvement sur
douze transitions successives. Chacune de ces étapes l'affirmait dans son
rapport ; c'est ici vérifié d'un seul tenant, sur la trace conservée, et non
étape par étape sur parole.

*Limite de ce contrôle, à déclarer.* Les rejeux conservés commencent à
l'étape 10 : un verdict déplacé puis rétabli entre deux rejeux successifs serait
invisible, et les mouvements antérieurs à l'étape 10 ne peuvent pas y être
retrouvés. Le contrôle vérifie qu'un point cité bouge et qu'un point qui bouge
est cité ; il ne vérifie pas que la phrase du journal décrit correctement le
mouvement — cela demande une lecture, faite ici.

---

## §6 — Le paragraphe de clôture

*À destination d'un chargé d'étude qui n'a pas suivi ce chantier. Sans jargon,
sans numéro de décision.*

> **Les journées où la sonde n'était pas dans l'eau**
>
> Une sonde thermique posée en rivière peut se retrouver à l'air libre : étiage
> qui découvre le lit, sonde décalée par une crue, support qui bouge. Elle
> continue d'enregistrer, mais elle mesure autre chose que la rivière — et les
> valeurs obtenues, souvent élevées, viennent gonfler le nombre de journées
> réputées dangereuses pour le poisson.
>
> L'outil repère ces journées et les retire de l'analyse. Il ne les repère pas
> parce que l'eau y est chaude : une canicule réchauffe l'eau et l'air ensemble,
> et ces journées-là sont conservées, car elles sont vraies. Il les repère parce
> que l'eau **cesse de suivre l'air comme elle le fait d'habitude à cette
> station**. Chaque station est comparée à elle-même : aucun seuil venu d'un
> autre cours d'eau n'est appliqué.
>
> Ce choix a une contrepartie qu'il faut connaître. Une rivière réduite à
> quelques flaques se découplerait elle aussi de l'air — et ce serait alors une
> vraie journée critique. Retirer une telle journée reviendrait à effacer une
> alerte réelle. Nous avons donc vérifié, une par une, toutes les journées
> retirées qui franchissaient un seuil biologique, c'est-à-dire toutes celles
> dont le retrait change quelque chose au diagnostic.
>
> Nous les avons confrontées à l'histoire thermique propre de leur station :
> une journée est tenue pour artefact si elle est à la fois plus chaude que tout
> ce que cette station a jamais montré à la même période de l'année, et plus
> détachée de l'air que dans 95 % de ses années passées. Sur le point le plus
> touché, la sonde affichait pendant trois semaines une eau à 20–25 °C, avec des
> minimums nocturnes jamais descendus sous 18 °C, alors que les nuits
> descendaient à 5 °C et que la rivière coulait à plus du double de son débit
> habituel de saison. Les trois autres années, la même station lisait 11 à 13 °C
> à la même période. La sonde n'était pas dans la rivière.
>
> **Ce que cette vérification ne peut pas faire.** Aucune série de températures,
> de débits ou de mesures d'air ne permet d'établir avec certitude qu'une sonde
> était hors de l'eau. Nous raisonnons par recoupement, et le recoupement laisse
> une part de journées sur lesquelles nous ne nous prononçons pas. Trois éléments
> lèveraient le doute, et aucun ne figure dans les données dont nous disposons :
> une **photographie ou une fiche de tournée datée**, une **lecture de hauteur
> d'eau au droit de la sonde** — le débit mesuré à la station dit où est la
> rivière, pas où est la sonde —, et une **seconde sonde au même point, calée à
> une autre hauteur** : deux sondes qui divergent désignent l'artefact, une seule
> ne le peut jamais.
>
> **Recommandation pratique.** Sur les stations où le diagnostic bascule d'une
> classe de risque à l'autre selon que ces journées sont retirées ou non, une
> visite de terrain avec relevé de la hauteur d'eau et photographie du point de
> pose vaut mieux que tout raffinement de calcul.

---

## Artefacts

Tous sous `out/etape19/`.

| fichier | contenu |
|---|---|
| `REGLE_SCELLEE.txt` | empreintes de la règle **et** du protocole, prises avant tout chiffre |
| `F_aucune_pose.txt` | preuve octet par octet qu'aucune source applicative n'a bougé |
| `B_populations.csv` | une ligne par journée jugée, avec sa population et son verdict |
| `B_synthese.csv` | les proportions par population, et le verdict de spécificité |
| `C_faux_negatifs.csv` | les journées signalées par le témoin et non marquées par le détecteur |
| `C_par_point.csv` | leur répartition par point |
| `C_impact.csv` | ce que le retrait des journées signalées changerait — mesuré, non conjecturé |
| `D_bie35.csv` | `BIE35-5__NA`, instruit hors chaîne |
| `E_mouvements.csv` | les mouvements de catégorie, étapes 10 à 17, et leur présence au journal |
| `99_console_*.txt` | traces console intégrales |
