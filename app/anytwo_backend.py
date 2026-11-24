"""Shared Anytwo destination API for source adapters.

Keep a single implementation in api_clients during the incremental extraction.
These re-exports intentionally preserve the existing public API and tests. Both
source adapters must use this boundary rather than copy target write logic.
Source-specific discovery/conversion remains outside this module.
"""
import re
from api_clients import (
    APIError, Anytwo, target_write, create_space, create_collection,
    create_object, add_membership, list_columns, add_column, set_column_value,
    set_markdown, append_markdown, attach_file, get_file_info, create_editor_block,
    local_get, local_binary, unwrap_list, _segment,
)

def server_version(api):
    """Read the bundled server version once per import, with a legacy fallback."""
    if not isinstance(api, Anytwo):
        return ()
    try:
        health = local_get(api.port, '/v1/health', timeout=2)
    except APIError:
        return ()
    match = re.search(r'\bv?(\d+)\.(\d+)\.(\d+)\b', str(health.get('version', '')))
    return tuple(map(int, match.groups())) if match else ()

__all__=[
    'APIError','Anytwo','target_write','create_space','create_collection',
    'create_object','add_membership','list_columns','add_column','set_column_value',
    'set_markdown','append_markdown','attach_file','get_file_info','create_editor_block',
    'local_get','local_binary','unwrap_list','_segment','set_space_icon',
    'create_template','set_default_template',
]


def create_template(api, sid, name, collections, emoji=None):
    """The native client identifies templates by their reserved collection."""
    properties = {'any': {'name': name}, 'template': {'title': name, 'version': 1}}
    if emoji:
        properties['any']['icon'] = emoji
    result = target_write(api, f'/spaces/{_segment(sid)}/objects', {
        'type': 'page', 'collections': list(dict.fromkeys([*collections, 'template'])),
        'initialProperties': properties})
    if not result.get('objectId'):
        raise APIError('Création du template : identifiant cible absent.')
    return str(result['objectId'])


def set_default_template(api, sid, cid, template_id, *, preserve_existing=False):
    path = f'/spaces/{_segment(sid)}/collections/{_segment(cid)}'
    collection = local_get(api.port, '/v1'+path)
    current = (collection.get('meta') or {}).get('defaultTemplate')
    if preserve_existing and current and current != template_id:
        raise APIError('La collection cible conserve son template par défaut existant.')
    target_write(api, path, {'meta': {'defaultTemplate': template_id}}, method='PATCH')
    saved = local_get(api.port, '/v1'+path)
    if (saved.get('meta') or {}).get('defaultTemplate') != template_id:
        raise APIError('Le template par défaut n’a pas pu être confirmé.')


def set_space_icon(api,sid,name,content,mime):
    """Use the same index-object file URI as the native space icon picker."""
    space=local_get(api.port,f'/v1/spaces/{_segment(sid)}')
    oid=space.get('spaceIndexObjectId')
    if not oid:raise APIError('Objet index de l’espace indisponible pour son icône.')
    fid=attach_file(api,sid,oid,name,content,mime)
    target_write(api,f'/spaces/{_segment(sid)}',{'iconCid':f'any://f/{sid}/{fid}'},method='PATCH')
    return fid


def next_overview_position(previous):
    # Lexid positions use printable ASCII excluding quote and backslash.
    alphabet = ''.join(chr(code) for code in range(33, 127) if chr(code) not in ('"', '\\'))
    if not previous:
        return 'H!#,'
    if any(char not in alphabet for char in previous):
        raise APIError('Position de widget Overview inconnue')
    pad = (-len(previous)) % 4
    if pad:
        return previous + '!' * (pad - 1) + '#'
    digits = [alphabet.index(char) for char in previous]
    carry, digits[-1] = divmod(max(0, digits[-1] - 1) + 100, len(alphabet) - 1)
    digits[-1] += 1
    for index in range(len(digits) - 2, -1, -1):
        carry, digits[index] = divmod(digits[index] + carry, len(alphabet))
    if carry:
        return next_overview_position(previous + '!!!#')
    return ''.join(alphabet[digit] for digit in digits)


def add_overview_widgets(api, sid, widgets):
    """Append mapped page and collection widgets to the installed Overview."""
    space = f'/spaces/{_segment(sid)}'
    bundle_id = 'system:overview/v1'
    try:
        bundle = local_get(api.port, f'/v1{space}/bundles/{_segment(bundle_id)}').get('bundle', {})
    except APIError as exc:
        if exc.status != 404:
            raise
        setup = target_write(api, '/catalog/overview/setup', {'spaceId': sid})
        bundle = next((entry['bundle'] for entry in setup.get('bundles', [])
                       if entry.get('bundle', {}).get('id') == bundle_id), {})
    root = bundle.get('rootId')
    if not root:
        raise APIError('Overview indisponible : identifiant du module introuvable')
    parts = local_get(api.port, f'/v1{space}/types/{_segment(root)}/parts').get('parts', [])
    dataset = next((ds['collection'] for part in parts if part.get('key') == 'entries'
                    for ds in part.get('datasets', []) if ds.get('key') == 'entries'
                    and ds.get('module') == 'records' and ds.get('collection')), None)
    if not dataset:
        raise APIError('Overview indisponible : jeu de données des widgets introuvable')

    def read_rows():
        rows = {}
        offset = 0
        for _ in range(100):
            result = local_get(api.port, f'/v1{space}/query', method='POST', body={
                'objectId': root, 'dataset': dataset, 'sort': ['id'], 'offset': offset, 'limit': 200})
            batch = unwrap_list(result)
            if not batch or any(row['id'] in rows for row in batch):
                if result.get('hasNext') or batch:
                    raise APIError('Pagination des widgets Overview incomplète')
                return rows
            rows.update((row['id'], row) for row in batch)
            if not result.get('hasNext') and len(batch) < 200:
                return rows
            offset += len(batch)
        raise APIError('Trop de widgets Overview : lecture interrompue')

    existing = read_rows()
    position = max((row.get('pos') or '' for row in existing.values()), default='')
    records, expected, results = [], {}, []
    for widget in widgets:
        widget_id = 'w:' + widget['kind'] + ':' + widget['target_id']
        old = existing.get(widget_id)
        if old is not None and not old.get('removed'):
            results.append({**widget, 'layout': old.get('layout') or 'views', 'status': 'existing'})
            continue
        position = next_overview_position(position)
        layout = 'link' if widget['layout'] == 'link' else None
        fields = {'pos': position, 'removed': False}
        if layout:
            fields['layout'] = layout
        ops = [{'type': '$set', 'path': key, 'value': value} for key, value in fields.items()]
        if layout is None and old is not None and 'layout' in old:
            ops.append({'type': '$unset', 'path': 'layout'})
        records.append({'id': widget_id, 'upsert': True, 'ops': ops})
        expected[widget_id] = {**fields, 'layout': layout}
        results.append({**widget, 'status': 'created'})
    if records:
        result = target_write(api, space+'/modify', {'objectId': root, 'dataset': dataset, 'records': records})
        if result.get('rejections'):
            raise APIError('Anytwo a refusé un ou plusieurs widgets Overview')
        saved = read_rows()
        for widget_id, fields in expected.items():
            actual = saved.get(widget_id, {})
            if any(actual.get(key) != value for key, value in fields.items()):
                raise APIError('Un widget ajouté à Overview n’a pas pu être confirmé')
    return results
