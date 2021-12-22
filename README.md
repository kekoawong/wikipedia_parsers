# wikipedia_parsers
Python scripts to parse wikipedia metadata for hdhp inferences to model virality of topics, structuring data into a format to pass into the inference scripts. The inference scripts can be found [here](https://github.com/kekoawong/hdhp.py) while the data scraped from wikipedia can be found on this site [here](https://dumps.wikimedia.org/backup-index.html).

## Dependencies:
* bs4
* ijson
* json
* xml
* pickle
* gzip
* dateutil
* urllib
* html.parser
* sys, os
* re

## Usage:

### parse_wiki.py
Main script. Will parse a large zipped wikipedia file, unzipping small portions at a time and outputting the parsed data into a specified json file or another supported format. 
```
Usage: parse_wiki.py [DATA_FILE] [options] [FILE_NAME]

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
```

### wiki_parse3.py
Contains various functions useful to the main parse_wiki.py script, structuring the data.

### xml_parse.py
Contains various function useful to the main parse_wiki.py file for parsing through files with an XML structure.

## Links

[Initial hdhp inferences library](https://github.com/Networks-Learning/hdhp.py).