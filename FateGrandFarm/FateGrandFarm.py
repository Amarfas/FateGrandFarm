import glob
from Nodes import Nodes
import Interpret as Inter
import Planner as Plan

# Maybe this should all be in a 'main' method? No clue about the etiquette there for more 'professional' programs.
path_prefix = Inter.standardize_path()

debug = Inter.Debug( path_prefix )

event_use = debug.note_config('Use Event', 'bool')
event_find = debug.note_config('Event Name')
last_area = debug.note_config('Last Area')
multi_event = debug.note_config('Multiple Event', 'bool')
remove_zeros = debug.note_config('Remove Zeros', 'bool')
drop_weight = debug.note_config('Drop Weight', 'float')

goals_debug = 'Test'

input_data = Inter.InputData( path_prefix + 'Files\\GOALS' + goals_debug + '.csv', glob.glob( path_prefix + 'Files\\* - Calc.csv' )[0], debug, remove_zeros )
run_caps = Inter.RunCaps(debug)

nodes = Nodes()
nodes.multi_event( path_prefix + 'Files\\', run_caps, debug, event_find, input_data.mat_count, input_data.ID_to_index, multi_event )
nodes.add_free_drop( glob.glob( path_prefix + 'Files\\* - APD.csv' )[0], run_caps, last_area, debug, input_data.skip_data_index )

run_cap_matrix = run_caps.build_run_cap_matrix()
prob , runs , total_AP = Plan.planner( nodes, debug, input_data, run_cap_matrix )

output = Plan.Output( path_prefix, debug )
output.print_out( prob.status, runs, total_AP, nodes.node_names )