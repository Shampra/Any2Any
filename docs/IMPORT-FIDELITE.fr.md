# Fidélité des imports Anytype

**[Français](IMPORT-FIDELITE.fr.md) · [English](IMPORT-FIDELITE.en.md)**

Ce document décrit le comportement actuel du convertisseur. Le [guide d’utilisation Anytype](NOTES-TECHNIQUES.fr.md) présente la sélection et les accès. Le [changelog](../CHANGELOG.md) conserve l’historique des changements.

## Propriétés et collections

Les membres d’une collection source reçoivent le supertag de la collection cible. Les propriétés sont écrites dans cette collection. Un supertag de type sert de repli aux objets hors collection lorsque leurs propriétés le nécessitent. Une propriété globale source peut être portée par plusieurs collections cibles sans devenir plusieurs identités source.

Les colonnes déclarées sans valeur sont créées. Les options de choix utilisent les libellés et couleurs du vocabulaire source. `lime` est normalisé vers `green` et `gray` vers `grey`. Lorsqu’une colonne cible existe, les différences de paramètres ou de couleurs sont signalées. Les options manquantes peuvent être ajoutées.

Les paramètres compatibles, notamment la présence d’heure et les options de choix, sont transposés. Les paramètres non appliqués sont archivés dans `xFormat.any2any.sourceSettings` avec un avertissement. Les restrictions de relations sont appliquées seulement lorsque leurs types cibles sont résolus.

Une date avec heure est stockée dans un descripteur datetime, même si la source annonce une simple date. Ce choix est effectué avant l’écriture des valeurs et préserve les tris. Les dates système source nécessaires aux vues sont conservées dans des colonnes distinctes des nouvelles dates de création de la destination.

Les propriétés fichiers/images ne deviennent pas des colonnes texte. Lorsque la récupération est activée, leur contenu est ajouté au début de la page sous le libellé de la propriété. Les images utilisent leur rendu intégré et les autres fichiers un lien de pièce jointe. Cette adaptation figure au bilan.

La comptabilité interne d’Anytype (`source_object`, `template_name_prefill_type` et les autres champs système de la liste interne) n’est jamais importée comme colonne. Ces clés sont reconnues par identifiant, jamais par libellé ni par préfixe : une propriété utilisateur nommée `template_notes`, dont la clé est un identifiant généré, reste importée. Un réglage de template non transposable est signalé dans le bilan.

## Liens et fichiers

Les liens de collections ciblent directement les collections Anytwo. Les collections ne sont pas dupliquées en pages de navigation. Les mentions deviennent des liens inline vers les objets importés. La réécriture des liens internes retire les paramètres et échappements de l’adresse Anytype d’origine.

Les fichiers liés comme objets source sont reconnus, y compris les PDF. Le nom et l’extension sont recherchés dans les métadonnées avant le transfert. Le préfixe technique d’import est retiré lorsqu’il est identifiable et qu’un nom lisible le suit. Les noms constitués uniquement d’un hash sont conservés. Le type MIME CSV est explicitement envoyé comme `text/csv`.

La bibliothèque de fichiers cible est lue une fois par import. La réutilisation d’un fichier existant vérifie le nom normalisé, la taille et le SHA-256 des octets. Les variantes et miniatures sont exclues. Un même fichier source référencé par plusieurs pages réutilise le même transfert dans cet espace. Le bilan détaille les transferts et réutilisations.

Les images emploient le Markdown natif et leurs largeurs en pixels utilisent le marqueur `any:image-width`. Les largeurs relatives sont approximées sur une référence de 720 px, avec le minimum natif de 96 px et un avertissement. Le résultat n’est pas proportionnel à toutes les tailles de fenêtre.

## Vues

Les collections sélectionnées et celles référencées par des vues sont résolues avant la création des pages. Une collection référencée archivée côté source peut recevoir ses propres vues compatibles. Les configurations de collection sont stockées dans les datasets natifs `dataviews` et `views`, avec la table `default` et ses vues ordonnées.

Les filtres ET/OU imbriqués, comparaisons simples, comparaisons de select simple, conditions de vide compatibles, listes `in`/`not_in`/`all_in`, présence et comparaisons texte compatibles sont remappés. Les options et références sont remplacées par leurs identifiants cible. Les tris ascendants/descendants, regroupements, propriétés visibles et ordre des colonnes sont repris lorsque leur configuration est transposable.

Les conditions inconnues, dates relatives, filtres contextuels, tris personnalisés ou règles de vide incompatibles provoquent un refus explicite de la vue concernée. La vue active n’est pas remplacée silencieusement par une vue moins filtrée. Les définitions et erreurs restent dans le bilan JSON.

