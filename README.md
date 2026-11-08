# Thermie & débits de référence

L'application évalue la **vulnérabilité thermique d'un cours d'eau pour le
poisson** : elle croise une chronique de température d'eau mesurée par une sonde
posée en rivière, la température de l'air d'une station météorologique de
référence et, quand elle existe, une chronique de débit. Elle en tire un
diagnostic — journées franchissant les seuils biologiques de l'espèce repère,
déroulement de la période de reproduction, note de synthèse allant du risque
faible au risque élevé — et, lorsque la température répond effectivement au
débit, un débit de référence thermique. Le tout est restitué à l'écran, dans un
rapport Word et dans un classeur Excel.

Application **Streamlit** sur package Python modulaire. Elle ne suppose aucun
bassin, aucune étude ni aucun contexte particulier : tout ce qui la paramètre
est fourni en entrée ou choisi dans la barre latérale.

## Version 4.7 — plusieurs sondes en une fois

Déposer plusieurs sondes et un ou plusieurs fichiers d'air fait apparaître un
**tableau de rapprochement sondes / station météo** : feuille Excel, colonnes,
cours d'eau et point sont pré-remplis par détection (format d'échange DCE
reconnu tel quel), la station d'air se choisit sonde par sonde, et le tableau
s'enregistre en CSV pour être rechargé à la session suivante. L'analyse tourne
sur toutes les sondes cochées, puis une synthèse les empile et tous les
rapports se téléchargent en un ZIP. Aucun calcul n'est modifié — voir
[`CHANGELOG.md`](CHANGELOG.md).

## Version 4.6

La 4.6 corrige **treize défauts** de la chaîne qui va de la lecture des fichiers
à la température normalisée : détection des sondes hors de l'eau, traçabilité
des données écartées, moyennes glissantes comptées en jours et non en lignes,
normale de l'air suivant le calendrier, statut de la normalisation affiché avant
les chiffres qu'il qualifie. Sur les trente-deux stations qui ont servi à les
mesurer, **deux ont changé de catégorie** ; partout ailleurs les catégories
publiées sont inchangées.

- [`CHANGELOG.md`](CHANGELOG.md) — les treize correctifs, un par ligne.
- `docs/BILAN_V4_6.md` — le bilan rédigé pour le maître d'ouvrage, sans
  prérequis technique : ce que l'outil faisait, ce qu'il fait, le détail des
  résultats déplacés, et **les limites qui subsistent** — mesurées, non
  adoucies. À lire avant de conclure quoi que ce soit d'un résultat.

## Ce que contient le dépôt, et ce qui s'exécute

Le code de l'application est ici. À côté de lui, deux dossiers portent la trace
du chantier de reprise : ils se lisent, ils ne s'exécutent pas.

| | Contenu | S'exécute ? |
|---|---|---|
| `app.py`, `thermie_debits/` | l'application | **oui** |
| `examples/` | trois chroniques de démonstration | **oui** |
| `docs/` | la trace méthodologique du chantier | non — documents |
| `tests/reference/` | le harnais de non-régression | **non — voir ci-dessous** |

### `docs/` — la trace méthodologique

Le carnet de méthode et les **vingt et un rapports d'étape**, qui suivent le
chantier dans l'ordre où il a eu lieu ; **trois spécifications** — le détecteur
de sondes hors d'eau et la validité du modèle air–eau, la convention unique de
normalisation, la complétude des journées ; et le **journal des résultats
déplacés**, qui recense station par station chaque conclusion publiée qui
change, avec la mesure de son déplacement.

### `tests/reference/` — le harnais de non-régression

Il fige, artefact par artefact, ce que produisait la version en service, puis
rejoue le corpus avec le code courant et compare. C'est lui qui permet
d'affirmer qu'un correctif a déplacé exactement ce qu'il annonçait, et rien
d'autre.

