# Pages de démonstration des sources

Les exemples JSON sont dans `examples/notion-test-page.json` et `examples/anytype-test-page.json`. Ils décrivent les blocs de base, sans identifiant privé ni clé.

`tools/create_test_pages.py` est un outil explicite de création de données fictives, indépendant de l’importeur en lecture seule. Sans argument, il génère seulement les exemples JSON. `--apply` active les écritures demandées ; pour Notion, il faut aussi nommer le workspace attendu :

```powershell
python -B tools/create_test_pages.py --apply --source notion --notion-workspace "Votre espace"
python -B tools/create_test_pages.py --apply --source anytype
```

La page parente Notion par défaut est « Test pour Anytwo » ; `--notion-parent` permet de préciser son titre. Elle doit être unique, à la racine, et autorisée pour la connexion. Le programme vérifie le nom de workspace avant toute création. Il crée une sous-page, pas un remplacement de la page parente.

Pour Anytype, le programme tente le nouvel espace « Test pour Anytwo » et utilise Cobaye1 uniquement si la création d’espace est refusée. La clé doit avoir l’écriture : le repli ne contourne pas ce droit. Les réglages des applications sont lus pour s’authentifier, sans modification ni copie des clés. Le programme n’élargit jamais les autorisations.

## Contenu

- Titres, texte, gras, italique, soulignement, barré, code, couleurs, paragraphes vides.
- Listes imbriquées, cases à cocher, toggles et titres repliables, citations, callouts, séparateurs.
- Colonnes, tableaux, équation et sommaire.
- Image PNG, son WAV synthétique, fichier texte, CSV, référence à la même image à plusieurs endroits, vidéo YouTube et signet.
- Notion : sous-page et mentions, bloc synchronisé et sa référence ; deux bases inline, deux projets et trois tâches, choix colorés, dates, relations, formules, rollups (somme et valeurs originales) et vue filtrée/triée avec propriétés masquées.
- Anytype : type de démonstration avec propriétés, deux objets liés, options colorées, collection et query, vue inline filtrée/triée et propriétés masquées. Le tableau contient une vraie checkbox de cellule.

Il ne s’agit pas d’une reproduction de tous les contrôles de l’interface : boutons, formulaires, automatisations, certains réglages visuels ou médias particuliers restent limités par l’API. Aucun chat/message n’est envoyé.

## Vérifications et reprise

Le journal local `reports/source-fixtures.json` conserve les ressources créées et les étapes terminées. Il est ignoré par Git, peut contenir des URL de fichiers temporaires et ne contient pas de clé d’API. Après un résultat réseau inconnu, vérifier les ressources avant toute relance : Notion ne fournit pas ici de garantie d’idempotence générale.

Les modèles créés pendant cette session ont été relus via leurs API : 40 blocs de premier niveau, deux projets et trois tâches dans Notion ; 43 blocs, quatre fichiers et une vue inline dans Anytype. Les sommes Notion ont été vérifiées à 100, 180 et 0 ; la vue possède son filtre et son tri. Les deux blocs image Anytype référencent le même objet fichier.
