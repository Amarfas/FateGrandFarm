import glob
from Nodes import Nodes
import Interpret as Inter
import Planner as Plan

# Maybe this should all be in a 'main' method? No clue about the etiquette there for more 'professional' programs.
Inter.standardize_path()

Inter.Debug().set_notice()
run_caps = Inter.RunCaps()
Inter.ConfigList().create_config_list()

goals_debug = 'Test'

input_data = Inter.InputData( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )

nodes = Nodes()
nodes.multi_event( run_caps, input_data.mat_count, input_data.ID_to_index )
nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, input_data.skip_data_index )

run_cap_matrix = run_caps.build_run_cap_matrix()
prob , runs , total_AP = Plan.planner( nodes, input_data, run_cap_matrix )

output = Plan.Output()
output.print_out( prob.status, runs, total_AP, nodes.node_names )