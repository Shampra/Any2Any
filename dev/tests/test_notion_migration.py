from copy import deepcopy
import json
import threading
import time
import unittest
from unittest.mock import Mock, patch
from anytwo_backend import APIError
from notion_demo import DemoNotion,ROOT,DB,SOURCE,PAGE,CHILD,SCHEMA,rich
from notion_migration import Engine
from notion_content import Content
from notion_views import normalise
from view_conversion import UnsupportedView
from notion_import_jobs import start
from notion_routes import budget
from notion_source import Notion


class Library:
    def __init__(self,*args):self.files={}
    def find(self,name,content):return self.files.get((name,content))
    def register(self,name,content,fid):self.files[(name,content)]=fid


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.source=DemoNotion();self.calls=[];self.counter=0
        def writer(path,body=None,*args,**kwargs):
            self.counter+=1;self.calls.append((path,deepcopy(body)));return 'target-'+str(self.counter)
        self.writer=writer;self.patches=[]
        for name in ('create_space','create_collection','add_column','create_object','set_column_value','set_markdown','attach_file'):
            patcher=patch('notion_migration.backend.'+name,side_effect=lambda *args,_name=name,**kw:writer(_name,args[1:],**kw));patcher.start();self.patches.append(patcher)
        for path,value in [('notion_migration.FileLibrary',Library),('view_conversion.local_get',Mock(return_value={'records':[]})),
                           ('view_conversion.target_write',Mock(side_effect=lambda *args,**kw: {'objectId':writer('view',args[1:])})),
                           ('notion_migration.backend.target_write',Mock(side_effect=lambda *args,**kw:{'objectId':writer('native',args[1:])}))]:
            patcher=patch(path,value);patcher.start();self.patches.append(patcher)
        self.addCleanup(lambda:[p.stop() for p in reversed(self.patches)])
        self.target=Mock();self.target.spaces.return_value=[{'id':'space','name':'Test'}]
        self.options={'files':False,'links':False,'destination':{'id':'space'}}
    def engine(self,selection=None):return Engine(self.source,self.target,selection or self.source.selection('page',ROOT,True),self.options)
    def test_end_to_end_preserves_membership_colors_formula_and_internal_links(self):
        e=self.engine();report=e.run()
        self.assertEqual(len(e.mapping),3);self.assertEqual(len(e.collections),1)
        objects=[body for path,body in self.calls if path=='create_object']
        member=next(body for body in objects if body[1]=='Première tâche')
        self.assertEqual(member[2],[e.collections[SOURCE]])
        self.assertEqual(next(body for body in objects if body[1]=='Carnet de démonstration')[2],[])
        columns=[body for path,body in self.calls if path=='add_column']
        state=next(body for body in columns if body[2]=='État')
        self.assertEqual(next(iter(state[5]['options'].values()))['color'],'blue')
        self.assertEqual(next(body for body in columns if body[2]=='Calcul')[4],'number')
        self.assertTrue(any('any://o/space/'+e.mapping[CHILD] in str(body) for path,body in self.calls if path=='set_markdown'))
        self.assertTrue(any('inline-view' in str(body) for path,body in self.calls if path=='set_markdown'))
        self.assertEqual(report['totals']['total'],3)
        self.assertTrue(any('anyUi' in str(body) and 'visible' in str(body) for path,body in self.calls if path=='view'))
    def test_empty_database_still_creates_schema(self):
        e=self.engine({'pages':{},'schemas':{SOURCE:deepcopy(SCHEMA)},'warnings':[]});report=e.run()
        self.assertEqual(len(e.collections),1);self.assertEqual(report['totals']['total'],0)
        self.assertFalse(any(path=='create_object' for path,_ in self.calls))
    def test_resume_reuses_checkpoint_identities_instead_of_creating_duplicates(self):
        first=self.engine();report=first.run();self.calls.clear()
        def columns(target,sid,cid):
            scope=next(s for s,c in first.collections.items() if c==cid)
            return [{'id':pid,'kind':kind,'xFormat':form} for (s,p),(pid,kind,form) in first.props.items() if s==scope]
        with patch('notion_migration.backend.list_columns',side_effect=columns):
            resumed=Engine(self.source,self.target,self.source.selection('page',ROOT,True),self.options,resume=report)
            resumed.run()
        self.assertEqual(resumed.mapping,first.mapping)
        self.assertFalse(any(path in ('create_space','create_collection','add_column','create_object') for path,_ in self.calls))
        self.assertTrue(any(path=='set_markdown' for path,_ in self.calls))
    def test_native_rollup_binds_destination_relation_and_target_property(self):
        from notion_demo import rich
        schemas={'projects':{'title':rich('Projets'),'properties':{'Budget':{'name':'Budget','id':'budget','type':'number'}}},
                 'tasks':{'title':rich('Tâches'),'properties':{
                     'Projet':{'name':'Projet','id':'project','type':'relation','relation':{'data_source_id':'projects'}},
                     'Total':{'name':'Total','id':'total','type':'rollup','rollup':{'relation_property_id':'project','rollup_property_id':'budget','function':'sum'}}}}}
        e=self.engine({'pages':{},'schemas':schemas,'warnings':[]});e.sid='space';e.create_schema()
        binding=e.props[('tasks','total')];config=json.loads(binding[2]['anyui']['rollup'])
        self.assertEqual(binding[1],'object');self.assertEqual(config['calculate'],'sum')
        self.assertEqual(config['relation']['propertyId'],e.props[('tasks','project')][0]);self.assertEqual(config['target']['propertyId'],e.props[('projects','budget')][0])
        relation=e.props[('tasks','project')][2]
        self.assertEqual(relation['relation']['targetTypes'],[e.collection_handles['projects']])
        self.assertNotEqual(relation['relation']['targetTypes'],[e.collections['projects']])
    def test_relation_and_title_rollup_work_when_target_collection_is_created_last(self):
        schemas={'tasks':{'title':rich('Tâches'),'properties':{
            'Projet':{'name':'Projet','id':'project','type':'relation','relation':{'data_source_id':'projects'}},
            'Noms':{'name':'Noms','id':'names','type':'rollup','rollup':{'relation_property_id':'project','rollup_property_id':'title','function':'show_original'}}}},
            'projects':{'title':rich('Projets'),'properties':{'Nom':{'name':'Nom','id':'title','type':'title'}}}}
        e=self.engine({'pages':{},'schemas':schemas,'warnings':[]});e.sid='space';e.create_schema()
        config=json.loads(e.props[('tasks','names')][2]['anyui']['rollup'])
        self.assertEqual(config['target'],{'ownerId':e.collections['projects'],'propertyId':'any.name'})
        self.assertEqual(e.props[('tasks','project')][2]['relation']['targetTypes'],[e.collection_handles['projects']])
        kinds=[path for path,_ in self.calls]
        self.assertLess(max(i for i,k in enumerate(kinds) if k=='create_collection'),kinds.index('add_column'))
    def test_number_currency_percent_and_separator_formats_preserve_values(self):
        e=self.engine();e.results={PAGE:{'issues':set()}}
        for source,slug,config in [('euro','currency',{'currency':'EUR'}),('dollar','currency',{'currency':'USD'}),('percent','percent',{}),('number_with_commas','number',{'separators':True})]:
            spec={'id':'number','type':'number','number':{'format':source}}
            kind,form=e.shape(SOURCE,'Nombre',spec)
            self.assertEqual(kind,'number');self.assertEqual(form['type'],slug);self.assertEqual(form.get('config',{}),config)
            self.assertEqual(e.value(PAGE,SOURCE,'Nombre',{'type':'number','number':0.125},form),0.125)
        self.assertEqual(e.issues(PAGE),set())
    def test_unknown_relation_target_never_becomes_an_unrestricted_or_self_relation(self):
        e=self.engine({'pages':{},'schemas':{'tasks':{'properties':{}}},'warnings':[]})
        prop={'id':'r','type':'relation','relation':{'data_source_id':'outside'}}
        self.assertIsNone(e.resolve_schema(prop['relation']))
        kind,form=e.shape('tasks','Lien',prop);self.assertEqual((kind,form['type']),('string','longtext'))
    def test_relation_target_schema_is_read_without_importing_its_pages(self):
        target='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';e=self.engine()
        e.schemas[SOURCE]['properties']['Parent']={'id':'parent','name':'Parent','type':'relation','relation':{'data_source_id':target}}
        original=self.source.data_source
        self.source.data_source=Mock(side_effect=lambda sid:{'id':target,'title':rich('Cible'),'properties':{}} if sid==target else original(sid))
        e.collect()
        self.assertIn(target,e.schemas);self.assertEqual(set(e.pages),{ROOT,CHILD,PAGE})
        self.source.data_source.assert_any_call(target)
    def test_source_property_identity_is_decoded_and_preferred_to_stale_name(self):
        from notion_migration import source_property
        schema={'properties':{'Ancien nom':{'id':'other'},'Budget renommé':{'id':'Vs%60T'}}}
        self.assertEqual(source_property(schema,'Vs`T','Ancien nom')['id'],'Vs%60T')
    def test_currency_property_keeps_numeric_view_comparisons(self):
        from notion_views import converter
        e=self.engine({'pages':{},'schemas':{'source':{'properties':{'Prix':{'id':'price','type':'number'}}}},'warnings':[]})
        e.collections={'source':'collection'};e.props={('source','price'):('price-id','number',{'type':'currency','config':{'currency':'EUR'}})}
        cv=converter(e,'source');query=cv.predicate({'property':'Prix','condition':'greater','value':10})
        self.assertIn("'collection.price-id': {'$gt': 10}",str(query))
    def test_no_parent_navigation_link_is_added_to_imported_child_page(self):
        e=self.engine();e.run()
        child=next(body for path,body in self.calls if path=='set_markdown' and body[1]==e.mapping[CHILD])
        self.assertNotIn('[↑',child[2]);self.assertNotIn(e.mapping[ROOT],child[2])
    def test_deleted_destination_prevents_all_writes(self):
        self.target.spaces.return_value=[]
        with self.assertRaises(APIError):self.engine().run()
        self.assertEqual(self.calls,[])
    def test_relation_remaps_and_reports_outside_scope(self):
        e=self.engine();e.results={PAGE:{'issues':set()}};e.mapping={CHILD:'child-target'}
        result=e.value(PAGE,SOURCE,'Lien',{'type':'relation','relation':[{'id':CHILD},{'id':'outside'}]}, {})
        self.assertEqual(result,['any://child-target']);self.assertTrue(e.issues(PAGE))
    def test_follow_links_imports_outside_page_and_honours_explicit_exclusions(self):
        class Linked(DemoNotion):
            def _send(self,path,method,body):
                if path.split('?',1)[0]=='/blocks/'+CHILD+'/children':
                    return {'object':'list','results':[{'id':'link','type':'link_to_page','link_to_page':{'type':'page_id','page_id':PAGE}}],'has_more':False}
                return super()._send(path,method,body)
        self.source=Linked();selection=self.source.selection('page',CHILD,True)
        self.options['links']=True;e=self.engine(selection);e.run()
        self.assertEqual(set(e.mapping),{CHILD,PAGE});self.assertIn(SOURCE,e.collections)
        selection['excluded']=[PAGE];blocked=self.engine(selection);blocked.run()
        self.assertEqual(set(blocked.mapping),{CHILD})
    def test_null_view_sort_and_column_lists_are_valid(self):
        view=normalise({'type':'table','sorts':None,'configuration':{'properties':None}},SCHEMA)
        self.assertEqual(view['sorts'],[]);self.assertEqual(view['columns'],[])
    def test_preview_with_linked_pages_expands_scope_without_destination_writes(self):
        import notion_jobs,notion_tree
        from notion_routes import budget
        original=self.source._send
        def send(path,method,body):
            if path.split('?',1)[0]=='/blocks/'+CHILD+'/children':
                return {'object':'list','results':[{'id':'link','type':'link_to_page','link_to_page':{'type':'page_id','page_id':PAGE}}],'has_more':False}
            return original(path,method,body)
        self.source._send=send;catalog=self.source.catalog()
        session={'client':self.source,'catalog':catalog,'nodes':notion_tree.nodes(catalog)}
        job=notion_jobs.start(session,{'whole':False,'rules':[{'key':'page:'+CHILD,'include':True}],'links':True,'files':False},threading.RLock(),budget)
        deadline=time.monotonic()+3
        while session['jobs'][job['id']]['state']=='running' and time.monotonic()<deadline:time.sleep(.01)
        result=session['jobs'][job['id']]
        self.assertEqual(result['state'],'done');self.assertEqual(result['result']['selected_pages'],2)
        self.assertEqual(result['result']['import_options'],{'files':False,'links':True});self.assertEqual(self.calls,[])
    def test_files_disabled_does_not_download(self):
        e=self.engine();e.results={PAGE:{'issues':set()}}
        with patch('notion_migration.download') as downloader:
            self.assertIsNone(e.media(PAGE,{'type':'external','external':{'url':'https://example.com/f.png'}},'image'))
            downloader.assert_not_called()
    def test_reused_file_references_share_one_upload_and_keep_filename(self):
        e=self.engine();e.options['files']=True;e.sid='space';e.mapping={PAGE:'target'};e.results={PAGE:{'issues':set(),'status':'created'}};e.library=Library()
        with patch('notion_migration.download',return_value=(b'image','image/png','photo.png')):
            first=e.media(PAGE,{'type':'external','external':{'url':'https://example.com/a'}},'image')
            second=e.media(PAGE,{'type':'external','external':{'url':'https://example.com/b'}},'image')
        self.assertEqual(first,second);self.assertEqual(first.name,'photo.png')
        self.assertEqual(sum(path=='attach_file' for path,_ in self.calls),1)
    def test_unsupported_active_view_is_not_replaced_by_unfiltered_inline(self):
        e=self.engine();e.sid='space';e.collections={SOURCE:'collection'};e.mapping={ROOT:'target'};e.results={ROOT:{'issues':set()}}
        e.databases={DB:self.source.database(DB)};e.views={DB:[{'type':'chart','data_source_id':SOURCE}]}
        result=e.inline_database(ROOT,DB)
        self.assertNotIn('inline-view',result);self.assertIn('collection',result)
        self.assertTrue(any('non convertie' in x for x in e.issues(ROOT)))
    def test_blocks_keep_toggle_blank_lines_and_safe_text(self):
        e=self.engine();e.results={ROOT:{'issues':set()}};e.sid='space';e.blocks={'toggle':[{'id':'inside','type':'paragraph','paragraph':{'rich_text':rich('Dedans')}}]}
        content=Content(e,ROOT)
        blocks=[{'id':'a','type':'paragraph','paragraph':{'rich_text':rich('Avant')}},{'id':'empty','type':'paragraph','paragraph':{'rich_text':[]}},
                {'id':'toggle','type':'toggle','has_children':True,'toggle':{'rich_text':rich('Ouvrir')}},
                {'id':'html','type':'paragraph','paragraph':{'rich_text':rich('<iframe>')}}]
        result=content.render(blocks)
        self.assertIn('Avant\n\n\n<!-- any:collapsible',result);self.assertIn('Dedans',result);self.assertNotIn('<iframe>',result)
    def test_view_filter_unknown_operator_fails_closed(self):
        with self.assertRaises(UnsupportedView):normalise({'type':'table','filter':{'property':'État','status':{'is_empty':True}}},SCHEMA)
    def test_cancelled_before_write_does_not_create_space(self):
        e=self.engine();e.check=Mock(side_effect=APIError('Arrêt',499))
        with self.assertRaises(APIError):e.run()
        self.assertEqual(self.calls,[])


