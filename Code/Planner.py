import glob
import math
import os
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
from Quest_Data import QuestData

def planner( quest_data: QuestData, data_files: Inter.DataFiles, run_cap_matrix = False, message = 2 ):
    run_int = Inter.ConfigList.run_int
    #use_all_tickets = Inter.ConfigList.use_all_tickets

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
                if message >= 2:
                    Inter.Debug().error_warning( 'Obtaining any ' + data_files.index_to_name[i] + ' is impossible with these restrictions.' )
                data_files.goals[i] = 0

    objective = cp.Minimize( AP_costs @ runs )

    constraints = [ drop_matrix @ runs >= data_files.goals ]
    if run_cap_matrix and run_cap_matrix[0].any():
        constraints.append( run_cap_matrix[0] @ runs <= run_cap_matrix[1] )

        #if use_all_tickets:
        #    constraints.append( run_cap_matrix[2] @ runs >= run_cap_matrix[3] )

    if run_int:
        constraints.append( np.eye(run_size) @ runs >= np.zeros((run_size,1), dtype=int) )

    prob = cp.Problem( objective , constraints )
    prob.solve()

    if (prob.status != 'optimal') and (message >= 1):
        Inter.Debug().error_warning( 'This solution is or was: ' + prob.status )
    
    if prob.status == 'infeasible':
        if message >= 1:
            Inter.Debug().error_warning( 'The applied Run Caps likely made the Goals impossible. Analysis will now remove Run Caps.' )
        constraints = [ drop_matrix @ runs >= data_files.goals ]
        if run_int:
            constraints.append( np.eye(run_size) @ runs >= np.zeros((run_size,1), dtype=int) )
        
        prob = cp.Problem( objective, constraints )
        prob.solve()

    # Makes Run counts integers.
    if run_int:
        return ( prob , runs.value , int(prob.value) )
    else: 
        run_int_values = np.zeros( (run_size,1) , dtype = int)
        count = 0
        for i in runs.value:
            if count == 511 or count == 512:
                x=1
            if i[0] < 0.1: 
                run_int_values[count,0] = 0
            elif (i[0] - math.floor(i[0])) < 0.01:
                run_int_values[count,0] = int(i[0])
            else: 
                run_int_values[count,0] = int(math.ceil(i[0]))
            count += 1

        return ( prob , run_int_values , int( AP_costs @ runs.value ) )

class Output:
    def __init__(self) -> None:
        pass

    def console_print( self, text, next_line = True ):
        print( text )
        return text + '\n' * next_line
    
    # Finds an appropriate indentation between each column of data.
    def find_indent( self, text ):
        indent = [0] * len(max( text, key = len ))
        for i in text:
            for j in range(len(i)):
                new = len(i[j])
                if new > indent[j]:
                    indent[j] = new + 1

        return indent
    
    def format_drop_text_file( self, text, output_longer, output_basic = False ):
        indent = self.find_indent(text)

        for i in range(len(text)):
            lead_text = "{:<{}}{:>{}}".format(text[i][0], indent[0], text[i][1], indent[1])
            if output_basic:
                output_basic += self.console_print( lead_text + text[i][2] )
                lead_text += '  =  '

            output_longer += lead_text
            for j in range( 3, len(text[i]), 2 ):
                output_longer += "{:>{}}{:<{}}".format(text[i][j], indent[j], text[i][j+1], indent[j+1])
            output_longer += '\n'
        
        return output_longer , output_basic
    
    def add_material_drops( self, text, drop_matrix_line, run_count, index_to_name, format ):
        for i in range(len( drop_matrix_line )):
            mat_drop = drop_matrix_line[i]
            if mat_drop > 0:
                text[-1].append( format.format( run_count*mat_drop ) + ' ' )
                text[-1].append( index_to_name[i] + ', ' )
        
        return text

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
                text = self.add_material_drops( text, nodes.drop_matrix[i], run_count, index_to_name, "{:.2f}" )

        # Formats the drop parts of the output files.
        output_drops, output = self.format_drop_text_file( text, output_drops, output)

        # Creates matrix of ticket choice information for each month.
        if ticket_start != -1 and ticket_start < (len(runs) - 1):
            ticket_text = []
            output_ticket = '\nThe choices you should make for Monthly Exchange Tickets are:\n'
            prev_choice_month = False

            for i in range(ticket_start, len(runs)):
                
                run_count = int(runs[i])
                if run_count > 0:

                    month_name = nodes.quest_names[i]
                    if prev_choice_month != month_name:
                        ticket_text.append([ month_name, ' = ', '' ])
                    
                    ticket_text = self.add_material_drops( ticket_text, nodes.drop_matrix[i], run_count, index_to_name, "{:.0f}" )

                    prev_choice_month = month_name

            # Formats the ticket parts of the output files.
            if ticket_text != []:
                output_ticket, i = self.format_drop_text_file( ticket_text, output_ticket )
                
                output += self.console_print( output_ticket, False )
                output_drops += output_ticket

        return output, output_drops
    
    def avoid_plan_name_error( self, former_plans, text ):
        os.makedirs(os.path.dirname(former_plans), exist_ok=True)
        with open( former_plans, 'w') as f:
            f.write(text)
            f.close()

    def file_creation( self, plan_name, file_name, text, debug_report = False ):
        name_prefix = Inter.path_prefix + 'Former Plans\\'
        name_suffix = time.strftime("%Y%m%d_%H%M%S__", time.localtime()) + file_name

        with open( Inter.path_prefix + file_name, 'w') as f:
            f.write(text)
            f.close()
        
        try:
            self.avoid_plan_name_error( name_prefix + plan_name + name_suffix, text )
        except OSError:
            if debug_report:
                text += '!! Plan Name not accepted by OS\n\n'
            self.avoid_plan_name_error( name_prefix + name_suffix, text )

    def make_debug_report( self, text, header = '' ):
        if text == []:
            return ''
        
        indent = self.find_indent(text)
        run_debug = header

        for i in range(len(text)):
            for j in range(len(text[i])):
                run_debug += "{:<{}}".format(text[i][j], indent[j])
            run_debug += '\n'
        
        return run_debug
    
    def create_note_file( self, plan_name = '' ):
        output = ''
        debug = Inter.Debug()
    
        if debug.error != '':
            output = '!! WARNING !!\n'
            output += debug.error + '\n'
    
        output += '__Configurations:\n'
        output += debug.config_notes + '\n'
        output += debug.monthly_notes
        output += self.make_debug_report( debug.event_notes, '__The Events included in this analysis are:\n' )  + '\n\n'
        output += self.make_debug_report( debug.lotto_notes, '__The lotto drop bonus for each node is:\n' )  + '\n\n'
        output += self.make_debug_report( debug.run_cap_debug, '__The following are notes to make sure that Run Caps were applied correctly:\n' )

        self.file_creation( plan_name, 'Config Notes.txt', output, True )


    def print_out( self, prob, runs, total_AP, nodes: QuestData, index_to_name, will_output_files = True ):
        output = self.console_print( 'These results are: ' + prob.status )
        output += self.console_print( 'The total AP required is: ' + "{:,}".format(total_AP) + '\n' )
        output += self.console_print( 'You should run:' )

        output, output_drops = self.create_drop_file( output, runs, nodes, index_to_name )
        
        if will_output_files:
            plan_name = Inter.ConfigList.plan_name
            if plan_name:
                plan_name += '_'

            self.file_creation( plan_name, 'Farming Plan.txt', output )
            self.file_creation( plan_name, 'Farming Plan Drops.txt', output_drops)
            self.create_note_file(plan_name)