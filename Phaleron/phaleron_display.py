#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Phaleron Display  --  Materialise VastRepository entries for presentation
=========================================================================

Phaleron's display layer owns:
    - Entry rendering (text, metadata, research fields)
    - Image regeneration from HyperGallery chunk addresses
    - 32x32 tile interlace (row-major, top-left first)
    - Garbage collection of regenerated image files

Images are regenerated on demand from HyperGallery addresses and written
to a local cache directory.  The GC reaps cache entries not accessed within
GC_TTL_SECONDS.  Canonical storage is always the chunk address list; the
cache is transient.

Public interface:
    PhaleronDisplay(cache_dir)
        .render_entry(entry)        -> dict   (display-ready payload)
        .render_image(image_ref)    -> str    (path to regenerated image file)
        .gc()                                 (reap stale cache entries)
"""

import hashlib
import json
import os
import time
from dataclasses import asdict
from typing import Optional

from Callimachus.vast_repository import Entry, ResearchEntry, ImageRef
from Callimachus.HyperWebster_Data_Storage.hypergallery import (
    HyperGallery, ImageSpec, PixelMode, VectorAddress
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHUNK_SIZE      = 32
GC_TTL_SECONDS  = 86400    # 24 hours


# ---------------------------------------------------------------------------
# PhaleronDisplay
# ---------------------------------------------------------------------------

class PhaleronDisplay:
    """
    Materialises VastRepository entries for human presentation.

    Parameters
    ----------
    cache_dir : str
        Directory where regenerated images are written.
        Created on first use if absent.
    """

    def __init__(self, cache_dir: str = "/tmp/phaleron_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Entry rendering
    # ------------------------------------------------------------------

    def render_entry(self, entry: Entry) -> dict:
        """
        Produce a display-ready dict from an Entry or ResearchEntry.

        Image fields are left as chunk address lists for the caller to
        pass to render_image() on demand; images are not regenerated here.
        """
        base = {
            "id":        entry.id,
            "url":       entry.url,
            "title":     entry.title,
            "text":      entry.text,
            "category":  entry.category,
            "subject":   entry.subject,
            "tags":      entry.tags,
            "timestamp": entry.timestamp,
            "fetcher":   entry.fetcher,
            "images":    entry.images,      # ImageRef dicts, not pixels
            "is_paper":  isinstance(entry, ResearchEntry),
        }

        if isinstance(entry, ResearchEntry):
            base["paper"] = {
                "authors":           entry.authors,
                "published":         entry.published,
                "venue":             entry.venue,
                "doi":               entry.doi,
                "abstract":          entry.abstract,
                "sigma":             entry.sigma,
                "p_value":           entry.p_value,
                "sample_size":       entry.sample_size,
                "confidence_source": entry.confidence_source,
            }

        return base

    # ------------------------------------------------------------------
    # Image regeneration
    # ------------------------------------------------------------------

    def render_image(self, image_ref) -> Optional[str]:
        """
        Regenerate a full image from its HyperGallery chunk addresses.

        Interlace order: row-major, top-left first (same as ingest order).
        Each 32x32 RGB tile is regenerated independently and composited
        onto a canvas of (width, height).

        Returns path to the regenerated PNG file, or None on failure.
        """
        try:
            from PIL import Image as PILImage
        except ImportError:
            return None

        # accept both ImageRef objects and plain dicts
        if isinstance(image_ref, dict):
            chunks     = image_ref.get("chunks", [])
            chunk_size = image_ref.get("chunk_size", CHUNK_SIZE)
            W          = image_ref.get("width",  0)
            H          = image_ref.get("height", 0)
        else:
            chunks     = image_ref.chunks
            chunk_size = image_ref.chunk_size
            W          = image_ref.width
            H          = image_ref.height

        if not chunks or W == 0 or H == 0:
            return None

        # cache key: hash of the chunk list
        cache_key  = hashlib.sha256(
            json.dumps(chunks).encode()
        ).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.png")

        # serve from cache if warm
        if os.path.isfile(cache_path):
            os.utime(cache_path, None)   # touch — reset GC clock
            return cache_path

        # regenerate
        canvas = PILImage.new("RGB", (W, H), (0, 0, 0))
        spec   = ImageSpec(chunk_size, chunk_size, PixelMode.RGB24)

        chunk_idx = 0
        for ty in range(0, H, chunk_size):
            for tx in range(0, W, chunk_size):
                if chunk_idx >= len(chunks):
                    break

                hex_label = chunks[chunk_idx]
                chunk_idx += 1

                try:
                    # hex label → VectorAddress → pixel values
                    # re-insert underscores every 8 hex chars for from_label
                    formatted = "_".join(
                        hex_label[i:i+8]
                        for i in range(0, len(hex_label), 8)
                    )
                    n_values = chunk_size * chunk_size * 3
                    va       = VectorAddress.from_label(formatted, n_values)
                    gallery  = HyperGallery(spec)
                    pixels   = gallery.regenerate_image(
                        type('R', (), {
                            'label':  formatted,
                            'length': n_values,
                        })()
                    )

                    # actual tile size (edge tiles may be smaller)
                    tw = min(chunk_size, W - tx)
                    th = min(chunk_size, H - ty)

                    tile_img = PILImage.new("RGB", (chunk_size, chunk_size))
                    flat     = []
                    for i in range(0, len(pixels), 3):
                        flat.append(tuple(pixels[i:i+3]))
                    tile_img.putdata(flat)

                    # crop padding off edge tiles
                    if tw < chunk_size or th < chunk_size:
                        tile_img = tile_img.crop((0, 0, tw, th))

                    canvas.paste(tile_img, (tx, ty))

                except Exception:
                    continue   # bad chunk → leave black; don't abort

        canvas.save(cache_path, "PNG")
        return cache_path

    # ------------------------------------------------------------------
    # Garbage collection
    # ------------------------------------------------------------------

    def gc(self) -> int:
        """
        Reap regenerated image files not accessed within GC_TTL_SECONDS.
        Returns count of files removed.
        """
        now     = time.time()
        reaped  = 0

        for fname in os.listdir(self.cache_dir):
            if not fname.endswith(".png"):
                continue
            fpath = os.path.join(self.cache_dir, fname)
            try:
                last_access = os.stat(fpath).st_atime
                if (now - last_access) > GC_TTL_SECONDS:
                    os.remove(fpath)
                    reaped += 1
            except OSError:
                continue

        return reaped
