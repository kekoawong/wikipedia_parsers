#!/usr/bin/env python3

import difflib
import sys
import bz2
import gzip
import time
import json
import xml.etree.ElementTree as ET
import datetime
import dateutil.parser as dp

def usage(status=0):
    ''' Display usage information and exit with specified status '''
    progname = os.path.basename(sys.argv[0])
    print(f'''Usage: {progname} [DATA_FILE.xml.bz2] [options] [FILE_NAME]

    [DATA_FILE.xml.bz2]         Zipped wikipedia file to parse. Must be in format idwiki-date-pages-meta-history.xml.bz2
    -f [FILE_NAME]              Specifies file name to save the formated parsed data into
    ''')
    sys.exit(status)

def bz2_generate_lines(data_file):
        
        with bz2.open(data_file, "rb") as f:
                for line in f:
                        yield line

def gzip_generate_lines(data_file):
        
        with gzip.open(data_file, "rb") as f:
                for line in f:
                        yield line

def parse_file(data_file, file_type):
        '''
        Function will read through zipped xml file and return dictionary of titles and timestamps
        File type is bz2 or gz
        '''
        if file_type == 'bz2':
                records_stream = bz2_generate_lines(data_file)
        elif file_type == 'gz':
                records_stream = gzip_generate_lines(data_file)
        else:
                print('Incorrect file type')
                sys.exit(1)
        store = {}
        text_flag = False
        prev_tag = '' # Previous line - to differentiate between <id>'s
        prev_str_builder = '' # Previous <text> revision
        str_builder = '' # To get <text> from every revisions
        temp = '' # Title
        title_count = 0 # How many Wiki articles have been processed
        loading_signal = 0
        for string in records_stream:
                
                loading_signal += 1
                if loading_signal == 1000000:
                        print(f'Loading...')
                        print(f'On article {temp} and have processed {title_count} articles')
                        loading_signal = 0
                #var = string.decode('utf-8').strip()
                var = string.decode().strip()

                # TODO: print line by line (debugger)
                #print(var)
                #time.sleep(0.01)
                #continue	
                
                if text_flag:

                        # Stop adding text - revision done
                        if '</text>' in var:
                                # str_builder += var.rstrip('</text>')
                                str_builder += var[:-7]

                                #print("Revision {} done. Full text is: {}.. FIN".format(revID, str_builder))
        
                                # Check for differences and add to dict
                                before , after = prev_str_builder.split() , str_builder.split()
                                added = set(after).difference(set(before))
                                removed = set(before).difference(set(after))

                                # Somehow if a and r are switched, it works..
                                for a in added:
                                #print('Added: ', a)
                                # can convert a to words here
                                        store[temp][ts]['Added'].append(a)

                                for r in removed:
                                #print('Removed: ', r)
                                # can convert r to words here
                                        store[temp][ts]['Removed'].append(r)

                                '''
                                for line in difflib.ndiff(prev_str_builder.split(), str_builder.split()):
                                if line[0] == ' ': continue
                                elif line[0] == '-': store[temp][ts]['Removed'].append(line[2:]) # removed from prev_str_builder - previous article
                                elif line[0] == '+': store[temp][ts]['Added'].append(line[2:]) # add into str_builder - current article
                                '''

                                prev_str_builder = ''
                                prev_str_builder = str_builder # Update to track previous <text>

                                text_flag = False
                                continue
                        
                        # Keep adding text (revision)
                        str_builder += var
                        str_builder += '\n'

                if var.startswith('<title>'):
                        title_count += 1
                        #title = var.rstrip('</title>').lstrip('<title>')
                        title = var[7:-8]
                        temp = title                
                        store[temp] = {} # Put title in dict
                        store[temp]['number of ts'] = 0 # Number of timestamps in dict

                elif var.startswith('<id>') and prev_tag:
                        # Title/page ID
                        if prev_tag.startswith('<ns>'):
                                #pageID = var.rstrip('</id>').lstrip('<id>')
                                pageID = var[4:-5]

                        # Revision ID
                        elif prev_tag.startswith('<revision>'):
                                #revID = var.rstrip('</id>').lstrip('<id>')
                                revID = var[4:-5]

                        # Author ID (don't care)
                        elif prev_tag.startswith('<username>'):
                                pass

                elif var.startswith('<timestamp>'):
                        #zulu = var.rstrip('</timestamp>').lstrip('<timestamp>')
                        zulu = var[11:-12]
                        ts = dp.parse(zulu).strftime('%s')

                        # Every timestamp has a list of removed text and list of added texts
                        store[temp][ts] = {}
                        store[temp][ts]['Removed'] = []
                        store[temp][ts]['Added'] = []
                        store[temp]['number of ts'] += 1

                # elif var.startswith('<text xml:space="preserve">'):
                elif var.startswith('<text '):
                        text_flag = True
                        trim_from = var.find('>') + 1
                        # clean = var.lstrip('<text xml:space="preserve">') # Get first line of that text until \n
                        clean = var[trim_from:]
                        #continue
                        if clean:
                                str_builder = ''
                                str_builder += clean
                                str_builder += '\n'

                # Update previous line before next iteration
                prev_tag = var
                # time.sleep(0.01)
                
        return store

def main():
        '''Parse Command line options'''
        arguments = sys.argv[1:]
        output_file = 'wiki_formated_data.json'
        if len(arguments) == 0:
                data_file = 'idwiki-20200201-pages-meta-history.xml.bz2'
        else:
                data_file = arguments.pop(0)
        if len(arguments) > 0:
                if arguments.pop(0) == '-f':
                        output_file = arguments.pop(0)
                else:
                        usage(1)

        store = parse_file(data_file)

        print('Writing to json...')
        with open(output_file, 'w') as outfile:
                json.dump(store, outfile)
        print('DONE!!!')
        
# Main Execution
if __name__ == '__main__':
    main()