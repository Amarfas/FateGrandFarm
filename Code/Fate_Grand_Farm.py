import os
import glob
from Quest_Data import QuestData
import Interpret as Inter
import Planner as Plan

Inter.standardize_path()
Inter.ConfigList().read_config_ini()

def main():
    path_pre = Inter.path_prefix
    run_caps = Inter.RunCaps()

    # Initiate reading .csv files
    calc_csv = glob.glob( os.path.join(path_pre, 'Data Files', '*Calc.csv') )[0]
    apd_csv = glob.glob(  os.path.join(path_pre, 'Data Files', '*APD.csv' ) )[0]

    goals_file = os.path.join(path_pre, Inter.ConfigList.settings['Goals File Name'])
    data_files = Inter.DataFiles( goals_file, calc_csv )

    # Interpret the the above files
    quest_data = QuestData( data_files )
    quest_data.multi_event( run_caps )
    quest_data.add_free_drop( apd_csv, run_caps )
    quest_data.read_monthly_ticket_list( run_caps )
    
    run_cap_matrix = run_caps.build_run_cap_matrix()
    
    # Run and print core analysis
    if data_files.goals.size > 0:
        plan = Plan.Planner( quest_data, data_files, run_cap_matrix )
        solution = plan.planner()

        Plan.Output().print_out( solution, quest_data )
    else:
        Inter.Debug().warning('Goals were not properly read.')
        Plan.Output().create_debug()

if Inter.ConfigList().settings['Debug on Fail']:
    try:
        main()
    except:
        Plan.Output().create_debug()
else:
    main()