# THERMIE BIO — bilan de la version 4.6

*Document destiné au maître d'ouvrage. Il ne suppose aucune connaissance du
code ni du déroulement des travaux.*

---

## A — Ce que l'outil faisait, ce qu'il fait

L'outil évalue la **vulnérabilité thermique** d'un cours d'eau pour le poisson.
Il croise une chronique de température d'eau, mesurée par une sonde posée dans
la rivière, avec la température de l'air d'une station météorologique voisine et,
quand elle existe, une chronique de débit. Il en tire un diagnostic : combien de
journées dépassent les seuils biologiques de l'espèce repère, comment se passe
la période de reproduction, et une note de synthèse allant du risque faible au
risque élevé.

**Ce qu'il faisait de travers, et que la version 4.6 corrige, tient en trois
familles.**

*Il prenait pour de l'eau chaude ce qui était de l'air.* Une sonde peut se
retrouver hors de l'eau — étiage qui découvre le lit, crue qui déplace le
support, pose ou dépose de l'appareil. Elle continue d'enregistrer, mais elle
mesure l'air. Ces journées gonflaient le compte des journées dangereuses. La
version antérieure disposait d'un test, mais il reposait sur un écart fixe de
4 °C entre l'eau et l'air, valeur qui suppose une station météo proche et un
climat donné ; sur ce corpus, il ne trouvait presque rien.

*Il jetait des données sans le dire.* Plusieurs étapes du traitement écartaient
silencieusement des mesures — une ligne illisible, une journée sans température
d'air, une valeur hors bornes. Rien n'en gardait trace. Un utilisateur ne
pouvait pas savoir si un résultat portait sur toute la chronique ou sur la
moitié.

*Il calculait des moyennes glissantes sur des lignes, non sur des jours.* Une
« moyenne sur sept jours » comptait sept enregistrements successifs. Quand la
chronique avait un trou de six mois, elle mélangeait deux saisons sans que rien
ne l'indique.

**Ce qu'il fait aujourd'hui.** Chaque station est comparée à elle-même : aucune
valeur venue d'un autre cours d'eau n'entre dans une règle. Chaque contrôle dit
ce qu'il a examiné, ce qu'il a trouvé, et ce sur quoi il ne se prononce pas — y
compris quand il n'a rien trouvé, car « rien à signaler » et « je n'ai pas pu
regarder » ne doivent pas se ressembler à l'écran. Chaque donnée écartée est
nommée, datée et motivée, dans un tableau consultable. Et lorsque la relation
entre l'air et l'eau ne peut pas être établie sur une chronique, l'outil le dit
au lieu de publier des résultats qui en dépendent.

---

## B — Les treize correctifs

*Ordonnés par ce qu'ils changent pour le lecteur, non par ordre de réalisation.*

### 1. La détection des sondes hors de l'eau

Le test précédent déclarait une sonde émergée si l'eau dépassait l'air de plus
de 4 °C. Ce seuil suppose une station météo proche et un climat comparable à
celui pour lequel il avait été choisi ; il n'a été atteint presque nulle part
sur ce corpus. Le nouveau test compare **chaque station à sa propre habitude, au
même mois** : est-ce que l'écart entre l'eau et l'air, aujourd'hui, sort de ce
que cette station montre ordinairement à cette période ? Un second niveau
d'examen s'ajoute lorsque le fichier d'air fournit les températures minimale et
maximale du jour, et vérifie la *forme* de la journée et non seulement son
niveau.

**Ce qu'il a déplacé :** c'est le seul correctif qui ait changé un diagnostic
publié. Deux stations sur trente-deux ont changé de catégorie — le détail est en
section C.

### 2. La fenêtre d'examen de ce détecteur, et la question « eau ou air ? »

Le détecteur ne regardait que de juin à septembre. Or les sondes se posent au
printemps, et une sonde qui enregistre avant d'être immergée produit exactement
la signature qu'on cherche. Sur trois stations de trois bassins différents, les
chroniques commencent le même jour de mai et les premières semaines sont
manifestement enregistrées hors de l'eau — deux d'entre elles suivent la même
courbe à moins d'un dixième de degré pendant trois semaines, ce que deux
rivières distinctes ne font jamais.

