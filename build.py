#!/usr/bin/env python3
"""
Build script for timcolonius.github.io
Generates docs/ from data files + content files.
Run:  python3 build.py
Deploy: git push  (GitHub Actions handles the rest)
"""

import os, re, shutil, html
from datetime import datetime
from pathlib import Path

import sheet_data

OUT      = Path("docs")

OUT.mkdir(exist_ok=True)
(OUT / "images").mkdir(exist_ok=True)

DATE = datetime.now().strftime("%Y-%m-%d")

# ── Shared design constants ────────────────────────────────────────────────────

SITE_TITLE  = "Computational and Data-Driven Fluid Dynamics"
PI_NAME     = "Tim Colonius"
PI_TITLE    = "Frank and Ora Lee Marble Professor of Mechanical Engineering"
INSTITUTION = "California Institute of Technology"
DEPT        = "Division of Engineering and Applied Science"
NAV_LINKS   = [
    ("Home",         "index.html"),
    ("People",       "people.html"),
    ("Publications", "publications.html"),
    ("Software",     "software.html"),
]

# ── HTML scaffolding ───────────────────────────────────────────────────────────

STYLE = """
/* ── Reset & base ─────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, sans-serif;
  font-size: 16px; line-height: 1.65;
  color: #1a1a1a; background: #fff;
}
a { color: #b1540a; text-decoration: none; }
a:hover { text-decoration: underline; }
img { max-width: 100%; height: auto; display: block; }

/* ── Layout ───────────────────────────────────────────────────────────── */
.container { max-width: 1140px; margin: 0 auto; padding: 0 1.5rem; }
.section    { padding: 3.5rem 0; }
.section + .section { border-top: 1px solid #eee; }

/* ── Top bar: Caltech logo strip ──────────────────────────────────────── */
.topbar {
  background: #fff; border-bottom: 1px solid #e0e0e0;
  padding: .65rem 0;
}
.topbar .container {
  display: flex; align-items: center; gap: 1.5rem;
}
.topbar-logo img { height: 34px; width: auto; flex-shrink: 0; }
.topbar-divider {
  width: 1px; height: 28px; background: #ccc; flex-shrink: 0;
}
.topbar-group {
  font-size: 1.25rem; font-weight: 500; color: #555;
  letter-spacing: .01em; white-space: nowrap;
}

/* ── Nav ──────────────────────────────────────────────────────────────── */
nav {
  background: #1a1a1a;
  position: sticky; top: 0; z-index: 100;
}
nav .container {
  display: flex; align-items: center;
  justify-content: flex-end;
  height: 48px;
}
.nav-links { display: flex; gap: 0; list-style: none; }
.nav-links a {
  color: #ccc; font-size: .88rem; padding: .55rem .85rem;
  display: block; letter-spacing: .03em; transition: color .15s;
}
.nav-links a:hover, .nav-links a.active { color: #fff; text-decoration: none; }
.nav-links a.active { border-bottom: 2px solid #FF6C0C; }

/* ── Flow image banner ────────────────────────────────────────────────── */
.banner {
  background: #fec91e;   /* matches left edge of flow_header.png */
  height: 81px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: flex-end;   /* image hugs the right */
}
.banner img {
  height: 81px;
  width: auto;          /* natural aspect ratio, no upscaling */
  display: block;
  flex-shrink: 0;
}

/* ── Hero (PI card) ───────────────────────────────────────────────────── */
.hero {
  background: #fff;
  border-top: 1px solid #eee;
  padding: 2.5rem 0;
}
.hero-inner {
  display: flex; gap: 2.5rem; align-items: flex-start;
}
.hero-photo {
  width: 155px; min-width: 155px; border-radius: 6px;
  box-shadow: 0 2px 12px rgba(0,0,0,.15);
}
.hero-photo-placeholder {
  width: 155px; min-width: 155px; height: 195px;
  background: #ddd; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  color: #999; font-size: .8rem; text-align: center;
}
.hero-text h1 { font-size: 1.9rem; font-weight: 700; margin-bottom: .25rem; color: #1a1a1a; }
.hero-text .subtitle {
  color: #FF6C0C; font-size: .95rem; font-weight: 600; margin-bottom: .15rem;
}
.hero-text .institution { color: #777; font-size: .88rem; margin-bottom: 1rem; }
.hero-text p { color: #333; font-size: .93rem; margin-bottom: .8rem; max-width: 580px; }
.hero-links { display: flex; gap: .75rem; flex-wrap: wrap; margin-top: 1rem; }
.btn {
  padding: .42rem 1.1rem; border-radius: 4px; font-size: .87rem;
  font-weight: 600; display: inline-block; transition: opacity .15s;
}
.btn:hover { opacity: .85; text-decoration: none; }
.btn-primary { background: #FF6C0C; color: #fff; }
.btn-outline { border: 1px solid #bbb; color: #444; background: transparent; }

/* ── Section headings ─────────────────────────────────────────────────── */
h2 {
  font-size: 1.45rem; font-weight: 700; margin-bottom: 1.5rem;
  padding-bottom: .5rem; border-bottom: 2px solid #FF6C0C; display: inline-block;
}
h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: .4rem; }

/* ── Cards ────────────────────────────────────────────────────────────── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1.5rem; margin-top: 1rem;
}
.card {
  border: 1px solid #e8e8e8; border-radius: 8px;
  padding: 1.4rem; background: #fafafa;
  transition: box-shadow .15s;
}
.card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); }
.card h3 { color: #1a1a1a; margin-bottom: .25rem; }
.card .meta { color: #888; font-size: .83rem; margin-bottom: .7rem; }
.card p { font-size: .9rem; color: #444; }

/* ── People grid ──────────────────────────────────────────────────────── */
.people-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1.5rem; margin-top: 1rem;
}
.person-card { text-align: center; }
.person-photo {
  width: 100%; aspect-ratio: 3/4; object-fit: cover;
  border-radius: 6px; margin-bottom: .6rem;
  background: #eee;
}
.person-photo-placeholder {
  width: 100%; aspect-ratio: 3/4;
  background: linear-gradient(135deg, #e8e8e8, #d0d0d0);
  border-radius: 6px; margin-bottom: .6rem;
  display: flex; align-items: center; justify-content: center;
  color: #aaa; font-size: 2rem;
}
.person-name { font-weight: 600; font-size: .9rem; margin-bottom: .15rem; }
.person-role { color: #888; font-size: .8rem; }

/* ── Alumni table ─────────────────────────────────────────────────────── */
.alumni-list { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: .9rem; }
.alumni-list th {
  text-align: left; padding: .4rem .75rem;
  border-bottom: 2px solid #eee; color: #888; font-size: .8rem;
  font-weight: 600; letter-spacing: .03em;
}
.alumni-list td { padding: .45rem .75rem; border-bottom: 1px solid #f0f0f0; }
.alumni-list tr:last-child td { border-bottom: none; }
.alumni-list .alum-year { color: #888; white-space: nowrap; }
.alumni-list .alum-thesis { color: #555; font-style: italic; font-size: .85rem; }
.alumni-list .alum-position { color: #444; font-size: .85rem; }

/* ── Research areas ───────────────────────────────────────────────────── */
.research-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem; margin-top: 1rem;
}
.research-card {
  position: relative;
  border: 1px solid #e8e8e8; border-radius: 8px; overflow: hidden;
  background: #fafafa; transition: box-shadow .15s;
}
.research-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); }
.research-card:focus { outline: 2px solid #FF6C0C; outline-offset: 2px; }
.rc-img { width: 100%; height: 230px; object-fit: contain; display: block; background: #fff;
  transition: filter .18s ease; }
.rc-img-placeholder {
  width: 100%; height: 230px;
  background: linear-gradient(135deg, #e8eff8, #c8d8e8);
  display: flex; align-items: center; justify-content: center;
  color: #8a9bb0; font-size: .82rem; text-align: center; padding: 1rem;
  transition: filter .18s ease;
}
.rc-body { padding: .85rem 1.2rem; }
.rc-body h3 { font-size: 1.05rem; margin-bottom: 0; }
/* Mouse devices: hover greys/dims the figure and reveals the blurb over it */
.research-card:hover .rc-img,  .research-card:focus-within .rc-img,
.research-card:hover .rc-img-placeholder, .research-card:focus-within .rc-img-placeholder {
  filter: grayscale(100%) brightness(.45);
}
.rc-blurb {
  position: absolute; top: 0; left: 0; right: 0; height: 230px; margin: 0;
  color: #fff; background: rgba(0,0,0,.25); text-shadow: 0 1px 3px rgba(0,0,0,.7);
  font-size: .8rem; line-height: 1.45; padding: .9rem 1.2rem; overflow: hidden;
  display: flex; flex-direction: column; justify-content: center;
  opacity: 0; transition: opacity .18s ease;
}
.rc-blurb p { margin-bottom: .5rem; }
.rc-blurb p:last-child { margin-bottom: 0; }
.research-card:hover .rc-blurb, .research-card:focus-within .rc-blurb { opacity: 1; }
/* Touch devices (no hover): show the blurb inline below the title, always visible */
@media (hover: none) {
  .rc-blurb {
    position: static; height: auto; opacity: 1; display: block;
    color: #444; background: none; text-shadow: none;
    padding: 0; margin-top: .5rem; font-size: .88rem;
  }
  .research-card:hover .rc-img, .research-card:focus-within .rc-img,
  .research-card:hover .rc-img-placeholder, .research-card:focus-within .rc-img-placeholder {
    filter: none;
  }
}

/* ── Software cards ───────────────────────────────────────────────────── */
.software-card {
  border: 1px solid #e8e8e8; border-radius: 8px;
  padding: 1.8rem; background: #fafafa;
  margin-bottom: 1.5rem;
  transition: box-shadow .15s;
}
.software-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); }
.software-card h3 { font-size: 1.2rem; color: #1a1a1a; margin-bottom: .3rem; }
.software-card .sw-tagline {
  color: #FF6C0C; font-size: .9rem; font-weight: 600; margin-bottom: .75rem;
}
.software-card p { font-size: .93rem; color: #444; margin-bottom: .7rem; max-width: 680px; }
.software-links { display: flex; gap: .75rem; flex-wrap: wrap; margin-top: 1rem; }

/* ── Publications ─────────────────────────────────────────────────────── */
.pub-filter {
  display: flex; gap: .75rem; margin-bottom: 1.5rem; flex-wrap: wrap;
  align-items: center;
}
.pub-filter input {
  padding: .4rem .75rem; border: 1px solid #ccc; border-radius: 4px;
  font-size: .9rem; flex: 1; min-width: 200px;
}
.pub-chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1.1rem; }
.pub-chip {
  border: 1px solid #ddd; background: #fff; color: #555;
  font-size: .8rem; padding: .32rem .85rem; border-radius: 999px;
  cursor: pointer; transition: background .15s, border-color .15s, color .15s;
}
.pub-chip:hover { border-color: #FF6C0C; color: #FF6C0C; }
.pub-chip.active { background: #FF6C0C; border-color: #FF6C0C; color: #fff; }
.pub-year-hdr { font-size: 1.1rem; font-weight: 700; color: #888;
  margin: 1.5rem 0 .6rem; border-bottom: 1px solid #eee; padding-bottom: .3rem; }
.pub-entry { padding: .6rem 0; border-bottom: 1px solid #f0f0f0; }
.pub-entry:last-child { border-bottom: none; }
.pub-title { font-weight: 600; font-size: .93rem; }
.pub-authors { color: #555; font-size: .85rem; margin: .15rem 0; }
.pub-venue { color: #777; font-size: .85rem; font-style: italic; }
.pub-links { margin-top: .25rem; font-size: .82rem; }
.pub-links a { color: #b1540a; margin-right: .75rem; }

/* ── Footer ───────────────────────────────────────────────────────────── */
footer {
  background: #1a1a1a; color: #888; font-size: .82rem;
  padding: 2rem 0; margin-top: 4rem;
}
footer .container { display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
footer a { color: #aaa; }

/* ── Responsive ───────────────────────────────────────────────────────── */
@media (max-width: 680px) {
  .hero-inner { flex-direction: column; }
  .hero-photo, .hero-photo-placeholder { width: 120px; min-width: 120px; }
  .nav-links a { padding: .55rem .5rem; font-size: .8rem; }
  .topbar-group { display: none; }
  .banner { height: 56px; }
  .banner img { height: 75px; }
  .alumni-list th:nth-child(3), .alumni-list td:nth-child(3) { display: none; }
}
"""

