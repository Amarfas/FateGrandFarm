import csv
import glob
import numpy as np
import cvxpy as cp
from FateGrandFarm import Debug

class Nodes:
    def __init__( self, goals, material_list_CSV, run_caps, debug, remove_zeros = False ):
        self.mat_count = 0
        self.mat_total = 0
        self.skip_data_index = {}
        self.remove_zeros = remove_zeros

        self.goals = []
        self.ID_to_index = {-1: [], -2: [], -3: [], -4: [], -5: [], -6: 'T'}
        self.index_to_name = {}
        self.interpret_CSVs( goals, material_list_CSV, debug )

        self.node_names = []
        self.AP_costs = []
        self.run_caps = run_caps
        self.cap_info = np.array([])
        self.drop_matrix = np.array([])
        self.hellfire_range = [9700000,500]
    
    # Interpret the Materials by groups between their gaps.
    def interpret_group( self, reader, mat_ID, mat_name, count, index, gaps, error, debug ):
        row = next(reader)
        if row[0] != error[0]:
            debug.error_warning( 'Does not seem to be the start of '+ error[1] +'. GOALS and/or Material List CSVs may need to be updated.' )
        
        while row[0][0:2] != '!!':
            try:
                matGoal = int(row[1])
            except:
                matGoal = 0
            
            # Flag whether or not to remove this material from the Drop Matrix.
            skip = self.remove_zeros and (matGoal == 0)
            self.skip_data_index[count] = skip

            count += 1
            row = next(reader)
            
            if skip:
                self.ID_to_index.setdefault( int(mat_ID[count]), 'T' )
            else:
                self.goals.append( [matGoal] )
                self.ID_to_index.setdefault( int(mat_ID[count]), index )
                self.index_to_name.setdefault( index, mat_name[count] )
                index += 1

                if gaps > 2:
                    self.ID_to_index[2-gaps].append( int(mat_ID[count]) )

        self.skip_data_index[count] = self.remove_zeros
        count += 1
        if not self.remove_zeros:
            self.goals.append([0])
            self.index_to_name.setdefault( index, '' )
            index += 1

        # Notes that negative Mat IDs should be skipped if the entry is empty.
        if gaps > 2:
            if self.ID_to_index[2-gaps] == []:
                self.ID_to_index[2-gaps] = 'T'
        
        return reader, count, index

    # Creates three dictionaries, 'IDtoIndex' maps a Material's ID to placement in Drop Matrix, or notes that it should be skipped with a 'T' value.
    # 'indexToName' maps placement in Drop Matrix to the corresponding Material's name.
    # 'skipDataIndex' maps whether or not an entry in the Free Drop Matrix should be skipped.
    # Also transforms the data in the GOALS csv into a computable column matrix.
    # count is generally incremented before 'matID' and 'matName' because the 0th index is not the start of the relevant values.
    def interpret_CSVs( self, goals_CSV, material_list_CSV, debug ):
        with open( material_list_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            mat_IDs = next(reader)
            while( mat_IDs[0][0:2] != 'ID' ):
                mat_IDs = next(reader)
            mat_names = next(reader)
            f.close()
        
        with open( goals_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            row = next(reader)

            count = 0
            index = 0

            # Warn if the gaps between Material groups do not line up.
            errors = [['Proof of Hero', 'Bronze Mats'],['Seed of Yggdrasil','Silver Mats'],['Claw of Chaos','Gold Mats'], 
                         ['Gem of Saber','Blue Gems'], ['Magic Gem of Saber','Red Gems'], ['Secret Gem of Saber','Gold Gems'],
                         ['Saber Piece','Statues'], ['Saber Monument', 'Monuments']]

            for gaps in range(8):
                reader, count, index = self.interpret_group( reader, mat_IDs, mat_names, count, index, gaps, errors[gaps], debug )

            row = next(reader)
            if row[0] != 'Saber Blaze':
                debug.error_warning( 'Does not seem to be the start of XP. GOALS and/or Material List CSVs may need to be updated.' )
            
            try:
                mat_goal = int(row[1])
            except:
                mat_goal = 0
            f.close()
        
        # 'Saber Blaze' index will be used in place of all XP drops.
        self.mat_count = index
        skip = self.remove_zeros and (mat_goal == 0)
        if skip:
            index = 'T'
        else:
            self.goals.append( [mat_goal] )
            self.ID_to_index[-6] = [ int(mat_IDs[count+1]) ]
            self.index_to_name.setdefault( index, 'Class Blaze' )
            self.mat_count += 1

        for i in range(16):
            self.skip_data_index[count] = skip
            count += 1
            self.ID_to_index.setdefault( int(mat_IDs[count]), index )
        
        self.mat_total = count
        self.goals = np.array(self.goals)

    # TODO: There are some issues with this method of assembling matrices.
    # The basic issue is that cvxpy analysis requires data in the form of numpy matrices, but the best way to form numpy matrices is to initialize its size.
    # This is because vstacking numpy matrices line by line is slow, because it rewrites the entire matrix every time.
    # ^^^ NOT CONFIRMED, maybe that's what I should do.
    # Unfortunately, in order to initialize the size, we have to know how many lines the csv is. This apparently requires reading through the entire csv once.
    # Since the csv's have to be read and added to the data line by line, this would be inelegant/slow.
    # For the above reasons, I have instead opted to put the data from the csv into an array first, and then turn those arrays into a numpy matrix before stacking.
    # This seems to have caused an issue with making a 'Run Cap' constraint, as the column matrixes are size '(X,)' rather than '(X,1)'
    # This doesn't make sense and tells me there needs to be some changes.

    # FIXED SIZE PROBLEM: rest should still be looked into.
    def assemble_matrix( self, add_AP_cost, add_drop_matrix ):
            if np.size( self.drop_matrix ) == 0:
                self.AP_costs = np.array( add_AP_cost )
                self.drop_matrix = np.array( add_drop_matrix )
            else:
                self.AP_costs = np.vstack(( self.AP_costs, add_AP_cost ))
                self.drop_matrix = np.vstack(( self.drop_matrix, add_drop_matrix ))
    
    def add_cap_info( self, true_name, node_group, caps, node_count ):
        try:
            node_type, group_num = node_group.split(' ')
        except:
            node_type = node_group
            group_num = 'None'

        if node_type == 'Event' or node_type == 'Lotto':
            type_cap = caps[0]
        else:
            if node_type == 'Raid':
                type_cap = caps[1]
            else:
                if node_type == 'Bleach':
                    type_cap = caps[2]
                else:
                    type_cap = 'None'

        add_info = [ true_name, node_type, group_num, type_cap, node_count ]
        if np.size( self.cap_info ) == 0:
            self.cap_info = np.array( add_info, dtype = object )
        else:
            self.cap_info = np.vstack(( self.cap_info, add_info ))
    
    def add_event_drop( self, event_drop_CSV, debug, multi_event ):
        start = event_drop_CSV.rindex('Efficiency ')+len('Efficiency ')
        event_name = event_drop_CSV[(start):event_drop_CSV.rindex(' - Event',start)]

        if not multi_event:
            debug.file_name = event_name
        debug.make_note( event_name + '\n' )

        with open( event_drop_CSV, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            event_node = next(reader)

            event_true_name = event_node[2]
            event_caps = self.run_caps
            event_cap_mod = []
            cap_add = False
            for i in event_node:
                if i == 'Event Run Caps':
                    cap_add = True
                if i == 'Raid Run Caps':
                    if event_cap_mod != []:
                        event_caps[0] = event_cap_mod
                        event_cap_mod = []

                if cap_add:
                    try:
                        event_cap_mod.append(int(i))
                    except:
                        a = 1
            if event_cap_mod != []:
                event_caps[1] = event_cap_mod

            # Finds where the lotto material drops start in the csv, as the formatting changes for these.
            mat_locations = []
            while mat_locations == []:
                try:
                    event_node = next(reader)
                except:
                    debug.error_warning( 'Sheet does not have columns labeled "ID".' )
                count = 0
                for i in event_node:
                    if i == 'ID': 
                        mat_locations.append(count)
                    count += 1

            event_AP_cost = []
            event_drop_matrix = []
            
            node_group = False
            node_group_count = 0

            # Interpretation of how this is supposed to read the Event Quest csv:
            # If there is no AP assigned or no material assigned in the first slot, skip this line.
            # If there is an AP assigned, assume the drops are part of a new node and start a new line of the Drop Matrix.
            # Add drops to the last made line in the Drop Matrix.
            for event_node in reader:
                if event_node[ mat_locations[0] ] == '' or event_node[1] == '': 
                    continue
                
                if node_group != event_node[3]:
                    if node_group != False:
                        self.add_cap_info( event_true_name, node_group, event_caps, node_group_count )
                    node_group = event_node[3]
                    node_group_count = 0
                node_group_count += 1

                self.node_names.append( event_name + ', ' + event_node[0] )
                event_AP_cost.append( [float(event_node[1])] )
                event_drop_matrix.append( np.zeros( self.mat_count ) )

                for i in mat_locations:
                    if event_node[i+2] != '':
                        mat_ID = int(event_node[i])
                        if self.ID_to_index[mat_ID] == 'T':
                            continue

                        dropRate = float(event_node[i+2]) / 100
                        if mat_ID >= self.hellfire_range[0] and mat_ID % self.hellfire_range[1] == 0:
                            dropRate *= 3

                        if mat_ID < 0:
                            mat_ID = self.ID_to_index[mat_ID]
                        else:
                            mat_ID = [mat_ID]
                        for j in mat_ID:
                            event_drop_matrix[-1][ self.ID_to_index[j] ] += dropRate
            f.close()
            
            self.add_cap_info( event_true_name, node_group, event_caps, node_group_count )
            self.assemble_matrix( event_AP_cost, event_drop_matrix )
    
    def add_free_drop( self, free_drop_CSV, last_area, debug ):
        with open( free_drop_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)

            # Find the starting index of the Materials and where the XP starts.
            mat_start = 0
            mat_end = 0
            while mat_end == 0:
                try:
                    free_drop = next(reader)
                except:
                    debug.error_warning( 'Sheet does not have a column labeled as referencing "Monument" mats.' )
                for i in range(len(free_drop)):
                    if free_drop[i].find('Bronze') >= 0:
                        mat_start = i
                    if free_drop[i].find('Monument') >= 0:
                        mat_end = i+9
                        break
            if mat_start == 0:
                debug.error_warning( 'Sheet does not have a column labeled as referencing "Bronze" mats.' )
            
            free_AP_cost = []
            free_drop_matrix = []

            node_group = False
            node_group_count = 0

            # Interpretation of how this is supposed to read the APD csv:
            # If the Singularity is further than the user wants to farm as defined in the config file, stop.
            # If the line is filler because the original google sheet copies the Japanese document formatting, skip it.
            # Else, start a new line of drop rate data.
            for free_drop in reader:
                if free_drop[0].find( last_area ) >= 0: 
                    break

                if free_drop[2] == '' or free_drop[2] == 'AP': 
                    continue

                if node_group != free_drop[3]:
                    if node_group != False:
                        self.add_cap_info( 'Free Quests', node_group, self.run_caps, node_group_count )
                    node_group = free_drop[3]
                    node_group_count = 0
                node_group_count += 1

                node_AP = int(free_drop[2])
                self.node_names.append( free_drop[0] + ', ' + free_drop[1] )
                free_AP_cost.append( [node_AP] )
                drop_matrix_add = []

                for i in range(mat_start,mat_end):
                    if not self.skip_data_index[i-mat_start]:
                        try: 
                            drop_matrix_add.append( node_AP / float(free_drop[i]) )
                        except:
                            drop_matrix_add.append(0)
                
                if not self.skip_data_index[i-mat_start]:
                    XP_mult = 1
                    for i in range(mat_end,mat_end+14):
                        if i == mat_end + 6:
                            XP_mult = 3
                        try:
                            drop_matrix_add[-1] += XP_mult * node_AP / float(free_drop[i])
                        except:
                            drop_matrix_add[-1] += 0

                free_drop_matrix.append( drop_matrix_add )
            f.close()
            
            self.add_cap_info( 'Free Quests', node_group, self.run_caps, node_group_count )
            self.assemble_matrix( free_AP_cost, free_drop_matrix )
    
    def multi_event( self, path, debug, event_find, multi_event ):
        if multi_event:
            debug.file_name = 'Multi'
            debug.make_note( 'The Events included in this analysis are:\n' )
            eventFolder = glob.glob( path + 'Events\\Multi Event Folder\\*' )
        else:
            debug.make( 'The Event included in this analysis is: ')
            eventFolder = glob.glob( path + '*' + event_find + '* - Event Quest.csv' )

        for event in eventFolder:
            self.add_event_drop( event , debug , multi_event )
        
        debug.make_note('\n')