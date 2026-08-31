# Manifeste d'archivage — volet thermique

*Établi le 28/08/2026. Ce document permet de reprendre le travail sans aucune explication orale.*


## 1. Ce dont on part

| Emplacement | Contenu | Origine |
|---|---|---|
| `data/eau/` | 27 classeurs `.xlsx`, un par point de mesure | sondes du réseau de suivi, export brut |
| `data/air/` | 2 fichiers `.csv` de température d'air journalière | Météo-France, stations LA_PESSE et CHAUX_DES_PRES |
| `data/referentiel/` | 3 classeurs `.xlsx` : stations, suivi de terrain, historique des capteurs | référentiel métier, export du 02/06/2026 |
| `data/ref_V4_5/` | code de l'outil qui traite le volet biologique | dépôt de cet outil, en LECTURE SEULE — jamais exécuté comme application, seuls ses chargeurs de fichiers sont importés |
| `data/Rapport_Phase2_V0.1_thermie.docx` | rapport d'accueil dont les livrables héritent les styles | bureau d'études |

`data/referentiel/` et `data/ref_V4_5/` sont en **lecture seule** : la chaîne n'y écrit rien, et une exécution complète ne modifie aucun de leurs horodatages. C'est vérifiable, et c'est vérifié à chaque clôture.


### Empreintes des fichiers sources, tels qu'ils ont servi

| Fichier | Octets | SHA-256 (16 premiers caractères) |
|---|---|---|
| data/eau/ABI3-6.xlsx | 178285 | 1d1d1bc766e7c3e7 |
| data/eau/BCH5-7.xlsx | 1187371 | 4dca9984820ad793 |
| data/eau/BIE0-3.xlsx | 2984040 | a0045ddc1ba77894 |
| data/eau/BIE10-8.xlsx | 2251180 | ad25619e7feaf66d |
| data/eau/BIE21-7.xlsx | 3342294 | b2e13a74b20a504f |
| data/eau/BIE27-9.xlsx | 2870692 | 8c124cd1c0079a65 |
| data/eau/BIE31-4.xlsx | 2624576 | 6d0ff9a00aff453c |
| data/eau/BIE32-4.xlsx | 2658478 | f8a3809f962be294 |
| data/eau/BIE35-5__NA.xlsx | 331332 | 2cdaa8ef317084a5 |
| data/eau/BIE37-9.xlsx | 2686834 | 81618e40fe619e45 |
| data/eau/BIE40-3.xlsx | 2868203 | d0aad18d3d262d7f |
| data/eau/BIE42-7.xlsx | 2700831 | 6e18ddad140c00d3 |
| data/eau/BIE46-5.xlsx | 757360 | 35475a9e6083e3c1 |
| data/eau/BIE5-2.xlsx | 1477906 | a69a43e4c9211d8b |
| data/eau/BIE5-9.xlsx | 1802583 | b7483cd28e14b10f |
| data/eau/BIE50-5.xlsx | 2194527 | 71dc8923bcd6b5ad |
| data/eau/BIE51-0.xlsx | 764546 | 2d9a3d8503185070 |
| data/eau/BIE56-1.xlsx | 3345597 | 99f42de3b487d53b |
| data/eau/BIE6-8.xlsx | 2511587 | 3d81772761a95685 |
| data/eau/BLE3-0.xlsx | 95353 | 2d1e82d89c94d18c |
| data/eau/FLU8-4.xlsx | 226933 | 77c5eef799d985c2 |
| data/eau/GRO9-1.xlsx | 142847 | d24e25268524927d |
| data/eau/HRI7-7.xlsx | 189104 | c98b15dcf6daaeeb |
| data/eau/LGV11-8.xlsx | 189376 | 765f321acc1168eb |
| data/eau/LIZ13-5.xlsx | 667381 | afc348449ad5813d |
| data/eau/LIZ5-5.xlsx | 899819 | fb3b7850e45575ec |
| data/eau/TAC16-4.xlsx | 259806 | 67e6f11ebcbc68b7 |
| data/air/CHAUX_DES_PRES.csv | 402572 | c136d640e1ba4fd9 |
| data/air/LA_PESSE.csv | 934626 | 9f211ac4335272cc |
| data/referentiel/2026-06-02_Stations.xlsx | 13604 | 480e862ef3ba1474 |
| data/referentiel/2026-06-02_historique_capteurs.xlsx | 13829 | 2f13a85431d3e5b4 |
| data/referentiel/2026-06-02_suivi_terrain.xlsx | 61116 | 0d49336b776f7763 |
| data/Rapport_Phase2_V0.1_thermie.docx | 388785 | 36bbe2aba6424134 |

