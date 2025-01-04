import configparser
import csv
import glob
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
import Debug_Interpret as IN
from Quest_Data import QuestData
from Debug_Quest_Data import QuestData as QT
from Planner import planner

# Mode 1: Check if 'Node Names', 'AP Costs', and 'Drop Matrices' are the same.
# Mode 2: Check if 'ID to Index', 'Skip Data Index', and 'Index to Name' lists are the same.
# Mode 3: Check if 'Run Matrix' and 'Run Caps' are similar or the same.
# Mode 4: Check if 'Planner' outputs are similar or the same.
# Mode 5: Compare times to 'Build Matrix' and run the 'Planner', with below 'rep' count.
# Modes 6-10: Compare times for building 'Run Caps', 'Data Files', 'Event Matrix',
#    'Free Matrix', and 'Run Cap Matrix', respectively
# 'test_Interpret' means that 'Debug_Interpret.py' is different
# 'Skip Default' means skipping a flat set of '' for fgf_config.ini

# 'Sample' has a bit of Bronze/Silver/Gold, no Gems, Statues, or XP.
# 'Test' has everything but Octuplets, including XP. Notably 1000+ Moonlight to break Run Caps
# 'Test1' has flat thousands of Bronze/Silver/Gold, but no mats after Traum
# 'Test2' has select few Bronze mats
# 'Test3' has thousands of quite a few mats, and a demand for 2 gold gems
# 'Test4' has 2000 of four Bronze mats, 100 of Gems/Statues, and 3000 XP

tests = { 'Test Interpret': True ,
        'Goals': [ '_Per', 'Test', 'Test1', 'Test2', 'Test3', 'Test4', '_Sample' ] ,
        'Events': [ 0, 1, 2, 3 ] ,
        'Modes': [ 1, 3, 4 ] ,
        #'Modes': [ 8 ]  ,
        'Reps': 100 ,
        'Config Test': True ,
        'Skip Default': True ,
        'Setting Start Num': 2500 ,
        'Setting Pause': -1 }

# Input different configuration changes you would like to automatically be tested
change_config = {'Event Cap':                [0, 2000] ,
                 'Lotto Cap':                [0, 2000] ,
                 'Raid Cap':                 [0, 500] ,
                 'Bleach Cap':               [0, 100] ,
                 'Training Grounds Half AP': ['n', 'y'] ,
                 'Training Grounds Third AP':[] ,
                 'Remove Zeros':             [] ,
                 'Run Count Integer':        ['n', 'y'] ,
                 'Monthly Ticket Per Day':   [0, 1, 4] ,
                 'Monthly Ticket Start Date':['', '12/31/24', '2/5/25', '8/20/25'] ,
                 'Monthly Ticket End Date':  ['', '1/1/25', '15 day', '5 month', '1 year'] ,
                 'Stop Here':                ['', 'Fuyuki', 'Bleach'] }

class PrintText():
    text = ''

    def __init__(self):
        pass

    def print( self, new_text ):
        if tests['Config Test']:
            self.text += new_text + '\n'
        else:
            print(new_text)

    def gen_unequal( self, norm, test ):
        return ' , value norm != test ; ' + str(norm) + ' != ' + str(test)

    def len_unequal( self, norm, test ):
        return ' , len norm != test ; ' + str(len(norm)) + ' != ' + str(len(test))


def build_config( events_test, skip_default ):
    config_list = []
    for i in range(len(events_test)):
        list_ini = {'Folder': str(events_test[i])}
        if skip_default:
            list_add = [list_ini]
        else:
            list_default = list_ini.copy()
            for key in change_config:
                list_default[key] = ''
            list_add = [list_default, list_ini]

        config_list += list_add
    
    return config_list

