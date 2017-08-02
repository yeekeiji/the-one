# Script File Guide

## taxiScript.sh

Automation of transforming raw epfl taxi data files into a single movement data
file for ONE. 

usage: `sh path/to/taxiScript.sh <number>`

The number is to specify the number of taxi files to make a movement dataset out
of. By default it will be 25 taxi files. Max of 536 taxi files can be selected

### Warnings

 - don't move the script or script/ dir. The script uses relative paths of
   both of these to call other scripts. 
 - install utm 0.4.2 from [pypi][utm].
 - assumes you have installed utm lib in a py env called python2. Please change
   this line in the script to whichever python env you have utm installed. 

[utm]: https://pypi.python.org/pypi/utm

## taxi2.py

Transforms individual taxi files into a modified form. Outputs files are of the 
form "node<nodeID>.txt where <nodeID> is the assigned node number. These 
nodeID's represent loop count that a particular file happened to be processed
in. Example: the 10th file to be processed by taxi2.py will have nodeID = 10.

 - rearranges the columns
 - transforms GPS coords into utm coordinates
 - adds a node id column, all with the same value b/c each file represents a
   single taxi.
 - removes the occupancy column

## taxiLog.py

Transforms the output files of taxi2.py into a single movement file. It also
shifts the value of all records to be the distance from the smallest value in
each column. This is to make the numbers smaller as the original data required
long long ints.

usage: `taxiLog.py <taxi.log> <node_master.txt>`


