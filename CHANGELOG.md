# Changes / Modifications

## 0.11.0 — 2026-11-24 — Mentions, clean properties, bilingual interface and Anytype import corrections

### English

- Convert Anytype inline `@` mentions to native object links in page text, tables, columns and the description. Mention targets join the import when linked items are enabled; otherwise the label stays as plain text with a report warning.
- Stop importing Anytype record bookkeeping (`Source object`, `template_name_prefill_type` and other internal keys) as Anytwo columns. Classification uses the verified property identity, never a label or a `template_` prefix, so custom properties such as `template_notes` are preserved; cleanup only removes columns this import created and tracked, and untranslatable template settings are reported.
- Fix property write failures: empty url/email/phone/number/date values are skipped instead of aborting the property, and relation columns always receive `any://` URI arrays.
- Stop creating a duplicate `X (Anytype)` text column when relation values point to objects that are not imported: the relation column is kept and only the missing references are dropped.
- Write page warnings and labels in the language chosen in the interface (French, English, German), and remove the bold markers that Anytwo displayed verbatim inside quotes.
- Preserve native toggles, columns, inline views, embedded properties, synced blocks, captions and media on the current Anytwo client. Server 0.5 HTML records remain valid editor markup; no version-based stripping is applied. Literal code and empty paragraphs are preserved.
- Translate the whole interface: every static label, plus report issues, API errors, progress and simulation messages, in English and German. The import window now fits the screen without zooming out.
- Publish French and English editions of every technical guide, with language switchers.
- Add a macOS double-click launcher (`Any2Any.command`) next to `demarrer.bat` and the standalone Windows executable.
- Import native Anytwo templates with their content, properties and unambiguous collection defaults. Preserve an existing destination default when it differs.
- Convert top-level Anytype tables of contents to native dynamic blocks on compatible Anytwo versions. Keep nested tables of contents as static block links.
- Preserve compatible nested AND/OR filters, single-select comparisons and empty-value conditions in both stored queries and client controls.
- Link source collections directly to their Anytwo collection, and apply saved views to referenced collections, including archived source collections. Preserve compatible filters, sorts, groups and visible properties.
- Preserve date/time values without downgrading their destination descriptor. Display readable source type names, convert object mentions to inline links and correctly rewrite escaped internal link parameters.
- Place Anytype file/image property content at the start of the page instead of creating text columns. Keep attachment reuse across pages.
- Refresh the Anytype compatibility list, its translations and public documentation. Keep release-publication tests independent of locally built archives.

### Français

- Convertir les mentions `@` Anytype en liens d’objet natifs dans le texte, les tableaux, les colonnes et la description. Les cibles rejoignent l’import avec l’option des éléments liés ; sinon le libellé reste en texte brut avec un avertissement dans le rapport.
- Ne plus importer la comptabilité interne d’Anytype (`Source object`, `template_name_prefill_type` et autres clés internes) comme colonnes Anytwo. La classification utilise l’identité vérifiée de la propriété, jamais un libellé ni un préfixe `template_` : les propriétés personnalisées telles que `template_notes` sont conservées ; le nettoyage ne retire que les colonnes créées et tracées par cet import, et les réglages de template non transposables sont signalés.
- Corriger les échecs d’écriture de propriétés : les valeurs url/email/téléphone/nombre/date vides sont ignorées au lieu d’annuler la propriété, et les colonnes de relation reçoivent toujours des tableaux d’URI `any://`.
- Ne plus créer de colonne texte en double « X (Anytype) » quand une relation pointe vers des objets non importés : la colonne de relation est conservée et seules les références absentes sont écartées.
- Écrire les avertissements et libellés des pages dans la langue choisie dans l’interface (français, anglais, allemand) et retirer les marqueurs de gras qu’Anytwo affichait tels quels dans les citations.
- Conserver les toggles, colonnes, vues en ligne, propriétés intégrées, blocs synchronisés, légendes et médias natifs sur le client Anytwo actuel. Les blocs HTML du serveur 0.5 restent un format valide pour l’éditeur ; aucun retrait de marqueurs selon la version. Le code littéral et les paragraphes vides sont préservés.
- Traduire toute l’interface : libellés statiques, problèmes du bilan, erreurs d’API, progression et messages de simulation, en anglais et en allemand. La fenêtre d’import tient désormais dans l’écran sans zoom arrière.
- Publier chaque guide technique en français et en anglais, avec un sélecteur de langue.
- Ajouter un lanceur macOS à double-clic (`Any2Any.command`) à côté de `demarrer.bat` et de l’exécutable Windows autonome.
- Importer les templates natifs Anytwo avec leur contenu, leurs propriétés et leur défaut de collection lorsqu’il est déterminable. Conserver un défaut cible existant lorsqu’il diffère.
- Convertir les sommaires Anytype de premier niveau en blocs dynamiques natifs sur les versions compatibles. Conserver les sommaires imbriqués sous forme de liens statiques vers les blocs.
- Reprendre les filtres ET/OU imbriqués compatibles, les comparaisons de select simple et les conditions de valeurs vides, dans la requête et les contrôles du client.
- Lier directement les collections source à leur collection Anytwo et appliquer les vues enregistrées aux collections référencées, même archivées côté source. Conserver les filtres, tris, regroupements et propriétés visibles compatibles.
- Préserver les dates avec heure sans rétrograder leur descripteur cible. Afficher les noms lisibles des types source, convertir les mentions en liens inline et réécrire correctement les paramètres échappés des liens internes.
- Placer le contenu des propriétés fichiers/images Anytype en début de page au lieu de créer des colonnes texte. Réutiliser les pièces jointes entre les pages.
- Actualiser la liste des incompatibilités Anytype, ses traductions et la documentation publique. Rendre les tests de publication indépendants des archives construites localement.

