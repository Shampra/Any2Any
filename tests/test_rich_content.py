import unittest
from unittest.mock import patch
from rich_content import ImportedFile, file_html, youtube_markdown
from migration import render_blocks, file_metadata
import test_regressions_v08 as files_fixture
import test_migration as migration_fixture


class RichContentTests(unittest.TestCase):
    def render(self,blocks,files=False,loader=None):
        issues=set()
        return render_blocks({'blocks':blocks},{},'s',{},files,loader,issues),issues

    def test_audio_is_native_file_link_with_original_filename(self):
        result,_=self.render([{'type':'audio','object_id':'bafy-id'}],True,
            lambda *_:ImportedFile('any://f/s/upload','enregistrement.mp3','audio/mpeg'))
        self.assertIn('[enregistrement.mp3](any://f/s/upload)',result)
        self.assertNotIn('bafy-id',result)
        self.assertNotIn('<audio',result)

    def test_filename_metadata_localized_with_internal_keys(self):
        self.assertEqual(file_metadata({'properties':{'Nom du fichier':'nextflix_titles',
            'Extension':'xlsx'},'property_internal_keys':{'Nom du fichier':'fileName',
            'Extension':'fileExt'}})[0],'nextflix_titles.xlsx')

    def test_upload_and_document_share_resolved_name(self):
        engine=files_fixture.RegressionV08().engine(files_fixture.FileSource({'fid':{'properties':{'fileName':'nextflix_titles.xlsx'}}}))
        with patch('migration.anytype_download',return_value=(b'xlsx','application/octet-stream')), patch('migration.attach_file',return_value='uploaded') as attach:
            uri=engine.add_file('page-id','fid','file bafyrei',None)
        self.assertEqual(attach.call_args.args[3],'nextflix_titles.xlsx')
        self.assertEqual(uri.name,'nextflix_titles.xlsx')
        self.assertIn('[nextflix_titles.xlsx]',file_html(uri,uri.name))

    def test_heading_toggle_groups_only_its_descendants(self):
        result,_=self.render([{'type':'toggle_heading_2','text':'Titre'},
            {'type':'paragraph','indent':1,'text':'Enfant'},
            {'type':'toggle','indent':1,'text':'Interne'},
            {'type':'paragraph','indent':2,'text':'Petit enfant'},
            {'type':'paragraph','text':'Après'}])
        self.assertIn('## Titre',result)
        self.assertEqual(result.count('<!-- any:collapsible '),2)
        self.assertEqual(result.count('Petit enfant'),1)
        self.assertGreater(result.index('Après'),result.rindex('<!-- /any:collapsible -->'))

    def test_table_checkboxes_keep_both_states_and_underline_dom_style(self):
        result,_=self.render([{'type':'table','rows':[{'cells':[
            {'type':'checkbox','checked':True,'text':'Oui'},
            {'type':'checkbox','checked':False,'text':'Non'},
            {'text':'<u>Souligné dans cellule</u>'}]}]}])
        self.assertIn('aria-checked="true"',result)
        self.assertIn('aria-checked="false"',result)
        self.assertIn('<u>Souligné dans cellule</u>',result)
        self.assertNotIn('☐',result)

    def test_unsupported_underline_keeps_text_and_reports_loss(self):
        result,issues=self.render([{'type':'paragraph','text':'<u>Texte **gras**</u> et `<u>code</u>`'}])
        self.assertIn('Texte **gras** et `<u>code</u>`',result)
        self.assertTrue(any('Soulignement' in issue for issue in issues))

    def test_youtube_lookalike_domain_is_rejected(self):
        self.assertIsNone(youtube_markdown('https://youtube.com.evil.example/watch?v=LMXMbeKyneQ'))
        self.assertIsNone(youtube_markdown('javascript:alert(1)'))
        self.assertIn('"provider":"youtube"',youtube_markdown('https://www.youtube-nocookie.com/embed/LMXMbeKyneQ'))


    def test_engine_transfers_emoji_and_image_icon_as_metadata(self):
        setup=migration_fixture.MigrationTests();setup.setUp()
        class Source:
            def object_detail(self,sid,oid):
                return {'icon':({'format':'emoji','emoji':'🌈'} if oid=='a' else
                    {'format':'image','file':'icon-source'}),'blocks':[]}
        with patch('migration.create_space',return_value='dest'), patch('migration.create_collection',return_value='col'), patch('migration.create_object',side_effect=['new-a','new-b']) as create, patch('migration.anytype_property_definitions',return_value={}), patch('migration.set_markdown'), patch('migration.set_column_value') as metadata, patch('migration.Engine.add_file',return_value=ImportedFile('any://f/dest/icon','icon.png')) as upload:
            setup.plan['selection']={'kind':'objects','ids':['a','b']}
            list(migration_fixture.Engine(Source(),object(),setup.inv,setup.plan).run())
        self.assertEqual(create.call_args_list[0].kwargs['emoji'],'🌈')
        upload.assert_called_once()
        self.assertTrue(any(call.args[-3:]==('any','icon','any://f/dest/icon') for call in metadata.call_args_list))