**Ces scripts ne tournent pas en l'état, et c'est normal.** Ils réclament deux
choses qui ne sont pas diffusées : le **corpus de test** et les **références
figées** qui en dérivent. Sans elles, un script s'arrête faute de trouver ses
entrées, ou refuse de comparer un rejeu à une référence dont il ne peut pas
établir la provenance. Ils sont publiés parce qu'ils **disent comment les
résultats ont été vérifiés** — pas pour être relancés tels quels.

### Pourquoi le corpus de test n'est pas diffusé

Ce sont des mesures réelles de stations réelles : chroniques de sonde, de débit
et de température d'air appartenant aux maîtres d'ouvrage des études dont elles
proviennent. Elles n'ont pas été collectées pour être republiées, et l'outil
n'en est pas propriétaire. Les références figées en dérivent directement — elles
en contiennent les valeurs — et suivent donc la même règle.

`examples/` fournit de quoi prendre l'application en main : des chroniques
**annuelles sur 3 ans**, nécessaires pour couvrir les trois phases de
reproduction.

## Cadre de lecture — que permet de conclure l'analyse ?

L'outil croise **deux questions distinctes** qu'il ne faut pas confondre, et
restitue le résultat sous forme de matrice (onglet Synthèse, figure exportable) :

| | **Levier débit opérant** | **Levier débit non opérant** |
|---|---|---|
| **Problème thermique avéré** | Débit thermique pertinent — objectif fondé et opposable | Problème réel, levier autre : ombrage, morphologie, rejets, nappe |
| **Pas de problème thermique** | Pas d'enjeu actuel, mais milieu sensible — surveillance | Approche thermique peu opérante — d'autres approches sont plus pertinentes |

Le postulat « le débit module la température » est testé explicitement (onglet
Relation Q–T°) par deux mesures — corrélation **brute** et **partielle à
température d'air égale** — déclinées sur trois gammes de débit pour détecter
les effets de seuil. Ces corrélations sont la **source unique** du projet : le
verrou du volet stress consomme exactement les mêmes valeurs, ce qui rend toute
contradiction d'affichage impossible.

## Espèce repère — un arbitrage en zone intermédiaire

Les seuils estivaux et le plancher de la classe « Faible » sont des propriétés
de **l'espèce repère**, non de la zonation. La zone intermédiaire SANDRE admet
deux espèces repères thermiques ; le choix se fait dans la barre latérale et
change les résultats.

| Zone | Espèce repère | Stress (Tmh_norm) | Létalité (Tmax_norm) | Plancher « Faible » |
|---|---|---|---|---|
| Salmonicole | Truite fario | > 18 °C | > 24 °C | 3 % |
| Intermédiaire | Ombre commun *(défaut)* | > 18 °C | > 23 °C | 3 % |
| Intermédiaire | Barbeau commun | > 24 °C | > 28 °C | 5 % |
| Cyprinicole | Brème commune | > 26 °C | > 30 °C | 5 % |

Le plancher de classe sert aussi de cible à la recherche du volet stress de
Q_thermie_bio : une seule valeur, deux usages, aucune divergence possible.

Retenir le barbeau n'assouplit pas l'analyse dans tous les compartiments : les
seuils estivaux sont plus élevés, mais la fenêtre de reproduction est plus
exigeante **côté froid** (ponte suspendue sous ≈ 15 °C en Tmh), ce qui peut
dégrader la composante fraie-croissance sur un cours d'eau frais.

## Fraie-croissance — trois phases, trois tolérances

| Espèce | Pré-frai | Ponte ★ | Incubation ★ |
|---|---|---|---|
| **Truite fario** | oct–nov · 1–10 °C | nov–janv · 4–8 °C | déc–mars · 4–8 °C |
| **Ombre commun** | mars · 5–9 °C | mars–avr · 7–10 °C | avr–mai · 6–10 °C |
| **Barbeau** | avr–mai · 11–17 °C | mai–juin · 15–20 °C | juin–juil · 15–20 °C |
| **Brochet** | févr · 4–7 °C | févr–mars · 7–11 °C | mars–avr · 8–12 °C |
| **Brème** | avr–mai · 12–16 °C | mai–juin · 15–20 °C | juin–juil · 16–21 °C |

