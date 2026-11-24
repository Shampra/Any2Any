"""Opt-in Anytype v2 -> Anytwo v1 import. Never mutates the source.

Conservative by design: no silent drops, no destructive target operations, no
false 'success' if properties/content fail. Values need mapping by *id* after
creation; links are resolved only after all target objects have been created.
"""
from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timezone
import hashlib
from copy import deepcopy
from rich_content import (ImportedFile, inline_html, native_columns, native_toggle,
                          descendant_end, rebase, depth as block_depth, youtube_markdown,
                          file_html, file_anchor_html, checkbox_html, remove_unsupported_inline, image_markdown,
                          image_width, legacy_markup, envelopes_supported)
from file_transfer import FileLibrary, strip_import_prefix
from view_conversion import (choice_options, enrich_descriptor, ViewConverter,
                             create_saved_views, modify_records, UnsupportedView)
from source_views import SourceViews, source_value, MISSING, is_recent_widget_document, is_recent_widget_block, RECENT_WIDGET_TARGETS
from inline_views import instance_id, inline_markdown, inline_records, property_names
from anytype_templates import Templates, is_template
import html
import json
import mimetypes
import re
import unicodedata
from urllib.parse import quote, unquote, urlparse, parse_qs

from api_clients import APIError, anytype_download, anytype_property_definitions
from anytwo_backend import (
                         create_space, create_collection, create_object, list_columns,
                         add_column, set_column_value, set_markdown, append_markdown,
                         attach_file, get_file_info, create_editor_block, add_membership,
                         delete_column, target_write, local_get, _segment)
from chat_archives import histories as chat_histories, markdown as chat_markdown
from page_text import page_text, notice, activate, language
from logic import identify_links, INTRINSIC_PROPERTIES, is_conversation, INLINE_MENTION_RE

MAX_OBJECTS = 500
SYSTEM = {x.replace('-', '_').replace(' ', '_').casefold() for x in INTRINSIC_PROPERTIES}
SYSTEM |= {'creation_date', 'last_modified_date', 'created_date', 'last_modified_by', 'created_by', 'last_opened_date', 'added_date', 'last_edited_by', 'last_edited_time'}
SYSTEM |= {'id', 'type', 'object_type', 'layout', 'icon', 'cover', 'description', 'name',
           'created_at', 'modified_at', 'created_by', 'modified_by', 'last_modified_by',
           'last_modified_date', 'creator', 'author', 'revision', 'space_id', 'workspace_id',
           'backlinks', 'links', 'internal_key', 'last_opened_date',
           'resolved_layout', 'origin', 'created_in_context', 'created_in_context_ref',
           'layout_align', 'is_archived', 'sync_status', 'import_type',
           'image_kind', 'participant_permissions', 'participant_status'}
SYSTEM |= {'source_object', 'sourceobject'}
TEXT = {'paragraph':'', 'heading_1':'# ', 'heading_2':'## ', 'heading_3':'### ',
        'quote':'> ', 'bulleted_list_item':'- ', 'numbered_list_item':'1. '}
KNOWN_UNSUPPORTED = {
    'dataview': 'Collection / vue intégrée',
    'table_of_contents': 'Table des matières',
    'property': 'Propriété intégrée à la page',
    'bookmark': 'Bookmark enrichi',
}
FILE_TYPES = {'image', 'file', 'video', 'audio', 'pdf'}

# Anytype can return application/octet-stream (or a similarly generic MIME)
# even for a recognizable CSV. In that case Anytwo may treat it as an untyped
# document. The file name is just as important: the Anytwo server uses the
# extension to refine generic and text/plain content types.
GENERIC_MIMES = {
    '', 'application/octet-stream', 'binary/octet-stream',
    'application/x-octet-stream', 'application/x-binary',
    'application/unknown', 'application/download',
}


def normalized_mime(value):
    if isinstance(value, dict):
        value = value.get('mime_type') or value.get('mime') or value.get('media')
    return str(value or '').split(';', 1)[0].strip().casefold()


def safe_filename(value):
    """Keep the original extension and remove only path/control characters."""
    if not isinstance(value, str):
        return ''
    name = value.strip().replace('\\', '/').rsplit('/', 1)[-1].strip()
    name = ''.join(ch for ch in name if ch >= ' ' and ch != '\x7f')
    return name[:240] if name not in ('.', '..') else ''


def has_file_extension(filename):
    last = safe_filename(filename).rsplit('.', 1)
    return len(last) == 2 and bool(last[0]) and 1 <= len(last[1]) <= 12 and last[1].isalnum()


def file_metadata(doc):
    if not isinstance(doc,dict):return '', ''
    props=doc.get('properties') if isinstance(doc.get('properties'),dict) else {}
    aliases=doc.get('property_internal_keys') or {}
    normalized={}
    for data in (props,doc):
        for key,value in data.items():
            if isinstance(value,dict):value=value.get('text') or value.get('value')
            normalized[re.sub('[^a-z0-9]','',str(aliases.get(key) or key).casefold())]=value
    name=''
    for key in ('filename','originalfilename','originalname','name'):
        value=normalized.get(key)
        if isinstance(value,str) and value.strip():
            candidate=safe_filename(value)
            if not name or has_file_extension(candidate):name=candidate
            if has_file_extension(name):break
    mime=''
    for key in ('mimetype','filemimetype','mime','media'):
        candidate=normalized_mime(normalized.get(key))
        if candidate and candidate not in GENERIC_MIMES:mime=candidate;break
    ext=str(normalized.get('extension') or normalized.get('fileext') or normalized.get('fileextension') or '').strip().lstrip('.')
    if name and re.fullmatch('[a-zA-Z0-9]{1,12}',ext) and not name.casefold().endswith('.'+ext.casefold()):name+='.'+ext
    if normalized.get('origin') in ('clipboard','import','imported'):
        name=strip_import_prefix(name)
    return name,mime


def resolve_file_mime(filename, declared=None, downloaded=None):
    """Choose a MIME without changing other formats that already work.

    For .csv, always use text/csv: Windows/Anytype may call it text/plain,
    application/vnd.ms-excel or application/octet-stream. For other file
    types keep a specific MIME provided by Anytype; correct only a generic
    response via the original extension.
    """
    if filename.casefold().endswith('.csv'):
        return 'text/csv'
    declared = normalized_mime(declared)
    downloaded = normalized_mime(downloaded)
    if declared not in GENERIC_MIMES:
        return declared
    if downloaded not in GENERIC_MIMES:
        return downloaded
    guessed = normalized_mime(mimetypes.guess_type(filename)[0])
    return guessed if guessed not in GENERIC_MIMES else 'application/octet-stream'


def slug(value, suffix=''):
    text = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower()
    text = re.sub(r'[^a-z0-9]+', '_', text).strip('_')[:40] or 'import'
    return (text + ('_' + hashlib.sha1(str(suffix).encode()).hexdigest()[:7] if suffix else ''))[:63]


def display(doc, fallback):
    props = doc.get('properties') or {}
    name = props.get('name') if isinstance(props, dict) else None
    return str(name or doc.get('name') or fallback)


# Anytype stores its own record bookkeeping in the same property map as user
# values. These keys describe the record itself (import provenance, template
# prefill, cover geometry...) rather than user data, so importing them only
# creates junk columns. Matching is by identifier, never by user label.
INTERNAL_RECORD_PROPERTIES = frozenset({
    'import_type', 'source_object', 'template_name_prefill_type',
    'unique_key', 'default_template_id', 'default_type_id', 'default_view_type',
    'size_in_bytes', 'deletion_change_id', 'internal_flags',
    'featured_relations', 'recommended_relations', 'recommended_featured_relations',
    'recommended_hidden_relations', 'recommended_file_relations', 'recommended_layout',
    'header_relations_layout', 'set_of', 'order_id',
    'cover_id', 'cover_type', 'cover_x', 'cover_y', 'cover_scale',
    'icon_name', 'icon_option', 'plural_name', 'layout_width',
})
def internal_record_property(identifier):
    """True for Anytype record bookkeeping keys that are never user columns.

    Matching is by the explicit set of identifiers Anytype itself declares.
    User property keys are generated ids and may share a display label with a
    system field, so a `template_` prefix is never a signal of system origin.
    """
    key = str(identifier or '').replace('-', '_').replace(' ', '_').casefold()
    return bool(key) and key in INTERNAL_RECORD_PROPERTIES


def import_artifacts(doc, vocabulary=None):
    """Labels of bookkeeping properties present in a source document.

    Only identifiers Anytype itself declares are returned, so a same-named
    user column is never reported as an artifact.
    """
    props = doc.get('properties')
    if not isinstance(props, dict): return {}
    aliases = doc.get('property_internal_keys') or {}
    found = {}
    for key in props:
        if not internal_record_property(key): continue
        internal = str(aliases.get(key) or key)
        meta = (vocabulary or {}).get(internal.casefold()) or {}
        found[str(meta.get('name') or internal)] = internal
    return found


def internal_property(name, vocabulary=None, doc=None):
    """Exclude documented system keys and explicitly hidden Anytype metadata.

    Never use a generic `unknown` format as a reason to discard user data.
    """
    key = str(name).replace('-', '_').replace(' ', '_').casefold()
    alias = (doc or {}).get('property_internal_keys') or {}
    internal = str(alias.get(name) or '').replace('-', '_').casefold()
    if key in SYSTEM or internal in SYSTEM:
        return True
    vocab = vocabulary or {}
    meta = vocab.get(key) or vocab.get(internal) or {}
    if not isinstance(meta, dict):
        return False
    if any(meta.get(flag) is True for flag in ('hidden','is_hidden','isHidden',
                                             'system','is_system','isSystem',
                                             'internal','is_internal','isInternal')):
        return True
    return str(meta.get('internal_key') or '').casefold() in SYSTEM


def custom_properties(doc, vocabulary=None):
    props = doc.get('properties')
    if not isinstance(props, dict): return {}
    return {str(key): value for key, value in props.items()
            if not internal_record_property(key) and not internal_property(key, vocabulary, doc)
            and value is not None}


def is_bookmark(obj, doc=None):
    # API builds sometimes expose the layout instead of a built-in Type label.
    source=obj or {}; detail=doc or {}
    raw=source.get('raw') if isinstance(source.get('raw'),dict) else {}
    return any(str(value or '').casefold() in ('bookmark','bookmarks') for value in (
        source.get('type'),source.get('layout'),detail.get('type'),
        detail.get('layout'),raw.get('type'),raw.get('layout')))



def bookmark_url(doc):
    props = doc.get('properties') or {}
    for mapping in (props, doc):
        if not isinstance(mapping, dict): continue
        for key, value in mapping.items():
            if key.casefold() in ('url', 'source', 'source_url', 'link', 'web_url'):
                if isinstance(value,dict):
                    value=value.get('value') or value.get('url') or value.get('link')
                if isinstance(value, str) and value.strip().startswith(('https://','http://')):
                    return value.strip()
    return None


def mapped_relation(value, mapping):
    """any://<objectId> references for imported objects, or None if one is missing."""
    values = value if isinstance(value, list) else [value]
    if not values or not all(isinstance(v, str) and v in mapping for v in values):
        return None
    return ['any://' + mapping[v] for v in values]

def relation_references(value, mapping):
    """any:// references from a stored value (URI, raw id, or a JSON list).

    Returns None when a reference was never imported, so callers can skip the
    write instead of sending a value the destination will reject.
    """
    items=value
    if isinstance(value,str):
        text=value.strip()
        if text.startswith('['):
            try:items=json.loads(text)
            except ValueError:items=[value]
        else:items=[value]
    if not isinstance(items,(list,tuple)) or not items:return None
    refs=[]
    for item in items:
        if not isinstance(item,str):return None
        if item.startswith('any://'):refs.append(item)
        elif item in mapping:refs.append('any://'+mapping[item])
        else:return None
    return refs
def titled_link(title, url):
    label=str(title or url).replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')
    return f'[{label}]({url})'


