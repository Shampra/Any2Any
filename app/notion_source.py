"""Read-only Notion API client (2026-03-11); no mutation endpoints."""
from __future__ import annotations
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from api_clients import APIError

API_VERSION='2026-03-11'
MAX_ITEMS=2000
MAX_BLOCKS=5000
READ_ROUTES={
    'GET':re.compile(r'^/(users/me|pages/[0-9a-f-]+(?:/properties/[A-Za-z0-9%_.~!-]+)?|data_sources/[0-9a-f-]+|databases/[0-9a-f-]+|blocks/[0-9a-f-]+(?:/children)?|views|views/[0-9a-f-]+)$'),
    'POST':re.compile(r'^/(search|data_sources/[0-9a-f-]+/query)$'),
}
CATALOG_WARNING='La recherche Notion peut avoir un délai d’indexation. Le périmètre est le contenu accessible à cette connexion, pas une garantie d’export complet de l’espace. Ajoutez une page ou base par son lien si nécessaire.'


def notion_id(value):
    value=str(value or '').strip()
    if '://' in value:
        parsed=urllib.parse.urlsplit(value)
        host=(parsed.hostname or '').lower()
        if parsed.scheme!='https' or not any(host==d or host.endswith('.'+d) for d in ('notion.so','notion.site','notion.com')):
            raise ValueError('Utilisez un lien Notion HTTPS ou son identifiant.')
        matches=re.findall(r'[0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',parsed.path)
        if not matches:raise ValueError('Identifiant Notion absent du lien.')
        value=matches[-1]
    try:return str(uuid.UUID(value))
    except (ValueError,AttributeError):raise ValueError('Identifiant Notion invalide.') from None


def text(items):
    return ''.join(str(x.get('plain_text') or x.get('text',{}).get('content') or '') for x in items or [] if isinstance(x,dict))


def title(obj):
    for prop in (obj.get('properties') or {}).values():
        if prop.get('type')=='title':return text(prop.get('title')) or '(Sans titre)'
    return text(obj.get('title')) or str(obj.get('name') or '(Sans titre)')


def summary(obj):
    return {'id':obj['id'],'name':title(obj),'kind':obj.get('object','page'),
            'parent':obj.get('parent') or {}}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


