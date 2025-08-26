"""Bounded-variable least-squares algorithm."""
import numpy as np
from numpy.linalg import norm, lstsq
from scipy.optimize import OptimizeResult

def cgls(A,b,l,u,itern=100,std=0,x0=None,crit=1e-10):
    #
    sa = A.shape
    Ac = sa[1]
    #
    crit2 = Ac*crit**2
    #
    if x0 is None:
       X = np.zeros([Ac,1])
    else:
       X = x0
    #
    bsq = np.sum(b**2)
    xi  = np.dot(A,X)-b
    rp  = np.sum(xi**2)
    g   = -1 * np.dot(A.T,xi)
    h   = g
    residu = np.zeros(itern,1)
    #
    for iiter in range(Ac*10):
        #
        xi = np.dot(A,h)
        anum = np.sum(g*h)
        aden = np.sum(xi**2)
        if aden==0:
           print(" ... Warning: very singular matrix" )
        anum = anum / aden
        X = X + anum*h
        #
        X[X<l] = l[X<l]
        X[X>u] = u[X>u]
        #
        xj = np.dot(A,X) - b
        #
        xj[np.abs(xj)<=std] = 0
        rsq = np.sum(xj**2)
        residu[iiter] = rsq
        #
        if rsq==rp or rsq<= bsq*crit2 or iiter==itern:
            qual = 1
            rsq = residu[0:iiter]
            return X, residu, qual
        #
        rp = rsq
        xi = np.dot(A.T,xj)
        gg = np.sum(g**2)
        dgg = np.sum((xi+g)*xi)
        if gg == 0:
            qual = 3
            X[:] = np.nan
            return X, residu, qual
        #
        g = -xi
        h = g + dgg / gg * h
        #
    #
    qual = 4
    return X,residu,qual

def compute_kkt_optimality(g, on_bound):
    """Compute the maximum violation of KKT conditions."""
    g_kkt = g * on_bound
    free_set = on_bound == 0
    g_kkt[free_set] = np.abs(g[free_set])
    return np.max(g_kkt)


def bvls(A, b, x_lsq, lb, ub, tol, max_iter, verbose, rcond=None):
    m, n = A.shape

    x = x_lsq.copy()
    on_bound = np.zeros(n)

    mask = x <= lb
    x[mask] = lb[mask]
    on_bound[mask] = -1

    mask = x >= ub
    x[mask] = ub[mask]
    on_bound[mask] = 1

    free_set = on_bound == 0
    active_set = ~free_set
    free_set, = np.nonzero(free_set)

    r = A.dot(x) - b
    cost = 0.5 * np.dot(r, r)
    initial_cost = cost
    g = A.T.dot(r)

    cost_change = None
    step_norm = None
    iteration = 0

    # This is the initialization loop. The requirement is that the
    # least-squares solution on free variables is feasible before BVLS starts.
    # One possible initialization is to set all variables to lower or upper
    # bounds, but many iterations may be required from this state later on.
    # The implemented ad-hoc procedure which intuitively should give a better
    # initial state: find the least-squares solution on current free variables,
    # if its feasible then stop, otherwise, set violating variables to
    # corresponding bounds and continue on the reduced set of free variables.

    while free_set.size > 0:
   
        iteration += 1
        x_free_old = x[free_set].copy()

        A_free = A[:, free_set]
        b_free = b - A.dot(x * active_set)
        z = lstsq(A_free, b_free, rcond=rcond)[0]

        lbv = z < lb[free_set]
        ubv = z > ub[free_set]
        v = lbv | ubv

        if np.any(lbv):
            ind = free_set[lbv]
            x[ind] = lb[ind]
            active_set[ind] = True
            on_bound[ind] = -1

        if np.any(ubv):
            ind = free_set[ubv]
            x[ind] = ub[ind]
            active_set[ind] = True
            on_bound[ind] = 1

        ind = free_set[~v]
        x[ind] = z[~v]

        r = A.dot(x) - b
        cost_new = 0.5 * np.dot(r, r)
        cost_change = cost - cost_new
        cost = cost_new
        g = A.T.dot(r)
        step_norm = norm(x[free_set] - x_free_old)

        if np.any(v):
            free_set = free_set[~v]
        else:
            break

    if max_iter is None:
        max_iter = n
    max_iter += iteration

    termination_status = None

    # Main BVLS loop.

    optimality = compute_kkt_optimality(g, on_bound)
    for iteration in range(iteration, max_iter):  # BVLS Loop A
        if optimality < tol:
            termination_status = 1

        if termination_status is not None:
            break

        move_to_free = np.argmax(g * on_bound)
        on_bound[move_to_free] = 0
        
        while True:   # BVLS Loop B

            free_set = on_bound == 0
            active_set = ~free_set
            free_set, = np.nonzero(free_set)
    
            x_free = x[free_set]
            x_free_old = x_free.copy()
            lb_free = lb[free_set]
            ub_free = ub[free_set]

            A_free = A[:, free_set]
            b_free = b - A.dot(x * active_set)
            z = lstsq(A_free, b_free, rcond=rcond)[0]

            lbv, = np.nonzero(z < lb_free)
            ubv, = np.nonzero(z > ub_free)
            v = np.hstack((lbv, ubv))

            if v.size > 0:
                alphas = np.hstack((
                    lb_free[lbv] - x_free[lbv],
                    ub_free[ubv] - x_free[ubv])) / (z[v] - x_free[v])

                i = np.argmin(alphas)
                i_free = v[i]
                alpha = alphas[i]

                x_free *= 1 - alpha
                x_free += alpha * z
                x[free_set] = x_free

                if i < lbv.size:
                    on_bound[free_set[i_free]] = -1
                else:
                    on_bound[free_set[i_free]] = 1
            else:
                x_free = z
                x[free_set] = x_free
                break

        step_norm = norm(x_free - x_free_old)

        r = A.dot(x) - b
        cost_new = 0.5 * np.dot(r, r)
        cost_change = cost - cost_new

        if cost_change < tol * cost:
            termination_status = 2
        cost = cost_new

        g = A.T.dot(r)
        optimality = compute_kkt_optimality(g, on_bound)

    if termination_status is None:
        termination_status = 0

    return OptimizeResult(
        x=x, fun=r, cost=cost, optimality=optimality, active_mask=on_bound,
        nit=iteration + 1, status=termination_status,
        initial_cost=initial_cost)
