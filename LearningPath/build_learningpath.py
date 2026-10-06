#!/usr/bin/env python3
"""Build the learning path pages from learningpath_source.txt.

Writes the pages into the folder learningpath/: LearningPath.html (overview, also saved as index.html)
and one page per chapter, LearningPath_ch1.html, ...

Usage:
    python3 build_learningpath.py            # build the page
    python3 build_learningpath.py --refresh  # also re-read the section list from the online notes

Source format (learningpath_source.txt):

    # Chapter title                 a chapter
    ## Block title                  a block of steps within the chapter
    > text                          learning goal of the block (optional)

    WATCH length | target | url | from | to
    READ target, target, ...
    DO target, target, ...
    NOTE
    (text on the following lines, until an empty line, describes the step)

    In any text: **bold** and [link text](address).

    Extra pages: a file page_<name>.txt in this folder (# title, ## headings, paragraphs, "- " lists)
    becomes LearningPath_<name>.html and is listed on the overview page.

    AI Short title                  a step in which the student works with an AI assistant

    CHECK                           self-check questions closing a block,
    - question                      one question per line starting with "- "

    BEFORE                          "Before you start" box, directly under the chapter title
    - item
    AFTER                           "After this chapter you can" box, at the end of the chapter
    - item

  - target is a section number of the notes (2.3.1) or an anchor of the notes
    (exercise-blood-pressure); it becomes a link to that place in the notes.
  - url is the address of the video, or just its Kaltura entry id (for example 1_lav8sk6t).
  - url, from and to are optional. from/to are times in the recording (mm:ss or h:mm:ss).
  - Put OPTIONAL in front of a step to mark it as optional.
  - Maths goes between dollar signs: $\\hat\\beta$.
"""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "learningpath_source.txt"
OUTPUT = "LearningPath"  # LearningPath.html and LearningPath_ch<N>.html
SITE = HERE / "learningpath"  # the folder with the finished pages: upload this folder as it is
CACHE = HERE / "notes_sections.json"
NOTES_URL = "https://othas.github.io/LIMO/"

HEADING = re.compile(
    r'<h[1-3]>(?:<span class="header-section-number">(.*?)</span>\s*)?(.*?)'
    r'<a href="#([^"]+)" class="anchor-section"',
    re.S,
)


def load_sections(refresh):
    """Map section numbers and anchors of the online notes to (anchor, title)."""
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    page = urllib.request.urlopen(NOTES_URL, timeout=60).read().decode("utf-8")
    sections = {}
    for number, title, anchor in HEADING.findall(page):
        title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        sections[anchor] = {"anchor": anchor, "title": title, "number": ""}
        if number:
            number = number.replace("Chapter", "").strip()
            sections[anchor]["number"] = number
            sections[number] = sections[anchor]
    CACHE.write_text(json.dumps(sections, indent=1, ensure_ascii=False), encoding="utf-8")
    return sections


def seconds(clock):
    total = 0
    for part in clock.split(":"):
        total = total * 60 + int(part)
    return total


KALTURA = ("https://cdnapisec.kaltura.com/p/2764431/sp/276443100/embedIframeJs/uiconf_id/45511891/"
           "partner_id/2764431?iframeembed=true&playerId=kaltura_player&entry_id=%s")


def video_url(url, start):
    """Let the recording start at the given time (Kaltura's st parameter, or {t} in the url)."""
    if re.fullmatch(r"\d_[a-z0-9]{8}", url):     # a Kaltura entry id instead of a full address
        url = KALTURA % url
    if not start:
        return url
    if "{t}" in url:
        return url.replace("{t}", str(seconds(start)))
    return url + ("&" if "?" in url else "?") + "st=" + str(seconds(start))


def text_html(text):
    """Escape text; $...$ becomes maths, **...** bold and [text](address) a link."""
    parts = text.split("$")
    out = []
    for i, part in enumerate(parts):
        part = html.escape(part, quote=False)
        if i % 2:
            out.append("\\(" + part + "\\)")
        else:
            part = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", part)
            part = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', part)
            out.append(part)
    return "".join(out)


def notes_link(target, sections, with_number=True):
    target = target.strip()
    if target not in sections:
        sys.exit("Unknown section or anchor in the notes: '%s'" % target)
    sec = sections[target]
    label = html.escape(sec["title"], quote=False)
    if sec["number"] and with_number:
        label = "Section " + sec["number"] + ": " + label
    return '<a href="%s#%s" target="_blank" rel="noopener">%s</a>' % (NOTES_URL, sec["anchor"], label)


