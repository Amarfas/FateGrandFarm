import glob
import math
import os
import numpy as np
import cvxpy as cp
import time
import Interpret as Inter
from Quest_Data import QuestData

class Solution():
    saved_format = -1

    daily_ticket = 1
    run_count_int = False

    def __init__(self, prob: cp.Problem, runs: cp.Variable, AP_costs,
                 index_to_name, run_cap_matrix ):
        self.status = prob.status
        self.AP_costs = AP_costs
        self.index_to_name = index_to_name
        self.run_caps = run_cap_matrix

        self.run_int, self.total_AP = self._interpret_data( prob, runs )
        self.ap_saved = []

        self.ap_empty = ['','','']
        if Solution.saved_format >= 1:
            self.ap_empty = ['','','','']

    def _interpret_data( self, prob: cp.Problem, runs: cp.Variable ):
        if prob.status == 'infeasible' and prob.value == math.inf:
            return runs.value, prob.value
        
        elif prob.status == 'unbounded':
            return runs.value, prob.value
        
        # Makes Run counts integers.
        elif self.run_count_int:
            return runs.value, int(prob.value)
        
        else: 
            run_int = np.zeros( (len(self.AP_costs[0]),1) , dtype = int)
            count = 0
            for i in runs.value:
                if i[0] < 0.1: 
                    run_int[count,0] = 0
                elif (i[0] - math.floor(i[0])) < 0.01:
                    run_int[count,0] = int(i[0])
                else: 
                    run_int[count,0] = int(math.ceil(i[0]))
                count += 1
            
            total_AP = int( self.AP_costs @ runs.value )
            
            return run_int, total_AP
        
    def get_AP_saved( self, read: list, i ):
        if Solution.saved_format >= 0:
            if i < 0:
                read.append( self.ap_empty )
            else:
                read.append( self.ap_saved[i] )

    def _finish_saved( self, *entries ):
        final = ['  AP Saved =']
        for add in entries:
            final.append(add)
        return final
        
    def _saved_format( self, ap_diff, units, format = '' ):
        f = '  '
        if format == '':
            result = f"{ap_diff:,}"
        elif format == '2f':
            result = f"{ap_diff:,.2f}"
        elif format == '3g':
            result = f"{ap_diff:,.3g}"

        if format == '2f' or format == '3g':
            res = result.split('.')
            if len(res) == 1:
                res.append('')
            else:
                res[1] = '.' + res[1]
            return self._finish_saved( res[0], res[1], f + units )

        else:
            return self._finish_saved( result, f + units )
        
    def _units_convert( self, ap_diff, i ):
        units_setting = Solution.saved_format
        ap_cost = self.AP_costs[0][i]
        
        if units_setting == 0:
            units, format = 'AP', ''
        
        elif units_setting > 0:
            if (ap_cost == 0):
                caps = self.run_caps
                for j in range(len(caps['Matrix'])):
                    if caps['Matrix'][j][i] > 0:
                        break
                total_tickets = caps['List'][j][0]

                if units_setting == 1:
                    ap_diff *= self.daily_ticket / total_tickets
                    units, format = 'AP / day', '2f'
                else:
                    ap_diff /= total_tickets
                    units, format = 'AP / ticket', '2f'

            else:
                ap_diff /= self.run_int[i][0]
                if units_setting == 1:
                    units, format = 'AP / run', '3g'
                else:
                    ap_diff /= ap_cost
                    units, format = 'AP / AP', '3g'
                
        return self._saved_format( ap_diff, units, format )
    
    def add_saved_ap( self, new_AP, index ):
        if new_AP == 'F':
            new_val = self.ap_empty

        elif isinstance( new_AP, int ):
            new_AP -= self.total_AP
            new_val = self._units_convert( new_AP, index[0] )

        elif new_AP == 'infeasible' or new_AP == 'unbounded':
            new_val = self._finish_saved('inf')

        else:
            new_val = self._finish_saved(new_AP)
        
        for i in range(len(index)):
            self.ap_saved.append(new_val)

    def read_settings(settings):
        Solution.run_count_int = settings['Run Count Integer']
        Solution.daily_ticket = settings['Monthly Ticket Per Day']
        run_AP_saved = settings['AP Saved']
        saved_units = settings['Units']

        if run_AP_saved and (saved_units > 2 or saved_units < 0):
            error = '"AP Saved Units" was not set to 0, 1, or 2. '
            error += 'Setting to 0 (AP).'
            Inter.Debug().warning(error)
            saved_units = 0
        
        if run_AP_saved:
            Solution.saved_format = saved_units


