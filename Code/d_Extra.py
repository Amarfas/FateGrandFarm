import numpy as np

class PrintText():
    text = ''
    print_out = True
    set_start = 0
    set_pause = -1
    setting_print = True

    set_num = -1
    config = {}
    goals = ''

    def __init__(self):
        pass

    def main_settings( self, tests ):
        PrintText.print_out = tests['Print']
        PrintText.set_start = tests['Setting Start Num']
        PrintText.set_pause = tests['Setting Pause']

    def print( self, new_text, override = False ):
        if self.print_out or override:
            print(new_text)
        else:
            PrintText.text += new_text + '\n'
    
    def new_config( self, config ):
        PrintText.config = config
        PrintText.setting_print = True

        PrintText.set_num = self.set_num + 1
        return (self.set_num < self.set_start)

    def print_setting( self, goals = '' ):
        if self.setting_print:
            print( '\n Setting ' + str(self.set_num) + ': ' + str(self.config) + '\n' )
            PrintText.setting_print = False

            if (int(self.set_num) == self.set_pause):
                self.print_out = True

        index = goals.find('GOALS')
        if index >= 0:
            goals = goals[index:]
        PrintText.goals = goals
        PrintText.text = ''
        self.print( "{:<{}}{:<{}}".format( '  Test results for:', 23, self.goals, 0 ) )

    def check_valid( self, valid ):
        self.print('')
        if valid == False:
            print(self.text)
            print( ' Setting ' + str(self.set_num) + ': ' + str(self.config) )
            self.print( "{:<{}}{:<{}}".format( ' Test results for:', 23, self.goals, 0 ) )
            a = 1
            pass
        return valid

    def print_config( self, config = False ):
        if config:
            PrintText.config = config
        print( '\n Setting ' + str(self.set_num) + ': ' + str(self.config) + '\n' )

    def gen_unequal( self, norm, test ):
        return ' , value norm != test ; ' + str(norm) + ' != ' + str(test)

    def len_unequal( self, norm, test ):
        return ' , len norm != test ; ' + str(len(norm)) + ' != ' + str(len(test))

def build_config( change_config, events_list, check_default = False, 
                 check_set = False ):
    config_list = []
    for i in range(len(events_list)):
        list_ini = {'Folder': str(events_list[i])}

        config_list += [list_ini]

        if check_default:
            list_default = list_ini.copy()
            for key in change_config:
                list_default[key] = ''
            config_list += [list_default]

        if check_set:
            max_num_set = 0
            for key in change_config:
                if len(change_config[key]) == 0:
                    continue
                max_num_set = max( max_num_set, len(change_config[key]) )

            for i in range(max_num_set):
                list_set = list_ini.copy()
                for key in change_config:
                    if len(change_config[key]) == 0:
                        continue
                    try:
                        list_set[key] = change_config[key][i]
                    except IndexError:
                        list_set[key] = change_config[key][0]
                config_list += [list_set]
    
    return config_list

# For some combos of settings, only one check for 0 Caps is necessary
def config_skip( config_list, config, key, add, cap_set, index ):
    skip = False

    # Conditions stated below: a setting past the 2nd, if TG Half AP is yes,
    #  if Remove Zeros is no, Run Count Integer is yes
    con_2 = (key == 'Training Grounds Half AP' and config == 'y')
    con_3 = (key == 'Training Grounds Third AP' and config == 'y')
    con_4 = (key == 'Remove Zeros' and config == 'n')
    con_5 = (key == 'Run Count Integer' and config == 'y')
    
    zero_count = 0
    if (add >= 2) or con_2 or con_3 or con_4 or con_5:
        for cap in cap_set:
            if config_list[index][cap] == 0:
                zero_count += 1

        if zero_count > 0 and zero_count < len(cap_set):
            skip = True
    return skip

# Create a set of all conbinations of changes to configuration / settings
def build_all_test( change_config, events_list, line_break = False ):
    config_list = build_config( change_config, events_list )
    cap_set = []

    for key in change_config:
        if len(change_config[key]) == 0:
            continue

        if key.endswith('Cap') or key.endswith('Per Day'):
            cap_set.append(key)

        size = len(config_list)
        add = 0
        skips = 0

        for config in change_config[key]:
            # Force Remove Zeros on if line breaks are being tested
            if key == 'Remove Zeros' and line_break:
                if add > 0:
                    break
                config = 'y'

            for i in range(size):
                if config_skip( config_list, config, key, add, cap_set, i ):
                    skips += 1
                    continue

                if add > 0:
                    config_list.append(config_list[i].copy())
                config_list[i + size * add - skips][key] = config
            add += 1
    return config_list