class ImportLifecycleTests(unittest.TestCase):
    def test_local_file_hosts_are_rejected_before_download(self):
        from notion_files import validate_url
        with patch('notion_files.socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaises(APIError):validate_url('https://example.com/file')
        for url in ('http://example.com/file','https://user:pass@example.com/file','https://example.com:8443/file'):
            with self.assertRaises(APIError):validate_url(url)
    def test_launch_is_idempotent_and_shares_destination_lock(self):
        import uuid
        source=DemoNotion();import notion_tree
        session={'client':source,'catalog':source.catalog(),'nodes':notion_tree.nodes(source.catalog())}
        lock=threading.Lock();gate=threading.Event();api=threading.RLock()
        data={'request_id':str(uuid.uuid4()),'whole':True,'rules':[],'files':False,'links':False,'destination':{'id':'space'}}
        with patch('notion_import_jobs.Engine') as constructor:
            constructor.return_value.run.side_effect=lambda:gate.wait(2) or {}
            first=start(session,data,api,lock,budget,31310,Mock())
            second=start(session,data,api,lock,budget,31310,Mock());self.assertEqual(first['id'],second['id'])
            self.assertFalse(lock.acquire(blocking=False));gate.set()
            deadline=time.monotonic()+3
            while session['jobs'][first['id']]['state']=='running' and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(constructor.call_count,1);self.assertTrue(lock.acquire(blocking=False));lock.release()
    def test_full_paginated_relation_property_is_read(self):
        client=Notion('fake');client.request=Mock(side_effect=[{'object':'list','results':[{'relation':{'id':'a'}}],'has_more':True,'next_cursor':'next'},
             {'object':'list','results':[{'relation':{'id':'b'}}],'has_more':False}])
        prop=client.complete_property(PAGE,{'id':'a%3Ab','type':'relation','relation':[]})
        self.assertEqual(prop['relation'],[{'id':'a'},{'id':'b'}]);self.assertIn('/a%3Ab?',client.request.call_args_list[0].args[0])


if __name__=='__main__':unittest.main()
