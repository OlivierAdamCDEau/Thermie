# Plan de la note méthodologique

*Document de travail. Ce n'est pas la note : c'est son plan, chapitre par chapitre, avec ses sources dans METHODO.md et ses manques.*

## Comment lire ce plan

`METHODO` renvoie aux sections de `METHODO.md`, qui est **cumulatif et chronologique**. La note est **thématique** : elle suit l'ordre du raisonnement, non celui du développement. Un même passage de METHODO peut alimenter deux chapitres ; une bonne moitié de METHODO — les hypothèses abandonnées, les diagnostics intermédiaires, les corrections de mon propre code — n'entrera pas dans la note et doit rester accessible en annexe technique.

Trois mentions reviennent :

- **[SOURCE]** — le contenu existe et se transpose ;
- **[À RÉÉCRIRE]** — le contenu existe mais dans une forme inadaptée à un lecteur non technique ;
- **[MANQUE]** — le contenu n'existe pas et doit être produit.

---

## 1. Périmètre et données

### 1.1 Ce que couvre l'étude, ce qu'elle ne couvre pas
- [SOURCE] METHODO §1.1 — périmètre volontairement restreint ; §1.9 — ce qui a été délibérément écarté.
- [SOURCE] METHODO §3B.7 — ce que recouvre un regroupement de points.
- [À RÉÉCRIRE] Le périmètre est aujourd'hui justifié par des arguments de faisabilité technique. Pour la note, il doit être formulé en termes de question de gestion : à quelle question ces points répondent-ils.
- **Figure** : `e_couverture_du_reseau` — périodes suivies, journées écartées, lacunes.

### 1.2 Origine et nature des données
- [SOURCE] METHODO §1.2 et §1.3 — réutilisation des loaders V4.5, traçabilité du format détecté ; §2.4 — couche horaire.
- [SOURCE] METHODO §1.8 et §3A.3 — le référentiel, et le code interne des fichiers qui fait autorité pour l'appariement.
- [SOURCE] **Figure** : `f_schema_de_situation`, produite à l'étape 6. Ce n'est pas une carte et ne s'en donne pas l'air : aucun fond topographique ni hydrographique n'est disponible dans le périmètre. Les points sont positionnés en Lambert 93, ceux d'un même cours d'eau reliés en pointillé dans l'ordre des PK — le trait est l'ordre de parcours, pas le cours d'eau. Échelle graphique et nord portés.

### 1.3 La référence d'air
- [SOURCE] METHODO §2.9 — comparaison des deux stations et ce qui a dû être corrigé ; §3B.14 — libellé de la période de référence.
- [À RÉÉCRIRE] Le choix de LA_PESSE est aujourd'hui exposé comme le résultat d'un arbitrage entre deux candidates. Pour la note, il faut dire ce que ce choix implique : une station d'altitude, plus froide que les sites, ce qui a des conséquences directes sur la détection (chapitre 3).

## 2. Représentativité des chroniques

### 2.1 Ce qu'une chronique doit valoir pour être publiée
- [SOURCE] METHODO §2.5 — validité journalière ; §2.6 — réindexation calendaire ; §3B.12 — classification à trois niveaux.
- [À RÉÉCRIRE] La règle des classes A/B/C est décrite par ses seuils. Pour la note, elle doit être décrite par son intention : ne publier une année que si la période où le maximum se produit a effectivement été observée.
- **Tableau** : « Classe de validité estivale, par point et par année ».

### 2.2 Longueur des chroniques et comparabilité
- [SOURCE] METHODO §4 (D14) — jamais de comparaison sur un extrême cumulé ; la synthèse est la médiane des années de classe A.
- [SOURCE] METHODO §4.10 — mention « valeur ponctuelle, non représentative » en deçà de trois années.
- **Tableau** : « Synthèse par point », colonne du nombre d'années de classe A.

## 3. Contrôle qualité et ses limites

