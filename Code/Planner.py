import glob
import math
import os
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
from Quest_Data import QuestData  

def planner( quest_data: QuestData, data_files: Inter.DataFiles, run_cap_mat = False, message = 2 ):
    plan_debug = {'Status': ''}
    #run_int = Inter.ConfigList.run_int
    run_int = Inter.ConfigList.settings['Run Count Integer']

    drop_matrix = np.transpose( quest_data.drop_matrix )
    AP_costs = np.transpose( quest_data.AP_costs )
    run_size = np.size( AP_costs )

    if run_int: 
        runs = cp.Variable( (run_size,1) , integer=True)
    else: 
        runs = cp.Variable( (run_size,1) , nonneg=True )

    # Checks to see if any drops exist for a desired Material.
    for i in range(data_files.mat_index_total):
        for j in drop_matrix[i]:
            if j > 0:
                break
        else:
            if data_files.index_to_name[i] != '':
                error = 'Obtaining any ' + data_files.index_to_name[i]
                error += ' is impossible with these restrictions.'
                Inter.Debug().warning( error, 2, message )
                data_files.goals[i] = 0

    objective = cp.Minimize( AP_costs @ runs )

    constr_ini = [ drop_matrix @ runs >= data_files.goals ]
    if run_int:
        constr_ini.append( np.eye(run_size) @ runs >= np.zeros((run_size,1), dtype=int) )
    
    constraints = constr_ini.copy()

    if run_cap_mat:
        if len(run_cap_mat) > 2:
            if run_cap_mat['Matrix'].any():
                constraints.append( run_cap_mat['Matrix'] @ runs <= run_cap_mat['List'] )
        elif run_cap_mat[0].any():
            constraints.append( run_cap_mat[0] @ runs <= run_cap_mat[1] )

    prob = cp.Problem( objective , constraints )
    prob.solve()
    
    if (prob.status != 'optimal') and (message >= 1):
        Inter.Debug().warning( 'This solution is or was: ' + prob.status )
    
    if prob.status == 'infeasible':
        plan_debug['Status'] = 'infeasible'

        error = 'The applied Run Caps likely made the Goals impossible.'
        Inter.Debug().warning( error, 1, message )

        # Run Count Integer removed because it applies extra constraints which
        # slow the analysis.
        if run_int:
            error = 'Run Count Integer will be removed for further analysis.'
            Inter.Debug().warning( error, 1, message )

            run_int = False
            runs = cp.Variable( (run_size,1) , nonneg=True )
            constr_ini = [ drop_matrix @ runs >= data_files.goals ]

        # Remove Bleached Earth Run Caps first, because of the exclusive mats
        # If that doesn't work, keep only the constraints for Monthly Tickets.
        for backup in ['Free Quests', 'Monthly']:
            if len(run_cap_mat) <= 2:
                break
            try:
                row = run_cap_mat['Event'].index(backup)
                if backup == 'Free Quests' and len(run_cap_mat['Matrix']) == 1:
                        continue
            except ValueError:
                continue

            if backup == 'Free Quests':
                error = 'Problem will be run again after removing Bleach Caps.'
                Inter.Debug().warning( error, 1, message)
                
                new_mat = np.delete( run_cap_mat['Matrix'], row, 0)
                new_list = np.delete( run_cap_mat['List'], row, 0)
            else:
                error = 'Problem will be run again after removing all Run Caps.'
                Inter.Debug().warning( error, 1, message)

                row_num = len(run_cap_mat['Matrix'])
                col_num = len(run_cap_mat['Matrix'][0])
                shape = ( row_num - row , col_num )

                dele = np.zeros( ( row_num, col_num ), dtype=bool )
                dele[row:] = True
                new_mat = np.reshape( run_cap_mat['Matrix'][dele,...], shape )

                dele = np.zeros( row_num, dtype=bool )
                dele[row:] = True
                new_list = run_cap_mat['List'][dele,...]
            
            constraints = constr_ini.copy()
            constraints.append( new_mat @ runs <= new_list )

            prob = cp.Problem( objective, constraints )
            prob.solve()

            if prob.status == 'optimal':
                break
            else:
                error = 'Analysis was still a failure.'
                Inter.Debug().warning( error, 1, message)
    
    total_AP = ''
    if prob.status == 'infeasible' and prob.value == math.inf:
        run_int = runs.value
        total_AP = prob.value
    
    # Makes Run counts integers.
    elif run_int:
        run_int = runs.value
        total_AP = int(prob.value)
    else: 
        run_int = np.zeros( (run_size,1) , dtype = int)
        count = 0
        for i in runs.value:
            if count == 511 or count == 512:
                x=1
            if i[0] < 0.1: 
                run_int[count,0] = 0
            elif (i[0] - math.floor(i[0])) < 0.01:
                run_int[count,0] = int(i[0])
            else: 
                run_int[count,0] = int(math.ceil(i[0]))
            count += 1
        
        total_AP = int( AP_costs @ runs.value )

    return ( prob , run_int , total_AP, plan_debug )