L'examen a donc été étendu à l'année entière. Mais un écart entre l'eau et l'air
grandit aussi bien quand l'eau monte que quand l'air descend, et une vague de
froid produisait la même signature qu'une sonde émergée : en février 2012, sept
sondes d'un même bassin auraient été déclarées hors de l'eau le même jour, avec
un air à −17 °C. Une seconde condition a donc été ajoutée : **l'eau doit aussi
être plus chaude que d'habitude à cette station et à ce mois-là**. Aucune valeur
n'y est calibrée — la frontière est la médiane de la station elle-même.

**Ce qu'il a déplacé :** le détecteur retient aujourd'hui 151 journées au lieu
de 69, avec une meilleure précision. **Aucun diagnostic publié n'en est
modifié**, les journées concernées tombant en dehors de la période d'été sur
laquelle se calculent les indicateurs.

### 3. Quand la relation air–eau ne peut pas être établie

L'outil corrige les températures observées de l'écart climatique de l'année, afin
que deux stations, ou deux années, soient comparables. Cette correction repose
sur un coefficient estimé statistiquement. Sur certaines chroniques, cette
estimation n'est pas fiable — trop peu de données, ou une relation trop bruitée.
Auparavant, le coefficient était utilisé quand même, et les résultats
s'imprimaient exactement comme ceux d'une station bien caractérisée.

Désormais, la fiabilité du coefficient est testée ; lorsqu'elle est insuffisante,
la correction n'est pas appliquée et **le document le dit** : les valeurs
décrivent l'année observée avec la météo qu'elle a eue, et ne sont comparables ni
à une autre station ni à une autre année.

### 4. Écarter n'est plus effacer

Quatre étapes du traitement supprimaient des données sans laisser de trace : le
contrôle qualité, la mise en correspondance de l'eau et de l'air, la lecture du
fichier de sonde, et l'agrégation en journées. Chacune produit désormais un
**tableau des données écartées** — la date, la cause, et la valeur concernée —
sans que rien ne change au calcul lui-même. Sur une station, on découvre ainsi
que l'année 2012 tout entière était absente des résultats, faute de température
d'air : cent deux journées d'été manquantes, que rien n'indiquait.

### 5. Les journées incomplètes sont signalées

Une journée dont la sonde n'a enregistré que quelques heures produit une moyenne
qui n'a pas le même sens qu'une journée complète. Ces journées sont maintenant
repérées — en comparant le plus grand trou de mesure de la journée à ce qui est
habituel sur cette station — et signalées, sans être exclues : la décision de
les écarter appartient au chargé d'étude, pas à l'outil.

### 6. Les moyennes glissantes portent sur des jours

Toutes les moyennes et écarts-types glissants comptaient un nombre de *lignes*
et non un nombre de *jours*. Sur une chronique continue, cela revient au même ;
sur une chronique trouée, une fenêtre de sept jours pouvait couvrir six mois.
Trois calculs étaient concernés — la détection de sonde bloquée, le lissage de
l'eau et celui de l'air. Ils s'appuient désormais sur le calendrier.

### 7. Le lissage porte sur toute la donnée disponible

Le lissage de la chronique d'eau, et celui de l'anomalie de l'air, ne portaient
que sur la partie déjà filtrée de la série. Une valeur écartée en amont creusait
donc un trou dans la moyenne glissante. Les deux lissages sont maintenant
calculés sur la série complète, puis restreints — l'ordre des opérations, ici,
change le résultat.

### 8. La normale de l'air suit le calendrier

La température « normale » d'un jour de l'année était calculée en numérotant les
jours depuis le 1ᵉʳ janvier. Une année bissextile décale ce numéro d'une unité à
partir du 1ᵉʳ mars : la normale du 15 juillet d'une année bissextile était celle
du 14 juillet des autres. Près de 90 % des jours de l'année étaient concernés.
Le calcul se fait maintenant sur le couple (mois, jour).

### 9. Les températures minimale et maximale de l'air ne sont plus jetées

Le fichier météorologique porte souvent, en plus de la moyenne du jour, ses
extrêmes. Ils étaient supprimés à la lecture. Les conserver a permis le second
niveau d'examen du détecteur de sondes hors d'eau.

### 10. Une famille d'indicateurs redondants a été retirée

L'outil publiait deux corrections climatiques différentes de la même
température, calculées de deux façons, sous deux noms voisins, dans le même
document. Après vérification, l'une n'était utilisée nulle part en aval et
n'était comparable à rien. Elle a été supprimée : **777 valeurs cessent d'être
publiées, aucun diagnostic n'en dépend**.

