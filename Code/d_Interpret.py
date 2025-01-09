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
    settings = {'Plan Name': '',
                'Training Grounds Half AP': False,
                'Training Grounds Third AP': False,
                'Remove Zeros': True,
                'Run Count Integer': False,
                'Monthly Ticket Per Day': 1,
                'Monthly Ticket Start Date': '',
                'Monthly Ticket End Date': '',
                'Stop Here': '',
                'Goals File Name': 'GOALS.csv',
                'Debug on Fail': True,
                'Output Files': True}
    tg_cut_AP = 1
    config = configparser.ConfigParser()

    def _config_error( self, key, key_value, text, make_note ):
        if key_value != '' and key_value != 'None' and make_note:
            if key == 'Goals File Name':
                Debug().warning('Input Goals File Name could not be found.')
            else:
                Debug().warning('Configuration "'+ key +'" was not '+ text +'.')
        return None
    
    def set_config( self, key, type = '', internal = True, make_note = True, section = 'DEFAULT' ):
        key_value = self.config[section][key]

        # Checks input GOALS file name. If it ends in .csv, assumes the file name is exactly correct.
        # Otherwise, checks if user just input an append to 'GOALS'.
        # Also checks if they thought a '_' or space were assumed.
        # If file name cannot be found, returns to default.
        if type == 'goals':
            if key_value.endswith('.csv') == False:
                key_value += '.csv'
                if key_value.startswith('GOALS') == False:
                    for i in [ '', '_', ' ' ]:
                        if glob.glob( path_prefix + 'GOALS' + i + key_value ) != []:
                            break
                    key_value = 'GOALS' + i + key_value
            
            if glob.glob( path_prefix + key_value ) == []:
                key_value = self._config_error( key, key_value, '', make_note )

        elif type == 'int':
            try:
                key_value = int(key_value.replace(',',''))
            except ValueError:
                key_value = self._config_error( key, key_value, 'an integer', make_note )

        elif type == 'float':
            try:
                key_value = float(key_value.replace(',',''))
            except ValueError:
                key_value = self._config_error( key, key_value, 'a number', make_note )

        elif type == 'bool':
            x = key_value.lower()
            if x == '1' or x == 'true' or x == 't' or x == 'yes' or x == 'y' or x == 'on':
                key_value = True
            elif x == '0' or x == 'false' or x == 'f' or x == 'no' or x == 'n' or x == 'off':
                key_value = False
            else:
                key_value = self._config_error( key, key_value, 'true/yes or false/no', make_note )

        if make_note:
            Debug().note_config(key, key_value)

        # 'Last Area' configuration, hopefully no Regions have ZZZZZ in their name in the future.
        if key == 'Stop Here' and key_value == '':
            key_value = 'ZZZZZ'
        
        if internal and key_value != None:
            ConfigList.settings[key] = key_value
        else:
            return key_value

    def check_if_date( self, key_value: str ):
        if key_value == '':
            return '', False
        else:
            key_value = key_value.split()[0].split('/')
            try:
                # Transform a 2 digit year into a 4 digit year
                year = int(key_value[2][:4])
                if year < 100:
                    year += 2000

                #new_date = [int(key_value[0][:2]), int(key_value[1][:2]), year]
                day = int(key_value[1][:2])
                month = int(key_value[0][:2])
                new_date = datetime( year, month, day )
                return new_date, False
            
            except ValueError:
                return '', ' did not have proper numbers for Day, Month, or Year.'
            except IndexError:
                return '', ' was not a full date.'
            
    def end_of_month( self, year, month ):
        year_mod = year + month // 12
        month_mod = month % 12 + 1
        next_mon = datetime( year_mod, month_mod, 1 )
        return next_mon - timedelta(seconds=1)

    def set_date_config( self, key, make_note = True, section = 'DEFAULT' ):
        key_value = self.config[section][key].lower()
        error = False

        # Checks to see if the format is 'MM/DD/YYYY'
        date_check, error = self.check_if_date( key_value )

        # If a start date is not input, then set the start date to today
        if key == 'Monthly Ticket Start Date':
            if date_check == '':
                # Fail-safe because you can't subtract offset-naive and offset-aware datetimes
                key_value = datetime.now(ZoneInfo("America/New_York"))
                year, month, day = key_value.year, key_value.month, key_value.day
                key_value = datetime( year, month, day )
            else:
                key_value = date_check

        elif key_value != '':
            # If input is not in 'MM/DD/YYYY' format, check to see if it's in '# Day' format
            # If it is in this format, end date is found by adding the time skip to the start date
            if date_check != '':
                key_value = date_check
            else:
                key_space_split = key_value.split()
                try:
                    time_skip, time_frame = int(key_space_split[0]), key_space_split[1]
                except ValueError:
                    key_value = ''
                else:
                    start: datetime = self.settings['Monthly Ticket Start Date']
                    if time_frame[:3] == 'yea':
                        error = False
                        key_value = datetime(start.year + time_skip, start.month, start.day)

                    elif time_frame[:3] == 'mon':
                        error = False
                        new_month_calc = start.month + time_skip - 1
                        new_month = new_month_calc % 12 + 1
                        new_year = start.year + new_month_calc // 12

                        # Makes sure there isn't an error later because the time lapsed month has fewer days
                        last_day_of_month = (self.end_of_month( new_year, new_month )).day
                        key_value = datetime(new_year, new_month, min(start.day, last_day_of_month))

                    elif time_frame[:3] == 'day':
                        error = False
                        key_value = start + timedelta(days = time_skip)

                    else:
                        error = ' did not say whether time should elapse by days, months, or years.'
                        key_value = ''
        
        if error:
            Debug().warning( 'Configuration "' + key + error )
        
        if make_note:
            if key_value == '':
                Debug().note_config(key, '')
            else:
                Debug().note_config(key, key_value.strftime('%m/%d/%Y'))

        ConfigList.settings[key] = key_value

    # Find if examined month is within date range
    def check_date( self, month, year ):
        days_left = -1
        error = False
        start: datetime = self.settings['Monthly Ticket Start Date']
        end: datetime = self.settings['Monthly Ticket End Date']

        try:
            if year < 100:
                year += 2000
            end_of_month = self.end_of_month( year, month )
            after_start = (end_of_month - start).days > 0

            start_of_month = datetime( year, month, 1 )
            before_end = (end == '') or (start_of_month - end).days < 0

            # Find how many days to count tickets for
            if after_start and before_end:
                if end != '' and month == end.month and year == end.year:
                    days_left = end.day
                else:
                    days_left = end_of_month.day

                if month == start.month and year == start.year:
                    days_left -= start.day

        except ValueError:
            error = True
        
        ticket_mult = min( self.settings['Monthly Ticket Per Day'], 4)
        month_cap = { 'Monthly': [ticket_mult * days_left] }
        month_name = end_of_month.strftime('%b %Y')

        return month_cap, month_name, error

    def read_config_ini(self):
        ConfigList.config.read( path_prefix + 'fgf_config.ini' )

        self.set_config('Debug on Fail', 'bool')
        Debug.notifications = self.set_config('Notifications', 'bool', False)
        self.set_config('Plan Name')

        self.set_config('Training Grounds Half AP', 'bool')
        self.set_config('Training Grounds Third AP', 'bool')
        ConfigList.tg_cut_AP = 1
        if self.settings['Training Grounds Third AP']:
            ConfigList.tg_cut_AP = 3
        elif self.settings['Training Grounds Half AP']:
            ConfigList.tg_cut_AP = 2

        self.set_config('Remove Zeros', 'bool')
        self.set_config('Run Count Integer', 'bool')

        self.set_config('Monthly Ticket Per Day', 'int')
        self.set_date_config('Monthly Ticket Start Date')
        self.set_date_config('Monthly Ticket End Date')

        self.set_config('Stop Here')
        self.set_config('Goals File Name', 'goals')
        self.set_config('Output Files', 'bool')


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
    
    def warning( self, note, threshold = 0, message = 2 ):
        if message >= threshold:
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
            Debug().warning( 'Lotto Drop Bonus for ' + event_name + ' was not recorded.')

