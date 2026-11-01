"""Explicit, standalone test-page creation. Never called by the read-only importer.
Run without --apply to generate the payloads only. Credentials never enter reports.
"""
from __future__ import annotations
import argparse,hashlib,io,json,math,os,struct,sys,time,urllib.error,urllib.parse,urllib.request,uuid,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server
from runtime_profile import get_profile
from notion_source import Notion,NoRedirect,title
from api_clients import Anytype,APIError
TITLE='Modèle de test — Any2Any'
REPORT=ROOT/'reports'/'source-fixtures.json'

def rich(text,**annotations):return [{'type':'text','text':{'content':text},**({'annotations':annotations} if annotations else {})}]
def nb(kind,text=None,**data):
    if text is not None:data['rich_text']=rich(text)
    return {'object':'block','type':kind,kind:data}
def notion_blocks():
    b=[nb('heading_1','Mises en page et contenu'),nb('paragraph','Données fictives pour contrôler la fidélité des imports. Aucun message n’est envoyé.'),
       nb('paragraph',rich_text=rich('Gras ',bold=True)+rich('Italique ',italic=True)+rich('Souligné ',underline=True)+rich('Barré ',strikethrough=True)+rich('Code',code=True)),
       nb('paragraph',rich_text=rich('Rouge ',color='red')+rich('Fond jaune',color='yellow_background')),nb('paragraph',''),nb('paragraph','Paragraphe après un bloc vide.'),
       nb('heading_2','Listes et cases à cocher'),nb('bulleted_list_item','Niveau 1',children=[nb('bulleted_list_item','Niveau 2')]),nb('numbered_list_item','Première étape'),nb('numbered_list_item','Deuxième étape'),nb('to_do','À faire',checked=False),nb('to_do','Terminé',checked=True),
       nb('toggle','Toggle de texte',children=[nb('paragraph','Contenu repliable'),nb('to_do','Case dans un toggle',checked=True)]),nb('heading_2','Titre repliable',is_toggleable=True,children=[nb('paragraph','Contenu du titre repliable')]),
       nb('quote','Une citation de démonstration.'),nb('callout','Un encadré avec une icône.',icon={'type':'emoji','emoji':'💡'},children=[nb('paragraph','Sous-contenu du callout')]),nb('divider'),
       nb('column_list',children=[nb('column',children=[nb('paragraph','Colonne gauche'),nb('to_do','Case à gauche',checked=False)]),nb('column',children=[nb('paragraph','Colonne droite'),nb('quote','Citation à droite')])]),
       nb('table',table_width=3,has_column_header=True,has_row_header=False,children=[nb('table_row',cells=[rich('Nom'),rich('Prix'),rich('État')]),nb('table_row',cells=[rich('Exemple A'),rich('12,50 €'),rich('Fait')]),nb('table_row',cells=[rich('Exemple B'),rich('8,25 €'),rich('À faire')])]),
       nb('code',rich_text=rich('def addition(a, b):\n    return a + b'),language='python'),nb('equation',expression=r'E=mc^2'),nb('table_of_contents',color='default'),
       nb('heading_2','Liens, médias et références'),nb('bookmark',url='https://www.notion.com/'),nb('embed',url='https://www.youtube.com/watch?v=LMXMbeKyneQ'),nb('video',type='external',external={'url':'https://www.youtube.com/watch?v=LMXMbeKyneQ'}),
       nb('synced_block',synced_from=None,children=[nb('paragraph','Contenu d’un bloc synchronisé de démonstration.')]),nb('breadcrumb'),nb('paragraph','Les bases liées, sous-pages et fichiers sont ajoutés ci-dessous. Certains éléments interactifs (boutons, formulaires, automatisations) ne sont pas entièrement créables via l’API.')]
    return b

