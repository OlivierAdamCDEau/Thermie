# Étape 21 — La clôture

Treize correctifs posés. Trois dettes réglées. La référence rebasée, l'ancienne
conservée. Trois livrables produits.

---

## §0 — Carnet de bord

| | |
|---|---|
| Code exécuté | `app/` (`THERMIE_CODE=app`) |
| Sources applicatives modifiées | **2 sur 16** — `qc.py`, `redaction.py` |
| Harnais modifié | `eprouver_temoin.py`, `verifier_integrite_references.py` |
| Harnais ajouté | `balayer_chemins_sortie.py`, `rebaser_cloture.py` |
| Références | 2 → **3** |
| Prédiction de la pose 1 | *aucun artefact ne bouge* — **confirmée**, 66 figés |

**D76 à l'entrée** : les manifestes décrivent leurs dossiers, `ref/` est propre,
retour 0.

**Un sceau rompu, et c'est écrit.** `eprouver_temoin.py` portait l'empreinte
`e78f370e…` depuis l'étape 19. Elle a rempli son office à l'étape 20, où le
script devait être rejoué **sans modification** pour que la comparaison des deux
épreuves ait un sens. Le corriger imposait de la rompre. La rupture est déclarée
en tête du fichier, l'empreinte d'origine y est reproduite, et elle reste au
dossier de l'étape 19. *Rompre un sceau sans le dire serait pire que ne l'avoir
jamais posé.*

---

## §1 — Les trois dettes (D121)

### 1.1 Le second membre atteint l'écran

Le correctif 13 avait ajouté un second membre à la marche 1 sans que l'écran le
nomme : un lecteur voyait que le détecteur avait tourné, pas qu'il comportait
deux membres. `qc.py` publie désormais **les mois** où ce membre s'abstient ;
`redaction.py` rend l'ensemble dans l'idiome du bloc « ce qui a été vérifié ».

Trois lignes s'ajoutent, dans la même forme que les autres :

> *Comment il distingue l'eau de l'air :* le premier niveau compare la
> température de l'eau à celle de l'air. Un tel écart grandit aussi bien quand
> l'eau monte que quand l'air descend, et la différence seule ne dit pas lequel
> des deux a bougé. Une seconde condition est donc exigée : **l'eau doit être
> plus chaude que d'habitude à cette station et à ce mois-là**. Un coup de
> froid, qui fait plonger l'air sans que l'eau bouge, ne passe plus pour une
> sonde sortie de l'eau.
>
> *Ce que cette seconde condition a écarté :* **aucune journée.** Sur cette
> chronique, les deux conditions ont toujours été d'accord.
>
> *Là où cette condition ne se prononce pas :* **mai** — trop peu de journées
> mesurées dans ce ou ces mois pour savoir ce qui y est habituel. Le contrôle ne
> marque alors aucune journée de ces mois, et cela ne vaut pas quitus : il n'a
> pas pu regarder.

