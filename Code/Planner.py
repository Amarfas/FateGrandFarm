import glob
import os
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
from Nodes import Nodes

def planner( nodes: Nodes, input_data: Inter.InputData, run_cap_matrix = False, run_int = False ):
    drop_matrix = np.transpose( nodes.drop_matrix )
    AP_costs = np.transpose( nodes.AP_costs )
    run_size = np.size( AP_costs )
    if run_int: 
        runs = cp.Variable( (run_size,1) , integer=True)
    else: 
        runs = cp.Variable( (run_size,1) , nonneg=True )

    for i in range(input_data.mat_count):
        for j in drop_matrix[i]:
            if j > 0: 
                break
        else:
            if input_data.index_to_name[i] != '':
                Inter.Debug().make_note( 'Obtaining any ' + input_data.index_to_name[i] + ' is impossible with these restrictions.' )
                input_data.goals[i] = 0

    objective = cp.Minimize( AP_costs @ runs )
    constraints = [ drop_matrix @ runs >= input_data.goals ]
    if run_cap_matrix:
        constraints.append( run_cap_matrix[0] @ runs <= run_cap_matrix[1] )

    prob = cp.Problem( objective , constraints )
    prob.solve()

    if run_int:
        return ( prob , runs.value , prob.value )
    else: 
        run_clean = np.zeros( (run_size,1) , dtype = int)
        count = 0
        for i in runs.value:
            if i[0] < 0.1: 
                run_clean[count,0] = 0
            else: 
                run_clean[count,0] = int(i[0]) + 1
            count += 1
        return ( prob , run_clean , int( AP_costs @ runs.value ) )

class Output:
    def __init__(self) -> None:
        pass

    def console_print( self, text ):
        print( text )
        return text + '\n'
    
    def print_drops( self, output, runs, nodes: Nodes, index_to_name ):
        output_drops = output

        for i in range(len(runs)):
            run_count = int(runs[i])
            if run_count > 0:
                text = nodes.node_names[i] + ':   ' + "{:,}".format(run_count) + ' times'
                output_drops += text + '  =  '

                if nodes.runs_per_box[i] != 'F':
                    text += '  ,   Boxes Farmed = ' + "{:.2f}".format( run_count / nodes.runs_per_box[i] )

                output += self.console_print(text)

                add_drop = ''
                for j in range(len( nodes.drop_matrix[i] )):
                    mat_drop = nodes.drop_matrix[i][j]
                    if mat_drop > 0:
                        if add_drop != '':
                            add_drop += ', '
                        add_drop += "{:.2f}".format( run_count*mat_drop ) + ' ' + index_to_name[j]
                
                output_drops += add_drop + '\n'

        return output, output_drops
    
    def avoid_error( self, former_plans, text ):
        os.makedirs(os.path.dirname(former_plans), exist_ok=True)
        with open( former_plans, 'w') as f:
            f.write(text)
            f.close()

    def file_creation( self, plan_name, time_stamp, file_name, text ):
        former_start = Inter.path_prefix + 'Former Plans\\'
        former_end = time_stamp + file_name

        with open( Inter.path_prefix + file_name, 'w') as f:
            f.write(text)
            f.close()
        
        try:
            self.avoid_error( former_start + plan_name + former_end, text )
        except:
            self.avoid_error( former_start + former_end, '!! Plan Name not accepted by OS\n' + text )
    
    def make_debug_report( self, plan_name = '', time_stamp = '' ):
        output = ''
        if Inter.Debug.error != '':
            output = '!! WARNING !!\n'
            output += Inter.Debug.error + '\n'
        output += '__Configurations:\n'
        output += Inter.Debug.config_notes + '\n'
        output += Inter.Debug.end_notes + '\n'
        output += Inter.Debug.lotto_notes + '\n'

        self.file_creation( plan_name, time_stamp, 'Debug.txt', output )


    def print_out( self, prob, runs, total_AP, nodes: Nodes, index_to_name, output_files = True ):
        output = self.console_print( 'These results are: ' + prob.status )
        output += self.console_print( 'The total AP required is: ' + "{:,}".format(total_AP) + '\n' )
        output += self.console_print( 'You should run:' )

        output, output_drops = self.print_drops( output, runs, nodes, index_to_name )
        
        if output_files:
            plan_name = Inter.ConfigList.plan_name
            if plan_name:
                plan_name += '_'
            time_stamp = time.strftime("%Y%m%d_%H%M%S__", time.localtime())

            self.file_creation( plan_name, time_stamp, 'Farming Plan.txt', output )
            self.file_creation( plan_name, time_stamp, 'Farming Plan Drops.txt', output_drops)

            self.make_debug_report( plan_name, time_stamp )