### 3.1 Le résultat qui commande ce chapitre — À PLACER EN PREMIER
- [SOURCE] METHODO §Étape 5, « Le résultat qui commande la lecture de tout ce chapitre ».
- **Énoncé attendu** : le débat sur le détecteur d'exondation ne change pas les indicateurs publiés, et c'est démontré. Trois versions successives du détecteur ont été comparées ; les classes de validité passent de 154/3/71 à 153/3/72, un seul couple point × année change, et **0 indicateur publiable** ne se déplace de plus d'un écart-type interannuel. Le socle recalculé aux deux bornes de l'intervalle de confiance du seuil ne déplace aucune classe.
- **Pourquoi en tête** : un lecteur qui découvre qu'un détecteur d'anomalie a été discuté pendant quatre étapes se demande légitimement si les chiffres qu'on lui remet en dépendent. Répondre d'emblée que non, et le démontrer, permet de lire tout le reste du chapitre comme une question de qualité de la donnée écartée — ce qu'elle est — et non comme une incertitude sur le résultat.

### 3.2 Deux phénomènes distincts, deux détecteurs
- [SOURCE] METHODO §3A.8 — deux phénomènes, deux détecteurs ; §3A.2 — le détecteur « hors d'eau » de V4.5, conservé mais dépossédé.
- [SOURCE] METHODO §3A.9 — le pic de manipulation, résultat négatif.

### 3.3 La détection d'exondation
- [SOURCE] METHODO §3A.10, §3A.11 — signature d'exondation, règle de l'épisode et non de la saison ; §3C.2 et §3C.3 — le mécanisme d'aveuglement, la direction du maximum.
- [SOURCE] METHODO §Étape 4bis, « Détection à hystérésis ».
- [À RÉÉCRIRE] Quatre étapes de mise au point sont racontées chronologiquement. La note doit présenter le détecteur **abouti** et renvoyer l'historique en annexe. Ne garder dans le corps que ce qui éclaire une limite du résultat.

### 3.4 Ce que le contrôle ne voit pas — limites déclarées
- [SOURCE] METHODO §Étape 5, « Deux sorties d'eau, deux signatures inverses » et « Ce qu'un examen annuel n'examine pas ».
- [SOURCE] METHODO §Étape 4bis, « La contrainte de spécificité ne valide pas ce seuil » — un test sans pouvoir discriminant ne valide rien.
- [SOURCE] Étape 5bis, diagnostic D51 : la complémentarité saisonnière des deux critères est établie, et son rendement mesuré — 2 journées d'hiver suspectes, 1 non couverte par un autre contrôle.
- **Énoncé attendu** : le contrôle est opérant d'avril à novembre ; en hiver, il repose sur les bornes physiques et le détecteur de plateau, pas sur la signature d'exondation. Le minimum hivernal publié a été vérifié de ce point de vue.
- **Tableau** : `data/socle/detection_par_saison.csv`, à mettre en annexe.

### 3.5 Ce que le seuil mesure, et avec quelle précision
- [SOURCE] METHODO §Étape 5, « Ce qu'un seuil quantile mesure » — intervalle de confiance par bootstrap, modalité « cas limite ».
- [À RÉÉCRIRE] Sous une forme qui ne suppose pas de connaître ce qu'est un quantile empirique.

## 4. Principe et validation de la normalisation

### 4.1 Pourquoi normaliser
- [SOURCE] METHODO §3B.9 — la normalisation devient conditionnelle.
- [SOURCE] **Exemple chiffré, étape 6** : BIE42-7, sur None au PK 42,7, a atteint 23,9 °C en 2022, année dont l'anomalie d'air estivale valait 2,4 °C ; ramené à une année normale, il en atteint 21,9 °C. Le détail du calcul et la subtilité qu'il révèle — l'indicateur normalisé n'est pas la valeur normalisée du jour du maximum brut — figurent au rapport d'étape 6, §2.

### 4.2 Le coefficient de sensibilité
- [SOURCE] METHODO §2.8 — intervalle de Newey-West ; §3C.8 — le R² et l'intervalle ne mesurent pas la même chose.
- [SOURCE] METHODO §3B.9 — statuts de normalisation et cas où elle n'est pas appliquée.
- **Figure** : `a_profil_longitudinal_bienne`, panneau haut.
- **Tableau** : « Sensibilité au climat, par point ».

