#!/usr/bin/env python3

import os
import sys
import json
import urllib.parse as urllib
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import re

def usage(status=0):
    ''' Display usage information and exit with specified status '''
    progname = os.path.basename(sys.argv[0])
    print(f'''Usage: {progname} [DATA_FILE] [options] [FILE_NAME]

    -f [FILE_NAME]      Specifies which file to save the tuples into
    -t [FILE_NAME]      Specifies which file to save the title and numbers dictionary into
    ''')
    sys.exit(status)

class MLStripper(HTMLParser):
    '''For stripping html'''
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def basic_parse_make_numbered_titles_file(data, file_name, min_timestamp, max_timestamp):
    '''Pass data in as ijson object'''
    # initialize variables
    prev = None
    curr = next(data, None)
    next_tup = next(data, None)
    index = -1
    prev_index = index
    total_tuples = 0
    tuples_of_title = 0
    title = next_tup[1]
    loading_signal = 0
    on_title = 0
    titles_dict = {}
    num_timestamps = 0

    # Iterate through object
    while curr:
        loading_signal += 1
        if loading_signal == 1000000:
            print(f'Loading, adding title {title} to dictionary...')
            loading_signal = 0
        if curr[0] == 'number':
            num_timestamps = curr[1]
        if curr[0] == 'map_key' and next_tup[0] == 'start_map' and (prev[0] == 'end_map' or prev[0] == 'number'):
            # Try collecting timestamp
            try:
                timestamp = float(curr[1])
            except ValueError:
                # is a title
                # add prev title to dictionary if has tuples
                if index != prev_index:
                    titles_dict[index] = {title : {'total_timestamps' : num_timestamps, 'usable_timestamps' : tuples_of_title}}
                title = curr[1]
                tuples_of_title = 0
            else:
                # do not collect if not in range
                if timestamp > min_timestamp and timestamp < max_timestamp:
                    words = ''
                    # collects all strings associated with timestamp
                    while next_tup[0] != 'end_map':
                        #increment
                        prev = curr
                        curr = next_tup
                        next_tup = next(data, None)
                        # collect string and make timestamp
                        if (curr[0] == 'string'):
                            words += convert_to_words(curr[1]) + ' '
                    
                    if len(words) > 0:
                        tuples_of_title += 1
                        total_tuples += 1
                        # increment index
                        if tuples_of_title == 1:
                            index += 1

        #increment
        prev = curr
        curr = next_tup
        next_tup = next(data, None)
    
    print(f'Writing dictionary to {file_name}')
    with open(file_name, 'w') as output_file:
        json.dump(titles_dict, output_file)
        output_file.close()

def dict_make_numbered_titles_file(data, file_name, min_timestamp, max_timestamp):
    '''
    Will make numbered titles dictionary in timestamp range and save to file
    data_json : data loaded in as json object. In format pascal has for wiki data
    file_name : name of file to save into
    min_timestamp and max_timestamp : range of times, in seconds, to save file. Should be same as range of yield tuples function
    '''
    # initialize title index, dictionary
    index = 0
    numbered_titles = {}
    
    for title in data:
        # get number of timestamps
        num_timestamps = data[title].get('number of ts')
        usable_timestamps = 0

        # loop through dictionary and create tuples
        for timestamp in data[title]:
            # skip number of ts entry
            if (timestamp == 'number of ts'):
                continue
            words = ''
            # collect timestamps within the time period
            if float(timestamp) > min_timestamp and float(timestamp) < max_timestamp:
                # get removed words
                for removed_string in data[title][timestamp]['Removed']:
                    words += convert_to_words(removed_string) + ' '
                # get added words
                for added_string in data[title][timestamp]['Added']:
                    words += convert_to_words(added_string) + ' '
                # check if there are words in edit
                if len(words) > 0:
                    usable_timestamps += 1
        # increment index and add to dictionary
        if usable_timestamps > 0:
            numbered_titles[index] = {title : {'total_timestamps' : num_timestamps, 'usable_timestamps' : usable_timestamps}}
            index += 1

    # write the dictionary to a new file
    with open(file_name, 'w') as output_file:
        json.dump(numbered_titles, output_file)
        output_file.close()

