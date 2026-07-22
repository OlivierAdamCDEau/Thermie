# Thermie & Débits de référence — HMUC Moselle

Outil d'analyse de la vulnérabilité thermique des cours d'eau et de calcul
des débits de référence thermique (étude HMUC du bassin Moselle — approche
thermique, Point 2 de la note méthodologique).

Application **Streamlit** reposant sur un package Python modulaire
(`thermie_debits/`) séparant strictement le calcul de la présentation.

---

## Fonctionnalités

- **Chargement robuste** des chroniques de sonde : auto-détection du
  séparateur, de l'encodage et des colonnes, avec mapping manuel corrigeable.
- **Normales calculées automatiquement** depuis un fichier air brut : l'app
  sélectionne les années 1991–2020, calcule la normale lissée de chaque jour
  calendaire, puis les écarts pour toutes les années observées.
- **Contrôle qualité** des chroniques (sonde hors d'eau, plateaux, MAD).
- **Sensibilité**, **vulnérabilité** (chronique/aiguë), **fraie-croissance**,
  **SGVT** (4 composantes), **débits de référence** (Q_thermie_bio / fonc).
- **Volet climatique** descriptif (bonus).

## Deux modes
- **Thermie seule** : caractérisation thermique + SGVT, sans débit.
- **Thermie + débits** : ajoute les débits de référence.

---

## Installation & lancement

```bash
pip install -r requirements.txt
streamlit run app.py
```

Des fichiers d'exemple sont fournis dans `examples/` pour tester
immédiatement (air brut 1991–2022, eau 2021–2022, débit).

En ligne de commande : éditer la CONFIG dans `run_cli.py` puis
`python run_cli.py`.

---

## Données attendues (CSV)

| Fichier | Contenu | Remarque |
|---|---|---|
| Sonde eau | Date (+heure) et température | séparateur/colonnes auto-détectés |
| **Air (référence)** | T° journalières **brutes** (ex. `AAAAMMJJ`, `TM`, `RR`) | **un seul fichier**, couvrant ≥ 1991–2020 et idéalement les années des mesures d'eau |
| Débit influencé | Vigicrues / Hub'eau | requis en mode thermie+débits |
| Débit désinfluencé | (optionnel) | |

> **Normales** : plus besoin de fichier `EcartNormales` pré-calculé. L'app
> établit les normales 1991–2020 et les écarts directement depuis l'air brut.
> Le lissage (± jours) et le seuil d'années minimum sont réglables.

## Base de débit (influencé / désinfluencé)

- Désinfluencé absent → base **influencée** (avertissement).
- Écart médian < seuil (10 % par défaut) → base **désinfluencée**, trous
  comblés par l'influencé.
- Écart ≥ seuil → bascule en base **influencée** (forte divergence = fortes
  pressions anthropiques).

---

## Déploiement Streamlit Community Cloud

1. Pousser ce dépôt sur GitHub.
2. Sur https://share.streamlit.io : « New app », sélectionner le dépôt,
   fichier principal `app.py`, branche `main`.
3. Déployer (les dépendances de `requirements.txt` s'installent seules).

## Structure

```
app.py                     interface Streamlit
run_cli.py                 exécution en ligne de commande
requirements.txt
.streamlit/config.toml     thème + upload élargi
examples/                  jeux de données de démonstration
thermie_debits/            package (cœur de calcul, sans I/O)
├── config.py   io_data.py   sniff.py   qc.py
├── core.py     figures.py   exports.py
├── climatique.py           orchestrator.py
```

---

*Méthodologie : note méthodologique HMUC (Point 2 — approche thermique).*
