#!/usr/bin/env python3
"""
acquire.py — Archimedes Math Crawler
======================================
Mathematical knowledge acquisition pipeline. Archimedes' forever job:
teach himself maths by scraping LaTeX from authoritative sources.

Sources (in priority order, each a swappable plugin):
    1. Wikipedia REST API           (en.wikipedia.org/api/rest_v1)
    2. Wikipedia Action API         (en.wikipedia.org/w/api.php) — fallback
    3. Wolfram MathWorld            (mathworld.wolfram.com)
    4. Encyclopedia of Math         (encyclopediaofmath.org)
    5. PlanetMath                   (planetmath.org)
    6. nLab                         (ncatlab.org)
    7. arXiv abstract API           (export.arxiv.org/api/query) — citation only
    8. DLMF                         (dlmf.nist.gov) — special functions reference

Output:    one JSON file per topic into alphabetically sharded dirs
           (topics_a/ ... topics_z/)
Resume:    on by default — skips topics already complete
Politeness:robots.txt respected per host, per-host rate limits, descriptive UA
LaTeX:     extracted from <math>, MathML, .tex inline, and Wikipedia formula imgs
Hyperindex:every formula gets a HyperWebster address slot for later assignment
Aule:      stream_event() shim wired in — zero-coupling, silent if Aule absent
lxml:      used over BeautifulSoup for performance (HyperWebster directive)
No Claude API gap-fill in first pass — flags only.

Author: Ptolemy Project / Archimedes Face
House style mirrors Philadelphos/LLM_Datatype_parser/acquire.py
"""

# ── Aule shim (zero coupling — silent no-op if Aule not running) ─────────────
try:
    from Aule.aule import stream_event as _emit
except ImportError:
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from Aule.aule import stream_event as _emit
    except ImportError:
        def _emit(channel, event_type, payload=None, **kwargs): pass

# ── Standard imports ──────────────────────────────────────────────────────────
import os
import sys
import re
import json
import time
import hashlib
import logging
import argparse
import urllib.parse
import urllib.robotparser
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    from lxml import etree, html as lxml_html
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    logging.warning("lxml not available — formula extraction will be degraded")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("archimedes.acquire")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
OUTPUT_ROOT = SCRIPT_DIR / "math_data"

# ── Identity ──────────────────────────────────────────────────────────────────
# Wikipedia and most academic sites require a descriptive User-Agent with contact.
# Override via env var if you ever go public with this.
USER_AGENT = os.environ.get(
    "ARCHIMEDES_USER_AGENT",
    "PtolemyArchimedes/1.0 (math research crawler; "
    "github.com/michaelrendier/Ptolemy; contact via repo issues)"
)

# ── Per-host rate limits (seconds between requests TO THAT HOST) ──────────────
HOST_DELAYS: Dict[str, float] = {
    "en.wikipedia.org":          1.0,    # WMF asks for 1 req/sec from non-bulk clients
    "mathworld.wolfram.com":     2.0,    # Wolfram is stricter
    "encyclopediaofmath.org":    1.5,
    "planetmath.org":            1.5,
    "ncatlab.org":               2.0,
    "export.arxiv.org":          3.0,    # arXiv asks for 3s minimum
    "dlmf.nist.gov":             1.5,
}
DEFAULT_HOST_DELAY = 2.0

# ── HTTP timeout ──────────────────────────────────────────────────────────────
HTTP_TIMEOUT = 30  # seconds

# ── API endpoints that bypass robots.txt ──────────────────────────────────────
# These are documented public APIs whose terms-of-use are the governing document
# (rate limits, UA identification). Their robots.txt is for site crawlers, not
# API consumers. We still respect their published rate limits via HOST_DELAYS.
API_ENDPOINT_PREFIXES = (
    "https://en.wikipedia.org/api/",
    "https://en.wikipedia.org/w/api.php",
    "https://encyclopediaofmath.org/api.php",
    "https://export.arxiv.org/api/",
)


