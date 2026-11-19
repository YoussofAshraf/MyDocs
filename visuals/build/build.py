#!/usr/bin/env python3
"""Build animated HTML explainer pages for every illustrated Markdown file.

For each .md file with Mermaid or ASCII diagrams, writes visuals/<same path>.html:
- Mermaid blocks are rendered to SVG once with the pinned mermaid-cli (cached by hash),
  then tagged with per-element timing so CSS @keyframes can build them up in order.
- ASCII blocks become a line-by-line reveal with highlighted arrows and ✅/❌ marks.
- Each figure is paired with the chapter prose around it and a step list that
  lights up in sync with the animation.

Usage:  cd visuals/build && npm install && python3 build.py
"""
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import markdown

BUILD = Path(__file__).resolve().parent
VIS = BUILD.parent
REPO = VIS.parent
CACHE = BUILD / '.cache'
MMDC = BUILD / 'node_modules' / '.bin' / 'mmdc'

ART = re.compile(r'[─│┌┐└┘├┤┬┴┼▶◀▼▲►◄→←↓↑↔═║╔╗╚╝]')
FENCE = re.compile(r'^```(\S*)\s*$')

TOPICS = {
    'docker-foundations-to-advanced': ('🐳', 'Docker'),
    'kafka-foundations-to-advanced': ('🪵', 'Kafka'),
    'kubernetes-foundations-to-advanced': ('☸️', 'Kubernetes'),
    'rabbitmq-foundations-to-advanced': ('🐰', 'RabbitMQ'),
    'practicals': ('🎓', 'Practicals'),
}


# ---------------------------------------------------------------- markdown parsing
def parse_blocks(text):
    """Split Markdown into heading / code / text blocks (top level only)."""
    blocks, buf, lines, i = [], [], text.split('\n'), 0

    def flush():
        chunk = '\n'.join(buf).strip()
        if chunk:
            blocks.append({'kind': 'text', 'md': chunk})
        buf.clear()

    while i < len(lines):
        line = lines[i]
        m = FENCE.match(line)
        if m:
            flush()
            lang, body, i = m.group(1), [], i + 1
            while i < len(lines) and not lines[i].startswith('```'):
                body.append(lines[i])
                i += 1
            blocks.append({'kind': 'code', 'lang': lang, 'code': '\n'.join(body)})
        elif re.match(r'^#{1,4} ', line):
            flush()
            level = len(line) - len(line.lstrip('#'))
            blocks.append({'kind': 'heading', 'level': level, 'title': line[level:].strip()})
        else:
            buf.append(line)
        i += 1
    flush()
    return blocks


def is_illustration(b):
    if b['kind'] != 'code':
        return False
    if b['lang'] == 'mermaid':
        return True
    return b['lang'] == '' and bool(ART.search(b['code']))


def strip_nav(md):
    return '\n'.join(l for l in md.split('\n') if not re.match(r'^\s*\[← ', l)).strip()


# ---------------------------------------------------------------- mermaid rendering
def render_mermaid(codes):
    """Render every Mermaid source once; return {sha: svg_text}."""
    CACHE.mkdir(exist_ok=True)
    out, todo = {}, []
    for code in codes:
        sha = hashlib.sha256(code.encode()).hexdigest()[:16]
        p = CACHE / f'{sha}.svg'
        if p.exists():
            out[sha] = p.read_text()
        elif sha not in [s for s, _ in todo]:
            todo.append((sha, code))
    if todo:
        if not MMDC.exists():
            sys.exit('mermaid-cli missing: run `npm install` in visuals/build first')
        work = CACHE / 'batch'
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir()
        src = '\n\n'.join(f'```mermaid\n{c}\n```' for _, c in todo)
        (work / 'in.md').write_text(src)
        print(f'rendering {len(todo)} Mermaid diagram(s)…')
        subprocess.run([str(MMDC), '-q', '-p', str(BUILD / 'puppeteer.json'),
                        '-c', str(BUILD / 'mermaid.json'), '-b', 'transparent',
                        '-i', str(work / 'in.md'), '-o', str(work / 'out.md')], check=True)
        for n, (sha, _) in enumerate(todo, 1):
            svg = (work / f'out-{n}.svg').read_text()
            (CACHE / f'{sha}.svg').write_text(svg)
            out[sha] = svg
        shutil.rmtree(work)
    return out


