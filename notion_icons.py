"""Deterministic icon conversion; never infer the contents of arbitrary images."""
import json
from urllib.parse import urlsplit,unquote

# Named Notion built-ins and legacy /icons/<name>_<color>.svg assets only.
ICON_EMOJI={
 'pot':'🍲','cooking-pot':'🍲','chef-hat':'🧑‍🍳','chef':'🧑‍🍳','wine-bottle':'🍾','wine':'🍷',
 'wine-glass':'🍷','whiskey':'🥃','whisky':'🥃','cocktail':'🍸','beer':'🍺',
 'calendar':'📅','clock':'🕒','checkmark':'✅','check':'✅','list':'📋','table':'📊',
 'chart':'📊','chart-bar':'📊','book':'📖','bookmark':'🔖','tag':'🏷️','tags':'🏷️',
 'dollar':'💵','euro':'💶','money':'💰','star':'⭐','heart':'❤️','person':'👤','people':'👥',
 'location':'📍','map-pin':'📍','link':'🔗','text':'📝','number':'🔢','hash':'#️⃣',
 'phone':'📞','email':'✉️','mail':'✉️','file':'📄','folder':'📁','image':'🖼️',
 'button':'🔘','calculator':'🧮','percent':'💯','search':'🔍','home':'🏠','globe':'🌐',
}

def emoji(icon):
    if not isinstance(icon,dict):return None
    if icon.get('emoji'):return icon['emoji']
    name=(icon.get('icon') or {}).get('name')
    if not name:
        url=((icon.get('external') or {}).get('url') or '')
        parsed=urlsplit(url)
        if parsed.hostname in ('www.notion.so','notion.so','www.notion.com','notion.com') and parsed.path.startswith('/icons/'):
            name=unquote(parsed.path.rsplit('/',1)[-1]).split('_')[0].removesuffix('.svg')
    return ICON_EMOJI.get(name)

def content_icon(icon):
    value=emoji(icon)
    if not value:return None
    return 'icon:v2:'+json.dumps({'assignment':{'kind':'emoji','grapheme':value},'color':'grey'},ensure_ascii=False,separators=(',',':'))
