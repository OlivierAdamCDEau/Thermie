# Étape 1 — corpus déclaré, corpus observé

`data/corpus.csv` est rempli **de mémoire, sans ouvrir les fichiers** : c'est sa consigne. Ce document lui oppose ce que l'inventaire et le harnais ont trouvé. Il ne corrige pas `corpus.csv`.

48 confrontation(s) : **7 écart(s)**, 5 champ(s) déclaré(s) « à vérifier » que l'inventaire renseigne, 18 champ(s) en texte libre non comparables terme à terme.

Un champ déclaré « à vérifier » n'est pas un écart : la consigne de `corpus.csv` autorise explicitement cette réponse. Il est marqué *précisé*.

## Déclaré / observé / statut

| Jeu | Champ | Déclaré | Observé | Statut |
|---|---|---|---|---|
| jeu_02 | `n_points` | 1 | 1 | conforme |
| jeu_02 | `format_eau` | csv | csv | conforme |
| jeu_02 | `air_tn_tx` | a verifier | oui | précisé |
| jeu_02 | `pas_eau` | infra-journalier (horaire, quelques periodes a 15 et 30 min) | pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h | **ÉCART** |
| jeu_02 | `debit` | oui | oui | conforme |
| jeu_02 | `particularite` | 0,1% jours censurés, données discontinues, modèle peu fiable, faible variance - résilience élevée | 1 fichier(s) a colonne d'heure separee, recomposee ; 4 horodatage(s) en double ; encodage utf-8-sig ; vocabulaire SANDRE | texte libre |
| jeu_02 | `[hors corpus.csv] fichiers d'air` | non prevu | 1 : Q_57_57623003-1950-2026_RR-T-Vent.csv | texte libre |
| jeu_02 | `[hors corpus.csv] debit desinfluence` | non prevu | aucun : le dossier debit/ ne porte qu'un fichier | texte libre |
| jeu_03 | `n_points` | 1 | 1 | conforme |
| jeu_03 | `format_eau` | csv | csv | conforme |
| jeu_03 | `air_tn_tx` | a verifier | oui | précisé |
| jeu_03 | `pas_eau` | infra-journalier (horaire, quelques periodes a 15 et 30 min) | pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h | **ÉCART** |
| jeu_03 | `debit` | oui | oui | conforme |
| jeu_03 | `particularite` | Sensibilité modérée, modèle valide, données discontinues mais non censurées | 1 fichier(s) sans colonne d'heure reconnue ; virgule decimale ; encodage latin-1 | texte libre |
| jeu_03 | `[hors corpus.csv] fichiers d'air` | non prevu | 1 : Q_57_57039001-1950-2024_RR-T-Vent.csv | texte libre |
| jeu_03 | `[hors corpus.csv] debit desinfluence` | non prevu | aucun : le dossier debit/ ne porte qu'un fichier | texte libre |
| jeu_04 | `n_points` | 1 | 1 | conforme |
| jeu_04 | `format_eau` | xlsx | xlsx ; feuille(s) : DONNÉES, Données d'événement, Détails | **ÉCART** |
| jeu_04 | `air_tn_tx` | a verifier | oui | précisé |
| jeu_04 | `pas_eau` | infra-journalier (horaire, quelques periodes a 15 et 30 min) | pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h | **ÉCART** |
| jeu_04 | `debit` | oui | oui | conforme |
| jeu_04 | `particularite` | Faible variance expliquée, Résilience élevée, Modèle peu fiable — interprétation prudente requise | colonne d'heure detectee mais non recomposee (la date porte deja une heure) ; classeur multi-feuilles ; 2 horodatage(s) en double ; colonne en Fahrenheit a cote du Celsius | texte libre |
| jeu_04 | `[hors corpus.csv] fichiers d'air` | non prevu | 1 : Q_57_57465001-1950-2024_RR-T-Vent.csv | texte libre |
| jeu_04 | `[hors corpus.csv] debit desinfluence` | non prevu | aucun : le dossier debit/ ne porte qu'un fichier | texte libre |
| jeu_05 | `n_points` | 1 | 1 | conforme |
| jeu_05 | `format_eau` | csv | csv | conforme |
| jeu_05 | `air_tn_tx` | a verifier | oui | précisé |
| jeu_05 | `pas_eau` | infra-journalier (horaire, quelques periodes a 15 et 30 min) | pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h | **ÉCART** |
| jeu_05 | `debit` | oui | oui | conforme |
| jeu_05 | `particularite` | R² variance modérée, sensibilité modérée, Modèle acceptable — résultats à nuancer | 1 fichier(s) sans colonne d'heure reconnue ; virgule decimale ; 2 horodatage(s) en double ; encodage utf-8-sig | texte libre |
| jeu_05 | `[hors corpus.csv] fichiers d'air` | non prevu | 1 : Q_57_57587003-1950-2024_RR-T-Vent.csv | texte libre |
| jeu_05 | `[hors corpus.csv] debit desinfluence` | non prevu | aucun : le dossier debit/ ne porte qu'un fichier | texte libre |
| jeu_bienne | `n_points` | 27 | 27 | conforme |
| jeu_bienne | `format_eau` | xlsx (feuille ValInstantanees) | xlsx ; feuille(s) : ValInstantanees | conforme |
| jeu_bienne | `air_tn_tx` | oui | oui | conforme |
| jeu_bienne | `pas_eau` | infra-journalier (horaire, quelques periodes a 15 et 30 min) | pas modal : 1 h, 1 j ; intervalles presents (>= 5 occurrences) : 43 s, 15 min, 30 min, 3557 s, 1 h, 1 j | **ÉCART** |
| jeu_bienne | `debit` | non | non | conforme |
| jeu_bienne | `particularite` | un fichier porte la date et l'heure dans deux colonnes separees | 26 fichier(s) a colonne d'heure separee, recomposee ; 1 fichier(s) sans colonne d'heure reconnue ; 2828 horodatage(s) en double ; virgule decimale dans la chronique d'air | texte libre |
| jeu_bienne | `[hors corpus.csv] fichiers d'air` | non prevu | 1 : LA_PESSE.csv | texte libre |
| jeu_bienne | `[hors corpus.csv] debit desinfluence` | non prevu | aucun : le dossier debit/ ne porte qu'un fichier | texte libre |
| jeu_exemples_v45 | `n_points` | 1 | 1 | conforme |
| jeu_exemples_v45 | `format_eau` | csv | csv | conforme |
| jeu_exemples_v45 | `air_tn_tx` | a verifier | oui | précisé |
| jeu_exemples_v45 | `pas_eau` | infra-journalier (horaire, quelques periodes a 15 et 30 min) | pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h, 6 h | **ÉCART** |
| jeu_exemples_v45 | `debit` | oui | oui | conforme |
| jeu_exemples_v45 | `particularite` | seulement 4 mois couverts, modèle valide, sensibilité modérée | 1 fichier(s) sans colonne d'heure reconnue ; encodage utf-8-sig | texte libre |
| jeu_exemples_v45 | `[hors corpus.csv] fichiers d'air` | non prevu | 1 : Temp Air Rupt-sur-Moselle_1950-2026.xlsx | texte libre |
| jeu_exemples_v45 | `[hors corpus.csv] debit desinfluence` | non prevu | aucun : le dossier debit/ ne porte qu'un fichier | texte libre |

