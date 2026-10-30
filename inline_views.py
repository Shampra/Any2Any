"""Anytwo inline-view client schema, checked against a native example."""
import hashlib
import json
import math
from view_conversion import UnsupportedView


def instance_id(host, identity):
    return 'any2any-'+hashlib.sha256((host+'\0'+identity).encode()).hexdigest()[:24]


def inline_markdown(sid,host,instance,label,source):
    envelope={'v':1,'kind':'inline-view','schema':1,'instance':instance,
              'data':{'space':sid,'host':host,'dataview':instance}}
    label=str(label).replace('\\','\\\\').replace('[','\\[').replace(']','\\]')
    return ('<!-- any:block '+json.dumps(envelope,separators=(',',':'))+' -->\n\n'
            +'['+label+'](any://o/'+sid+'/'+source+')\n\n'
            +'<!-- /any:block '+json.dumps({'instance':instance},separators=(',',':'))+' -->')


def property_names(view):
    names=[]
    def visit(node):
        if 'filters' in node:
            for child in node['filters']:visit(child)
        elif node.get('property'):names.append(str(node['property']))
    for node in view.get('filters',[]):visit(node)
    names.extend(str(v['property']) for v in view.get('sorts',[]) if v.get('property'))
    names.extend(str(v['property']) for v in view.get('columns',[]) if v.get('property') and not v.get('hidden'))
    return list(dict.fromkeys(names))


def ui_field(converter,name):
    fields=converter.fields(name)
    if len(fields)!=1:raise UnsupportedView('Propriété de vue en ligne ambiguë : '+str(name))
    path,spec,form=fields[0]
    return ('any.name' if path=='any.name' else path.split('.',1)[1]),spec,form


def ui_clause(converter,node,identity):
    # Validate against the same conservative rules as the stored server query.
    converter.predicate(node)
    if 'filters' in node:
        if not node['filters']:raise UnsupportedView('Groupe vide non représentable par le client Inline view')
        return {'id':identity,'kind':'group','conjunction':node['operator'],
                'children':[ui_clause(converter,n,identity+'-'+str(i)) for i,n in enumerate(node['filters'])]}
    prop,spec,form=ui_field(converter,node['property'])
    op=node['condition'];fmt=spec.get('format');value=node.get('value')
    if fmt in ('text','url','email','phone'):
        operator={'equal':'is','not_equal':'is-not'}.get(op)
        if operator is None:raise UnsupportedView('Condition texte non transposable dans une vue en ligne')
        if not isinstance(value,str) or not value.strip():raise UnsupportedView('Filtre texte vide ignoré par le client Inline view')
        condition={'kind':'text','operator':operator,'value':str(value)}
    elif fmt=='number':
        operator={'equal':'eq','not_equal':'neq','greater':'gt','less':'lt','greater_or_equal':'gte','less_or_equal':'lte'}.get(op)
        if operator is None:raise UnsupportedView('Condition numérique non transposable dans une vue en ligne')
        try:
            if isinstance(value,bool) or not math.isfinite(float(value)):raise ValueError()
        except (ValueError,TypeError):raise UnsupportedView('Valeur numérique de filtre invalide')
        condition={'kind':'number','operator':operator,'value':'' if op=='exists' else str(value)}
    elif fmt=='checkbox':
        if op not in ('equal','not_equal') or not isinstance(value,bool):raise UnsupportedView('Filtre booléen non transposable')
        condition={'kind':'boolean','value':value if op=='equal' else not value}
    elif fmt in ('select','multi_select','objects'):
        operator={'in':'contains','not_in':'does-not-contain','all_in':'is'}.get(op)
        if operator is None:raise UnsupportedView('Filtre de liste non transposable dans une vue en ligne')
        values=converter.value(value,spec,form)
        if not values:raise UnsupportedView('Filtre de liste vide ignoré par le client Inline view')
        # The client turns raw object IDs into any:// references itself.
        if fmt=='objects':values=[v.removeprefix('any://') for v in values]
        # The client interprets several relation values as ALL, even for
        # "contains". Expand ANY to an OR of singleton clauses. Conversely,
        # single-select "is" means ANY, so expand ALL to an AND there.
        conjunction=('or' if fmt=='objects' and op=='in' else
                     'and' if fmt=='select' and op=='all_in' else None)
        if conjunction and len(values)>1:
            return {'id':identity,'kind':'group','conjunction':conjunction,
                'children':[{'id':identity+'-'+str(i),'propertyId':prop,
                    'condition':{'kind':'choice','operator':'contains','values':[v]}}
                    for i,v in enumerate(values)]}
        condition={'kind':'choice','operator':operator,'values':values}
    elif fmt=='date':
        if node.get('include_time') or form.get('type')=='datetime':raise UnsupportedView('Filtre avec heure non transposable en ligne')
        operator={'equal':'is','not_equal':'is-not','greater':'after','greater_or_equal':'on-or-after'}.get(op)
        if operator is None:raise UnsupportedView('Condition date non transposable en ligne')
        condition={'kind':'date','operator':operator,'value':converter.value(value,spec,form)['$date'][:10]}
    else:raise UnsupportedView('Format de filtre non transposable en ligne : '+str(fmt))
    return {'id':identity,'propertyId':prop,'condition':condition}


def inline_records(converter,block,scope,instance,issues):
    records=[];failed=[];active_failed=False
    views=list(block.get('views') or [{}])
    active=block.get('active_view') or block.get('active_view_id')
    if active:views.sort(key=lambda v:v.get('id')!=active)
    for index,view in enumerate(views):
        try:
            layout,query,settings=converter.convert(view,{'any.collections':scope})
            clauses=[ui_clause(converter,n,instance+'-filter-'+str(i)) for i,n in enumerate(view.get('filters',[]))]
            sorts=[{'id':instance+'-sort-'+str(i),'propertyId':ui_field(converter,n['property'])[0],
                    'dir':n.get('direction','asc')} for i,n in enumerate(view.get('sorts',[]))]
            query['anyUi']={'version':1,'source':{'kind':'collection','id':scope},'filters':clauses,'sort':sorts}
            visible=[]
            for column in view.get('columns',[]):
                if column.get('hidden') or column.get('property')=='name':continue
                try:visible.append(ui_field(converter,column['property'])[0])
                except UnsupportedView:issues.add('Colonne de vue en ligne non disponible : '+str(column.get('property')))
            settings.update(visible=visible,pageSize=10)
            if layout not in ('list','gallery'):
                issues.add('Disposition de vue en ligne adaptée en liste : '+layout)
                layout='list'
            if view.get('group_by'):raise UnsupportedView('Regroupement non pris en charge par les vues en ligne du client')
            records.append({'id':instance+'.list' if not records else instance+'.view-'+str(index),
                'dataview':instance,'name':view.get('name') or 'Vue Anytype','pos':f'a{index:06d}',
                'layout':layout,'query':query,'layoutSettings':settings})
        except (UnsupportedView,ValueError,TypeError,KeyError) as exc:
            failed.append(str(exc))
            if index==0:active_failed=True
    if not records:raise UnsupportedView('; '.join(failed))
    if len(records)>1:issues.add('Vue en ligne : première vue affichée ; autres vues conservées comme vues enregistrées')
    if active_failed:
        raise UnsupportedView('Vue active non convertible : '+failed[0])
    return records,failed