*(Rendu sur `BLE3-0`, dont mai compte sept journées pour dix requises — l'un des
six couples relevés à l'étape 20.)*

**Une phrase devenue fausse, corrigée au passage.** L'écran annonçait
« **{n} journées** de la période estivale ». La fenêtre est l'année entière
depuis le correctif 13 ; l'affichage ne l'avait pas suivi.

### 1.2 `eprouver_temoin.py` cesse d'écrire en dur

Sa sortie est désormais redirigeable — `--sortie <dossier>`, avec `out/etape19`
pour défaut, de sorte que le rejouer sans argument reproduit exactement l'ancien
comportement. Le témoin final de cette étape a été produit avec `--sortie
out/etape21/temoin`, ce qui vérifie la réparation par l'usage.

### 1.3 Le balayage des chemins de sortie

**La question posée n'était pas la bonne, et la corriger a été le travail.**
Chercher « les chemins de sortie en dur » désigne **cinquante scripts sur
soixante-quatre** — et n'apprend rien : un script d'étape 3 qui écrit dans
`out/etape3/` ne peut écraser que ses propres sorties.

Le critère utile est autre : **le script peut-il être rejoué plus tard, et sa
sortie est-elle alors redirigeable ?**

| | |
|---|---:|
| scripts du harnais | 64 |
| qui écrivent dans un dossier d'étape | 50 |
| **qui écrivent dans une étape antérieure à la leur** | **0** |
| à sortie figée et lisant dans une autre étape — candidats au rejeu | 7 |

Aucun script n'écrit dans une étape antérieure à la sienne. Sept ont une sortie
figée tout en lisant des étapes antérieures, ce qui les désigne comme conçus
pour servir au-delà de leur étape d'origine ; **un seul a effectivement été
rejoué** par une étape ultérieure, et c'est celui de l'incident. Les six autres
écrivent chez eux : les rejouer n'écrase que leurs propres sorties.

### La prédiction

> *Aucun artefact ne bouge. L'affichage ne calcule rien.*

**Confirmée.** Rejeu complet après pose 1, comparé à celui de l'étape 20 :

| | |
|---|---:|
| artefacts comparés | 66 |
| **qui bougent** | **0** |
| figés | 66 |

---

## §2 — Le rebasage de clôture (D83, branche B)

### La copie, vérifiée avant toute destruction

L'ancienne référence a été copiée **d'abord**, et la copie confrontée à
l'original empreinte par empreinte **avant** que quoi que ce soit ne soit
reconstruit :

| | |
|---|---:|
| fichiers copiés | **78** |
| manquants | 0 |
| divergents | 0 |

*On ne détruit pas un témoin sur la foi d'une copie non vérifiée.* Le script
s'arrête avant le rebasage si cette vérification échoue.

### Les trois références

| référence | source | étape | ce qu'elle atteste |
|---|---|---|---|
| `tests/reference/` | `app` | 21 | ce que l'outil produit **aujourd'hui** |
| `tests/reference_v4_5/` | `ref` | 6 | l'état **en service** avant les travaux — c'est contre elle que les treize correctifs ont été mesurés |
| `tests/reference_cli/` | `ref` | 6 | le même état par l'autre chemin de paramètres |

La provenance de la nouvelle référence porte la mention des deux autres, pour
qu'un lecteur qui n'ouvre que ce fichier sache où est le témoin V4.5.

### 2.3 — Les vérifications

| contrôle | retour | |
|---|---:|---|
| `check_reference.py` sur `tests/reference` (app) | **0** | **DIFF VIDE — la référence est reproductible** |
| `check_reference.py` sur `tests/reference_v4_5` (ref) | 1 | trois artefacts divergent, tous par ajout de colonnes |
| `check_reference.py` sur `tests/reference_cli` (ref, cli) | 1 | les mêmes trois |
| **D70 — comparaison de sources croisées** | **3** | **refusée** : « la référence a été produite par `app`, le rejeu demandé est `ref` » |
| `verifier_integrite_references.py` — **les trois** | **0** | 66 + 66 + 66 artefacts, **0 empreinte divergente** |

**Les deux références V4.5 ne rendent pas 0, et je ne les y force pas.** La cause
est mesurée, non supposée :

> `comparer_schemas.py` entre `tests/reference_v4_5` et un rejeu `ref`
> d'aujourd'hui : **60 artefacts identiques sur les colonnes communes,
> 19 colonnes ajoutées, 0 colonne disparue, 0 valeur modifiée.**

Le harnais a gagné dix-neuf colonnes de diagnostic depuis l'étape 6. Le code
V4.5 n'a pas changé de comportement — **c'est l'enregistrement qui s'est
enrichi**. Les trois artefacts qui divergent sont exactement ceux qui ont gagné
des colonnes, sur les deux références, ce qui confirme la cause unique.

Les rendre reproductibles supposerait de les reconstruire, c'est-à-dire
**d'effacer les artefacts contre lesquels treize correctifs ont été mesurés**. Le
contrôle qui convient à un témoin figé n'est pas la reproductibilité par le code
d'aujourd'hui, c'est l'intégrité de son manifeste — et elle passe sur les trois.
`verifier_integrite_references.py` couvre désormais la troisième.

### 2.4 — `comparer_schemas.py` entre l'ancienne et la nouvelle

Il fonctionne, et c'est ce qui permettra à une version ultérieure de mesurer son
écart à la V4.6 exactement comme la V4.6 a mesuré le sien à la V4.5. Sa
particularité est justement de comparer deux états **sans exiger qu'ils aient le
même schéma** : c'est l'outil des transitions de version.

---

## §3 — Les contrôles finaux

| contrôle | résultat | retour |
|---|---|---:|
| `check_reference.py` — `tests/reference` (V4.6) | DIFF VIDE, reproductible | **0** |
| `check_reference.py` — `tests/reference_v4_5` | 19 colonnes ajoutées, 0 valeur changée | 1 |
| `check_reference.py` — `tests/reference_cli` | idem | 1 |
| D70 — sources croisées | **refus**, comme voulu | 3 |
| `verifier_integrite_references.py` — trois références | 198 artefacts, 0 divergente, `ref/` propre | **0** |
| `empreintes_app.py` — les seize sources | 14 identiques, **2 modifiées** et déclarées | 2 |
| Rejeu complet après pose 1 | 66 artefacts, **0 bouge** | — |
| Témoin scellé, une dernière fois | *voir ci-dessous* | 0 |

**Les deux sources modifiées** sont `qc.py` (le champ de diagnostic des mois
d'abstention) et `redaction.py` (leur rendu). Le calcul du second membre,
`ecart_a_la_mediane`, **n'est pas modifié d'un caractère** — et le rejeu à zéro
artefact déplacé le prouve.

### Le témoin scellé, pour mémoire

`temoin_regime.py` porte toujours son empreinte d'origine `ef98c126…`.
`eprouver_temoin.py` a vu la sienne rompue, délibérément et par écrit, pour la
seule raison du chemin de sortie ; **sa règle et ses populations sont
inchangées**.

---

## §4 — Les trois livrables

| document | destinataire | contenu |
|---|---|---|
| [`docs/BILAN_V4_6.md`](BILAN_V4_6.md) | **maître d'ouvrage** | ce que l'outil faisait et ce qu'il fait ; les treize correctifs, un paragraphe chacun, ordonnés par importance pour le lecteur ; le bilan des verdicts station par station ; les limites, sans les adoucir ; ce qu'il faudrait pour lever les doutes |
| [`docs/CHANTIER_AVAL.md`](CHANTIER_AVAL.md) | **chantier suivant** | neuf points transmis, chacun avec sa référence dans le code, la mesure déjà faite, et la décision qui reste à prendre |
| [`docs/METHODO.md`](METHODO.md) | **mémoire technique** | le carnet des vingt et une étapes, complété d'une section de clôture : l'état final, les trois références, et les douze règles de méthode que le chantier a produites |

Aucun numéro de décision, aucun nom de fonction et aucun jargon dans le premier ;
c'était la contrainte, et elle a été tenue.

---

## §5 — Ce qui reste ouvert, une dernière fois

Neuf points sont transmis. Trois méritent d'être répétés ici, parce qu'ils
touchent des chiffres publiés.

**1. Deux journées de La Plaine à Raon-sur-Plaine sont encore publiées comme
vulnérabilité aiguë, et ne devraient très probablement pas l'être.** Les 3 et
4 juin 2011 appartiennent au bloc artefactuel du 18 mai au 14 juin. Le détecteur
ne les voit pas parce que **l'air était chaud ces jours-là** — 19 à 20 °C contre
10 à 15 °C le reste du bloc —, ce qui referme l'écart eau-air sous le seuil.
Après le correctif 13, ce sont les trois seules journées que le témoin
indépendant signale encore sur cette station, contre seize avant. Les corriger
demande de promouvoir en détecteur un témoin de vérification, avec son propre
cycle de validation.

**2. La feuille de synthèse du classeur ne porte pas le statut de la correction
climatique.** C'est pourtant la seule feuille destinée à comparer des stations
entre elles. Deux lignes empilées, l'une normalisée et l'autre non, s'y lisent
comme comparables. Le blocage est connu : l'en-tête est invariant par
construction, pour permettre l'empilement avec des versions antérieures.

**3. Un indicateur qui ne bouge pas parce qu'il est saturé n'est pas un
indicateur non affecté.** Sur La Canner à Vigy, le retrait de vingt journées
enregistrées hors de l'eau pendant la période de reproduction déplace le
coefficient de correction de 39 % sans que le score publié change — il était
déjà à son maximum. Sur une station moins dégradée, les mêmes vingt journées
auraient pesé.

Et une station, `BIE35-5__NA`, ne produit toujours aucun résultat : sa chronique
ne contient aucun jour de juin à septembre. Le comportement est correct ; il
fallait le dire.

---

## Artefacts

Sous `out/etape21/`.

| fichier | contenu |
|---|---|
| `A_empreintes.txt` | les seize sources applicatives, avant et après |
| `B_chemins_sortie.csv` | où chaque script du harnais écrit, et le risque de rejeu |
| `C_schemas_v45.txt` | l'ancienne référence contre un rejeu d'aujourd'hui : 0 valeur changée |
| `D_check_*.txt` | les trois vérifications de référence, et le refus D70 |
| `F_integrite.txt` | l'intégrité des trois manifestes |
| `rejeu_pose1/` | le rejeu qui confirme la prédiction : 66 artefacts, 0 bouge |
| `temoin/` | le témoin scellé, une dernière fois, produit via `--sortie` |
| `99_console_*.txt` | les traces intégrales |
