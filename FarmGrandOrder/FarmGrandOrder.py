import configparser
import csv
import glob
import numpy as np
import cvxpy as cp

class Nodes:
    def __init__( self , goals , materialListCSV , eventCap = '' ):
        self.goals = []
        self.interpretGoals(goals)

        self.dictIDtoIndex = {}
        self.dictIndexToName = {}
        self.createMatDicts(materialListCSV)

        self.matCount = list( self.dictIDtoIndex.items() )[-7][1] + 1
        self.nodeNames = []
        self.APCost = []
        self.runCap = []
        self.dropMatrix = np.array([])
        self.eventCap = eventCap

    # Debugging function that checks to see if the material names are in the right spot/spelled correctly.
    # Should probably be deleted for final code.
    def checkMatNames( self, goals ):
        with open( goals, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            count = -2
            for i in reader:
                count += 1
                try: 
                    a = int(i[1])
                except: 
                    continue

                try: 
                    a = self.dictIDtoIndex[i[0]]
                except: 
                    print(i[0])
    
    # TODO: Change code so that undesired materials (Goal Quantity = 0) are skipped entirely.
    # Also store the skipped materials so the rest of the functions and correctly assemble the matrices.
    def interpretGoals( self, goals ):
        with open( goals, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            readLine = next(reader)

            for row in reader:
                try:
                    self.goals.append( [int(row[2])] )
                except:
                    self.goals.append( [0] )
            f.close()

        self.goals = np.array(self.goals)
    
    # Creates two dictionaries, one mapping a mat's ID to placement in Drop Matrix, and the other mapping placement in Matrix to its Name.
    def createMatDicts( self, materialListCSV ):
        with open( materialListCSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            matID = next(reader)
            matID = next(reader)
            matID = next(reader)
            matName = next(reader)
            f.close()
        
        # Special case for ID's less than 0, which are used to refer multiple materials (Ex. all 7 Blue, Red, or Gold Gems)
        for i in range(1,len(matID)):
            if int(matID[i]) < 0:
                self.dictIDtoIndex.setdefault( matID[i], int(matID[i]) )
            else:
                self.dictIDtoIndex.setdefault( matID[i], i-1 )
            self.dictIndexToName.setdefault( i-1, matName[i] )

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
    
    def addEventDrop( self, eventDropCSV ):
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
                if eventNode[5] == '': 
                    continue

                if eventNode[1] != '':
                    self.nodeNames.append( eventName + ', ' + eventNode[0] )
                    eventAPCost.append( [float(eventNode[1])] )
                    eventRunCap.append( [self.eventCap] )
                    eventDropMatrix.append( np.zeros( self.matCount ) )

                for i in materialLoc:
                    if eventNode[i+2] != '':
                        if int(eventNode[i]) > 0:
                            eventDropMatrix[-1][ self.dictIDtoIndex[eventNode[i]] ] = float(eventNode[i+2]) / 100
            f.close()
            
            self.assembleMatrix( eventAPCost, eventRunCap, eventDropMatrix )
    
    def addFreeDrop( self, freeDropCSV, lastArea ):
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

                self.nodeNames.append( freeDrop[0] + ', ' + freeDrop[1] )
                freeAPCost.append( [int(freeDrop[2])] )
                freeRunCap.append( [100000] )
                dropMatrixAdd = []

                for i in freeDrop[4:(self.matCount+4)]:
                    try: 
                        dropMatrixAdd.append( round( int(freeDrop[2]) / float(i) , 6 ) )
                    except: 
                        dropMatrixAdd.append(0)
                freeDropMatrix.append( dropMatrixAdd )
            f.close()
            
            self.assembleMatrix( freeAPCost, freeRunCap, freeDropMatrix )
    
    def multiEvent( self, multiEventFolder ):
        for i in multiEventFolder:
            self.addEventDrop(i)
        return 'Multi'

# Makes it so the program works whether it's started in the 'FarmingGrandOrder' overarching directory or the 'FarmGrandOrder' folder.
# May be unnecessary, but trying to get python file pathing to work is more annoying than I remember.
def standardizePath():
    pathDir = ''
    if glob.glob('FarmGrandOrder') == []:
        return '..\\' + pathDir
    else: return pathDir

# TODO: Decide if this even needs to be a global variable or just a class.
def makeNote( note ):
    global endNotes
    endNotes += note + '\n'
    print(note)

def planner( nodes , type = 'nonneg' ):
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
                makeNote( 'Obtaining any ' + nodes.dictIndexToName[i] + ' is impossible with these restrictions.' )
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
        return ( prob , runClean , int( APCost @ runClean ) )
    else: 
        return ( prob , runs.value , prob.value )

# Maybe this should all be in a 'main' method? No clue about the etiquette there for more 'professional' programs.

endNotes = ''
pathPrefix = standardizePath()

config = configparser.ConfigParser()
config.read( pathPrefix + 'config\\farmgo_config.ini' )

eventUse = config['DEFAULT']['Use Event']
eventFind = config['DEFAULT']['Event Name']
lastArea = config['DEFAULT']['Last Area']
multEvent = config['DEFAULT']['Multiple Event']
eventCap = int( config['DEFAULT']['Event Cap'] )
dropWeight = float(config['DEFAULT']['Drop Weight'])

if lastArea == '': 
    lastArea = 'ZZZZZ'

nodes = Nodes( pathPrefix + 'Files\\GOALS.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] )
if multEvent == 'y':
    nodes.multiEvent( glob.glob( pathPrefix + 'Files\\Events\\Multi Event Folder\\*' ) )
else:
    nodes.addEventDrop( glob.glob( pathPrefix + 'Files\\*' + eventFind + '* - Event Quest.csv' )[0] )
nodes.addFreeDrop( glob.glob( pathPrefix + 'Files\\* - APD.csv' )[0] , lastArea )

prob , runs , totalAP = planner( nodes )

print( 'These results are: ' + prob.status)
print( 'The total AP required is: ' + "{:,}".format(totalAP) )
print( 'You should run:')

count = 0
for i in runs:
    if i > 0:
        print( nodes.nodeNames[count] + ': ' + "{:,}".format(int(i)) + ' times')
    count += 1