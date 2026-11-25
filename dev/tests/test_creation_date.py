"""Creation stamps use Anytwo's derived field, never a shadow column."""
import unittest
from unittest.mock import patch

from inline_views import inline_records
from migration import Engine, creation_date_property, custom_properties, declared_properties
from test_inline_views import Source
from view_conversion import ViewConverter, collection_presentation


class CreationDateTests(unittest.TestCase):
    def test_system_aliases_are_excluded_from_values_and_declared_columns(self):
        for key in ('created_date', 'createdDate', 'createdAt', 'creation_date'):
            with self.subTest(key=key):
                self.assertEqual(custom_properties({'properties':{key:'2020-01-01'}}), {})
                self.assertEqual(declared_properties({'property_definitions':[
                    {'property':key, 'name':'Creation date', 'format':'date'}]}, {}), [])
                self.assertTrue(creation_date_property(key))

    def test_custom_creation_date_homonym_is_preserved_by_identity(self):
        spec = {'key':'custom_date', 'internal_key':'abc123', 'name':'Creation date', 'format':'date'}
        vocabulary = {'creation date':spec}
        doc = {'properties':{'Creation date':'2020-01-01'},
               'property_internal_keys':{'Creation date':'abc123'}}
        self.assertFalse(creation_date_property('Creation date', vocabulary))
        self.assertEqual(custom_properties(doc, vocabulary), doc['properties'])
        self.assertEqual(len(declared_properties({'property_definitions':[
            {'property':'abc123', 'name':'Creation date', 'format':'date'}]}, vocabulary)), 1)

    def scoped(self, name='created_date', metadata=None, bindings=None):
        e = Engine(Source(), object(), {'all':[], 'types':[], 'members':{}},
                   {'source_space':{'id':'src'}, 'target':{}})
        e.dest_sid = 'dest'; e.mapping = {'b':'new-b'}
        cv = ViewConverter(bindings or {}, e.mapping, {}, metadata or {})
        view = {'type':'table', 'columns':[{'property':'name'}, {'property':name}],
                'sorts':[{'property':name, 'direction':'desc', 'include_time':True}]}
        issues = set()
        with patch.object(e, 'col', return_value='real'), \
             patch.object(e, 'property') as create, patch('migration.set_column_value') as write, \
             patch('migration.add_membership'):
            _, scoped = e.inline_scope('a', {'object_id':'col', 'views':[view]}, ['b'], cv, issues)
        create.assert_not_called(); write.assert_not_called()
        return scoped, view, issues

    def test_collection_display_and_sort_use_the_native_readonly_stamp(self):
        cv, view, issues = self.scoped(metadata={'created_date':{
            'key':'created_date', 'internal_key':'createdDate', 'name':'Creation date', 'format':'date'}})
        _, query, settings = cv.convert(view, {'any.collections':'real'})
        query, settings = collection_presentation(cv, view, 'real', query, settings, issues)
        self.assertEqual(query['sort'][0], '-createdAt')
        self.assertEqual(query['anyUi']['sort'], [{'propertyId':'createdAt', 'dir':'desc'}])
        self.assertIn('createdAt', settings['visible'])
        self.assertNotIn('createdAt', settings['hidden'])
        self.assertTrue(any('date source non conservée' in issue for issue in issues))

    def test_inline_view_keeps_a_usable_native_creation_sort(self):
        cv, view, issues = self.scoped('createdDate')
        rows, failed = inline_records(cv, {'views':[view]}, 'real', 'instance', issues, native_layouts=True)
        self.assertFalse(failed)
        self.assertEqual(rows[0]['query']['sort'][0], '-createdAt')
        self.assertEqual(rows[0]['query']['anyUi']['sort'][0]['propertyId'], 'createdAt')

    def test_custom_date_view_does_not_get_replaced_by_the_native_stamp(self):
        spec = {'key':'custom_date', 'internal_key':'abc123', 'name':'Creation date', 'format':'date'}
        cv, view, issues = self.scoped('Creation date', {'creation date':spec}, {
            'creation date':[('real.custom', spec, {'type':'datetime'})]})
        self.assertEqual(cv.convert(view, {})[1]['sort'][0], '-real.custom')
        self.assertFalse(issues)
