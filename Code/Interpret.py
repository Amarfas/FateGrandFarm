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
    tg_half_AP = False
    remove_zeros = True
    run_int = False
    last_area = ''
    debug_on_fail = True
    create_output_files = True
    config = configparser.ConfigParser()

    def set_config( self, key, type = '', section = 'DEFAULT', make_note = True ):
        key_value = self.config[section][key]

        if type == 'int':
            try:
                key_value = int(key_value.replace(',',''))
            except ValueError:
                if key_value != '' and key_value != 'None':
                    Debug().error_warning( 'Configuration "' + key + '" was not a number.')
                key_value = None

        if type == 'float':
            try:
                key_value = float(key_value.replace(',',''))
            except ValueError:
                Debug().error_warning( 'Configuration "' + key + '" was not a number.')
                key_value = None

        if type == 'bool':
            x = key_value.lower()
            if x == '1' or x == 'true' or x == 't' or x == 'yes' or x == 'y' or x == 'on':
                key_value = True
            else:
                if x == '0' or x == 'false' or x == 'f' or x == 'no' or x == 'n' or x == 'off':
                    key_value = False
                else:
                    Debug().error_warning( 'Configuration "' + key + '" was not yes or no/true or false.')

        if make_note:
            Debug().note_config(key, key_value)

        # 'Last Area' configuration, hopefully no Regions have ZZZZZ in their name in the future.
        if key == 'Stop Here' and key_value == '':
            return 'ZZZZZ'
        return key_value

    def read_config_ini(self):
        ConfigList.config.read( path_prefix + 'fgf_config.ini' )

        ConfigList.debug_on_fail = self.set_config('Debug on Fail', 'bool')
        Debug.notifications = self.set_config('Notifications', 'bool')

        ConfigList.plan_name = self.set_config('Plan Name')
        ConfigList.tg_half_AP = self.set_config('Training Grounds Half AP', 'bool')
        ConfigList.remove_zeros = self.set_config('Remove Zeros', 'bool')
        ConfigList.run_int = self.set_config('Run Count Integer', 'bool')
        ConfigList.last_area = self.set_config('Stop Here')
        ConfigList.create_output_files = self.set_config('Output Files', 'bool')

# Compiles statements to be included in the Debug output text file.
class Debug():
    error = ''
    config_notes = ''
    event_notes = 'The Events included in this analysis are:\n'
    lotto_notes = ''
    run_cap_debug = []
    notifications = True

    def __init__(self) -> None:
        pass
    
    def error_warning( self, note ):
        note = '!! ' + note
        if self.notifications:
            print(note)
        Debug.error += note + '\n'

    def note_config( self, key, key_value ):
        Debug.config_notes += key + ' = ' + str(key_value) + '\n'

    def add_debug( self, note, index, new = False ):
        if new:
            Debug.run_cap_debug.append( [''] * new )
        Debug.run_cap_debug[-1][index] += note

    def note_event_list( self, note ):
        Debug.event_notes += note
    
    # Lot of information, has its own category so it can be forced to the bottom
    def add_lotto_drop_bonus( self, note ):
        if Debug.lotto_notes == '':
            Debug.lotto_notes += 'The lotto drop bonus for each node is:\n'
        Debug.lotto_notes += note

