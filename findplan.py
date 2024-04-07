#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find, select, and copy to clipboard MSOE STAT advising file for a given student"""

import os
import argparse
from glob import glob
from warnings import warn
import hashlib
from io import StringIO
import numpy as np
import pandas as pd
import pyperclip

def ranged_input(upper_end):
    """Prompt the user until they enter an int between 0 and argument"""
    if upper_end == 0:
        return 0 # no need to prompt if there is only 1 option
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

def get_default_stat_paths():
    """Return default paths to search for STAT plans"""
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
    return plan_path

def get_plans(student_name, pths=get_default_stat_paths()):
    """
    Recursively search all paths in pths for plans for student_name and return
    DataFrame of unique plans found. Sorted with most recent mtime first.
    """
    found_plan = []
    for pth in pths:
        if os.path.isdir(pth):
            found_plan += glob(f'{pth}/**/{student_name}*.txt', recursive=True)
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

    return data_frame

def extract_and_remove_fields(df, fields):
    """
    Extracts fields with identical values and returns a dictionary of these values
    and a DataFrame with the fields removed. Raises an error if any field does not
    contain identical values for every record.

    Parameters:
    - df: Pandas DataFrame from which to extract fields.
    - fields: List of field names to extract and remove.

    Returns:
    - A tuple containing:
        1. A dictionary of field names with the associated identical value.
        2. The DataFrame with specified fields removed.
    """
    field_values = {}
    for field in fields:
        if not df[field].nunique(dropna=False) == 1:
            raise ValueError(f"Field '{field}' does not have identical values for every record.")
        field_values[field] = df[field].iloc[0]

    # Remove the specified fields from the DataFrame
    df_reduced = df.drop(columns=fields)

    return field_values, df_reduced

def sem_tup_str(tup):
    """ Convert semester tuple, example: (2024, 'S2') becomes "2024S2" """
    return str(tup[0]) + tup[1]

STATUS_CATEGORIES = ['successful', 'unsuccessful', 'NoCredit', 'wip', 'unscheduled', 'scheduled',
    'missing']

def read_stat_plan(fn):
    """
    Given the path to a STAT plan, return corresponding DataFrame and calculate credits completed
    and WIP. Doesn't include unsuccessful, NoCredit, or missing courses. Calculates semester
    credits and raises an error if various sequenece rules are violated (e.g., a course is planned
    in a past semester).
    """
    # read_csv supports 1 comment character, but we have 2, so preprocess:
    with open(fn, 'r', encoding='utf-8') as file:
        filtered_lines = [line for line in file if not line.strip().startswith(('<','>'))]
    buffer = StringIO(''.join(filtered_lines)) # convert to file-like object

    plan = pd.read_csv(buffer, sep='\t', skiprows=1, index_col=["Year", "Term"],
        names=["ID", "Year", "Term", "Prefix_Number", "Credits", "Status", "Course Name",
            "Last Name", "First Name", "Major", "Current Standing", "Email", "UNKNOWN 1", "Minor",
            "UNKNOWN 2", "UNKNOWN 3", "UNKNOWN 4", "Advisor 1", "Advisor 2", "UNKNOWN 5",
            "UNKNOWN 6", "Requirement"], dtype={'Status': 'category'})

    plan['Status'] = pd.Categorical(plan['Status'], categories=STATUS_CATEGORIES)
    extra_values = set(plan['Status'].unique()) - set(STATUS_CATEGORIES)
    if extra_values: # set not empty, nan indicates something couldn't convert
        raise ValueError("Unrecognized Status category") # too late to find nan source

    _, plan = extract_and_remove_fields(plan, ["ID", "Last Name", "First Name", "Major",
        "Current Standing", "Email", "Minor", "Advisor 1", "Advisor 2",
        "UNKNOWN 1", "UNKNOWN 2", "UNKNOWN 3", "UNKNOWN 4", "UNKNOWN 5", "UNKNOWN 6"
    ])

    # Break course number into parts
    plan['Prefix'] = plan['Prefix_Number'].str[:5].str.rstrip()
    plan['Number'] = plan['Prefix_Number'].str[5:]
    plan.drop('Prefix_Number', axis=1, inplace=True)
    plan = plan.sort_values(["Prefix", "Number"]) # 1st since less significant
    plan = plan.sort_index(level=["Year", "Term"])

    # Convert everything to semester credits
    plan['SemCredits'] = plan.apply(lambda row: row['Credits'] if len(row['Prefix']) == 3
                                    else (2/3) * row['Credits'] if len(row['Prefix']) == 2
                                    else np.nan, axis=1)

    plan = plan[~plan['Status'].isin(['unsuccessful', 'NoCredit', 'missing'])] # not earned credits

    for k in ['Credits', 'SemCredits']:
        if np.all(plan[k] % 1 == 0):
            plan[k] = plan[k].astype('int32')

    idx, sem_credits, last_term = {}, {}, {}
    for k in ['successful', 'wip']:
        idx[k] = plan['Status'] == k
        sem_credits[k] = plan.loc[idx[k],'SemCredits'].sum()
        last_term[k] = sem_tup_str(plan[idx[k]].index[-1]) if any(idx[k]) else None

    print(f"{sem_credits['successful']:.2f} credits are complete as of {last_term['successful']}")
    if sem_credits['wip'] > 0:
        print(
            f"{sem_credits['successful']+sem_credits['wip']:.2f} credits will be complete "
            f"with successful WIP through {last_term['wip']}"
        )
    else:
        print("There is no WIP.")

    earned_credits_term = plan.groupby(['Year', 'Term']).agg(
        {'Credits': 'sum', 'SemCredits': 'sum'}).reset_index()
    earned_credits_term['TotalSemCredits'] = earned_credits_term['SemCredits'].cumsum()
    print(earned_credits_term.to_string(index=False))
    if sem_credits['wip'] < 90:
        senior_terms = earned_credits_term[earned_credits_term['TotalSemCredits'] >= 90]
        if not senior_terms.empty:
            print("Senior standing will be reached after "
                f"{sem_tup_str(senior_terms.iloc[0][['Year', 'Term']].tolist())}")

    return plan

def main(args):
    """Find matching advising plans, copy user selection to clipboard"""
    data_frame = get_plans(args.name, args.directory)

    if data_frame.empty:
        print('No plans found, exiting...')
        return -1

    pd.options.display.max_colwidth = None
    print(data_frame)

    selected_plan = data_frame.at[ranged_input(data_frame.index.max()),'path']

    print(selected_plan)
    pyperclip.copy(selected_plan)
    print('Filename copied to clipboard')

    if not args.no_summary:
        plan = read_stat_plan(selected_plan)
        print(plan)

    return 0

if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', type=str, help='LastName | LastName_FirstInit | LastName_FirstName')
    parser.add_argument('-d', '--directory', type=str, default=get_default_stat_paths(),
        help='Directories to search')
    parser.add_argument('-n', '--no-summary', action='store_true', help="Don't summarize plan")
    main(parser.parse_args())
