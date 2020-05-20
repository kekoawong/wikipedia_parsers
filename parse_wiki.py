#!/usr/bin/env python3

import sys
import os
import datetime as dt
import string
import pickle
import json
import ijson
# include these scripts in same directory
from wiki_parser3 import dict_yield_tuples, dict_make_numbered_titles_file, basic_parse_yield_tuples, basic_parse_make_numbered_titles_file
from xml_parse import parse_file


def usage(status=0, error_message=''):
    ''' Display usage information and exit with specified status '''
    progname = os.path.basename(sys.argv[0])
    print(f'''Usage: {progname} [DATA_FILE] [options] [FILE_NAME]

    [DATA_FILE]             Data file to parse. Must be one of the following extensions:

        1. bz2 :    Must be in format idwiki-date-pages-meta-history.xml.bz2 from wikimedia.
        2. gz :     Must be in format idwiki-date-pages-meta-history.xml.gz from wikimedia.
        3. json :   Pre-parsed file that is created using the -f flag from this program. Must be in this format.

    OPTIONS:
    -h                          Display usage                            
    -f [FILE_NAME]              Save parsed data from bz2 or gz file into json dictionary file. Must have .json extension.
    -t [FILE_NAME]              Save parsed tuples in format for hdhp inference to pickle file specified.
    -d [FILE_NAME]              Save dictionary of numbers associated with collected titles into file.
    -y [MIN_YEAR] [MAX_YEAR]    Specify the years to collect timestamps. Will go to end of max year. Default is 2000 to end of 2020.
    ''')
    print(f'ERROR: {error_message}')
    sys.exit(status)

def save_object(object, file_name):
    with open(file_name, 'wb') as object_file:
        pickle.dump(object, object_file)
        object_file.close()

def dict_save_tuples(data, file_name, min_timestamp, max_timestamp):
    '''Function will parse tuples from dictionary data and save into file_name specified'''

    '''Yield and sort tuples'''
    print('Loading into generator object')
    gen_obj = dict_yield_tuples(data, min_timestamp, max_timestamp)
    print('Expanding into list')
    list_obj = list(gen_obj)
    print(f'Sorting tuples list of length {len(list_obj)}...')
    tuples = sorted(list_obj, key=lambda tup: tup[0])

    print("Sorting complete and saving to file")
    save_object(tuples, file_name)

def parse_tuples_and_save(data_file, save_file, min_timestamp, max_timestamp):
    '''Function will get tuples from json data file and save to pickle file'''

    print("Opening data file...")
    with open(data_file, 'r') as read_file:
        print("Loading into file using ijson...")
        events = ijson.basic_parse(read_file)
        print("Loaded into ijson object!")
    
        print("Loading generator object...")
        gen_obj = basic_parse_yield_tuples(events, min_timestamp, max_timestamp)

        print("Expanding object into list...")
        list_obj = list(gen_obj)

        read_file.close()

    # get list sorted by the first value
    print(f'Sorting tuples list of length {len(list_obj)}...')
    tuples = sorted(list_obj, key=lambda tup: tup[0])

    '''Save objects to files'''
    print("Sorting complete and saving to file")
    save_object(tuples, save_file)

def make_dict_from_json(data_file, output_file, min_timestamp, max_timestamp):
    '''Will make dictionary from parsing json'''
    print("Opening data file...")
    with open(data_file, 'r') as read_file:
        print("Loading into file using ijson...")
        events = ijson.basic_parse(read_file)
        print("Loaded into ijson object!")
    
        print("Making dictionary...")
        basic_parse_make_numbered_titles_file(events, output_file, min_timestamp, max_timestamp)


def main():
    '''Set variables'''
    arguments = sys.argv[1:]
    if len(arguments) == 0:
        usage(1, 'No arguments')
    data_file = arguments.pop(0)
    min_year = 2000
    max_year = 2020
    file_type = ''
    output_json_file = ''
    output_tuples_file = ''
    output_titles_file = ''
    json_file = False
    save_json_file = False
    save_tuples_file = False
    save_titles_file = False
    
    '''Check data file'''
    if data_file.endswith('.bz2'):
        if not data_file.endswith('pages-meta-history.xml.bz2'):
            usage(2, 'File must be in format idwiki-date-pages-meta-history.xml.bz2')
        file_type = 'bz2'
    elif data_file.endswith('.gz'):
        if not data_file.endswith('pages-meta-history.xml.gz'):
            usage(2, 'File must be in format idwiki-date-pages-meta-history.xml.gz')
        file_type = 'gz'
    elif data_file.endswith('.json'):
        json_file = True
    else:
        usage(2, 'Unsupported data file extension')

    '''Parse Command line options'''
    while len(arguments) > 0:
        arg = arguments.pop(0)
        if arg == '-h':
            usage(0)
        elif arg == '-f':
            output_json_file = arguments.pop(0)
            save_json_file = True
            if not output_json_file.endswith('.json'):
                print('Output file must be a json file')
                exit(2)
            if json_file:
                print('Data file already in json format')
                exit(2)
        elif arg == '-t':
            output_tuples_file = arguments.pop(0)
            save_tuples_file = True
        elif arg == '-d':
            output_titles_file = arguments.pop(0)
            save_titles_file = True
        elif arg == '-y':
            min_year = int(arguments.pop(0))
            max_year = int(arguments.pop(0))
        else:
            usage(3, 'Incorrect Argument')
    
    '''Convert years to min and max timestamp'''
    dt_min = dt.datetime(min_year, 1, 1)
    dt_max = dt.datetime(max_year, 12, 31, 23, 59) # will get all of the year
    min_timestamp = float( dt_min.replace(tzinfo=dt.timezone.utc).timestamp() )
    max_timestamp = float( dt_max.replace(tzinfo=dt.timezone.utc).timestamp() )

    '''Execute functions for data file'''
    if not json_file and (save_tuples_file or save_json_file or save_titles_file):
        print(f'Starting to parse through {data_file}')
        store = parse_file(data_file, file_type)
        if save_json_file:
            print(f'Writing dictionary to {output_json_file}...')
            with open(output_json_file, 'w') as outfile:
                    json.dump(store, outfile)
            print('Saved to json file ')
        if save_tuples_file:
            print(f'Starting to write tuples list to file {output_tuples_file}...')
            dict_save_tuples(store, output_tuples_file, min_timestamp, max_timestamp)
        if save_titles_file:
            print(f'Writing titles dictionary to {output_titles_file}...')
            dict_make_numbered_titles_file(store, output_titles_file, min_timestamp, max_timestamp)

    elif json_file and (save_tuples_file or save_titles_file):
        if save_tuples_file:
            parse_tuples_and_save(data_file, output_tuples_file, min_timestamp, max_timestamp)
        if save_titles_file:
            make_dict_from_json(data_file, output_titles_file, min_timestamp, max_timestamp)

    else:
        usage(4, 'No instructions specified')

    print('Complete')
        
# Main Execution
if __name__ == '__main__':
    main()
