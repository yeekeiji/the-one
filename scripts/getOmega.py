# create plots of Omega values over time
# generates a data file that has the progression of omega values

# USAGE NOTES:
# ------------
# USAGE: python getOmega.py [option] <files>
# Computing Omega file ( yields a 2 column csv with (time, omega) pairs
# ex. python getOmega.py -c mDataFile.txt output.txt gamma.txt
# Input1: mDataFile.txt = file generated from mExtract.sh. Csv of matrix data from sim
# Input2: output.txt = file name you want to output to. If dne will be created in
#       current dir
# Input3: gamma.txt = space delimited file of gamma values to use for this
#       computation. The number of gammas must match the number of hops in
#       mDataFile.txt
#
# ex. python getOmega.py -p omegaFile.txt -n r122
# Input1: omegaFile.txt = csv file of (time, omega) pairs. Output from -c
#       option. MUST prefix with '-p'
# Input2: r122 = name of node in same format. Ex. if you want a node from group
#       s labeled as 106 -> s106. MUST prefix with '-n'
# ---------------

# compute omega(m) where omega is the following formula:
# m = vector of hops = h+1 elements, gamma matches the size of m
# Dot product between m and gamma vector. Gamma is a control vector 
# that controls how much we care about each relay of information
# Omega(m) = sum( gamma(i) * m(i) ) = < gamma, m >
def omega(gamma, m):
    if( len(gamma) != len(m) ):
        raise ValueError('Mismatch in dimensions of gamma or m. Must be the \
        same size')
    else:
        out = 0;
        for i in range(len(m)):
            out += gamma[i]*m[i]

        return out

# command line interface
def main():
    # command line interface definitions
    parser = argparse.ArgumentParser(description=
'''Compute omega values from matrix files''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
'''More on Usage:
python getOmega.py <matrixFile> <outputFile> <gammaFile>
gammaFile = space delimited row of values to use as gamma
outputFile = Name of the output file you want
matrixFile = data file with m values
 ''') 

    # required argument definition. Files you need
    parser.add_argument('files', type=argparse.FileType('r'), \
                        nargs='+')
    parser.add_argument('-c', '--compute', help='compute omegas from data',
                        action='store_true', default=False)
    parser.add_argument('-p', '--plot', help='create time vs. omega plot',
                        action='store_true', default=False)
    parser.add_argument('-n', '--node', type=str, help='name of node that you \
        followed')

    # important call that looks at arguments you've passed in to script
    args = parser.parse_args()
    
    if args.plot:
        # import required libs
        import pandas as pd
        import matplotlib.pyplot as plt

        # grab csv data & store in dataframe
        df = pd.read_csv(args.files[0].name, header=None)

        # plot time vs omega values
        plt.plot(df[0], df[1])

        # add labels and title
        plt.xlabel('Simulation Time (s)')
        plt.ylabel('Omega(m)')
        plt.title('Progression of Omega over Time wrt ' + args.node)

        # save file
        plt.savefig(args.node+'OmegaPlot.txt')


    if args.compute:
        gamma = []

        with open(args.files[2].name, 'r') as f:
            line = f.read()
            line = line.split()
            for elem in line:
                gamma.append(float(elem))
                
        with open(args.files[1].name, 'w') as g:
            with open(args.files[0].name, 'r') as f:
                for line in f:
                    m = []
                    line = line.split(',')
                    for i in range(len(line)-3):
                        m.append(float(line[i+3]))
                    # need to put in gamma values 
                    value = omega(gamma, m)
                    g.write(str(line[0]) + ',' + str(value) + '\n')

if __name__ == '__main__':
    import argparse
    main()
