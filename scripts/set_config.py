#! /usr/bin/env python
'''
generate the setting files for the relative comparison simulations
'''

import argparse
import itertools

# parser settings
# Init and description
parser = argparse.ArgumentParser(description="Settings File Generator", 
                                 formatter_class=argparse.RawTextHelpFormatter)

# Arguments and description
parser.add_argument("-f", type=argparse.FileType('r'), help="Filename of Run" \
"Sim settings file")

# Parse the args and set file to a usable var
args = parser.parse_args()
open_file = args.f

# empty dictioanry to store run index options
runIndex = {}
router = {}

with open_file as f:
    for line in f:
        # Ignore comments in the run-sim file
        if '#' in line:
            continue

        # get key: list( run index ) pairs
        elif '[' in line:
            content = line.split()
            RUN_INDEX_SIZE = len(content)

            # strip the '[',']', ';' chars from content
            content = [elem.strip('[];') for elem in content]

            # adding run-index values you want in master dictionary
            runIndex[content[0]] = content[2:]

name1 = 'test'
count = 0
for key in runIndex:
    g = open((name1+'_'+str(count)), w+)
    g.write(key + '=')
        
# print(";".join(content[2:]))
