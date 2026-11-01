"""Run both source regression suites from the organized checkout."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
sys.path.insert(0,str(ROOT/'dev'))
if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(ROOT/'dev/tests'))
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(not result.wasSuccessful())
