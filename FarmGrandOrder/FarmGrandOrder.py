import configparser
import csv
import glob
import numpy as np
import cvxpy as cp

class Nodes:
    def __init__( self , goals , materialListCSV , removeZeros = 'n' ):
        self.matCount = 0
        self.matTotal = 0
        self.skipID = {}
        self.skipDataIndex = {}
        self.removeZeros = removeZeros

        self.goals = []
        self.IDtoIndex = {}
        self.indexToName = {}
        self.lottoIndex = [[],[],[],[],[],[]]
        self.interpretMats( goals, materialListCSV )

        self.nodeNames = []
        self.APCost = []
        self.runCap = []
        self.dropMatrix = np.array([])
        self.hellfireRange = [94,100]

    def lottoIndexInit( self , gaps , currentMaterial ):
        error = ''
        if gaps == 3:
            if currentMaterial != 'Gem of Saber':
                error = 'Blue Gems'
        if gaps == 4:
            if currentMaterial != 'Magic Gem of Saber':
                error = 'Red Gems'
        if gaps == 5:
            if currentMaterial != 'Secret Gem of Saber':
                error = 'Gold Gems'
        if gaps == 6:
            if currentMaterial != 'Saber Piece':
                error = 'Statues'
        if gaps == 7:
            if currentMaterial != 'Saber Monument':
                error = 'Monuments'
        if gaps == 8:
            if currentMaterial != 'Saber Blaze':
                error = 'XP'
        
        if error != '':
            debug.errorWarning( 'Does not seem to be the start of '+ error +'. GOALS CSV may need to be updated.' )
        return -1 * ( gaps - 2 ) 

    # Creates four dictionaries, one mapping a Material's ID to placement in Drop Matrix, one mapping placement in Matrix to its Name,
    # one interprating whether a Material's calculation should be skipped by its ID, and another interprating by its placement in the data matrix.
    # Also transforms the data in the GOALS csv into a computable matrix.
    def interpretMats( self, goals, materialListCSV ):
        with open( materialListCSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            matID = next(reader)
            while( matID[0][0:2] != 'ID' ):
                matID = next(reader)
            matName = next(reader)
            f.close()
        
        with open( goals, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            readLine = next(reader)

            count = 0
            index = 0
            gaps = 0

            lottoIndexPointer = 0
            change = False
            skip = False

            for row in reader:
                try:
                    matGoal = int(row[1])
                except:
                    matGoal = 0
                
                if matGoal == 0 and self.removeZeros == 'y':
                    skip = True
                
                self.skipDataIndex[count] = skip
                count += 1
                self.skipID[ int(matID[count]) ] = skip

                if change == True:
                    change = False
                    lottoIndexPointer = self.lottoIndexInit( gaps , row[0] )

                if row[0][0:2] == '!!':
                    gaps += 1
                    change = True
                    if matName[count] != '':
                        debug.errorWarning( 'Gaps between materials in GOALS and the Material List/Calc CSVs do not align. One may need to be updated.' )
                else:
                    if lottoIndexPointer < 0 and not skip:
                        self.lottoIndex[lottoIndexPointer].append( matID[count] )

                if skip == True:
                    skip = False
                else:
                    self.goals.append( [matGoal] )
                    
                    self.IDtoIndex.setdefault( matID[count], index )
                    self.indexToName.setdefault( index, matName[count] )
                    index += 1
            f.close()

        if self.indexToName[index-1] == 'Saber Blaze':
            self.indexToName[index-1] = 'Class Blaze'

        self.matCount = index
        self.matTotal = count
        if matGoal == 0 and self.removeZeros == 'y':
            skip = True
        for i in range(15):
            self.skipDataIndex[count] = skip
            count += 1
            self.skipID[ int(matID[count]) ] = skip
            self.IDtoIndex.setdefault( matID[count], self.matCount-1 )
        
        self.skipID[-6] = skip
        for i in range(-5,0):
            if self.lottoIndex[i] == []:
                skip = True
            else:
                skip = False
            self.skipID[i] = skip
        
        self.goals = np.array(self.goals)

    # TODO: There are some issues with this method of assembling matrices.
    # The basic issue is that cvxpy analysis requires data in the form of numpy matrices, but the best way to form numpy matrices is to initialize its size.
    # This is because vstacking numpy matrices line by line is slow, because it rewrites the entire matrix every time.
    # ^^^ NOT CONFIRMED, maybe that's what I should do.
    # Unfortunately, in order to initialize the size, we have to know how many lines the csv is. This apparently requires reading through the entire csv once.
    # Since the csv's have to be read and added to the data line by line, this would be inelegant/slow.
    # For the above reasons, I have instead opted to put the data from the csv into an array first, and then turn those arrays into a numpy matrix before stacking.
    # This seems to have caused an issue with making a 'Run Cap' constraint, as the column matrixes are size '(X,)' rather than '(X,1)'
    # This doesn't make sense and tells me there needs to be some changes.

    # FIXED SIZE PROBLEM: rest should still be looked into.
    def assembleMatrix( self, addAPCost, addRunCap, addDropMatrix ):
            if np.size( self.dropMatrix ) == 0:
                self.APCost = np.array( addAPCost )
                self.runCap = np.array( addRunCap )
                self.dropMatrix = np.array( addDropMatrix )
            else:
                self.APCost = np.vstack(( self.APCost, addAPCost ))
                self.runCap = np.vstack(( self.runCap, addRunCap ))
                self.dropMatrix = np.vstack(( self.dropMatrix, addDropMatrix ))
    
    def addEventDrop( self, eventDropCSV, eventCap = '' ):
        start = eventDropCSV.rindex('Efficiency_ ')
        eventName = eventDropCSV[(start+12):eventDropCSV.rindex(' - Event',start)]

        with open( eventDropCSV, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            eventDrop = next(reader)
        
            # Finds where the lotto material drops start in the csv, as the formatting changes for these.
            materialLoc = []
            count = 0
            for i in eventDrop:
                if i == 'ID': 
                    materialLoc.append(count)
                count += 1

            eventAPCost = []
            eventDropMatrix = []
            eventRunCap = []

            # Interpretation of how this is supposed to read the Event Quest csv:
            # If there is no material assigned in the first slot, skip this line.
            # If there is an AP assigned, assume the drops are part of a new node and start a new line of the Drop Matrix.
            # Add drops to the last made line in the Drop Matrix.
            for eventNode in reader:
                if materialLoc[0] == '': 
                    continue

                if eventNode[1] != '':
                    self.nodeNames.append( eventName + ', ' + eventNode[0] )
                    eventAPCost.append( [float(eventNode[1])] )
                    eventRunCap.append( [eventCap] )
                    eventDropMatrix.append( np.zeros( self.matCount ) )

                for i in materialLoc:
                    if eventNode[i+2] != '':
                        matID = [int(eventNode[i])]
                        if self.skipID[matID[0]]:
                            continue

                        dropRate = float(eventNode[i+2]) / 100
                        if matID[0] >= self.hellfireRange[0] and matID[0] <= self.hellfireRange[1]:
                            dropRate *= 3

                        if matID[0] < 0:
                            matID = self.lottoIndex[matID[0]]
                        for j in matID:
                            eventDropMatrix[-1][ self.IDtoIndex[str(j)] ] += dropRate

            f.close()
            
            self.assembleMatrix( eventAPCost, eventRunCap, eventDropMatrix )
    
    def addFreeDrop( self, freeDropCSV, lastArea = 'ZZZZ' ):
        with open( freeDropCSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            freeDrop = next(reader)

            freeAPCost = []
            freeRunCap = []
            freeDropMatrix = []

            # Interpretation of how this is supposed to read the APD csv:
            # If the Singularity is further than the user wants to farm as defined in the config file, stop.
            # If the line is filler because the original google sheet copies the Japanese document formatting, skip it.
            # Else, start a new line of drop rate data.
            for freeDrop in reader:
                if freeDrop[0].find( lastArea ) >= 0: 
                    break

                if freeDrop[2] == '' or freeDrop[2] == 'AP': 
                    continue

                nodeAP = int(freeDrop[2])
                self.nodeNames.append( freeDrop[0] + ', ' + freeDrop[1] )
                freeAPCost.append( [nodeAP] )
                freeRunCap.append( [100000] )
                dropMatrixAdd = []

                if self.removeZeros == 'y':
                    count = -1
                    for i in freeDrop[4:(self.matTotal+4)]:
                        count += 1
                        if not self.skipDataIndex[count]:
                            try: 
                                dropMatrixAdd.append( nodeAP / float(i) )
                            except:
                                dropMatrixAdd.append(0)
                    
                    if not self.skipDataIndex[count+1]:
                        XPMult = 1
                        for i in range(self.matTotal+4,self.matCount+18):
                            if i == self.matCount + 10:
                                XPMult = 3
                            try:
                                dropMatrixAdd[-1] += XPMult * nodeAP / float(freeDrop[i])
                            except:
                                dropMatrixAdd[-1] += 0
                
                else:
                    for i in freeDrop[4:(self.matCount+3)]:
                        try: 
                            dropMatrixAdd.append( nodeAP / float(i) )
                        except: 
                            dropMatrixAdd.append(0)
                    
                    dropMatrixAdd.append(0)
                    XPMult = 1
                    for i in range(self.matCount+3,self.matCount+18):
                        if i == self.matCount + 10:
                            XPMult = 3
                        try:
                            dropMatrixAdd[-1] += XPMult * nodeAP / float(freeDrop[i])
                        except:
                            dropMatrixAdd[-1] += 0

                freeDropMatrix.append( dropMatrixAdd )
            f.close()
            
            self.assembleMatrix( freeAPCost, freeRunCap, freeDropMatrix )
    
    def multiEvent( self, multiEventFolder, eventCap = '' ):
        for i in multiEventFolder:
            self.addEventDrop( i , eventCap )
        return 'Multi'

# Makes it so the program works whether it's started in the 'FarmingGrandOrder' overarching directory or the 'FarmGrandOrder' folder.
# May be unnecessary, but trying to get python file pathing to work is more annoying than I remember.
def standardizePath():
    pathDir = ''
    if glob.glob('FarmGrandOrder') == []:
        return '..\\' + pathDir
    else: return pathDir

# Compiles statements to be included in the Debug output text file.
class Debug:
    def __init__( self , pathPrefix ):
        self.error = ''
        self.configNotes = 'The Path Prefix is: ' + pathPrefix + '\n'
        self.endNotes = ''

        self.notifications = True
        self.notifications = self.config('Notifications', 'bool')
    
    def errorWarning( self , note ):
        note = '!! ' + note
        if self.notifications == 'y':
            print(note)
        self.error += note + '\n'

    def config( self , key , type = '' , section = 'DEFAULT' ):
        keyValue = config[section][key]

        if type == 'int':
            try:
                keyValue = int(keyValue)
            except:
                self.errorWarning( 'Configuration "' + key + '" was not a number.')
                keyValue = 'False'

        if type == 'float':
            try:
                keyValue = float(keyValue)
            except:
                self.errorWarning( 'Configuration "' + key + '" was not a number.')
                keyValue = 'False'

        if type == 'bool':
            x = keyValue.lower()
            if x == '1' or x == 'true' or x == 't' or x == 'yes' or x == 'y' or x == 'on':
                keyValue = True
            else:
                if x == '0' or x == 'false' or x == 'f' or x == 'no' or x == 'n' or x == 'off':
                    self.errorWarning( 'Configuration "' + key + '" was not a yes or no/true or false.')
                keyValue = False
    
        self.configNotes += key + ' = ' + str(keyValue)
        return keyValue

    def makeNote( self , note ):
        if self.notifications == 'y':
            print(note)
        self.endNotes += note + '\n'

def planner( nodes , notes , type = 'nonneg' ):
    dropMatrix = np.transpose( nodes.dropMatrix )
    APCost = np.transpose( nodes.APCost )
    runSize = np.size( APCost )
    if type == 'nonneg': 
        runs = cp.Variable( (runSize,1) , nonneg=True)
    else: 
        runs = cp.Variable( (runSize,1) , integer=True )

    for i in range(nodes.matCount):
        for j in dropMatrix[i]:
            if j > 0: break
        else:
            if nodes.dictIndexToName[i] != '':
                notes.makeNote( 'Obtaining any ' + nodes.dictIndexToName[i] + ' is impossible with these restrictions.' )
                nodes.goals[i] = 0

    objective = cp.Minimize( APCost @ runs )
    constraints = [ dropMatrix @ runs >= nodes.goals ]
    prob = cp.Problem( objective , constraints )
    prob.solve()

    if type == 'nonneg':
        runClean = np.zeros( (runSize,1) , dtype = int)
        count = 0
        for i in runs.value:
            if i[0] < 0.1: 
                runClean[count,0] = 0
            else: 
                runClean[count,0] = int(i[0]) + 1
            count += 1
        return ( prob , runClean , int( APCost @ runs.value ) )
    else: 
        return ( prob , runs.value , prob.value )

# Maybe this should all be in a 'main' method? No clue about the etiquette there for more 'professional' programs.
pathPrefix = standardizePath()

config = configparser.ConfigParser()
config.read( pathPrefix + 'config\\farmgo_config.ini' )

debug = Debug( pathPrefix )

eventUse = debug.config('Use Event')
eventFind = debug.config('Event Name')
lastArea = debug.config('Last Area')
multEvent = debug.config('Multiple Event')
eventCap = debug.config('Event Cap' ,'int')
removeZeros = debug.config('Remove Zeros')
dropWeight = debug.config('Drop Weight', 'float')

if lastArea == '': 
    lastArea = 'ZZZZZ'

nodes = Nodes( pathPrefix + 'Files\\GOALS.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] , removeZeros  )
if multEvent == 'y':
    nodes.multiEvent( glob.glob( pathPrefix + 'Files\\Events\\Multi Event Folder\\*' ) )
else:
    nodes.addEventDrop( glob.glob( pathPrefix + 'Files\\*' + eventFind + '* - Event Quest.csv' )[0] )
nodes.addFreeDrop( glob.glob( pathPrefix + 'Files\\* - APD.csv' )[0] , lastArea )

prob , runs , totalAP = planner( nodes , debug )

print( 'These results are: ' + prob.status)
print( 'The total AP required is: ' + "{:,}".format(totalAP) )
print( 'You should run:')

count = 0
for i in runs:
    if i > 0:
        print( nodes.nodeNames[count] + ': ' + "{:,}".format(int(i)) + ' times')
    count += 1