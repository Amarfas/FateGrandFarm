import configparser
import csv
import glob
import numpy as np
import cvxpy as cp
import time
import FarmGrandOrder as FGO
from NodesTest import Nodes

testMode = [ 1, 2 ]
tolerance = 0.01
rep = 100

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
                            return 'F: ('+str(row)+','+str(col)+'): '+str(j)+' != '+str(b[row][col]) 
                        else:
                            print( 'F: ('+str(row)+','+str(col)+'): '+str(j)+' != '+str(b[row][col]) )
                else:
                    if j != b[row][col]:
                        print( 'F: ('+str(row)+','+str(col)+'): '+str(j)+' != '+str(b[row][col]) )
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


def Comparison( testModes ):
    print('\n')
    endNotes = ''
    pathPrefix = FGO.standardizePath()

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

    nodes = FGO.Nodes( pathPrefix + 'Files\\GOALS.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] )
    BuildMatrix( nodes, multEvent, pathPrefix, eventFind, lastArea )

    nodes2 = Nodes( pathPrefix + 'Files\\GOALS.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] )
    BuildMatrix( nodes2, multEvent, pathPrefix, eventFind, lastArea )

    for i in testModes:
        if i == 1:
            print( 'Nodes Names equal: ' + CheckMatrix( nodes.nodeNames , nodes2.nodeNames , 'T' , 'T' ))
            print( 'AP Cost equal: ' + CheckMatrix( nodes.APCost , nodes2.APCost ))
            print( 'Drop Matrix equal: ' + CheckMatrix( nodes.dropMatrix , nodes2.dropMatrix ))
        
        if i == 2:
            prob , runs , totalAP = FGO.planner( nodes )
            prob2 , runs2 , totalAP2 = FGO.planner( nodes2 )

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
                prob , runs , totalAP = FGO.planner( nodes )
            t1 = ( time.time() - t1 ) / rep
            print( 'Time1 per iter: ' + str(t1) )

            t2 = time.time()
            for i in range(rep):
                nodes2 = Nodes( pathPrefix + 'Files\\GOALS.csv' , glob.glob( pathPrefix + 'Files\\* - Calc.csv' )[0] )
                BuildMatrix( nodes2, multEvent, pathPrefix, eventFind, lastArea )
                prob2 , runs2 , totalAP2 = FGO.planner( nodes2 )
            t2 = ( time.time() - t2 ) / rep
            print( 'Time2 per iter: ' + str(t2) )

            print( 'Difference: ' + str(t2-t1) )

Comparison( testMode )