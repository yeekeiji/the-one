#! /usr/bin/env python2

import pandas as pd

# usage: python taxiLog.py < logFile > < dataFile >
# example: python taxiLog.py taxi.log node_master.txt 
# above is the default values for log & total taxi file
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=argparse.FileType('r'),\
                        nargs='+')

    args = parser.parse_args()

    # expecting two input files as command line options
    # logFile = the taxi.log file w/max,min & badDataCnt
    # dataFile = the full sorted / concat file of all data
    logFile = args.files[0].name
    dataFile = args.files[1].name

    df = pd.read_csv(logFile, sep=' ', header=None)
    
    # number of data records rm from original data
    # during munging step
    badDataCnt = df[0].sum()

    # Not sure what to do with val atm
    # send to screen
    # may need to redirect & save in file later
    print("Number of latlon Coordinates: " + str(badDataCnt))

    # x and y min 
    # use these to shift starting points of each important col
    xmin = df[1].min()
    ymin = df[3].min()

    # data is the FULL concat & sorted file
    # expected to be in the following form:
    # time nodeId xCoord yCoord
    data = pd.read_csv(dataFile, sep=' ', header=None)

    # need to extract the time min value
    # ESPECIALY the min to normalize the time values 
    timeMin = data[0].min()

    # shifting wrt to the smallest value in each data column
    data[0] = data[0] - timeMin
    data[2] = data[2] - xmin
    data[3] = data[3] - ymin

    # need to grab new values for min & max b/c not abs vals
    # min & max have changed b/c of the shift ops above
    # in the new data set you are dumping to file
    timeMin = data[0].min()
    timeMax = data[0].max()
    xmin = data[2].min()
    xmax = data[2].max()
    ymin = data[3].min()
    ymax = data[3].max()

    data.to_csv("node_master.txt", sep=' ', index=False, header=None)
    
    # dump mv file header to a new file. Need to concat on cmdline 
    # afterwards to get full ONE compliant data file
    header = [timeMin, timeMax, xmin, xmax, ymin, ymax] 

    with open("nodeData.txt", 'w') as f: 
        f.write( (' '.join( str(elem) for elem in header) ) + '\n')

    # DO node_master.txt >> nodeData.txt on the command line as the last 
    # processing step
    # use nodeData.txt, this is the final movement file that should work
    # in the ONE simulator

if __name__ == "__main__":
    import argparse
    main()

