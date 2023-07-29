import glob
from Nodes import Nodes
import Interpret as Inter
import Planner as Plan

Inter.standardize_path()
Inter.ConfigList().create_config_list()

def main():
    run_caps = Inter.RunCaps()

    goals_debug = 'Test2'

    input_data = Inter.InputData( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )

    nodes = Nodes()
    nodes.multi_event( run_caps, input_data.mat_count, input_data.ID_to_index )
    nodes.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, input_data.skip_data_index )

    run_cap_matrix = run_caps.build_run_cap_matrix()
    prob , runs , total_AP = Plan.planner( nodes, input_data, run_cap_matrix, Inter.ConfigList.run_int )

    output = Plan.Output()
    output.print_out( prob, runs, total_AP, nodes, input_data.index_to_name, Inter.ConfigList.output_files )

if Inter.ConfigList().debug_on_fail:
    try:
        main()
    except:
        Plan.Output().make_debug_report()
else:
    main()