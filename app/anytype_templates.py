"""Read Anytype templates and attach native Anytwo templates to imported owners."""
from copy import deepcopy

from anytwo_backend import APIError, set_column_value, set_default_template
from source_views import source_value, MISSING


def is_template(doc):
    return (doc.get('kind') in ('template', 'bundled_template')
            or doc.get('type') == 'template' or bool(doc.get('template_for')))


class Templates:
    def __init__(self, engine):
        self.engine = engine
        self.rows = {}
        self.warnings = set()
        self.collection_templates = {}

    def type_key(self, value):
        value = str(value or '')
        aliases = {value, value.removeprefix('type-').removeprefix('ot-')}
        for typ in self.engine.inv['types']:
            if aliases.intersection({str(typ.get(k, '')) for k in ('id', 'key', 'name')}):
                return typ['key']
        return value

    def discover(self, entries, docs, reasons, collections=()):
        engine = self.engine
        used = {self.type_key(item.get('type')) for oid, item in entries.items()
                if not is_template(docs.get(oid, {}))}
        used.update(self.type_key(doc.get('template_for')) for doc in docs.values() if is_template(doc))
        required = set()
        for collection in collections:
            try:
                document = engine.source_views.document(collection['id'])
            except (APIError, ValueError, KeyError, TypeError):
                continue
            for block in document.get('blocks', []):
                if block.get('type') != 'dataview':
                    continue
                for view in block.get('views') or []:
                    if view.get('default_type_id'):
                        used.add(self.type_key(view['default_type_id']))
                    if view.get('default_template_id') and view['default_template_id'] not in ('blank', 'none'):
                        oid = view['default_template_id']
                        required.add(oid)
                        self.collection_templates.setdefault(oid, set()).add(collection['id'])
        read = getattr(engine.source, 'templates', None)
        rows = []
        if (used or required) and read is not None:
            try:
                rows = read(engine.sid)
            except APIError as exc:
                self.warnings.add('Templates source non lus : '+str(exc))
        for oid, doc in list(docs.items()):
            if is_template(doc):
                self.rows[oid] = {'id':oid, 'template_for':self.type_key(doc.get('template_for'))}
        for row in rows:
            key = self.type_key(row.get('template_for'))
            if key not in used and row.get('id') not in self.rows and row.get('id') not in required:
                continue
            oid = row.get('id')
            if not oid:
                continue
            try:
                doc = docs.get(oid) or engine.source_views.document(oid)
            except (APIError, ValueError) as exc:
                self.warnings.add('Template source inaccessible : '+str(exc))
                continue
            self.rows[oid] = {**row, 'template_for':key}
            docs[oid] = doc
        for oid, row in self.rows.items():
            doc = docs[oid]
            key = row['template_for']
            name = str((doc.get('properties') or {}).get('name') or row.get('name') or 'Template Anytype')
            entries[oid] = {'id':oid, 'name':name, 'type':key}
            engine.names[oid] = name
            reasons.setdefault(oid, ['Template du type source « '+key+' »'])
        missing = required - self.rows.keys()
        if missing:
            self.warnings.add('Templates référencés par une vue mais indisponibles : '+str(len(missing)))

    def scopes(self, source_id, entries):
        engine = self.engine
        key = self.rows[source_id]['template_for']
        scopes = []
        for collection_source in sorted(self.collection_templates.get(source_id, set())):
            cid = engine.col_cache.get('collection:'+collection_source)
            if cid and cid not in scopes:
                scopes.append(cid)
        for oid, item in entries.items():
            if oid in self.rows or self.type_key(item.get('type')) != key:
                continue
            for cid in sorted(engine.memberships.get(oid, set())):
                if cid not in scopes:
                    scopes.append(cid)
        return scopes

    def mirror_values(self):
        """One source template can supply properties to several collections."""
        engine = self.engine
        for oid in self.rows:
            if oid not in engine.mapping:
                continue
            result = engine.results[oid]
            for cid in engine.memberships.get(oid, set()):
                if cid == engine.property_owner.get(oid):
                    continue
                for saved in engine.written_properties.get(oid, {}).values():
                    try:
                        pid, form = engine.property(cid, saved['label'], saved['format'], None,
                            result['issues'], {}, override=(saved['kind'], deepcopy(saved['form'])))
                        value = deepcopy(saved['value'])
                        if saved['format'] in ('select', 'multi_select'):
                            keys = {opt['name']:key for key,opt in form.get('options', {}).items()}
                            value = [keys[saved['form']['options'][key]['name']] for key in value]
                        set_column_value(engine.target, engine.dest_sid, engine.mapping[oid], cid, pid, value)
                    except (APIError, KeyError, TypeError, ValueError) as exc:
                        result['errors'].append('Propriété de template non reproduite : '+str(exc))

    def defaults(self, entries, docs):
        engine = self.engine
        choices = {}
        for oid, row in self.rows.items():
            if row.get('default'):
                for cid in engine.memberships.get(oid, set()):
                    choices.setdefault(cid, set()).add(oid)
        # A collection's active view takes precedence over the type-wide default.
        for source_id, doc in engine.collection_documents.items():
            cid = engine.col_cache.get('collection:'+source_id)
            for block in doc.get('blocks', []):
                if block.get('type') != 'dataview':
                    continue
                views = list(block.get('views') or [])
                active = block.get('active_view') or block.get('active_view_id')
                if active:
                    views.sort(key=lambda view:view.get('id') != active)
                if views and 'default_template_id' in views[0]:
                    selected = views[0]['default_template_id']
                    choices[cid] = {selected} if selected and selected not in ('blank', 'none') else set()
                configured = {v['default_template_id'] for v in views if v.get('default_template_id')}
                if len(configured) > 1:
                    self.warnings.add('Templates différents selon les vues : seul le défaut de la vue active est appliqué à la collection Anytwo')
        installed = []
        for cid, source_ids in choices.items():
            if not cid or not source_ids:
                continue
            if len(source_ids) != 1:
                self.warnings.add('Templates par défaut concurrents dans une collection cible : aucun défaut arbitraire appliqué')
                continue
            oid = next(iter(source_ids))
            result = engine.results.get(oid, {})
            if not result.get('target_id') or result.get('errors'):
                self.warnings.add('Template par défaut non appliqué : template non importé complètement')
                continue
            try:
                set_default_template(engine.target, engine.dest_sid, cid, engine.mapping[oid],
                    preserve_existing=cid in engine.existing_collections)
                installed.append({'collection_id':cid, 'source_id':oid, 'target_id':engine.mapping[oid]})
            except APIError as exc:
                self.warnings.add('Template par défaut non appliqué : '+str(exc))
        # Keep the source-template lineage that the native client can display.
        for oid, doc in docs.items():
            if oid in self.rows or oid not in engine.mapping:
                continue
            ref = source_value(doc, 'source_object')
            if ref is MISSING:
                continue
            refs = ref if isinstance(ref, list) else [ref]
            templates = [value for value in refs if value in self.rows and value in engine.mapping]
            if len(templates) == 1:
                try:
                    set_column_value(engine.target, engine.dest_sid, engine.mapping[oid], 'any', 'template',
                                     {'id':engine.mapping[templates[0]], 'version':1})
                except APIError as exc:
                    self.warnings.add('Référence au template non appliquée : '+str(exc))
        engine.report['templates'] = {'defaults':installed, 'objects':[
            {'source_id':oid, 'target_id':engine.mapping.get(oid), 'template_for':row['template_for']}
            for oid,row in self.rows.items()]}
