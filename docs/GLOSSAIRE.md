# Glossaire

*Destiné à la note remise au maître d'ouvrage. Une entrée par terme, sans formule : les définitions techniques figurent en annexe.*

**Amplitude nycthémérale**  
Écart entre la température maximale et la température minimale d'une même journée. Elle mesure la capacité du milieu à amortir le cycle jour-nuit : une eau abondante et ombragée l'amortit fortement, un filet d'eau exposé la suit presque comme l'air.

**Anomalie**  
Écart entre une valeur observée et la normale du même jour de l'année. Une anomalie d'air de +2 °C un 15 juillet signifie que ce 15 juillet a été plus chaud de 2 °C que la moyenne des 15 juillet de la période de référence.

**Autocorrélation**  
Le fait qu'une valeur ressemble à celle de la veille. Les températures en sont fortement affectées, ce qui interdit de traiter les journées comme des mesures indépendantes : les intervalles de confiance seraient trop étroits, donc trompeusement rassurants.

**Classe de validité**  
Note attribuée à chaque couple point × année selon la complétude de sa chronique estivale. A : publiable sans réserve. B : publiable avec réserve. C : non publié, la période où le maximum se produit n'ayant pas été suffisamment observée.

**Exondation**  
Situation d'une sonde qui n'est plus dans l'eau — niveau descendu, sonde déchaussée. Elle mesure alors l'air, et sa chronique décrit le temps qu'il fait plutôt que l'état du cours d'eau. Il faut la détecter pour écarter ces journées.

**Hystérésis**  
Manière de détecter un régime qui dure : on exige beaucoup pour déclencher, moins pour maintenir. Sans elle, un épisode unique se fragmente en plusieurs dès que le signal faiblit une journée — une sonde sortie de l'eau n'y retourne pas parce qu'une journée a été couverte.

**Intervalle de confiance**  
Fourchette dans laquelle la valeur vraie se situe avec une probabilité donnée, ici 95 %. Un coefficient de 0,45 avec un intervalle [0,40 ; 0,50] est bien déterminé ; le même avec [0,10 ; 0,80] ne l'est pas, et les deux s'écriraient pourtant « 0,45 ».

**Moyenne mobile**  
Moyenne calculée sur une fenêtre glissante — sept ou trente jours. Elle décrit une contrainte qui dure, là où un maximum journalier décrit un instant. Un organisme aquatique subit les deux, mais pas de la même façon.

**Normale**  
Moyenne de référence calculée sur trente années, ici 1996-2020, jour de l'année par jour de l'année. Elle définit ce qu'est une année « normale » et sert de point zéro aux anomalies. Attention : elle appartient au passé, elle ne décrit pas le climat futur.

**Point kilométrique (PK)**  
Distance d'un point de mesure à la source de son cours d'eau, en kilomètres. Il donne l'ordre amont-aval et permet de lire un profil longitudinal.

**Quantile**  
Valeur en dessous de laquelle tombe une proportion donnée des observations. Le quantile 99 d'un échantillon est dépassé par une observation sur cent. Un seuil calé sur un quantile est mesuré et non choisi — mais il hérite de l'incertitude de l'échantillon qui l'a produit.

**Sensibilité au climat (m)**  
De combien la température de l'eau varie quand celle de l'air varie de 1 °C. Un point à m = 0,20 est fortement tamponné — source, apport souterrain ; un point à m = 0,55 suit l'air de près. C'est une mesure de vulnérabilité au réchauffement, pas de température.

**Signature**  
Forme caractéristique d'un phénomène dans la donnée, indépendamment du niveau. Une sonde exondée n'est pas repérée parce qu'elle lit chaud — une canicule aussi — mais parce que son amplitude journalière rejoint celle de l'air.

**Spécificité**  
Part des journées correctement reconnues comme normales par un détecteur. Une spécificité de 99,5 % signifie qu'une journée normale sur deux cents est signalée à tort. Elle ne dit rien de ce que le détecteur manque, qui est une autre question et souvent la plus difficile.

**Écart interquartile**  
Étendue qui contient la moitié centrale des valeurs, une fois écartés le quart le plus bas et le quart le plus haut. Plus robuste que l'étendue totale, qui dépend entièrement de ses deux extrêmes.

---

## Un usage à ne pas faire

**Ne cherchez jamais une tendance temporelle dans une série normalisée.** La normalisation retranche à chaque journée l'anomalie d'air de ce jour-là. Chercher un réchauffement dans une série normalisée revient donc à chercher le signal qu'on vient d'en soustraire : on trouve zéro par construction, et l'on conclut à tort que le cours d'eau ne se réchauffe pas.

Pour une tendance, la série **brute** et elle seule. Le normalisé sert à comparer des points entre eux — c'est la seule façon de comparer des chroniques mesurées sur des années différentes — et le brut à décrire ce qui a réellement eu lieu.


---

*thermie_points 0.6 — CORRECTIFS_V4_6.md — révision étape 6.*

