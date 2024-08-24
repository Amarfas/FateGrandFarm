import configparser
import csv
import glob
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
import Interpret_Test as IN
from Quest_Data import QuestData
from Quest_Data_Test import QuestData as QT
from Planner import planner

# Mode 1: Check if Node Names, AP Costs, and Drop Matrices are equal.
# Mode 2: Check if Planner outputs are similar or the same.
# Mode 3: Compare run times, with below 'rep' count.
# 'tolerance' defines the minimum difference that will break the matrix comparison
# 'tolerance2' defines the maximum difference that'll be ignored in matrix comparisons

test_list = [ 'Test', 'Test1', 'Test2', 'Test3', 'Test4', 'Test_Per' ]

test_modes = [ 1 ]
tolerance = 0.01
tolerance2 = 0
rep = 100
goals_debug = ''
mult_test = True
test_Interpret_py = True

# Input different configuration changes you would like to automatically be tested
change_config = {'TG_half_AP':     False ,
                 'remove_zeros':   False ,
                 'run_int':        True ,
                 'stop_here':      [] ,
                 'monthly_ticket': [] ,
                 'monthly_start':  [] ,
                 'monthly_end':    [] }

def build_matrix( ver ):
    if test_Interpret_py and ver == 'NodesTest':
        input_data = IN.DataFiles( IN.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( IN.path_prefix + 'Data Files\\*Calc.csv' )[0] )
        run_caps = IN.RunCaps()
    else:
        input_data = Inter.DataFiles( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )
        run_caps = Inter.RunCaps()

    if ver == 'Nodes':
        nodes = QuestData()
        nodes.multi_event( run_caps, input_data.ID_to_index, input_data.drop_index_count )
        nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, input_data.skip_data_index )
        nodes.read_monthly_ticket_list( run_caps, input_data.ID_to_index, input_data.drop_index_count )

    if ver == 'NodesTest':
        nodes = QT()
        nodes.multi_event( run_caps, input_data.ID_to_index, input_data.drop_index_count )
        nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, input_data.skip_data_index )
        #nodes.read_monthly_ticket_list( run_caps, input_data.ID_to_index, input_data.drop_index_count )

    return nodes, input_data, run_caps, run_caps.build_run_cap_matrix()

def check_reverb( norm, test, norm_data = {}, test_data = {}, index = 'i', coord = [], layer = 0 ):
    index_list = ['i', 'j', 'k', 'l', 'm', 'n']

    for i in range(len(norm)):
        norm_data[ 'd_' + index ] = norm[i]
        test_data[ 'd_' + index ] = test[i]
        new_coord = coord + [i]

        # If string, will just keep repeating otherwise
        if isinstance(norm[i], str):
            if norm[i] != test[i]:
                return 'F: (' + index + ') = ' + str(new_coord) + ' , value norm != test'
            else:
                valid = 'T'
        else:
            try:
                if len(norm[i]) != len(test[i]):
                    return 'F: (' + index + ') = ' + str(new_coord) + ' , len norm != test'
            except:
                if norm[i] != test[i]:
                    return 'F: (' + index + ') = ' + str(new_coord) + ' , value norm != test'
                else:
                    valid = 'T'
            else:
                new_index = index + ',' + index_list[layer+1]
                valid = check_reverb( norm[i], test[i], norm_data, test_data, new_index, new_coord, layer+1 )
                if valid[0] != 'T':
                    return valid

    if len(norm) == 0 or len(test) == 0:
        if len(norm) == len(test):
            valid = 'T: Both arrays empty'
        else:
            valid = 'F: Only one was empty'

    return valid

