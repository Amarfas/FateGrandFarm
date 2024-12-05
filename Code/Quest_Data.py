import csv
import glob
import numpy as np
from datetime import datetime, timedelta
import Interpret as Inter

class QuestData:
    def __init__( self ):
        self.quest_names = []
        self.AP_costs = []
        self.drop_matrix = np.array([])

        self.runs_per_box = []
        self.hellfire_range = [9700000,500]

        self.remove_zeros = Inter.ConfigList.remove_zeros
        self.run_int = Inter.ConfigList.run_int
        self.tg_half_AP = Inter.ConfigList.tg_half_AP
        self.last_area = Inter.ConfigList.last_area

        self.recorded_months = []
        self.first_monthly = {}
        self.last_monthly = {}

    def assemble_matrix( self, add_matrix ):
        if add_matrix['Drop'] != []:
            if np.size( self.drop_matrix ) == 0:
                self.AP_costs = np.array( add_matrix['AP Cost'] )
                self.drop_matrix = np.array( add_matrix['Drop'] )
            else:
                self.AP_costs = np.vstack(( self.AP_costs, add_matrix['AP Cost'] ))
                self.drop_matrix = np.vstack(( self.drop_matrix, add_matrix['Drop'] ))
    
    # quest_rpb = "runs per box" for the quest
    def add_box_run_info( self, is_lotto, quest_rpb = 0 ):
        if is_lotto:
            self.runs_per_box.append( float(quest_rpb) )
        else:
            self.runs_per_box.append( 'F' )
    
    def find_data_columns( self, reader ):
        data_col = {'ID':[], 'drop':[], 'rbox':176}

        while data_col['ID'] == []:
            try:
                event_node = next(reader)
            except StopIteration:
                Inter.Debug().error_warning( 'Sheet does not have columns labeled "ID".' )

            for i in range(len(event_node)):
                if event_node[i] == 'Location':
                    data_col.setdefault('loc',i)
                if event_node[i] == 'AP':
                    data_col.setdefault('AP',i)
                if event_node[i] == 'Type':
                    data_col.setdefault('type',i)
                if event_node[i] == 'Lotto':
                    data_col.setdefault('lotto',i)
                if event_node[i] == 'R/Box':
                    data_col['rbox'] = i

                # Multiple Material IDs and their corresponding drops.
                if event_node[i] == 'ID': 
                    data_col['ID'].append(i)
                if event_node[i] == 'Drop%':
                    data_col['drop'].append(i)
        
        return data_col, reader
    
    def find_event_name( self, event_drop_CSV ):
        fluff_to_remove = ['FGO Efficiency ',
                        'Events Farm' + '\\']
        
        for i in fluff_to_remove:
            if event_drop_CSV.find(i) >= 0:
                start = event_drop_CSV.rfind(i)+len(i)
                break

        fluff_to_remove = [' - Event', '.csv']
        for i in fluff_to_remove:
            if event_drop_CSV.rfind(i) >= 0:
                end = event_drop_CSV.rfind(i)
                break

        return event_drop_CSV[start:end]
    
    def add_event_line( self, event_quest, data_indices, drop_index_count, ID_to_index, is_normal = True ):
        event_drop_add = np.zeros( drop_index_count )

        # If 0s are meant to be removed, only add data if desired Materials are dropped
        add_data = True - self.remove_zeros

        for i in range(len(data_indices['ID'])):
            if event_quest[data_indices['drop'][i]] != '':
                mat_ID = int(event_quest[ data_indices['ID'][i] ])

                # Skips adding Material if it has no assigned index
                if ID_to_index[mat_ID] == 'F':
                    continue

                drop_rate = 1
                if is_normal:
                    drop_rate = float(event_quest[ data_indices['drop'][i] ]) / 100

                # Determines whether Material has one of the XP Hellfire IDs
                if mat_ID >= self.hellfire_range[0] and mat_ID % self.hellfire_range[1] == 0:
                    drop_rate *= 3

                # Allows certain negative IDs to input data for multiple Materials.
                if mat_ID < 0:
                    mat_ID = ID_to_index[mat_ID]
                else:
                    mat_ID = [mat_ID]

                for j in mat_ID:
                    add_data = True
                    event_drop_add[ ID_to_index[j] ] += drop_rate
        
        return event_drop_add, add_data

    def add_event_drop( self, event_drop_CSV, run_caps: Inter.RunCaps, ID_to_index, drop_index_count ):
        debug = Inter.Debug()
        event_name = self.find_event_name(event_drop_CSV)
        debug.note_event_list( event_name, 0, 2 )
        debug.add_runcap_debug( event_name, 0, 6 )

        with open( event_drop_CSV, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            event_quest = next(reader)

            event_true_name = event_quest[2]
            event_caps = run_caps.determine_event_caps(event_quest)

            AP_Buyback = False
            for i in range(len(event_quest)):
                if event_quest[i].find('Buyback') >= 0:
                    if event_quest[i+1] != '':
                        AP_Buyback = True
                    break

            data_col, reader = self.find_data_columns(reader)

            event_matrix = {'AP Cost': [], 'Drop': []}
            
            # Keeps track of Event groups to properly apply Run Caps ('Event', 'Raid', 'Lotto 2', etc).
            quest_group = {'Type': False, 'Count': 0}
            event_lotto = False

            # Interpretation of how this is supposed to read the Event Quest csv:
            # If there is no AP assigned or no material assigned in the first slot, skip this line.
            # If there is, assume the drops are part of a new node and start a new line of the Drop Matrix.
            # Add drops to the last line made in the Drop Matrix.
            for event_quest in reader:
                try:
                    quest_AP_cost = float(event_quest[ data_col['AP'] ])

                    if event_quest[ data_col['ID'][0] ] == '':
                        continue
                except ValueError:
                    continue
                
                quest_name = event_name + ', ' + event_quest[ data_col['loc'] ]

                if event_quest[ data_col['type'] ][0:5] == 'Lotto' and event_quest[ data_col['rbox'] ] != '':
                    is_lotto = True
                    event_lotto = True
                    debug.add_lotto_drop_bonus( quest_name, event_quest[ data_col['lotto'] ])
                else:
                    is_lotto = False

                event_drop_add, add_data = self.add_event_line( event_quest, data_col, drop_index_count, ID_to_index )

                # Check if current Quest is part of the same group as the last, change Run Cap data accordingly
                quest_group = run_caps.add_group_info( add_data, event_true_name, event_quest[ data_col['type'] ], 
                                                            quest_group, event_caps )

                if add_data:
                    self.quest_names.append( quest_name )
                    event_matrix['AP Cost'].append( [quest_AP_cost] )
                    event_matrix['Drop'].append( event_drop_add )

                    self.add_box_run_info( is_lotto, event_quest[ data_col['rbox'] ] )
            f.close()
            
            # Event Lotto has its own logic check just in case more Types creep into the data at the end.
            if event_lotto and AP_Buyback:
                debug.note_event_list(' , AP Buyback was on', 1)

            run_caps.assemble_group_info( event_true_name, quest_group, event_caps )
            self.assemble_matrix( event_matrix )
    
    def multi_event( self, run_caps, ID_to_index, drop_index_count ):
        events_farm_folder = glob.glob( Inter.path_prefix + 'Events Farm\\*' )

        for event in events_farm_folder:
            self.add_event_drop( event, run_caps, ID_to_index, drop_index_count )

    # Assumes first Material data point has a Header with "Bronze" in it, 
    #   and that "Saber Blaze" is 9 columns after the "Monuments"  start.
    # Now checks for "Blaze" and "Bond" headers, or uses the original list size to determine data end.
    def find_data_range( self, reader, list_size ):
        mat_start = 0
        blaze_start = 0
        mat_end = 0

        while blaze_start == 0:
            try:
                free_drop = next(reader)
            except StopIteration:
                Inter.Debug().error_warning( 'Sheet does not have a column labeled as referencing "Bond".' )

            for i in range(len(free_drop)):  
                if free_drop[i].find('Bronze') >= 0:
                    mat_start = i
                if free_drop[i].find('Monument') >= 0:
                    blaze_start = i+9
                if free_drop[i].find('Blaze') >= 0 or free_drop[i].find('XP') >= 0:
                    blaze_start = i+1
                if free_drop[i].find('Bond') >= 0:
                    mat_end = i
                    break
            
            # Emergency if there is nothing labeled as referencing "Bond".
            if mat_start != 0:
                mat_end = list_size + mat_start

        if mat_start == 0:
            Inter.Debug().error_warning( 'Sheet does not have a column labeled as referencing "Bronze" mats.' )
        if blaze_start == 0:
            Inter.Debug().error_warning( 'Sheet does not have a column labeled with "Monument" or "Blaze" mats.' )

        return reader, mat_start, blaze_start, mat_end
    
    def add_free_drop( self, free_drop_CSV, run_caps: Inter.RunCaps, skip_data_index, list_size ):
        with open( free_drop_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)

            reader, mat_start, blaze_start, mat_end = self.find_data_range( reader, list_size )

            free_cap = Inter.RunCaps().set_config_caps(True)
            
            free_matrix = {'AP Cost': [], 'Drop': []}

            # Notes Quest groups to properly apply Run Caps, as well as Half AP.
            quest_group = {'Type': False, 'Count': 0}

            # Interpretation of how this is supposed to read the APD csv:
            # If the Singularity is further than the user wants to farm as defined in the config file, stop.
            # If the line is filler because the google sheet copied the old Japanese formatting, skip it.
            # Else, start a new line of drop rate data.
            for free_drop in reader:
                if free_drop[0].find( self.last_area ) >= 0: 
                    break

                try:
                    normal_quest_AP = int(free_drop[2])
                except ValueError:
                    continue

                drop_matrix_add = []
                add_data = True - self.remove_zeros

                current_quest_AP = normal_quest_AP

                # Drop rate calculated from normal quest AP.
                # Half AP effectively doubles drop rate when optimizing run counts.
                if free_drop[3] == 'Daily' and self.tg_half_AP:
                    current_quest_AP = int(normal_quest_AP/2)

                for i in range(mat_start,blaze_start):
                    if not skip_data_index[i-mat_start]:
                        try:
                            drop_matrix_add.append( normal_quest_AP / float(free_drop[i]) )
                            add_data = True
                        except ValueError:
                            drop_matrix_add.append(0)

                if not skip_data_index[i-mat_start]:
                    XP_mult = 1
                    for i in range(blaze_start,mat_end):
                        # Assumes Hellfires are about 6 columns after "Saber Blaze."
                        if i == blaze_start + 6:
                            XP_mult = 3

                        try:
                            drop_matrix_add[-1] += XP_mult * normal_quest_AP / float(free_drop[i])
                            add_data = True
                        except ValueError:
                            drop_matrix_add[-1] += 0
                
                quest_group = run_caps.add_group_info( add_data, 'Free Quests', free_drop[3], quest_group, free_cap )

                if add_data:
                    self.quest_names.append( free_drop[0] + ', ' + free_drop[1] )
                    free_matrix['AP Cost'].append( [current_quest_AP] )
                    free_matrix['Drop'].append( drop_matrix_add )

                    self.add_box_run_info(False)
            f.close()
            
            run_caps.assemble_group_info( 'Free Quests', quest_group, free_cap )
            self.assemble_matrix( free_matrix )
    
    def add_monthly_ticket_choices( self, monthly_ticket_CSV, run_caps: Inter.RunCaps, ID_to_index, drop_index_count, 
                                   start_date: datetime, end_date: datetime, ticket_mult, debug: Inter.Debug ):

        with open( monthly_ticket_CSV, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            ticket_choices = next(reader)

            # Find if current month is within date range
            days_left = -1
            try:
                month = int(ticket_choices[1])
                year = int(ticket_choices[3])
                if year < 100:
                    year += 2000
                end_of_month = datetime(year + month // 12, month % 12 + 1, 1) - timedelta(seconds=1)
                
                after_start = (end_of_month - start_date).days > 0
                before_end = (end_date == '') or (datetime(year, month, 1) - end_date).days < 0

                # Find how many days to count tickets for
                if after_start and before_end:
                    if end_date != '' and month == end_date.month and year == end_date.year:
                        days_left = end_date.day
                    else:
                        days_left = end_of_month.day

                    if month == start_date.month and year == start_date.year:
                        days_left -= start_date.day

            except ValueError:
                fluff = 'Data Files\\'
                csv_name = monthly_ticket_CSV[( monthly_ticket_CSV.rfind(fluff) + len(fluff) ):]
                debug.error_warning('Date could not be read in monthly .csv : ' + csv_name)
            
            if days_left > 0:
                month_cap = { 'Monthly': [ticket_mult * days_left] }
                month_name = end_of_month.strftime('%b %Y')

                data_indices, reader = self.find_data_columns(reader)

                monthly_matrix = {'AP Cost': [], 'Drop': []}
                
                # Used for properly applying run caps to entire month.
                month_group = {'Type': False, 'Count': 0}

                # If there is no material assigned in the first slot, skip this line.
                # Add ticket choices as drops to the last made line in the Drop Matrix.
                for ticket_choices in reader:
                    # Skips adding line if no Material or if Material has no assigned index, so it's meant be skipped
                    try:
                        if ID_to_index[ int(ticket_choices[ data_indices['ID'][0] ]) ] == 'F':
                            continue
                    except ValueError:
                        continue

                    # data_indices addon necessary to avoid error in add_event_drop_line.
                    # add_event_drop_line made to save lines
                    data_indices['drop'] = [ data_indices['ID'][0] ]
                    ticket_add, add_data = self.add_event_line( ticket_choices, data_indices, drop_index_count, 
                                                               ID_to_index, False )

                    # Keeps count of the number of entries in the month and adds group data
                    month_group = run_caps.add_group_info( add_data, month_name, 'Monthly', month_group, month_cap )

                    if add_data:
                        self.quest_names.append( month_name )
                        monthly_matrix['AP Cost'].append( [0] )
                        monthly_matrix['Drop'].append( ticket_add )

                        self.add_box_run_info(False)
                f.close()

                run_caps.assemble_group_info( month_name, month_group, month_cap )
                self.assemble_matrix( monthly_matrix )
                self.recorded_months.append(month_name)

                first = self.first_monthly
                if first == {}:
                    self.first_monthly = {'Month': month, 'Year': year, 'Date': month_name}
                    self.last_monthly = {'Month': month, 'Year': year, 'Date': month_name}
                else:
                    if (year < first['Year']) or (year == first['Year'] and month < first['Month']):
                        self.first_monthly = {'Month': month, 'Year': year, 'Date': month_name}
                    else:
                        last = self.last_monthly
                        if (year > last['Year']) or (year == last['Year'] and month > last['Month']):
                            self.last_monthly = {'Month': month, 'Year': year, 'Date': month_name}


    def read_monthly_ticket_list( self, run_caps, ID_to_index, drop_index_count ):
        ticket_mult = min( Inter.ConfigList.monthly_ticket_num, 4)
        if ticket_mult > 0:
            debug = Inter.Debug()

            start = Inter.ConfigList.monthly_ticket_start
            start = datetime(start[2], start[0], start[1])

            end = Inter.ConfigList.monthly_ticket_end
            if end != '':
                end = datetime(end[2], end[0], end[1])

            monthly_ticket_folder = glob.glob( Inter.path_prefix + 'Data Files\\*Monthly*\\*' )
            for month in monthly_ticket_folder:
                self.add_monthly_ticket_choices( month, run_caps, ID_to_index, drop_index_count, 
                                                start, end, ticket_mult, debug )
        
            debug.note_monthly_date_range( self.first_monthly, self.last_monthly )