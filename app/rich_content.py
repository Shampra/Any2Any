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


def feature_envelope_supported(version, feature):
    """Whether this client interprets a native envelope kind natively.

    Anytwo 0.5 stores HTML comments as generic html blocks, so the collapsible,
    columns and embed envelopes become visible page text. The native dynamic
    table-of-contents block is interpreted from 0.4.1 and remains valid there.
    An unknown or unexpected version keeps native envelopes untouched.
    """
    if not version or isinstance(version, (str, bytes)):
        return True
    try:
        parsed = tuple(int(part) for part in version)
    except (TypeError, ValueError):
        return True
    if feature == 'table-of-contents':
        return parsed >= (0, 4, 1)
    return parsed < (0, 5, 0)


def envelopes_supported(version):
    """True when every legacy envelope feature is still interpreted natively."""
    return all(feature_envelope_supported(version, feature)
               for feature in ('collapsible', 'columns', 'embed'))


ENVELOPE_COMMENT_RE=re.compile(r'[ \t]*<!--\s*/?\s*any:[^\n]*?-->[ \t]*')
COLLAPSIBLE_ENVELOPE_RE=re.compile(
    r'<!--\s*any:collapsible\s[^\n]*?-->[ \t]*\n+[ \t]*([^\n]+?)[ \t]*\n+[ \t]*<!--\s*any:collapsible-content\s*-->')
FENCE_OPEN_RE=re.compile(r'^[ \t]*(`{3,}|~{3,})([^\n]*)$')
TOC_ENVELOPE_OPEN_RE=re.compile(r'^[ \t]*<!--\s*any:block\s+[^\n]*?"table-of-contents"[^\n]*?-->[ \t]*$')


def _protected_blocks(lines):
    """Split lines into literal blocks the fallback must not rewrite.

    Fenced code (3+ backticks or tildes, closed by the same character and at
    least the same length) and native dynamic table-of-contents envelopes are
    returned as (start, end) index ranges. An unclosed fence protects the rest
    of the document, so a stray fence can never expose markers to stripping.
    """
    ranges=[];index=0
    while index<len(lines):
        opening=FENCE_OPEN_RE.match(lines[index])
        if opening and not (opening.group(1)[0]=='`' and '`' in opening.group(2)):
            char=opening.group(1)[0];length=len(opening.group(1))
            closing=re.compile(r'^[ \t]*'+re.escape(char)+r'{'+str(length)+r',}[ \t]*$')
            end=index+1
            while end<len(lines) and not closing.match(lines[end]):end+=1
            end=min(end+1,len(lines))
            ranges.append((index,end));index=end;continue
        if TOC_ENVELOPE_OPEN_RE.match(lines[index]):
            end=index+1
            while end<len(lines) and not re.match(r'^[ \t]*<!--\s*/any:block',lines[end]):end+=1
            end=min(end+1,len(lines))
            ranges.append((index,end));index=end;continue
        index+=1
    return ranges


def legacy_markup(markdown):
    """Rewrite unsupported envelopes as plain Markdown for newer clients.

    Anytwo 0.5 stores HTML comments as generic html blocks instead of the native
    collapsible, columns and embed nodes, so those envelopes would be displayed
    as page text. Toggle titles stay visible as bold titles or headings, while
    fenced code and the native dynamic table-of-contents block are preserved
    verbatim.
    """
    def toggle(match):
        title=match.group(1)
        return title if title.startswith('#') else '**'+title+'**'
    lines=str(markdown).split('\n')
    ranges=_protected_blocks(lines)
    if not ranges:
        return _legacy_markup_text(str(markdown),toggle)
    def sentinel(position):
        # A NUL-delimited token cannot appear in Markdown source text.
        return '\x00any2any-protected-'+str(position)+'\x00'
    pieces=[];cursor=0
    for position,(start,end) in enumerate(ranges):
        pieces.append('\n'.join(lines[cursor:start]))
        pieces.append(sentinel(position))
        cursor=end
    pieces.append('\n'.join(lines[cursor:]))
    text=_legacy_markup_text('\n'.join(pieces),toggle)
    for position,(start,end) in enumerate(ranges):
        text=text.replace(sentinel(position),'\n'.join(lines[start:end]))
    return text


def _legacy_markup_text(markdown,toggle):
    text=COLLAPSIBLE_ENVELOPE_RE.sub(toggle,markdown)
    text=ENVELOPE_COMMENT_RE.sub('',text)
    return re.sub(r'\n{3,}','\n\n',text).strip('\n')


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


def youtube_markdown(value,identity='',label='Vidéo YouTube'):
    canonical=youtube_canonical(value)
    if canonical is None:return None
    instance='any2any-'+hashlib.sha256((identity+'\0'+canonical).encode()).hexdigest()[:24]
    envelope={'v':1,'kind':'embed','schema':1,'instance':instance,
              'data':{'provider':'youtube','url':canonical}}
    opening='<!-- any:block '+json.dumps(envelope,separators=(',',':'))+' -->'
    closing='<!-- /any:block '+json.dumps({'instance':instance},separators=(',',':'))+' -->'
    return opening+'\n\n['+label+']('+canonical+')\n\n'+closing


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


def remove_unsupported_inline(text, keep_underline=False):
    tags = 'sub|sup' if keep_underline else 'u|sub|sup'
    parts=re.split(r'(`+[^`]*`+)',text)
    return ''.join(part if index%2 else re.sub(r'</?(?:'+tags+r')>','',part)
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
