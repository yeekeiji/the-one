#! /bin/sh

# original settings
# java -Xmx512M -cp target:lib/ECLA.jar:lib/DTNConsoleConnection.jar core.DTNSim $*

# changed heap to accelerate simualtions, changed -Xmx512M to -Xmx2048M
# Increases the amount of heap memory allocated to JAVA vm
# java -Xmx2048M -cp target:lib/ECLA.jar:lib/DTNConsoleConnection.jar core.DTNSim $*

# alt ver for Maxprop's TimSort error
# when running Maxprop b/c of one of the network flow algs, will get this error
java -Xmx8G -Djava.util.Arrays.useLegacyMergeSort=true \
 -cp target:lib/ECLA.jar:lib/DTNConsoleConnection.jar core.DTNSim $*
 
