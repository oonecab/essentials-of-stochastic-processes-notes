"""Publish reader-facing navigation and static views of source documents."""
from datetime import datetime
from html import escape, unescape
import io
from pathlib import PurePosixPath
import json
import posixpath
import re
import zipfile
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

BOOKS = {'stochastic': 'Durrett · 随机过程', 'weiss': 'Weiss · 数据结构与算法',
         'csapp': 'CS:APP · 深入理解计算机系统', 'visual-group-theory': 'Carter · 视觉群论',
         'measure-probability': '程士宏 · 测度论与概率论基础'}
EXTERNAL_LINKS = {
    'https://epubs.siam.org/doi/10.1137/0206024': 'https://www.cs.jhu.edu/~misha/Spring23/Knuth77.pdf',
    'https://epubs.siam.org/doi/10.1137/0218001': 'https://www.dcs.gla.ac.uk/~pat/cpM/papers/GAC/SMJ000001%5B1%5D.pdf',
    'https://ntrs.nasa.gov/api/citations/20000115620/downloads/20000115620.pdf': 'https://nas.nasa.gov/assets/nas/pdf/techreports/2000/nas-00-003.pdf',
    'https://www.math.fau.edu/combinatorics/previous-years/20th-cgtc-entire-program-booklet.pdf': 'https://math.fau.edu/combinatorics/previous-years/20th-cgtc-entire-program-booklet.pdf',
}


def relative(source, target):
    return posixpath.relpath(target, posixpath.dirname(source))


def navigation(name):
    book = name.split('/')[0]
    home = relative(name, 'index.html').removesuffix('index.html')
    overview = relative(name, book + '/notes/book_overview.html')
    return (f'<nav class="reader-bar" aria-label="笔记阅读导航"><div class="reader-bar-inner">'
            f'<a class="reader-home" href="{home}" data-notes-home="true">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5 2 12l7 7M2 12h19"/></svg>'
            f'笔记首页</a><span class="reader-book">{BOOKS[book]}</span>'
            f'<div class="reader-bar-links"><a href="{overview}">全书地图</a>'
            '<a href="#top">页首 ↑</a></div></div></nav>')


def rewrite_link(name, href, views):
    url = urlsplit(unescape(href))
    if url.scheme or url.netloc:
        return EXTERNAL_LINKS.get(unescape(href), href)
    target = urlsplit(urljoin('https://notes.zzzping.top/' + name, unescape(href))).path.lstrip('/')
    if target in views:
        return relative(name, views[target]) + ('?' + url.query if url.query else '') + ('#' + url.fragment if url.fragment else '')
    return href


