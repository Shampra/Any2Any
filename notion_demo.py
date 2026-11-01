"""Deterministic Notion fixtures for the local demo, without network access."""
from copy import deepcopy
from notion_source import Notion

ROOT='11111111-1111-1111-1111-111111111111'
DB='22222222-2222-2222-2222-222222222222'
SOURCE='33333333-3333-3333-3333-333333333333'
PAGE='44444444-4444-4444-4444-444444444444'
CHILD='55555555-5555-5555-5555-555555555555'
def rich(value):return [{'type':'text','text':{'content':value},'plain_text':value}]
def page(oid,name,parent):return {'object':'page','id':oid,'parent':parent,'properties':{'Nom':{'id':'title','type':'title','title':rich(name)}}}
ROOT_PAGE=page(ROOT,'Carnet de démonstration',{'type':'workspace','workspace':True})
ITEM=page(PAGE,'Première tâche',{'type':'data_source_id','data_source_id':SOURCE,'database_id':DB})
ITEM['properties']['État']={'id':'state','type':'status','status':{'name':'À faire','color':'blue'}}
ITEM['properties']['Calcul']={'id':'calc','type':'formula','formula':{'type':'number','number':42}}
CHILD_PAGE=page(CHILD,'Sous-page',{'type':'page_id','page_id':ROOT})
SCHEMA={'object':'data_source','id':SOURCE,'title':rich('Tâches'),'parent':{'type':'database_id','database_id':DB},'properties':{'Nom':{'id':'title','name':'Nom','type':'title','title':{}},'État':{'id':'state','name':'État','type':'status','status':{'options':[{'id':'todo','name':'À faire','color':'blue'}],'groups':[]}}}}
DATABASE={'object':'database','id':DB,'title':rich('Projet de démonstration'),'parent':{'type':'page_id','page_id':ROOT},'data_sources':[{'id':SOURCE,'name':'Tâches'}]}

def listed(items):return {'object':'list','results':deepcopy(items),'has_more':False,'next_cursor':None}

class DemoNotion(Notion):
    def __init__(self):super().__init__('demo-not-sent');self.interval=0
    def _send(self,path,method,body):
        clean=path.split('?',1)[0]
        if clean.startswith('/pages/') and '/properties/' in clean:
            from urllib.parse import unquote
            _,_,oid,_,pid=clean.split('/')
            page={ROOT:ROOT_PAGE,PAGE:ITEM,CHILD:CHILD_PAGE}[oid]
            prop=next(p for p in page['properties'].values() if p['id']==unquote(pid))
            if prop['type'] in ('title','rich_text','relation','people'):
                return listed([{'object':'property_item','type':prop['type'],prop['type']:x} for x in prop[prop['type']]])
            return {'object':'property_item',**deepcopy(prop)}
        if clean=='/users/me':return {'object':'user','id':'demo','name':'Any2Any Démo','bot':{'workspace_name':'Notion fictif'}}
        if clean=='/search':return listed([ROOT_PAGE,CHILD_PAGE,SCHEMA,ITEM])
        if clean=='/databases/'+DB:return deepcopy(DATABASE)
        if clean=='/data_sources/'+SOURCE:return deepcopy(SCHEMA)
        if clean=='/data_sources/'+SOURCE+'/query':return listed([ITEM])
        if clean.startswith('/pages/'):
            return deepcopy({ROOT:ROOT_PAGE,PAGE:ITEM,CHILD:CHILD_PAGE}[clean.split('/')[-1]])
        if clean=='/blocks/'+ROOT+'/children':return listed([{'id':CHILD,'type':'child_page','child_page':{'title':'Sous-page'},'has_children':False},{'id':DB,'type':'child_database','child_database':{'title':'Projet'},'has_children':False}])
        if clean.startswith('/blocks/'):return listed([{'id':'66666666-6666-6666-6666-666666666666','type':'paragraph','paragraph':{'rich_text':rich('Contenu de démonstration.')},'has_children':False}])
        if clean.startswith('/views/'):
            return self._send('/views',method,body)['results'][0]
        if clean=='/views':return listed([{'id':'77777777-7777-7777-7777-777777777777','type':'table','name':'À faire','data_source_id':SOURCE,'filter':{'property':'État','status':{'equals':'À faire'}},'sorts':[],'configuration':{'type':'table','properties':[{'property_id':'title','visible':True},{'property_id':'state','visible':False}]}}])
        raise AssertionError('Unexpected demo endpoint: '+path)
