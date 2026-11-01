# Relations et rollups Anytwo : vérification API

Vérification du client local le 31 octobre 2026, en lecture seule. Aucun test de migration n’a été écrit dans Anytwo.

## Relation

L’API documente une propriété `kind: array` avec `xFormat.type: relation`. Les valeurs sont des tableaux de références `any://<objectId>`. Le descripteur porte notamment `config.multiple` et les restrictions de cible. La conversion doit remapper les identifiants des objets, des propriétaires et des propriétés ; les identifiants Notion ne sont pas utilisables directement. Les relations inverses et les cibles hors sélection demandent une adaptation distincte.

Source : [types de données Anytwo](https://docs.any.org/database/data-types.html).

## Rollup

Le contrat local `GET /v1/openapi.json` n’annonce pas de route spéciale « rollup ». Il expose cependant les routes génériques de propriétés des collections/types et un `xFormat` qui conserve les paramètres de son espace de noms client.

La lecture de propriétés déjà créées dans Test space confirme :

- `kind: object`, `xFormat.type: rollup` ;
- configuration JSON sérialisée dans `xFormat.anyui.rollup` ;
- `relation.direction: own`, `relation.ownerId` et `relation.propertyId` ;
- `target.ownerId` et `target.propertyId` ;
- opérateurs observés `calculate: sum` et `calculate: original`, avec `showAs: number`.

La configuration peut donc être transportée par l’API générique des propriétés. La conversion doit créer les schémas et relations avant de remapper ces références. Elle ne doit pas écrire le résultat Notion à la place d’une définition de calcul. Le comportement du calcul après création via l’importeur doit encore être validé dans le client : les observations ne prouvent pas l’équivalence de tous les opérateurs Notion.

Le rapport classe désormais le rollup comme **à adapter**, plutôt que comme résultat systématiquement figé. Une fonction sans correspondance validée conserve un avertissement et son résultat archivé. Le module Notion configure maintenant ces deux agrégations lorsque les identifiants de relation et de propriété cible ont été remappés. Les descripteurs ont été créés dans l’espace de test dédié ; le recalcul visuel dans le client reste à vérifier.

Les exemples réels ne sont pas copiés dans ce document : les identifiants et les noms de propriétés personnels restent hors du dépôt.

## Correction et contrôle du 1 novembre 2026

La restriction d’une relation doit renseigner relation.targetTypes avec le xKey du supertag cible. L’absence de cette restriction empêche aussi le client de proposer la relation dans l’éditeur de rollup. Le titre cible utilise l’identifiant any.name, associé au propriétaire collection cible ; le couple any / name initialement généré ne correspondait à aucun choix du client.

Après correction du modèle importé dans Sri, les fonctions réelles du client reconnaissent les choix Projet → Name et Projet → Budget. Les calculs retournent les noms attendus et les sommes 100, 180 et 0. Ceci valide ces configurations somme/valeurs originales ; les autres opérations restent à vérifier. Les valeurs des propriétés n’ont pas été réécrites.


## Two-way et average : contrôle du 1 novembre 2026

Le client stocke le lien inverse dans xFormat.anyui.inverseOwner et inverseProperty. Il ne reconnaît la paire que si la définition opposée pointe réciproquement vers la première, avec les identifiants propriétaires/propriétés de destination. La conversion Notion les applique après création des schémas, sans recréer les propriétés.

L’opérateur natif de moyenne est calculate: average dans le même descripteur anyui.rollup. L’API générique permet de le transporter ; l’évaluation par le client sur la copie en mémoire des objets importés reproduit les 53 résultats numériques du bilan Notion contrôlé, dont 11,5. Aucun PATCH n’a été envoyé pour cette vérification : seules les définitions simulées ont été remplacées dans le contexte de calcul isolé. La moyenne suit la relation propre à chaque objet ; elle ne porte pas sur toute la collection cible.
