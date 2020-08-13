import cirq
import numpy as np

from .cnx_n_m import multicontrolgate

def grovers_integer_search(c, reg, ancilla, val, num_rounds=None):
    assert 0 <= val < 2 ** len(reg)
    
    N = len(reg)
    m = len(ancilla)
    
    vals = [int(i) for i in list(bin(val))[2:][::-1]]
    
    if num_rounds is None:
        num_rounds = int(np.round(np.pi * 2 ** (N/2-2), 0))
    else:
        num_rounds = num_rounds
            
    def oracle():
        c.h(reg[-1])
        
        for i, v in enumerate(vals):
            if not v:
                c.x(reg[i])
                
        multicontrolgate(c, reg[:-1], reg[-1], ancilla, [])
        
        for i, v in enumerate(vals):
            if not v:
                c.x(reg[i])
                
        c.h(reg[-1])
        
    def diffusion():
        for control in reg:
            c.h(control)
            c.x(control)
            
        c.h(reg[-1])
        multicontrolgate(c, reg[:-1], reg[-1], ancilla, [])
        c.h(reg[-1])
        
        for control in reg:
            c.x(control)
            c.h(control)
            
    for control in reg:
        c.h(control)
        
    for _ in range(num_rounds):
        oracle()
        diffusion()


def generate_grover_integer_search_circuit(n, m, val, num_rounds=None):
    '''
        n: register size
        m: number of ancilla (clean)
        val: which val to search for
        num_rounds: none if do optimal
    '''
    qs = list(range(n + m))
    c = qiskit.circuit.QuantumCircuit(n + m)
    grovers_integer_search(c, qs[:n], qs[n:], val, num_rounds)
    return c
