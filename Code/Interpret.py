import configparser
import csv
import glob
import numpy as np

# Makes it so the program works whether it's started in the 'FarmingGrandOrder' overarching directory or the 'FarmGrandOrder' folder.
def standardize_path():
    global path_prefix
    if glob.glob('Code') == []:
        path_prefix = '..\\'
    else:
        path_prefix = ''

    Debug.config_notes = 'The Path Prefix is: ' + path_prefix + '\n'

class ConfigList():
    plan_name = ''
    tg_half_AP = ''
    remove_zeros = ''
    run_int = ''
    last_area = ''
    output_files = ''
    config = configparser.ConfigParser()

    def set_config( self, key, type = '', section = 'DEFAULT' ):
        key_value = self.config[section][key]

        if type == 'int':
            try:
                key_value = int(key_value)
            except ValueError:
                if key_value != '' and key_value != 'None':
                    Debug().error_warning( 'Configuration "' + key + '" was not a number.')
                key_value = None

        if type == 'float':
            try:
                key_value = float(key_value)
            except ValueError:
                Debug().error_warning( 'Configuration "' + key + '" was not a number.')
                key_value = None

        if type == 'bool':
            x = key_value.lower()
            if x == '1' or x == 'true' or x == 't' or x == 'yes' or x == 'y' or x == 'on':
                key_value = True
            else:
                if not (x == '0' or x == 'false' or x == 'f' or x == 'no' or x == 'n' or x == 'off'):
                    Debug().error_warning( 'Configuration "' + key + '" was not yes or no/true or false.')
                key_value = False
    
        Debug().note_config(key, key_value)

        # 'Last Area' configuration
        if key == 'Last Area' and key_value == '':
            return 'ZZZZZ'
        return key_value

    def create_config_list(self):
        ConfigList.config.read( path_prefix + 'fgf_config.ini' )

        Debug.notifications = self.set_config('Notifications', 'bool')
        ConfigList.plan_name = self.set_config('Plan Name')
        ConfigList.tg_half_AP = self.set_config('Training Grounds Half AP', 'bool')
        ConfigList.remove_zeros = self.set_config('Remove Zeros', 'bool')
        ConfigList.run_int = self.set_config('Run Count Integer', 'bool')
        ConfigList.last_area = self.set_config('Last Area')
        ConfigList.output_files = self.set_config('Output Files', 'bool')

# Compiles statements to be included in the Debug output text file.
class Debug():
    error = ''
    config_notes = ''
    end_notes = ''
    lotto_notes = ''
    notifications = True
    
    def error_warning( self, note ):
        note = '!! ' + note
        if self.notifications:
            print(note)
        Debug.error += note + '\n'

    def note_config( self, key, key_value ):
        Debug.config_notes += key + ' = ' + str(key_value) + '\n'

    def make_note( self, note , notice = False ):
        if self.notifications and notice:
            print(note)
        Debug.end_notes += note
    
    def add_lotto( self, note ):
        if Debug.lotto_notes == '':
            Debug.lotto_notes += 'The lotto drop bonus for each node is:\n'
        Debug.lotto_notes += note

class InputData:
    def __init__( self, goals_CSV, material_list_CSV ):
        self.mat_count = 0
        self.mat_total = 0
        self.remove_zeros = ConfigList.remove_zeros

        self.skip_data_index = {}
        self.ID_to_index = {-1: [], -2: [], -3: [], -4: [], -5: [], -6: 'T'}
        self.index_to_name = {}

        self.goals = []
        self._interpret_CSVs( goals_CSV, material_list_CSV )
    
    # Interpret the Materials by groups between their gaps.
    def _interpret_group( self, reader, mat_ID, mat_name, count, index, gaps, error ):
        row = next(reader)
        if row[0] != error[0]:
            Debug().error_warning( 'Does not seem to be the start of '+ error[1] +'. GOALS and/or Material List CSVs may need to be updated.' )
        
        while row[0][0:2] != '!!':
            try:
                matGoal = int(row[1])
            except ValueError:
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

    # Creates three dictionaries, 'ID_to_index' maps a Material's ID to placement in Drop Matrix, or notes that it should be skipped with a 'T' value.
    # 'index_to_name' maps placement in Drop Matrix to the corresponding Material's name.
    # 'skip_data_index' maps whether or not an entry in the Free Drop Matrix should be skipped.
    # Also transforms the data in the GOALS csv into a computable column matrix.
    def _interpret_CSVs( self, goals_CSV, material_list_CSV ):
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
                reader, count, index = self._interpret_group( reader, mat_IDs, mat_names, count, index, gaps, errors[gaps] )

            row = next(reader)
            if row[0] != 'Saber Blaze':
                Debug().error_warning( 'Does not seem to be the start of XP. GOALS and/or Material List CSVs may need to be updated.' )
            
            try:
                mat_goal = int(row[1])
            except ValueError:
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

