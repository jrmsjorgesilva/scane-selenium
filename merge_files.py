#!/usr/bin/env python

import os
from datetime import datetime
from glob import glob

import pandas as pd

# File paths
pwd = os.getcwd()
DOWNLOADS_PATH = '{}/downloads'.format(pwd)
OUTPUT_FILES_PATH = '{}/merged_files'.format(pwd)


def concatenate_files(files):
    df_list = []
    for file in files:
        try:
            df = pd.read_csv(file, encoding='utf-16', delimiter='\t', low_memory=False)
            df_list.append(df)
        except UnicodeError:
            print 'Corrupt file: {}'.format(file)
            continue
        except UnicodeDecodeError:
            df = pd.read_csv(file, encoding='utf-8', delimiter='\t', low_memory=False)
            df_list.append(df)
    return pd.concat(df_list)


def concatenate_and_clean(input_file_name, should_cleanup=False):
    # Merge all the csv files for __topic__ into one
    exported_files = glob('{}/*.csv'.format(DOWNLOADS_PATH))
    if len(exported_files) == 0:
        return

    # `Clean` merged __topic__ file
    df = concatenate_files(exported_files)
    df = df.sort_values('Domain Rating')
    df = df[['Referring Page URL', 'Link URL', 'Type', 'Language']]
    df = df[(df['Language'] == 'en') | (df['Language'].isnull())]
    df = df[df['Type'] != 'Nofollow']

    date = datetime.today().strftime('%Y%m%d')
    base_file_name = '{0}_{1}_backlinks'.format(date, input_file_name)

    # Write excel file
    excel_file_path = '{0}/{1}.xlsx'.format(OUTPUT_FILES_PATH, base_file_name)
    writer = pd.ExcelWriter(
        excel_file_path,
        engine='xlsxwriter',
        options={'strings_to_urls': False}
    )
    df.to_excel(writer, index=False, encoding='utf-8')
    writer.save()

    # Write `Referring Page URL's` to text file
    df = df[['Referring Page URL']]
    raw_txt_path = '{0}/{1}RAW.txt'.format(OUTPUT_FILES_PATH, base_file_name)
    df.to_csv(raw_txt_path, header=None, index=False, encoding='utf-16')

    if should_cleanup:
        # Remove all files from the downloads dir
        for f in exported_files:
            os.remove(f)


if __name__ == '__main__':
    import sys
    try:
        concatenate_and_clean(sys.argv[1])
    except IndexError:
        print 'ERROR: you did not provide an output file name - `python merge_files.py <outputfilename>`'
        sys.exit()