### 4.3 La démonstration que la normalisation fait ce qu'elle annonce
- **Figure** : `b_effet_de_la_normalisation` — c'est la pièce maîtresse du chapitre.
- [SOURCE] METHODO §3B.10 — extensions et invariance.
- **Énoncé attendu** : la correction est proportionnelle à l'anomalie d'air de l'année et de signe opposé, corrélation −0,73, pente −0,71 °C/°C.

### 4.4 Ce que la normalisation ne fait pas
- [SOURCE] METHODO §3B.11 — coefficient de sensibilité de l'amplitude, grandeur distincte.
- [SOURCE] Étape 5bis, figure `d_amplitude_nycthemerale` : la normalisation resserre la dispersion des amplitudes sauf en hiver, où elle l'élargit. **À ne pas dissimuler** — c'est cohérent avec le chapitre 3.4.

## 5. Définition des indicateurs

### 5.1 Les indicateurs retenus et leur convention de lecture
- [SOURCE] METHODO §Étape 4 — indicateurs par couple point × année, moyennes mobiles à fenêtres strictes.
- [SOURCE] METHODO §4 (D14) et étape 4bis (D18) — extrême cumulé, sens et non-comparabilité.
- [À RÉÉCRIRE] Chaque indicateur doit être présenté par ce qu'il sert à décider, pas par sa formule. La formule va en annexe.

### 5.2 Brut ou normalisé : lequel publier et quand
- [SOURCE] **Décision D52, étape 6.** Ce ne sont pas deux versions du même chiffre, ce sont deux grandeurs : le normalisé répond à « qu'aurait lu ce point sous un climat normal », le brut à « qu'a fait l'eau ».
- **Comparer des points entre eux → NORMALISÉ**, toujours : seule façon de comparer des chroniques mesurées sur des années différentes.
- **Décrire un fait observé → BRUT**, toujours : un maximum atteint, un seuil franchi, un épisode vécu par le milieu. Le normalisé est une reconstruction, il n'a jamais eu lieu.
- **Chercher une tendance temporelle → BRUT, JAMAIS NORMALISÉ.**
- **À écrire en gras dans la note** : la normalisation retranche l'anomalie d'air de l'année. Chercher un réchauffement dans une série normalisée revient à chercher le signal qu'on vient de soustraire — on trouve zéro par construction, et l'on conclut à tort que le cours d'eau ne se réchauffe pas. C'est le seul mésusage grave que ce jeu permette, et il est facile à commettre de bonne foi.
- **Restitution** : les deux séries en colonnes adjacentes, BRUT D'ABORD, avec un rappel d'emploi en tête de chaque tableau.

## 6. Résultats

### 6.1 Le profil longitudinal
- **Figure** : `a_profil_longitudinal_bienne`.
- [SOURCE] METHODO §Étape 5bis — « La règle générale, mise au jour par l'analyse de BIE6-8 ».

### 6.2 La comparaison entre points
- **Figures** : `c_comparaison_maximum_estival`, `c_comparaison_moyenne_30_jours`.
- **Tableau** : « Synthèse par point ».

### 6.3 Les amplitudes nycthémérales
- **Figure** : `d_amplitude_nycthemerale`.

### 6.4 Ce que ces résultats permettent de dire, et pas davantage
- [MANQUE] Aucune interprétation écologique n'a été produite, et le travail ne comporte aucune donnée biologique. Si la note doit conclure sur des enjeux piscicoles, la matière est à apporter par le bureau d'études — l'outil ne la contient pas.

## 7. Limites et réserves nommées

### 7.1 Les réserves attachées à des points précis
- **Tableau** : « Réserves nommées » — quatre points en réserve de robustesse au seuil, un point en réserve d'implantation.
- [SOURCE] METHODO §3C.1 — robustesse au seuil ; §Étape 4bis, « Limites nouvelles » — BIE40-3.
- **Règle de restitution** : ces réserves accompagnent obligatoirement les indicateurs des points concernés. Une réserve de seuil appelle une fourchette ; une réserve d'implantation appelle une visite de terrain.

