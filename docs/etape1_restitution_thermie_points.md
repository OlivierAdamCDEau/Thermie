# Étape 1 · D.2 — le détecteur de mise hors d'eau de `ref/thermie_points/`

Restitution seule. `ref/thermie_points/` ne contient qu'une archive ; elle est lue en place, jamais ré-extraite (D9), et rien n'est écrit dans `ref/` (D1). Les numéros de ligne renvoient aux fichiers **tels qu'ils sont dans l'archive**.

## Les fonctions, avec fichier:ligne

| Fichier (dans l'archive) | Ligne | Fonction | Rôle |
|---|---|---|---|
| `thermie_points/qualite.py` | 194 | `calculer_signatures` | calcule les trois signatures R_ampl, E_min, E_max sur la fenêtre d'examen, et restreint les jours diagnosticables |
| `thermie_points/qualite.py` | 243 | `ajouter_reference_par_point` | relativise une signature à la médiane du même point au même mois |
| `thermie_points/qualite.py` | 321 | `marquer_episodes` | déclenchement, prolongation par hystérésis, marge calendaire, fusion |
| `thermie_points/criteres.py` | 81 | `ajouter_grandeurs_relativisees` | ajoute E_max_rel (écart) et R_ampl_rel (rapport) |
| `thermie_points/criteres.py` | 145 | `appliquer_couple` | applique le couple de conditions EN CONJONCTION |
| `thermie_points/criteres.py` | 161 | `couverture_analytique` | déclare, point par point et par le calcul, si la détection est opérante |
| `thermie_points/criteres.py` | 231 | `couverture_par_saison` | même déclaration, par point ET par saison |
| `thermie_points/criteres.py` | 355 | `garde_fou` | ajoute le plancher R_ampl au candidat, si l'artefact est confirmé |
| `thermie_points/criteres.py` | 672 | `plancher_r_ampl` | calcule le plancher comme quantile de R_ampl sur les négatifs terrain |
| `thermie_points/criteres.py` | 375 | `rejouer_selection` | rejoue la règle de sélection, garde-fous compris |
| `thermie_points/fiches.py` | 74 | `extraire_episodes` | regroupe les jours marqués en épisodes, avec hystérésis et fusion |

## Les entrées exigées

| Grandeur | Définition | Entrée exigée |
|---|---|---|
| `R_ampl` | `(T_eau_max − T_eau_min) / (TX − TN)` | extrêmes journaliers d'eau **et** `TX` et `TN` de la station d'air |
| `E_min` | `T_eau_min − TN` | `T_eau_min` et `TN` |
| `E_max` | `T_eau_max − TX` | `T_eau_max` et `TX` |
| `E_max_rel` | `E_max −` médiane de `E_max` du même point au même mois | l'historique du point, mois par mois |
| `R_ampl_rel` | `R_ampl /` médiane de `R_ampl` du même point au même mois | idem |

Les extrêmes journaliers ne sont retenus que sur les jours de niveau « complet », c'est-à-dire construits à partir de mesures infra-journalières suffisamment denses. **Le détecteur exige donc TN, TX et de l'infra-journalier ; il ne fonctionne pas sur une moyenne journalière seule.**

## Les paramètres et leurs valeurs

| Constante | Valeur | Fichier:ligne | Ce qu'elle règle |
|---|---|---|---|
| `AMPL_AIR_MIN` | `6.0` | `thermie_points/qualite.py:191` | amplitude d'air minimale sous laquelle le jour n'est pas diagnosticable |
| `EPISODE_MIN_JOURS` | `3` | `thermie_points/qualite.py:177` | longueur minimale d'une séquence pour ouvrir un épisode |
| `EPISODE_MARGE_JOURS` | `1` | `thermie_points/qualite.py:178` | marge ajoutée de part et d'autre d'un épisode |
| `QUANTILE_PLANCHER` | `0.99` | `thermie_points/criteres.py:62` | quantile de R_ampl sur les négatifs terrain, pour le garde-fou strict |
| `QUANTILE_PLANCHER_PROLONGATION` | `0.95` | `thermie_points/criteres.py:72` | quantile relâché, pour la seule prolongation |
| `PROLONGATION` | `{"R_ampl_rel": 1.0, "E_max_rel": 0.5}` | `thermie_points/criteres.py:78` | couple relâché du maintien (hystérésis) |
| `SPECIFICITE_MIN` | `99.5` | `thermie_points/criteres.py:59` | spécificité minimale exigée par la règle de sélection |
| `COUVERTURE_MIN_POINTS` | `1.0` | `thermie_points/criteres.py:60` | part des points devant détecter à w = 1 |
| `FUSION_JOURS` | `5` | `thermie_points/fiches.py:45` | écart maximal entre deux épisodes pour qu'ils soient fusionnés |
| `MARGE_JOURS` | `7` | `thermie_points/fiches.py:39` | marge affichée autour d'un épisode sur la fiche (affichage seul) |
| `CRITERE_RETENU` | `{"col_a": "R_ampl_rel", "sens_a": ">", "seuil_a": 1.5, "col_b": "E_max_rel", "sens_b": ">", "seuil_b": 1.5}` | `thermie_points/etape4.py:62` | le couple retenu à l'étape 4 |
| `VARIANTE_PLANCHER_060` | `{"col_a": "R_ampl", "sens_a": ">", "seuil_a": 0.6, "col_b": "E_max_rel", "sens_b": ">", "seuil_b": 1.0}` | `thermie_points/etape4.py:60` | la variante conservée pour comparaison |
| `CRITERE_ETAPE5` | `{"col_a": "R_ampl", "sens_a": ">", "seuil_a": 0.35, "col_b": "E_max_rel", "sens_b": ">", "seuil_b": 1.0}` | `thermie_points/etape5.py:59` | le vainqueur de la sélection rejouée à l'étape 5 |
| `MOIS_ESTIVAUX` | `(6, 7, 8, 9)` | `thermie_points/common.py:81` | fenêtre d'examen par défaut |
| `MARGE_TX_C` | `2.0` | `thermie_points/common.py:106` | marge du signalement indépendant fondé sur TX (n'exclut rien) |
| `TROU_MAX_COMPLET_H` | `3` | `thermie_points/common.py:71` | trou maximal pour qu'un jour soit « complet » |
| `HEURES_MIN_COMPLET` | `20` | `thermie_points/common.py:72` | heures minimales renseignées pour qu'un jour soit « complet » |
| `TROU_MAX_VALIDE_H` | `6` | `thermie_points/common.py:70` | trou maximal pour qu'un jour soit « valide » |

## La règle, en conjonction

`criteres.appliquer_couple` applique **deux conditions et leur conjonction**, jamais leur disjonction. La raison est écrite dans la fonction : le maximum d'un cours d'eau peu profond et exposé peut dépasser `TX` par rayonnement direct sans exondation ; seule la conjonction de deux signatures désigne une sonde hors d'eau.

Quatre couples candidats sont définis (`criteres.CANDIDATS`), et le sens de chaque comparaison compte : sous exondation `E_min` **descend** vers 0 tandis que `E_max` **monte**. Le couple retenu à l'étape 4 est `R_ampl_rel > 1,5` **ET** `E_max_rel > 1,5`, assorti du garde-fou `R_ampl > 0,67`. Le vainqueur de la sélection rejouée à l'étape 5 est `R_ampl > plancher` **ET** `E_max_rel > 1,0`.

## L'hystérésis

`qualite.marquer_episodes` enchaîne trois mécanismes, dans cet ordre :

1. **Déclenchement** — une séquence d'au moins `EPISODE_MIN_JOURS` jours suspects **consécutifs dans le calendrier** ouvre un épisode ; un jour suspect isolé est signalé sans exclure.
2. **Prolongation** — une fois l'épisode ouvert, il s'étend de part et d'autre tant que le critère **relâché** `PROLONGATION` reste vérifié. La prolongation ne peut jamais *ouvrir* un épisode.
3. **Fusion** — deux épisodes séparés de moins de `FUSION_JOURS` jours sont fusionnés, et les jours intercalaires marqués.

La marge est **calendaire et non positionnelle** : la série n'est indexée que sur juin-septembre, si bien qu'une marge positionnelle rattacherait le 30 septembre d'une année au 1er juin de la suivante.

## Valeurs codées en dur, et hypothèses implicites sur les données

| Valeur / hypothèse | Où | Ce qu'elle suppose |
|---|---|---|
| `AMPL_AIR_MIN = 6.0` °C | `qualite.py` | que le dénominateur `TX − TN` soit assez grand pour que le rapport ait un sens ; en deçà, le jour est déclaré non diagnosticable, ni marqué ni sain |
| Seuils `1,5` / `1,5` et plancher `0,67` | `etape4.py` | calés sur la distribution du bassin de la Bienne et sur des négatifs terrain ; ce sont des propriétés du jeu, pas de la méthode |
| `POINTS_RESERVE` et `GROUPES_RELECTURE` | `fiches.py` | des codes de points du bassin de la Bienne sont écrits en dur, ainsi qu'un **jugement humain** de relecture attaché à un couple (point, année) |
| `STATION_REFERENCE = "LA_PESSE"` | `common.py` | une station d'air unique, nommée en dur, plus haute et plus froide que les sites — c'est cette asymétrie qui donne sa marge à `E_max` et la retire à `E_min` |
| `NOMS_COURS_EAU = {"BIE": "Bienne"}` et `MOTIF_CODE_POINT` | `common.py` | que les codes de points suivent la nomenclature à trois lettres du réseau de la Bienne |
| `MOIS_ESTIVAUX = (6, 7, 8, 9)` | `common.py` | que l'exondation soit un phénomène estival ; l'émersion hivernale a une signature **inverse** et relève d'autres contrôles |
| Niveau de jour « complet » | `common.py` | de l'infra-journalier dense : aucun trou > 3 h et au moins 20 h renseignées. Une chronique déjà agrégée au jour ne peut pas satisfaire ce critère |
| `TN` et `TX` de la station d'air | partout | qu'ils soient lus et transmis. La chaîne de V4.5 ne les lit pas (`io_data.py:432`) |

