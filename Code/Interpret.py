import configparser
import csv
import glob
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Makes it so the program works whether it's started in the 'FateGrandFarm' overarching directory
#  or the 'Code' folder.
def standardize_path():
    global path_prefix
    if glob.glob('Code') == []:
        path_prefix = '..\\'
    else:
        path_prefix = ''

    Debug().note_config( 'The Path Prefix is', path_prefix )

class ConfigList():
    plan_name = ''
    tg_half_AP = False
    remove_zeros = True
    run_int = False
    last_area = ''
    monthly_ticket_num = 1
    monthly_ticket_start = ''
    monthly_ticket_end = ''
    #use_all_tickets = True
    debug_on_fail = True
    create_output_files = True
    config = configparser.ConfigParser()

    def set_config( self, key, type = '', section = 'DEFAULT', make_note = True ):
        key_value = self.config[section][key]

        if type == 'int':
            try:
                key_value = int(key_value.replace(',',''))
            except ValueError:
                if key_value != '' and key_value != 'None' and make_note:
                    Debug().error_warning( 'Configuration "' + key + '" was not an integer.')
                key_value = None

        if type == 'float':
            try:
                key_value = float(key_value.replace(',',''))
            except ValueError:
                if key_value != '' and key_value != 'None' and make_note:
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
                    Debug().error_warning( 'Configuration "' + key + '" was not yes / true or no / false.')

        if make_note:
            Debug().note_config(key, key_value)

        # 'Last Area' configuration, hopefully no Regions have ZZZZZ in their name in the future.
        if key == 'Stop Here' and key_value == '':
            return 'ZZZZZ'
        return key_value

    def check_if_date( self, key, key_value ):
        if key_value == '':
            return '', False
        else:
            key_value = key_value.split()[0].split('/')
            try:
                # Transform a 2 digit year into a 4 digit year
                year = int(key_value[2][:4])
                if year < 100:
                    year += 2000

                new_date = [int(key_value[0][:2]), int(key_value[1][:2]), year]
                return new_date, False
            
            except ValueError:
                return '', ' did not have proper numbers for Day, Month, or Year.'
            except IndexError:
                return '', ' was not a full date.'

    def set_date_config( self, key, section = 'DEFAULT', make_note = True ):
        key_value = self.config[section][key].lower()
        error = False

        if key == 'Monthly Ticket Start Date':
            key_value, error = self.check_if_date( key, key_value )
            if key_value == '':
                t = datetime.now(ZoneInfo("America/New_York"))
                key_value = [t.month, t.day, t.year]

        elif key_value != '':
            date_check, error = self.check_if_date( key, key_value )
            if error:
                key_space_split = key_value.split()
                try:
                    time_skip, time_frame = int(key_space_split[0]), key_space_split[1]
                except ValueError:
                    key_value = ''
                else:
                    rel_time = self.monthly_ticket_start
                    if time_frame[:3] == 'yea':
                        error = False
                        key_value = [rel_time[0], rel_time[1], rel_time[2] + time_skip]

                    elif time_frame[:3] == 'mon':
                        error = False
                        new_month_calc = rel_time[0] + time_skip - 1
                        new_month = new_month_calc % 12 + 1
                        new_year = rel_time[2] + new_month_calc // 12

                        # Makes sure there isn't an error later because the time lapsed month has fewer days
                        last_day_of_month = (datetime(new_year + new_month // 12, new_month % 12 + 1, 1) 
                                             - timedelta(seconds=1)).day
                        key_value = [new_month, min(rel_time[1], last_day_of_month), new_year]

                    elif time_frame[:3] == 'day':
                        error = False
                        new_date = datetime(rel_time[2], rel_time[0], rel_time[1]) + timedelta(days = time_skip)
                        key_value = [new_date.month, new_date.day, new_date.year]

                    else:
                        error = ' did not say whether time should elapse by days, months, or years.'
                        key_value = ''
            else:
                key_value = date_check
        
        if error:
            Debug().error_warning( 'Configuration "' + key + error)
        
        if make_note:
            if key_value == '':
                Debug().note_config(key, '')
            else:
                date_for_entry = datetime(key_value[2], key_value[0], key_value[1])
                Debug().note_config(key, date_for_entry.strftime('%m/%d/%Y'))

        return key_value

    def read_config_ini(self):
        ConfigList.config.read( path_prefix + 'fgf_config.ini' )

        ConfigList.debug_on_fail = self.set_config('Debug on Fail', 'bool')
        Debug.notifications = self.set_config('Notifications', 'bool')

        ConfigList.plan_name = self.set_config('Plan Name')
        ConfigList.tg_half_AP = self.set_config('Training Grounds Half AP', 'bool')
        ConfigList.remove_zeros = self.set_config('Remove Zeros', 'bool')
        ConfigList.run_int = self.set_config('Run Count Integer', 'bool')
        ConfigList.monthly_ticket_num = self.set_config('Monthly Ticket Per Day', 'int')
        ConfigList.monthly_ticket_start = self.set_date_config('Monthly Ticket Start Date')
        ConfigList.monthly_ticket_end = self.set_date_config('Monthly Ticket End Date')
        #ConfigList.use_all_tickets = self.set_config('Use All Tickets', 'bool')
        ConfigList.last_area = self.set_config('Stop Here')
        ConfigList.create_output_files = self.set_config('Output Files', 'bool')

# Compiles statements to be included in the Debug output text file.
class Debug():
    error = ''
    config_notes = []
    monthly_notes = ''
    event_notes = []
    lotto_notes = []
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
        Debug.config_notes.append( [ key, ' = ' + str(key_value) ] )
    
    def note_monthly_date_range( self, first, last ):
        if first != {}:
            if (first['Month'] == last['Month']) and (first['Year'] == last['Year']):
                Debug.monthly_notes = 'The only Monthly Ticket Exchange included was ' + first['Date']
            else:
                Debug.monthly_notes = 'Monthly Ticket Exchange went from ' + first['Date'] + ' to ' + last['Date']
            Debug.monthly_notes += '.\n\n'

    def add_runcap_debug( self, note, index, new_entry_index_num = False ):
        if new_entry_index_num:
            Debug.run_cap_debug.append( [''] * new_entry_index_num )
        Debug.run_cap_debug[-1][index] += note

    def note_event_list( self, note, index, new_entry_index_num = False ):
        if new_entry_index_num:
            Debug.event_notes.append( [''] * new_entry_index_num )
        Debug.event_notes[-1][index] += note
    
    # Lot of information, has its own category so it can be forced to the bottom
    def add_lotto_drop_bonus( self, event_name, bonus ):
        try:
            bonus = str(bonus)
            bonus_text = '+' + ( ' ' * (len(bonus) == 1) ) + bonus
            Debug.lotto_notes.append([ event_name, '=  ' + bonus_text ])
        except:
            Debug().error_warning( 'Lotto Drop Bonus for ' + event_name + ' was not recorded.')

class DataFiles:
    def __init__( self, goals_CSV, material_list_CSV ):
        self.drop_index_count = 0
        self.list_size = 0
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

    # Interpret the Materials one group at a time, using the gaps in the Mat ID List to keep track of groups.
    # Now can use the first item to determine which group it is.
    def _interpret_group( self, reader, mat_ID_list, mat_name_list, list_index, drop_index, 
                         gaps, expected_mat ):
        goals_CSV_row = next(reader)

        if mat_name_list[list_index] == expected_mat[gaps][0]:
            list_index -= 1
            first_ID_check = 0
        else:
            try:
                first_ID_check = int(mat_ID_list[list_index])
            except ValueError:
                first_ID_check = 0
    
        if goals_CSV_row[0] != expected_mat[gaps][0] or first_ID_check > 100:
            Debug().error_warning( 'Does not seem to be the start of '+ expected_mat[gaps][1] + 
                                  '. GOALS and/or Material List CSVs may need to be updated.' )

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
                self.ID_to_index.setdefault( int(mat_ID_list[list_index]), drop_index )
                self.index_to_name.setdefault( drop_index, mat_name_list[list_index] )
                drop_index += 1

                # Adds Gems, Statues, Monuments, and XP cards to a special collective ID. 
                # Should be negative.
                if gaps > 2:
                    self.ID_to_index[2-gaps].append( int(mat_ID_list[list_index]) )

        # If zeros are removed, gaps never matter. Otherwise, they need token additions.
        self.skip_data_index[list_index] = self.remove_zeros
        list_index += 1
        if not self.remove_zeros and mat_name_list[list_index] != expected_mat[gaps + 1][0]:
            self.goals.append([0])
            self.index_to_name.setdefault( drop_index, '' )
            drop_index += 1

        # Notes that negative Mat IDs should be skipped if the entry is empty.
        if gaps > 2:
            if self.ID_to_index[2-gaps] == []:
                self.ID_to_index[2-gaps] = 'F'
        
        return reader, list_index, drop_index
    
    # 'Saber Blaze' index will be used in place of all XP drops.
    def _interpret_XP_data( self, mat_IDs, list_index, drop_index, xp_goal, xp_index_count ):
        skip = self.remove_zeros and (xp_goal == 0)
        if skip:
            drop_index = 'F'
        else:
            self.goals.append( [xp_goal] )
            self.ID_to_index[-6] = [ int(mat_IDs[list_index+1]) ]
            self.index_to_name.setdefault( drop_index, 'Class Blaze' )
            self.drop_index_count += 1

        for i in range( xp_index_count ):
            self.skip_data_index[list_index] = skip
            list_index += 1
            self.ID_to_index.setdefault( int(mat_IDs[list_index]), drop_index )
        
        self.list_size = list_index

    # Creates three dictionaries: 'ID_to_index' maps a Material's ID to placement in the Drop Matrix, 
    #   or notes that it should be skipped with an 'F' value.
    # 'index_to_name' maps placement in Drop Matrix to the corresponding Material's name.
    # 'skip_data_index' maps whether or not an entry in the Free Drop Matrix should be skipped.
    # Also transforms the data in the GOALS csv into a computable column matrix.
    def _interpret_CSVs( self, goals_CSV, material_list_CSV ):
        mat_ID_list, mat_name_list = self._find_material_CSV_data(material_list_CSV)
        
        with open( goals_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            goals_csv_row = next(reader)

            list_index = 0
            drop_index = 0

            # Warn if the gaps between Material groups do not line up.
            expected_mat = [['Proof of Hero', 'Bronze Mats'],['Seed of Yggdrasil','Silver Mats'],
                            ['Claw of Chaos','Gold Mats'], ['Gem of Saber','Blue Gems'], 
                            ['Magic Gem of Saber','Red Gems'], ['Secret Gem of Saber','Gold Gems'],
                            ['Saber Piece','Statues'], ['Saber Monument', 'Monuments'], ['Saber Blaze', 'XP']]

            for gaps in range(8):
                reader, list_index, drop_index = self._interpret_group( reader, mat_ID_list, mat_name_list, list_index, 
                                                                       drop_index, gaps, expected_mat )
            
            if mat_name_list[list_index] == expected_mat[gaps+1][0]:
                list_index -= 1
                xp_index_count = 14
            else:
                xp_index_count = 15

            self.drop_index_count = drop_index

            goals_csv_row = next(reader)
            if goals_csv_row[0] != 'Saber Blaze':
                Debug().error_warning( 'Does not seem to be the start of XP.' + 
                                      'GOALS and/or Material List CSVs may need to be updated.' )
            
            try:
                xp_goal = int(goals_csv_row[1])
            except ValueError:
                xp_goal = 0

            f.close()

        self._interpret_XP_data( mat_ID_list, list_index, drop_index, xp_goal, xp_index_count )

        if self.goals == []:
            Debug().error_warning("You have assigned no goals.")
        self.goals = np.array(self.goals)

class RunCaps():
    def __init__(self):
        self.group_to_member_count = []
        self.group_name_list = []
        self.run_cap_list = []
        #self.ticket_use_list = []
        self.matrix_col = 0
        self.run_int = ConfigList.run_int

        self.group_type_list = ['Event', 'Lotto', 'Raid', 'Bleach']
        self.config_run_cap = self.set_config_caps()

    def set_config_caps( self, make_note = False ):
        config_caps = {}
        for group_type in self.group_type_list:
            config_caps[group_type] = [ConfigList().set_config(group_type + ' Cap', 'int', make_note=make_note)]
        return config_caps

    def determine_event_caps( self, event_node ):
        debug = Debug()
        cap_debug_notes = ' ,     is default = '
        event_caps = {}
        for group_type in self.group_type_list:
            event_caps[group_type] = self.config_run_cap[group_type]

        new_cap = []
        cap_read = False
        for index in event_node:
            if index.find('Event Run Caps') >= 0:
                cap_read = 'Event'
            if index.find('Raid Run Caps') >= 0:
                if new_cap != []:
                    # Event Caps are contexually either "Event" or "Lotto" Caps
                    event_caps[cap_read] = new_cap
                    event_caps['Lotto'] = new_cap

                    # Noted as a deviation from fgf_config value
                    debug.note_event_list( ' , Event Run Cap was ' + str(new_cap), 1 )
                    cap_debug_notes = ' , Changed Caps --> '
                    new_cap = []

                cap_read = 'Raid'
            
            if cap_read:
                try:
                    new_cap.append(int(index.replace(',','')))
                except ValueError:
                    pass

        if new_cap != []:
            event_caps[cap_read] = new_cap
            debug.note_event_list( ' , Raid Run Cap was ' + str(new_cap), 1 )
            cap_debug_notes = ' , Changed Caps --> '
        
        debug.add_runcap_debug( cap_debug_notes, 1 )

        index = 1
        space = ' , '
        for group_type in self.group_type_list:
            index += 1
            if index == 5:
                space = ''
            debug.add_runcap_debug( group_type + ': ' + str(event_caps[group_type]) + space, index )
        
        return event_caps
    
    # Assembles Quests into groups based on their Quest Types
    # Applies a single Run Cap to all Quests in the same group (such as "Lotto 1")
    def assemble_group_info( self, true_name, group, quest_caps ):
        if group['Type'] and group['Count'] > 0:
            self.matrix_col += group['Count']

            try:
                group_type, group_num = group['Type'].split(' ')
            except ValueError:
                group_type = group['Type']
                group_num = '1'

            type_info = [ true_name, group_type, group_num ]
            self.group_to_member_count.append([type_info, group['Count']])
            
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
                        Debug().error_warning('Quest Type Group Number was not an integer.')
                
                if not type_info in self.group_name_list:
                    self.group_name_list.append(type_info)
                    self.run_cap_list.append([cap_input])

                    # Cap -1 so that there's some leeway for the algorithm
                    #if group_type == 'Monthly':
                    #    self.ticket_use_list.append([cap_input - 1])
                    #else:
                    #    self.ticket_use_list.append([0])
                    
    # Determines if the current Quest has the same Quest type as the last
    # If so, increments group size. Otherwise, adds the data to a list and starts a new counter.
    def add_group_info( self, add_quest_data, true_name, cur_group_type, prev_group, quest_caps = False ):
        if prev_group['Type'] != cur_group_type:
            self.assemble_group_info( true_name, prev_group, quest_caps )

            # If Quest Data is included, number of members for that group start at 1.
            return {'Type': cur_group_type, 'Count': add_quest_data}
        prev_group['Count'] += add_quest_data
        return prev_group
    
    def build_run_cap_matrix(self):
        run_matrix = np.zeros( ( len(self.run_cap_list), self.matrix_col ), dtype=int)
        #use_ticket_matrix = np.zeros( ( len(self.run_cap_list), self.matrix_col ), dtype=int)

        # For lists in group_to_member_count: i[1] is the count, 
        #   i[0] is the matching name/type info, [0][1] is type
        col = 0
        for i in self.group_to_member_count:
            start = col
            col += i[1]

            if i[0] in self.group_name_list:
                row = self.group_name_list.index(i[0])
                run_matrix[row][start:col] = 1

                #if i[0][1] == 'Monthly':
                    #use_ticket_matrix[row][start:col] = 1

        return [ run_matrix, np.array(self.run_cap_list) ]
        # ^^ add in == use_ticket_matrix, np.array(self.ticket_use_list) 