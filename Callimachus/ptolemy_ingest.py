#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
ptolemy_ingest  --  Web Ingestion Pipeline
==========================================

Fetches, cleans, NLP-tags, and writes pages to the VastRepository.

Fetch routing:
    requests    static HTML, PHP-rendered, Node/Express server-side
    lynx        malformed / tag-sparse / query-string-heavy responses
    (JS-dependent dynamic content is a separate headless path, not here)

Image handling:
    Each <img> in the content body div is tiled into 32x32 RGB chunks,
    addressed through HyperGallery, and stored as an ImageRef on the entry.
    No raw image files are stored.  Phaleron regenerates on demand.

NLP tagging:
    spaCy en_core_web_sm assigns category, subject, tags to every entry.
    ResearchEntry is used when paper metadata (DOI, abstract, sigma) is found.

Public interface:
    ingest_page(url, vast_repository) -> Entry | ResearchEntry
"""

import hashlib
import re
import subprocess
import time
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse, urlunparse, urlencode, parse_qs

import requests
from lxml import html as lxml_html
import html2text
import spacy

from Callimachus.vast_repository import (
    VastRepository, Entry, ResearchEntry, ImageRef, _entry_id
)
from Callimachus.HyperWebster_Data_Storage.hypergallery import (
    HyperGallery, ImageSpec, PixelMode
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHUNK_SIZE   = 32
REQUESTS_UA  = ("Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36")
FETCH_TIMEOUT = 15   # seconds
IMG_CONTEXT   = 120  # chars either side of <img> in text
MAX_IMG_FETCH  = 50  # per page cap


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class IngestResult:
    entry_id:   str
    table:      str
    subject:    str
    text:       str
    images:     list
    confidence: float
    entry:      object   # Entry | ResearchEntry


# ---------------------------------------------------------------------------
# URL normalisation
# ---------------------------------------------------------------------------

_STRIP_PARAMS = re.compile(
    r'[?&](utm_\w+|fbclid|gclid|ref|session\w*|sid|token)=[^&]*',
    re.IGNORECASE
)

def _normalise_url(url: str) -> str:
    url = _STRIP_PARAMS.sub('', url)
    url = url.rstrip('/')
    parsed = urlparse(url)
    return urlunparse(parsed)


# ---------------------------------------------------------------------------
# Fetch routing
# ---------------------------------------------------------------------------

def _needs_lynx(raw_html: str) -> bool:
    tag_count   = len(re.findall(r'<[a-zA-Z]', raw_html))
    query_count = raw_html.count('?')
    return tag_count < 10 and query_count > 20


def _fetch_requests(url: str) -> Optional[str]:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": REQUESTS_UA},
            timeout=FETCH_TIMEOUT
        )
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def _fetch_lynx_text(url: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["lynx", "-dump", "-nolist", "-image_links", url],
            capture_output=True, text=True, timeout=FETCH_TIMEOUT
        )
        return result.stdout or None
    except Exception:
        return None


def _fetch_lynx_images(url: str) -> list:
    try:
        result = subprocess.run(
            ["lynx", "-dump", "-listonly", "-image_links", url],
            capture_output=True, text=True, timeout=FETCH_TIMEOUT
        )
        return [ln.strip() for ln in result.stdout.splitlines()
                if ln.strip().startswith("http")]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# HTML extraction
# ---------------------------------------------------------------------------

_H2T = html2text.HTML2Text()
_H2T.ignore_links   = False
_H2T.ignore_images  = True
_H2T.body_width     = 0


def _extract_body_div(raw_html: str):
    """Return the most likely content container element via lxml."""
    tree = lxml_html.fromstring(raw_html)

    # prefer explicit content containers
    for selector in (
        'article', 'main', '[role="main"]',
        '#content', '#main', '.content', '.post', '.article',
        'div.entry', 'div.post', 'div#article'
    ):
        nodes = tree.cssselect(selector)
        if nodes:
            return nodes[0]

    # fallback: largest <div> by text length
    divs = tree.cssselect('div')
    if divs:
        return max(divs, key=lambda d: len(d.text_content()))

    return tree.find('.//body') or tree


def _extract_title(raw_html: str) -> str:
    try:
        tree  = lxml_html.fromstring(raw_html)
        title = tree.findtext('.//title') or ""
        h1    = tree.findtext('.//h1')   or ""
        return (h1.strip() or title.strip())
    except Exception:
        return ""


def _html_to_text(element) -> str:
    from lxml import etree
    raw = etree.tostring(element, encoding="unicode", method="html")
    return _H2T.handle(raw).strip()


def _surrounding_context(element, full_text: str) -> str:
    """Grab ±IMG_CONTEXT chars around element's text in the page text."""
    snippet = (element.text_content() or "")[:30]
    pos     = full_text.find(snippet)
    if pos == -1:
        return ""
    start = max(0, pos - IMG_CONTEXT)
    end   = min(len(full_text), pos + IMG_CONTEXT)
    return full_text[start:end]


