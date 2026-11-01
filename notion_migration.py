"""Notion -> Anytwo importer. All destination I/O uses the common backend."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import uuid
from urllib.parse import unquote
import anytwo_backend as backend
from anytwo_backend import APIError, _segment
from notion_source import MAX_ITEMS, MAX_BLOCKS, notion_id, title, text
from notion_content import Content, escape
from notion_icons import content_icon,emoji
from rich_content import ImportedFile, image_markdown, file_html
from file_transfer import FileLibrary
from notion_files import download, filename
from notion_views import normalise, converter
from view_conversion import modify_records, create_saved_views, UnsupportedView
from inline_views import instance_id, inline_records, inline_markdown


def stable(value):return 'notion_'+hashlib.sha256(str(value).encode()).hexdigest()[:20]


CURRENCIES={
    'dollar':'USD','canadian_dollar':'CAD','australian_dollar':'AUD','euro':'EUR','pound':'GBP',
    'yen':'JPY','ruble':'RUB','rupee':'INR','won':'KRW','yuan':'CNY','real':'BRL','lira':'TRY',
    'rupiah':'IDR','franc':'CHF','hong_kong_dollar':'HKD','new_zealand_dollar':'NZD',
    'krona':'SEK','norwegian_krone':'NOK','mexican_peso':'MXN','rand':'ZAR',
    'new_taiwan_dollar':'TWD','danish_krone':'DKK','zloty':'PLN','baht':'THB',
    'forint':'HUF','koruna':'CZK','shekel':'ILS','chilean_peso':'CLP',
    'philippine_peso':'PHP','dirham':'AED','colombian_peso':'COP','riyal':'SAR',
    'ringgit':'MYR','leu':'RON','argentine_peso':'ARS','uruguayan_peso':'UYU',
    'singapore_dollar':'SGD',
}


def number_descriptor(prop):
    fmt=(prop.get('number') or {}).get('format','number')
    if fmt in CURRENCIES:return {'type':'currency','config':{'currency':CURRENCIES[fmt]}}
    if fmt=='percent':return {'type':'percent'}
    if fmt=='number_with_commas':return {'type':'number','config':{'separators':True}}
    return {'type':'number'}


def source_property(schema,pid=None,name=None):
    properties=schema.get('properties',{})
    if pid is not None:
        for prop in properties.values():
            if prop.get('id') is not None and unquote(str(prop['id']))==unquote(str(pid)):return prop
    return properties.get(name) if name is not None else None


def references(node):
    result=set()
    if isinstance(node,list):
        for item in node:result.update(references(item))
    elif isinstance(node,dict):
        mention=node.get('mention') or {};target=mention.get('page') or mention.get('database')
        if target and target.get('id'):result.add(target['id'])
        link=node.get('link_to_page') or {}
        for field in ('page_id','database_id'):
            if link.get(field):result.add(link[field])
        for key,value in node.items():
            if key in ('url','href') and isinstance(value,str):
                try:result.add(notion_id(value))
                except ValueError:pass
            elif isinstance(value,(dict,list)):result.update(references(value))
    return result


def validate_options(data):
    for name in ('files','links'):
        if not isinstance(data.get(name),bool):raise ValueError('Option '+name+' invalide.')
    dest=data.get('destination')
    if not isinstance(dest,dict):raise ValueError('Choisissez un espace Anytwo.')
    if dest.get('id')=='__create__':
        name=dest.get('name')
        if not isinstance(name,str) or not name.strip() or len(name.strip())>120:raise ValueError('Nom du nouvel espace invalide.')
    elif not isinstance(dest.get('id'),str) or not dest['id']:raise ValueError('Espace de destination invalide.')
    return {'files':data['files'],'links':data['links'],'destination':deepcopy(dest)}


class Engine:
    def __init__(self,source,target,selection,options,progress=lambda message:None,check=lambda:None,save=lambda report:None,resume=None):
        self.source=source;self.target=target;self.selection=deepcopy(selection);self.options=validate_options(options)
        self.progress=progress;self.check=check;self.save=save;self.sid=None
        self.pages=self.selection['pages'];self.schemas=self.selection['schemas'];self.blocks={};self.views={};self.databases={}
        self.mapping={};self.collections={};self.props={};self.names={};self.view_hosts={};self.uploads={};self.rollups=set()
        self.metrics=lambda **values:None;self.content_plans={};self.synced_sources={};self.collection_handles={}
        self.report={'id':str(uuid.uuid4()),'source':'notion','started_at':datetime.now(timezone.utc).isoformat(),
                     'status':'running','objects':[],'collections':[],'views':[],'errors':[],'warnings':list(selection.get('warnings',[])),
                     'options':self.options,'target_space':None,'mapping':{},'totals':{}}
        self.results={}
        if resume:
            if resume.get('source')!='notion' or not resume.get('target_space'):raise ValueError('Bilan de reprise invalide.')
            if set(resume.get('mapping',{}))-set(self.pages):raise ValueError('La sélection ne contient plus toutes les pages de cet import.')
            self.report=deepcopy(resume);self.report.setdefault('previous_errors',[]).extend(self.report.get('errors',[]));self.report['errors']=[];self.report['status']='running'
            self.sid=resume['target_space'];self.mapping=dict(resume.get('mapping',{}))
            self.collections={x['source_id']:x['target_id'] for x in resume.get('collections',[])}
            self.collection_handles={x['source_id']:x.get('xKey') or stable(self.report['id']+x['source_id']) for x in resume.get('collections',[])}
            self.view_hosts={x['page']:x['target_id'] for x in resume.get('views',[]) if x.get('page') and x.get('target_id')}
            for row in resume.get('objects',[]):self.results[row['source_id']]={**deepcopy(row),'issues':set() ,'errors':[]}
            # Bind only columns identified by the previous checkpoint, never by name alone.
            for collection in resume.get('collections',[]):
                columns={str(x.get('id') or x.get('propId')):x for x in backend.list_columns(target,self.sid,collection['target_id'])}
                for p in collection.get('properties',[]):
                    col=columns.get(p['target_id'])
                    if col:
                        form=col.get('xFormat') or {'type':'longtext'}
                        self.props[(collection['source_id'],p['source_id'])]=(p['target_id'],col.get('kind','string'),form)
                        if form.get('type')=='rollup':self.rollups.add((collection['source_id'],p['source_id']))

    def issues(self,oid):return self.results[oid]['issues']

    def checkpoint(self):
        self.report['target_space']=self.sid;self.report['mapping']=dict(self.mapping)
        self.report['objects']=[{**r,'issues':sorted(r['issues'])} for r in self.results.values()]
        self.report['totals']=dict(Counter(r['status'] for r in self.results.values()),total=len(self.results))
        self.save(deepcopy(self.report))

    def resolve_schema(self,relation):
        sid=relation.get('data_source_id')
        if sid:return sid if sid in self.schemas else None
        did=relation.get('database_id')
        if not did:return None
        candidates=[sid for sid,s in self.schemas.items() if s.get('parent',{}).get('database_id')==did]
        return candidates[0] if len(candidates)==1 else None

    def collect(self):
        """Complete source snapshot before the first destination write."""
        self.metrics(phase='reading',pages=len(self.pages),blocks=0)
        count=0;scanned=set();pending=list(self.pages)
        while pending:
            self.check();oid=pending.pop(0)
            if oid in scanned:continue
            scanned.add(oid);page=self.pages[oid];self.names[oid]=title(page)
            self.progress('Lecture complète : '+self.names[oid])
            properties=[(name,prop) for name,prop in page.get('properties',{}).items() if prop.get('id')]
            with ThreadPoolExecutor(max_workers=4) as pool:
                completed=list(pool.map(lambda item:(item[0],self.source.complete_property(oid,item[1])),properties))
            page['properties'].update(completed)
            refs=references(page.get('properties',{}));todo=[oid];visited=set()
            for prop in page.get('properties',{}).values():
                if prop.get('type')=='relation':refs.update(x['id'] for x in prop.get('relation',[]))
            while todo:
                bid=todo.pop()
                if bid in visited:continue
                visited.add(bid);self.check()
                rows=self.source.children(bid);self.blocks[bid]=rows;count+=len(rows)
                self.metrics(pages=len(self.pages),pages_read=len(scanned),blocks=count)
                if count>MAX_BLOCKS:raise APIError('Import supérieur à la limite de blocs ; réduisez la sélection.')
                for block in rows:
                    refs.update(references(block))
                    typ=block.get('type');data=block.get(typ) or {}
                    if typ=='child_database':
                        did=block['id'];db=self.source.database(did);self.databases[did]=db
                        try:
                            if did not in self.views:self.views[did]=self.source.views(did)
                        except APIError as exc:
                            if exc.status not in (403,404):raise
                            self.report['warnings'].append('Vues de la base non lisibles : '+title(db));self.views[did]=[]
                        for view in self.views[did]:
                            source_id=view.get('data_source_id')
                            if not source_id:continue
                            if source_id not in self.schemas:self.schemas[source_id]=self.source.data_source(source_id)
                            if self.options['links'] and source_id not in {p.get('parent',{}).get('data_source_id') for p in self.pages.values()}:refs.add(source_id)
                    if typ=='link_to_page' and data.get('page_id'):refs.add(data['page_id'])
                    for rich in data.get('rich_text',[]):
                        mention=rich.get('mention') or {};ref=mention.get('page') or mention.get('database')
                        if ref:refs.add(ref['id'])
                        url=(rich.get('text',{}).get('link') or {}).get('url') or rich.get('href')
                        if url:
                            try:refs.add(notion_id(url))
                            except ValueError:pass
                    if typ=='synced_block' and (data.get('synced_from') or {}).get('block_id'):
                        original=data['synced_from']['block_id'];self.blocks[block['id']]=self.source.children(original)
                        # The reference's content must be available to the renderer under its own ID.
                        for child in self.blocks[block['id']]:
                            if child.get('has_children'):todo.append(child['id'])
                        count+=len(self.blocks[block['id']]);block['has_children']=True
                    elif block.get('has_children') and typ not in ('child_page','child_database'):todo.append(block['id'])
            if self.options['links']:
                for ref in sorted(refs-set(self.pages)-set(self.selection.get('excluded',[]))):
                    self.check()
                    try:
                        resolved=self.source.resolve(ref);extra=self.source.selection(resolved['kind'],ref,True,excluded=self.selection.get('excluded',[]))
                        if len(set(self.pages)|set(extra['pages']))>MAX_ITEMS:raise APIError('Trop de pages liées ; réduisez le périmètre.')
                        for pid,obj in extra['pages'].items():
                            if pid not in self.pages and pid not in self.selection.get('excluded',[]):self.pages[pid]=obj;pending.append(pid)
                        self.schemas.update(extra['schemas'])
                    except APIError as exc:
                        if exc.status not in (403,404):raise
                        self.report['warnings'].append('Élément lié inaccessible : '+ref)
        # A relation needs a target schema even when linked pages are not selected.
        # Read definitions only: this never queries/imports that source's members.
        pending=list(self.schemas);checked=set()
        while pending:
            self.check()
            sid=pending.pop()
            if sid in checked:continue
            checked.add(sid)
            for prop in self.schemas[sid].get('properties',{}).values():
                if prop.get('type')!='relation':continue
                relation=prop.get('relation') or {};target=relation.get('data_source_id')
                try:
                    if not target and relation.get('database_id'):
                        db=self.source.database(relation['database_id']);self.databases[db['id']]=db
                        sources=db.get('data_sources',[])
                        if len(sources)==1:target=sources[0]['id']
                    if target and target not in self.schemas:
                        if len(self.schemas)>=MAX_ITEMS:raise APIError('Trop de schémas de relation ; réduisez le périmètre.')
                        self.progress('Lecture des propriétés de la collection liée…')
                        self.schemas[target]=self.source.data_source(target);pending.append(target)
                        self.report['warnings'].append('Schéma cible de relation importé sans élargir la sélection de pages : '+title(self.schemas[target]))
                except APIError as exc:
                    if exc.status not in (403,404):raise
                    self.report['warnings'].append('Schéma cible de relation inaccessible ; définition source conservée.')
        for sid,schema in self.schemas.items():
            did=schema.get('parent',{}).get('database_id')
            if did and did not in self.databases:self.databases[did]=self.source.database(did)
        for did in self.databases:
            self.names[did]=title(self.databases[did])
            self.check()
            try:
                if did not in self.views:self.views[did]=self.source.views(did)
            except APIError:self.views[did]=[];self.report['warnings'].append('Vues de la base non lisibles : '+title(self.databases[did]))
        # Include properties present in values but missing from a stale schema response.
        for oid,page in self.pages.items():
            sid=(page.get('parent') or {}).get('data_source_id')
            if sid and sid in self.schemas:
                props=self.schemas[sid].setdefault('properties',{})
                for name,value in page.get('properties',{}).items():props.setdefault(name,{'id':value.get('id'),'name':name,'type':value.get('type')})

    def shape(self,sid,name,prop):
        typ=prop['type'];form={'type':'longtext'};kind='string'
        if typ=='title':return None
        if typ in ('rich_text','url','email','phone_number'):
            form={'type':{'rich_text':'text','phone_number':'phone'}.get(typ,typ)}
        elif typ=='number':kind='number';form=number_descriptor(prop)
        elif typ=='checkbox':kind='boolean';form={'type':'checkbox'}
        elif typ in ('date','created_time','last_edited_time'):
            kind='datetime';has_time=typ!='date' or any('T' in str((p.get('properties',{}).get(name,{}).get('date') or {}).get('start','')) for p in self.pages.values())
            form={'type':'datetime' if has_time else 'date'}
        elif typ in ('select','multi_select','status'):
            options={}
            for index,opt in enumerate((prop.get(typ) or {}).get('options',[])):
                key=stable(opt.get('id') or opt['name']);options[key]={'name':opt['name'],'pos':f'a{index:06d}'}
                if opt.get('color') and opt['color']!='default':options[key]['color']={'gray':'grey'}.get(opt['color'],opt['color'])
            for page in self.pages.values():
                if page.get('parent',{}).get('data_source_id')!=sid:continue
                value=page.get('properties',{}).get(name,{}).get(typ)
                for opt in (value if isinstance(value,list) else [value] if value else []):
                    if not any(x['name']==opt['name'] for x in options.values()):options[stable(opt.get('id') or opt['name'])]={'name':opt['name'],'color':{'gray':'grey'}.get(opt.get('color'),'grey')}
            kind='array';form={'type':'choice','options':options,'config':{'multiple':typ=='multi_select','optionSort':'manual'}}
        elif typ=='relation':
            target_sid=self.resolve_schema(prop.get('relation') or {})
            if target_sid:
                handle=self.collection_handles.get(target_sid) or stable(self.report['id']+target_sid)
                kind='array';form={'type':'relation','config':{'multiple':(prop.get('relation') or {}).get('limit')!=1},'relation':{'targetTypes':[handle]}}
            else:form={'type':'longtext'}
        elif typ=='formula':
            vals=[p.get('properties',{}).get(name,{}).get('formula',{}) for p in self.pages.values() if p.get('parent',{}).get('data_source_id')==sid]
            types={v.get('type') for v in vals if v}
            if types=={'number'}:kind='number';form={'type':'number'}
            elif types=={'boolean'}:kind='boolean';form={'type':'checkbox'}
            elif types=={'date'}:kind='datetime';form={'type':'datetime'}
        icon=content_icon(prop.get('icon'))
        if icon:form['icon']=icon
        form['any2any']={'sourceSettings':json.dumps(prop,ensure_ascii=False)}
        return kind,form

    def create_schema(self):
        run=self.report['id']
        for sid,schema in self.schemas.items():
            self.check();did=schema.get('parent',{}).get('database_id');db=self.databases.get(did,{})
            name=title(db) if len(db.get('data_sources',[]))==1 else title(schema)
            self.progress('Création de la collection : '+name)
            cid=self.collections.get(sid)
            if not cid:
                cid=backend.create_collection(self.target,self.sid,name,stable(run+sid));self.collections[sid]=cid
                self.report['collections'].append({'source_id':sid,'target_id':cid,'name':name,'xKey':stable(run+sid),'properties':[]});self.checkpoint()
            self.collection_handles.setdefault(sid,stable(run+sid))
            source_icon=db.get('icon') or schema.get('icon') or {};icon=content_icon(source_icon)
            if not icon and self.options['files'] and source_icon.get('type') in ('file','external'):
                try:
                    data=source_icon.get(source_icon['type']) or {}
                    content,mime,filename=download(data.get('url',''),'collection-icon',self.check)
                    fid=backend.attach_file(self.target,self.sid,cid,filename,content,mime)
                    icon=f'any://f/{self.sid}/{fid}'
                except APIError as exc:self.report['warnings'].append('Image de collection non récupérée : '+str(exc))
            if icon:
                try:backend.target_write(self.target,f'/spaces/{_segment(self.sid)}/collections/{_segment(cid)}',{'iconCid':icon},method='PATCH')
                except APIError as exc:self.report['warnings'].append('Icône de collection non appliquée : '+str(exc))
        # All collections/handles exist before creating any relation properties.
        for sid,schema in self.schemas.items():
            cid=self.collections[sid]
            collection=next(c for c in self.report['collections'] if c['source_id']==sid)
            for pname,prop in schema.get('properties',{}).items():
                if prop.get('type') in ('title','rollup'):continue
                if (sid,prop['id']) in self.props:continue
                self.check();kind,form=self.shape(sid,pname,prop)
                pid=backend.add_column(self.target,self.sid,cid,pname,stable(prop['id']),kind,form)
                self.props[(sid,prop['id'])]=(pid,kind,form)
                collection['properties'].append({'source_id':prop['id'],'target_id':pid,'name':pname})
                self.checkpoint()
        self.link_inverse_relations()
        for sid,schema in self.schemas.items():
            cid=self.collections[sid]
            for name,prop in schema.get('properties',{}).items():
                if prop.get('type')!='rollup':continue
                if (sid,prop['id']) in self.props:continue
                self.check();kind,form=self.rollup_shape(sid,prop)
                icon=content_icon(prop.get('icon'))
                if icon:form['icon']=icon
                if form['type']=='rollup':self.rollups.add((sid,prop['id']))
                pid=backend.add_column(self.target,self.sid,cid,name,stable(prop['id']),kind,form);self.props[(sid,prop['id'])]=(pid,kind,form)
                self.report['collections'][list(self.collections).index(sid)]['properties'].append({'source_id':prop['id'],'target_id':pid,'name':name})
                self.checkpoint()

    def link_inverse_relations(self):
        """Pair already-created source properties; never invent a reverse column."""
        for sid,schema in self.schemas.items():
            for prop in schema.get('properties',{}).values():
                rel=prop.get('relation') or {};dual=rel.get('dual_property')
                if prop.get('type')!='relation' or not dual:continue
                target_sid=self.resolve_schema(rel)
                reverse=source_property(self.schemas.get(target_sid,{}),dual.get('synced_property_id'),dual.get('synced_property_name'))
                binding=self.props.get((sid,prop['id']));other=self.props.get((target_sid,(reverse or {}).get('id')))
                if not binding or not other or binding[2].get('type')!='relation' or other[2].get('type')!='relation':
                    self.report['warnings'].append('Relation bidirectionnelle non appariée : '+prop.get('name',prop['id']))
                    continue
                # Refuse a stale reverse pointer belonging to another source.
                if self.resolve_schema((reverse or {}).get('relation') or {})!=sid:
                    self.report['warnings'].append('Relation inverse incohérente ; appariement non appliqué : '+prop.get('name',prop['id']))
                    continue
                self.check();owner=self.collections[sid];other_owner=self.collections[target_sid]
                anyui={'inverseOwner':other_owner,'inverseProperty':other[0]}
                backend.target_write(self.target,f'/spaces/{_segment(self.sid)}/collections/{_segment(owner)}/properties/{_segment(binding[0])}',
                                     {'set':{'xFormat.anyui.'+key:value for key,value in anyui.items()}},method='PATCH')
                binding[2].setdefault('anyui',{}).update(anyui)

    def rollup_shape(self,sid,prop):
        config=prop.get('rollup') or {};schema=self.schemas[sid]
        relation=source_property(schema,config.get('relation_property_id'),config.get('relation_property_name'))
        target_sid=self.resolve_schema((relation or {}).get('relation') or {})
        target_prop=source_property(self.schemas.get(target_sid,{}),config.get('rollup_property_id'),config.get('rollup_property_name'))
        relbinding=self.props.get((sid,(relation or {}).get('id')));targetbinding=self.props.get((target_sid,(target_prop or {}).get('id')))
        calculate={'sum':'sum','average':'average','min':'min','max':'max','median':'median','range':'range','show_original':'original','show_unique':'unique','count_all':'count-all','count_empty':'count-empty','count_not_empty':'count-not-empty'}.get(config.get('function'))
        target_title=(target_prop or {}).get('type')=='title';archive={'sourceSettings':json.dumps(prop,ensure_ascii=False)}
        if calculate and relbinding and relbinding[2].get('type')=='relation' and (targetbinding or target_title):
            rollup={'relation':{'direction':'own','ownerId':self.collections[sid],'propertyId':relbinding[0]},
                    'target':{'ownerId':self.collections[target_sid],'propertyId':'any.name' if target_title else targetbinding[0]},'calculate':calculate,'showAs':'number'}
            return 'object',{'type':'rollup','anyui':{'rollup':json.dumps(rollup)},'any2any':archive}
        return 'string',{'type':'longtext','any2any':archive}

    def value(self,oid,sid,name,prop,form):
        typ=prop.get('type');value=prop.get(typ);issues=self.issues(oid)
        if typ=='rich_text':
            if any(any(v for k,v in (x.get('annotations') or {}).items() if k!='color') or (x.get('annotations') or {}).get('color') not in (None,'default') for x in value or []):
                issues.add('Mise en forme de propriété texte adaptée en texte brut')
                self.results[oid].setdefault('source_values',{})[name]=deepcopy(prop)
            return text(value)
        if typ in ('url','email','phone_number','number','checkbox'):
            if typ=='number':
                spec=json.loads(form.get('any2any',{}).get('sourceSettings','{}'))
                fmt=(spec.get('number') or {}).get('format')
                if fmt not in (None,'number','number_with_commas','percent') and fmt not in CURRENCIES:
                    issues.add('Format numérique source inconnu archivé ; valeur conservée sans format d’affichage')
            return value
        if typ in ('select','multi_select','status'):
            options={v['name']:k for k,v in form.get('options',{}).items()};items=value if isinstance(value,list) else [value] if value else []
            if typ=='status':issues.add('Groupes du workflow Notion archivés ; choix simple importé')
            return [options[x['name']] for x in items]
        if typ=='date':
            if not value:return None
            if value.get('end') or value.get('time_zone'):issues.add('Intervalle/fuseau de date archivé dans le rapport ; seule la date de début est native')
            start=value['start'];return {'$date':start+'T00:00:00Z' if len(start)==10 else start}
        if typ in ('created_time','last_edited_time'):return {'$date':value} if value else None
        if typ=='relation':
            if form.get('type')=='longtext':
                issues.add('Cible de relation inaccessible ou ambiguë : références conservées en texte, sans relation non restreinte')
                return json.dumps(value,ensure_ascii=False)
            outside=[x['id'] for x in value or [] if x['id'] not in self.mapping]
            if outside:issues.add(f'Relation : {len(outside)} cible(s) hors périmètre non importée(s)')
            return ['any://'+self.mapping[x['id']] for x in value or [] if x['id'] in self.mapping]
        if typ=='formula':
            issues.add('Formule : résultat figé ; expression archivée dans le descripteur')
            if not value:return None
            inner=value.get(value.get('type'))
            if value.get('type')=='date':return {'$date':inner['start']} if inner else None
            if form['type'] in ('number','checkbox'):return inner
            return json.dumps(inner,ensure_ascii=False) if isinstance(inner,(dict,list)) else str(inner) if inner is not None else None
        if typ=='rollup':
            issues.add('Rollup non transposable : résultat figé ; définition archivée')
            return json.dumps(value,ensure_ascii=False)
        if typ=='files':
            links=[]
            for file in value or []:
                uri=self.media(oid,file,'file')
                if uri:links.append(file_html(uri,uri.name))
            issues.add('Propriété fichiers adaptée en liens vers les pièces jointes importées')
            return '\n'.join(links)
        if typ in ('people','created_by','last_edited_by'):
            issues.add('Personnes/auteurs conservés comme texte, sans comptes ni droits')
            people=value if isinstance(value,list) else [value] if value else []
            return ', '.join(x.get('name') or x.get('id','') for x in people)
        issues.add('Propriété adaptée en texte : '+str(typ))
        return json.dumps(value,ensure_ascii=False) if value is not None else None

    def media(self,oid,data,typ):
        if not self.options['files']:self.issues(oid).add('Fichier non récupéré : option désactivée');return None
        source=(data.get(data.get('type','file')) or {});url=source.get('url')
        if not url:self.issues(oid).add('URL de fichier indisponible');return None
        if url in self.uploads:return self.uploads[url]
        self.check()
        try:
            content,mime,name=download(url,data.get('name',''),self.check)
            import mimetypes
            if '.' not in name and (extension:=mimetypes.guess_extension(mime)):name+=extension
            fid=self.library.find(name,content)
            if not fid:fid=backend.attach_file(self.target,self.sid,self.mapping[oid],name,content,mime);self.library.register(name,content,fid)
            uri=ImportedFile('any://f/'+self.sid+'/'+fid,name,mime);self.uploads[url]=uri
            if not any(x['target_id']==fid for x in self.report.setdefault('files',[])):
                self.report['files'].append({'source_page':oid,'target_id':fid,'name':name,'size':len(content)})
            self.checkpoint();return uri
        except APIError as exc:
            if exc.status==499:raise
            self.issues(oid).add(str(exc));return None

    def database_sources(self,did):
        db=self.databases.get(did,{})
        return list(dict.fromkeys([x['id'] for x in db.get('data_sources',[])]+[v['data_source_id'] for v in self.views.get(did,[]) if v.get('data_source_id')]))

    def database_content(self,oid,did):
        db=self.databases.get(did,{})
        # Full-page databases are navigation links, not embedded views.
        if db.get('is_inline') is False:
            links=[]
            for sid in self.database_sources(did):
                if sid in self.collections:links.append('['+escape(title(db))+'](any://o/'+self.sid+'/'+self.collections[sid]+')')
            if not links:
                self.issues(oid).add('Base liée hors sélection : '+title(db))
                return '['+escape(title(db))+'](https://www.notion.so/'+did.replace('-','')+')'
            return '\n\n'.join(links)
        return self.inline_database(oid,did)

    def inline_database(self,oid,did):
        db=self.databases.get(did,{})
        fragments=[]
        for sid in self.database_sources(did):
            cid=self.collections.get(sid)
            if not cid:continue
            self.check();instance=instance_id(self.mapping[oid],did+sid);issues=self.issues(oid)
            try:
                block=self.view_block(sid,issues,did=did,inline=True)
                records,failed=inline_records(converter(self,sid),block,cid,instance,issues)
                root=self.view_hosts.get(oid)
                if not root:
                    result=backend.target_write(self.target,f'/spaces/{_segment(self.sid)}/objects',{'type':'dataview','initialProperties':{'dataview':{'host':self.mapping[oid]}}})
                    root=result.get('objectId')
                    if not root:raise APIError('Objet de vues sans identifiant.')
                    self.view_hosts[oid]=root
                label=title(db) if title(db) not in ('Untitled','(Sans titre)') else title(self.schemas[sid])
                modify_records(self.target,self.sid,root,'dataviews',[{'id':instance,'name':label,'pos':'a'+instance}])
                modify_records(self.target,self.sid,root,'views',records)
                fragments.append(inline_markdown(self.sid,self.mapping[oid],instance,label,cid))
                self.report['views'].append({'source':did,'page':oid,'status':'created','failed':failed,'target_id':root})
                issues.update('Vue non convertie : '+x for x in failed)
            except (UnsupportedView,APIError) as exc:
                issues.add('Vue inline non convertie : '+str(exc));fragments.append('['+escape(title(db))+'](any://o/'+self.sid+'/'+cid+')')
                self.report['views'].append({'source':did,'page':oid,'status':'unsupported','message':str(exc)})
        if not fragments:
            self.issues(oid).add('Base intégrée hors sélection : '+title(db))
            fragments.append('['+escape(title(db))+'](https://www.notion.so/'+did.replace('-','')+')')
        return '\n\n'.join(fragments)

    def view_block(self,sid,issues,did=None,inline=False):
        did=did or self.schemas[sid].get('parent',{}).get('database_id');source=self.views.get(did,[]);views=[]
        # The first source view remains first: never silently replace an unsupported active filter.
        for view in source:
            if view.get('data_source_id') and view['data_source_id']!=sid:continue
            try:views.append(normalise(view,self.schemas[sid],issues,inline=inline))
            except UnsupportedView as exc:
                issues.add('Vue non convertie : '+str(exc))
                if inline:views.append({'id':view.get('id'),'name':view.get('name'),'type':'unsupported'})
        if not views:
            if source:raise UnsupportedView('Aucune vue de cette source convertible')
            issues.add('Réglages de vues indisponibles : vue de collection sans filtre source')
            views=[{'name':'Données importées','type':'table'}]
        return {'is_collection':True,'views':views}

    def copy_workspace_icon(self):
        url=self.selection.get('workspace_icon')
        if not url:
            self.report['warnings'].append('Image de l’espace non disponible via la connexion Notion par jeton ; l’espace Anytwo conserve son icône par défaut.')
            return
        try:
            self.progress('Récupération de l’image de l’espace…')
            content,mime,name=download(url,'workspace-icon',self.check)
            if not mime.startswith('image/'):raise APIError('L’icône de l’espace n’est pas une image.')
            backend.set_space_icon(self.target,self.sid,name,content,mime)
        except APIError as exc:self.report['warnings'].append('Image de l’espace non reprise : '+str(exc))

    def run(self):
        self.collect();self.check()
        self.report['source_schemas']=deepcopy(self.schemas);self.report['source_views']=deepcopy(self.views)
        for oid,page in self.pages.items():
            self.results.setdefault(oid,{'source_id':oid,'name':title(page),'target_id':None,'status':'pending','issues':set(),'errors':[],
                               'source_dates':{'created':page.get('created_time'),'modified':page.get('last_edited_time')}})
        self.metrics(phase='writing');dest=self.options['destination'];self.progress('Ouverture de la destination Anytwo…')
        if self.sid:
            if self.sid not in {s['id'] for s in self.target.spaces()}:raise APIError('L’espace de reprise est supprimé ou inaccessible.')
        elif dest['id']=='__create__':
            self.sid=backend.create_space(self.target,dest['name'].strip())
            # Persist identity before optional media work, so failures cannot lose it.
            self.checkpoint()
            self.copy_workspace_icon()
        else:
            if dest['id'] not in {s['id'] for s in self.target.spaces()}:raise APIError('Espace Anytwo supprimé ou inaccessible ; actualisez la destination.')
            self.sid=dest['id']
        self.checkpoint();self.library=FileLibrary(self.target,self.sid);self.create_schema()
        for oid,page in self.pages.items():
            if oid in self.mapping:continue
            self.check();self.progress('Création de la page : '+title(page));sid=page.get('parent',{}).get('data_source_id')
            icon=page.get('icon') or {};warnings=[]
            target_id=backend.create_object(self.target,self.sid,title(page),[self.collections[sid]] if sid in self.collections else [],content_icon(icon),warnings)
            self.mapping[oid]=target_id;self.results[oid].update(target_id=target_id,status='created');self.issues(oid).update(warnings);self.checkpoint()
        from notion_native import prepare_synced,finalise
        prepare_synced(self)
        # All page identities exist before relations, internal links and file references are written.
        for oid,page in self.pages.items():
            self.check();self.progress('Contenu et propriétés : '+title(page));sid=page.get('parent',{}).get('data_source_id');issues=self.issues(oid)
            for name,prop in page.get('properties',{}).items():
                if prop.get('type')=='title':continue
                binding=self.props.get((sid,prop.get('id')))
                if not binding:
                    issues.add('Propriété sans schéma de collection : '+name)
                    self.results[oid].setdefault('source_values',{})[name]=deepcopy(prop)
                    continue
                if (sid,prop.get('id')) in self.rollups:
                    self.results[oid].setdefault('source_values',{})[name]=deepcopy(prop)
                    issues.add('Rollup natif configuré ; définition et résultat source conservés dans le bilan')
                    continue
                self.check()
                try:
                    value=self.value(oid,sid,name,prop,binding[2])
                    backend.set_column_value(self.target,self.sid,self.mapping[oid],self.collections[sid],binding[0],value)
                    if prop.get('type') in ('date','formula','rollup','relation'):
                        # Keep exact intervals, expressions/results and outside-scope references in private report.
                        self.results[oid].setdefault('source_values',{})[name]=deepcopy(prop)
                except APIError as exc:
                    if exc.status==499:raise
                    self.results[oid]['errors'].append('Propriété '+name+' : '+str(exc))
            content=Content(self,oid);markdown=content.render(self.blocks.get(oid,[]))
            icon=page.get('icon') or {}
            if icon.get('type') in ('file','external') and not emoji(icon):
                uri=self.media(oid,icon,'image')
                if uri:
                    try:backend.set_column_value(self.target,self.sid,self.mapping[oid],'any','icon',str(uri))
                    except APIError:issues.add('Icône image non appliquée')
            if page.get('cover'):
                uri=self.media(oid,page['cover'],'image')
                if uri:markdown=image_markdown(uri,'Couverture')+'\n\n'+markdown;issues.add('Couverture conservée comme image en tête de page')
            try:backend.set_markdown(self.target,self.sid,self.mapping[oid],markdown)
            except APIError as exc:self.results[oid]['errors'].append('Contenu : '+str(exc))
            self.results[oid]['status']='partial' if issues or self.results[oid]['errors'] else 'imported';self.checkpoint()
        finalise(self)
        for sid,cid in self.collections.items():
            self.check();warnings=set()
            try:
                block=self.view_block(sid,warnings)
                root,failed=create_saved_views(self.target,self.sid,cid,block,{'type':'collection','collection_items':[oid for oid,p in self.pages.items() if p.get('parent',{}).get('data_source_id')==sid]},[],converter(self,sid),warnings,table_key='default')
                self.report['views'].append({'source':sid,'target_id':root,'status':'created','failed':failed})
            except (UnsupportedView,APIError) as exc:warnings.add('Vue de collection non convertie : '+str(exc))
            self.report['warnings'].extend(sorted(warnings));self.checkpoint()
        self.report['status']='partial' if any(r['status']=='partial' for r in self.results.values()) or self.report['warnings'] else 'done'
        self.report['finished_at']=datetime.now(timezone.utc).isoformat();self.checkpoint();return self.report
