import numpy as np
import cvxpy as cp
import csv
import glob
import timeit
import FarmGrandOrder

class Nodes2:
    def __init__( self , goals , materialListCSV ):
        self.goals = []
        self.skipCol = []
        with open( goals , newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            goalLine = next( reader )
            count = 0
            while True:
                try: goalLine = next(reader)
                except: break
                try: 
                    i = int(goalLine[1])
                    if i == 0: self.skipCol.append(count)
                    else: self.goals.append(i)
                except: self.skipCol.append(count)
                count += 1
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
                self.dropMatrix = np.vstack( self.dropMatrix , eventDropMatrix )
    
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

def checkMatrix( a , b , s = 'F' , sa = 'F' ):
    count = -1
    for i in a:
        count += 1
        if s == 'F': n = np.size(b[count])
        else: n = len(b[count])
        try:
            count2 = 0
            if sa == 'F': m = np.size(b[count])
            else: m = len(i)
            if m != n:
                return 'F'
            for j in i:
                if j != b[count][count2]:
                    return 'F'
                count2 += 1
        except:
            if n != 1:
                return 'F'
            if i != b[count]:
                return 'F'
    return 'T'

def comparison( testNum ):
    eventInput = 'Eff'
    pathPrefix = FarmGrandOrder.standardizePath()

    if testNum <= 2:
        nodes = FarmGrandOrder.Nodes( pathPrefix + 'GOALS.csv', glob.glob( pathPrefix + '* - Calc.csv' )[0] )
        nodes.addEventDrop( glob.glob( pathPrefix + '*' + eventInput + '* - Event Quest.csv' )[0] )
        nodes.addFreeDrop( glob.glob( pathPrefix + '* - APD.csv' )[0] )

        nodes2 = Nodes2( pathPrefix + 'GOALS.csv', glob.glob( pathPrefix + '* - Calc.csv' )[0] )
        nodes2.addEventDrop( glob.glob( pathPrefix + '*' + eventInput + '* - Event Quest.csv' )[0] )
        nodes2.addFreeDrop( glob.glob( pathPrefix + '* - APD.csv' )[0] )

        if testNum == 1:
            print( checkMatrix( nodes.getNodeName() , nodes2.getNodeName() , 'T' , 'T' ))
            print( checkMatrix( nodes.getAPCost() , nodes2.getAPCost() ))
            print( checkMatrix( nodes.getDropMatrix() , nodes2.getDropMatrix() ))
        
        if testNum == 2:
            runSize = np.size( nodes.getAPCost() )
            runs = cp.Variable( (runSize,1) , nonneg=True )
            objective = cp.Minimize( nodes.getAPCost() @ runs )
            constraints = [ np.transpose( nodes.getDropMatrix() ) @ runs >= nodes.getGoals() ]
            prob = cp.Problem( objective , constraints )
            prob.solve()

            runSize2 = np.size( nodes2.getAPCost() )
            runs2 = cp.Variable( (runSize2,1) , nonneg=True )
            objective2 = cp.Minimize( nodes2.getAPCost() @ runs2 )
            constraints2 = [ np.transpose( nodes2.getDropMatrix() ) @ runs2 >= nodes2.getGoals() ]
            prob2 = cp.Problem( objective2 , constraints2 )
            prob2.solve()

            if prob.value == prob2.value: print('T')
            else: print('F')
            print( checkMatrix( runs.value , runs2.value ) )
    
    else:
        a = 1

comparison( 2 )