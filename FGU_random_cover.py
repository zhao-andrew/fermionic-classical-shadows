#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import itertools

#%% Functions for permutation matrices

def perm_parity(input_list):
    """
    Determines the parity of the permutation required to sort the list.
    Outputs 0 (even) or 1 (odd).
    """
    
    parity = 0
    for i, j in itertools.combinations(range(len(input_list)), 2):
        if input_list[i] > input_list[j]:
            parity += 1
    
    return parity % 2

def rand_sym_mat(N):
    """
    Generates a random N x N permutation matrix.
    """
    Q = np.eye(N, dtype='int')
    
    p = np.random.permutation(np.arange(N))
    
    return Q[:, p]

def rand_alt_mat(N):
    """
    Generates a random N x N permutation matrix of determinant +1.
    """
    
    Q = np.eye(N, dtype='int')
    
    s = 1
    while s > 0:
        p = np.random.permutation(np.arange(N))
        s = perm_parity(p)
    
    return Q[:, p]

def rand_sym_perm(N):
    """
    Generates a random N-permutation (as a tuple). Permutations in this form
    can be thought of as maps p : {0, ..., N-1} -> {0, ..., N-1}, i -> p[i],
    where p[i] is the i-th element of the tuple p.
    """
    
    return tuple(np.random.permutation(np.arange(N)))

def rand_alt_perm(N):
    """
    Generates a random N-permutation of even parity.
    """
    
    s = 1
    while s > 0:
        p = np.random.permutation(np.arange(N))
        s = perm_parity(p)
    
    return tuple(p)

#%% Functions for measurement counts

def permute_majorana(indices, Q):
    """
    Permutes indices according to the permutation Q. Rather than returning the
    resulting indices as-is, it returns them sorted along with the sign of the
    permutation which was required to do so (NOT the sign of Q).

    Parameters
    ----------
    indices : iterable of int
        Input (Majorana operator) indices; length-2k indices correspond to a
        k-RDM operator.
    Q : iterable of int
        Length-2n permutation.

    Returns
    -------
    tuple
        The image of the permutation, sorted.
    sign : int
        The sign required to sort the permuted indices.

    """
    
    l = [Q[i] for i in indices]
    sign = (-1)**perm_parity(l)
    l.sort()
    
    return tuple(l), sign

def invert_permutation(permutation):
    """
    Given input permutation Q, returns Q^{-1}.

    Parameters
    ----------
    permutation : iterable
        A permutation as an iterable.

    Returns
    -------
    tuple
        The inverse permutation.

    """
    
    return tuple(np.arange(len(permutation))[np.argsort(permutation)])

def tally_majorana_matches(ops_dict, Q, k_max=None):
    """
    Given a 2n x 2n permutation Q, mark which elements of obs_dict can be
    measured (diagonalized) by the fermionic Gaussian circuit U(Q).

    Parameters
    ----------
    ops_dict : dict
        Dictionary of Majorana operators which we wish to measure. {key : val}
        pattern should be {(Majorana indices) : number of times accounted for}.
    Q : iterable of int
        Permutation as a 2n-length tuple.
    k_max : int, optional
        The maximum Majorana degree in obs_dict to check for. If None, the
        maximum degree is automatically determined. It is preferrable to set
        this for speed.

    Returns
    -------
    list
        List of operators measured, as a tuple in the form (Majorana, diagonal
        Majorana, sign), where sign is the associated sign accrued by the
        unitary action. That is,
        
        U(Q) (Majorana) U(Q)^\dagger = sign * (diagonal Majorana).

    """
    
    if k_max is None:
        k_max = max([len(term) for term in ops_dict])
    
    n = len(Q) // 2
    
    measured_ops = []
    
    for j in range(1, k_max+1):
        for P in itertools.combinations(range(n), j):
            diag_index = [2*p + i for p in P for i in range(2)]
            
            Q_inv = invert_permutation(Q)
            permuted_diag_index, sign = permute_majorana(diag_index, Q_inv)
        
            if permuted_diag_index in ops_dict:
                ops_dict[permuted_diag_index] += 1
                measured_ops.append((permuted_diag_index, tuple(diag_index),
                                     sign))
    
    return measured_ops

def construct_random_measurements_FGU(ops_dict, n, k_max=None, r=10):
    """
    Constructs a random cover of ops_dict using the hyperparameter r. That is,
    it generates random 2n-permutations until all Majorana operators in
    ops_dict have been accounted for at least r times.

    Parameters
    ----------
    ops_dict : dict
        Dictionary of Majorana operators which we wish to measure. {key : val}
        pattern should be {(Majorana indices) : number of times accounted for}.
    n : int
        Number of fermionic orbitals.
    k_max : int, optional
        The maximum Majorana degree in obs_dict to check for. If None, the
        maximum degree is automatically determined. It is preferrable to set
        this for speed.
    r : int, optional
        The minimum number of times each operator must be covered until the
        function halts. The default is 10.

    Returns
    -------
    random_measurements : dict
        The resulting cover of Majorana operators. The dictionary pattern is
        {permutation : [(measured_op_indices, sign)]}.

    """
    
    random_measurements = {}
    
    while any(counts < r for counts in ops_dict.values()):
        Q = rand_sym_perm(2*n)
        if Q in random_measurements:
            continue
        
        measured_ops = tally_majorana_matches(ops_dict, Q,
                                                     k_max=k_max)
        
        if len(measured_ops) > 0:
            random_measurements[Q] = measured_ops
    
    return random_measurements

#%% Example usage

if __name__ == '__main__':
    
    """Set system size and order of k-RDM desired (usually k = 2 is sufficient,
    e.g., for local electron-electron interactions)."""
    n_orbitals = 6
    k = 2
    
    """Construct a k-RDM in the Majorana representation as a dictionary of form
    {majorana_indices : expectation_value}. Here, we insert all possible Majorana
    operators if we are interested in the entire k-RDM; however, the dictionary
    can be constructed differently if only a subset of observables are desired."""
    majorana_k_rdm_counts = {}
    for j in range(1, k + 1):
        for mu in itertools.combinations(range(2 * n_orbitals), 2 * j):
            majorana_k_rdm_counts[mu] = 0
    
    """Generate a random cover of FGU measurement settings such that all Majorana
    operators are covered at least r = 50 times. This means that if one wishes to
    estimate each operator to statistical accuracy corresponding to S samples, each
    measurement setting (circuit) needs to be repeated only S/r times. Note that
    specifying the k_max parameter is merely for a minor computational speedup in
    the case that we are targeting the entire k-RDM, and is not necessary."""
    rand_meas = construct_random_measurements_FGU(majorana_k_rdm_counts, n_orbitals,
                                                  k_max=k, r=50)
