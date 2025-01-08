import csv
import glob
import numpy as np
from datetime import datetime, timedelta
import d_Interpret as Inter

class QuestData:
    def __init__( self, folder = 'Events Farm\\' ):
        self.folder = folder

        self.quest_names = []
        self.AP_costs = []
        self.drop_matrix = np.array([])

        self.runs_per_box = []
        self.hellfire_range = [9700000,500]

        self.remove_zeros = Inter.ConfigList.settings['Remove Zeros']
        self.tg_cut_AP = Inter.ConfigList.tg_cut_AP
        #self.last_area = Inter.ConfigList.settings['Stop Here']

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

    def prepare_data( self, matrix, name, AP_cost, drop_data, rbox = 'F' ):
        self.quest_names.append( name )
        matrix['AP Cost'].append( [AP_cost] )
        matrix['Drop'].append( drop_data )

        self.runs_per_box.append(rbox)
        return matrix
    
    def find_data_columns( self, reader ):
        data_col = {'ID':[], 'drop':[], 'rbox':176}

        while data_col['ID'] == []:
            try:
                event_node = next(reader)
            except StopIteration:
                Inter.Debug().warning( 'Sheet does not have columns labeled "ID".' )

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
    
    def find_event_name( self, csv_line ):
        fluff_to_remove = ['FGO Efficiency ',
                            self.folder]
        
        for i in fluff_to_remove:
            if csv_line.find(i) >= 0:
                start = csv_line.rfind(i)+len(i)
                break

        fluff_to_remove = [' - Event', '.csv']
        for i in fluff_to_remove:
            if csv_line.rfind(i) >= 0:
                end = csv_line.rfind(i)
                break

        return csv_line[start:end]
    
    def add_event_line( self, csv_line, data_col, mat_index_total, ID_to_index, monthly = False ):
        event_drop_add = np.zeros( mat_index_total )

        # If 0s are meant to be removed, only add data if desired Materials are dropped
        add_data = True - self.remove_zeros

        for i in range(len(data_col['ID'])):
            if csv_line[data_col['drop'][i]] != '':
                mat_ID = int(csv_line[ data_col['ID'][i] ])

                # Skips adding Material if it has no assigned index
                if ID_to_index[mat_ID] == 'F':
                    continue

                drop_rate = 1
                if monthly == False:
                    drop_rate = float(csv_line[ data_col['drop'][i] ]) / 100

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
    
    def main_body( self, reader, matrix, group, quest, data_col, mat_i_tot, ID_to_index, run_caps, debug ):
        event_lotto = False
        AP_Buyback = False
        last_area = Inter.ConfigList.settings['Stop Here']
        skip_data_index = {}

        for csv_line in reader:
            try:
                if group['Type'] == 'Monthly':
                    # Skips adding line if no Material or if Mat has no assigned index, so it's meant be skipped
                    if ID_to_index[ int(csv_line[ data_col['ID'][0] ]) ] == 'F':
                        continue
                elif group['Quest'] == 'Free Quests':
                    if csv_line[0].find( last_area ) >= 0: 
                        break

                    AP_normal = int(csv_line[2])
                    cur_type = csv_line[3]
                else:
                    AP_cost = float(csv_line[ data_col['AP'] ])

                    if csv_line[ data_col['ID'][0] ] == '':
                        continue
            except ValueError:
                continue

            if group['Type'] == 'Monthly':
                name = quest
                rbox = 'F'

                # data_col addon necessary to avoid error in add_event_line. Made to save lines.
                data_col['drop'] = [ data_col['ID'][0] ]
                AP_cost = 0
                cur_type = 'Monthly'

            elif group['Quest'] == 'Free Quests':
                name = csv_line[0] + ', ' + csv_line[1]
                rbox = 'F'

                drop_data = []
                AP_cost = AP_normal

                # Drop rate calculated from normal quest AP.
                # Half AP effectively doubles drop rate when optimizing run counts.
                if cur_type == 'Daily' and self.tg_cut_AP > 1:
                    AP_cost = int( AP_cost / self.tg_cut_AP )

                add_data = True - self.remove_zeros

                for i in range(data_col['Start'],data_col['Blaze']):
                    if not skip_data_index[i-data_col['Start']]:
                        try:
                            drop_data.append( AP_normal / float(csv_line[i]) )
                            add_data = True
                        except ValueError:
                            drop_data.append(0)

                if not skip_data_index[i-data_col['Start']]:
                    XP_mult = 1
                    for i in range(data_col['Blaze'],data_col['End']):
                        # Assumes Hellfires are about 6 columns after "Saber Blaze."
                        if i == data_col['Blaze'] + 6:
                            XP_mult = 3

                        try:
                            drop_data[-1] += XP_mult * AP_normal / float(csv_line[i])
                            add_data = True
                        except ValueError:
                            drop_data[-1] += 0
            else:
                name = quest + ', ' + csv_line[ data_col['loc'] ]
                cur_type = csv_line[ data_col['type'] ]

                try:
                    rbox = float(csv_line[ data_col['rbox'] ])
                    lotto_check = csv_line[ data_col['type'] ][0:5]

                    if lotto_check == 'Lotto':
                        event_lotto = True
                        debug.add_lotto_drop_bonus( name, csv_line[ data_col['lotto'] ])
                    else:
                        if lotto_check == 'Pseud':
                            debug.add_lotto_drop_bonus( name, csv_line[ data_col['lotto'] ])
                        rbox = 'F'
                except ValueError:
                    rbox = 'F'

            drop_data, add_data = self.add_event_line( csv_line, data_col, mat_i_tot, ID_to_index, group['Type'] )

            # Check if current Quest is part of the same group as the last, change Run Cap data accordingly
            group = run_caps.add_group_info( add_data, cur_type, group )

            if add_data:
                matrix = self.prepare_data( matrix, name, AP_cost, drop_data, rbox )
        
        # Event Lotto has its own logic check just in case more Types creep into the data at the end.
        if event_lotto and AP_Buyback:
            debug.note_event_list(' , AP Buyback was on', 1)

        #run_caps.assemble_group_info( group, caps )
        run_caps.assemble_group_info( group )
        self.assemble_matrix( matrix )



    def add_event_drop( self, event_csv, run_caps: Inter.RunCaps, ID_to_index, mat_index_total ):
        debug = Inter.Debug()
        event_name = self.find_event_name(event_csv)
        debug.note_event_list( event_name, 0, 2 )
        debug.add_runcap_debug( event_name, 0, 6 )

        with open( event_csv, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            csv_line = next(reader)

            event_true_name = csv_line[2]
            event_caps = run_caps.determine_event_caps(csv_line)

            AP_Buyback = False
            for i in range(len(csv_line)):
                if csv_line[i].find('Buyback') >= 0:
                    if csv_line[i+1] != '':
                        AP_Buyback = True
                    break

            data_col, reader = self.find_data_columns(reader)

            event_matrix = {'AP Cost': [], 'Drop': []}
            
            # Keeps track of Event groups to properly apply Run Caps ('Event', 'Raid', 'Lotto 2', etc).
            #quest_group = {'Quest': event_true_name, 'Type': False, 'Count': 0}
            quest_group = {'Quest': event_true_name, 'Type': False, 'Count': 0, 'Cap': event_caps}
            event_lotto = False

            # Interpretation of how this is supposed to read the Event Quest csv:
            # If there is no AP assigned or no material assigned in the first slot, skip this line.
            # If there is, assume the drops are part of a new node and start a new line of the Drop Matrix.
            # Add drops to the last line made in the Drop Matrix.
            for csv_line in reader:
                try:
                    AP_cost = float(csv_line[ data_col['AP'] ])

                    if csv_line[ data_col['ID'][0] ] == '':
                        continue
                except ValueError:
                    continue
                
                quest_name = event_name + ', ' + csv_line[ data_col['loc'] ]

                try:
                    rbox = float(csv_line[ data_col['rbox'] ])
                    lotto_check = csv_line[ data_col['type'] ][0:5]

                    if lotto_check == 'Lotto':
                        event_lotto = True
                        debug.add_lotto_drop_bonus( quest_name, csv_line[ data_col['lotto'] ])
                    else:
                        if lotto_check == 'Pseud':
                            debug.add_lotto_drop_bonus( quest_name, csv_line[ data_col['lotto'] ])
                        rbox = 'F'
                except ValueError:
                    rbox = 'F'

                drop_data, add_data = self.add_event_line( csv_line, data_col, mat_index_total, ID_to_index )

                # Check if current Quest is part of the same group as the last, change Run Cap data accordingly
                quest_group = run_caps.add_group_info( add_data, csv_line[ data_col['type'] ], 
                                                            #quest_group, event_caps )
                                                            quest_group )

                if add_data:
                    event_matrix = self.prepare_data( event_matrix, quest_name, AP_cost, drop_data, rbox )
            f.close()
            
            # Event Lotto has its own logic check just in case more Types creep into the data at the end.
            if event_lotto and AP_Buyback:
                debug.note_event_list(' , AP Buyback was on', 1)

            #run_caps.assemble_group_info( quest_group, event_caps )
            run_caps.assemble_group_info( quest_group )
            self.assemble_matrix( event_matrix )
    
    def multi_event( self, run_caps, ID_to_index, mat_index_total ):
        events_farm_folder = glob.glob( Inter.path_prefix + self.folder + '*' )

        for event in events_farm_folder:
            self.add_event_drop( event, run_caps, ID_to_index, mat_index_total )

    # Assumes first Material data point has a Header with "Bronze" in it, 
    #   and that "Saber Blaze" is 9 columns after the "Monuments"  start.
    # Now checks for "Blaze" and "Bond" headers, or uses the original list size to determine data end.
    def find_data_range( self, reader, csv_width ):
        mat_start = 0
        blaze_start = 0
        mat_end = 0

        while blaze_start == 0:
            try:
                free_drop = next(reader)
            except StopIteration:
                Inter.Debug().warning( 'Sheet does not have a column labeled as referencing "Bond".' )

            for i in range(len(free_drop)):  
                if free_drop[i].find('Bronze') >= 0:
                    mat_start = i
                if free_drop[i].find('Monument') >= 0:
                    blaze_start = i + 9
                if free_drop[i].find('Blaze') >= 0 or free_drop[i].find('XP') >= 0:
                    blaze_start = i + 1
                if free_drop[i].find('Bond') >= 0:
                    mat_end = i
                    break
            
            # Emergency if there is nothing labeled as referencing "Bond".
            if mat_start != 0:
                mat_end = csv_width + mat_start

        if mat_start == 0:
            Inter.Debug().warning( 'Sheet does not have a column labeled as referencing "Bronze" mats.' )
        if blaze_start == 0:
            Inter.Debug().warning( 'Sheet does not have a column labeled with "Monument" or "Blaze" mats.' )

        return reader, mat_start, blaze_start, mat_end
    
    def add_free_drop( self, free_csv, run_caps: Inter.RunCaps, skip_data_index, csv_width ):
        with open( free_csv, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            last_area = Inter.ConfigList.settings['Stop Here']

            reader, mat_start, blaze_start, mat_end = self.find_data_range( reader, csv_width )

            free_cap = Inter.RunCaps().set_config_caps(True)
            
            free_matrix = {'AP Cost': [], 'Drop': []}

            # Notes Quest groups to properly apply Run Caps, as well as Half AP.
            #quest_group = {'Quest': 'Free Quests', 'Type': False, 'Count': 0}
            quest_group = {'Quest': 'Free Quests', 'Type': False, 'Count': 0, 'Cap': free_cap}

            # Interpretation of how this is supposed to read the APD csv:
            # If the Singularity is further than the user wants to farm as defined in the config file, stop.
            # If the line is filler because the google sheet copied the old Japanese formatting, skip it.
            # Else, start a new line of drop rate data.
            for csv_line in reader:
                if csv_line[0].find( last_area ) >= 0: 
                    break

                try:
                    normal_quest_AP = int(csv_line[2])
                    quest_type = csv_line[3]
                except ValueError:
                    continue

                drop_data = []
                add_data = True - self.remove_zeros

                cur_quest_AP = normal_quest_AP

                # Drop rate calculated from normal quest AP.
                # Half AP effectively doubles drop rate when optimizing run counts.
                if quest_type == 'Daily' and self.tg_cut_AP > 1:
                    cur_quest_AP = int( normal_quest_AP / self.tg_cut_AP )

                for i in range(mat_start,blaze_start):
                    if not skip_data_index[i-mat_start]:
                        try:
                            drop_data.append( normal_quest_AP / float(csv_line[i]) )
                            add_data = True
                        except ValueError:
                            drop_data.append(0)

                if not skip_data_index[i-mat_start]:
                    XP_mult = 1
                    for i in range(blaze_start,mat_end):
                        # Assumes Hellfires are about 6 columns after "Saber Blaze."
                        if i == blaze_start + 6:
                            XP_mult = 3

                        try:
                            drop_data[-1] += XP_mult * normal_quest_AP / float(csv_line[i])
                            add_data = True
                        except ValueError:
                            drop_data[-1] += 0
                
                #quest_group = run_caps.add_group_info( add_data, quest_type, quest_group, free_cap )
                quest_group = run_caps.add_group_info( add_data, quest_type, quest_group )

                if add_data:
                    quest_name = csv_line[0] + ', ' + csv_line[1]
                    free_matrix = self.prepare_data( free_matrix, quest_name, cur_quest_AP, drop_data )
            f.close()
            
            #run_caps.assemble_group_info( quest_group, free_cap )
            run_caps.assemble_group_info( quest_group )
            self.assemble_matrix( free_matrix )
    
    def add_monthly_choices( self, ticket_csv, run_caps: Inter.RunCaps, ID_to_index, mat_index_total, 
                                   debug: Inter.Debug ):
        with open( ticket_csv, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            csv_line = next(reader)

            month = int(csv_line[1])
            year = int(csv_line[3])

            month_cap, month_name, error = Inter.ConfigList().check_date( month, year )

            if error:
                fluff = 'Data Files\\'
                csv_name = ticket_csv[( ticket_csv.rfind(fluff) + len(fluff) ):]
                debug.warning('Date could not be read in monthly .csv : ' + csv_name)
            
            if month_cap['Monthly'][0] > 0:
                data_col, reader = self.find_data_columns(reader)

                monthly_matrix = {'AP Cost': [], 'Drop': []}
                
                # Used for properly applying run caps to entire month.
                #month_group = {'Quest': month_name, 'Type': False, 'Count': 0}
                month_group = {'Quest': month_name, 'Type': 'Monthly', 'Count': 0, 'Cap': month_cap}

                # If there is no material assigned in the first slot, skip this line.
                # Add ticket choices as drops to the last made line in the Drop Matrix.
                for csv_line in reader:
                    # Skips adding line if no Material or if Material has no assigned index, so it's meant be skipped
                    try:
                        if ID_to_index[ int(csv_line[ data_col['ID'][0] ]) ] == 'F':
                            continue
                    except ValueError:
                        continue

                    # data_col addon necessary to avoid error in add_event_line. Made to save lines.
                    data_col['drop'] = [ data_col['ID'][0] ]
                    ticket_add, add_data = self.add_event_line( csv_line, data_col, mat_index_total, 
                                                               ID_to_index, True )

                    # Keeps count of the number of entries in the month and adds group data
                    month_group = run_caps.add_group_info( add_data, 'Monthly', month_group )
                    #month_group = run_caps.add_group_info( add_data, 'Monthly', month_group, month_cap )

                    if add_data:
                        monthly_matrix = self.prepare_data( monthly_matrix, month_name, 0, ticket_add )
                f.close()

                run_caps.assemble_group_info( month_group )
                #run_caps.assemble_group_info( month_group, month_cap )
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


    def read_monthly_ticket_list( self, run_caps, ID_to_index, mat_index_total ):
        ticket_mult = min( Inter.ConfigList.settings['Monthly Ticket Per Day'], 4)
        if ticket_mult > 0:
            debug = Inter.Debug()

            monthly_ticket_folder = glob.glob( Inter.path_prefix + 'Data Files\\*Monthly*\\*' )
            for month in monthly_ticket_folder:
                self.add_monthly_choices( month, run_caps, ID_to_index, mat_index_total, debug )
        
            debug.note_monthly_date_range( self.first_monthly, self.last_monthly )