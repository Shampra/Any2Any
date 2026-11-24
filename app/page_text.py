"""Text the importer writes inside pages, in every interface language.

The interface is translated in the browser, but page content is written by the
Python engine before any display, so those sentences need their own catalog.
Keys are stable identifiers; each entry holds French, English and German.
"""

LANGUAGES = ('fr', 'en', 'de')

TEXTS = {
    # Anytype page notices.
    'notice.table_skipped': (
        'Attention : tableau non importé',
        'Warning: table not imported',
        'Hinweis: Tabelle nicht importiert'),
    'notice.file_skipped': (
        'Attention : fichier non importé : {name}',
        'Warning: file not imported: {name}',
        'Hinweis: Datei nicht importiert: {name}'),
    'notice.content_unreadable': (
        'Attention : contenu non importable (structure des blocs non reconnue).',
        'Warning: content could not be imported (unrecognized block structure).',
        'Hinweis: Inhalt konnte nicht importiert werden (unbekannte Blockstruktur).'),
    'notice.link_not_rebuilt': (
        'Attention : lien vers « {name} » non reconstruit.',
        'Warning: link to “{name}” could not be rebuilt.',
        'Hinweis: Link auf „{name}“ konnte nicht neu erstellt werden.'),
    'notice.bookmark_no_url': (
        'Attention : bookmark sans URL exploitable.',
        'Warning: bookmark without a usable URL.',
        'Hinweis: Lesezeichen ohne verwendbare URL.'),
    'notice.toc_dynamic': (
        'Attention : table des matières dynamique non importée.',
        'Warning: dynamic table of contents not imported.',
        'Hinweis: Dynamisches Inhaltsverzeichnis nicht importiert.'),
    'notice.property_block': (
        'Attention : propriété intégrée non reproduite : {field}.',
        'Warning: inline property not reproduced: {field}.',
        'Hinweis: Eingebettete Eigenschaft nicht übernommen: {field}.'),
    'notice.property_block_value': (
        'Valeur source : {value}',
        'Source value: {value}',
        'Quellwert: {value}'),
    'notice.secondary_views': (
        'Attention : certaines vues secondaires n’ont pas été converties.',
        'Warning: some secondary views were not converted.',
        'Hinweis: Einige sekundäre Ansichten wurden nicht konvertiert.'),
    'notice.views': (
        'Attention : certaines vues n’ont pas été converties ; définition source conservée dans le rapport.',
        'Warning: some views were not converted; the source definition is kept in the report.',
        'Hinweis: Einige Ansichten wurden nicht konvertiert; die Quelldefinition bleibt im Bericht.'),
    'notice.collection_view': (
        'Attention : collection ou vue intégrée non importée.',
        'Warning: inline collection or view not imported.',
        'Hinweis: Eingebettete Sammlung oder Ansicht nicht importiert.'),
    'notice.table_complex': (
        'Attention : tableau complexe non importé.',
        'Warning: complex table not imported.',
        'Hinweis: Komplexe Tabelle nicht importiert.'),
    'notice.embed': (
        'Attention : contenu intégré non importé.',
        'Warning: embedded content not imported.',
        'Hinweis: Eingebetteter Inhalt nicht importiert.'),
    'notice.block_unsupported': (
        'Attention : bloc non pris en charge (« {type} »).',
        'Warning: unsupported block (“{type}”).',
        'Hinweis: Nicht unterstützter Block („{type}“).'),
    'notice.bookmark_not_imported': (
        'Attention : bookmark non importé : URL introuvable.',
        'Warning: bookmark not imported: no URL found.',
        'Hinweis: Lesezeichen nicht importiert: keine URL gefunden.'),
    'notice.source_file': (
        'Attention : fichier source non importé.',
        'Warning: source file not imported.',
        'Hinweis: Quelldatei nicht importiert.'),
    'notice.dynamic_views': (
        'Attention : les vues ou requêtes dynamiques de cet objet n’ont pas été reproduites.',
        'Warning: this object’s dynamic views or queries were not reproduced.',
        'Hinweis: Die dynamischen Ansichten oder Abfragen dieses Objekts wurden nicht übernommen.'),
    'notice.missing_links': (
        'Attention : certains liens renvoient à des objets Anytype non importés.',
        'Warning: some links point to Anytype objects that were not imported.',
        'Hinweis: Einige Links verweisen auf nicht importierte Anytype-Objekte.'),
    'notice.partial_properties': (
        'Attention : certaines propriétés ou parties de cet objet n’ont pas été importées.',
        'Warning: some properties or parts of this object were not imported.',
        'Hinweis: Einige Eigenschaften oder Teile dieses Objekts wurden nicht importiert.'),
    'notice.rich_rejected': (
        'Attention : présentation riche non reproduite.',
        'Warning: rich layout not reproduced.',
        'Hinweis: Aufwendiges Layout nicht übernommen.'),
    'notice.content_failed': (
        'Attention : le contenu original n’a pas pu être transféré. Consultez le rapport de migration.',
        'Warning: the original content could not be transferred. See the migration report.',
        'Hinweis: Der Originalinhalt konnte nicht übertragen werden. Siehe Migrationsbericht.'),
    # Page labels.
    'label.embed': (
        'Contenu intégré',
        'Embedded content',
        'Eingebetteter Inhalt'),
    'label.embed_processor': (
        'Contenu intégré {processor}',
        'Embedded {processor} content',
        'Eingebetteter Inhalt ({processor})'),
    'label.youtube': (
        'Vidéo YouTube',
        'YouTube video',
        'YouTube-Video'),
    'label.cover': (
        'Couverture de {name}',
        'Cover of {name}',
        'Titelbild von {name}'),
    'label.cover_short': (
        'Couverture',
        'Cover',
        'Titelbild'),
    'label.linked_object': (
        'Objet lié',
        'Linked object',
        'Verknüpftes Objekt'),
    'label.view': (
        'Vue : {name}',
        'View: {name}',
        'Ansicht: {name}'),
    'label.toc_links': (
        'Sommaire · {links}',
        'Contents · {links}',
        'Inhalt · {links}'),
    'label.toc_empty': (
        'Sommaire : aucun titre accessible.',
        'Contents: no reachable heading.',
        'Inhalt: keine erreichbare Überschrift.'),
    'label.toc_too_many': (
        'Sommaire : trop de titres pour être regroupés dans un bloc.',
        'Contents: too many headings to group into one block.',
        'Inhalt: zu viele Überschriften für einen Block.'),
    # Chat archives.
    'chat.title': (
        'Archive du chat **{name}** — {count} message(s).',
        'Chat archive **{name}** — {count} message(s).',
        'Chat-Archiv **{name}** — {count} Nachricht(en).'),
    'chat.intro': (
        'Les auteurs et dates ci-dessous proviennent d’Anytype. Cette page est une archive, pas une conversation active.',
        'The authors and dates below come from Anytype. This page is an archive, not an active conversation.',
        'Die folgenden Autoren und Daten stammen aus Anytype. Diese Seite ist ein Archiv, kein aktives Gespräch.'),
    'chat.unknown_date': (
        'Date inconnue',
        'Unknown date',
        'Unbekanntes Datum'),
    'chat.unknown_author': (
        'Auteur inconnu',
        'Unknown author',
        'Unbekannter Autor'),
    'chat.edited': (
        'modifié le {stamp}',
        'edited on {stamp}',
        'bearbeitet am {stamp}'),
    'chat.reply': (
        '↪ En réponse à {target}',
        '↪ In reply to {target}',
        '↪ Als Antwort auf {target}'),
    'chat.reply_missing': (
        'un message absent de cet historique ({id})',
        'a message missing from this history ({id})',
        'eine in diesem Verlauf fehlende Nachricht ({id})'),
    'chat.attachment': (
        'Pièce jointe',
        'Attachment',
        'Anhang'),
    'chat.attachment_unavailable': (
        'Pièce jointe indisponible : {name}',
        'Attachment unavailable: {name}',
        'Anhang nicht verfügbar: {name}'),
    'chat.attachment_missing': (
        'Pièce jointe non importée : {name}',
        'Attachment not imported: {name}',
        'Anhang nicht importiert: {name}'),
    'chat.object_missing': (
        'Objet lié non importé : {name} ({id})',
        'Linked object not imported: {name} ({id})',
        'Verknüpftes Objekt nicht importiert: {name} ({id})'),
    'chat.reactions': (
        'Réactions : {list}',
        'Reactions: {list}',
        'Reaktionen: {list}'),
    'chat.empty': (
        'Ce chat ne contient aucun message.',
        'This chat has no message.',
        'Dieser Chat enthält keine Nachricht.'),
}


def language(value):
    """Normalize a plan/settings language code, defaulting to French."""
    code = str(value or 'fr').strip().lower()[:2]
    return code if code in LANGUAGES else 'fr'


_ACTIVE = 'fr'


def activate(value):
    """Select the language of the import currently running.

    Page content is produced by many helpers that carry no language of their
    own. The server runs one import at a time, so the engine sets the active
    language once per run instead of threading it through every renderer.
    """
    global _ACTIVE
    _ACTIVE = language(value)


def active():
    return _ACTIVE


def page_text(key, lang=None, **fields):
    entry = TEXTS[key]
    template = entry[LANGUAGES.index(active() if lang is None else language(lang))]
    return template.format(**fields) if fields else template


def notice(key, lang=None, **fields):
    """A blockquote warning; quotes are written without inline markup."""
    return '> ' + page_text(key, lang, **fields)
