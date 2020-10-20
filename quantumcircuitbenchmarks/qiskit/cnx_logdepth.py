import qiskit
import numpy as np
from .cnx_halfdirty import *

def string_to_gate(circuit, s):
    if s[0] == 'toffoli':
        circuit.toffoli(s[1], s[2], s[3])
    if s[0] == 'cx':
        circuit.cx(s[1], s[2])
    if s[0] == 'cnx_log_depth':
        cnx_log_depth(circuit, *s[1:])
    if s[0] == 'cnx_half_dirty':
        cnx_halfdirty(circuit, *s[1:])
        
def cnx_log_depth(circuit, controls, target, ancilla):
    if len(controls) == 2:
        circuit.toffoli(controls[0], controls[1], target)
    elif len(controls) == 1:
        circuit.cx(controls[0], target)
    else:
        # Build the list
        depth = int(np.ceil(np.log2(len(controls))) - 1)
        new_bits = controls
        curr_ancil = 0
        store_gates = []
        for layer in range(depth):
            bits = new_bits
            new_bits = []
            for i in range(len(bits)//2):
                g = ('toffoli', bits[2*i], bits[2*i+1], ancilla[curr_ancil])
                string_to_gate(circuit, g) 
                store_gates.append(g)
                new_bits.append(ancilla[curr_ancil])
                curr_ancil = curr_ancil + 1
            if len(bits) % 2 == 1:
                new_bits.append(bits[-1])
                
        circuit.toffoli(new_bits[0], new_bits[1], target)
        # Get the ancilla back
        for g in reversed(store_gates):
            string_to_gate(circuit, g)
            
def generate_cnx_log_depth(n):
    # N controls, N + N - 2 + 1 total qubits = n => N = (n + 1) / 2
    assert (n + 1) % 2 == 0
    
    qs = list(range(n))
    N = int((n + 1) / 2)
    c = qiskit.circuit.QuantumCircuit(n)
    cnx_log_depth(c, qs[:N], qs[N], qs[N+1:])
    return c