def select_scope(inv, plan):
    selection = plan.get('selection') or {}
    kind = selection.get('kind')
    reasons = {}
    roots = []
    selected_cols = []
    target = plan.get('target') or {}
    if kind == 'space':
        roots = inv['objects'][:]+inv['collections'][:]
        selected_cols = inv['collections'][:]
        for item in roots: reasons[item['id']] = [f'Sélectionné via l’espace « {plan["source_space"]["name"]} »']
    elif kind == 'collection':
        cid = selection.get('collection_id')
        col = next((c for c in inv['collections'] if c['id'] == cid), None)
        if not col: raise APIError('Collection source inconnue (rechargez l’espace).')
        selected_cols = [col]
        roots = inv['members'].get(cid, [])[:]
        for item in roots: reasons[item['id']] = [f'Sélectionné via la collection « {col["name"]} »']
    elif kind == 'types':
        keys = set(selection.get('type_keys') or [])
        matched = [t for t in inv['types'] if t['key'] in keys]
        if not keys or len(matched) != len(keys): raise APIError('Type source introuvable.')
        for typ in matched:
            for item in typ['items']:
                roots.append(item)
                reasons.setdefault(item['id'], []).append(f'Sélectionné via le type « {typ["name"]} »')
    elif kind == 'objects':
        ids = set(selection.get('ids') or [])
        roots = [item for item in inv['objects'] if item['id'] in ids]
        if not ids or len(roots) != len(ids): raise APIError('Objet source introuvable.')
        for item in roots: reasons[item['id']] = ['Sélectionné individuellement']
    else:
        raise APIError('Sélection source manquante.')
    unique = {}
    for item in roots: unique[item['id']] = item
    if target.get('space_mode') not in ('existing', 'create') or not target.get('space_name'):
        raise APIError('Espace cible invalide.')
    if target.get('space_mode') == 'existing' and not target.get('space_id'):
        raise APIError('ID de l’espace cible manquant.')
    return list(unique.values()), reasons, selected_cols


def discover_documents(source, sid, inv, selected, reasons, follow, view_sources=None):
    view_sources=view_sources or SourceViews(source,sid,inv)
    indexed = {item['id']:item for item in inv['all'] if not is_conversation(item)}
    # Also reference collection entities by name; they are not imported as pages.
    all_ids = {item['id'] for item in inv['all']}
    queue = deque(selected)
    docs = {}; entries = {}; problems = []
    ignored = set(RECENT_WIDGET_TARGETS)
    while queue:
        obj = queue.popleft()
        if is_conversation(obj):
            continue
        oid = obj['id']
        if oid in entries or oid in ignored: continue
        if len(entries) >= MAX_OBJECTS:
            raise APIError(f'Limite de sécurité : plus de {MAX_OBJECTS} objets dans le périmètre. Aucune écriture effectuée.')
        entries[oid] = obj
        try:
            doc = view_sources.document(oid)
            if not isinstance(doc, dict): raise APIError('Réponse objet non JSON.')
            if is_recent_widget_document(doc,obj):
                ignored.add(oid)
                entries.pop(oid)
                continue
            if is_conversation(doc):
                problems.append((oid, 'Chat / discussion ignoré (non importable)'))
                continue
            docs[oid] = doc
        except (APIError, ValueError) as e:
            problems.append((oid, f'Lecture de la source impossible : {e}'))
            continue
        structural=set()
        for block in doc.get('blocks') or []:
            if not isinstance(block,dict) or block.get('type')!='dataview':continue
            if block.get('object_id'):structural.add(block['object_id'])
            if is_recent_widget_block(block):
                continue
            try:
                # Resolve even without follow, so conversion later uses the same
                # source definition. Only follow expands the import perimeter.
                view_sources.resolve(doc,block)
                if follow:
                    for ref in view_sources.matching(doc,block):
                        if ref in view_sources.items:indexed.setdefault(ref,view_sources.items[ref])
                        if ref in indexed and ref not in entries and not any(x['id']==ref for x in queue):
                            reasons.setdefault(ref,[]).append(f'Document de la vue intégrée de « {obj["name"]} »')
                            queue.append(indexed[ref])
            except (APIError,UnsupportedView,ValueError,TypeError,KeyError) as exc:
                problems.append((oid,'Documents de vue intégrée non résolus : '+str(exc)))
        links = identify_links(doc, all_ids, oid)-structural
        for ref in sorted(links):
            if ref in ignored or ref in entries or any(x['id']==ref for x in queue): continue
            if ref not in indexed:
                problems.append((oid, f'Référence vers une collection / un objet non migrable : {ref}'))
            elif is_conversation(indexed[ref]):
                problems.append((oid, 'Lien vers un chat / une discussion non importé'))
            elif follow:
                reasons.setdefault(ref, []).append(f'Lié à « {obj["name"]} »')
                queue.append(indexed[ref])
    return entries, docs, problems


def reference_link(ref, mapping, target_sid, names):
    if ref not in mapping:
        return None
    return f'any://o/{target_sid}/{mapping[ref]}'


def replace_inline_links(text, mapping, sid, names, issues):
    # Anytype serialises inline @ mentions as HTML-like tags the client would
    # otherwise display verbatim. Both object_id and objectId are accepted.
    def mention(match):
        oid = unquote((match.group(1) or match.group(2) or '').strip())
        label = html.unescape(match.group(3)).strip() or str(names.get(oid) or oid)
        uri = reference_link(oid, mapping, sid, names)
        if not uri:
            issues.add('Mention vers un objet non importé')
            return label
        return titled_link(label, uri)
    text = INLINE_MENTION_RE.sub(mention, str(text))
    # AnyBlock inline links use Markdown with anytype://object?objectId=<id>.
    def old_url(m):
        params = parse_qs(m.group(2).replace(r'\&', '&'))
        oid = (params.get('objectId') or [''])[0]
        new = reference_link(oid, mapping, sid, names)
        if not new:
            issues.add('Lien vers un objet non importé')
            return m.group(0)
        return m.group(1) + new + ')'
    text = re.sub(r'(\]\()anytype://object\?([^\s)]+)\)', old_url, text)
    return text


def _nested_fragment(blocks, mapping=None, sid=None, names=None, issues=None,
                     files_allowed=False, file_import=None):
    pieces=[]
    issues=issues if issues is not None else set()
    mapping=mapping or {}; names=names or {}
    i=0
    while i<len(blocks):
        block=blocks[i]; i+=1
        if not isinstance(block,dict):continue
        kind=block.get('type')
        if kind=='row':
            markup,consumed=rich_columns(blocks,i-1,mapping,sid,names,issues,files_allowed,file_import)
            if markup:
                pieces.append(markup);i+=consumed-1
                continue
        original=replace_inline_links(block.get('text') or '',mapping,sid,names,issues)
        text=inline_html(original)
        if kind in ('heading_1','heading_2','heading_3'):
            level=int(kind[-1]); pieces.append(f'<h{level}>{text}</h{level}>')
        elif kind=='table':
            markup=rich_table(block,issues,mapping,sid,names,files_allowed,file_import)
            pieces.append(markup or '<p>'+page_text('notice.table_skipped')+'</p>')
        elif kind=='code':
            pieces.append('<pre><code>'+html.escape(str(block.get('text') or ''))+'</code></pre>')
        elif kind in FILE_TYPES:
            fid=str(block.get('object_id') or block.get('hash') or '')
            name=str(block.get('name') or kind)
            if files_allowed and file_import and fid:
                try:
                    imported=file_import(fid,name,block.get('mime_type'))
                    name=getattr(imported,'name',name)
                    uri=html.escape(str(imported),quote=True)
                    label=html.escape(name)
                    width=block_width(block)
                    size=f' style="width:{width}%;max-width:100%"' if width and width<=100 else f' style="width:{width}px;max-width:100%"' if width else ' style="max-width:100%"'
                    pieces.append(f'<img src="{uri}" alt="{label}"{size}>' if kind=='image' else file_anchor_html(imported,name))
                except APIError as exc:
                    issues.add('Fichier imbriqué non importé : '+str(exc))
                    pieces.append('<p>'+page_text('notice.file_skipped',name=html.escape(name))+'</p>')
            else:
                issues.add('Fichier imbriqué non importé (indisponible ou option désactivée)')
                pieces.append('<p>'+page_text('notice.file_skipped',name=html.escape(name))+'</p>')
        elif kind in ('row','column','group','table_row','table_cell'):
            nested=block.get('blocks') or block.get('children') or []
            if isinstance(nested,list):pieces.append(_nested_fragment(nested,mapping,sid,names,issues,files_allowed,file_import))
        elif kind=='divider':pieces.append('<hr>')
        elif kind in ('checkbox','check_list_item'):pieces.append(checkbox_html(text,block.get('checked',False)))
        elif kind in ('paragraph','text','quote','bulleted_list_item','numbered_list_item'):
            tag='blockquote' if kind=='quote' else 'p'
            marker='• ' if kind=='bulleted_list_item' else '1. ' if kind=='numbered_list_item' else ''
            pieces.append(f'<{tag}>{marker}{text}</{tag}>')
        else:
            # Unknown blocks retain their JSON via the normal converter, instead
            # of vanishing when their text field happens to be empty.
            md=render_blocks({'blocks':[block]},mapping,sid,names,files_allowed,file_import,issues,rich_mode=False)
            pieces.append('<div>'+inline_html(md)+'</div>')
        if block.get('background_color') or block.get('backgroundColor'):
            issues.add("Couleur d’arrière-plan de bloc")
    return ''.join(pieces)


def block_width(block):
    raw=(block.get('fields') or {}) if isinstance(block.get('fields'),dict) else {}
    style=(block.get('style') or {}) if isinstance(block.get('style'),dict) else {}
    width=block.get('width',raw.get('width',style.get('width')))
    try:
        val=float(width)
        if 0<val<=1: return max(5,min(100,int(val*100)))
        if 1<val<=2400: return int(val)
    except (ValueError,TypeError,OverflowError): pass
    return None


def rich_columns(blocks, row_index, mapping=None, sid=None, names=None, issues=None, files_allowed=False, file_import=None):
    """Read a v2 row + indented columns, returning HTML and consumed length.
    Indentation is authoritative in AnyBlock's flat block sequence.
    """
    row=blocks[row_index]
    try: base=int(row.get('indent',0))
    except (ValueError,TypeError): base=0
    last=row_index+1
    while last<len(blocks):
        try: level=int(blocks[last].get('indent',0))
        except (ValueError,TypeError,AttributeError): break
        if level<=base: break
        last+=1
    children=blocks[row_index+1:last]
    if not children: return '',1
    columns=[]
    for i,b in enumerate(children):
        if not isinstance(b,dict) or b.get('type')!='column' or int(b.get('indent',base+1))!=base+1:continue
        try: depth=int(b.get('indent',base+1))
        except (ValueError,TypeError): depth=base+1
        end=i+1
        while end<len(children):
            try: other=int(children[end].get('indent',0))
            except (ValueError,TypeError,AttributeError):break
            if other<=depth:break
            end+=1
        columns.append((b,children[i+1:end]))
    if not columns: return '',last-row_index
    count=len(columns)
    parts=[]
    for b,child in columns:
        width=block_width(b)
        if width is not None and width<=100: css=f'width:{width}%;'
        else: css=f'width:{round(100/count)}%;'
        parts.append('<td style="vertical-align:top;'+css+'">'+(_nested_fragment(child,mapping,sid,names,issues,files_allowed,file_import) or '&nbsp;')+'</td>')
    return '<table role="presentation" class="anytype-columns"><tbody><tr>'+''.join(parts)+'</tr></tbody></table>',last-row_index


def _table_cell_html(cell, issues, mapping=None, sid=None, names=None, files_allowed=False, file_import=None):
    """Keep AnyBlock v2 cell content, including compound blocks and checkboxes."""
    if cell is None:
        return ''
    if isinstance(cell, list):
        return _nested_fragment(cell,mapping,sid,names,issues,files_allowed,file_import)
    if isinstance(cell, dict):
        if cell.get('background_color') or cell.get('backgroundColor'):
            issues.add('Couleur des cellules du tableau non reproduite')
        kind = str(cell.get('type') or '')
        if kind in ('checkbox', 'check_list_item'):
            value=cell.get('text') or ''
            if mapping is not None and isinstance(value,str):
                value=replace_inline_links(value,mapping,sid,names or {},issues)
            return checkbox_html(inline_html(value),cell.get('checked',False))
        if isinstance(cell.get('blocks'), list):
            return _nested_fragment(cell['blocks'],mapping,sid,names,issues,files_allowed,file_import)
        value=cell.get('text') if cell.get('text') is not None else cell.get('value', '')
        if isinstance(value, (str,int,float,bool)):
            if mapping is not None and isinstance(value,str):value=replace_inline_links(value,mapping,sid,names or {},issues)
            return inline_html(value)
        return inline_html(json.dumps(value,ensure_ascii=False))
    if mapping is not None and isinstance(cell,str):cell=replace_inline_links(cell,mapping,sid,names or {},issues)
    return inline_html(cell)