## 2. La commande unique

```
python thermie_points/rejouer.py
```

Quatorze étapes s'enchaînent, de l'inventaire des chroniques à la liasse. Durée mesurée : **24 minutes** sur une machine de bureau ordinaire. Le détail :

| Étape | Code de retour | Durée (s) |
|---|---|---|
| inventaire | 0 | 91,2 |
| etape2 | 0 | 84,6 |
| etape3a | 0 | 101,6 |
| etape3b | 0 | 131 |
| etape3c | 0 | 100,3 |
| etape4 | 0 | 98,3 |
| etape4bis | 0 | 98,5 |
| etape5 | 0 | 367,8 |
| etape5bis | 0 | 15,6 |
| etape6 | 0 | 106,7 |
| etape7 | 0 | 53,5 |
| etape7bis | 0 | 53,4 |
| etape8 | 0 | 69,6 |
| etape9 | 0 | 66,7 |

La reprise partielle est possible — `python thermie_points/rejouer.py etape6` repart de l'étape nommée — mais elle suppose que les états antérieurs sont ceux du même jeu de données. En cas de doute, tout rejouer coûte moins cher qu'une vérification.


## 3. Ce qui est produit

| Dossier | Statut | Contenu |
|---|---|---|
| `data/socle/` | PRODUIT | les tables de la chaîne : socle horaire et journalier, sensibilités, indicateurs annuels et de synthèse, table des cours d'eau, historique des décomptes |
| `out/inventaire/, out/socle/, out/etape*/` | INTERNE | un dossier par étape : rapport d'étape, classeur de validation, figures de travail |
| `out/livraison/` | REMIS | la liasse, et elle seule : note d'expertise, annexes, note méthodologique, figures, logigrammes, données, couche SIG, lisez-moi |
| `docs/` | INTERNE | le carnet de méthode, le registre des correctifs, le présent manifeste et la liste des points ouverts |
| `METHODO.md` | INTERNE | le carnet de méthode, cumulatif : jamais réécrit, seulement complété |

La liasse compte **41 pièces**, listées dans son propre « Lisez-moi ».


## 4. Ce qui est remis, et ce qui ne l'est pas

**Remis** — le contenu de `out/livraison/`, et rien d'autre.

**Non remis** :

- `METHODO.md` — carnet de méthode cumulatif — il porte le raisonnement étape par étape, y compris les hypothèses abandonnées
- `docs/CORRECTIFS_V4_6.md` — registre des écarts avec l'outil du volet biologique, chacun caractérisé comme correctif ou non
- `out/*/RAPPORT_ETAPE*.md` — les rapports d'étape, qui portent le carnet de bord de chaque étape
- `out/*/validation*.xlsx, out/*/coherence*.xlsx` — les classeurs de contrôle, qui servent à vérifier, pas à restituer

Ces documents disent comment le travail a été fait, avec ses hésitations et ses corrections. Ils sont indispensables pour reprendre ou contester un résultat, et ils n'ont pas leur place dans une liasse : un maître d'ouvrage y lirait le chantier au lieu du résultat. Ils sont conservés, pas remis.


## 5. Les décisions qui ne se déduisent d'aucune donnée

Ce sont les seules qu'il faudra **reprendre** sur un autre jeu. Tout le reste est mécanique et se relit dans le code.


### Station d'air de référence

**Ce qui a été décidé.** LA_PESSE (1133 m) plutôt que CHAUX_DES_PRES.

**Sur quoi.** Deux stations couvrent le bassin. CHAUX_DES_PRES (854 m) ne compte que 7 années dans la période de référence, pour un seuil de 20 : elle ne peut pas servir de station de normalisation, et l'outil du volet biologique émettrait lui-même l'avertissement. LA_PESSE (1133 m) couvre 1996-2026, soit 25 années dans la période de référence ; c'est sa date de début qui fixe la normale à 1996-2020 et non à la période trentenaire usuelle 1991-2020. La comparaison des deux stations a été faite sur leur PÉRIODE COMMUNE, seule façon d'isoler l'effet de station de l'effet de période.

**Ce qu'il faut en faire ailleurs.** Sur un autre bassin, la station se choisit d'abord sur la couverture dans la période de référence, jamais sur la proximité géographique seule ; et la période de normale suit la station retenue, jamais l'inverse. À noter pour la lecture : ici la station la plus HAUTE est la plus chaude en moyenne — accumulation d'air froid en creux, fréquente sur les plateaux du Jura — de sorte qu'un décalage entre deux stations ne se déduit pas de leur différence d'altitude.


### Cours d'eau des préfixes GRO et LGV

