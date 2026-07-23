# Thermie & Débits de référence — HMUC Moselle

Analyse de la vulnérabilité thermique des cours d'eau et calcul des débits de
référence thermique (étude HMUC du bassin Moselle — approche thermique,
Point 2 de la note méthodologique). Application **Streamlit** sur package
Python modulaire.

## Cadre de lecture — que permet de conclure l'analyse ?

L'outil croise **deux questions distinctes** qu'il ne faut pas confondre, et
restitue le résultat sous forme de matrice (onglet Synthèse, figure exportable) :

| | **Levier débit opérant** | **Levier débit non opérant** |
|---|---|---|
| **Problème thermique avéré** | Débit thermique pertinent — objectif fondé et opposable | Problème réel, levier autre : ombrage, morphologie, rejets, nappe |
| **Pas de problème thermique** | Pas d'enjeu actuel, mais milieu sensible — surveillance | Approche thermique peu opérante — d'autres volets HMUC sont plus pertinents |

Le postulat « le débit module la température » est testé explicitement (onglet
Relation Q–T°) par deux mesures — corrélation **brute** et **partielle à
température d'air égale** — déclinées sur trois gammes de débit pour détecter
les effets de seuil. Ces corrélations sont la **source unique** du projet : le
verrou du volet stress consomme exactement les mêmes valeurs, ce qui rend toute
contradiction d'affichage impossible.

## Fraie-croissance — trois phases, trois tolérances

| Espèce | Pré-frai | Ponte ★ | Incubation ★ |
|---|---|---|---|
| **Truite fario** | oct–nov · 1–10 °C | nov–janv · 4–8 °C | déc–mars · 4–8 °C |
| **Ombre commun** | mars · 5–9 °C | mars–avr · 7–10 °C | avr–mai · 6–10 °C |
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
- **Normales 1991–2020** calculées depuis un fichier air brut.
- **Onglet Indicateurs** : Tmax/Tmin (avec dates), amplitude nycthémérale,
  Tmm30j — bruts et compensés — + 4 corrélations avec R².
- **Coupure des lacunes** : pas de raccord à travers les trous de mesure.
- **Sorties débits** : valeur brute + PNDA sur chaque distribution
  (désinfluencé prioritaire, influencé en secondaire).
- **Export XLSX** détaillant chaque phase de reproduction.

## Installation & lancement
```bash
pip install -r requirements.txt
streamlit run app.py
```
Exemples dans `examples/` — chroniques **annuelles sur 3 ans**, nécessaires pour
couvrir les trois phases de reproduction. En CLI : éditer `run_cli.py` puis
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
