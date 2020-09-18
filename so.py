#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Summarize MSOE EECS SO XLSX files"""

# TODO: Recursive

import os
import argparse
from datetime import datetime
import pandas as pd
import openpyxl

TIME_TAG = datetime.now().strftime('%G%m%dT%H%M%S') # used to tag artifacts created by this run

def main(args):
    """Summarize MSOE EECS SO XLSX files"""
    level_rows = [24, 28, 32, 36, 40]
    level_cols = {'Level_str': 'D', 'Level_int': 'F', 'Count': 'G', 'Percentage': 'F'}
    level = ['Exemplary', 'Accomplished', 'Proficient', 'Developing', 'Beginning']

    metadata = {'Program': 'C3', 'Course Number': 'C5', 'Quarter/Year': 'C7',
        'Section': 'G5', 'Instructor': 'G7', 'Outcome': 'A10', 'Percent Proficient': 'B17'}

    all_data = []
    for filename in os.listdir(args.directory):
        if filename.endswith(".xlsx"):
            full_path = os.path.join(args.directory, filename)
            print(full_path)
            #table = pd.read_excel(io=full_path)
            workbook = openpyxl.load_workbook(full_path, data_only=True) # values, not formulas
            sheet = workbook['Form']
            assert sheet[level_cols['Level_str']+f'{level_rows[0]}'].value == level[0], \
                'Unexpected format: did not find highest level description where expected'
            count = []
            for row in level_rows:
                count.append(sheet[level_cols['Count']+f'{row}'].value)
            print(count)

            data_values = []
            for key in metadata:
                data_values.append(sheet[metadata[key]].value)

            data_values.append(count)

            all_data.append(data_values)

    col_names = list(metadata.keys())
    col_names.append('Count From Highest Level')

    dataframe = pd.DataFrame(all_data, columns=col_names)
    dataframe.to_excel(TIME_TAG+'.xlsx')
    # import IPython; IPython.embed()

if __name__ == "__main__":
    # execute only if run as a script

    assessment_path = ['Box', 'EECS Faculty and Staff', 'EECS Assessment Process',
        'Student Outcome Assessment Forms', 'CE', '2019', 'Q1']

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--directory', type=str,
        default=os.path.join(os.path.expanduser("~"), *assessment_path),
        help='Directory to analyze')
    main(parser.parse_args())