### 11. Les valeurs par défaut de l'interface

Une trentaine de réglages proposés par l'interface étaient écrits en dur, en
double du paramétrage de référence. Dix-sept coïncidaient — et c'était le
risque : un doublon qui coïncide ne se voit pas, il diverge le jour où l'un des
deux change. Ils sont désormais dérivés d'une source unique.

### 12. Chaque contrôle publie son état

Un contrôle qu'on a désactivé, ou qui n'a pas pu s'exécuter faute de données,
affichait la même chose qu'un contrôle qui n'avait rien trouvé. Un onglet
« ce qui a été vérifié » présente désormais chaque contrôle, ce qu'il a examiné,
ce qu'il a trouvé et ce sur quoi il s'abstient — **y compris quand il n'a rien
trouvé**. Ce texte figure aussi dans le rapport Word et le classeur Excel.

### 13. Le statut de la correction climatique dans les livrables

Les documents remis ne disaient pas si les températures publiées étaient
corrigées du climat ou brutes. Une station dont le coefficient a été rejeté
publiait des chiffres typographiquement identiques à ceux d'une station
normalisée. Le statut figure désormais dans le rapport et dans le classeur,
**avant** les chiffres qu'il qualifie.

---

## C — Le bilan des verdicts

**Sur trente-deux stations et treize correctifs, deux stations ont changé de
catégorie, et rien d'autre n'a bougé.** Les deux mouvements viennent du même
correctif — la détection des sondes hors de l'eau.

### La Plaine à Raon-sur-Plaine — trois catégories sur trois

| indicateur | avant | après |
|---|---|---|
| journées de létalité | **10** | **2** |
| catégorie | vulnérabilité aiguë **sévère** | vulnérabilité aiguë **ponctuelle** |
| stress chronique | 3,15 % — **modéré** | 0,47 % — **faible** |
| note de synthèse | 2,33 / 10 — **Risque Modéré** | 1,50 / 10 — **Risque Faible (zone refuge)** |

**Huit des dix journées de vulnérabilité aiguë sévère de cette station étaient la
sonde hors de l'eau.** Ce sont les 5, 6, 8, 11, 12 et 14 juin 2011, et les 21 et
23 juin 2012.

La démonstration ne repose pas sur le seul détecteur. Du 20 mai au 14 juin 2011,
cette sonde affiche une eau entre 20 et 25 °C sans discontinuer, avec un
**minimum nocturne jamais descendu sous 18,2 °C**, alors que les nuits
descendaient à 5 °C et que la rivière coulait à **plus du double de son débit
médian d'été**. Puis, le 15 juin, la lecture chute de 22,3 à 12,9 °C en deux
jours *pendant que l'air monte*, et retrouve exactement le régime des autres
années. Les trois autres mois de juin de cette station affichent 11 à 13 °C de
moyenne. Une rivière vosgienne de tête de bassin qui coule à 2,8 m³/s ne porte
pas une eau à 22 °C quand l'air descend à 5 °C la nuit.

*Cette station était publiée « Risque Modéré » avec dix journées de
vulnérabilité aiguë sévère. Huit de ces dix journées étaient la sonde hors de
l'eau.*

### La Canner à Vigy — une catégorie

| indicateur | avant | après |
|---|---|---|
| journées de létalité | **1** | **0** |
| catégorie | vulnérabilité aiguë **ponctuelle** | **absence** de vulnérabilité aiguë |
| note de synthèse | 3,17 / 10 | 2,50 / 10 — Risque Modéré *(inchangé)* |

La journée en cause est le 1ᵉʳ juin 2021, seuil de létalité 30 °C. Elle
appartient à un bloc de vingt-quatre journées enregistrées avant que la sonde ne
soit posée : sur cette période, la chronique de cette station et celle d'un
ruisseau d'un autre bassin sont identiques à moins d'un dixième de degré.

### Les autres mouvements, sans changement de catégorie

Deux stations voient leur compte de journées de létalité bouger sans changer de
catégorie : l'une passe de 6 à 5, l'autre de 29 à 33 — c'est la seule station où
la vulnérabilité **augmente**, le détecteur y écartant des journées que
l'ancienne version laissait passer, ce qui refroidit le coefficient de correction
et relève les températures corrigées des autres journées.

