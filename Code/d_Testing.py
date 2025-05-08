import os
import glob
import math
import numpy as np
import cvxpy as cp
import time
import random
import Interpret as Inter
import d_Interpret as IN
from Quest_Data import QuestData
from d_Quest_Data import QuestData as QT
import Planner as Plan
import d_Planner as PL
import d_Extra as ex
import d_Extra_Temp as ex2

# Mode 1-6: Compare variable values: 1 = 'Node Names', 'AP Costs', and 'Drop Matrices';
#    2 = 'ID to Index', 'Skip Data Index', and 'Index to Name';
#    3 = 'Run Matrix' and 'Run Caps'; 4 = 'Planner'; 5 = 'Debug'; 6 = 'Output'
# Mode 7: Compare times to 'Build Matrix' and run the 'Planner', with below 'rep' count.
# Mode 8-14: Compare times for building: 8 = 'Data Files', 9 = 'Event Matrix',
#    10 = 'Free Matrix', 11 = 'Monthly Matrix', 12 = 'Run Cap Matrix',
#    13 = 'Planner', and 14 = 'Output'
# 'Config Test' is checking all combos of settings in change_config
# 'Check Default' means skipping a flat set of '' for fgf_config.ini
# 'Check Settings' will put every kind of setting ASAP
# 'Line Break' will test with one side using APD and Calc csv's with line breaks
# 'No Skip' will cause every variation of 'change_config' to be included
# 'No Extreme' excludes results over 10,000 from timer data

# 'Sample' has a bit of Bronze/Silver/Gold, no Gems, Statues, or XP.
# 'Test' has everything but Octuplets, including XP. Notably 1000+ Moonlight to break Run Caps
# 'Test1' has flat thousands of Bronze/Silver/Gold, but no mats after Traum
# 'Test2' has select few Bronze mats
# 'Test3' has thousands of quite a few mats, and a demand for 2 gold gems
# 'Test4' has 2000 of four Bronze mats, 100 of Gems/Statues, and 3000 XP

tests = {'Print': False ,
        'Goals': [ 'Per', 'Test', 'Test1', 'Test2', 'Test3', 'Test4', 'Sample' ] ,
        'Folder': [ 0, 1, 2, 3 ] ,
        'Modes': [ 1, 2, 3, 4 ] ,
        'Reps': 100 ,
        'Config Test': True ,
        'Check Default': True ,
        'Check Settings': True ,
        'Setting Start Num': 0 ,
        'Setting Pause': -1 ,
        'Line Break': False ,
        'Random Testing': True ,
        'No Skip': True ,
        'No Extreme': True
        }

# Input different configuration changes you would like to automatically be tested
change_config = {'Event Cap':                [2000, 0, 1000] ,
                 'Lotto Cap':                [2000, 0, 1000] ,
                 'Raid Cap':                 [500, 0, 200] ,
                 'Bleach Cap':               [100, 0, 500] ,
                 'Training Grounds Half AP': ['n', 'y'] ,
                 'Training Grounds Third AP':['n', 'y'] ,
                 'Bleached Earth Half AP':   ['n', 'y'] ,
                 'Remove Zeros':             ['y', 'n'] ,
                 'Run Count Integer':        ['n', 'y'] ,
                 'Monthly Ticket Per Day':   [1, 0, 4] ,
                 'Monthly Ticket Start Date':['', '12/31/24', '2/5/25', '8/20/25'] ,
                 'Monthly Ticket End Date':  ['', '1/1/25', '15 day', '5 month', '1 year'] ,
                 'Stop Here':                ['', 'Fuyuki', 'Salem', 'Paper Moon'] }


