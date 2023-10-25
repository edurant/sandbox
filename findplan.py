#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find, select, and copy to clipboard MSOE STAT advising file for a given student"""

import os
import argparse
from glob import glob
from warnings import warn
import hashlib
import pandas as pd
import pyperclip

def ranged_input(upper_end):
    """Prompt the user until they enter an int between 0 and argument"""
    while True:
        user_input = input(f"Selection (0-{upper_end})? ")
        try:
            idx = int(user_input)
            if 0 <= idx <= upper_end:
                return idx
            print(f"Please enter an integer between 0 and {upper_end} inclusive.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

def file_sha224(pth):
    """Encapsulate file opening, hashing, and closing operations"""
    with open(pth, 'rb') as file:
        return hashlib.file_digest(file, "sha224").hexdigest()[-4:]

def main(args):
    """Find all matching advising plans, sort by date, copy user selection to clipboard"""
    # Build the list of plans
    found_plan = []
    for pth in args.directory:
        if os.path.isdir(pth):
            found_plan += glob(f'{pth}/**/{args.name}*.txt', recursive=True)
        else:
            warn(f"Directory not found: {pth}")
    found_plan = [p for p in found_plan if "courseHistories" not in p]

    # Create DataFrame with all plan information
    data_frame = pd.DataFrame({
        'path': found_plan,
        'mtime': pd.to_datetime([int(os.path.getmtime(pth)) for pth in found_plan], unit='s'),
        'sha224': ['…' + file_sha224(pth) for pth in found_plan]
    })

    # Filter and sort
    data_frame = data_frame.loc[data_frame.groupby('sha224')['mtime'].idxmin()] # oldest only
    data_frame = data_frame.sort_values(by=['mtime'], ascending=False, ignore_index=True)

    if data_frame.empty:
        print('No plans found, exiting...')
        return -1

    pd.options.display.max_colwidth = None
    print(data_frame)

    selected_plan = data_frame.iloc[ranged_input(data_frame.index.max())].path

    print(selected_plan)
    pyperclip.copy(selected_plan)
    print('Filename copied to clipboard')

    return 0

if __name__ == "__main__":
    # execute only if run as a script
    plan_path = [
        ['Box', 'EECS-Transition', '_Updated-Advising-Plans'], # PD read-only
        ['Box', 'EECS Faculty and Staff', 'Advising Plans [DO NOT UPLOAD HERE]'], # former PD write
        ['Box', 'EECS Advising Plans'], # all-advisor writable, PD readable
        ['Dropbox', 'msoe', 'misc', 'advising', 'specificStudents', 'plans'] # local
    ]
    #    ['Box', 'EECS-Transition', '_Course-Histories'], # not plan, use to make new plan
    home_path = os.path.expanduser("~")
    plan_path = [os.path.join(home_path, *pth) for pth in plan_path]
    plan_path.extend(glob(os.path.join(home_path, "Box", "STAT-*/"))) # advisor-specific

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', type=str, help='LastName | LastName_FirstInit | LastName_FirstName')
    parser.add_argument('-d', '--directory', type=str, default=plan_path,
        help='Directories to search')
    main(parser.parse_args())
