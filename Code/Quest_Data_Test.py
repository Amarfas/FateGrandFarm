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
    
    def add_lotto_info( self, is_lotto, event_node = [], data_indices = [] ):
        if is_lotto:
            self.runs_per_box.append( float(event_node[ data_indices['rbox'] ]) )
        else:
            self.runs_per_box.append( 'F' )
    
    def find_data_indices( self, reader ):
        data_indices = {'ID':[], 'drop':[]}
        while data_indices['ID'] == []:
            try:
                event_node = next(reader)
            except:
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
                    data_indices.setdefault('rbox',i)

                if event_node[i] == 'ID': 
                    data_indices['ID'].append(i)
                if event_node[i] == 'Drop%':
                    data_indices['drop'].append(i)
        
        return data_indices, reader
    
    def find_event_name( self, event_drop_CSV ):
        event_folder = ['FGO Efficiency ',
                        'Events Farm' + '\\']
        
        for i in event_folder:
            if event_drop_CSV.find(i) >= 0:
                start = event_drop_CSV.find(i)+len(i)
                break
        
        event_folder = [' - Event',
                        '.csv']
        for i in event_folder:
            if event_drop_CSV.rfind(i) >= 0:
                end = event_drop_CSV.rfind(i)
                break

        return event_drop_CSV[start:end]

    def add_event_drop( self, event_drop_CSV, run_caps: Inter.RunCaps, mat_count, ID_to_index ):
        event_name = self.find_event_name(event_drop_CSV)
        Inter.Debug().note_event_list( event_name )

        with open( event_drop_CSV, newline = '', encoding = 'latin1' ) as f:
            reader = csv.reader(f)
            event_node = next(reader)

            event_true_name = event_node[2]
            event_caps = run_caps.determine_event_caps(event_node)
            for i in range(len(event_node)):
                if event_node[i] == 'Buyback?:':
                    if not bool(event_node[i+1].strip()):
                        AP_Buyback = True
                    else:
                        AP_Buyback = False
                    break

            data_indices, reader = self.find_data_indices(reader)

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
                    node_AP_cost = float(event_node[ data_indices['AP'] ])
                    if not bool(event_node[ data_indices['ID'][0] ].strip()):
                        continue
                except ValueError:
                    continue
                
                node_name = event_name + ', ' + event_node[ data_indices['loc'] ]
                if event_node[ data_indices['type'] ][0:5] == 'Lotto':
                    is_lotto = True
                    Inter.Debug().add_lotto_drop_bonus(  node_name + '  =  +' + event_node[ data_indices['lotto'] ] + '\n')
                else:
                    is_lotto = False

                event_drop_add = np.zeros( mat_count )
                if self.remove_zeros:
                    add_data = False
                else:
                    add_data = True

                for i in range(len(data_indices['ID'])):
                    if event_node[data_indices['drop'][i]] != '':
                        mat_ID = int(event_node[ data_indices['ID'][i] ])
                        if ID_to_index[mat_ID] == 'F':
                            continue

                        dropRate = float(event_node[ data_indices['drop'][i] ]) / 100
                        if mat_ID >= self.hellfire_range[0] and mat_ID % self.hellfire_range[1] == 0:
                            dropRate *= 3

                        if mat_ID < 0:
                            mat_ID = ID_to_index[mat_ID]
                        else:
                            mat_ID = [mat_ID]
                        for j in mat_ID:
                            add_data = True
                            event_drop_add[ ID_to_index[j] ] += dropRate

                node_group, group_count = run_caps.evaluate_group_info( add_data, event_node[data_indices['type']], event_true_name, node_group, group_count, event_caps )
                if add_data:
                    self.quest_names.append( node_name )
                    event_AP_cost.append( [node_AP_cost] )
                    event_drop_matrix.append( event_drop_add )

                    self.add_lotto_info( is_lotto, event_node, data_indices )
            f.close()
            
            run_caps.add_group_info( event_true_name, node_group, group_count, event_caps )
            self.assemble_matrix( event_AP_cost, event_drop_matrix )
    
    def multi_event( self, run_caps, mat_count, ID_to_index ):
        Inter.Debug().note_event_list( 'The Events included in this analysis are:\n' )
        eventFolder = glob.glob( Inter.path_prefix + 'Events Farm\\*' )

        for event in eventFolder:
            self.add_event_drop( event, run_caps, mat_count, ID_to_index )
        
        Inter.Debug().note_event_list('\n')
    
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

            free_cap = Inter.RunCaps().set_config_caps(True)
            
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
                
                node_group, group_count = run_caps.evaluate_group_info( add_data, free_drop[3], 'Free Quests', node_group, group_count, free_cap )
                if add_data:
                    self.quest_names.append( free_drop[0] + ', ' + free_drop[1] )
                    free_AP_cost.append( [node_AP] )
                    free_drop_matrix.append( drop_matrix_add )

                    self.add_lotto_info(False)
            f.close()
            
            run_caps.add_group_info( 'Free Quests', node_group, group_count, free_cap )
            self.assemble_matrix( free_AP_cost, free_drop_matrix )