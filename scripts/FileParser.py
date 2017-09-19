#!/usr/bin/python3
# python scripts to parse the-one sim files

import argparse
import ntpath
import  os
import shlex
from subprocess import Popen, PIPE, STDOUT
import pandas as pd
import numpy as np

class FileParser:
    ''' Abstract class that holds utilities for derived parsers.
    '''

    def __init__(self, fileName):
        '''
            Constructor. Initializes a FileParser object.

            Attributes
            ----------
            fileName : String describing the name of the file you want to parse
        '''
        self.file = fileName

    def getPathLeaf(self, path=None):
        '''
            Grabs a file name w/out the full path

            Parameters
            ----------
            path : String describing the full file path name of a file
            default value : obj's own self.file that describes the FileParser obj;
            assigned inside the function

            Examples
            --------
            path = '/home/userName/Documents/coolFile.txt'
            getPathLeaf(path) -> returns : coolFile.txt
        '''
        # set default value for the path if no value is given
        if path == None:
            path = self.file

        head, tail = ntpath.split(path)

        return tail

    def getCoreName(self, rType):
        '''
            Returns the core name or .log version of file name
            Core name -> file name w/out extension

            Parameters
            ----------
            rType : int {0 or 1}
                0 : someFile.ext -> someFile
                1 : someFile.ext -> someFile.log
        '''
        fileName = self.file[:self.file.find('.')]
        if rType == 0:
            return fileName
        else:
            return fileName + '.log'

    def grabSettings(self, input):
        '''
            Parses a file for the specific string values you feed into this
            function. 

            Parameters
            ----------
            input : List or solitary key string(s) you want to scrape the values
            of from a particular file. This expects the file is in a key value
            pair format. 

            Return
            ------
            output : List or single string that represents the value of the
            keys fed into the function.

            Examples
            --------
            input = [Scenario.name, .router, ...]
            The function will return the values to the keys you input to the
            function in the same relative order.

            output = ['test1', 'ProphetRouter', ...]
        '''
        if type(input) == str:
            input = list(input)
        elif type(input) != list and type(input) != str:
            print("Wrong type of input. Needs String or List of keys to"\
            + "search for")

        # dict holds values for output
         

            