def _is_api_endpoint(url: str) -> bool:
    return any(url.startswith(p) for p in API_ENDPOINT_PREFIXES)



# ═════════════════════════════════════════════════════════════════════════════
# POLITE HTTP CLIENT
# ═════════════════════════════════════════════════════════════════════════════

class PoliteClient:
    """
    Single requests.Session with:
      - per-host last-request-time tracking
      - per-host rate limiting via HOST_DELAYS
      - robots.txt cache + enforcement
      - descriptive User-Agent
      - retry with exponential backoff on 429/5xx
    """

    def __init__(self, user_agent: str = USER_AGENT):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent":      user_agent,
            "Accept":          "application/json, text/html;q=0.9, */*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self._last_request: Dict[str, float] = {}
        self._robots: Dict[str, urllib.robotparser.RobotFileParser] = {}

    # ── robots.txt ────────────────────────────────────────────────────────────

    def _robots_for(self, host: str) -> Optional[urllib.robotparser.RobotFileParser]:
        if host in self._robots:
            return self._robots[host]
        rp = urllib.robotparser.RobotFileParser()
        robots_url = f"https://{host}/robots.txt"
        try:
            r = self.session.get(robots_url, timeout=HTTP_TIMEOUT)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
                self._robots[host] = rp
                _emit("crawl", "robots_loaded", {"host": host})
                return rp
            else:
                # robots.txt missing/forbidden — flag explicitly as "no rules
                # available" so can_fetch() returns True. We bear the politeness
                # burden ourselves via per-host rate limits + descriptive UA.
                log.info(f"robots.txt for {host}: HTTP {r.status_code} — assuming permissive")
                self._robots[host] = None
                return None
        except Exception as e:
            log.warning(f"robots.txt fetch failed for {host}: {e} — assuming permissive")
            self._robots[host] = None
            return None

    def can_fetch(self, url: str) -> bool:
        if _is_api_endpoint(url):
            return True   # documented API — respect API ToS, not site robots.txt
        host = urllib.parse.urlparse(url).hostname or ""
        if not host:
            return False
        rp = self._robots_for(host)
        if rp is None:
            return True   # robots.txt unavailable — proceed politely
        try:
            return rp.can_fetch(USER_AGENT, url)
        except Exception:
            return True  # be permissive on parser errors

    # ── rate limit ────────────────────────────────────────────────────────────

    def _wait_for(self, host: str):
        delay = HOST_DELAYS.get(host, DEFAULT_HOST_DELAY)
        last  = self._last_request.get(host, 0.0)
        gap   = time.monotonic() - last
        if gap < delay:
            time.sleep(delay - gap)
        self._last_request[host] = time.monotonic()

    # ── core GET ──────────────────────────────────────────────────────────────

    def get(self, url: str, *, params: Optional[Dict] = None,
            max_retries: int = 3) -> Optional[requests.Response]:
        """
        Polite GET. Returns Response on 2xx, None on permanent failure.
        Honours robots.txt, per-host rate limits, retries on 429/5xx.
        """
        host = urllib.parse.urlparse(url).hostname or ""

        if not self.can_fetch(url):
            log.warning(f"robots.txt disallows: {url}")
            _emit("crawl", "robots_block", {"url": url})
            return None

        attempt = 0
        while attempt < max_retries:
            self._wait_for(host)
            try:
                r = self.session.get(url, params=params, timeout=HTTP_TIMEOUT)
            except requests.RequestException as e:
                log.warning(f"GET {url} attempt {attempt+1}: {e}")
                _emit("crawl", "http_error", {"url": url, "error": str(e), "attempt": attempt+1})
                attempt += 1
                time.sleep(2 ** attempt)
                continue

            if r.status_code == 200:
                _emit("crawl", "http_ok", {"url": url, "bytes": len(r.content)})
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                # backoff: respect Retry-After if present
                retry_after = r.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** (attempt + 2)
                log.info(f"GET {url} HTTP {r.status_code} — backoff {wait}s")
                _emit("crawl", "http_backoff", {"url": url, "status": r.status_code, "wait": wait})
                time.sleep(wait)
                attempt += 1
                continue

            # 4xx other than 429 — permanent
            log.info(f"GET {url} HTTP {r.status_code} — giving up")
            _emit("crawl", "http_fail", {"url": url, "status": r.status_code})
            return None

        log.warning(f"GET {url} exhausted retries")
        return None