### 7.2 Les limites de méthode
- [SOURCE] METHODO §LIMITES DE LA VALIDATION, intégralement.
- [SOURCE] METHODO §3A.12 et §3B.13 — ce que la validation terrain a permis et ce qu'elle n'a pas permis ; périmètre déclaré.
- [SOURCE] METHODO §3B.5 — le test sur épisode documenté, inconclusif.

### 7.3 Ce que ces limites ne remettent pas en cause
- [SOURCE] METHODO §Étape 5bis, « Ce que ces limites ne remettent pas en cause ».
- **Renvoi au chapitre 3.1** : la démonstration de robustesse est le contrepoids de ce chapitre, et les deux doivent se répondre explicitement.

## 8. Annexes

- **A1. Historique des versions du détecteur** — [SOURCE] METHODO étapes 3A, 3C, 4, 4bis, 5. Y renvoyer tout le récit chronologique retiré du chapitre 3.3.
- **A2. Registre des correctifs par rapport à V4.5** — [SOURCE] `docs/CORRECTIFS_V4_6.md`, à joindre tel quel : c'est le document qui établit qu'aucune divergence n'est un choix méthodologique alternatif.
- **A3. Formules des indicateurs** — [SOURCE] METHODO étape 4.
- **A4. Capacité de détection par point et par saison** — [SOURCE] `data/socle/detection_par_saison.csv`.
- **A5. Charte graphique** — [SOURCE] `thermie_points/charte.py`, résumé produit à l'étape 5bis.
- **A6. Glossaire** — [SOURCE] `docs/GLOSSAIRE.md`, quinze entrées, sans formule. Il porte aussi, en fin de document, l'usage à ne pas faire (D52).

## Ce qui manque, récapitulé

| Manque | Chapitre | Nature | État |
|---|---|---|---|
| Règle d'emploi : brut ou normalisé selon l'usage | 5.2 | décision | **LEVÉ** — décision D52, étape 6 |
| Schéma de situation des points | 1.2 | production | **LEVÉ** — figure `f_schema_de_situation`, étape 6 |
| Exemple chiffré de normalisation | 4.1 | calcul | **LEVÉ** — BIE42-7 × 2022, étape 6 |
| Glossaire | A6 | rédaction | **LEVÉ** — `docs/GLOSSAIRE.md`, étape 6 |
| Formulation du périmètre en question de gestion | 1.1 | rédaction | à écrire avec la note |
| Interprétation écologique | 6.4 | **hors périmètre** | à apporter par le bureau d'études |

**Plus aucun manque n'est bloquant.** Le seul qui demandait une décision — et
non une rédaction — est tranché : la règle d'emploi entre indicateurs bruts et
normalisés.

Reste une seule pièce que ce travail ne peut pas produire : **l'interprétation
écologique**. Le jeu de données ne comporte aucune donnée biologique, et aucune
n'a été demandée. Si la note doit conclure sur des enjeux piscicoles, la matière
est à apporter par le bureau d'études ; l'outil fournit les températures, leurs
limites et leurs réserves, rien de plus. Le nommer ici évite qu'on l'attende de
l'outil au moment de la rédaction.

**Chiffres de référence pour la note**, une fois pour toutes (§3 du rapport
d'étape 6) : 63 147 journées mesurées sur
27 points, soit 242 couples point × année, dont
220 reçoivent une classe de validité et 156 sont
publiables.

---|---|---|
| Carte de situation des points | 1.2 | aucun fond cartographique dans le périmètre |
| Formulation du périmètre en question de gestion | 1.1 | rédaction |
| Exemple chiffré de normalisation sur un point réel | 4.1 | à produire, calcul immédiat |
| Règle d'emploi : brut ou normalisé selon l'usage | 5.2 | **décision à prendre**, pas une rédaction |
| Interprétation écologique | 6.4 | hors périmètre de l'outil, à apporter par le bureau d'études |
| Glossaire | A6 | rédaction |

**Un seul de ces manques est bloquant** : la règle d'emploi entre indicateurs bruts et normalisés (5.2). Les deux jeux sont calculés, vérifiés et publiables, mais rien ne dit lequel sert à quoi. Écrire le chapitre 5 sans cette décision reviendrait à la prendre implicitement.

---

*thermie_points 0.5bis — CORRECTIFS_V4_6.md — révision étape 5bis.*

