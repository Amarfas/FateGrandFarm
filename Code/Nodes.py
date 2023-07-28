import csv
import glob
import numpy as np
import Interpret as Inter

class Nodes:
    def __init__( self ):
        self.node_names = []
        self.AP_costs = []
        self.drop_matrix = np.array([])
        self.hellfire_range = [9700000,500]

        self.remove_zeros = Inter.ConfigList.remove_zeros

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
            if add_drop_matrix != []:
                if np.size( self.drop_matrix ) == 0:
                    self.AP_costs = np.array( add_AP_cost )
                    self.drop_matrix = np.array( add_drop_matrix )
                else:
                    self.AP_costs = np.vstack(( self.AP_costs, add_AP_cost ))
                    self.drop_matrix = np.vstack(( self.drop_matrix, add_drop_matrix )) 

    def add_event_drop( self, event_drop_CSV, run_caps: Inter.RunCaps, mat_count, ID_to_index ):
        event_folder = ['FGO Efficiency ',
                        'Efficiency ',
                        'Events Farm' + '\\']
        
        for i in event_folder:
            if event_drop_CSV.find(i) >= 0:
                start = event_drop_CSV.rfind(i)+len(i)
                break

        event_name = event_drop_CSV[(start):event_drop_CSV.rindex(' - Event',start)]
        Inter.Debug().make_note( event_name + '\n' )

        with open( event_drop_CSV, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            event_node = next(reader)

            event_true_name = event_node[2]
            event_caps = run_caps.determine_event_caps(event_node)

            mat_locations = []
            while mat_locations == []:
                try:
                    event_node = next(reader)
                except:
                    Inter.Debug().error_warning( 'Sheet does not have columns labeled "ID".' )
                count = 0
                for i in event_node:
                    if i == 'ID': 
                        mat_locations.append(count)
                    count += 1

            event_AP_cost = []
            event_drop_matrix = []
            
            node_group = False
            group_count = 0

            # Interpretation of how this is supposed to read the Event Quest csv:
            # If there is no AP assigned or no material assigned in the first slot, skip this line.
            # If there is an AP assigned, assume the drops are part of a new node and start a new line of the Drop Matrix.
            # Add drops to the last made line in the Drop Matrix.
            for event_node in reader:
                try:
                    float(event_node[1])
                    if not bool(event_node[mat_locations[0]].strip()):
                        continue
                except ValueError: continue
                
                event_drop_add = np.zeros( mat_count )
                if self.remove_zeros:
                    add_data = False
                else:
                    add_data = True

                for i in mat_locations:
                    if event_node[i+2] != '':
                        mat_ID = int(event_node[i])
                        if ID_to_index[mat_ID] == 'T':
                            continue

                        dropRate = float(event_node[i+2]) / 100
                        if mat_ID >= self.hellfire_range[0] and mat_ID % self.hellfire_range[1] == 0:
                            dropRate *= 3

                        if mat_ID < 0:
                            mat_ID = ID_to_index[mat_ID]
                        else:
                            mat_ID = [mat_ID]
                        for j in mat_ID:
                            add_data = True
                            event_drop_add[ ID_to_index[j] ] += dropRate
                
                node_group, group_count = run_caps.evaluate_group_info( add_data, event_node[3], event_true_name, node_group, group_count, event_caps )
                if add_data:
                    self.node_names.append( event_name + ', ' + event_node[0] )
                    event_AP_cost.append( [float(event_node[1])] )
                    event_drop_matrix.append( event_drop_add )
            f.close()
            
            run_caps.add_group_info( event_true_name, node_group, group_count, event_caps )
            self.assemble_matrix( event_AP_cost, event_drop_matrix )
    
    def multi_event( self, run_caps, mat_count, ID_to_index ):
        Inter.Debug().make_note( 'The Events included in this analysis are:\n' )
        eventFolder = glob.glob( Inter.path_prefix + 'Events Farm\\*' )

        for event in eventFolder:
            self.add_event_drop( event, run_caps, mat_count, ID_to_index )
        
        Inter.Debug().make_note('\n')
    
    def add_free_drop( self, free_drop_CSV, run_caps: Inter.RunCaps, skip_data_index ):
        with open( free_drop_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)

            # Find the starting index of the Materials and where the XP starts.
            mat_start = 0
            mat_end = 0
            while mat_end == 0:
                try:
                    free_drop = next(reader)
                except:
                    Inter.Debug().error_warning( 'Sheet does not have a column labeled as referencing "Monument" mats.' )
                for i in range(len(free_drop)):
                    if free_drop[i].find('Bronze') >= 0:
                        mat_start = i
                    if free_drop[i].find('Monument') >= 0:
                        mat_end = i+9
                        break
            if mat_start == 0:
                Inter.Debug().error_warning( 'Sheet does not have a column labeled as referencing "Bronze" mats.' )
            
            free_AP_cost = []
            free_drop_matrix = []

            node_group = False
            group_count = 0

            half_AP = Inter.ConfigList.tg_half_AP

            # Interpretation of how this is supposed to read the APD csv:
            # If the Singularity is further than the user wants to farm as defined in the config file, stop.
            # If the line is filler because the original google sheet copies the Japanese document formatting, skip it.
            # Else, start a new line of drop rate data.
            for free_drop in reader:
                if free_drop[0].find( Inter.ConfigList.last_area ) >= 0: 
                    break

                try:
                    node_AP = int(free_drop[2])
                except ValueError:
                    continue

                if free_drop[3] == 'Daily' and half_AP:
                    node_AP *= float( node_AP / int(node_AP/2) )

                drop_matrix_add = []
                if self.remove_zeros:
                    add_data = False
                else:
                    add_data = True

                for i in range(mat_start,mat_end):
                    if not skip_data_index[i-mat_start]:
                        try:
                            add_data = True
                            drop_matrix_add.append( node_AP / float(free_drop[i]) )
                        except ValueError:
                            drop_matrix_add.append(0)
                
                if not skip_data_index[i-mat_start]:
                    XP_mult = 1
                    for i in range(mat_end,mat_end+14):
                        if i == mat_end + 6:
                            XP_mult = 3
                        try:
                            add_data = True
                            drop_matrix_add[-1] += XP_mult * node_AP / float(free_drop[i])
                        except ValueError:
                            drop_matrix_add[-1] += 0
                
                node_group, group_count = run_caps.evaluate_group_info( add_data, free_drop[3], 'Free Quests', node_group, group_count )
                if add_data:
                    self.node_names.append( free_drop[0] + ', ' + free_drop[1] )
                    free_AP_cost.append( [node_AP] )
                    free_drop_matrix.append( drop_matrix_add )
            f.close()
            
            run_caps.add_group_info( 'Free Quests', node_group, group_count )
            self.assemble_matrix( free_AP_cost, free_drop_matrix )