## 0.10.2 — 2026-11-16 — Migration fidelity / Fidélité des imports

### English

- Restore Anytype page and collection widgets in Anytwo Overview, in source order. Keep Link widgets as links, use Views for other layouts and skip built-in widgets such as Recently edited.
- Preserve compatible Anytype text filters and empty filter controls without dropping the saved view or its sort.
- Resolve linked Anytype file objects as attachments, including PDFs, and reuse file references across pages.
- Preserve underlining on compatible Anytwo versions. Import supported Anytype property blocks and create static links to headings for tables of contents.
- Preserve compatible Notion inline tables and boards, embed owned databases as native collection blocks, and transfer date ranges and more filters.
- Select the newly created Anytwo space for the next Notion import and clarify remaining migration limits.

### Français

- Reprendre les widgets Anytype de pages et de collections dans l’Overview d’Anytwo, dans l’ordre source. Conserver le mode Link, utiliser Views pour les autres modes et ignorer les widgets système comme Recently edited.
- Conserver les filtres texte Anytype compatibles et les contrôles de filtre vides, ainsi que le tri de la vue.
- Récupérer les objets fichiers liés depuis Anytype, dont les PDF, et réutiliser leurs références entre les pages.
- Conserver le soulignement sur les versions compatibles d’Anytwo, reprendre les blocs de propriétés Anytype pris en charge et fournir des sommaires statiques liés aux titres.
- Préserver les tableaux et kanbans intégrés Notion compatibles, insérer les bases intégrées comme blocs de collection natifs et reprendre les plages de dates et davantage de filtres.
- Sélectionner l’espace Anytwo nouvellement créé pour le prochain import Notion et préciser les limites restantes.

## 0.10.1 — 2026-11-01 — Distribution layout / Organisation de l’application

### English

- Add a standalone Windows x64 ZIP with Any2Any.exe at the top level, a bundled _internal runtime and documentation in a subfolder.
- Group source/runtime files under app and development material under dev; adapt launchers, builders, tests and release automation.
- Preserve existing settings and both source import paths. Test the extracted executable before publication.

### Français

- Ajouter un ZIP Windows x64 autonome : Any2Any.exe à la racine, dépendances dans _internal et documentation en sous-dossier.
- Ranger le code et les ressources dans app, et les outils/tests dans dev ; adapter lanceurs, construction, tests et publication.
- Conserver les réglages et les deux parcours d’import. Vérifier l’exécutable après extraction avant publication.


## 0.10.0 — 2026-11-01 — English — unified Anytype / Notion application

- Choose Anytype or Notion at startup; shared Anytwo backend and one main launcher.
- Notion imports: tree selection, files, native formatting, views, grouping, two-way relations and compatible rollups.
- Preserve gallery Fit image and use side peek unless full-page opening is explicitly requested.
- Fewer Notion reads, shared cache, interrupted-read reuse and detailed progress.
- Clean source archive without credentials, private reports or development diagnostics.