★ phases critiques : au moins une doit être couverte pour que le sous-indicateur
soit évalué. Un jour partagé entre deux phases reçoit le score le plus contraignant.

**Trois paliers** (sur températures normalisées ; les % sur températures brutes
sont restitués pour information) : optimum strict → aucune pénalité ; tolérance
élargie → pénalité intermédiaire ; au-delà → pénalité forte.

**Traitement du froid** — deux situations biologiques distinctes :
- *truite* (pondeur automnal) : le froid **ralentit** l'incubation → pénalité
  intermédiaire ;
- *ombre, brochet, brème* (pondeurs printaniers/estivaux) : le froid **bloque**
  la reproduction (refus de frayer, atrésie folliculaire) → pénalité forte.
  Ce blocage ne s'applique qu'aux phases critiques : en pré-frai, une eau froide
  décale le frai sans le compromettre.

**Classement** : maximum entre sévérité moyenne (0,22 / 1,05 / 1,75) et temps en
zone létale (2 % / 6 % / 15 %).

Sources : Elliott & Hurley (1998), Réalis-Doyelle et al. (2016), Crisp (1993) ·
Jungwirth & Winkler (1984), Humpesch (1985) · Hokanson et al. (1973), Bry (1996) ·
Herzig & Winkler (1986), Poncin et al. (1996), Sych et al. (1999).

## Q_thermie_bio — déclenchement
- **Volet létal** = déclencheur principal.
- **Volet stress chronique** = retenu seulement si le stress est matériel
  (plancher paramétrable) **et** réellement piloté par le débit.

## Autres fonctionnalités
- **Formats d'entrée souples** : CSV (séparateur détecté par cohérence
  tabulaire, encodage auto) et Excel `.xls`/`.xlsx` (feuille, en-tête décalé,
  date+heure séparées), mapping manuel corrigeable.
- **Normales 1991–2020** calculées depuis un fichier air brut, sur le couple
  (mois, jour) — insensibles aux années bissextiles.
- **Onglet « Ce qui a été vérifié »** : chaque contrôle y dit ce qu'il a examiné,
  ce qu'il a trouvé et ce sur quoi il s'abstient — y compris quand il n'a rien
  trouvé. Repris à l'identique dans le rapport Word et le classeur.
- **Données écartées tracées** : les quatre étapes qui écartent des mesures
  produisent chacune un tableau daté et motivé. Écarter n'est plus effacer.
- **Statut de la normalisation** annoncé avant les chiffres qu'il qualifie :
  quand la relation air–eau ne peut pas être établie, la correction climatique
  n'est pas appliquée et le document le dit.
- **Onglet Indicateurs** : Tmax/Tmin (avec dates), amplitude nycthémérale,
  Tmm30j brut, plus 4 corrélations avec R².
- **Coupure des lacunes** : pas de raccord à travers les trous de mesure ; les
  fenêtres glissantes comptent des jours de calendrier.
- **Sorties débits** : valeur brute + PNDA sur chaque distribution
  (désinfluencé prioritaire, influencé en secondaire).
- **Livrables** : rapport Word en chapitres et classeur Excel en onglets
  miroirs, détaillant chaque phase de reproduction.

## Installation & lancement
```bash
pip install -r requirements.txt
streamlit run app.py
```
En CLI : éditer `run_cli.py` puis `python run_cli.py`.

## Déploiement Streamlit Cloud
GitHub → https://share.streamlit.io → fichier `app.py`, branche `main`.

## Structure
```
app.py  run_cli.py  requirements.txt  .streamlit/  examples/
thermie_debits/
├── config.py  io_data.py  sniff.py  qc.py  indicateurs.py
├── core.py    figures.py  exports.py  climatique.py
├── orchestrator.py  livrables.py  redaction.py  print_style.py
```

*Le carnet de méthode complet est dans `docs/`.*