## Les écarts, un par un

**É1 — jeu_02 · `pas_eau`**

- déclaré : infra-journalier (horaire, quelques periodes a 15 et 30 min)
- observé : pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h

**É2 — jeu_03 · `pas_eau`**

- déclaré : infra-journalier (horaire, quelques periodes a 15 et 30 min)
- observé : pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h

**É3 — jeu_04 · `format_eau`**

- déclaré : xlsx
- observé : xlsx ; feuille(s) : DONNÉES, Données d'événement, Détails

**É4 — jeu_04 · `pas_eau`**

- déclaré : infra-journalier (horaire, quelques periodes a 15 et 30 min)
- observé : pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h

**É5 — jeu_05 · `pas_eau`**

- déclaré : infra-journalier (horaire, quelques periodes a 15 et 30 min)
- observé : pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h

**É6 — jeu_bienne · `pas_eau`**

- déclaré : infra-journalier (horaire, quelques periodes a 15 et 30 min)
- observé : pas modal : 1 h, 1 j ; intervalles presents (>= 5 occurrences) : 43 s, 15 min, 30 min, 3557 s, 1 h, 1 j

**É7 — jeu_exemples_v45 · `pas_eau`**

- déclaré : infra-journalier (horaire, quelques periodes a 15 et 30 min)
- observé : pas modal : 1 h ; intervalles presents (>= 5 occurrences) : 1 h, 6 h