def anytype_document():
    def ab(kind,text=None,indent=0,**data):return {'type':kind,'indent':indent,**({'text':text} if text is not None else {}),**data}
    b=[ab('heading_1','Mises en page et contenu'),ab('paragraph','Données fictives pour contrôler la fidélité des imports.'),ab('paragraph','**Gras**, *italique*, <u>souligné</u>, ~~barré~~, `code`, [lien](https://example.com).'),ab('paragraph','<font color="red">Rouge</font> et <font background="yellow">fond jaune</font>.'),ab('paragraph',''),ab('paragraph','Paragraphe après un bloc vide.'),ab('heading_2','Listes et cases'),ab('bulleted_list_item','Niveau 1'),ab('bulleted_list_item','Niveau 2',indent=1),ab('numbered_list_item','Première étape'),ab('numbered_list_item','Deuxième étape'),ab('checkbox','À faire',checked=False),ab('checkbox','Terminé',checked=True),ab('toggle','Toggle de texte'),ab('paragraph','Contenu repliable',indent=1),ab('toggle_heading_2','Titre repliable'),ab('paragraph','Contenu du titre',indent=1),ab('quote','Citation de démonstration'),ab('callout','Un encadré de démonstration',icon={'format':'emoji','emoji':'💡'}),ab('divider',style='line'),ab('row'),ab('column',indent=1),ab('paragraph','Colonne gauche',indent=2),ab('column',indent=1),ab('paragraph','Colonne droite',indent=2),ab('table',columns=[{'width':200},{'width':120}],rows=[{'is_header':True,'cells':['Élément','État']},{'cells':['Case réelle',{'type':'checkbox','text':'Terminé','checked':True}]},{'cells':['Texte en forme',{'type':'paragraph','text':'**Gras** et <u>souligné</u>'}]}]),ab('code','def addition(a, b):\n    return a + b',language='python'),ab('equation','E=mc^2',processor='latex'),ab('embed','https://www.youtube.com/watch?v=LMXMbeKyneQ',processor='youtube'),ab('bookmark',url='https://anytype.io'),ab('table_of_contents'),ab('heading_3','Fin du modèle')]
    return {'formatVersion':'2.0','kind':'page','type':'page','template':'none','icon':{'format':'emoji','emoji':'🧪'},'properties':{'name':TITLE},'blocks':b}

