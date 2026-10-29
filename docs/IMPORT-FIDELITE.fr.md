# Fidélité des imports — 29 octobre 2026

Cette passe améliore la fidélité des imports Anytype vers Anytwo. Les README ne contiennent pas de numéro de version.

## Propriétés

- Conservation des options inutilisées, des noms, couleurs et de leur ordre déclaré ; lecture complémentaire de la liste de tags Anytype quand le vocabulaire n'est pas inclus dans les métadonnées v2.
- Résolution des propriétés par identifiant, nom et légende `property_internal_keys` ; schéma des types conservé même pour les colonnes sans valeur.
- Description de propriété envoyée comme description native. Date avec heure et cardinalité simple des relations transposées lorsque déclarées. Restrictions de relation remappées vers les collections correspondant aux types importés quand toutes sont disponibles.
- Paramètres sans équivalent sûr (lecture seule, valeur par défaut, limite numérique de cardinalité) conservés dans les métadonnées `xFormat.any2any.sourceSettings` et signalés comme non appliqués. Leur archivage ne recrée pas leur comportement.
- Une propriété existante n'est pas reconfigurée silencieusement : les différences de paramètres ou de couleur sont signalées. Les options manquantes sont ajoutées avec leurs couleurs lorsque disponibles.
- Les propriétés de relation utilisent la forme API `any://<objectId>`, tandis que le contenu des pages conserve ses liens de navigation avec espace.

## Vues

Les propriétés et leurs valeurs sont transférées avant la conversion des vues. Les vues de collections sélectionnées et les blocs `dataview` des pages sont examinés. Un objet natif `dataview` est rattaché à la page ou collection cible et reçoit des enregistrements `dataviews` et `views` via `/modify`. Les rejets partiels sont traités comme des échecs.

Les sources de collections sont limitées aux identifiants effectivement importés, sans élargissement aux autres données de destination. Les sources par types utilisent les collections de types ; les sources par propriété conservent une condition de présence. Une source explicitement vide reste vide. Les vues partageant une page utilisent le même objet hôte avec des identifiants de tables et de vues distincts.

Filtres pris en charge : groupes AND/OR imbriqués, comparaisons simples de scalaires, listes `in`/`not_in`/`all_in`, présence. Les identifiants de propriétés, options et relations sont remappés. Les tris ascendants/descendants et le regroupement sont transposés quand la propriété a une seule destination. Un filtre inconnu, une date relative, une comparaison dont les règles de vide diffèrent, un tri personnalisé ou ambigu font refuser la vue entière : aucun filtre n'est simplement retiré.

Les définitions sources de toutes les vues sont conservées dans le rapport JSON (`views`). Les réglages visuels des colonnes, cartes, agrégations et l'ordre manuel sont archivés dans `layoutSettings.any2any.sourceView`, mais leur application par le client n'est pas démontrée. Les dispositions table/list/board/gallery sont envoyées comme indications au client, sans garantie de rendu.

**Limite importante :** les vues sont enregistrées et rattachées via le schéma officiel ; le convertisseur insère un lien à l'emplacement source. Il ne prétend pas créer un bloc interactif au même endroit dans le corps de page : le format de bloc intégré du client n'est pas suffisamment documenté. La vérification visuelle dans Anytwo reste indispensable.

## Colonnes et tableaux

- Parcours récursif des lignes et colonnes imbriquées, sans duplication des colonnes intérieures.
- Images et pièces jointes dans les colonnes transférées par le même mécanisme que les fichiers des blocs principaux ; échecs explicites.
- Conservation du code sans l'interpréter comme mise en forme ; liens d'objets réécrits dans les cellules, y compris les cellules composées de plusieurs blocs.
- Conservation des blocs inconnus avec leur JSON au lieu de les supprimer lorsqu'ils n'ont pas de texte.

La disposition utilise désormais les marqueurs natifs `any:columns` / `any:column`, avec les largeurs sources et les contenus imbriqués. Le parseur du client installé les reconstruit comme de véritables colonnes. Une disposition mal formée conserve son contenu en séquence avec avertissement.

## Références vérifiées

- https://docs.any.org/types/index.html — objets de vues, datasets, hôte.
- https://docs.any.org/types/editor.html — blocs, parents, styles ; frontière entre stockage et rendu.
- https://docs.any.org/database/reading-data.html — filtres et tris cibles.
- https://github.com/anyproto/any/blob/main/docs/27-descriptors.md — paramètres de propriétés et espaces de noms d'extension.
- https://github.com/anyproto/any-block/blob/main/format/v2/SPEC.md — filtres, sources, propriétés et colonnes Anytype.
- https://developers.anytype.io/docs/reference/2025-11-08/list-tags — lecture du vocabulaire des choix.

Les schémas de vues et d'écriture ont également été lus sur l'API installée (any v0.3.4). Aucune donnée utilisateur n'a été importée ou modifiée pendant la recherche. Les vérifications automatisées utilisent des API simulées.


## Mise en forme, médias et icônes

Vérification isolée avec le parseur réel du client installé (build `7a477ecc`, serveur any v0.3.4), sans accès à ses données ni aux médias distants :

- Toggles : marqueurs `any:collapsible`, avec titres et contenu imbriqué. Le parseur produit `collapsible-container`, `collapsible-title` et `collapsible-content`.
- YouTube : enveloppe native `any:block`, de type `embed`, fournisseur `youtube`. Le parseur produit `extension-block`, sans afficher de code iframe.
- Audio : lien de fichier natif `any://f/…` avec le vrai nom et son extension. Le parseur produit `file-link` ; le client choisit son lecteur audio selon l’extension.
- Tableaux : listes HTML de type checklist, reconnues comme cases cochables avec leur état. Le soulignement HTML est conservé dans les cellules, dont l’import utilise le DOM.
- Fichiers : nom et extension recherchés dans les métadonnées sources, puis réutilisés dans le téléversement et le document.
- Icônes : propriété universelle `any.icon` pour les emoji ; fichier téléversé et même propriété pour les icônes images.

**Limite du soulignement hors tableau :** le parseur Markdown de ce client n’a pas de transformateur pour `<u>`, même si le moteur de texte sait représenter le style. Le migrateur conserve le texte sans les balises visibles et signale la perte dans le rapport. Les exposants et indices suivent la même règle. Les balises dans du code restent littérales. Les couleurs de texte et de fond restent limitées par Anytwo.

Les tests automatisés couvrent les formats émis et les transferts simulés. Le propriétaire du projet a ensuite vérifié les corrections signalées dans Anytwo. Les limites décrites ici, notamment le soulignement hors tableau et le rendu des vues, restent applicables.

La page de référence créée par l’utilisateur, « Demo pour import » dans « Test space », a ensuite été consultée en lecture seule. Son Markdown confirme les marqueurs de toggle, les liens audio natifs et l’enveloppe YouTube employés ici, ainsi que les deux états de checklist dans les tableaux.
