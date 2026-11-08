# Journal des versions

## 4.7 — 2026-11-08
- **Aucun calcul modifié.** Les changements portent sur la lecture des
  fichiers et sur l'interface ; sur une même entrée lue de la même façon,
  les résultats sont identiques à ceux de la 4.6.
- **« cannot convert float NaN to integer ».** Une station d'air sans aucune
  température moyenne (TM) — fréquent dans les exports Météo-France, où un
  même nom de commune regroupe des postes anciens sans TM — donnait un air
  vide, et le calcul des normales s'arrêtait sur cette erreur muette. Le
  message nomme désormais la station et la colonne en cause.
- **Colonne de température d'air appliquée.** Sur un export Météo-France, la
  colonne choisie à l'écran (ex. TNTXM) était ignorée : TM était toujours
  lu. Elle est désormais appliquée ; le défaut reste TM.
- **Feuille Excel détectée.** Dans un classeur à plusieurs feuilles, la
  feuille retenue par défaut est celle qui porte le plus de lignes date +
  température, et non plus la première. Au format d'échange DCE, la
  première feuille porte les métadonnées de pose et la chronique est en
  seconde. À défaut de feuille qui se distingue, la première reste retenue.
- **Colonne « T » reconnue** comme température (format DCE), en nom entier
  seulement.
- **Plusieurs sondes, plusieurs fichiers d'air.** Au-delà d'une sonde ou
  d'un fichier d'air, un tableau de rapprochement sondes / station météo
  s'affiche : feuille, colonnes, cours d'eau et point pré-remplis par
  détection, station d'air choisie par sonde. Il s'enregistre en CSV et se
  recharge. L'analyse tourne sur toutes les sondes cochées ; l'échec de
  l'une n'arrête pas les autres et s'affiche dans la synthèse. Une
  synthèse empile la fiche de chaque sonde (CSV), et tous les rapports
  Word + Excel se téléchargent en un ZIP. Avec une seule sonde et un seul
  fichier d'air, l'interface est celle de la 4.6.
- **Tests autonomes** : `tests/test_lecture_multi.py` (fichiers fabriqués,
  sans le corpus).

## 4.6 — 2026-08-31
- **Ce qui change à la lecture.** La normalisation climatique et le
  contrôle qualité ne suivent plus les mêmes règles : sur trente-deux
  stations, deux changent de catégorie et voient leur note de synthèse se
  déplacer, et le tableau mensuel des indicateurs perd trois colonnes.
  Partout ailleurs, les catégories publiées sont inchangées.
- **Détection des sondes hors de l'eau.** L'écart fixe de 4 °C entre l'eau
  et l'air — qui supposait une station météo proche et un climat donné, et
  n'était atteint presque nulle part — cède la place à une comparaison de
  chaque station à sa propre habitude, au même mois ; un second niveau
  d'examen vérifie la forme de la journée lorsque le fichier d'air fournit
  ses températures minimale et maximale. C'est le seul correctif qui ait
  déplacé un diagnostic publié.
- **Fenêtre d'examen du détecteur portée à l'année entière.** Il ne
  regardait que juin à septembre, alors que les sondes se posent au
  printemps et qu'une sonde qui enregistre avant d'être immergée produit
  exactement la signature cherchée. Une seconde condition écarte la
  confusion avec une vague de froid : l'eau doit aussi être plus chaude que
  d'habitude à cette station et à ce mois-là. 151 journées retenues au lieu
  de 69, aucun diagnostic publié modifié.
- **La relation air–eau peut désormais être déclarée non établie.** La
  fiabilité du coefficient de correction climatique est testée ;
  insuffisante, la correction n'est pas appliquée et le document le dit —
  les valeurs décrivent l'année observée avec la météo qu'elle a eue, et ne
  sont comparables ni à une autre station ni à une autre année.
- **Écarter n'est plus effacer.** Les quatre étapes qui supprimaient des
  données sans trace — contrôle qualité, mise en correspondance de l'eau et
  de l'air, lecture du fichier de sonde, agrégation en journées —
  produisent chacune un tableau des données écartées (date, cause, valeur),
  sans que rien ne change au calcul. Une station y révèle une année 2012
  entièrement absente des résultats faute de température d'air : cent deux
  journées d'été manquantes que rien n'indiquait.