def rich_table(block, issues, mapping=None, sid=None, names=None, files_allowed=False, file_import=None):
    """Encode the table for Anytwo, reporting specific cell conversion losses."""
    rows=block.get('rows') or []
    if not isinstance(rows,list) or not rows:return None
    columns=block.get('columns') or []
    col_html=''
    if isinstance(columns,list) and columns:
        colgroups=[]
        for col in columns:
            width=block_width(col) if isinstance(col,dict) else None
            colgroups.append('<col'+(f' style="width:{width}px"' if width and width>100 else
                                     f' style="width:{width}%"' if width else '')+'>')
        col_html='<colgroup>'+''.join(colgroups)+'</colgroup>'
    output=[]
    for ri,row in enumerate(rows):
        cells=row.get('cells',[]) if isinstance(row,dict) else row
        if not isinstance(cells,list):return None
        output.append('<tr>')
        for cell in cells:
            data=cell if isinstance(cell,dict) else {}
            tag='th' if (isinstance(row,dict) and (row.get('is_header') or row.get('isHeader'))) or (ri==0 and block.get('header')) else 'td'
            attrs=[]
            for k in ('rowspan','colspan'):
                try:
                    n=int(data.get(k,1))
                    if 1<n<100:attrs.append(f'{k}="{n}"')
                except (ValueError,TypeError):pass
            output.append(f'<{tag}'+(' '+ ' '.join(attrs) if attrs else '')+'>'+_table_cell_html(cell,issues,mapping,sid,names,files_allowed,file_import)+f'</{tag}>')
        output.append('</tr>')
    return '<table>'+col_html+'<tbody>'+''.join(output)+'</tbody></table>'


def youtube_embed(raw):
    return youtube_markdown(raw)


def bookmark_block_url(block):
    for container in (block, block.get('fields'), block.get('bookmark'), block.get('data')):
        if not isinstance(container,dict):continue
        for key in ('url','source','source_url','link','web_url'):
            value=container.get(key)
            if isinstance(value,dict):value=value.get('url') or value.get('value')
            if isinstance(value,str) and value.strip().startswith(('https://','http://')):
                return value.strip()
    return None


def bookmark_block_title(block, names, fallback):
    # Anytype's embedded bookmark block often lacks a title, but points at
    # an object whose name is returned by the space inventory.
    for field in ('title','name','caption','text'):
        value=block.get(field)
        if isinstance(value,str) and value.strip():return value.strip()
    for field in ('object_id','objectId','target_object_id','targetObjectId'):
        ref=block.get(field)
        if ref and names.get(str(ref)):return names[str(ref)]
    for nested in ('bookmark','fields','data'):
        value=block.get(nested)
        if isinstance(value,dict):
            for field in ('title','name','caption'):
                label=value.get(field)
                if isinstance(label,str) and label.strip():return label.strip()
    return fallback


def render_blocks(doc, mapping, sid, names, files_allowed, file_import, issues, rich_mode=True, native_embeds=None, keep_underline=False):
    blocks = doc.get('blocks') or []
    if not isinstance(blocks, list):
        issues.add('Structure de blocs inconnue')
        return notice('notice.content_unreadable')
    lines = []
    i=0
    while i<len(blocks):
        block=blocks[i]
        i+=1
        if not isinstance(block, dict): continue
        typ = str(block.get('type') or '')
        try: depth = min(max(0, int(block.get('indent', 0))), 12)
        except (TypeError, ValueError): depth = 0
        pad = '  '*depth
        txt = replace_inline_links(block.get('text') or '', mapping, sid, names, issues)
        if typ in TEXT or typ == 'checkbox' or typ.startswith('toggle'):
            cleaned = remove_unsupported_inline(txt, keep_underline)
            if cleaned != txt:
                issues.add('Soulignement/exposant/indice non pris en charge par l’import Markdown Anytwo : texte conservé sans balises')
            txt = cleaned
        if block.get('background_color') or block.get('backgroundColor'):
            issues.add("Couleur d’arrière-plan de bloc")
        def render_children(children):
            return render_blocks({'blocks':children},mapping,sid,names,files_allowed,file_import,issues,rich_mode=rich_mode,native_embeds=native_embeds,keep_underline=keep_underline)
        if typ in ('toggle','toggle_heading_1','toggle_heading_2','toggle_heading_3') and rich_mode:
            end=descendant_end(blocks,i-1)
            lines.append(native_toggle(block,rebase(blocks[i:end],depth+1),render_children,txt))
            i=end
        elif typ=='row' and rich_mode:
            markup,consumed=native_columns(blocks,i-1,render_children)
            if markup:
                lines.append(markup);i+=consumed-1
            else:
                issues.add('Disposition en colonnes non reconstructible : contenu conservé en séquence')
        elif typ in TEXT:
            prefix = TEXT[typ]
            if typ == 'quote': prefix = '> '
            # A blank source paragraph is intentional spacing; Markdown
            # blank lines alone collapse. A zero-width character keeps a node.
            lines.append((pad + prefix + (txt if txt else '\u200b')).rstrip())
        elif typ == 'checkbox':
            lines.append(pad + ('- [x] ' if block.get('checked') else '- [ ] ') + txt)
        elif typ in ('code',):
            lang = re.sub('[^a-zA-Z0-9_+-]', '', str(block.get('language') or ''))
            lines.append(f'```{lang}\n{block.get("text") or ""}\n```')
        elif typ in ('callout','toggle','toggle_heading_1','toggle_heading_2','toggle_heading_3'):
            if typ != 'callout': issues.add('Blocs repliables (repliage perdu)')
            symbol = (block.get('icon') or {}).get('emoji', 'ℹ️') if isinstance(block.get('icon'), dict) else 'ℹ️'
            lines.append(f'{pad}> {symbol} {txt}' if typ=='callout' else pad+'**'+txt+'**')
        elif typ == 'divider': lines.append('---')
        elif typ == 'row':
            markup,consumed=rich_columns(blocks,i-1,mapping,sid,names,issues,files_allowed,file_import) if rich_mode else ('',1)
            if markup:
                lines.append(markup)
                i+=consumed-1
                issues.add('Colonnes préservées en HTML (rendu à vérifier dans Anytwo)')
            else:
                issues.add('Disposition en colonnes simplifiée')
        elif typ in ('column','group'):
            # A column/group without its parent row cannot be reconstructed.
            issues.add('Disposition en colonnes simplifiée')
        elif typ in ('video','bookmark') and rich_mode and youtube_markdown(block.get('url') or ''):
            lines.append(youtube_markdown(block['url'],str(block.get('id') or i),page_text('label.youtube')))
        elif typ in FILE_TYPES:
            fid = str(block.get('object_id') or block.get('hash') or '')
            name = str(block.get('name') or (typ+' '+fid[:10]))
            if fid and files_allowed:
                try:
                    uri = file_import(fid, name, block.get('mime_type'))
                    name=getattr(uri,'name',name)
                    if typ=='image' and block.get('style')!='link':
                        lines.append(image_markdown(uri,name,image_width(block,uri,issues)))
                    else:lines.append(file_html(uri,name))
                except (APIError, ValueError) as e:
                    issues.add(f'Fichier indisponible : {name} ({e})')
                    lines.append(notice('notice.file_skipped',name=name)+'.')
            else:
                issues.add('Fichiers non importés'+(' (option désactivée)' if not files_allowed else ' (identifiant absent)'))
                lines.append(notice('notice.file_skipped',name=name)+'.')
        elif typ == 'link':
            oid = str(block.get('object_id') or '')
            name = names.get(oid, oid or page_text('label.linked_object'))
            uri = reference_link(oid, mapping, sid, names)
            if uri: lines.append(f'[{name}]({uri})')
            else:
                issues.add('Lien vers un objet non importé')
                lines.append(notice('notice.link_not_rebuilt',name=name))
        elif typ == 'bookmark':
            issues.add('Bookmark enrichi non reproduit')
            url = bookmark_block_url(block) or ''
            title=bookmark_block_title(block,names,url)
            lines.append(titled_link(title,url) if url else notice('notice.bookmark_no_url'))
        elif typ in ('table_of_contents','tableOfContents'):
            issues.add('Table des matières non reproduite')
            lines.append(notice('notice.toc_dynamic'))
        elif typ == 'property':
            issues.add('Propriété intégrée à la page non reproduite')
            field = block.get('key') or block.get('property') or '(inconnue)'
            value = (doc.get('properties') or {}).get(field, '')
            lines.append(notice('notice.property_block',field=field) +
                         (' '+page_text('notice.property_block_value',value=json.dumps(value, ensure_ascii=False)) if value else ''))
        elif typ == 'any2any_property':
            lines.append(block['markdown'])
        elif typ == 'any2any_toc':
            lines.append(block.get('markdown') or block['marker'])
        elif typ == 'any2any_inline_view':
            lines.append(block['markdown'])
            if block.get('failed'):lines.append(notice('notice.secondary_views'))
        elif typ == 'any2any_saved_view':
            lines.append(titled_link(page_text('label.view',name=str(block.get('name') or 'Anytype')), 'any://o/'+sid+'/'+block['target_id']))
            if block.get('failed'):
                lines.append(notice('notice.views'))
        elif typ == 'dataview':
            issues.add('Collection / vue intégrée non reproduite')
            lines.append(notice('notice.collection_view'))
        elif typ == 'table':
            markup=rich_table(block,issues,mapping,sid,names,files_allowed,file_import) if rich_mode else None
            if markup:
                lines.append(markup)
            else:
                # Rebuild what we can in Markdown without discarding text.
                rows=block.get('rows') or []
                values=[]
                for row in rows:
                    cells=row.get('cells',[]) if isinstance(row,dict) else row
                    if not isinstance(cells,list):continue
                    def cell_markdown(cell):
                        if isinstance(cell,dict) and isinstance(cell.get('blocks'),list):
                            return render_blocks({'blocks':cell['blocks']},mapping,sid,names,files_allowed,file_import,issues,rich_mode=False)
                        if isinstance(cell,list):
                            return render_blocks({'blocks':cell},mapping,sid,names,files_allowed,file_import,issues,rich_mode=False)
                        value=cell.get('text',cell.get('value','')) if isinstance(cell,dict) else cell
                        return replace_inline_links(str(value) if value is not None else '',mapping,sid,names,issues)
                    values.append([cell_markdown(c) for c in cells])
                if values:
                    width=max(len(r) for r in values)
                    for ri,row in enumerate(values):
                        lines.append('| '+' | '.join(x.replace('|','\\|').replace('\n',' ') for x in (row+['']*(width-len(row))))+' |')
                        if ri==0:lines.append('| '+' | '.join(['---']*width)+' |')
                    issues.add('Tableau converti en Markdown (structure enrichie non garantie)')
                else:
                    issues.add('Tableau complexe non reproduit')
                    lines.append(notice('notice.table_complex'))
        elif typ in ('embed','equation'):
            content = str(block.get('text') or block.get('url') or '')
            processor = str(block.get('processor') or 'latex')
            if processor in ('latex','mermaid','graphviz','chart','kroki','excalidraw','drawio'):
                lang = 'math' if processor=='latex' else processor
                lines.append('```'+lang+'\n'+content+'\n```')
                issues.add(f'Rendu intégré « {processor} » remplacé par son code source')
            elif rich_mode and youtube_markdown(content):
                lines.append(youtube_markdown(content,str(block.get('id') or i),page_text('label.youtube')))
            elif content.startswith(('https://','http://')):
                lines.append(f'[{page_text("label.embed_processor",processor=processor)}]({content})')
                issues.add(f'Intégration externe « {processor} » remplacée par un lien')
            else:
                issues.add(f'Intégration « {processor} » non reproduite')
                lines.append(notice('notice.embed'))
        elif typ in ('title','description','featured_properties','icon','chat','widget'):
            issues.add('Bloc système ou widget non reproduit')
        else:
            issues.add(f'Bloc inconnu « {typ or "sans type"} »')
            lines.append(notice('notice.block_unsupported',type=typ))
            # Preserve the raw data, rather than silently throwing it away.
            lines.append('```json\n'+json.dumps(block,ensure_ascii=False,indent=2)+'\n```')
    return '\n\n'.join(line for line in lines if line)


