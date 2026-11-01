import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from runtime_profile import get_profile,seed_unified_settings
from notion_views import normalise,converter
from notion_migration import Engine
from notion_demo import SCHEMA,SOURCE,DemoNotion
from view_conversion import create_saved_views
from inline_views import inline_records
from tools.build_release import build,ROOT

class UnifiedAppTests(unittest.TestCase):
    def test_unified_profile_is_separate_and_reuses_only_protected_development_settings(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'APPDATA':folder}):
            profile=get_profile('unified');self.assertEqual(profile.config_dir,Path(folder)/'any2any');self.assertEqual(profile.port,8766)
            prefix='dpapi:' if os.name=='nt' else 'plain:'
            originals={}
            for name,data in [('notion-dev',{'notion_token':prefix+'saved-notion','source_kind':'notion','anytwo_port':31310}),('anytype-dev',{'anytype_key':prefix+'saved-anytype','anytype_port':31009})]:
                path=get_profile(name).config_dir/'settings.json';path.parent.mkdir(parents=True);path.write_text(json.dumps(data),encoding='utf-8');originals[path]=path.read_bytes()
            seed_unified_settings(profile);target=profile.config_dir/'settings.json';saved=json.loads(target.read_text(encoding='utf-8'))
            self.assertEqual(saved['notion_token'],prefix+'saved-notion');self.assertEqual(saved['anytype_key'],prefix+'saved-anytype')
            for path,before in originals.items():self.assertEqual(path.read_bytes(),before)
            target.write_text('{"existing":true}',encoding='utf-8');seed_unified_settings(profile);self.assertEqual(json.loads(target.read_text()),{'existing':True})

    def test_distribution_is_reproducible_and_excludes_private_or_development_files(self):
        with tempfile.TemporaryDirectory() as folder:
            first,_,a=build(output=Path(folder)/'first.zip');second,_,b=build(output=Path(folder)/'second.zip');self.assertEqual(a,b)
            with zipfile.ZipFile(first) as archive:
                names=archive.namelist();self.assertIn('demarrer.bat',names);self.assertIn('app/notion_migration.py',names)
                self.assertFalse(any(any(part in name for part in ('reports/','settings.json','.git/','tests/','tools/','__pycache__','.env')) for name in names))
                manifest=json.loads(archive.read('docs/BUILD.json'));self.assertIn('app/server.py',manifest['sha256'])
                self.assertIn(b'--profile unified',archive.read('demarrer.bat'))

    def test_gallery_fit_and_side_peek_reach_collection_and_inline_view_records(self):
        from unittest.mock import Mock
        e=Engine(DemoNotion(),Mock(),{'pages':{},'schemas':{SOURCE:SCHEMA}}, {'files':False,'links':False,'destination':{'id':'space'}})
        e.collections={SOURCE:'collection'};e.props={};e.sid='space'
        for config,mode,fit in [({'cover_aspect':'contain'},'side-peek',True),({'cover_aspect':'cover','open_pages_in':'full_page'},'full-screen',False),({'cover_aspect':'contain','open_pages_in':'center_peek'},'side-peek',True)]:
            view=normalise({'type':'gallery','configuration':config},SCHEMA)
            with patch('view_conversion.modify_records') as write:
                create_saved_views(e.target,e.sid,'collection',{'is_collection':True,'views':[view]}, {'type':'collection','collection_items':[]},[],converter(e,SOURCE),set(),root_id='host',table_key='default')
            record=write.call_args_list[-1].args[-1][0]
            rows,_=inline_records(converter(e,SOURCE),{'views':[view]},'collection','instance',set())
            for settings in (record['layoutSettings'],rows[0]['layoutSettings']):
                self.assertEqual(settings['openMode'],mode);self.assertEqual(settings['galleryFitImage'],fit)

if __name__=='__main__':unittest.main()
