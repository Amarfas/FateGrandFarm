import os
import glob
from Quest_Data import QuestData
import Interpret as Inter
import Planner as Plan

Inter.standardize_path()
Inter.ConfigList().read_config_ini()

def main():
    path_pre = Inter.path_prefix
    notice = Inter.Debug.notifications
    
    run_caps = Inter.RunCaps()

    # Find path for the primary '.csv' files
    if notice: print('Reading Calc and APD .csv files...', end=' ')
    calc_csv = glob.glob( os.path.join(path_pre, 'Data Files', '*Calc.csv') )[0]
    apd_csv = glob.glob(  os.path.join(path_pre, 'Data Files', '*APD.csv' ) )[0]
    if notice: print('Complete!')

    #   'DataFiles' interprets the 'GOALS' and 'Calc' csv's in order to tell all
    #  other classes where the Materials go and what their positions mean.
    if notice: print('Reading GOALS file...', end=' ')
    goals_file = os.path.join(path_pre, Inter.ConfigList.settings['Goals File Name'])
    data_files = Inter.DataFiles( goals_file, calc_csv )
    if notice: print('Complete!')

    #   'QuestData' uses the above information to interpret the Free Quest, Event, and
    # Monthly Ticket data, producing matrices that are used by 'Planner' and 'Output',
    # and giving 'RunCaps' tkey information.
    if notice: print('Reading Quest data .csv files...', end=' ')
    quest_data = QuestData( data_files )
    quest_data.multi_event( run_caps )
    quest_data.add_free_drops( apd_csv, run_caps )
    quest_data.read_monthly_ticket_list( run_caps )
    if notice: print('Complete!')
    
    # 'RunCaps' puts its namesake into a form that can be read by 'Planner'.
    if notice: print('Creating Run Cap Matrix...', end=' ')
    run_cap_matrix = run_caps.build_run_cap_matrix()
    if notice: print('Complete!')
    
    #  'Planner' produces a 'Solution' using matrices from 'QuestData', the interpreted
    # 'Goals' from DataFiles (as well as Mat naming information), and the Run Cap Matrices
    if data_files.goals.size > 0 and data_files.goals_total > 0:
        plan = Plan.Planner( quest_data, data_files, run_cap_matrix )
        solution = plan.planner()

        #  'Output' writes a report using the above 'Solution', pointer information from
        # 'QuestData', and all the information that's been sent to 'Debug' in the background.
        Plan.Output().print_out( solution, quest_data )
    else:
        Inter.Debug().warning('Goals were not properly read.')
        Plan.Output().create_debug_report()

if Inter.ConfigList().settings['Debug on Fail']:
    try:
        main()
    except:
        Plan.Output().create_debug_report()
else:
    main()