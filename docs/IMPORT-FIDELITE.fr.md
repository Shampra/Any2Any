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

Les définitions sources de toutes les vues sont conservées dans le rapport JSON (`views`). La visibilité et l’ordre des propriétés sont appliqués aux vues natives de collection via `layoutSettings.visible`, `hidden` et `order`. Les largeurs, cartes, agrégations et l’ordre manuel des documents restent archivés dans `layoutSettings.any2any.sourceView` quand leur application n’est pas vérifiée. Les dispositions table/list/board/gallery sont envoyées comme indications au client, sans garantie de rendu.

**Depuis 0.9.3 :** les blocs de vue dans les pages utilisent désormais l’enveloppe native `any:block`, `kind: inline-view`. Son `instance` correspond à la table `dataviews`, et sa configuration principale est enregistrée sous `<instance>.list`, avec `query.anyUi.source`, `filters` et `sort`. Le client reconstruit sa requête à partir de ces réglages : enregistrer seulement `query.filter` ne suffit pas.

Les vues en ligne réutilisent désormais leur véritable collection source ou la collection représentant leur type source. Elles ne créent plus de supertag technique « Vue · … » par bloc. Plusieurs vues d’une même collection partagent la même source, mais gardent leurs enregistrements de vues, filtres et tris distincts. Si les propriétés appartiennent déjà à cette source, elles sont réutilisées ; sinon, les champs nécessaires y sont copiés. Ces copies ne sont pas synchronisées avec une propriété homonyme d’une autre collection.

Le client actuel ne propose qu’une source type/collection par bloc Inline view. Une source composée qui ne peut pas être exprimée par ce modèle est refusée explicitement, sans fabrication de collection technique. Une collection cible préexistante contenant d’autres documents que ceux du périmètre source est également refusée pour cette vue, afin de ne pas élargir silencieusement ses résultats. Les anciens supertags techniques des essais précédents ne sont pas supprimés automatiquement.

L’option d’inclusion des éléments liés explore aussi les documents des vues intégrées, en respectant les filtres évaluables, récursivement et sans doublons. Elle sait suivre une query par type, notamment une query sur les collections : les collections affichées sont alors représentées par des pages qui contiennent leurs propres vues. Décochée, l’option n’ajoute aucun document de vue ; celle-ci reste limitée au périmètre choisi, avec avertissement si nécessaire. La simulation affiche le même élargissement.

Les vues en ligne du client affichent les dispositions liste et galerie. Une table source est adaptée en liste avec avertissement ; un regroupement ou un filtre non convertible est refusé explicitement. La vue active (ou la première vue en l’absence d’indication) n’est jamais remplacée silencieusement par une vue moins filtrée. Les vues secondaires sont conservées comme vues enregistrées, sans prétendre que le bloc offre leur sélecteur.

La page de démonstration fournie par le propriétaire a confirmé le format natif. Le parseur et le constructeur de requêtes du client installé ont reconnu le bloc, le filtre numérique et le tri émis, ainsi que les filtres de dates, booléens, sélections et relations. La logique ANY/ALL des relations est traduite explicitement pour éviter une restriction ou un élargissement involontaire. Les filtres vides que le client ignorerait sont refusés. La suite complète de 99 tests automatisés passe. Un essai sur la source réellement signalée, avec toutes les écritures cibles simulées en mémoire, a converti les deux vues de la page en échec. Aucun nouvel objet utilisateur Anytwo n’a été créé pendant ces contrôles.

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


## Fichiers et images — correction du 30 octobre 2026

- Les noms d’origine sont résolus avant le transfert, même lorsque le bloc fournit déjà une extension. Le motif technique de 32 caractères hexadécimaux suivi d’un nom lisible est retiré des métadonnées issues d’un import/clipboard. Les noms constitués uniquement d’un hash sont conservés. L’extension déclarée reste ajoutée aux noms contenant déjà des points, notamment les enregistrements audio/vidéo horodatés.
- Les images ordinaires utilisent le Markdown natif `![nom](any://f/espace/fichier)`, avec le même échappement que le client. Les largeurs en pixels utilisent le commentaire natif `any:image-width`. Les pourcentages de largeur Anytype n’ont pas d’équivalent natif exact : ils sont approximés en pixels sur un bloc de référence de 720 px, avec un avertissement dans le rapport.
- La bibliothèque de l’espace cible est lue une fois par import. Un fichier existant n’est réutilisé que si le nom normalisé, la taille et le SHA-256 des octets correspondent ; le nom seul ne suffit pas. Les variantes/miniatures sont exclues. Si le contenu n’est pas vérifiable, un transfert normal est utilisé.
- Un même fichier Anytype référencé depuis plusieurs pages utilise le même fichier Anytwo, tout en restant une image intégrée à chaque emplacement. Les caches sont séparés par espace cible. Les transferts et réutilisations figurent dans `file_transfers` du rapport.
- Les deux images signalées dans « Cobaye1 » ont été retrouvées par contenu avec leurs identifiants existants, sans téléversement ni modification de page. Le code réel du client a reconnu les noms avec espaces, underscores, crochets et esperluettes comme des images natives.