def transform_reading_page(blob, name, views, *, csapp_pdf_included=False):
    source = blob.decode('utf-8')
    if '<body>' not in source or 'reader-bar' in source:
        raise ValueError('Expected a canonical, untransformed reading page: ' + name)
    source = source.replace('</head>', f'<link rel="stylesheet" href="{relative(name, "reader.css")}"></head>', 1)
    source = source.replace('<body>', '<body class="portal-reader">' + navigation(name), 1)
    # Narrow-screen anchors sit below the home bar and the collapsed TOC.
    marker_threshold = ('wide.matches ? 110 : 144' if name.startswith('csapp/notes/')
                        else 'wide.matches ? 100 : 110')
    if source.count(marker_threshold) != 1:
        raise ValueError('Expected one TOC reading-position threshold: ' + name)
    source = source.replace(marker_threshold, 'wide.matches ? 100 : 132', 1)
    home = relative(name, 'index.html').removesuffix('index.html')
    marker = '<p class="chapter-nav">'
    source = source.replace(marker, marker + f'<a href="{home}" data-notes-home="true">笔记首页</a>', 1)
    before, footer = source.split('<footer>', 1)
    if marker not in footer:
        raise ValueError('Missing footer navigation: ' + name)
    footer = footer.replace(marker, marker + f'<a class="reader-footer-home" href="{home}" data-notes-home="true">← 笔记首页</a>', 1)
    source = before + '<footer>' + footer

    def update(match):
        tag = match[0]
        href = re.search(r'\bhref="([^"]*)"', tag)
        if not href or re.search(r'\bdownload(?:\s|=|>)', tag):
            return tag
        destination = rewrite_link(name, href[1], views)
        if destination != href[1]:
            tag = tag[:href.start(1)] + destination + tag[href.end(1):]
        elif urlsplit(unescape(href[1])).path.endswith(('.c', '.py')) and not urlsplit(href[1]).scheme:
            tag = tag[:-1] + ' download>'
        return tag
    source = re.sub(r'<a\b[^>]*>', update, source)
    if name.startswith('csapp/notes/') and not csapp_pdf_included:
        # Keep page references readable when this release omits the source PDF.
        source = re.sub(r'<a class="source-pdf" href="\.\./csapp\.pdf#page=\d+">([^<]*)</a>',
                        lambda m: '<span class="source-printed">' + m[1] + '</span>', source)
        if '../csapp.pdf' in source:
            raise ValueError('Unmarked CSAPP local-source link: ' + name)
    if name == 'stochastic/notes/book_overview.html':
        source = source.replace('>code 目录</a>', '>示例程序与运行说明</a>')
        source = source.replace('最终 HTML 中的代码是维护入口，校验脚本每次重新提取到临时目录。',
                                '可以先在正文理解算法，再下载源文件，按各章运行说明检查自己的计算。')
        pattern = r'<p>在项目根目录运行下面命令。.*?</code></pre>'
        replacement = ('<p>下载程序后，在自己的电脑上运行。Python 3 示例使用标准库；C 程序需要支持 C11 的编译器。'
                       '先从无需输入的泊松过程仿真开始，各章说明提供对应参数、输入示例与结果解释。</p>'
                       '<pre><code id="validation-commands" data-language="shell"># 下载 poisson.py 后运行 Python 示例\n'
                       'python3 poisson.py\n\n# 下载 poisson.c 后编译并运行 C 示例\n'
                       'clang -std=c11 -O2 poisson.c -lm -o poisson\n./poisson</code></pre>')
        source, count = re.subn(pattern, lambda _: replacement, source, flags=re.S)
        if count != 1:
            raise ValueError('Expected one overview command guide')
    return source.encode('utf-8')


def link(href, text, download=False):
    return f'<a href="{escape(href, quote=True)}"' + (' download' if download else '') + f'>{escape(str(text))}</a>'


def stats(items):
    return '<div class="doc-stats">' + ''.join(f'<div class="doc-stat"><strong>{escape(str(value))}</strong>{escape(label)}</div>' for value, label in items) + '</div>'


def table(headers, rows, wide=False):
    return ('<div class="doc-scroll"><table' + (' class="doc-wide"' if wide else '') + '><thead><tr>' +
            ''.join(f'<th scope="col">{escape(h)}</th>' for h in headers) + '</tr></thead><tbody>' +
            ''.join('<tr>' + ''.join('<td>' + value + '</td>' for value in row) + '</tr>' for row in rows) + '</tbody></table></div>')


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y年%m月%d日 %H:%M（北京时间）')


def document(name, title, intro, body, raw=None, recorded=None):
    overview = relative(name, name.split('/')[0] + '/notes/book_overview.html')
    home = relative(name, 'index.html').removesuffix('index.html')
    tools = link(overview, '返回全书地图')
    if raw:
        tools += link(relative(name, raw), '下载原始记录' if raw.endswith('.json') else '下载原始说明', True)
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(title)} · 读书笔记</title><link rel="icon" href="{relative(name, "favicon.svg")}" type="image/svg+xml">'
            f'<link rel="stylesheet" href="{relative(name, "reader.css")}"></head>'
            '<body class="portal-reader">' + navigation(name) + '<main class="portal-doc" id="top" tabindex="-1">'
            f'<header><p class="doc-kicker">{BOOKS[name.split("/")[0]]} / 阅读资料</p><h1>{escape(title)}</h1>'
            f'<p class="doc-intro">{escape(intro)}</p>' + (f'<p class="doc-meta">记录时间：{timestamp(recorded)}</p>' if recorded else '') +
            '<div class="doc-links">' + tools + '</div></header>' + body +
            '<footer><div class="doc-links">' + link(home, '← 笔记首页') + link(overview, '全书地图') + link('#top', '回到页首 ↑') + '</div></footer></main></body></html>').encode('utf-8')