def check_matrix( overall, text, norm, test, np_array = True, extra = False, extra_test = False ):
    valid_2 = 'NA'
    if np_array:
        # Checking void or empty sets
        if norm.size > 0 and test.size > 0:
            try:
                valid_1 = (norm == test).all()
                valid_2 = norm.shape == test.shape

            except ValueError:
                for i in range(len(norm)):
                    valid_1 = (norm[i] == test[i]).all()
                    valid_2 = norm[i].shape == test[i].shape
                    if valid_1 == False or valid_2 == False:
                        break

            except AttributeError:
                valid_1 = (norm == test)
        else:
            valid_1 = (len(norm) == len(test))
    else:
        valid_1 = (norm == test)
    
    try:
        if len(norm) != len(test):
            valid_3 = 'F: At highest layer, len norm != test'
        else:
            valid_3 = check_reverb( norm, test, {'d_': norm}, {'d_': test}, 'i', [], 0 )
    except TypeError:
        # Checking for similar errors in solving the problem if runs are 'None'
        if extra.status == extra_test.status and norm == None and test == None:
            valid_3 = 'T: prob status = ' + extra.status
        else:
            valid_3 = 'F: Different problem status: norm: ' + extra.status + ' , test: ' + extra_test.status

    print( "{:<{}}{:<{}}".format( text, 24, str(valid_1) + ', ' + (str(valid_2) + ', ') * int(valid_2 != 'NA') + valid_3, 0 ) )

    if valid_2 == 'NA':
        valid_2 = True
    return overall and valid_1 and valid_2 and (valid_3[0] == 'T')

print('\n')

Inter.standardize_path()
Inter.ConfigList().read_config_ini()
if test_Interpret_py:
    IN.standardize_path()
    IN.ConfigList().read_config_ini()

valid = True
goals_list = [goals_debug]
if mult_test:
    goals_list = test_list

for goals_debug in goals_list:
    nodes, input_data, run_caps, run_cap_matrix = build_matrix('Nodes')
    nodes_test, input_data_test, run_caps_test, run_cap_matrix_test = build_matrix('NodesTest')

    print( "{:<{}}{:<{}}".format( '  Test results for:', 23, 'GOALS' + goals_debug + '.csv:', 0 ) )
    for i in test_modes:
        if i == 1:
            #print( 'Nodes Names equal: ' + check_matrix_proto( nodes.quest_names, nodes_test.quest_names, 1, 1, matrix = 'node_names' ))
            valid = check_matrix( valid, 'Nodes Names equal:', nodes.quest_names, nodes_test.quest_names, False )
            valid = check_matrix( valid, 'AP Cost equal:', nodes.AP_costs, nodes_test.AP_costs )
            valid = check_matrix( valid, 'Drop Matrix equal:', nodes.drop_matrix, nodes_test.drop_matrix )
            print('')
        
        if i == 2:
            prob , runs , total_AP = planner( nodes, input_data, run_cap_matrix, 1 )
            prob2 , runs2 , total_AP2 = planner( nodes_test, input_data_test, run_cap_matrix_test, 1 )

            valid = check_matrix( valid, 'Run counts equal:', runs, runs2, True, prob, prob2 )
            if total_AP == total_AP2: 
                print( "{:<{}}{:<{}}".format( 'Total AP equal:', 24, 'T: AP = ' + str(total_AP), 0 ) )
            else: 
                print( "{:<{}}{:<{}}".format( 'Total AP equal:', 24, 'F: norm: '+str(total_AP)+' != test: '+str(total_AP2), 0 ) )
                valid = False
            print('')
        
        if i == 3:
            t1 = time.time()
            for j in range(rep):
                nodes, input_data, run_caps, run_cap_matrix = build_matrix('Nodes')
                prob , runs , total_AP = planner( nodes, input_data, run_cap_matrix, 0 )
            t1 = ( time.time() - t1 ) / rep
            print( '   Time1 per iter: ' + str(t1) )

            t2 = time.time()
            for j in range(rep):
                nodes, input_data, run_caps, run_cap_matrix = build_matrix('NodesTest')
                prob2 , runs2 , total_AP2 = planner( nodes, input_data, run_cap_matrix, 0 )
            t2 = ( time.time() - t2 ) / rep
            print( '   Time2 per iter: ' + str(t2) )

            print( ' Difference x1,000: ' + str(1000*(t2-t1)) + '\n' )

        
        if i == 4:
            run_cap_matrix = run_caps.build_run_cap_matrix()
            run_cap_matrix_test = run_caps_test.build_run_cap_matrix()
            valid = check_matrix( valid, 'Run Matrix equal:', run_cap_matrix[0], run_cap_matrix_test[0] )
            valid = check_matrix( valid, 'Run Cap equal:', run_cap_matrix[1], run_cap_matrix_test[1] )
            print('')
        
        if i == 5:
            t1 = time.time()
            for j in range(rep):
                run_cap_matrix = run_caps.build_run_cap_matrix()
            t1 = ( time.time() - t1 ) / rep
            print( '   Time1 per iter: ' + str(t1) )

            t2 = time.time()
            for j in range(rep):
                run_cap_matrix_test = run_caps_test.build_run_cap_matrix()
            t2 = ( time.time() - t2 ) / rep
            print( '   Time2 per iter: ' + str(t2) )

            print( ' Difference x1,000,000: ' + str(1000000*(t2-t1)) + '\n' )
        
        if i == 6:
            i1 = Inter.DataFiles( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )
            i2 = Inter.DataFiles( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )

            eq1 = (i1.ID_to_index == i2.ID_to_index)
            eq2 = (i1.skip_data_index == i2.skip_data_index)
            eq3 = (i1.index_to_name == i2.index_to_name)
            print( 'ID to Index equal: ' + str(eq1) )
            print( 'Skip Data Index equal: ' + str(eq2) )
            print( 'Index to Name equal: ' + str(eq3) + '\n')
            valid = valid and eq1 and eq2 and eq2

