import os
import json
import numpy as np
import math

class PrintText():
    text = ''
    print_out = True
    set_start = 0
    set_pause = -1
    setting_print = True
    setting = ''

    set_num = -1
    run_int = {'Removed Sets': [], 'Min Removed': {'Name': 'Min; '}, 
               'Max Run Int': {'Name': 'Max; '}}
    config = {}
    goals = ''

    valid = True
    path_pre = ''
    path_pre_d = ''

    def __init__(self):
        pass

    @classmethod
    def main_settings(cls, tests, path_pre, path_pre_d):
        cls.print_out = tests['Print']
        cls.set_start = tests['Setting Start Num']
        cls.set_pause = tests['Setting Pause']

        cls.path_pre = path_pre
        cls.path_pre_d = path_pre_d

    def print(self, new_text, override = False):
        if self.print_out or override:
            print(new_text)
        else:
            PrintText.text += new_text + '\n'

    def write_print(self, new_text, add, file):
        if new_text != '':
            self.print(new_text)
            file_path = os.path.join(PrintText().debug_path(), file)
            with open(file_path, 'w') as f:
                f.write(add + new_text)
                f.close()
    
    @classmethod
    def new_config(cls, config):
        cls.config = config
        cls.setting_print = True

        cls.set_num = cls.set_num + 1
        return (cls.set_num < cls.set_start)
    
    def setting_style(self, new=''):
        text = f'{new} Setting {str(self.set_num)}: {str(self.config)}{new}'
        print(text)
        return text
    
    def print_test_results(self):
        self.print('{:<{}}{:<{}}'.format('  Test results for:', 23,
                                         self.goals, 0))

    def print_setting(self):
        if self.setting_print:
            PrintText.setting = self.setting_style('\n')
            PrintText.setting_print = False

            if (int(self.set_num) == self.set_pause):
                self.print_out = True

    def print_goals_line(self, goals=''):
        index = goals.find('GOALS')
        if index >= 0:
            goals = goals[index:]
        PrintText.goals = goals
        PrintText.text = ''
        self.print_test_results()

    def check_valid(self, new_test = ''):
        if new_test != '':
            PrintText.valid = PrintText.valid and new_test
        self.print('')
        if PrintText.valid == False:
            print(self.text)
            self.setting_style()
            self.print_test_results()
            a = 1
            pass

    def print_config(self, config=False):
        if config:
            PrintText.config = config
        self.setting_style('\n')

    @staticmethod
    def matrix_unequal(style, norm, test, index='', new_coord=''):
        if style == 'high':
            text = 'F: At highest layer , '
        else:
            text = f'F: ({index}) = {str(new_coord)} , '

        if style == 'gen':
            text += f'value norm != test ; {str(norm)} != {str(test)}'
        else:
            text += f'len norm != test ; {str(len(norm))} != {str(len(test))}'
        return text
    
    def add_run_int(self, size: dict, set = 'Min Removed'):
        original: dict = PrintText.run_int[set]
        p = 2 * (set == 'Min Removed') - 1

        for key in size.keys():    
            test = (original.get(key, 'F') == 'F')
            test = test or ((p * size[key]) < (p * original[key][key]))
            if test:
                original[key] = size  

    def _write_run_line(self, mat):
        runs = ' x {:,}'.format(mat['Runs'])
        text = 'Drop Matrix = {:,} ; '.format(mat['Drop Mat'])
        text += 'Goals x Runs = ' + str(mat['Goals']) + runs + ' ; '
        text += 'Run Matrix = {:,} ; '.format(mat['Run Mat'])
        text += 'Run List x Runs = ' + str(mat['Run List']) + runs + '\n\n'
        return text

    def _write_run_dim(self, size):
        text = ''
        min_set = PrintText.run_int['Min Removed']
        max_set = PrintText.run_int['Max Run Int']
        size_set = {'Name': 'Cur; ', ' ': size}

        for mat in [min_set, max_set, size_set]:
            if len(mat) < 2:
                continue

            for key in mat.keys():
                if key == 'Name': continue

                if key == 'Runs' or key == ' ':
                    text += mat['Name']
                else:
                    text += '     '
                text += '{:<{}}'.format(key, 8) + ': '
                text += self._write_run_line(mat[key])
        return text

    def check_failure(self, config, tool, goals):
        text = ''
        if config:
            size = {'Runs':     np.size(tool.nodes.AP_costs),
                    'Drop Mat': np.size(tool.nodes.drop_matrix),
                    'Goals':        len(tool.input.goals),
                    'Run Mat':  np.size(tool.run_mat['Matrix'])}
            size['Run List'] = int(size['Run Mat'] / size['Runs'])

            lgc1 = (size['Runs'] > 200)
            lgc2 = (size['Drop Mat'] > 4000 and size['Run Mat'] == 0)
            if lgc1 or lgc2:
                PrintText.run_int['Removed Sets'].append(self.set_num)
                self.add_run_int(size, 'Min Removed')
                return True

            text = self._write_run_dim(size)

            self.add_run_int(size, 'Max Run Int')

        self.print_setting()
        add = PrintText.setting + '\n'
        self.write_print(text, add, 'Run_Cap_Matrix_Dimensions.txt')
        self.print_goals_line(goals)
        return False
    
    def ini_path(self):
        return os.path.join(PrintText.path_pre, 'fgf_config.ini')
    
    def debug_path(self, test=False):
        if test:
            pre = PrintText.path_pre_d
        else:
            pre = PrintText.path_pre
        return os.path.join(pre, 'Code', '_debug')
    
    def ini_debug_path(self):
        debug = self.debug_path()
        return os.path.join(debug, 'fgf_config_test.ini')
    
    def data_prefix(self, line_break=False):
        if line_break:
            path1 = os.path.join(PrintText().debug_path(),
                                 'Data Files Test')
            path2 = os.path.join(PrintText().debug_path(True),
                                 'Data Files Test 2')
            file_path = [path1, path2]
        else:
            file_path = [os.path.join(PrintText.path_pre  , 'Data Files'),
                         os.path.join(PrintText.path_pre_d, 'Data Files')]
        return file_path