def nav_html(active: str) -> str:
    links = ""
    for label, href in NAV_LINKS:
        cls = ' class="active"' if href == active else ""
        links += f'<li><a href="{href}"{cls}>{label}</a></li>\n'
    return f"""
<div class="topbar">
  <div class="container">
    <a class="topbar-logo" href="https://www.caltech.edu" target="_blank">
      <img src="images/caltech_logo.png" alt="Caltech"/>
    </a>
    <div class="topbar-divider"></div>
    <span class="topbar-group">Computational and Data-Driven Fluid Dynamics</span>
  </div>
</div>
<nav>
  <div class="container">
    <ul class="nav-links">{links}</ul>
  </div>
</nav>"""

def footer_html() -> str:
    return f"""
<footer>
  <div class="container">
    <span>{PI_NAME} &nbsp;·&nbsp; {DEPT} &nbsp;·&nbsp; {INSTITUTION}</span>
    <span>Last updated: {DATE}</span>
  </div>
</footer>"""

def banner_html() -> str:
    return """
<div class="banner">
  <img src="images/flow_header.png" alt="Vortex shedding simulation"/>
</div>"""

def page(title: str, active: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title} — {SITE_TITLE}</title>
  <link rel="stylesheet" href="style.css"/>
</head>
<body>
{nav_html(active)}
{banner_html()}
{body}
{footer_html()}
</body>
</html>
"""

# ── Home ───────────────────────────────────────────────────────────────────────

def _research_section():
    """Sheet-driven research areas as an image-card grid (home page).
    A missing/absent figure file falls back to a placeholder box."""
    ws = sheet_data.workbook()["Research"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h).strip().lower() if h else "" for h in rows[0]]
    col = lambda name: next((i for i, h in enumerate(hdr) if h == name), None)
    ci = {k: col(k) for k in ("title", "blurb", "image", "alt_text")}
    def g(r, key):
        i = ci[key]
        return str(r[i]).strip() if i is not None and i < len(r) and r[i] else ""

    cards = ""
    for r in rows[1:]:
        title = g(r, "title")
        if not title:
            continue
        img, alt = g(r, "image"), (g(r, "alt_text") or g(r, "title"))
        if img and (OUT / "images" / img).exists():
            fig = f'<img class="rc-img" src="images/{html.escape(img)}" alt="{html.escape(alt)}"/>'
        else:
            fig = '<div class="rc-img-placeholder">figure coming soon</div>'
        paras = "".join(f"<p>{html.escape(p.strip())}</p>"
                        for p in re.split(r"\n\s*\n|\n", g(r, "blurb")) if p.strip())
        cards += f"""
      <div class="research-card" tabindex="0">
        {fig}
        <div class="rc-body">
          <h3>{html.escape(title)}</h3>
          <div class="rc-blurb">{paras}</div>
        </div>
      </div>"""
    return f"""
