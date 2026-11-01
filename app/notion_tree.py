"""Notion hierarchy and branch selection, independent from destination writes."""
from notion_source import notion_id,summary,MAX_ITEMS,MAX_BLOCKS
from api_clients import APIError

KINDS=('page','database','data_source')
SELECTION_MAX_DEPTH=2

def key(obj):return obj['kind']+':'+obj['id']

def parent_id(obj):
    if obj.get('ancestor_id'):return obj['ancestor_id']
    parent=obj.get('parent') or {}
    return next((parent[x] for x in ('page_id','data_source_id','database_id','block_id') if parent.get(x)),None)

def nodes(catalog):
    return {key(obj):dict(obj) for field in ('pages','databases','data_sources') for obj in catalog[field]}

def repair(client,items):
    """Bridge structural blocks and absent searchable ancestors, with a bounded walk."""
    by_id={obj['id']:obj for obj in items.values()};resolved={};failed=set();warnings=[]
    def ancestor(parent,seen):
        oid=parent_id({'parent':parent})
        if not oid or oid in seen:return None
        if oid in by_id:return oid
        if oid in resolved:return resolved[oid]
        if oid in failed:return None
        if len(resolved)+len(failed)>=256:
            warnings.append('Certains parents restent à vérifier : limite de reconstruction atteinte.')
            return None
        seen=seen|{oid};kind=parent.get('type') or next((k for k in ('page_id','data_source_id','database_id','block_id') if parent.get(k)),None)
        try:
            getter={'page_id':client.page,'database_id':client.database,'data_source_id':client.data_source,'block_id':client.block}.get(kind)
            if getter is None:return None
            obj=getter(oid)
            if kind=='block_id':
                target=ancestor(obj.get('parent') or {},seen)
            else:
                item=summary(obj);items[key(item)]=item;by_id[oid]=item
                target=oid
                higher=ancestor(obj.get('parent') or {},seen)
                if higher:item['ancestor_id']=higher
            resolved[oid]=target
            return target
        except APIError as exc:
            if exc.status not in (403,404):raise
            failed.add(oid);return None
    for item in list(items.values()):
        target=ancestor(item.get('parent') or {},{item['id']})
        if target:item['ancestor_id']=target
    return list(dict.fromkeys(warnings))

def forest(items):
    by_id={obj['id']:key(obj) for obj in items.values()}
    result=[]
    for obj in items.values():
        item=dict(obj);candidate=by_id.get(parent_id(obj))
        # A missing or cyclic ancestor must not make an accessible item disappear.
        seen={key(obj)};cursor=candidate
        while cursor and cursor not in seen:
            seen.add(cursor);cursor=by_id.get(parent_id(items[cursor]))
        item['parent_key']=candidate if candidate and cursor is None else None
        item['unresolved_parent']=item['parent_key'] is None and bool(parent_id(obj))
        result.append(item)
    return sorted(result,key=lambda x:(x['name'].casefold(),key(x)))

def navigation(items):
    """Only expose root + two levels; keep the complete graph for recursive import."""
    rows=forest(items);mapping={key(x):x for x in rows}
    for row in rows:
        depth=0;parent=row['parent_key'];seen=set()
        while parent and parent not in seen:
            seen.add(parent);depth+=1;parent=mapping[parent]['parent_key']
        row['depth']=depth;row['selection_leaf']=depth>=SELECTION_MAX_DEPTH
    return [x for x in rows if x['depth']<=SELECTION_MAX_DEPTH]


def children(client,node):
    kind=node['kind'];oid=node['id']
    if kind=='database':
        db=client.database(oid)
        return [{'id':x['id'],'name':x.get('name') or node['name'],'kind':'data_source','parent':{'database_id':oid}} for x in db.get('data_sources',[])]
    if kind=='data_source':
        return [summary(x) for x in client.paginate('/data_sources/'+notion_id(oid)+'/query',method='POST') if not x.get('archived') and not x.get('in_trash')]
    result=[];pending=[oid];visited=set();count=0
    while pending:
        bid=pending.pop()
        if bid in visited:continue
        visited.add(bid)
        for block in client.children(bid):
            count+=1
            if count>MAX_BLOCKS:raise APIError('Page trop volumineuse : réduisez le périmètre.')
            typ=block.get('type')
            if typ in ('child_page','child_database'):
                obj=client.page(block['id']) if typ=='child_page' else client.database(block['id'])
                if not obj.get('archived') and not obj.get('in_trash'):
                    item=summary(obj);item['parent']={'page_id':oid};result.append(item)
            elif block.get('has_children'):pending.append(block['id'])
    return result

def select(client,known,rules,whole,catalog):
    if not isinstance(whole,bool) or not isinstance(rules,list) or len(rules)>200:raise ValueError('Sélection arborescente invalide.')
    mapping={key(x):x for x in forest(known)};chosen={};schemas={};warnings=[];cache={};seen=set();excluded=set()
    for rule in rules:
        if not isinstance(rule,dict) or rule.get('key') not in mapping or not isinstance(rule.get('include'),bool) or rule['key'] in seen:
            raise ValueError('Élément de sélection inconnu ou répété. Rechargez l’arborescence.')
        seen.add(rule['key'])
    def depth(k):
        n=0;visited=set()
        while k and k not in visited:visited.add(k);k=mapping[k]['parent_key'];n+=1
        return n
    blocked={mapping[r['key']]['id'] for r in rules if not r['include']}
    def read(node):
        k=key(node)
        # Prune excluded descendants before touching their blocks/databases.
        # A deeper explicit inclusion is read separately below.
        ancestors=set();current=k
        while current and current not in ancestors:
            ancestors.add(current);current=mapping[current]['parent_key']
        pruning=blocked-{mapping[a]['id'] for a in ancestors}
        if k not in cache:cache[k]=client.selection(node['kind'],node['id'],True,excluded=pruning,allow_excluded_parent=True)
        return cache[k]
    def apply(selection,include):
        warnings.extend(selection['warnings'])
        if include:
            chosen.update(selection['pages']);schemas.update(selection['schemas']);excluded.difference_update(selection['pages'])
        else:
            excluded.update(selection['pages'])
            for oid in selection['pages']:chosen.pop(oid,None)
            for sid in selection['schemas']:schemas.pop(sid,None)
        if len(chosen)>MAX_ITEMS:raise APIError('Sélection trop volumineuse : choisissez moins de branches.')
    if whole:
        # Traverse known roots rather than search again; includes manually added roots.
        for node in mapping.values():
            if node['parent_key'] is None and node['id'] not in blocked:apply(read(node),True)
    for rule in sorted(rules,key=lambda x:depth(x['key'])):
        if rule['include']:apply(read(mapping[rule['key']]),True)
    excluded.update(mapping[rule['key']]['id'] for rule in rules if not rule['include'])
    if not chosen and not schemas:raise ValueError('Sélectionnez au moins une page ou une base.')
    used={(obj.get('parent') or {}).get('data_source_id') for obj in chosen.values()}
    for sid in used-{None}:
        if sid not in schemas:schemas[sid]=client.data_source(sid)
    return {'pages':chosen,'schemas':schemas,'excluded':sorted(excluded),'warnings':list(dict.fromkeys(warnings+catalog.get('warnings',[])))}