class DataFiles:
    def __init__( self, goals_CSV, material_list_CSV ):
        self.remove_zeros = ConfigList.settings['Remove Zeros']

        # Free Quest section
        self.csv_col_total = 0
        self.skip_data_index = {}

        # Event Quest and Monthly Ticket section
        self.mat_index_total = 0
        self.ID_to_index = {-1: [], -2: [], -3: [], -4: [], -5: [], -6: 'F'}

        # Planner section
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
    def _interpret_group( self, reader, ID_list, name_list, csv_i, mat_i, gaps ):
        # Warn if the gaps between Material groups do not line up.
        expected = [['Proof of Hero', 'Bronze Mats'],['Seed of Yggdrasil','Silver Mats'],
                    ['Claw of Chaos','Gold Mats'], ['Gem of Saber','Blue Gems'], 
                    ['Magic Gem of Saber','Red Gems'], ['Secret Gem of Saber','Gold Gems'],
                    ['Saber Piece','Statues'], ['Saber Monument', 'Monuments'], 
                    ['Saber Blaze', 'EXP']]
        
        goals_CSV_row = next(reader)

        if name_list[csv_i] == expected[gaps][0]:
            csv_i -= 1
            first_ID_check = 0
        else:
            try:
                first_ID_check = int(ID_list[csv_i])
            except ValueError:
                first_ID_check = 0
    
        if goals_CSV_row[0] != expected[gaps][0] or first_ID_check > 100:
            Debug().warning( 'Does not seem to be the start of '+ expected[gaps][1] + 
                                  '. GOALS and/or Material List CSVs may need to be updated.' )

        while goals_CSV_row[0][0:2] != '!!':
            try:
                mat_goal = int(goals_CSV_row[1].replace(',',''))
            except ValueError:
                mat_goal = 0
            
            # Flag whether or not to remove this material from the Drop Matrix.
            skip = self.remove_zeros and (mat_goal == 0)
            self.skip_data_index[csv_i] = skip

            csv_i += 1
            goals_CSV_row = next(reader)
            
            if skip:
                self.ID_to_index.setdefault( int(ID_list[csv_i]), 'F' )
            else:
                self.goals.append( [mat_goal] )
                self.ID_to_index.setdefault( int(ID_list[csv_i]), mat_i )
                self.index_to_name.setdefault( mat_i, name_list[csv_i] )
                mat_i += 1

                # Adds Gems, Statues, Monuments, and XP cards to a special collective ID. 
                # Should be negative.
                if gaps > 2:
                    self.ID_to_index[2-gaps].append( int(ID_list[csv_i]) )

        # If zeros are removed, gaps never matter. Otherwise, they need token additions.
        self.skip_data_index[csv_i] = self.remove_zeros
        csv_i += 1
        if not self.remove_zeros and name_list[csv_i] != expected[gaps + 1][0]:
            self.goals.append([0])
            self.index_to_name.setdefault( mat_i, '' )
            mat_i += 1

        # Notes that negative Mat IDs should be skipped if the entry is empty.
        if gaps > 2:
            if self.ID_to_index[2-gaps] == []:
                self.ID_to_index[2-gaps] = 'F'
        
        return reader, csv_i, mat_i
    
    # 'Saber Blaze' index will be used in place of all XP drops.
    def _interpret_XP_data( self, mat_IDs, csv_i, mat_i, xp_goal, xp_index_count ):
        skip = self.remove_zeros and (xp_goal == 0)
        if skip:
            mat_i = 'F'
        else:
            self.goals.append( [xp_goal] )
            self.ID_to_index[-6] = [ int(mat_IDs[csv_i+1]) ]
            self.index_to_name.setdefault( mat_i, 'Class Blaze' )
            self.mat_index_total += 1

        for i in range( xp_index_count ):
            self.skip_data_index[csv_i] = skip
            csv_i += 1
            self.ID_to_index.setdefault( int(mat_IDs[csv_i]), mat_i )
        
        self.csv_col_total = csv_i

    # Creates three dictionaries: 'ID_to_index' maps a Material's ID to placement in the Drop Matrix, 
    #   or notes that it should be skipped with an 'F' value.
    # 'index_to_name' maps placement in Drop Matrix to the corresponding Material's name.
    # 'skip_data_index' maps whether or not an entry in the Free Drop Matrix should be skipped.
    # Also transforms the data in the GOALS csv into a computable column matrix.
    def _interpret_CSVs( self, goals_CSV, material_list_CSV ):
        ID_list, name_list = self._find_material_CSV_data(material_list_CSV)
        
        with open( goals_CSV, newline = '', encoding = 'Latin1' ) as f:
            reader = csv.reader(f)
            goals_csv_row = next(reader)

            csv_i = 0
            mat_i = 0

            for gaps in range(8):
                reader, csv_i, mat_i = self._interpret_group( reader, ID_list, name_list, csv_i, 
                                                                mat_i, gaps )
            
            if name_list[csv_i] == 'Saber Blaze':
                csv_i -= 1
                xp_index_count = 14
            else:
                xp_index_count = 15

            self.mat_index_total = mat_i

            goals_csv_row = next(reader)
            if goals_csv_row[0] != 'Saber Blaze':
                Debug().warning( 'Does not seem to be the start of XP.' + 
                                      'GOALS and/or Material List CSVs may need to be updated.' )
            
            try:
                xp_goal = int(goals_csv_row[1])
            except ValueError:
                xp_goal = 0

            f.close()

        self._interpret_XP_data( ID_list, csv_i, mat_i, xp_goal, xp_index_count )

        if self.goals == []:
            Debug().warning("You have assigned no goals.")
        self.goals = np.array(self.goals)