class Output:
    def __init__(self) -> None:
        pass

    def console_print( self, text, next_line = True ):
        print( text )
        return text + '\n' * next_line
    
    # Finds an appropriate indentation between each column of data.
    def find_indent( self, text ):
        indent = [0] * len(max( text, key = len ))
        for line in text:
            for j in range(len(line)):
                # Want a bit of padding if there are entries, but no spacing if there aren't
                new_longest = len(line[j]) + 1
                if new_longest > (indent[j] + 1):
                    indent[j] = new_longest

        return indent

    def add_gained_mats( self, text, drop_matrix_line, run_count, index_to_name, num_format ):
        gained_mats = False
        for i in range(len( drop_matrix_line )):
            mat_drop = drop_matrix_line[i]
            if mat_drop > 0:
                text[-1].append( num_format.format( run_count*mat_drop ) + ' ' )
                text[-1].append( index_to_name[i] + ' , ')
                gained_mats = True
        
        # Remove the ', ' from the last mat. 'gained_mats' flag just for extra security
        if gained_mats:
            last_mat_len = len(text[-1][-1])
            text[-1][-1] = text[-1][-1][0:( last_mat_len - 2 )]
        
        return text

    # 'text' array formatting: [0] is the Quest name, [1] is the number of runs, 
    #   [2] is boxes, [3] is average number of [4] acquired. Repeats.
    def format_farming_plan_text( self, text, output_longer, output_basic = False ):
        indent = self.find_indent(text)

        for line in text:
            lead_text = "{:<{}}{:>{}}".format(line[0], indent[0], line[1], indent[1])
            if output_basic:
                # Adds number of boxes farmed
                output_basic += self.console_print( lead_text + line[2] )
                lead_text += '  =  '

            # Adds average acquired Mats for 'Farming Plan Drops'
            output_longer += lead_text
            for i in range( 3, len(line), 2 ):
                output_longer += "{:>{}}{:<{}}".format(line[i], indent[i], line[i+1], indent[i+1])
            output_longer += '\n'
        
        return output_longer , output_basic

    def create_drop_file( self, output, runs, nodes: QuestData, index_to_name ):
        output_drops = output
        text = []
        ticket_start = -1

        # Creates matrix of drop data information for each quest.
        for i in range(len(runs)):
            if nodes.quest_names[i] in nodes.recorded_months:
                ticket_start = i
                break

            run_count = int(runs[i])
            if run_count > 0:
                text.append([nodes.quest_names[i] + ':', "{:,}".format(run_count) + ' times', ''])

                if nodes.runs_per_box[i] != 'F':
                    text[-1][2] = '   Boxes Farmed = ' + "{:.2f}".format( run_count / nodes.runs_per_box[i] )

                # For Farming Plan Drops
                text = self.add_gained_mats( text, nodes.drop_matrix[i], run_count, index_to_name, "{:.2f}" )

        # Formats the drop parts of the output files.
        output_drops, output = self.format_farming_plan_text( text, output_drops, output)

        # Creates matrix of ticket choice information for each month.
        if ticket_start != -1 and ticket_start < (len(runs) - 1):
            ticket_text = []
            output_ticket = '\nThe choices you should make for Monthly Exchange Tickets are:\n'
            prev_relevant_month = False
            prev_relevant_year = False

            for i in range(ticket_start, len(runs)):

                run_count = int(runs[i])
                if run_count > 0:

                    month_name = nodes.quest_names[i]
                    if month_name != prev_relevant_month:

                        cur_year = month_name.split()[1]
                        if cur_year != prev_relevant_year:
                            if prev_relevant_year != False:
                                ticket_text.append([ '----', '', '' ])
                            prev_relevant_year = cur_year

                        ticket_text.append([ month_name, '= ', '' ])
                    
                    ticket_text = self.add_gained_mats( ticket_text, nodes.drop_matrix[i], run_count, 
                                                       index_to_name, "{:.0f}" )

                    prev_relevant_month = month_name

            # Formats the ticket parts of the output files.
            if ticket_text != []:
                output_ticket, i = self.format_farming_plan_text( ticket_text, output_ticket )
                
                output += self.console_print( output_ticket, False )
                output_drops += output_ticket

        return output, output_drops
    
    def avoid_plan_name_error( self, former_plans, text ):
        os.makedirs(os.path.dirname(former_plans), exist_ok=True)
        with open( former_plans, 'w') as f:
            f.write(text)
            f.close()

    def file_creation( self, plan_name, file_name, text, debug_report = False, failure = False ):
        name_prefix = Inter.path_prefix + 'Former Plans\\'
        name_suffix = time.strftime("%Y%m%d_%H%M%S__", time.localtime()) + file_name

        main_file_name = Inter.path_prefix + file_name
        if failure:
            main_file_name = Inter.path_prefix + plan_name + file_name

        with open( main_file_name, 'w') as f:
            f.write(text)
            f.close()
        
        try:
            self.avoid_plan_name_error( name_prefix + plan_name + name_suffix, text )
        except OSError:
            if debug_report:
                text += '!! Plan Name not accepted by OS\n\n'
            self.avoid_plan_name_error( name_prefix + name_suffix, text )

    def make_report( self, text, header = '' ):
        if text == []:
            return ''
        
        indent = self.find_indent(text)

        run_debug = header + '\n'
        for i in range(len(text)):
            for j in range(len(text[i])):
                run_debug += "{:<{}}".format(text[i][j], indent[j])
            run_debug += '\n'
        
        return run_debug
    
    def create_note_file( self, plan_name = '', failure = False ):
        output = ''
        debug = Inter.Debug()
    
        if debug.error != '':
            output = '!! WARNING !!\n'
            output += debug.error + '\n'
    
        output += self.make_report( debug.config_notes, '__Configurations:')+'\n'
        output += debug.monthly_notes +'\n'
        output += self.make_report( debug.event_notes,'__The Events included in this analysis were:' ) +'\n\n'
        output += self.make_report( debug.lotto_notes,'__The Lotto Drop Bonuses for each Quest were:' ) +'\n\n'
        text = '__The following are notes to make sure that Run Caps were applied correctly:'
        output += self.make_report( debug.run_cap_debug, text )

        self.file_creation( plan_name, 'Config Notes.txt', output, True, failure )

    def print_out( self, prob, runs, total_AP, nodes: QuestData, index_to_name ):
        output = self.console_print( 'These results are: ' + prob.status )
        output += self.console_print( 'The total AP required is: ' + "{:,}".format(total_AP) + '\n' )
        output += self.console_print( 'You should run:' )

        output, output_drops = self.create_drop_file( output, runs, nodes, index_to_name )
        
        if Inter.ConfigList.settings['Output Files'] :
            plan_name = Inter.ConfigList.settings['Plan Name']
            if plan_name:
                plan_name += '_'

            self.file_creation( plan_name, 'Farming Plan.txt', output )
            self.file_creation( plan_name, 'Farming Plan Drops.txt', output_drops)
            self.create_note_file(plan_name)