import csv
import glob
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
import d_Interpret as IN
from Quest_Data import QuestData
from d_Quest_Data import QuestData as QT
from Planner import planner
import d_Extra as ex

# Mode 1: Check if 'Node Names', 'AP Costs', and 'Drop Matrices' are the same.
# Mode 2: Check if 'ID to Index', 'Skip Data Index', and 'Index to Name' lists are the same.
# Mode 3: Check if 'Run Matrix' and 'Run Caps' are similar or the same.
# Mode 4: Check if 'Planner' outputs are similar or the same.
# Mode 5: Compare times to 'Build Matrix' and run the 'Planner', with below 'rep' count.
# Mode 6-10: Compare times for building 'Data Files', 'Event Matrix',
#    'Free Matrix', 'Monthly Matrix', and 'Run Cap Matrix', respectively
# 'Check Default' means skipping a flat set of '' for fgf_config.ini
# 'Check Settings' will put every kind of setting ASAP
# 'Line Break' will test with one side using APD and Calc csv's with line breaks

# 'Sample' has a bit of Bronze/Silver/Gold, no Gems, Statues, or XP.
# 'Test' has everything but Octuplets, including XP. Notably 1000+ Moonlight to break Run Caps
# 'Test1' has flat thousands of Bronze/Silver/Gold, but no mats after Traum
# 'Test2' has select few Bronze mats
# 'Test3' has thousands of quite a few mats, and a demand for 2 gold gems
# 'Test4' has 2000 of four Bronze mats, 100 of Gems/Statues, and 3000 XP

tests = { 'Print': True ,
        'Goals': [ '_Per', 'Test', 'Test1', 'Test2', 'Test3', 'Test4', '_Sample' ] ,
        'Events': [ 0, 1, 2, 3 ] ,
        'Modes': [ 1, 2, 3, 4 ] ,
        'Modes': [ 7, 9 ]  ,
        'Modes': [ 1, 2, 3, 4 ] ,
        'Reps': 100 ,
        'Config Test': False ,
        'Check Default': False ,
        'Check Settings': True ,
        'Setting Start Num': 0 ,
        'Setting Pause': -1 ,
        'Line Break': False }

# Input different configuration changes you would like to automatically be tested
change_config = {'Event Cap':                [2000, 0] ,
                 'Lotto Cap':                [2000, 0] ,
                 'Raid Cap':                 [500, 0] ,
                 'Bleach Cap':               [100, 0] ,
                 'Training Grounds Half AP': ['n', 'y'] ,
                 'Training Grounds Third AP':['n', 'y'] ,
                 'Remove Zeros':             ['y', 'n'] ,
                 'Run Count Integer':        ['n', 'y'] ,
                 'Monthly Ticket Per Day':   [1, 0, 4] ,
                 'Monthly Ticket Start Date':['', '12/31/24', '2/5/25', '8/20/25'] ,
                 'Monthly Ticket End Date':  ['', '1/1/25', '15 day', '5 month', '1 year'] ,
                 'Stop Here':                ['', 'Fuyuki', 'Bleach'] }

def build_matrix( goals, pre, new_code = True ):
    if new_code:
        input_data = Inter.DataFiles( goals, glob.glob( pre[0] + '*Calc.csv' )[0] )
        run_caps = Inter.RunCaps()
    else:
        input_data =    IN.DataFiles( goals, glob.glob( pre[1] + '*Calc.csv' )[0] )
        run_caps =    IN.RunCaps()
    
    folder = 'Events Farm\\'
    if config['Folder'] != '':
        folder = 'Code\\_debug\\Events_List\\' + config['Folder'] + '\\'

    if new_code:
        nodes = QuestData( input_data, folder )
        nodes.multi_event( run_caps, input_data.ID_to_index, input_data.mat_index_total )
        nodes.add_free_drop( glob.glob( pre[0] + '*APD.csv' )[0], run_caps )
        nodes.read_monthly_ticket_list( run_caps, input_data.ID_to_index, input_data.mat_index_total )

    else:
        nodes = QT(folder)
        nodes.multi_event( run_caps, input_data.ID_to_index, input_data.mat_index_total )
        nodes.add_free_drop( glob.glob( pre[1] + '*APD.csv' )[0], 
                            run_caps, input_data.skip_data_index, input_data.csv_col_total )
        nodes.read_monthly_ticket_list( run_caps, input_data.ID_to_index, input_data.mat_index_total )

    return nodes, input_data, run_caps, run_caps.build_run_cap_matrix()

def add_total_time( timer, time_dif, *category ):
    if isinstance(category[0], list):
        category = category[0]
    
    current = str(category[0])
    if len(category) > 1:
        addon = list(category)[1:]
        try:
            timer[current] = add_total_time( timer[current], time_dif, addon )
        except KeyError:
            timer[current] = add_total_time( {}, time_dif, addon )
    else:
        try:
            timer[current]['Tot'] += time_dif
            timer[current]['Rep'] += 1
            timer[current]['Avg'] = timer[current]['Tot'] / timer[current]['Rep']
        except KeyError:
            timer[current] = {'Avg': time_dif, 'Tot': time_dif, 'Rep': 1}

    return timer

