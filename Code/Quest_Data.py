import csv
import glob
import numpy as np
import Interpret as Inter

class QuestData:
    def __init__( self ):
        self.quest_names = []
        self.AP_costs = []
        self.drop_matrix = np.array([])

        self.runs_per_box = []

        self.hellfire_range = [9700000,500]

        self.remove_zeros = Inter.ConfigList.remove_zeros
        self.tg_half_AP = Inter.ConfigList.tg_half_AP
        self.last_area = Inter.ConfigList.last_area


    # There are some issues with this method of assembling matrices.
    # The basic issue is that cvxpy analysis requires data in the form of numpy matrices, but the best way to form numpy matrices is to initialize its size.
    # This is because vstacking numpy matrices line by line is slow, because it rewrites the entire matrix every time.
    # Unfortunately, in order to initialize the size, we have to know how many lines the csv is. This apparently requires reading through the entire csv once.
    # Since the csv's have to be read and added to the data line by line, this would be inelegant/slow.
    # For the above reasons, I have instead opted to put the data from the csv into an array first, and then turn those arrays into a numpy matrix before stacking.
    def assemble_matrix( self, add_AP_cost, add_drop_matrix ):
            if add_drop_matrix != []:
                if np.size( self.drop_matrix ) == 0:
                    self.AP_costs = np.array( add_AP_cost )
                    self.drop_matrix = np.array( add_drop_matrix )
                else:
                    self.AP_costs = np.vstack(( self.AP_costs, add_AP_cost ))
                    self.drop_matrix = np.vstack(( self.drop_matrix, add_drop_matrix ))
    
    def add_box_run_info( self, is_lotto, quest_rpb = 0 ):
        if is_lotto:
            self.runs_per_box.append( float(quest_rpb) )
        else:
            self.runs_per_box.append( 'F' )
    
    def find_data_indices( self, reader ):
        data_indices = {'ID':[], 'drop':[], 'rbox':176}

        while data_indices['ID'] == []:
            try:
                event_node = next(reader)
            except StopIteration:
                Inter.Debug().error_warning( 'Sheet does not have columns labeled "ID".' )

            for i in range(len(event_node)):
                if event_node[i] == 'Location':
                    data_indices.setdefault('loc',i)
                if event_node[i] == 'AP':
                    data_indices.setdefault('AP',i)
                if event_node[i] == 'Type':
                    data_indices.setdefault('type',i)
                if event_node[i] == 'Lotto':
                    data_indices.setdefault('lotto',i)
                if event_node[i] == 'R/Box':
                    data_indices['rbox'] = i

                # Multiple Material IDs and their corresponding drops.
                if event_node[i] == 'ID': 
                    data_indices['ID'].append(i)
                if event_node[i] == 'Drop%':
                    data_indices['drop'].append(i)
        
        return data_indices, reader
    
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

    def add_event_drop( self, event_drop_CSV, run_caps: Inter.RunCaps, ID_to_index, drop_index_count ):
        debug = Inter.Debug()
        event_name = self.find_event_name(event_drop_CSV)
        debug.note_event_list( event_name )
        debug.add_debug( event_name, 0, 5 )

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

            data_indices, reader = self.find_data_indices(reader)

            event_AP_cost = []
            event_drop_matrix = []
            
            # Notes Event groups to properly apply Run Caps.
            quest_group = False
            member_count = 0
            event_lotto = False

            # Interpretation of how this is supposed to read the Event Quest csv:
            # If there is no AP assigned or no material assigned in the first slot, skip this line.
            # If there is an AP assigned, assume the drops are part of a new node and start a new line of the Drop Matrix.
            # Add drops to the last made line in the Drop Matrix.
            for event_quest in reader:
                try:
                    quest_AP_cost = float(event_quest[ data_indices['AP'] ])

                    if event_quest[ data_indices['ID'][0] ] == '':
                        continue
                except ValueError:
                    continue
                
                quest_name = event_name + ', ' + event_quest[ data_indices['loc'] ]

                if event_quest[ data_indices['type'] ][0:5] == 'Lotto' and event_quest[ data_indices['rbox'] ] != '':
                    is_lotto = True
                    event_lotto = True
                    debug.add_lotto_drop_bonus(  quest_name + '  =  +' + event_quest[ data_indices['lotto'] ] + '\n')
                else:
                    is_lotto = False

                event_drop_add = np.zeros( drop_index_count )

                if self.remove_zeros:
                    add_data = False
                else:
                    add_data = True

                for i in range(len(data_indices['ID'])):
                    if event_quest[data_indices['drop'][i]] != '':
                        mat_ID = int(event_quest[ data_indices['ID'][i] ])

                        # Skips adding Material if it has no assigned index, so if it was assigned to be skipped
                        if ID_to_index[mat_ID] == 'F':
                            continue

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

                quest_group, member_count = run_caps.evaluate_group_info( add_data, event_quest[ data_indices['type'] ], 
                                                                         event_true_name, quest_group, member_count, event_caps )

                if add_data:
                    self.quest_names.append( quest_name )
                    event_AP_cost.append( [quest_AP_cost] )
                    event_drop_matrix.append( event_drop_add )

                    self.add_box_run_info( is_lotto, event_quest[ data_indices['rbox'] ] )
            f.close()
            
            # Event Lotto has own separate logic check just in case more Types creep into the data at the end.
            if event_lotto and AP_Buyback:
                debug.note_event_list( '  ,  AP Buyback was on\n' )
            else:
                debug.note_event_list('\n')

            run_caps.add_group_info( event_true_name, quest_group, member_count, event_caps )
            self.assemble_matrix( event_AP_cost, event_drop_matrix )
    
    def multi_event( self, run_caps, ID_to_index, drop_index_count, ):
        events_farm_folder = glob.glob( Inter.path_prefix + 'Events Farm\\*' )

        for event in events_farm_folder:
            self.add_event_drop( event, run_caps, ID_to_index, drop_index_count )
        
        Inter.Debug().note_event_list('\n')

    # Assumes first Material data point has a Header with "Bronze" in it, and that "Saber Blaze" is 9 columns after the "Monuments"  start.
    def find_data_range( self, reader ):
        mat_start = 0
        mat_end = 0

        while mat_end == 0:
            try:
                free_drop = next(reader)
            except StopIteration:
                Inter.Debug().error_warning( 'Sheet does not have a column labeled as referencing "Monument" mats.' )

            for i in range(len(free_drop)):  
                if free_drop[i].find('Bronze') >= 0:
                    mat_start = i
                if free_drop[i].find('Monument') >= 0:
                    mat_end = i+9
                    break
        if mat_start == 0:
            Inter.Debug().error_warning( 'Sheet does not have a column labeled as referencing "Bronze" mats.' )
        
        return reader, mat_start, mat_end
    
    def add_free_drop( self, free_drop_CSV, run_caps: Inter.RunCaps, skip_data_index ):
        with open( free_drop_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)

            reader, mat_start, mat_end = self.find_data_range( reader )

            free_cap = Inter.RunCaps().set_config_caps(True)
            
            free_AP_cost = []
            free_drop_matrix = []

            # Notes Quest groups to properly apply Run Caps, as well as Half AP.
            quest_group = False
            member_count = 0

            # Interpretation of how this is supposed to read the APD csv:
            # If the Singularity is further than the user wants to farm as defined in the config file, stop.
            # If the line is filler because the original google sheet copies the Japanese document formatting, skip it.
            # Else, start a new line of drop rate data.
            for free_drop in reader:
                if free_drop[0].find( self.last_area ) >= 0: 
                    break

                try:
                    normal_quest_AP = int(free_drop[2])
                except ValueError:
                    continue

                drop_matrix_add = []

                if self.remove_zeros:
                    add_data = False
                else:
                    add_data = True

                current_quest_AP = normal_quest_AP
                # Drop rate calculated from normal quest AP so that Half AP effectively doubles drop rate when optimizing run counts.
                if free_drop[3] == 'Daily' and self.tg_half_AP:
                    current_quest_AP = int(normal_quest_AP/2)

                for i in range(mat_start,mat_end):
                    if not skip_data_index[i-mat_start]:
                        try:
                            add_data = True
                            drop_matrix_add.append( normal_quest_AP / float(free_drop[i]) )
                        except ValueError:
                            drop_matrix_add.append(0)
                
                if not skip_data_index[i-mat_start]:
                    XP_mult = 1
                    for i in range(mat_end,mat_end+14):
                        # Assumes Hellfires will being at about 6 columns after "Saber Blaze."
                        if i == mat_end + 6:
                            XP_mult = 3

                        try:
                            add_data = True
                            drop_matrix_add[-1] += XP_mult * normal_quest_AP / float(free_drop[i])
                        except ValueError:
                            drop_matrix_add[-1] += 0
                
                quest_group, member_count = run_caps.evaluate_group_info( add_data, free_drop[3], 'Free Quests', quest_group, member_count, free_cap )

                if add_data:
                    self.quest_names.append( free_drop[0] + ', ' + free_drop[1] )
                    free_AP_cost.append( [current_quest_AP] )
                    free_drop_matrix.append( drop_matrix_add )

                    self.add_box_run_info(False)
            f.close()
            
            run_caps.add_group_info( 'Free Quests', quest_group, member_count, free_cap )
            self.assemble_matrix( free_AP_cost, free_drop_matrix )