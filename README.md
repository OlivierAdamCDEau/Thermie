# Thermie & Débits de référence — HMUC Moselle

Outil d'analyse de la vulnérabilité thermique des cours d'eau et de calcul
des débits de référence thermique, dans le cadre de l'étude HMUC du bassin
Moselle (approche thermique — Point 2 de la note méthodologique).

Application web **Streamlit** reposant sur un package Python modulaire
(`thermie_debits/`) séparant strictement le calcul de la présentation.

---

## Fonctionnalités

- **Contrôle qualité** automatique des chroniques (sonde hors d'eau,
  plateaux, valeurs aberrantes, outliers MAD) — paramétrable.
- **Normalisation climatique** sur les normales 1991–2020.
- **Sensibilité thermique** (couplage air–eau, indice de robustesse |ρ−r|).
- **Vulnérabilité** chronique et aiguë, par zonation piscicole.
- **Fraie-croissance** : composante dédiée aux stades précoces, par espèce
  repère, avec gestion des chroniques lacunaires (mois central).
- **SGVT** (Score Global de Vulnérabilité Thermique) à 4 composantes.
- **Débits de référence** : Q_thermie_bio (principal) et Q_thermie_fonc.
- **Volet climatique** descriptif (bonus).

## Deux modes
- **Thermie seule** : caractérisation thermique + SGVT, sans débit.
- **Thermie + débits** : ajoute les débits de référence.

---

## Installation locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501. Des fichiers d'exemple sont
fournis dans `examples/` pour tester immédiatement.

## Utilisation en ligne de commande (batch)

```bash
# éditer la CONFIG dans run_cli.py puis :
python run_cli.py
```

---

## Déploiement sur Streamlit Community Cloud

1. Pousser ce dépôt sur GitHub.
2. Sur https://share.streamlit.io, « New app », sélectionner le dépôt.
3. Fichier principal : `app.py`. Branche : `main`.
4. Déployer. Les dépendances de `requirements.txt` sont installées
   automatiquement.

---

## Structure

```
.
├── app.py                  # interface Streamlit
├── run_cli.py              # exécution en ligne de commande
├── requirements.txt
├── .streamlit/
│   └── config.toml         # thème + taille max d'upload
├── examples/               # jeux de données de démonstration
│   ├── eau.csv  air.csv  EcartNormales.csv  debit.csv
└── thermie_debits/         # package (cœur de calcul, sans I/O)
    ├── config.py           # paramètres typés
    ├── io_data.py          # loaders + fusion débits
    ├── qc.py               # contrôle qualité
    ├── core.py             # chaîne de calcul
    ├── figures.py          # figures matplotlib
    ├── exports.py          # exports CSV / XLSX
    ├── climatique.py       # volet climatique bonus
    └── orchestrator.py     # enchaînement → objet Resultats
```

## Données attendues (CSV, séparateur `;`)

| Fichier | Contenu |
|---|---|
| Sonde eau | Date (+ heure) et température de l'eau |
| Air (Météo-France) | Colonnes `AAAAMMJJ`, `TM` (et `RR` si disponible) |
| Normales | `Date`, `Delta_TMm`, `TMm` (référence 1991–2020) |
| Débit influencé | Vigicrues / Hub'eau (requis en mode thermie+débits) |
| Débit désinfluencé | Optionnel |

## Base de débit (influencé / désinfluencé)

- Désinfluencé absent → base **influencée** (avertissement).
- Désinfluencé présent, écart médian < seuil (10 % par défaut) → base
  **désinfluencée**, trous comblés par l'influencé.
- Écart ≥ seuil → bascule en base **influencée** (forte divergence =
  fortes pressions anthropiques).

---

*Méthodologie : voir la note méthodologique HMUC (Point 2 — approche thermique).*