# Create a set of all conbinations of changes to configuration / settings
def build_config_test( change_config, events_test ):
    config_list = build_config( events_test, True )
    cap_set = []

    for key in change_config:
        if key.endswith('Cap') or key.endswith('Per Day'):
            cap_set.append(key)

        size = len(config_list)
        add = 0
        skips = 0

        for config in change_config[key]:
            for i in range(size):
                # For sets of settings, only one check for 0 Caps is necessary
                zero_count = 0
                if add >= 2:
                    for cap in cap_set:
                        if config_list[i][cap] == 0:
                            zero_count += 1
                    if zero_count > 0 and zero_count < len(cap_set):
                        skips += 1
                        continue

                if add > 0:
                    config_list.append(config_list[i].copy())
                config_list[i + size * add - skips][key] = config
            add += 1

    print( 'Number of Settings: ' + str(len(config_list)) + '\n' )
    
    return config_list

# Change 'fgf_config.ini' to match 'change_config' settings
def set_config( config, temp_ini ):
    if temp_ini == []:
        with open('fgf_config.ini') as f:
            temp_ini = f.readlines()
            f.close
            
        # Make sure it's not grabbing files from halfway through a previously aborted test
        if temp_ini[1] == '# TEST\n':
            with open('OLD Files\\fgf_config_test.ini') as f:
                temp_ini = f.readlines()
                f.close
            
            with open('fgf_config.ini', 'w') as f:
                f.writelines(temp_ini)
                f.close
    else:
        new_ini = temp_ini.copy()
        new_ini[1] = '# TEST\n'
        line = 0
        for key in config:
            if key == 'Folder':
                continue

            while(True):
                line += 1
                if line > len(new_ini):
                    break
                if new_ini[line].startswith(key):
                    new_ini[line] = key + ' = ' + str(config[key]) + '\n'
                    break

        with open('fgf_config.ini', 'w') as f:
            f.writelines(new_ini)
            f.close
        
    return temp_ini

def build_matrix( ver, goals ):
    if tests['Test Interpret'] and ver == 'NodesTest':
        input_data =    IN.DataFiles( goals, glob.glob(    IN.path_prefix + 'Data Files Test\\*Calc.csv' )[0] )
        run_caps =    IN.RunCaps()
    else:
        input_data = Inter.DataFiles( goals, glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )
        run_caps = Inter.RunCaps()
    
    folder = 'Events Farm\\'
    if config['Folder'] != '':
        folder = 'OLD Files\\aEVENTS TEST\\' + config['Folder'] + '\\'

    if ver == 'Nodes':
        nodes = QuestData(folder)
        nodes.multi_event( run_caps, input_data.ID_to_index, input_data.mat_index_total )
        nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files\\*APD.csv' )[0], 
                            run_caps, input_data.skip_data_index, input_data.csv_col_total )
        nodes.read_monthly_ticket_list( run_caps, input_data.ID_to_index, input_data.mat_index_total )

    if ver == 'NodesTest':
        nodes = QT(folder)
        nodes.multi_event( run_caps, input_data.ID_to_index, input_data.mat_index_total )
        nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files Test\\*APD.csv' )[0], 
                            run_caps, input_data.skip_data_index, input_data.csv_col_total )
        nodes.read_monthly_ticket_list( run_caps, input_data.ID_to_index, input_data.mat_index_total )

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
                return 'F: (' + index + ') = ' + str(new_coord) + txt.gen_unequal( norm[i], test[i] )
            else:
                valid = 'T'
        else:
            try:
                if len(norm[i]) != len(test[i]):
                    return 'F: (' + index + ') = ' + str(new_coord) + txt.len_unequal( norm[i], test[i] )
            except:
                if norm[i] != test[i]:
                    return 'F: (' + index + ') = ' + str(new_coord) + txt.gen_unequal( norm[i], test[i] )
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
            invalid = 'norm'
            if len(test) == 0:
                invalid = 'test'
            valid = 'F: Only one was empty (' + str(invalid) + ')'

    return valid

