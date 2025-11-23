import Planner as plan
import numpy as np

class Test_15(plan.Planner):
    valid = True

    def __init__(self, toolkit):
        nodes = toolkit.nodes
        input_data = toolkit.input
        run_cap_matrix = toolkit.run_mat

        planner = plan.Planner( nodes, input_data, run_cap_matrix, 0 )
        sol: plan.Solution = planner.planner()

        self.drop_matrix = planner.drop_matrix
        self.run_caps = planner.run_caps
        self.AP_costs = planner.ap_costs

        if sol.status == 'optimal' and planner.run_size > 1:
            self._calculate_ap_saved
    
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
        Test_15.valid = False
        a = 1
    
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

    def _cut_dict( self, matrix, index, monthly = True ):
        new_mat = {}
        new_cut = self._cut_matrix( matrix['Matrix'], index, 1 )

        if monthly:
            for i in range(len(matrix['Matrix'])):
                if matrix['Matrix'][i][index[0]] > 0:
                    self.test = i
                    new_mat['Event'] = self._cut_matrix( matrix['Event'], [i] )
                    new_mat['List'] = self._cut_matrix( matrix['List'], [i] )
                    new_mat['Matrix'] = self._cut_matrix( new_cut, [i] )
                    return new_mat

        new_mat['Event'] = np.copy( matrix['Event'] )
        new_mat['List'] = matrix['List'].copy()
        new_mat['Matrix'] = new_cut
        return new_mat

    def _cut_planner( self, logic, index, monthly = False ):
        if not logic:
            return 'F', index
        
        self.test = ''
        new_drops = self._cut_matrix( self.drop_matrix, index, 1 )
        new_run_caps = self._cut_dict( self.run_caps, index, monthly )
        new_costs = self._cut_matrix( self.AP_costs, index, 1 )

        self.check( new_drops, new_run_caps, new_costs, index )