class Toolkit():
    def __init__(self, goals, pre, folder = '', new_code = True):
        toolkit = Toolkit.build_matrix(goals, pre, folder, new_code)
        self.nodes: QuestData = toolkit['nodes']
        self.input: Inter.DataFiles = toolkit['input']
        self.run_caps: Inter.RunCaps = toolkit['runCaps']
        self.run_mat = toolkit['runMat']

    def build_matrix(goals, pre, folder = '', new_code = True):
        file_path = glob.glob( os.path.join( pre, '*Calc.csv' ) )[0]
        if new_code:
            input_data = Inter.DataFiles( goals, file_path )
            run_caps = Inter.RunCaps()
        else:
            input_data =    IN.DataFiles( goals, file_path )
            run_caps =    IN.RunCaps()

        if folder != '':
            folder = os.path.join( 'Code', '_debug', 'Events_List', folder )
        else:
            folder = 'Events Farm'

        file_path = glob.glob( os.path.join( pre, '*APD.csv' ) )[0]
        if new_code:
            nodes = QuestData( input_data, folder )
        else:
            nodes = QT( input_data, folder )
        
        nodes.multi_event( run_caps )
        nodes.add_free_drops( file_path, run_caps )
        nodes.read_monthly_ticket_list( run_caps )

        toolkit = {'nodes': nodes,
                'input': input_data,
                'runCaps': run_caps,
                'runMat': run_caps.build_run_cap_matrix()}
        return toolkit
    
    def test_planner(self, new_code = True, mes = 0):
        if new_code:
            plan = Plan.Planner( self.nodes, self.input, self.run_mat, mes )
            return plan.planner()
        else:
            return PL.planner( self.nodes, self.input, self.run_mat, mes )
    
    def add_solution(self, new_code = True):
        if new_code:
           self.solution: Plan.Solution = self.test_planner(new_code)
        else:
            prob, runs, tot_AP = self.test_planner(new_code)
            self.prob: cp.Problem = prob
            self.runs: cp.Variable = runs
            self.tot_AP = tot_AP

def add_time( timer: dict, time_dif, data, cur ):
    total = time_dif + timer.setdefault( cur, {} ).get( 'Tot', 0 )
    rep = 1 + timer[cur].get( 'Rep', 0 )
    timer[cur]['Avg'] = total / rep
    timer[cur]['Tot'] = total
    timer[cur]['Rep'] = rep
    timer[cur]['Max'] = max( time_dif, timer[cur].get('Max', -1*math.inf) )
    timer[cur]['Min'] = min( time_dif, timer[cur].get('Min', math.inf) )

    if cur == 'x':
        t1 = data[0] + timer[cur].get( 'M Tot', 0 )
        t2 = data[1] + timer[cur].get( 'd Tot', 0 )
        if t2 == 0:
            time_mult = -100 * (t1 != 0)
        else:
            time_mult = (t2-t1) / t2 * 100
        
        timer[cur]['Md Avg'] = time_mult
        timer[cur]['M Tot'] = t1
        timer[cur]['d Tot'] = t2

    return timer

def add_time2( timer, time_dif, data, cur ):
    t1, t2 = data
    try:
        timer[cur]['Tot'] += time_dif
        timer[cur]['Rep'] += 1
        timer[cur]['Avg'] = timer[cur]['Tot'] / timer[cur]['Rep']
        timer[cur]['Max'] = max( time_dif, timer[cur]['Max'] )
        timer[cur]['Min'] = min( time_dif, timer[cur]['Min'] )

        if cur == 'x':
            timer[cur]['M Tot'] += t1
            timer[cur]['d Tot'] += t2
            timer[cur]['Md Avg'] = (timer[cur]['d Tot'] - timer[cur]['M Tot'])
            timer[cur]['Md Avg'] *= 100 / timer[cur]['d Tot']

    except KeyError:
        timer[cur] = {'Avg': time_dif, 'Tot': time_dif, 'Rep': 1, 
                    'Max': time_dif, 'Min': time_dif}
        if cur == 'x':
            timer[cur].update({'Md Avg': (t2-t1) / t2 * 100, 
                                'M Tot': t1, 'd Tot': t2})

    return timer

def add_time_fld( timer: dict, time_dif, data, *category ):
    if isinstance(category[0], list):
        category = category[0]
    
    cur = str(category[0])
    if len(category) > 1:
        nxt_lvl = timer.setdefault( cur, {} )
        timer[cur] = add_time_fld( nxt_lvl, time_dif, data, list(category)[1:] )
    else:
        timer = add_time( timer, time_dif, data, cur )
    
    return timer

