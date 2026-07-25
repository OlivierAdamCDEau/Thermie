# Journal des versions

## 3.4 — 2026-07-26
- **Correctif majeur — polices trop grandes à l'écran** : le plancher de
  lisibilité à l'impression (8 pt à 16/24,7 cm) s'appliquait par erreur
  directement à l'affichage, gonflant des textes calibrés pour l'écran
  (ex. jauge SGVT) sans réajuster leur espacement, provoquant des
  chevauchements. Architecture corrigée : l'écran conserve les proportions
  d'origine ; seule la copie téléchargée (`print_style.make_print_ready`)
  applique le plancher, sur une figure dupliquée indépendamment.
- **Correctif — débordement de tableau** : le calcul du budget de caractères
  se basait sur la largeur totale de la figure plutôt que sur la largeur
  réelle de l'axe contenant le tableau (qui n'en occupe qu'une fraction à
  cause du panneau voisin) — corrigé et vérifié sans débordement résiduel.
- **Légendes réellement translucides** : opacité ramenée de 0,90 à 0,62.
- **Période d'affichage** : format JJ/MM/AAAA ; correctif de réactivité — les
  trois figures chroniques (Synthèse, QC, Vulnérabilité) se régénèrent
  maintenant à la volée à chaque changement, sans relancer l'analyse.
- **Fraie-croissance** : quand plusieurs années sont disponibles, chaque
  campagne annuelle (ex. automne-hiver pour la truite) est présentée dans
  son propre panneau plutôt que sur un seul axe continu — échelle de
  température partagée par espèce pour une comparaison directe. Repli
  automatique sur l'ancien rendu à une colonne si une seule campagne.
- **Indicateurs** : les corrélations à débit en abscisse sont désormais
  régressées sur log(Q) plutôt que Q brut — cohérent avec le reste de la
  méthode (PNDA, corrélation partielle Q↔T°, débits classés, tous en
  échelle log) et avec la nature en rendements décroissants du tampon
  thermique. Validé sur cas contrôlé avant application (R² 0,37→0,86 quand
  la relation est réellement logarithmique).
- **Climatique** : retour à matplotlib (l'essai Plotly n'apportait pas de
  valeur ajoutée jugée suffisante) ; axe des années forcé en entiers
  (corrige définitivement les tickmarks décimaux) ; seuils d'étiage et de
  débit estival toujours explicités en clair. Ajout d'un graphique bonus
  (précipitations annuelles vs sévérité de l'étiage).

## 3.3 — 2026-07-25
- **Impression/Word** : toutes les figures garantissent désormais une police
  ≥ 8 pt une fois collées à 16 cm (portrait) ou 24,7 cm (paysage) — plancher
  calculé automatiquement selon la largeur réelle de chaque figure
  (`print_style.py`). Tailles de figure resserrées en conséquence.
- **Tableaux** : retour à la ligne automatique dans les tableaux matplotlib
  (synthèse SGVT, sensibilité) pour ne plus tronquer une valeur trop longue.
- **Légendes** : fond semi-opaque systématique pour ne plus masquer une
  courbe ; repositionnées hors du graphique sur la figure fraie-croissance.
- **Jauge SGVT** : bande colorée élargie, aspect forcé à l'égalité (moins
  étirée verticalement).
- **Chroniques** : coupure des lacunes généralisée (QC, vulnérabilité) ;
  fenêtre d'affichage optionnelle (période fixe) sans jamais modifier les
  calculs sous-jacents.
- **Fraie-croissance** : repères de phase et légende repositionnés sans
  chevauchement (vérifié) ; export XLSX dédié (synthèse + détail par phase).
- **Indicateurs** : nouvelle figure de synthèse mensuelle/annuelle ; échelle
  log sur les deux corrélations à débit en abscisse.
- **Vulnérabilité** : libellés de l'axe des dates sur les deux panneaux
  (haut et bas), plus seulement le panneau du bas.
- **Relation Q–T°** : échelle log sur le graphique de gauche (nuage brut).
- **Climatique** : bascule intégrale vers Plotly (interactif, zoom, survol,
  export) ; axe des années en entiers propres ; seuils d'étiage et de débit
  estival explicités en clair dans les titres.
- Boutons de téléchargement PNG systématisés sur toutes les figures.

## 3.2 — 2026-07-24
- Anomalie d'air **lissée** (7 j par défaut, réglable) pour la compensation :
  la série normalisée était jusqu'ici ~8× plus bruitée que la brute, car on
  retranchait une anomalie journalière à une moyenne hebdomadaire. Moyenne et
  écart-type inchangés, seul le bruit disparaît.
- Chronique (onglet Synthèse) : affichage simultané de l'eau **brute** et
  **compensée**, avec la zone d'écart ombrée.

## 3.1 — 2026-07-24
- Correction : l'expander « Paramètres fraie » de la barre latérale lisait
  encore l'ancienne structure (KeyError `fenetre`) — il affiche désormais les
  trois phases par espèce.
- Correction : `fig_synthese` plantait sur les espèces non évaluables.
- Suppression de code devenu mort (`_rombough_check`).

## 3.0 — 2026-07-23
- Fraie en **trois phases** (pré-frai / ponte / incubation) avec seuils propres.
- Froid **bloquant** pour les pondeurs printaniers et estivaux, ralentissant
  pour la truite ; blocage restreint aux phases critiques.
- **Matrice de diagnostic** à deux entrées (problème thermique × levier débit).
- Relation Q–T° en **source unique** (contrôle par l'air lissé).
- Numéro de version affiché dans l'application.