def hydrate_bookmark_blocks(doc, source, sid, names, cache=None):
    """Resolve source bookmark references when block metadata omits the title.

    Do not fetch remote websites. Only read local Anytype object metadata.
    """
    cache = cache if cache is not None else {}
    enriched = None
    for index,block in enumerate(doc.get('blocks') or []):
        if not isinstance(block,dict) or block.get('type') != 'bookmark':continue
        ref=block.get('object_id') or block.get('objectId') or block.get('target_object_id')
        if not ref:continue
        title=bookmark_block_title(block,names,None)
        url=bookmark_block_url(block)
        if title and url:continue
        if ref not in cache:
            try:cache[ref] = source.object_detail(sid,str(ref))
            except (APIError,ValueError,TypeError):cache[ref]={}
        detail=cache.get(ref)
        if not isinstance(detail,dict):continue
        candidate=display(detail,'')
        fallback_url=bookmark_url(detail)
        if candidate:names[str(ref)]=candidate
        updated=dict(block)
        if candidate and not title:updated['title']=candidate
        if fallback_url and not url:updated['url']=fallback_url
        if updated != block:
            if enriched is None:enriched=[dict(b) if isinstance(b,dict) else b for b in doc['blocks']]
            enriched[index]=updated
    if enriched is not None:return {**doc,'blocks':enriched}
    return doc


def write_markdown_with_embeds(target, sid, oid, markdown, native_embeds, issues, markers=True):
    """Resolve legacy markers to native envelopes; never emit iframe source."""
    for index,embed in enumerate(native_embeds):
        replacement=youtube_markdown(embed.get('url',''),str(index),page_text('label.youtube'))
        if replacement is None:
            replacement=titled_link(page_text('label.embed'),embed.get('url',''))
            issues.add('Intégration non reconnue : lien externe de remplacement')
        markdown=markdown.replace(f'ANYTWO_NATIVE_EMBED_{index:04d}_PLACEHOLDER',replacement)
    return set_markdown(target,sid,oid,markdown if markers else legacy_markup(markdown))


def source_format(name, value, metadata):
    record = metadata.get(name.casefold()) or {}
    fmt = str(record.get('format') or '').casefold()
    if fmt: return fmt
    if isinstance(value, bool): return 'checkbox'
    if isinstance(value, (int,float)): return 'number'
    if isinstance(value, (list,tuple)): return 'multi_select' if all(isinstance(x,str) for x in value) else 'unknown'
    return 'text' if isinstance(value,str) else 'unknown'


def column_shape(fmt, value, issues):
    """Returns descriptor, value; caller rewrites object refs separately."""
    if fmt in ('text','email','url','phone'):
        kind = 'string'; form = {'type':fmt if fmt!='text' else 'text'}
        return kind, form, str(value)
    if fmt == 'number' and isinstance(value, (int,float)) and not isinstance(value,bool):
        return 'number', {'type':'number'}, value
    if fmt == 'checkbox' and isinstance(value,bool):
        return 'boolean', {'type':'checkbox'}, value
    if fmt == 'date' and isinstance(value,str):
        return 'datetime', {'type':'date' if 'T00:00:00' in value or len(value)==10 else 'datetime'}, {'$date':value[:10]+'T00:00:00Z' if len(value)==10 else value}
    if fmt in ('select','multi_select'):
        vals = value if isinstance(value,list) else [value]
        if all(isinstance(x,str) for x in vals):
            options = {slug(x, x): {'name':x} for x in vals}
            return 'array', {'type':'choice','options':options,'config':{'multiple':fmt=='multi_select'}}, list(options)
    issues.add(f'Propriété « {fmt} » conservée en texte (format non transposable)')
    return 'string', {'type':'longtext'}, json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value


def date_has_time(value):
    if isinstance(value, dict):
        value = value.get('$date')
    if not isinstance(value, str) or 'T' not in value:
        return False
    try:
        instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if instant.tzinfo:
            instant = instant.astimezone(timezone.utc)
        return bool(instant.hour or instant.minute or instant.second or instant.microsecond)
    except ValueError:
        return True



def declared_properties(type_document, vocabulary):
    """Read actual Anytype v2 type schema, including columns without values."""
    candidates = type_document.get('property_definitions')
    if candidates is None:
        candidates = (type_document.get('type_settings') or {}).get('property_definitions')
    if candidates is None: candidates = type_document.get('properties')
    if not isinstance(candidates, list): return []
    out, seen = [], set()
    for raw in candidates:
        if not isinstance(raw, dict): continue
        key = str(raw.get('property') or raw.get('key') or raw.get('name') or '').strip()
        if not key: continue
        meta = vocabulary.get(key.casefold()) or {}
        label = str(raw.get('name') or meta.get('name') or key)
        normalized = label.casefold().replace('-', '_').replace(' ', '_')
        if (internal_record_property(key) or internal_record_property(raw.get('internal_key'))
                or internal_property(label, vocabulary) or internal_property(key, vocabulary)
                or key.casefold() in seen):
            continue
        fmt = str(raw.get('format') or meta.get('format') or 'text').casefold()
        options = raw.get('options') or meta.get('options') or []
        seen.add(key.casefold())
        out.append({**meta, **raw, 'key':key,'name':label,'format':fmt,'options':options})
    return out


def declared_column_shape(spec):
    """Provide a column definition without fabricating a dummy property value."""
    fmt = spec['format']
    if fmt in ('text','url','email','phone'):
        return 'string', {'type':fmt}
    if fmt == 'number': return 'number', {'type':'number'}
    if fmt == 'checkbox': return 'boolean', {'type':'checkbox'}
    if fmt == 'date': return 'datetime', {'type':'datetime' if spec.get('_requires_datetime') else 'date'}
    if fmt == 'objects': return 'array', {'type':'relation','config':{'multiple':True}}
    if fmt in ('select','multi_select'):
        opts=choice_options(spec.get('options') or [], slug)
        return 'array', {'type':'choice','options':opts,'config':{'multiple':fmt=='multi_select'}}
    return 'string', {'type':'longtext'}