# ═════════════════════════════════════════════════════════════════════════════
# LATEX EXTRACTION
# ═════════════════════════════════════════════════════════════════════════════
# Wikipedia renders math as <math> tags in MediaWiki source, but in rendered
# HTML it appears as:
#   - <math> MathML element
#   - <img class="mwe-math-fallback-image-inline" alt="LaTeX source">
#   - <span class="mwe-math-element">…</span>
#   - <annotation encoding="application/x-tex">LaTeX source</annotation>
#
# MathWorld uses inline images; LaTeX is in the alt text or in a separate
# .tex file linked from the page. PlanetMath ships LaTeX directly. nLab uses
# MathJax with raw LaTeX in $...$ delimiters.

_LATEX_PATTERNS = [
    # MathML annotation with TeX source (Wikipedia, others)
    (re.compile(r'<annotation[^>]+encoding=["\']application/x-tex["\'][^>]*>'
                r'(.*?)</annotation>', re.DOTALL),                        "mathml_annotation"),
    # Wikipedia fallback image alt text
    (re.compile(r'<img[^>]+class=["\'][^"\']*mwe-math-fallback[^"\']*["\']'
                r'[^>]+alt=["\']([^"\']+)["\']', re.DOTALL),               "wiki_fallback_alt"),
    # Wikipedia legacy <img class="tex" alt="...">
    (re.compile(r'<img[^>]+class=["\']tex["\'][^>]+alt=["\']([^"\']+)["\']',
                re.DOTALL),                                                "wiki_tex_alt"),
    # MathJax / KaTeX inline: $...$ or $$...$$
    (re.compile(r'\$\$(.+?)\$\$', re.DOTALL),                              "tex_display"),
    (re.compile(r'(?<![\\$])\$([^\$\n][^\$\n]*?)\$(?!\$)', re.DOTALL),     "tex_inline"),
    # \[ ... \] and \( ... \)
    (re.compile(r'\\\[(.+?)\\\]', re.DOTALL),                              "tex_bracket_display"),
    (re.compile(r'\\\((.+?)\\\)', re.DOTALL),                              "tex_bracket_inline"),
]


def extract_latex(html_or_text: str, source_tag: str) -> List[Dict[str, str]]:
    """
    Pull every LaTeX expression out of a chunk of HTML or plain text.
    Returns a list of dicts: {latex, kind, hash, hyperwebster_address}.
    De-duplicates by SHA-256 of the trimmed LaTeX string.
    """
    found: Dict[str, Dict[str, str]] = {}  # hash -> entry
    for pattern, kind in _LATEX_PATTERNS:
        for m in pattern.finditer(html_or_text):
            raw = m.group(1).strip()
            if not raw or len(raw) < 2:
                continue
            # crude HTML-entity unescape for &lt; &gt; &amp;
            tex = (raw.replace("&lt;", "<")
                      .replace("&gt;", ">")
                      .replace("&amp;", "&")
                      .replace("&quot;", '"'))
            h = hashlib.sha256(tex.encode("utf-8")).hexdigest()[:16]
            if h not in found:
                found[h] = {
                    "latex":                tex,
                    "kind":                 kind,
                    "source":               source_tag,
                    "hash":                 h,
                    "hyperwebster_address": None,   # filled by Callimachus later
                }
    return list(found.values())


# ═════════════════════════════════════════════════════════════════════════════
# SOURCE PLUGINS — each returns a TopicRecord-shaped dict
# ═════════════════════════════════════════════════════════════════════════════