class EventLog(FileParser):
    '''
        Event Log Parser. Inherits from FileParser class.
    '''

    def __init__(self, eventLog):
        '''
            Event Log Parser object Constructor. 

            Attributes
            ----------
            file : String describing the name of the file you want to parse
            totalC : Int describing the total number of messages created
            totalD : Int describing the total number of messages successfully
            delivered
            msgs : Dictionary that tracks messages and their replica count

            Parameters
            ----------
            eventLog : String describing the name of the file you want to parse
        '''
        FileParser.__init__(self, eventLog)
        self.totalC = 0
        self.totalD = 0
        self.msgs = {}

    def isTracked(self, msgName):
        '''
            Checks the msgs dictionary to see if it's already tracking the
            replica count of a particular message.

            Parameters
            ----------
            msgName : String identifying the message you are checking, ex: 'M1'
            
            Return
            ------
            bool {True, False} referencing whether the msgName is in dict msgs
        '''
        if msgName in self.msgs:
            return True
        else:
            return False

    def getLogName(self):
        '''
            Getter method for the event log file name

            Return
            ------
            string describing the name of the file this object is parsing
        '''
        return self.file

    def getMsg(self):
        '''
            Getter method for dictionary of msgs

            Return
            ------
            Dictionary : full of replica counts for messages you have seen so far
        '''
        return self.msgs

    def getCCnt(self):
        '''
            Getter Method for the total number of created messages
            
            Return
            ------
            Int : total number of messages created
        '''
        return self.totalC

    def getDCnt(self):
        '''
            Getter method for the total number of delivered messages

            Return
            ------
            Int : total number of messages delivered
        '''
        return self.totalD

    def nrofMsgs(self):
        '''
            Counts the total number of unique messages in report file
            Note: this should be the same as getCCnt

            Return
            ------
            Int : total number of unique messages in dictionary msgs
        '''
        return len(self.msgs)

    def nrofReps(self):
        '''
            Finds the total number of messages created.
            nrofReps = #( copies encountered )
            
            Return
            ------
            Int : total number of messages created. Returns the number of
            replicas that we use as a metric
        '''
        return sum(self.msgs.values())

    def addMsg(self, msgName):
        '''
           add msgName to msg dictionary

           Parameter
           ---------
           msgName : String describing the name of the msg you are adding
        '''
        self.msgs[msgName] = 1

    def updateMsg(self, msgName):
        '''
            update existing count of msgName in msgs dictionary

            Parameter
            ---------
            msgName : String describing the name of the message count you need
            to update
        '''
        self.msgs[msgName] += 1

    def calcSuccess(self):
        '''
            calculate the successful delivery ratio. 

            Return
            ------
            Float : ratio of #(delivered) / #(created)
        '''
        if self.totalC != 0.0:
            return float(self.totalD) / float(self.totalC)
        else:
            return 0.0

    def parseAttr(self):
        '''
            Main parser function that constructs 
                a. the msg dict
                b. created messages
                c. delivered messages

            Parameters
            ----------
            void

            Return
            ------
            void : modifies internal data member. Use getters to see results.
        '''
        with open(self.file, 'r') as f:
            for line in f:
                line = line[:-1]
                content = line.split()
                msgName = ''

                # finding the msg that triggered the event
                # checks for a message event, denoted by 'M'
                # if settings set Message prefix != 'M' change to that char
                # ex. if 'M26' in line set msgName
                for elem in content:
                    # checking each word in line for 'M'
                    if 'M' in elem:
                        msgName = elem
                        break
                
                # update if tracked, add if not
                # skip if no msgs ref in line
                if self.isTracked(msgName):
                    if 'DE' in content:
                        if 'D' in content:
                            self.totalD += 1
                        else:
                            self.updateMsg(msgName)
                    else:
                        continue

                # no message events in current line
                elif msgName == '':
                    continue

                # new message created
                elif 'C' in content:
                    self.addMsg(msgName)
                    self.totalC += 1

    def summary(self):
        '''
            Prints a nice summary of the following:
                a. Number of unique messages created
                b. Number of delivered messages
                c. Successful delivery ratio
                d. Number of replicas
        '''
        print(self.getLogName())
        print('\tNumber of unique msgs created = ' + str(self.nrofMsg()))
        print('\tNumber of delivered msgs = ' + str(self.getDCnt()))
        print('\tSuccessful delivery ratio = ' + \
            str(self.calcSuccess()))
        print('\tNumber of replicas = ' + str(self.nrofReps()))

