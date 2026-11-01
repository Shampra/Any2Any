import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from tools.build_release import build,ROOT
from tools.build_windows import package_windows

class DistributionLayoutTests(unittest.TestCase):
    def test_source_archive_has_no_runtime_modules_at_the_top_level(self):
        with tempfile.TemporaryDirectory() as folder:
            archive,_,_=build(output=Path(folder)/'source.zip')
            with zipfile.ZipFile(archive) as z:
                names=z.namelist();self.assertIn('demarrer.bat',names);self.assertIn('app/server.py',names)
                self.assertFalse(any('/' not in name and name.endswith('.py') for name in names))
                self.assertFalse(any(name.startswith('dev/') for name in names))
                z.extractall(folder)
            result=subprocess.run([sys.executable,'-B',str(Path(folder)/'app/server.py'),'--help'],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_windows_archive_keeps_only_the_executable_at_the_top_level(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle=Path(folder)/'bundle';(bundle/'_internal/static').mkdir(parents=True)
            (bundle/'Any2Any.exe').write_bytes(b'fake-PE-for-layout-test');(bundle/'_internal/python312.dll').write_bytes(b'dll')
            (bundle/'_internal/static/index.html').write_bytes(b'page')
            path=package_windows(bundle,output=Path(folder)/'windows.zip')
            with zipfile.ZipFile(path) as z:
                self.assertEqual([name for name in z.namelist() if '/' not in name],['Any2Any.exe'])
                manifest=json.loads(z.read('documentation/BUILD.json'))
                for name,digest in manifest['sha256'].items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),path.with_suffix('.sha256').read_text().split()[0])

if __name__=='__main__':unittest.main()
