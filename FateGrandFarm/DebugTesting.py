import configparser
import csv
import glob
import numpy as np
import cvxpy as cp
import time
import FateGrandFarm as FGF
from NodesTest import Nodes

# Mode 1: Check if Node Names, AP Costs, and Drop Matrices are equal.
# Mode 2: Check if Planner outputs are similar or the same.
# Mode 3: Compare run times, with below 'rep' count.
# 'tolerance' defines the minimum difference that will break the matrix comparison
# 'tolerance2' defines the maximum difference that'll be ignored in matrix comparisons

test_modes = [ 1, 2 ]
tolerance = 0.01
tolerance2 = 0
rep = 100
goals_test = ''

def check_matrix( a , b , s = 'F' , sa = 'F' ):
    # 's = F' means 'b' is an array
    # 'sa = F' means 'a' is an array

    flag = False
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
                return 'F1 : ('+str(row)+','+str(col)+') : m != n : '+str(m)+' != '+str(n)
            for j in i:
                if m > 1:
                    if j != b[row][col]:
                        dif = abs(float(j) - float(b[row][col]))
                        if col < 54 and dif > tolerance:
                            return 'F2: ('+str(row)+','+str(col)+') '+nodes.nodeNames[row]+': '+str(j)+' != '+str(b[row][col])
                        else:
                            if dif > tolerance2:
                                print( 'F3: ('+str(row)+','+str(col)+') '+nodes.nodeNames[row]+': '+str(j)+' != '+str(b[row][col]) )
                                flag = True

                else:
                    if j != b[row][col]:
                        print( 'F4: ('+str(row)+','+str(col)+') '+nodes.nodeNames[row]+': '+str(j)+' != '+str(b[row][col]) )
                        flag = True
                col += 1

        except:
            if n != 1:
                return 'F5: ('+str(row)+',~): n != 1'
            if i != b[row]:
                return 'F6: ('+str(row)+',~): '+str(i)+' != '+str(b[row])
    if flag:
        return 'F'
    return 'T'

def build_matrix( ver ):
    if ver == 'FarmGrandOrder':
        nodes = FGF.Nodes( path_prefix + 'Files\\GOALS' + goals_test + '.csv', glob.glob( path_prefix + 'Files\\* - Calc.csv' )[0] , run_caps, debug, remove_zeros )
        nodes.multi_event( path_prefix + 'Files\\', debug, event_find, multi_event )
        nodes.add_free_drop( glob.glob( path_prefix + 'Files\\* - APD.csv' )[0], last_area, debug )
    if ver == 'NodesTest':
        nodes = Nodes( path_prefix + 'Files\\GOALS' + goals_test + '.csv', glob.glob( path_prefix + 'Files\\* - Calc.csv' )[0], run_caps, debug, remove_zeros )
        nodes.multi_event( path_prefix + 'Files\\' , debug, event_find, multi_event )
        nodes.add_free_drop( glob.glob( path_prefix + 'Files\\* - APD.csv' )[0], last_area, debug )
    return nodes

print('\n')
path_prefix = FGF.standardize_path()

config = configparser.ConfigParser()
config.read( path_prefix + 'config\\farmgo_config.ini' )

debug = FGF.Debug( path_prefix )

event_use = debug.config('Use Event', 'bool')
event_find = debug.config('Event Name')
last_area = debug.config('Last Area')
multi_event = debug.config('Multiple Event', 'bool')
run_caps = [ [debug.config('Event Cap' ,'int')], [debug.config('Raid Cap' ,'int')], debug.config('Bleach Cap' ,'int') ]
remove_zeros = debug.config('Remove Zeros', 'bool')
drop_weight = debug.config('Drop Weight', 'float')

nodes = build_matrix('FarmGrandOrder')
nodes2 = build_matrix('NodesTest')

for i in test_modes:
    if i == 1:
        print( 'Nodes Names equal: ' + check_matrix( nodes.node_names, nodes2.node_names, 'T', 'T' ))
        print( 'AP Cost equal: ' + check_matrix( nodes.AP_costs, nodes2.AP_costs ))
        print( 'Drop Matrix equal: ' + check_matrix( nodes.drop_matrix, nodes2.drop_matrix ))
    
    if i == 2:
        prob , runs , total_AP = FGF.planner( nodes, debug )
        prob2 , runs2 , total_AP2 = FGF.planner( nodes2, debug )

        print( 'Run counts equal: ' + check_matrix( runs, runs2 ) )
        if total_AP == total_AP2: 
            print('Total AP equal: T')
        else: 
            print('Total AP equal: F: '+str(total_AP)+' != '+str(total_AP2))
    
    if i == 3:
        t1 = time.time()
        for i in range(rep):
            nodes = build_matrix('FarmGrandOrder')
            prob , runs , total_AP = FGF.planner( nodes, debug )
        t1 = ( time.time() - t1 ) / rep
        print( 'Time1 per iter: ' + str(t1) )

        t2 = time.time()
        for i in range(rep):
            nodes2 = build_matrix('NodesTest')
            prob2 , runs2 , total_AP2 = FGF.planner( nodes2, debug )
        t2 = ( time.time() - t2 ) / rep
        print( 'Time2 per iter: ' + str(t2) )

        print( 'Difference: ' + str(t2-t1) )