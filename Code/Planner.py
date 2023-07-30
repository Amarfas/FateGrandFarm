import glob
import os
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
from Quest_Data import QuestData

def planner( quest_data: QuestData, data_files: Inter.DataFiles, run_cap_matrix = False, run_int = False ):
    drop_matrix = np.transpose( quest_data.drop_matrix )
    AP_costs = np.transpose( quest_data.AP_costs )
    run_size = np.size( AP_costs )

    if run_int: 
        runs = cp.Variable( (run_size,1) , integer=True)
    else: 
        runs = cp.Variable( (run_size,1) , nonneg=True )

    # Checks to see if any drops exist for a desired Material.
    for i in range(data_files.drop_index_count):
        for j in drop_matrix[i]:
            if j > 0:
                break
        else:
            if data_files.index_to_name[i] != '':
                Inter.Debug().error_warning( 'Obtaining any ' + data_files.index_to_name[i] + ' is impossible with these restrictions.' )
                data_files.goals[i] = 0

    objective = cp.Minimize( AP_costs @ runs )

    constraints = [ drop_matrix @ runs >= data_files.goals ]
    if run_cap_matrix:
        constraints.append( run_cap_matrix[0] @ runs <= run_cap_matrix[1] )
    if run_int:
        constraints.append( np.eye(run_size) @ runs >= np.zeros((run_size,1)) )

    prob = cp.Problem( objective , constraints )
    prob.solve()

    if prob.status == 'infeasible':
        prob = cp.Problem( objective, [ drop_matrix @ runs >= data_files.goals ] )
        prob.solve()
        Inter.Debug().error_warning( 'The applied Run Caps made the Goals impossible.' )

    # Makes Run counts integers.
    if run_int:
        return ( prob , runs.value , prob.value )
    else: 
        run_int_values = np.zeros( (run_size,1) , dtype = int)
        count = 0
        for i in runs.value:
            if i[0] < 0.1: 
                run_int_values[count,0] = 0
            else: 
                run_int_values[count,0] = int(i[0]) + 1
            count += 1
        return ( prob , run_int_values , int( AP_costs @ runs.value ) )

class Output:
    def __init__(self) -> None:
        pass

    def console_print( self, text ):
        print( text )
        return text + '\n'
    
    def create_drop_file( self, output, runs, nodes: QuestData, index_to_name ):
        output_drops = output
        text = []

        # Creates matrix of drop data information for each quest.
        for i in range(len(runs)):
            run_count = int(runs[i])
            if run_count > 0:
                text.append([nodes.quest_names[i] + ':', "{:,}".format(run_count) + ' times'])

                if nodes.runs_per_box[i] != 'F':
                    text[-1].append('   Boxes Farmed = ' + "{:.2f}".format( run_count / nodes.runs_per_box[i] ))
                else:
                    text[-1].append('')
                text[-1].append('  =  ')

                for j in range(len( nodes.drop_matrix[i] )):
                    mat_drop = nodes.drop_matrix[i][j]
                    if mat_drop > 0:
                        text[-1].append( "{:.2f}".format( run_count*mat_drop ) + ' ' + index_to_name[j] + ', ' )

        # Finds an appropriate indentation between each column of data.
        indent = []
        for i in text:
            for j in range(len(i)):
                try:
                    new = len(i[j])
                    if new > indent[j]:
                        indent[j] = new
                except IndexError:
                    indent.append(new)
        
        # Formats the output files.
        for i in range(len(text)):
            lead_text = "{:<{}}{:>{}}".format(text[i][0], indent[0], text[i][1], indent[1])
            output += self.console_print( lead_text + text[i][2] )

            output_drops += lead_text
            for j in range(3,len(text[i])):
                output_drops += "{:<{}}".format(text[i][j], indent[j]+1)
            output_drops += '\n'

        return output, output_drops
    
    def avoid_plan_name_error( self, former_plans, text ):
        os.makedirs(os.path.dirname(former_plans), exist_ok=True)
        with open( former_plans, 'w') as f:
            f.write(text)
            f.close()

    def file_creation( self, plan_name, time_stamp, file_name, text, debug_report = False ):
        name_prefix = Inter.path_prefix + 'Former Plans\\'
        name_suffix = time_stamp + file_name

        with open( Inter.path_prefix + file_name, 'w') as f:
            f.write(text)
            f.close()
        
        try:
            self.avoid_plan_name_error( name_prefix + plan_name + name_suffix, text )
        except OSError:
            if debug_report:
                text += '!! Plan Name not accepted by OS\n\n'
            self.avoid_plan_name_error( name_prefix + name_suffix, text )

    
    def make_debug_report( self, plan_name = '', time_stamp = '' ):
        output = ''
        if Inter.Debug.error != '':
            output = '!! WARNING !!\n'
            output += Inter.Debug.error + '\n'
        output += '__Configurations:\n'
        output += Inter.Debug.config_notes + '\n'
        output += Inter.Debug.end_notes + '\n'
        output += Inter.Debug.lotto_notes + '\n'

        self.file_creation( plan_name, time_stamp, 'Debug.txt', output, True )


    def print_out( self, prob, runs, total_AP, nodes: QuestData, index_to_name, will_output_files = True ):
        output = self.console_print( 'These results are: ' + prob.status )
        output += self.console_print( 'The total AP required is: ' + "{:,}".format(total_AP) + '\n' )
        output += self.console_print( 'You should run:' )

        output, output_drops = self.create_drop_file( output, runs, nodes, index_to_name )
        
        if will_output_files:
            plan_name = Inter.ConfigList.plan_name
            if plan_name:
                plan_name += '_'
            time_stamp = time.strftime("%Y%m%d_%H%M%S__", time.localtime())

            self.file_creation( plan_name, time_stamp, 'Farming Plan.txt', output )
            self.file_creation( plan_name, time_stamp, 'Farming Plan Drops.txt', output_drops)
            self.make_debug_report( plan_name, time_stamp )