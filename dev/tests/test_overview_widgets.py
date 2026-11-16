import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from anytwo_backend import add_overview_widgets
from api_clients import APIError
from migration import Engine


class OverviewWidgetTests(unittest.TestCase):
    def test_source_selection_only_keeps_mapped_pages_and_collections_in_order(self):
        source = Mock()
        source.widgets.return_value = [
            {'target': '_recently_edited', 'layout': 'list'},
            {'target': 'section-page', 'kind': 'section'},
            {'target': 'page', 'layout': 'link', 'scope': 'space'},
            {'target': 'collection', 'layout': 'tree'},
            {'target': 'page', 'layout': 'tree', 'scope': 'personal'},
            {'target': 'outside', 'layout': 'link'},
            {'target': 'query', 'layout': 'view'},
        ]
        engine = Engine(source, object(), {'all': [], 'types': [], 'members': {}}, {'source_space': {'id': 'src'}})
        engine.dest_sid = 'dest'
        engine.mapping = {'page': 'p', 'section-page': 's', 'query': 'q'}
        engine.col_cache = {'collection:collection': 'c'}
        entries = {key: {'type': 'page'} for key in engine.mapping}
        with patch('anytwo_backend.add_overview_widgets') as write:
            engine.import_widgets(entries, {'query': {'query_source': {}}})
        source.widgets.assert_called_once_with('src')
        self.assertEqual(write.call_args.args[2], [
            {'source_id': 'page', 'target_id': 'p', 'kind': 'object', 'layout': 'link'},
            {'source_id': 'collection', 'target_id': 'c', 'kind': 'collection', 'layout': 'views'},
        ])

    def test_install_then_append_widgets_and_reuse_existing_on_retry(self):
        api = SimpleNamespace(port=31310)
        root = {'id': 'system:overview/v1', 'rootId': 'root'}
        parts = {'parts': [{'key': 'entries', 'datasets': [
            {'key': 'entries', 'module': 'records', 'collection': 'widgetRecords'},
        ]}]}
        rows = {'w:object:existing': {'id': 'w:object:existing', 'pos': 'H!#,'}}
        original = rows['w:object:existing'].copy()
        installed = False

        def read(port, path, **kwargs):
            if '/bundles/' in path:
                if installed:
                    return {'bundle': root}
                raise APIError('Bundle absent', 404)
            if path.endswith('/parts'):
                return parts
            self.assertEqual(kwargs['body']['dataset'], 'widgetRecords')
            return {'records': list(rows.values())}

        def write(target, path, body):
            nonlocal installed
            if path == '/catalog/overview/setup':
                installed = True
                return {'bundles': [{'bundle': root}]}
            self.assertEqual(path, '/spaces/dest/modify')
            for record in body['records']:
                rows[record['id']] = {'id': record['id'], **{op['path']: op['value'] for op in record['ops']}}
            return {}

        widgets = [
            {'kind': 'object', 'target_id': 'p', 'layout': 'link'},
            {'kind': 'collection', 'target_id': 'c', 'layout': 'views'},
        ]
        with patch('anytwo_backend.local_get', side_effect=read), patch('anytwo_backend.target_write', side_effect=write) as writes:
            self.assertEqual([item['status'] for item in add_overview_widgets(api, 'dest', widgets)], ['created', 'created'])
            self.assertEqual([item['status'] for item in add_overview_widgets(api, 'dest', widgets)], ['existing', 'existing'])
        self.assertEqual(writes.call_count, 2)
        self.assertEqual(rows[original['id']], original)
        self.assertEqual(rows['w:object:p']['layout'], 'link')
        self.assertNotIn('layout', rows['w:collection:c'])
        self.assertLess(original['pos'], rows['w:object:p']['pos'])
        self.assertLess(rows['w:object:p']['pos'], rows['w:collection:c']['pos'])
