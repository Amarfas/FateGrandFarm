import os
import csv
import glob
import numpy as np
import Interpret as Inter

class QuestData:
    def __init__( self, data_files: Inter.DataFiles, folder = 'Events Farm' ):
        self.folder = folder
        self.add_data_ini = True - Inter.ConfigList.settings['Remove Zeros']

        # Event Quest and Monthly Ticket section
        self.ID_to_index = data_files.ID_to_index
        self.mat_index_total = data_files.mat_index_total

        # Free Quest section
        self.csv_col_total = data_files.csv_col_total
        self.skip_data_index = data_files.skip_data_index
        self.skip_data_shift = {}

        # Output data
        self.quest_names = []
        self.AP_costs = []
        self.drop_matrix = np.array([])

        self.runs_per_box = []
        self.hellfire_range = [9700000,500]

        # Date range for Monthly Tickets
        self.first_month = []
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

    def _add_data_row( self, matrix, name, AP_cost, drop_data, rbox = 'F' ):
        self.quest_names.append( name )
        matrix['AP Cost'].append( [AP_cost] )
        matrix['Drop'].append( drop_data )

        self.runs_per_box.append(rbox)
        return matrix
    
    
    # Event Data section
    def _find_data_columns( self, reader ):
        data_col = {'ID':[], 'drop':[], 'rbox':176}

        while data_col['ID'] == []:
            try:
                csv_line = next(reader)
            except StopIteration:
                Inter.Debug().warning( 'Sheet does not have columns labeled "ID".' )

            for i in range(len(csv_line)):
                if csv_line[i] == 'Location':
                    data_col.setdefault('loc',i)
                elif csv_line[i] == 'AP':
                    data_col.setdefault('AP',i)
                elif csv_line[i] == 'Type':
                    data_col.setdefault('type',i)
                elif csv_line[i] == 'Lotto':
                    data_col.setdefault('lotto',i)
                elif csv_line[i] == 'R/Box':
                    data_col['rbox'] = i

                # Multiple Material IDs and their corresponding drops.
                elif csv_line[i] == 'ID': 
                    data_col['ID'].append(i)
                elif csv_line[i] == 'Drop%':
                    data_col['drop'].append(i)
        
        return data_col, reader
    
    def _find_event_name( self, csv_line ):
        fluff_to_remove = ['FGO Efficiency',
                            self.folder]
        for i in fluff_to_remove:
            if csv_line.find(i) >= 0:
                start = csv_line.rfind(i) + len(i)
                break

        if csv_line[start] == '\\':
            start += 1

        fluff_to_remove = [' - Event', '.csv']
        for i in fluff_to_remove:
            if csv_line.rfind(i) >= 0:
                end = csv_line.rfind(i)
                break

        event_name = csv_line[start:end]
        debug = Inter.Debug()
        debug.note_event_list( event_name, 0, 2 )
        debug.add_runcap_debug( event_name, 0, 6 )

        return event_name
    
    def _read_event_row( self, csv_line, data_col ):
        event_drop_add = np.zeros( self.mat_index_total )
        ID_to_index = self.ID_to_index

        # If 0s are meant to be removed, only add data if desired Materials are dropped
        add_data = self.add_data_ini

        for i in range(len(data_col['ID'])):
            try:
                mat_ID = int(csv_line[ data_col['ID'][i] ])
                drop_rate = float(csv_line[ data_col['drop'][i] ]) / 100
            except ValueError:
                continue

            # Skips adding Material if it has no assigned index
            if ID_to_index[mat_ID] == 'F':
                continue

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
    
    # Interpretation of how this is supposed to read the Event Quest csv:
    # If there is no AP assigned or no material assigned in the first slot, skip this line.
    # If there is, assume the drops are part of a new node and start a new line of the Drop Matrix.
    # Add drops to the last line made in the Drop Matrix.
    def _read_event_data( self, reader, run_caps: Inter.RunCaps, matrix, group, event_name ):
        event_lotto = False
        data_col, reader = self._find_data_columns(reader)

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
                    Inter.Debug().add_lotto_drop_bonus( name, bonus )
                elif cur_type[0:5] == 'Pseud':
                    Inter.Debug().add_lotto_drop_bonus( name, bonus )
            except ValueError:
                pass

            drop_data, add_data = self._read_event_row( csv_line, data_col )

            # Check if current Quest is part of the same group as the last, change Run Cap data accordingly
            group = run_caps.add_group_info( add_data, cur_type, group )

            if add_data:
                self._add_data_row( matrix, name, AP_cost, drop_data, rbox )
        
        return group, event_lotto

    def _add_event_drops( self, event_csv, run_caps: Inter.RunCaps ):
        event_name = self._find_event_name(event_csv)

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
            
            # Keeps track of Event groups to properly apply Run Caps ('Event', 'Raid', 'Lotto 2', etc).
            group = {'Quest': event_true_name, 'Type': False, 'Count': 0, 'Cap': event_caps}

            matrix = {'AP Cost': [], 'Drop': []}

            group, event_lotto = self._read_event_data( reader, run_caps, matrix, group, event_name )
            f.close()
            
        # Event Lotto has its own logic check just in case more Types creep into the data at the end.
        if event_lotto and AP_buyback:
            Inter.Debug().note_event_list(' , AP Buyback was on', 1)

        run_caps.assemble_group_info( group )
        self.assemble_matrix( matrix )
    
    def multi_event( self, run_caps ):
        file_path = os.path.join( Inter.path_prefix, self.folder, '**', '*.csv' )
        events_farm_folder = glob.glob( file_path, recursive=True )

        for event in events_farm_folder:
            self._add_event_drops( event, run_caps )


    # Free Data section
    def _set_free_columns( self, mat_start, blaze_start, mat_end ):
        if mat_start == -1:
            error = 'Sheet does not have a column labeled as referencing "Bronze" mats.'
            Inter.Debug().warning(error)
        
        if blaze_start == -1:
            blaze_start = mat_end
            error = 'Sheet does not have a column labeled with "Monument" or "Blaze".'
            Inter.Debug().warning(error)

        # Might make the program faster to not have to repeat these calculations
        for key in self.skip_data_index:
            self.skip_data_shift[ key + mat_start ] = self.skip_data_index[key]
        
        self.start_to_blaze = range( mat_start, blaze_start )
        self.blaze_to_end = range( blaze_start, mat_end )
        self.hellfire_start = blaze_start + 6

    # Assumes first Material data point has a Header with "Bronze" in it, 
    #   and that "Saber Blaze" is 9 columns after the "Monuments"  start.
    # Now checks for "Blaze" and "Bond" headers.
    def _find_free_columns( self, reader ):
        mat_start = -1
        blaze_start = -1

        while blaze_start == -1:
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
            # Uses the original calc.csv list size to determine data end.
            if mat_start >= -1:
                mat_end = self.csv_col_total + mat_start

        self._set_free_columns( mat_start, blaze_start, mat_end )
        return reader
    
    def _read_free_row( self, csv_line, AP_cost ):
        drop_data = []
        add_data = self.add_data_ini

        for i in self.start_to_blaze:
            if not self.skip_data_shift[i]:
                try:
                    drop_data.append( AP_cost / float(csv_line[i]) )
                    add_data = True
                except ValueError:
                    drop_data.append(0)

        if not self.skip_data_shift[i]:
            XP_mult = 1
            for i in self.blaze_to_end:
                # Assumes Hellfires are about 6 columns after "Saber Blaze."
                if i == self.hellfire_start:
                    XP_mult = 3

                try:
                    drop_data[-1] += XP_mult * AP_cost / float(csv_line[i])
                    add_data = True
                except ValueError:
                    pass

        return drop_data, add_data
    
    # Interpretation of how this is supposed to read the APD csv:
    # If the Singularity is further than the user wants to farm as defined in the config file, stop.
    # If the line is filler because the google sheet copied the old Japanese formatting, skip it.
    # Else, start a new line of drop rate data.
    def _read_free_data( self, reader, run_caps: Inter.RunCaps, matrix, group ):
        cut_AP = Inter.ConfigList.cut_AP
        last_area = Inter.ConfigList.settings['Stop Here']

        for csv_line in reader:
            region = csv_line[0]
            if region.startswith('Arch.'):
                region = 'Archetype Inception'
            
            if region.find( last_area ) >= 0: 
                break

            try:
                AP_cost = int(csv_line[2])
                cur_type = csv_line[3]
            except ValueError:
                continue

            drop_data, add_data = self._read_free_row( csv_line, AP_cost )
            
            group = run_caps.add_group_info( add_data, cur_type, group )

            # Drop rate calculated from normal quest AP.
            # Half AP effectively doubles drop rate when optimizing run counts.
            # After the rest of the calculations in order to not cancel out the gain.
            if cur_type == 'Daily' or cur_type == 'Bleach':
                if cut_AP[cur_type] > 1:
                    AP_cost = int( AP_cost / cut_AP[cur_type] )

            if add_data:
                quest_name = region + ', ' + csv_line[1]
                self._add_data_row( matrix, quest_name, AP_cost, drop_data )
        return group
    
    def add_free_drops( self, free_csv, run_caps: Inter.RunCaps ):
        with open( free_csv, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            #cut_AP = Inter.ConfigList.cut_AP
            #last_area = Inter.ConfigList.settings['Stop Here']

            reader = self._find_free_columns(reader)

            free_cap = Inter.RunCaps().set_config_caps(True)

            # Notes Quest groups to properly apply Run Caps, as well as Half AP.
            group = {'Quest': 'Free Quests', 'Type': False, 'Count': 0, 'Cap': free_cap}
            matrix = {'AP Cost': [], 'Drop': []}

            group = self._read_free_data( reader, run_caps, matrix, group )
            f.close()

        run_caps.assemble_group_info( group )
        self.assemble_matrix( matrix )
    

    # Monthly Ticket Data section
    def _find_ticket_range( self, month_name, month, year ):
        self.first_month.append(month_name)

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

    def _find_month_ID( self, reader, month_name ):
        while True:
            try:
                csv_line = next(reader)
            except StopIteration:
                error = 'Monthly ' + month_name + ' sheet does not have a column labeled "ID".'
                Inter.Debug().warning( error )
                return 2, reader

            for i in range(len(csv_line)):
                if csv_line[i] == 'ID': 
                    return i, reader
    
    def _add_ticket_choice( self, mat_ID ):
        event_drop_add = np.zeros( self.mat_index_total )

        # If 0s are meant to be removed, only add data if desired Materials are dropped
        index = self.ID_to_index[mat_ID]
        if index == 'F':
            return event_drop_add, self.add_data_ini

        # Determines whether Material has one of the XP Hellfire IDs
        drop_rate = 1
        if mat_ID >= self.hellfire_range[0] and mat_ID % self.hellfire_range[1] == 0:
            drop_rate *= 3

        event_drop_add[ index ] = drop_rate
        return event_drop_add, True

    def _add_monthly_choices( self, reader, data_col_ID, group, run_caps:Inter.RunCaps ):
        matrix = {'AP Cost': [], 'Drop': []}

        # If there is no material assigned in the first slot, skip this line.
        # Add ticket choices as drops to the last made line in the Drop Matrix.
        for csv_line in reader:
            try:
                # Skips adding line if no Material or if Mat has no assigned index, 
                #   so it's meant be skipped
                mat_ID = int(csv_line[ data_col_ID ])
            except ValueError:
                continue

            drop_data, add_data = self._add_ticket_choice( mat_ID )

            # Keeps count of the number of entries in the month and adds group data
            group = run_caps.add_group_info( add_data, 'Monthly', group )

            if add_data:
                self._add_data_row( matrix, group['Quest'], 0, drop_data )

        run_caps.assemble_group_info( group )
        self.assemble_matrix( matrix )
    
    def _check_month( self, ticket_csv, run_caps: Inter.RunCaps ):
        with open( ticket_csv, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            csv_line = next(reader)

            month = int(csv_line[1])
            year = int(csv_line[3])

            month_cap, month_name, error = Inter.ConfigList().check_date( month, year )

            if error:
                csv_name = ticket_csv[ticket_csv.rfind('y20'):]
                if csv_name == -1:
                    csv_name = ticket_csv[ticket_csv.rfind('Monthly'):]
                Inter.Debug().warning('Date could not be read in monthly .csv : ' + csv_name)
            
            if month_cap['Monthly'][0] > 0:
                # Used for properly applying run caps to entire month.
                group = {'Quest': month_name, 'Type': 'Monthly',
                         'Count': 0, 'Cap': month_cap}

                data_col_ID, reader = self._find_month_ID( reader, month_name )

                self._add_monthly_choices( reader, data_col_ID, group, run_caps )

                self._find_ticket_range( month_name, month, year )
            f.close()

    def read_monthly_ticket_list( self, run_caps ):
        ticket_mult = min( Inter.ConfigList.settings['Monthly Ticket Per Day'], 4)

        if ticket_mult > 0:
            file_path = os.path.join( Inter.path_prefix, 'Data Files', '*Monthly*', '*' )
            monthly_ticket_folder = glob.glob( file_path )

            for month in monthly_ticket_folder:
                self._check_month( month, run_caps )
        
            Inter.Debug().note_monthly_date_range( self.first_monthly, self.last_monthly )