class Specs(FileParser):
    '''
        One settings file parser. In particular, it is designed to parse and
        grab information from what is called specification files in our
        workflow. These are the simulation run specific settings files that
        modify an existing base setting file with options like Router, Routing
        parameters, BLE range, etc.
    '''

    # list of strings that we want to check for in a spec file
    # each string correlates to a specific setting that we want to grab
    attr = ['.router', \
            '.transmitRange']

    def __init__(self, spec):
        FileParser.__init__(self, spec)

    def grabSettings(self):
        '''
            Grabs the key-value pairs from the spec file that we need for futher
            analysis.

            Parameters
            ----------
            settings : list containing the key strings we need to search for inside
            of the spec file.

            Return
            ------
            output : map containing the key-value pairs of the specific keys we fed
            into the function and any Router parameters we find.
        '''
        output = {}
        KEY_INDEX = 0
        VAL_INDEX = 1
        routerFlag = False
        routerName = ''
        settingFound = False

        with open(self.file, 'r') as f:
            # iterate through each line of the file
            for line in f:
                # skip comments
                if '#' in line:
                    continue

                # declaration needed outside loop for persistence
                # carries last checked elem outside of loop b/c scope
                elem = ''
                # checks for each attr in class var attr
                for elem in self.attr:
                    if elem in line:
                        settingFound = True
                        break

                # router found in the settings file already
                if routerFlag:
                    # found a Router parameter; append to output
                    if routerName in line:
                        settingFound = True
                        elem = routerName

                # case statements that parse the line depending on the setting
                if settingFound:
                    # reset the flag
                    settingFound = False

                    # grab the key value pair of the line
                    pair = grabPairs(line)

                    # case 1, router obj found
                    if elem == '.router':
                        pair[KEY_INDEX] = 'Router'
                        routerName = pair[VAL_INDEX]
                        routerFlag = True

                    # case 2, BLE Range found
                    if elem == '.transmitRange':
                        pair[KEY_INDEX] = 'BLE_RANGE'
                        
                    # case Router.param found, do nothing special

                    # append settings found to output map
                    output[ pair[KEY_INDEX] ] = pair[VAL_INDEX]
        return output 

class Base(FileParser):
    '''
        Base File parser. Primary goal is to seach through the base file for
        the following information:

        1. reports directory path
    '''
    settings = ['.reportDir']

    def __init__(self, baseFile):
        '''
            constructor for a base file object.
        '''
        FileParser.__init__(self, baseFile)

    def grabSettings(self):
        '''
            parses the base file for the value strings listed in the member
            list 'settings'

            Return
            ------
            output : map of each key-value pair found in the settings file.
        '''
        with open(self.file, 'r') as f:
            # flag for handling different cases of values in file
            output = {}
            settingsFound = False
            KEY_INDEX = 0
            VAL_INDEX = 1
            for line in f:
                # skip comments 
                if '#' in line:
                    continue

                elem = ''
                for elem in self.settings:
                    if elem in line:
                        settingsFound = True
                        break

                if settingsFound:
                    # reset the flag for next iteration
                    settingsFound = False
                    pair = grabPairs(line)
                    
                    if elem == '.reportDir':
                        pair[KEY_INDEX] = 'ReportDir'

                    output[ pair[KEY_INDEX] ] = pair[VAL_INDEX]
        return output

class MsgStats(FileParser):
    '''
        MessageStatsReport log parser. Extracts several metric values for final
        analysis.

        List of qualities to grab from log
        ----------------------------------
        1. Latency Average
        2. Latency Median
        3. Hop Count Average
        4. Hop Count Median

    '''
    # List holding the key strings to search for in Message Log file
    quals = ['latency_avg',\
             'latency_med',\
             'hopcount_avg',\
             'hopcount_med']
    
    def __init__(self, msgLog):
        '''
            Constructor for the message log parser obj. Requires a
            MessageStatsReport to be generated during ONE simulation.

            Attribute
            ---------
            file : String describing the name of the MessageStatsReport
            metrics : dictionary containing the key-value pairs we grabbed from
            a MessageStatsReport log file. The list of all key-val pairs we
            want are contained in the 'quals' variable.
        '''
        # inherited init. Sets the file parameter
        FileParser.__init__(self, msgLog)
        self.metrics = {}

    def grabQuals(self):
        '''
            Grab the qualities in list 'quals' from the MessageStatsReport log
            file.
            
            Return
            ------
            dictionary : holding key-value pairs that describe the values in quals.
            Mostly these are metrics values we are interested in.
        '''
        with open(self.file, 'r') as f:
            for line in f:
                # line var = list holding each word in the line
                # ONE has only 2 words in each line
                # file is arranged in key value pairs one each line
                # except the first line
                if ':' not in line:
                    continue

                line = grabPairs(line, ':')

                # key = line[0]; value = line[1]

                # looking for metric value str inside log file lines
                if line[0] in self.quals:
                    # add quality key-value pair into output map
                    self.metrics[ line[0] ] = line[1]

    def getMetrics(self):
        '''
            Getter method to return the map of key-value pairs stripped from
            input file.
        '''
        return self.metrics