def inline(text, name, views):
    pieces = re.split(r'(`[^`]+`|\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*)', text)
    output = []
    for piece in pieces:
        if piece.startswith('`') and piece.endswith('`'):
            output.append('<code>' + escape(piece[1:-1]) + '</code>')
        elif piece.startswith('**') and piece.endswith('**'):
            output.append('<strong>' + escape(piece[2:-2]) + '</strong>')
        elif re.fullmatch(r'\[[^\]]+\]\([^)]+\)', piece):
            match = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', piece)
            output.append(link(rewrite_link(name, match[2], views), match[1], urlsplit(match[2]).path.endswith(('.c', '.py'))))
        else:
            output.append(escape(piece))
    return ''.join(output)


def markdown(text, name, views):
    """Render the headings, paragraphs, lists, tables and fenced code in our READMEs."""
    lines = text.splitlines()
    output, paragraph, listing = [], [], []
    def flush():
        if paragraph:
            output.append('<p>' + inline(' '.join(paragraph), name, views) + '</p>'); paragraph.clear()
        if listing:
            output.append('<ul>' + ''.join('<li>' + inline(item, name, views) + '</li>' for item in listing) + '</ul>'); listing.clear()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith('```'):
            flush(); code = []; index += 1
            while index < len(lines) and not lines[index].startswith('```'):
                code.append(lines[index]); index += 1
            output.append('<pre><code>' + escape('\n'.join(code)) + '</code></pre>')
        elif line.startswith('# '):
            flush()  # The first heading is supplied by document().
        elif re.match(r'^#{2,6} ', line):
            flush(); depth = len(line.split(' ')[0]); level = min(depth, 3)
            output.append(f'<h{level}>' + inline(line[depth + 1:], name, views) + f'</h{level}>')
        elif line.startswith('|') and index + 1 < len(lines) and re.match(r'^\|[\s:|-]+\|$', lines[index + 1]):
            flush(); headers = [cell.strip() for cell in line.strip('|').split('|')]; rows = []; index += 2
            while index < len(lines) and lines[index].startswith('|'):
                rows.append([inline(cell.strip(), name, views) for cell in lines[index].strip('|').split('|')]); index += 1
            output.append(table(headers, rows, True)); continue
        elif re.match(r'^[-*] ', line):
            if paragraph: flush()
            listing.append(line[2:])
        elif not line.strip():
            flush()
        else:
            if listing: flush()
            paragraph.append(line)
        index += 1
    flush()
    return ''.join(output)


