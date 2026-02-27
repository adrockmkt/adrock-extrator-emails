#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update Fortune 500 list (JSON) automatically.

Strategy:
- Prefer Wikipedia tables that contain columns like Rank + Name/Company.
- Fallback across a small set of candidate URLs.
- Output:
  - data/fortune500/fortune500_<year>.json           (versioned)
  - data/fortune500/fortune500_<year>.meta.json      (versioned metadata)
  - fortune500.json                                  (latest pointer list)
  - fortune500.meta.json                             (latest metadata)

Optionally:
- git add/commit/tag/push
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple, List

import requests

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # pandas is optional but recommended


CANDIDATE_URLS = [
    # Strict source: only the page that contains the full 500-company table
    "https://en.wikipedia.org/wiki/List_of_Fortune_500_companies",
]


STOPWORDS = {
    "inc", "inc.", "incorporated",
    "corp", "corp.", "corporation",
    "co", "co.", "company",
    "ltd", "ltd.", "limited",
    "plc",
    "llc",
    "lp",
    "sa", "s.a",
    "nv", "n.v",
    "ag",
    "the",
    "&",
}


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def safe_run(cmd: list[str], check: bool = True) -> int:
    p = subprocess.run(cmd, check=False)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}")
    return p.returncode


def normalize_company_token(name: str) -> str:
    """
    Produce a stable token suitable for block lists and matching:
    - lowercase
    - strip accents? (kept as-is; can add unidecode if needed)
    - remove punctuation
    - remove common corporate suffixes
    - collapse whitespace
    - join words with single space, then convert spaces to hyphen
    """
    n = name.strip().lower()

    # Replace & with 'and' to stabilize
    n = n.replace("&", " and ")

    # Remove parenthetical notes
    n = re.sub(r"\([^)]*\)", " ", n)

    # Keep alphanumerics and spaces only
    n = re.sub(r"[^a-z0-9\s]", " ", n)

    # Normalize whitespace
    n = re.sub(r"\s+", " ", n).strip()

    # Remove stopwords at the end (suffix trimming)
    parts = n.split()
    while parts and parts[-1] in STOPWORDS:
        parts.pop()

    # Also remove leading "the"
    if parts and parts[0] == "the":
        parts = parts[1:]

    token = "-".join(parts).strip("-")
    return token


def fetch_html(url: str, timeout: int = 30, user_agent: str = "adrock-fortune500-bot/1.0") -> str:
    headers = {"User-Agent": user_agent}
    r = requests.get(
        url,
        headers=headers,
        timeout=timeout,
        allow_redirects=False,
    )
    r.raise_for_status()

    # Hard validation: no redirects allowed.
    if r.is_redirect or r.status_code in (301, 302, 303, 307, 308):
        raise RuntimeError(
            f"Redirect detected. Expected direct Fortune 500 page, got redirect to: {r.headers.get('Location')}"
        )

    final_url = r.url.lower()

    # Accept both canonical Fortune 500 page and the consolidated
    # "largest companies in the United States by revenue" page,
    # which now contains the Fortune 500 table.
    if not (
        final_url.endswith("/list_of_fortune_500_companies")
        or final_url.endswith("/list_of_largest_companies_in_the_united_states_by_revenue")
    ):
        raise RuntimeError(
            f"Unexpected final URL (not recognized Fortune source page): {r.url}"
        )

    if not r.text or len(r.text) < 1000:
        raise RuntimeError(f"HTML response too small or empty for URL: {url}")
    return r.text


def detect_year_from_text(html: str) -> Optional[int]:
    """
    Best-effort: detect a 4-digit year likely representing the list year.
    If not found, fall back to current year.
    """
    # Look for "Fortune 500 list of 2025" patterns etc.
    years = re.findall(r"\b(20\d{2})\b", html)
    if not years:
        return None

    # Use the max year found as a heuristic
    try:
        y = max(int(x) for x in years)
        if 2000 <= y <= (dt.datetime.utcnow().year + 1):
            return y
    except Exception:
        return None
    return None


@dataclass
class ExtractResult:
    companies_raw: list[str]
    companies_tokens: list[str]
    source_url: str
    detected_year: int
    table_signature: str  # helpful for debugging


