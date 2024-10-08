import glob
from Quest_Data import QuestData
import Interpret as Inter
import Planner as Plan

Inter.standardize_path()
Inter.ConfigList().read_config_ini()

def main():
    run_caps = Inter.RunCaps()

    # Used to easily test different 'GOALS.csv' inputs.
    goals_debug = ''

    data_files = Inter.DataFiles( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )

    quest_data = QuestData()
    quest_data.multi_event( run_caps, data_files.ID_to_index, data_files.drop_index_count )
    quest_data.add_free_drop( glob.glob( Inter.path_prefix + 'Data Files\\*APD.csv' )[0], run_caps, data_files.skip_data_index )
    quest_data.read_monthly_ticket_list( run_caps, data_files.ID_to_index, data_files.drop_index_count )

    # First index is the run matrix, second index is the matric with all run caps.
    run_cap_matrix = run_caps.build_run_cap_matrix()
    prob , runs , total_AP = Plan.planner( quest_data, data_files, run_cap_matrix )

    Plan.Output().print_out( prob, runs, total_AP, quest_data, data_files.index_to_name, Inter.ConfigList.create_output_files )

if Inter.ConfigList().debug_on_fail:
    try:
        main()
    except:
        Plan.Output().create_note_file('FAILED_EXECUTION__')
else:
    main()