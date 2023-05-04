#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find, select, and copy to clipboard MSOE STAT advising file for a given student"""

import os
import argparse
from glob import glob
import pandas as pd
import pyperclip
#import webbrowser

def main(args):
    """Find all matching advising plans, sort by date, copy user selection to clipboard"""
    found_plan = []
    for pth in args.directory:
        found_plan += glob(f'{pth}/**/{args.name}*.txt', recursive=True)

    data_frame = pd.DataFrame(found_plan, columns=['path'])
    data_frame['mtime'] = pd.to_datetime([os.path.getmtime(pth) for pth in found_plan], unit='s')
    data_frame.sort_values(by=['mtime'])

    if data_frame.empty:
        print('No plans found, exiting...')
        return -1

    print(data_frame)

    idx = int(input("Selection? ")) # TODO: Validate type & range
    selected_plan = data_frame.iloc[idx].path
    #pd.set_option('display.max_colwidth', None) # FIXME: Why is this having no effect?
    print(selected_plan)
    pyperclip.copy(selected_plan)
    print('Filename copied to clipboard')

    # Pushing the filename into the STAT webapp isn't functional.
    #html_file_path = os.path.abspath("findplan-bridge.html")
    #webbrowser.open(f"file://{html_file_path}?filename={selected_plan}")

if __name__ == "__main__":
    # execute only if run as a script
    plan_path = [
        ['Box', 'EECS-Transition', '_Updated-Advising-Plans'], # read-only
        ['Box', 'EECS Faculty and Staff', 'Advising Plans'], # writable
        ['Dropbox', 'msoe', 'misc', 'advising', 'specificStudents', 'plans'] # local
    ]
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', type=str, help='LastName | LastName_FirstName')
    parser.add_argument('-d', '--directory', type=str,
        default=[os.path.join(os.path.expanduser("~"), *pth) for pth in plan_path],
        help='Directories to search')
    main(parser.parse_args())
