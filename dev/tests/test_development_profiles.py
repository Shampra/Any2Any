import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from runtime_profile import get_profile
import server

class DevelopmentProfileTests(unittest.TestCase):
    def test_profiles_do_not_share_stable_settings_or_each_other(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'APPDATA':tmp}):
            notion=get_profile('notion-dev');anytype=get_profile('anytype-dev')
            self.assertNotEqual(notion.config_dir,anytype.config_dir)
            self.assertNotEqual(notion.port,anytype.port)
            self.assertNotIn(8765,(notion.port,anytype.port))
            for p in (notion,anytype):
                self.assertNotEqual(p.config_dir,Path(tmp)/'anytype-anytwo-importer')
                self.assertEqual(p.config_dir.parent,Path(tmp)/'any2any-dev')

    def test_unqualified_start_is_isolated_and_invalid_profile_is_refused(self):
        with patch.dict(os.environ,{},clear=True):self.assertEqual(get_profile().name,'unified')
        with self.assertRaises(ValueError):get_profile('stable')

    def test_profile_switch_controls_both_load_and_save_paths(self):
        previous=server.RUNTIME_PROFILE.name
        try:
            with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'APPDATA':tmp}):
                for name in ('notion-dev','anytype-dev'):
                    server.configure_runtime(name)
                    self.assertEqual(server.CONFIG_PATH,Path(tmp)/'any2any-dev'/name/'settings.json')
                    self.assertEqual(server.load_settings()['anytype_key'],'')
        finally:server.configure_runtime(previous)

if __name__=='__main__':unittest.main()