<div class="container">
  <div class="section">
    <h2>Research</h2>
    <div class="research-grid">{cards}
    </div>
  </div>
</div>"""

def build_home():
    bio_paras = [
        "We develop and apply high-fidelity numerical methods to study "
        "a wide range of problems in fluid mechanics, with emphasis on "
        "flow-induced sound, multi-phase flows, flow instability and control, "
        "and high-performance computing.",
        "Our group is part of the <a href='https://www.caltech.edu'>California Institute "
        "of Technology</a>, <a href='https://eas.caltech.edu'>Division of Engineering and "
        "Applied Science</a>, <a href='https://mce.caltech.edu'>Department of Mechanical "
        "and Civil Engineering</a>.",
    ]
    bio_html = "".join(f"<p>{p}</p>\n" for p in bio_paras)

    # PI photo for hero block
    photo_index = _build_photo_index()
    pi_photo_match = _find_photo("Tim", "Colonius", photo_index)
    if pi_photo_match:
        pi_photo_html = f'<img class="hero-photo" src="images/{pi_photo_match.name}" alt="{PI_NAME}"/>'
    else:
        pi_photo_html = '<div class="hero-photo-placeholder">Photo</div>'

    body = f"""
{_research_section()}
<div class="hero">
  <div class="container">
    <div class="hero-inner">
      {pi_photo_html}
      <div class="hero-text">
        <h1>{PI_NAME}</h1>
        <div class="subtitle">{PI_TITLE}</div>
        <div class="institution">{INSTITUTION} &nbsp;·&nbsp; {DEPT}</div>
        {bio_html}
        <div class="hero-links">
          <a class="btn btn-primary" href="cv.pdf" target="_blank">CV (PDF)</a>
          <a class="btn btn-outline" href="publications.html">Publications</a>
          <a class="btn btn-outline"
             href="https://scholar.google.com/citations?user=zrUK8W0AAAAJ&hl=en"
             target="_blank">Google Scholar</a>
        </div>
      </div>
    </div>
  </div>
