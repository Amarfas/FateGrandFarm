import configparser
import csv
import glob
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
from Nodes import Nodes
from NodesTest import Nodes as NodesTest
from Planner import planner

# Mode 1: Check if Node Names, AP Costs, and Drop Matrices are equal.
# Mode 2: Check if Planner outputs are similar or the same.
# Mode 3: Compare run times, with below 'rep' count.
# 'tolerance' defines the minimum difference that will break the matrix comparison
# 'tolerance2' defines the maximum difference that'll be ignored in matrix comparisons

test_modes = [ 1, 2, 3 ]
tolerance = 0.01
tolerance2 = 0
rep = 100
goals_debug = 'Test'

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
                        k = b[row][col]
                        dif = abs(float(j) - float(k))
                        if col < 54 and dif > tolerance:
                            return 'F2: ('+str(row)+','+str(col)+') '+nodes.node_names[row]+': '+str(j)+' != '+str(k)
                        else:
                            if dif > tolerance2:
                                print( 'F3: ('+str(row)+','+str(col)+') '+nodes.node_names[row]+': '+str(j)+' != '+str(k) )
                                flag = True
                        return 'F2: ('+str(row)+','+str(col)+') '+nodes.node_names[row]+': '+str(j)+' != '+str(k)

                else:
                    if j != b[row][col]:
                        print( 'F4: ('+str(row)+','+str(col)+') '+nodes.node_names[row]+': '+str(j)+' != '+str(b[row][col]) )
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
    if ver == 'Nodes':
        nodes = Nodes()
        nodes.multi_event( path_prefix + 'Files\\', run_caps, debug, event_find, input_data.mat_count, input_data.ID_to_index, multi_event )
        nodes.add_free_drop( glob.glob( path_prefix + 'Files\\* - APD.csv' )[0], run_caps, last_area, debug, input_data.skip_data_index )
    if ver == 'NodesTest':
        nodes = NodesTest()
        nodes.multi_event( path_prefix + 'Files\\', run_caps, debug, event_find, input_data.mat_count, input_data.ID_to_index, multi_event )
        nodes.add_free_drop( glob.glob( path_prefix + 'Files\\* - APD.csv' )[0], run_caps, last_area, debug, input_data.skip_data_index )
    return nodes

print('\n')
path_prefix = Inter.standardize_path()

debug = Inter.Debug( path_prefix )

event_use = debug.note_config('Use Event', 'bool')
event_find = debug.note_config('Event Name')
last_area = debug.note_config('Last Area')
multi_event = debug.note_config('Multiple Event', 'bool')
run_caps_old = [ [debug.note_config('Event Cap' ,'int')], [debug.note_config('Raid Cap' ,'int')], [debug.note_config('Bleach Cap' ,'int')] ]
remove_zeros = debug.note_config('Remove Zeros', 'bool')
drop_weight = debug.note_config('Drop Weight', 'float')

run_caps = Inter.RunCaps(debug)
input_data = Inter.InputData( path_prefix + 'Files\\GOALS' + goals_debug + '.csv', glob.glob( path_prefix + 'Files\\* - Calc.csv' )[0], debug, remove_zeros )

nodes = build_matrix('Nodes')
nodes_test = build_matrix('NodesTest')

for i in test_modes:
    if i == 1:
        print( 'Nodes Names equal: ' + check_matrix( nodes.node_names, nodes_test.node_names, 'T', 'T' ))
        print( 'AP Cost equal: ' + check_matrix( nodes.AP_costs, nodes_test.AP_costs ))
        print( 'Drop Matrix equal: ' + check_matrix( nodes.drop_matrix, nodes_test.drop_matrix ))
        print( 'Cap Info Matrix equal: ' + check_matrix( run_caps.node_info, nodes_test.node_info ))
    
    if i == 2:
        prob , runs , total_AP = planner( nodes, debug, input_data )
        prob2 , runs2 , total_AP2 = planner( nodes_test, debug, input_data )

        print( '\nRun counts equal: ' + check_matrix( runs, runs2 ) )
        if total_AP == total_AP2: 
            print('\nTotal AP equal: T')
        else: 
            print('\nTotal AP equal: F: '+str(total_AP)+' != '+str(total_AP2))
    
    if i == 3:
        for goals_debug in [ '', 'Test', 'Test1', 'Test2']:
            print( '\nFor GOALS' + goals_debug + '.csv:')

            t1 = time.time()
            for j in range(rep):
                run_caps = Inter.RunCaps(debug)
                nodes = build_matrix('Nodes')
                prob , runs , total_AP = planner( nodes, debug, input_data )
            t1 = ( time.time() - t1 ) / rep
            print( '   Time1 per iter: ' + str(t1) )

            t2 = time.time()
            for j in range(rep):
                run_caps = Inter.RunCaps(debug)
                nodes_test = build_matrix('NodesTest')
                prob2 , runs2 , total_AP2 = planner( nodes_test, debug, input_data )
            t2 = ( time.time() - t2 ) / rep
            print( '   Time2 per iter: ' + str(t2) )

            print( ' Difference x1,000: ' + str(1000*(t2-t1)) )