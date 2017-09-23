#!/usr/bin/sh

# arg $1 = -1 : splits matrix data files of multiple watched nodes 
#   takes as inputs the name of each watched node
#   ex. if you have two watched nodes:
#           sh mExtract.sh -1 dataFile.txt n123 m109
# arg $1 = -2 : assumes the dataFile is of only 1 watched node
#   It grabs only the watched node's matrix values when connecting to a
#   specified destination node. Works for multiple destination nodes too.
#   ex. if you want only the data wrt node named r199
#           sh mExtract.sh -2 dataFile.txt r199
#
# output : filtered version of original dataFile with only rows with matches
#   to specific destination nodes or watchnodes.
#   Output of -1 : nodeName + Mvalues.txt. Ex. r199Mvalues.txt
#   Output of -2 : nodeName + onlyX.txt. Ex. s122only.txt

# useful for the cluster scenario where we are looking at mutliple nodes
# decouples node data from dumpFile.txt that's generated from HeraDebug Router
if [ "$1" -eq -1 ] 
    then
        for elem in "${@:3}"
        do
            echo "Creating file with only $elem data"
            awk -F "," -v var="$elem" '{if($2 == var) { print }}' "$2" > "$elem"Mvalues.txt;
        done
else if [ "$1" -eq -2 ]
    then
        # secondary parsing for only the connections between two particular
        # nodes over time
        for elem in "${@:3}"
        do
            echo "Grabbing data with destination node $elem"
            prefix=$(basename "$2")
            prefix="${prefix:0:4}"
            awk -F "," -v var="$elem" '{if($3 == var) {print}}' "$2" > \
            "$prefix"-"$elem"only.txt;
        done
    fi
fi