</div>
"""
    (OUT / "index.html").write_text(page(PI_NAME, "index.html", body))
    print("  index.html")

# ── People ─────────────────────────────────────────────────────────────────────

def _parse_year(val):
    """Return a 4-digit year int from varied formats, or None."""
    if not val: return None
    s = str(val).strip()
    if s.lower() in ("none", "", "nan"): return None
    try: return int(float(s))           # "2021.0" or "2021"
    except ValueError: pass
    m = re.match(r'(\d{4})', s)         # "2025-06-01 00:00:00"
    return int(m.group(1)) if m else None

def _norm_name(s: str) -> str:
    """Lowercase + strip diacritics for fuzzy name matching."""
    s = s.lower().strip()
    for a, b in [
        ('é','e'),('è','e'),('ê','e'),('ë','e'),('á','a'),('à','a'),('â','a'),
        ('ä','a'),('ã','a'),('å','a'),('í','i'),('ì','i'),('î','i'),('ï','i'),
        ('ó','o'),('ò','o'),('ô','o'),('ö','o'),('õ','o'),('ø','o'),('ú','u'),
        ('ù','u'),('û','u'),('ü','u'),('ý','y'),('ÿ','y'),('ñ','n'),('ç','c'),
        ('š','s'),('č','c'),('ž','z'),('ř','r'),('ß','ss'),('æ','ae'),('œ','oe'),
    ]:
        s = s.replace(a, b)
    return s

def _role_label(role: str) -> str:
    """Human-readable role label from spreadsheet code."""
    r = role.strip()
    if re.match(r'^G\d+$', r):          return "Graduate Research Assistant"
    if re.match(r'^P\d+$', r):          return "Postdoctoral Scholar"
    if "postdoc" in r.lower():          return "Postdoctoral Scholar"
    if r.lower() == "faculty":          return "Principal Investigator"
    if r.lower() == "staff scientist":  return "Staff Scientist"
    if r.lower() == "surf":             return "Undergraduate Researcher"
    if r.lower() == "visitor":          return "Visiting Researcher"
    if "grad student" in r.lower():     return "Graduate Research Assistant"
    return r  # fallback: display as-is

def _build_photo_index() -> dict:
    """Scan docs/images/ and return { norm_stem → Path } for every image file.
    Used to match a person's name to their photo file (non-people images like
    logos/banners/research simply won't match any person name)."""
    index = {}
    img_dir = OUT / "images"
    if not img_dir.exists():
        return index
    for f in img_dir.iterdir():
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            index[_norm_name(f.stem)] = f
    return index

def _find_photo(first: str, last: str, photo_index: dict):
    """
    Return the Path of the best matching photo, or None.
    Tries (in order):
      1. Exact normalized last name  (Glenn.jpg → 'glenn' == norm('Glenn'))
      2. Exact normalized first name (Ethan.png → 'ethan' == norm('Ethan'))
      3. Any stem that is a substring of last or first name
         (Catsoulis.jpg → 'catsoulis' ∈ norm('Soto Catsoulis'))
      4. Last or first name that is a substring of a stem
         (handles longer compound filenames if user adds them later)
    """
    nl = _norm_name(last)
    nf = _norm_name(first)
    if nl in photo_index: return photo_index[nl]
    if nf in photo_index: return photo_index[nf]
    for stem, path in photo_index.items():
        if stem and (stem in nl or stem in nf):
            return path
    for stem, path in photo_index.items():
        if nl and nl in stem: return path
        if nf and nf in stem: return path
    return None