- **Les journées incomplètes sont signalées.** Une journée dont la sonde
  n'a enregistré que quelques heures est repérée — en comparant son plus
  grand trou de mesure à ce qui est habituel sur la station — puis
  signalée, sans être exclue : la décision de l'écarter appartient au
  chargé d'étude, pas à l'outil.
- **Les moyennes glissantes portent sur des jours, non sur des lignes.**
  Sur une chronique trouée, une fenêtre de sept jours pouvait couvrir six
  mois. Les trois calculs concernés — détection de sonde bloquée, lissage
  de l'eau, lissage de l'air — s'appuient désormais sur le calendrier.
- **Le lissage porte sur toute la donnée disponible.** Le lissage de la
  chronique d'eau et celui de l'anomalie de l'air ne portaient que sur la
  partie déjà filtrée de la série, où chaque valeur écartée en amont
  creusait un trou. Ils sont maintenant calculés sur la série complète,
  puis restreints — l'ordre des opérations change le résultat.
- **La normale de l'air suit le calendrier.** Elle était calculée en
  numérotant les jours depuis le 1ᵉʳ janvier ; une année bissextile décale
  ce numéro d'une unité à partir du 1ᵉʳ mars, et la normale du 15 juillet y
  était celle du 14. Près de 90 % des jours de l'année étaient concernés.
  Le calcul se fait sur le couple (mois, jour).
- **Les températures minimale et maximale de l'air ne sont plus jetées.**
  Souvent portées par le fichier météorologique en plus de la moyenne du
  jour, elles étaient supprimées à la lecture ; les conserver a permis le
  second niveau d'examen du détecteur de sondes hors d'eau.
- **Retrait d'une famille d'indicateurs redondants.** Deux corrections
  climatiques de la même température, calculées de deux façons, étaient
  publiées sous des noms voisins dans le même document ; celle qui
  n'alimentait rien en aval et n'était comparable à rien est supprimée. Le
  tableau mensuel des indicateurs passe de 11 à 8 colonnes, 777 valeurs
  cessent d'être publiées, aucun diagnostic n'en dépend.
- **Les valeurs par défaut de l'interface viennent d'une source unique.**
  Une trentaine de réglages étaient écrits en dur, en double du paramétrage
  de référence, et dix-sept coïncidaient — c'était précisément le risque :
  un doublon qui coïncide ne se voit pas, il diverge le jour où l'un des
  deux change.
- **Chaque contrôle publie son état.** Un contrôle désactivé, ou qui n'a
  pas pu s'exécuter faute de données, affichait la même chose qu'un
  contrôle n'ayant rien trouvé. Un onglet « ce qui a été vérifié » présente
  désormais chaque contrôle, ce qu'il a examiné, ce qu'il a trouvé et ce
  sur quoi il s'abstient — y compris quand il n'a rien trouvé. Le même
  texte figure dans le rapport Word et le classeur Excel.
- **Le statut de la correction climatique figure dans les livrables.** Une
  station dont le coefficient a été rejeté publiait des chiffres
  typographiquement identiques à ceux d'une station normalisée. Le rapport
  et le classeur disent maintenant si les températures sont normalisées ou
  brutes, avant les chiffres que ce statut qualifie.

## 4.5 — 2026-07-30
- **Zone intermédiaire : choix de l'espèce repère.** La zonation SANDRE
  intermédiaire admet deux espèces repères thermiques ; l'ombre commun
  (inchangé, retenu par défaut) et désormais le barbeau commun
  (*Barbus barbus*). Le choix est explicite dans la barre latérale et tracé
  jusque dans les livrables.
- **Les seuils estivaux descendent au niveau espèce.** Les seuils de stress
  chronique et de létalité, ainsi que le plancher de la classe « Faible »,
  sont des propriétés de l'espèce repère et non de la zonation : ils sont
  désormais portés par l'espèce et non plus par le contexte. Aucun
  changement de valeur pour les trois espèces déjà en place.
