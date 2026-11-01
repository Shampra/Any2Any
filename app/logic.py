"""Pure selection, indexing and simulation helpers. No write calls anywhere."""
from __future__ import annotations
import re
from urllib.parse import unquote
from collections import deque
from typing import Any
from api_clients import APIError


def is_collection(obj):
    # v2 layouts and older API shapes are deliberately both understood.
    raw = obj.get('raw') or {}
    type_ = str(obj.get('type') or '').lower()
    layout = str(obj.get('layout') or raw.get('layout') or '').lower()
    return type_ in ('collection', 'object_type_collection') or layout == 'collection' or raw.get('kind') == 'collection'


# Anytype exposes discussion/chat as objects in some client builds. These
# represent conversations, not importable pages, and must stay out of the UI,
# including collection membership and linked-object discovery.
NON_IMPORTABLE_TYPES = {'chat', 'chats', 'discussion', 'discussions',
                        'message', 'messages', 'space_chat', 'chat_message'}


def is_conversation(obj):
    raw = obj.get('raw') or obj
    values = (obj.get('type'), obj.get('layout'), raw.get('kind'),
              raw.get('layout'), raw.get('type'), raw.get('type_key'),
              raw.get('typeKey'))
    for value in values:
        if isinstance(value, dict):
            value = value.get('key') or value.get('name') or value.get('id')
        if str(value or '').casefold().strip().replace('-', '_') in NON_IMPORTABLE_TYPES:
            return True
    if raw.get('isChat') is True or raw.get('is_chat') is True or raw.get('isDiscussion') is True:
        return True
    return False


GENERIC_TYPES = {'page', 'pages', 'note', 'notes'}

# These are intrinsic Anytwo fields, not collection columns. Names, icons and
# type identifiers are intrinsic to object creation as well.
INTRINSIC_PROPERTIES = {
    'name', 'title', 'icon', 'type', 'id', 'createdate', 'creationdate',
    'created_date', 'created_time', 'created_at', 'creation_date', 'createdby',
    'created_by', 'creator', 'author', 'lastmodifieddate', 'last_modified_date',
    'last_modified_by', 'modifiedby', 'modified_by', 'modifiedat',
    'modified_at', 'lastmodifiedby', 'last_modified_time', 'updated_at',
    # Anytype internal metadata, never user-created data columns.
    'resolved_layout', 'resolvedlayout', 'origin', 'created_in_context',
    'created_in_context_ref', 'createdincontext', 'layout_align',
    'internal_key', 'is_archived', 'revision', 'last_opened_date',
    'space_id', 'workspace_id', 'sync_status', 'created_in_context_ref',
    'import_type', 'image_kind', 'participant_permissions', 'participant_status',
}


def has_custom_fields(source, key='properties'):
    """True/False when fields are explicit; None when API omitted them.

    Missing fields are *not* proof that an object is property-free. This is
    deliberately conservative to avoid selecting 'without collection' by mistake.
    """
    if not isinstance(source, dict):
        return None
    fields = source.get(key)
    if fields is None:
        return None
    if not isinstance(fields, (dict, list)):
        return None
    if isinstance(fields, dict):
        identifiers = fields.keys()
    else:
        identifiers = [(f.get('property') or f.get('key') or f.get('name') or f.get('id') or '')
                       for f in fields if isinstance(f, dict)]
    for field in identifiers:
        normalized = str(field).casefold().replace('-', '_').replace(' ', '_')
        if normalized and normalized not in INTRINSIC_PROPERTIES:
            return True
    return False


def property_state(typ, items):
    """Classify a type as 'yes', 'no', or 'unknown' w.r.t. custom fields."""
    type_fields = has_custom_fields(typ, 'property_definitions')
    if type_fields is None:
        type_fields = has_custom_fields(typ, 'properties')
    object_fields = [has_custom_fields(x.get('raw', x)) for x in items]
    results = [type_fields, *object_fields]
    if True in results:
        return 'yes'
    if results and all(v is False for v in results):
        return 'no'
    return 'unknown'


def requires_collection(typ):
    # Without a confirmed negative, assume columns may exist.
    return typ.get('property_state', 'unknown') != 'no'



def is_generic_type(typ):
    return str(typ.get('key', '')).casefold() in GENERIC_TYPES or str(typ.get('layout', '')).casefold() == 'note'


