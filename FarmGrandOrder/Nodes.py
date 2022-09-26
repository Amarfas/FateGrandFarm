import numpy as np
import csv

class Nodes:
    def __init__( self , goals , materialListCSV ):
        self.goals = []
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

        self.matDict = {}
        with open( materialListCSV , newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            matList = next( reader )
            matList = next( reader )
            matList = next( reader )
        count = -1
        for i in matList:
            self.matDict[i] = count
            count += 1

        self.matCount = list( self.matDict.items() )[-1][1] +1
        self.nodeName = []
        self.APCost = []
        self.dropMatrix = np.array([])
    
    def checkMatNames( self , goals ):
        with open( goals , newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            count = -2
            for i in reader:
                count += 1
                try: a = int(i[1])
                except: continue

                try: a = self.matDict[i[0]]
                except: print( i[0] )
    
    def eventDropLoop( self , eventDrop , materialLoc , qpPivot ):
        dropMatrixAdd = np.zeros( self.matCount )
        for i in materialLoc:
            if eventDrop[i+1] != '':
                if i < qpPivot:
                    dropMatrixAdd[ self.matDict[eventDrop[i]] ] = float(eventDrop[i+1])
                else:
                    dropMatrixAdd[ self.matDict[eventDrop[i]] ] = round( int(eventDrop[1]) / float(eventDrop[i+1]) , 6 )
        return dropMatrixAdd
    
    def freeDropLoop( self, freeDrop ):
        dropMatrixAdd = []
        for i in freeDrop[4:(self.matCount+4)]:
            try:
                dropMatrixAdd.append( round( int(freeDrop[2]) / float(i) , 6 ) )
            except:
                dropMatrixAdd.append(0)
        return dropMatrixAdd
    
    def addEventDrop( self , eventDropCSV , eventName = 'Event' ):
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
            eventDrop = next( reader )
            while True:
                if eventDrop[5] == '': continue
                if eventDrop[1] == '':
                    for i in materialLoc:
                        if eventDrop[i+1] != '':
                            eventDropMatrix[-1][ self.matDict[eventDrop[i]] ] = float(eventDrop[i+1])
                else:
                    self.nodeName.append( eventName + ', ' + eventDrop[0] )
                    eventAPCost.append( int(eventDrop[1]) )
                    eventDropMatrix.append( self.eventDropLoop( eventDrop , materialLoc , qpPivot ) )
                
                try: eventDrop = next( reader )
                except: break
            
            if np.size( self.dropMatrix ) == 0:
                self.APCost = np.array( eventAPCost )
                self.dropMatrix = np.array( eventDropMatrix )
            else:
                self.APCost = np.append( self.APCost , eventAPCost )
                self.dropMatrix = np.vstack( (self.dropMatrix , eventDropMatrix) )
    
    def addFreeDrop( self , freeDropCSV ):
        with open( freeDropCSV , newline = '' , encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            freeDrop = next( reader )

            freeAPCost = []
            freeDropMatrix = []
            while True:
                try: freeDrop = next( reader )
                except: break
                if freeDrop[2] == '' or freeDrop[2] == 'AP': continue

                self.nodeName.append( freeDrop[0] + ', ' + freeDrop[1] )
                freeAPCost.append( int(freeDrop[2]) )
                freeDropMatrix.append( self.freeDropLoop( freeDrop ) )
            
            if np.size( self.dropMatrix ) == 0:
                self.APCost = np.array( freeAPCost )
                self.dropMatrix = np.array( freeDropMatrix )
            else:
                self.APCost = np.append( self.APCost , freeAPCost )
                self.dropMatrix = np.vstack( (self.dropMatrix , freeDropMatrix) )
    
    def getGoals( self ):
        return self.goals
    
    def getMatCount( self ):
        return self.matCount

    def getNodeName( self ):
        return self.nodeName
    
    def getAPCost( self ):
        return self.APCost
    
    def getDropMatrix( self ):
        return self.dropMatrix