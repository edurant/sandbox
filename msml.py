#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract a student's advising plan from XLSX master file.
This is a development version with critical functionality not yet implemented.
TODO: Also, this contains some code used for parsing SO assessment files that
may be useful as a baseline for parsing the advising master file.
"""

import os
import re
import argparse
import shutil
from datetime import datetime
from itertools import islice
import pandas as pd
import openpyxl

def check_file_accessibility(filename):
    """ Check if the file is accessible for reading. """
    try:
        with open(filename, 'r') as file:
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

TIME_TAG = datetime.now().strftime('%G%m%dT%H%M%S') # used to tag artifacts created by this run

METADATA = {'Program': 'C3', 'Course Number': 'C5', 'Quarter/Year': 'C7',
    'Section': 'G5', 'Instructor': 'G7', 'Outcome': 'A10', 'Percent Proficient': 'B17'}
LEVEL = ['Exemplary', 'Accomplished', 'Proficient', 'Developing', 'Beginning']

# extract just outcome number from longer string
OUTCOME_NUMBER = [re.compile(r"^\((\w+)\)"), # < AY20
                  re.compile(r"^\[\w+\s(\d)\]")] # >= AY20

def get_pandas(ws):
    """Interpret an Excel worksheet as a pandas DataFrame, minding column headings, etc."""
    # TODO: Determine whether using last name as index causes problems since last name isn't unique
    data = ws.values
    cols = next(data)[1:]
    data = list(data)
    idx = [r[0] for r in data]
    data = (islice(r, 1, None) for r in data)
    df = pd.DataFrame(data, index=idx, columns=cols)
    return df

def get_so_data(full_path):
    """Read summary SO assessment data from the given XLSX file"""
    level_rows = [24, 28, 32, 36, 40]
    level_cols = {'Level_str': 'D', 'Level_int': 'F', 'Count': 'G', 'Percentage': 'F'}

    workbook = openpyxl.load_workbook(full_path, data_only=True) # values, not formulas
    sheet = workbook['Form']
    assert sheet[level_cols['Level_str']+f'{level_rows[0]}'].value == LEVEL[0], \
        'Unexpected format: did not find highest level description where expected'

    data_values = []
    for field, cell in METADATA.items():
        value = sheet[cell].value
        if field == 'Outcome':
            for pattern in OUTCOME_NUMBER:
                if result := pattern.match(value):
                    value = result[1] # discard extra text; [0] is entire match
                    break
        data_values.append(value)

    for row in level_rows:
        data_values.append(sheet[level_cols['Count']+f'{row}'].value)

    return data_values

def main(args):
    """Summarize MSOE EECS SO XLSX files recursively"""
    all_data = []

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

    print(df) # debug

    #col_names = list(METADATA.keys())
    #col_names.extend(LEVEL)

    #dataframe = pd.DataFrame(all_data, columns=col_names)
    #dataframe.to_excel(TIME_TAG+'.xlsx')

if __name__ == "__main__":
    # execute only if run as a script

    data_path = ['OneDrive - Milwaukee School of Engineering', 'MSML Admin', 'msml.xlsx']

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    #parser.add_argument('-y', '--year', type=int, default=2020, help='4-digit academic year')
    parser.add_argument('-f', '--file', type=str,
        default=os.path.join(os.path.expanduser("~"), *data_path),
        help='File to analyze')
    main(parser.parse_args())
