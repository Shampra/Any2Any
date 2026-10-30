import unittest
from unittest.mock import patch,Mock
from api_clients import APIError
from chat_archives import histories,markdown
from rich_content import ImportedFile
from migration import Engine


class ChatArchiveTests(unittest.TestCase):
    def test_cursor_pagination_restores_oldest_first_and_checks_count(self):
        source=Mock(port=1,key='k')
        source.request.side_effect=[{'messages':[{'id':'b'},{'id':'c'}],'has_more':True,'next_before':'x +/','message_count':3},
            {'messages':[{'id':'a'}],'has_more':False}]
        with patch('chat_archives.paginated',return_value=[{'id':'chat','name':'Chat'}]):out=histories(source,'space')
        self.assertEqual([m['id'] for m in out[0]['messages']],['a','b','c'])
        self.assertIn('before=x%20%2B%2F',source.request.call_args.args[0])
        self.assertNotIn('offset',source.request.call_args.args[0])

    def test_incomplete_history_is_refused_before_import(self):
        for page in ({'messages':[],'has_more':True},
                     {'messages':[{'id':'a'}],'has_more':False,'message_count':2}):
            with self.subTest(page=page),patch('chat_archives.paginated',return_value=[{'id':'chat'}]):
                with self.assertRaises(APIError):histories(Mock(port=1,key='k',request=Mock(return_value=page)),'space')

    def test_message_layout_dates_edits_replies_reactions_and_embedded_image(self):
        h={'name':'Example','messages':[
            {'id':'a','author':'Alice','author_id':'alice','at':'2026-01-02T12:00:00Z','text':'Hello\nSecond line'},
            {'id':'b','author':'Bob','at':'2026-01-02T13:00:00Z','edited_at':'2026-01-02T14:00:00Z',
             'text':'**Reply**','reply_to':'a','reactions':{'👍':2},'attachments':[{'id':'f','type':'image'}]}]}
        load=Mock(return_value=ImportedFile('any://f/s/f','image.png'))
        out=markdown(h,True,load,set())
        self.assertIn('> **Alice** · 02/01/2026 12:00:00 +0000',out)
        self.assertIn('> Second line',out);self.assertIn('modifié le',out)
        self.assertIn('En réponse à Alice',out);self.assertIn('👍 2',out)
        self.assertIn('> ![image.png](any://f/s/f)',out);self.assertEqual(out.count('\n\n---'),2)

    def test_files_disabled_and_unavailable_are_reported_without_loss_of_text(self):
        h={'name':'Chat','messages':[{'id':'a','text':'Kept','attachments':[{'id':'f','type':'file'}]}]}
        load=Mock(side_effect=APIError('offline'));issues=set()
        out=markdown(h,False,load,issues);load.assert_not_called();self.assertIn('Kept',out);self.assertTrue(issues)
        out=markdown(h,True,load,issues);self.assertIn('Pièce jointe indisponible',out)

    def test_object_attachment_is_not_downloaded_as_file(self):
        h={'name':'Chat','messages':[{'id':'a','attachments':[{'id':'page','type':'link'}]}]}
        load=Mock();out=markdown(h,False,load,set(),object_link=lambda oid:'[Page](any://o/s/'+oid+')')
        load.assert_not_called();self.assertIn('[Page](any://o/s/page)',out)

    def engine(self,enabled):
        inv={'all':[],'objects':[],'collections':[],'members':{},'types':[]}
        plan={'source_space':{'id':'src'},'selection':{'kind':'space'},
              'target':{'space_mode':'create','space_name':'Dest'},'archive_chats':enabled}
        return Engine(Mock(),Mock(),inv,plan)

    def test_option_off_does_not_read_chat_api(self):
        with patch('migration.chat_histories') as read,patch('migration.anytype_property_definitions',return_value={}),patch('migration.create_space',return_value='dest'):
            events=list(self.engine(False).run())
        read.assert_not_called();self.assertEqual(events[-1]['totals']['total'],0)

    def test_option_on_creates_archive_page_and_retains_author_metadata(self):
        history={'id':'chat','name':'Chat','warnings':[],'messages':[{'id':'m','author_id':'alice','author':'Alice','text':'Hi'}]}
        with patch('migration.chat_histories',return_value=[history]),patch('migration.anytype_property_definitions',return_value={}),patch('migration.create_space',return_value='dest'),patch('migration.create_object',return_value='page') as create,patch('migration.set_markdown') as body:
            events=list(self.engine(True).run())
        create.assert_called_once();self.assertEqual(create.call_args.args[3],[])
        self.assertIn('Alice',body.call_args.args[3]);self.assertEqual(events[-1]['totals']['imported'],1)
        self.assertEqual(events[-1]['chat_archives'][0]['messages'][0]['author_id'],'alice')
        self.assertEqual(sum(e['event']=='object' for e in events),1)

    def test_failed_read_performs_no_target_write(self):
        with patch('migration.chat_histories',side_effect=APIError('incomplete')),patch('migration.anytype_property_definitions',return_value={}),patch('migration.create_space') as create:
            with self.assertRaises(APIError):list(self.engine(True).run())
        create.assert_not_called()

if __name__=='__main__':unittest.main()
