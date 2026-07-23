# Thermie & Débits de référence — HMUC Moselle

Analyse de la vulnérabilité thermique des cours d'eau et calcul des débits de
référence thermique (étude HMUC du bassin Moselle — approche thermique,
Point 2 de la note méthodologique). Application **Streamlit** sur package
Python modulaire.

## Fonctionnalités
- **Formats d'entrée souples** : CSV (séparateur détecté par cohérence
  tabulaire, encodage auto) et Excel `.xls`/`.xlsx` (choix de feuille,
  en-tête décalé, date+heure séparées), mapping manuel corrigeable.
- **Normales 1991–2020** calculées depuis un fichier air brut.
- Contrôle qualité, sensibilité, vulnérabilité, fraie-croissance, SGVT.
- **Onglet Indicateurs** : Tmax/Tmin (avec dates), amplitude nycthémérale,
  Tmm30j — bruts et compensés — + 4 corrélations avec R².
- **Onglet Relation Q–T°** : test préalable du postulat fondateur (voir plus bas).
- **Coupure des lacunes** : pas de raccord à travers les trous de mesure.

## Test préalable — le débit module-t-il la température ?
Toute l'approche « débits thermiques » repose sur un postulat : le débit pilote
la température de l'eau. Un onglet dédié le vérifie avant les débits, avec deux
mesures et trois gammes de débit :

- **corrélation brute** — inclut l'effet structurel du régime d'étiage ;
- **corrélation partielle à température d'air égale** — isole le rôle propre du
  débit ; robuste même sur une seule saison (elle n'exige pas de répétitions
  inter-annuelles, contrairement à un contrôle par le calendrier qui, sur une
  seule année, effacerait le signal en même temps que le confondant).

Les gammes (toute la gamme, sous la médiane, quart inférieur) révèlent les
**effets de seuil** : une relation qui se renforce vers les bas débits malgré la
réduction de variance signale une perte d'inertie thermique concentrée en
étiage.

Le verdict est gradué — *établie*, *faible*, *absente*, *inversée* — et reste
**informatif** : aucun calcul n'est interrompu, mais une réserve explicite est
affichée dans l'onglet Débits lorsque la relation n'est pas établie.

## Fraie-croissance — pondération à 3 niveaux
Score journalier sur **températures normalisées** (les % sur températures
brutes sont affichés pour information) :

| Zone | Pénalité |
|---|---|
| Optimum strict | aucune (0) |
| Fenêtre élargie, non létale | intermédiaire (1) |
| Au-delà, côté chaud (létalité embryonnaire) | forte (3) |

| Espèce | Optimum | Élargie |
|---|---|---|
| Truite fario | 6–8 °C | 4–10 °C |
| Ombre commun | 6–8 °C | 6–10 °C |
| Brochet | 8–14 °C | 8–15 °C |
| Brème | 12–21 °C | 12–23 °C |

Côté froid, la pénalité est plafonnée au palier intermédiaire (le froid ralentit
l'incubation sans létalité massive).

**Classement** : maximum entre le classement par sévérité moyenne
(seuils 0,22 / 1,05 / 1,75) et par temps en zone létale (2 % / 6 % / 15 %),
afin que la létalité ne soit jamais diluée par une bonne moyenne. Repères :
≥ 75 % du temps dans l'optimum → P0 ; 100 % en fenêtre élargie sans létalité
→ P1 ; ≥ 6 % de létalité → P2 ; ≥ 15 % → P3.

## Q_thermie_bio — déclenchement
- **Volet létal** = déclencheur principal (fiable, relié aux bas débits).
- **Volet stress chronique** = retenu **seulement** si deux conditions
  cumulatives sont réunies : *matérialité* (% de jours estivaux stressés
  au-dessus d'un plancher paramétrable, 10 % par défaut) et *causalité*
  (corrélation négative concluante, brute ou partielle).

Faute de quoi, agir sur le débit ne réduirait pas le stress : le volet est
écarté avec sa raison, et Q_thermie_bio repose sur le seul volet létal — ou
devient non applicable. La courbe stress/débit reste affichée en diagnostic.

## Sorties débits
Une **valeur brute** (base de calcul retenue) et son **PNDA** lu sur chaque
distribution — désinfluencé prioritaire, influencé en secondaire.

## Installation & lancement
```bash
pip install -r requirements.txt
streamlit run app.py
```
Exemples dans `examples/` (CSV, Excel, débits influencé et désinfluencé).
En CLI : éditer `run_cli.py` puis `python run_cli.py`.

## Déploiement Streamlit Cloud
GitHub → https://share.streamlit.io → fichier `app.py`, branche `main`.

## Structure
```
app.py  run_cli.py  requirements.txt  .streamlit/  examples/
thermie_debits/
├── config.py  io_data.py  sniff.py  qc.py  indicateurs.py
├── core.py    figures.py  exports.py
├── climatique.py          orchestrator.py
```

*Méthodologie : note méthodologique HMUC (Point 2 — approche thermique).*