# 1st Boolean is same values, 2nd Boolean is same shape
# 'T' or 'F' better describes the problem
def check_matrix( overall, text, norm, test, np_array = True, extra = False, extra_test = False ):
    valid_2 = 'NA'
    if np_array:
        try:
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
            else:
                valid_1 = (len(norm) == len(test))
        except AttributeError:
            valid_1 = (norm == test)
    else:
        valid_1 = (norm == test)
    
    try:
        if len(norm) != len(test):
            valid_3 = 'F: At highest layer' + txt.len_unequal( norm, test )
        else:
            valid_3 = check_reverb( norm, test, {'d_': norm}, {'d_': test}, 'i', [], 0 )
    except TypeError:
        # Checking for similar errors in solving the problem if runs are 'None'
        if extra.status == extra_test.status and norm == None and test == None:
            valid_3 = 'T: prob status = ' + extra.status
        else:
            valid_3 = 'F: Different problem status: norm: ' + extra.status + ' , test: ' + extra_test.status

    txt.print( "{:<{}}{:<{}}".format( text, 24, str(valid_1) + ', ' + 
                        (str(valid_2) + ', ') * int(valid_2 != 'NA') + valid_3, 0 ) )

    if valid_2 == 'NA':
        valid_2 = True
    return overall and valid_1 and valid_2 and (valid_3[0] == 'T')

def change_time( total_timer, test, t1, t2, mult ):
    txt.print( '   Time1 per iter: ' + str(t1) )
    txt.print( '   Time2 per iter: ' + str(t2) )

    time_dif = (t2-t1) * mult
    mult_text = format(mult,',')
    txt.print( ' ' + test + ' Difference x' + mult_text + ': ' + str(time_dif) + '\n' )

    try:
        total_timer[test] += time_dif
    except KeyError:
        total_timer[test] = time_dif
    return total_timer

def check_valid( valid ):
    txt.print('')
    if valid == False:
        if tests['Config Test']:
            print(txt.text)

        print( '\n Setting ' + str(set_num) + ': ' + str(config) + '\n' )
        print( "{:<{}}{:<{}}".format( '  Test results for:', 23, goals, 0 ) )
        pass
    return valid

def test_1( valid, nodes: QuestData, nodes2: QuestData ):
    valid = check_matrix( valid, 'Nodes Names equal:', nodes.quest_names, nodes2.quest_names, False )
    valid = check_matrix( valid, 'AP Cost equal:', nodes.AP_costs, nodes2.AP_costs )
    valid = check_matrix( valid, 'Drop Matrix equal:', nodes.drop_matrix, nodes2.drop_matrix )
    return check_valid(valid)

def test_2( valid, goals ):
    i1 = Inter.DataFiles( goals , glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )
    i2 = IN.DataFiles(    goals , glob.glob( Inter.path_prefix + 'Data Files Test\\*Calc.csv' )[0] )

    eq1 = (i1.ID_to_index == i2.ID_to_index)
    eq2 = (i1.skip_data_index == i2.skip_data_index)
    eq3 = (i1.index_to_name == i2.index_to_name)
    txt.print( 'ID to Index equal: ' + str(eq1) )
    txt.print( 'Skip Data Index equal: ' + str(eq2) )
    txt.print( 'Index to Name equal: ' + str(eq3) )
    return check_valid( valid and eq1 and eq2 and eq3 )

def test_3( valid, run_caps: Inter.RunCaps, run_caps2: Inter.RunCaps ):
    run_cap_matrix = run_caps.build_run_cap_matrix()
    run_cap_matrix2 = run_caps2.build_run_cap_matrix()
    valid = check_matrix( valid, 'Run Matrix equal:', run_cap_matrix['Matrix'], run_cap_matrix2[0] )
    valid = check_matrix( valid, 'Run Cap equal:', run_cap_matrix['List'], run_cap_matrix2[1] )
    return check_valid(valid)

