# Étape 1 · D.4 — `data/socle/reconciliation_v45.csv`

Restitution seule : la structure est décrite, **aucun écart n'est recalculé** à ce stade.

Le fichier est lu dans `ref/thermie_points/thermie_points.zip`, en place, sans ré-extraction (D9).

## Structure

- 26 lignes de données, 22 colonnes, séparateur `;`, BOM UTF-8, virgule décimale.
- Une ligne par **point de mesure**, pas par date : le fichier ne porte aucune chronique, seulement des statistiques agrégées.

### Les grandeurs comparées

| Grandeur | Statistiques | Conventions comparées | Unité de l'écart |
|---|---|---|---|
| `Tmh_norm` | médiane, p95, maximum | thermie_points / convention V4.5 | °C |
| `Tmax_norm` | médiane, p95, maximum | thermie_points / convention V4.5 | °C |
| Jours retenus | effectif | thermie_points / convention V4.5 | jours, plus une part conservée en % |

Chaque triplet est écrit trois fois : la valeur sous chaque convention, puis leur différence, en colonne `… — écart`. **L'unité d'écart est le degré Celsius** pour les températures normalisées, le **jour** pour les effectifs, le **point de pourcentage** pour la part conservée.

### Ce que l'écart isole, d'après `thermie_points/reconciliation.py`

> Les deux versions sont calculées dans la **même chaîne**, à partir des mêmes colonnes de la couche L2 : `qc_ok` pour thermie_points, `qc_ok_v45` pour la convention V4.5. […] L'écart mesuré isole donc exactement les familles **D1 et D2** du registre […]. C'est une limite de la mesure et il faut la dire : ce n'est pas « V4.5 rejoué intégralement », c'est « la convention d'exclusion de V4.5 appliquée à nos données corrigées ».

## Période couverte

Le fichier **ne porte aucune colonne de date** : ni période, ni année. La période n'est donc pas lisible dans le fichier lui-même. Elle se déduit du contexte du projet clos — la fenêtre estivale (juin-septembre) des chroniques du bassin de la Bienne — mais elle n'y est pas écrite.

## Les points couverts

- 26 points dans le fichier.
- **26** de ces points sont dans le corpus `data/` et donc dans le harnais.
- **0** point(s) du fichier ne sont pas dans le corpus : —.
- **6** point(s) du corpus ne sont pas dans le fichier : BIE35-5__NA, LA PLAINE A RAON-SUR-PLAINE, La Moselle à Hielle, Le ruisseau de Gorze à Gorze, Le ruisseau de la Flotte à Château-Voue, SN 21069646 - La Canner à Vigy 1.
  Les points des jeux `jeu_02` a `jeu_05` et `jeu_exemples_v45` en font partie par construction : le fichier ne couvre que le bassin de la Bienne. Ceux du bassin de la Bienne qui n'y figurent pas sont signales ci-dessous.
- Point(s) du bassin de la Bienne absent(s) du fichier : BIE35-5__NA.
- Appariement par code normalise (le suffixe `__NA` du nom de fichier ne figure pas dans les tables du projet clos) : BIE35-5__NA -> BIE35-5.

## Les artefacts du harnais permettraient-ils de recalculer ces écarts ?

| Grandeur du fichier | Artefact du harnais | Recalculable ? |
|---|---|---|
| `Tmh_norm` médiane / p95 / maximum | `07_t_norm.csv`, grandeur `Tmh_norm` | **oui**, côté convention V4.5 seulement |
| `Tmax_norm` médiane / p95 / maximum | `07_t_norm.csv`, grandeur `Tmax_norm` | **oui**, côté convention V4.5 seulement |
| Jours retenus — convention V4.5 | `02_effectifs.csv`, colonne `journees_retenues_apres_fusion` | **oui** |
| Jours retenus — thermie_points | aucun | **non** : le harnais n'exécute que `ref/v4_5/` (D3) |
| `… — écart` | — | **non** : un écart exige les deux côtés |

Autrement dit : le harnais fournit **une** des deux colonnes de chaque paire. La colonne thermie_points ne peut venir que du projet clos ou d'un rejeu de son code, ce que l'étape 1 ne fait pas.

Deux réserves s'ajoutent, et elles ne sont pas mineures :

1. La fenêtre n'est pas la même. Le fichier agrège la fenêtre estivale ; `07_t_norm.csv` porte **toutes** les journées retenues. Un filtre sur juin-septembre serait nécessaire, et il n'est pas écrit dans le fichier — il se lit dans `reconciliation.py`.
2. Sur les 26 points communs, **11** font échouer la chaîne de V4.5 dans le harnais : ils ne produisent aucune valeur de `Tmh_norm`, donc aucun terme à comparer.