Ces corrections s’appliquent aux prochains imports. Réutiliser un ancien fichier préfixé ne renomme pas sa fiche dans la bibliothèque ; le nouvel emplacement utilise un libellé nettoyé. Les pages et fichiers déjà créés par les essais précédents ne sont ni réécrits ni supprimés automatiquement.

### Espacements, tailles et propriétés de collection

Les paragraphes vides sont conservés comme paragraphes contenant un caractère sans largeur, pour éviter leur fusion par le Markdown. Les largeurs relatives Anytype sont approximées en pixels sur une largeur de bloc de référence de 720 px, puis limitées au minimum natif de 96 px ; le rapport signale cette approximation. Le rendu ne sera donc pas proportionnel à chaque largeur de fenêtre.

Les options et couleurs des selects sont lues via `/v2/spaces/:space_id/properties/:key/options`. Les propriétés des documents sont aussi disponibles dans leur collection source, y compris si elles sont masquées dans la vue. Les dates avec heure restent en datetime pour préserver les tris ; les propriétés visibles de la vue restent distinctes des colonnes présentes dans la collection. Ces corrections concernent les prochains imports et ne réparent pas automatiquement les copies déjà créées.

### Archives des chats (option)

Les chats restent exclus des pages et types ordinaires. L’option « Importer les chats en tant qu’archives », désactivée par défaut, archive tous les chats exposés par `/v2/spaces/:space_id/chats` pour l’espace source, même si la sélection de pages est partielle. Elle ne découvre pas séparément les discussions d’objets absentes de cette liste.

Une page par chat, regroupée par jour, du plus ancien au plus récent : citations avec en-têtes auteur/date (fuseau explicite), réponses, modifications, réactions et séparateurs entre messages. Les images sont intégrées et les autres fichiers liés si la récupération des fichiers est activée. Les liens vers des objets déjà importés sont reconstruits ; les autres sont signalés. Aucun appel de publication dans les chats Anytwo n’est effectué. Les réactions restent des annotations d’archive. Aucun cadre ou couleur de callout non vérifié n’est inventé.

La lecture suit `next_before`, sans `offset`. Les historiques incomplets, incohérents ou les curseurs répétés provoquent un arrêt avant toute écriture cible. La simulation annonce les pages supplémentaires sans écrire ni télécharger les fichiers. Le rapport JSON contient les messages sources et leurs identifiants, notamment ceux des auteurs, pour conserver les métadonnées et permettre de futures améliorations de présentation.

### Identité des propriétés, palette et collections imbriquées

Une propriété globale Anytype peut être écrite dans plusieurs supertags cibles lorsque des objets ont des types différents. Ces emplacements ne définissent pas des propriétés sources différentes : dans une collection ou vue intégrée, leurs valeurs sont réunies dans une seule colonne portant le nom source. Les valeurs de select sont traduites par libellé lorsque les clés cibles diffèrent. Une contradiction entre valeurs ou entre identités sources homonymes provoque un signalement explicite ; aucun suffixe technique n’est inventé. Les références de propriétés appartenant uniquement à des types hors du périmètre sont ignorées.

Le vert source `lime` est traduit vers `green`, reconnu par le client Anytwo ; le code source de sa palette inclut `green` mais pas `lime`. La valeur `gray` est normalisée en `grey`.

L’import d’un espace conserve aussi les collections comme pages de navigation avec leurs vues intégrées. Les appartenances aux collections parentes utilisent les identifiants de `collection_items` du document source, même si l’endpoint listant les membres omet des collections imbriquées. L’appartenance d’une collection ne signifie pas automatiquement que chaque page affichant cette collection en vue intégrée appartient au même parent.

### Propriétés portées par les collections et vue native

Les membres d’une collection importée reçoivent son supertag équivalent et leurs propriétés sont écrites directement dans celui-ci. Un objet membre de plusieurs collections garde ces appartenances ; les propriétés requises sont disponibles dans chacune. Le supertag du type source sert de repli pour les objets hors collection importée, ou de destination explicitement choisie pour un import par type. On ne rajoute plus automatiquement « Page » aux membres d’une collection. Les champs comptables n’apparaissent donc plus dans le supertag de repli de pages qui n’ont qu’un Tag.

Une collection utilise la table native `dataviews/default` et sa première vue `views/default` (les suivantes restent dans la même table). Les propriétés visibles, masquées et leur ordre sont appliqués ; les tris se trouvent dans `query.sort` et dans `query.anyUi.sort`. Les dates source sont conservées dans une propriété de collection, distincte de la date de création de la copie importée. Le Tag peut être défini et renseigné tout en étant masqué dans cette vue. L’hôte de vues existant est réutilisé lors d’un import dans une collection existante. Les largeurs restent locales au client et sont archivées avec avertissement.
