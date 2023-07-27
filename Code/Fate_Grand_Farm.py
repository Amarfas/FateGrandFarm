import glob
from Nodes import Nodes
import Interpret as Inter
import Planner as Plan

# Maybe this should all be in a 'main' method? No clue about the etiquette there for more 'professional' programs.
path_prefix = Inter.standardize_path()

debug = Inter.Debug( path_prefix )
tg_half_AP = debug.note_config('Training Grounds Half AP', 'bool')
run_caps = Inter.RunCaps(debug)
remove_zeros = debug.note_config('Remove Zeros', 'bool')
run_int = debug.note_config('Run Count Integer', 'bool')
last_area = debug.note_config('Last Area')
output_text = debug.note_config('Output Text')

goals_debug = ''

input_data = Inter.InputData( path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( path_prefix + 'Data Files\\*Calc.csv' )[0], debug, remove_zeros )

nodes = Nodes(remove_zeros)
nodes.multi_event( path_prefix, run_caps, debug, input_data.mat_count, input_data.ID_to_index )
nodes.add_free_drop( glob.glob( path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, last_area, debug, input_data.skip_data_index )

run_cap_matrix = run_caps.build_run_cap_matrix()
prob , runs , total_AP = Plan.planner( nodes, debug, input_data, run_cap_matrix, run_int )

output = Plan.Output( path_prefix, debug )
output.print_out( prob.status, runs, total_AP, nodes.node_names, output_text )