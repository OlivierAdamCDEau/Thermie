# Ce qui est transmis au chantier suivant

*Chaque point porte sa référence dans le code, la mesure déjà faite, et la
décision qui reste à prendre. L'objet de ce document est qu'un chantier
ultérieur commence avec des chiffres, non avec une intuition.*

Les travaux de la V4.6 se sont interdit d'ouvrir un correctif nouveau après
l'étape 17 : tout ce qui a été trouvé ensuite est ici, mesuré et non corrigé.

---

## 1. La cécité du détecteur quand l'air monte

**Où** — `app/thermie_debits/qc.py:340` (`e_moy = T_eau_max − T_air`), et la
conjonction en `qc.py:388-402`.

**Le mécanisme.** Le détecteur de sonde hors d'eau mesure l'écart entre l'eau et
l'air, relativisé à l'habitude de la station au même mois. Quand l'air est
anormalement **chaud**, cet écart se referme sur l'artefact et la journée n'est
pas marquée. Le second membre posé au correctif 13 traite le cas symétrique —
l'air anormalement froid — et ne touche pas celui-ci.

**Ce qui est mesuré.** Trois journées identifiées au jour près, sur une station :
**La Plaine à Raon-sur-Plaine, les 2, 3 et 4 juin 2011.**

| date | `T_eau_max` | `T_air` | écart | marquée |
|---|---:|---:|---:|---|
| 2011-06-02 | 22,56 | 17,4 | 5,16 | non |
| 2011-06-03 | 24,53 | 19,2 | 5,33 | non |
| 2011-06-04 | 25,31 | 20,2 | 5,11 | non |
| *les journées marquées du même bloc* | | *10 à 15 °C* | *5,9 à 9,6* | *oui* |

Ces trois journées appartiennent au bloc artefactuel du 18 mai au 14 juin 2011.
Après le correctif 13, ce sont les **trois seules** journées que le témoin
indépendant signale encore sur cette station, contre seize avant.

**Ce que cela coûte aujourd'hui.** Deux d'entre elles — les 3 et 4 juin — sont
publiées comme journées de vulnérabilité aiguë sur cette station.

**Ce qu'il faudrait décider.** Promouvoir en détecteur le témoin de vérification
qui les a identifiées — le point comparé à lui-même, à la même date des autres
années — ou non. Ce témoin existe, il est spécifié et scellé
(`tests/reference/temoin_regime.py`), et sa spécificité a été établie sur
9 625 journées de contrôle : il sonne sur 0,135 % d'entre elles. Mais un témoin
de vérification et un détecteur n'ont pas le même régime de preuve, et le
promouvoir demande son propre cycle de validation.

---

## 2. La moyenne mobile de trente jours, hors de la chaîne corrigée

**Où** — `app/thermie_debits/indicateurs.py:137` (`_tmm30j`).

**Le défaut.** `Tmm30j` porte les **deux** défauts corrigés partout ailleurs : sa
fenêtre compte des lignes et non des jours (corrigé au correctif 2 dans la chaîne
principale), et elle s'appuie sur un index positionnel. Sur une chronique trouée,
« trente jours » peut couvrir plusieurs mois.

**Ce qui est mesuré.** L'indicateur est **publié** : dans le classeur Excel, et
comme repère horizontal sur une figure. Son pendant « compensé » a été supprimé
au correctif 10 (voie B) ; `Tmm30j brut` subsiste.

**Ce qu'il faudrait décider.** Soit le corriger comme les autres moyennes
glissantes, soit le déclarer explicitement hors chaîne dans le livrable. La note
qui le signale est aujourd'hui **affichée à l'écran** ; elle ne l'est pas dans le
classeur.

---

## 3. La colonne d'heure reconnue par préfixe

**Où** — `app/thermie_debits/io_data.py:79-82`.

**Le défaut.** La colonne d'heure est identifiée par un `startswith`, la colonne
de date par inclusion. Le format `chmes_heure` n'est pas reconnu.

