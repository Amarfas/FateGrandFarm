import csv
import glob
import numpy as np
import Interpret as Inter

class QuestData:
    def __init__( self, data_files: Inter.DataFiles, folder = 'Events Farm\\' ):
        self.folder = folder
        self.ID_to_index = data_files.ID_to_index
        self.mat_index_total = data_files.mat_index_total
        self.remove_zeros = Inter.ConfigList.settings['Remove Zeros']

        self.quest_names = []
        self.AP_costs = []
        self.drop_matrix = np.array([])

        self.runs_per_box = []
        self.hellfire_range = [9700000,500]

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
                elif event_node[i] == 'AP':
                    data_col.setdefault('AP',i)
                elif event_node[i] == 'Type':
                    data_col.setdefault('type',i)
                elif event_node[i] == 'Lotto':
                    data_col.setdefault('lotto',i)
                elif event_node[i] == 'R/Box':
                    data_col['rbox'] = i

                # Multiple Material IDs and their corresponding drops.
                elif event_node[i] == 'ID': 
                    data_col['ID'].append(i)
                elif event_node[i] == 'Drop%':
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
    
    #def add_event_line( self, csv_line, data_col, mat_index_total, ID_to_index, monthly = False ):
    def add_event_line( self, csv_line, data_col, monthly = False ):
        event_drop_add = np.zeros( self.mat_index_total )
        ID_to_index = self.ID_to_index

        # If 0s are meant to be removed, only add data if desired Materials are dropped
        add_data = True - self.remove_zeros

        for i in range(len(data_col['ID'])):
            if csv_line[data_col['drop'][i]] != '':
                mat_ID = int(csv_line[ data_col['ID'][i] ])

                # Skips adding Material if it has no assigned index
                if ID_to_index[mat_ID] == 'F':
                #if self.ID_to_index[mat_ID] == 'F':
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
                    #mat_ID = self.ID_to_index[mat_ID]
                else:
                    mat_ID = [mat_ID]

                for j in mat_ID:
                    add_data = True
                    event_drop_add[ ID_to_index[j] ] += drop_rate
                    #event_drop_add[ self.ID_to_index[j] ] += drop_rate
        
        return event_drop_add, add_data

    def add_event_drop( self, event_csv, run_caps: Inter.RunCaps, ID_to_index, mat_index_total ):
        debug = Inter.Debug()
        event_name = self.find_event_name(event_csv)
        debug.note_event_list( event_name, 0, 2 )
        debug._add_runcap_debug( event_name, 0, 6 )

        with open( event_csv, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            csv_line = next(reader)

            event_true_name = csv_line[2]
            event_caps = run_caps.determine_event_caps(csv_line)

            AP_buyback = False
            for i in range(len(csv_line)):
                if csv_line[i].find('Buyback') >= 0:
                    if csv_line[i+1] != '':
                        AP_buyback = True
                    break

            data_col, reader = self.find_data_columns(reader)
            
            # Keeps track of Event groups to properly apply Run Caps ('Event', 'Raid', 'Lotto 2', etc).
            group = {'Quest': event_true_name, 'Type': False, 'Count': 0, 'Cap': event_caps}

            matrix = {'AP Cost': [], 'Drop': []}
            event_lotto = False

            # Interpretation of how this is supposed to read the Event Quest csv:
            # If there is no AP assigned or no material assigned in the first slot, skip this line.
            # If there is, assume the drops are part of a new node and start a new line of the Drop Matrix.
            # Add drops to the last line made in the Drop Matrix.
            for csv_line in reader:
                try:
                    first_ID_check = int( csv_line[ data_col['ID'][0] ] )
                    AP_cost = float(csv_line[ data_col['AP'] ])

                except ValueError:
                    continue

                name = event_name + ', ' + csv_line[ data_col['loc'] ]
                cur_type = csv_line[ data_col['type'] ]

                rbox = 'F'
                try:
                    rbox_read = float(csv_line[ data_col['rbox'] ])
                    bonus = csv_line[ data_col['lotto'] ]

                    if cur_type[0:5] == 'Lotto':
                        event_lotto = True
                        rbox = rbox_read
                        debug.add_lotto_drop_bonus( name, bonus )
                    elif cur_type[0:5] == 'Pseud':
                        debug.add_lotto_drop_bonus( name, bonus )
                except ValueError:
                    pass

                #drop_data, add_data = self.add_event_line( csv_line, data_col, ID_to_index )
                drop_data, add_data = self.add_event_line( csv_line, data_col )


                # Check if current Quest is part of the same group as the last, change Run Cap data accordingly
                group = run_caps.add_group_info( add_data, cur_type, group )

                if add_data:
                    matrix = self.prepare_data( matrix, name, AP_cost, drop_data, rbox )
            f.close()
            
        # Event Lotto has its own logic check just in case more Types creep into the data at the end.
        if event_lotto and AP_buyback:
            Inter.Debug().note_event_list(' , AP Buyback was on', 1)

        run_caps.assemble_group_info( group )
        self.assemble_matrix( matrix )
    
    def multi_event( self, run_caps, ID_to_index, mat_index_total ):
        events_farm_folder = glob.glob( Inter.path_prefix + self.folder + '*' )

        for event in events_farm_folder:
            self.add_event_drop( event, run_caps, ID_to_index, mat_index_total )
    
    def add_free_drop( self, free_csv, run_caps: Inter.RunCaps ):
        with open( free_csv, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            tg_cut_AP = Inter.ConfigList.tg_cut_AP
            last_area = Inter.ConfigList.settings['Stop Here']

            free_read = Inter.FreeReader()
            reader = free_read.find_data_columns(reader)

            free_cap = Inter.RunCaps().set_config_caps(True)

            # Notes Quest groups to properly apply Run Caps, as well as Half AP.
            group = {'Quest': 'Free Quests', 'Type': False, 'Count': 0, 'Cap': free_cap}
            matrix = {'AP Cost': [], 'Drop': []}

            # Interpretation of how this is supposed to read the APD csv:
            # If the Singularity is further than the user wants to farm as defined in the config file, stop.
            # If the line is filler because the google sheet copied the old Japanese formatting, skip it.
            # Else, start a new line of drop rate data.
            for csv_line in reader:
                free_read.csv_line = csv_line
                if csv_line[0].find( last_area ) >= 0: 
                    break

                try:
                    AP_cost = int(csv_line[2])
                    cur_type = csv_line[3]
                except ValueError:
                    continue

                drop_data, add_data = free_read.add_drop_line( AP_cost )
                
                group = run_caps.add_group_info( add_data, cur_type, group )

                # Drop rate calculated from normal quest AP.
                # Half AP effectively doubles drop rate when optimizing run counts.
                # After the rest of the calculations in order to not cancel out the gain.
                if cur_type == 'Daily' and tg_cut_AP > 1:
                    AP_cost = int( AP_cost / tg_cut_AP )

                if add_data:
                    quest_name = csv_line[0] + ', ' + csv_line[1]
                    matrix = self.prepare_data( matrix, quest_name, AP_cost, drop_data )
            f.close()

        run_caps.assemble_group_info( group )
        self.assemble_matrix( matrix )

    def _find_ticket_range( self, month_name, month, year ):
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

    def _add_monthly_choices( self, reader, group, run_caps: Inter.RunCaps, ID_to_index, mat_index_total ):
        #month_read = Inter.EventReader()
        #reader = month_read.find_data_columns(reader)
        data_col, reader = self.find_data_columns(reader)
        
        matrix = {'AP Cost': [], 'Drop': []}

        # If there is no material assigned in the first slot, skip this line.
        # Add ticket choices as drops to the last made line in the Drop Matrix.
        for csv_line in reader:
            #month_read.read_csv_line( csv_line )
            #month_read.csv_line = csv_line                
            try:
                # Skips adding line if no Material or if Mat has no assigned index, 
                #   so it's meant be skipped
                #if (month_read.ID_to_index[ int(month_read.read_col_mat('ID', 0)) ] == 'F'):
                #if (ID_to_index[ int(csv_line[ data_col['ID'][0] ]) ] == 'F'):
                if (self.ID_to_index[ int(csv_line[ data_col['ID'][0] ]) ] == 'F'):
                    continue
            
            except ValueError:
                continue

            # data_col addon necessary to avoid error in add_event_line. Made to save lines.
            data_col['drop'] = [ data_col['ID'][0] ]
            #month_read.data_col['drop'] = [ month_read.data_col['ID'][0] ]
            #month_read.read_csv['drop'] = [ month_read.read_csv['ID'][0] ]
            #drop_data, add_data = month_read.add_drop_line('Monthly')
            drop_data, add_data = self.add_event_line( csv_line, data_col, mat_index_total,
                                                      ID_to_index, 'Monthly' )

            # Keeps count of the number of entries in the month and adds group data
            group = run_caps.add_group_info( add_data, 'Monthly', group )

            if add_data:
                matrix = self.prepare_data( matrix, group['Quest'], 0, drop_data )

        run_caps.assemble_group_info( group )
        self.assemble_matrix( matrix )
    
    def _check_month( self, ticket_csv, run_caps: Inter.RunCaps, ID_to_index, mat_index_total ):
        with open( ticket_csv, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            csv_line = next(reader)

            month = int(csv_line[1])
            year = int(csv_line[3])

            month_cap, month_name, error = Inter.ConfigList().check_date( month, year )

            if error:
                fluff = 'Data Files\\'
                csv_name = ticket_csv[( ticket_csv.rfind(fluff) + len(fluff) ):]
                Inter.Debug().warning('Date could not be read in monthly .csv : ' + csv_name)
            
            if month_cap['Monthly'][0] > 0:
                # Used for properly applying run caps to entire month.
                group = {'Quest': month_name, 'Type': 'Monthly', 'Count': 0, 'Cap': month_cap}
                month_read = Inter.MonthReader()
                reader = month_read.find_data_columns(reader)

                matrix, qn, rpb = month_read.add_monthly_choices( reader, group, run_caps, 
                                                                self.quest_names, self.runs_per_box )

                self.quest_names = qn
                self.runs_per_box = rpb
                self.assemble_matrix( matrix )
                #self._add_monthly_choices( reader, group, run_caps, ID_to_index, mat_index_total )

                self._find_ticket_range( month_name, month, year )
            f.close()

    def read_monthly_ticket_list( self, run_caps, ID_to_index, mat_index_total ):
        ticket_mult = min( Inter.ConfigList.settings['Monthly Ticket Per Day'], 4)
        if ticket_mult > 0:

            monthly_ticket_folder = glob.glob( Inter.path_prefix + 'Data Files\\*Monthly*\\*' )
            for month in monthly_ticket_folder:
                self._check_month( month, run_caps, ID_to_index, mat_index_total )
        
            Inter.Debug().note_monthly_date_range( self.first_monthly, self.last_monthly )