def _photo_html(first: str, last: str, name_display: str, photo_index: dict) -> str:
    """Return <img> tag if a matching photo is found, else initials placeholder."""
    match = _find_photo(first, last, photo_index)
    if match:
        return f'<img class="person-photo" src="images/{match.name}" alt="{name_display}"/>'
    initials = "".join(w[0].upper() for w in name_display.split() if w)[:2]
    return f'<div class="person-photo-placeholder">{initials}</div>'

def build_people():
    """Build people.html from the People tab of the Google sheet."""
    photo_index = _build_photo_index()

    # ── Load members ──────────────────────────────────────────────────────
    current: list[dict] = []
    alumni_phd: list[dict] = []
    alumni_postdoc: list[dict] = []

    if True:  # data comes from the Google sheet (see sheet_data.py)
        try:
            wb = sheet_data.workbook()

            # ── Build thesis index from Publications: tag → {title, url} ──────
            thesis_index = {}   # cite_key → {"title": ..., "url": ...}
            ws_pub = wb["Publications"]
            pub_hdrs = None
            for raw in ws_pub.iter_rows(values_only=True):
                if raw[0] == "Entry type":
                    pub_hdrs = [str(h).strip() if h else "" for h in raw]; continue
                if not pub_hdrs: continue
                if str(raw[0]).strip().lower() != "phdthesis": continue
                def _pfld(row, key, _h=pub_hdrs):
                    try: return str(row[_h.index(key)]).strip() if row[_h.index(key)] else ""
                    except: return ""
                tag   = _pfld(raw, "Tag")
                title = _pfld(raw, "Title")
                url   = _pfld(raw, "Persistent URL")
                if tag and title:
                    thesis_index[tag] = {"title": title, "url": url}

            # ── Load people (header-based: column order may change) ────────────
            ws = wb["People"]
            rows = list(ws.iter_rows(values_only=True))
            hdr = [str(h).strip() if h else "" for h in rows[0]]
            def _col(sub, _h=hdr):
                return next((i for i, h in enumerate(_h) if sub.lower() in h.lower()), None)
            ix = {k: _col(k) for k in
                  ("Last", "First", "Role", "End date", "Thesis tag",
                   "Present Position", "Link")}
            def _g(r, key, _ix=ix):
                i = _ix[key]
                return str(r[i]).strip() if i is not None and i < len(r) and r[i] else ""
            for r in rows[1:]:
                last  = _g(r, "Last")
                first = _g(r, "First")
                if not last and not first: continue
                role  = _g(r, "Role")
                year  = _parse_year(_g(r, "End date"))
                rec = {"first": first, "last": last, "role": role, "year": year,
                       "position": _g(r, "Present Position"), "link": _g(r, "Link")}
                if role == "GRA Advisee":
                    th = thesis_index.get(_g(r, "Thesis tag"), {})
                    rec["thesis_title"] = th.get("title", "")
                    rec["thesis_url"]   = th.get("url", "")
                    alumni_phd.append(rec)
                elif role == "Postdoc Advisee":
                    alumni_postdoc.append(rec)
                else:
                    current.append(rec)
            wb.close()
        except Exception as e:
            print(f"  WARNING: could not load people data: {e}")

    # ── Always include PI at top of current group ─────────────────────────
    pi_rec = {"first": "Tim", "last": "Colonius", "role": "Faculty", "year": None}
    # Remove any spreadsheet entry for Tim (avoid duplicates)
    current = [p for p in current if not
               (_norm_name(p["first"]) == "tim" and _norm_name(p["last"]) == "colonius")]
    current.insert(0, pi_rec)   # Tim is now current[0]
    def _is_admin(p): return "admin" in p["role"].lower() or "assistant" in p["role"].lower()
    admin  = [p for p in current[1:] if _is_admin(p)]
    others = [p for p in current[1:] if not _is_admin(p)]
    rest   = sorted(others, key=lambda p: (p["last"].lower(), p["first"].lower()))
    current = [pi_rec] + admin + rest  # Tim | Kristen | ABC...
    # Alumni: most recent year first, then alpha
    alumni_phd.sort(key=lambda p: (-(p["year"] or 0), p["last"]))
    alumni_postdoc.sort(key=lambda p: (-(p["year"] or 0), p["last"]))

    # ── Render current group ──────────────────────────────────────────────
    current_cards = ""
    for p in current:
        name = f"{p['first']} {p['last']}"
        photo = _photo_html(p["first"], p["last"], name, photo_index)
        label = _role_label(p["role"])
        current_cards += f"""
    <div class="person-card">
      {photo}
      <div class="person-name">{name}</div>
      <div class="person-role">{label}</div>
    </div>"""

    if not current_cards:
        current_cards = "<p style='color:#888'>People data not yet loaded.</p>"

    # ── Render alumni tables ──────────────────────────────────────────────
    def alumni_rows(people, show_thesis=False):
        if not people:
            return "<p style='color:#888'>No records found.</p>"
        rows = ""
        for p in people:
            # Name: link to personal website if available
            name_text = f"{p['first']} {p['last']}"
            lnk = p.get("link", "")
            name_cell = (f'<a href="{lnk}" target="_blank">{name_text}</a>'
                         if lnk else name_text)
            yr = str(p["year"]) if p["year"] else "—"

            # Position cell
            pos = p.get("position", "")
            pos_cell = f'<td class="alum-position">{pos}</td>'

            # Thesis cell
            thesis_cell = ""
            if show_thesis:
                title = p.get("thesis_title", "")
                turl  = p.get("thesis_url", "")
                if title and turl:
                    thesis_cell = f'<td class="alum-thesis"><a href="{turl}" target="_blank">{title}</a></td>'
                elif title:
                    thesis_cell = f'<td class="alum-thesis">{title}</td>'
                else:
                    thesis_cell = '<td class="alum-thesis"></td>'

            rows += f"""
<tr>
  <td>{name_cell}</td>
  <td class="alum-year">{yr}</td>
  {pos_cell}
  {thesis_cell}
</tr>"""

        extra_hdrs = '<th>Thesis</th>' if show_thesis else ''
        return f"""
<table class="alumni-list">
  <thead><tr><th>Name</th><th>Year</th><th>Present Position</th>{extra_hdrs}</tr></thead>
  <tbody>{rows}</tbody>
</table>"""

    body = f"""
<div class="container">
  <div class="section">
    <h2>Current Group</h2>
    <div class="people-grid">
      {current_cards}
    </div>
  </div>

  <div class="section">
    <h2>Former Graduate Students</h2>
    {alumni_rows(alumni_phd, show_thesis=True)}
  </div>

  <div class="section">
    <h2>Former Postdocs</h2>
    {alumni_rows(alumni_postdoc, show_thesis=False)}
  </div>
</div>"""
    (OUT / "people.html").write_text(page("People", "people.html", body))
    print("  people.html")