class Planner():
    def __init__( self, quest_data: QuestData, data_files: Inter.DataFiles, 
                 run_cap_mat: dict, message = 2 ) -> None:
        settings = Inter.ConfigList.settings

        # Main Settings
        self.run_count_int = settings['Run Count Integer']
        self.message = message

        # Main Data for Analysis
        self.drop_matrix = np.transpose( quest_data.drop_matrix )
        self.AP_costs = np.transpose( quest_data.AP_costs )
        self.run_size = np.size( self.AP_costs )
        self.goals = data_files.goals.copy()
        self.run_caps = run_cap_mat.copy()

        # Data to Help Interpret Analysis
        self.mat_index_total = data_files.mat_index_total
        self.index_to_name = data_files.index_to_name.copy()

        self.recorded_months = quest_data.recorded_months
        self.quest_names = quest_data.quest_names

        Solution.read_settings(settings)

        # Primarily for debugging
        self.debug = {'Goals': self.goals.copy(),
                      'Index to Name': self.index_to_name.copy(),
                      'Run Caps': self.run_caps.copy()}

    def _warning( self, error, threshold = 1, message = '', pos = 0 ):
        if message == '':
            message = self.message
        Inter.Debug().warning( error, threshold, message, pos )

    def _check_mats_available( self ):
        for i in range(self.mat_index_total):
            for drop_rate in self.drop_matrix[i]:
                if drop_rate > 0:
                    break
            else:
                if self.index_to_name[i] != '':
                    error = 'Obtaining any ' + self.index_to_name[i]
                    error += ' is impossible with these restrictions.'
                    self._warning( error, 2, pos = 1 )
                    self.index_to_name[i] = ''
                    self.goals[i] = 0
    
    def _solver( self, cut = False, drop_matrix = False, run_caps = False, AP_costs = False ):
        # Checks to see if this is for AP Saved using modified data
        run_size = self.run_size - cut
        if not cut:
            drop_matrix = self.drop_matrix
            run_caps = self.run_caps
            AP_costs = self.AP_costs

        # Set 'runs' variable
        if self.run_count_int:
            runs = cp.Variable( (run_size,1) , integer=True)
        else: 
            runs = cp.Variable( (run_size,1) , nonneg=True )

        # Set 'constraints' conditions 
        constraints = [ drop_matrix @ runs >= self.goals ]
        if self.run_count_int:
            constraints.append( np.eye(run_size) @ runs >= np.zeros((run_size,1), dtype=int) )
        if run_caps['Matrix'].any():
            constraints.append( run_caps['Matrix'] @ runs <= run_caps['List'] )

        # Set the 'objective' condition and run analysis
        objective = cp.Minimize( AP_costs @ runs )

        prob = cp.Problem( objective , constraints )
        prob.solve()

        return prob, runs

    def _backup_remove_non_months( self, row ):
        self._warning('Problem will be run again after removing all Run Caps.')

        row_num = len(self.run_caps['Matrix'])
        col_num = len(self.run_caps['Matrix'][0])
        shape = ( row_num - row , col_num )

        dele = np.zeros( ( row_num, col_num ), dtype=bool )
        dele[row:] = True
        new_matrix = np.reshape( self.run_caps['Matrix'][dele,...], shape )
        self.run_caps['Matrix'] = new_matrix

        dele = np.zeros( row_num, dtype=bool )
        dele[row:] = True
        self.run_caps['List'] = self.run_caps['List'][dele,...]
    
    def _backup_remove_bleach( self, row ):
        self._warning('Problem will be run again after removing Bleach Caps.')
        self.run_caps['Matrix'] = np.delete( self.run_caps['Matrix'], row, 0)
        self.run_caps['List'] = np.delete( self.run_caps['List'], row, 0)
    
    # Remove Bleached Earth Run Caps first, because of the exclusive mats
    # If that doesn't work, keep only the constraints for Monthly Tickets.
    def _remove_runcaps( self, prob, runs ):
        run_caps = self.run_caps['Event']

        for row in range(len(run_caps)):
            if run_caps[row] == 'Free Quests':
                self._backup_remove_bleach(row)
                prob, runs = self._solver()

                if prob.status == 'optimal':
                    break
                else:
                    self._warning('Analysis was still a failure.')
            
            if run_caps[row] in self.recorded_months:
                self._backup_remove_non_months(row)
                prob, runs = self._solver()

                if prob.status != 'optimal':
                    self._warning('Analysis was still a failure.')
                break

        return prob, runs

    def _backup_planner( self, prob: cp.Problem, runs ):
        if self.message >= 1:
            Inter.Debug().warning( 'This solution is or was: ' + prob.status )

        # Run Count Integer removed because it applies extra constraints
        #   which slow the analysis.
        if self.run_count_int:
            error = 'Run Count Integer will be removed for further analysis.'
            self._warning(error)

            self.run_count_int = False
            Solution.run_count_int = False
        
        if prob.status == 'infeasible':
            error = 'The applied Run Caps likely made the Goals impossible.'
            self._warning(error)
            prob, runs = self._remove_runcaps( prob, runs )

        if prob.status == 'unbounded':
            prob, runs = self._solver()

        return prob, runs
    
    def _correct_end( self, end_i, default ):
        if end_i == '':
            return default
        else:
            return end_i + 1
    
    def delete_matrix( self, matrix, start_i = 0, end_i = '', axis = 0 ):
        dim = 1
        if isinstance( matrix[0], np.ndarray ):
            dim = 2

        row_num = len(matrix)
        if dim == 1:
            end_i = self._correct_end( end_i, row_num )
            dele = np.ones( row_num, dtype=bool )
            dele[start_i:end_i] = False
            return matrix[dele,...]

        elif dim == 2:
            col_num = len(matrix[0])
            dele = np.ones( ( row_num, col_num ), dtype=bool )

            if axis == 0:
                end_i = self._correct_end( end_i, row_num )
                dele[start_i:end_i] = False
                shape = ( row_num - end_i + start_i , col_num )
            else:
                end_i = self._correct_end( end_i, col_num )
                dele[:,start_i:end_i] = False
                shape = ( row_num, col_num - end_i + start_i )

            return np.reshape( matrix[dele,...], shape )
    
    def _cut_i_matrix( self, matrix, index, axis = 0 ):
        if isinstance( matrix, np.ndarray ):
            new_mat = np.copy( matrix )

            if len(index) == 1:
                new_mat = np.delete( new_mat, index[0], axis )
            else:
                new_mat = self.delete_matrix(new_mat, index[0], index[-1], axis )

        elif isinstance( matrix, list ):
            new_mat = matrix.copy()

            for t in range(len(index)):
                if axis == 0:
                    new_mat.pop(index[0])
                if axis == 1:
                    for i in range(len(matrix)):
                        new_mat[i].pop(index[0])
        return new_mat
    
    def _cut_i_dict( self, matrix, index, monthly = False ):
        new_mat = {}
        new_cut = self._cut_i_matrix( matrix['Matrix'], index, 1 )

        if monthly:
            for i in range(len(matrix['Matrix'])):
                if matrix['Matrix'][i][index[0]] > 0:
                    new_mat['Event'] = self._cut_i_matrix( matrix['Event'], [i] )
                    new_mat['List'] = self._cut_i_matrix( matrix['List'], [i] )
                    new_mat['Matrix'] = self._cut_i_matrix( new_cut, [i] )
                    return new_mat

        new_mat['Event'] = np.copy( matrix['Event'] )
        new_mat['List'] = matrix['List'].copy()
        new_mat['Matrix'] = new_cut
        return new_mat

    def _cut_planner( self, index, monthly = False ):
        new_drops = self._cut_i_matrix( self.drop_matrix, index, 1 )
        new_run_caps = self._cut_i_dict( self.run_caps, index, monthly )
        new_costs = self._cut_i_matrix( self.AP_costs, index, 1 )

        prob, runs = self._solver( len(index), new_drops, new_run_caps, new_costs )

        if prob.status == 'optimal':
            sol = Solution( prob, runs, new_costs, self.index_to_name, new_run_caps )
            return sol.total_AP
        else:
            return prob.status
        
    def _calculate_saved_months( self, sol: Solution, start ):
        prev_month = self.quest_names[start]
        index = []
        used = []

        for i in range( start, len(sol.run_int) ):
            cur_month = self.quest_names[i]

            if cur_month != prev_month:
                if len(used) > 0:
                    new_AP = self._cut_planner( index, True )
                else:
                    new_AP = 'F'
                sol.add_saved_ap( new_AP, index )
                
                index = []
                used = []

            index.append(i)
            if int(sol.run_int[i]) > 0:
                used.append(i)
                
            prev_month = cur_month
        
        if len(used) > 0:
            new_AP = self._cut_planner( index, True )
        else:
            new_AP = 'F'
        sol.add_saved_ap( new_AP, index )

    def _calculate_AP_saved( self, sol: Solution ):
        for i in range(len(sol.run_int)):
            if self.quest_names[i] in self.recorded_months:
                sol = self._calculate_saved_months( sol, i )
                break

            if int(sol.run_int[i]) > 0:
                new_AP = self._cut_planner([i])
            else:
                new_AP = 'F'
            sol.add_saved_ap( new_AP, [i] )

    # 'message' corresponds to how important the warnings for this run will be.
    # If 'message' is not higher than 'warning's threshold (default = 0),
    #    text will not be printed.
    def planner( self ):
        self._check_mats_available()

        prob, runs = self._solver()

        if prob.status != 'optimal':
            prob, runs = self._backup_planner( prob, runs ) 

        sol = Solution(prob, runs, self.AP_costs, 
                       self.index_to_name, self.run_caps)

        if (prob.status == 'optimal') and (sol.saved_format >= 0) and self.run_size > 1:
            self._calculate_AP_saved(sol)

        return sol