**Ce qui est mesuré.** Sur `BLE3-0` : **2 952 mesures toutes datées à minuit**,
d'où 2 828 horodatages en double. Les agrégats journaliers restent justes — le
regroupement par date fonctionne — mais **toute grandeur dépendant de l'heure
perd son sens** : amplitude jour-nuit, extrêmes horodatés, et le second niveau du
détecteur de sonde hors d'eau, qui ne peut alors pas se prononcer.

**Ce qu'il faudrait décider.** Élargir la reconnaissance des noms de colonnes, ou
la rendre explicite dans l'interface. Le second choix est plus sûr : un
`startswith` élargi échouera sur le format suivant.

---

## 4. L'amplitude jour-nuit calculée sur des journées trouées

**Où** — `app/thermie_debits/indicateurs.py:37` (`_amplitude_journaliere`).

**Le défaut.** L'amplitude nycthémérale est calculée sur les mesures disponibles
d'une journée, sans que le critère de complétude posé au correctif 12 lui soit
appliqué. Une journée dont la sonde n'a enregistré que six heures produit une
amplitude qui n'en est pas une.

**Ce qui est mesuré.** Le critère de complétude désigne **145 journées** sur le
corpus ; **141** figurent dans les artefacts, les quatre manquantes appartenant à
la station dont la chaîne échoue. Ces journées entrent aujourd'hui dans le calcul
d'amplitude sans distinction.

**Ce qu'il faudrait décider.** Appliquer le critère de trou maximal à
l'amplitude, ou publier l'amplitude avec l'effectif de la journée à côté. Ce
module est **en aval** de la chaîne de normalisation, et rien n'y a été posé
pendant ces travaux — c'était une limite de périmètre, déclarée à l'étape 16.

---

## 5. L'artefact contamine sa propre référence

**Où** — `app/thermie_debits/qc.py:143` (`relativiser`) et `qc.py` (le second
membre, `ecart_a_la_mediane`).

**Le mécanisme.** Les deux membres du détecteur comparent une journée à
l'habitude de sa station **au même mois, toutes années confondues**. Cette
habitude est une médiane et une dispersion calculées sur des journées qui
peuvent elles-mêmes être des artefacts.

**Ce qui est mesuré.** Sur une chronique de trois années, un bloc d'artefact de
vingt-deux journées en mai représente un quart du groupe mensuel. Il tire la
médiane vers lui et gonfle la dispersion, ce qui réduit son propre écart relatif.
Le biais va toujours vers l'innocence de la journée examinée — le détecteur
**sous-détecte** — ce qui est le sens prudent, mais non nul : c'est ce mécanisme
qui a fait échouer une variante du correctif 13 en écartant quinze journées de
mai pourtant corroborées.

**Ce qu'il faudrait décider.** Un estimateur robuste aux blocs — médiane élaguée,
ou référence construite en excluant itérativement les journées marquées. C'est
une **méthode nouvelle**, et c'est pourquoi elle n'a pas été posée ici.

---

## 6. La feuille de synthèse ne porte pas le statut de la correction climatique

**Où** — `app/thermie_debits/livrables.py`, feuille `06_SYNTHESE`.

**Le défaut.** Le statut de la correction climatique — températures corrigées ou
brutes — figure dans le rapport Word, dans la feuille des états déclarés et dans
la feuille de thermie. **Il ne figure pas dans la feuille de synthèse**, qui est
pourtant la seule destinée à comparer des stations entre elles, donc celle où
son absence est la plus dangereuse.

**La raison, et le blocage.** L'en-tête de cette feuille est invariant par
construction, pour que les lignes de plusieurs stations s'empilent telles
quelles. Y ajouter une colonne casserait l'empilement avec des stations produites
par une version antérieure.

**Ce qu'il faudrait décider.** Rompre l'invariance de l'en-tête, avec une règle
de migration, ou porter le statut ailleurs. **Deux lignes empilées, l'une
normalisée et l'autre non, s'y lisent aujourd'hui comme comparables.**