Pour toutes les autres stations, **les catégories publiées sont inchangées**. Les
treize correctifs ont modifié des valeurs — des effectifs, des pourcentages au
centième — sans franchir aucune borne de classe.

---

## D — Les journées où la sonde n'était pas dans l'eau

*Ce paragraphe répond à la question la plus fréquente sur ce type de correction,
et il est reproduit tel qu'il a été rédigé au cours des travaux.*

> Une sonde thermique posée en rivière peut se retrouver à l'air libre : étiage
> qui découvre le lit, sonde décalée par une crue, support qui bouge. Elle
> continue d'enregistrer, mais elle mesure autre chose que la rivière — et les
> valeurs obtenues, souvent élevées, viennent gonfler le nombre de journées
> réputées dangereuses pour le poisson.
>
> L'outil repère ces journées et les retire de l'analyse. Il ne les repère pas
> parce que l'eau y est chaude : une canicule réchauffe l'eau et l'air ensemble,
> et ces journées-là sont conservées, car elles sont vraies. Il les repère parce
> que l'eau **cesse de suivre l'air comme elle le fait d'habitude à cette
> station**. Chaque station est comparée à elle-même : aucun seuil venu d'un
> autre cours d'eau n'est appliqué.
>
> Ce choix a une contrepartie qu'il faut connaître. Une rivière réduite à
> quelques flaques se découplerait elle aussi de l'air — et ce serait alors une
> vraie journée critique. Retirer une telle journée reviendrait à effacer une
> alerte réelle. Nous avons donc vérifié, une par une, toutes les journées
> retirées qui franchissaient un seuil biologique, c'est-à-dire toutes celles
> dont le retrait change quelque chose au diagnostic.
>
> Nous les avons confrontées à l'histoire thermique propre de leur station :
> une journée est tenue pour artefact si elle est à la fois plus chaude que tout
> ce que cette station a jamais montré à la même période de l'année, et plus
> détachée de l'air que dans 95 % de ses années passées. Sur le point le plus
> touché, la sonde affichait pendant trois semaines une eau à 20–25 °C, avec des
> minimums nocturnes jamais descendus sous 18 °C, alors que les nuits
> descendaient à 5 °C et que la rivière coulait à plus du double de son débit
> habituel de saison. Les trois autres années, la même station lisait 11 à 13 °C
> à la même période. La sonde n'était pas dans la rivière.
>
> **Ce que cette vérification ne peut pas faire.** Aucune série de températures,
> de débits ou de mesures d'air ne permet d'établir avec certitude qu'une sonde
> était hors de l'eau. Nous raisonnons par recoupement, et le recoupement laisse
> une part de journées sur lesquelles nous ne nous prononçons pas. Trois éléments
> lèveraient le doute, et aucun ne figure dans les données dont nous disposons :
> une **photographie ou une fiche de tournée datée**, une **lecture de hauteur
> d'eau au droit de la sonde** — le débit mesuré à la station dit où est la
> rivière, pas où est la sonde —, et une **seconde sonde au même point, calée à
> une autre hauteur** : deux sondes qui divergent désignent l'artefact, une seule
> ne le peut jamais.
>
> **Recommandation pratique.** Sur les stations où le diagnostic bascule d'une
> classe de risque à l'autre selon que ces journées sont retirées ou non, une
> visite de terrain avec relevé de la hauteur d'eau et photographie du point de
> pose vaut mieux que tout raffinement de calcul.

---

## E — Les limites

*Elles ne sont pas adoucies. Chacune est mesurée, non supposée.*

### Deux journées de La Plaine sont encore publiées à tort, très probablement

Les 2, 3 et 4 juin 2011 appartiennent au même bloc que les huit journées
retirées : l'eau y est à 24–25 °C début juin, sur une station dont les trois
autres mois de juin plafonnent à 12–13 °C. Le détecteur ne les voit pas, et la
raison est mécanique : **l'air était chaud ces jours-là** — 17 à 20 °C contre 10
à 15 °C le reste du bloc. L'écart entre l'eau et l'air s'en trouve réduit, il
passe sous le seuil, et la journée n'est pas marquée.