# util functions not part of a particular class
def grabPairs(line,separator='='):
    '''
        Grabs the key value pair inside of the input string. Assumes you are
        passing in a line of a settings file that holds key-value pairs. This
        function also strips the whitespaces from each element in the line and
        expects the key & value to have no whitespaces inside.

        Assumes the key-value pair is set using a '='

        Parameters
        ----------
        line : string containing the entire line of a settings file. This is
        expected to have a key-value pair inside of it. 

        seperator : char to split line on. The default is '='

        Ex. line = 'HeraRouter.lambda = 1,2,3,4'

        Return
        ------
        output : list with the following structure: [key, value]
    '''
    # strips the line into a list holding [key, value]
    # albeit possibly not in the correct form 
    line = line.split(separator)
    
    # strips whitespace from key and value elements in the list
    for i in range(len(line)):
        line[i] = line[i].replace(' ', '')
    
    # strip '\n' from value term of list
    line[1] = line[1].rstrip('\n')

    return line

def add2Log(smallDF, bigDF):
    '''
        concatenate two df log files containing simulation results.

        Parameters
        ----------
        smallDF : string naming the smaller dataframe you want to add
        bigDF : string naming the bigger dataframe that will grow larger
        
        Return
        ------
        void : all outputs are files being saved
    '''
    # load and assuming a std sep=','
    # assuming here that the smallDF file is NOT empty
    df = pd.read_csv(smallDF)

    # checks for empty files
    # touch file.txt creates a file.txt w/ size == 0
    if os.stat(bigDF).st_size == 0: 
        df.to_csv(bigDF, header=True, index=False)
    else:
        masterDF = pd.read_csv(bigDF)
        # concatenate and store results
        masterDF = masterDF.append(df, ignore_index=True)
        masterDF.to_csv(bigDF, header=True, index=False)