---

## 7. Cinq comportements que le corpus n'exerce pas

Ces branches du programme n'ont **jamais été exécutées** pendant ces travaux. Ce
n'est pas un défaut constaté ; c'est un défaut possible non exclu.

| branche | où |
|---|---|
| débit désinfluencé | `io_data.fusionner_debits` |
| normales fournies en fichier plutôt que calculées | `io_data.charger_normales` |
| export d'air multi-stations | `io_data.charger_air_brut` |
| garde-fou de dispersion nulle | `qc.relativiser`, branche `mad ≤ plancher` |
| lecture des écarts à la normale par la branche `EcartNormales` | `io_data` |

**Ce qu'il faudrait.** Un jeu de données qui les exerce, ou des tests unitaires
qui les couvrent. Aucune des deux n'existe.

---

## 8. Le compte des journées marquées par la vue héritée

**Où** — `tests/reference/build_reference.py`, colonne `motif` de
`03_journees_ecartees.csv`.

**Le défaut.** Cette colonne porte le **premier** motif d'une journée, celui que
la version antérieure lui donnait. Une journée écartée d'abord pour dépassement
de bornes, puis marquée hors d'eau, n'y affiche que le premier motif. Compter les
journées marquées en filtrant cette colonne les sous-estime.

**Ce qui est mesuré.** Après le correctif 13 : **150 par la vue héritée, 151 par
la chaîne complète** — une journée, `LA PLAINE 2011-05-24`. Une colonne
`motifs_complets` a été ajoutée à l'artefact ; **la vue héritée est inchangée**,
et elle reste ce que consomment les outils écrits avant.

**Ce qu'il faudrait décider.** Faire de `motifs_complets` la colonne de référence
pour tout comptage futur, et le documenter, ou renommer la vue héritée pour que
son usage soit explicite.

---

## 9. Les deux références V4.5 ne sont plus reproductibles au bit près

**Où** — `tests/reference_v4_5/`, `tests/reference_cli/`.

**Le constat.** Ces deux références sont figées à l'étape 6. Le harnais a depuis
gagné **dix-neuf colonnes** de diagnostic. Les rejouer avec l'outillage
d'aujourd'hui produit donc des artefacts plus larges, et la comparaison au bit
près échoue sur trois fichiers — ceux qui ont gagné des colonnes.

**Ce qui est mesuré.** **60 artefacts sur 66 sont identiques sur les colonnes
communes ; 19 colonnes ajoutées ; 0 colonne disparue ; 0 valeur modifiée.**
Le code V4.5 n'a pas changé de comportement — c'est l'enregistrement qui s'est
enrichi.

**Ce qu'il faudrait décider.** Soit reconstruire ces témoins avec l'outillage
actuel, ce qui les rendrait reproductibles mais **effacerait les artefacts contre
lesquels treize correctifs ont été mesurés**, soit les laisser figés et
considérer que le contrôle qui leur convient est l'intégrité de leur manifeste —
qui, elle, passe. C'est le choix retenu ici, et il est réversible.

---

## Comment reprendre

Les mesures citées ci-dessus sont toutes rejouables. Les scripts sont dans
`tests/reference/`, chacun exécutable seul, et les artefacts sous `out/`.

Trois documents portent l'ensemble : `docs/METHODO.md` (le carnet de bord des
vingt et une étapes et les règles de méthode qu'elles ont produites),
`docs/VERDICTS_MODIFIES.md` (tout ce qui a bougé dans les résultats publiés, et
tout ce qui n'a pas bougé), et `docs/BILAN_V4_6.md` (le bilan destiné au maître
d'ouvrage).

Les trois références permettent de mesurer l'écart d'une version future à la
V4.6 exactement comme la V4.6 a mesuré le sien à la V4.5 — c'est l'objet de
`tests/reference/comparer_schemas.py`, qui compare deux états d'artefacts sans
exiger qu'ils aient le même schéma.