def build_inventory(api, space_id, progress=None):
    say = progress or (lambda x: None)
    say('Lecture des objets et des types de l’espace…')
    all_objects = [o for o in api.objects(space_id) if not is_conversation(o)]
    types_list = [t for t in api.types(space_id) if not is_conversation(t)]
    collections = sorted((x for x in all_objects if is_collection(x)), key=lambda x: x['name'].casefold())
    members = {}
    claimed = set()
    for i, col in enumerate(collections, 1):
        say(f'Analyse des collections ({i}/{len(collections)}) : {col["name"]}')
        items = [o for o in api.members(space_id, col['id']) if not is_conversation(o)]
        members[col['id']] = items
        claimed.update(item['id'] for item in items)
    # Membership in a collection is independent of an object's Type: never hide
    # a Book just because it also belongs to a user-created collection.
    objects = [x for x in all_objects if not is_collection(x)]
    known = {str(t['key']).casefold(): t for t in types_list}
    for item in objects:
        key = str(item.get('type', '')).strip()
        if not key:
            key = 'unknown'
        if key.casefold() not in known:
            known[key.casefold()] = {'id': key, 'key': key, 'name': key.title(), 'layout': item.get('layout', '')}
    groups = []
    for t in known.values():
        if is_conversation(t):
            continue
        key = str(t['key']).casefold()
        aliases = {key, str(t['id']).casefold()}
        items = sorted((x for x in objects if str(x.get('type', '')).casefold() in aliases),
                       key=lambda x: x['name'].casefold())
        if items:
            meta = t
            if is_generic_type(t) and has_custom_fields(t, 'property_definitions') is None:
                # A Page/Note might have custom columns even though the basic
                # type list is sparse. Probe the type once, not each object.
                fetch = getattr(api, 'type_detail', None)
                if fetch:
                    try:
                        detail = fetch(space_id, t['key'])
                        if isinstance(detail, dict):
                            meta = {**t, **detail}
                    except APIError:
                        pass
            state = property_state(meta, items)
            groups.append({'id': t['id'], 'key': t['key'], 'name': t['name'], 'layout': t.get('layout', ''),
                           'generic': is_generic_type(t), 'property_state': state,
                           'requires_collection': state != 'no', 'items': items})
    groups.sort(key=lambda t: (t['name'].casefold(), t['key']))
    standalone = sorted((x for x in objects if x['id'] not in claimed), key=lambda x: x['name'].casefold())
    return {'all': all_objects, 'collections': collections, 'members': members,
            'types': groups, 'objects': objects, 'standalone': standalone,
            'stats': {'total': len(all_objects), 'collections': len(collections),
                      'types': len(groups), 'standalone': len(standalone)}}


def summary_inventory(inventory):
    return {'collections': [{**{k: col[k] for k in ('id', 'name', 'type')},
                              'count': len(inventory['members'].get(col['id'], []))}
                             for col in inventory['collections']],
            'types': [{'id': t['id'], 'key': t['key'], 'name': t['name'],
                       'generic': t['generic'], 'property_state': t.get('property_state', 'unknown'),
                       'requires_collection': requires_collection(t), 'count': len(t['items']),
                       'items': [{k: obj[k] for k in ('id', 'name', 'type')} for obj in t['items']]}
                      for t in inventory['types']],
            'stats': inventory['stats']}


def identify_links(document, known_ids, self_id):
    """Conservative references (object IDs, not arbitrary words or external URLs)."""
    refs = set()
    names = {'target', 'target_id', 'targetId', 'object_id', 'objectId', 'ref',
             'object', 'linked_object', 'linkedObject', 'links', 'objects', 'references',
             'relation', 'relations', 'value', 'ids', 'id'}

    def visit(value, key='', depth=0):
        if depth > 26:
            return
        if isinstance(value, dict):
            for k, v in value.items():
                visit(v, k, depth+1)
        elif isinstance(value, list):
            for v in value:
                visit(v, key, depth+1)
        elif isinstance(value, str):
            if value in known_ids and value != self_id and (key in names or key.endswith('_id')):
                refs.add(value)
            if 'anytype://object?objectId=' in value:
                for match in re.finditer(r'anytype://object\?objectId=([^)&\s]+)', value):
                    oid = unquote(match.group(1))
                    if oid in known_ids and oid != self_id:
                        refs.add(oid)
    visit(document)
    return refs


