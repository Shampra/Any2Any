"""Runtime profiles for the unified app and isolated development."""
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    port: int

    @property
    def config_dir(self):
        root=Path(os.getenv('APPDATA',Path.home()/'.config'))
        return root/'any2any' if self.name=='unified' else root/'any2any-dev'/self.name

PROFILES={name:RuntimeProfile(name,port) for name,port in
          (('unified',8766),('notion-dev',8876),('anytype-dev',8877))}

def get_profile(name=None):
    selected=name or os.getenv('ANY2ANY_PROFILE','unified')
    if selected not in PROFILES:
        raise ValueError('Profil inconnu : '+selected)
    return PROFILES[selected]


def seed_unified_settings(profile):
    """Reuse protected development credentials once, without changing either profile."""
    if profile.name!='unified':return
    target=profile.config_dir/'settings.json'
    if target.exists():return
    import json
    data={}
    for name in ('notion-dev','anytype-dev'):
        try:source=json.loads((get_profile(name).config_dir/'settings.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):continue
        if not isinstance(source,dict):continue
        fields=('notion_token','anytwo_port','source_kind') if name=='notion-dev' else ('anytype_key','anytype_port')
        for field in fields:
            value=source.get(field)
            if field in ('notion_token','anytype_key'):
                prefix='dpapi:' if os.name=='nt' else 'plain:'
                if not isinstance(value,str) or not value.startswith(prefix):continue
            elif field.endswith('_port'):
                if value is not None and (not isinstance(value,int) or isinstance(value,bool) or not 1<=value<=65535):continue
            elif value not in ('anytype','notion'):continue
            data[field]=value
    if not data:return
    target.parent.mkdir(parents=True,exist_ok=True)
    try:
        with target.open('x',encoding='utf-8') as stream:
            if os.name!='nt':os.chmod(target,0o600)
            json.dump(data,stream,ensure_ascii=False,indent=2)
    except FileExistsError:pass
