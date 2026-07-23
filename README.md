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
- **Onglet Relation Q–T°** : test préalable du postulat fondateur.
- **Coupure des lacunes** : pas de raccord à travers les trous de mesure.

## Fraie-croissance — trois phases, trois tolérances

Chaque espèce repère est évaluée sur **trois phases successives** dont les
exigences thermiques diffèrent. Un jour appartenant à deux phases qui se
chevauchent reçoit le score le plus contraignant. Le score global porte sur
l'ensemble de la fenêtre ; le détail par phase est restitué.

| Espèce | Pré-frai | Ponte ★ | Incubation ★ |
|---|---|---|---|
| **Truite fario** (oct→mars) | oct–nov · 1–10 °C | nov–janv · 4–8 °C | déc–mars · 4–8 °C |
| **Ombre commun** (mars→mai) | mars · 5–9 °C | mars–avr · 7–10 °C | avr–mai · 6–10 °C |
| **Brochet** (févr→avr) | févr · 4–7 °C | févr–mars · 7–11 °C | mars–avr · 8–12 °C |
| **Brème** (avr→juil) | avr–mai · 12–16 °C | mai–juin · 15–20 °C | juin–juil · 16–21 °C |

★ phases critiques : au moins une doit être couverte pour que le sous-indicateur
soit évalué.

**Pondération à trois paliers** (sur températures normalisées ; les % sur
températures brutes sont affichés pour information) : optimum strict → aucune
pénalité ; tolérance élargie → pénalité intermédiaire ; au-delà → pénalité forte.

**Traitement du froid.** Côté chaud, dépasser la tolérance élargie signifie
létalité embryonnaire. Côté froid, deux situations biologiques distinctes :
- *truite* (pondeur automnal) — le froid **ralentit** l'incubation sans mortalité
  massive : pénalité plafonnée au palier intermédiaire ;
- *ombre, brochet, brème* (pondeurs printaniers et estivaux) — le froid **bloque**
  la reproduction (refus de frayer, atrésie folliculaire chez la brème) : échec
  reproducteur, pénalité forte. Ce blocage ne s'applique qu'aux phases critiques,
  car en pré-frai une eau froide décale simplement le frai sans le compromettre.

**Classement** : maximum entre le classement par sévérité moyenne
(0,22 / 1,05 / 1,75) et par temps en zone létale (2 % / 6 % / 15 %).

Sources : Elliott & Hurley (1998), Réalis-Doyelle et al. (2016), Crisp (1993) ·
Jungwirth & Winkler (1984), Humpesch (1985) · Hokanson et al. (1973), Bry (1996) ·
Herzig & Winkler (1986), Poncin et al. (1996), Sych et al. (1999).

## Test préalable — le débit module-t-il la température ?
Deux mesures — corrélation **brute** et **partielle à température d'air égale**
(robuste même sur une seule saison) — déclinées sur trois gammes de débit pour
détecter les effets de seuil. Verdict gradué (établie / faible / absente /
inversée), **informatif** : aucun calcul n'est interrompu, mais une réserve
explicite s'affiche dans l'onglet Débits.

## Q_thermie_bio — déclenchement
- **Volet létal** = déclencheur principal.
- **Volet stress chronique** = retenu seulement si le stress est matériel
  (plancher paramétrable) **et** réellement piloté par le débit.

## Sorties débits
Une **valeur brute** (base de calcul retenue) et son **PNDA** lu sur chaque
distribution — désinfluencé prioritaire, influencé en secondaire.

## Installation & lancement
```bash
pip install -r requirements.txt
streamlit run app.py
```
Exemples dans `examples/` (chroniques **annuelles**, nécessaires pour couvrir
les trois phases de reproduction). En CLI : éditer `run_cli.py` puis
`python run_cli.py`.

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