class RunCaps():
    def __init__(self):
        self.config_caps = { 'Event':[ConfigList().set_config('Event Cap' ,'int')],
                            'Lotto':[ConfigList().set_config('Lotto Cap' ,'int')],
                            'Raid':[ConfigList().set_config('Raid Cap' ,'int')],
                            'Bleach':[ConfigList().set_config('Bleach Cap' ,'int')] }
        self.node_info = []

    def determine_event_caps( self, event_node ):
        event_caps = self.config_caps
        new_cap = []
        cap_read = False
        for i in event_node:
            if i == 'Event Run Caps:':
                cap_read = 'Event'
            if i == 'Raid Run Caps:':
                if new_cap != []:
                    event_caps[cap_read] = new_cap
                    event_caps['Lotto'] = new_cap
                    Debug().make_note( ' , Event Run Cap was ' + str(new_cap) )
                    new_cap = []
                cap_read = 'Raid'
            
            if cap_read:
                try:
                    new_cap.append(int(i))
                except ValueError: pass

        if new_cap != []:
            event_caps[cap_read] = new_cap
            Debug().make_note( ' , Raid Run Cap was ' + str(new_cap) )
        
        return event_caps
    
    def add_group_info( self, true_name, node_group, group_count, node_caps = False ):
        if node_group and group_count > 0:
            try:
                node_type, group_num = node_group.split(' ')
            except ValueError:
                node_type = node_group
                group_num = 1
            
            if node_caps:
                cap = node_caps.get(node_type)
            else:
                cap = self.config_caps.get(node_type)
            
            if cap == None or len(cap) == 0:
                cap = None
            else:
                if len(cap) == 1:
                    cap = cap[0]
                else:
                    try:
                        cap = cap[ (int(group_num) - 1) % len(cap) ]
                    except ValueError:
                        Debug().error_warning('Type Group Number was not an integer.')

            self.node_info.append([ true_name, node_type, group_num, group_count, cap ])
    
    def evaluate_group_info( self, add_data, prev_group, true_name, node_group, group_count, node_caps = False ):
        if node_group != prev_group:
            self.add_group_info( true_name, node_group, group_count, node_caps )
            return prev_group, add_data
        return node_group, group_count + add_data
    
    def build_run_cap_matrix(self):
        # [ true_name, group, #, count, cap ]
        name_tracker = []
        run_cap = []

        row = 1
        col = 0
        node_add = 0
        for i in self.node_info:
            start = col
            col += i[3]
            node_add += i[3]

            if i[4] != None:
                if name_tracker == []:
                    name_tracker.append(i[0:3])
                    run_cap.append([i[4]])

                    run_matrix = np.zeros((1,col))
                    run_matrix[0][start:col] = 1
                else:
                    run_matrix = np.hstack(( run_matrix, np.zeros(( row, node_add )) ))

                    row_find = 0
                    for j in name_tracker:
                        if i[0:3] == j[0:3]:
                            break
                        row_find += 1
                    else:
                        name_tracker.append(i[0:3])
                        run_cap.append([i[4]])
                        row += 1

                        run_matrix = np.vstack(( run_matrix, np.zeros((1,col)) ))
                        row_find = -1

                    run_matrix[row_find][start:col] = 1

                node_add = 0

        if node_add > 0:
            run_matrix = np.hstack(( run_matrix, np.zeros(( row, node_add )) ))

        return [ run_matrix, np.array(run_cap) ]
    
    def build_run_cap_matrix_test(self):
        # [ true_name, group, #, count, cap ]
        name_tracker = []
        run_cap = []

        row = 1
        col = 0
        node_add = 0
        for i in self.node_info:
            start = col
            col += i[3]
            node_add += i[3]

            if i[4] != None:
                if name_tracker == []:
                    name_tracker.append(i[0:3])
                    run_cap.append([i[4][0]])

                    run_matrix = np.zeros((1,col))
                    run_matrix[0][start:col] = 1
                else:
                    run_matrix = np.hstack(( run_matrix, np.zeros(( row, node_add )) ))

                    row_find = 0
                    for j in name_tracker:
                        if i[0:3] == j[0:3]:
                            break
                        row_find += 1
                    else:
                        name_tracker.append(i[0:3])
                        run_cap.append([i[4][0]])
                        row += 1

                        run_matrix = np.vstack(( run_matrix, np.zeros((1,col)) ))
                        row_find = -1

                    run_matrix[row_find][start:col] = 1

                node_add = 0
        
        if node_add > 0:
            run_matrix = np.hstack(( run_matrix, np.zeros(( row, node_add )) ))

        return [ run_matrix, np.array(run_cap) ]