def text_of(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def add_attr(svg, el_id, attrs):
    """Append attributes to the opening tag that carries id=el_id."""
    pat = re.compile(r'(<[a-zA-Z]+[^>]*?\sid="%s")' % re.escape(el_id))
    return pat.sub(lambda m: m.group(1) + attrs, svg, count=1)


def set_style_var(svg, el_id, var, value):
    pat = re.compile(r'(<[a-zA-Z]+)([^>]*?\sid="%s"[^>]*?)(/?>)' % re.escape(el_id))

    def fix(m):
        tag = m.group(2)
        if ' style="' in tag:
            tag = tag.replace(' style="', f' style="{var}:{value};', 1)
        else:
            tag += f' style="{var}:{value}"'
        return m.group(1) + tag + m.group(3)

    return pat.sub(fix, svg, count=1)


def tag_sequence(svg, idx, positions):
    """Tag messages and notes by vertical position (Mermaid draws notes before messages in the DOM)."""
    tag_re = re.compile(r'<(text|line|path|rect)\b[^>]*?class="(messageText|messageLine[01]|note|noteText)"[^>]*?/?>')
    found = []
    for m in tag_re.finditer(svg):
        tag, kind = m.group(0), m.group(2)
        ym = re.search(r'\sy1?="([\d.-]+)"', tag)
        y = float(ym.group(1)) if ym else 0.0
        hm = re.search(r'\sheight="([\d.-]+)"', tag)
        found.append({'m': m, 'kind': kind, 'y': y, 'h': float(hm.group(1)) if hm else 0.0})
    events = sorted((f for f in found if f['kind'] in ('messageText', 'note')), key=lambda f: f['y'])
    for n, ev in enumerate(events):
        ev['step'] = n
    for f in found:
        if f['kind'].startswith('messageLine'):
            above = [e for e in events if e['kind'] == 'messageText' and e['y'] <= f['y'] + 1]
            f['step'] = max(above, key=lambda e: e['y'])['step'] if above else 0
        elif f['kind'] == 'noteText':
            box = [e for e in events if e['kind'] == 'note' and e['y'] - 1 <= f['y'] <= e['y'] + e['h'] + 1]
            f['step'] = box[0]['step'] if box else 0
    out, pos, dots = [], 0, []
    for f in sorted(found, key=lambda f: f['m'].start()):
        m, tag = f['m'], f['m'].group(0)
        t = positions(f.get('step', 0))
        close = 2 if tag.endswith('/>') else 1
        if ' style="' in tag:
            new = tag.replace(' style="', f' style="--t:{t:.2f};', 1)
        else:
            new = tag[:-close] + f' style="--t:{t:.2f}"' + tag[-close:]
        if f['kind'].startswith('messageLine'):
            new = new.replace('<' + m.group(1), '<' + m.group(1) + ' pathLength="1"', 1)
            c = re.search(r'x1="([\d.-]+)" y1="([\d.-]+)" x2="([\d.-]+)" y2="([\d.-]+)"', tag)
            if c:
                x1, y1, x2, y2 = c.groups()
                dots.append(f'<circle class="pkt seq" r="5" style="--t:{t:.2f};offset-path:path(\'M {x1} {y1} L {x2} {y2}\')"/>')
        out.append(svg[pos:m.start()])
        out.append(new)
        pos = m.end()
    out.append(svg[pos:])
    svg = ''.join(out)
    return svg.replace('</svg>', ''.join(dots) + '</svg>', 1) if dots else svg


SEQ_ARROW = re.compile(r'^\s*([^\s:>-][^:>]*?)\s*(-{1,2}(?:>>|>|x|\)))\s*[+-]?\s*([^:]+?)\s*:\s*(.*)$')


def sequence_steps(code):
    names, steps = {}, []
    for line in code.split('\n'):
        s = line.strip()
        m = re.match(r'^(participant|actor)\s+(\S+)(?:\s+as\s+(.+))?$', s)
        if m:
            names[m.group(2)] = m.group(3) or m.group(2)
            continue
        m = re.match(r'^Note\s+(?:over|left of|right of)\s+([^:]+):\s*(.*)$', s, re.I)
        if m:
            who = ', '.join(names.get(w.strip(), w.strip()) for w in m.group(1).split(','))
            steps.append(('note', who, '', m.group(2)))
            continue
        m = SEQ_ARROW.match(s)
        if m and not s.startswith(('loop', 'alt', 'opt', 'par', 'rect', 'critical', 'else')):
            a, arrow, b, msg = m.groups()
            kind = 'reply' if arrow.startswith('--') else 'call'
            steps.append((kind, names.get(a, a), names.get(b, b), msg))
    return steps


def br(s):
    return html.escape(re.sub(r'<br\s*/?>', ' ', s))


def animate_mermaid(svg, code, idx):
    """Return (svg_markup, steps[(t, html)], total_seconds, kind)."""
    svg = re.sub(r'<\?xml[^>]*>', '', svg).strip()
    old_id = re.search(r'<svg[^>]*\sid="([^"]+)"', svg).group(1)
    new_id = f'mm{idx}'
    svg = svg.replace(old_id, new_id)
    vb = re.search(r'viewBox="[\d.-]+ [\d.-]+ ([\d.]+)', svg)
    if vb:  # natural width, so narrow screens scroll the stage instead of shrinking the text
        svg = svg.replace('<svg ', f'<svg data-w="{float(vb.group(1)):.0f}" ', 1)
    kind = code.strip().split()[0]
    steps = []

    if kind == 'sequenceDiagram':
        STEP = 1.0
        svg = tag_sequence(svg, idx, lambda s: 0.4 + s * STEP)
        for n, (k, a, b, msg) in enumerate(sequence_steps(code)):
            t = 0.4 + n * STEP
            if k == 'note':
                steps.append((t, f'📝 <b>{br(a)}</b>: {br(msg)}'))
            else:
                arrow = '⇠' if k == 'reply' else '→'
                steps.append((t, f'<b>{br(a)}</b> {arrow} <b>{br(b)}</b>: {br(msg)}'))
        total = 0.4 + max(len(steps), 1) * STEP
        return svg, steps, total, kind

    ns = {'s': 'http://www.w3.org/2000/svg'}
    try:
        root = ET.fromstring(re.sub(r'<br\s*/?>', ' ', svg))
    except ET.ParseError:
        return svg, [], 0, kind

    nodes = {}  # mermaid id -> (element id, label)
    for g in root.iter('{http://www.w3.org/2000/svg}g'):
        cls, gid = g.get('class', ''), g.get('id', '')
        if cls.startswith('node') and gid:
            m = re.match(rf'{new_id}-(?:flowchart-)?(.+?)-\d+$', gid)
            key = m.group(1) if m else gid
            if gid.startswith(f'{new_id}-state-'):
                key = gid[len(new_id) + 7:].rsplit('-', 1)[0]
            nodes[key] = (gid, text_of(g) or key)

    edges = []
    for p in root.iter('{http://www.w3.org/2000/svg}path'):
        cls = p.get('class', '')
        if 'flowchart-link' in cls or 'transition' in cls.split():
            edges.append(p)
    labels = [g for g in root.iter('{http://www.w3.org/2000/svg}g') if g.get('class') == 'edgeLabel']

    def endpoints(eid):
        m = re.match(rf'{new_id}-L_(.+)_\d+$', eid or '')
        if not m:
            return None, None
        body = m.group(1)
        for a in sorted(nodes, key=len, reverse=True):
            if body.startswith(a + '_') and body[len(a) + 1:] in nodes:
                return a, body[len(a) + 1:]
        return None, None

    # choreography: walk edges in definition order on one clock
    clock, node_t, edge_plan = 0.3, {}, []
    for e in edges:
        a, b = endpoints(e.get('id'))
        if a and a not in node_t:
            node_t[a] = clock
            clock += 0.35
        t = clock
        clock += 0.65
        if b and b not in node_t:
            node_t[b] = clock
            clock += 0.15
        edge_plan.append((e, a, b, t))
    for k in nodes:  # nodes without edges appear first
        node_t.setdefault(k, 0.1)
    total = clock
    scale = min(1.0, 14.0 / total) if total else 1.0
    if not edges:  # e.g. state diagram without parsable ids: stagger in DOM order
        for n, k in enumerate(nodes):
            node_t[k] = 0.2 + n * 0.4
        total = 0.2 + len(nodes) * 0.4

    for k, (gid, _) in nodes.items():
        svg = set_style_var(svg, gid, '--t', f'{node_t[k] * scale:.2f}')

    dots, src_lines = [], code
    state_pairs = re.findall(r'^\s*(\[\*\]|[\w.]+)\s*-->\s*(\[\*\]|[\w.]+)\s*(?::\s*(.*))?$', src_lines, re.M)
    for n, (e, a, b, t) in enumerate(edge_plan):
        t *= scale
        eid = e.get('id')
        dotted = 'dotted' in e.get('class', '') or 'dashed' in e.get('class', '')
        if eid:
            svg = set_style_var(svg, eid, '--t', f'{t:.2f}')
            if not dotted:
                svg = add_attr(svg, eid, ' pathLength="1"')
            d = e.get('d', '')
            if d:
                dots.append((eid, f'<circle class="pkt" r="4.5" style="--t:{t:.2f};offset-path:path(\'{d}\')"/>'))
        lab = text_of(labels[n]) if n < len(labels) else ''
        if kind.startswith('state') and n < len(state_pairs):
            sa, sb, sl = state_pairs[n]
            a_txt, b_txt = ('●' if sa == '[*]' else sa), ('◉' if sb == '[*]' else sb)
            lab = re.sub(r'<br\s*/?>', ' ', sl) if sl else lab
        else:
            a_txt = nodes[a][1] if a in nodes else '…'
            b_txt = nodes[b][1] if b in nodes else '…'
        arrow = '⇢' if dotted else '→'
        steps.append((t, f'<b>{html.escape(a_txt)}</b> {arrow} <b>{html.escape(b_txt)}</b>'
                         + (f' <span class="lbl">{html.escape(lab)}</span>' if lab else '')))

    # edge labels appear with their edge
    lab_iter = iter([t * scale for _, _, _, t in edge_plan])

    def lab_fix(m):
        t = next(lab_iter, 0.0)
        return m.group(0)[:-1] + f' style="--t:{t + 0.35:.2f}">'

    svg = re.sub(r'<g class="edgeLabel"[^>]*>', lab_fix, svg)
    # packets travel inside the same group as their edge so coordinates match
    for eid, dot in dots:
        svg = re.sub(r'(<path[^>]*\sid="%s"[^>]*/>)' % re.escape(eid), lambda m: m.group(1) + dot, svg, count=1)
    return svg, steps, total * scale, kind


# ---------------------------------------------------------------- ASCII reveal
GLYPHS = [
    (re.compile(r'[→←↓↑↔▶◀▼▲►◄]+|─+>|<─+|-->|<--|=>'), 'ar'),
    (re.compile(r'✅|✔️?'), 'ok'),
    (re.compile(r'❌|✗'), 'no'),
    (re.compile(r'⚠️?'), 'warn'),
    (re.compile(r'[─│┌┐└┘├┤┬┴┼═║╔╗╚╝]+'), 'bx'),
]


def ascii_line(line):
    spans, pos = [], 0
    hits = []
    for rx, cls in GLYPHS:
        for m in rx.finditer(line):
            hits.append((m.start(), m.end(), cls))
    hits.sort()
    taken = -1
    for s, e, cls in hits:
        if s < taken:
            continue
        spans.append(html.escape(line[pos:s]))
        spans.append(f'<span class="{cls}">{html.escape(line[s:e])}</span>')
        pos = taken = e
    spans.append(html.escape(line[pos:]))
    return ''.join(spans)


def animate_ascii(code):
    lines = code.split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    STEP = min(0.22, 6.0 / max(len(lines), 1))
    out, steps = [], []
    for n, line in enumerate(lines):
        t = 0.2 + n * STEP
        out.append(f'<span class="ln" style="--t:{t:.2f}">{ascii_line(line) or " "}</span>')
    # step list: lines that carry an annotation (← …) or a verdict
    for n, line in enumerate(lines):
        note = re.search(r'(?:←|<-)\s+(.+)$', line)
        if note and len(note.group(1).strip()) > 3:
            steps.append((0.2 + n * STEP, html.escape(note.group(1).strip())))
    total = 0.2 + len(lines) * STEP
    return '<pre class="ascii">' + ''.join(out) + '</pre>', steps[:12], total


# ---------------------------------------------------------------- page assembly
MD = markdown.Markdown(extensions=['tables', 'fenced_code', 'sane_lists'])


def md_html(text, link_fix):
    MD.reset()
    h = MD.convert(text)
    return re.sub(r'href="([^"#:]+\.md)(#[^"]*)?"', lambda m: f'href="{link_fix(m.group(1))}"', h)


READ_HINT = {
    'flowchart': 'Boxes light up as the flow reaches them and each arrow draws in the order the guide defines it. Glowing dots keep running along the arrows to show which way things move.',
    'graph': 'Boxes light up as the flow reaches them and each arrow draws in the order the guide defines it. Glowing dots keep running along the arrows to show which way things move.',
    'sequenceDiagram': 'Read it top to bottom: each message is sent in turn, and a dot travels from the sender to the receiver. Dashed lines are replies.',
    'stateDiagram-v2': 'States appear one after another and each transition draws in order. ● is the start and ◉ is the end.',
    'ascii': 'The drawing is revealed line by line. Arrows pulse, and ✅ / ❌ marks pop in to show the verdicts.',
}

KIND_LABEL = {'flowchart': 'Flow', 'graph': 'Flow', 'sequenceDiagram': 'Sequence',
              'stateDiagram-v2': 'State machine', 'ascii': 'Diagram'}


def clean_heading(t):
    return re.sub(r'\s+', ' ', t).strip()


def inline_md(t):
    """Heading text -> safe inline HTML (code, bold, italics), links dropped."""
    t = html.escape(clean_heading(t))
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    return re.sub(r'(?<![\w*])\*([^*]+)\*(?![\w*])', r'<i>\1</i>', t)


def page_for(md_path, rel_out, pages, svgs, fig_counter):
    text = md_path.read_text()
    blocks = parse_blocks(text)
    out_dir = (VIS / rel_out).parent
    src_dir = md_path.parent

    def link_fix(target):
        tgt = (src_dir / target).resolve()
        rel = tgt.relative_to(REPO) if tgt.is_relative_to(REPO) else None
        if rel and str(rel) in pages:
            return os.path.relpath(VIS / pages[str(rel)], out_dir)
        return os.path.relpath(tgt, out_dir)

    title = next((b['title'] for b in blocks if b['kind'] == 'heading' and b['level'] == 1), md_path.stem)
    level = next((e for e in ('🟢', '🟡', '🔴') if e in title), '')
    nav = re.search(r'^\s*(\[← .*)$', text, re.M)
    nav_html = ''
    if nav:
        nav_html = md_html(nav.group(1), link_fix).replace('<p>', '').replace('</p>', '')
    figs, h2, h3 = [], '', ''
    for i, b in enumerate(blocks):
        if b['kind'] == 'heading':
            if b['level'] == 2:
                h2, h3 = b['title'], ''
            elif b['level'] >= 3:
                h3 = b['title']
            continue
        if not is_illustration(b):
            continue
        before, after = [], []
        j = i - 1
        while j >= 0 and blocks[j]['kind'] == 'text':
            before.insert(0, strip_nav(blocks[j]['md']))
            j -= 1
        j = i + 1
        while j < len(blocks) and blocks[j]['kind'] == 'text':
            after.append(blocks[j]['md'])
            j += 1
        # a text block shared by two figures is shown with the first one only
        prev_fig = figs[-1] if figs else None
        if prev_fig and prev_fig['after_idx'] and i - 1 in prev_fig['after_idx']:
            before = []
        fig_counter[0] += 1
        n = fig_counter[0]
        if b['lang'] == 'mermaid':
            sha = hashlib.sha256(b['code'].encode()).hexdigest()[:16]
            body, steps, total, kind = animate_mermaid(svgs[sha], b['code'], n)
            w = re.search(r'data-w="(\d+)"', body)
            stage = f'<div class="stage mermaid" style="--w:{w.group(1) if w else 600}px">{body}</div>'
        else:
            body, steps, total = animate_ascii(b['code'])
            kind = 'ascii'
            stage = f'<div class="stage">{body}</div>'
        figs.append({
            'h2': h2, 'h3': h3, 'stage': stage, 'steps': steps, 'total': total, 'kind': kind,
            'before': md_html('\n\n'.join(x for x in before if x), link_fix),
            'after': md_html('\n\n'.join(after), link_fix),
            'after_idx': set(range(i + 1, j)),
        })

    css = os.path.relpath(VIS / 'assets' / 'visuals.css', out_dir)
    js = os.path.relpath(VIS / 'assets' / 'visuals.js', out_dir)
    home = os.path.relpath(VIS / 'index.html', out_dir)
    src_link = os.path.relpath(md_path, out_dir)
    topic = rel_out.split('/')[0]
    emoji, tname = TOPICS.get(topic, ('📘', topic))
    guide_idx = pages.get(f'{topic}/README.md')
    crumbs = f'<a href="{home}">All guides</a>'
    if guide_idx and str(md_path.relative_to(REPO)) != f'{topic}/README.md':
        crumbs += f' <span>›</span> <a href="{os.path.relpath(VIS / guide_idx, out_dir)}">{emoji} {tname}</a>'

    toc = ''.join(
        f'<li><a href="#fig-{k + 1}"><span class="num">{k + 1}</span>{inline_md(f["h3"] or f["h2"]) or "Overview"}</a></li>'
        for k, f in enumerate(figs))

    cards = []
    for k, f in enumerate(figs):
        head = clean_heading(f['h2']) or 'Overview'
        sub = f'<p class="sub">{inline_md(f["h3"])}</p>' if f['h3'] else ''
        steps = ''
        if f['steps']:
            items = ''.join(f'<li style="--t:{t:.2f}">{s}</li>' for t, s in f['steps'])
            steps = f'<div class="steps"><h4>Step by step</h4><ol>{items}</ol></div>'
        prose = f['before'] + f['after']
        explain = f'<div class="prose">{prose}</div>' if prose.strip() else ''
        cards.append(f'''
<section class="fig play" id="fig-{k + 1}" data-kind="{f["kind"]}" style="--total:{f["total"]:.2f}">
  <header class="fig-head">
    <div><span class="tag">{KIND_LABEL.get(f["kind"], "Diagram")} · {k + 1}/{len(figs)}</span>
    <h2>{inline_md(head)}</h2>{sub}</div>
    <div class="ctl" role="group" aria-label="Animation controls">
      <button class="replay" type="button" title="Replay">↻ Replay</button>
      <button class="pause" type="button" title="Pause or resume">⏸</button>
      <select class="speed" aria-label="Speed"><option value="2">0.5×</option><option value="1" selected>1×</option><option value="0.5">2×</option></select>
    </div>
  </header>
  {f["stage"]}
  <div class="progress"><span></span></div>
  <p class="hint">👀 {READ_HINT.get(f["kind"], READ_HINT["flowchart"])}</p>
  <div class="explain">{explain}{steps}</div>
</section>''')

    t_clean = re.sub(r'\s*[🟢🟡🔴]\s*$', '', title)
    desc = f'{len(figs)} animated illustration{"s" if len(figs) != 1 else ""} from {md_path.relative_to(REPO)}'
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(t_clean)} · Visual</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="stylesheet" href="{css}">
</head>
<body>
<header class="top">
  <nav class="crumbs">{crumbs}</nav>
  <h1>{html.escape(title)}</h1>
  <p class="meta">{desc} · <a href="{src_link}">read the Markdown</a>{" · " + {"🟢": "Beginner", "🟡": "Intermediate", "🔴": "Advanced"}[level] if level else ""}</p>
  {f'<nav class="chapnav">{nav_html}</nav>' if nav_html else ''}
  <ol class="toc">{toc}</ol>