class Notion:
    def __init__(self,token):
        self._token=str(token or '').strip()
        if not self._token or len(self._token)>4096 or '\n' in self._token or '\r' in self._token:
            raise APIError('Saisissez le jeton Notion dans ce formulaire local.')
        self._lock=threading.Lock();self._last=0.;self._cooldown=0.;self.interval=.35;self.deadline=None
        self._inflight=threading.BoundedSemaphore(4);self._transport=threading.local();self._cache_lock=threading.Lock();self._read_cache=None;self.check_cancel=None
        self.progress=None;self._child_cache=None;self.telemetry=None;self.statistics=None
        self._opener=urllib.request.build_opener(NoRedirect());self._transport.opener=self._opener

    def _check(self):
        if self.check_cancel:self.check_cancel()
        if self.deadline is not None and time.monotonic()>=self.deadline:
            raise APIError('Délai de lecture Notion dépassé. Réessayez ou choisissez un périmètre plus petit.',504)

    def _pause(self,seconds):
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            self._check();time.sleep(min(.1,max(0,until-time.monotonic())))

    def request(self,path,*,method='GET',body=None):
        self._check();endpoint=urllib.parse.urlsplit(path)
        if endpoint.scheme or endpoint.netloc or not READ_ROUTES.get(method,re.compile(r'(?!)')).fullmatch(endpoint.path):
            raise APIError('Opération Notion interdite : ce connecteur est en lecture seule.')
        def load():return self._request(path,method,body)
        if self._read_cache is not None:
            key=(method,path,json.dumps(body,sort_keys=True,separators=(',',':')))
            return self._read_cache.read(key,load,self._check)
        return load()

    def _request(self,path,method,body):
        for attempt in range(3):
            self._check()
            while not self._inflight.acquire(timeout=.1):self._check()
            try:
                # Reserve starts at a global rate; network waits overlap across workers.
                while True:
                    self._check()
                    with self._lock:
                        now=time.monotonic();delay=max(self.interval-(now-self._last),self._cooldown-now,0)
                        if delay<=0:self._last=now;break
                    self._pause(min(delay,.1))
                if self.telemetry:self.telemetry(path)
                if self.progress:self.progress(None)
                try:return self._send(path,method,body)
                except urllib.error.HTTPError as exc:
                    if exc.code in (429,529):
                        try:retry=max(0,float(exc.headers.get('Retry-After',str(2**attempt))))
                        except ValueError:retry=2**attempt
                        with self._lock:self._cooldown=max(self._cooldown,time.monotonic()+retry)
                        if attempt<2 and retry<=60 and (self.deadline is None or time.monotonic()+retry<self.deadline):
                            if self.progress:self.progress(f'Pause demandée par Notion : {retry:g} seconde(s)…')
                            continue
                        raise APIError('Notion limite les requêtes. Réessayez après le délai indiqué par son service.',exc.code) from None
                    messages={401:'Jeton Notion invalide ou révoqué.',403:'Accès Notion refusé : vérifiez la lecture du contenu et les pages autorisées.',404:'Objet Notion introuvable ou non partagé avec la connexion.'}
                    raise APIError(messages.get(exc.code,f'Notion répond HTTP {exc.code} ; aucune écriture source effectuée.'),exc.code) from None
                except (urllib.error.URLError,OSError,TimeoutError) as exc:
                    self._check()
                    if isinstance(exc,TimeoutError) or isinstance(getattr(exc,'reason',None),TimeoutError):
                        raise APIError('Notion ne répond pas dans le délai de la requête. Les lectures terminées sont conservées ; réessayez.',504) from None
                    raise APIError('Connexion à Notion interrompue. Les lectures terminées sont conservées ; vérifiez le réseau puis réessayez.') from None
            finally:self._inflight.release()

    def _send(self,path,method,body):
        data=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request('https://api.notion.com/v1'+path,data=data,method=method,
            headers={'Authorization':'Bearer '+self._token,'Notion-Version':API_VERSION,
                     'Content-Type':'application/json','User-Agent':'Any2Any-Notion-Development'})
        timeout=min(25,max(.1,self.deadline-time.monotonic())) if self.deadline is not None else 25
        opener=getattr(self._transport,'opener',None)
        if opener is None:opener=urllib.request.build_opener(NoRedirect());self._transport.opener=opener
        with opener.open(req,timeout=timeout) as response:
            raw=response.read(16*1024*1024+1)
        if len(raw)>16*1024*1024:raise APIError('Réponse Notion trop volumineuse ; réduisez la sélection.')
        try:
            value=json.loads(raw)
            if not isinstance(value,dict):raise ValueError()
            return value
        except (ValueError,UnicodeDecodeError):raise APIError('Réponse Notion non reconnue.') from None

    def paginate(self,path,*,method='GET',body=None):
        result=[];cursor=None;seen=set()
        for _ in range(100):
            payload={**(body or {}),'page_size':100}
            if cursor:payload['start_cursor']=cursor
            if method=='GET':
                sep='&' if '?' in path else '?'
                data=self.request(path+sep+urllib.parse.urlencode(payload))
            else:data=self.request(path,method=method,body=payload)
            if not isinstance(data,dict) or not isinstance(data.get('results'),list):raise APIError('Liste Notion non reconnue.')
            result.extend(data['results'])
            status=data.get('request_status') or {}
            if status.get('incomplete_reason'):raise APIError('Notion indique une liste incomplète : réduisez le périmètre.')
            if data.get('has_more') is False:return result
            if 'has_more' not in data:raise APIError('Pagination Notion non vérifiable.')
            cursor=data.get('next_cursor')
            if not cursor or cursor in seen:raise APIError('Pagination Notion bloquée ; liste incomplète refusée.')
            seen.add(cursor)
        raise APIError('Limite de pagination atteinte ; liste Notion incomplète refusée.')

    def identity(self):
        obj=self.request('/users/me')
        if obj.get('object')!='user' or not obj.get('id'):raise APIError('Identité Notion non reconnue.')
        bot=obj.get('bot') or {}
        return {'name':obj.get('name') or 'Connexion Notion','workspace_name':bot.get('workspace_name') or 'Contenu Notion autorisé','api_version':API_VERSION,'workspace_icon':bot.get('workspace_icon')}

    def page(self,value):return self.request('/pages/'+notion_id(value))
    def complete_property(self,page_id,prop):
        """Read all items for properties that the page response may truncate."""
        kind=prop.get('type')
        if kind not in ('title','rich_text','relation','people','formula','rollup'):return prop
        # Page/query values are authoritative unless they can be truncated.
        if not prop.get('has_more'):
            value=prop.get(kind)
            if kind=='relation' and prop.get('has_more') is False:return prop
            if kind in ('title','rich_text','people') and isinstance(value,list):
                if kind=='people' and len(value)<25:return prop
                if kind in ('title','rich_text') and len(value)<25 and sum(x.get('type')=='mention' for x in value)<25:return prop
            if kind=='formula' and isinstance(value,dict) and value.get('type') in ('number','boolean','date'):return prop
            if kind=='rollup' and isinstance(value,dict) and value.get('type') in ('number','date'):return prop
        pid=urllib.parse.quote(urllib.parse.unquote(str(prop['id'])),safe='')
        path='/pages/'+notion_id(page_id)+'/properties/'+pid
        data=self.request(path+'?page_size=100')
        if data.get('object')!='list':return {**prop,**{k:v for k,v in data.items() if k not in ('object','id')}}
        rows=[];seen=set()
        for _ in range(100):
            rows.extend(data.get('results',[]))
            if not data.get('has_more'):break
            cursor=data.get('next_cursor')
            if not cursor or cursor in seen:raise APIError('Pagination de propriété bloquée.')
            seen.add(cursor);data=self.request(path+'?'+urllib.parse.urlencode({'page_size':100,'start_cursor':cursor}))
        else:raise APIError('Propriété trop volumineuse ; lecture incomplète refusée.')
        if kind in ('title','rich_text','relation','people'):
            return {**prop,kind:[row[kind] for row in rows if kind in row],'has_more':False}
        final=(data.get('property_item') or {}).get(kind)
        if final is not None:return {**prop,kind:final}
        raise APIError('Résultat calculé complet indisponible.')
    def database(self,value):return self.request('/databases/'+notion_id(value))
    def data_source(self,value):return self.request('/data_sources/'+notion_id(value))
    def block(self,value):return self.request('/blocks/'+notion_id(value))
    def children(self,value):
        oid=notion_id(value);cache=self._child_cache
        if cache is not None and oid in cache:return cache[oid]
        result=self.paginate('/blocks/'+oid+'/children')
        with self._cache_lock:
            if cache is not None and sum(map(len,cache.values()))+len(result)<=MAX_BLOCKS:cache[oid]=result
        return result
    def views(self,value):
        rows=self.paginate('/views?database_id='+notion_id(value))
        return [self.request('/views/'+notion_id(row['id'])) for row in rows]

    def catalog(self):
        found=self.paginate('/search',method='POST');pages={};sources={};databases={};warnings=[CATALOG_WARNING]
        for obj in found:
            if obj.get('in_trash') or obj.get('archived'):continue
            if obj.get('object')=='page':pages[obj['id']]=summary(obj)
            elif obj.get('object')=='data_source':sources[obj['id']]=summary(obj)
        parents={s['parent'].get('database_id') for s in sources.values()}-{None}
        for did in sorted(parents):
            try:
                db=self.database(did);databases[db['id']]=summary(db)
                for item in db.get('data_sources',[]):
                    sources.setdefault(item['id'],{'id':item['id'],'name':item.get('name') or title(db),'kind':'data_source','parent':{'database_id':db['id']}})
            except APIError as exc:warnings.append('Base parente non lisible : '+str(exc))
        sort=lambda values:sorted(values,key=lambda x:(x['name'].casefold(),x['id']))
        return {'pages':sort(pages.values()),'databases':sort(databases.values()),'data_sources':sort(sources.values()),'warnings':warnings}

    def resolve(self,value):
        oid=notion_id(value)
        for getter in (self.page,self.database,self.data_source):
            try:return summary(getter(oid))
            except APIError as exc:
                if exc.status not in (400,404):raise
        raise APIError('Page/base/source inaccessible. Vérifiez son partage avec la connexion.',404)

    def selection(self,kind,value=None,include_subpages=True,excluded=None,allow_excluded_parent=False):
        excluded=set(excluded or ());pages={};schemas={};warnings=[];visited=set();block_count=0
        def add(obj):
            parent=obj.get('parent') or {}
            if obj['id'] in excluded or ((not allow_excluded_parent or obj['id']!=value) and any(parent.get(k) in excluded for k in ('page_id','database_id','data_source_id','block_id'))) or obj.get('archived') or obj.get('in_trash'):return
            pages[obj['id']]=obj
            if self.statistics:self.statistics(pages=len(pages))
            if self.progress:self.progress(f'Sélection : {len(pages)} page(s) repérée(s)…')
            if len(pages)>MAX_ITEMS:raise APIError(f'Sélection supérieure à {MAX_ITEMS} pages : choisissez une base ou page plus précise.')
        def source(sid):
            sid=notion_id(sid)
            if sid in excluded or sid in schemas:return
            schema=self.data_source(sid)
            if (not allow_excluded_parent or sid!=value) and (schema.get('parent') or {}).get('database_id') in excluded:return
            schemas[sid]=schema
            for obj in self.paginate('/data_sources/'+sid+'/query',method='POST'):add(obj)
        def database(did):
            if did in excluded:return
            db=self.database(did)
            for item in db.get('data_sources',[]):source(item['id'])
        if kind=='accessible':
            cat=self.catalog();warnings.extend(cat['warnings'])
            for obj in cat['pages']:add(self.page(obj['id']))
            for item in cat['data_sources']:source(item['id'])
            roots=list(pages)
        elif kind=='database':database(value);roots=list(pages)
        elif kind=='data_source':source(value);roots=list(pages)
        elif kind=='page':
            if value in excluded:return {'pages':{},'schemas':{},'warnings':[]}
            obj=self.page(value);add(obj);roots=list(pages)
        else:raise ValueError('Choisissez contenu accessible, base, source de données ou page.')
        if include_subpages:
            count_lock=threading.Lock()
            def scan(oid):
                nonlocal block_count
                found_pages=[];found_databases=[];containers=[oid];seen_blocks=set()
                while containers:
                    self._check();bid=containers.pop()
                    if bid in seen_blocks:continue
                    seen_blocks.add(bid)
                    for block in self.children(bid):
                        if block['id'] in excluded:continue
                        with count_lock:
                            block_count+=1
                            if self.statistics:self.statistics(blocks=block_count)
                            if block_count>MAX_BLOCKS:raise APIError('Arborescence trop volumineuse ; choisissez un périmètre plus petit.')
                        typ=block.get('type')
                        if typ=='child_page':found_pages.append(block['id'])
                        elif typ=='child_database':found_databases.append(block['id'])
                        elif block.get('has_children'):containers.append(block['id'])
                return found_pages,found_databases
            queue=list(dict.fromkeys(roots))
            with ThreadPoolExecutor(max_workers=4) as pool:
                while queue:
                    batch=list(dict.fromkeys(oid for oid in queue[:4] if oid not in visited));queue=queue[4:];visited.update(batch)
                    for child_pages,child_databases in pool.map(scan,batch):
                        for child in pool.map(self.page,list(dict.fromkeys(oid for oid in child_pages if oid not in pages))):add(child)
                        queue.extend(oid for oid in child_pages if oid not in visited and oid not in excluded)
                        for did in child_databases:
                            before=set(pages);database(did);queue.extend(sorted(set(pages)-before))
        for obj in list(pages.values()):
            sid=(obj.get('parent') or {}).get('data_source_id')
            if sid and sid not in schemas:schemas[sid]=self.data_source(sid)
        return {'pages':pages,'schemas':schemas,'warnings':warnings}

    def analyse(self,selection,ids):
        chosen=list(dict.fromkeys(ids));pages=selection['pages']
        if (not chosen and not selection['schemas']) or any(oid not in pages for oid in chosen):raise ValueError('Sélection invalide : rechargez les éléments.')
        blocks=Counter();properties=Counter();warnings=set(selection['warnings']);visited=set()
        for index,oid in enumerate(chosen,1):
            if self.progress:self.progress(f'Analyse des pages : {index} / {len(chosen)}…')
            obj=pages[oid]
            for prop in obj.get('properties',{}).values():
                typ=prop.get('type','unknown');properties[typ]+=1
                if prop.get('has_more') or typ in ('relation','people','rich_text','title','formula','rollup'):
                    warnings.add('Les propriétés paginées et calculées devront être relues intégralement lors de l’import ; cette analyse ne valide pas leur exhaustivité.')
            pending=[oid]
            while pending:
                bid=pending.pop()
                if bid in visited:continue
                visited.add(bid)
                for block in self.children(bid):
                    typ=block.get('type','unsupported');blocks[typ]+=1
                    if sum(blocks.values())>MAX_BLOCKS:raise APIError('Analyse trop volumineuse : réduisez la sélection.')
                    if typ=='unsupported':warnings.add('Contenu inaccessible à l’API Notion : '+str((block.get('unsupported') or {}).get('block_type','inconnu')))
                    if block.get('has_children') and typ not in ('child_page','child_database'):pending.append(block['id'])
        views=[]
        dbs={s.get('parent',{}).get('database_id') for s in selection['schemas'].values()}-{None}
        for did in dbs:
            try:views.extend(self.views(did))
            except APIError as exc:warnings.add('Réglages de vues non lus : '+str(exc))
        from notion_compatibility import assess
        compatibility=assess(blocks,properties,views)
        return {'compatibility':compatibility,'selected_pages':len(chosen),'blocks':dict(blocks),'property_types':dict(properties),
                'data_sources':[{'id':s['id'],'name':title(s),'properties':s.get('properties',{})} for s in selection['schemas'].values()],
                'views':views,'warnings':sorted(warnings),
                'import_available':True,'source_modified':False,
                'next_step':'Vérification terminée : choisissez la destination Anytwo puis lancez Importer. Les adaptations seront détaillées dans le bilan.'}