class RunCaps():
    def __init__(self):
        self.group_list = []
        self.relevant_groups = []
        self.run_cap_list = []
        self.matrix_col = 0

        self.group_type_list = ['Event', 'Lotto', 'Raid', 'Bleach']
        self.config_default = self.set_config_caps()

    def set_config_caps( self, make_note = False ):
        config_caps = {'Event': [2000], 
                       'Lotto': [2000], 
                        'Raid': [500], 
                      'Bleach': [100]}
        for group_type in self.group_type_list:
            group_cap = ConfigList().set_config(group_type + ' Cap', 'int', False, make_note)
            if group_cap != None:
                config_caps[group_type] = [group_cap]
        return config_caps

    def determine_event_caps( self, event_csv ):
        debug = Debug()
        cap_debug_notes = ' ,     is default = '
        event_caps = self.config_default.copy()
        #event_caps = {}
        #for group_type in self.group_type_list:
        #    event_caps[group_type] = self.config_default[group_type]

        new_cap = []
        cap_read = False
        for col in event_csv:
            if col.find('Event Run Caps') >= 0:
                cap_read = 'Event'
            if col.find('Raid Run Caps') >= 0:
                if new_cap != []:
                    # Event Caps are contexually either "Event" or "Lotto" Caps
                    event_caps[cap_read] = new_cap
                    event_caps['Lotto'] = new_cap

                    # Noted as a deviation from fgf_config value
                    debug.note_event_list( ' , Event Run Cap was '+ str(new_cap), 1 )
                    cap_debug_notes = ' , Changed Caps --> '
                    new_cap = []

                cap_read = 'Raid'
            
            if cap_read:
                try:
                    new_cap.append(int(col.replace(',','')))
                except ValueError:
                    pass

        if new_cap != []:
            event_caps[cap_read] = new_cap
            debug.note_event_list( ' , Raid Run Cap was ' + str(new_cap), 1 )
            cap_debug_notes = ' , Changed Caps --> '
        
        debug.add_runcap_debug( cap_debug_notes, 1 )

        col = 1
        space = ' , '
        for group_type in self.group_type_list:
            col += 1
            if col == 5:
                space = ''
            debug.add_runcap_debug( group_type + ': ' + str(event_caps[group_type]) + space, col )
        
        return event_caps
    
    # Assembles Quests into groups based on their Quest Types
    # Applies a single Run Cap to all Quests in the same group (such as "Lotto 1")
    def assemble_group_info( self, group ):
    #def assemble_group_info( self, group, caps ):
        if group['Type'] and group['Count'] > 0:
            self.matrix_col += group['Count']

            try:
                group_class, group_num = group['Type'].split(' ')
            except ValueError:
                group_class = group['Type']
                group_num = '1'

            group['Full Type'] = [ group['Quest'], group_class, group_num ]
            self.group_list.append(group)
            
            # For the purposes of Run Caps, Pseudo-Lottos are Lottos
            if group_class == 'Pseudo':
                group_class = 'Lotto'
            cap_list = group['Cap'].get(group_class)
            #cap_list = caps.get(group_class)
            
            if cap_list == None or len(cap_list) == 0 or cap_list[0] == None:
                cap_input = None
            else:
                if len(cap_list) == 1:
                    cap_input = cap_list[0]
                else:
                    try:
                        cap_input = cap_list[ (int(group_num) - 1) % len(cap_list) ]
                    except ValueError:
                        Debug().warning('Quest Type Number was not an integer.')
                
                if not group['Full Type'] in self.relevant_groups:
                    self.relevant_groups.append(group['Full Type'])
                    self.run_cap_list.append([cap_input])
                    
    # Determines if the current Quest has the same Quest type as the last
    # If so, increments group size. Otherwise, adds the data to a list and starts a new counter.
    def add_group_info( self, add_quest_data, cur_group_type, prev_group ):
    #def add_group_info( self, add_quest_data, cur_group_type, prev_group, caps = False ):
        if prev_group['Type'] != cur_group_type:
            self.assemble_group_info( prev_group )
            #self.assemble_group_info( prev_group, caps )

            # If Quest Data is included, number of members for that group start at 1.
            new_group = {'Quest': prev_group['Quest'], 'Type': cur_group_type, 
                         'Count': add_quest_data, 'Cap': prev_group['Cap']}
                         #'Count': add_quest_data}
            return new_group
        
        prev_group['Count'] += add_quest_data
        return prev_group
    
    def build_run_cap_matrix(self):
        row_num = len(self.run_cap_list)
        col_num = self.matrix_col
        matrix = {'Event': [''] * row_num, 
                  'List': np.array(self.run_cap_list),
                  'Matrix': np.zeros( ( row_num, col_num ), dtype=int),
                  'Bleach': -1,
                  'Monthly': -1}

        # For lists in group_to_member_count: group[1] is the count, 
        #   group[0] is the matching name/type info, [0][1] is type
        col = 0
        for group in self.group_list:
            start = col
            col += group['Count']

            if group['Full Type'] in self.relevant_groups:
                row = self.relevant_groups.index(group['Full Type'])
                matrix['Event'][row] = group['Quest']
                matrix['Matrix'][row][start:col] = 1

                # Hedge in case the Run Caps for Bleach and others are too high.
                # Even if Planner removes Run Caps, Monthly limits stay
                if group['Type'] == 'Bleach':
                    matrix['Bleach'] = row
                elif group['Type'] == 'Monthly' and matrix['Monthly'] < 0:
                    matrix['Monthly'] = row

        return matrix