def test_4( valid, nodes, nodes2, input_data, input_data2, run_cap_matrix, run_cap_matrix2):
    mes = 1 - tests['Config Test']
    prob , runs , tot_AP, plan_d = planner( nodes, input_data, run_cap_matrix, mes )

    # Temporary for testing Run Cap fixes in planner
    if plan_d['Status'] == 'infeasible':
        run_cap_matrix2 = run_cap_matrix

    prob2 , runs2 , tot_AP2, plan_d2 = planner( nodes2, input_data2, run_cap_matrix2, mes )

    valid = check_matrix( valid, 'Run counts equal:', runs, runs2, True, prob, prob2 )
    if tot_AP == tot_AP2: 
        txt.print( "{:<{}}{:<{}}".format( 'Total AP equal:', 24, 'T: AP = ' + str(tot_AP), 0 ) )
    else: 
        txt.print( "{:<{}}{:<{}}".format( 'Total AP equal:', 24, 'F: norm: '+ str(tot_AP) + 
                                    ' != test: ' + str(tot_AP2), 0 ) )
        valid = False
    return check_valid(valid)

def test_5( total_time, goals ):
    t1 = time.time()
    for t in range(tests['Reps']):
        nodes, input_data, run_caps, run_cap_matrix = build_matrix( 'Nodes', goals )
        prob , runs , tot_AP, plan_d = planner( nodes, input_data, run_cap_matrix, 0 )
    t1 = ( time.time() - t1 ) / tests['Reps']

    t2 = time.time()
    for t in range(tests['Reps']):
        nodes, input_data, run_caps, run_cap_matrix = build_matrix( 'NodesTest', goals )
        prob2 , runs2 , tot_AP2, plan_d2 = planner( nodes, input_data, run_cap_matrix, 0 )
    t2 = ( time.time() - t2 ) / tests['Reps']

    return change_time( total_time, 'Build + Planner', t1, t2, 1000 )

def test_6( total_time ):
    t1 = time.time()
    for t in range(tests['Reps']):
        run_caps = Inter.RunCaps()
    t1 = ( time.time() - t1 ) / tests['Reps']

    t2 = time.time()
    for t in range(tests['Reps']):
        run_caps = IN.RunCaps()
    t2 = ( time.time() - t2 ) / tests['Reps']

    return change_time( total_time, 'Run Caps', t1, t2, 1000000 )

def test_7( total_time, goals ):
    t1 = time.time()
    for t in range(tests['Reps']):
        input_data = Inter.DataFiles( goals, glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )
    t1 = ( time.time() - t1 ) / tests['Reps']

    t2 = time.time()
    for t in range(tests['Reps']):
        input_data = IN.DataFiles( goals, glob.glob( IN.path_prefix + 'Data Files Test\\*Calc.csv' )[0] )
    t2 = ( time.time() - t2 ) / tests['Reps']

    return change_time( total_time, 'Data Files', t1, t2, 1000000 )

def test_8( total_time, run_caps, run_caps2, input_data, input_data2 ):
    folder = 'Events Farm\\'
    if config['Folder'] != '':
        folder = 'OLD Files\\aEVENTS TEST\\' + config['Folder'] + '\\'

    t1 = time.time()
    for t in range(tests['Reps']):
        nodes = QuestData(folder)
        nodes.multi_event( run_caps, input_data.ID_to_index, input_data.mat_index_total )
    t1 = ( time.time() - t1 ) / tests['Reps']

    t2 = time.time()
    for t in range(tests['Reps']):
        nodes = QT(folder)
        nodes.multi_event( run_caps2, input_data2.ID_to_index, input_data2.mat_index_total )
    t2 = ( time.time() - t2 ) / tests['Reps']

    return change_time( total_time, 'Event', t1, t2, 1000000 )