## 0.10.0 — 2026-11-01 — Français — application commune Anytype / Notion

- Choix de la source au démarrage, moteur Anytwo commun et lanceur principal unique.
- Import Notion : sélection arborescente, fichiers, formats natifs, vues, regroupements, relations bidirectionnelles et rollups compatibles.
- Conservation de Fit image et ouverture en side peek sauf indication explicite de pleine page.
- Réduction des lectures, cache partagé, réutilisation après interruption et progression détaillée.
- Archive source sans secrets, rapports privés ni diagnostics de développement.


## 0.9.3 — 2026-10-30 — Collections, inline views and chat archives

### English

Experimental release focused on source fidelity and native Anytwo collections/views.

- Import inline queries and collections as native inline views, preserving supported filters and sorts. Include matching documents recursively when linked-object inclusion is enabled, with the same scope in the preview.
- Configure the actual default collection view: visible/hidden properties, column order and sorting by the original Anytype creation date.
- Store members’ properties directly in their collection supertags. Use type supertags as a fallback outside imported collections; avoid redundant Page memberships and artificial suffixed properties. Preserve nested collection navigation pages and parent memberships.
- Retrieve select options and colors through the Anytype v2 API, including unused options; translate the source `lime` color to Anytwo’s native `green`.
- Render images with native Markdown. Clean technical filename prefixes, preserve original names/extensions and reuse library files only after matching normalized name, size and SHA-256 content. Share transferred assets across pages within the same destination space.
- Preserve intentional empty paragraphs and pixel image widths. Approximate relative image widths against a 720 px block reference, with an explicit report warning.
- Add an optional, disabled-by-default chat archive import: one page per chat in the source space, grouped by day, with authors, timestamps, edits, replies, reactions and optional attachments. Chats remain excluded from ordinary object/type import; no messages are posted to Anytwo chats.
- Check chat-history pagination and completeness before destination writes. Include archives in the preview and JSON report.
- Hide linked-object inclusion for whole-space imports and exclude destination spaces explicitly marked deleted, removed or left.
- Reuse native view hosts and collection sources. Refuse unsupported filters, ambiguous properties and unconvertible active views instead of silently broadening results.
- Validation: **137 automated tests pass**, including regression and simulated HTTP integration coverage; targeted source/API and installed-client checks were also performed.

**Limits:** this remains an experimental preview. Simple imports create new copies; synchronization and automatic rollback are unavailable. Inline tables may be adapted to lists, collection column widths remain local client settings, and unsupported presentation settings are archived with warnings. These changes improve future imports; existing imports are not repaired automatically.

### Français

Version expérimentale axée sur la fidélité à la source et les collections/vues natives d’Anytwo.

- Import des queries et collections intégrées comme vues en ligne natives, avec conservation des filtres et tris compatibles. Inclusion récursive des documents correspondants si le suivi des éléments liés est activé, avec le même périmètre dans la simulation.
- Configuration de la véritable vue par défaut des collections : propriétés visibles/masquées, ordre des colonnes et tri par date de création Anytype d’origine.
- Propriétés des membres portées directement par les supertags de leurs collections. Supertags de type en repli hors collection importée ; suppression des appartenances Page redondantes et des propriétés suffixées artificielles. Conservation des pages de navigation des collections imbriquées et de leurs appartenances parentes.
- Lecture des options et couleurs de select via l’API Anytype v2, y compris les options inutilisées ; conversion du vert source `lime` vers le vert natif Anytwo `green`.
- Images en Markdown natif. Nettoyage des préfixes techniques, conservation des noms/extensions d’origine et réutilisation des fichiers de bibliothèque après correspondance du nom normalisé, de la taille et du SHA-256. Fichiers transférés partagés entre pages d’un même espace cible.
- Conservation des paragraphes vides et des largeurs d’images en pixels. Approximation des largeurs relatives sur un bloc de référence de 720 px, signalée dans le rapport.
- Option d’archivage des chats désactivée par défaut : une page par chat de l’espace source, regroupement par jour, auteurs, dates, modifications, réponses, réactions et pièces jointes facultatives. Chats exclus de l’import ordinaire des objets/types ; aucun message publié dans les chats Anytwo.
- Contrôle de la pagination et de l’exhaustivité des historiques avant toute écriture cible. Archives incluses dans la simulation et le rapport JSON.
- Option des éléments liés masquée pour un espace entier et exclusion des espaces cibles explicitement supprimés, retirés ou quittés.
- Réutilisation des hôtes de vues et collections sources natifs. Refus des filtres non pris en charge, propriétés ambiguës et vues actives non convertibles, sans élargissement silencieux des résultats.
- Validation : **137 tests automatisés réussis**, dont des régressions et intégrations HTTP simulées ; vérifications ciblées des données/API sources et du client installé également effectuées.