## Caractéristiques NON COUVERTES

Ce que l'outil sait lire mais qu'aucun jeu du corpus n'exerce. Elles sont **nommées, pas comblées** (D6) : fabriquer un jeu de test pour les couvrir reviendrait à tester l'idée qu'on se fait du format, pas le format.

Deux natures de vide sont distinguées : celui qu'aucun jeu n'exerce, et celui qu'**aucun jeu ne pourrait exercer** parce que le code ne peut pas y arriver.

| Famille | Caractéristique | Nature |
|---|---|---|
| separateur | separateur : virgule detecte par sniff (hors parseur debit) | non exercé par le corpus |
| separateur | separateur : tabulation | non exercé par le corpus |
| separateur | separateur : barre verticale | non exercé par le corpus |
| encodage | encodage utf-8 | **inatteignable par construction** — sniff.ENCODAGES commence par utf-8-sig (sniff.py:19), qui decode aussi bien l'UTF-8 sans BOM : la branche « utf-8 » n'est jamais atteinte |
| encodage | encodage cp1252 | **inatteignable par construction** — latin-1 precede cp1252 dans sniff.ENCODAGES (sniff.py:19) et ne leve jamais : la branche cp1252 n'est jamais atteinte |
| encodage | encodage utf-8(replace) | **inatteignable par construction** — le repli errors=replace (sniff.py:156) suppose que toute la cascade a echoue ; latin-1 ne peut pas echouer |
| format | fichier Excel ancien (.xls, moteur xlrd) | non exercé par le corpus |
| format | fichier Excel a macros (.xlsm) | non exercé par le corpus |
| date | format de date : YYYY-MM-DD (sans heure) | non exercé par le corpus |
| date | format de date : DD/MM/YYYY HH:MM (sans secondes) | non exercé par le corpus |
| date | format de date : date en anglais (Jan, Feb...) | non exercé par le corpus |
| date | format de date : serie Excel numerique brute | non exercé par le corpus |
| date | format de date : horodatage avec fuseau explicite (+02:00) dans la valeur | non exercé par le corpus |
| pas | intervalle de 2 h (7200 s) reellement present (>= 5 occurrences) | non exercé par le corpus |
| pas | chronique d'eau livree deja agregee au jour par la source (et non par perte de la colonne d'heure) | non exercé par le corpus |
| air | fichier d'air SANS TN ni TX | non exercé par le corpus |
| air | export Meteo-France MULTI-stations (stations_air non vide) | non exercé par le corpus |
| debit | debit desinfluence fourni | non exercé par le corpus |
| debit | normales pre-calculees (EcartNormales.csv) fournies — branche fichier_normales | non exercé par le corpus |
| harnais | journees ecartees a motif NON_RECUPERABLE | non exercé par le corpus |
| harnais | chevauchement de series sur un meme point (plusieurs fichiers pour un meme code) | non exercé par le corpus |