class Output:
    text_written = []
    not_test = True
    
    def __init__(self) -> None:
        pass

    def final_write( self, file_name, text, main = False ):
        if main:
            Output.text_written.append( [file_name, text.split('\n')] )

        if Output.not_test:
            with open( file_name, 'w') as f:
                f.write(text)
                f.close()

    def console_print( self, text, next_line = True ):
        if Output.not_test:
            print( text )
        return text + '\n' * next_line
    
    # Finds an appropriate indentation between each column of data.
    def find_indent( self, text ):
        if isinstance( text, dict ):
            indent = {}
            for key in text.keys():
                indent[key] = self.find_indent(text[key])
                return indent
            
        elif len(text) > 0 and isinstance( text[0], list ):
            indent = [0] * len(max( text, key = len ))
            for line in text:
                for j in range(len(line)):
                    # Want a bit of padding if there are entries, 
                    #    but no spacing if there aren't
                    new_longest = len(line[j]) + 1
                    if new_longest > (indent[j] + 1):
                        indent[j] = new_longest
            return indent
        
        else:
            indent = 0
            for j in range(len(text)):
                new_longest = len(text[j]) + 1
                if new_longest > (indent + 1):
                    indent = new_longest
            return indent
        
    def read_AP_saved( self, ap, ind ):
        if len(ap) == 3:
            return "{:<{}}{:>{}}{:<{}}".format(ap[0], ind[0], ap[1], 
                                               ind[1], ap[2], ind[2])
        else:
            txt1 = "{:<{}}{:>{}}".format(ap[0], ind[0], ap[1], ind[1])
            txt2 = "{:<{}}{:<{}}".format(ap[2], ind[2], ap[3], ind[3])
            return txt1 + txt2

    def write_farming_plan( self, txt, two = False ):
        output = ''
        output_m = ''
        
        fmt = {'Qst': "{:<{}}", 'Run': "{:>{}}", 'Box': "{:<{}}",
               'Drop': "{:>{}}", 'Mat': "{:<{}}", 'Save': "{:>{}}"}
        ind = {}
        for key in txt.keys():
            ind[key] = self.find_indent(txt[key])

        for i in range(len(txt['Qst'])):
            lead = ''
            for key in [ 'Qst', 'Run' ]:
                lead += fmt[key].format( txt[key][i], ind[key] )

            tail = ''
            if txt['Save'] != []:
                tail = self.read_AP_saved( txt['Save'][i], ind['Save'] )

            if two:
                # Adds number of boxes farmed
                if tail:
                    new_m = lead + fmt['Box'].format( txt['Box'][i], ind['Box'] )
                    new_m += tail
                else:
                    new_m = lead + txt['Box'][i]
                output_m += self.console_print( new_m )
                lead += '  =  '

            # Adds average acquired Mats for 'Farming Plan Drops'
            output += lead
            for j in range(len(ind['Drop'])):
                if j > len(txt['Drop'][i]) - 1:
                    if two or Solution.saved_format < 0:
                        break
                    else:
                        output += ' ' * ( ind['Drop'][j] + ind['Mat'][j] )

                elif txt['Drop'][i][j] == '' or txt['Drop'][i][j] is None:
                    continue
                else:
                    for key in [ 'Drop', 'Mat' ]:
                        output += fmt[key].format( txt[key][i][j], ind[key][j] )

            if not two and Solution.saved_format >= 0:
                output += ' ' * 10 + tail
            output += '\n'
        
        if two:
            return output_m , output
        else:
            return output
    
    def add_drops( self, txt, drop_line, runs, index_to_name, fmt ):
        gained_mats = False
        if txt['Drop'] == []:
            txt['Drop'].append([])
            txt['Mat'].append([])

        for i in range(len( drop_line )):
            mat_drop = drop_line[i]
            if mat_drop > 0:
                txt['Drop'][-1].append( fmt.format( runs*mat_drop ) + ' ' )
                txt['Mat'][-1].append( index_to_name[i] + ' , ')
                gained_mats = True
        
        # Remove the ', ' from the last mat. 'gained_mats' flag just for extra security
        if gained_mats:
            last_mat = txt['Mat'][-1][-1]
            txt['Mat'][-1][-1] = last_mat[0:( len(last_mat) - 2 )]
        
        return txt
    
    def new_month( self, txt, sol: Solution, new_Qst, new_Run, new_Drop, i = -1 ):
        txt['Qst'].append(new_Qst)
        txt['Run'].append(new_Run)
        txt['Drop'].append(new_Drop)
        txt['Mat'].append(new_Drop.copy())

        sol.get_AP_saved( txt['Save'], i )
        return txt
    
    def read_ticket_data(self, txt, start, sol: Solution, nodes: QuestData ):
        prev_relevant_month = False
        prev_relevant_year = False

        for i in range(start, len(sol.run_int)):

            run_count = int(sol.run_int[i])
            if run_count > 0:

                month_name = nodes.quest_names[i]
                if month_name != prev_relevant_month:

                    cur_year = month_name.split()[1]
                    if cur_year != prev_relevant_year:
                        if prev_relevant_year != False:
                            txt = self.new_month( txt, sol, '----', '', [''] )
                        prev_relevant_year = cur_year

                    txt = self.new_month( txt, sol, month_name, '= ', [], i )
                
                txt = self.add_drops(txt, nodes.drop_matrix[i], run_count, 
                                     sol.index_to_name, "{:.0f}" )

                prev_relevant_month = month_name

        return txt
    
    def read_drop_data( self, txt, sol: Solution, nodes: QuestData ):
        ticket_start = -1

        for i in range(len(sol.run_int)):
            if nodes.quest_names[i] in nodes.recorded_months:
                ticket_start = i
                break

            run_count = int(sol.run_int[i])
            if run_count > 0:
                txt['Qst'].append( nodes.quest_names[i] + ':' )
                txt['Run'].append( "{:,}".format(run_count) + ' times' )

                if nodes.runs_per_box[i] != 'F':
                    boxes = '   Boxes Farmed = '
                    boxes += "{:.2f}".format( run_count / nodes.runs_per_box[i] )
                else:
                    boxes = ''
                txt['Box'].append(boxes)

                sol.get_AP_saved( txt['Save'], i )

                # For Farming Plan Drops
                txt['Drop'].append([])
                txt['Mat'].append([])
                txt = self.add_drops(txt, nodes.drop_matrix[i], run_count, 
                                     sol.index_to_name, "{:.2f}" )
        return txt, ticket_start

    def create_drop_file(self, sol: Solution, nodes: QuestData ):
        txt = {}
        for key in [ 'Qst', 'Run', 'Box', 'Mat', 'Drop', 'Save' ]:
            txt[key] = []

        # Creates matrix of drop data information for each quest.
        txt, ticket_start = self.read_drop_data( txt, sol, nodes )

        # Formats the drop parts of the output files.
        output_m, output_d = self.write_farming_plan( txt, True )

        # Creates matrix of ticket choice information for each month.
        if ticket_start != -1 and ticket_start < (len(sol.run_int) - 1):
            txt_t = {}
            for key in txt.keys():
                txt_t[key] = []
            txt_t = self.read_ticket_data(txt_t, ticket_start, sol, nodes )

            # Formats the ticket parts of the output files.
            if txt_t['Qst'] != []:
                output_t = '\nThe choices you should make for '
                output_t += 'Monthly Exchange Tickets are:\n'
                output_t += self.write_farming_plan( txt_t )
                
                output_m += self.console_print( output_t, False )
                output_d += output_t

        return output_m, output_d


    def avoid_plan_name_error( self, former_plans, text ):
        os.makedirs(os.path.dirname(former_plans), exist_ok=True)
        self.final_write( former_plans, text )


    def file_creation( self, plan_name, file_name, text, 
                      debug_report = False, failure = False ):
        path_pre = Inter.path_prefix
        name_prefix = os.path.join( path_pre, 'Former Plans' )
        name_suffix = time.strftime("%Y%m%d_%H%M%S__", time.localtime()) + file_name

        main_file_name = os.path.join( path_pre, file_name )
        if failure:
            main_file_name = os.path.join( path_pre, plan_name + file_name )

        self.final_write( main_file_name, text, True )
        
        try:
            file_name = os.path.join( name_prefix, plan_name + name_suffix )
            self.avoid_plan_name_error( file_name, text )
        except OSError:
            if debug_report:
                text = '!! Plan Name not accepted by OS\n\n' + text
            file_name = os.path.join( name_prefix, name_suffix )
            self.avoid_plan_name_error( file_name, text )


    def make_report( self, text, header = '', extra = 0 ):
        if text == []:
            return ''
        
        indent = self.find_indent(text)

        run_debug = '__' + header + '\n'
        for i in range(len(text)):
            for j in range(len(text[i])):
                run_debug += "{:<{}}".format(text[i][j], indent[j])
            run_debug += '\n'
        
        run_debug += '\n' * extra
        return run_debug
    
    
    def create_note_file( self, plan_name = '', fail = False ):
        output = ''
        debug = Inter.Debug()
    
        if debug.error[0] != '':
            output = '!! WARNING !!\n'
            output += debug.error[0] + '\n'
        
        if debug.error[1] != '':
            output += debug.error[1] + '\n'
    
        output += self.make_report( debug.config_notes, 'Configurations:', 1 )

        output += debug.monthly_notes + '\n'

        txt = 'The Events included in this analysis were:'
        output += self.make_report( debug.event_notes, txt, 2 )

        txt = 'The Lotto Drop Bonuses for each Quest were:'
        output += self.make_report( debug.lotto_notes, txt, 2 )

        txt = 'The following are notes to make sure that '
        txt += 'Run Caps were applied correctly:'
        output += self.make_report( debug.run_cap_debug, txt )

        self.file_creation( plan_name, 'Config Notes.txt', output, True, fail )


    def create_debug(self):
        if Output.not_test:
            print('FAILED EXECUTION')
        Output().create_note_file( 'FAILED_EXECUTION__', True )


    def print_out( self, sol: Solution, nodes: QuestData ):
        if sol.run_int is None:
            Output().create_debug()
        else:
            out = self.console_print( 'These results are: ' + sol.status )
            txt = 'The total AP required is: ' + "{:,}".format(sol.total_AP)+'\n'
            out += self.console_print( txt )
            out += self.console_print( 'You should run:' )

            out_m, out_d = self.create_drop_file( sol, nodes )
            out_d = out + out_d
            out += out_m
            
            if Inter.ConfigList.settings['Output Files']:
                plan_name = Inter.ConfigList.settings['Plan Name']
                if plan_name:
                    plan_name += '_'

                self.file_creation( plan_name, 'Farming Plan.txt', out )
                self.file_creation( plan_name, 'Farming Plan Drops.txt', out_d)
                self.create_note_file(plan_name)