def make_config( change_config, tests ):
    config_list = build_config( change_config, tests['Events'], 
                               tests['Check Default'], tests['Check Settings'] )
    if tests['Config Test']:
        config_list += build_all_test( change_config, tests['Events'], 
                                      tests['Line Break'] )
    
    num_set = len(config_list)
    print( 'Number of Settings: ' + str(num_set) + '\n' )
    return config_list, num_set

# Change 'fgf_config.ini' to match 'change_config' settings
def set_config( config, temp_ini ):
    if temp_ini == []:
        with open('fgf_config.ini') as f:
            temp_ini = f.readlines()
            f.close
            
        # Make sure it's not grabbing files from halfway through a previously aborted test
        if temp_ini[1] == '# TEST\n':
            with open('Code\\_debug\\Goals\\fgf_config_test.ini') as f:
                temp_ini = f.readlines()
                f.close
            
            with open('fgf_config.ini', 'w') as f:
                f.writelines(temp_ini)
                f.close
    else:
        new_ini = temp_ini.copy()
        new_ini[1] = '# TEST\n'
        line = 0
        for key in config:
            if key == 'Folder':
                continue

            while(True):
                line += 1
                if line > len(new_ini):
                    break
                if new_ini[line].startswith(key):
                    new_ini[line] = key + ' = ' + str(config[key]) + '\n'
                    break

        with open('fgf_config.ini', 'w') as f:
            f.writelines(new_ini)
            f.close
        
    return temp_ini

def check_reverb( norm, test, norm_data = {}, test_data = {}, index = 'i', coord = [], layer = 0 ):
    index_list = ['i', 'j', 'k', 'l', 'm', 'n']

    for i in range(len(norm)):
        norm_data[ 'd_' + index ] = norm[i]
        test_data[ 'd_' + index ] = test[i]
        new_coord = coord + [i]

        # If string, will just keep repeating otherwise
        if isinstance(norm[i], str):
            if norm[i] != test[i]:
                return 'F: (' + index + ') = ' + str(new_coord) + PrintText().gen_unequal( norm[i], test[i] )
            else:
                valid = 'T'
        else:
            try:
                if len(norm[i]) != len(test[i]):
                    return 'F: (' + index + ') = ' + str(new_coord) + PrintText().len_unequal( norm[i], test[i] )
            except:
                #if abs(norm[i] - test[i]) > 1e-14:
                if norm[i] != test[i]:
                    return 'F: (' + index + ') = ' + str(new_coord) + PrintText().gen_unequal( norm[i], test[i] )
                else:
                    valid = 'T'
            else:
                new_index = index + ',' + index_list[layer+1]
                valid = check_reverb( norm[i], test[i], norm_data, test_data, new_index, new_coord, layer+1 )
                if valid[0] != 'T':
                    return valid

    if len(norm) == 0 or len(test) == 0:
        if len(norm) == len(test):
            valid = 'T: Both arrays empty'
        else:
            invalid = 'norm'
            if len(test) == 0:
                invalid = 'test'
            valid = 'F: Only one was empty (' + str(invalid) + ')'

    return valid

# 1st Boolean is same values, 2nd Boolean is same shape
# 'T' or 'F' better describes the problem
def check_matrix( overall, text, norm, test, np_array = True, extra = False, extra_test = False ):
    valid_2 = 'NA'
    if np_array:
        try:
            # Checking void or empty sets
            if norm.size > 0 and test.size > 0:
                try:
                    valid_1 = (norm == test).all()
                    #valid_1 = np.allclose( norm, test, 1e-14,1e-15)
                    valid_2 = norm.shape == test.shape

                except ValueError:
                    for i in range(len(norm)):
                        valid_1 = (norm[i] == test[i]).all()
                        valid_2 = norm[i].shape == test[i].shape
                        if valid_1 == False or valid_2 == False:
                            break
            else:
                valid_1 = (len(norm) == len(test))
        except AttributeError:
            valid_1 = (norm == test)
    else:
        valid_1 = (norm == test)
    
    try:
        if len(norm) != len(test):
            valid_3 = 'F: At highest layer' + PrintText().len_unequal( norm, test )
        else:
            valid_3 = check_reverb( norm, test, {'d_': norm}, {'d_': test}, 'i', [], 0 )
    except TypeError:
        # Checking for similar errors in solving the problem if runs are 'None'
        if extra.status == extra_test.status and norm == None and test == None:
            valid_3 = 'T: prob status = ' + extra.status
        else:
            valid_3 = 'F: Different problem status: norm: ' + extra.status + ' , test: ' + extra_test.status

    PrintText().print( "{:<{}}{:<{}}".format( text, 24, str(valid_1) + ', ' + 
                        (str(valid_2) + ', ') * int(valid_2 != 'NA') + valid_3, 0 ) )

    if valid_2 == 'NA':
        valid_2 = True
    return overall and valid_1 and valid_2 and (valid_3[0] == 'T')