print( 'Overall Tests Were: ' + str(valid) )

def check_matrix_proto( norm, test ,is_norm_array = False ,is_test_array = False, matrix = False ):
    # 's = F' means 'b' is an array
    # 'sa = F' means 'a' is an array

    flag = False
    row = -1
    for i in norm:
        row += 1
        if isinstance(i,str) and isinstance(test[row],str):
            if i != test[row]:
                if matrix == 'node_names':
                    print( 'F6: ('+str(row)+',~): '+str(i)+' != '+str(test[row]) )
                    #row += 1
                    flag = True
                else:
                    return 'F6: ('+str(row)+',~): '+str(i)+' != '+str(test[row])
        else:
            if not is_norm_array: 
                n = np.size(test[row])
            else: 
                n = len(test[row])
            try:
                col = 0
                if not is_test_array: 
                    m = np.size(i)
                else:
                    m = len(i)
                if m != n:
                    return 'F1 : ('+str(row)+','+str(col)+') : m != n : '+str(m)+' != '+str(n)
                for j in i:
                    if m > 1:
                        if j != test[row][col]:
                            k = test[row][col]
                            dif = abs(float(j) - float(k))
                            if col < 54 and dif > tolerance:
                                return 'F2: ('+str(row)+','+str(col)+') '+nodes.quest_names[row]+': '+str(j)+' != '+str(k)
                            else:
                                if dif > tolerance2:
                                    print( 'F3: ('+str(row)+','+str(col)+') '+nodes.quest_names[row]+': '+str(j)+' != '+str(k) )
                                    flag = True
                            return 'F2: ('+str(row)+','+str(col)+') '+nodes.quest_names[row]+': '+str(j)+' != '+str(k)

                    else:
                        if j != test[row][col]:
                            print( 'F4: ('+str(row)+','+str(col)+') '+nodes.quest_names[row]+': '+str(j)+' != '+str(test[row][col]) )
                            #row += 1
                            flag = True
                    col += 1

            except:
                if n != 1:
                    return 'F5: ('+str(row)+',~): n != 1'
                if i != test[row]:
                    return 'F6: ('+str(row)+',~): '+str(i)+' != '+str(test[row])
    if flag:
        return 'F'
    return 'T'