def change_time( test_package, test, timer, t1, t2 ):
    ex.PrintText().print( '   Time1 per iter: ' + str(t1) )
    ex.PrintText().print( '   Time2 per iter: ' + str(t2) )

    mult = 1000000

    time_dif = (t2-t1) * mult
    if t2 == 0:
        time_mult = -100 * (t1 != 0)
    else:
        time_mult = (t2-t1) / t2 * 100
    
    mult_text = format(mult,',')
    ex.PrintText().print( ' ' + test + ' Difference x' + 
                          mult_text + ': ' + str(time_dif) + '\n' )
    

    goals = test_package['Goals']
    config = test_package['Config']

    if timer['No Extreme'] and time_dif > 10000:
        timer['Skip'].append({'Time': time_dif, 'Goals': goals, 'Config': config})
        return timer

    t = { '-': time_dif, 'x': time_mult }
    d = [ t1, t2 ]
    
    for i in ['-','x']:
        timer = add_time_fld( timer, t[i], d, test, 'Tot', i )

        goals_test = goals[ ( max(goals.find('GOALS'), 0) + 5 ): ]
        timer = add_time_fld( timer, t[i], d, test, 'Goal',  goals_test, i )

        for j in config:
            timer = add_time_fld(timer, t[i], d, test, 'Config', 
                                 j, str(config[j]), i )

def test_1( nodes: QuestData, nodes2: QuestData ):
    ex.check_matrix( 'Nodes Names', nodes.quest_names, nodes2.quest_names, False )
    ex.check_matrix( 'AP Cost', nodes.AP_costs, nodes2.AP_costs )
    ex.check_matrix( 'Drop Matrix', nodes.drop_matrix, nodes2.drop_matrix )
    ex.PrintText().check_valid()

def test_2( goals, pre ):
    file_path = glob.glob( os.path.join( pre[0], '*Calc.csv' ) )[0]
    i1 = Inter.DataFiles( goals , file_path )
    file_path = glob.glob( os.path.join( pre[1], '*Calc.csv' ) )[0]
    i2 = IN.DataFiles(    goals , file_path )

    eq1 = (i1.ID_to_index == i2.ID_to_index)
    eq2 = (i1.skip_data_index == i2.skip_data_index)
    eq3 = (i1.index_to_name == i2.index_to_name)
    ex.PrintText().print( "{:<{}}{:<{}}".format( 'ID to Index equal:', 24, str(eq1), 0 ) )
    ex.PrintText().print( "{:<{}}{:<{}}".format( 'Skip Data Index equal:', 24, str(eq2), 0 ) )
    ex.PrintText().print( "{:<{}}{:<{}}".format( 'Index to Name equal:', 24, str(eq3), 0) )
    ex.PrintText().check_valid( eq1 and eq2 and eq3 )

def test_3( run_caps: Inter.RunCaps, run_caps2: Inter.RunCaps ):
    run_cap_matrix = run_caps.build_run_cap_matrix()
    run_cap_matrix2 = run_caps2.build_run_cap_matrix()
    ex.check_matrix( 'Run Matrix', run_cap_matrix['Matrix'], run_cap_matrix2['Matrix'] )
    ex.check_matrix( 'Run Cap', run_cap_matrix['List'], run_cap_matrix2['List'] )
    ex.PrintText().check_valid()

def test_4( tool ):
    mes = tests['Print']
    sol: Plan.Solution = tool['M'].test_planner( mes = mes)
    prob2 , runs2 , tot_AP2 = tool['d'].test_planner( False, mes)

    ex.check_matrix( 'Run Counts', sol.run_int, runs2, True, sol, prob2 )
    if sol.total_AP == tot_AP2: 
        ex.PrintText().print( "{:<{}}{:<{}}".format('Total AP equal:', 24, 
                                                    'T: AP = ' + str(sol.total_AP), 0 ) )
    else:
        txt = 'F: norm: '+ str(sol.total_AP) + ' != test: ' + str(tot_AP2)
        ex.PrintText().print( "{:<{}}{:<{}}".format( 'Total AP equal:', 24, txt, 0 ) )
        ex.PrintText.valid = False
    ex.PrintText().check_valid()

