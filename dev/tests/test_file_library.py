import unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_regressions_v08 as fixture
from api_clients import APIError
from file_transfer import FileLibrary,strip_import_prefix
from migration import file_metadata,render_blocks
from rich_content import ImportedFile


class FileLibraryTests(unittest.TestCase):
    def test_clipboard_prefix_removed_but_hash_only_names_preserved(self):
        prefix='157180d2dfacc50c496acab88dbda478'
        doc={'properties':{'name':prefix+'Croquis 20_03_2023 14_55','file_ext':'png','origin':'clipboard'}}
        self.assertEqual(file_metadata(doc)[0],'Croquis 20_03_2023 14_55.png')
        self.assertEqual(strip_import_prefix(prefix+'.png'),prefix+'.png')
        self.assertEqual(strip_import_prefix('a'*64+'.png'),'a'*64+'.png')
        self.assertEqual(file_metadata({'properties':{'name':prefix+'Croquis','file_ext':'png'}})[0],prefix+'Croquis.png')

    def test_source_extension_survives_dots_in_display_name(self):
        self.assertEqual(file_metadata({'properties':{'name':'20.03.2023, 14.50.13','file_ext':'webm'}})[0],'20.03.2023, 14.50.13.webm')

    def test_existing_legacy_name_is_reused_only_after_hash_verification(self):
        library=FileLibrary(SimpleNamespace(port=123),'space')
        with patch('file_transfer.local_get',return_value={'files':[{'fileId':'old','name':'8894b9f4c88976616b128bd86473c2a1go_paperless__fr.png','size':3}]}), patch('file_transfer.local_binary',return_value=(b'png','image/png')) as get:
            self.assertEqual(library.find('go_paperless__fr.png',b'png'),'old')
            self.assertEqual(library.find('go_paperless__fr.png',b'png'),'old')
        get.assert_called_once()

    def test_same_name_and_size_with_different_bytes_is_not_reused(self):
        library=FileLibrary(SimpleNamespace(port=123),'space')
        with patch('file_transfer.local_get',return_value={'files':[{'fileId':'old','name':'image.png','size':3}]}), patch('file_transfer.local_binary',return_value=(b'OLD','image/png')):
            self.assertIsNone(library.find('image.png',b'NEW'))

    def test_unavailable_library_file_does_not_produce_a_broken_reuse(self):
        library=FileLibrary(SimpleNamespace(port=123),'space')
        with patch('file_transfer.local_get',return_value={'files':[{'fileId':'old','name':'image.png','size':3}]}), patch('file_transfer.local_binary',side_effect=APIError('not available',409)):
            self.assertIsNone(library.find('image.png',b'png'))

    def test_thumbnails_are_never_reused_as_originals(self):
        library=FileLibrary(SimpleNamespace(port=123),'space')
        with patch('file_transfer.local_get',return_value={'files':[{'fileId':'thumb','name':'image.png','size':3,'variant':'thumb'}]}), patch('file_transfer.local_binary') as content:
            self.assertIsNone(library.find('image.png',b'png'))
        content.assert_not_called()

    def test_same_source_file_shared_by_two_pages_is_uploaded_once(self):
        engine=fixture.RegressionV08().engine()
        engine.mapping['second']='second-target';engine.results['second']={'issues':set()}
        with patch('migration.anytype_download',return_value=(b'png','image/png')) as download, patch('migration.attach_file',return_value='new') as upload:
            first=engine.add_file('page-id','fid','image.png',None)
            second=engine.add_file('second','fid','image.png',None)
        self.assertEqual(first,second)
        download.assert_called_once();upload.assert_called_once()

    def test_different_source_ids_with_identical_named_payload_share_upload(self):
        engine=fixture.RegressionV08().engine()
        with patch('migration.anytype_download',return_value=(b'png','image/png')), patch('migration.attach_file',return_value='new') as upload:
            first=engine.add_file('page-id','fid1','image.png',None)
            second=engine.add_file('page-id','fid2','image.png',None)
        self.assertEqual(first,second);upload.assert_called_once()

    def test_cache_never_reuses_a_reference_from_another_destination_space(self):
        engine=fixture.RegressionV08().engine()
        with patch('migration.anytype_download',return_value=(b'png','image/png')), patch('migration.attach_file',side_effect=['first','second']) as upload:
            first=engine.add_file('page-id','fid','image.png',None)
            engine.dest_sid='another-space'
            second=engine.add_file('page-id','fid','image.png',None)
        self.assertNotEqual(first,second);self.assertEqual(upload.call_count,2)

    def test_images_use_native_markdown_even_with_source_width(self):
        issues=set()
        out=render_blocks({'blocks':[{'type':'image','object_id':'fid','style':'embed','fields':{'width':240}}]},
            {},'dest',{},True,lambda *_:ImportedFile('any://f/dest/existing','Croquis 20_03_2023 [test].png'),issues)
        self.assertEqual(out,'![Croquis 20_03_2023 \\[test\\].png](any://f/dest/existing)<!-- any:image-width=240 -->')
        self.assertNotIn('<img',out);self.assertNotIn('&#91;',out)

    def test_image_explicitly_shown_as_link_remains_a_file_link(self):
        out=render_blocks({'blocks':[{'type':'image','object_id':'fid','style':'link'}]},
            {},'dest',{},True,lambda *_:ImportedFile('any://f/dest/existing','image.png'),set())
        self.assertEqual(out,'[image.png](any://f/dest/existing)')
