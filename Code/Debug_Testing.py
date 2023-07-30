import configparser
import csv
import glob
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
from Quest_Data import QuestData
from Quest_Data_Test import QuestData as QT
from Planner import planner

# Mode 1: Check if Node Names, AP Costs, and Drop Matrices are equal.
# Mode 2: Check if Planner outputs are similar or the same.
# Mode 3: Compare run times, with below 'rep' count.
# 'tolerance' defines the minimum difference that will break the matrix comparison
# 'tolerance2' defines the maximum difference that'll be ignored in matrix comparisons

test_modes = [ 1, 2 ]
tolerance = 0.01
tolerance2 = 0
rep = 100
goals_debug = ''
mult_test = 1

def check_matrix( a, b ,is_a_array = False ,is_b_array = False, matrix = False ):
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
            if not is_a_array: 
                n = np.size(b[row])
            else: 
                n = len(b[row])
            try:
                col = 0
                if not is_b_array: 
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
                                return 'F2: ('+str(row)+','+str(col)+') '+nodes.quest_names[row]+': '+str(j)+' != '+str(k)
                            else:
                                if dif > tolerance2:
                                    print( 'F3: ('+str(row)+','+str(col)+') '+nodes.quest_names[row]+': '+str(j)+' != '+str(k) )
                                    flag = True
                            return 'F2: ('+str(row)+','+str(col)+') '+nodes.quest_names[row]+': '+str(j)+' != '+str(k)

                    else:
                        if j != b[row][col]:
                            print( 'F4: ('+str(row)+','+str(col)+') '+nodes.quest_names[row]+': '+str(j)+' != '+str(b[row][col]) )
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
    run_caps = Inter.RunCaps()

    if ver == 'Nodes':
        nodes = QuestData()
        nodes.multi_event( run_caps, input_data.ID_to_index, input_data.drop_index_count )
        nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, input_data.skip_data_index )

    if ver == 'NodesTest':
        nodes = QT()
        nodes.multi_event( run_caps, input_data.drop_index_count, input_data.ID_to_index )
        nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, input_data.skip_data_index )

    return nodes, run_caps, run_caps.build_run_cap_matrix()

print('\n')
Inter.standardize_path()
Inter.ConfigList().read_config_ini()

input_data = Inter.DataFiles( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )

nodes, run_caps, run_cap_matrix = build_matrix('Nodes')
nodes_test, run_caps_test, run_cap_matrix_test = build_matrix('NodesTest')

if mult_test:
    goals_list = [ '', 'Test', 'Test1', 'Test2']
else:
    goals_list = [goals_debug]

for goals_debug in goals_list:
    print( 'Test results for: GOALS' + goals_debug + '.csv:')
    for i in test_modes:
        if i == 1:
            print( 'Nodes Names equal: ' + check_matrix( nodes.quest_names, nodes_test.quest_names, 1, 1, matrix = 'node_names' ))
            print( 'AP Cost equal: ' + check_matrix( nodes.AP_costs, nodes_test.AP_costs ))
            print( 'Drop Matrix equal: ' + check_matrix( nodes.drop_matrix, nodes_test.drop_matrix ))
            #print( 'Cap Info Matrix equal: ' + check_matrix( run_caps.node_info, nodes_test.node_info ))
            print('')
        
        if i == 2:
            prob , runs , total_AP = planner( nodes, input_data )
            prob2 , runs2 , total_AP2 = planner( nodes_test, input_data )

            print( 'Run counts equal: ' + check_matrix( runs, runs2 ) )
            if total_AP == total_AP2: 
                print('Total AP equal: T')
            else: 
                print('Total AP equal: F: '+str(total_AP)+' != '+str(total_AP2))
            print('')
        
        if i == 3:
            t1 = time.time()
            for j in range(rep):
                nodes, run_caps, run_cap_matrix = build_matrix('Nodes')
                prob , runs , total_AP = planner( nodes, input_data, run_cap_matrix )
            t1 = ( time.time() - t1 ) / rep
            print( '   Time1 per iter: ' + str(t1) )

            t2 = time.time()
            for j in range(rep):
                nodes, run_caps, run_cap_matrix = build_matrix('NodesTest')
                prob2 , runs2 , total_AP2 = planner( nodes, input_data, run_cap_matrix )
            t2 = ( time.time() - t2 ) / rep
            print( '   Time2 per iter: ' + str(t2) )

            print( ' Difference x1,000: ' + str(1000*(t2-t1)) + '\n' )

        
        if i == 4:
            run_cap_matrix1 = run_caps.build_run_cap_matrix()
            run_cap_matrix2 = run_caps.build_run_cap_matrix_test()
            print( 'Run Matrix equal: ' + check_matrix( run_cap_matrix1[0], run_cap_matrix2[0] ))
            print( 'Run Cap equal: ' + check_matrix( run_cap_matrix1[1], run_cap_matrix2[1] ))
            print('')
        
        if i == 5:
            t1 = time.time()
            for j in range(rep):
                run_cap_matrix1 = run_caps.build_run_cap_matrix()
            t1 = ( time.time() - t1 ) / rep
            print( '   Time1 per iter: ' + str(t1) )

            t2 = time.time()
            for j in range(rep):
                run_cap_matrix2 = run_caps.build_run_cap_matrix_test()
            t2 = ( time.time() - t2 ) / rep
            print( '   Time2 per iter: ' + str(t2) )

            print( ' Difference x1,000,000: ' + str(1000000*(t2-t1)) + '\n' )
        
        if i == 6:
            i1 = Inter.DataFiles( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )
            i2 = Inter.DataFiles( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0], True )
            #print( 'ID to Index equal: ' + check_matrix( i1.ID_to_index, i2.ID_to_index, 1, 1))
            #print( 'Skip Data Index equal: ' + check_matrix( i1.skip_data_index, i2.skip_data_index, 1, 1 ))
            #print( 'Index to Name equal: ' + check_matrix( i1.index_to_name, i2.index_to_name, 1, 1 ))

            print( 'ID to Index equal: ' + str(i1.ID_to_index == i2.ID_to_index) )
            print( 'Skip Data Index equal: ' + str(i1.skip_data_index == i2.skip_data_index) )
            print( 'Index to Name equal: ' + str(i1.index_to_name == i2.index_to_name) )
