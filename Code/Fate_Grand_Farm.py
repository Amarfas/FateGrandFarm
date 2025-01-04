import glob
from Quest_Data import QuestData
import Interpret as Inter
import Planner as Plan

Inter.standardize_path()
Inter.ConfigList().read_config_ini()

def main():
    path_pre = Inter.path_prefix
    run_caps = Inter.RunCaps()

    # Used to easily test different 'GOALS.csv' inputs.
    # goals_debug = 'Per'

    #data_files = Inter.DataFiles( Inter.path_prefix + 'GOALS' + goals_debug + '.csv', 
    #                             glob.glob( Inter.path_prefix + 'Data Files\\*Calc.csv' )[0] )

    #goals = path_pre + Inter.ConfigList.goals_file
    goals = path_pre + Inter.ConfigList.settings['Goals File Name']
    calc_csv = glob.glob( path_pre + 'Data Files\\*Calc.csv' )[0]
    apd_csv = glob.glob( path_pre + 'Data Files\\*APD.csv' )[0]

    data_files = Inter.DataFiles( goals, calc_csv )

    quest_data = QuestData()
    quest_data.multi_event( run_caps, data_files.ID_to_index, data_files.mat_index_total )
    quest_data.add_free_drop( apd_csv, run_caps, data_files.skip_data_index, data_files.csv_col_total )
    quest_data.read_monthly_ticket_list( run_caps, data_files.ID_to_index, data_files.mat_index_total )

    # First index is the run matrix, second index is the matric with all run caps.
    run_cap_matrix = run_caps.build_run_cap_matrix()
    prob , runs , total_AP, deb = Plan.planner( quest_data, data_files, run_cap_matrix )

    Plan.Output().print_out( prob, runs, total_AP, quest_data, data_files.index_to_name )

if Inter.ConfigList().settings['Debug on Fail']:
    try:
        main()
    except:
        print('FAILED EXECUTION')
        Plan.Output().create_note_file('FAILED_EXECUTION__')
else:
    main()