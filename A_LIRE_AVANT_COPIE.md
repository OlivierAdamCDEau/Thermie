# Ce que contient cette archive, et ce qu'il manque

Contenu a copier tel quel dans le dossier synchronise
`...\GitHub\Thermie bio\`. Les chemins se superposent : `docs\` et
`tests\reference\` n'existent pas encore cote depot, ils seront crees.

## Ce qui est deja a jour et n'est PAS dans l'archive

Le code applicatif. Les onze sources modifiees, `VERSION.txt` (4.6) et
`CHANGELOG.md` sont deja en place dans le dossier synchronise, verifies
identiques a l'etat final octet pour octet. Ne recopie rien du code.

## Ce que l'archive apporte

| dossier | contenu |
|---|---|
| `docs\` | 38 documents : METHODO, BILAN_V4_6, CHANTIER_AVAL, VERDICTS_MODIFIES, les trois specifications, le registre, les quatre restitutions et les rapports d'etape |
| `tests\reference\` | 60 scripts du harnais, `.py` uniquement |
| `.gitignore` | remplace celui du depot |

`docs\etape1_extraits_bruts.md` est volontairement absent : il contient les
cinq premieres lignes brutes des 46 fichiers du corpus. Donnee, non methode.

## CE QU'IL MANQUE, et que tu dois ajouter depuis ton disque

Deux choses, parce qu'elles ne sont jamais parvenues au controle.

**1. `docs\etape18_rapport.md`.** La livraison de l'etape 18 n'a jamais ete
transmise ; seul son compte rendu l'a ete. Le fichier existe sur ton disque,
dans `THERMIE_BIO_V4_6\docs\`. Copie-le dans `docs\`.

**2. Quatre scripts du harnais.** L'archive en porte 60, le rapport de cloture
en compte 64. Les manquants sont probablement ceux de l'etape 18, dont la
livraison manque de meme.

Pour les retrouver : compare le contenu de `THERMIE_BIO_V4_6\tests\reference\`
(les `.py` seulement) a celui de `tests\reference\` de cette archive, et copie
la difference.

**Ne copie AUCUN sous-dossier de `tests\reference\`.** Les dossiers `jeu_*`
contiennent les cinq classeurs et cinq rapports Word produits pour tes clients,
et pres de cent mille lignes de temperatures.

## README.md

Il decrit encore l'application sans mentionner la V4.6, ni `docs\`, ni le
harnais. Il n'est pas dans cette archive : il doit etre reecrit par l'app, avec
la mention que les scripts de `tests\reference\` ne tournent pas en l'etat,
faute du corpus et des references figees, qui ne sont pas diffuses.

## Verification, avant de pousser

`git status` doit montrer, en plus des fichiers de code deja modifies :
`docs\` (39 fichiers avec l'etape 18), `tests\reference\` (`.py` seulement),
`.gitignore`.

Rien d'autre. Un `.csv`, un `.xlsx`, un dossier `jeu_` qui apparait signifie
qu'un sous-dossier a suivi. Refais le controle apres `git add`.