def change_time( test_package, test, t1, t2, mult ):
    ex.PrintText().print( '   Time1 per iter: ' + str(t1) )
    ex.PrintText().print( '   Time2 per iter: ' + str(t2) )

    time_dif = (t2-t1) * mult
    mult_text = format(mult,',')
    ex.PrintText().print( ' ' + test + ' Difference x' + mult_text + ': ' + str(time_dif) + '\n' )

    timer = test_package['Time']
    timer = add_total_time( timer, time_dif, test, 'Tot' )

    goals = test_package['Goals']
    goals_test = goals[ max(goals.find('GOALS'), 0): ]
    timer = add_total_time( timer, time_dif, test, 'Goal',  goals_test )

    config = test_package['Config']
    for i in config:
        timer = add_total_time( timer, time_dif, test, 'Config',  i, str(config[i]) )

    test_package['Time'] = timer
    return test_package

def test_1( valid, nodes: QuestData, nodes2: QuestData ):
    valid = ex.check_matrix( valid, 'Nodes Names equal:', nodes.quest_names, nodes2.quest_names, False )
    valid = ex.check_matrix( valid, 'AP Cost equal:', nodes.AP_costs, nodes2.AP_costs )
    valid = ex.check_matrix( valid, 'Drop Matrix equal:', nodes.drop_matrix, nodes2.drop_matrix )
    return ex.PrintText().check_valid(valid)

def test_2( valid, goals, pre ):
    i1 = Inter.DataFiles( goals , glob.glob( pre[0] + '*Calc.csv' )[0] )
    i2 = IN.DataFiles(    goals , glob.glob( pre[1] + '*Calc.csv' )[0] )

    eq1 = (i1.ID_to_index == i2.ID_to_index)
    eq2 = (i1.skip_data_index == i2.skip_data_index)
    eq3 = (i1.index_to_name == i2.index_to_name)
    ex.PrintText().print( 'ID to Index equal: ' + str(eq1) )
    ex.PrintText().print( 'Skip Data Index equal: ' + str(eq2) )
    ex.PrintText().print( 'Index to Name equal: ' + str(eq3) )
    return ex.PrintText().check_valid( valid and eq1 and eq2 and eq3 )

def test_3( valid, run_caps: Inter.RunCaps, run_caps2: Inter.RunCaps ):
    run_cap_matrix = run_caps.build_run_cap_matrix()
    run_cap_matrix2 = run_caps2.build_run_cap_matrix()
    valid = ex.check_matrix( valid, 'Run Matrix equal:', run_cap_matrix['Matrix'], run_cap_matrix2['Matrix'] )
    valid = ex.check_matrix( valid, 'Run Cap equal:', run_cap_matrix['List'], run_cap_matrix2['List'] )
    return ex.PrintText().check_valid(valid)

def test_4( valid, nodes, nodes2, input_data, input_data2, run_cap_matrix, run_cap_matrix2 ):
    mes = 1 - tests['Config Test']
    prob , runs , tot_AP, plan_d = planner( nodes, input_data, run_cap_matrix, mes )
    prob2 , runs2 , tot_AP2, plan_d2 = planner( nodes2, input_data2, run_cap_matrix2, mes )

    valid = ex.check_matrix( valid, 'Run counts equal:', runs, runs2, True, prob, prob2 )
    if tot_AP == tot_AP2: 
        ex.PrintText().print( "{:<{}}{:<{}}".format( 'Total AP equal:', 24, 'T: AP = ' + str(tot_AP), 0 ) )
    else: 
        ex.PrintText().print( "{:<{}}{:<{}}".format( 'Total AP equal:', 24, 'F: norm: '+ str(tot_AP) + 
                                    ' != test: ' + str(tot_AP2), 0 ) )
        valid = False
    return ex.PrintText().check_valid(valid)

def test_time_types( test_num, pre, goals, run_caps, input_data, new_code ):
    if test_num == 5:
        nodes, input_data, run_caps, run_cap_matrix = build_matrix( goals, pre, new_code )
        prob , runs , tot_AP, plan_d = planner( nodes, input_data, run_cap_matrix, 0 )

    elif test_num == 6:
        if new_code:
            input_data = Inter.DataFiles( goals, glob.glob( pre[0] + '*Calc.csv' )[0] )
        else:
            input_data = IN.DataFiles( goals, glob.glob( pre[1] + '*Calc.csv' )[0] )

    elif test_num >= 7 or test_num <= 9:
        folder = 'Events Farm\\'
        if config['Folder'] != '':
            folder = 'Code\\_debug\\Events_List\\' + config['Folder'] + '\\'

        if new_code:
            nodes = QuestData( input_data, folder )
        else:
            nodes = QT(folder)

        if test_num == 7:
            nodes.multi_event( run_caps, input_data.ID_to_index, input_data.mat_index_total )
        elif test_num == 8:
            if new_code:
                nodes.add_free_drop( glob.glob( pre[0] + '*APD.csv' )[0], run_caps )
            else:
                nodes.add_free_drop( glob.glob( pre[1] + '*APD.csv' )[0], 
                            run_caps, input_data.skip_data_index, input_data.csv_col_total )
        elif test_num == 9:
            if new_code:
                nodes.read_monthly_ticket_list( run_caps, input_data.ID_to_index, input_data.mat_index_total )
            else:
                nodes.read_monthly_ticket_list( run_caps, input_data.ID_to_index, input_data.mat_index_total )
    
    elif test_num == 10:
        run_cap_matrix = run_caps.build_run_cap_matrix()