def _topic_record(topic: str) -> Dict[str, Any]:
    return {
        "topic":         topic,
        "first_encountered": datetime.now(timezone.utc).isoformat(),  # Rabies Principle: immutable
        "sources":       {},        # source_id -> {url, fetched_at, ok, ...}
        "formulas":      [],        # list of latex extraction dicts
        "references":    [],        # citations / further reading
        "see_also":      [],        # related topic names for crawl frontier
        "incomplete":    [],        # field names that came back empty
        "hyperwebster_address": None,
    }


# ── Wikipedia REST + Action API ──────────────────────────────────────────────

def fetch_wikipedia(topic: str, client: PoliteClient, record: Dict[str, Any]):
    """Pull Wikipedia article: summary via REST, full HTML via Action API."""
    src = "wikipedia"
    title_url = urllib.parse.quote(topic.replace(" ", "_"))

    # Summary endpoint (REST API) — quick metadata
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_url}"
    _emit("api", "api_call", {"source": src, "endpoint": "summary", "topic": topic})
    r = client.get(summary_url)
    summary_data = None
    if r is not None:
        try:
            summary_data = r.json()
            _emit("api", "api_hit", {"source": src, "endpoint": "summary", "topic": topic})
        except Exception as e:
            log.warning(f"wikipedia summary parse: {e}")

    # Full HTML via Action API parse — gives us the rendered article with math
    parse_url = "https://en.wikipedia.org/w/api.php"
    parse_params = {
        "action":     "parse",
        "page":       topic,
        "prop":       "text|sections|links|externallinks|references",
        "format":     "json",
        "redirects":  1,
        "disablelimitreport": 1,
    }
    _emit("api", "api_call", {"source": src, "endpoint": "parse", "topic": topic})
    r = client.get(parse_url, params=parse_params)
    parse_data = None
    if r is not None:
        try:
            parse_data = r.json()
        except Exception as e:
            log.warning(f"wikipedia parse json: {e}")

    record["sources"][src] = {
        "url":        f"https://en.wikipedia.org/wiki/{title_url}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ok":         parse_data is not None and "parse" in (parse_data or {}),
    }

    if summary_data:
        record["summary"] = summary_data.get("extract")
        record["sources"][src]["page_id"]    = summary_data.get("pageid")
        record["sources"][src]["wikibase"]   = summary_data.get("wikibase_item")

    if parse_data and "parse" in parse_data:
        p = parse_data["parse"]
        html_text = p.get("text", {}).get("*", "")
        if html_text:
            # LaTeX extraction
            record["formulas"].extend(extract_latex(html_text, "wikipedia"))
            # See-also frontier: internal links categorised as math
            for link in p.get("links", []):
                lname = link.get("*")
                if lname:
                    record["see_also"].append(lname)
            # External references (papers, official sites)
            for ext in p.get("externallinks", []):
                if ext:
                    record["references"].append({"source": "wikipedia", "url": ext})
        _emit("api", "api_hit", {"source": src, "endpoint": "parse", "topic": topic,
                                 "formulas": len(record["formulas"])})
    else:
        record["incomplete"].append("wikipedia.parse")
        _emit("api", "api_miss", {"source": src, "topic": topic})


# ── Wolfram MathWorld ────────────────────────────────────────────────────────

def fetch_mathworld(topic: str, client: PoliteClient, record: Dict[str, Any]):
    """MathWorld pages live at mathworld.wolfram.com/<TopicCamelCase>.html"""
    src = "mathworld"
    slug = "".join(w.capitalize() for w in topic.replace("-", " ").split())
    url = f"https://mathworld.wolfram.com/{slug}.html"
    _emit("api", "api_call", {"source": src, "topic": topic, "url": url})
    r = client.get(url)
    record["sources"][src] = {
        "url":        url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ok":         r is not None,
    }
    if r is not None:
        record["formulas"].extend(extract_latex(r.text, "mathworld"))
        _emit("api", "api_hit", {"source": src, "topic": topic})
    else:
        record["incomplete"].append("mathworld")


# ── Encyclopedia of Mathematics ──────────────────────────────────────────────

