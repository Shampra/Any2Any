import unittest
from unittest.mock import Mock,patch
from view_conversion import ViewConverter,collection_presentation
import anytwo_backend as backend

class SharedViewSettingsTests(unittest.TestCase):
    def test_optional_presentation_is_shared_but_existing_views_are_unchanged(self):
        c=ViewConverter({}, {}, {}, {})
        _,_,original=c.convert({'type':'gallery'},{})
        self.assertNotIn('galleryFitImage',original);self.assertNotIn('openMode',original)
        _,_,settings=c.convert({'type':'gallery','presentation':{'galleryFitImage':True,'openMode':'side-peek'}},{})
        self.assertTrue(settings['galleryFitImage']);self.assertEqual(settings['openMode'],'side-peek')

    def test_group_settings_use_the_native_collection_property_id(self):
        c=ViewConverter({'tag':[('collection.prop',{'format':'select'},{'type':'choice'})]}, {}, {}, {})
        query,settings=collection_presentation(c,{'group_settings':{'property':'tag','sort':'desc','hideEmpty':True}},'collection',{}, {},set())
        self.assertEqual(query['groupBy'],{'propId':'prop'});self.assertEqual(query['anyUi']['group']['sort'],'desc')

    def test_space_icon_attaches_to_index_and_patches_native_file_reference(self):
        api=Mock();api.port=31310
        with patch('anytwo_backend.local_get',return_value={'spaceIndexObjectId':'index'}),patch('anytwo_backend.attach_file',return_value='file'),patch('anytwo_backend.target_write') as write:
            backend.set_space_icon(api,'space','icon.png',b'content','image/png')
        write.assert_called_once_with(api,'/spaces/space',{'iconCid':'any://f/space/file'},method='PATCH')

if __name__=='__main__':unittest.main()
