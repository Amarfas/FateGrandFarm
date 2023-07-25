import configparser
import csv
import glob
import numpy as np
import cvxpy as cp

# Makes it so the program works whether it's started in the 'FarmingGrandOrder' overarching directory or the 'FarmGrandOrder' folder.
def standardize_path():
    pathDir = ''
    if glob.glob('FateGrandFarm') == []:
        return '..\\' + pathDir
    return pathDir

# Compiles statements to be included in the Debug output text file.
class Debug:
    def __init__( self, path_prefix ):
        self.file_name = ''
        self.error = ''
        self.config_notes = 'The Path Prefix is: ' + path_prefix + '\n'
        self.end_notes = ''

        self.config = configparser.ConfigParser()
        self.config.read( path_prefix + 'config\\farmgo_config.ini' )

        self.notifications = True
        self.notifications = self.note_config('Notifications', 'bool')
    
    def error_warning( self, note ):
        note = '!! ' + note
        if self.notifications:
            print(note)
        self.error += note + '\n'

    def note_config( self, key, type = '', section = 'DEFAULT' ):
        keyValue = self.config[section][key]

        if type == 'int':
            try:
                keyValue = int(keyValue)
            except:
                if key != 'Event Cap' and keyValue != '':
                    self.error_warning( 'Configuration "' + key + '" was not a number.')
                keyValue = 'NaN'

        if type == 'float':
            try:
                keyValue = float(keyValue)
            except:
                self.error_warning( 'Configuration "' + key + '" was not a number.')
                keyValue = 'Nan'

        if type == 'bool':
            x = keyValue.lower()
            if x == '1' or x == 'true' or x == 't' or x == 'yes' or x == 'y' or x == 'on':
                keyValue = True
            else:
                if not (x == '0' or x == 'false' or x == 'f' or x == 'no' or x == 'n' or x == 'off'):
                    self.error_warning( 'Configuration "' + key + '" was not yes or no/true or false.')
                keyValue = False
    
        self.config_notes += key + ' = ' + str(keyValue) + '\n'

        # 'Last Area' configuration
        if key == 'Last Area' and keyValue == '':
            return 'ZZZZZ'
        return keyValue

    def make_note( self, note , notice = False ):
        if self.notifications and notice:
            print(note)
        self.end_notes += note

class InputData:
    def __init__( self, goals_CSV, material_list_CSV, debug, remove_zeros = False ):
        self.mat_count = 0
        self.mat_total = 0
        self.remove_zeros = remove_zeros

        self.ID_to_index = {-1: [], -2: [], -3: [], -4: [], -5: [], -6: 'T'}
        self.skip_data_index = {}
        self.index_to_name = {}

        self.goals = []
        self._interpret_CSVs( goals_CSV, material_list_CSV, debug )
    
    # Interpret the Materials by groups between their gaps.
    def _interpret_group( self, reader, mat_ID, mat_name, count, index, gaps, error, debug: Debug ):
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
    def _interpret_CSVs( self, goals_CSV, material_list_CSV, debug: Debug ):
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
                reader, count, index = self._interpret_group( reader, mat_IDs, mat_names, count, index, gaps, errors[gaps], debug )

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