def assets():
    # Small deterministic PNG and WAV plus readable files, all generated locally.
    import zlib
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    pixels=b''.join(b'\0'+b''.join(bytes(((x*255)//319,(y*255)//119,180)) for x in range(320)) for y in range(120))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',320,120,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b'')
    audio=io.BytesIO()
    with wave.open(audio,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes(b''.join(struct.pack('<h',int(5000*math.sin(2*math.pi*440*i/8000))) for i in range(4000)))
    return [('image-test.png','image/png',png,'image'),('audio-test.wav','audio/wav',audio.getvalue(),'audio'),('document-test.txt','text/plain','Pièce jointe de test Any2Any.\n'.encode(),'file'),('tableau-test.csv','text/csv',b'nom;prix\nExemple A;12.50\nExemple B;8.25\n','file')]

class HTTP:
    def __init__(self,base,token,notion=False):self.base=base;self.token=token;self.notion=notion;self.opener=urllib.request.build_opener(NoRedirect());self.last=0
    def request(self,path,method='GET',body=None,raw=None,content_type=None):
        if not path.startswith('/') or '://' in path:raise ValueError('Relative API path required')
        if self.notion:time.sleep(max(0,.36-(time.monotonic()-self.last)));self.last=time.monotonic()
        headers={'Authorization':'Bearer '+self.token,'Content-Type':content_type or 'application/json'}
        if self.notion:headers['Notion-Version']='2026-03-11'
        else:
            if method!='GET':headers['Idempotency-Key']=str(uuid.uuid5(uuid.NAMESPACE_URL,path+json.dumps(body,sort_keys=True)+(hashlib.sha256(raw).hexdigest() if raw is not None else '')))
        data=raw if raw is not None else json.dumps(body,ensure_ascii=False).encode() if body is not None else None
        req=urllib.request.Request(self.base+path,data=data,method=method,headers=headers)
        try:
            with self.opener.open(req,timeout=30) as response:return json.load(response)
        except urllib.error.HTTPError as exc:
            try:message=json.loads(exc.read()).get('message','Request refused')
            except Exception:message='Request refused'
            raise APIError(f'HTTP {exc.code}: {message}',exc.code) from None
    def upload(self,path,name,mime,data):
        boundary='any2any-'+uuid.uuid4().hex
        raw=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n').encode()+data+f'\r\n--{boundary}--\r\n'.encode()
        return self.request(path,'POST',raw=raw,content_type='multipart/form-data; boundary='+boundary)

def save(report):
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def create_notion(report,workspace,parent_title):
    settings=json.loads((get_profile('notion-dev').config_dir/'settings.json').read_text(encoding='utf-8'));token=server.protected_decode(settings.get('notion_token',''))
    reader=Notion(token);identity=reader.identity()
    if identity['workspace_name']!=workspace:raise ValueError('La connexion Notion ne vise pas l’espace demandé.')
    matches=[x for x in reader.paginate('/search',method='POST',body={'query':parent_title,'filter':{'value':'page','property':'object'}}) if title(x)==parent_title and x.get('parent',{}).get('type')=='workspace']
    if len(matches)!=1:raise ValueError('Page racine Test pour Anytwo non identifiée de façon unique.')
    parent=matches[0]['id'];http=HTTP('https://api.notion.com',token,True);state=report.setdefault('notion',{'parent':parent,'steps':{},'warnings':[]});steps=state.setdefault('steps',{});state.setdefault('warnings',[]);state.setdefault('parent',parent)
    if state['parent']!=parent:raise ValueError('Le parent a changé ; vérifier le rapport avant reprise.')
    def step(key,fn):
        if key not in steps:steps[key]=fn();save(report)
        return steps[key]
    model=step('page',lambda:http.request('/v1/pages','POST',{'parent':{'type':'page_id','page_id':parent},'icon':{'type':'emoji','emoji':'🧪'},'properties':{'title':{'type':'title','title':rich(TITLE)}},'children':notion_blocks()}));pid=model['id']
    for name,mime,data,kind in assets():
        def upload(name=name,mime=mime,data=data):
            entry=http.request('/v1/file_uploads','POST',{'mode':'single_part','filename':name,'content_type':mime});sent=http.upload('/v1/file_uploads/'+entry['id']+'/send',name,mime,data);return {'id':entry['id'],'status':sent.get('status')}
        try:
            uploaded=step('upload-'+name,upload)
            if 'block-'+name not in steps:
                entry={kind:{'type':'file_upload','file_upload':{'id':uploaded['id']},'caption':rich(name)},'type':kind,'object':'block'}
                if kind=='file':entry[kind]['name']=name
                result=http.request('/v1/blocks/'+pid+'/children','PATCH',{'children':[entry]});steps['block-'+name]={'ids':[x['id'] for x in result.get('results',[])]};save(report)
        except APIError as exc:state['warnings'].append(name+': '+str(exc));save(report)
    project_properties={'Nom':{'title':{}},'Budget':{'number':{'format':'euro'}},'Actif':{'checkbox':{}},'Type':{'select':{'options':[{'name':'Gagné','color':'green'},{'name':'Dépensé','color':'red'}]}},'Tag':{'multi_select':{'options':[{'name':'Famille','color':'blue'},{'name':'Test','color':'yellow'}]}}}
    def db(name,properties):return http.request('/v1/databases','POST',{'parent':{'type':'page_id','page_id':pid},'title':rich(name),'is_inline':True,'initial_data_source':{'properties':properties}})
    projects=step('projects-db',lambda:db('Projets de test',project_properties));psid=projects['data_sources'][0]['id']
    tasks_props={'Nom':{'title':{}},'Projet':{'relation':{'data_source_id':psid,'single_property':{}}},'Prix':{'number':{'format':'euro'}},'Date':{'date':{}},'Terminé':{'checkbox':{}},'Notes':{'rich_text':{}},'Site':{'url':{}},'Courriel':{'email':{}},'Téléphone':{'phone_number':{}},'Prix doublé':{'formula':{'expression':'prop("Prix") * 2'}},'Budget lié':{'rollup':{'relation_property_name':'Projet','rollup_property_name':'Budget','function':'sum'}},'Noms liés':{'rollup':{'relation_property_name':'Projet','rollup_property_name':'Nom','function':'show_original'}}}
    tasks=step('tasks-db',lambda:db('Tâches de test',tasks_props));tsid=tasks['data_sources'][0]['id']
    def row(sid,props):return http.request('/v1/pages','POST',{'parent':{'type':'data_source_id','data_source_id':sid},'properties':props})
    a=step('project-a',lambda:row(psid,{'Nom':{'title':rich('Projet A')},'Budget':{'number':100},'Actif':{'checkbox':True},'Type':{'select':{'name':'Gagné'}},'Tag':{'multi_select':[{'name':'Famille'},{'name':'Test'}]}}))
    b=step('project-b',lambda:row(psid,{'Nom':{'title':rich('Projet B')},'Budget':{'number':80},'Actif':{'checkbox':False},'Type':{'select':{'name':'Dépensé'}}}))
    for i,(name,price,done,links) in enumerate([('Tâche simple',12.5,False,[a['id']]),('Tâche terminée',8.25,True,[a['id'],b['id']]),('Tâche sans relation',0,False,[])]):
        step('task-'+str(i),lambda name=name,price=price,done=done,links=links:row(tsid,{'Nom':{'title':rich(name)},'Prix':{'number':price},'Terminé':{'checkbox':done},'Projet':{'relation':[{'id':x} for x in links]},'Date':{'date':{'start':'2026-10-31T14:30:00+01:00'}},'Notes':{'rich_text':rich('Texte de test souligné',underline=True)},'Site':{'url':'https://example.com'},'Courriel':{'email':'test@example.com'},'Téléphone':{'phone_number':'+33 1 00 00 00 00'}}))
    child=step('child',lambda:http.request('/v1/pages','POST',{'parent':{'page_id':pid},'properties':{'title':{'title':rich('Sous-page de démonstration')}},'children':[nb('paragraph','Cette page est liée à plusieurs endroits pour tester le remappage des références.')]}))
    step('references',lambda:http.request('/v1/blocks/'+pid+'/children','PATCH',{'children':[nb('link_to_page',type='page_id',page_id=child['id']),nb('paragraph',rich_text=[{'type':'mention','mention':{'type':'page','page':{'id':child['id']}}}])]}))
    if 'extra-media-reference' not in steps and 'upload-image-test.png' in steps:
        step('extra-media-reference',lambda:http.request('/v1/blocks/'+pid+'/children','PATCH',{'children':[nb('image',type='file_upload',file_upload={'id':steps['upload-image-test.png']['id']},caption=rich('Même image, deuxième emplacement'))]}))
    originals=[x for x in reader.children(pid) if x.get('type')=='synced_block' and not x['synced_block'].get('synced_from')]
    if originals:step('synced-reference',lambda:http.request('/v1/blocks/'+pid+'/children','PATCH',{'children':[nb('synced_block',synced_from={'type':'block_id','block_id':originals[0]['id']})]}))
    try:
        schema=reader.data_source(tsid);properties=schema['properties']
        step('filtered-view',lambda:http.request('/v1/views','POST',{'database_id':tasks['id'],'data_source_id':tsid,'name':'Tâches ouvertes — filtrées','type':'table','filter':{'property':'Terminé','checkbox':{'equals':False}},'sorts':[{'property':'Date','direction':'ascending'}],'configuration':{'type':'table','properties':[{'property_id':prop['id'],'visible':name in ('Nom','Date','Prix','Projet','Budget lié')} for name,prop in properties.items()]}}))
    except APIError as exc:
        warning='Vue filtrée : '+str(exc)
        if warning not in state['warnings']:state['warnings'].append(warning)
    state.pop('error',None)
    state.update(url=model.get('url'),verified={'top_blocks':len(reader.children(pid)),'project_rows':len(reader.paginate('/data_sources/'+psid+'/query',method='POST')),'task_rows':len(reader.paginate('/data_sources/'+tsid+'/query',method='POST'))});save(report)
    return state

def create_anytype(report):
    settings=json.loads((Path(os.environ['APPDATA'])/'anytype-anytwo-importer'/'settings.json').read_text(encoding='utf-8'));key=server.protected_decode(settings.get('anytype_key',''));api=Anytype(settings.get('anytype_port',31009),key)
    grant=api.request('/auth/whoami').get('grant',{})
    if grant.get('permission')=='read':raise APIError('La clé Anytype est encore en lecture seule.',403)
    http=HTTP('http://127.0.0.1:'+str(api.port),key);state=report.setdefault('anytype',{'steps':{},'warnings':[]});steps=state.setdefault('steps',{});state.setdefault('warnings',[])
    if 'space' not in steps:
        existing=[s for s in api.spaces() if s['name']=='Test pour Anytwo']
        if len(existing)>1:raise ValueError('Plusieurs espaces Test pour Anytwo : vérifier la cible avant création.')
        try:space=existing[0] if len(existing)==1 else http.request('/v2/spaces?ids=full','POST',{'name':'Test pour Anytwo','description':'Banc d’essai Any2Any — données fictives'})
        except APIError as exc:
            if exc.status not in (403,409,422,501):raise
            candidates=[s for s in api.spaces() if s['name']=='Cobaye1']
            if len(candidates)!=1:raise ValueError('Espace de repli Cobaye1 non identifié.')
            space=candidates[0];state['warnings'].append('Création d’espace refusée : utilisation de Cobaye1.')
        steps['space']=space;save(report)
    sid=steps['space']['id'];path='/v2/spaces/'+urllib.parse.quote(sid,safe='')
    if 'page' not in steps:
        document=anytype_document();validation=api.request('/validate',method='POST',body=document)
        if validation.get('errors'):raise ValueError('Document Anytype invalide : '+json.dumps(validation['errors']))
        steps['page']=http.request(path+'/objects?ids=full','POST',document);save(report)
    def step(key,fn):
        if key not in steps:steps[key]=fn();save(report)
        return steps[key]
    pid=steps['page']['id'];media=[]
    for name,mime,data,kind in assets():
        file=step('file-'+name,lambda name=name,mime=mime,data=data:http.upload(path+'/files',name,mime,data))
        media.append({'type':kind,'object_id':file['id'],'name':name,'mime_type':mime,'style':'embed' if kind in ('image','audio') else 'link'})
    media.append({'type':'image','object_id':steps['file-image-test.png']['id'],'name':'image-test.png','style':'embed'})
    step('media-blocks',lambda:http.request(path+'/objects/'+pid,'PATCH',{'ops':[{'op':'insert_blocks','blocks':[{'type':'heading_2','text':'Fichiers et médias'},*media]}]}))
    definitions=[{'name':'Prix test','key':'a2a_prix','format':'number'},{'name':'Type test','key':'a2a_type','format':'select','options':[{'name':'Gagné','color':'green'},{'name':'Dépensé','color':'red'}]},{'name':'Tag test','key':'a2a_tag','format':'multi_select','options':[{'name':'Famille','color':'blue'},{'name':'Test','color':'yellow'}]},{'name':'Date test','key':'a2a_date','format':'date'},{'name':'Terminé test','key':'a2a_done','format':'checkbox'},{'name':'Relation test','key':'a2a_relation','format':'objects'}]
    for definition in definitions:step('property-'+definition['key'],lambda definition=definition:http.request(path+'/properties','POST',definition))
    sample_a=step('sample-a',lambda:http.request(path+'/objects?ids=full','POST',{'type':'page','name':'Exemple A — Gagné','properties':{'Prix test':12.5,'Type test':'Gagné','Tag test':['Famille','Test'],'Terminé test':False,'Date test':'2026-10-31'},'markdown':'Exemple avec propriétés et options colorées.'}))
    sample_b=step('sample-b',lambda:http.request(path+'/objects?ids=full','POST',{'type':'page','name':'Exemple B — Dépensé','properties':{'Prix test':8.25,'Type test':'Dépensé','Tag test':['Test'],'Terminé test':True,'Relation test':[sample_a['id']]},'markdown':'Cet objet est lié à Exemple A.'}))
    collection=step('collection',lambda:http.request(path+'/collections?ids=full','POST',{'name':'Collection de test','items':[sample_a['id'],sample_b['id']]}))
    step('sample-type',lambda:http.request(path+'/types?ids=full','POST',{'name':'Exemple Any2Any','plural_name':'Exemples Any2Any','api_key':'a2a_demo','layout':'basic','property_definitions':[{'property':definition['key'],'section':'hidden' if definition['format']=='multi_select' else 'featured'} for definition in definitions]}))
    for key in ('sample-a','sample-b'):step('type-'+key,lambda key=key:http.request(path+'/objects/'+steps[key]['id'],'PATCH',{'ops':[{'op':'set_type','type':'a2a_demo'}]}))
    columns=[{'property':'name','width':240},{'property':'Prix test','aggregation':'sum'},{'property':'Type test'},{'property':'Tag test','hidden':True},{'property':'Date test'},{'property':'Terminé test'}]
    views=[{'name':'Ouvertes','type':'table','filters':[{'property':'Terminé test','condition':'equal','value':False}],'sorts':[{'property':'Date test','direction':'asc'}],'columns':columns},{'name':'Toutes en liste','type':'list','columns':columns}]
    query=step('query',lambda:http.request(path+'/queries?ids=full','POST',{'name':'Query de test — filtres et tris','type':'a2a_demo','views':views}))
    blocks=[{'type':'heading_2','text':'Collections, vues et relations'},{'type':'link','object_id':sample_a['id'],'card_style':'card'},{'type':'link','object_id':sample_b['id'],'card_style':'text'},{'type':'link','object_id':collection['id'],'card_style':'card'},{'type':'dataview','object_id':query['id'],'views':views}]
    step('views-blocks',lambda:http.request(path+'/objects/'+pid,'PATCH',{'ops':[{'op':'insert_blocks','blocks':blocks}]}))
    readback=api.request('/spaces/'+sid+'/objects/'+pid+'?ids=full');state['verified']={'blocks':len(readback.get('blocks',[])),'files':len(media)-1,'sample_pages':2,'collection':collection['id'],'query':query['id']}
    state.pop('error',None);state['result']=steps['page'];save(report);return state

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--notion-workspace');parser.add_argument('--notion-parent',default='Test pour Anytwo');parser.add_argument('--apply',action='store_true');parser.add_argument('--source',choices=('notion','anytype','all'),default='all');args=parser.parse_args()
    (ROOT/'examples').mkdir(exist_ok=True)
    (ROOT/'examples'/'notion-test-page.json').write_text(json.dumps({'title':TITLE,'children':notion_blocks()},ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'examples'/'anytype-test-page.json').write_text(json.dumps(anytype_document(),ensure_ascii=False,indent=2),encoding='utf-8')
    if not args.apply:print('Payloads generated. --apply explicitly creates the requested source fixtures.');return
    if args.source in ('notion','all') and not args.notion_workspace:parser.error('--notion-workspace est requis pour confirmer l’espace Notion visé.')
    report=json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.exists() else {}
    for source,fn in (('notion',create_notion),('anytype',create_anytype)):
        if args.source not in ('all',source):continue
        try:
            value=fn(report,args.notion_workspace,args.notion_parent) if source=='notion' else fn(report);print(source,json.dumps({'url':value.get('url'),'verified':value.get('verified'),'warnings':value.get('warnings'), 'result':value.get('result')},ensure_ascii=False))
        except Exception as exc:
            report.setdefault(source,{})['error']=str(exc);save(report);print(source,type(exc).__name__,str(exc))
if __name__=='__main__':main()