# ── Publications ───────────────────────────────────────────────────────────────

def build_publications():
    _build_publications_inline()

def _build_publications_inline():
    from collections import defaultdict

    wb = sheet_data.workbook()
    ws = wb["Publications"]
    headers = None
    rows = []
    for raw in ws.iter_rows(values_only=True):
        if raw[0] == "Entry type":
            headers = [str(h).strip() if h else "" for h in raw]
            continue
        if headers:
            rec = {headers[i]: (str(v).strip() if v is not None and not hasattr(v, "strftime")
                                 else (v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else ""))
                   for i, v in enumerate(raw) if i < len(headers)}
            if any(rec.values()): rows.append(rec)

    # Research areas (tag, title) for the filter chips, in Research-sheet order
    research_areas = []
    rrows = list(wb["Research"].iter_rows(values_only=True))
    rh = [str(x).strip().lower() if x else "" for x in rrows[0]]
    rti, rtt = rh.index("tag"), rh.index("title")
    for raw in rrows[1:]:
        if rti < len(raw) and raw[rti]:
            research_areas.append((str(raw[rti]).strip(),
                                   str(raw[rtt]).strip() if rtt < len(raw) and raw[rtt] else ""))
    wb.close()

    def fld(r, k): return r.get(k) or ""
    def authors_display(raw):
        parts = [a.strip() for a in raw.replace("{","").replace("}","").split("/") if a.strip()]
        def flip(a):
            p = [x.strip() for x in a.split(",", 1)]
            return f"{p[1]} {p[0]}" if len(p) == 2 else a
        return ", ".join(flip(a) for a in parts)

    TYPE_LABELS = {
        "article": "Journal Article", "inproceedings": "Conference Paper",
        "phdthesis": "PhD Thesis", "misc": "Preprint", "incollection": "Book Chapter",
    }
    TYPE_COLORS = {
        "article": "#dbeafe", "inproceedings": "#dcfce7",
        "phdthesis": "#fef9c3", "misc": "#f3e8ff", "incollection": "#ffedd5",
    }

    by_year = defaultdict(list)
    for r in rows:
        try: y = int(float(fld(r, "Year")))
        except: y = 0
        by_year[y].append(r)

    pub_rows = ""
    for yr in sorted(by_year, reverse=True):
        pub_rows += f'<div class="pub-year-hdr">{yr}</div>'
        for r in by_year[yr]:
            etype = fld(r, "Entry type").lower()
            label = TYPE_LABELS.get(etype, etype)
            color = TYPE_COLORS.get(etype, "#eee")
            badge = (f'<span style="background:{color};padding:1px 7px;border-radius:3px;'
                     f'font-size:.75rem;font-weight:600;margin-right:.5rem">{label}</span>')
            title   = fld(r, "Title")
            authors = authors_display(fld(r, "Author"))
            href = _pub_href(r)
            title_html = (f'<a href="{html.escape(href)}" target="_blank">{html.escape(title)}</a>'
                          if href else html.escape(title))
            venue_line = _format_venue(r) + _doi_suffix(r)
            area_tags = " ".join(t.strip().lower()
                                  for t in fld(r, "Research Areas").replace(";", ",").split(",") if t.strip())
            pub_rows += f"""
<div class="pub-entry" data-areas="{html.escape(area_tags)}">
  {badge}<span class="pub-title">{title_html}</span>
  <div class="pub-authors">{authors}</div>
  {'<div class="pub-venue">' + venue_line + '</div>' if venue_line.strip() else ''}
</div>"""

    chips = '<button class="pub-chip active" data-area="" onclick="setArea(this)">All</button>'
    for tag, title in research_areas:
        chips += (f'<button class="pub-chip" data-area="{html.escape(tag)}" '
                  f'onclick="setArea(this)">{html.escape(title)}</button>')

    body = f"""
<div class="container">
  <div class="section">
    <h2>Publications</h2>
    <div class="pub-chips">{chips}</div>
    <div class="pub-filter">
      <input type="text" id="pubsearch" placeholder="Filter by title, author, journal…"
             oninput="filterPubs()"/>
      <a class="btn btn-primary" href="publications.bib" download>Download .bib</a>
    </div>
    <div id="publist">{pub_rows}</div>
  </div>
</div>
<script>
let activeArea = "";
function setArea(btn) {{
  activeArea = btn.getAttribute('data-area');
  document.querySelectorAll('.pub-chip').forEach(c => c.classList.toggle('active', c === btn));
  filterPubs();
}}
function filterPubs() {{
  const q = document.getElementById('pubsearch').value.toLowerCase();
  document.querySelectorAll('.pub-entry').forEach(el => {{
    const areas = (el.getAttribute('data-areas') || '').split(' ');
    const matchArea = !activeArea || areas.indexOf(activeArea) !== -1;
    const matchText = !q || el.textContent.toLowerCase().includes(q);
    el.style.display = (matchArea && matchText) ? '' : 'none';
  }});
  document.querySelectorAll('.pub-year-hdr').forEach(hdr => {{
    let sib = hdr.nextElementSibling, any = false;
    while (sib && sib.classList.contains('pub-entry')) {{
      if (sib.style.display !== 'none') any = true;
      sib = sib.nextElementSibling;
    }}
    hdr.style.display = any ? '' : 'none';
  }});
}}
</script>"""
    (OUT / "publications.html").write_text(page("Publications", "publications.html", body))
    # Serve the bibliography generated by gen_cv_lists.py (run earlier in the pipeline).
    bib_src = Path("colonius.bib")
    (OUT / "publications.bib").write_text(
        bib_src.read_text(encoding="utf-8") if bib_src.exists() else "", encoding="utf-8")
    print("  publications.html")