**Deux de ces trois journées sont aujourd'hui comptées comme journées de
vulnérabilité aiguë sur cette station.** Les corriger supposerait de transformer
en détecteur l'outil de vérification qui les a identifiées, ce qui demande son
propre cycle de validation. Le choix a été de le signaler plutôt que de
l'improviser.

### Un indicateur qui ne bouge pas parce qu'il est saturé n'est pas un indicateur non affecté

Sur La Canner à Vigy, le retrait de vingt journées enregistrées hors de l'eau
pendant la période de reproduction déplace le coefficient de correction de 39 %.
Le score de reproduction, lui, ne bouge pas : **il était déjà à son maximum**.
Sur une station moins dégradée, les mêmes vingt journées auraient pesé sur le
résultat publié.

### L'artefact contamine sa propre référence

Le détecteur compare chaque journée à l'habitude de sa station au même mois. Sur
une chronique de trois années, un bloc d'artefact de trois semaines représente un
quart des journées de ce mois : il tire l'habitude vers lui et se rend
lui-même moins visible. Ce mécanisme est mesuré et connu ; le corriger
demanderait une méthode d'estimation différente, hors du périmètre de ces
travaux.

### Trois indicateurs restent en dehors de la chaîne corrigée

- **La moyenne mobile de trente jours** est calculée hors de la chaîne
  principale et porte encore les deux défauts corrigés ailleurs — support en
  lignes plutôt qu'en jours. Elle est publiée dans le classeur et sert de repère
  visuel sur une figure.
- **L'amplitude jour-nuit** est calculée sur des journées éventuellement
  trouées, sans que le nombre de mesures effectivement disponibles n'entre dans
  le calcul.
- **La reconnaissance de la colonne d'heure** échoue sur un format de fichier
  présent dans le corpus : sur cette station, toutes les mesures sont datées à
  minuit. Les moyennes journalières restent justes, mais toute grandeur qui
  dépend de l'heure — amplitude, extrêmes horodatés — perd son sens.

### Cinq comportements que le corpus ne met pas à l'épreuve

Le jeu de données disponible n'exerce pas cinq branches du programme : le débit
désinfluencé, les normales fournies en fichier plutôt que calculées, l'export
d'air multi-stations, le garde-fou de dispersion nulle, et une variante de
lecture des écarts à la normale. **Elles n'ont donc pas pu être vérifiées.** Ce
n'est pas un défaut constaté ; c'est un défaut possible non exclu.

### Une station ne produit aucun résultat

`BIE35-5__NA` ne fournit aucun diagnostic, et la raison est simple : sa
chronique va du 10 décembre 2010 au 24 mai 2012 et **ne contient aucun jour de
juin à septembre**. Sans été, il n'y a ni relation air–eau à estimer, ni
vulnérabilité estivale à calculer. Le comportement est correct ; il fallait le
dire plutôt que le laisser passer pour une panne.

---

## F — Ce qu'il faudrait pour lever les doutes restants

Aucune série de mesures — température, débit, air — ne permet d'établir avec
certitude qu'une sonde était hors de l'eau. Trois éléments le permettraient, et
aucun ne figure dans les données dont nous disposons :

1. **Une fiche de tournée datée, ou une photographie du point de pose.** C'est
   la seule pièce qui tranche directement, et elle tranche définitivement.
2. **Une lecture de hauteur d'eau au droit de la sonde**, ou la cote de calage
   de l'appareil rapportée au niveau. Le débit mesuré à la station
   hydrométrique ne la remplace pas : *il dit où est la rivière, pas où est la
   sonde.*
3. **Une seconde sonde au même point, calée à une autre hauteur.** Deux sondes
   qui divergent désignent l'artefact ; une seule ne le peut jamais.

Pour les campagnes à venir, deux pratiques suffiraient à supprimer l'essentiel
du doute : **noter la date de pose et de dépose de chaque sonde** — les blocs
d'enregistrement hors de l'eau les plus nets de ce corpus sont des périodes
antérieures à l'immersion —, et **relever la hauteur d'eau au droit de la sonde
à chaque visite**.

**Recommandation immédiate.** Sur les stations où le diagnostic bascule d'une
classe de risque à l'autre selon que les journées suspectes sont retirées ou
non — deux stations sur trente-deux dans ce corpus —, une visite de terrain avec
relevé de hauteur d'eau et photographie du point de pose vaut mieux que tout
raffinement de calcul.
