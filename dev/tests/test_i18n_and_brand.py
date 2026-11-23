"""Lightweight checks for Any2Any public branding and UI localization."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
            html = (ROOT / 'app' / 'static' / name).read_text(encoding='utf-8')
            self.assertIn('data-language-choice', html)
            for lng in ('fr', 'en', 'de'):
                self.assertIn(f'value="{lng}"', html)

    @unittest.skipUnless(shutil.which('node'), 'Node.js is not required to run the app')
    def test_dictionary_returns_french_english_german(self):
        js = ROOT / 'app' / 'static' / 'i18n.js'
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

    @unittest.skipUnless(shutil.which('node'), 'Node.js is not required to run the app')
    def test_report_and_log_strings_are_translated(self):
        js = ROOT / 'app' / 'static' / 'i18n.js'
        cases = {
            'Source des données': 'Data source',
            'Rigus — partiel · 1 adaptation(s), 0 erreur(s)': 'Rigus — partial · 1 adaptation(s), 0 error(s)',
            'Disposition en colonnes simplifiée': 'Column layout simplified',
            "Sélectionné via l’espace « County »": 'Selected through the space “County”',
            'Overview Anytwo : 2 widget(s) ajouté(s), 0 déjà présent(s).':
                'Anytwo Overview: 2 widget(s) added, 0 already present.',
            'ID Anytwo :': 'Anytwo ID: ',
            'Contenu non reproduit :': 'Content not reproduced: ',
            'Propriété « unknown » conservée en texte (format non transposable)':
                'Property “unknown” kept as text (format cannot be mapped)',
        }
        script = """const fs=require('fs'),vm=require('vm');
const sandbox={navigator:{language:'fr-FR'},localStorage:{getItem:()=>null,setItem:()=>{}}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
const cases=JSON.parse(process.argv[2]);
for(const [source,expected] of Object.entries(cases)){
  const got=sandbox.Any2AnyI18n.t(source,'en');
  if(got!==expected){console.error(JSON.stringify([source,expected,got]));process.exit(2);}
}
"""
        subprocess.run(['node', '-e', script, str(js), json.dumps(cases)], check=True, capture_output=True, text=True)

    def test_every_static_ui_string_has_a_translation(self):
        js = ROOT / 'app' / 'static' / 'i18n.js'
        html = (ROOT / 'app' / 'static' / 'index.html').read_text(encoding='utf-8')
        # Markup is the reference: no visible French label may lack a dictionary entry.
        script = """const fs=require('fs'),vm=require('vm');
const sandbox={navigator:{language:'fr-FR'},localStorage:{getItem:()=>null,setItem:()=>{}}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
const html=fs.readFileSync(process.argv[2],'utf8');
const t=sandbox.Any2AnyI18n.t;
const skip=new Set(['Any2Any','Anytype','Notion','Anytwo','FR','EN','DE','A','JSON','API','ID','NOTION → ANYTWO','SIMULATION']);
const missing=new Set();
const body=html.replace(/<script[\s\S]*?<\/script>/g,'').replace(/<style[\s\S]*?<\/style>/g,'');
for(const m of body.matchAll(/>([^<>]+)</g)){
  const text=m[1].replace(/&nbsp;/g,'\u00a0').trim();
  if(!text||text.length<3||!/[a-zA-Zà-ÿ]/.test(text))continue;
  if(/^[\d\s·:—↗!✕⌁→↻✓•×]+$/.test(text))continue;
  if(skip.has(text)||/^https?:\/\//.test(text))continue;
  if(t(text,'en')===text&&t(text,'de')===text)missing.add(text);
}
for(const m of html.matchAll(/(?:placeholder|title|aria-label)="([^"]+)"/g)){
  const text=m[1].replace(/&nbsp;/g,'\u00a0').trim();
  if(!text||!/[a-zA-Zà-ÿ]/.test(text)||skip.has(text)||/^https?:\/\//.test(text))continue;
  if(t(text,'en')===text&&t(text,'de')===text)missing.add(text);
}
if(missing.size){console.error(JSON.stringify([...missing]));process.exit(3);}
"""
        subprocess.run(['node', '-e', script, str(js), str(ROOT / 'app' / 'static' / 'index.html')],
                       check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
