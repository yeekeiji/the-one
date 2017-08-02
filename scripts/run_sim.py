import argparse
import shlex
from fileParse import FileParse
from subprocess import Popen, PIPE, STDOUT

class DTNSim:
    """ a simulation obj to automate multiple simulation
        calls
    """
    
    # base_file = str of base file name
    # specs_file = str of specs file name
    def __init__(self, base_file, specs_file):
        self.cmd = '/bin/sh one.sh -b 1 file1 file2'
        self.base = base_file
        self.specs = specs_file

    def createLog(self):

        baseFile = FileParse(self.base)
        specsFile = FileParse(self.specs)
        logFile = specsFile.getCoreName(1)

        
        with open(logFile, 'w') as f:
            # assuming base file name is the name of the batch
            f.write( 'Batch = ' + baseFile.getCoreName(0) + '\n' )
            f.write( 'Base File = ' + baseFile.getPathLeaf() + '\n' )
            f.write( 'Settings File = ' + self.specs + '\n' )
            f.write( 'Log File = ' + logFile + '\n' )
            f.write( 'ID = ' + baseFile.getCoreName(0) + \
                '_' + self.getCoreName(self.specs, 0) + '\n')
            f.write( 'Dataset = ' + baseFile.getDataName() + '\n' )
            d = specsFile.getSpecs()
            for i in d:
                f.write(i + ' = ' + d[i] + '\n') 


    def RunCmd(self):
        # creating correct cmd for bash
        self.cmd = shlex.split(self.cmd)
        self.cmd[4] = self.base
        self.cmd[5] = self.specs

        # create logfile name from specs file
        logFile = self.getCoreName(self.specs, 1)

        with Popen(self.cmd, stdout=PIPE, stderr=STDOUT,\
                   bufsize=1) as p,\
                   open(logFile, 'a') as f:
            for line in p.stdout:
                print(line.decode("utf-8"))
                f.write(line.decode("utf-8"))

def main():

    # get command line args, base file and spec files
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=argparse.FileType('r'), \
                        nargs='+')
    args = parser.parse_args()
 
    # create DTNSim obj for each specs file
    base = args.files[0]
    simList = [DTNSim(base.name, args.files[i].name) for i in \
                range(1, len(args.files))]

    for i in simList:
        print(i.base)
        print(i.specs)
    # run each simulation cmd one by one
    for sim in simList:
        sim.createLog()
        sim.RunCmd()

if __name__ == '__main__':
    main()