def convert_secs_to_days(seconds):
    return seconds/86400.0

def convert_secs_to_months(seconds):
    return seconds/2629800.0

def convert_to_words(input_string):
    '''Will take in an string with html or url and get the usable words out of it'''

    # decode url
    new_string = urllib.unquote(input_string)

    # strip the html
    new_string = strip_tags(new_string)

    # Split with regex to find alphabetic words
    words_in_string = re.findall(r'\w+', new_string)
    words = ''

    for word in words_in_string:
        # filter out common extensions
        if word == 'com' or word == 'png' or word == 'jpeg' or word == 'gov' or word == 'org' or word == 'io' or word == 'http' or word == 'https':
            continue
        # check is ASCII and contains all alphabetic characters
        # if removed_word.isalpha() and all(ord(c) < 128 for c in removed_word):
        # convert to lower case and add to words string
        word = word.lower()
        words += word + ' '

    return words.strip()

def dict_yield_tuples(data, min_timestamp, max_timestamp):
    '''
    Pass data as a dict object
    Function will go through wiki data in the format that Pascal has formatted
    Will make tuples in the form (timestamp, words_in_edit, article_number, metadata)
    Words in edit come from removed and added words
    
    '''

    # initialize title index
    index = 0
    loading_signal = 0
    total_tuples = 0
    
    for title in data:
        # show loading signal
        loading_signal += 1
        if loading_signal == 10000000:
            print(f'Loading, on title {index}, with {total_tuples} total tuples')
            loading_signal = 0
        
        # set num tuples created
        tuples_of_title = 0

        # loop through dictionary and create tuples
        for timestamp in data[title]:
            # skip number of ts entry
            if (timestamp == 'number of ts'):
                continue
            words = ''
            # collect timestamps within the time period
            if float(timestamp) > min_timestamp and float(timestamp) < max_timestamp:
                # get removed words
                for removed_string in data[title][timestamp]['Removed']:
                    words += convert_to_words(removed_string) + ' '
                # get added words
                for added_string in data[title][timestamp]['Added']:
                    words += convert_to_words(added_string) + ' '
                # check if there are words in edit
                if len(words) > 0:
                    # create tuple
                    tuple1 = (convert_secs_to_months(float(timestamp)-min_timestamp), words.rstrip(), index, [])
                    tuples_of_title += 1
                    total_tuples += 1
                    yield tuple1
        # increment index
        if tuples_of_title > 0:
            index += 1

def basic_parse_yield_tuples(data, min_timestamp, max_timestamp):
    ''' Data passed in as ijson basic parse object'''

    # initialize variables
    prev = None
    curr = next(data, None)
    next_tup = next(data, None)
    index = -1
    total_tuples = 0
    tuples_of_title = 0
    title = next_tup[1]
    loading_signal = 0
    on_title = 0
    # titles = 2702864

    # Iterate through object
    while curr:
        loading_signal += 1
        if loading_signal == 10000000:
            print(f'Loading, on title {on_title}, with {total_tuples} total tuples')
            loading_signal = 0
        if curr[0] == 'map_key' and next_tup[0] == 'start_map' and (prev[0] == 'end_map' or prev[0] == 'number'):
            # Try collecting timestamp
            try:
                timestamp = float(curr[1])
            except ValueError:
                # is a title
                title = curr[1]
                tuples_of_title = 0
                on_title += 1
            else:
                # do not collect if not in range
                if timestamp > min_timestamp and timestamp < max_timestamp:
                    words = ''
                    # collects all strings associated with timestamp
                    while next_tup[0] != 'end_map':
                        #increment
                        prev = curr
                        curr = next_tup
                        next_tup = next(data, None)
                        # collect string and make timestamp
                        if (curr[0] == 'string'):
                            words += convert_to_words(curr[1]) + ' '
                    
                    if len(words) > 0:
                        tuples_of_title += 1
                        total_tuples += 1
                        # increment index
                        if tuples_of_title == 1:
                            index += 1
                        # create tuple
                        tuple1 = (convert_secs_to_months(timestamp-min_timestamp), words.rstrip(), index, [])
                        yield tuple1

        #increment
        prev = curr
        curr = next_tup
        next_tup = next(data, None)


