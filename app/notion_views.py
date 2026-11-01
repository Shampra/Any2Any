"""Adapt Notion views to the existing conservative destination view converter."""
import re
from urllib.parse import unquote
from notion_icons import content_icon
from view_conversion import UnsupportedView, ViewConverter


def normalise(view,schema,issues=None,*,inline=False):
    properties=schema.get('properties',{})
    names={unquote(str(p.get('id'))):name for name,p in properties.items()}
    def name(value):
        if value in properties:return 'name' if properties[value].get('type')=='title' else value
        resolved=names.get(unquote(str(value)))
        if resolved:return 'name' if properties[resolved].get('type')=='title' else resolved
        raise UnsupportedView('Propriété de vue introuvable : '+str(value))
    def clause(node):
        for op in ('and','or'):
            if op in node:
                if not isinstance(node[op],list) or not node[op]:raise UnsupportedView('Groupe de filtre vide')
                return {'operator':op,'filters':[clause(x) for x in node[op]]}
        if 'property' not in node:raise UnsupportedView('Filtre système ou dynamique non pris en charge')
        prop=name(node['property']);typ=next((k for k in node if k not in ('property','type')),None)
        condition=node.get(typ)
        if not isinstance(condition,dict) or len(condition)!=1:raise UnsupportedView('Filtre Notion non reconnu')
        op,value=next(iter(condition.items()))
        ops={'equals':'equal','does_not_equal':'not_equal','greater_than':'greater','less_than':'less','greater_than_or_equal_to':'greater_or_equal','less_than_or_equal_to':'less_or_equal','after':'greater','on_or_after':'greater_or_equal'}
        if typ in ('select','multi_select','status','relation'):
            op={'equals':'in','does_not_equal':'not_in','contains':'in','does_not_contain':'not_in'}.get(op)
            if op is None:raise UnsupportedView('Condition de choix/relation non transposable')
            value=value if isinstance(value,list) else [value]
        elif typ in ('rich_text','title','url','email','phone_number') and op in ('contains','does_not_contain'):
            if not isinstance(value,str) or not value.strip() or value!=value.strip():raise UnsupportedView('Filtre texte vide ou espaces significatifs non transposables')
            op='notion_contains' if op=='contains' else 'notion_not_contains'
        else:
            op=ops.get(op)
            if op is None:raise UnsupportedView('Condition Notion non transposable exactement')
        result={'property':prop,'condition':op,'value':value}
        if typ=='date' and ('T' in str(value)):result['include_time']=True
        return result
    config=view.get('configuration') or {}
    kind=view.get('type','table')
    group=config.get('group_by') or config.get('group') or view.get('group_by')
    grouping=None
    if group:
        if not isinstance(group,dict):raise UnsupportedView('Regroupement Notion non reconnu')
        group_prop=name(group.get('property_id') or group.get('property'))
        if inline:
            if issues is not None:issues.add('Vue groupée adaptée en liste sans regroupement ; filtres et tris conservés')
            kind='list'
        else:
            order=(group.get('sort') or {}).get('type','manual')
            sort={'manual':'manual','ascending':'asc','descending':'desc','alphabetical':'asc','reverse_alphabetical':'desc'}.get(order)
            if not sort:raise UnsupportedView('Ordre des groupes non transposable : '+str(order))
            grouping={'property':group_prop,'sort':sort,'hideEmpty':bool(group.get('hide_empty_groups',False))}
    if kind not in ('table','list','board','gallery'):raise UnsupportedView('Rendu de vue non reproduit : '+kind)
    sorts=[]
    for item in view.get('sorts') or []:
        direction={'ascending':'asc','descending':'desc'}.get(item.get('direction'))
        if not direction:raise UnsupportedView('Direction de tri inconnue')
        sorts.append({'property':name(item.get('property')),'direction':direction})
    columns=[]
    for item in config.get('properties') or []:
        try:resolved=name(item.get('property_id') or item.get('property'))
        except UnsupportedView:
            if issues is not None:issues.add('Colonne de vue supprimée ou inaccessible ignorée : '+str(item.get('property_id') or item.get('property')))
            continue
        columns.append({'property':resolved,'hidden':item.get('visible') is False})
    filters=([clause(view['filter'])] if view.get('filter') else [])
    for pid,condition in (view.get('quick_filters') or {}).items():
        if condition:filters.append(clause({'property':pid,**condition}))
    opening=config.get('open_pages_in') or view.get('open_pages_in')
    presentation={'openMode':'full-screen' if opening in ('full_page','full-page','full_screen','full-screen') else 'side-peek'}
    if config.get('cover_aspect') in ('contain','cover'):presentation['galleryFitImage']=config['cover_aspect']=='contain'
    label=view.get('name')
    if not label or label=='Untitled':label={'table':'Tableau','board':'Tableau Kanban','list':'Liste','gallery':'Galerie'}.get(view.get('type'),'Vue Notion')
    return {'id':view.get('id'),'name':label,'type':'kanban' if kind=='board' else kind,
            'filters':filters,'sorts':sorts,'columns':columns,'presentation':presentation,**({'group_settings':grouping} if grouping else {}),**({'icon':content_icon(view['icon'])} if content_icon(view.get('icon')) else {})}


class NotionViewConverter(ViewConverter):
    def query(self,block,host,members):
        # Each Notion collection is newly created and contains exactly its imported members.
        # Use native membership, rather than exposing hundreds of IDs as a UI filter.
        if getattr(self,'collection_scope',None) and block.get('is_collection'):
            return {'any.collections':self.collection_scope}
        return super().query(block,host,members)

    def predicate(self,node):
        op=node.get('condition')
        if op not in ('notion_contains','notion_not_contains'):return super().predicate(node)
        value=node.get('value')
        if not isinstance(value,str) or not value or value!=value.strip():raise UnsupportedView('Valeur du filtre texte invalide')
        parts=[]
        for path,spec,form in self.fields(node.get('property')):
            if spec.get('format') not in ('text','url','email','phone'):raise UnsupportedView('Filtre texte sur propriété non textuelle')
            escaped=re.sub(r'([.*+?^${}()|\[\]\\])',r'\\\1',value)
            rule={'$regex':'(?i)'+escaped}
            if op=='notion_not_contains':rule={'$not':rule}
            part={path:rule}
            if not path.startswith('any.'):part={'$and':[{'any.collections':path.split('.')[0]},part]}
            parts.append(part)
        return parts[0] if len(parts)==1 else {'$or':parts}


def converter(engine,sid):
    bindings={}
    for name,prop in engine.schemas[sid].get('properties',{}).items():
        binding=engine.props.get((sid,prop.get('id')))
        if not binding:continue
        pid,kind,form=binding
        fmt={'choice':'multi_select' if form.get('config',{}).get('multiple') else 'select',
             'relation':'objects','datetime':'date','longtext':'text','phone':'phone','currency':'number','percent':'number'}.get(form['type'],form['type'])
        bindings[name.casefold()]=[(engine.collections[sid]+'.'+pid,{'format':fmt},form)]
    result=NotionViewConverter(bindings,engine.mapping,{}, {})
    result.collection_scope=engine.collections[sid]
    return result