def build_reader_views(blobs):
    views = {'stochastic/code/README.md': 'stochastic/code/index.html',
             'weiss/notes/README.md': 'weiss/notes/reading_guide.html'}
    for name in blobs:
        if name.startswith('stochastic/code/') and name.endswith('/README.md'):
            views[name] = name.removesuffix('README.md') + 'index.html'
    for stem in ('source_manifest', 'review_manifest', 'validation'):
        views[f'stochastic/notes/{stem}.json'] = f'stochastic/notes/{stem}.html'
    if 'csapp/code/README.md' in blobs:
        views['csapp/code/README.md'] = 'csapp/code/index.html'
    if 'visual-group-theory/code/README.md' in blobs:
        views['visual-group-theory/code/README.md'] = 'visual-group-theory/code/index.html'
    if 'measure-probability/code/README.md' in blobs:
        views['measure-probability/code/README.md'] = 'measure-probability/code/index.html'
    generated = {}
    programs = json.loads(blobs['stochastic/code/programs.json'])['programs']
    index = 'stochastic/code/index.html'
    cards = []
    for program in programs:
        source = program['files']['c']
        directory = str(PurePosixPath(source).parent)
        buttons = [link(relative(index, 'stochastic/' + program['page']) + '#' + program['anchor'], '正文中的算法与代码'),
                   link(relative(index, 'stochastic/' + directory + '/index.html'), '本章运行说明')]
        buttons += [link(relative(index, 'stochastic/' + path), '下载 ' + {'c': 'C', 'python': 'Python'}[label], True) for label, path in program['files'].items()]
        cards.append('<article class="program-card"><p class="doc-kicker">第 ' + str(program['chapter']) + ' 章 / ' + escape(program['id']) +
                     '</p><h3>' + escape(program['title']) + '</h3><div class="doc-links">' + ''.join(buttons) + '</div></article>')
    body = stats([(7, '组算法示例'), (14, '份 C / Python 源文件'), (6, '章运行说明')])
    body += '<div class="doc-note"><p>' + link('examples.zip', '下载全部示例程序（ZIP）', True) + '</p><p class="small">包含六章源码、运行说明与 Makefile。解压后在包含 code 目录的文件夹运行各章命令，或用 <code>make -C code</code> 编译全部 C 程序。</p></div>'
    body += '<section id="programs"><h2>按章节选择程序</h2><div class="program-grid">' + ''.join(cards) + '</div></section>'
    body += ('<section id="run"><h2>从一次运行开始</h2><p>先下载第二章的 <code>poisson.py</code>，在保存文件的目录打开终端。'
             'Python 3 使用标准库，程序会输出指数间隔构造的泊松计数仿真及理论对照。</p>'
             '<pre><code>python3 poisson.py</code></pre><p>如果使用 C，下载同一组的 <code>poisson.c</code>，用支持 C11 的编译器编译。'
             '数学库通过 <code>-lm</code> 链接。</p><pre><code>clang -std=c11 -O2 poisson.c -lm -o poisson\n./poisson</code></pre>'
             '<div class="doc-note">第一章和第六章的一些程序需要从标准输入读取矩阵或金融模型参数。请使用对应章节运行说明中的完整输入示例。</div>'
             '<p>正文保留可展开的完整 C 与 Python 代码。读算法时关注模型和边界，运行程序时将输出与正文中的计算及实验记录对照。</p></section>')
    generated[index] = document(index, '示例程序与运行说明', '从正文中的算法出发，选择一组程序，在自己的电脑上复现实验或核对计算。', body, 'stochastic/code/README.md')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path, blob in sorted(blobs.items()):
            if path.startswith('stochastic/code/'):
                entry = zipfile.ZipInfo(path.removeprefix('stochastic/'), date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, blob)
    generated['stochastic/code/examples.zip'] = buffer.getvalue()
    for raw, name in views.items():
        if raw.endswith('.md') and raw != 'stochastic/code/README.md':
            text = blobs[raw].decode('utf-8'); title = text.splitlines()[0].removeprefix('# ')
            generated[name] = document(name, title, '按原有说明阅读运行方法、输入条件与对应的正文入口。', markdown(text, name, views), raw)
    source = json.loads(blobs['stochastic/notes/source_manifest.json'])
    review = json.loads(blobs['stochastic/notes/review_manifest.json'])
    validation = json.loads(blobs['stochastic/notes/validation.json'])
    files = {chapter['chapter']: PurePosixPath(chapter['file']).name for chapter in review['chapters']}
    name = views['stochastic/notes/source_manifest.json']
    rows = []
    for front in source['front_matter']:
        rows.append([link(front['file'], '序言'), escape(str(front['printed_start']) + '–' + str(front['printed_end'])),
                     link('../assets/essentials-of-stochastic-processes.pdf#page=' + str(front['pdf_start']), str(front['pdf_start']) + '–' + str(front['pdf_end'])), '—'])
    for chapter in source['chapters']:
        number = int(chapter['name'].replace('chapter', '')) if chapter['name'].startswith('chapter') else None
        if number in files:
            rows.append([link(files[number], '第 ' + str(number) + ' 章'), escape(str(chapter['printed_start']) + '–' + str(chapter['printed_end'])),
                         link('../assets/essentials-of-stochastic-processes.pdf#page=' + str(chapter['pdf_start']), str(chapter['pdf_start']) + '–' + str(chapter['pdf_end'])),
                         str(len(chapter.get('exercises', [])))])
        elif chapter['name'] == 'appendix_a':
            rows.append([link('appendix_a_probability_review.html', '附录 A · 概率论复习'), escape(str(chapter['printed_start']) + '–' + str(chapter['printed_end'])),
                         link('../assets/essentials-of-stochastic-processes.pdf#page=' + str(chapter['pdf_start']), str(chapter['pdf_start']) + '–' + str(chapter['pdf_end'])), '—'])
    body = stats([(source['pdf_pages'], '页原书 PDF'), (len(source['numbered_results']), '条编号定理、引理与定义'), (236, '道章节习题')])
    body += '<h2>版本与页码对应</h2><p>Richard Durrett，<i>Essentials of Stochastic Processes</i>，第三版（2016）。正文印刷页1对应 PDF 第10页，印刷空白页146与268未收录，因此后续页序偏移会改变。笔记中的原书链接使用实际 PDF 页序。</p>'
    body += table(['章节', '原书印刷页', '实际 PDF 页序', '习题数'], rows)
    body += '<h2>源文件指纹</h2><p class="small">SHA-256 用于确认 PDF 文件身份与换版后的差异。</p><p class="hash-value">' + escape(source['sha256']) + '</p>'
    generated[name] = document(name, '原书版本与页码', '查看各章的原书页码范围，或从目录直接打开笔记与对应 PDF。', body, 'stochastic/notes/source_manifest.json')
    name = views['stochastic/notes/review_manifest.json']
    data = review['statistics']
    body = stats([(data['exercises_reviewed'], '道习题复核记录'), (data['numbered_theorems_and_lemmas'], '条编号定理与引理'), (data['question_corrections'], '处题干核正')])
    body += '<section id="scope"><h2>怎样使用这份记录</h2><p>记录逐项核对题设、全部小问、边界和计算步骤；数学陈述按原书与论证核对，数值程序另用独立基准和实际运行检查。阅读时可以从下方题号回到解答，或打开对应的原书页面。</p></section>'
    body += '<section id="chapters"><h2>逐章与逐题定位</h2>'
    for chapter in review['chapters']:
        rows = []
        for exercise in chapter['exercise_review']:
            pages = exercise['source_pdf_pages']
            rows.append([link(files[chapter['chapter']] + '#' + exercise['anchor'], exercise['number']),
                         '、'.join(link('../assets/essentials-of-stochastic-processes.pdf#page=' + str(page), str(page)) for page in pages),
                         '题设与小问已对照' if exercise['statement_and_subparts_review'] == 'compared with source' else escape(exercise['statement_and_subparts_review']),
                         str(exercise['solution_steps']) + ' 步'])
        body += f'<details class="doc-details" id="review-chapter-{chapter["chapter"]}"><summary>第 {chapter["chapter"]} 章 · {len(rows)} 道习题</summary>'
        body += ''.join('<p>' + escape(finding) + '</p>' for finding in chapter['findings']) + table(['题号与解答', 'PDF 页', '题干复核', '解答展开'], rows, True) + '</details>'
    body += '</section><section id="corrections"><h2>重要校注</h2>'
    for correction in review['notable_corrections']:
        body += '<details class="doc-details"><summary>' + escape(correction['location']) + '</summary><p>' + escape(correction['correction']) + '</p>'
        body += '<div class="doc-links">' + ''.join(link('../assets/essentials-of-stochastic-processes.pdf#page=' + str(page), '原书 PDF 第 ' + str(page) + ' 页') for page in correction.get('pdf_pages', [])) + '</div></details>'
    body += '</section><p>' + link('validation.html', '查看程序与页面验证结果') + '</p>'
    generated[name] = document(name, '逐章与逐题校订记录', '按章节定位题设、解答及原书校注，了解每一类复核记录所依据的证据。', body, 'stochastic/notes/review_manifest.json', review['generated_at_utc'])
    name = views['stochastic/notes/validation.json']
    checks = validation['program_checks']
    body = stats([(checks['code_pairs'], '组 C / Python 程序'), (checks['numerical_fixtures'], '项独立数值基准'), (checks['invalid_inputs'], '组非法输入检查')])
    labels = {'balanced_html':'HTML 结构','formula_conversion':'静态公式转换','annotation_bindings':'阅读注解定位','numbered_source_coverage':'编号陈述覆盖','source_html_consistency':'源码与网页代码一致','pdf_links':'PDF 链接','c11_strict':'严格 C11 编译','asan_ubsan':'内存与未定义行为检查','python':'Python 实际运行','cross_language':'C / Python 输出对照','content_regressions':'已知内容问题回归','tooling_regressions':'检查工具回归'}
    body += '<h2>程序与结构检查</h2>' + table(['检查项目','已记录的结果'], [[escape(label), '<span class="status-pass">通过</span>' if checks.get(key)=='pass' else escape(str(checks.get(key,'未记录')))] for key,label in labels.items()])
    browser = validation['browser_checks']
    body += '<h2>页面与浏览器检查</h2><p>记录包含 ' + '、'.join(str(width) + 'px' for width in browser['widths']) + ' 宽度下的页面检查，以及目录定位、习题深链接、代码展开和阅读注解的交互。</p>'
    body += '<div class="doc-note">这些结果记录有限输入、数值基准和实际浏览器操作的表现。完整题干与数学论证的依据见逐章校订记录。</div><div class="doc-links">' + link('review_manifest.html', '逐章校订记录') + link('source_manifest.html', '原书版本与页码') + '</div>'
    generated[name] = document(name, '程序与页面验证结果', '用清晰的检查项目查看已有验证结果，并区分数值运行、页面功能与数学内容的复核依据。', body, 'stochastic/notes/validation.json', validation['generated_at_utc'])
    if 'csapp/code/README.md' in blobs:
        name = views['csapp/code/README.md']
        text = blobs['csapp/code/README.md'].decode().split('## 校验', 1)[0]
        generated[name] = document(name, '教学程序与运行说明',
            '选择一组程序，复现位表示、地址布局、流水线时间、归约或缓存计算。',
            markdown(text, 'csapp/code/README.md', views), 'csapp/code/README.md')
    if 'visual-group-theory/code/README.md' in blobs:
        raw = 'visual-group-theory/code/README.md'
        name = views[raw]
        text = blobs[raw].decode().split('## 校验', 1)[0]
        generated[name] = document(name, '从群动作到 Galois 理论的程序',
            '从位置交换、Cayley 图与运算表，到 Sylow 子群与分裂域的精确自同构，复现十组 C11/Python 程序。',
            markdown(text, raw, views), raw)
    if 'measure-probability/code/README.md' in blobs:
        raw = 'measure-probability/code/README.md'
        name = views[raw]
        text = blobs[raw].decode().split('## 校验', 1)[0]
        generated[name] = document(name, '集合、积分与条件期望程序',
            '用三组 C11/Python 程序连接可测结构、简单函数逼近、积分、测度分解与条件均值。',
            markdown(text, raw, views), raw)
    return generated, views
