
import numpy as np
from hylaa.hybrid_automaton import LinearHybridAutomaton, HyperRectangle, LinearConstraint
from hylaa.star import init_hr_to_star
from hylaa.engine import HylaaSettings, HylaaEngine
from hylaa.containers import PlotSettings
from hylaa.pv_container import PVObject
from hylaa.timerutil import Timers
from hylaa.simutil import compute_simulation
import matplotlib.pyplot as plt
from control import *


def define_ha(settings, usafe_r):
    # x' = Ax + Bu + c
    '''make the hybrid automaton and return it'''

    ha = LinearHybridAutomaton()
    ha.variables = ["x", "y"]

    loc1 = ha.new_mode('loc1')

    a_matrix = np.array([[2, -1], [1, 0]], dtype=float)

    loc1.c_vector = np.array([0, 0], dtype=float)

    b_matrix = np.array([[2], [0]], dtype=float)

    Q = np.array([[100, 0], [0, 1]], dtype=float)
    u_dim = len(b_matrix[0])

    R = np.eye(u_dim)
    (X, L, G) = care(a_matrix, b_matrix, Q, R)
    control_f = open("./control_vals.txt", "a")
    control_f.write("Q: "+str(Q)+"\n")
    control_f.write("P: "+str(X)+"\n")
    control_f.write("K: "+str(G)+"\n")
    control_f.write("PBK: "+str(np.matmul(X, np.matmul(b_matrix, G)))+"\n")
    control_f.write("PA: "+str(np.matmul(X, a_matrix))+"\n")
    control_f.write("A'P: "+str(np.matmul(a_matrix.T, X))+"\n")
    control_f.close()
    k_matrix = np.array(G)

    a_bk_matrix = a_matrix - np.matmul(b_matrix, k_matrix)
    loc1.a_matrix = a_bk_matrix

    error = ha.new_mode('_error')
    error.is_error = True

    trans = ha.new_transition(loc1, error)

    usafe_set_constraint_list = []
    if usafe_r is None:
        usafe_set_constraint_list.append(LinearConstraint([-1.0, 0.0], -1.0))
    else:
        usafe_star = init_hr_to_star(settings, usafe_r, ha.modes['_error'])

        for constraint in usafe_star.constraint_list:
            usafe_set_constraint_list.append(constraint)

    for constraint in usafe_set_constraint_list:
        trans.condition_list.append(constraint)

    return ha, usafe_set_constraint_list


def define_init_states(ha, init_r):
    '''returns a list of (mode, HyperRectangle)'''
    # Variable ordering: [x, y]
    rv = []
    rv.append((ha.modes['loc1'], init_r))

    return rv


def define_settings():
    'get the hylaa settings object'
    plot_settings = PlotSettings()
    plot_settings.plot_mode = PlotSettings.PLOT_IMAGE
    plot_settings.xdim = 0
    plot_settings.ydim = 1

    s = HylaaSettings(step=0.01, max_time=10.0, disc_dyn=False, plot_settings=plot_settings)
    s.stop_when_error_reachable = False
    
    return s


def run_hylaa(settings, init_r, usafe_r):

    'Runs hylaa with the given settings, returning the HylaaResult object.'

    ha, usafe_set_constraint_list = define_ha(settings, usafe_r)
    init = define_init_states(ha, init_r)

    engine = HylaaEngine(ha, settings)
    reach_tree = engine.run(init)

    return PVObject(len(ha.variables), usafe_set_constraint_list, reach_tree)


if __name__ == '__main__':
    settings = define_settings()
    init_r = HyperRectangle([(-2.0, -1.0), (-2.0, -1.0)])

    pv_object = run_hylaa(settings, init_r, None)
    depth_direction = np.identity(len(init_r.dims))
    control_f = open("./control_vals.txt", "a")
    for idx in range(len(init_r.dims)):
        deepest_ce_1 = pv_object.compute_deepest_ce(depth_direction[idx])
        # print(deepest_ce_1.ce_depth)
        deepest_ce_2 = pv_object.compute_deepest_ce(-depth_direction[idx])
        print("depth difference: {}".format(abs(deepest_ce_1.ce_depth - deepest_ce_2.ce_depth)))
        # print(deepest_ce_2.ce_depth)
        control_f.write("depth difference: "+str(abs(deepest_ce_1.ce_depth - deepest_ce_2.ce_depth)) + "\n")
    control_f.write("******************\n")
    control_f.close()
    # pv_object.compute_robust_ce()