def step_title(kind, args, sections):
    if kind in ("NOTE", "CHECK"):
        return ""
    if kind == "AI":
        return text_html(args)
    if kind == "WATCH":
        fields = [f.strip() for f in args.split("|")] + [""] * 4
        label, target, url, start, end = fields[:5]
        movie = "the video"
        if url:
            movie = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (
                html.escape(video_url(url, start)), movie)
        title = "Watch " + movie
        if label:
            title += " (%s)" % html.escape(label)
        if start and end:
            title += " (from %s to %s)" % (html.escape(start), html.escape(end))
        elif start:
            title += " (from %s)" % html.escape(start)
        if target:
            title += " on " + notes_link(target, sections)
        return title
    links = [notes_link(t, sections) for t in args.split(",") if t.strip()]
    verb = "Read" if kind == "READ" else "Make"
    return verb + " " + ", ".join(links)


STEP = re.compile(r"^(OPTIONAL\s+)?(WATCH|READ|DO|NOTE|CHECK|AI)\b\s*(.*)$")
BADGE = {"WATCH": "Watch", "READ": "Read", "DO": "Do", "NOTE": "Note", "CHECK": "Check", "AI": "AI"}
BOX = {"BEFORE": "Before you start", "AFTER": "After this chapter you can"}


def lines_html(lines):
    """Plain lines become a paragraph, lines starting with "- " a list."""
    text = " ".join(l for l in lines if not l.startswith("- "))
    items = [l[2:] for l in lines if l.startswith("- ")]
    out = "<p>%s</p>" % text_html(text) if text else ""
    if items:
        out += "<ul>%s</ul>" % "".join("<li>%s</li>" % text_html(i) for i in items)
    return out


def step_id(kind, args, block, used):
    """An id that stays the same when other steps are added or removed."""
    if kind == "WATCH":
        fields = [x.strip() for x in args.split("|")]
        what = fields[1] if len(fields) > 1 and fields[1] else fields[0]
    elif kind in ("NOTE", "CHECK"):
        what = block
    else:
        what = args
    sid = kind.lower() + "-" + re.sub(r"[^a-z0-9]+", "-", what.lower()).strip("-")
    used[sid] = used.get(sid, 0) + 1
    return sid if used[sid] == 1 else "%s-%d" % (sid, used[sid])


def build(sections):
    """Return the chapters as a list of dicts: title, key, body (html) and ids (of the steps)."""
    chapters = []
    body = used = None
    block = ""
    open_block = False

    def close_block():
        nonlocal open_block
        if open_block:
            body.append("</ol></section>")
            open_block = False

    for paragraph in SOURCE.read_text(encoding="utf-8").split("\n\n"):
        lines = [l.rstrip() for l in paragraph.strip().splitlines() if not l.startswith("//")]
        if not lines:
            continue
        first = lines[0]
        if first.startswith("# "):
            if chapters:
                close_block()
            m = re.search(r"Chapter\s+(\d+)", first)
            key = "ch" + (m.group(1) if m else str(len(chapters) + 1))
            body, used = [], {}
            chapters.append({"title": first[2:].strip(), "key": key, "body": body, "ids": []})
        elif body is None:
            sys.exit("The source file must start with a chapter title (# ...).")
        elif first.startswith("## "):
            close_block()
            block = first[3:].strip()
            body.append('<section class="block"><h3>%s</h3>' % text_html(block))
            goals = [l[1:].strip() for l in lines[1:] if l.startswith(">")]
            if goals:
                body.append('<p class="goal">%s</p>' % text_html(" ".join(goals)))
            body.append("<ol>")
            open_block = True
        elif first.strip() in BOX:
            close_block()
            body.append('<section class="box %s"><h3>%s</h3>%s</section>'
                        % (first.strip().lower(), BOX[first.strip()], lines_html(lines[1:])))
        else:
            m = STEP.match(first)
            if not m or not open_block:
                sys.exit("Cannot read this part of the source file:\n" + paragraph)
            optional, kind, args = m.groups()
            sid = step_id(kind, args, block, used)
            chapters[-1]["ids"].append(sid)
            title = "Check yourself" if kind == "CHECK" else step_title(kind, args, sections)
            body.append(
                '<li class="step %s%s"><input type="checkbox" id="%s" aria-label="done">'
                '<div><span class="badge">%s</span>%s%s%s</div></li>'
                % (kind.lower(), " optional" if optional else "", sid, BADGE[kind],
                   '<span class="opt">optional</span>' if optional else "",
                   '<span class="title">%s</span>' % title if title else "",
                   lines_html(lines[1:])))
    if chapters:
        close_block()
    return chapters


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script>
window.MathJax = {tex: {macros: {mb: ['\\boldsymbol{#1}', 1]}}};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>
:root { --bg:#fbfaf7; --card:#fff; --ink:#1f2328; --soft:#5b636d; --line:#e2dfd8; --accent:#a3123a;
        --watch:#1d5fa8; --read:#6a4c93; --do:#2f7d4f; --note:#7a6a3a; --check:#b3541e; --ai:#0e7c86; --tint:#f4efe6; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#16181b; --card:#1f2226; --ink:#e7e5e0; --soft:#a2a8b0; --line:#33373d; --accent:#f08aa5;
          --watch:#7fb3ee; --read:#c0a3e6; --do:#7fcf9c; --note:#d2c08a; --check:#f0a878; --ai:#6fd0d8; --tint:#262422; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
       font:17px/1.55 Georgia, "Times New Roman", serif; }