def build_config(change_config, tests, first=False):
    events_list = tests['Folder']
    check_default = (first and tests['Check Default'])
    check_set = (first and tests['Check Settings'])
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
                max_num_set = max(max_num_set, len(change_config[key]))

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
def config_skip(config_list, config, key, add, cap_set, index):
    skip = False

    # Conditions stated below: a setting past the 2nd, if TG Half AP is yes,
    #  if Remove Zeros is no, Run Count Integer is yes
    con_2 = (key == 'Training Grounds Half AP' and config == 'y')
    con_3 = (key == 'Training Grounds Third AP' and config == 'y')
    con_4 = (key == 'Bleached Earth Half AP' and config == 'y')
    con_5 = (key == 'Remove Zeros' and config == 'n')
    con_6 = (key == 'Run Count Integer' and config == 'y')
    
    zero_count = 0
    if (add >= 2) or con_2 or con_3 or con_4 or con_5 or con_6:
        for cap in cap_set:
            if config_list[index][cap] == 0:
                zero_count += 1

        if zero_count > 0 and zero_count < len(cap_set):
            skip = True
    return skip

# Create a set of all conbinations of changes to configuration / settings
def build_all_test(change_config, tests):
    no_skip = tests['No Skip']
    line_break = tests['Line Break']
    config_list = build_config(change_config, tests)
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
                if not no_skip and config_skip(config_list, config, 
                                               key, add, cap_set, i):
                    skips += 1
                    continue

                if add > 0:
                    config_list.append(config_list[i].copy())
                config_list[i + size*add - skips][key] = config
            add += 1
    return config_list

