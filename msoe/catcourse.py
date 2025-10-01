#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch and parse course catalog listings to course links in markdown.

Supports multiple universities that use the "catalog.UNIVERSITY.edu" Acalog/PHP system.
Default university is 'msoe'. You can select others with -u/--university.
"""

import argparse
import re
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

# Known cur_cat_oid to navoid mappings per university.
# Keep insertion order so we can choose a sensible default cur_cat_oid (the last entry).
NAVOID_LOOKUP: Dict[str, Dict[int, int]] = {
    "msoe": {
        40: 1392,  # UG AY25 June
        41: 1448,  # GR AY25 June
        42: 1486,  # UG AY26
        43: 1542,  # GR AY26
    },
    "unt": {
        20: 2106,  # UG AY19
        37: 4264,  # UG AY26
    },
}

# Validate university token: only lower-case letters, underscore, hyphen.
_UNIVERSITY_RE = re.compile(r"^[a-z_-]+$")


def safe_university_token(u: str) -> str:
    """
    Validate and normalize the university token.

    Allowed characters: a-z, underscore, hyphen. Token is lowercased.
    """
    token = (u or "").lower()
    if not _UNIVERSITY_RE.match(token):
        raise ValueError(
            "Invalid university token. Allowed characters are lower-case letters, '_' and '-'."
        )
    return token


def university_catalog_base(token: str) -> str:
    """
    Build the catalog base URL from the safe token.

    e.g. 'msoe' -> 'https://catalog.msoe.edu'
    """
    token = safe_university_token(token)
    return f"https://catalog.{token}.edu"


# This global will be set in main() based on selected university
NAVOID: Dict[int, int] = {}


def fetch_and_parse_url(
    base_url: str, course_prefix: str, cur_cat_oid: int, navoid: int
) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Fetch the webpage and parse it for course links.

    Parameters:
    base_url (str): The base URL to fetch, e.g. 'https://catalog.msoe.edu/content.php'
    course_prefix (str): The course prefix (e.g., 'CSC').
    cur_cat_oid (int): The cur_cat_oid parameter value.
    navoid (int): The navoid parameter value, -1 to infer from cur_cat_oid

    Returns:
    catalog_title (str)
    course_links (list[tuple[str, str, str]]): List of (number, title, link) tuples.
    """
    if navoid == -1:
        if cur_cat_oid in NAVOID:
            navoid = NAVOID[cur_cat_oid]
        else:
            raise ValueError(f"Cannot infer navoid for {cur_cat_oid=}, use -n")

    params = {"filter[27]": course_prefix, "cur_cat_oid": cur_cat_oid, "navoid": navoid}
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()  # Ensure we notice bad responses

    soup = BeautifulSoup(response.content, "html.parser")
    title_span = soup.find("span", class_="acalog_catalog_name")
    if not title_span:
        raise RuntimeError("Could not find catalog title on the page.")
    catalog_title = title_span.get_text(strip=True)

    # Derive catalog site root from base_url (everything before '/content.php')
    # to correctly form absolute links for each course.
    if "/content.php" in base_url:
        site_root = base_url.split("/content.php", 1)[0]
    else:
        # Fallback: try to trim trailing path and use base
        site_root = base_url.rsplit("/", 1)[0]

    course_links: List[Tuple[str, str]] = []
    for a_tag in soup.find_all("a", href=re.compile(r"^preview_course")):
        text = a_tag.get_text(strip=True)
        if not text:
            continue  # Some entries might lack text; skip them gracefully

        # Split into number and title at the first dash
        parts = re.split(r"\s*-\s*", text, maxsplit=1)
        course_number = parts[0].replace(" ", "")
        course_title = parts[1].strip() if len(parts) > 1 else ""

        # Build an absolute link; replace '_nopop' to get the full page
        href = a_tag.get("href", "")
        course_link = f"{site_root}/{href.replace('_nopop', '')}"

        course_links.append((course_number, course_title, course_link))

    return catalog_title, course_links


def main() -> None:
    """Parse arguments, fetch the webpage, and print results."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-u",
        "--university",
        type=str,
        default="msoe",
        help="University token (before '.edu'), e.g. 'msoe' or 'unt'.",
    )
    parser.add_argument(
        "-p", "--course_prefix", type=str, default="CSC", help="Course prefix"
    )
    # Note: default for cur_cat_oid is resolved dynamically after we know the university
    parser.add_argument(
        "-c",
        "--cur_cat_oid",
        type=int,
        help="cur_cat_oid (defaults to the latest known for the selected university if omitted)",
    )
    parser.add_argument(
        "-n",
        "--navoid",
        type=int,
        default=-1,
        help="navoid (use -1 to infer from built-in mapping when available)",
    )

    args = parser.parse_args()

    try:
        uni_token = safe_university_token(args.university)
    except ValueError as e:
        parser.error(str(e))
        return  # unreachable, but keeps type-checkers happy

    # Determine NAVOID mapping for this university (if known)
    known_mapping = NAVOID_LOOKUP.get(uni_token)

    # Resolve cur_cat_oid default (if needed) based on mapping (if known)
    if known_mapping:
        # Use the last key by insertion order as the default catalog oid
        default_cur = list(known_mapping.keys())[-1]
    else:
        default_cur = None  # Unknown: user must supply -c and -n

    # Choose final cur_cat_oid
    cur_cat_oid = args.cur_cat_oid if args.cur_cat_oid is not None else default_cur

    # If university is unknown, require both -c and -n (navoid must not be -1)
    if known_mapping:
        global NAVOID
        NAVOID = known_mapping.copy()
    else:
        if cur_cat_oid is None or args.navoid == -1:
            parser.error(
                f"Unknown university '{uni_token}'. Supply both -c/--cur_cat_oid and -n/--navoid."
            )

    # Build base URL for the selected university
    catalog_base = university_catalog_base(uni_token)
    base_url = f"{catalog_base}/content.php"

    catalog_title, course_links = fetch_and_parse_url(
        base_url, args.course_prefix, cur_cat_oid, args.navoid
    )

    print(catalog_title)
    for course_number, course_title, course_link in course_links:
        print(f'[{course_number}]: {course_link} "{course_title}"')


if __name__ == "__main__":
    main()