main { max-width: 820px; margin: 0 auto; padding: 32px 16px 64px; }
h1, h2, h3, .badge, .toc, .progress, .opt, button { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
h1 { font-size: 30px; margin: 0 0 4px; }
.lead { color: var(--soft); margin: 0 0 16px; }
.toc { font-size: 14px; margin-bottom: 8px; display:flex; flex-wrap:wrap; gap: 6px 18px; }
.toc.bottom { margin-top: 32px; }
.chap { display:block; text-decoration:none; color:inherit; }
.chap:hover { border-color: var(--accent); }
.chap h3 { color: var(--accent); }
.chap .n { font: 13px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: var(--soft); }
.chap .bar { margin-top: 6px; }
.chap.extra { background: var(--tint); border-left: 4px solid var(--accent); }
.prose p { margin: 0 0 12px; }
.prose ul { margin: 0 0 12px; padding-left: 22px; }
.lead:empty { display: none; }
a { color: var(--accent); }
.progress { position: sticky; top: 0; background: var(--bg); padding: 10px 0; font-size: 13px;
            color: var(--soft); display:flex; gap:12px; align-items:center; z-index: 2; }
.bar { flex:1; height:6px; background: var(--line); border-radius:3px; overflow:hidden; }
.bar i { display:block; height:100%; width:0; background: var(--do); }
button { font-size:12px; color:var(--soft); background:none; border:1px solid var(--line);
         border-radius:4px; padding:2px 8px; cursor:pointer; }
h2 { font-size: 23px; margin: 40px 0 12px; padding-bottom: 6px; border-bottom: 2px solid var(--accent); }
.block { background: var(--card); border:1px solid var(--line); border-radius:8px;
         padding: 16px 20px; margin: 16px 0; }
h3 { font-size: 17px; margin: 0 0 6px; }
.goal { color: var(--soft); font-style: italic; margin: 0 0 8px; }
ol { list-style:none; margin:0; padding:0; }
.step { display:flex; gap:12px; padding: 12px 0; border-top:1px solid var(--line); }
.step input { margin-top: 6px; width:17px; height:17px; flex:none; accent-color: var(--do); }
.step > div { min-width: 0; }
.step p { margin: 4px 0 0; overflow-wrap: anywhere; }
.title { font-weight: bold; }
.badge { display:inline-block; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.06em;
         border:1px solid currentColor; border-radius:3px; padding:0 6px; margin-right:8px; vertical-align: 2px; }
.watch .badge { color: var(--watch); } .read .badge { color: var(--read); }
.do .badge { color: var(--do); } .note .badge { color: var(--note); }
.check .badge { color: var(--check); }
.ai .badge { color: var(--ai); }
.step ul, .box ul { margin: 6px 0 0; padding-left: 20px; }
.step li, .box li { margin: 4px 0; }
.box { background: var(--tint); border-left: 4px solid var(--accent); border-radius: 4px;
       padding: 14px 20px; margin: 16px 0; }
.box p { margin: 0 0 4px; }
.opt { font-size:12px; color: var(--soft); margin-right:8px; }
.step.done > div { opacity: .55; }
@media print { .progress { display:none; } .block { break-inside: avoid; } }
</style>
</head>
<body>
<main>
<div class="toc">__NAV__</div>
<h1>__H1__</h1>
<p class="lead">__LEAD__</p>
<div class="progress"><span id="count"></span><div class="bar"><i id="fill"></i></div>
<button id="reset" type="button">Reset</button></div>
__BODY__
<div class="toc bottom">__NAV__</div>
</main>
<script>
(function () {
  var PREFIX = 'limo-learningpath-';
  function load(key) { try { return JSON.parse(localStorage.getItem(PREFIX + key)) || {}; } catch (e) { return {}; } }
  // overview page: progress per chapter
  document.querySelectorAll('.chap[data-key]').forEach(function (c) {
    var done = load(c.dataset.key), ids = c.dataset.ids.split(' '), n = 0;
    ids.forEach(function (id) { if (done[id]) n++; });
    c.querySelector('.n').textContent = n + ' of ' + ids.length + ' steps done';
    c.querySelector('.bar i').style.width = (100 * n / ids.length) + '%';
  });
  // chapter page: ticks
  var boxes = document.querySelectorAll('.step input');
  if (!boxes.length) { document.querySelector('.progress').style.display = 'none'; return; }
  var KEY = '__KEY__', done = load(KEY);
  function show() {
    var n = 0;
    boxes.forEach(function (b) {
      b.checked = !!done[b.id];
      b.parentNode.classList.toggle('done', b.checked);
      if (b.checked) n++;
    });
    document.getElementById('count').textContent = n + ' of ' + boxes.length + ' steps done';
    document.getElementById('fill').style.width = (100 * n / boxes.length) + '%';
  }
  function save() { try { localStorage.setItem(PREFIX + KEY, JSON.stringify(done)); } catch (e) {} }
  boxes.forEach(function (b) {
    b.addEventListener('change', function () { done[b.id] = b.checked; save(); show(); });
  });
  document.getElementById('reset').addEventListener('click', function () { done = {}; save(); show(); });
  show();
})();
</script>
</body>
</html>
"""


def build_extra(path):
    """An extra page (page_<name>.txt): # title, ## headings, paragraphs and "- " lists."""
    title, body = path.stem[5:].replace("_", " "), []
    for paragraph in path.read_text(encoding="utf-8").split("\n\n"):
        lines = [l.rstrip() for l in paragraph.strip().splitlines() if not l.startswith("//")]
        if not lines:
            continue
        if lines[0].startswith("## "):
            body.append("<h2>%s</h2>" % text_html(lines[0][3:]))
            lines = lines[1:]
        elif lines[0].startswith("# "):
            title = lines[0][2:].strip()
            lines = lines[1:]
        if lines:
            body.append('<div class="prose">%s</div>' % lines_html(lines))
    return title, "\n".join(body)


def write_page(name, key, title, h1, lead, nav, body):
    page = PAGE
    for mark, value in (("__TITLE__", title), ("__H1__", h1), ("__LEAD__", lead), ("__NAV__", nav),
                        ("__KEY__", key), ("__BODY__", body)):
        page = page.replace(mark, value)
    SITE.mkdir(exist_ok=True)
    (SITE / name).write_text(page, encoding="utf-8")
    if name == OUTPUT + ".html":      # so that the address of the folder itself also works
        (SITE / "index.html").write_text(page, encoding="utf-8")
    print("Wrote", SITE.name + "/" + name)


def main():
    sections = load_sections("--refresh" in sys.argv)
    chapters = build(sections)
    notes = '<a href="%s" target="_blank" rel="noopener">online course notes</a>' % NOTES_URL
    for c in chapters:
        c["file"] = "%s_%s.html" % (OUTPUT, c["key"])

    extras = []
    for path in sorted(HERE.glob("page_*.txt")):
        title, body = build_extra(path)
        extras.append({"title": title, "file": "%s_%s.html" % (OUTPUT, path.stem[5:]), "body": body})

    cards = "\n".join(
        '<a class="block chap" href="%s" data-key="%s" data-ids="%s"><h3>%s</h3>'
        '<span class="n"></span><div class="bar"><i></i></div></a>'
        % (c["file"], c["key"], " ".join(c["ids"]), text_html(c["title"])) for c in chapters)
    write_page(OUTPUT + ".html", "", "Linear Models: learning path", "Linear Models: learning path",
               "Choose a chapter and work through its steps in order. Each step links to the %s. "
               "Your progress is remembered in this browser." % notes, "", "".join(
                   '<a class="block chap extra" href="%s"><h3>%s</h3><span class="n">Read this first</span></a>\n'
                   % (e["file"], text_html(e["title"])) for e in extras) + cards)
    for e in extras:
        write_page(e["file"], "", e["title"], text_html(e["title"]), "",
                   '<a href="%s.html">Overview</a>' % OUTPUT, e["body"])

    for i, c in enumerate(chapters):
        nav = ['<a href="%s.html">Overview</a>' % OUTPUT]
        if i > 0:
            nav.append('<a href="%s">&larr; %s</a>' % (chapters[i - 1]["file"], text_html(chapters[i - 1]["title"])))
        if i + 1 < len(chapters):
            nav.append('<a href="%s">%s &rarr;</a>' % (chapters[i + 1]["file"], text_html(chapters[i + 1]["title"])))
        write_page(c["file"], c["key"], "Learning path: " + c["title"], text_html(c["title"]),
                   "Work through the steps in order. Each step links to the %s. Tick a step when you have "
                   "finished it; your ticks are remembered in this browser." % notes,
                   "".join(nav), "\n".join(c["body"]))


if __name__ == "__main__":
    main()
