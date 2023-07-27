import glob
import os
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
from Nodes import Nodes

def planner( nodes: Nodes, debug: Inter.Debug, input_data: Inter.InputData, run_cap_matrix = False, run_int = False ):
    drop_matrix = np.transpose( nodes.drop_matrix )
    AP_costs = np.transpose( nodes.AP_costs )
    run_size = np.size( AP_costs )
    if run_int: 
        runs = cp.Variable( (run_size,1) , integer=True)
    else: 
        runs = cp.Variable( (run_size,1) , nonneg=True )

    for i in range(input_data.mat_count):
        for j in drop_matrix[i]:
            if j > 0: break
        else:
            if input_data.index_to_name[i] != '':
                debug.make_note( 'Obtaining any ' + input_data.index_to_name[i] + ' is impossible with these restrictions.' )
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
    def __init__( self, path_prefix, debug: Inter.Debug ):
        self.path_prefix = path_prefix
        self.debug = debug

    def console_print( self, text ):
        print( text )
        return text + '\n'

    def file_creation( self, file_name, text ):
        specific = time.ctime(time.time()).replace(':','_') + '__' + self.debug.file_name + ' '
        plan_folder = self.path_prefix
        former_plans = plan_folder + 'Former Plans\\' + specific + file_name

        with open( plan_folder + file_name, 'w') as f:
            f.write(text)
            f.close()
        
        os.makedirs(os.path.dirname(former_plans), exist_ok=True)
        with open( former_plans, 'w') as f:
            f.write(text)
            f.close()

    def print_out( self, optimal, runs, total_AP, node_names, output_text = False ):
        output = self.console_print( 'These results are: ' + optimal )
        output += self.console_print( 'The total AP required is: ' + "{:,}".format(total_AP) )
        output += self.console_print( 'You should run:' )

        count = 0
        for i in runs:
            if i > 0:
                output += self.console_print( node_names[count] + ': ' + "{:,}".format(int(i)) + ' times')
            count += 1
        
        if output_text:
            self.file_creation( 'Farming Plan.txt' , output )

            output = ''
            if self.debug.error != '':
                output = '!! WARNING !!\n'
                output += self.debug.error + '\n'
            output += '__Configurations:\n'
            output += self.debug.config_notes + '\n'
            output += self.debug.end_notes

            self.file_creation( 'Debug.txt' , output )