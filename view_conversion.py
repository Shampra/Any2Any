"""Source-faithful view conversion. Unsupported predicates fail closed.

Only documented server query shapes are generated. Client-specific settings
are archived separately; archiving is never reported as a working conversion.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json

from api_clients import APIError, target_write, _segment


class UnsupportedView(ValueError):
    pass


def choice_options(options, key_factory):
    result = {}
    for index, item in enumerate(options or []):
        item = {'name': item} if isinstance(item, str) else item
        if not isinstance(item, dict) or not isinstance(item.get('name'), str):
            continue
        name = item['name']
        key = key_factory(name, name)
        if key in result:
            raise ValueError('Options homonymes : identité ambiguë pour ' + name)
        result[key] = {'name': name, 'pos': f'a{index:06d}'}
        if item.get('color'):
            result[key]['color'] = item['color']
    return result


def enrich_descriptor(spec, form, issues=None):
    """Translate supported settings and archive the others without inventing rules."""
    form = deepcopy(form)
    saved = {k: spec[k] for k in ('include_time', 'max_count', 'readonly',
             'default_value', 'object_types', 'description', 'section') if k in spec}
    if saved:
        # JSON text avoids interpreting source property names as dotted CRDT paths.
        form['any2any'] = {'sourceSettings': json.dumps(saved, ensure_ascii=False)}
    if form.get('type') == 'choice':
        form.setdefault('config', {})['optionSort'] = 'manual'
    if spec.get('format') == 'date' and 'include_time' in spec:
        form['type'] = 'datetime' if spec['include_time'] else 'date'
    if spec.get('format') == 'objects' and 'max_count' in spec:
        form.setdefault('config', {})['multiple'] = spec['max_count'] != 1
    if issues is not None:
        for key in ('readonly', 'default_value', 'max_count'):
            if key in spec and not (key == 'max_count' and spec.get('format') == 'objects' and spec[key] == 1):
                issues.add(f'Paramètre {key} de « {spec.get("name", "propriété")} » conservé en métadonnées, non appliqué')
    return form


def modify_records(api, sid, oid, dataset, rows):
    result = target_write(api, f'/spaces/{_segment(sid)}/modify', {
        'objectId': oid, 'dataset': dataset,
        'records': [{'id': row['id'], 'upsert': True,
                     'ops': [{'type': '$set', 'path': k, 'value': v}
                             for k, v in row.items() if k != 'id']} for row in rows]})
    if result.get('rejections'):
        raise APIError('Écriture de vue partiellement refusée : ' + json.dumps(result['rejections'], ensure_ascii=False))
    return result


def combine(operator, nodes):
    # Keep empty logical groups: AND([]) and OR([]) are not interchangeable.
    if len(nodes) == 1:
        return nodes[0]
    return {operator: nodes}


class ViewConverter:
    def __init__(self, bindings, mapping, type_collections, metadata):
        self.bindings = bindings
        self.mapping = mapping
        self.type_collections = type_collections
        self.metadata = metadata

    def fields(self, name):
        if str(name).casefold() == 'name':
            return [('any.name', {'format': 'text'}, {})]
        found = self.bindings.get(str(name).casefold(), [])
        if not found:
            raise UnsupportedView('Propriété non transposée : ' + str(name))
        return found

    def value(self, value, spec, form):
        fmt = spec.get('format')
        if isinstance(value, str) and value.startswith('_filter_template_'):
            raise UnsupportedView('Filtre dynamique dépendant du contexte Anytype')
        if fmt in ('select', 'multi_select'):
            options = form.get('options', {})
            keys = {v.get('name'): k for k, v in options.items()}
            def option(v):
                if v not in keys:
                    raise UnsupportedView('Option de filtre introuvable : ' + str(v))
                return keys[v]
            return [option(v) for v in value] if isinstance(value, list) else option(value)
        if fmt in ('objects', 'files'):
            def reference(v):
                if v not in self.mapping or fmt == 'files':
                    raise UnsupportedView('Référence de filtre non importée : ' + str(v))
                return 'any://' + self.mapping[v]
            return [reference(v) for v in value] if isinstance(value, list) else reference(value)
        if fmt == 'date' and value is not None:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                value = datetime.fromtimestamp(value, timezone.utc).isoformat().replace('+00:00', 'Z')
            if not isinstance(value, str):
                raise UnsupportedView('Date de filtre invalide')
            if len(value) == 10:
                value += 'T00:00:00Z'
            return {'$date': value}
        return value

    def predicate(self, node):
        if not isinstance(node, dict):
            raise UnsupportedView('Filtre source mal formé')
        if 'filters' in node:
            op = node.get('operator')
            if op not in ('and', 'or') or not isinstance(node['filters'], list):
                raise UnsupportedView('Groupe de filtres inconnu')
            return combine('$' + op, [self.predicate(n) for n in node['filters']])
        if node.get('date_preset') or node.get('nested_property') or node.get('include_time'):
            raise UnsupportedView('Date relative, heure ou sous-propriété de filtre non transposable exactement')
        condition = node.get('condition')
        # Empty conditions and array equality differ between engines: refuse rather
        # than widen a view by silently dropping a predicate.
        scalar_ops = {'equal': '$eq', 'not_equal': '$ne', 'greater': '$gt',
                      'less': '$lt', 'greater_or_equal': '$gte', 'less_or_equal': '$lte',
                      'in': '$in', 'not_in': '$nin', 'all_in': '$all'}
        variants = []
        for path, spec, form in self.fields(node.get('property')):
            if spec.get('format')=='date' and condition in ('less','less_or_equal'):
                raise UnsupportedView('Comparaison de dates : comportement Anytype des valeurs vides non reproduit')
            if condition == 'exists':
                rule = {'$exists': True}
            elif condition in ('contains', 'not_contains') and spec.get('format') in ('text', 'url', 'email', 'phone'):
                raise UnsupportedView('Comparaison de texte : collation Anytype non garantie')
            elif condition in scalar_ops:
                if spec.get('format') in ('select', 'multi_select', 'objects', 'files') and condition in ('equal', 'not_equal'):
                    raise UnsupportedView('Égalité de listes Anytype non garantie')
                value = self.value(node.get('value'), spec, form)
                if condition in ('in', 'not_in', 'all_in') and not isinstance(value, list):
                    raise UnsupportedView('Filtre de liste sans liste')
                rule = {scalar_ops[condition]: value}
            else:
                raise UnsupportedView('Condition non transposable : ' + str(condition))
            part = {path: rule}
            # Scope each property-owner variant so missing fields in other
            # collections cannot satisfy negation predicates.
            if not path.startswith('any.'):
                part = {'$and': [{'any.collections': path.split('.')[0]}, part]}
            variants.append(part)
        return combine('$or', variants)

    def query(self, block, host, members):
        if block.get('source'):
            raise UnsupportedView('Source de requête historique non résolue')
        if block.get('is_collection') or host.get('type_internal_key') == 'collection' or host.get('type') == 'collection':
            source_ids = host.get('collection_items', members)
            if not isinstance(source_ids, list):
                raise UnsupportedView('Liste de membres invalide')
            return {'id': {'$in': [self.mapping[v] for v in source_ids if v in self.mapping]}}
        source = host.get('query_source')
        if not isinstance(source, dict):
            if host.get('kind') == 'object_type':
                source = {'types': [host.get('internal_key')]}
            else:
                raise UnsupportedView('Source de vue non déterminée')
        parts = []
        for typ in source.get('types', []):
            key = str(typ).removeprefix('type-').removeprefix('ot-')
            cid = self.type_collections.get(key)
            if not cid:
                raise UnsupportedView('Type source non importé : ' + str(typ))
            parts.append({'any.collections': cid})
        for prop in source.get('properties', []):
            parts.append(self.predicate({'property': prop, 'condition': 'exists'}))
        # Explicitly empty source stays empty, never means all destination objects.
        return combine('$or', parts) if parts else {'id': {'$in': []}}

    def convert(self, view, source_filter):
        layout = {'table': 'table', 'grid': 'table', 'list': 'list', 'kanban': 'board', 'gallery': 'gallery'}.get(view.get('type', 'table'))
        if layout is None:
            raise UnsupportedView('Disposition non vérifiée : ' + str(view.get('type')))
        predicates = [source_filter]
        predicates.extend(self.predicate(f) for f in view.get('filters', []))
        query = {'type': 'plain', 'filter': combine('$and', predicates)}
        sorts = []
        for item in view.get('sorts', []):
            if item.get('direction', 'asc') not in ('asc', 'desc') or any(item.get(k) for k in ('custom_order', 'empty_placement', 'include_time', 'no_collate')):
                raise UnsupportedView('Tri personnalisé ou placement des valeurs vides non transposable')
            fields = self.fields(item.get('property'))
            if len(fields) != 1:
                raise UnsupportedView('Tri sur une propriété répartie entre plusieurs collections')
            sorts.append(('-' if item.get('direction') == 'desc' else '') + fields[0][0])
        if sorts:
            query['sort'] = sorts + ['id']
        if view.get('group_by'):
            fields = self.fields(view['group_by'])
            if len(fields) != 1:
                raise UnsupportedView('Regroupement ambigu entre collections')
            query['groupBy'] = fields[0][0]
        # Column vocabulary is client-owned. Preserve source exactly in a vendor
        # bag, never pretend it controls the client's actual widths or visibility.
        settings = {'any2any': {'sourceView': json.dumps(view, ensure_ascii=False)}}
        return layout, query, settings


def create_saved_views(api, sid, host_id, block, source_host, members, converter, issues, root_id=None, table_key='table-0'):
    source_filter = converter.query(block, source_host, members)
    if block.get('is_collection') or source_host.get('type_internal_key')=='collection':
        omitted=[v for v in source_host.get('collection_items',members) if v not in converter.mapping]
        if omitted:issues.add(f'Vue limitée au périmètre importé : {len(omitted)} membre(s) source non importé(s)')
    converted = []
    failed = []
    for index, view in enumerate(block.get('views') or [{}]):
        try:
            layout, query, settings = converter.convert(view, source_filter)
            converted.append({'id': f'{table_key}-view-{index}', 'name': view.get('name') or 'Vue Anytype',
                              'pos': f'a{index:06d}', 'dataview': table_key,
                              'layout': layout, 'query': query, 'layoutSettings': settings})
        except (UnsupportedView, TypeError, ValueError) as exc:
            failed.append(str(exc))
    if not converted:
        raise UnsupportedView('; '.join(failed))
    if root_id is None:
        root = target_write(api, f'/spaces/{_segment(sid)}/objects', {
            'type': 'dataview', 'initialProperties': {'any': {'name': 'Vues Anytype'}, 'dataview': {'host': host_id}}})
        root_id = root.get('objectId')
    if not root_id:
        raise APIError('Objet de vues créé sans identifiant')
    modify_records(api, sid, root_id, 'dataviews', [{'id': table_key, 'name': block.get('name') or 'Anytype', 'pos': 'a'+table_key}])
    modify_records(api, sid, root_id, 'views', converted)
    issues.add('Vues enregistrées rattachées à la page ; emplacement et rendu intégrés à vérifier dans Anytwo')
    if any(v.get('columns') or any(k in v for k in ('card_size', 'hide_icon', 'groups', 'object_orders', 'wrap_content', 'alternate_rows', 'cover_property', 'end_property', 'default_type_id', 'default_template_id')) for v in block.get('views', [])):
        issues.add('Réglages visuels et ordre manuel des vues archivés, non appliqués au client Anytwo')
    for message in failed:
        issues.add('Vue non convertie : ' + message)
    return root_id, failed
