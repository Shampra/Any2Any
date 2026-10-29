"""Lightweight checks for Any2Any public branding and UI localization."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicReadmeTests(unittest.TestCase):
    def test_both_readmes_have_alpha_warning(self):
        for name, phrase in [('README.md', 'versions alpha'), ('README.en.md', 'alpha versions')]:
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertIn('# Any2Any', text)
            self.assertIn(phrase, text)
            self.assertIn('README.en.md', text)
            self.assertIn('README.md', text)

    def test_language_picker_on_both_screens(self):
        for name in ('index.html', 'pair.html'):
            html = (ROOT / 'static' / name).read_text(encoding='utf-8')
            self.assertIn('data-language-choice', html)
            for lng in ('fr', 'en', 'de'):
                self.assertIn(f'value="{lng}"', html)

    @unittest.skipUnless(shutil.which('node'), 'Node.js is not required to run the app')
    def test_dictionary_returns_french_english_german(self):
        js = ROOT / 'static' / 'i18n.js'
        script = '''const fs=require('fs'),vm=require('vm');
const sandbox={navigator:{language:'fr-FR'},localStorage:{getItem:()=>null,setItem:()=>{}}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
const t=sandbox.Any2AnyI18n.t;
if(t('Importer vos données','en')!=='Import your data') process.exit(2);
if(t('Importer vos données','de')!=='Daten importieren') process.exit(3);
if(t('Importer vos données','fr')!=='Importer vos données') process.exit(4);
if(t('Any2Any · Importer','en')!=='Any2Any · Import') process.exit(5);
'''
        subprocess.run(['node', '-e', script, str(js)], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