def test_9( total_time, run_caps, run_caps2, input_data, input_data2 ):
    folder = 'Events Farm\\'
    if config['Folder'] != '':
        folder = 'OLD Files\\aEVENTS TEST\\' + config['Folder'] + '\\'

    t1 = time.time()
    for t in range(tests['Reps']):
        nodes = QuestData(folder)
        nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files Test\\*APD.csv' )[0], 
                            run_caps, input_data.skip_data_index, input_data.csv_col_total )
    t1 = ( time.time() - t1 ) / tests['Reps']

    t2 = time.time()
    for t in range(tests['Reps']):
        nodes = QT(folder)
        nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files Test\\*APD.csv' )[0], 
                            run_caps2, input_data2.skip_data_index, input_data2.csv_col_total )
    t2 = ( time.time() - t2 ) / tests['Reps']

    return change_time( total_time, 'Free', t1, t2, 1000000 )

def test_10( total_time, run_caps, run_caps2 ):
    t1 = time.time()
    for t in range(tests['Reps']):
        run_cap_matrix = run_caps.build_run_cap_matrix()
    t1 = ( time.time() - t1 ) / tests['Reps']

    t2 = time.time()
    for t in range(tests['Reps']):
        run_cap_matrix2 = run_caps2.build_run_cap_matrix()
    t2 = ( time.time() - t2 ) / tests['Reps']

    return change_time( total_time, 'Run Cap Matrix', t1, t2, 1000000 )


Inter.standardize_path()
if tests['Test Interpret']:
    IN.standardize_path()

for i in range(len(tests['Goals'])):
    tests['Goals'][i] = Inter.path_prefix + 'GOALS' + tests['Goals'][i] + '.csv'

if len(tests['Events']) == 0:
    tests['Events'] = ['']
config_list = build_config( tests['Events'], tests['Skip Default'] )

if tests['Config Test']:
    config_list += build_config_test( change_config, tests['Events'] )

valid = True
txt = PrintText()
temp_ini = []
set_num = -1
total_time = {}

# MAIN algorithm
for config in config_list:
    temp_ini = set_config( config, temp_ini )
    setting_print = True

    set_num += 1
    if set_num < tests['Setting Start Num']:
        continue

    Inter.ConfigList().read_config_ini()
    if tests['Test Interpret']:
        IN.ConfigList().read_config_ini()

    for goals in tests['Goals']:
        nodes, input_data, run_caps, run_cap_matrix = build_matrix( 'Nodes', goals )
        if Inter.ConfigList.settings['Run Count Integer'] and len(nodes.AP_costs) > 100:
            continue

        nodes2, input_data2, run_caps2, run_cap_matrix2 = build_matrix( 'NodesTest', goals )

        if setting_print:
            print( '\n Setting ' + str(set_num) + ': ' + str(config) + '\n' )
            setting_print = False

            if (int(set_num) == int(tests['Setting Pause'])):
                tests['Config Test'] = False

        txt.text = ''
        txt.print( "{:<{}}{:<{}}".format( '  Test results for:', 23, goals, 0 ) )

        for test in tests['Modes']:
            if test == 1:
                valid = test_1( valid, nodes, nodes2 )
            elif test == 2:
                valid = test_2( valid, goals )
            elif test == 3:
                valid = test_3( valid, run_caps, run_caps2 )
            elif test == 4:
                valid = test_4( valid, nodes, nodes2, input_data, input_data2, run_cap_matrix, run_cap_matrix2 )
            elif test == 5:
                total_time = test_5( total_time, goals )
            elif test == 6:
                total_time = test_6( total_time )
            elif test == 7:
                total_time = test_7( total_time, goals )
            elif test == 8:
                total_time = test_8( total_time, run_caps, run_caps2, input_data, input_data2 )
            elif test == 9:
                total_time = test_9( total_time, run_caps, run_caps2, input_data, input_data2 )
            elif test == 10:
                total_time = test_10( total_time, run_caps, run_caps2 )

print( 'Overall Tests Were: ' + str(valid) )
if len(total_time) > 0:
    print(total_time)

# Resets .ini files
with open('fgf_config.ini', 'w') as f:
    f.writelines(temp_ini)
    f.close

with open('OLD Files\\fgf_config_test.ini', 'w') as f:
    f.writelines(temp_ini)
    f.close