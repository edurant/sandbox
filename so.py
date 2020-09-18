#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Summarize MSOE EECS SO XLSX files recursively"""

# TODO: Update OUTCOME_NUMBER re to handle new format from AY20. Currently pass without condensing.

# TODO: Simpler args for selecting program or (program, year)

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

OUTCOME_NUMBER = re.compile(r"^\((\w+)\)") # extract just output number from longer string

def get_so_data(full_path):
    """Read summary SO assessment data from the given XLSX file"""
    level_rows = [24, 28, 32, 36, 40]
    level_cols = {'Level_str': 'D', 'Level_int': 'F', 'Count': 'G', 'Percentage': 'F'}

    workbook = openpyxl.load_workbook(full_path, data_only=True) # values, not formulas
    sheet = workbook['Form']
    assert sheet[level_cols['Level_str']+f'{level_rows[0]}'].value == LEVEL[0], \
        'Unexpected format: did not find highest level description where expected'

    data_values = []
    for key in METADATA:
        value = sheet[METADATA[key]].value
        if key == 'Outcome':
            if result := OUTCOME_NUMBER.match(value):
                value = result[0] # discard extra text if pattern is matched
        data_values.append(value)

    for row in level_rows:
        data_values.append(sheet[level_cols['Count']+f'{row}'].value)

    return data_values

def main(args):
    """Summarize MSOE EECS SO XLSX files recursively"""
    all_data = []
    for dirpath, _, filenames in os.walk(args.directory):
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
        'Student Outcome Assessment Forms', 'CE', '2020']

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--directory', type=str,
        default=os.path.join(os.path.expanduser("~"), *assessment_path),
        help='Directory to analyze')
    main(parser.parse_args())