def make_config_list(change_config, tests):
    if len(tests['Folder']) == 0:
        tests['Folder'] = ['']

    config_list = build_config(change_config, tests, True)
    if tests['Config Test']:
        config_list += build_all_test(change_config, tests)
    
    num_set = len(config_list)
    print('Number of Settings: ' + str(num_set) + '\n')
    return config_list, num_set

def find_GOALS_tests(tests: list):
    for i in range(len(tests['Goals'])):
        if tests['Line Break']:
            temp = os.path.join(PrintText().debug_path(), 'Data Files Test',
                                'Goals', 'GOALS_')
        else:
            if tests['Goals'][i][:4] == 'Test':
                temp = os.path.join(PrintText().debug_path(),
                                    'Goals', 'GOALS_')
            else:
                temp = os.path.join(PrintText.path_pre, 'GOALS_')
        tests['Goals'][i] = os.path.join(temp + tests['Goals'][i] + '.csv')
    return tests

def find_line_break_tests(test_package: dict, tests: list):
    if tests['Line Break']:
        test_package['Data_Prefix'] = PrintText().data_prefix(True)
        
        for mode in [ 1, 2, 3 ]:
            if mode in tests['Modes']:
                text = ('Line Break Test probably cannot handle Test #'
                        + str(mode))
                PrintText().print(text, True)
                tests['Modes'].remove(mode)
    
    return test_package, tests

def prepare_test_package(change_config, tests):
    test_package = {'Data_Prefix': PrintText().data_prefix() ,
                    'Reps': tests['Reps'] , 
                    'Temp_ini': [] }

    tests = find_GOALS_tests(tests)
    config_list, test_package['Set Num'] = make_config_list(change_config,
                                                            tests)
    test_package, tests = find_line_break_tests(test_package, tests)
    
    return config_list, test_package, tests

def prev_ini_line_skip(line: str):
    skip_first_char = [' ' , '\n', '\t', '[', '#']
    for char in skip_first_char:
        if line[0] == char:
            return True
    
    skip_key = ['Plan Name', 'Goals File Name', 'Notifications',
                'Debug on Fail', 'Output Files', 'List of Areas']
    skip_key += ['AP Saved', 'Units']
    for key in skip_key:
        if line.startswith(key):
            return True
    
    return False

def prev_ini_read(temp_ini: list, folders=['']):
    config_list = [{'Folder': str(i)} for i in folders]
    for line in temp_ini:
        if prev_ini_line_skip(line):
            continue

        text = line.split('=')
        key = text[0].rstrip()
        for config in config_list:
            config[key] = text[1].lstrip().rstrip()
    
    return config_list

def initial_config(test_package: dict, tests: dict):
    config_main = []

    main_ini_path = PrintText().ini_path()
    with open(main_ini_path) as f:
        temp_ini = f.readlines()
        f.close
    
    # Make sure it's not grabbing files from halfway
    # through a previously aborted test
    if temp_ini[1] == '# TEST\n':
        if tests['Use_Last_Setting']:
            config_main += prev_ini_read(temp_ini, tests['Folder'])

        backup_ini = PrintText().ini_debug_path()
        with open(backup_ini) as f:
            temp_ini = f.readlines()
            f.close

    config_main += prev_ini_read(temp_ini)
    test_package['Temp_ini'] = temp_ini

    return config_main

# Change 'fgf_config.ini' to match 'change_config' settings
def set_config(test_package: dict):
    config: dict = test_package['Config']
    new_ini: list = test_package['Temp_ini'].copy()
    new_ini[1] = '# TEST\n'

    line = 0
    for key in config:
        if key == 'Folder' or key == 'Original Setting':
            continue

        while(True):
            line += 1
            if line > len(new_ini):
                break
            if new_ini[line].startswith(key):
                new_ini[line] = key + ' = ' + str(config[key]) + '\n'
                break

    with open(PrintText().ini_path(), 'w') as f:
        f.writelines(new_ini)
        f.close

