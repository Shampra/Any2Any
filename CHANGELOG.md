# Changes / Modifications

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
