"""Notion block/rich-text conversion to the shared Anytwo document dialect."""
import html
import json
import re
from notion_source import notion_id, text
from rich_content import native_toggle, youtube_markdown, image_markdown, file_html


def escape(value):
    return re.sub(r'([\\`*\[\]<>_~#|+.!-])',r'\\\1',str(value))


def mark(value,delimiter):
    # Lexical/CommonMark deliberately rejects '**word **' and '* word*'.
    # Notion often places the separating space inside the annotated run.
    match=re.fullmatch(r'(\s*)(.*?)(\s*)',value,re.S)
    before,body,after=match.groups()
    return before+delimiter+body+delimiter+after if body else value


def safe_url(value):
    from urllib.parse import urlsplit
    value=str(value or '')
    try:
        parsed=urlsplit(value)
        if parsed.scheme in ('http','https','mailto','tel','any') and not any(ord(c)<32 for c in value):
            return value.replace(' ', '%20').replace('(', '%28').replace(')', '%29')
    except ValueError:pass
    return ''


class Content:
    def __init__(self,engine,source_id):
        self.e=engine;self.source_id=source_id;self.issues=engine.issues(source_id);self.seen=set()
        if not hasattr(engine,'content_plans'):engine.content_plans={}
        self.plan=engine.content_plans.setdefault(source_id,{'headings':[],'tocs':[],'synced':[]})

    def link(self,url):
        try:oid=notion_id(url)
        except ValueError:return safe_url(url)
        if oid in self.e.mapping:return 'any://o/'+self.e.sid+'/'+self.e.mapping[oid]
        sources=self.e.database_sources(oid) if hasattr(self.e,'database_sources') else [x['id'] for x in self.e.databases.get(oid,{}).get('data_sources',[])]
        collections=[self.e.collections[sid] for sid in sources if sid in self.e.collections]
        if len(collections)==1:return 'any://o/'+self.e.sid+'/'+collections[0]
        self.issues.add('Lien Notion hors périmètre conservé comme lien vers la source')
        return safe_url(url)

    def rich(self,items):
        result=[]
        for item in items or []:
            kind=item.get('type');ann=item.get('annotations') or {}
            value=escape(item.get('plain_text') or item.get('text',{}).get('content') or '')
            url=(item.get('text',{}).get('link') or {}).get('url') or item.get('href')
            if kind=='mention':
                mention=item.get('mention') or {};target=mention.get('page') or mention.get('database')
                if target:
                    oid=target['id'];value=escape(self.e.names.get(oid) or value or 'Page liée')
                    url='https://www.notion.so/'+oid.replace('-','')
                elif mention.get('date'):value=escape(mention['date'].get('start',''))
            if kind=='equation':value='$'+item.get('equation',{}).get('expression','')+'$'
            if ann.get('code'):
                raw=text([item]);fence='`'*(max([len(x) for x in re.findall(r'`+',raw)]+[0])+1)
                value=fence+' '+raw+' '+fence
            else:
                if ann.get('bold'):value=mark(value,'**')
                if ann.get('italic'):value=mark(value,'*')
                if ann.get('strikethrough'):value=mark(value,'~~')
            if ann.get('underline'):self.issues.add('Soulignement non pris en charge par le pont Markdown Anytwo ; texte conservé sans balises')
            if ann.get('color') not in (None,'default'):self.issues.add('Couleur de texte/fond non reproduite')
            if url:
                target=self.link(url)
                if target:value='['+value+']('+target+')'
            result.append(value)
        return ''.join(result)

    def children(self,block):
        return self.e.blocks.get(block['id'],[]) if block.get('has_children') else []

    def render(self,blocks):
        parts=[];blanks=0
        for block in blocks:
            self.e.check()
            if block['id'] in self.seen:
                self.issues.add('Référence cyclique de bloc ignorée');continue
            self.seen.add(block['id'])
            typ=block.get('type','unsupported');data=block.get(typ) or {};children=self.children(block)
            value=self.rich(data.get('rich_text',[]));nested=''
            if typ in ('heading_1','heading_2','heading_3'):
                self.plan['headings'].append({'source_id':block['id'],'level':int(typ[-1]),'text':value,'label':text(data.get('rich_text',[]))})
            if data.get('color') not in (None,'default'):self.issues.add('Couleur de texte/fond non reproduite')
            if typ=='paragraph' and not value and not children:
                blanks+=1;self.seen.remove(block['id']);continue
            if typ=='toggle' or typ.startswith('heading_') and data.get('is_toggleable'):
                kind='toggle_'+typ if typ.startswith('heading_') else 'toggle'
                fragment=native_toggle({'type':kind},children,self.render,value)
            elif typ=='column_list':
                cols=children;ratios=[(c.get('column') or {}).get('width_ratio') or 1 for c in cols]
                fragment='<!-- any:columns '+json.dumps({'widths':ratios})+' -->'
                for col in cols:fragment+='\n\n<!-- any:column -->\n\n'+self.render(self.children(col))
                fragment+='\n\n<!-- /any:columns -->'
            elif typ=='table':
                rows=[]
                for index,row in enumerate(children):
                    cells=[]
                    for ci,cell in enumerate(row.get('table_row',{}).get('cells',[])):
                        tag='th' if (index==0 and data.get('has_column_header')) or (ci==0 and data.get('has_row_header')) else 'td'
                        from rich_content import inline_html
                        cells.append('<'+tag+'>'+inline_html(self.rich(cell))+'</'+tag+'>')
                    rows.append('<tr>'+''.join(cells)+'</tr>')
                fragment='<table><tbody>'+''.join(rows)+'</tbody></table>'
            elif typ in ('image','audio','video','file','pdf'):
                url=(data.get(data.get('type','file')) or {}).get('url','')
                fragment=youtube_markdown(url,block['id']) if typ=='video' else None
                if fragment is None:
                    uri=self.e.media(self.source_id,data,typ)
                    if uri:fragment=image_markdown(uri,uri.name,data.get('width')) if typ=='image' else file_html(uri,uri.name)
                    else:fragment='> Pièce jointe non récupérée : '+escape(data.get('name') or typ)
                caption=text(data.get('caption',[]))
                if caption and typ=='image' and uri:
                    from notion_native import caption_image
                    fragment=caption_image(fragment,caption,self.e.mapping[self.source_id],block['id'])
                elif caption:fragment+='\n\n'+self.rich(data.get('caption',[]))
            elif typ in ('embed','bookmark','link_preview'):
                url=data.get('url','');fragment=youtube_markdown(url,block['id'])
                if not fragment:
                    target=self.link(url);fragment='['+escape(url)+']('+target+')' if target else escape(url)
                    if typ=='embed':self.issues.add('Embed fournisseur non pris en charge : conservé comme lien')
            elif typ=='child_database':fragment=self.e.database_content(self.source_id,block['id'])
            elif typ=='child_page':
                oid=self.e.mapping.get(block['id']);name=escape(data.get('title') or self.e.names.get(block['id'],'Sous-page'))
                fragment='['+name+'](any://o/'+self.e.sid+'/'+oid+')' if oid else name
                if not oid:self.issues.add('Page enfant non importée')
            elif typ=='link_to_page':
                target=data.get(data.get('type','page_id'));fragment=self.rich([{'type':'mention','mention':{'page':{'id':target}}}]) if target else ''
            elif typ=='synced_block':
                from notion_native import synced_block
                fragment=synced_block(self.e,self.source_id,block,self.render(children),self.plan)
            elif typ=='callout':
                from notion_icons import emoji
                options={};icon=emoji(data.get('icon'))
                if icon:options['icon']=icon
                body=([value] if value else [])+([self.render(children)] if children else [])
                fragment='<!-- any:callout '+json.dumps(options,ensure_ascii=False,separators=(',',':'))+' -->\n\n'+'\n\n'.join(body)
                fragment+='\n\n<!-- /any:callout -->'
            elif typ=='code':
                raw=text(data.get('rich_text'));fence='`'*max(3,max([len(x)+1 for x in re.findall(r'`+',raw)]+[0]))
                lang=re.sub(r'[^A-Za-z0-9_+-]','',data.get('language',''))
                fragment=fence+lang+'\n'+raw+'\n'+fence
            elif typ=='equation':fragment='$$\n'+data.get('expression','')+'\n$$'
            elif typ=='divider':fragment='---'
            elif typ=='table_of_contents':
                from notion_native import marker
                fragment=marker('toc',self.source_id,block['id']);self.plan['tocs'].append(fragment)
            elif typ=='breadcrumb':
                self.issues.add('Fil d’Ariane source non recréé');fragment=''
            elif typ in ('paragraph','heading_1','heading_2','heading_3','bulleted_list_item','numbered_list_item','to_do','quote','column'):
                prefix={'heading_1':'# ','heading_2':'## ','heading_3':'### ','bulleted_list_item':'- ','numbered_list_item':'1. ','quote':'> '}.get(typ,'')
                if typ=='to_do':prefix='- [x] ' if data.get('checked') else '- [ ] '
                fragment=prefix+value
                if children:
                    nested=self.render(children)
                    if typ in ('bulleted_list_item','numbered_list_item','to_do'):nested='\n'.join('    '+line for line in nested.split('\n'))
                    fragment+='\n'+nested if typ in ('bulleted_list_item','numbered_list_item','to_do') else '\n\n'+nested
            else:
                self.issues.add('Bloc non reproduit : '+typ);fragment=value
                self.e.results[self.source_id].setdefault('unconverted_blocks',[]).append({'id':block['id'],'type':typ,'source':data})
                if children:fragment+='\n\n'+self.render(children)
            self.seen.remove(block['id'])
            if not fragment:continue
            parts.append(('\n'*(2+blanks) if parts else '\n'*blanks)+fragment);blanks=0
        return ''.join(parts)+'\n'*blanks