# ── Software ───────────────────────────────────────────────────────────────────

def _pub_index():
    """Return {tag: record} from the Publications tab, for citation lookups."""
    ws = sheet_data.workbook()["Publications"]
    hdr = None
    idx = {}
    for raw in ws.iter_rows(values_only=True):
        if raw and raw[0] == "Entry type":
            hdr = [str(h).strip() if h else "" for h in raw]
            continue
        if not hdr:
            continue
        rec = {hdr[i]: (str(v).strip() if v else "")
               for i, v in enumerate(raw) if i < len(hdr)}
        if rec.get("Tag"):
            idx[rec["Tag"]] = rec
    return idx

def _pub_href(rec):
    """Best single link for a publication's title: persistent URL, else DOI."""
    url = rec.get("Persistent URL", "").strip()
    doi = rec.get("DOI", "").strip()
    return url or (f"https://doi.org/{doi}" if doi else "")

def _doi_suffix(rec):
    """Compact DOI link to append at the end of a line ('' if no DOI)."""
    doi = rec.get("DOI", "").strip()
    if not doi:
        return ""
    return (f' <a href="https://doi.org/{html.escape(doi)}" target="_blank" '
            f'style="font-style:normal">doi:{html.escape(doi)}</a>')

def _format_venue(rec):
    """Type-aware venue/details (HTML, no year or link), IEEE-style, mirroring the
    CV. Different publication types use different columns; absent ones are skipped.
    Shared by the publications page and the software-page references."""
    import html as _h
    et = rec.get("Entry type", "").lower()
    g = lambda k: rec.get(k, "").strip()
    em = lambda s: f"<em>{_h.escape(s)}</em>"
    esc = _h.escape
    vol, num, pages = g("Volume"), g("Issue/Number"), g("Page Range")

    if et == "article":
        out = [em(g("Publication Title"))] if g("Publication Title") else []
        if vol:   out.append(f"vol. {esc(vol)}")
        if num:   out.append(f"no. {esc(num)}")
        if pages: out.append(esc(pages))
        return ", ".join(out)

    if et == "inproceedings":
        venue = g("Publication Title") or g("Publisher")
        out = "in " + em(venue) if venue else ""
        if pages: out += (", " if out else "") + esc(pages)
        return out

    if et == "incollection":
        out = "in " + em(g("Publication Title")) if g("Publication Title") else ""
        if g("Editor"):    out += f", {esc(g('Editor'))}, Ed."
        if g("Publisher"): out += (", " if out else "") + esc(g("Publisher"))
        if pages:          out += (", " if out else "") + esc(pages)
        return out

    if et == "phdthesis":
        out = "Ph.D. thesis"
        if g("School"): out += ", " + em(g("School"))
        return out

    if et == "misc":
        if g("Publication Title"): return em(g("Publication Title"))
        if g("Submitted to"):      return "submitted to " + em(g("Submitted to"))
        return ""

    return em(g("Publication Title")) if g("Publication Title") else ""