- **Barbeau — seuils retenus** (revue bibliographique dédiée) :
  - stress chronique **24 °C** sur Tmh_norm — borne haute de l'optimum
    adulte (Souchon & Tissot 2012, Table III) ;
  - létalité **28 °C** sur Tmax_norm — IULT 24 h de 30 °C à 20 °C
    d'acclimatation (Kraiem & Pattee 1980), minorée de la marge in situ
    recommandée par les auteurs de la synthèse ;
  - plancher de classe « Faible » **5 %** — le plancher à 3 % était fondé
    sur la sensibilité des sténothermes froides, ce que le barbeau,
    mésotherme, n'est pas ;
  - reproduction en trois phases : pré-frai avr–mai (11–17 °C, élargie
    9–20), ponte mai–juin (15–20 °C, élargie 14–25), incubation juin–juil
    (15–20 °C, élargie 13–22), froid bloquant.
  - Le seuil de déclenchement de 13,5 °C de Baras & Philippart (1999) est
    établi sur la température **minimale journalière** ; l'indicateur
    travaillant sur Tmh (moyenne mobile 7 j des moyennes journalières), il
    est converti forfaitairement à ≈ 15 °C.
- **Un seul plancher pour deux usages.** Le plancher de classe pilote
  désormais aussi la cible du volet stress de Q_thermie_bio : la classe
  affichée et le débit recherché ne peuvent plus diverger.
- **Défaut latent corrigé** : la colonne « Espèce repère » du schéma fixe de
  la feuille de synthèse lisait une clé inexistante et renvoyait
  systématiquement « — ». Elle est désormais renseignée. Le schéma reste
  invariant (aucune colonne ajoutée ou retirée).

## 4.4 — 2026-08-03
- **Revue de conformité** de l'ensemble des demandes accumulées depuis le
  début du chantier de mise en forme : 40 points vérifiés un à un dans le
  code livré (et non de mémoire), tous conformes — mise en forme des
  figures, tableaux, légendes, jauge SGVT, lacunes, période d'affichage,
  fraie par campagne, échelles log, volet climatique, livrables docx/xlsx,
  réglages de la barre latérale, gestion du débit désinfluencé.
- **Défaut latent corrigé** : au-delà de 10 années de chronique, deux
  années prenaient silencieusement la même couleur sur les figures
  fraie-croissance et vulnérabilité (palette tab10 cyclique). La palette
  est conservée — sa séparation visuelle (distance RGB minimale ≈ 0,27)
  est nettement supérieure à celle d'une palette de 20 teintes (≈ 0,10),
  et le cas courant reste 2 à 4 années — mais la limite est désormais
  signalée explicitement sur la figure, avec le détail des années
  concernées (ex. « 2010/2020 · 2011/2021 »), au lieu d'un piège de
  lecture invisible.

