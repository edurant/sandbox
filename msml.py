#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract a student's advising plan from XLSX master file.
TODO: Check graduation requirements
"""

import os
import re
import argparse
import shutil
from itertools import islice
import pprint
import numpy as np
import pandas as pd
import openpyxl

def check_file_accessibility(filename):
    """ Check if the file is accessible for reading. """
    try:
        with open(filename, 'rb'):
            return True
    except PermissionError:
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def create_local_copy(source_path, destination_path=os.path.join('.','temp.xlsx')):
    """ Create a local copy of the file. """
    try:
        # .copy and .copyfile fail to read when locked even though xcopy and .copy2 succeed
        shutil.copy2(source_path, destination_path)
        # TODO: Don't leave temp.xlsx in place when exiting
        return True
    except Exception as e:
        print(f"Error while creating a local copy: {e}")
        return False

def get_pandas(ws):
    """Interpret an Excel worksheet as a pandas DataFrame, minding column headings, etc."""
    # TODO: Consider dropping historic students, or tagging them in output
    data = ws.values
    cols = next(data)[1:]
    data = list(data)
    idx = [r[0] for r in data]
    data = (islice(r, 1, None) for r in data)
    df = pd.DataFrame(data, index=idx, columns=cols)
    return df

TERMS = {1: 'Fall', 2: 'Spring', 3: 'Summer'}

def semester_code_to_string(code):
    """Convert a semester code like 1S24 to a description like Fall, '23"""
    m = re.match(r'(\d)S(\d{2})', code)
    sem, yr = [int(m.group(i)) for i in [1, 2]]
    if sem == 0:
        yr = yr - 1
        sem = sem + len(TERMS)
    elif sem == 1: # academic year to calendar year
        yr = yr - 1
    return f"{TERMS[sem]}, '{yr}"

def get_class_list(record):
    """Given student record as pandas.Series, extract courses as dictionary of list per semester"""

    matched_dict = {} # Create a dictionary to hold the matching elements

    # Iterate over the series and group values by matching labels
    for label, value in record.items():
        m = re.match(r'^(\dS\d{2}) ', label)
        if m: # Is it a course?
            label = semester_code_to_string(m.group(1))
            if label not in matched_dict:
                matched_dict[label] = []
            matched_dict[label].append(value)
    return matched_dict

def main(args):
    """Find a specified student and summarize their record"""
    if check_file_accessibility(args.file):
        print("File is accessible for reading.")
    else:
        print("File is not accessible. Assuming OneDrive lock.")
        if create_local_copy(args.file):
            print("Local copy created successfully.")
            args.file = 'temp.xlsx'
        else:
            print("Failed to create a local copy. Cannot proceed.")
            args.file = None
            return -1

    # Load the workbook and select the first worksheet
    wb = openpyxl.load_workbook(args.file, data_only=True)
    ws = wb.active

    df = get_pandas(ws)

    [ln, _, fn] = args.name.partition('_')
    df = df.loc[[ln]]
    if fn:
        df = df[df['First Name'] == fn]
    if df.shape[0] != 1:
        print(f'{df.shape[0]} records matching {args.name}: {df['First Name'].tolist()}, exiting…')
        return -1

    record = df.iloc[0]
    record = record[record.notnull()]
    record = record.transform(lambda c: int(c) if isinstance(c, np.float64) and c == int(c) else c)
    print(record)

    classes = get_class_list(record)
    pprint.pprint(classes, sort_dicts=False)

if __name__ == "__main__":
    # execute only if run as a script

    data_path = ['OneDrive - Milwaukee School of Engineering', 'MSML Admin', 'msml.xlsx']

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', type=str, help='LastName (if unique) | LastName_FirstName')
    parser.add_argument('-f', '--file', type=str,
        default=os.path.join(os.path.expanduser("~"), *data_path),
        help='File to analyze')
    main(parser.parse_args())
