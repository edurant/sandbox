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
    data_frame = pd.DataFrame(found_plan, columns=['path'])
    data_frame['mtime'] = pd.to_datetime([int(os.path.getmtime(pth)) for pth in found_plan],
        unit='s') # int truncates to whole seconds
    data_frame['sha224'] = ['…'+hashlib.file_digest(open(pth,'rb'), "sha224")
        .hexdigest()[-4:] for pth in found_plan]

    # Filter and sort
    data_frame = data_frame.loc[data_frame.groupby('sha224')['mtime'].idxmin()] # oldest only
    data_frame = data_frame.sort_values(by=['mtime'], ascending=False, ignore_index=True)

    if data_frame.empty:
        print('No plans found, exiting...')
        return -1

    pd.options.display.max_colwidth = None
    print(data_frame)

    idx = int(input("Selection? ")) # TODO: Validate type & range
    selected_plan = data_frame.iloc[idx].path

    print(selected_plan)
    pyperclip.copy(selected_plan)
    print('Filename copied to clipboard')

    return 0

if __name__ == "__main__":
    # execute only if run as a script
    plan_path = [
        ['Box', 'EECS-Transition', '_Updated-Advising-Plans'], # PD read-only
        ['Box', 'EECS Faculty and Staff', 'Advising Plans'], # PD writable
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