def test_5():
    d1 = Inter.Debug()
    d2 = IN.Debug()

    ex.check_matrix( 'Error', d1.error, d2.error)
    ex.check_matrix( 'Config Notes', d1.config_notes, d2.config_notes )
    eq = (d1.monthly_notes == d2.monthly_notes)
    ex.check_matrix( 'Event Notes', d1.event_notes, d2.event_notes )
    ex.check_matrix( 'Lotto Notes', d1.lotto_notes, d2.lotto_notes )
    ex.check_matrix( 'Run Cap Debug', d1.run_cap_debug, d2.run_cap_debug )
    ex.PrintText().check_valid( eq )

def test_6( tool ):
    Plan.Output.text_written = []
    if tool['M'].input.goals.size > 0:
        solution = tool['M'].test_planner()
        Plan.Output().print_out( solution, tool['M'].nodes )
    else:
        Plan.Output().create_debug_report()
    txt1 = Plan.Output.text_written

    PL.Output.text_written = []
    if tool['d'].input.goals.size > 0:
        prob , runs , total_AP = tool['d'].test_planner(False)
        PL.Output().print_out(prob, runs, total_AP, tool['d'].nodes, 
                              tool['d'].input.index_to_name )
    else:
        PL.Output().create_debug()
    txt2 = PL.Output.text_written

    ex.check_matrix( 'Output Files', txt1, txt2 )
    ex.PrintText().check_valid()

def test_building_drop( test_num, config, pre, tool: Toolkit, new_code ):
    folder = 'Events Farm'
    if config['Folder'] != '':
        folder = os.path.join( 'Code', '_debug', 'Events_List', config['Folder'] )

    if new_code:
        nodes = QuestData( tool.input, folder )
    else:
        nodes = QT( tool.input, folder )

    # Actual tests
    if test_num == 9:
        nodes.multi_event( tool.run_caps )

    elif test_num == 10:
        file_path = glob.glob( os.path.join( pre, '*APD.csv' ) )[0]
        nodes.add_free_drops( file_path, tool.run_caps )

    elif test_num == 11:
        nodes.read_monthly_ticket_list( tool.run_caps )

def test_time_types( test_num, config, pre, goals, tool: Toolkit, new_code ):
    if test_num == 7:
        toolkit = Toolkit( goals, pre, config['Folder'], new_code )
        toolkit.test_planner(new_code)

    elif test_num == 8:
        file_path = glob.glob( os.path.join( pre, '*Calc.csv' ) )[0]
        if new_code:
            input_data = Inter.DataFiles( goals, file_path )
        else:
            input_data = IN.DataFiles( goals, file_path )

    elif test_num >= 9 and test_num <= 11:
        test_building_drop( test_num, config, pre, tool, new_code )
    
    elif test_num == 12:
        run_cap_matrix = tool.run_caps.build_run_cap_matrix()
    
    elif test_num == 13:
        tool.test_planner(new_code)

    elif test_num >= 14:
        if new_code:
            Plan.Output().print_out( tool.solution, tool.nodes )
        else:
            PL.Output().print_out( tool.prob, tool.runs, tool.tot_AP, 
                                   tool.nodes, tool.input.index_to_name )

def time_loop( test_num, test_package, toolkit: Toolkit, new_code = True ):
    reps = test_package['Reps']
    goals = test_package['Goals']
    pre = test_package['Data_Prefix'][1]
    if new_code:
        pre = test_package['Data_Prefix'][0]
    config = test_package['Config']

    if test_num == 14:
        toolkit.add_solution(new_code)

    t = time.time()
    for loop in range(reps):
        test_time_types( test_num, config, pre, goals, toolkit, new_code )
    t = ( time.time() - t ) / reps
    return t

