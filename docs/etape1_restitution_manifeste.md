# Étape 1 · D.3 — `docs/MANIFESTE.md`, ce qui porte sur la chaîne lecture → T_norm

Restitution seule. Les décisions retenues sont **citées telles quelles**, sans reformulation. Les autres sont listées par titre et ne sont pas développées.

Le manifeste est lu dans `ref/thermie_points/thermie_points.zip` (`docs/MANIFESTE.md`), en place, sans ré-extraction (D9).

## Décisions qui portent sur la chaîne lecture → T_norm

### Station d'air de référence

*Pourquoi cette décision relève du périmètre :* La station d'air fixe la normale journaliere, donc Delta_TMm, donc T_air_std et la temperature normalisee. Elle fixe aussi la periode de reference effective, que V4.5 code en dur a 1991-2020 (io_data.py:306) mais calcule sur les seules annees disponibles (io_data.py:511-512).

Citation intégrale :

> **Ce qui a été décidé.** LA_PESSE (1133 m) plutôt que CHAUX_DES_PRES.
>
> **Sur quoi.** Deux stations couvrent le bassin. CHAUX_DES_PRES (854 m) ne compte que 7 années dans la période de référence, pour un seuil de 20 : elle ne peut pas servir de station de normalisation, et l'outil du volet biologique émettrait lui-même l'avertissement. LA_PESSE (1133 m) couvre 1996-2026, soit 25 années dans la période de référence ; c'est sa date de début qui fixe la normale à 1996-2020 et non à la période trentenaire usuelle 1991-2020. La comparaison des deux stations a été faite sur leur PÉRIODE COMMUNE, seule façon d'isoler l'effet de station de l'effet de période.
>
> **Ce qu'il faut en faire ailleurs.** Sur un autre bassin, la station se choisit d'abord sur la couverture dans la période de référence, jamais sur la proximité géographique seule ; et la période de normale suit la station retenue, jamais l'inverse. À noter pour la lecture : ici la station la plus HAUTE est la plus chaude en moyenne — accumulation d'air froid en creux, fréquente sur les plateaux du Jura — de sorte qu'un décalage entre deux stations ne se déduit pas de leur différence d'altitude.

## Décisions hors périmètre — titres seuls

Elles sont nommées, non développées : les développer reviendrait à ouvrir un débat que l'étape 1 n'a pas à ouvrir.

- Cours d'eau des préfixes GRO et LGV
- Relecture experte des épisodes d'exondation
- Point écarté de toute comparaison
- Réserve d'implantation
- Réserve de robustesse au seuil

## Autres sections du manifeste — titres seuls

- 1. Ce dont on part
- 2. La commande unique
- 3. Ce qui est produit
- 4. Ce qui est remis, et ce qui ne l'est pas
- 5. Les décisions qui ne se déduisent d'aucune donnée
- 6. Ce que le rejeu ne reconstruit pas
- 7. Les versions employées