## 4.3 — 2026-08-02
- **Refonte de la gestion du débit désinfluencé** (donnée rare à valoriser
  pleinement, sans compromettre la robustesse de l'analyse) :
  - **Suppression de la bascule d'analyse.** La recherche du seuil
    biologique (Q*_vuln) et le test de causalité débit↔température se font
    désormais toujours sur l'influencé — l'eau réellement présente, seule
    variable causalement reliée à la température observée. Le
    désinfluencé, reconstruction hypothétique, ne sert plus de base
    d'analyse conditionnelle.
  - **Restitution systématique.** Dès que le désinfluencé est fourni, son
    PNDA et sa courbe de débits classés sont toujours calculés et affichés
    à côté de ceux de l'influencé — plus jamais conditionnés à un seuil de
    proximité entre les deux séries. Une forte divergence est elle-même
    une information (intensité de la pression anthropique), pas une raison
    d'écarter la donnée.
  - **Deux écarts médians, sans arbitrage** : annuel et juin-septembre,
    tous deux calculés et restitués. L'écart annuel seul peut masquer une
    divergence estivale majeure — vérifié sur cas test (2,9 % annuel
    contre 1027 % en JJAS pour un prélèvement concentré en été).
  - Le comblement des trous du désinfluencé par l'influencé reste
    conditionné à un seuil (inchangé dans son principe), mais retenu
    seulement si le pire des deux écarts (annuel, JJAS) passe le test.
  - L'écart JJAS rejoint la fiche de synthèse à schéma fixe (43 colonnes)
    comme indicateur comparable entre stations ; le bandeau de l'app
    l'affiche en évidence quand le désinfluencé est disponible.
  - Messages d'avertissement robustes aux cas limites (jours communs
    insuffisants en JJAS et/ou à l'année).

## 4.2 — 2026-08-01
- **Outil rendu générique** : dernières mentions d'un contexte d'étude
  particulier retirées — titre de page, en-tête principal de l'app, texte
  de la matrice de diagnostic et de ses conduites à tenir (cas « approche
  peu opérante »). Plus aucune référence dans le code ni les livrables.
- **Barre latérale réorganisée** :
  - Section 1 (Données) : les deux téléchargements de débit (influencé,
    désinfluencé) remontent juste après eau/air, visibles d'emblée qu'ils
    soient utilisés ou non (un message signale s'ils seront ignorés en
    mode « thermie seule »).
  - Section 2 (Contexte & mode) : accueille désormais le calcul des
    normales (déplacé depuis la section 1) et le volet climatique
    (renommé, la mention « bonus » retirée). Le seuil de comblement
    désinfluencé devient optionnel — une case à cocher (décochée par
    défaut) donne accès au réglage fin ; sans cocher, la valeur par défaut
    (10 %) s'applique silencieusement.
  - Section 3 (Métadonnées) : ajout du nom de la station Météo-France de
    référence, propagé dans le récapitulatif des sources, la fiche de
    synthèse à schéma fixe (39 colonnes désormais) et les deux livrables.
- **Contrôle qualité** : « Exclure la saison JJAS entière » décochée par
  défaut ; seuil d'écart hors d'eau porté à 10 °C par défaut (plafond du
  curseur relevé de 10 à 15 °C).

## 4.1 — 2026-07-31
- **Rapport Word générique** : retrait de la mention HMUC/Moselle sur la
  page de garde et de tous les renvois à la note méthodologique — le
  document ne présuppose plus un contexte d'étude particulier.
- **Axe des dates adaptatif** (chronique thermique et contrôle qualité) :
  l'intervalle entre repères s'ajuste à l'étendue réelle de la période
  (mensuel en-deçà de 400 j, trimestriel jusqu'à 900 j, semestriel jusqu'à
  ~6 ans, annuel au-delà) — corrige le chevauchement de dizaines
  d'étiquettes observé sur les chroniques pluriannuelles.
- **§1.5** : ajout d'une phrase d'intérêt de la normalisation climatique —
  rendre les stations et les années comparables malgré des contextes et
  des périodes d'enregistrement hétérogènes.
- **Corrélations indicateurs scindées** : les 2 corrélations sans débit
  (amplitude et écart eau-air vs température de l'eau) rejoignent le §2.2,
  toujours produites même sans hydrométrie ; les 2 avec débit restent au
  §4.3, désormais générées indépendamment plutôt que par découpage d'une
  figure à 4 panneaux.
- **Chapitre de synthèse** : nouveau bloc « Débit de référence retenu » en
  ouverture — Q_thermie_bio en priorité (résultat principal), repli
  explicite et commenté sur Q_thermie_fonc si non déterminé, PNDA
  désinfluencé présenté avant l'influencé. Repris dans la fiche station du
  classeur Excel. Testé sur les deux branches (bio déterminé / repli fonc).

## 4.0 — 2026-07-30
- **Livrables station « prêts à copier »** — nouveau module `livrables.py` :
  - **Rapport Word** organisé en chapitres séparés par des sauts de page,
    axé résultats (les rappels méthodologiques sont réduits à de courts
    renvois à la note méthodologique Point 2) : 1. Données mobilisées et
    qualité — avec un encadré dédié à la **validité du modèle air–eau**,
    fondement de toute la normalisation ; 2. Vulnérabilité thermique
    estivale ; 3. Vulnérabilité de la reproduction ; 4. Relation
    débit–température, diagnostic de validité de la démarche et débits de
    référence ; 5. Synthèse (SGVT, conclusion, réserves, fiche de synthèse).
    Les chapitres sans objet sont omis.
  - **Classeur Excel** en onglets miroirs du rapport.
- **`redaction.py`** — source unique des textes d'interprétation (verdicts,
  robustesse, conclusions, réserves), consommée à la fois par l'application
  et par les livrables : le rapport dit nécessairement la même chose que ce
  que l'utilisateur a lu à l'écran, et une correction de formulation se
  propage partout.
- **Fiche de synthèse à schéma fixe** (38 colonnes invariantes) : une
  station sans débit produit exactement les mêmes colonnes qu'une station
  complète, renseignées « non applicable ». Vérifié sur 4 configurations et
  3 stations réelles : les lignes s'empilent directement dans un tableau de
  comparaison inter-sites, sans aucune valeur manquante ni retraitement.
- **SGVT déplacé au chapitre de synthèse** : il agrège quatre composantes
  dont la dernière (fraie) n'est établie qu'au chapitre 3 ; le présenter
  une fois toutes ses composantes connues supprime une référence en avant.
- Nouvelle dépendance : `python-docx`.

## 3.7 — 2026-07-29
- **Clim1** : remplace l'écart aux normales par la température de l'air
  annuelle moyenne, dans le même style visuel que les précipitations
  (barres colorées au-dessus/en-dessous de la moyenne, ligne de moyenne).
- **Clim2** (renommé "Répartition annuelle des régimes de débit") :
  remplace le comptage des jours sous 2 seuils par une barre empilée
  couvrant la totalité de l'année (vérifié : 365-366 jours par barre),
  répartie en 6 classes de régime — de la crue (> 2× médiane) à l'étiage
  critique (< 15 % médiane) — sur un dégradé de couleur continu
  bleu foncé → rouge foncé.
- **Clim3** (débit moyen estival) : ajout d'une seconde ligne de repère —
  la médiane estivale — en plus du seuil d'étiage déjà présent.
- **Clim6** (précipitations × stress thermique) : contraste des tailles de
  bulles nettement accru (normalisation min-max sur la plage observée,
  ratio ~12× entre plus petite et plus grande bulle contre ~2× avant) ;
  axe Y basé sur le stress thermique chronique (seuil du contexte
  piscicole) plutôt que la létalité aiguë, plus discriminant d'une année
  sur l'autre ; suppression de la droite de tendance et de la mention
  « bonus ».

## 3.6 — 2026-07-28
- **Correctif tableau de synthèse** : les lignes de titre de section
  (SENSIBILITÉ, VULNÉRABILITÉ...) produisaient un remplissage triangulaire
  défectueux — bug de rendu de `Cell.visible_edges` sous cette version de
  matplotlib, vérifié par scan pixel (la couleur se réduisait
  progressivement du haut vers le bas de la ligne). Remplacé par une
  bordure peinte de la même couleur que le fond ; fusion visuelle propre
  vérifiée sur les 4 lignes de section (fond et bordure uniformes).
- **Chronique thermique** : légende déplacée sous le graphique.
- **Fraie-croissance** : figure aérée (hauteur +11 %, plus d'espace entre
  le sous-titre gris et les intitulés de phase, plus d'espace entre l'axe
  des dates et la légende). Le filtrage par période s'applique désormais
  correctement (il ne l'était pas — la figure utilisait encore la version
  figée du dernier calcul, comme corrigé précédemment pour Vulnérabilité).
- **Relation Q–T°** : étiquettes mineures de l'axe log masquées
  (NullFormatter) — supprime le chevauchement des libellés type « 2×10⁰ ».
- **Climatique** : diagnostic explicite (console + app) quand le graphique
  bonus précipitations × canicule ne peut pas être produit, précisant
  laquelle des conditions (précipitations, débit, couverture ≥ 350 j/an,
  4 années minimum) n'est pas réunie.

## 3.5 — 2026-07-27
- **SGVT** : la jauge et le tableau de synthèse sont désormais deux figures
  autonomes (`fig_synthese_tableau` / `fig_synthese_jauge`) — la jauge
  dispose de bien plus de place et ne chevauche plus aucun texte ; le
  tableau, libéré de la contrainte de largeur partagée, gagne en lisibilité.
- **Tableau de synthèse** : les lignes de titre de section (SENSIBILITÉ,
  VULNÉRABILITÉ ESTIVALE, FRAIE-CROISSANCE, SCORE GLOBAL) sont fusionnées
  visuellement sur toute la largeur du tableau (bordures internes masquées)
  au lieu d'être cantonnées à la première colonne, ce qui forçait un retour
  à la ligne serré et peu lisible.
- **Fraie-croissance** : remplacement de la grille de panneaux par
  campagne (qui pouvait chevaucher ses titres avec de nombreuses années)
  par une **superposition sur un seul axe**, une couleur par année. Un
  calendrier saisonnier synthétique gère correctement les fenêtres à cheval
  sur le nouvel an (truite, octobre-mars).
- **Vulnérabilité (juin-septembre)** : même principe de superposition par
  année, avec la **même palette de couleurs** que la figure fraie-croissance
  (une année = une couleur, cohérente entre les deux onglets).
- **Climatique** : graphique bonus revu — précipitations annuelles en
  abscisse (années à couverture complète uniquement), jours de canicule
  aquatique (T_eau_max > seuil létal) en ordonnée, taille des bulles
  proportionnelle aux jours d'étiage de l'année (annoté sous chaque point).

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
