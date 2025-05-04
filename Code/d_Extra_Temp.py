import Planner as Plan
import numpy as np

class Test_14():
    def __init__(self, toolkit):
        nodes = toolkit['nodes']
        input_data = toolkit['input']
        run_cap_matrix = toolkit['runMat']

        plan = Plan.Planner( nodes, input_data, run_cap_matrix, 0 )
        prob , runs , tot_AP = plan.planner()

        self.drop_matrix = plan.drop_matrix
        self.run_caps = plan.run_caps
        self.AP_costs = plan.AP_costs

        if prob.status == 'optimal' and plan.run_size > 1:
            self._saved_AP( runs, tot_AP )
    
    def check_matrix( self, m1, m2, index, axis = 0, mat = False ):
        if len(m1) == 0:
            num = 0
            if isinstance( self.test, int ):
                num += 1
            if len(m2) > num:
                self.hole()

        elif len(m1) > 1:
            x = 0
            for i in range(len(m1)):
                if mat and isinstance( self.test, int ) and x == self.test:
                    x += 1
                if axis == 0 and x == index:
                    x += 1
                
                if len(m1[0]) > 1:
                    y = 0
                    for j in range(len(m1[0])):
                        if axis == 1 and y == index:
                            y += 1

                        if (m1[i][j] != m2[x][y]):
                            self.hole()
                        y += 1

                elif (m1[i][0] != m2[x][0]):
                    self.hole()
                x += 1

        elif len(m1[0]) > 1:
            y = 0
            for j in range(len(m1[0])):
                if axis == 1 and y == index:
                    y += 1

                if (m1[0][j] != m2[0][y]):
                    self.hole()
                y += 1

        elif (m1[0][0] != m2[0][0]):
            self.hole()
    
    def hole(self):
        a = 1
        b = 1
    
    def check_dict( self, m1, m2: dict, index ):
        for key in m2.keys():
            if key == 'Event':
                x = 0
                for i in range(len(m1[key])):
                    if isinstance( self.test, int ) and x == self.test:
                        x += 1
                    if (m1[key][i] != m2[key][x]):
                        self.hole()
                    x += 1
            else:
                self.check_matrix( m1[key], m2[key], index, 1, True )
    
    def check( self, drops, run_caps, costs, index ):
        self.check_matrix( drops, self.drop_matrix, index, 1 )
        self.check_dict( run_caps, self.run_caps, index )
        self.check_matrix( costs, self.AP_costs, index, 1 )

    def _cut_index( self, matrix, index, axis = 0 ):
        if isinstance( matrix, np.ndarray ):
            new_mat = np.copy( matrix )

        elif isinstance( matrix, list ):
            new_mat = matrix.copy()

        elif isinstance( matrix, dict ):
            try:
                mat = matrix['Matrix']
            except:
                return matrix

            new_mat = {}
            new_cut = self._cut_index( matrix['Matrix'], index, 1 )
            for i in range(len(mat)):
                if mat[i][index] > 0:
                    col = i
                    break
            else:
                col = 'F'
            
            if col != 'F':
                if np.sum(mat, axis = 1)[i] == 1:
                    self.test = i
                    new_mat['Event'] = self._cut_index( matrix['Event'], i )
                    new_mat['List'] = self._cut_index( matrix['List'], i )
                    new_mat['Matrix'] = self._cut_index( new_cut, i )
                    return new_mat

            new_mat['Event'] = np.copy( matrix['Event'] )
            new_mat['List'] = matrix['List'].copy()
            new_mat['Matrix'] = new_cut
            return new_mat

        return np.delete( new_mat, index, axis )

    def _cut_planner( self, index ):
        self.test = ''
        new_drops = self._cut_index( self.drop_matrix, index, 1 )
        new_run_caps = self._cut_index( self.run_caps, index )
        new_costs = self._cut_index( self.AP_costs, index, 1 )
        self.check( new_drops, new_run_caps, new_costs, index )

    def _saved_AP( self, run_int, total_AP ):
        AP_saved = []
        for i in range(len(run_int)):
            if int(run_int[i]) > 0:
                new_AP = self._cut_planner(i)

                if isinstance( new_AP, int ):
                    new_AP -= total_AP
                AP_saved.append(new_AP)

            else:
                AP_saved.append(0)