def simulate(anytype, inventory, plan):
    """Yield a safe read-only preview; the importer is not implemented yet."""
    selection = plan.get('selection') or {}
    kind = selection.get('kind')
    source_space = plan.get('source_space') or {}
    if kind not in ('space', 'collection', 'types', 'objects'):
        raise APIError('Sélectionnez un espace, une collection, un ou plusieurs types ou objets.')
    target = plan.get('target') or {}
    if not (target.get('space_name') or '').strip():
        raise APIError('Définissez un espace de destination.')
    if target.get('collection_mode') == 'create' and not (target.get('collection_name') or '').strip():
        raise APIError('Indiquez le nom de la nouvelle collection.')
    selected = []
    additional_collections = []
    if kind == 'space':
        selected = inventory['objects']+inventory['collections']
        yield f'ESPACE : {source_space.get("name", "?")} — {len(selected)} objets, {len(inventory["collections"])} collections et {len(inventory["types"])} types.'
        additional_collections = [x['name'] for x in inventory['collections']]
        additional_collections += [t['name'] for t in inventory['types'] if not t['generic'] or requires_collection(t)]
    elif kind == 'collection':
        cid = selection.get('collection_id')
        collection = next((x for x in inventory['collections'] if x['id'] == cid), None)
        if not collection:
            raise APIError('Collection source introuvable : rechargez la liste.')
        selected = inventory['members'].get(cid, [])
        yield f'COLLECTION : {collection["name"]} — {len(selected)} éléments.'
    elif kind == 'types':
        keys = set(selection.get('type_keys') or [])
        matched = [t for t in inventory['types'] if t['key'] in keys]
        if not keys or len(keys) != len(matched):
            raise APIError('Types sélectionnés introuvables : rechargez l’espace.')
        mappings = {x.get('key'): x for x in (target.get('type_mappings') or [])}
        ids = set()
        for t in matched:
            setting = mappings.get(t['key'])
            if not setting:
                raise APIError(f'Correspondance manquante pour le type « {t["name"]} ».')
            coll_mode = setting.get('collection_mode')
            if coll_mode not in ('none', 'existing', 'create'):
                raise APIError(f'Destination incorrecte pour le type « {t["name"]} ».')
            if coll_mode == 'none' and requires_collection(t):
                raise APIError(f'Le type « {t["name"]} » doit être importé dans une collection pour conserver ses propriétés.')
            if coll_mode == 'create' and not str(setting.get('collection_name') or '').strip():
                raise APIError(f'Donnez un nom à la collection du type « {t["name"]} ».')
            yield f'TYPE : {t["name"]} — {len(t["items"])} objets ; destination : '+(
                'sans collection' if coll_mode == 'none' else
                ('collection existante « '+str(setting.get('collection_name'))+' »' if coll_mode == 'existing'
                 else 'nouvelle collection « '+str(setting.get('collection_name'))+' »'))+'.'
            for item in t['items']:
                if item['id'] not in ids:
                    ids.add(item['id']); selected.append(item)
        yield f'SÉLECTION : {len(selected)} objets distincts (déduplication entre types).'
    else:
        chosen = set(selection.get('ids') or [])
        selected = [x for x in inventory['objects'] if x['id'] in chosen]
        if not chosen or len(selected) != len(chosen):
            raise APIError('La sélection a changé : rechargez la liste des objets.')
        yield f'OBJETS : {len(selected)} élément(s) sélectionné(s) individuellement.'
        mappings = {x.get('key'): x for x in (target.get('type_mappings') or [])}
        required = [t for t in inventory['types'] if requires_collection(t)
                    and any(obj['id'] in chosen for obj in t['items'])]
        for t in required:
            setting = mappings.get(t['key'])
            if not setting or setting.get('collection_mode') not in ('create', 'existing'):
                raise APIError(f'Collection de destination obligatoire pour le type « {t["name"]} » (propriétés à préserver).')
            if setting['collection_mode'] == 'create' and not str(setting.get('collection_name') or '').strip():
                raise APIError(f'Nom de collection manquant pour le type « {t["name"]} ».')
            yield f'→ {"Création simulée" if setting["collection_mode"] == "create" else "Utilisation"} de la collection « {setting.get("collection_name")} » pour le type « {t["name"]} ». '

    if target.get('space_mode') == 'existing':
        yield f'→ Utilisation de l’espace Anytwo « {target["space_name"]} ».'
    else:
        yield f'→ Création simulée de l’espace Anytwo « {target["space_name"]} ».'
    if kind == 'space':
        for name in sorted(set(additional_collections), key=str.casefold):
            yield f'→ Création simulée de la collection « {name} » (collection ou type structuré).'
        yield '→ Les types sans propriétés confirmées peuvent rester hors collection ; en cas de doute, une collection est prévue pour préserver les propriétés.'
    elif kind != 'types':
        if target.get('collection_mode') == 'create':
            yield f'→ Création simulée de la collection « {target["collection_name"]} ».'
        elif target.get('collection_mode') == 'existing':
            yield f'→ Utilisation de la collection « {target.get("collection_name", "?")} ».'

    files = bool(plan.get('files'))
    follow = bool(plan.get('follow_links')) and kind!='space'
    yield f'OPTIONS : fichiers {"inclus" if files else "ignorés"}, liens {"suivis" if follow else "non suivis"}.'
    if files:
        yield 'FICHIERS : transfert prévu, pièces jointes non inspectées dans ce prototype.'
    indexed = {x['id']: x for x in inventory['all']}
    for items in inventory['members'].values():
        indexed.update({x['id']: x for x in items})
    ids = set(indexed)
    from source_views import SourceViews
    from view_conversion import UnsupportedView
    view_sources=SourceViews(anytype,source_space['id'],inventory)
    queued = deque(selected)
    visited = set()
    selected_ids = {x['id'] for x in selected}
    extra = 0
    errors = 0
    while queued:
        obj = queued.popleft()
        oid = obj['id']
        if oid in visited:
            continue
        visited.add(oid)
        yield f'OBJET : {obj["name"]} — serait importé.'
        try:
            doc = view_sources.document(oid)
            structural=set();view_ids=set()
            for block in doc.get('blocks') or []:
                if not isinstance(block,dict) or block.get('type')!='dataview':continue
                if block.get('object_id'):structural.add(block['object_id'])
                if follow:
                    try:view_ids.update(view_sources.matching(doc,block))
                    except (APIError,UnsupportedView,ValueError,TypeError,KeyError) as exc:
                        yield '  ! Documents de vue intégrée non résolus : '+str(exc)
            indexed.update(view_sources.items)
            for ref in sorted((identify_links(doc, ids, oid)-structural)|view_ids):
                target_name = indexed[ref]['name']
                if ref in visited or any(x['id'] == ref for x in queued):
                    continue
                if follow:
                    queued.append(indexed[ref])
                    if ref not in selected_ids:
                        extra += 1
                    if ref in view_ids:yield f'  ↳ Document de vue intégrée « {target_name} » : objet ajouté au périmètre.'
                    else:yield f'  ↳ Lien vers « {target_name} » : objet ajouté au périmètre.'
                elif ref not in selected_ids:
                    yield f'  ↳ Lien vers « {target_name} » : non suivi (option désactivée).'
        except APIError as exc:
            errors += 1
            yield f'  ! Impossible d’inspecter les liens : {exc}'
        if len(visited) + len(queued) > 5000:
            yield '! Limite de sécurité de 5 000 objets atteinte : analyse arrêtée.'
            break
    yield f'BILAN : {len(visited)} objet(s) prévu(s), {extra} ajouté(s) par les liens, {errors} erreur(s) de lecture.'
    if plan.get('archive_chats'):
        from chat_archives import histories
        archives=histories(anytype,source_space['id'])
        for chat in archives:
            yield f'ARCHIVE CHAT : {chat["name"]} — {len(chat["messages"])} message(s), une page prévue.'
        yield f'CHATS : {len(archives)} archive(s) supplémentaire(s), tous les chats de l’espace source.'
    else:
        yield 'CHATS : exclus (option archives désactivée).'
    yield 'TERMINÉ : simulation uniquement. Aucun objet n’a été créé, modifié ou téléchargé.'