</header>
<main>{"".join(cards)}</main>
<footer class="bottom">{f'<nav class="chapnav">{nav_html}</nav>' if nav_html else ''}</footer>
<script src="{js}"></script>
</body>
</html>
'''
    return page, title, len(figs)


def chapters_from_readme(md_path):
    rows = []
    for m in re.finditer(r'^\|\s*(\d+)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|', md_path.read_text(), re.M):
        rows.append({'num': m.group(1), 'title': m.group(2), 'file': m.group(3),
                     'level': m.group(4).strip(), 'learn': m.group(5).strip()})
    return rows


def main():
    sources = sorted(p for p in REPO.glob('**/*.md')
                     if not any(part in ('node_modules', 'labs', 'visuals', '.git', '.claude') for part in p.relative_to(REPO).parts)
                     and p.name != 'CLAUDE.md')
    illustrated, all_mermaid = [], []
    for p in sources:
        bl = [b for b in parse_blocks(p.read_text()) if is_illustration(b)]
        if bl:
            illustrated.append(p)
            all_mermaid += [b['code'] for b in bl if b['lang'] == 'mermaid']
    svgs = render_mermaid(all_mermaid)

    pages = {}
    for p in illustrated:
        rel = p.relative_to(REPO)
        name = 'index.html' if p.name == 'README.md' else p.stem + '.html'
        pages[str(rel)] = str(rel.parent / name)

    summary = []
    counter = [0]
    for p in illustrated:
        rel = str(p.relative_to(REPO))
        out = VIS / pages[rel]
        out.parent.mkdir(parents=True, exist_ok=True)
        html_text, title, nfig = page_for(p, pages[rel], pages, svgs, counter)
        if p.name == 'README.md':
            html_text = html_text.replace('</main>', guide_grid(p, pages, out.parent) + '</main>')
        out.write_text(html_text)
        summary.append((rel, pages[rel], title, nfig))
        print(f'{nfig:3d} figs  {pages[rel]}')
    write_home(summary, pages)
    print(f'{len(summary)} pages, {sum(s[3] for s in summary)} figures → {VIS}')


def guide_grid(readme, pages, out_dir):
    rows = chapters_from_readme(readme)
    if not rows:
        return ''
    cards = []
    for r in rows:
        key = str((readme.parent / r['file']).relative_to(REPO))
        href = os.path.relpath(VIS / pages[key], out_dir) if key in pages else os.path.relpath(readme.parent / r['file'], out_dir)
        cards.append(f'<a class="chap" href="{href}"><span class="num">{r["num"]}</span>'
                     f'<b>{html.escape(r["title"])}</b><span class="lvl">{html.escape(r["level"])}</span>'
                     f'<small>{html.escape(re.sub(r"`", "", r["learn"]))}</small></a>')
    return f'<section class="grid-wrap"><h2>📚 Chapters</h2><div class="grid">{"".join(cards)}</div></section>'


def write_home(summary, pages):
    groups = {}
    for rel, out, title, nfig in summary:
        groups.setdefault(rel.split('/')[0], []).append((rel, out, title, nfig))
    sections = []
    for topic, items in groups.items():
        emoji, name = TOPICS.get(topic, ('📘', topic))
        items.sort(key=lambda x: (not x[0].endswith('README.md'), x[0]))
        lis = ''.join(
            f'<a class="chap" href="{o}"><span class="num">{"★" if r.endswith("README.md") else Path(r).stem[:2]}</span>'
            f'<b>{html.escape(re.sub(r"^\d+ · ", "", t))}</b><small>{n} animated figure{"s" if n != 1 else ""}</small></a>'
            for r, o, t, n in items)
        sections.append(f'<section class="grid-wrap"><h2>{emoji} {html.escape(name)}</h2><div class="grid">{lis}</div></section>')
    total = sum(s[3] for s in summary)
    (VIS / 'index.html').write_text(f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Animated Study Guides</title>
<meta name="description" content="Animated walkthroughs of every illustration in the guides.">
<link rel="stylesheet" href="assets/visuals.css">
</head>
<body>
<header class="top hero">
  <h1>🎬 Animated Study Guides</h1>
  <p class="meta">{total} illustrations from {len(summary)} Markdown files, rebuilt as step-by-step animations. Each figure comes with the guide's own explanation, and every page links back to its source chapter.</p>
  <div class="demo" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
</header>
<main>{"".join(sections)}</main>
</body>
</html>
''')


if __name__ == '__main__':
    main()
