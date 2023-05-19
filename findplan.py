#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find, select, and copy to clipboard MSOE STAT advising file for a given student"""

import os
import argparse
from glob import glob
import hashlib
import pandas as pd
import pyperclip

def main(args):
    """Find all matching advising plans, sort by date, copy user selection to clipboard"""
    found_plan = []
    for pth in args.directory:
        found_plan += glob(f'{pth}/**/{args.name}*.txt', recursive=True)

    data_frame = pd.DataFrame(found_plan, columns=['path'])
    data_frame['mtime'] = pd.to_datetime([int(os.path.getmtime(pth)) for pth in found_plan],
        unit='s') # int truncates to whole seconds
    data_frame['md5'] = ['…'+hashlib.md5(open(pth,'rb').read()).hexdigest()[-4:]
        for pth in found_plan]

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
        ['Box', 'EECS-Transition', '_Updated-Advising-Plans'], # read-only
        ['Box', 'EECS Faculty and Staff', 'Advising Plans'], # writable
        ['Dropbox', 'msoe', 'misc', 'advising', 'specificStudents', 'plans'] # local
    ]
    #    ['Box', 'EECS-Transition', '_Course-Histories'], # not plan, use to make new plan

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', type=str, help='LastName | LastName_FirstName')
    parser.add_argument('-d', '--directory', type=str,
        default=[os.path.join(os.path.expanduser("~"), *pth) for pth in plan_path],
        help='Directories to search')
    main(parser.parse_args())