class DataFiles:
    def __init__( self, goals_CSV, material_list_CSV ):
        self.drop_index_count = 0
        self.data_index_count = 0
        self.remove_zeros = ConfigList.remove_zeros

        self.skip_data_index = {}
        self.ID_to_index = {-1: [], -2: [], -3: [], -4: [], -5: [], -6: 'F'}
        self.index_to_name = {}

        self.goals = []
        self._interpret_CSVs( goals_CSV, material_list_CSV )
    
    def _find_material_CSV_data( self, material_CSV ):
        with open( material_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)

            mat_ID_list = next(reader)
            while( mat_ID_list[0][0:2] != 'ID' ):
                mat_ID_list = next(reader)

            mat_name_list = next(reader)
            f.close()

            return mat_ID_list, mat_name_list

    # Interpret the Materials by groups between their gaps.
    def _interpret_group( self, reader, mat_ID_list, mat_name_list, list_index, drop_matrix_index, gaps, expected_mat ):
        goals_CSV_row = next(reader)
        if goals_CSV_row[0] != expected_mat[0]:
            Debug().error_warning( 'Does not seem to be the start of '+ expected_mat[1] +'. GOALS and/or Material List CSVs may need to be updated.' )
        
        while goals_CSV_row[0][0:2] != '!!':
            try:
                mat_goal = int(goals_CSV_row[1])
            except ValueError:
                mat_goal = 0
            
            # Flag whether or not to remove this material from the Drop Matrix.
            skip = self.remove_zeros and (mat_goal == 0)
            self.skip_data_index[list_index] = skip

            list_index += 1
            goals_CSV_row = next(reader)
            
            if skip:
                self.ID_to_index.setdefault( int(mat_ID_list[list_index]), 'F' )
            else:
                self.goals.append( [mat_goal] )
                self.ID_to_index.setdefault( int(mat_ID_list[list_index]), drop_matrix_index )
                self.index_to_name.setdefault( drop_matrix_index, mat_name_list[list_index] )
                drop_matrix_index += 1

                # Adds Gems, Statues, Monuments, and XP cards to a special collective ID. Should be negative.
                if gaps > 2:
                    self.ID_to_index[2-gaps].append( int(mat_ID_list[list_index]) )

        # If zeros are removed, gaps never matter. Otherwise, they need token additions.
        self.skip_data_index[list_index] = self.remove_zeros
        list_index += 1
        if not self.remove_zeros:
            self.goals.append([0])
            self.index_to_name.setdefault( drop_matrix_index, '' )
            drop_matrix_index += 1

        # Notes that negative Mat IDs should be skipped if the entry is empty.
        if gaps > 2:
            if self.ID_to_index[2-gaps] == []:
                self.ID_to_index[2-gaps] = 'F'
        
        return reader, list_index, drop_matrix_index
    
    # 'Saber Blaze' index will be used in place of all XP drops.
    def _interpret_XP_data( self, mat_IDs, list_index, drop_matrix_index, xp_goal ):
        skip = self.remove_zeros and (xp_goal == 0)
        if skip:
            drop_matrix_index = 'F'
        else:
            self.goals.append( [xp_goal] )
            self.ID_to_index[-6] = [ int(mat_IDs[list_index+1]) ]
            self.index_to_name.setdefault( drop_matrix_index, 'Class Blaze' )
            self.drop_index_count += 1

        for i in range(16):
            self.skip_data_index[list_index] = skip
            list_index += 1
            self.ID_to_index.setdefault( int(mat_IDs[list_index]), drop_matrix_index )
        
        self.data_index_count = list_index

    # Creates three dictionaries, 'ID_to_index' maps a Material's ID to placement in Drop Matrix, or notes that it should be skipped with an 'F' value.
    # 'index_to_name' maps placement in Drop Matrix to the corresponding Material's name.
    # 'skip_data_index' maps whether or not an entry in the Free Drop Matrix should be skipped.
    # Also transforms the data in the GOALS csv into a computable column matrix.
    def _interpret_CSVs( self, goals_CSV, material_list_CSV ):
        mat_ID_list, mat_name_list = self._find_material_CSV_data(material_list_CSV)
        
        with open( goals_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            goals_csv_row = next(reader)

            list_index = 0
            drop_matrix_index = 0

            # Warn if the gaps between Material groups do not line up.
            expected_mat = [['Proof of Hero', 'Bronze Mats'],['Seed of Yggdrasil','Silver Mats'],['Claw of Chaos','Gold Mats'], 
                         ['Gem of Saber','Blue Gems'], ['Magic Gem of Saber','Red Gems'], ['Secret Gem of Saber','Gold Gems'],
                         ['Saber Piece','Statues'], ['Saber Monument', 'Monuments']]

            for gaps in range(8):
                reader, list_index, drop_matrix_index = self._interpret_group( reader, mat_ID_list, mat_name_list, list_index, drop_matrix_index, gaps, expected_mat[gaps] )

            self.drop_index_count = drop_matrix_index

            goals_csv_row = next(reader)
            if goals_csv_row[0] != 'Saber Blaze':
                Debug().error_warning( 'Does not seem to be the start of XP. GOALS and/or Material List CSVs may need to be updated.' )
            
            try:
                xp_goal = int(goals_csv_row[1])
            except ValueError:
                xp_goal = 0

            f.close()

        self._interpret_XP_data( mat_ID_list, list_index, drop_matrix_index, xp_goal )
        if self.goals == []:
            Debug().error_warning("You have assigned no goals.")
        self.goals = np.array(self.goals)

class RunCaps():
    def __init__(self):
        self.group_to_member_count = []
        self.group_name_list = []
        self.run_cap_list = []
        self.matrix_col = 0

    def set_config_caps( self, make_note = False ):
        return { 'Event':[ConfigList().set_config('Event Cap', 'float', make_note=make_note)],
                'Lotto':[ConfigList().set_config('Lotto Cap', 'float', make_note=make_note)],
                'Raid':[ConfigList().set_config('Raid Cap', 'float', make_note=make_note)],
                'Bleach':[ConfigList().set_config('Bleach Cap', 'float', make_note=make_note)] }

    def determine_event_caps( self, event_node ):
        debug = Debug()
        cap_debug_notes = '  ,  is default = '
        event_caps = self.set_config_caps()

        new_cap = []
        cap_read = False
        for i in event_node:
            if i.find('Event Run Caps') >= 0:
                cap_read = 'Event'
            if i.find('Raid Run Caps') >= 0:
                if new_cap != []:
                    # Event Caps are contexually either "Event" or "Lotto" Caps
                    event_caps[cap_read] = new_cap
                    event_caps['Lotto'] = new_cap

                    # Noted as a deviation from fgf_config value
                    debug.note_event_list( '  ,  Event Run Cap was ' + str(new_cap) )
                    debug.add_debug( '  ,  Event Run Cap was ' + str(new_cap), 2 )
                    new_cap = []

                cap_read = 'Raid'
            
            if cap_read:
                try:
                    new_cap.append(int(i.replace(',','')))
                    cap_debug_notes = '  -->  '
                except ValueError:
                    pass

        if new_cap != []:
            event_caps[cap_read] = new_cap
            debug.note_event_list( '  ,  Raid Run Cap was ' + str(new_cap) )
            debug.add_debug( '  ,  Raid Run Cap was ' + str(new_cap), 2 )
        
        debug.add_debug( cap_debug_notes, 3 )
        debug.add_debug( str(event_caps) + '\n', 4 )
        return event_caps
    
    def add_group_info( self, true_name, group_name, member_count, quest_caps ):
        if group_name and member_count > 0:
            self.matrix_col += member_count

            try:
                group_type, group_num = group_name.split(' ')
            except ValueError:
                group_type = group_name
                group_num = '1'

            type_info = [ true_name, group_type, group_num ]
            self.group_to_member_count.append([type_info, member_count])
            
            cap_list = quest_caps.get(group_type)
            
            if cap_list == None or len(cap_list) == 0 or cap_list[0] == None:
                cap_input = None
            else:
                if len(cap_list) == 1:
                    cap_input = cap_list[0]
                else:
                    try:
                        cap_input = cap_list[ (int(group_num) - 1) % len(cap_list) ]
                    except ValueError:
                        Debug().error_warning('Type Group Number was not an integer.')
                
                if not type_info in self.group_name_list:
                    self.group_name_list.append(type_info)
                    self.run_cap_list.append([cap_input])
    
    def evaluate_group_info( self, add_quest_data, group_name, true_name, prev_group, member_count, quest_caps = False ):
        if prev_group != group_name:
            self.add_group_info( true_name, prev_group, member_count, quest_caps )

            # If Quest Data is not to be added, does not count as an additional member. If included, members start at 1.
            return group_name, add_quest_data
        return prev_group, member_count + add_quest_data
    
    def build_run_cap_matrix(self):
        run_matrix = np.zeros(( len(self.run_cap_list), self.matrix_col ))

        col = 0
        for i in self.group_to_member_count:
            start = col
            col += i[1]

            if i[0] in self.group_name_list:
                row = self.group_name_list.index(i[0])
                run_matrix[row][start:col] = 1

        return [ run_matrix, np.array(self.run_cap_list) ]