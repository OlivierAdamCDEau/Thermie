# Thermie & Débits de référence — HMUC Moselle

Outil d'analyse de la vulnérabilité thermique des cours d'eau et de calcul
des débits de référence thermique (étude HMUC du bassin Moselle — approche
thermique, Point 2 de la note méthodologique).

Application **Streamlit** reposant sur un package Python modulaire
(`thermie_debits/`).

## Fonctionnalités
- Chargement robuste des sondes (auto-détection séparateur/encodage/colonnes,
  mapping manuel corrigeable).
- Normales 1991–2020 calculées automatiquement depuis un fichier air brut
  (sélection des années, normale journalière lissée, écarts).
- Contrôle qualité, sensibilité, vulnérabilité, fraie-croissance, SGVT,
  débits de référence, volet climatique (bonus).

## Deux modes
- **Thermie seule** : caractérisation thermique + SGVT, sans débit.
- **Thermie + débits** : ajoute les débits de référence.

## Sorties débits
Chaque débit de référence (Q_thermie_bio prépondérant, Q_thermie_fonc en
complément) est exprimé par **une valeur brute** (base de calcul retenue) et
son **PNDA** lu sur chaque distribution : désinfluencé prioritaire, influencé
en information secondaire. Si le désinfluencé n'est pas fourni, l'influencé
devient la référence par défaut.

## Installation & lancement
```bash
pip install -r requirements.txt
streamlit run app.py
```
Exemples fournis dans `examples/` (dont un débit désinfluencé) pour tester
immédiatement. En CLI : éditer `run_cli.py` puis `python run_cli.py`.

## Données attendues (CSV)
| Fichier | Contenu | Remarque |
|---|---|---|
| Sonde eau | Date (+heure) et température | séparateur/colonnes auto-détectés |
| Air (référence) | T° journalières **brutes** (`AAAAMMJJ`, `TM`, `RR`) | un seul fichier ≥ 1991–2020 |
| Débit influencé | Vigicrues / Hub'eau | requis en mode thermie+débits |
| Débit désinfluencé | (optionnel) | active la double expression PNDA |

## Déploiement Streamlit Cloud
Pousser sur GitHub → https://share.streamlit.io → New app → fichier `app.py`,
branche `main`. Les dépendances s'installent depuis `requirements.txt`.

## Structure
```
app.py  run_cli.py  requirements.txt  .streamlit/config.toml  examples/
thermie_debits/
├── config.py  io_data.py  sniff.py  qc.py
├── core.py    figures.py  exports.py
├── climatique.py          orchestrator.py
```

*Méthodologie : note méthodologique HMUC (Point 2 — approche thermique).*