class Engine:
    def __init__(self, source, target, inventory, plan):
        self.source=source; self.target=target; self.inv=inventory; self.plan=plan
        self.sid = plan['source_space']['id']
        self.dest_sid = None
        self.col_cache={}; self.prop_cache={}; self.upload_cache={}; self.mapping={}; self.property_owner={}
        self.source_file_metadata_cache={}
        self.source_file_dimensions={}
        self.link_file_types={}
        self.file_libraries={}
        self.existing_collections=set()
        self.memberships={}
        self.property_bindings={}
        self.written_properties={}
        self.created_columns=[]
        self.property_previews={}
        self.type_names={str(t.get('key')):t.get('name') for t in inventory['types']}
        self.source_views=SourceViews(source,self.sid,inventory)
        self.collection_documents={}
        self.view_reports=[]
        self.view_hosts={}
        self.widget_warnings = set()
        self.native_markup=True
        self.language=language(plan.get('language'))
        self.templates = Templates(self)
        self.type_defs={}; self.collection_reports=[]; self.results={}; self.report={'status':'running','objects':[],'errors':[], 'warnings':{},'created':{}}
        self.names={obj['id']:obj['name'] for obj in inventory['all']}

    def finish_report(self, status=None, error=None):
        counters=Counter(r['status'] for r in self.results.values())
        issues=Counter(issue for r in self.results.values() for issue in r['issues'])
        issues.update(issue for cr in self.collection_reports for issue in cr['issues'])
        issues.update(self.widget_warnings)
        issues.update(self.templates.warnings)
        if error:
            self.report['errors'].append(str(error))
        self.report['status']=status or ('done' if not counters['error'] and not counters['partial'] and not self.widget_warnings and not self.templates.warnings else 'partial')
        self.report['objects']=[{'name':r['name'],'source_id':oid,'target_id':r['target_id'],
                                 'status':r['status'],'reason':r['reason'],
                                 'issues':sorted(r['issues']),'errors':r['errors']}
                                for oid,r in self.results.items()]
        self.report['warnings']=dict(issues)
        self.report['source_type_definitions']=deepcopy(self.type_defs)
        self.report['views']=self.view_reports
        self.report['collections']=self.collection_reports
        self.report['totals']={'imported':counters['imported'],'partial':counters['partial'],
                               'error':counters['error'] + counters['pending'] + counters['created'],
                               'total':len(self.results)}
        return self.report

    def emit(self, event, **data): return {'event':event, **data}

    def warn(self, oid, message): self.results[oid]['issues'].add(message)

    def page_markdown(self, markdown):
        """Keep native envelopes only on clients that still interpret them."""
        return markdown if self.native_markup else legacy_markup(markdown)

    def remove_import_artifacts(self, documents, vocabulary):
        """Drop Anytwo columns that only mirror Anytype import bookkeeping.

        Deletion eligibility is never inferred from a display name: a column
        is only removed when this import created it and its exact source
        property identity is a verified system field. Columns created by this
        import are tracked in `created_columns` with their source key.
        """
        artifacts = {}
        for doc in documents:
            artifacts.update(import_artifacts(doc, vocabulary))
        if not artifacts: return []
        template_settings = {key for key in artifacts.values()
                             if str(key).replace('-', '_').replace(' ', '_').casefold().startswith('template_')}
        if template_settings:
            self.report.setdefault('template_settings_not_translated', []).extend(sorted(template_settings))
        identities = {str(key).replace('-', '_').replace(' ', '_').casefold()
                      for key in artifacts.values()}
        removed = []
        for column in self.created_columns:
            source = str(column.get('source_key') or '').replace('-', '_').replace(' ', '_').casefold()
            if source not in identities: continue
            cid = column['collection_id']; prop_id = column['property_id']
            try:
                delete_column(self.target, self.dest_sid, cid, prop_id)
            except (APIError, ValueError, TypeError) as exc:
                self.report.setdefault('artifact_warnings', []).append(
                    f'Colonne technique « {column["label"]} » non supprimée : {exc}')
                continue
            removed.append({'name': column['label'], 'collection_id': cid, 'property_id': prop_id})
        return removed

    def import_widgets(self, entries, docs):
        from anytwo_backend import add_overview_widgets

        collections = {key.removeprefix('collection:'): cid for key, cid in self.col_cache.items()
                       if key.startswith('collection:')}
        pages = {}
        for source_id, item in entries.items():
            target = self.mapping.get(source_id)
            doc = docs.get(source_id, {})
            if (target and not is_conversation(item) and not is_bookmark(item, doc)
                    and item.get('type') not in (FILE_TYPES | {'set', 'query', 'object_type', 'template'})
                    and item.get('layout') not in FILE_TYPES
                    and 'query_source' not in doc and doc.get('kind') != 'object_type' and not is_template(doc)):
                pages[source_id] = target
        if not pages and not collections:
            return []
        read_widgets = getattr(self.source, 'widgets', None)
        if read_widgets is None:
            return []
        try:
            source_widgets = read_widgets(self.sid)
        except APIError as exc:
            self.widget_warnings.add('Widgets Anytype non lus : '+str(exc))
            return []

        widgets = {}
        for row in source_widgets:
            source_id = row.get('target')
            if not isinstance(source_id, str) or not source_id or source_id.startswith('_'):
                continue
            if row.get('kind') == 'section' or row.get('type') == 'section' or row.get('layout') == 'section':
                continue
            if source_id in collections:
                kind, target = 'collection', collections[source_id]
            elif source_id in pages:
                kind, target = 'object', pages[source_id]
            else:
                continue
            # Shared widgets precede personal ones. Keep the first occurrence
            # when both scopes pin the same target to the shared Overview.
            widgets.setdefault((kind, target), {
                'source_id': source_id, 'target_id': target, 'kind': kind,
                'layout': 'link' if row.get('layout') == 'link' else 'views',
            })
        if not widgets:
            return []
        try:
            return add_overview_widgets(self.target, self.dest_sid, list(widgets.values()))
        except (APIError, KeyError, TypeError, ValueError) as exc:
            self.widget_warnings.add('Widgets Overview non confirmés : '+str(exc))
            return []

    def col(self, key, name, existing=None):
        if key in self.col_cache: return self.col_cache[key]
        if existing:
            cid=existing
            self.existing_collections.add(cid)
        else:
            cid=create_collection(self.target,self.dest_sid,name,slug(name,key))
            self.report['created'].setdefault('collections',[]).append(name)
            self.report['created'].setdefault('collection_details',[]).append({'id':cid,'name':name})
        self.col_cache[key]=cid
        return cid

    def register_source_collections(self, docs):
        """Resolve structural collection references before creating page objects."""
        for source_id, doc in list(docs.items()):
            candidates = [(source_id, doc)]
            for block in doc.get('blocks') or []:
                if not isinstance(block, dict) or block.get('type') != 'dataview' or not block.get('object_id'):
                    continue
                try:
                    host, _, _ = self.source_views.resolve(doc, block)
                    candidates.append((block['object_id'], host))
                except (APIError, UnsupportedView, ValueError, KeyError, TypeError):
                    continue
            for ref, host in candidates:
                if host.get('type') != 'collection' and host.get('type_internal_key') != 'collection':
                    continue
                self.collection_documents.setdefault(ref, host)
                name = (host.get('properties') or {}).get('name') or self.names.get(ref) or 'Collection Anytype'
                self.mapping[ref] = self.col('collection:'+ref, name)
                self.names[ref] = name
                if not any(row.get('source_id') == ref for row in self.collection_reports):
                    self.collection_reports.append({'source_id':ref, 'name':name, 'issues':[]})

    def type_column(self, key, name, *, force=False):
        target = self.plan['target']
        typmap = next((x for x in (target.get('type_mappings') or []) if x.get('key')==key),None)
        if typmap and typmap.get('collection_mode')=='existing':
            return self.col('type:'+key, typmap.get('collection_name') or name, typmap.get('collection_id'))
        if typmap and typmap.get('collection_mode')=='create':
            return self.col('type:'+key, typmap.get('collection_name') or name)
        if typmap and typmap.get('collection_mode')=='none' and not force:
            return None
        return self.col('type:'+key, name)

    def property(self, cid, name, fmt, value, issues, metadata, override=None, source_key=None):
        kind, form = override if override else column_shape(fmt, value, issues)[:2]
        meta=metadata.get(name.casefold(), {})
        saved=json.loads((form.get('any2any') or {}).get('sourceSettings') or '{}')
        restrictions=saved.get('object_types') or []
        if restrictions and fmt=='objects':
            targets=[]
            for source_type in restrictions:
                source_key=str(source_type).removeprefix('type-').removeprefix('ot-')
                typ=next((t for t in self.inv['types'] if source_key in (t['key'],t.get('id'),t['name'])),None)
                target_id=self.col_cache.get('type:'+(typ['key'] if typ else source_key))
                if not target_id:break
                targets.append(target_id)
            if len(targets)==len(restrictions):form={**form,'relation':{'targetTypes':targets}}
            else:issues.add('Restriction de types de « '+name+' » archivée : certains types cibles ne sont pas importés')
        form=enrich_descriptor({**meta, 'name':name, 'format':fmt}, form, issues)
        key=(cid,name.casefold(),kind,form.get('type') if isinstance(form,dict) else None)
        if key in self.prop_cache: return self.prop_cache[key]
        current = list_columns(self.target, self.dest_sid, cid)
        for p in current:
            if str(p.get('name') or '').casefold()==name.casefold() and p.get('kind')==kind and (not p.get('xFormat') or p.get('xFormat',{}).get('type')==form.get('type')):
                existing_form=p.get('xFormat') or form
                if existing_form.get('config',{}) != form.get('config',{}):
                    issues.add(f'Paramètres de la propriété existante « {name} » différents : conservés sans modification')
                for option_key,option in form.get('options',{}).items():
                    same=next((v for v in existing_form.get('options',{}).values() if v.get('name')==option.get('name')),None)
                    if same and option.get('color') and same.get('color')!=option['color']:
                        issues.add(f'Couleur différente pour « {option["name"]} » dans la propriété existante « {name} » : conservée')
                self.prop_cache[key]=(str(p['id']),existing_form)
                return self.prop_cache[key]
        if any(str(p.get('name') or '').casefold()==name.casefold() for p in current):
            issues.add(f'Propriété « {name} » : même nom mais format différent dans la collection cible')
            name += ' (Anytype)'
        pid = add_column(self.target,self.dest_sid,cid,name,slug(name,(cid,name,fmt)),kind,form)
        self.created_columns.append({'source_key':source_key or name,'collection_id':cid,
                                     'property_id':pid,'label':name})
        self.prop_cache[key]=(pid,form)
        return self.prop_cache[key]


    def inline_scope(self, source_id, block, source_ids, converter, issues):
        # A view is not a supertag. Reuse the actual source collection/type;
        # never manufacture one collection for each inline block.
        host,_,_=self.source_views.resolve(self.source_views.document(source_id),block)
        ref=block.get('object_id') or source_id
        if host.get('type')=='collection' or host.get('type_internal_key')=='collection' or (not block.get('object_id') and block.get('is_collection')):
            scope=self.col('collection:'+ref,self.names.get(ref) or (host.get('properties') or {}).get('name') or 'Collection Anytype')
        else:
            source=host.get('query_source')
            if host.get('kind')=='object_type':source={'types':[host.get('internal_key')]}
            if not isinstance(source,dict) or len(source.get('types',[]))!=1 or source.get('properties'):
                raise UnsupportedView('Source composée de vue en ligne non représentable sans collection artificielle')
            key=str(source['types'][0]).removeprefix('type-').removeprefix('ot-')
            typ=next((t for t in self.inv.get('types',[]) if key in (t['key'],t.get('id'))),{})
            key=typ.get('key') or key
            scope=self.type_column(key,typ.get('name') or self.names.get(ref) or key)
            if not scope:raise UnsupportedView('Type source sans collection de destination')
        included=[oid for oid in source_ids if oid in self.mapping]
        if scope in self.existing_collections:
            try:
                outside=local_get(self.target.port,f'/v1/spaces/{_segment(self.dest_sid)}/objects/query',
                    method='POST',body={'filter':{'$and':[{'any.collections':scope},
                        {'id':{'$nin':[self.mapping[oid] for oid in included]}}]},'limit':1})
            except (APIError,AttributeError) as exc:
                raise UnsupportedView('Périmètre de la collection cible existante non vérifiable : '+str(exc))
            if outside.get('records'):
                raise UnsupportedView('Collection cible existante contenant des documents hors périmètre source : vue non élargie')
        omitted=len(source_ids)-len(included)
        if omitted:issues.add(f'Vue limitée au périmètre importé : {omitted} membre(s) source non importé(s)')
        for oid in included:
            owned=self.memberships.setdefault(oid,set())
            if scope not in owned:
                add_membership(self.target,self.dest_sid,self.mapping[oid],scope)
                owned.add(scope)
        bindings={};mirrored={}
        names=list(dict.fromkeys(n for view in block.get('views',[]) for n in property_names(view)))
        # Every custom field belongs in the source collection, including fields
        # hidden by this particular view. Mirror values and descriptors together.
        for oid in included:
            for saved in self.written_properties.get(oid,{}).values():
                spec=saved.get('spec',{});name=str(spec.get('key') or spec.get('internal_key') or saved.get('label') or '')
                if not name:continue
                if name not in names:names.append(name)
        for name in names:
            if name.casefold()=='name':continue
            if name!='type' and internal_record_property(name):continue
            declared=next((v for v in block.get('properties',[]) if str(v.get('property','')).casefold()==name.casefold()),{})
            source_spec=converter.metadata.get(name.casefold()) or declared
            if source_spec.get('format') == 'files':
                continue
            candidates=[] if name=='type' else converter.bindings.get(name.casefold(),[])
            if included:
                owners={owner for oid in included for owner in self.memberships.get(oid,set())}
                owners.update(self.property_owner.get(oid) for oid in included)
                candidates=[c for c in candidates if c[0].split('.')[0] in owners or
                    any(c[0] in self.written_properties.get(oid,{}) for oid in included)]
            if candidates:
                identities={str(spec.get('internal_key') or spec.get('key') or spec.get('id') or name).casefold()
                            for _,spec,_ in candidates}
                if len(identities)>1:
                    raise UnsupportedView('Propriétés homonymes distinctes dans la source : '+name)
                # One source property can be carried by several destination type
                # collections. They are storage locations, not distinct columns.
                preferred=next((c for c in candidates if c[0].split('.')[0]==scope),candidates[0])
                path,spec,form=preferred
                target_binding=next((mirrored[c[0]] for c in candidates if c[0] in mirrored),None)
                if target_binding is None:
                    if path.split('.')[0]==scope:target_binding=preferred
                    else:
                        kind=declared_column_shape({**spec,'format':spec.get('format') or 'text'})[0]
                        pid,actual=self.property(scope,str(spec.get('name') or name),spec.get('format') or 'text',None,issues,converter.metadata,
                            override=(kind,deepcopy(form)),
                            source_key=str(spec.get('internal_key') or spec.get('key') or spec.get('id') or name))
                        target_binding=(scope+'.'+pid,spec,actual)
                    for oid in included:
                        values=[]
                        for source_path,source_spec,source_form in candidates:
                            saved=self.written_properties.get(oid,{}).get(source_path)
                            if saved is None:continue
                            value=deepcopy(saved['value'])
                            if source_spec.get('format') in ('select','multi_select'):
                                options=target_binding[2].get('options',{})
                                target_keys={v['name']:k for k,v in options.items()}
                                value=[target_keys[source_form['options'][k]['name']] for k in value]
                            if value not in values:values.append(value)
                        if len(values)>1:raise UnsupportedView('Valeurs contradictoires pour la propriété source : '+name)
                        if values and target_binding[0] not in self.written_properties.get(oid,{}):
                            written=values[0]
                            if target_binding[1].get('format')=='objects':
                                written=relation_references(written,self.mapping)
                                if written is None:
                                    issues.add('Référence de relation non importée : valeur ignorée')
                                    continue
                            set_column_value(self.target,self.dest_sid,self.mapping[oid],scope,target_binding[0].split('.',1)[1],written)
                for source_path,_,_ in candidates:mirrored[source_path]=target_binding
                bindings[name.casefold()]=[target_binding]
                continue
            # System fields are absent from custom-property migration. Preserve
            # source values as ordinary scope columns instead of sorting on the
            # new import timestamps of the destination objects.
            found=[]
            for oid in included:
                doc=self.source_views.document(oid)
                value=source_value(doc,name,self.source_views.items.get(oid))
                if name == 'type' and value is not MISSING:
                    value = self.type_names.get(str(value)) or next(
                        (t.get('name') for t in self.inv['types'] if str(value) in (str(t.get('id')), str(t.get('key')))), str(value))
                if value is not MISSING:found.append((oid,value))
            declared=next((v for v in block.get('properties',[]) if str(v.get('property','')).casefold()==name.casefold()),{})
            spec=deepcopy(converter.metadata.get(name.casefold()) or declared)
            if name=='type':spec={'name':'Type','format':'text'}
            if not found and not spec:continue
            fmt=spec.get('format') or ('date' if name in ('created_date','last_modified_date','last_opened_date') else 'text')
            if name=='type':fmt='text'
            # A relation column only accepts an array of any:// URIs. When the
            # source value cannot be mapped, keep the value as text instead of
            # creating a relation column the destination will reject.
            references=[]
            if fmt=='objects':
                references=[mapped_relation(value,self.mapping) for _,value in found]
                if not found or not all(references):
                    issues.add(f'Référence externe dans la propriété « {name} » conservée en texte')
                    spec['format']='text';fmt='text';references=[]
            spec.update(format=fmt,name=spec.get('name') or name)
            kind,form=declared_column_shape(spec)
            if fmt=='date' and found and any(date_has_time(v) for _,v in found):
                form['type']='datetime'
            pid,actual=self.property(scope,spec['name'],fmt,found[0][1] if found else None,issues,converter.metadata,override=(kind,form),
                source_key=str(spec.get('internal_key') or spec.get('key') or spec.get('id') or name))
            bindings[name.casefold()]=[(scope+'.'+pid,spec,actual)]
            for index,(oid,value) in enumerate(found):
                converted=references[index] if fmt=='objects' else column_shape(fmt,value,issues)[2]
                set_column_value(self.target,self.dest_sid,self.mapping[oid],scope,pid,converted)
        return scope,ViewConverter(bindings,converter.mapping,converter.type_collections,converter.metadata,anytype_controls=converter.anytype_controls)


    def convert_property_blocks(self, doc, source_id, issues):
        if getattr(self, 'destination_version', ()) < (0, 4, 1):
            return
        from inline_views import instance_id
        from notion_native import envelope
        owners = self.memberships.get(source_id, set())
        system = {'creator':('author','Created by'), 'createdby':('author','Created by'),
                  'createddate':('createdAt','Creation date'), 'creationdate':('createdAt','Creation date'),
                  'lastmodifieddate':('modifiedAt','Last modified date'),
                  'lastmodifiedby':('modifiedBy','Last modified by')}
        for index, block in enumerate(doc.get('blocks') or []):
            if not isinstance(block, dict) or block.get('type') != 'property':
                continue
            key = str(block.get('key') or block.get('property') or '')
            aliases = doc.get('property_internal_keys') or {}
            internal = str(aliases.get(key) or key)
            candidates = {}
            for alias in (key, internal):
                for path, spec, _ in self.property_bindings.get(alias.casefold(), []):
                    owner, prop = path.split('.', 1)
                    if owner in owners:
                        candidates[path] = (owner, prop, spec.get('name') or key)
            if len(candidates) == 1:
                owner, prop, label = next(iter(candidates.values()))
            elif not candidates and (builtin := system.get(re.sub(r'[\s_-]+', '', internal.casefold()))):
                prop, label = builtin
                owner = 'any'
                issues.add('Propriété système intégrée « '+label+' » : valeur calculée par Anytwo sur la page importée')
            else:
                continue
            oid = self.mapping[source_id]
            identity = instance_id(oid,'property:'+str(block.get('id') or index))
            block['markdown'] = envelope('property',identity,
                {'space':self.dest_sid,'object':oid,'owner':owner,'property':prop},
                re.sub(r'([\\`*_\[\]<>#])',r'\\\1',str(label)).replace('\n',' '))
            block['type'] = 'any2any_property'

    def convert_views(self, doc, target_id, converter, issues, source_id):
        doc=deepcopy(doc)
        original_blocks=doc.get('blocks') or []
        blocks=[b for b in original_blocks if not isinstance(b,dict) or not is_recent_widget_block(b)]
        if doc.get('views') and not any(b.get('type')=='dataview' for b in blocks if isinstance(b,dict)):
            if len(blocks)==len(original_blocks):
                blocks=blocks+[{'type':'dataview','views':doc['views'],
                               'is_collection':doc.get('type_internal_key')=='collection' or doc.get('type')=='collection'}]
            else:
                doc.pop('views',None)
        for block_index,block in enumerate(blocks):
            if not isinstance(block,dict) or block.get('type')!='dataview': continue
            original=deepcopy(block)
            report={'source_id':source_id,'block_id':block.get('id'), 'source':original, 'status':'unsupported'}
            try:
                source_host,source_ids,views=self.source_views.resolve(doc,block)
                reference=block.get('object_id')
                block['views']=views
                table_key=instance_id(target_id,str(block.get('id') or block_index))
                if target_id != self.col_cache.get('collection:'+source_id):
                    scope,scoped_converter=self.inline_scope(source_id,block,source_ids,converter,issues)
                    records,failed=inline_records(scoped_converter,block,scope,table_key,issues,
                        native_layouts=getattr(self, 'destination_version', ()) >= (0, 3, 6))
                    view_id=self.view_hosts.get(target_id)
                    if view_id is None:
                        root=target_write(self.target,f'/spaces/{_segment(self.dest_sid)}/objects',{
                            'type':'dataview','initialProperties':{'dataview':{'host':target_id}}})
                        view_id=root.get('objectId')
                    if not view_id:raise APIError('Objet de vues créé sans identifiant')
                    modify_records(self.target,self.dest_sid,view_id,'dataviews',[
                        {'id':table_key,'name':block.get('name') or views[0].get('name') or 'Vue Anytype','pos':f'a{block_index:06d}'}])
                    modify_records(self.target,self.dest_sid,view_id,'views',records)
                    self.view_hosts[target_id]=view_id
                    markup=inline_markdown(self.dest_sid,target_id,table_key,
                        block.get('name') or views[0].get('name') or 'Vue Anytype',scope,layout=records[0]['layout'])
                    block.clear();block.update({'type':'any2any_inline_view','markdown':markup,
                        'failed':failed,'indent':original.get('indent',0)})
                else:
                    members=source_ids
                    table_key='default'
                    view_id,failed=create_saved_views(self.target,self.dest_sid,target_id,block,source_host,members,converter,issues,
                        root_id=self.view_hosts.get(target_id),table_key=table_key)
                    self.view_hosts[target_id]=view_id
                    block.clear();block.update({'type':'any2any_saved_view','name':original.get('name'),
                        'target_id':view_id,'failed':failed,'indent':original.get('indent',0)})
                report.update(status='partial' if failed else 'created',target_id=view_id,errors=failed)
            except (UnsupportedView,APIError,TypeError,ValueError,KeyError) as exc:
                issues.add('Vue non convertie : '+str(exc))
                report['error']=str(exc)
            self.view_reports.append(report)
        doc['blocks']=blocks
        return doc

    def add_file(self, oid, fid, name, mime):
        # A source payload is shared across pages, while references stay space-local.
        key=(self.dest_sid,fid)
        if key in self.upload_cache:return self.upload_cache[key]
        original_name=safe_filename(name)
        inventory_name=safe_filename(self.names.get(fid,''))
        extra_mime=''
        if has_file_extension(inventory_name) and strip_import_prefix(inventory_name)==inventory_name:
            original_name=inventory_name
        else:
            if fid not in self.source_file_metadata_cache:
                try:
                    detail=self.source.object_detail(self.sid,fid)
                    self.source_file_metadata_cache[fid]=file_metadata(detail)
                    props=detail.get('properties') or {}
                    self.source_file_dimensions[fid]=(props.get('width_in_pixels'),props.get('height_in_pixels'))
                except (APIError,AttributeError,ValueError,TypeError):
                    self.source_file_metadata_cache[fid]=('','')
            source_name,extra_mime=self.source_file_metadata_cache[fid]
            if source_name:original_name=source_name
            elif inventory_name:original_name=inventory_name
        original_name=original_name or ('fichier-'+str(fid)[:14])
        content,detected=anytype_download(self.source,self.sid,fid)
        declared=mime if normalized_mime(mime) not in GENERIC_MIMES else extra_mime
        actual_mime=resolve_file_mime(original_name,declared,detected)
        if not has_file_extension(original_name):
            ext='.csv' if actual_mime=='text/csv' else mimetypes.guess_extension(actual_mime)
            if ext:original_name+=ext
            else:self.results[oid]['issues'].add('Extension du fichier source introuvable : '+original_name)
        library=self.file_libraries.setdefault(self.dest_sid,FileLibrary(self.target,self.dest_sid))
        new=library.find(original_name,content)
        reused=new is not None
        if new is None:
            new=attach_file(self.target,self.dest_sid,self.mapping[oid],original_name,content,actual_mime)
            library.register(original_name,content,new)
        width,height=self.source_file_dimensions.get(fid,(None,None))
        uri=ImportedFile(f'any://f/{self.dest_sid}/{new}',original_name,actual_mime,width,height)
        self.upload_cache[key]=uri
        self.report.setdefault('file_transfers',[]).append({'source_id':fid,'target_id':new,
            'name':original_name,'action':'reused' if reused else 'uploaded'})
        if actual_mime == 'text/csv':
            # Useful to diagnose a server-side regression without failing a
            # successful upload on older preview clients without this route.
            try:
                info = get_file_info(self.target, self.dest_sid, new)
                recorded = normalized_mime(info.get('mime') or info.get('mimeType'))
                if recorded and recorded != 'text/csv':
                    self.results[oid]['issues'].add(
                        f'CSV « {original_name} » : Anytwo a enregistré le type {recorded} au lieu de text/csv')
            except (APIError, ValueError, TypeError, KeyError, AttributeError):
                pass
        return uri

    def resolve_file_links(self, blocks):
        """Anytype may represent a file card as a link to its file object."""
        for block in blocks:
            if isinstance(block, list):
                self.resolve_file_links(block)
                continue
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'link':
                fid = block.get('object_id') or block.get('objectId')
                if isinstance(fid, str) and fid:
                    if fid not in self.link_file_types:
                        document = self.source_views.docs.get(fid)
                        if document is None and fid not in self.names:
                            try:
                                document = self.source_views.document(fid)
                            except (APIError, ValueError):
                                pass
                        known = self.source_views.items.get(fid, {})
                        document = document or {}
                        kinds = [source.get(key) for source in (document, known, known.get('raw') or {})
                                 for key in ('kind', 'type', 'type_internal_key', 'layout')]
                        kinds = [re.sub(r'[^a-z]', '', value.casefold()) for value in kinds if isinstance(value, str)]
                        kind = next((value for value in kinds if value in FILE_TYPES | {'fileobject'}), None)
                        self.link_file_types[fid] = 'file' if kind == 'fileobject' else kind
                        if kind and document:
                            self.source_file_metadata_cache[fid] = file_metadata(document)
                            props = document.get('properties') or {}
                            if isinstance(props, dict):
                                self.source_file_dimensions[fid] = (props.get('width_in_pixels'), props.get('height_in_pixels'))
                    kind = self.link_file_types[fid]
                    if kind:
                        name, mime = self.source_file_metadata_cache.get(fid, ('', ''))
                        block.update(type=kind, object_id=fid, style='link',
                                     name=name or self.names.get(fid) or block.get('name'),
                                     mime_type=mime or block.get('mime_type'))
            for children in ('blocks', 'children', 'rows', 'cells'):
                if isinstance(block.get(children), list):
                    self.resolve_file_links(block[children])

    def run(self):
        from anytwo_backend import server_version
        activate(self.language)
        self.destination_version = server_version(self.target)
        # Anytwo 0.5+ shows the native comment envelopes as page text, so the
        # importer keeps a plain Markdown rendering that degrades gracefully.
        self.native_markup = envelopes_supported(self.destination_version)
        if not self.native_markup:
            yield self.emit('message', message='Ce client Anytwo affiche les marqueurs de mise en page : blocs repliables, colonnes et intégrations sont écrits en Markdown simple.')
        plan=self.plan; inv=self.inv
        if plan.get('mode') not in ('simple', None):
            raise APIError('Le mode synchronisation nécessite une gestion des mises à jour : il n’est pas activé dans cette version. Choisissez « Import simple ».')
        roots, reasons, selected_cols = select_scope(inv,plan)
        entries, docs, read_errors = discover_documents(self.source,self.sid,inv,roots,reasons,bool(plan.get('follow_links')) and plan['selection']['kind']!='space',self.source_views)
        if not docs and entries: raise APIError('Aucun document source lisible. Aucune écriture effectuée.')
        self.templates.discover(entries, docs, reasons, selected_cols)
        if len(entries) > MAX_OBJECTS:
            raise APIError(f'Plus de {MAX_OBJECTS} objets, templates inclus. Aucune écriture effectuée.')
        yield self.emit('message',message=f'Lecture de {len(docs)} objets source · {len(read_errors)} avertissement(s).')
        try: metadata = anytype_property_definitions(self.source,self.sid)
        except APIError as exc:
            metadata={}; yield self.emit('message',message=f'! Métadonnées des propriétés indisponibles : {exc} (conversion prudente)')
        # Inspect the type vocabulary before creating anything in Anytwo.
        # This is essential to keep empty (but user-defined) property columns.
        used_keys={str(obj.get('type') or '').casefold() for obj in entries.values()}
        for typ in inv['types']:
            key = str(typ['key'])
            if key.casefold() not in used_keys: continue
            try:
                detail = self.source.type_detail(self.sid,key) if hasattr(self.source,'type_detail') else {}
                if not isinstance(detail,dict): detail = {}
                label=(detail.get('properties') or {}).get('name')
                if label:
                    self.type_names[key]=label
                    self.type_names[str(typ.get('id'))]=label
                defs = declared_properties(detail,metadata)
                for spec in defs:
                    if spec.get('format') == 'date':
                        spec['_requires_datetime'] = any(
                            date_has_time(source_value(doc, spec['key'])) or date_has_time(source_value(doc, spec['name']))
                            for oid, doc in docs.items() if entries[oid].get('type') == key)
                if not defs and detail.get('property_definitions') is None:
                    yield self.emit('message', message=f'! Schéma du type « {typ["name"]} » incomplet : les colonnes sans valeur peuvent manquer.')
            except APIError as exc:
                defs=[]
                yield self.emit('message', message=f'! Schéma du type « {typ["name"]} » inaccessible : {exc}')
            self.type_defs[key]=defs
        archives=chat_histories(self.source,self.sid) if plan.get('archive_chats') else []
        if archives:yield self.emit('message',message=f'{len(archives)} chat(s) à importer en archives.')
        target=plan['target']
        self.dest_sid = target['space_id'] if target['space_mode']=='existing' else create_space(self.target,target['space_name'])
        if target['space_mode']=='create':
            self.report['created']['space']={'id':self.dest_sid,'name':target['space_name']}
        yield self.emit('message',message=f'Espace Anytwo : {target["space_name"]} ({"existant" if target["space_mode"]=="existing" else "créé"}).')
        for col in selected_cols:
            col_issues=set()
            try:
                source_col=self.source_views.document(col['id'])
                self.collection_documents[col['id']]=source_col
                if source_col.get('filters') or source_col.get('sorts'):
                    col_issues.add('Filtres / tris hors définition de vue conservés dans le rapport')
                    self.view_reports.append({'source_id':col['id'],'source':source_col,'status':'unsupported','error':'Filtres hors vue structurée'})
            except (APIError,TypeError,ValueError,KeyError):
                col_issues.add('Configuration avancée de la collection source non vérifiable')
            self.collection_reports.append({'source_id':col['id'], 'name':col['name'], 'issues':sorted(col_issues)})
            cid = self.col('collection:'+col['id'],
                           target.get('collection_name') or col['name'] if len(selected_cols)==1 else col['name'],
                           target.get('collection_id') if len(selected_cols)==1 and target.get('collection_mode')=='existing' else None)
            yield self.emit('message',message=f'Collection « {col["name"]} » → {cid}')
        self.register_source_collections(docs)
        types_by_obj={obj['id']:typ for typ in inv['types'] for obj in typ['items']}
        member_cols={oid:[] for oid in docs}
        for source_id, source_doc in self.collection_documents.items():
            cid=self.col_cache.get('collection:'+source_id)
            source_ids=set(source_doc.get('collection_items',[]))
            source_ids.update(item['id'] for item in inv['members'].get(source_id,[]))
            for member_id in source_ids:
                if member_id in member_cols:member_cols[member_id].append(cid)
        # First pass: all pages and their collection memberships (no relations yet).
        for oid, obj in sorted(entries.items(), key=lambda item:item[0] in self.templates.rows):
            self.results[oid]={'name':obj['name'],'source_id':oid,'target_id':None,
                               'reason':reasons.get(oid,['Lié indirectement à la sélection']),
                               'issues':set(), 'errors':[], 'status':'pending'}
            for eoid,msg in read_errors:
                if eoid==oid: self.warn(oid,msg)
            if oid not in docs:
                self.results[oid]['status']='error'
                self.results[oid]['errors'].append('Objet source non lisible')
                continue
            if oid in self.collection_documents:
                self.results[oid]['target_id']=self.col_cache['collection:'+oid]
                self.results[oid]['status']='created'
                continue
            props = {} if is_bookmark(obj,docs[oid]) else custom_properties(docs[oid],metadata)
            template = oid in self.templates.rows
            typ = None if template else types_by_obj.get(oid)
            typkey=(typ or {}).get('key') or obj.get('type') or 'page'
            cols=self.templates.scopes(oid, entries) if template else list(member_cols.get(oid,[]))
            # Existing source collection memberships own the properties. A type
            # collection is only a fallback for objects outside source collections.
            type_col=None
            if not cols and not is_bookmark(obj,docs[oid]) and (props or self.type_defs.get(typkey)):
                type_col=self.type_column(typkey,(typ or {}).get('name') or typkey,force=True)
                if type_col not in cols: cols.append(type_col)
            elif not cols and not is_bookmark(obj,docs[oid]) and plan['selection']['kind'] in ('types','objects'):
                type_col=self.type_column(typkey,(typ or {}).get('name') or typkey)
                if type_col and type_col not in cols: cols.append(type_col)
            self.property_owner[oid]=type_col or (cols[0] if cols else None)
            if target.get('collection_mode') in ('create','existing') and plan['selection']['kind']=='objects' and not cols:
                cols.append(self.col('selected-objects',target['collection_name'],
                                     target.get('collection_id') if target['collection_mode']=='existing' else None))
            cols=[x for x in cols if x]
            member_cols[oid]=cols
            try:
                icon = docs[oid].get('icon') or {}
                emoji = str(icon.get('emoji') or '') if isinstance(icon,dict) and icon.get('format')=='emoji' else (icon if isinstance(icon,str) else '')
                icon_warnings=[]
                if template:
                    from anytwo_backend import create_template
                    self.mapping[oid]=create_template(self.target,self.dest_sid,obj['name'],cols,emoji=emoji or None)
                elif emoji:
                    self.mapping[oid]=create_object(self.target,self.dest_sid,obj['name'],cols,
                                                    emoji=emoji,icon_warnings=icon_warnings)
                    self.results[oid]['issues'].update(icon_warnings)
                else:
                    self.mapping[oid]=create_object(self.target,self.dest_sid,obj['name'],cols)
                self.memberships[oid]=set(cols)
                self.results[oid]['target_id']=self.mapping[oid]
                self.results[oid]['status']='created'
                if isinstance(icon,dict) and icon.get('format')=='image':
                    icon_file=icon.get('file') or icon.get('object_id')
                    if icon_file:
                        try:
                            icon_uri=self.add_file(oid,str(icon_file),'icone-'+obj['name'],None)
                            set_column_value(self.target,self.dest_sid,self.mapping[oid],'any','icon',str(icon_uri))
                        except APIError as exc:self.warn(oid,'Icône image non transférée : '+str(exc))
                    else:self.warn(oid,'Icône image sans identifiant de fichier')
                elif icon and not emoji:
                    self.warn(oid,'Format d’icône source non transposable automatiquement')
                yield self.emit('message',message=f'Créé : {obj["name"]}')
            except APIError as exc:
                self.results[oid]['status']='error';self.results[oid]['errors'].append(str(exc))
                yield self.emit('message',message=f'! Création impossible « {obj["name"]} » : {exc}')
        # Define all source type columns, including empty ones, before writing values.
        for typkey,defs in self.type_defs.items():
            defined_owners=set()
            for oid,obj in entries.items():
                if (obj.get('type') or 'page') != typkey or oid not in self.mapping or is_bookmark(obj,docs.get(oid)): continue
                cid=self.property_owner.get(oid)
                if not cid or not defs or cid in defined_owners: continue
                defined_owners.add(cid)
                issues=self.results[oid]['issues']
                for spec in defs:
                    if spec['format'] == 'files':
                        continue
                    try:
                        pid,form=self.property(cid,spec['name'],spec['format'],None,issues,metadata,
                                      override=(declared_column_shape(spec)[0], enrich_descriptor(spec, declared_column_shape(spec)[1], issues)),
                                      source_key=str(spec.get('key') or spec.get('internal_key') or spec.get('id')))
                        for alias in (spec['key'],spec['name'],spec.get('id'),spec.get('internal_key')):
                            if alias:
                                binding=(cid+'.'+pid,spec,form)
                                bucket=self.property_bindings.setdefault(str(alias).casefold(),[])
                                if not any(b[0]==binding[0] for b in bucket):bucket.append(binding)
                    except (APIError,ValueError,TypeError,KeyError) as exc:
                        self.results[oid]['errors'].append('Définition de propriété « '+spec['name']+' » : '+str(exc))
                # Define empty fields once for each actual property owner.
        # Second pass: properties, links, files and content. Content failures must not be hidden.
        for oid,doc in docs.items():
            r = self.results[oid]
            if not r['target_id']: continue
            if oid in self.collection_documents:
                continue
            props={} if is_bookmark(entries[oid],doc) else custom_properties(doc,metadata)
            cols=member_cols.get(oid,[])
            for name,value in props.items():
                fmt=source_format(name,value,metadata)
                aliases=doc.get('property_internal_keys') or {}
                meta=metadata.get(str(aliases.get(name) or name).casefold(),metadata.get(name.casefold(),{}))
                typkey=entries[oid].get('type') or 'page'
                declared=next((s for s in self.type_defs.get(typkey,[]) if name.casefold() in (s['key'].casefold(),s['name'].casefold())),{})
                meta={**meta, **declared}
                fmt=str(meta.get('format') or fmt).casefold()
                label=str(meta.get('name') or name)
                if fmt == 'files':
                    values=value if isinstance(value,list) else [value]
                    preview=[]
                    for fid in values:
                        if not isinstance(fid,str):
                            r['errors'].append(f'Fichier de propriété « {name} » : ID invalide')
                            continue
                        if not plan.get('files'):
                            r['issues'].add('Fichiers de propriété non repris (option désactivée)')
                            continue
                        try:
                            uri=self.add_file(oid,fid,label+'-'+fid[:10],None)
                            preview.append(image_markdown(uri,getattr(uri,'name',label))
                                if getattr(uri,'mime','').startswith('image/') else file_html(uri,getattr(uri,'name',label)))
                        except APIError as exc:
                            r['errors'].append(f'Fichier de propriété « {name} » : {exc}')
                    if preview:
                        self.property_previews.setdefault(oid,[]).append('**'+label+'**\n\n'+'\n\n'.join(preview))
                        r['issues'].add('Propriété fichier « '+label+' » : contenu placé en début de page')
                    continue
                if not cols:
                    r['errors'].append(f'Propriété « {name} » sans collection de destination')
                    continue
                # Anytwo rejects an empty value for these formats instead of
                # ignoring it; writing "" aborted the whole property of a page.
                if isinstance(value,str) and not value.strip() and fmt in ('url','email','phone','number','date'):
                    r['issues'].add(f'Valeur vide ignorée pour la propriété « {label} »')
                    continue
                if fmt=='url' and isinstance(value,str) and not urlparse(value.strip()).scheme:
                    # Keep a relative address as text rather than lose it to a
                    # format the destination cannot store.
                    r['issues'].add(f'Valeur non absolue pour « {label} » conservée en texte')
                    fmt='text'
                primary=self.property_owner.get(oid) or cols[0]
                try:
                    if fmt=='objects':
                        values=value if isinstance(value,list) else [value]
                        kept=[v for v in values if isinstance(v,str) and v in self.mapping]
                        if len(kept)!=len(values):
                            # Keeping the relation format avoids a duplicate
                            # text column named "X (Anytype)" in the collection.
                            r['issues'].add(f'Référence externe dans la propriété « {name} » ignorée')
                        if not kept:
                            continue
                        converted=['any://'+self.mapping[v] for v in kept]
                        spec=('array',{'type':'relation','config':{'multiple':len(kept)>1}})
                    if fmt!='objects':
                        kind, form, converted = column_shape(fmt,value,r['issues'])
                    else:
                        kind,form=spec
                    if meta.get('_options_unavailable'):
                        r['issues'].add('Vocabulaire et couleurs de « '+label+' » indisponibles dans l’API source')
                    self.report.setdefault('property_settings',{})[str(meta.get('internal_key') or meta.get('key') or name)]=deepcopy(meta)
                    if fmt in ('select','multi_select') and meta.get('options') is not None:
                        form=declared_column_shape({**meta,'format':fmt})[1]
                    form=enrich_descriptor({**meta,'format':fmt,'name':label}, form, r['issues'])
                    if fmt=='date' and form.get('type')=='date' and date_has_time(converted):
                        form['type']='datetime'
                    pid,actual_form=self.property(primary,label,fmt,value,r['issues'],metadata,
                                                  override=(kind,form),
                                                  source_key=str(meta.get('internal_key') or meta.get('key') or name))
                    if fmt in ('select','multi_select'):
                        # Options must be extended in a later pass if the column pre-exists.
                        options=actual_form.setdefault('options',{}) if isinstance(actual_form,dict) else {}
                        label_to_key={str(v.get('name')):k for k,v in options.items() if isinstance(v,dict)}
                        vs=value if isinstance(value,list) else [value]
                        for v in vs:
                            if v not in label_to_key:
                                new_key=slug(v,v)
                                from api_clients import target_write, _segment
                                target_write(self.target, f'/spaces/{_segment(self.dest_sid)}/collections/{_segment(primary)}/properties/{_segment(pid)}',
                                             {'set': {f'xFormat.options.{new_key}.{k}':val for k,val in (form.get('options',{}).get(new_key) or {'name':v}).items()}},method='PATCH')
                                label_to_key[v]=new_key
                                options[new_key]=form.get('options',{}).get(new_key) or {'name':v}
                        converted=[label_to_key[v] for v in vs]
                    for alias in (name,label,meta.get('key'),meta.get('id'),meta.get('internal_key'),declared.get('key'),(doc.get('property_internal_keys') or {}).get(name)):
                        if alias:
                            binding=(primary+'.'+pid, {**meta,'format':fmt}, actual_form)
                            bucket=self.property_bindings.setdefault(str(alias).casefold(),[])
                            if not any(b[0]==binding[0] for b in bucket): bucket.append(binding)
                    set_column_value(self.target,self.dest_sid,r['target_id'],primary,pid,converted)
                    self.written_properties.setdefault(oid,{})[primary+'.'+pid]={
                        'kind':kind,'format':fmt,'label':label,'spec':{**meta,'format':fmt},
                        'form':deepcopy(actual_form),'value':deepcopy(converted)}
                except (APIError,KeyError,ValueError,TypeError) as exc:
                    r['errors'].append(f'Propriété « {name} » : {exc}')
        self.templates.mirror_values()
        # Third pass: views and page bodies use the complete property/id mapping.
        converter=ViewConverter(self.property_bindings,self.mapping,
            {k[5:]:v for k,v in self.col_cache.items() if k.startswith('type:')},metadata,anytype_controls=True)
        for source_id,source_doc in self.collection_documents.items():
            cid=self.col_cache.get('collection:'+source_id)
            issues=set()
            scoped=converter
            for block in source_doc.get('blocks',[]):
                if block.get('type')!='dataview':continue
                try:
                    _,scoped=self.inline_scope(source_id,block,
                        source_doc.get('collection_items',[o['id'] for o in inv['members'].get(source_id,[])]),converter,issues)
                except (UnsupportedView,APIError,ValueError,TypeError,KeyError) as exc:
                    issues.add('Propriétés de collection non reproduites : '+str(exc))
            self.convert_views(source_doc,cid,scoped,issues,source_id)
            if source_id in self.results:
                self.results[source_id]['issues'].update(issues)
            report=next((r for r in self.collection_reports if r.get('source_id') == source_id),None)
            if report is not None: report['issues']=sorted(set(report['issues'])|issues)
        for oid,doc in docs.items():
            r=self.results[oid]
            if not r['target_id']: continue
            if oid in self.collection_documents:
                r['status']='partial' if r['issues'] or r['errors'] else 'imported'
                yield self.emit('object',name=r['name'],source_id=oid,target_id=r['target_id'],
                    status=r['status'],reason=r['reason'],issues=sorted(r['issues']),errors=r['errors'])
                continue
            props=custom_properties(doc,metadata)
            doc=self.convert_views(doc,r['target_id'],converter,r['issues'],oid)
            self.resolve_file_links(doc.get('blocks') or [])
            issues=r['issues']
            self.convert_property_blocks(doc,oid,issues)
            toc_tokens = set()
            if self.destination_version >= (0, 4, 1):
                from notion_native import marker, replace_toc_markers, envelope
                for index, block in enumerate(doc.get('blocks') or []):
                    if isinstance(block, dict) and block.get('type') in ('table_of_contents','tableOfContents'):
                        token = marker('toc', oid, str(block.get('id') or index))
                        if block_depth(block) == 0:
                            block.update(type='any2any_toc', markdown=envelope(
                                'table-of-contents', instance_id(oid, str(block.get('id') or index)), {}, ''))
                        else:
                            toc_tokens.add(token)
                            block.update(type='any2any_toc', marker=token)
            cover=doc.get('cover')
            cover_line=''
            if isinstance(cover,dict) and cover.get('format')=='image' and cover.get('file'):
                if plan.get('files'):
                    try:
                        uri=self.add_file(oid,str(cover['file']),'couverture-'+r['name']+'.png','image/png')
                        cover_line=image_markdown(uri,page_text('label.cover',name=r['name']))
                        issues.add('Couverture ajoutée dans la page (présentation d’origine non reproduite)')
                    except APIError as e:
                        issues.add('Couverture image non importée : '+str(e))
                else:
                    issues.add('Couverture image non importée (option fichiers désactivée)')
            elif cover:
                issues.add('Couverture Anytype non reproduite')
            query_missing = ('query_source' in doc or bool(doc.get('views'))) and not any(
                b.get('type') in ('dataview', 'any2any_inline_view', 'any2any_saved_view')
                for b in doc.get('blocks', []) if isinstance(b, dict)
            )
            if query_missing:
                issues.add('Vues / requêtes dynamiques non reproduites')
                self.view_reports.append({'source_id':oid,'status':'unsupported','source':deepcopy(doc),'error':'Définition sans bloc de vue exploitable'})
            if props and (doc.get('property_settings') or doc.get('property_definitions')):
                issues.add('Portée des propriétés Anytype non reproduite (valeurs reprises en colonnes)')
            for warning in (doc.get('warnings') or []):
                detail = warning.get('message') or warning.get('code') if isinstance(warning, dict) else str(warning)
                issues.add('Lecture Anytype : '+str(detail)[:160])
            def load_file(fid, name, mime): return self.add_file(oid,fid,name,mime)
            markdown_embeds=[]
            if not is_bookmark(entries[oid],doc):
                doc=hydrate_bookmark_blocks(doc,self.source,self.sid,self.names)
            if is_bookmark(entries[oid],doc):
                url=bookmark_url(doc)
                markdown=titled_link(r['name'],url) if url else notice('notice.bookmark_not_imported')
                issues.add('Bookmark converti en lien titré' if url else 'Bookmark sans URL exploitable')
            else:
                markdown_embeds=[]
                markdown = render_blocks(doc,self.mapping,self.dest_sid,self.names,bool(plan.get('files')),
                                         load_file,issues,native_embeds=markdown_embeds,
                                         keep_underline=self.destination_version >= (0, 4, 1))
            # Source file objects may have no editor blocks at all. Keep their
            # actual payload as a downloadable attachment on the target page.
            source_type=(next((x for x in entries.values() if x['id']==oid),{}) .get('type') or '').casefold()
            if source_type in FILE_TYPES and not any(b.get('type') in FILE_TYPES for b in doc.get('blocks') or [] if isinstance(b,dict)):
                if plan.get('files'):
                    try:
                        uri=self.add_file(oid,oid,r['name'],None)
                        markdown += '\n\n'+(image_markdown(uri,getattr(uri,'name',r['name'])) if source_type=='image' else file_html(uri,getattr(uri,'name',r['name'])))
                    except APIError as e:
                        issues.add('Fichier source non importé : '+str(e))
                        markdown+='\n\n'+notice('notice.source_file')
                else:
                    issues.add('Fichier source non importé (option désactivée)')
            # Icons are object metadata, not body text. An optional native emoji
            # value is attempted at object creation; never duplicate it here.
            if cover_line:
                markdown='\n\n'.join(x for x in (cover_line,markdown) if x)
            if self.property_previews.get(oid):
                markdown='\n\n'.join([*self.property_previews[oid],markdown])
            if query_missing:
                markdown += '\n\n'+notice('notice.dynamic_views')
            description=(doc.get('properties') or {}).get('description') if isinstance(doc.get('properties'),dict) else None
            if description:
                description=replace_inline_links(str(description),self.mapping,self.dest_sid,self.names,issues)
                markdown='> '+description+'\n\n'+markdown
            if {'Lien vers un objet non importé','Mention vers un objet non importé'} & issues:
                markdown+='\n\n'+notice('notice.missing_links')
            # Property failures are also explicit in the target page.
            if r['errors']:
                markdown += '\n\n'+notice('notice.partial_properties')
            if markdown.strip():
                try:
                    write_markdown_with_embeds(self.target,self.dest_sid,r['target_id'],markdown,markdown_embeds,issues,markers=self.native_markup)
                except APIError as e:
                    # Retry a conservative representation rather than replacing
                    # the entire page by one warning and losing all its text.
                    if not is_bookmark(entries[oid],doc):
                        simpler_issues=set()
                        fallback=render_blocks(doc,self.mapping,self.dest_sid,self.names,
                                               bool(plan.get('files')),load_file,simpler_issues,
                                               rich_mode=False)
                        fallback=notice('notice.rich_rejected')+'\n\n'+fallback
                    else:
                        fallback=markdown
                    if cover_line:
                        fallback='\n\n'.join(x for x in (cover_line,fallback) if x)
                    if self.property_previews.get(oid):
                        fallback='\n\n'.join([*self.property_previews[oid],fallback])
                    try:
                        set_markdown(self.target,self.dest_sid,r['target_id'],self.page_markdown(fallback))
                        r['issues'].add('Rendu riche rejeté par Anytwo : version simplifiée importée')
                    except APIError as e2:
                        r['errors'].append(f'Contenu : {e}; tentative de repli : {e2}')
                        try:
                            set_markdown(self.target,self.dest_sid,r['target_id'],self.page_markdown(
                                         notice('notice.content_failed')))
                        except APIError:
                            r['errors'].append('Impossible d’insérer le message de remplacement dans la page.')
                if toc_tokens:
                    try:
                        replace_toc_markers(self.target,self.dest_sid,r['target_id'],toc_tokens,issues)
                    except APIError as exc:
                        issues.add('Sommaire non finalisé : '+str(exc))
            r['status'] = 'partial' if r['errors'] or r['issues'] else 'imported'
            output={'name':r['name'],'source_id':oid,'target_id':r['target_id'],
                    'status':r['status'],'reason':r['reason'],
                    'issues':sorted(issues),'errors':r['errors']}
            yield self.emit('object', **output)
        # Include objects that were unreadable or impossible to create.
        for oid,r in self.results.items():
            if r['target_id'] and oid in docs: continue
            yield self.emit('object',name=r['name'],source_id=oid,target_id=r['target_id'],
                            status='error',reason=r['reason'],issues=sorted(r['issues']),errors=r['errors'])
        # Chats remain excluded from normal page/type discovery. Only this
        # explicit option creates archive pages; never call target chat APIs.
        for history in archives:
            oid=history['id'];name='Archive du chat · '+history['name']
            r={'name':name,'source_id':oid,'target_id':None,'reason':['Option archive des chats de l’espace source'],
               'issues':set(history['warnings']),'errors':[],'status':'error'}
            self.results[oid]=r
            self.report.setdefault('chat_archives',[]).append(history)
            try:
                self.mapping[oid]=create_object(self.target,self.dest_sid,name,[])
                r['target_id']=self.mapping[oid]
                content=chat_markdown(history,bool(plan.get('files')),
                    lambda fid,label,mime:self.add_file(oid,fid,label,mime),r['issues'],
                    lambda text:replace_inline_links(text,self.mapping,self.dest_sid,self.names,r['issues']),
                    lambda ref:titled_link(self.names.get(ref,page_text('label.linked_object')),reference_link(ref,self.mapping,self.dest_sid,self.names)) if ref in self.mapping else None)
                set_markdown(self.target,self.dest_sid,r['target_id'],self.page_markdown(content))
                r['status']='partial' if r['issues'] else 'imported'
            except (APIError,ValueError,TypeError,KeyError) as exc:r['errors'].append(str(exc))
            yield self.emit('object',**{**r,'issues':sorted(r['issues'])})
        self.templates.defaults(entries, docs)
        for warning in sorted(self.templates.warnings):
            yield self.emit('message', message='! '+warning)
        removed = self.remove_import_artifacts(list(docs.values()), metadata)
        if removed:
            self.report['removed_properties'] = removed
            yield self.emit('message', message='Propriétés techniques Anytype retirées : '
                            + ', '.join(sorted({item['name'] for item in removed})) + '.')
        widgets = self.import_widgets(entries, docs)
        if widgets:
            self.report['widgets'] = widgets
            count = sum(widget['status'] == 'created' for widget in widgets)
            yield self.emit('message', message=f'Overview Anytwo : {count} widget(s) ajouté(s), {len(widgets)-count} déjà présent(s).')
        for warning in sorted(self.widget_warnings):
            yield self.emit('message', message='! '+warning)
        yield self.emit('summary',**self.finish_report())
