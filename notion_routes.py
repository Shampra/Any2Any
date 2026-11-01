"""Local Notion connection, scoped inventory and read-only analysis routes."""
from copy import deepcopy
import threading
import uuid
import time
from contextlib import contextmanager
from urllib.parse import parse_qs
from api_clients import APIError
from anytwo_backend import Anytwo
from notion_source import Notion,summary
import notion_tree
from notion_cache import session_cache

LOCK=threading.RLock()

@contextmanager
def budget(client,seconds):
    previous=getattr(client,'deadline',None)
    client.deadline=time.monotonic()+seconds
    try:yield
    finally:client.deadline=previous



@contextmanager
def access():
    if not LOCK.acquire(timeout=.25):raise APIError('Une lecture Notion est déjà en cours. Réessayez dans quelques secondes.',409)
    try:yield
    finally:LOCK.release()


def handle(method,path,data,state,save_settings,protect_encode,query='',import_lock=None,save_report=None):
    if not isinstance(data,dict):raise ValueError('Objet JSON attendu.')
    if path in ('/api/notion/job','/api/notion/cancel'):
        from notion_jobs import inspect_job
        return inspect_job(method,path,data,query,state.get('notion',{}))
    with access():
        session=state.setdefault('notion',{'selections':{}})
        settings=state['settings']
        if method=='GET' and path=='/api/notion/status':
            return {'connected':bool(session.get('client')),'has_token':bool(settings.get('notion_token')),
                    'identity':session.get('identity'),'remembered':bool(settings.get('notion_remember')),'import_available':not state['demo']}
        if method=='POST' and path=='/api/notion/connect':
            if state['demo']:
                from notion_demo import DemoNotion
                client=DemoNotion();token='demo-not-sent'
            else:
                token=str(data.get('token') or settings.get('notion_token') or '').strip()
                client=Notion(token)
            remember=data.get('remember',False)
            if not isinstance(remember,bool):raise ValueError('Choix de mémorisation invalide.')
            if remember and not state['demo'] and not protect_encode(token).startswith('dpapi:'):
                raise APIError('Mémorisation sécurisée indisponible. Décochez la mémorisation pour utiliser la session seulement.')
            with budget(client,5):
                identity=client.identity()
                client.request('/search',method='POST',body={'page_size':1})
            catalog={'pages':[],'databases':[],'data_sources':[],
                     'warnings':['Connexion validée. Inventaire à charger ; vous pouvez aussi ajouter directement une page ou une base par son lien.']}
            previous=deepcopy(settings)
            try:
                settings.update(notion_token=token,notion_remember=remember)
                if not state['demo']:save_settings()
            except Exception:
                settings.clear();settings.update(previous);raise
            state['notion']={'client':client,'identity':identity,'catalog':catalog,'nodes':{},'loaded_nodes':set(),'catalog_loaded':False,'selections':{}}
            return {'connected':True,'identity':identity,'catalog':catalog,'has_token':bool(token),'remembered':remember,'import_available':not state['demo']}
        if method=='POST' and path=='/api/notion/disconnect':
            settings.update(notion_token='',notion_remember=False)
            if not state['demo']:save_settings()
            state['notion']={'selections':{}}
            return {'connected':False}
        client=session.get('client')
        if client is None:raise APIError('Validez d’abord la connexion Notion dans le formulaire local.',401)
        if method=='POST' and path=='/api/notion/import':
            if state['demo']:raise APIError('Le mode démo ne crée aucune donnée. Connectez Notion pour importer.',400)
            if import_lock is None or save_report is None:raise APIError('Service d’import indisponible.',503)
            from notion_import_jobs import start
            return start(session,data,LOCK,import_lock,budget,settings['anytwo_port'],save_report)
        if method=='GET' and path=='/api/notion/catalog' and parse_qs(query).get('refresh')==['true']:
            session.pop('read_checkpoint',None);session.pop('import_checkpoint',None)
        client._read_cache=session_cache(session)
        if method=='GET' and path=='/api/notion/catalog':
            if parse_qs(query).get('refresh')==['true']:
                with budget(client,90):
                    catalog=client.catalog();items=notion_tree.nodes(catalog)
                    catalog['warnings'].extend(notion_tree.repair(client,items))
                session['catalog']=catalog;session['nodes']=items;session['loaded_nodes']=set();session['catalog_loaded']=True;session.pop('analysis_checkpoint',None)
            return session['catalog']
        if method=='POST' and path=='/api/notion/resolve':
            with budget(client,40):obj=client.resolve(data.get('reference'))
            field={'page':'pages','database':'databases','data_source':'data_sources'}.get(obj['kind'])
            if field is None:raise ValueError('Cet objet Notion n’est pas sélectionnable.')
            cat=session['catalog'];cat[field]=[x for x in cat[field] if x['id']!=obj['id']]+[obj]
            session.setdefault('nodes',{})[notion_tree.key(obj)]=obj
            session.pop('analysis_checkpoint',None)
            return {'object':obj,'catalog':cat}
        if method=='GET' and path=='/api/notion/tree':
            return {'nodes':notion_tree.navigation(session.get('nodes',{})),
                    'loaded':session.get('catalog_loaded',False),'loaded_nodes':sorted(session.get('loaded_nodes',set())),'warnings':session['catalog']['warnings']}
        if method=='POST' and path=='/api/notion/children':
            node=session.get('nodes',{}).get(data.get('key'))
            if node is None:raise ValueError('Élément inconnu : rechargez l’arborescence.')
            visible={notion_tree.key(x):x for x in notion_tree.navigation(session['nodes'])}
            if data.get('key') not in visible or visible[data['key']]['selection_leaf']:
                raise ValueError('La sélection est limitée à la racine et deux niveaux. Les descendants seront inclus avec leur parent.')
            k=notion_tree.key(node);loaded=session.setdefault('loaded_nodes',set())
            if k not in loaded:
                with budget(client,8 if data.get('prefetch') is True else 30):items=notion_tree.children(client,node)
                for obj in items:session['nodes'][notion_tree.key(obj)]=obj
                loaded.add(k)
            return {'nodes':notion_tree.navigation(session['nodes']),'expanded':k,'loaded_nodes':sorted(loaded)}
        if method=='POST' and path=='/api/notion/analyse':
            from notion_jobs import start
            return start(session,data,LOCK,budget)
        if method=='POST' and path=='/api/notion/tree-selection':
            with budget(client,90):selection=notion_tree.select(client,session.get('nodes',{}),data.get('rules'),data.get('whole',False),session['catalog'])
            ticket=str(uuid.uuid4());session['selections'][ticket]=selection
            while len(session['selections'])>4:session['selections'].pop(next(iter(session['selections'])))
            return {'ticket':ticket,'pages':[summary(x) for x in selection['pages'].values()],
                    'warnings':selection['warnings'],'import_available':not state['demo']}
        if method=='POST' and path=='/api/notion/selection':
            kind=data.get('kind');oid=data.get('id')
            if kind!='accessible':
                field={'page':'pages','database':'databases','data_source':'data_sources'}.get(kind)
                if not field or not any(x['id']==oid for x in session['catalog'][field]):
                    raise ValueError('Choisissez un élément de l’inventaire ou ajoutez-le par son lien.')
            include=data.get('include_subpages',True)
            if not isinstance(include,bool):raise ValueError('Option sous-pages invalide.')
            with budget(client,90):selection=client.selection(kind,oid,include)
            ticket=str(uuid.uuid4());session['selections'][ticket]=selection
            while len(session['selections'])>4:session['selections'].pop(next(iter(session['selections'])))
            return {'ticket':ticket,'pages':sorted([summary(x) for x in selection['pages'].values()],key=lambda x:(x['name'].casefold(),x['id'])),
                    'warnings':selection['warnings'],'import_available':not state['demo']}
        if method=='POST' and path=='/api/notion/preview':
            selection=session['selections'].get(data.get('ticket'))
            if selection is None:raise ValueError('Sélection expirée ou connexion changée : rechargez les éléments.')
            ids=data.get('ids')
            if not isinstance(ids,list) or not all(isinstance(x,str) for x in ids):raise ValueError('Liste de pages invalide.')
            with budget(client,90):return client.analyse(selection,ids)
        if method=='GET' and path=='/api/notion/targets':
            if state['demo']:return {'spaces':[{'id':'notion-test','name':'Test import Notion'}]}
            return {'spaces':Anytwo(settings['anytwo_port']).spaces()}
        raise APIError('Ressource Notion introuvable.',404)
