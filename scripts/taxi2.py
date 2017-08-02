#!/usr/bin/python2

# need utm package ->
# transforms data into x,y form
# python script to handle epfl taxi data
# assuming some of epfl's data structure

import pandas as pd
import numpy as np
import utm

class Taxi:
    """ 
    epfl taxi data parser,
    @ args = taxi data txt file 
    @ out = taxi file in ONE compliant ext mov file
    """

    def __init__(self, filename, id, oprefix="node", logFile="taxi.log"): 
        """ constructor for taxi class obj.

        parameters: 
        ==========================================================
        filename & id should be required variables as we don't want overwrite

        filename = string var of input data file name

        id = int number used in the out file name. Also used as
        a unique node id in out file. Remember this needs to be 0 start index.  

        oprefix = output file prefix ex. if you want all outs node1.txt (the
        default) you should put the string to replace "node"

        logfile = optional string var specifying the name of the log file to
        dump min,max pairs of X and Y coords for self.file
        """
        
        # used to spec file to grab data from
        self.file = filename
        
        # controls output file properties
        self.id = id
        self.oprefix = oprefix
        self.logFile = logFile

        # attr stats is the taxi file vals you want to dump a
        # log file, e.g. badDataCnt, xmin, xmax, ymin, ymax, 
        # here badDataCnt is the number of records (aka rows) of data
        # you removed
        self.stat = ''


    # helper function for modData
    # generate pandas ver of data for manip later
    # No required input
    # returns a dataframe obj using pandas csv function
    def grabData(self):
        return pd.read_csv(self.file, sep=' ', header=None)

    # helper function, writes data to output file
    # @input df = dataframe you need to write to file
    # this df is the post-proc dataframe
    # @return = void 
    def writeData(self, df):
        # create output filename str from nodeId & oprefix
        out = self.oprefix + str(self.id) + ".txt"

        # don't add row number (aka index) column or headers
        # use ' ' (space) separator
        df.to_csv(out, sep=' ', index=False, header=False, mode='w')

    # turns the in mem data df into desired output format
    # Does the following modifications
    # insert unique node id as 2nd col
    # make unix time column 1 (1 = starting index)
    # convert GPS coords to utm ~ cartesian coords
    def modData(self):
        # Const vars for taxi format
        STORE_SIZE = 3          # Nr of cols in storage matrix
        LAT = 0                 # df's latitude data column nr
        LON = 1                 # df's longitude data column nr
        X = 1                   # storage matrix's lat col nr
        Y = 2                   # storage matrix's lon col nr
        TIME = 3                # df's unix time column nr
        ST_TIME = 0             # storage matrix's time column nr
        LATMID = 37             # val for lat that all others are near
        LONMID = -122           # val for lon thta all others are near

        # get data into a dataframe
        data = self.grabData()

        # Dataset's original size
        TOTAL = data.shape

        # prune data by looking at lat,lon 
        # want only lat,lon pairs w/ (+/-)1 in lat & lon coords
        # +/- 1 from (37, -122)
        data = data[ data[LAT].between(LATMID-1, LATMID+1) &\
                data[LON].between(LONMID-1, LONMID+1) ]

        # need to reindex b/c now have index lines w/ missing
        # values. Will broadcast to the full index side with NaN
        # for missing values
        # the drop=True drops the old index column. If left will still
        # get bad index values & a new index column
        data = data.reset_index(drop=True)

        # Find the number of dumped data records
        badDataCnt = TOTAL[0] - data.shape[0]

        # append badDataCnt to log file string
        self.setStat(str(badDataCnt))

        # nodeID, x, y cols of final data; created for storage
        storage = pd.DataFrame(self.id, index=np.arange(data.shape[0]),\
            columns=np.arange(STORE_SIZE))

        # inserting converted vals of GPS -> UTM coords
        # grab the utm_x and utm_y (first two vals), 
        # last two are dci => don't care i values 
        # Need 4 vars to match syntax of utm script and strip utm vals
        for i in range(data.shape[0]):
            storage.iloc[i,X], storage.iloc[i,Y], dc1, dc2 = \
                utm.conversion.from_latlon(data.iloc[i,LAT],\
                data.iloc[i,LON])

        # construct the output ver of df
        data = pd.concat([ data[TIME], storage[ST_TIME], storage[X], \
            storage[Y]], axis=1, keys=["time", "nodId", "utmX", "utmY"]) 

        # returns modified dataframe in correct output format
        return data


    # find the optimal utm values from transformed dataframe
    # @input df = dataframe you need to extract min & max col vals of
    # @input lst = list of column labels / id's you need min and max of 
    # @return = list w/ adjacent min, max pairs for each elem of lst input 
    def findMinMax(self, df, lst):
        # return list init
        optimum = []

        # calc min and max, append to optimum
        # use pd's .min() & .max() func. faster
        for elem in lst:
            optimum.append( df[ elem ].min() )
            optimum.append( df[ elem ].max() )

        return optimum

    # append input to log file string
    # Parameters:
    # @arg value = string that you want to append to log file string
    # @return = void (manips internal self.stats str var
    def setStat(self, value):
        # add a space to the end of the self.stat line
        # if there is text already there
        if(len(self.stat) != 0):
            self.stat += ' '

        # handling diffent types of inputs
        # direct append for strings
        # if it's a list (like optima) turn into a str then 
        # append
        if type(value) == str:
            self.stat += value

        # turns list inputs into str then appends
        elif type(value) == list:
            appStr = " ".join(str(elem) for elem in value)
            self.stat += appStr

        # for bad values raise error
        else:
            raise ValueError

    # append optimal x and y values to a file
    # optimum is a list of optimal values you want to dump to logfile
    # optimum should be in correct order of (minA, maxA, minB, maxB, ...)
    def dump2Log(self):
        # write log file string self.stat to log file  
        with open(self.logFile, 'a') as f:
            f.write(self.stat + '\n')



###################################################################################
## Separate main() function to run cmd line script 

# usage: python taxi2.py < taxi files > 
def main():                                                                                          
    # get command line args, base file and spec files                                                
    parser = argparse.ArgumentParser()                                                               
    parser.add_argument('files', type=argparse.FileType('r'), \
                        nargs='+')
    args = parser.parse_args()                                                                       
    # create list of ELog elems to parse
    taxiFleet = [Taxi(filename=args.files[i].name, id=i) for i in range(len(args.files))]
    
    for cab in taxiFleet:
        # get the dataframe you want to output as csv
        out = cab.modData()             # output dataframe

        # find optima from dataframe
        cols = ["utmX", "utmY"]         # columns you need optima of
        optima = cab.findMinMax(out, cols)

        # write operations, 
        # write optima to log & data to new txt file
        # log file has format badDataCnt, minX, maxX, minY, maxY
        cab.setStat(optima)
        cab.dump2Log()
        cab.writeData(out) 

if __name__ == '__main__':
    import argparse
    main()