def check_reverb(norm, test, norm_data={}, test_data={},
                 index='i', coord=[], layer=0):
    index_list = ['i', 'j', 'k', 'l', 'm', 'n']

    for i in range(len(norm)):
        norm_data['d_' + index] = norm[i]
        test_data['d_' + index] = test[i]
        new_coord = coord + [i]

        # If string, will just keep repeating otherwise
        if isinstance(norm[i], str):
            if norm[i] != test[i]:
                white_space_ignore = False
                if (norm[i].rstrip() != test[i].rstrip()) and white_space_ignore:
                    return PrintText.matrix_unequal('gen', norm[i], test[i],
                                                    index, new_coord)
                else:
                    a = [norm[i], test[i]]
                    valid = 'T'
            else:
                valid = 'T'
        else:
            try:
                if len(norm[i]) != len(test[i]):
                    return PrintText.matrix_unequal('len', norm[i], test[i],
                                                    index, new_coord)
            except:
                #if abs(norm[i] - test[i]) > 1e-14:
                if norm[i] != test[i]:
                    return PrintText.matrix_unequal('gen', norm[i], test[i],
                                                    index, new_coord)
                else:
                    valid = 'T'
            else:
                new_index = index + ',' + index_list[layer+1]
                valid = check_reverb(norm[i], test[i], norm_data, test_data,
                                     new_index, new_coord, layer + 1)
                if valid[0] != 'T':
                    return valid

    if len(norm) == 0 or len(test) == 0:
        if len(norm) == len(test):
            valid = 'T: Both arrays empty'
        else:
            invalid = 'norm'
            if len(test) == 0:
                invalid = 'test'
            valid = f'F: Only one was empty ({str(invalid)})'

    return valid

# 1st Boolean is same values, 2nd Boolean is same shape
# 'T' or 'F' better describes the problem
def check_matrix(text, kit, np_array=True, extra=False):
    norm = kit[0]
    test = kit[1]
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
            valid_3 = PrintText.matrix_unequal('high', norm, test)
        else:
            valid_3 = check_reverb(norm, test, {'d_': norm}, {'d_': test})
    except TypeError:
        # Checking for similar errors in solving the problem if runs are 'None'
        if (extra[0].status == extra[1].status
                and norm == None and test == None):
            valid_3 = 'T: prob status = ' + extra[0].status
        else:
            valid_3 = (f'F: Different problem status: norm: {extra[0].status}'
                       + f' , test: {extra[1].status}')

    text += ' equal:'
    valid_txt = (str(valid_1) + ', '
                 + (str(valid_2) + ', ') * int(valid_2 != 'NA')
                 + valid_3)
    PrintText().print('{:<{}}{:<{}}'.format(text, 24, valid_txt, 0))

    if valid_2 == 'NA':
        valid_2 = True
    PrintText.valid = (PrintText.valid and valid_1
                       and valid_2 and (valid_3[0] == 'T'))
    #PrintText().check_valid()

def record_last(test_package: dict, timer: dict):
    last_test_path = os.path.join(PrintText().debug_path(),
                                  'Last_Test_Package.json')
    with open(last_test_path, 'w', encoding='utf-8') as f:
        json.dump(test_package, f, ensure_ascii=False, indent=4)
        f.close

    last_time_path = os.path.join(PrintText().debug_path(), 'Last_Time.json')
    with open(last_time_path, 'w', encoding='utf-8') as f:
        json.dump(timer, f, ensure_ascii=False, indent=4)
        f.close

def reset_ini(test_package: dict, timer: dict):
    print('Overall Tests Were: ' + str(PrintText.valid))
    for key in timer.keys():
        if key == 'No Extreme' or key == 'Skip': continue
        if len(timer[key]) > 0:
            print(str(timer[key]) + '\n')
    
    # Resets .ini files
    main_ini_path = PrintText().ini_path()
    with open(main_ini_path, 'w') as f:
        f.writelines(test_package['Temp_ini'])
        f.close

    backup_ini = PrintText().ini_debug_path()
    with open(backup_ini, 'w') as f:
        f.writelines(test_package['Temp_ini'])
        f.close