def yield_tuples(data, min_timestamp, max_timestamp):
    '''
    Pass data as a ijson object, first part of tuple is wiki title, second is the dictionary associated
    Function will go through wiki data in the format that Pascal has formatted
    Will make tuples in the form (timestamp, words_in_edit, article_number, metadata)
    Words in edit come from removed and added words
    
    '''

    # initialize title index, dictionary, list
    index = 0
    total_tuples = 0

    for title_tuple in data:
        # set num tuples created
        tuples_of_title = 0
        title_dict = title_tuple[1]

        # loop through dictionary and create tuples
        for timestamp in title_dict:
            # skip number of ts entry
            if (timestamp == 'number of ts'):
                continue
            words = ''
            # collect timestamps within the time period
            if float(timestamp) > min_timestamp and float(timestamp) < max_timestamp:
                # get removed words
                for removed_string in title_dict[timestamp]['Removed']:
                    words += convert_to_words(removed_string) + ' '
                # get added words
                for added_string in title_dict[timestamp]['Added']:
                    words += convert_to_words(added_string) + ' '
                # check if there are words in edit
                if len(words) > 0:
                    # create tuple
                    tuple1 = (convert_secs_to_months(float(timestamp)-min_timestamp), words.rstrip(), index, [])
                    tuples_of_title += 1
                    total_tuples += 1
                    yield tuple1
        # increment index
        if tuples_of_title > 0:
            index += 1

def parse_data(data_file, tuples_file, numbered_titles_file):

    with open(data_file, 'r') as read_file, open(tuples_file, 'w') as output_tuples_file:

        data = json.load(read_file) # take lots of space

        # set min and max timestamps to between 2004 and 2005
        min_timestamp = 1072915200
        # max_timestamp = 1104537600 , this is for between 2004 and 2005
        max_timestamp = 1586803325 # until present day

        # get tuples from data
        for tup in dict_yield_tuples(data, min_timestamp, max_timestamp):
            input_string = str(tup) + '\n'
            output_tuples_file.write(input_string)
        output_tuples_file.close()

        # make dictionary of titles
        make_numbered_titles_file(data, numbered_titles_file, min_timestamp, max_timestamp)
        read_file.close()        

def find_min_timestamp(data_json):
    '''Will find the minimum timestamp in the dictionary'''
    min_timestamp = sys.float_info.max
    for title in data_json:
        num_timestamps = data_json[title].pop('number of ts', None)
        for timestamp in data_json[title]:
            if float(timestamp) < min_timestamp:
                min_timestamp = float(timestamp)
            break
    return min_timestamp

def main():
    ''' Parse command line arguments'''
    # set variables
    arguments = sys.argv[1:]
    if len(arguments) == 0:
        usage(1)
    data_file = arguments.pop(0)
    tuples_file = 'tuples.txt'
    numbered_titles_file = 'numbered_titles.json'

    # parse arguments
    while len(arguments) > 0:
        arg = arguments.pop(0)
        if arg.startswith('-'):
            if arg == '-f':
                tuples_file = arguments.pop(0)
            elif arg == '-t':
                numbered_titles_file = arguments.pop(0)
            else:
                usage(1)
        else:
             usage(1)
    # call function
    parse_data(data_file, tuples_file, numbered_titles_file)

# Main Execution
if __name__ == '__main__':
    main()
