"""Full-pipeline regressions for collection references and faithful property storage."""
from contextlib import ExitStack
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from api_clients import APIError
from migration import Engine, date_has_time, replace_inline_links
from rich_content import ImportedFile


class Source:
    def templates(self, sid):
        return []

    def type_detail(self, sid, key):
        return {'properties':{'name':'Readable page type'}, 'type_settings':{'property_definitions':[
            {'property':'Due','name':'Due','format':'date','include_time':False},
            {'property':'Files','name':'Files','format':'files'},
            {'property':'State','name':'State','format':'select'}]}}

    def object_detail(self, sid, oid):
        columns=[{'property':'name'}, {'property':'type'}, {'property':'Due'}, {'property':'Files'}]
        if oid in ('c','archived'):
            count=9 if oid=='archived' else 1
            return {'type':'collection','properties':{'name':oid},'collection_items':['a'],
                'blocks':[{'type':'dataview','is_collection':True,'properties':[
                    {'property':'Files','format':'files'}], 'views':[
                    {'name':('Archived view '+str(i)) if oid=='archived' else 'All',
                     'type':['table','list','gallery'][i%3], 'columns':columns,
                     'group_by':'State','sorts':[{'property':'Due','direction':'desc'}],
                     'filters':[{'property':'State','condition':'not_in','value':['Hidden']}]}
                    for i in range(count)]}]}
        return {'type':'fixture_page','properties':{'name':'Page','Due':'2026-11-21T14:30:00Z',
                'Files':['image-id'],'State':['Ready']}, 'blocks':[
            {'type':'paragraph','text':'INTRO'}, {'type':'link','object_id':'c'},
            {'type':'paragraph','text':'<mention object_id="a">Inline label</mention>'},
            {'type':'dataview','object_id':'c','views':[{'name':'Inline',
                'columns':[{'property':'name'},{'property':'Due'}]}]},
            {'type':'dataview','object_id':'archived'}]}


