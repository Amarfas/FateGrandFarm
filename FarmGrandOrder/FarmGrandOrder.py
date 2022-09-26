import configparser
import csv
import glob
import numpy as np
import cvxpy as cp

class Nodes:
    def __init__( self , goals , materialListCSV ):
        self.goals = []
        self.setGoals( goals )

        self.matIndex = {}
        self.matDict = {}
        for i in materialListCSV:
            self.addMatDict(i)

        self.matCount = list( self.matIndex.items() )[-1][1] +1
        self.nodeName = []
        self.APCost = []
        self.dropMatrix = np.array([])
        self.runCap = []

    def checkMatNames( self , goals ):
        with open( goals , newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            count = -2
            for i in reader:
                count += 1
                try: a = int(i[1])
                except: continue

                try: a = self.matIndex[i[0]]
                except: print( i[0] )
    
    def addMatDict( self , materialListCSV ):
        with open( materialListCSV , newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            matList = next( reader )
            matList = next( reader )
            matList = next( reader )
        count = -1
        for i in matList:
            self.matIndex.setdefault( i , count )
            self.matDict.setdefault( count , i )
            count += 1
    
    def setGoals( self , goals ):
        with open( goals , newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            goalLine = next( reader )
            while True:
                goalLine = next(reader)
                if goalLine[0] == 'Berserker Hellfire':
                    self.goals.append( [int(goalLine[1])] )
                    break
                try: self.goals.append( [int(goalLine[1])] )
                except: self.goals.append( [0] )
        self.goals = np.array( self.goals )

    def addMatrices( self , addAPCost , addRunCap , addDropMatrix ):
            if np.size( self.dropMatrix ) == 0:
                self.APCost = np.array( addAPCost )
                self.runCap = np.array( addRunCap )
                self.dropMatrix = np.array( addDropMatrix )
            else:
                self.APCost = np.append( self.APCost , addAPCost )
                self.runCap = np.append( self.runCap , addRunCap )
                self.dropMatrix = np.vstack( ( self.dropMatrix , addDropMatrix ) )
    
    def addEventDrop( self , eventDropCSV ):
        start = eventDropCSV.rindex('Efficiency_ ')
        eventName = eventDropCSV[(start+12):eventDropCSV.rindex(' - Event',start)]

        with open( eventDropCSV , newline = '' , encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            eventDrop = next( reader )
        
            count = 0
            materialLoc = []
            qpPivot = 0
            for i in eventDrop:
                if i == 'Material': materialLoc.append( count )
                if i == 'QP': qpPivot = count
                count += 1
            
            eventAPCost = []
            eventDropMatrix = []
            eventRunCap = []
            eventDrop = next( reader )
            while True:
                if eventDrop[5] == '': continue
                if eventDrop[1] == '':
                    for i in materialLoc:
                        if eventDrop[i+1] != '':
                            eventDropMatrix[-1][ self.matIndex[eventDrop[i]] ] = dropWeight * float(eventDrop[i+1])
                else:
                    self.nodeName.append( eventName + ', ' + eventDrop[0] )
                    eventAPCost.append( float(eventDrop[1]) )
                    eventRunCap.append( eventCap )
                    eventDropMatrix.append( np.zeros( self.matCount ) )
                    for i in materialLoc:
                        if eventDrop[i+1] != '':
                            if i < qpPivot:
                                eventDropMatrix[-1][ self.matIndex[eventDrop[i]] ] = dropWeight * float(eventDrop[i+1])
                            else:
                                eventDropMatrix[-1][ self.matIndex[eventDrop[i]] ] = round( float(eventDrop[1]) / float(eventDrop[i+1]) , 6 )
                
                try: eventDrop = next( reader )
                except: break
            
            self.addMatrices( eventAPCost , eventRunCap , eventDropMatrix )
    
    def addFreeDrop( self , freeDropCSV , lastArea ):
        with open( freeDropCSV , newline = '' , encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            freeDrop = next( reader )

            freeAPCost = []
            freeRunCap = []
            freeDropMatrix = []
            while True:
                try: freeDrop = next( reader )
                except: break
                if freeDrop[0].find( lastArea ) >= 0: break
                if freeDrop[2] == '' or freeDrop[2] == 'AP': continue

                self.nodeName.append( freeDrop[0] + ', ' + freeDrop[1] )
                freeAPCost.append( int(freeDrop[2]) )
                freeRunCap.append( 100000 )
                dropMatrixAdd = []
                for i in freeDrop[4:(self.matCount+4)]:
                    try: dropMatrixAdd.append( round( int(freeDrop[2]) / float(i) , 6 ) )
                    except: dropMatrixAdd.append(0)
                freeDropMatrix.append( dropMatrixAdd )
            
            self.addMatrices( freeAPCost , freeRunCap , freeDropMatrix )
    
    def multiEvent( self , multiEventFolder ):
        for i in multiEventFolder:
            self.addEventDrop(i)
        return 'Multi'

def standardizePath():
    pathDir = ''
    if glob.glob('FarmGrandOrder') == []:
        return '..\\' + pathDir
    else: return pathDir

def makeNote( note ):
    global endNotes
    endNotes += note + '\n'
    print(note)

def planner( dropMatrix , goals , type = 'nonneg' ):
    runSize = np.size( nodes.APCost )
    if type == 'nonneg': runs = cp.Variable( (runSize,1) , nonneg=True)
    else: runs = cp.Variable( (runSize,1) , integer=True )

    for i in range(nodes.matCount):
        for j in dropMatrix[i]:
            if j > 0: break
        else:
            if nodes.matDict[i] != '':
                makeNote( 'Obtaining any ' + nodes.matDict[i] + ' is impossible with these restrictions.' )
                goals[i] = 0

    objective = cp.Minimize( nodes.APCost @ runs )
    constraints = [ dropMatrix @ runs >= goals ]
    prob = cp.Problem( objective , constraints )
    prob.solve()

    if type == 'nonneg':
        runClean = np.zeros( (runSize,1) , dtype = int)
        count = 0
        for i in runs.value:
            if i[0] < 0.1: runClean[count,0] = 0
            else: runClean[count,0] = int(i[0]) + 1
            count += 1
        return ( prob , runClean , int( nodes.APCost @ runClean ) )
    else: 
        return ( prob , runs.value , prob.value )

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

if lastArea == '': lastArea = 'ZZZZZ'

nodes = Nodes( pathPrefix + 'Files\\GOALS.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' ) )
if multEvent == 'y':
    nodes.multiEvent( glob.glob( pathPrefix + 'Files\\Events\\Multi Event Folder\\*' ) )
else:
    nodes.addEventDrop( glob.glob( pathPrefix + 'Files\\*' + eventFind + '* - Event Quest.csv' )[0] )
nodes.addFreeDrop( glob.glob( pathPrefix + 'Files\\* - APD.csv' )[0] , lastArea )

prob , runs , totalAP = planner( np.transpose( nodes.dropMatrix ) , nodes.goals )

print( 'These results are: ' + prob.status)
print( 'The total AP required is: ' + "{:,}".format(totalAP) )
print( 'You should run:')

count = 0
for i in runs:
    if i > 0:
        print( nodes.nodeName[count] + ': ' + "{:,}".format(int(i)) + ' times')
    count += 1