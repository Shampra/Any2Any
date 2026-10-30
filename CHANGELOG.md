# Changes / Modifications

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
