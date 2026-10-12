"""Small, shared HTML inspection utilities; no browser or third-party dependency."""
from dataclasses import dataclass, field
from html.parser import HTMLParser
import re
from urllib.parse import unquote, urljoin, urlsplit

VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


@dataclass
class Element:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    start: int = 0
    content_start: int = 0
    content_end: int = 0
    end: int = 0

    def walk(self, tag=None):
        if tag is None or self.tag == tag:
            yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.walk(tag)

    def text(self):
        return ''.join(child.text() if isinstance(child, Element) else child for child in self.children)

    def has_class(self, name):
        return name in self.attrs.get('class', '').split()


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.offsets = [0] + [m.end() for m in re.finditer('\n', source)]
        self.root = Element('document')
        self.stack = [self.root]
        self.feed(source)
        self.close()
        if len(self.stack) != 1:
            raise ValueError('Unclosed HTML element: ' + self.stack[-1].tag)

    def position(self):
        line, col = self.getpos()
        return self.offsets[line-1] + col

    def handle_starttag(self, tag, attrs):
        start = self.position()
        node = Element(tag, dict(attrs), start=start,
                       content_start=start+len(self.get_starttag_text()))
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)
        else:
            node.content_end = node.end = node.content_start

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            node = self.stack.pop()
            node.content_end = node.end = node.content_start

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            raise ValueError('Unbalanced HTML closing tag: ' + tag)
        node = self.stack.pop()
        node.content_end = self.position()
        node.end = node.content_end + len('</'+tag+'>')

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def canonical(node, omit_programs=False):
    if isinstance(node, str):
        return re.sub(r'\s+', ' ', node)
    attrs = {k: v for k, v in sorted(node.attrs.items()) if k != 'xmlns'}
    children = [] if omit_programs and node.tag == 'code' and attrs.get('data-language') in {'c','python'} else [canonical(x, omit_programs) for x in node.children]
    return [node.tag, attrs, children]


def css_dependencies(css):
    # Decode CSS escapes before inspection, including escaped identifiers and line joins.
    css = re.sub(r'\\\r?\n', '', css)
    css = re.sub(r'\\([0-9a-fA-F]{1,6})\s?|\\([^\r\n])',
                 lambda m: chr(int(m[1], 16)) if m[1] else m[2], css)
    css = re.sub(r'/\*[\s\S]*?\*/', '', css)
    if re.search(r'@import\b|\b(?:image-set|-webkit-image-set)\s*\(', css, re.I):
        return True
    # SVG marker references such as url(#arrow) stay inside the document.
    # Reject every other URL, including malformed url() expressions.
    for match in re.finditer(r'\burl\s*\(([^)]*)(\)|$)', css, re.I):
        target = match[1].strip().strip('\"\'')
        if match[2] != ')' or not re.fullmatch(r'#[A-Za-z_][\w.-]*', target):
            return True
    return False


def check_resources(source, name, packaged=None, allow_entry_refresh=False):
    """Allow navigation links, but require reading pages to embed their resources."""
    document = Document(source)
    references, scripts = [], []
    for node in document.root.walk():
        attrs = node.attrs
        if node.tag == 'base':
            raise ValueError(name+': base changes relative link resolution')
        if any(k.lower().startswith('on') for k in attrs):
            raise ValueError(name+': inline event-handler attribute')
        if node.tag == 'style' and css_dependencies(node.text()):
            raise ValueError(name+': CSS resource dependency')
        if 'style' in attrs and css_dependencies(attrs['style']):
            raise ValueError(name+': inline CSS resource dependency')
        if node.tag == 'meta' and attrs.get('http-equiv','').lower() == 'refresh':
            content = attrs.get('content','')
            if not (allow_entry_refresh and name == 'index.html' and
                    re.fullmatch(r'0\s*;\s*url=notes/book_overview\.html', content, re.I)):
                raise ValueError(name+': unexpected meta refresh')
            references.append('notes/book_overview.html')
        if node.tag in {'script','link','img','iframe','source','video','audio','object','embed','use'} and any(k in attrs for k in {'src','srcset','href','xlink:href','data','poster'}):
            raise ValueError(name+': reading resource is not embedded: '+node.tag)
        if 'href' in attrs:
            references.append(attrs['href'])
        if node.tag == 'script' and attrs.get('type','') in {'','module','text/javascript','application/javascript'}:
            scripts.append(node.text())
    for ref in references:
        url = urlsplit(ref)
        if url.scheme == 'file' or url.scheme in {'javascript','vbscript'}:
            raise ValueError(name+': nonportable or executable navigation URL')
        if url.scheme or url.netloc or not url.path:
            continue
        target = unquote(urlsplit(urljoin('https://static.example/'+name, ref)).path).lstrip('/')
        if packaged is not None and target not in packaged:
            raise ValueError(name+': link outside release: '+ref)
    return {'references': references, 'scripts': scripts}
