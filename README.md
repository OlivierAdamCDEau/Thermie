# Thermie & Débits de référence — HMUC Moselle

Outil d'analyse de la vulnérabilité thermique des cours d'eau et de calcul
des débits de référence thermique (étude HMUC du bassin Moselle — approche
thermique, Point 2 de la note méthodologique).

Application **Streamlit** reposant sur un package Python modulaire.

## Fonctionnalités
- **Formats d'entrée souples** : CSV (séparateur/encodage auto-détectés) et
  Excel `.xls`/`.xlsx` (choix de la feuille, détection de l'en-tête décalé,
  date+heure séparées), avec mapping manuel corrigeable.
- **Normales 1991–2020** calculées automatiquement depuis un fichier air brut.
- **Contrôle qualité**, sensibilité, vulnérabilité, fraie-croissance, SGVT,
  débits de référence.
- **Onglet Indicateurs** : Tmax/Tmin (mensuels + annuels, avec dates),
  amplitude nycthémérale (moy ± σ), Tmm30j — bruts et compensés — plus quatre
  corrélations linéaires (amplitude/débit, amplitude/T°eau, écart T°eau−T°air
  /débit, écart/T°eau) avec R².
- **Coupure des lacunes** : les tracés ne relient plus les points de part et
  d'autre d'un trou de mesure (détection auto du pas d'échantillonnage).
- **Volet climatique** descriptif (bonus).

## Deux modes
- **Thermie seule** : caractérisation thermique + SGVT, sans débit.
- **Thermie + débits** : ajoute les débits de référence.

## Sorties débits
Chaque débit de référence (Q_thermie_bio prépondérant, Q_thermie_fonc en
complément) : **une valeur brute** (base de calcul retenue) et son **PNDA** lu
sur chaque distribution — désinfluencé prioritaire, influencé en secondaire.

## Installation & lancement
```bash
pip install -r requirements.txt
streamlit run app.py
```
Exemples dans `examples/` (dont un fichier Excel de démonstration). En CLI :
éditer `run_cli.py` puis `python run_cli.py`.

## Données attendues
| Fichier | Contenu | Formats |
|---|---|---|
| Sonde eau | Date (+heure) et température | CSV, xls, xlsx |
| Air (référence) | T° journalières brutes (`AAAAMMJJ`, `TM`, `RR`) | CSV, xls, xlsx |
| Débit influencé | Vigicrues / Hub'eau | CSV |
| Débit désinfluencé | (optionnel) | CSV |

## Déploiement Streamlit Cloud
Pousser sur GitHub → https://share.streamlit.io → fichier `app.py`, branche
`main`. Dépendances installées depuis `requirements.txt` (dont `xlrd` pour .xls).

## Structure
```
app.py  run_cli.py  requirements.txt  .streamlit/  examples/
thermie_debits/
├── config.py  io_data.py  sniff.py  qc.py  indicateurs.py
├── core.py    figures.py  exports.py
├── climatique.py          orchestrator.py
```

*Méthodologie : note méthodologique HMUC (Point 2 — approche thermique).*