def time_loop( test_num, test_package, run_caps, input_data, new_code = True ):
    reps = test_package['Reps']
    goals = test_package['Goals']
    pre = test_package['Data_Prefix']

    t = time.time()
    for loop in range(reps):
        test_time_types( test_num, pre, goals, run_caps, input_data, new_code )
    t = ( time.time() - t ) / reps
    return t

def test_time( test_num, test_package, run_caps, run_caps2, input_data, input_data2 ):
    t1 = time_loop( test_num, test_package, run_caps, input_data )
    t2 = time_loop( test_num, test_package, run_caps2, input_data2, False )

    test_name = {5: 'Build + Planner', 6: 'Data Files', 7: 'Event', 
                 8: 'Free', 9: 'Month', 10: 'Run Cap Matrix'}

    return change_time( test_package, test_name[test_num], t1, t2, 1000000 )

Inter.standardize_path()
IN.standardize_path()
ex.PrintText().main_settings(tests)

valid = True
test_package = {'Time': {} , 
                'Data_Prefix': [Inter.path_prefix + 'Data Files\\',
                                Inter.path_prefix + 'Data Files\\'] ,
                'Reps': tests['Reps'] , 
                'Temp_ini': [] ,
                }

# Finding GOALS.csv testing sheets
for i in range(len(tests['Goals'])):
    if tests['Goals'][i][:4] == 'Test':
        temp = 'Code\\_debug\\Goals\\GOALS_'
    else:
        temp = 'GOALS'
    tests['Goals'][i] = Inter.path_prefix + temp + tests['Goals'][i] + '.csv'

if len(tests['Events']) == 0:
    tests['Events'] = ['']
config_list, test_package['Set Num'] = ex.make_config( change_config, tests )

# Finding line break testing sheets:
if tests['Line Break']:
    temp = Inter.path_prefix + 'Code\\_debug\\'
    test_package['Data_Prefix'] = [temp + 'Data Files Test\\',
                                   temp + 'Data Files Test 2\\']
    tests['Modes'].remove(3)

del temp

def goals_loop( valid, test_package, tests ):
    pre = test_package['Data_Prefix']

    for goals in tests['Goals']:
        test_package['Goals'] = goals

        nodes, input_data, run_caps, run_cap_matrix = build_matrix(goals, pre)
        if Inter.ConfigList.settings['Run Count Integer'] and len(nodes.AP_costs) > 100:
            continue
        nodes2, input_data2, run_caps2, run_cap_matrix2 = build_matrix(goals, pre, False)

        ex.PrintText().print_setting(goals)

        for test_num in tests['Modes']:
            if test_num == 1:
                valid = test_1( valid, nodes, nodes2 )
            elif test_num == 2:
                valid = test_2( valid, goals, pre )
            elif test_num == 3:
                valid = test_3( valid, run_caps, run_caps2 )
            elif test_num == 4:
                valid = test_4( valid, nodes, nodes2, input_data, input_data2, 
                               run_cap_matrix, run_cap_matrix2 )
            elif test_num >= 5:
                test_package = test_time( test_num, test_package, run_caps, run_caps2, 
                                         input_data, input_data2 )
    return valid, test_package

# MAIN algorithm
for config in config_list:
    test_package['Config'] = config
    test_package['Temp_ini'] = ex.set_config( config, test_package['Temp_ini'] )

    if ex.PrintText().new_config(config):
        continue

    Inter.ConfigList().read_config_ini()
    IN.ConfigList().read_config_ini()

    valid, test_package = goals_loop( valid, test_package, tests )

print( 'Overall Tests Were: ' + str(valid) )
for i in test_package['Time']:
    if len(test_package['Time'][i]) > 0:
        print( test_package['Time'][i] + '\n' )

# Resets .ini files
with open('fgf_config.ini', 'w') as f:
    f.writelines(test_package['Temp_ini'])
    f.close

with open('OLD Files\\fgf_config_test.ini', 'w') as f:
    f.writelines(test_package['Temp_ini'])
    f.close

with open('Code\\_debug\\Goals\\fgf_config_test.ini', 'w') as f:
    f.writelines(test_package['Temp_ini'])
    f.close