**Limites :** cette version reste expérimentale. L’import simple crée de nouvelles copies ; synchronisation et annulation automatique indisponibles. Les tables intégrées peuvent être adaptées en listes, les largeurs de colonnes restent locales au client et les réglages de présentation non transposables sont archivés avec avertissement. Ces changements améliorent les prochains imports ; les copies existantes ne sont pas réparées automatiquement.

## 0.9.2 — 2026-10-29 — Import fidelity improvements

### English

- Restore page emoji icons using Anytwo’s native icon property, and upload image icons as page metadata.
- Import collapsible text and heading blocks as native toggles, preserving nested content.
- Rebuild block columns using Anytwo’s native column format, retaining source widths and nested content without duplication.
- Preserve interactive checkboxes and their checked state inside tables.
- Import audio attachments as native file links recognized by Anytwo’s audio player.
- Resolve original attachment filenames and extensions from Anytype metadata, and use them for both uploads and document links.
- Import supported YouTube URLs as native embeds, replacing the previous HTML iframe approach.
- Preserve select options, including unused options, labels, colors and declared order. Improve property identifier resolution, descriptions, date/time settings and supported relation settings.
- Convert supported collection/page views into native saved views, remapping sources, filters, sorts, groups and property references. Unsupported or ambiguous filters reject the view instead of silently broadening its results.
- Archive source view layouts and property settings that have no safely supported equivalent, with explicit import warnings. Saved views are linked from the source position; interactive inline placement is not implemented.
- Remove visible underline/subscript/superscript HTML tags from ordinary text while preserving their content and reporting the formatting loss. Underline remains supported in HTML table cells; code stays literal. Text and background colors remain limited by Anytwo.
- Add regression and simulated HTTP integration coverage: 80 automated tests pass. Native rich-content formats were also checked against the installed client’s parser; the project owner verified the reported fixes in Anytwo.

### Français

- Rétablissement des icônes emoji des pages via la propriété native Anytwo et transfert des icônes images comme métadonnées de page.
- Import des textes et titres repliables en toggles natifs, avec leur contenu imbriqué.
- Reconstruction des colonnes de blocs dans le format natif Anytwo, avec les largeurs sources et les contenus imbriqués, sans duplication.
- Conservation des cases à cocher interactives et de leur état dans les tableaux.
- Import des pièces jointes audio sous forme de liens de fichiers natifs reconnus par le lecteur audio Anytwo.
- Recherche du nom et de l’extension d’origine des pièces jointes dans les métadonnées Anytype, puis réutilisation pour le téléversement et les liens du document.
- Import des URL YouTube prises en charge comme intégrations natives, en remplacement de l’ancienne approche par iframe HTML.
- Conservation des options de sélection, y compris les options inutilisées, libellés, couleurs et ordre déclaré. Amélioration de la résolution des propriétés, des descriptions, des réglages date/heure et des paramètres de relation pris en charge.
- Conversion des vues de collections/pages compatibles en vues enregistrées natives, avec remappage des sources, filtres, tris, groupes et références de propriétés. Un filtre inconnu ou ambigu fait refuser la vue au lieu d’élargir silencieusement ses résultats.
- Archivage des dispositions de vues et paramètres de propriétés sans équivalent sûr, avec avertissements explicites. Les vues enregistrées sont liées depuis leur emplacement source ; le placement interactif en ligne n’est pas implémenté.
- Suppression des balises HTML visibles de soulignement, indice et exposant dans le texte ordinaire, avec conservation du contenu et signalement de la perte de mise en forme. Le soulignement reste pris en charge dans les cellules HTML ; le code reste littéral. Les couleurs de texte et de fond restent limitées par Anytwo.
- Ajout de tests de régression et d’intégration HTTP simulée : 80 tests automatisés passent. Les formats de contenu enrichi ont aussi été vérifiés avec le parseur du client installé ; le propriétaire du projet a vérifié les corrections signalées dans Anytwo.
