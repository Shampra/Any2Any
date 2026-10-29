import unittest
from unittest.mock import patch

from api_clients import APIError, create_object
from logic import build_inventory, is_conversation
from migration import (custom_properties, declared_properties, internal_property, render_blocks,
                       bookmark_url, titled_link, youtube_embed)


class Inventory:
    def objects(self, sid):
        return [
            {'id':'a','name':'Page','type':'page'},
            {'id':'b','name':'Discussion du projet','type':'discussion'},
            {'id':'c','name':'Salon','type':'chat'},
            {'id':'col','name':'Recettes','type':'collection'},
            {'id':'d','name':'Réunion','type':'note'}]

    def types(self, sid):
        return [{'id':'page','key':'page','name':'Pages'},
                {'id':'chat','key':'chat','name':'Chats'},
                {'id':'discussion','key':'discussion','name':'Discussions'},
                {'id':'note','key':'note','name':'Notes'}]

    def members(self,sid,cid):
        return [self.objects(sid)[0],self.objects(sid)[1]]

    def type_detail(self,sid,key):return {'property_definitions':[]}


class RegressionV06(unittest.TestCase):
    def test_chat_and_discussion_are_absent_from_selection_and_collections(self):
        inv=build_inventory(Inventory(),'space')
        self.assertEqual({o['id'] for o in inv['objects']},{'a','d'})
        self.assertEqual([x['id'] for x in inv['members']['col']],['a'])
        self.assertEqual({t['key'] for t in inv['types']},{'page','note'})
        self.assertTrue(is_conversation({'type':'chat'}))
        self.assertTrue(is_conversation({'layout':'discussion'}))
        self.assertFalse(is_conversation({'type':'page','name':'Chat de travail'}))

    def test_internal_fields_are_ignored_but_custom_preserved(self):
        doc={'properties':{'Origin':'webclipper','resolved_layout':'basic',
                'created_in_context_ref':'CID','created_in_context':['CID'],
                'picture':{'some':'value'},'Score':10}}
        props=custom_properties(doc)
        self.assertEqual(props,{'picture':{'some':'value'},'Score':10})
        self.assertTrue(internal_property('created_in_context'))
        self.assertEqual(declared_properties({'property_definitions':[
            {'property':'Origin','format':'number'},
            {'property':'Score','format':'number'}]},{} )[0]['name'],'Score')

    def test_bookmark_keeps_only_titled_link(self):
        doc={'properties':{'URL':'https://example.com/item','Origin':'webclipper'}}
        self.assertEqual(bookmark_url(doc),'https://example.com/item')
        self.assertEqual(titled_link('Mon signet','https://example.com/item'),
                         '[Mon signet](https://example.com/item)')
        issues=set()
        text=render_blocks({'blocks':[{'type':'bookmark','url':'https://example.com/item',
                         'title':'Mon signet'}]}, {},'sid',{},False,lambda *_:None,issues)
        self.assertIn('[Mon signet](https://example.com/item)',text)
        self.assertNotIn('Signet :',text)

    def test_html_rich_tables_columns_images_youtube(self):
        blocks=[{'type':'row','indent':0},
                {'type':'column','indent':1,'fields':{'width':.35}},
                {'type':'paragraph','indent':2,'text':'Gauche'},
                {'type':'column','indent':1,'fields':{'width':.65}},
                {'type':'paragraph','indent':2,'text':'Droite'},
                {'type':'paragraph','indent':0,'text':'Suite'},
                {'type':'table','rows':[{'is_header':True,'cells':[{'text':'Nom'},{'text':'Prix'}]},
                                        {'cells':[{'text':'**Produit**','background_color':'red'},
                                                  {'text':'30','colspan':2}]}]},
                {'type':'image','object_id':'f','name':'Image','fields':{'width':200}},
                {'type':'embed','processor':'youtube','url':'https://youtu.be/AbCdEfGhI01'}]
        issues=set()
        result=render_blocks({'blocks':blocks},{},'sid',{},True,lambda *_:'any://f/sid/newf',issues)
        self.assertIn('<!-- any:columns ',result)
        self.assertIn('Gauche',result)
        self.assertIn('Droite',result)
        self.assertIn('Suite',result)
        self.assertIn('<table><tbody>',result)
        self.assertIn('<strong>Produit</strong>',result)
        self.assertIn('width="200"',result)
        self.assertIn('https://www.youtube.com/watch?v=AbCdEfGhI01',result)
        self.assertIn('Couleur des cellules du tableau non reproduite',issues)
        self.assertEqual(youtube_embed('https://evil.com/a'),None)
        self.assertEqual(youtube_embed('https://youtu.be/bad'),None)

    def test_realistic_anyblock_table_with_widths_and_compound_cells(self):
        issues=set()
        result=render_blocks({'blocks':[{'type':'table',
          'columns':[{'id':'a','width':120},{'id':'b','width':180}],
          'rows':[{'is_header':True,'cells':['Désignation','Terminé']},
                  {'cells':[{'type':'paragraph','text':'Texte **gras**'},
                            {'type':'checkbox','checked':True,'text':'Validé'}]}]}]},
          {},'sid',{},False,lambda *_:None,issues)
        self.assertIn('<colgroup>',result)
        self.assertIn('width:120px',result)
        self.assertIn('<strong>gras</strong>',result)
        self.assertIn('aria-checked="true">Validé',result)

    def test_image_relative_width_is_percentage_not_pixels(self):
        issues=set()
        result=render_blocks({'blocks':[{'type':'image','object_id':'f',
          'name':'Miniature','fields':{'width':0.45}}]}, {},'sid',{},True,
          lambda *_:'any://f/sid/new',issues)
        self.assertIn('width:45%',result)
        self.assertNotIn('width="45"',result)

    def test_native_emoji_attempt_and_safe_fallback(self):
        responses=[APIError('champ icon non pris en charge',400),{'objectId':'obj2'}]
        def req(*args,**kwargs):
            answer=responses.pop(0)
            if isinstance(answer,Exception):raise answer
            return answer
        warnings=[]
        with patch('api_clients.target_write',side_effect=req) as call:
            oid=create_object(object(),'sp','Ma page',[],emoji='🌈',icon_warnings=warnings)
        self.assertEqual(oid,'obj2')
        self.assertEqual(call.call_count,2)
        self.assertIn('Icône emoji non reconnue',warnings[0])
        self.assertIn('icon',call.call_args_list[0].args[2]['initialProperties']['any'])
        self.assertNotIn('icon',call.call_args_list[1].args[2]['initialProperties']['any'])

if __name__=='__main__':unittest.main()