def extract_from_tables(html: str, source_url: str) -> Optional[ExtractResult]:
    if pd is None:
        return None

    # Pandas read_html can parse multiple tables; we pick the best one.
    try:
        tables = pd.read_html(html, flavor="lxml")
    except Exception as e:
        # Avoid hanging or obscure parser errors
        raise RuntimeError(f"Failed to parse HTML tables via pandas.read_html: {e}")
    best: Optional[Tuple[int, Any, str]] = None  # (score, df, signature)

    for idx, df in enumerate(tables):
        # Hard limit to avoid pathological pages with hundreds of tables
        # Increased limit because the full Fortune 500 table may appear
        # after many auxiliary tables (navboxes, breakdowns, etc.)
        if idx > 100:
            break
        cols = [str(c).strip().lower() for c in df.columns.tolist()]

        # Ignore known non-company tables (e.g., breakdown by state or metro area)
        if any(x in cols for x in ["metropolitan area", "state", "companies"]) and not any(
            x in cols for x in ["company", "name"]
        ):
            continue

        colset = set(cols)

        # Scoring heuristic: prefer tables with Rank + Company/Name
        score = 0
        if any("rank" == c or "rank" in c for c in cols):
            score += 3
        if any("company" == c or "name" == c or "companies" in c for c in cols):
            score += 3
        if any("revenue" in c for c in cols):
            score += 1
        if any("employees" in c for c in cols):
            score += 1

        # Must have at least Rank and Company-ish
        if score < 6:
            continue

        signature = f"table#{idx} cols={cols}"
        if best is None or score > best[0]:
            best = (score, df, signature)

    if best is None:
        return None

    _, df, signature = best
    cols = [str(c).strip() for c in df.columns.tolist()]
    cols_lower = [c.lower() for c in cols]

    # Find name column
    name_col = None
    for target in ["company", "name"]:
        for c, cl in zip(cols, cols_lower):
            if cl == target or target in cl:
                name_col = c
                break
        if name_col:
            break

    if not name_col:
        return None

    raw = (
        df[name_col]
        .astype(str)
        .map(lambda x: x.strip())
        .tolist()
    )

    # Remove obvious non-names
    raw = [x for x in raw if x and x.lower() not in {"nan", "none"}]

    # Deduplicate preserving order
    seen = set()
    raw_unique = []
    for x in raw:
        if x not in seen:
            seen.add(x)
            raw_unique.append(x)

    tokens = [normalize_company_token(x) for x in raw_unique]
    tokens = [t for t in tokens if t]  # remove empty

    # Sanity check: Fortune 500 list must be very close to 500 companies.
    # Reject breakdown tables (state/metro) or partial lists.
    if not (480 <= len(tokens) <= 520):
        return None

    # Additional hard validation:
    # Ensure there is a Rank column and that it spans roughly 1..500.
    rank_col = None
    for c, cl in zip(cols, cols_lower):
        if cl == "rank" or "rank" in cl:
            rank_col = c
            break

    if not rank_col:
        return None

    try:
        ranks = (
            df[rank_col]
            .astype(str)
            .str.extract(r"(\d+)", expand=False)
            .dropna()
            .astype(int)
            .tolist()
        )
    except Exception:
        return None

    if not ranks:
        return None

    min_rank = min(ranks)
    max_rank = max(ranks)

    # Expect something close to 1..500
    if min_rank > 5 or max_rank < 480:
        return None

    # Year detection
    year = detect_year_from_text(html) or dt.datetime.utcnow().year

    return ExtractResult(
        companies_raw=raw_unique,
        companies_tokens=tokens,
        source_url=source_url,
        detected_year=year,
        table_signature=signature,
    )


def extract_fortune500(urls: list[str]) -> ExtractResult:
    last_err = None
    for url in urls:
        try:
            html = fetch_html(url, timeout=20)
            res = extract_from_tables(html, url)
            # Strict acceptance: must already have passed 480..520 + rank validation
            if res:
                return res
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(
        "Could not extract Fortune 500 list from candidate sources. "
        f"Last error: {last_err}"
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-latest", default="fortune500.json", help="Path for latest list JSON")
    ap.add_argument("--out-dir", default="data/fortune500", help="Directory for versioned outputs")
    ap.add_argument("--urls", nargs="*", default=CANDIDATE_URLS, help="Override candidate source URLs")

    ap.add_argument("--commit", action="store_true", help="Run git add + commit for generated files")
    ap.add_argument("--commit-message", default="chore: update fortune500 list (auto)", help="Git commit message")
    ap.add_argument("--tag", default="", help="Optional git tag to create (e.g., v4.3.0)")
    ap.add_argument("--push", action="store_true", help="Push branch and tags after commit/tag")

    args = ap.parse_args()

    out_latest = Path(args.out_latest)
    out_dir = Path(args.out_dir)

    res = extract_fortune500(args.urls)

    # Versioned filenames
    year = res.detected_year
    versioned_json = out_dir / f"fortune500_{year}.json"
    versioned_meta = out_dir / f"fortune500_{year}.meta.json"

    latest_meta = Path("fortune500.meta.json")

    # Payload: tokens only (your “blocklist” style)
    tokens_payload = res.companies_tokens

    meta_payload = {
        "fetched_at_utc": utc_now_iso(),
        "source_url": res.source_url,
        "detected_year": year,
        "count": len(res.companies_tokens),
        "table_signature": res.table_signature,
        "sha256": sha256_text(json.dumps(tokens_payload, ensure_ascii=False)),
        "notes": "Tokens are normalized company identifiers for enterprise-size detection/blocklist. Not official Fortune data dump.",
    }

    # Write versioned + latest
    write_json(versioned_json, tokens_payload)
    write_json(versioned_meta, meta_payload)
    write_json(out_latest, tokens_payload)
    write_json(latest_meta, meta_payload)

    print(f"[OK] Generated:\n- {versioned_json}\n- {versioned_meta}\n- {out_latest}\n- {latest_meta}")
    print(f"[OK] Count: {meta_payload['count']} | Year: {year} | Source: {res.source_url}")

    # Optional git automation
    if args.commit:
        files_to_add = [str(versioned_json), str(versioned_meta), str(out_latest), str(latest_meta)]
        safe_run(["git", "add", *files_to_add])
        safe_run(["git", "commit", "-m", args.commit_message], check=False)  # allow no-op
        if args.tag:
            safe_run(["git", "tag", args.tag])
        if args.push:
            # push current branch
            safe_run(["git", "push", "origin", "HEAD"])
            if args.tag:
                safe_run(["git", "push", "origin", args.tag])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ABORT] Interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)