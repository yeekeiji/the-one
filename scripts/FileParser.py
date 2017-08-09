#!/usr/bin/python3
# python scripts to parse the-one sim files

import argparse
import ntpath
import shlex
from subprocess import Popen, PIPE, STDOUT

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
            nrofReps = #( unique msgs ) + #( replicas )
            
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
        return float(self.totalD) / float(self.totalC)

    def parseAttr(self):
        '''
            Main parser function that constructs 
                a. the msg dict
                b. created messages
                c. delivered messages
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

    def __init__(self, spec):
        FileParser.__init__(self, spec)


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
    quals = ['latency_avg:',\
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

    def grabQuals():
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
                line = line.split()
                key = line[0]
                value = line[1]

                # looking for metric value str inside log file lines
                if key in quals:
                    # add quality key-value pair into output map
                    self.metrics[ key[:-1] ] = value

