#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Given the XLSX master file for MSML course planning, do one of the following:
* Produce a student's advising plan
* For named students (MSML, not certificates):
  * Given a course code, list each term it is planned and who is taking it
  * Given a term code, list each course that is planned and who is taking it
"""

# TODO:
# Support LastName_FirstInitial

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

def is_course_code(s):
    """Return true if the given string is a valid course code"""
    return bool(re.match(r'^[A-Za-z]{3}[x\d]{4}$', s))

def is_term_code(s):
    """Return true if the given string is a valid term code"""
    return bool(re.match(r'^\dS[\d]{2}$', s))

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

def make_electives_unique(li):
    """Append sequential numbers to required electives so names are unique"""
    j = 0 # elective number
    for i, crs in enumerate(li):
        if crs == "CSC5xxx":
            j = j + 1
            li[i] = crs + ' ' + str(j)

def get_requirements(class_list, need_csc5610, need_mth5810):
    """
    Given dict of semester course plans and needed topic flags from admission
    decision, provide a reconciliation of how and whether the degree
    requirements are met.
    """
    requirements = ["CSC5201", "CSC6621", "CSC6605", "PHL6001", "CSC7901", "CSC5xxx"]
    if need_csc5610:
        requirements.insert(0,"CSC5610")
    else:
        requirements.append("CSC5xxx")
    # Electives must be at end of requirements since greedy matching below
    requirements.append("MTH5810" if need_mth5810 else "CSC5xxx")
    make_electives_unique(requirements)

    # Flatten the lists of classes into a single list
    planned = [s for sublist in class_list.values() for s in sublist]

    # handle special case CSC5201, which can be met by CSC5201, CSC6711, or CSC6712
    csc5201 = ["CSC5201", "CSC6711", "CSC6712"]
    reqs = {}
    for opt in csc5201:
        if opt in planned:
            reqs["CSC5201"] = opt
            requirements.remove("CSC5201")
            planned.remove(opt)
            break
    for crs in requirements.copy():
        if crs.startswith("CSC5xxx"):
            for opt in planned:
                if opt.startswith("CSC") and opt[3].isdigit() and int(opt[3]) >= 5:
                    reqs[crs] = opt
                    requirements.remove(crs)
                    planned.remove(opt)
                    break
        else:
            if crs in planned:
                reqs[crs] = crs
                requirements.remove(crs)
                planned.remove(crs)
    for crs in requirements: # no plan to meet remaining requirements
        reqs[crs] = 'unplanned'
    ex = 0
    for opt in planned: # remaining planned courses don't meet a requirement
        ex = ex + 1
        reqs["Extra course " + str(ex)] = opt
    return reqs

def summarize_student(args, df):
    """Find a specified student and summarize their record"""
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

    print("\nAdvising Plan:")
    classes = get_class_list(record)
    pprint.pprint(classes, sort_dicts=False)

    print("\nRequirements Check:")
    reqs = get_requirements(classes, record['CSC5610 Needed?'], record['MTH5810 Needed?'])
    pprint.pprint(reqs, sort_dicts=False)

    return 0

def full_names(d):
    """Given a DataFrame with first and last names, return a list of full names"""
    return (d['First Name'] + ' ' + d['Last Name']).tolist()

def summarize_course(args, df):
    """Given a course code, list MSML students planning to take it"""

    # Drop summary and historic rows, keeping only the records of students who
    # were or will actually be enrolled at some point in time. The first blank/None
    # index value indicates the end of these students.
    try:
        none_index_pos = df.index.tolist().index(None)
    except ValueError:
        # If None is not in the index, use the length of the DataFrame
        none_index_pos = len(df)
    df = df.iloc[:none_index_pos]

    results = []

    # Iterate over each column in the DataFrame
    # TODO: All column names that aren't a term should also be ignored to avoid spurious hits
    for col in df.columns.drop(['First Name', 'MTH5810 Needed?']):
        # Check if any cell in the column contains the course code
        matching_rows = df[df[col].astype(str).str.contains(args.name, na=False)]

        # For each matching row, append a new row to the results list with the Last Name,
        # First Name, and the column name (which is the name of the term)
        for _, row in matching_rows.iterrows():
            results.append({'Last Name': row.name, 'First Name': row['First Name'],
                'Term': col.split(' ', 1)[0]})

    grouped = pd.DataFrame(results).groupby('Term', sort=False).apply(full_names).to_dict()
    pprint.pprint(grouped, sort_dicts=False)
    for k, v in grouped.items():
        print(f"{k}: {len(v)} students")

    return 0

def summarize_term(args, df):
    """Given a term, list courses scheduled to run and students in each course"""

    # Drop summary and historic rows, keeping only the records of students who
    # were or will actually be enrolled at some point in time. The first blank/None
    # index value indicates the end of these students.
    try:
        none_index_pos = df.index.tolist().index(None)
    except ValueError:
        # If None is not in the index, use the length of the DataFrame
        none_index_pos = len(df)
    df = df.iloc[:none_index_pos]

    results = []

    # Iterate over each column in the given term
    for col in [f"{args.name} C{i}" for i in range(1, 4)]:
        # Find non-blank cells
        matching_rows = df[df[col].astype(str).str.strip() != '']
        for _, row in matching_rows.iterrows():
            results.append({'Last Name': row.name, 'First Name': row['First Name'],
                'Course': row[col]})

    grouped = pd.DataFrame(results)
    grouped.sort_values(by=['Last Name', 'First Name'], inplace=True)
    grouped = grouped.groupby('Course').apply(full_names).to_dict()

    pprint.pprint(grouped)
    for k, v in grouped.items():
        print(f"{k}: {len(v)} students")

    return 0

def main(args):
    """Perform actions requested by command line arguments"""
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

    if is_course_code(args.name):
        return summarize_course(args, df)
    if is_term_code(args.name):
        return summarize_term(args, df)
    return summarize_student(args, df)

if __name__ == "__main__":
    # execute only if run as a script

    data_path = ['OneDrive - Milwaukee School of Engineering', 'MSML Admin', 'msml.xlsx']

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', type=str,
        help='LastName (if unique) | LastName_FirstName | CourseCode | TermCode')
    parser.add_argument('-f', '--file', type=str,
        default=os.path.join(os.path.expanduser("~"), *data_path),
        help='File to analyze')
    main(parser.parse_args())