**Ce qui a été décidé.** Grosdar → affluent du Tacon ; Longviry → affluent de la Bienne.

**Sur quoi.** Le référentiel porte plusieurs milieux sur ces deux préfixes, dont les premières lignes sont fautives. L'arbitrage est porté par la colonne `source_de_la_donnee` de la table produite, ligne à ligne.

**Ce qu'il faut en faire ailleurs.** Toute correction de cette nature doit rester une table SÉPARÉE et tracée : corriger en place le référentiel rendrait l'erreur invisible et la correction incontestable.


### Relecture experte des épisodes d'exondation

**Ce qui a été décidé.** 6 couples point × année classés en deux groupes : exondation manifeste (BIE40-3 tous millésimes, BIE51-0 en 2025) et exondation probable (BIE21-7 2012, BIE5-9 2020, BIE0-3 2018, TAC16-4 2015).

**Sur quoi.** Ce classement est un JUGEMENT porté sur les fiches d'épisode, pas une sortie du calcul. Il est restitué dans chaque fiche pour que la fiche régénérée le porte avec elle.

**Ce qu'il faut en faire ailleurs.** Sur un autre jeu, les fiches doivent être relues : aucun seuil ne remplace cette lecture, et c'est elle qui a fait apparaître les défauts que tous les contrôles automatiques avaient laissé passer.


### Point écarté de toute comparaison

**Ce qui a été décidé.** GRO9-1.

**Sur quoi.** 193 journées mesurées sur cinq ans d'étendue, dont une lacune de plus de quatre ans. La chronique existe mais ne porte aucune comparaison.

**Ce qu'il faut en faire ailleurs.** Le critère est la couverture, pas la qualité de la mesure : un point peut être juste et incomparable.


### Réserve d'implantation

**Ce qui a été décidé.** BIE40-3.

**Sur quoi.** Épisodes d'exondation répétés en 2015, 2018 et 2023, et 22 valeurs négatives en hiver. La question n'est pas de savoir si les épisodes sont réels, mais si le point renseigne le cours d'eau.

**Ce qu'il faut en faire ailleurs.** Cette réserve appelle une visite de terrain ; elle ne se lève pas par le calcul.


### Réserve de robustesse au seuil

**Ce qui a été décidé.** BIE21-7, BIE5-2, BIE51-0, LIZ5-5.

**Sur quoi.** Le maximum estival de ces quatre points change selon le seuil du détecteur d'exondation. La valeur publiée est celle du seuil retenu, et la réserve dit qu'elle en dépend.

**Ce qu'il faut en faire ailleurs.** À refaire sur tout nouveau jeu : c'est une propriété du jeu, pas de la méthode.


## 6. Ce que le rejeu ne reconstruit pas

Un manifeste qui promet tout ne promet rien. Deux limites, aucune ne touchant une pièce remise :


**Carnet de méthode, sections des étapes 1 à 4.** Ces quatre sections ont été écrites à la main et ne sont produites par aucun code. À partir de l'étape 4bis, chaque étape réécrit sa propre section de façon idempotente. Un rejeu depuis un dossier vide reconstruit donc le carnet à partir de l'étape 4bis seulement. Le carnet est interne : aucune pièce remise n'en dépend.


**Ordre des sections du carnet et du registre.** Les sections y figurent dans l'ordre où elles ont été écrites, qui n'est pas celui de la chaîne — l'étape 4bis est postérieure à l'étape 8. Un rejeu les range dans l'ordre d'exécution. Le contenu de chaque section est le même ; seul leur ordre diffère.


## 7. Les versions employées

| Bibliothèque | Version | Rôle |
|---|---|---|
| Python | 3.14.0 | interpréteur (AMD64) |
| numpy | 2.3.4 | calcul numérique |
| pandas | 2.3.3 | tables et séries |
| matplotlib | 3.10.7 | toutes les figures, sans exception |
| scipy | 1.16.3 | régression et tests |
| statsmodels | 0.14.5 | intervalles HAC |
| openpyxl | 3.1.5 | classeurs Excel |
| docx | 1.2.0 | documents Word (python-docx) |
| pyarrow | 23.0.1 | format parquet |
| docx2pdf | 0.1.8 | export PDF via Word |
| PIL | 12.0.0 | contrôle des images (Pillow) |

Les figures sont produites par **Matplotlib seul** : aucune autre bibliothèque graphique n'intervient, ce qui garantit qu'une figure se régénère à l'identique tant que Matplotlib ne change pas de version majeure. Les polices sont vectorisées à l'export SVG (`svg.fonttype = path`) : le rendu ne dépend pas des polices installées chez le lecteur.

