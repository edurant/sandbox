#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Summarize MSOE EECS SO XLSX files recursively"""

# TODO: order by outcome number, course number, section

# TODO: Add columns (N>=pro,N) to summarize as required by process.

# TODO: Format row bands per outcome

# TODO: Year should default to current AY

# TODO: Select year range

import os
import re
import argparse
from datetime import datetime
import pandas as pd
import openpyxl

TIME_TAG = datetime.now().strftime('%G%m%dT%H%M%S') # used to tag artifacts created by this run

METADATA = {'Program': 'C3', 'Course Number': 'C5', 'Quarter/Year': 'C7',
    'Section': 'G5', 'Instructor': 'G7', 'Outcome': 'A10', 'Percent Proficient': 'B17'}
LEVEL = ['Exemplary', 'Accomplished', 'Proficient', 'Developing', 'Beginning']

PROGRAM = {'BME', 'CE', 'CS', 'EE', 'SE'}

# extract just outcome number from longer string
OUTCOME_NUMBER = [re.compile(r"^\((\w+)\)"), # < AY20
                  re.compile(r"^\[\w+\s(\d)\]")] # >= AY20

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
    assert args.program in PROGRAM, f'Program code {args.program} is not recognized'
    assert 1980 < args.year < 2999, f'Academic year ({args.year}) must be in 4-digit format'
    for dirpath, _, filenames in os.walk(os.path.join(args.directory, args.program,
        str(args.year))):
        for filename in filenames:
            if filename.endswith(".xlsx"):
                full_path = os.path.join(dirpath, filename)
                print(full_path)
                all_data.append(get_so_data(full_path))

    col_names = list(METADATA.keys())
    col_names.extend(LEVEL)

    dataframe = pd.DataFrame(all_data, columns=col_names)
    dataframe.to_excel(TIME_TAG+'.xlsx')

if __name__ == "__main__":
    # execute only if run as a script

    assessment_path = ['Box', 'EECS Faculty and Staff', 'EECS Assessment Process',
        'Student Outcome Assessment Forms'] # Next 2 levels: program code, 4-digit AY

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', '--program', type=str, default='CE', help='Academic program code')
    parser.add_argument('-y', '--year', type=int, default=2020, help='4-digit academic year')
    parser.add_argument('-d', '--directory', type=str,
        default=os.path.join(os.path.expanduser("~"), *assessment_path),
        help='Directory to analyze')
    main(parser.parse_args())