def main():
    # command line interface definitions
    parser = argparse.ArgumentParser(description=

'''ONE simulator file parser. This script processes several 
types of log files that ONE generates / uses. It then 
scrapes several key values & concatenates them into a 
master log file for futher analysis.''',

        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
'''More on Usage:
python FileParser.py [fileType option flag] <baseFile> <files...>

args
----
fileType option flag : is one of the flags in {-e, -m, -s}
<baseFile> : the base specification settings file for batch.
\tthis is required if -s is used
<files...> : file that you want to parse 
\t-e : EventLogReport.txt
\t-m : MessageStatsReport.txt
\t-s : specificationFile.txt (this is the secondary ONE settings
\t passed in to run the simulation. It holds info like 
\t Routers + Router.params
\t-a : performs all info extraction in one call to python
\t-c : concat the local sim results to the master sim results file
 ''') 

    # required argument definition. Files you need
    parser.add_argument('files', type=argparse.FileType('r'), \
                        nargs='+')

    # optional argument definitions
    parser.add_argument('-m', '--MessageReport', help='message stats file \
                        input', action='store_true', default=False)
    parser.add_argument('-s', '--Specs', help='specification file input', \
                        action='store_true', default=False)
    parser.add_argument('-e', '--EventLog', help='eventLogReport file input', \
                        action='store_true', default=False)
    parser.add_argument('-a', '--all', help='automation w/ all parsers', \
                        action='store_true', default=False)
    parser.add_argument('-r', '--reports', help='get report dir from base', \
                        action='store_true', default=False)
    parser.add_argument('-c', '--addResults', help='add sim results to log', \
                        action='store_true', default=False)

    # important call that looks at arguments you've passed in to script
    args = parser.parse_args()
    
    if args.EventLog:
        # -e flag
        # ALL file inputs should be EventLogReport.txt files
        eventLogs = [EventLog(args.files[i].name) for i in \
            range(len(args.files))]

        # parse for each log file
        for elem in eventLogs:
            # parse the eventLog
            elem.parseAttr()

            # extract values from the eventLog
            # need to add print statements here for value grabbing
            elem.nrofMsgs()
            elem.nrofReps()
            elem.calcSuccess()
            print(str(elem.calcSuccess()))

    if args.Specs:
        # -s flag
        # these files are expected to be parsed 1 at a time.
        # don't need to have built in multi-file cases
        specFile = Specs(args.files[0].name)
        out = specFile.grabSettings()

        # outs dict of desired pairs
        print(out)

    if args.MessageReport:
        # -m flag
        # ALL file inputs should be MessageStatsReport.txt files
        # turn file names into iterable w/ MsgStats objs
        msgFiles = [MsgStats(args.files[i].name) for i in \
            range(len(args.files))]

        # outs dict w/ desired metric pairs
        for elem in msgFiles:
            elem.grabQuals()
            print(elem.getMetrics())

    if args.reports:
        # -r flag
        # expects a baseFile.txt input
        # prints out the partial path of reports dir
        # set in the baseFile.txt
        baseFile = Base(args.files[0].name)
        bmap = baseFile.grabSettings()
        for elem in bmap:
            if elem == 'ReportDir':
                report = bmap[elem]
                break

        # ensure there exists a trailing / in the return file path
        if report[-1] != '/':
            report = report + '/'

        print(report)


    if args.addResults:
        # -c flag
        # expects 3 file names:
        # smallDF, bigDF, backup
        # give full path for backup so that it can be stored correctly
        # assumed smallDF & bigDF inside the current dir .
        smallDF = args.files[0].name
        bigDF = args.files[1].name

        # concatenate & save a backup
        add2Log(smallDF, bigDF)
            
    if args.all:
        # condense file parsing to only one call of python interpretor
        # expects a specific file order
        # <base> <specs> <MsgStats> <Elog> <csvFile>
        # expects csvFile to have a header
        
        # output csv formatted line. 
        header = []
        row = []

        # file 1, batch file
        batchFile = FileParser( args.files[0].name )
        header.append( 'batch' )
        row.append( batchFile.getPathLeaf() )

        # file 2, specFile name, router information
        specFile = Specs(args.files[1].name)
        header.append( 'specFile' )
        row.append( specFile.getPathLeaf() )
        
        # process the specFile & add
        specMap = specFile.grabSettings()
        for elem in specMap:
            header.append(elem)
            row.append(specMap[elem])

        # file 3, message stats
        msgFile = MsgStats(args.files[2].name)
        msgFile.grabQuals()
        msgMetrics = msgFile.getMetrics()
        for elem in msgMetrics:
            header.append(elem)
            row.append(msgMetrics[elem])

        # file 4, replicas, success ratio 
        eLog = EventLog(args.files[3].name)
        eLog.parseAttr()
        header.append('Replicas')
        header.append('Delivery_Ratio')

        # need string conversion here b/c all other vars are str
        # will throw error if you try to use non-strings for print
        row.append(str(eLog.nrofReps()))
        row.append(str(eLog.calcSuccess()))

        # create a row dataframe to append to local chunk
        df = pd.DataFrame(columns = header)
        df.loc[0] = [ row[i] for i in range(len(row)) ]
        
        # load local csv of sim results
        # assuming std ',' delim file
        # this is handling the mismatch of column cases in
        # event that a new column is created
        # checks for empty file, if so write results, else append
        if  os.stat(args.files[4].name).st_size == 0:
            df.to_csv(args.files[4].name, sep=',', header=True, index=False)
        else:
            masterDF = pd.read_csv(args.files[4].name)
            masterDF = masterDF.append(df, ignore_index=True)
            # write back to file
            masterDF.to_csv(args.files[4].name, sep=',', header=True, index=False)


if __name__ == '__main__':
    main()
