import configparser
import csv
import glob
import numpy as np
import cvxpy as cp
import time
import FarmGrandOrder as FGO
from NodesTest import Nodes

# Mode 1: Check if Node Names, AP Costs, and Drop Matrices are equal.
# Mode 2: Check if Planner outputs are similar or the same.
# Mode 3: Compare run times, with below 'rep' count.

testModes = [ 1, 2 ]
tolerance = 0.01
rep = 100
goalstest = 'test2'

def CheckMatrix( a , b , s = 'F' , sa = 'F' ):
    # 's = F' means 'b' is an array
    # 'sa = F' means 'a' is an array
    row = -1
    for i in a:
        row += 1
        if s == 'F': 
            n = np.size(b[row])
        else: 
            n = len(b[row])
        try:
            col = 0
            if sa == 'F': 
                m = np.size(i)
            else: 
                m = len(i)

            if m != n:
                return 'F : ('+str(row)+','+str(col)+') : m != n : '+str(m)+' != '+str(n)
            for j in i:
                if m > 1:
                    if j != b[row][col]:
                        if col < 54 and abs(int(j) - int(b[row][col])) > tolerance:
                            return 'F: ('+str(row)+','+str(col)+') '+nodes.nodeNames[row]+': '+str(j)+' != '+str(b[row][col])
                        else:
                            print( 'F: ('+str(row)+','+str(col)+') '+nodes.nodeNames[row]+': '+str(j)+' != '+str(b[row][col]) )
                else:
                    if j != b[row][col]:
                        print( 'F: ('+str(row)+','+str(col)+') '+nodes.nodeNames[row]+': '+str(j)+' != '+str(b[row][col]) )
                col += 1

        except:
            if n != 1:
                return 'F: ('+str(row)+',~): n != 1'
            if i != b[row]:
                return 'F: ('+str(row)+',~): '+str(i)+' != '+str(b[row])
    return 'T'

def BuildMatrix( nodes, multEvent, pathPrefix, eventFind, lastArea ):
    if multEvent == 'y':
        nodes.multiEvent( glob.glob( pathPrefix + 'Files\\Events\\Multi Event Folder\\*' ) )
    else:
        nodes.addEventDrop( glob.glob( pathPrefix + 'Files\\*' + eventFind + '* - Event Quest.csv' )[0] )
    nodes.addFreeDrop( glob.glob( pathPrefix + 'Files\\* - APD.csv' )[0] , lastArea )



print('\n')
pathPrefix = FGO.standardizePath()

config = configparser.ConfigParser()
config.read( pathPrefix + 'config\\farmgo_config.ini' )

debug = FGO.Debug( pathPrefix )

eventUse = debug.config('Use Event')
eventFind = debug.config('Event Name')
lastArea = debug.config('Last Area')
multEvent = debug.config('Multiple Event')
eventCap = debug.config('Event Cap' ,'int')
removeZeros = debug.config('Remove Zeros')
dropWeight = debug.config('Drop Weight', 'float')

if lastArea == '': 
    lastArea = 'ZZZZZ'

nodes = FGO.Nodes( pathPrefix + 'Files\\GOALS' + goalstest + '.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] , removeZeros )
BuildMatrix( nodes, multEvent, pathPrefix, eventFind, lastArea )

nodes2 = Nodes( pathPrefix + 'Files\\GOALS' + goalstest + '.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] , removeZeros )
BuildMatrix( nodes2, multEvent, pathPrefix, eventFind, lastArea )

for i in testModes:
    if i == 1:
        print( 'Nodes Names equal: ' + CheckMatrix( nodes.nodeNames , nodes2.nodeNames , 'T' , 'T' ))
        print( 'AP Cost equal: ' + CheckMatrix( nodes.APCost , nodes2.APCost ))
        print( 'Drop Matrix equal: ' + CheckMatrix( nodes.dropMatrix , nodes2.dropMatrix ))
    
    if i == 2:
        prob , runs , totalAP = FGO.planner( nodes , debug )
        prob2 , runs2 , totalAP2 = FGO.planner( nodes2 , debug )

        print( 'Run counts equal: ' + CheckMatrix( runs , runs2 ) )
        if totalAP == totalAP2: 
            print('Total AP equal: T')
        else: 
            print('Total AP equal: F: '+str(totalAP)+' != '+str(totalAP2))
    
    if i == 3:
        t1 = time.time()
        for i in range(rep):
            nodes = FGO.Nodes( pathPrefix + 'Files\\GOALS.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] )
            BuildMatrix( nodes, multEvent, pathPrefix, eventFind, lastArea )
            prob , runs , totalAP = FGO.planner( nodes , debug )
        t1 = ( time.time() - t1 ) / rep
        print( 'Time1 per iter: ' + str(t1) )

        t2 = time.time()
        for i in range(rep):
            nodes2 = Nodes( pathPrefix + 'Files\\GOALS.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] )
            BuildMatrix( nodes2, multEvent, pathPrefix, eventFind, lastArea )
            prob2 , runs2 , totalAP2 = FGO.planner( nodes2 , debug )
        t2 = ( time.time() - t2 ) / rep
        print( 'Time2 per iter: ' + str(t2) )

        print( 'Difference: ' + str(t2-t1) )