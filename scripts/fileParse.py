import ntpath

class FileParse:
    """ use a passed file as attribute. return information about passed file
    """

    # init func. Assume fileName is str
    def __init__(self, fileName):
        '''
            construtor function. It initializes the FileParse class obj.

            Parameters
            ----------
            fileName : String describing a ONE compliant file's name string.
        '''
        self.file = fileName

    def getPathLeaf(self, path=None):
        '''
            Grabs a file name w/out the full path 

            Parameters
            ----------
            path : String describing the full file path name of a file
            default value : obj's own self.file that describes the FileParse
            obj, assigned inside of function

            Examples
            --------
            path = '/home/userName/Documents/coolFile.txt'
            getPathLeaf(path) -> returns : coolFile.txt
        '''
        # sets default value for path if no value is given
        if path == None:
            path = self.file
            
        head, tail = ntpath.split(path)
        return tail

    def getCoreName(self, rType):
        '''
            Returns the core name or .log version of name.
            Core name => file name w/out extension

            Parameters
            ----------
            rType : int {1 or 0}. 
                0 = someFile.ext (i.e. it has an extension that you want to get
                rid of)

                1 = someFile.ext and you want someFile.log

        '''
        fileName = self.file[:self.file.find('.')]
        if rType == 0:
            return fileName
        else:
            return fileName + '.log'

    def getDataName(self):
        '''
            Get the dataset's name from the base settings file
        '''
        with open(self.file, 'r') as f:
            for line in f:
                if 'ExternalEvents.filePath' in line:
                    spot = line.find('=')
                    if line[spot + 1] == ' ':
                        filePath = line[(spot + 2):]
                    else:
                        filePath = line[(spot + 1):]
                    return self.getPathLeaf(filePath)
                    
                else:
                    continue

            # fails to find dataset in file
            return 'no dataset given'

    def getSpecs(self):
        '''
            return dictionary of all settings
            EXCEPT:
                1. Scenario.name
        '''
        specs = {}
        with open(self.file, 'r') as f:
            for line in f:
                if '#' in line:
                    continue
                elif 'Scenario.name' in line:
                    continue
                else:
                    spot = line.find('=')
                    if line[spot - 1] == ' ':
                        key = line[:( spot-1 ) ]
                    else:
                        key = line[:spot]

                    if line[spot + 1] == ' ':
                        val = line[: ( spot + 2 ) ]
                    else:
                        val = line[: ( spot + 1 ) ]

                    temp = {key, val}
                    specs.update(temp)

            return specs
