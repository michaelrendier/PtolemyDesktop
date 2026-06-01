#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Phaleron Search  --  Query interface delegating to Callimachus VastRepository
==============================================================================

Phaleron never touches indexes directly.
Callimachus owns the address spaces; Phaleron is a consumer.

Public interface:
    PhaleronSearch(vast_repository)
        .find(term, category, subject, tags, limit)
        .find_by_url(url)
        .find_by_chunk(chunk_address)
        .find_nearby(entry_id, n)
        .categories()
"""

from Callimachus.vast_repository import VastRepository, Entry, ResearchEntry


class PhaleronSearch:
    """
    Search gateway for Phaleron.  All queries pass through Callimachus.
    """

    def __init__(self, vast: VastRepository):
        self._vast = vast

    # ------------------------------------------------------------------
    # Primary search
    # ------------------------------------------------------------------

    def find(self,
             term:     str  = None,
             category: str  = None,
             subject:  str  = None,
             tags:     list = None,
             limit:    int  = 50) -> list:
        """
        Free-text and NLP-field search.

        Parameters
        ----------
        term     : matches title + body text (case-insensitive substring)
        category : exact category name
        subject  : substring match on subject field
        tags     : all supplied tags must be present on the entry
        limit    : max results (default 50)

        Returns list of Entry / ResearchEntry, newest first.
        """
        return self._vast.search(
            term     = term,
            category = category,
            subject  = subject,
            tags     = tags,
            limit    = limit,
        )

    # ------------------------------------------------------------------
    # Direct lookup
    # ------------------------------------------------------------------

    def find_by_url(self, url: str):
        """
        Retrieve a single entry by its source URL.
        Returns Entry / ResearchEntry or None.
        """
        return self._vast.lookup_by_url(url)

    def find_by_id(self, entry_id: str):
        """
        Retrieve a single entry by its hex entry id.
        Returns Entry / ResearchEntry or None.
        """
        return self._vast.lookup(entry_id)

    # ------------------------------------------------------------------
    # Visual chunk search
    # ------------------------------------------------------------------

    def find_by_chunk(self, chunk_address: str) -> list:
        """
        Find all entries containing a specific HyperGallery chunk address.
        chunk_address is a bare hex string (no 0x prefix).

        Used for visual similarity queries and duplicate detection.
        Returns list of Entry objects.
        """
        return self._vast.chunk_match(chunk_address)

    # ------------------------------------------------------------------
    # Address-space proximity
    # ------------------------------------------------------------------

    def find_nearby(self, entry_id: str, n: int = 10) -> list:
        """
        Return n entries nearest to entry_id in the HyperWebster address space.
        Useful for surfacing related content without explicit tagging.
        """
        return self._vast.proximity(entry_id, n)

    # ------------------------------------------------------------------
    # Catalogue
    # ------------------------------------------------------------------

    def categories(self) -> list:
        """Return all category names currently in the VastRepository."""
        return self._vast.categories()

    def list_category(self, category: str) -> list:
        """Return lightweight index metadata for all entries in a category."""
        return self._vast.list_entries(category)

    # ------------------------------------------------------------------
    # Formatting helpers for the display layer
    # ------------------------------------------------------------------

    @staticmethod
    def summary(entry) -> dict:
        """
        Minimal display-ready dict for a search result row.
        Full entry is passed to PhaleronDisplay for rendering.
        """
        return {
            "id":        entry.id,
            "url":       entry.url,
            "title":     entry.title,
            "subject":   entry.subject,
            "category":  entry.category,
            "tags":      entry.tags,
            "timestamp": entry.timestamp,
            "is_paper":  isinstance(entry, ResearchEntry),
        }
