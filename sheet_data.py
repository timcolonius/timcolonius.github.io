#!/usr/bin/env python3
"""Fetch the public-safe Google Sheet (tabs: People, Publications, CV Data)
as an openpyxl workbook.

Both gen_cv_lists.py and build.py read their data through here, so local and
CI builds use the exact same source with no manual download step. The sheet is
a published, public-safe *subset* of the private master workbook.

Override the source with the SHEET_EXPORT_URL env var (e.g. to point at a test
copy) — otherwise the default published sheet below is used.
"""

import os
import sys
from io import BytesIO

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl not found — run: pip install openpyxl")

# Published derived sheet, shared "anyone with the link can view".
SHEET_ID = "1XC5Q-L72w3_q3rGqYa4vKxpWA5wdLCdgSlgCyo36K7g"
DEFAULT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

_cache = None  # downloaded bytes, fetched once per process


def _download() -> bytes:
    global _cache
    if _cache is not None:
        return _cache
    import urllib.request
    import urllib.error
    url = os.environ.get("SHEET_EXPORT_URL") or DEFAULT_URL
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "colonius-site-build"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except urllib.error.URLError as e:
        sys.exit(f"ERROR: could not fetch the spreadsheet.\n  URL: {url}\n  {e}\n"
                 "  Check your network, or that the sheet is shared "
                 "'anyone with the link can view'.")
    if data[:2] != b"PK":  # a real .xlsx is a zip archive → starts with 'PK'
        sys.exit(f"ERROR: fetched data is not a valid .xlsx ({len(data)} bytes).\n"
                 f"  URL: {url}\n  The sheet is probably not shared publicly, "
                 "or the URL is wrong.")
    _cache = data
    return data


def workbook():
    """Return a fresh read-only, data-only openpyxl workbook of the sheet."""
    return openpyxl.load_workbook(BytesIO(_download()), data_only=True, read_only=True)