class CollectionRegressionTests(unittest.TestCase):
    def run_import(self):
        page={'id':'a','name':'Page','type':'fixture_page'}
        collection={'id':'c','name':'Collection','type':'collection'}
        inventory={'all':[page,collection],'objects':[page],'collections':[collection],
            'members':{'c':[page]}, 'types':[{'id':'fixture_page','key':'fixture_page',
                'name':'Readable pages','items':[page]}]}
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'space'},
            'target':{'space_mode':'create','space_name':'Destination'},'mode':'simple',
            'files':True,'follow_links':False}
        columns={}; values={}; bodies={}; saved=[]; created=[]
        def collection_create(api,sid,name,key):
            cid='collection-'+str(len(columns))
            columns[cid]=[]
            return cid
        def object_create(api,sid,name,collections,**kwargs):
            created.append(name)
            return 'page-'+str(len(created))
        def column_create(api,sid,cid,name,key,kind,form):
            pid='prop-'+name
            columns[cid].append({'id':pid,'name':name,'kind':kind,'xFormat':deepcopy(form)})
            return pid
        def set_value(api,sid,oid,cid,pid,value):
            descriptor=next(col for col in columns[cid] if col['id']==pid)['xFormat']
            if descriptor.get('type')=='date' and date_has_time(value):
                raise APIError('date must be midnight UTC')
            values[(oid,cid,pid)]=value
        def write(api,path,body,**kwargs):
            return {'objectId':'view-root-'+str(len(saved)), 'rejections':[]}
        def modify(api,sid,host,dataset,records):
            saved.extend({'host':host,'dataset':dataset,**deepcopy(row)} for row in records)
            return {'rejections':[]}
        metadata={'due':{'name':'Due','format':'date','include_time':False},
            'files':{'name':'Files','format':'files'},
            'state':{'name':'State','format':'select','options':[{'name':'Ready'},{'name':'Hidden'}]}}
        mocks={'migration.create_space':lambda *args:'dest',
            'migration.create_collection':collection_create,'migration.create_object':object_create,
            'migration.list_columns':lambda api,sid,cid:columns[cid],
            'migration.add_column':column_create,'migration.set_column_value':set_value,
            'migration.set_markdown':lambda api,sid,oid,text:bodies.__setitem__(oid,text),
            'migration.anytype_property_definitions':lambda *args:metadata,
            'migration.target_write':write,'view_conversion.target_write':write,
            'migration.modify_records':modify,'view_conversion.modify_records':modify,
            'view_conversion.local_get':lambda *args,**kwargs:{'records':[]},
            'anytwo_backend.server_version':lambda *args:(0,4,1)}
        with ExitStack() as stack:
            for name,action in mocks.items():
                stack.enter_context(patch(name,side_effect=action))
            engine=Engine(Source(),SimpleNamespace(port=0),inventory,plan)
            stack.enter_context(patch.object(engine,'add_file',return_value=ImportedFile(
                'any://f/dest/file','photo.png','image/png')))
            report=list(engine.run())[-1]
        return engine,report,columns,values,bodies,saved,created

    def test_collection_links_target_the_collection_without_a_duplicate_page(self):
        engine,report,columns,values,bodies,saved,created=self.run_import()
        self.assertEqual(created,['Page'])
        self.assertEqual(engine.mapping['c'],engine.col_cache['collection:c'])
        self.assertIn('(any://o/dest/'+engine.mapping['c']+')',bodies[engine.mapping['a']])
        self.assertEqual(next(row for row in report['objects'] if row['source_id']=='c')['target_id'],engine.mapping['c'])

    def test_datetime_does_not_get_downgraded_or_abort_inline_views(self):
        engine,report,columns,values,bodies,saved,created=self.run_import()
        dates=[col for cols in columns.values() for col in cols if col['name']=='Due']
        self.assertTrue(dates)
        self.assertTrue(all(col['xFormat']['type']=='datetime' for col in dates))
        self.assertIn('"kind":"inline-view"',bodies[engine.mapping['a']])
        self.assertFalse(any('midnight' in str(row) for row in report['views']))

    def test_files_are_content_and_type_labels_are_readable(self):
        engine,report,columns,values,bodies,saved,created=self.run_import()
        self.assertFalse(any(col['name']=='Files' for cols in columns.values() for col in cols))
        text=bodies[engine.mapping['a']]
        self.assertLess(text.index('![photo.png]'),text.index('INTRO'))
        self.assertIn('[Inline label](any://o/dest/'+engine.mapping['a']+')',text)
        self.assertIn('Readable page type',values.values())
        self.assertNotIn('fixture_page',values.values())

    def test_referenced_archived_collection_gets_all_views_with_filters_and_order(self):
        engine,report,columns,values,bodies,saved,created=self.run_import()
        views=[row for row in saved if row.get('name','').startswith('Archived view ')]
        self.assertEqual(len(views),9)
        self.assertEqual([row['name'] for row in views],['Archived view '+str(i) for i in range(9)])
        self.assertTrue(all(row['query']['anyUi']['filters'] for row in views))
        self.assertTrue(all(row['query']['anyUi']['sort'][0]['dir']=='desc' for row in views))
        self.assertTrue(all(row['query']['anyUi']['group']['propertyId']=='prop-State' for row in views))
        main=next(row for row in saved if row.get('name')=='All')
        self.assertIn('prop-Due',main['layoutSettings']['visible'])

    def test_escaped_source_query_parameters_are_removed_from_the_new_internal_link(self):
        issues=set()
        source='[Label](anytype://object?objectId=source\\&spaceId=old-space)'
        self.assertEqual(replace_inline_links(source,{'source':'target'},'dest',{},issues),
                         '[Label](any://o/dest/target)')
        self.assertFalse(issues)


if __name__=='__main__':
    unittest.main()