def fetch_encyclopedia_of_math(topic: str, client: PoliteClient, record: Dict[str, Any]):
    """encyclopediaofmath.org — MediaWiki-based; uses same Action API pattern."""
    src = "encyclopediaofmath"
    parse_url = "https://encyclopediaofmath.org/api.php"
    params = {
        "action":  "parse",
        "page":    topic,
        "prop":    "text|externallinks",
        "format":  "json",
        "redirects": 1,
    }
    _emit("api", "api_call", {"source": src, "topic": topic})
    r = client.get(parse_url, params=params)
    record["sources"][src] = {
        "url":        f"https://encyclopediaofmath.org/wiki/{urllib.parse.quote(topic)}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ok":         False,
    }
    if r is not None:
        try:
            data = r.json()
            if "parse" in data:
                html_text = data["parse"].get("text", {}).get("*", "")
                record["formulas"].extend(extract_latex(html_text, src))
                record["sources"][src]["ok"] = True
                _emit("api", "api_hit", {"source": src, "topic": topic})
        except Exception as e:
            log.warning(f"{src} parse: {e}")
    if not record["sources"][src]["ok"]:
        record["incomplete"].append(src)


# ── PlanetMath ───────────────────────────────────────────────────────────────

def fetch_planetmath(topic: str, client: PoliteClient, record: Dict[str, Any]):
    src  = "planetmath"
    slug = topic.replace(" ", "")
    url  = f"https://planetmath.org/{slug}"
    _emit("api", "api_call", {"source": src, "topic": topic, "url": url})
    r = client.get(url)
    record["sources"][src] = {
        "url":        url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ok":         r is not None,
    }
    if r is not None:
        record["formulas"].extend(extract_latex(r.text, src))
        _emit("api", "api_hit", {"source": src, "topic": topic})
    else:
        record["incomplete"].append(src)


# ── nLab ─────────────────────────────────────────────────────────────────────

def fetch_nlab(topic: str, client: PoliteClient, record: Dict[str, Any]):
    src  = "nlab"
    slug = topic.replace(" ", "+")
    url  = f"https://ncatlab.org/nlab/show/{slug}"
    _emit("api", "api_call", {"source": src, "topic": topic, "url": url})
    r = client.get(url)
    record["sources"][src] = {
        "url":        url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ok":         r is not None,
    }
    if r is not None:
        record["formulas"].extend(extract_latex(r.text, src))
        _emit("api", "api_hit", {"source": src, "topic": topic})
    else:
        record["incomplete"].append(src)


# ── arXiv (citation/abstract only — no full text scraping) ───────────────────

