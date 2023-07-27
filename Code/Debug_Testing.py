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

test_modes = [ 1 , 2 ]
tolerance = 0.01
tolerance2 = 0
rep = 100
goals_debug = ''

def check_matrix( a, b ,s = 'F' ,sa = 'F', matrix = False ):
    # 's = F' means 'b' is an array
    # 'sa = F' means 'a' is an array

    flag = False
    row = -1
    for i in a:
        row += 1
        if isinstance(i,str) and isinstance(b[row],str):
            if i != b[row]:
                if matrix == 'node_names':
                    print( 'F6: ('+str(row)+',~): '+str(i)+' != '+str(b[row]) )
                    #row += 1
                    flag = True
                else:
                    return 'F6: ('+str(row)+',~): '+str(i)+' != '+str(b[row])
        else:
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
                            #row += 1
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
    run_caps = Inter.RunCaps(debug)

    if ver == 'Nodes':
        nodes = Nodes(remove_zeros)
        nodes.multi_event( path_prefix, run_caps, debug, input_data.mat_count, input_data.ID_to_index )
        nodes.add_free_drop( glob.glob( path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, last_area, debug, input_data.skip_data_index )

    if ver == 'NodesTest':
        nodes = NodesTest(remove_zeros)
        nodes.multi_event( path_prefix, run_caps, debug, input_data.mat_count, input_data.ID_to_index )
        nodes.add_free_drop( glob.glob( path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, last_area, debug, input_data.skip_data_index )

    return nodes, run_caps, run_caps.build_run_cap_matrix()

print('\n')
path_prefix = Inter.standardize_path()

debug = Inter.Debug( path_prefix )
tg_half_AP = debug.note_config('Training Grounds Half AP', 'bool')
remove_zeros = debug.note_config('Remove Zeros', 'bool')
run_int = debug.note_config('Run Count Integer', 'bool')
last_area = debug.note_config('Last Area')

input_data = Inter.InputData( path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( path_prefix + 'Data Files\\*Calc.csv' )[0], debug, remove_zeros )

nodes, run_caps, run_cap_matrix = build_matrix('Nodes')
nodes_test, run_caps_test, run_cap_matrix_test = build_matrix('NodesTest')

for i in test_modes:
    if i == 1:
        print( 'Nodes Names equal: ' + check_matrix( nodes.node_names, nodes_test.node_names, 'T', 'T', matrix = 'node_names' ))
        print( 'AP Cost equal: ' + check_matrix( nodes.AP_costs, nodes_test.AP_costs ))
        print( 'Drop Matrix equal: ' + check_matrix( nodes.drop_matrix, nodes_test.drop_matrix ))
        #print( 'Cap Info Matrix equal: ' + check_matrix( run_caps.node_info, nodes_test.node_info ))
    
    if i == 2:
        print('\n')
        prob , runs , total_AP = planner( nodes, debug, input_data )
        prob2 , runs2 , total_AP2 = planner( nodes_test, debug, input_data )

        print( 'Run counts equal: ' + check_matrix( runs, runs2 ) )
        if total_AP == total_AP2: 
            print('Total AP equal: T')
        else: 
            print('Total AP equal: F: '+str(total_AP)+' != '+str(total_AP2))
    
    if i == 3:
        for goals_debug in [ '', 'Test', 'Test1', 'Test2']:
            print( '\nFor GOALS' + goals_debug + '.csv:')

            t1 = time.time()
            for j in range(rep):
                nodes, run_caps, run_cap_matrix = build_matrix('Nodes')
                prob , runs , total_AP = planner( nodes, debug, input_data, run_cap_matrix )
            t1 = ( time.time() - t1 ) / rep
            print( '   Time1 per iter: ' + str(t1) )

            t2 = time.time()
            for j in range(rep):
                nodes, run_caps, run_cap_matrix = build_matrix('NodesTest')
                prob2 , runs2 , total_AP2 = planner( nodes, debug, input_data, run_cap_matrix )
            t2 = ( time.time() - t2 ) / rep
            print( '   Time2 per iter: ' + str(t2) )

            print( ' Difference x1,000: ' + str(1000*(t2-t1)) )
    
    if i == 4:
        run_cap_matrix1 = run_caps.build_run_cap_matrix()
        run_cap_matrix2 = run_caps.build_run_cap_matrix_test()
        print( 'Run Matrix equal: ' + check_matrix( run_cap_matrix1[0], run_cap_matrix2[0] ))
        print( 'Run Cap equal: ' + check_matrix( run_cap_matrix1[1], run_cap_matrix2[1] ))
    
    if i == 5:
        #print( 'Cap Info Matrix equal: ' + check_matrix( run_caps.node_info, nodes_test.node_info ))
        print( 'Run Info equal: ' + check_matrix( run_caps.run_info, run_caps_test.run_info ))