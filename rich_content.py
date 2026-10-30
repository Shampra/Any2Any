"""Anytwo desktop document dialect, verified against client 7a477ecc.

Native envelopes are Markdown handled by the client, not arbitrary HTML
iframes or undocumented editor block types. No source scripts are executed.
"""
import hashlib
import html
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs


class ImportedFile(str):
    def __new__(cls, uri, name, mime='', width=None, height=None):
        obj=super().__new__(cls,uri);obj.name=name;obj.mime=mime;obj.width=width;obj.height=height
        return obj


def depth(block):
    try:return max(0,int(block.get('indent',0)))
    except (ValueError,TypeError):return 0


def descendant_end(blocks,start):
    base=depth(blocks[start]);end=start+1
    while end<len(blocks) and isinstance(blocks[end],dict) and depth(blocks[end])>base:
        end+=1
    return end


def rebase(blocks,amount):
    return [{**b,'indent':max(0,depth(b)-amount)} if isinstance(b,dict) else b for b in blocks]


def native_columns(blocks,start,render):
    end=descendant_end(blocks,start);base=depth(blocks[start]);columns=[];i=start+1
    while i<end:
        block=blocks[i]
        if block.get('type')!='column' or depth(block)!=base+1:
            return None,1  # malformed layout: let ordinary traversal keep its content
        stop=descendant_end(blocks,i)
        columns.append((block,rebase(blocks[i+1:stop],base+2)));i=stop
    if len(columns)<2:return None,1
    widths=[]
    for block,_ in columns:
        raw=block.get('fields') or {}
        try:
            width=float(block.get('width',raw.get('width',1)))
            if not 0<width<100000:return None,1
        except (ValueError,TypeError):width=1
        widths.append(width)
    header='<!-- any:columns '+json.dumps({'widths':widths},separators=(',',':'))+' -->'
    parts=[header]
    for _,children in columns:
        parts.extend(['<!-- any:column -->',render(children)])
    parts.append('<!-- /any:columns -->')
    return '\n\n'.join(parts),end-start


def native_toggle(block,children,render,title):
    kind=block.get('type','toggle')
    if kind.startswith('toggle_heading_'):
        title='#'*int(kind[-1])+' '+title
    opened=block.get('open') if isinstance(block.get('open'),bool) else False
    return '\n\n'.join(['<!-- any:collapsible {"open":'+str(opened).lower()+'} -->',
                         title,'<!-- any:collapsible-content -->',render(children),
                         '<!-- /any:collapsible -->'])


def youtube_canonical(value):
    try:
        url=urlparse(str(value).strip())
        if url.scheme not in ('http','https') or url.username or url.password:return None
        host=(url.hostname or '').casefold()
        if host in ('youtu.be','www.youtu.be'):
            video=url.path.strip('/')
        elif host in ('youtube.com','www.youtube.com','m.youtube.com','youtube-nocookie.com','www.youtube-nocookie.com'):
            if url.path=='/watch':video=(parse_qs(url.query).get('v') or [''])[0]
            elif re.fullmatch(r'/(?:embed|shorts|live)/[^/]+/?',url.path):video=url.path.rstrip('/').split('/')[-1]
            else:return None
        else:return None
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}',video):return None
        return 'https://www.youtube.com/watch?v='+video
    except (ValueError,TypeError):return None


def youtube_markdown(value,identity=''):
    canonical=youtube_canonical(value)
    if canonical is None:return None
    instance='any2any-'+hashlib.sha256((identity+'\0'+canonical).encode()).hexdigest()[:24]
    envelope={'v':1,'kind':'embed','schema':1,'instance':instance,
              'data':{'provider':'youtube','url':canonical}}
    opening='<!-- any:block '+json.dumps(envelope,separators=(',',':'))+' -->'
    closing='<!-- /any:block '+json.dumps({'instance':instance},separators=(',',':'))+' -->'
    return opening+'\n\n[Vidéo YouTube]('+canonical+')\n\n'+closing


def file_anchor_html(uri,name):
    # The client imports this anchor as FileLinkNode; an audio extension selects
    # its native mini-player. Keep the exact original filename as its label.
    return '<p><a data-any-file-link="" href="'+html.escape(str(uri),quote=True)+'">'+html.escape(name)+'</a></p>'


def checkbox_html(text,checked):
    return '<ul __lexicalListType="check"><li role="checkbox" aria-checked="'+str(bool(checked)).lower()+'">'+text+'</li></ul>'


class SafeInline(HTMLParser):
    allowed={'u','sub','sup','s','strong','em','br'}
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
    def handle_starttag(self,tag,attrs):
        self.parts.append('<'+tag+'>' if tag in self.allowed and not attrs else html.escape(self.get_starttag_text()))
    def handle_endtag(self,tag):self.parts.append('</'+tag+'>' if tag in self.allowed else html.escape('</'+tag+'>'))
    def handle_data(self,data):self.parts.append(html.escape(data))


def inline_html(text):
    value=str(text);codes=[]
    def code(match):
        codes.append('<code>'+html.escape(match.group(1))+'</code>')
        return '\x01CODE'+str(len(codes)-1)+'\x02'
    value=re.sub(r'`([^`]+)`',code,value)
    parser=SafeInline();parser.feed(value);parser.close();value=''.join(parser.parts)
    value=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',value)
    value=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<em>\1</em>',value)
    value=re.sub(r'~~(.+?)~~',r'<s>\1</s>',value)
    # Only explicit safe schemes are activated after escaping source HTML.
    value=re.sub(r'\[([^\]]+)\]\(((?:https?://|any://)[^ )]+)\)',r'<a href="\2">\1</a>',value)
    value=value.replace('\n','<br>')
    for index,fragment in enumerate(codes):value=value.replace('\x01CODE'+str(index)+'\x02',fragment)
    return value


def file_html(uri,name):
    """Standalone native FileLinkNode (audio filenames select the player)."""
    label=html.escape(str(name),quote=False).replace('\r','&#13;').replace('\n','&#10;')
    label=re.sub(r'([\\\[\]])',r'\\\1',label)
    target=str(uri).replace('(',r'\(').replace(')',r'\)')
    return '['+label+']('+target+')'


def remove_unsupported_inline(text):
    # Markdown has no underline/subscript/superscript transformer in this
    # client. Keep the content and report the loss, without showing HTML tags.
    parts=re.split(r'(`+[^`]*`+)',text)
    return ''.join(part if index%2 else re.sub(r'</?(?:u|sub|sup)>','',part)
                   for index,part in enumerate(parts))


def image_markdown(uri,name,width=None):
    # Same escaping and width annotation as the desktop ImageNode exporter.
    return '!'+file_html(uri,name)+(f'<!-- any:image-width={int(width)} -->' if width else '')


def image_width(block, imported, issues):
    fields=block.get('fields') if isinstance(block.get('fields'),dict) else {}
    style=block.get('style') if isinstance(block.get('style'),dict) else {}
    raw=block.get('width',fields.get('width',style.get('width')))
    try:
        value=float(raw)
        if 0<value<=1:
            # Anytwo persists pixels only. Use a stable page-width reference,
            # not intrinsic file dimensions (which describe a different scale).
            issues.add('Largeur relative d’image approximée sur une largeur de bloc de référence de 720 px')
            return max(96,round(720*value))
        if 1<value<=2400:return max(96,round(value))
    except (ValueError,TypeError,OverflowError):pass
    return None
