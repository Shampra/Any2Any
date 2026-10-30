"""Read-only source resolution and traversal for embedded Anytype views."""
from api_clients import APIError
from view_conversion import UnsupportedView

MISSING = object()


def source_value(doc, key, fallback=None):
    key=str(key).casefold()
    props=doc.get('properties') or {}
    aliases=doc.get('property_internal_keys') or {}
    for name,value in props.items():
        if key in (str(name).casefold(),str(aliases.get(name,'')).casefold()):
            return value
    for name,value in doc.items():
        if str(name).casefold()==key:
            return value
    if fallback:
        raw=fallback.get('raw') or fallback
        for name,value in raw.items():
            if str(name).casefold()==key:return value
    return MISSING


def matches_filter(node, doc, item):
    if not isinstance(node,dict):raise UnsupportedView('Filtre source mal formé')
    if 'filters' in node:
        if node.get('operator') not in ('and','or'):raise UnsupportedView('Groupe de filtres inconnu')
        values=[matches_filter(n,doc,item) for n in node['filters']]
        return all(values) if node['operator']=='and' else any(values)
    if any(node.get(k) for k in ('date_preset','nested_property','include_time')):
        raise UnsupportedView('Filtre dynamique non évalué pour la découverte')
    value=source_value(doc,node.get('property'),item)
    other=node.get('value');op=node.get('condition')
    if op=='exists':return value is not MISSING
    if value is MISSING:return op in ('not_equal','not_in')
    if op=='equal':return value==other
    if op=='not_equal':return value!=other
    if op in ('in','not_in','all_in'):
        if not isinstance(other,list):raise UnsupportedView('Filtre de liste sans liste')
        values=value if isinstance(value,list) else [value]
        return (all(v in values for v in other) if op=='all_in' else
                not any(v in other for v in values) if op=='not_in' else any(v in other for v in values))
    if op in ('greater','less','greater_or_equal','less_or_equal'):
        try:return {'greater':lambda:value>other,'less':lambda:value<other,
                    'greater_or_equal':lambda:value>=other,'less_or_equal':lambda:value<=other}[op]()
        except TypeError:return False
    raise UnsupportedView('Condition de découverte non prise en charge : '+str(op))


class SourceViews:
    def __init__(self,source,sid,inventory):
        self.source=source;self.sid=sid;self.inv=inventory;self.docs={}
        self.items={v['id']:v for v in inventory['all']}
        for members in inventory.get('members',{}).values():
            self.items.update({v['id']:v for v in members})
        self.cache={}

    def document(self,oid):
        if oid not in self.docs:
            doc=self.source.object_detail(self.sid,oid)
            if not isinstance(doc,dict):raise APIError('Définition de vue source invalide')
            self.docs[oid]={**doc,'id':oid}
        return self.docs[oid]

    def type_keys(self,value):
        raw=str(value);keys={raw,raw.removeprefix('type-').removeprefix('ot-')}
        for typ in self.inv['types']:
            if keys.intersection({str(typ.get('id')),str(typ.get('key'))}):
                keys.update((str(typ.get('id')),str(typ.get('key'))))
        return keys

    def resolve(self,doc,block):
        ref=block.get('object_id')
        host=self.document(ref) if ref else doc
        # The referenced object's kind is authoritative, not an inline flag.
        collection=(host.get('type_internal_key')=='collection' or host.get('type')=='collection')
        if not ref and block.get('is_collection'):collection=True
        if collection:
            ids=host.get('collection_items')
            if ids is None:ids=[v['id'] for v in self.inv['members'].get(ref or host.get('id'),[])]
            if not isinstance(ids,list):raise UnsupportedView('Liste de membres source invalide')
        else:
            source=host.get('query_source')
            if not isinstance(source,dict) and host.get('kind')=='object_type':
                key=host.get('internal_key')
                if not key:raise UnsupportedView('Identifiant interne du type source absent')
                source={'types':[key]}
            if not isinstance(source,dict):raise UnsupportedView('Source de vue non déterminée')
            types=set().union(*(self.type_keys(t) for t in source.get('types',[])))
            ids=[]
            for oid,item in self.items.items():
                if str(item.get('type')) in types:
                    ids.append(oid);continue
                if source.get('properties'):
                    detail=self.document(oid)
                    if any(source_value(detail,p,item) is not MISSING for p in source['properties']):ids.append(oid)
        views=block.get('views')
        if views is None:
            primary=next((b for b in host.get('blocks',[]) if isinstance(b,dict) and b.get('type')=='dataview'),{})
            views=host.get('views') or primary.get('views') or [{}]
        return host,list(dict.fromkeys(ids)),views

    def matching(self,doc,block):
        _,ids,views=self.resolve(doc,block)
        result=[]
        for oid in ids:
            if oid not in self.items:
                detail=self.document(oid)
                self.items[oid]={'id':oid,'name':str((detail.get('properties') or {}).get('name') or oid),
                                 'type':detail.get('type') or 'page','raw':detail}
            detail=None
            for view in views:
                filters=view.get('filters') or []
                if not filters:
                    result.append(oid);break
                if detail is None:detail=self.document(oid)
                if all(matches_filter(n,detail,self.items[oid]) for n in filters):
                    result.append(oid);break
        return result