def fetch_arxiv(topic: str, client: PoliteClient, record: Dict[str, Any], max_results: int = 5):
    src = "arxiv"
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"ti:{topic} OR abs:{topic}",
        "max_results":  max_results,
        "sortBy":       "relevance",
    }
    _emit("api", "api_call", {"source": src, "topic": topic})
    r = client.get(url, params=params)
    record["sources"][src] = {
        "url":        f"{url}?{urllib.parse.urlencode(params)}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ok":         r is not None,
    }
    if r is None:
        record["incomplete"].append(src)
        return
    if not LXML_AVAILABLE:
        record["incomplete"].append(src + ".no_lxml")
        return
    try:
        root = etree.fromstring(r.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title   = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            link    = ""
            for l in entry.findall("atom:link", ns):
                if l.get("type") == "text/html":
                    link = l.get("href", "")
                    break
            record["references"].append({
                "source":  src,
                "title":   title,
                "abstract": summary[:500],   # cap — we're a crawler, not a mirror
                "url":     link,
            })
            # arXiv abstracts often contain inline TeX between $...$
            record["formulas"].extend(extract_latex(summary, "arxiv_abstract"))
        _emit("api", "api_hit", {"source": src, "topic": topic,
                                 "results": len(root.findall("atom:entry", ns))})
    except Exception as e:
        log.warning(f"arxiv parse: {e}")
        record["incomplete"].append(src + ".parse")


# ── DLMF (Digital Library of Mathematical Functions, NIST) ───────────────────

def fetch_dlmf(topic: str, client: PoliteClient, record: Dict[str, Any]):
    """DLMF is reference-grade for special functions. Search-only entry."""
    src = "dlmf"
    url = "https://dlmf.nist.gov/search/search"
    params = {"q": topic}
    _emit("api", "api_call", {"source": src, "topic": topic})
    r = client.get(url, params=params)
    record["sources"][src] = {
        "url":        f"{url}?{urllib.parse.urlencode(params)}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ok":         r is not None,
    }
    if r is not None:
        # DLMF search results page — just extract any LaTeX previews and links
        record["formulas"].extend(extract_latex(r.text, src))
        if LXML_AVAILABLE:
            try:
                tree = lxml_html.fromstring(r.content)
                for a in tree.xpath("//a[contains(@href, '/')]"):
                    href = a.get("href", "")
                    if href.startswith("/") and ("." in href.split("/")[-1] or
                                                 href.startswith("/")):
                        record["references"].append({
                            "source": src,
                            "title":  (a.text_content() or "").strip()[:200],
                            "url":    f"https://dlmf.nist.gov{href}",
                        })
            except Exception as e:
                log.warning(f"dlmf parse: {e}")
        _emit("api", "api_hit", {"source": src, "topic": topic})
    else:
        record["incomplete"].append(src)


# ── Plugin registry ──────────────────────────────────────────────────────────

SOURCE_PLUGINS = [
    ("wikipedia",            fetch_wikipedia),
    ("mathworld",            fetch_mathworld),
    ("encyclopediaofmath",   fetch_encyclopedia_of_math),
    ("planetmath",           fetch_planetmath),
    ("nlab",                 fetch_nlab),
    ("arxiv",                fetch_arxiv),
    ("dlmf",                 fetch_dlmf),
]


# ═════════════════════════════════════════════════════════════════════════════
# SHARDING + RESUME
# ═════════════════════════════════════════════════════════════════════════════

def _sanitize_filename(topic: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_\-]+", "_", topic.strip()).strip("_")
    return safe.lower() or "_unnamed"


def shard_dir(topic: str) -> Path:
    first = topic[0].lower() if topic and topic[0].isalpha() else "_"
    d = OUTPUT_ROOT / f"topics_{first}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def topic_path(topic: str) -> Path:
    return shard_dir(topic) / f"{_sanitize_filename(topic)}.json"


def is_complete(topic: str) -> bool:
    p = topic_path(topic)
    if not p.exists():
        return False
    try:
        with open(p) as f:
            data = json.load(f)
        return not data.get("incomplete")
    except Exception:
        return False


def load_existing(topic: str) -> Optional[Dict[str, Any]]:
    p = topic_path(topic)
    if not p.exists():
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def save_record(record: Dict[str, Any]):
    p = topic_path(record["topic"])
    # Rabies Principle: first_encountered must NEVER be overwritten on resume.
    existing = load_existing(record["topic"])
    if existing and "first_encountered" in existing:
        record["first_encountered"] = existing["first_encountered"]
    with open(p, "w") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)


# ═════════════════════════════════════════════════════════════════════════════
# DRIVER
# ═════════════════════════════════════════════════════════════════════════════

def acquire_topic(topic: str, client: PoliteClient,
                  enabled: Optional[List[str]] = None) -> Dict[str, Any]:
    record = _topic_record(topic)
    log.info(f"Acquiring: {topic}")
    _emit("acquire", "topic_start", {"topic": topic})

    plugins = SOURCE_PLUGINS
    if enabled:
        plugins = [(n, f) for (n, f) in SOURCE_PLUGINS if n in enabled]

    for name, fn in plugins:
        try:
            fn(topic, client, record)
        except Exception as e:
            log.error(f"{name} crashed on {topic}: {e}")
            record["incomplete"].append(f"{name}.exception")
            _emit("acquire", "plugin_error", {"source": name, "topic": topic, "error": str(e)})

    # de-duplicate see_also and references
    record["see_also"]   = sorted(set(record["see_also"]))
    record["references"] = list({(r.get("url") or r.get("title") or ""): r
                                  for r in record["references"]}.values())

    _emit("acquire", "topic_done", {
        "topic":      topic,
        "formulas":   len(record["formulas"]),
        "see_also":   len(record["see_also"]),
        "incomplete": record["incomplete"],
    })
    return record


