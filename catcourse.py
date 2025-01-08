#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Fetch and parse MSOE course catalog to course links in markdown."""

import re
import argparse
import requests
from bs4 import BeautifulSoup

NAVOID = {  # map from cur_cat_oid to navoid
    40: 1392,  # UG AY25 June
    41: 1448,  # GR AY25 June
}


def fetch_and_parse_url(base_url, course_prefix, cur_cat_oid, navoid):
    """
    Fetch the webpage and parse it for course links.

    Parameters:
    base_url (str): The base URL to fetch.
    course_prefix (str): The course prefix.
    cur_cat_oid (int): The cur_cat_oid parameter value.
    navoid (int): The navoid parameter value, -1 to infer from cur_cat_oid

    Returns:
    catalog title
    list of tuples: List of (course_number, course_link) tuples.
    """
    if navoid == -1:
        if cur_cat_oid in NAVOID:
            navoid = NAVOID[cur_cat_oid]
        else:
            raise ValueError(
                f"Cannot infer navoid for cur_cat_oid={cur_cat_oid}, use -n"
            )

    params = {"filter[27]": course_prefix, "cur_cat_oid": cur_cat_oid, "navoid": navoid}
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()  # Ensure we notice bad responses

    soup = BeautifulSoup(response.content, "html.parser")
    catalog_title = soup.find("span", class_="acalog_catalog_name").get_text(strip=True)
    course_links = []

    for a_tag in soup.find_all("a", href=re.compile(r"^preview_course")):
        course_number = re.split(r"\s*-\s*", a_tag["title"])[0].replace(" ", "")
        course_link = f"https://catalog.msoe.edu/{a_tag['href'].replace('_nopop', '')}"
        course_links.append((course_number, course_link))

    return catalog_title, course_links


def main():
    """Parse arguments, parse the webpage, and print the results."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-p", "--course_prefix", type=str, default="CSC", help="Course prefix"
    )
    parser.add_argument(
        "-c",
        "--cur_cat_oid",
        type=int,
        default=list(NAVOID.keys())[-1],
        help="cur_cat_oid",
    )
    parser.add_argument(
        "-n", "--navoid", type=int, default=-1, help="navoid, -1 to infer"
    )
    args = parser.parse_args()

    base_url = "https://catalog.msoe.edu/content.php"

    catalog_title, course_links = fetch_and_parse_url(
        base_url, args.course_prefix, args.cur_cat_oid, args.navoid
    )

    print(catalog_title)
    for course_number, course_link in course_links:
        print(f"[{course_number}]: {course_link}")


if __name__ == "__main__":
    main()