# ---------------------------------------------------------------------------
# HyperGallery chunk addressing
# ---------------------------------------------------------------------------

def _fetch_image_bytes(src_url: str) -> Optional[bytes]:
    try:
        resp = requests.get(
            src_url,
            headers={"User-Agent": REQUESTS_UA},
            timeout=FETCH_TIMEOUT
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def _pixels_to_chunks(raw_pixels: list, W: int, H: int,
                      gallery: HyperGallery) -> list:
    """
    Tile an RGB pixel value list into CHUNK_SIZE x CHUNK_SIZE tiles.
    Each tile → HyperGallery address → bare hex string.
    Returns ordered list of hex chunk addresses (row-major, top-left first).
    Edge tiles are zero-padded to CHUNK_SIZE x CHUNK_SIZE.
    """
    C   = CHUNK_SIZE
    chunks = []

    for ty in range(0, H, C):
        for tx in range(0, W, C):
            tile_vals = []
            for py in range(C):
                for px in range(C):
                    sx = tx + px
                    sy = ty + py
                    if sx < W and sy < H:
                        base = (sy * W + sx) * 3
                        tile_vals += raw_pixels[base:base+3]
                    else:
                        tile_vals += [0, 0, 0]   # zero-pad edge

            spec = ImageSpec(C, C, PixelMode.RGB24)
            tg   = HyperGallery(spec)
            rec  = tg.index_image(tile_vals)
            # bare hex: VectorAddress label strips underscores → single hex run
            chunks.append(rec.label.replace("_", ""))

    return chunks


def _store_image(src_url: str, alt: str, context: str) -> Optional[ImageRef]:
    """
    Fetch image, tile into 32x32 RGB chunks, store via HyperGallery.
    Returns ImageRef or None on failure.
    """
    from PIL import Image
    import io

    raw_bytes = _fetch_image_bytes(src_url)
    if not raw_bytes:
        return None

    try:
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        W, H = img.size
        raw_pixels = list(img.tobytes())  # flat R G B R G B ...

        spec    = ImageSpec(C := CHUNK_SIZE, C, PixelMode.RGB24)
        gallery = HyperGallery(spec)
        chunks  = _pixels_to_chunks(raw_pixels, W, H, gallery)

        return ImageRef(
            chunks     = chunks,
            chunk_size = CHUNK_SIZE,
            width      = W,
            height     = H,
            alt        = alt,
            context    = context,
            source_url = src_url,
        )
    except Exception:
        return None


def _collect_images(body_element, page_text: str,
                    base_url: str) -> list:
    """
    Extract <img> tags from body element, store each via HyperGallery.
    Returns list of ImageRef objects.
    """
    refs  = []
    count = 0

    for img_el in body_element.cssselect('img'):
        if count >= MAX_IMG_FETCH:
            break

        src = img_el.get('src', '').strip()
        if not src:
            continue

        src = urljoin(base_url, src)
        alt = img_el.get('alt', '').strip()
        ctx = _surrounding_context(img_el, page_text)

        ref = _store_image(src, alt, ctx)
        if ref:
            refs.append(ref)
            count += 1

    return refs


# ---------------------------------------------------------------------------
# NLP tagging
# ---------------------------------------------------------------------------

try:
    _NLP = spacy.load("en_core_web_sm")
except OSError:
    _NLP = None


# Fixed category vocabulary — NLP classifies into this set.
# New categories require deliberate addition here.
_CATEGORIES = [
    "web_research",
    "research_paper",
    "mathematics",
    "physics",
    "chemistry",
    "biology",
    "computer_science",
    "history",
    "philosophy",
    "literature",
    "geography",
    "technology",
    "medicine",
    "astronomy",
    "engineering",
    "economics",
    "art",
    "law",
    "linguistics",
    "miscellaneous",
]

# Paper-domain signals for ResearchEntry routing
_PAPER_DOMAINS = re.compile(
    r'(arxiv\.org|doi\.org|pubmed|nature\.com/articles|'
    r'science\.org|nih\.gov|semanticscholar|jstor\.org|'
    r'springer\.com|wiley\.com|tandfonline|ieee\.org)',
    re.IGNORECASE
)
_DOI_RE = re.compile(r'10\.\d{4,9}/[^\s"<>]+')


def _is_research(url: str, raw_html: str) -> bool:
    if _PAPER_DOMAINS.search(url):
        return True
    if url.lower().endswith('.pdf'):
        return True
    if _DOI_RE.search(raw_html[:4000]):
        return True
    return False


def _classify_category(doc) -> str:
    """
    Classify into fixed vocabulary using spaCy NER entity types.
    Falls back to noun-chunk similarity against category strings.
    """
    if _NLP is None:
        return "web_research"

    ent_type_map = {
        "ORG": "technology", "PRODUCT": "technology",
        "GPE": "geography",  "LOC": "geography",
        "PERSON": "history", "NORP": "history",
        "LAW": "law",        "EVENT": "history",
        "WORK_OF_ART": "art","LANGUAGE": "linguistics",
        "MONEY": "economics","PERCENT": "economics",
    }

    ent_counts: dict = {}
    for ent in doc.ents:
        cat = ent_type_map.get(ent.label_)
        if cat:
            ent_counts[cat] = ent_counts.get(cat, 0) + 1

    if ent_counts:
        return max(ent_counts, key=ent_counts.get)

    # noun-chunk frequency fallback
    chunks = [c.root.lemma_.lower() for c in doc.noun_chunks]
    if not chunks:
        return "web_research"

    freq: dict = {}
    for c in chunks:
        freq[c] = freq.get(c, 0) + 1

    top = max(freq, key=freq.get)

    # map top noun to nearest category
    science_words = {"equation","theorem","proof","algorithm","network",
                     "circuit","particle","molecule","cell","gene","orbit",
                     "quantum","neural","matrix","vector","tensor"}
    if top in science_words:
        return "mathematics"

    return "web_research"


def _extract_subject(title: str, doc) -> str:
    """
    Derive a 1–5 word title-case noun-phrase subject.
    Weights <h1>/title heavily; uses top TF noun chunk as fallback.
    """
    STOPWORDS = {"the","a","an","of","in","on","at","to","for",
                 "and","or","but","is","are","was","were","with"}

    if title:
        words = [w for w in title.split() if w.lower() not in STOPWORDS]
        if words:
            return " ".join(words[:5]).title()

    chunks = list(doc.noun_chunks)
    if chunks:
        by_len = sorted(chunks, key=lambda c: len(c.text), reverse=True)
        words  = [w for w in by_len[0].text.split()
                  if w.lower() not in STOPWORDS]
        return " ".join(words[:5]).title()

    return title[:50].title() if title else "Unknown"


def _extract_tags(doc, n: int = 8) -> list:
    """
    Top-n noun chunks + named entities, deduplicated, lowercase.
    """
    seen: set = set()
    tags: list = []

    for ent in doc.ents:
        t = ent.text.strip().lower()
        if t and t not in seen:
            seen.add(t)
            tags.append(t)

    for chunk in doc.noun_chunks:
        t = chunk.root.lemma_.strip().lower()
        if t and t not in seen:
            seen.add(t)
            tags.append(t)

    return tags[:n]


def _nlp_tag(title: str, text: str) -> dict:
    if _NLP is None:
        return {"category": "web_research", "subject": title or "Unknown",
                "tags": []}

    preview = title + ". " + text[:2000]
    doc     = _NLP(preview)

    return {
        "category": _classify_category(doc),
        "subject":  _extract_subject(title, doc),
        "tags":     _extract_tags(doc),
    }


# ---------------------------------------------------------------------------
# Research paper metadata extraction
# ---------------------------------------------------------------------------

_SIGMA_RE    = re.compile(r'(\d+\.?\d*)\s*[σ-]?sigma', re.IGNORECASE)
_PVALUE_RE   = re.compile(r'p\s*[=<]\s*(0\.\d+)', re.IGNORECASE)
_SAMPLE_RE   = re.compile(r'n\s*=\s*(\d+)', re.IGNORECASE)
_ABSTRACT_RE = re.compile(
    r'<(?:div|section|p)[^>]*(?:id|class)=["\']?abstract["\']?[^>]*>'
    r'(.*?)</(?:div|section|p)>',
    re.IGNORECASE | re.DOTALL
)


def _extract_paper_meta(raw_html: str, text: str, url: str) -> dict:
    meta: dict = {}

    # DOI
    doi_match = _DOI_RE.search(raw_html[:8000])
    if doi_match:
        meta["doi"] = doi_match.group(0).rstrip('.,;)')

    # abstract
    abs_match = _ABSTRACT_RE.search(raw_html)
    if abs_match:
        abs_text = re.sub(r'<[^>]+>', '', abs_match.group(1)).strip()
        meta["abstract"] = abs_text[:1500]
        search_text = abs_text
    else:
        search_text = text[:3000]

    # sigma
    sig = _SIGMA_RE.search(search_text)
    if sig:
        meta["sigma"]             = float(sig.group(1))
        meta["confidence_source"] = "abstract"

    # p-value
    pv = _PVALUE_RE.search(search_text)
    if pv:
        meta["p_value"] = float(pv.group(1))

    # sample size
    ss = _SAMPLE_RE.search(search_text)
    if ss:
        meta["sample_size"] = int(ss.group(1))

    # venue from <meta> tags
    tree = lxml_html.fromstring(raw_html)
    for attr in ('citation_journal_title', 'og:site_name'):
        node = tree.cssselect(f'meta[name="{attr}"], meta[property="{attr}"]')
        if node:
            meta["venue"] = node[0].get("content", "").strip()
            break

    # authors
    authors = []
    for node in tree.cssselect('meta[name="citation_author"]'):
        a = node.get("content", "").strip()
        if a:
            authors.append(a)
    if authors:
        meta["authors"] = authors

    # published date
    for attr in ('citation_date', 'article:published_time', 'date'):
        node = tree.cssselect(f'meta[name="{attr}"], meta[property="{attr}"]')
        if node:
            meta["published"] = node[0].get("content", "")[:10]
            break

    return meta


# ---------------------------------------------------------------------------
# Main ingest function
# ---------------------------------------------------------------------------

def ingest_page(url: str,
                vast: VastRepository) -> IngestResult:
    """
    Fetch, clean, NLP-tag, image-store, and write one page to VastRepository.

    Parameters
    ----------
    url  : target URL
    vast : open VastRepository instance

    Returns
    -------
    IngestResult with entry_id, table, subject, text, images, confidence, entry
    """
    url      = _normalise_url(url)
    eid      = _entry_id(url)
    ts       = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # --- fetch ---
    raw_html = _fetch_requests(url)
    fetcher  = "requests"

    if raw_html is None or _needs_lynx(raw_html or ""):
        raw_html = _fetch_requests(url)   # retry once
        if raw_html is None:
            fetcher  = "lynx"
            raw_html = ""

    if fetcher == "lynx" or (raw_html and _needs_lynx(raw_html)):
        fetcher  = "lynx"
        raw_text = _fetch_lynx_text(url) or ""
        title    = ""
        images_  = []
    else:
        # --- extract body ---
        body     = _extract_body_div(raw_html)
        title    = _extract_title(raw_html)
        raw_text = _html_to_text(body)
        images_  = _collect_images(body, raw_text, url)

    # --- NLP ---
    nlp_result = _nlp_tag(title, raw_text)
    category   = nlp_result["category"]
    subject    = nlp_result["subject"]
    tags       = nlp_result["tags"]

    # --- build entry ---
    base_fields = dict(
        id        = eid,
        url       = url,
        fetcher   = fetcher,
        timestamp = ts,
        title     = title,
        text      = raw_text,
        category  = category,
        subject   = subject,
        tags      = tags,
        images    = [vars(img) if isinstance(img, ImageRef) else img
                     for img in images_],
    )

    is_paper = (category == "research_paper") or _is_research(url, raw_html)

    if is_paper:
        paper_meta = _extract_paper_meta(raw_html, raw_text, url)
        entry = ResearchEntry(**base_fields, **paper_meta)
    else:
        entry = Entry(**base_fields)

    # --- store ---
    vast.store(entry)

    return IngestResult(
        entry_id   = eid,
        table      = category,
        subject    = subject,
        text       = raw_text,
        images     = images_,
        confidence = 1.0 if is_paper and paper_meta.get("doi") else 0.0,
        entry      = entry,
    )
