import argparse
import shlex
import sys
from subprocess import Popen, PIPE, STDOUT

class ELog:
    """ Event log objects w/ methods to track attr
    """
 

    # eventLog = str of EventLogReport file name
    def __init__(self, eventLog):
        self.logFile = eventLog
        self.totalC = 0
        self.totalD = 0
        self.msgs = {}

    # checks the msgs dict to see if already tracking replica cnt
    # @param msgName string name of msg you are checking, ex: 'M1'
    # @return bool {True, False} referencing whether msgName is in dict msgs
    def isTracked(self, msgName):
        if msgName in self.msgs:
            return True
        else:
            return False

    # getter method for logFile string name
    def getLogName(self):
        return self.logFile

    # getter metod for dictionary of msgs
    def getMsg(self):
        return self.msgs

    # getter method for total number of created msgs
    def getCCnt(self):
        return self.totalC

    # getter method for total number of delivered msgs
    def getDCnt(self):
        return self.totalD

    # total number of unique messages in report file
    # note this is the same as var totalC
    def nrofMsg(self):
        return len(self.msgs)

    # number of replicas
    def nrofReps(self):
        return sum(self.msgs.values())

    # setter method to add msgName to msg dictionary
    # input is a msgName string, inits value to 1
    def msgAdd(self, msgName):
        self.msgs[msgName] = 1

    # setter method to update existing cnt of msgName replicas
    def msgUpdate(self, msgName):
        self.msgs[msgName] += 1

    # calcs the successful delivery ratio
    def calcSuccess(self):
        return float(self.totalD) / float(self.totalC)

    # calcs the msg dict, total created and delivered msgs
    def parseAttr(self):
        with open(self.logFile, 'r') as f:
            for line in f:
                # don't grab the /n char
                line = line[:-1]
                content = line.split()
                msgName = ''

                # finding the msg that triggered event
                for elem in content:
                    if 'M' in elem:
                        msgName = elem
                        break

                #if 'C' in content and self.isTracked(msgName):
                #    print(content)
                # update if tracked, add if not
                # skip if no mgs ref in line
                if self.isTracked(msgName):
                    if 'DE' in content:
                        if 'D' in content:
                            self.totalD += 1
                        else:
                            self.msgUpdate(msgName)
                    else:
                        continue
                elif msgName == '':
                    continue
                elif 'C' in content:
                    self.msgAdd(msgName)
                    self.totalC += 1

    # print the summary of EvenLogReport file
    def summary(self):
        print(self.getLogName())
        print('\tNumber of unique msgs created = ' + str(self.nrofMsg()))
        print('\tNumber of delivered msgs = ' + str(self.getDCnt()))
        print('\tSuccessful Delivery Ratio = ' + \
            str(self.calcSuccess()))
        print('\tNumber of Replicas = ' + str(self.nrofReps()))

    # turns relevant data into json data format. 1 json document for each Elog
    # NEED TO DO STILL
    # def datify(self):
        

def main():

    # get command line args, base file and spec files
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=argparse.FileType('r'), \
                        nargs='+')
    args = parser.parse_args()
 
    # create list of ELog elems to parse
    eventLogs = [ELog(args.files[i].name) for i in range(len(args.files))]
    
    for elem in eventLogs:
        elem.parseAttr()
        elem.summary()
        print()
    
if __name__ == '__main__':
    main()