Les vues inline utilisent l’enveloppe `any:block` de type `inline-view`. Leur configuration principale est stockée sous `<instance>.list`, avec la source, les filtres et le tri dans `query.anyUi`. Elles réutilisent leur collection source ou la collection représentant leur type source. Une source composée de plusieurs collections est refusée.

Les versions compatibles d’Anytwo acceptent les dispositions table et kanban inline. Les clients plus anciens peuvent utiliser une liste de remplacement. Les regroupements et les vues secondaires gardent les limites propres au client. Une collection cible préexistante contenant des objets hors périmètre ne sert pas à élargir silencieusement les résultats d’une vue importée.

Les réglages de largeur, d’ordre manuel et de présentation non appliqués sont archivés dans `layoutSettings.any2any.sourceView`. Les vues, propriétés et valeurs de la collection restent distinctes de la liste de colonnes visibles dans un affichage particulier.

## Templates et sommaires

Les templates des types concernés et ceux explicitement référencés par les vues de collection sont lus dans l’API source. Ils deviennent des templates natifs Anytwo avec leur contenu, leur icône, leurs propriétés et leurs collections. Une collection vide peut également recevoir son template.

Le défaut de la vue active prend priorité sur le défaut du type. Anytwo conserve un défaut par collection. Des défauts concurrents ou des défauts différents selon les vues sont signalés. Un défaut déjà présent dans une collection cible existante est conservé lorsqu’il diffère.

Sur les versions compatibles, les sommaires de premier niveau deviennent des blocs dynamiques `table-of-contents`. Les sommaires imbriqués sont adaptés en liens statiques vers les identifiants réels des titres. Le bilan signale l’absence de mise à jour automatique dans ce cas.

## Blocs, mise en forme et médias

Les toggles et titres repliables utilisent les marqueurs natifs `any:collapsible`. Les colonnes utilisent `any:columns` et `any:column`, avec leur contenu imbriqué. Une disposition mal formée conserve son contenu en séquence avec avertissement. Les tableaux conservent leurs cellules et leurs cases à cocher. Les paragraphes vides utilisent un caractère sans largeur afin d’éviter leur fusion par le Markdown.

Les vidéos YouTube utilisent une enveloppe native `embed`. Les fichiers audio utilisent les liens de fichiers reconnus par le lecteur du client. Les icônes utilisent la propriété universelle `any.icon`, avec un emoji ou une référence de fichier. Les bookmarks enrichis deviennent des liens titrés.

Le client Anytwo actuel interprète ces marqueurs natifs, même lorsque le serveur les stocke en blocs `html`. Ils sont transmis sans nettoyage global : les retirer ferait perdre la structure des colonnes, les vues en ligne, les propriétés intégrées, les légendes et la synchronisation des blocs. Les éléments réellement non pris en charge restent adaptés individuellement et signalés dans le bilan.

Le soulignement dépend du support Markdown de la version Anytwo. Les couleurs de texte, de fond, de blocs, de cellules et de callouts, l’alignement et les mises en page avancées avec vues dans des callouts ou colonnes restent des limites. Les balises de code sont conservées littéralement, y compris à l’intérieur des blocs de code.

## Widgets et chats

Les widgets basés sur une page ou une collection importée sont ajoutés à l’Overview partagé dans l’ordre source. Link reste Link et les autres modes deviennent Views. Les sections et entrées système, dont Recently edited, sont ignorées. Les doublons de cible entre widgets partagés et personnels sont évités.

Les chats et discussions sont exclus de l’import ordinaire. L’option d’archives lit les chats exposés par l’API de l’espace et produit une page par chat, avec auteurs, dates, réponses, modifications, réactions et fichiers selon les options. Les messages deviennent du contenu d’archive. La lecture utilise la pagination par curseur et un historique incomplet provoque un arrêt avant les écritures de destination.

## Références et validation

La suite de tests utilise des sources et destinations simulées. Des relectures d’API, rejeux de conversion et vérifications ciblées du parseur du client complètent cette validation. Le rendu doit être vérifié pour les formats et versions utilisés.

- [API Anytype v2](https://developers.anytype.io/docs/reference/v2/)
- [Format AnyBlock v2](https://github.com/anyproto/any-block/blob/main/format/v2/SPEC.md)
- [API HTTP Anytwo](https://docs.any.org/reference/http-api.html)
- [Lecture et filtres Anytwo](https://docs.any.org/database/reading-data.html)
- [Éditeur Anytwo](https://docs.any.org/types/editor.html)