# ── Default seed list ─────────────────────────────────────────────────────────
# Spread across mathematical territories for first-pass shakeout.
DEFAULT_SEEDS = [
    # Foundations
    "Set theory", "Category theory", "Type theory",
    # Algebra
    "Group theory", "Ring theory", "Lie algebra", "Octonion",
    # Analysis
    "Calculus", "Functional analysis", "Measure theory", "Fourier analysis",
    # Number theory
    "Riemann zeta function", "Modular form", "Fermat's Last Theorem", "Prime number theorem",
    # Geometry / Topology
    "Riemannian manifold", "Symplectic manifold", "Kähler manifold",
    "Algebraic topology", "Knot theory",
    # Cohomology
    "K-theory", "Étale cohomology", "Motivic cohomology",
    # Dynamics
    "Ergodic theory", "Dynamical system",
    # Math physics (your territory)
    "Noether's theorem", "Yang–Mills theory", "Standard Model",
    # Special functions reference
    "Gamma function", "Bessel function",
]


def main():
    parser = argparse.ArgumentParser(
        description="Archimedes Math Crawler — acquire mathematical topic records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("topics", nargs="*",
                        help="Topic names to crawl. If omitted, uses --seeds.")
    parser.add_argument("--seeds", action="store_true",
                        help="Run the built-in DEFAULT_SEEDS list.")
    parser.add_argument("--seeds-file", type=Path,
                        help="Read topic names from file (one per line, '#' comments ok).")
    parser.add_argument("--sources", default="",
                        help="Comma-separated source plugins to enable (default: all). "
                             "Choices: " + ",".join(n for n, _ in SOURCE_PLUGINS))
    parser.add_argument("--no-resume", action="store_true",
                        help="Re-fetch even if a complete JSON exists for the topic.")
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT,
                        help=f"Output root (default: {OUTPUT_ROOT})")
    args = parser.parse_args()

    if args.output != OUTPUT_ROOT:
        globals()["OUTPUT_ROOT"] = args.output
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    # Build topic list
    topics: List[str] = list(args.topics)
    if args.seeds:
        topics.extend(DEFAULT_SEEDS)
    if args.seeds_file:
        with open(args.seeds_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    topics.append(line)
    # de-dupe, preserve order
    seen = set()
    topics = [t for t in topics if not (t in seen or seen.add(t))]

    if not topics:
        parser.error("No topics given. Pass topic names, --seeds, or --seeds-file.")

    enabled = [s.strip() for s in args.sources.split(",") if s.strip()] or None
    client  = PoliteClient()

    log.info(f"Archimedes acquire: {len(topics)} topic(s), output → {OUTPUT_ROOT}")
    _emit("acquire", "run_start", {"topics": len(topics), "output": str(OUTPUT_ROOT)})

    ok = skipped = failed = 0
    for topic in topics:
        if not args.no_resume and is_complete(topic):
            log.info(f"  skip (complete): {topic}")
            skipped += 1
            continue
        try:
            record = acquire_topic(topic, client, enabled=enabled)
            save_record(record)
            ok += 1
        except KeyboardInterrupt:
            log.warning("Interrupted by user — partial state saved.")
            break
        except Exception as e:
            log.error(f"Topic crashed: {topic}: {e}")
            failed += 1

    log.info(f"Done. ok={ok}  skipped={skipped}  failed={failed}")
    _emit("acquire", "run_done", {"ok": ok, "skipped": skipped, "failed": failed})


if __name__ == "__main__":
    main()