def _format_citation(rec):
    """Full one-line HTML citation (authors, title, venue, year, link) for the
    software-page references. Venue formatting is shared with the publications page."""
    import html as _h
    parts = [a.strip() for a in rec.get("Author", "").replace("{", "").replace("}", "").split("/") if a.strip()]
    names = []
    for a in parts:
        s = [x.strip() for x in a.split(",", 1)]
        names.append(f"{s[1]} {s[0]}" if len(s) == 2 else a)
    if len(names) > 6:
        authors = ", ".join(names[:6]) + ", et al."
    elif len(names) > 1:
        authors = ", ".join(names[:-1]) + ", and " + names[-1]
    else:
        authors = names[0] if names else ""
    year = rec.get("Year", "")
    try:
        year = str(int(float(year)))
    except ValueError:
        pass
    venue = _format_venue(rec)
    href = _pub_href(rec)
    title = rec.get("Title", "")
    title_html = (f'<a href="{_h.escape(href)}" target="_blank">{_h.escape(title)}</a>'
                  if href else _h.escape(title))
    out = ""
    if authors: out += _h.escape(authors) + ", "
    if title:   out += f"&ldquo;{title_html},&rdquo; "
    if venue:   out += venue
    if year:    out += f" ({_h.escape(year)})"
    out += "."
    out += _doi_suffix(rec)
    return out

def build_software():
    """Build software.html from the Software tab (header-based; Badges and Notice
    columns are optional). References are formatted from the Publications tab."""
    pubidx = _pub_index()
    ws = sheet_data.workbook()["Software"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h).strip() if h else "" for h in rows[0]]
    col = lambda name: next((i for i, h in enumerate(hdr) if h.lower() == name.lower()), None)
    ci = {k: col(k) for k in ("Repo", "Description", "Github", "Documentation",
                              "Blurb", "Refs", "Badges", "Notice")}
    def g(r, key):
        i = ci[key]
        return str(r[i]).strip() if i is not None and i < len(r) and r[i] else ""

    cards_html = ""
    for r in rows[1:]:
        name = g(r, "Repo")
        if not name:
            continue
        paras = "".join(f"<p>{html.escape(p.strip())}</p>"
                        for p in re.split(r"\n\s*\n|\n", g(r, "Blurb")) if p.strip())
        badges_html = "".join(
            f'<span style="background:#f0f0f0;border-radius:3px;padding:2px 9px;'
            f'font-size:.78rem;font-weight:600;color:#555;margin-right:.4rem">{html.escape(b.strip())}</span>'
            for b in g(r, "Badges").split(",") if b.strip()
        )
        badges_div = f'<div style="margin-bottom:.85rem">{badges_html}</div>' if badges_html else ""
        links_html = ""
        if g(r, "Github"):
            links_html += f'<a class="btn btn-primary" href="{html.escape(g(r, "Github"))}" target="_blank">GitHub</a>'
        if g(r, "Documentation"):
            links_html += f'<a class="btn btn-outline" href="{html.escape(g(r, "Documentation"))}" target="_blank">Documentation</a>'
        warning_html = ""
        if g(r, "Notice"):
            warning_html = (
                f'<div style="background:#fff8e1;border-left:3px solid #fec91e;'
                f'padding:.55rem .9rem;border-radius:3px;font-size:.85rem;'
                f'color:#7a6000;margin-bottom:.85rem">⚠️ {html.escape(g(r, "Notice"))}</div>'
            )
        ref_items = ""
        for k in [x.strip() for x in g(r, "Refs").split(",") if x.strip()]:
            rec = pubidx.get(k)
            if not rec:
                print(f"  WARNING: software reference key not found in Publications: {k} (in {name})")
                continue
            ref_items += f'<li style="margin-bottom:.4rem">{_format_citation(rec)}</li>'
        refs_html = ""
        if ref_items:
            refs_html = (
                '<div style="margin-top:1rem;border-top:1px solid #eee;padding-top:.7rem">'
                '<div style="font-size:.75rem;font-weight:700;color:#666;'
                'text-transform:uppercase;letter-spacing:.04em;margin-bottom:.45rem">'
                'Key references</div>'
                f'<ol style="font-size:.82rem;color:#555;line-height:1.45;'
                f'margin:0;padding-left:1.2rem">{ref_items}</ol></div>'
            )
        cards_html += f"""
<div class="software-card">
  <h3>{html.escape(name)}</h3>
  <div class="sw-tagline">{html.escape(g(r, "Description"))}</div>
  {badges_div}
  {warning_html}{paras}
  {"<div class='software-links'>" + links_html + "</div>" if links_html else ""}
  {refs_html}
</div>"""

    body = f"""
<div class="container">
  <div class="section">
    <h2>Software</h2>
    <p style="margin-bottom:2rem; color:#555; font-size:.95rem;">
      Our group develops and maintains open-source software tools for
      computational fluid dynamics. All codes are freely available on GitHub.
    </p>
    {cards_html}
  </div>
</div>"""
    (OUT / "software.html").write_text(page("Software", "software.html", body))
    print("  software.html")

# ── CSS ────────────────────────────────────────────────────────────────────────

def build_css():
    (OUT / "style.css").write_text(STYLE)
    print("  style.css")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"Building {SITE_TITLE}  →  {OUT}/")
    build_css()
    build_home()
    build_people()
    build_publications()
    build_software()

    # ── Copy CV PDF (compiled from cv/Colonius.tex) ──────────────────────
    cv_src = Path(__file__).parent / "cv" / "Colonius.pdf"
    if cv_src.exists():
        shutil.copy2(cv_src, OUT / "cv.pdf")
        print(f"  cv.pdf")
    else:
        print(f"  cv.pdf  WARNING: Colonius.pdf not found — run latexmk first")

    print(f"Done — {len(list(OUT.iterdir()))} files in {OUT}/")

if __name__ == "__main__":
    main()
