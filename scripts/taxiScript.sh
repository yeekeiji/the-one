#!/usr/bin/sh 

# script for parsing epfl's taxi data into ONE
# compliant form. This is a a control script that 
# controls other python scripts that do the actual data
# transformations

# usage: sh ${PATH}/the-one/scripts/taxiScript.sh <number>
# <number> represents the number of taxi files you want to process from full
# epfl dataset

# grabs dir where this script lives
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

# grabs path to the-one/ folder on system, the one containing this script
ONE="$(dirname "$SCRIPT_DIR")"

# assumes you have downloaded epfl's taxi dataset in the data folder as follows
data="$ONE"'/data/epfl/cabspottingdata/'

# name of the taxi file parser, extracts the necessary info from original data
taxiScript="$SCRIPT_DIR"'/taxi2.py'

# concatenates all modified data files and shifts all data wrt smallest vals
shiftScript="$SCRIPT_DIR"'/taxiLog.py'

# taxiCnt need to be in range [1, 536]. Total # of taxi files = 536
if [ -z "$1" ]
then 
    taxiCnt=25
else
    taxiCnt="$1"
fi

# utm lib installed in python 2 on this system, use python2 env
# this line may vary depending on how you've set up your sys
# this is to activate the python environment where utm lib is installed
source activate python2

# parse only the specified number of taxis from the whole data set
ls "$data"new* | head -n "$taxiCnt" | xargs python "$taxiScript"

# turn all node*.txt files into one data file sorted by unix time
sort -k 1 node* > node_master.txt

# shift data to lower values 
python "$shiftScript" taxi.log node_master.txt

# rename the final nodeData.txt file w/ nrofTaxi files used
mv nodeData.txt nodeData"$taxiCnt".txt