def test_time( test_num, test_package, timer, tool ):
    t1 = time_loop( test_num, test_package, tool['M'] )
    t2 = time_loop( test_num, test_package, tool['d'], False )

    test_name = {7: 'Build + Planner', 8: 'Data Files', 9: 'Event', 
                 10: 'Free', 11: 'Month', 12: 'Run Cap Matrix',
                 13: 'Planner', 14: 'Output'}

    change_time( test_package, test_name[test_num], timer, t1, t2 )

def reset_debug(print):
    for debug in [ Inter, IN ]:
        debug.error = [ '', '' ]
        debug.config_notes = []
        debug.monthly_notes = ''
        debug.event_notes = []
        debug.lotto_notes = []
        debug.run_cap_debug = []
        debug.notifications = print

def config_loop( test_package, tests, timer ):
    # data_files = -9% ish? maybe? -4.77 or -0.8% (6841s)
    # output = -9.84% or -11.056%? and -266.125 (667 samples) or -236.19 (165 samples)?
    # Run_Cap_Matrix is -1.247 and -3.4%? (80s) or 1.94 and 5.13% (93s) or 1.07 and 1.31% (176s) or 2.06 and -3.04% (483s) or 0 and -4% / 0 Md (1544s)
    # Planner is ~.12% (80 samples) or -327.27 and -2.16% (93 samples) or -419 and -1.7% (176s) or 104.3 and -0.3% /8.54 MD (483s) or -17 and 0%/Md (1544s)
    # Monthly is +15.25 or -1.73% / 0.3? (6839s)
    # Event is -197.5 or -0.85% (867s) or -145 and -0.5 (2186s)
    # Free is 25.4 or -0.1% (870s)or -70 and -0.45 (2193s)
    ex.set_config(test_package)

    # Skips if Setting # is before the starting Set
    if ex.PrintText().new_config(test_package['Config']):
        return

    Inter.ConfigList.cut_AP = {'Daily': 1, 'Bleach': 1}
    IN.ConfigList.cut_AP = {'Daily': 1, 'Bleach': 1}
    Inter.ConfigList().read_config_ini()
    IN.ConfigList().read_config_ini()

    pre = test_package['Data_Prefix']
    for goals in tests['Goals']:
        reset_debug(tests['Print'])
        test_package['Goals'] = goals

        tool = {'M': Toolkit(goals, pre[0], test_package['Config']['Folder'])}

        if ex.PrintText().check_failure(IN.ConfigList.settings['Run Count Integer'], 
                                        tool['M'], goals ): break
        tool['d'] = Toolkit(goals, pre[1], test_package['Config']['Folder'], False)

        for test_num in tests['Modes']:
            if test_num == 1:
                test_1( tool['M'].nodes, tool['d'].nodes )
            elif test_num == 2:
                test_2( goals, pre )
            elif test_num == 3:
                test_3( tool['M'].run_caps, tool['d'].run_caps )
            elif test_num == 4:
                test_4( tool )
            elif test_num == 5:
                test_5()
            elif test_num == 6:
                test_6( tool )
            elif test_num >= 7 and test_num <= 14:
                test_time( test_num, test_package, timer, tool )
            elif test_num == 15:
                ex2.Test_14(tool['M'])

# Initializing starts here
Inter.standardize_path()
IN.standardize_path()
Plan.Output.not_test = False
PL.Output.not_test = False
Inter.Debug.notifications = tests['Print']
IN.Debug.notifications = tests['Print']

ex.PrintText().main_settings(tests, Inter.path_prefix, IN.path_prefix)
config_list, test_package, tests = ex.prepare_test_package(change_config, tests)
timer = {'No Extreme': tests['No Extreme'], 'Skip': []}

config_main = ex.initial_config(test_package)
config_list = config_main + config_list

if tests['Random Testing']:
    random.shuffle(config_list)
    if tests['No Skip'] and len(config_list) > 10000:
        config_list = config_list[:10000]

# MAIN algorithm
for config in config_list:
    test_package['Config'] = config
    config_loop( test_package, tests, timer )
    ex.record_last( test_package, timer )

ex.reset_ini( test_package, timer )