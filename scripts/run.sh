#!/usr/bin/sh

# automation script for ONE Sim & Hera Project
# 8/14/17 SJSU

# usage: sh ${PATH}/the-one/scripts/run.sh <baseFile.txt> <specFiles*.txt>
# 
# <baseFile.txt> : ONE compliant settings file that has key-values common to all
#           simulation cases you want to try
#
# <specFiles*.txt> : should be a command to use all settings files. i.e. set
# these files to all have similar names so that you can run all of them as args
# to this script.
#
# should run this script inside the dir holding all the spec and base files.
# ex. ${PATH}/the-one/batch_settings/b003/
# use above path if you are running the 3rd batch with a common base file & many
# specs / test cases

# grabs the dir that this script lives in.
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

# grabs the path to the-one/ folder on system
ONE="$(dirname "$SCRIPT_DIR")"

# fist positional argument must be the base file. 
BASEFILE="$1"

# since it's not guarenteed to run this script from batch folder
# extract out the base file name
BATCH=$(basename "$BASEFILE")
BATCH_NOEXT="${BATCH%.*}"

# Python script that has a command line interface to parse files
#!/usr/bin/sh

PARSER="$SCRIPT_DIR"/FileParser.py

# create a new file called local.log for processing.
LOCAL_LOG="$(dirname "$BASEFILE")"/"$(date '+%y-%m-%d-%k:%M')".log
touch "$LOCAL_LOG"

# CHANGE IF: placed master log file with all sim results differs from below
MASTER_LOG="$ONE"/batch_settings/master.log

# for each spec file inputted as an arg, run one.sh base.txt specN.txt
# and process results
for spec in "${@:2}"
    do
        # grab the base of the current file name
        stem=$(basename "$spec")
        stem="${stem%.*}"


        # run simulation & store stdout & stderr
        sh "$ONE"/one.sh -b 1 "$BASEFILE" "$spec" 2>&1 | tee \
            "$ONE"/log/"$BATCH_NOEXT"/"$stem".log

        # only if the simulation exits correctly, process results
        if [ "$?" -eq 0 ]
        then 
            # find & store report names
            report=$(python "$PARSER" -r "$BASEFILE")
            report="$ONE"/"$report"
            msgStatsFile="$report""$stem"_MessageStatsReport.txt
            eLogFile="$report""$stem"_EventLogReport.txt

            # process results & store in a local file called local log
            python "$PARSER" -a "$BASEFILE" "$spec" \
                "$msgStatsFile" "$eLogFile" "$LOCAL_LOG"
            
        else
            # skip files that didn't run correctly.
            # their report files may be empty or other complications
            continue
        fi
    done


# back up the master log file
cp "$MASTER_LOG" "$(dirname "$MASTER_LOG")/"master.bak

# concatenate the log files, local remains unchanged
python "$PARSER" -c "$LOCAL_LOG" "$MASTER_LOG"
