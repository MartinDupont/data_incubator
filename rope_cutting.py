# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 13:43:32 2018

@author: martin
"""
import random
import numpy as np
# ========================= functions ======================================= #
def cut_the_rope(T, N):
    # Recursive base cases
    if N == 3:
        return 1
    if N < 3:
        return N
    if T == 1:
        return N
          
    first = random.choice(range(1, N))
    second = random.choice(range(1, N-2))
    if second >= first:
        second += 1
        # cheap way of implementing selection of interior points without replacement

    section_1 = min((first, second)) # this will return the length of the leftmost segment
    section_2 = abs(first - second)
    section_3 = N - max((first, second))
    
    N = max(section_1, section_2, section_3) 
    S = cut_the_rope(T-1, N) 
    return S


def generate_samples(T, N, n_samples):
    out = np.zeros(n_samples)
    for i in range(n_samples):
        out[i] = cut_the_rope(T, N)
        
    return out


# ================== Start main code ======================================== #
n_samples = 100000000    
samples = generate_samples(5, 64, n_samples)

print("Mean for T=5 and N=64: {}".format(np.mean(samples)))
print("Sigma for T=5 and N=64: {}".format(np.sqrt(np.var(samples))))   
 
n_samples_gt_4 = np.sum(samples > 4)
n_samples_gt_8 = np.sum(samples > 8)
prob = n_samples_gt_8*1.0/n_samples_gt_4
print("Conditional probability of g.t. 8 given g.t. 4 for T=5 and N=64: {}".format(prob))

samples = generate_samples(10, 1024, n_samples)

print("Mean for T=10 and N=1024: {}".format(np.mean(samples)))
print("Sigma for T=10 and N=1024: {}".format(np.sqrt(np.var(samples))))   
n_samples_gt_6 = np.sum(samples > 6)
n_samples_gt_12 = np.sum(samples > 12)
prob = n_samples_gt_12 * 1.0/n_samples_gt_6
print("Conditional probability of g.t. 8 given g.t. 4 for T=10 and N=1024: {}".format(prob))





   